from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    CONDITIONAL_TRAP_CLASS_MASK,
    CONDITIONAL_TRAP_CLASS_VALUE,
    ConditionalTrapState,
    ExactWord,
    LogicalPhase,
    apply_conditional_trap_cycle,
    decode_conditional_trap,
    is_conditional_trap_class,
)


def _opcode(condition: int) -> int:
    return 0x080000 | condition


def _accept(
    state: ConditionalTrapState,
    condition: int,
) -> tuple[ConditionalTrapState, object]:
    result = apply_conditional_trap_cycle(
        state,
        phase=LogicalPhase.STATE_1,
        phase_advance=True,
        execute=True,
        opcode=_opcode(condition),
    )
    return result.state, result


def _commit(state: ConditionalTrapState, *, phase_advance: bool = True):
    return apply_conditional_trap_cycle(
        state,
        phase=LogicalPhase.STATE_7,
        phase_advance=phase_advance,
    )


class ConditionalTrapTests(unittest.TestCase):
    def test_complete_type_22_partition_and_fields(self) -> None:
        for condition in range(16):
            action = decode_conditional_trap(_opcode(condition))
            self.assertIsNotNone(action)
            assert action is not None
            self.assertEqual(action.condition, condition)
        self.assertEqual(CONDITIONAL_TRAP_CLASS_MASK, 0xFFFFF0)
        self.assertEqual(CONDITIONAL_TRAP_CLASS_VALUE, 0x080000)

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x080010, 0x090000, 0x0A0000):
            self.assertFalse(is_conditional_trap_class(opcode))
            self.assertIsNone(decode_conditional_trap(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_conditional_trap(opcode)

    def test_reset_clears_trap_halt_and_pending_state(self) -> None:
        state = ConditionalTrapState(
            pc=0x1234,
            pending=True,
            pending_taken=True,
            trap_asserted=True,
            halted=True,
        )
        result = apply_conditional_trap_cycle(state, reset=True)
        self.assertEqual(result.state, ConditionalTrapState())
        self.assertEqual(result.state.pc, 4)
        self.assertFalse(result.phase_hold)

    def test_taken_trap_asserts_only_on_state_seven_to_eight(self) -> None:
        state = apply_conditional_trap_cycle(
            ConditionalTrapState(), setup_pc=0x1234
        ).state
        state, accepted = _accept(state, 15)
        self.assertTrue(accepted.instruction_accepted)
        self.assertTrue(accepted.condition_true)
        self.assertTrue(state.pending)
        self.assertFalse(state.trap_asserted)
        for phase in range(LogicalPhase.STATE_2, LogicalPhase.STATE_7):
            intermediate = apply_conditional_trap_cycle(
                state, phase=phase, phase_advance=True
            )
            self.assertEqual(intermediate.state, state)
            self.assertFalse(intermediate.trap_event)
        committed = _commit(state)
        self.assertTrue(committed.boundary_valid)
        self.assertTrue(committed.pc_write)
        self.assertTrue(committed.trap_event)
        self.assertTrue(committed.state.trap_asserted)
        self.assertTrue(committed.state.halted)
        self.assertTrue(committed.phase_hold)
        self.assertEqual(committed.state.pc, 0x1235)

    def test_state_seven_wait_does_not_assert_or_advance(self) -> None:
        state, _ = _accept(ConditionalTrapState(), 15)
        stalled = _commit(state, phase_advance=False)
        self.assertEqual(stalled.state, state)
        self.assertFalse(stalled.pc_write)
        self.assertFalse(stalled.trap_event)
        committed = _commit(stalled.state)
        self.assertTrue(committed.trap_event)

    def test_false_trap_advances_pc_without_halting(self) -> None:
        state = apply_conditional_trap_cycle(
            ConditionalTrapState(), setup_astat=ExactWord(8, 0)
        ).state
        state = apply_conditional_trap_cycle(state, setup_pc=0x3FFF).state
        state, accepted = _accept(state, 0)
        self.assertTrue(accepted.instruction_accepted)
        self.assertFalse(accepted.condition_true)
        committed = _commit(state)
        self.assertTrue(committed.boundary_valid)
        self.assertTrue(committed.pc_write)
        self.assertFalse(committed.trap_event)
        self.assertFalse(committed.state.halted)
        self.assertEqual(committed.state.pc, 0)

    def test_not_ce_does_not_modify_counter(self) -> None:
        state = apply_conditional_trap_cycle(
            ConditionalTrapState(), setup_counter=2
        ).state
        state, accepted = _accept(state, 14)
        self.assertTrue(accepted.condition_true)
        committed = _commit(state)
        self.assertTrue(committed.trap_event)
        self.assertEqual(committed.state.counter.value, 2)
        self.assertFalse(committed.counter_test)
        self.assertFalse(committed.counter_decremented)

    def test_unknown_condition_fails_closed_without_pending_action(self) -> None:
        result = apply_conditional_trap_cycle(
            ConditionalTrapState(),
            phase=LogicalPhase.STATE_1,
            execute=True,
            opcode=_opcode(0),
        )
        self.assertTrue(result.invalid_condition_state)
        self.assertFalse(result.instruction_accepted)
        self.assertFalse(result.state.pending)

    def test_halt_handshake_clears_trap_then_release_resumes(self) -> None:
        state, _ = _accept(ConditionalTrapState(), 15)
        state = _commit(state).state
        waiting = apply_conditional_trap_cycle(
            state, phase=LogicalPhase.STATE_8, halt_recognized=False
        )
        self.assertTrue(waiting.state.trap_asserted)
        acknowledged = apply_conditional_trap_cycle(
            waiting.state,
            phase=LogicalPhase.STATE_8,
            halt_recognized=True,
        )
        self.assertFalse(acknowledged.state.trap_asserted)
        self.assertTrue(acknowledged.state.halted)
        self.assertTrue(acknowledged.state.halt_handoff)
        held = apply_conditional_trap_cycle(
            acknowledged.state,
            phase=LogicalPhase.STATE_8,
            halt_recognized=True,
        )
        self.assertTrue(held.phase_hold)
        resumed = apply_conditional_trap_cycle(
            held.state,
            phase=LogicalPhase.STATE_8,
            halt_recognized=False,
        )
        self.assertTrue(resumed.resume_event)
        self.assertFalse(resumed.state.halted)
        self.assertFalse(resumed.phase_hold)

    def test_execute_while_halted_cannot_replace_pending_state(self) -> None:
        state, _ = _accept(ConditionalTrapState(), 15)
        state = _commit(state).state
        held = apply_conditional_trap_cycle(
            state,
            phase=LogicalPhase.STATE_1,
            execute=True,
            opcode=_opcode(15),
        )
        self.assertEqual(held.state, state)
        self.assertFalse(held.instruction_accepted)

    def test_wrong_phase_invalid_opcode_and_setup_conflicts_are_atomic(self) -> None:
        state = ConditionalTrapState()
        wrong_phase = apply_conditional_trap_cycle(
            state,
            phase=LogicalPhase.STATE_2,
            execute=True,
            opcode=_opcode(15),
        )
        self.assertTrue(wrong_phase.phase_mismatch)
        self.assertEqual(wrong_phase.state, state)
        invalid = apply_conditional_trap_cycle(
            state,
            phase=LogicalPhase.STATE_1,
            execute=True,
            opcode=0,
        )
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_conditional_trap_cycle(
            state,
            phase=LogicalPhase.STATE_1,
            execute=True,
            opcode=_opcode(15),
            setup_pc=1,
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)

    def test_halt_release_preserves_following_instruction_address(self) -> None:
        state = apply_conditional_trap_cycle(
            ConditionalTrapState(), setup_pc=0x0555
        ).state
        state, _ = _accept(state, 15)
        state = _commit(state).state
        state = apply_conditional_trap_cycle(
            state, phase=LogicalPhase.STATE_8, halt_recognized=True
        ).state
        resumed = apply_conditional_trap_cycle(
            state, phase=LogicalPhase.STATE_8, halt_recognized=False
        )
        self.assertEqual(resumed.state.pc, 0x0556)
        self.assertTrue(resumed.resume_event)


if __name__ == "__main__":
    unittest.main()
