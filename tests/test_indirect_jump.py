from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    INDIRECT_JUMP_CLASS_MASK,
    INDIRECT_JUMP_CLASS_VALUE,
    CounterState,
    ExactWord,
    IndirectJumpState,
    SequencerStacksState,
    apply_indirect_jump_cycle,
    decode_indirect_jump,
    is_indirect_jump_class,
)


def _opcode(call: bool, i_local: int, condition: int) -> int:
    return 0x0B0000 | (i_local << 6) | (int(call) << 4) | condition


class IndirectJumpTests(unittest.TestCase):
    def test_complete_type_19_partition_and_fields(self) -> None:
        supported = 0
        unsupported = 0
        for i_local in range(4):
            for call in (False, True):
                for condition in range(16):
                    action = decode_indirect_jump(
                        _opcode(call, i_local, condition)
                    )
                    self.assertIsNotNone(action)
                    assert action is not None
                    self.assertEqual(action.call, call)
                    self.assertEqual(action.i_local, i_local)
                    self.assertEqual(action.i_address, i_local + 4)
                    self.assertEqual(action.condition, condition)
                    supported += action.supported
                    unsupported += not action.supported
        self.assertEqual(INDIRECT_JUMP_CLASS_MASK, 0xFFFF20)
        self.assertEqual(INDIRECT_JUMP_CLASS_VALUE, 0x0B0000)
        self.assertEqual(supported, 124)
        self.assertEqual(unsupported, 4)

    def test_fixed_bit_five_and_nonclass_words_fail_closed(self) -> None:
        for opcode in (0, 0x0B0020, 0x0A0000, 0x0C0000):
            self.assertFalse(is_indirect_jump_class(opcode))
            self.assertIsNone(decode_indirect_jump(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_indirect_jump(opcode)

    def test_reset_restores_pc_and_invalidates_targets(self) -> None:
        state = IndirectJumpState(
            pc=0x1234,
            counter=CounterState(9),
            stacks=SequencerStacksState(pc_entries=(3,), count_entries=(7,)),
            i4_i7=(1, 2, 3, 4),
        )
        result = apply_indirect_jump_cycle(state, reset=True)
        self.assertEqual(result.state, IndirectJumpState.reset())
        self.assertEqual(result.state.pc, 4)
        self.assertEqual(result.state.i4_i7, (None, None, None, None))

    def test_each_dag2_i_register_supplies_unmodified_target(self) -> None:
        state = IndirectJumpState.reset()
        targets = (0x0111, 0x1222, 0x2333, 0x3444)
        for local, target in enumerate(targets):
            state = apply_indirect_jump_cycle(
                state, setup_i=(local, target)
            ).state
        for local, target in enumerate(targets):
            result = apply_indirect_jump_cycle(
                state, execute=True, opcode=_opcode(False, local, 15)
            )
            self.assertTrue(result.boundary_valid)
            self.assertTrue(result.pma_indirect_drive)
            self.assertEqual(result.indirect_address, target)
            self.assertEqual(result.state.pc, target)
            self.assertEqual(result.state.i4_i7, targets)

    def test_false_condition_does_not_require_valid_target(self) -> None:
        state = apply_indirect_jump_cycle(
            IndirectJumpState.reset(), setup_astat=ExactWord(8, 0)
        ).state
        state = apply_indirect_jump_cycle(state, setup_pc=0x3FFF).state
        result = apply_indirect_jump_cycle(
            state, execute=True, opcode=_opcode(False, 2, 0)
        )
        self.assertTrue(result.boundary_valid)
        self.assertFalse(result.condition_true)
        self.assertFalse(result.indirect_address_valid)
        self.assertFalse(result.pma_indirect_drive)
        self.assertEqual(result.state.pc, 0)

    def test_taken_transfer_with_unknown_target_fails_closed(self) -> None:
        state = IndirectJumpState.reset()
        result = apply_indirect_jump_cycle(
            state, execute=True, opcode=_opcode(False, 0, 15)
        )
        self.assertTrue(result.condition_known)
        self.assertTrue(result.invalid_target_state)
        self.assertFalse(result.boundary_valid)
        self.assertEqual(result.state, state)

    def test_taken_call_pushes_pc_plus_one(self) -> None:
        state = apply_indirect_jump_cycle(
            IndirectJumpState.reset(), setup_pc=0x0100
        ).state
        state = apply_indirect_jump_cycle(state, setup_i=(3, 0x2200)).state
        result = apply_indirect_jump_cycle(
            state, execute=True, opcode=_opcode(True, 3, 15)
        )
        self.assertEqual(result.state.pc, 0x2200)
        self.assertEqual(result.state.stacks.pc_entries, (0x0101,))
        self.assertTrue(result.pc_stack_push_accepted)

    def test_jump_not_ce_decrements_or_restores_counter(self) -> None:
        state = apply_indirect_jump_cycle(
            IndirectJumpState.reset(), setup_i=(0, 0x1000)
        ).state
        state = apply_indirect_jump_cycle(state, setup_counter=7).state
        state = apply_indirect_jump_cycle(state, setup_counter=1).state
        expired = apply_indirect_jump_cycle(
            state, execute=True, opcode=_opcode(False, 0, 14)
        )
        self.assertFalse(expired.condition_true)
        self.assertTrue(expired.counter_restored)
        self.assertEqual(expired.state.counter.value, 7)
        decremented = apply_indirect_jump_cycle(
            expired.state, execute=True, opcode=_opcode(False, 0, 14)
        )
        self.assertTrue(decremented.condition_true)
        self.assertTrue(decremented.counter_decremented)
        self.assertEqual(decremented.state.counter.value, 6)
        self.assertEqual(decremented.state.pc, 0x1000)

    def test_call_not_ce_is_explicitly_unsupported(self) -> None:
        state = apply_indirect_jump_cycle(
            IndirectJumpState.reset(), setup_i=(0, 0x1000)
        ).state
        result = apply_indirect_jump_cycle(
            state, execute=True, opcode=_opcode(True, 0, 14)
        )
        self.assertTrue(result.class_valid)
        self.assertFalse(result.action_valid)
        self.assertTrue(result.unsupported_call_ce)
        self.assertEqual(result.state, state)

    def test_unknown_condition_preserves_state(self) -> None:
        state = apply_indirect_jump_cycle(
            IndirectJumpState.reset(), setup_i=(0, 0x1000)
        ).state
        result = apply_indirect_jump_cycle(
            state, execute=True, opcode=_opcode(False, 0, 0)
        )
        self.assertTrue(result.invalid_condition_state)
        self.assertEqual(result.state, state)

    def test_pc_stack_overflow_loses_only_new_return(self) -> None:
        entries = tuple(range(16))
        state = IndirectJumpState(
            pc=0x0100,
            stacks=SequencerStacksState(pc_entries=entries),
            i4_i7=(0x2000, None, None, None),
        )
        result = apply_indirect_jump_cycle(
            state, execute=True, opcode=_opcode(True, 0, 15)
        )
        self.assertEqual(result.state.pc, 0x2000)
        self.assertEqual(result.state.stacks.pc_entries, entries)
        self.assertTrue(result.state.stacks.pc_overflow)
        self.assertFalse(result.pc_stack_push_accepted)

    def test_invalid_and_setup_conflicts_are_atomic(self) -> None:
        state = IndirectJumpState.reset()
        invalid = apply_indirect_jump_cycle(state, execute=True, opcode=0)
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_indirect_jump_cycle(
            state,
            execute=True,
            opcode=_opcode(False, 0, 15),
            setup_i=(0, 1),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        two_setups = apply_indirect_jump_cycle(
            state, setup_pc=9, setup_i=(0, 1)
        )
        self.assertTrue(two_setups.integration_conflict)
        self.assertEqual(two_setups.state, state)


if __name__ == "__main__":
    unittest.main()
