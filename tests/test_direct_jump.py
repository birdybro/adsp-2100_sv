from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DIRECT_JUMP_CLASS_MASK,
    DIRECT_JUMP_CLASS_VALUE,
    CounterState,
    DirectJumpState,
    ExactWord,
    SequencerStacksState,
    apply_direct_jump_cycle,
    decode_direct_jump,
    is_direct_jump_class,
)


def _opcode(call: bool, address: int, condition: int) -> int:
    return 0x180000 | (int(call) << 18) | (address << 4) | condition


class DirectJumpTests(unittest.TestCase):
    def test_complete_type_10_partition_and_fields(self) -> None:
        supported = 0
        unsupported = 0
        for call in (False, True):
            for address in range(1 << 14):
                for condition in range(16):
                    opcode = _opcode(call, address, condition)
                    action = decode_direct_jump(opcode)
                    self.assertIsNotNone(action)
                    assert action is not None
                    self.assertEqual(action.call, call)
                    self.assertEqual(action.address, address)
                    self.assertEqual(action.condition, condition)
                    supported += action.supported
                    unsupported += not action.supported
        self.assertEqual(DIRECT_JUMP_CLASS_MASK, 0xF80000)
        self.assertEqual(DIRECT_JUMP_CLASS_VALUE, 0x180000)
        self.assertEqual(supported, 507_904)
        self.assertEqual(unsupported, 16_384)

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x17FFFF, 0x200000):
            self.assertFalse(is_direct_jump_class(opcode))
            self.assertIsNone(decode_direct_jump(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_direct_jump(opcode)

    def test_reset_restores_pc_and_invalidates_context(self) -> None:
        state = DirectJumpState(
            pc=0x1234,
            counter=CounterState(9),
            stacks=SequencerStacksState(pc_entries=(3,), count_entries=(7,)),
        )
        result = apply_direct_jump_cycle(state, reset=True)
        self.assertEqual(result.state, DirectJumpState.reset())
        self.assertEqual(result.state.pc, 4)
        self.assertIsNone(result.state.counter.value)

    def test_unconditional_jump_uses_full_direct_address(self) -> None:
        state = apply_direct_jump_cycle(
            DirectJumpState.reset(), setup_pc=0x3FFF
        ).state
        result = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(False, 0x2345, 15),
        )
        self.assertTrue(result.boundary_valid)
        self.assertTrue(result.explicit_transfer)
        self.assertEqual(result.state.pc, 0x2345)
        self.assertFalse(result.pc_stack_push)

    def test_false_jump_advances_with_fourteen_bit_wrap(self) -> None:
        state = apply_direct_jump_cycle(
            DirectJumpState.reset(), setup_pc=0x3FFF
        ).state
        state = apply_direct_jump_cycle(
            state, setup_astat=ExactWord(8, 0)
        ).state
        result = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(False, 0x1234, 0),
        )
        self.assertTrue(result.boundary_valid)
        self.assertFalse(result.condition_true)
        self.assertEqual(result.state.pc, 0)

    def test_taken_call_pushes_cycle_start_pc_plus_one(self) -> None:
        state = apply_direct_jump_cycle(
            DirectJumpState.reset(), setup_pc=0x0100
        ).state
        result = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(True, 0x2200, 15),
        )
        self.assertEqual(result.state.pc, 0x2200)
        self.assertEqual(result.state.stacks.pc_entries, (0x0101,))
        self.assertTrue(result.pc_stack_push_accepted)

    def test_false_call_does_not_push(self) -> None:
        state = apply_direct_jump_cycle(
            DirectJumpState.reset(), setup_astat=ExactWord(8, 0)
        ).state
        result = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(True, 0x2200, 0),
        )
        self.assertEqual(result.state.pc, 5)
        self.assertEqual(result.state.stacks.pc_entries, ())

    def test_jump_not_ce_decrements_and_expired_restores_outer_count(self) -> None:
        state = apply_direct_jump_cycle(
            DirectJumpState.reset(), setup_counter=7
        ).state
        state = apply_direct_jump_cycle(state, setup_counter=1).state
        self.assertEqual(state.stacks.count_entries, (7,))
        expired = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(False, 0x1000, 14),
        )
        self.assertFalse(expired.condition_true)
        self.assertTrue(expired.counter_test)
        self.assertTrue(expired.counter_restored)
        self.assertEqual(expired.state.counter.value, 7)
        self.assertEqual(expired.state.stacks.count_entries, ())
        decremented = apply_direct_jump_cycle(
            expired.state,
            execute=True,
            opcode=_opcode(False, 0x1000, 14),
        )
        self.assertTrue(decremented.condition_true)
        self.assertTrue(decremented.counter_decremented)
        self.assertEqual(decremented.state.counter.value, 6)
        self.assertEqual(decremented.state.pc, 0x1000)

    def test_conditional_call_not_ce_is_explicitly_unsupported(self) -> None:
        state = apply_direct_jump_cycle(
            DirectJumpState.reset(), setup_counter=3
        ).state
        result = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(True, 0x1000, 14),
        )
        self.assertTrue(result.class_valid)
        self.assertFalse(result.action_valid)
        self.assertTrue(result.unsupported_call_ce)
        self.assertEqual(result.state, state)

    def test_unknown_condition_and_invalid_counter_preserve_state(self) -> None:
        state = DirectJumpState.reset()
        unknown_astat = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(False, 0x1000, 0),
        )
        self.assertTrue(unknown_astat.invalid_condition_state)
        self.assertEqual(unknown_astat.state, state)
        invalid_counter = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(False, 0x1000, 14),
        )
        self.assertTrue(invalid_counter.invalid_condition_state)
        self.assertEqual(invalid_counter.state, state)

    def test_pc_stack_overflow_loses_new_return_not_call_target(self) -> None:
        entries = tuple(range(16))
        state = DirectJumpState(
            pc=0x0100,
            astat=DirectJumpState.reset().astat,
            stacks=SequencerStacksState(pc_entries=entries),
        )
        result = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(True, 0x2000, 15),
        )
        self.assertEqual(result.state.pc, 0x2000)
        self.assertEqual(result.state.stacks.pc_entries, entries)
        self.assertTrue(result.state.stacks.pc_overflow)
        self.assertFalse(result.pc_stack_push_accepted)

    def test_invalid_and_setup_conflict_are_atomic(self) -> None:
        state = DirectJumpState.reset()
        invalid = apply_direct_jump_cycle(state, execute=True, opcode=0)
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_direct_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(False, 1, 15),
            setup_pc=9,
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)


if __name__ == "__main__":
    unittest.main()
