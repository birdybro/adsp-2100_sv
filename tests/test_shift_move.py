from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    DREG,
    DREGWrite,
    ExactWord,
    SHIFT_MOVE_CLASS_MASK,
    SHIFT_MOVE_CLASS_VALUE,
    ShiftMoveState,
    UNKNOWN,
    apply_shift_move_cycle,
    decode_shift_move,
    is_shift_move_class,
    read_dreg,
    shift_move_unsupported_reason,
)


LEGAL_XOPS = (0, 2, 3, 4, 5, 6, 7)


def _opcode(sf: int, xop: int, destination: DREG, source: DREG) -> int:
    return (
        0x100000
        | (sf << 11)
        | (xop << 8)
        | (int(destination) << 4)
        | int(source)
    )


def _setup_dreg(
    state: ShiftMoveState,
    destination: DREG,
    value: int,
) -> ShiftMoveState:
    return apply_shift_move_cycle(
        state,
        setup_dreg=DREGWrite(destination, ExactWord(16, value)),
    ).state


def _setup_astat(state: ShiftMoveState, value: int) -> ShiftMoveState:
    return apply_shift_move_cycle(
        state,
        setup_astat=ExactWord(8, value),
    ).state


def _sr(state: ShiftMoveState, alternate: bool = False) -> int | None:
    bank = state.alternate if alternate else state.primary
    if not all(isinstance(value, ExactWord) for value in bank.sr):
        return None
    sr0, sr1 = bank.sr
    assert isinstance(sr0, ExactWord)
    assert isinstance(sr1, ExactWord)
    return (sr1.value << 16) | sr0.value


class ShiftMoveTests(unittest.TestCase):
    def test_complete_type_14_partition_and_fields(self) -> None:
        supported = 0
        unused_x = 0
        unavailable_xop = 0
        collision = 0
        for payload in range(1 << 16):
            opcode = 0x100000 | payload
            self.assertTrue(is_shift_move_class(opcode))
            action = decode_shift_move(opcode)
            reason = shift_move_unsupported_reason(opcode)
            if action is not None:
                self.assertIsNone(reason)
                self.assertEqual(action.sf, (payload >> 11) & 0xF)
                self.assertEqual(action.xop, (payload >> 8) & 0x7)
                self.assertEqual(action.move_destination, DREG((payload >> 4) & 0xF))
                self.assertEqual(action.move_source, DREG(payload & 0xF))
                supported += 1
            elif reason == "UNVERIFIED_UNUSED_X":
                unused_x += 1
            elif reason == "UNAVAILABLE_SHIFTER_XOP":
                unavailable_xop += 1
            elif reason == "UNSUPPORTED_DESTINATION_COLLISION":
                collision += 1
            else:
                self.fail(f"unclassified Type 14 payload 0x{payload:04x}")
        self.assertEqual(SHIFT_MOVE_CLASS_MASK, 0xFF0000)
        self.assertEqual(SHIFT_MOVE_CLASS_VALUE, 0x100000)
        self.assertEqual(supported, 25_648)
        self.assertEqual(unused_x, 32_768)
        self.assertEqual(unavailable_xop, 4_096)
        self.assertEqual(collision, 3_024)

    def test_nonclass_and_out_of_range_words_fail_closed(self) -> None:
        for opcode in (0, 0x0FFFFF, 0x110000, 0xFFFFFF):
            self.assertFalse(is_shift_move_class(opcode))
            self.assertIsNone(decode_shift_move(opcode))
            self.assertIsNone(shift_move_unsupported_reason(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_shift_move(opcode)

    def test_parallel_move_and_shift_read_cycle_start_values(self) -> None:
        state = _setup_astat(ShiftMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.SI, 0x1234)
        state = _setup_dreg(state, DREG.SE, 0)
        state = _setup_dreg(state, DREG.MR0, 0xABCD)
        result = apply_shift_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0, DREG.SI, DREG.MR0),
        )
        self.assertTrue(result.boundary_valid)
        self.assertTrue(result.move_result_known)
        self.assertTrue(result.shifter_result_known)
        self.assertTrue(result.move_write)
        self.assertTrue(result.sr_write)
        self.assertEqual(read_dreg(result.state.primary, DREG.SI), ExactWord(16, 0xABCD))
        self.assertEqual(_sr(result.state), 0x12340000)

    def test_move_reads_old_computation_destination(self) -> None:
        state = _setup_astat(ShiftMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.SI, 0x1111)
        state = _setup_dreg(state, DREG.SE, 0)
        state = _setup_dreg(state, DREG.SR0, 0x5678)
        state = _setup_dreg(state, DREG.SR1, 0x1234)
        result = apply_shift_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0, DREG.AX0, DREG.SR0),
        )
        self.assertEqual(read_dreg(result.state.primary, DREG.AX0), ExactWord(16, 0x5678))
        self.assertEqual(_sr(result.state), 0x11110000)

    def test_all_function_destinations_and_status_updates(self) -> None:
        state = _setup_astat(ShiftMoveState.reset(), 1 << ASTATBit.AV)
        state = _setup_dreg(state, DREG.SI, 0x8000)
        state = _setup_dreg(state, DREG.SE, 0xFFF1)
        state = _setup_dreg(state, DREG.MR0, 0x1234)
        hix = apply_shift_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0xD, 0, DREG.AX0, DREG.MR0),
        )
        self.assertEqual(read_dreg(hix.state.primary, DREG.AX0), ExactWord(16, 0x1234))
        self.assertEqual(read_dreg(hix.state.primary, DREG.SE), ExactWord(16, 1))
        self.assertFalse(hix.state.status.astat.bit(ASTATBit.SS))
        self.assertTrue(hix.se_write)
        self.assertTrue(hix.ss_write)

        exp_lo_state = _setup_dreg(hix.state, DREG.SE, 0xFFF1)
        exp_lo_state = _setup_dreg(exp_lo_state, DREG.SI, 0)
        exp_lo = apply_shift_move_cycle(
            exp_lo_state,
            execute=True,
            opcode=_opcode(0xE, 0, DREG.AX1, DREG.MR0),
        )
        self.assertEqual(read_dreg(exp_lo.state.primary, DREG.SE), ExactWord(16, 0xFFE1))
        self.assertTrue(exp_lo.se_write)
        self.assertFalse(exp_lo.ss_write)

        sb_state = apply_shift_move_cycle(
            exp_lo.state,
            setup_sb=ExactWord(5, 0x10),
        ).state
        sb_state = _setup_dreg(sb_state, DREG.SI, 0x4000)
        expadj = apply_shift_move_cycle(
            sb_state,
            execute=True,
            opcode=_opcode(0xF, 0, DREG.AY0, DREG.MR0),
        )
        self.assertEqual(expadj.state.primary.sb, ExactWord(5, 0))
        self.assertTrue(expadj.sb_write)

    def test_same_destination_collisions_are_never_executed(self) -> None:
        for sf, destination in (
            (0, DREG.SR0),
            (0xB, DREG.SR1),
            (0xC, DREG.SE),
            (0xD, DREG.SE),
            (0xE, DREG.SE),
        ):
            opcode = _opcode(sf, 0, destination, DREG.AX0)
            self.assertIsNone(decode_shift_move(opcode))
            self.assertEqual(
                shift_move_unsupported_reason(opcode),
                "UNSUPPORTED_DESTINATION_COLLISION",
            )

    def test_selected_bank_updates_and_inactive_bank_preservation(self) -> None:
        state = _setup_astat(ShiftMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.SI, 0x1111)
        state = _setup_dreg(state, DREG.SE, 0)
        state = _setup_dreg(state, DREG.MR0, 0xAAAA)
        state = apply_shift_move_cycle(state, setup_mstat=ExactWord(4, 1)).state
        state = _setup_dreg(state, DREG.SI, 0x2222)
        state = _setup_dreg(state, DREG.SE, 0)
        state = _setup_dreg(state, DREG.MR0, 0xBBBB)
        result = apply_shift_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0, DREG.AX0, DREG.MR0),
        )
        self.assertIs(result.state.primary.ax[0], UNKNOWN)
        self.assertEqual(read_dreg(result.state.alternate, DREG.AX0), ExactWord(16, 0xBBBB))
        self.assertEqual(_sr(result.state, alternate=True), 0x22220000)

    def test_unknown_parallel_sources_invalidate_only_their_destinations(self) -> None:
        state = _setup_astat(ShiftMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.SI, 0x1234)
        state = _setup_dreg(state, DREG.SE, 0)
        known_shift = apply_shift_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0, DREG.AX0, DREG.MR0),
        )
        self.assertIs(known_shift.state.primary.ax[0], UNKNOWN)
        self.assertEqual(_sr(known_shift.state), 0x12340000)

        unknown_shift_state = _setup_dreg(ShiftMoveState.reset(), DREG.MR0, 0xCAFE)
        unknown_shift = apply_shift_move_cycle(
            unknown_shift_state,
            execute=True,
            opcode=_opcode(0, 0, DREG.AX0, DREG.MR0),
        )
        self.assertEqual(read_dreg(unknown_shift.state.primary, DREG.AX0), ExactWord(16, 0xCAFE))
        self.assertIsNone(_sr(unknown_shift.state))

    def test_reset_preserves_banks_and_invalid_words_are_atomic(self) -> None:
        state = _setup_astat(ShiftMoveState.reset(), 0xFF)
        state = _setup_dreg(state, DREG.SI, 0x1234)
        reset = apply_shift_move_cycle(state, reset=True)
        self.assertEqual(read_dreg(reset.state.primary, DREG.SI), ExactWord(16, 0x1234))
        self.assertFalse(reset.state.status.astat.is_fully_known)
        self.assertEqual(reset.state.status.mstat, ExactWord(4, 0))

        for opcode in (
            0x108000,
            _opcode(0, 1, DREG.AX0, DREG.AX1),
            _opcode(0, 0, DREG.SR0, DREG.AX1),
            0,
        ):
            invalid = apply_shift_move_cycle(
                state,
                execute=True,
                opcode=opcode,
            )
            self.assertTrue(invalid.invalid_opcode)
            self.assertEqual(invalid.state, state)

    def test_setup_and_execute_collisions_fail_atomically(self) -> None:
        state = _setup_astat(ShiftMoveState.reset(), 0)
        conflict = apply_shift_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0, DREG.AX0, DREG.AX1),
            setup_dreg=DREGWrite(DREG.MR0, ExactWord(16, 1)),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)


if __name__ == "__main__":
    unittest.main()
