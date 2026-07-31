from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    ASTATState,
    ComputationalBank,
    DIVIDE_SIGN_CLASS_MASK,
    DIVIDE_SIGN_CLASS_VALUE,
    DIVIDE_X_DREG,
    DREG,
    DREGWrite,
    DivideSignInputs,
    DivideSignState,
    ExactWord,
    StatusRegisters,
    UNKNOWN,
    apply_divide_sign_cycle,
    decode_divide_sign,
    is_divide_sign_class,
    read_dreg,
)


def _opcode(yop: int, xop: int) -> int:
    return 0x060000 | (yop << 11) | (xop << 8)


def _bank(*, ay0: int = 0x8001, ay1: int = 0x1234, af: int = 0xFEDC) -> ComputationalBank:
    return ComputationalBank(
        ax=(ExactWord(16, 0x0102), ExactWord(16, 0x8102)),
        ay=(ExactWord(16, ay0), ExactWord(16, ay1)),
        ar=ExactWord(16, 0x7FFF),
        af=ExactWord(16, af),
        mr=(ExactWord(16, 0x8000), ExactWord(16, 0x0001), ExactWord(8, 0x80)),
        sr=(ExactWord(16, 0xFFFF), ExactWord(16, 0x0000)),
    )


def _state(
    *,
    primary: ComputationalBank | None = None,
    alternate: ComputationalBank | None = None,
    astat: int = 0xD5,
    mstat: int = 0,
) -> DivideSignState:
    return DivideSignState(
        primary=primary or _bank(),
        alternate=alternate or _bank(ay0=0x1111, ay1=0x2222, af=0x3333),
        status=StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, astat)),
            mstat=ExactWord(4, mstat),
        ),
    )


class DivideSignTests(unittest.TestCase):
    def test_machine_readable_semantics_and_operand_roles(self) -> None:
        root = Path(__file__).resolve().parents[1]
        isa = json.loads(
            (root / "docs/generated/adsp2100_isa.yaml").read_text(encoding="utf-8")
        )
        instruction = next(
            item for item in isa["instructions"]
            if item["id"] == "DIVIDE-SIGN-TYPE-24"
        )
        self.assertEqual(instruction["status_flags_written"], ["AQ"])
        self.assertEqual(instruction["documented_cycles"]["base_instruction_cycles"], 1)
        semantics = json.loads(
            (root / "docs/generated/adsp2100_divide_sign_slice.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(semantics["decode"]["source_closed_words"], 16)
        self.assertEqual(semantics["cycle_contract"]["non_aq_astat_bits"], "PRESERVED")
        formats = json.loads(
            (root / "docs/generated/adsp2100_instruction_formats.yaml").read_text(
                encoding="utf-8"
            )
        )
        roles = {
            item["original_type"]: {field["id"]: field["role"] for field in item["fields"]}
            for item in formats["formats"]
            if item["original_type"] in (23, 24)
        }
        self.assertEqual(roles[23]["XOP"], "DIVISOR_INPUT")
        self.assertEqual(roles[24]["YOP"], "UPPER_DIVIDEND_INPUT")
        self.assertEqual(roles[24]["XOP"], "DIVISOR_INPUT")

    def test_complete_type_24_partition_and_supported_operand_subset(self) -> None:
        supported = 0
        for yop in range(4):
            for xop in range(8):
                opcode = _opcode(yop, xop)
                action = decode_divide_sign(opcode)
                self.assertIsNotNone(action)
                assert action is not None
                self.assertEqual((action.yop, action.xop), (yop, xop))
                self.assertEqual(action.supported, yop in (1, 2))
                supported += int(action.supported)
        self.assertEqual(supported, 16)
        self.assertEqual(DIVIDE_SIGN_CLASS_MASK, 0xFFE0FF)
        self.assertEqual(DIVIDE_SIGN_CLASS_VALUE, 0x060000)

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0x000000, 0x060001, 0x062000, 0x071000):
            self.assertFalse(is_divide_sign_class(opcode))
            self.assertIsNone(decode_divide_sign(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_divide_sign(opcode)

    def test_hand_derived_primary_fixtures(self) -> None:
        self.assertEqual(_opcode(1, 0), 0x060800)  # DIVS AY1, AX0
        self.assertEqual(_opcode(2, 5), 0x061500)  # DIVS AF, MR2
        self.assertEqual(_opcode(1, 0).to_bytes(3, "big").hex(), "060800")
        self.assertEqual(_opcode(2, 5).to_bytes(3, "big").hex(), "061500")

    def test_divs_uses_cycle_start_values_and_preserves_non_aq_status(self) -> None:
        state = _state(
            primary=_bank(ay0=0x8001, ay1=0xC001),
            astat=0xD5,
        )
        result = apply_divide_sign_cycle(
            state,
            DivideSignInputs(execute=True, opcode=_opcode(1, 0)),
        )
        self.assertTrue(result.boundary_valid)
        self.assertTrue(result.source_known)
        self.assertTrue(result.result_known)
        # AX0 is positive and AY1 negative, so qsign/AQ is one.
        self.assertIs(result.quotient_sign, True)
        self.assertEqual(result.state.primary.af, ExactWord(16, 0x8003))
        self.assertEqual(result.state.primary.ay[0], ExactWord(16, 0x0003))
        old = state.status.astat.to_word().value
        new = result.state.status.astat.to_word().value
        self.assertEqual(new & ~(1 << ASTATBit.AQ), old & ~(1 << ASTATBit.AQ))
        self.assertTrue(result.state.status.astat.bit(ASTATBit.AQ))

    def test_every_divisor_selection_obeys_sign_xor(self) -> None:
        state = _state()
        for xop, dreg in enumerate(DIVIDE_X_DREG):
            divisor = read_dreg(state.primary, dreg)
            assert isinstance(divisor, ExactWord)
            for yop, upper in ((1, state.primary.ay[1]), (2, state.primary.af)):
                assert isinstance(upper, ExactWord)
                result = apply_divide_sign_cycle(
                    state,
                    DivideSignInputs(execute=True, opcode=_opcode(yop, xop)),
                )
                expected = bool(((divisor.value ^ upper.value) >> 15) & 1)
                self.assertEqual(result.quotient_sign, expected)
                self.assertEqual(
                    result.state.primary.af,
                    ExactWord(16, ((upper.value << 1) & 0xFFFF) | 1),
                )
                self.assertEqual(
                    result.state.primary.ay[0],
                    ExactWord(16, 0x0002 | int(expected)),
                )

    def test_selected_alternate_bank_only_is_updated(self) -> None:
        state = _state(mstat=1)
        result = apply_divide_sign_cycle(
            state,
            DivideSignInputs(execute=True, opcode=_opcode(2, 7)),
        )
        self.assertEqual(result.state.primary, state.primary)
        self.assertNotEqual(result.state.alternate, state.alternate)
        self.assertEqual(result.state.alternate.af, ExactWord(16, 0x6666))
        self.assertEqual(result.state.alternate.ay[0], ExactWord(16, 0x2222))

    def test_unsupported_yop_and_nonclass_execution_are_action_free(self) -> None:
        state = _state()
        for opcode in (_opcode(0, 0), _opcode(3, 7), 0x071000):
            result = apply_divide_sign_cycle(
                state,
                DivideSignInputs(execute=True, opcode=opcode),
            )
            self.assertFalse(result.action_valid)
            self.assertFalse(result.boundary_valid)
            self.assertTrue(result.invalid_opcode)
            self.assertEqual(result.state, state)
        self.assertTrue(
            apply_divide_sign_cycle(
                state,
                DivideSignInputs(execute=True, opcode=_opcode(0, 0)),
            ).unsupported_subencoding
        )

    def test_unknown_source_invalidates_only_documented_destinations(self) -> None:
        original = _state(primary=replace(_bank(), ay=(ExactWord(16, 1), UNKNOWN)))
        result = apply_divide_sign_cycle(
            original,
            DivideSignInputs(execute=True, opcode=_opcode(1, 0)),
        )
        self.assertTrue(result.boundary_valid)
        self.assertFalse(result.source_known)
        self.assertIs(result.state.primary.af, UNKNOWN)
        self.assertIs(result.state.primary.ay[0], UNKNOWN)
        self.assertIs(result.state.status.astat.bit(ASTATBit.AQ), UNKNOWN)
        for bit in ASTATBit:
            if bit != ASTATBit.AQ:
                self.assertEqual(
                    result.state.status.astat.bit(bit),
                    original.status.astat.bit(bit),
                )

    def test_setup_writes_and_execute_conflicts_are_explicit(self) -> None:
        state = DivideSignState()
        state = apply_divide_sign_cycle(
            state,
            DivideSignInputs(mstat_write=ExactWord(4, 1)),
        ).state
        state = apply_divide_sign_cycle(
            state,
            DivideSignInputs(dreg_write=DREGWrite(DREG.AY0, ExactWord(16, 2))),
        ).state
        state = apply_divide_sign_cycle(
            state,
            DivideSignInputs(af_write=ExactWord(16, 3)),
        ).state
        self.assertEqual(state.alternate.ay[0], ExactWord(16, 2))
        self.assertEqual(state.alternate.af, ExactWord(16, 3))
        conflict = apply_divide_sign_cycle(
            state,
            DivideSignInputs(
                execute=True,
                opcode=_opcode(2, 0),
                astat_write=ExactWord(8, 0),
            ),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)

    def test_reset_preserves_authentic_unknown_computational_state(self) -> None:
        reset = apply_divide_sign_cycle(
            _state(),
            DivideSignInputs(reset=True, execute=True, opcode=_opcode(1, 0)),
        )
        self.assertEqual(reset.state, DivideSignState())
        self.assertIs(reset.state.primary.af, UNKNOWN)
        self.assertIs(reset.state.status.astat.bit(ASTATBit.AQ), UNKNOWN)
        self.assertFalse(reset.boundary_valid)


if __name__ == "__main__":
    unittest.main()
