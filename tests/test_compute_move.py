from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    COMPUTE_MOVE_CLASS_MASK,
    COMPUTE_MOVE_CLASS_VALUE,
    ComputeMoveState,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_compute_move_cycle,
    compute_move_unsupported_reason,
    decode_compute_move,
    is_compute_move_class,
    read_dreg,
)


def _opcode(
    z: int,
    amf: int,
    yop: int,
    xop: int,
    destination: DREG,
    source: DREG,
) -> int:
    return (
        0x280000
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (int(destination) << 4)
        | int(source)
    )


def _setup_dreg(state: ComputeMoveState, destination: DREG, value: int) -> ComputeMoveState:
    return apply_compute_move_cycle(
        state,
        setup_dreg=DREGWrite(destination, ExactWord(16, value)),
    ).state


def _setup_astat(state: ComputeMoveState, value: int) -> ComputeMoveState:
    return apply_compute_move_cycle(state, setup_astat=ExactWord(8, value)).state


class ComputeMoveTests(unittest.TestCase):
    def test_complete_type_8_partition_and_fields(self) -> None:
        supported = 0
        amf_zero = 0
        collision = 0
        for payload in range(1 << 19):
            opcode = 0x280000 | payload
            self.assertTrue(is_compute_move_class(opcode))
            action = decode_compute_move(opcode)
            reason = compute_move_unsupported_reason(opcode)
            if action is not None:
                self.assertIsNone(reason)
                self.assertEqual(action.z, (payload >> 18) & 1)
                self.assertEqual(action.amf, (payload >> 13) & 0x1F)
                self.assertEqual(action.yop, (payload >> 11) & 3)
                self.assertEqual(action.xop, (payload >> 8) & 7)
                self.assertEqual(action.move_destination, DREG((payload >> 4) & 0xF))
                self.assertEqual(action.move_source, DREG(payload & 0xF))
                supported += 1
            elif reason == "UNVERIFIED_AMF_ZERO":
                amf_zero += 1
            elif reason == "UNSUPPORTED_DESTINATION_COLLISION":
                collision += 1
            else:
                self.fail(f"unclassified Type 8 payload 0x{payload:05x}")
        self.assertEqual(COMPUTE_MOVE_CLASS_MASK, 0xF80000)
        self.assertEqual(COMPUTE_MOVE_CLASS_VALUE, 0x280000)
        self.assertEqual(supported, 476_672)
        self.assertEqual(amf_zero, 16_384)
        self.assertEqual(collision, 31_232)

    def test_nonclass_and_out_of_range_words_fail_closed(self) -> None:
        for opcode in (0, 0x27FFFF, 0x300000, 0xFFFFFF):
            self.assertFalse(is_compute_move_class(opcode))
            self.assertIsNone(decode_compute_move(opcode))
            self.assertIsNone(compute_move_unsupported_reason(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_compute_move(opcode)

    def test_original_alu_example_uses_cycle_start_operand(self) -> None:
        state = _setup_astat(ComputeMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.AX0, 3)
        state = _setup_dreg(state, DREG.AY0, 4)
        state = _setup_dreg(state, DREG.MR2, 0xFFFE)
        result = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, DREG.AX0, DREG.MR2),
        )
        self.assertTrue(result.boundary_valid)
        self.assertTrue(result.alu_write)
        self.assertTrue(result.alu_status_write)
        self.assertEqual(read_dreg(result.state.primary, DREG.AR), ExactWord(16, 7))
        self.assertEqual(read_dreg(result.state.primary, DREG.AX0), ExactWord(16, 0xFFFE))
        self.assertFalse(result.state.status.astat.bit(ASTATBit.AZ))

    def test_move_reads_old_alu_result_destination(self) -> None:
        state = _setup_astat(ComputeMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.AR, 0x1234)
        state = _setup_dreg(state, DREG.AX0, 5)
        state = _setup_dreg(state, DREG.AY0, 6)
        result = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, DREG.AX1, DREG.AR),
        )
        self.assertEqual(read_dreg(result.state.primary, DREG.AX1), ExactWord(16, 0x1234))
        self.assertEqual(read_dreg(result.state.primary, DREG.AR), ExactWord(16, 11))

    def test_mac_accumulate_and_move_commit_together(self) -> None:
        state = _setup_astat(ComputeMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.MX0, 0x4000)
        state = _setup_dreg(state, DREG.MY0, 0x4000)
        state = _setup_dreg(state, DREG.MR0, 0)
        state = _setup_dreg(state, DREG.MR1, 1)
        state = _setup_dreg(state, DREG.MR2, 0)
        state = _setup_dreg(state, DREG.SR1, 0xCAFE)
        result = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x08, 0, 0, DREG.AY0, DREG.SR1),
        )
        self.assertTrue(result.mac_write)
        self.assertTrue(result.mac_status_write)
        self.assertEqual(read_dreg(result.state.primary, DREG.AY0), ExactWord(16, 0xCAFE))
        self.assertEqual(read_dreg(result.state.primary, DREG.MR0), ExactWord(16, 0))
        self.assertEqual(read_dreg(result.state.primary, DREG.MR1), ExactWord(16, 0x2001))
        self.assertFalse(result.state.status.astat.bit(ASTATBit.MV))

    def test_feedback_destinations_do_not_collide_with_dregs(self) -> None:
        state = _setup_astat(ComputeMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.AX0, 1)
        state = _setup_dreg(state, DREG.AY0, 2)
        state = _setup_dreg(state, DREG.MR0, 0x7777)
        alu = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(1, 0x13, 0, 0, DREG.AR, DREG.MR0),
        )
        self.assertEqual(alu.state.primary.af, ExactWord(16, 3))
        self.assertEqual(read_dreg(alu.state.primary, DREG.AR), ExactWord(16, 0x7777))

        state = _setup_dreg(alu.state, DREG.MX0, 0x4000)
        state = _setup_dreg(state, DREG.MY0, 0x4000)
        mac = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(1, 0x04, 0, 0, DREG.MR0, DREG.AR),
        )
        self.assertEqual(mac.state.primary.mf, ExactWord(16, 0x2000))
        self.assertEqual(read_dreg(mac.state.primary, DREG.MR0), ExactWord(16, 0x7777))

    def test_result_destination_collisions_never_execute(self) -> None:
        cases = (
            _opcode(0, 0x10, 0, 0, DREG.AR, DREG.AX0),
            _opcode(0, 0x01, 0, 0, DREG.MR0, DREG.AX0),
            _opcode(0, 0x0F, 0, 0, DREG.MR1, DREG.AX0),
            _opcode(0, 0x08, 0, 0, DREG.MR2, DREG.AX0),
        )
        for opcode in cases:
            self.assertIsNone(decode_compute_move(opcode))
            self.assertEqual(
                compute_move_unsupported_reason(opcode),
                "UNSUPPORTED_DESTINATION_COLLISION",
            )

    def test_selected_bank_updates_and_reset_preserves_banks(self) -> None:
        state = _setup_astat(ComputeMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.AX0, 1)
        state = _setup_dreg(state, DREG.AY0, 2)
        state = apply_compute_move_cycle(state, setup_mstat=ExactWord(4, 1)).state
        state = _setup_dreg(state, DREG.AX0, 10)
        state = _setup_dreg(state, DREG.AY0, 20)
        result = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, DREG.MX0, DREG.AX0),
        )
        self.assertIs(result.state.primary.ar, UNKNOWN)
        self.assertEqual(result.state.alternate.ar, ExactWord(16, 30))
        self.assertEqual(read_dreg(result.state.alternate, DREG.MX0), ExactWord(16, 10))
        reset = apply_compute_move_cycle(result.state, reset=True)
        self.assertEqual(reset.state.alternate.ar, ExactWord(16, 30))
        self.assertEqual(reset.state.status.mstat, ExactWord(4, 0))

    def test_unknown_sources_invalidate_only_affected_destinations(self) -> None:
        state = _setup_astat(ComputeMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.AX0, 1)
        state = _setup_dreg(state, DREG.AY0, 2)
        known_compute = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, DREG.MX0, DREG.SR0),
        )
        self.assertEqual(known_compute.state.primary.ar, ExactWord(16, 3))
        self.assertIs(known_compute.state.primary.mx[0], UNKNOWN)

        state = _setup_astat(ComputeMoveState.reset(), 0)
        state = _setup_dreg(state, DREG.SR0, 0xABCD)
        unknown_compute = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, DREG.MX0, DREG.SR0),
        )
        self.assertEqual(unknown_compute.state.primary.mx[0], ExactWord(16, 0xABCD))
        self.assertIs(unknown_compute.state.primary.ar, UNKNOWN)
        self.assertIs(unknown_compute.state.status.astat.bit(ASTATBit.AZ), UNKNOWN)

    def test_invalid_and_setup_conflict_are_atomic(self) -> None:
        state = _setup_astat(ComputeMoveState.reset(), 0x55)
        for opcode in (
            _opcode(0, 0, 0, 0, DREG.AX0, DREG.AX1),
            _opcode(0, 0x13, 0, 0, DREG.AR, DREG.AX1),
            0,
        ):
            result = apply_compute_move_cycle(state, execute=True, opcode=opcode)
            self.assertTrue(result.invalid_opcode)
            self.assertEqual(result.state, state)
        conflict = apply_compute_move_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, DREG.AX0, DREG.AX1),
            setup_dreg=DREGWrite(DREG.MR0, ExactWord(16, 1)),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)


if __name__ == "__main__":
    unittest.main()
