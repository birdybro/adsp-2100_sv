from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    CONDITIONAL_COMPUTE_CLASS_MASK,
    CONDITIONAL_COMPUTE_CLASS_VALUE,
    ConditionalComputeState,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_conditional_compute_cycle,
    decode_conditional_compute,
    is_conditional_compute_class,
    read_dreg,
)


def _opcode(z: int, amf: int, yop: int, xop: int, condition: int) -> int:
    return (
        0x200000
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | condition
    )


def _setup_dreg(
    state: ConditionalComputeState,
    destination: DREG,
    value: int,
) -> ConditionalComputeState:
    return apply_conditional_compute_cycle(
        state,
        setup_dreg=DREGWrite(destination, ExactWord(16, value)),
    ).state


def _setup_astat(state: ConditionalComputeState, value: int) -> ConditionalComputeState:
    return apply_conditional_compute_cycle(
        state,
        setup_astat=ExactWord(8, value),
    ).state


class ConditionalComputeTests(unittest.TestCase):
    def test_complete_type_9_class_and_fields(self) -> None:
        count = 0
        nop_count = 0
        for z in range(2):
            for amf in range(32):
                for yop in range(4):
                    for xop in range(8):
                        for condition in range(16):
                            opcode = _opcode(z, amf, yop, xop, condition)
                            action = decode_conditional_compute(opcode)
                            self.assertIsNotNone(action)
                            assert action is not None
                            self.assertEqual(action.z, z)
                            self.assertEqual(action.amf, amf)
                            self.assertEqual(action.yop, yop)
                            self.assertEqual(action.xop, xop)
                            self.assertEqual(action.condition, condition)
                            nop_count += action.is_nop
                            count += 1
        self.assertEqual(CONDITIONAL_COMPUTE_CLASS_MASK, 0xF800F0)
        self.assertEqual(CONDITIONAL_COMPUTE_CLASS_VALUE, 0x200000)
        self.assertEqual(count, 32_768)
        self.assertEqual(nop_count, 1_024)

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x1FFFFF, 0x200010, 0x27FFFF, 0x280000):
            self.assertFalse(is_conditional_compute_class(opcode))
            self.assertIsNone(decode_conditional_compute(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_conditional_compute(opcode)

    def test_original_alu_example_reads_prior_carry(self) -> None:
        state = _setup_astat(ConditionalComputeState.reset(), 0x08)
        state = _setup_dreg(state, DREG.AX0, 3)
        state = _setup_dreg(state, DREG.AY0, 4)
        result = apply_conditional_compute_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x12, 0, 0, 8),
        )
        self.assertTrue(result.condition_true)
        self.assertTrue(result.alu_write)
        self.assertEqual(read_dreg(result.state.primary, DREG.AR), ExactWord(16, 8))

    def test_original_mac_example_false_is_one_cycle_nop(self) -> None:
        state = _setup_astat(ConditionalComputeState.reset(), 1 << int(ASTATBit.MV))
        state = _setup_dreg(state, DREG.MX0, 0x4000)
        state = _setup_dreg(state, DREG.MY0, 0x4000)
        state = _setup_dreg(state, DREG.MR0, 0x1111)
        state = _setup_dreg(state, DREG.MR1, 0x2222)
        state = _setup_dreg(state, DREG.MR2, 0)
        result = apply_conditional_compute_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x0B, 0, 0, 13),
        )
        self.assertTrue(result.boundary_valid)
        self.assertTrue(result.condition_known)
        self.assertFalse(result.condition_true)
        self.assertFalse(result.mac_write)
        self.assertEqual(result.state, state)

    def test_mac_true_updates_result_and_mv_atomically(self) -> None:
        state = _setup_astat(ConditionalComputeState.reset(), 0)
        state = _setup_dreg(state, DREG.MX0, 0x4000)
        state = _setup_dreg(state, DREG.MY0, 0x4000)
        state = _setup_dreg(state, DREG.MR0, 0)
        state = _setup_dreg(state, DREG.MR1, 1)
        state = _setup_dreg(state, DREG.MR2, 0)
        result = apply_conditional_compute_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x08, 0, 0, 15),
        )
        self.assertTrue(result.mac_write)
        self.assertTrue(result.mac_status_write)
        self.assertEqual(read_dreg(result.state.primary, DREG.MR1), ExactWord(16, 0x2001))
        self.assertFalse(result.state.status.astat.bit(ASTATBit.MV))

    def test_feedback_destination_and_selected_bank(self) -> None:
        state = _setup_astat(ConditionalComputeState.reset(), 0)
        state = _setup_dreg(state, DREG.AX0, 1)
        state = _setup_dreg(state, DREG.AY0, 2)
        state = apply_conditional_compute_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        state = _setup_dreg(state, DREG.AX0, 10)
        state = _setup_dreg(state, DREG.AY0, 20)
        result = apply_conditional_compute_cycle(
            state,
            execute=True,
            opcode=_opcode(1, 0x13, 0, 0, 15),
        )
        self.assertIs(result.state.primary.af, UNKNOWN)
        self.assertEqual(result.state.alternate.af, ExactWord(16, 30))
        self.assertIs(result.state.alternate.ar, UNKNOWN)

    def test_amf_zero_is_documented_no_operation_alias(self) -> None:
        state = _setup_astat(ConditionalComputeState.reset(), 0x5D)
        for z in range(2):
            for yop in range(4):
                for xop in range(8):
                    for condition in range(16):
                        result = apply_conditional_compute_cycle(
                            state,
                            execute=True,
                            opcode=_opcode(z, 0, yop, xop, condition),
                        )
                        self.assertTrue(result.boundary_valid)
                        self.assertTrue(result.nop_action)
                        self.assertTrue(result.result_known)
                        self.assertEqual(result.state, state)

    def test_unknown_predicate_invalidates_only_possible_writes(self) -> None:
        state = ConditionalComputeState.reset()
        state = _setup_dreg(state, DREG.AX0, 1)
        state = _setup_dreg(state, DREG.AY0, 2)
        result = apply_conditional_compute_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, 0),
        )
        self.assertTrue(result.boundary_valid)
        self.assertFalse(result.condition_known)
        self.assertIs(result.state.primary.ar, UNKNOWN)
        self.assertIs(result.state.status.astat.bit(ASTATBit.AZ), UNKNOWN)
        self.assertEqual(result.state.status.mstat, state.status.mstat)

    def test_false_condition_does_not_require_known_operands(self) -> None:
        state = _setup_astat(ConditionalComputeState.reset(), 0)
        result = apply_conditional_compute_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, 0),
        )
        self.assertFalse(result.condition_true)
        self.assertTrue(result.result_known)
        self.assertEqual(result.state, state)

    def test_reset_invalid_and_setup_conflict_are_atomic(self) -> None:
        state = _setup_astat(ConditionalComputeState.reset(), 0x55)
        invalid = apply_conditional_compute_cycle(state, execute=True, opcode=0)
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_conditional_compute_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0x13, 0, 0, 15),
            setup_dreg=DREGWrite(DREG.MR0, ExactWord(16, 1)),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        reset = apply_conditional_compute_cycle(state, reset=True)
        self.assertEqual(reset.state.status.mstat, ExactWord(4, 0))
        self.assertEqual(reset.state.primary, state.primary)


if __name__ == "__main__":
    unittest.main()
