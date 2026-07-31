from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    CONDITIONAL_RETURN_CLASS_MASK,
    CONDITIONAL_RETURN_CLASS_VALUE,
    ConditionalReturnState,
    CounterState,
    ExactWord,
    SequencerStacksState,
    StatusStackEntry,
    StatusStackState,
    apply_conditional_return_cycle,
    decode_conditional_return,
    is_conditional_return_class,
)


def _opcode(interrupt_return: bool, condition: int) -> int:
    return 0x0A0000 | (int(interrupt_return) << 4) | condition


class ConditionalReturnTests(unittest.TestCase):
    def test_complete_type_20_partition_and_fields(self) -> None:
        count = 0
        for interrupt_return in (False, True):
            for condition in range(16):
                action = decode_conditional_return(
                    _opcode(interrupt_return, condition)
                )
                self.assertIsNotNone(action)
                assert action is not None
                self.assertEqual(action.interrupt_return, interrupt_return)
                self.assertEqual(action.condition, condition)
                count += 1
        self.assertEqual(CONDITIONAL_RETURN_CLASS_MASK, 0xFFFFE0)
        self.assertEqual(CONDITIONAL_RETURN_CLASS_VALUE, 0x0A0000)
        self.assertEqual(count, 32)

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x090000, 0x0A0020, 0x0B0000):
            self.assertFalse(is_conditional_return_class(opcode))
            self.assertIsNone(decode_conditional_return(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_conditional_return(opcode)

    def test_reset_restores_documented_state_without_fabrication(self) -> None:
        state = ConditionalReturnState(
            pc=0x1234,
            counter=CounterState(7),
            stacks=SequencerStacksState(pc_entries=(1, 2)),
            status_stack=StatusStackState(
                entries=(StatusStackEntry.from_word(ExactWord(16, 0xABCD)),)
            ),
        )
        result = apply_conditional_return_cycle(state, reset=True)
        self.assertEqual(result.state, ConditionalReturnState.reset())
        self.assertEqual(result.state.pc, 4)
        self.assertFalse(result.state.status.astat.is_fully_known)
        self.assertEqual(result.state.status.mstat.value, 0)
        self.assertEqual(result.state.status.imask.value, 0)

    def test_taken_rts_pops_pc_only(self) -> None:
        state = apply_conditional_return_cycle(
            ConditionalReturnState.reset(), setup_pc_stack_push=0x1234
        ).state
        state = apply_conditional_return_cycle(
            state, setup_status_stack_push=ExactWord(16, 0x5A96)
        ).state
        result = apply_conditional_return_cycle(
            state, execute=True, opcode=_opcode(False, 15)
        )
        self.assertTrue(result.boundary_valid)
        self.assertTrue(result.pc_stack_pop_valid)
        self.assertFalse(result.status_stack_pop)
        self.assertFalse(result.status_restored)
        self.assertEqual(result.state.pc, 0x1234)
        self.assertEqual(result.state.status_stack, state.status_stack)

    def test_taken_rti_pops_both_and_restores_status_atomically(self) -> None:
        state = ConditionalReturnState.reset()
        state = apply_conditional_return_cycle(
            state, setup_astat=ExactWord(8, 0x01)
        ).state
        state = apply_conditional_return_cycle(
            state, setup_mstat=ExactWord(4, 0x2)
        ).state
        state = apply_conditional_return_cycle(
            state, setup_imask=ExactWord(4, 0x3)
        ).state
        state = apply_conditional_return_cycle(
            state, setup_pc_stack_push=0x2345
        ).state
        state = apply_conditional_return_cycle(
            state, setup_status_stack_push=ExactWord(16, 0xA5BC)
        ).state
        result = apply_conditional_return_cycle(
            state, execute=True, opcode=_opcode(True, 15)
        )
        self.assertTrue(result.pc_stack_pop_valid)
        self.assertTrue(result.status_stack_pop_valid)
        self.assertTrue(result.status_restored)
        self.assertEqual(result.state.pc, 0x2345)
        self.assertEqual(result.state.status.astat.to_word().value, 0xA5)
        self.assertEqual(result.state.status.mstat.value, 0xB)
        self.assertEqual(result.state.status.imask.value, 0xC)
        self.assertFalse(result.state.stacks.pc_entries)
        self.assertFalse(result.state.status_stack.entries)

    def test_false_return_advances_without_requiring_stack_context(self) -> None:
        state = apply_conditional_return_cycle(
            ConditionalReturnState.reset(), setup_astat=ExactWord(8, 0)
        ).state
        state = apply_conditional_return_cycle(state, setup_pc=0x3FFF).state
        for interrupt_return in (False, True):
            result = apply_conditional_return_cycle(
                state,
                execute=True,
                opcode=_opcode(interrupt_return, 0),
            )
            self.assertTrue(result.boundary_valid)
            self.assertFalse(result.condition_true)
            self.assertFalse(result.invalid_return_context)
            self.assertEqual(result.state.pc, 0)
            self.assertEqual(result.state.stacks, state.stacks)
            self.assertEqual(result.state.status_stack, state.status_stack)

    def test_taken_empty_contexts_fail_closed_atomically(self) -> None:
        empty = ConditionalReturnState.reset()
        rts = apply_conditional_return_cycle(
            empty, execute=True, opcode=_opcode(False, 15)
        )
        self.assertTrue(rts.invalid_return_context)
        self.assertEqual(rts.state, empty)

        pc_only = apply_conditional_return_cycle(
            empty, setup_pc_stack_push=0x1111
        ).state
        rti = apply_conditional_return_cycle(
            pc_only, execute=True, opcode=_opcode(True, 15)
        )
        self.assertTrue(rti.invalid_return_context)
        self.assertEqual(rti.state, pc_only)

        status_only = replace_status_stack(empty, 0x1234)
        missing_pc = apply_conditional_return_cycle(
            status_only, execute=True, opcode=_opcode(True, 15)
        )
        self.assertTrue(missing_pc.invalid_return_context)
        self.assertEqual(missing_pc.state, status_only)

    def test_rts_does_not_require_status_stack(self) -> None:
        state = apply_conditional_return_cycle(
            ConditionalReturnState.reset(), setup_pc_stack_push=0x0101
        ).state
        result = apply_conditional_return_cycle(
            state, execute=True, opcode=_opcode(False, 15)
        )
        self.assertTrue(result.boundary_valid)
        self.assertEqual(result.state.pc, 0x0101)

    def test_return_not_ce_never_decrements_or_restores_counter(self) -> None:
        state = apply_conditional_return_cycle(
            ConditionalReturnState.reset(), setup_counter=7
        ).state
        state = apply_conditional_return_cycle(state, setup_counter=2).state
        state = apply_conditional_return_cycle(
            state, setup_pc_stack_push=0x2222
        ).state
        taken = apply_conditional_return_cycle(
            state, execute=True, opcode=_opcode(False, 14)
        )
        self.assertTrue(taken.condition_true)
        self.assertEqual(taken.state.pc, 0x2222)
        self.assertEqual(taken.state.counter.value, 2)
        self.assertEqual(taken.state.stacks.count_entries, (7,))
        self.assertFalse(taken.counter_test)
        self.assertFalse(taken.counter_decremented)
        self.assertFalse(taken.counter_restored)

    def test_unknown_condition_preserves_state(self) -> None:
        state = apply_conditional_return_cycle(
            ConditionalReturnState.reset(), setup_pc_stack_push=0x2222
        ).state
        result = apply_conditional_return_cycle(
            state, execute=True, opcode=_opcode(False, 0)
        )
        self.assertTrue(result.invalid_condition_state)
        self.assertEqual(result.state, state)

    def test_rti_condition_uses_live_pre_restore_status(self) -> None:
        state = apply_conditional_return_cycle(
            ConditionalReturnState.reset(), setup_astat=ExactWord(8, 1)
        ).state
        state = apply_conditional_return_cycle(
            state, setup_pc_stack_push=0x3456
        ).state
        state = apply_conditional_return_cycle(
            state, setup_status_stack_push=ExactWord(16, 0x0000)
        ).state
        result = apply_conditional_return_cycle(
            state, execute=True, opcode=_opcode(True, 0)
        )
        self.assertTrue(result.condition_true)
        self.assertEqual(result.state.pc, 0x3456)
        self.assertEqual(result.state.status.astat.to_word().value, 0)

    def test_invalid_and_setup_conflicts_are_atomic(self) -> None:
        state = ConditionalReturnState.reset()
        invalid = apply_conditional_return_cycle(state, execute=True, opcode=0)
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_conditional_return_cycle(
            state,
            execute=True,
            opcode=_opcode(False, 15),
            setup_pc_stack_push=1,
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        two_setups = apply_conditional_return_cycle(
            state, setup_pc=1, setup_astat=ExactWord(8, 0)
        )
        self.assertTrue(two_setups.integration_conflict)
        self.assertEqual(two_setups.state, state)


def replace_status_stack(
    state: ConditionalReturnState,
    word: int,
) -> ConditionalReturnState:
    return ConditionalReturnState(
        pc=state.pc,
        status=state.status,
        counter=state.counter,
        stacks=state.stacks,
        status_stack=StatusStackState(
            entries=(StatusStackEntry.from_word(ExactWord(16, word)),)
        ),
    )


if __name__ == "__main__":
    unittest.main()
