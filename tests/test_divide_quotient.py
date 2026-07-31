from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    ASTATState,
    ComputationalBank,
    DIVIDE_QUOTIENT_CLASS_MASK,
    DIVIDE_QUOTIENT_CLASS_VALUE,
    DIVIDE_X_DREG,
    DREG,
    DREGWrite,
    DivideQuotientInputs,
    DivideQuotientState,
    DivideSignInputs,
    DivideSignState,
    ExactWord,
    StatusRegisters,
    UNKNOWN,
    apply_divide_quotient_cycle,
    apply_divide_sign_cycle,
    decode_divide_quotient,
    is_divide_quotient_class,
    read_dreg,
)


def _opcode(xop: int) -> int:
    return 0x071000 | (xop << 8)


def _bank(
    *,
    ay0: int = 0x8001,
    ay1: int = 0x1234,
    af: int = 0x0003,
) -> ComputationalBank:
    return ComputationalBank(
        ax=(ExactWord(16, 0x0002), ExactWord(16, 0x8002)),
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
) -> DivideQuotientState:
    return DivideQuotientState(
        primary=primary or _bank(),
        alternate=alternate or _bank(ay0=0x1111, ay1=0x2222, af=0x3333),
        status=StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, astat)),
            mstat=ExactWord(4, mstat),
        ),
    )


class DivideQuotientTests(unittest.TestCase):
    def test_machine_readable_semantics_and_operand_role(self) -> None:
        root = Path(__file__).resolve().parents[1]
        isa = json.loads(
            (root / "docs/generated/adsp2100_isa.yaml").read_text(encoding="utf-8")
        )
        instruction = next(
            item for item in isa["instructions"]
            if item["id"] == "DIVIDE-QUOTIENT-TYPE-23"
        )
        self.assertEqual(instruction["status_flags_read"], ["AQ"])
        self.assertEqual(instruction["status_flags_written"], ["AQ"])
        self.assertEqual(instruction["documented_cycles"]["base_instruction_cycles"], 1)
        semantics = json.loads(
            (root / "docs/generated/adsp2100_divide_quotient_slice.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(semantics["decode"]["source_closed_words"], 8)
        self.assertEqual(semantics["cycle_contract"]["non_aq_astat_bits"], "PRESERVED")

    def test_complete_type_23_partition(self) -> None:
        for xop in range(8):
            action = decode_divide_quotient(_opcode(xop))
            self.assertIsNotNone(action)
            assert action is not None
            self.assertEqual(action.xop, xop)
            self.assertEqual(action.divisor_name, (
                "AX0", "AX1", "AR", "MR0", "MR1", "MR2", "SR0", "SR1"
            )[xop])
        self.assertEqual(DIVIDE_QUOTIENT_CLASS_MASK, 0xFFF8FF)
        self.assertEqual(DIVIDE_QUOTIENT_CLASS_VALUE, 0x071000)

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0x000000, 0x071001, 0x070000, 0x060800):
            self.assertFalse(is_divide_quotient_class(opcode))
            self.assertIsNone(decode_divide_quotient(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_divide_quotient(opcode)

    def test_hand_derived_primary_fixtures(self) -> None:
        self.assertEqual(_opcode(0), 0x071000)  # DIVQ AX0
        self.assertEqual(_opcode(7), 0x071700)  # DIVQ SR1
        self.assertEqual(_opcode(0).to_bytes(3, "big").hex(), "071000")
        self.assertEqual(_opcode(7).to_bytes(3, "big").hex(), "071700")

    def test_old_aq_selects_subtract_or_add_and_all_writes_are_atomic(self) -> None:
        subtract_state = _state(primary=_bank(af=0x0003, ay0=0x8001), astat=0xD5 & ~0x20)
        subtract = apply_divide_quotient_cycle(
            subtract_state,
            DivideQuotientInputs(execute=True, opcode=_opcode(0)),
        )
        self.assertFalse(subtract.old_aq)
        self.assertFalse(subtract.add_divisor)
        self.assertEqual(subtract.alu_result, ExactWord(16, 0x0001))
        self.assertFalse(subtract.new_aq)
        self.assertTrue(subtract.quotient_bit)
        self.assertEqual(subtract.state.primary.af, ExactWord(16, 0x0003))
        self.assertEqual(subtract.state.primary.ay[0], ExactWord(16, 0x0003))

        add_state = _state(primary=_bank(af=0xFFFF, ay0=0x8001), astat=0x20)
        add = apply_divide_quotient_cycle(
            add_state,
            DivideQuotientInputs(execute=True, opcode=_opcode(0)),
        )
        self.assertTrue(add.old_aq)
        self.assertTrue(add.add_divisor)
        self.assertEqual(add.alu_result, ExactWord(16, 0x0001))
        self.assertFalse(add.new_aq)
        self.assertTrue(add.quotient_bit)
        self.assertEqual(add.state.primary.af, ExactWord(16, 0x0003))
        self.assertEqual(add.state.primary.ay[0], ExactWord(16, 0x0003))

    def test_every_divisor_selection_and_non_aq_status_preservation(self) -> None:
        for old_aq in (False, True):
            astat = 0xD5 | (int(old_aq) << int(ASTATBit.AQ))
            if not old_aq:
                astat &= ~(1 << int(ASTATBit.AQ))
            state = _state(astat=astat)
            for xop, dreg in enumerate(DIVIDE_X_DREG):
                divisor = read_dreg(state.primary, dreg)
                assert isinstance(divisor, ExactWord)
                partial = state.primary.af
                ay0 = state.primary.ay[0]
                assert isinstance(partial, ExactWord)
                assert isinstance(ay0, ExactWord)
                result = apply_divide_quotient_cycle(
                    state,
                    DivideQuotientInputs(execute=True, opcode=_opcode(xop)),
                )
                raw = (
                    partial.value + divisor.value
                    if old_aq
                    else partial.value - divisor.value
                ) & 0xFFFF
                new_aq = bool(((divisor.value ^ raw) >> 15) & 1)
                self.assertEqual(result.alu_result, ExactWord(16, raw))
                self.assertEqual(result.new_aq, new_aq)
                self.assertEqual(result.quotient_bit, not new_aq)
                self.assertEqual(
                    result.state.primary.af,
                    ExactWord(16, ((raw << 1) & 0xFFFF) | (ay0.value >> 15)),
                )
                self.assertEqual(
                    result.state.primary.ay[0],
                    ExactWord(16, ((ay0.value << 1) & 0xFFFF) | int(not new_aq)),
                )
                before = state.status.astat.to_word().value
                after = result.state.status.astat.to_word().value
                self.assertEqual(after & 0xDF, before & 0xDF)

    def test_selected_alternate_bank_only_is_updated(self) -> None:
        state = _state(mstat=1)
        result = apply_divide_quotient_cycle(
            state,
            DivideQuotientInputs(execute=True, opcode=_opcode(7)),
        )
        self.assertEqual(result.state.primary, state.primary)
        self.assertNotEqual(result.state.alternate, state.alternate)

    def test_unknown_source_invalidates_only_documented_destinations(self) -> None:
        bits = list(ASTATState.from_word(ExactWord(8, 0xD5)).bits)
        bits[int(ASTATBit.AQ)] = UNKNOWN
        state = replace(
            _state(),
            status=replace(_state().status, astat=ASTATState(tuple(bits))),
        )
        result = apply_divide_quotient_cycle(
            state,
            DivideQuotientInputs(execute=True, opcode=_opcode(0)),
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
                    state.status.astat.bit(bit),
                )

    def test_invalid_setup_conflict_and_reset_are_fail_closed(self) -> None:
        state = _state()
        invalid = apply_divide_quotient_cycle(
            state,
            DivideQuotientInputs(execute=True, opcode=0x060800),
        )
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_divide_quotient_cycle(
            state,
            DivideQuotientInputs(
                execute=True,
                opcode=_opcode(0),
                dreg_write=DREGWrite(DREG.AY0, ExactWord(16, 0)),
            ),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        reset = apply_divide_quotient_cycle(
            state,
            DivideQuotientInputs(reset=True, execute=True, opcode=_opcode(0)),
        )
        self.assertEqual(reset.state, DivideQuotientState())
        self.assertIs(reset.state.primary.af, UNKNOWN)
        self.assertIs(reset.state.status.astat.bit(ASTATBit.AQ), UNKNOWN)

    def test_signed_divs_then_fifteen_divq_sequence(self) -> None:
        cases = (
            (0x2000, 0x0000, 0x4000, 0x4000),
            (0xE000, 0x0000, 0x4000, 0xC000),
            (0x1000, 0x0000, 0x4000, 0x2000),
        )
        for upper, lower, divisor, expected_quotient in cases:
            bank = replace(
                _bank(ay0=lower, ay1=upper),
                ax=(ExactWord(16, divisor), ExactWord(16, 0)),
            )
            sign_state = DivideSignState(
                primary=bank,
                alternate=_bank(),
                status=StatusRegisters(
                    astat=ASTATState.from_word(ExactWord(8, 0x95)),
                ),
            )
            initialized = apply_divide_sign_cycle(
                sign_state,
                DivideSignInputs(execute=True, opcode=0x060800),
            )
            quotient_state = DivideQuotientState(
                initialized.state.primary,
                initialized.state.alternate,
                initialized.state.status,
            )
            for _ in range(15):
                quotient_state = apply_divide_quotient_cycle(
                    quotient_state,
                    DivideQuotientInputs(execute=True, opcode=_opcode(0)),
                ).state
            self.assertEqual(
                quotient_state.primary.ay[0],
                ExactWord(16, expected_quotient),
            )
            self.assertEqual(
                quotient_state.status.astat.to_word().value & 0xDF,
                0x95 & 0xDF,
            )


if __name__ == "__main__":
    unittest.main()
