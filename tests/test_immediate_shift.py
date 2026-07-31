from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DREG,
    DREGWrite,
    ExactWord,
    ImmediateShiftState,
    SHIFTER_XOP_DREG,
    UNKNOWN,
    apply_immediate_shift_cycle,
    decode_immediate_shift,
    is_immediate_shift_class,
    read_dreg,
)


def _opcode(sf: int, xop: int, exponent: int) -> int:
    return 0x0F0000 | (sf << 11) | (xop << 8) | (exponent & 0xFF)


def _setup(
    state: ImmediateShiftState,
    destination: DREG,
    value: int,
) -> ImmediateShiftState:
    return apply_immediate_shift_cycle(
        state,
        setup_dreg=DREGWrite(destination, ExactWord(16, value)),
    ).state


def _sr(state: ImmediateShiftState, alternate: bool = False) -> int | None:
    bank = state.alternate if alternate else state.primary
    if not all(isinstance(value, ExactWord) for value in bank.sr):
        return None
    sr0, sr1 = bank.sr
    assert isinstance(sr0, ExactWord)
    assert isinstance(sr1, ExactWord)
    return (sr1.value << 16) | sr0.value


class ImmediateShiftTests(unittest.TestCase):
    def test_complete_type_15_partition_and_fields(self) -> None:
        legal = 0
        unsupported = 0
        for payload in range(1 << 15):
            opcode = 0x0F0000 | payload
            self.assertTrue(is_immediate_shift_class(opcode))
            action = decode_immediate_shift(opcode)
            sf = (opcode >> 11) & 0xF
            xop = (opcode >> 8) & 0x7
            if sf <= 7 and xop in SHIFTER_XOP_DREG:
                self.assertIsNotNone(action)
                assert action is not None
                self.assertEqual(action.sf, sf)
                self.assertEqual(action.xop, xop)
                self.assertEqual(action.source, SHIFTER_XOP_DREG[xop])
                self.assertEqual(action.exponent, ExactWord(8, opcode & 0xFF))
                legal += 1
            else:
                self.assertIsNone(action)
                unsupported += 1
        self.assertEqual(legal, 14_336)
        self.assertEqual(unsupported, 18_432)

    def test_non_type_15_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x0EFFFF, 0x0F8000, 0xFFFFFF):
            self.assertFalse(is_immediate_shift_class(opcode))
            self.assertIsNone(decode_immediate_shift(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_immediate_shift(opcode)

    def test_original_manual_logical_and_arithmetic_examples(self) -> None:
        state = _setup(ImmediateShiftState.reset(), DREG.SI, 0xB6A3)
        logical = apply_immediate_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0, -5),
        )
        self.assertTrue(logical.boundary_valid)
        self.assertEqual(_sr(logical.state), 0x05B51800)
        arithmetic = apply_immediate_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(4, 0, -5),
        )
        self.assertEqual(_sr(arithmetic.state), 0xFDB51800)

    def test_or_mode_and_immediate_exponent_leave_se_unchanged(self) -> None:
        state = ImmediateShiftState.reset()
        state = _setup(state, DREG.SI, 0x1234)
        state = _setup(state, DREG.SE, 0x005A)
        state = _setup(state, DREG.SR0, 0x00F0)
        state = _setup(state, DREG.SR1, 0x8000)
        result = apply_immediate_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(1, 0, 0),
        )
        self.assertEqual(_sr(result.state), 0x923400F0)
        self.assertEqual(
            read_dreg(result.state.primary, DREG.SE),
            ExactWord(16, 0x005A),
        )

    def test_cycle_start_bank_selection_and_inactive_bank_preservation(self) -> None:
        state = ImmediateShiftState.reset()
        state = _setup(state, DREG.SI, 0x1111)
        state = _setup(state, DREG.SR0, 0xAAAA)
        state = _setup(state, DREG.SR1, 0xBBBB)
        state = apply_immediate_shift_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        state = _setup(state, DREG.SI, 0x2222)
        state = _setup(state, DREG.SR0, 0xCCCC)
        state = _setup(state, DREG.SR1, 0xDDDD)
        result = apply_immediate_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(2, 0, 0),
        )
        self.assertEqual(_sr(result.state), 0xBBBBAAAA)
        self.assertEqual(_sr(result.state, alternate=True), 0x00002222)

    def test_unknown_source_invalidates_sr_without_fabrication(self) -> None:
        result = apply_immediate_shift_cycle(
            ImmediateShiftState.reset(),
            execute=True,
            opcode=_opcode(0, 0, 0),
        )
        self.assertTrue(result.boundary_valid)
        self.assertFalse(result.result_known)
        self.assertIs(result.state.primary.sr[0], UNKNOWN)
        self.assertIs(result.state.primary.sr[1], UNKNOWN)

    def test_reset_selects_primary_without_erasing_banks(self) -> None:
        state = _setup(ImmediateShiftState.reset(), DREG.SI, 0x1111)
        state = apply_immediate_shift_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        state = _setup(state, DREG.SI, 0x2222)
        result = apply_immediate_shift_cycle(state, reset=True)
        self.assertEqual(result.state.mstat, ExactWord(4, 0))
        self.assertEqual(
            read_dreg(result.state.primary, DREG.SI),
            ExactWord(16, 0x1111),
        )
        self.assertEqual(
            read_dreg(result.state.alternate, DREG.SI),
            ExactWord(16, 0x2222),
        )

    def test_unsupported_invalid_and_conflicting_cycles_preserve_state(self) -> None:
        state = _setup(ImmediateShiftState.reset(), DREG.SI, 0x1234)
        unsupported = apply_immediate_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(8, 0, 0),
        )
        self.assertTrue(unsupported.unsupported_subencoding)
        self.assertTrue(unsupported.invalid_opcode)
        self.assertEqual(unsupported.state, state)
        unavailable_xop = apply_immediate_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 1, 0),
        )
        self.assertTrue(unavailable_xop.unsupported_subencoding)
        self.assertEqual(unavailable_xop.state, state)
        conflict = apply_immediate_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0, 0),
            setup_dreg=DREGWrite(DREG.AX0, ExactWord(16, 0x5678)),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)


if __name__ == "__main__":
    unittest.main()
