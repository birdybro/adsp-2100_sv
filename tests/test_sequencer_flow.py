from __future__ import annotations

import random
import unittest

from sim.reference_models.adsp2100_model.sequencer import (
    ExplicitFlow,
    select_sequencer_flow,
)


class SequencerFlowTests(unittest.TestCase):
    def test_bad_addresses_and_flow_fail_closed(self) -> None:
        base = {
            "pc": 0,
            "explicit_flow": ExplicitFlow.NONE,
            "explicit_taken": False,
            "explicit_target": 0,
            "loop_active": False,
            "loop_end": 0,
            "loop_start": 0,
            "loop_termination_true": False,
            "loop_uses_counter": False,
        }
        for name in ("pc", "explicit_target", "loop_end", "loop_start"):
            invalid = dict(base)
            invalid[name] = 0x4000
            with self.assertRaises(ValueError):
                select_sequencer_flow(**invalid)
        invalid = dict(base)
        invalid["explicit_flow"] = 4
        with self.assertRaises(ValueError):
            select_sequencer_flow(**invalid)

    def test_sequential_flow_and_program_address_wrap(self) -> None:
        result = select_sequencer_flow(
            pc=0x3FFF,
            explicit_flow=ExplicitFlow.NONE,
            explicit_taken=False,
            explicit_target=0x1234,
            loop_active=False,
            loop_end=0x3FFF,
            loop_start=0x0100,
            loop_termination_true=False,
            loop_uses_counter=False,
        )
        self.assertEqual(result.next_pc, 0)
        self.assertEqual(result.pc_stack_push_value, 0)
        self.assertFalse(result.explicit_transfer)
        self.assertFalse(result.loop_back)
        self.assertFalse(result.loop_exit)

    def test_jump_call_and_return_actions(self) -> None:
        common = {
            "pc": 0x0123,
            "explicit_taken": True,
            "explicit_target": 0x2345,
            "loop_active": False,
            "loop_end": 0,
            "loop_start": 0,
            "loop_termination_true": False,
            "loop_uses_counter": False,
        }
        jump = select_sequencer_flow(
            explicit_flow=ExplicitFlow.JUMP,
            **common,
        )
        call = select_sequencer_flow(
            explicit_flow=ExplicitFlow.CALL,
            **common,
        )
        returned = select_sequencer_flow(
            explicit_flow=ExplicitFlow.RETURN,
            **common,
        )
        self.assertEqual(jump.next_pc, 0x2345)
        self.assertTrue(jump.explicit_transfer)
        self.assertFalse(jump.pc_stack_push)
        self.assertTrue(call.pc_stack_push)
        self.assertEqual(call.pc_stack_push_value, 0x0124)
        self.assertTrue(returned.pc_stack_pop)

    def test_false_explicit_condition_allows_loop_back(self) -> None:
        result = select_sequencer_flow(
            pc=0x0200,
            explicit_flow=ExplicitFlow.CALL,
            explicit_taken=False,
            explicit_target=0x3000,
            loop_active=True,
            loop_end=0x0200,
            loop_start=0x0100,
            loop_termination_true=False,
            loop_uses_counter=False,
        )
        self.assertEqual(result.next_pc, 0x0100)
        self.assertTrue(result.loop_back)
        self.assertFalse(result.pc_stack_push)
        self.assertFalse(result.explicit_transfer)

    def test_ordinary_loop_exit_pops_associated_stacks(self) -> None:
        result = select_sequencer_flow(
            pc=0x0200,
            explicit_flow=ExplicitFlow.NONE,
            explicit_taken=False,
            explicit_target=0,
            loop_active=True,
            loop_end=0x0200,
            loop_start=0x0100,
            loop_termination_true=True,
            loop_uses_counter=True,
        )
        self.assertEqual(result.next_pc, 0x0201)
        self.assertTrue(result.pc_stack_pop)
        self.assertTrue(result.loop_stack_pop)
        self.assertTrue(result.count_stack_pop)
        self.assertTrue(result.loop_counter_test)
        self.assertTrue(result.loop_exit)

    def test_non_counter_loop_never_touches_count_stack(self) -> None:
        result = select_sequencer_flow(
            pc=9,
            explicit_flow=ExplicitFlow.NONE,
            explicit_taken=False,
            explicit_target=0,
            loop_active=True,
            loop_end=9,
            loop_start=3,
            loop_termination_true=True,
            loop_uses_counter=False,
        )
        self.assertFalse(result.count_stack_pop)
        self.assertFalse(result.loop_counter_test)

    def test_taken_call_at_loop_end_has_explicit_precedence(self) -> None:
        result = select_sequencer_flow(
            pc=0x0200,
            explicit_flow=ExplicitFlow.CALL,
            explicit_taken=True,
            explicit_target=0x3000,
            loop_active=True,
            loop_end=0x0200,
            loop_start=0x0100,
            loop_termination_true=True,
            loop_uses_counter=True,
        )
        self.assertEqual(result.next_pc, 0x3000)
        self.assertEqual(result.pc_stack_push_value, 0x0201)
        self.assertTrue(result.pc_stack_push)
        self.assertFalse(result.pc_stack_pop)
        self.assertFalse(result.loop_stack_pop)
        self.assertFalse(result.count_stack_pop)
        self.assertFalse(result.loop_counter_test)
        self.assertFalse(result.loop_exit)

    def test_taken_return_at_loop_end_performs_only_return_pop(self) -> None:
        result = select_sequencer_flow(
            pc=0x0200,
            explicit_flow=ExplicitFlow.RETURN,
            explicit_taken=True,
            explicit_target=0x0100,
            loop_active=True,
            loop_end=0x0200,
            loop_start=0x0100,
            loop_termination_true=False,
            loop_uses_counter=True,
        )
        self.assertTrue(result.pc_stack_pop)
        self.assertFalse(result.loop_stack_pop)
        self.assertFalse(result.loop_counter_test)
        self.assertFalse(result.loop_back)

    def test_random_explicit_transfers_never_mutate_loop_stacks(self) -> None:
        rng = random.Random(0x2100)
        for _ in range(10000):
            flow = rng.choice(
                (ExplicitFlow.JUMP, ExplicitFlow.CALL, ExplicitFlow.RETURN)
            )
            result = select_sequencer_flow(
                pc=rng.randrange(0x4000),
                explicit_flow=flow,
                explicit_taken=True,
                explicit_target=rng.randrange(0x4000),
                loop_active=True,
                loop_end=rng.randrange(0x4000),
                loop_start=rng.randrange(0x4000),
                loop_termination_true=bool(rng.getrandbits(1)),
                loop_uses_counter=bool(rng.getrandbits(1)),
            )
            self.assertTrue(result.explicit_transfer)
            self.assertFalse(result.loop_stack_pop)
            self.assertFalse(result.count_stack_pop)
            self.assertFalse(result.loop_counter_test)
            self.assertFalse(result.loop_back)
            self.assertFalse(result.loop_exit)


if __name__ == "__main__":
    unittest.main()
