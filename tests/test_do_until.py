from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DO_UNTIL_CLASS_MASK,
    DO_UNTIL_CLASS_VALUE,
    CounterState,
    DoUntilState,
    SequencerStacksState,
    apply_do_until_cycle,
    decode_do_until,
    is_do_until_class,
)


def _opcode(end_address: int, termination: int) -> int:
    return 0x140000 | (end_address << 4) | termination


class DoUntilTests(unittest.TestCase):
    def test_complete_type_11_partition_and_fields(self) -> None:
        count = 0
        for end_address in range(1 << 14):
            for termination in range(16):
                opcode = _opcode(end_address, termination)
                action = decode_do_until(opcode)
                self.assertIsNotNone(action)
                assert action is not None
                self.assertEqual(action.end_address, end_address)
                self.assertEqual(action.termination, termination)
                count += 1
        self.assertEqual(DO_UNTIL_CLASS_MASK, 0xFC0000)
        self.assertEqual(DO_UNTIL_CLASS_VALUE, 0x140000)
        self.assertEqual(count, 262_144)

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x13FFFF, 0x180000):
            self.assertFalse(is_do_until_class(opcode))
            self.assertIsNone(decode_do_until(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_do_until(opcode)

    def test_reset_restores_pc_and_invalidates_context(self) -> None:
        state = DoUntilState(
            pc=0x1234,
            counter=CounterState(7),
            stacks=SequencerStacksState(
                pc_entries=(5,),
                loop_entries=((15 << 14) | 9,),
            ),
        )
        result = apply_do_until_cycle(state, reset=True)
        self.assertEqual(result.state, DoUntilState.reset())
        self.assertEqual(result.state.pc, 4)

    def test_pushes_pc_plus_one_and_loop_descriptor_atomically(self) -> None:
        state = apply_do_until_cycle(
            DoUntilState.reset(), setup_pc=0x0100
        ).state
        result = apply_do_until_cycle(
            state, execute=True, opcode=_opcode(0x0234, 1)
        )
        self.assertTrue(result.boundary_valid)
        self.assertEqual(result.state.pc, 0x0101)
        self.assertEqual(result.state.stacks.pc_entries, (0x0101,))
        self.assertEqual(
            result.state.stacks.loop_entries,
            ((1 << 14) | 0x0234,),
        )
        self.assertTrue(result.pc_stack_push_accepted)
        self.assertTrue(result.loop_stack_push_accepted)
        self.assertFalse(result.pm_data_access)
        self.assertFalse(result.dm_access)

    def test_every_termination_code_is_stored_exactly(self) -> None:
        for termination in range(16):
            result = apply_do_until_cycle(
                DoUntilState.reset(),
                execute=True,
                opcode=_opcode(0x1234, termination),
            )
            self.assertEqual(
                result.state.stacks.loop_entries,
                ((termination << 14) | 0x1234,),
            )

    def test_nested_distinct_end_is_accepted(self) -> None:
        outer = apply_do_until_cycle(
            DoUntilState.reset(), execute=True, opcode=_opcode(8, 15)
        )
        inner = apply_do_until_cycle(
            outer.state, execute=True, opcode=_opcode(7, 0)
        )
        self.assertTrue(inner.boundary_valid)
        self.assertEqual(inner.state.stacks.pc_entries, (5, 6))
        self.assertEqual(len(inner.state.stacks.loop_entries), 2)

    def test_nested_same_end_is_rejected_atomically(self) -> None:
        outer = apply_do_until_cycle(
            DoUntilState.reset(), execute=True, opcode=_opcode(8, 15)
        )
        inner = apply_do_until_cycle(
            outer.state, execute=True, opcode=_opcode(8, 1)
        )
        self.assertFalse(inner.boundary_valid)
        self.assertTrue(inner.unsupported_nested_same_end)
        self.assertEqual(inner.state, outer.state)

    def test_do_at_outer_terminal_is_held_under_oq_018(self) -> None:
        outer = apply_do_until_cycle(
            DoUntilState.reset(), execute=True, opcode=_opcode(8, 15)
        )
        at_end = apply_do_until_cycle(outer.state, setup_pc=8).state
        result = apply_do_until_cycle(
            at_end, execute=True, opcode=_opcode(9, 1)
        )
        self.assertFalse(result.boundary_valid)
        self.assertTrue(result.unsupported_do_at_loop_end)
        self.assertEqual(result.state, at_end)

    def test_nested_do_requires_valid_outer_ce_context(self) -> None:
        malformed = DoUntilState(
            pc=5,
            stacks=SequencerStacksState(
                pc_entries=(5,),
                loop_entries=((14 << 14) | 8,),
            ),
        )
        invalid = apply_do_until_cycle(
            malformed, execute=True, opcode=_opcode(7, 15)
        )
        self.assertTrue(invalid.invalid_loop_context)
        self.assertEqual(invalid.state, malformed)
        valid_state = apply_do_until_cycle(malformed, setup_counter=3).state
        valid = apply_do_until_cycle(
            valid_state, execute=True, opcode=_opcode(7, 15)
        )
        self.assertTrue(valid.boundary_valid)

    def test_missing_outer_pc_stack_context_is_rejected(self) -> None:
        malformed = DoUntilState(
            pc=5,
            stacks=SequencerStacksState(
                loop_entries=((15 << 14) | 8,),
            ),
        )
        result = apply_do_until_cycle(
            malformed, execute=True, opcode=_opcode(7, 15)
        )
        self.assertTrue(result.invalid_loop_context)
        self.assertEqual(result.state, malformed)

    def test_fifth_nested_do_reports_loop_stack_overflow(self) -> None:
        state = DoUntilState.reset()
        for end_address in (12, 11, 10, 9):
            result = apply_do_until_cycle(
                state, execute=True, opcode=_opcode(end_address, 15)
            )
            self.assertTrue(result.loop_stack_push_accepted)
            state = result.state
        overflow = apply_do_until_cycle(
            state, execute=True, opcode=_opcode(8, 15)
        )
        self.assertTrue(overflow.boundary_valid)
        self.assertTrue(overflow.loop_stack_overflow_event)
        self.assertTrue(overflow.state.stacks.loop_overflow)
        self.assertEqual(len(overflow.state.stacks.loop_entries), 4)
        self.assertEqual(len(overflow.state.stacks.pc_entries), 5)

    def test_invalid_and_setup_conflicts_preserve_state(self) -> None:
        state = DoUntilState.reset()
        invalid = apply_do_until_cycle(state, execute=True, opcode=0)
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_do_until_cycle(
            state,
            execute=True,
            opcode=_opcode(8, 15),
            setup_pc=9,
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        two_setups = apply_do_until_cycle(
            state, setup_pc=9, setup_counter=3
        )
        self.assertTrue(two_setups.integration_conflict)
        self.assertEqual(two_setups.state, state)


if __name__ == "__main__":
    unittest.main()
