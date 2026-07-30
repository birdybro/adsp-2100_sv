from __future__ import annotations

import json
from pathlib import Path
import random
import unittest

from sim.reference_models.adsp2100_model import (
    COUNT_STACK_DEPTH,
    LOOP_STACK_DEPTH,
    PC_STACK_DEPTH,
    SequencerStacksInputs,
    SequencerStacksState,
    apply_sequencer_stacks_cycle,
)


ROOT = Path(__file__).resolve().parents[1]


class SequencerStackMetadataTests(unittest.TestCase):
    def test_original_stack_dimensions_and_controls(self) -> None:
        metadata = json.loads(
            (ROOT / "docs/generated/adsp2100_status_registers.yaml").read_text(
                encoding="utf-8"
            )
        )
        stacks = metadata["stack_architecture"]
        self.assertEqual((stacks["PC"]["depth"], stacks["PC"]["width"]), (16, 14))
        self.assertEqual(
            (stacks["COUNT"]["depth"], stacks["COUNT"]["width"]),
            (4, 14),
        )
        self.assertEqual(
            (stacks["LOOP"]["depth"], stacks["LOOP"]["width"]),
            (4, 18),
        )
        self.assertEqual(stacks["PC"]["stack_control_field"]["bit"], 4)
        self.assertEqual(stacks["COUNT"]["stack_control_field"]["bit"], 2)
        self.assertEqual(stacks["LOOP"]["stack_control_field"]["bit"], 3)


class SequencerStacksModelTests(unittest.TestCase):
    def test_reset_clears_pointers_and_overflow_not_data_by_fiat(self) -> None:
        state = SequencerStacksState(
            pc_entries=(1,),
            count_entries=(2,),
            loop_entries=(3,),
            pc_overflow=True,
            count_overflow=True,
            loop_overflow=True,
        )
        result = apply_sequencer_stacks_cycle(
            state,
            SequencerStacksInputs(
                reset=True,
                pc_push=True,
                pc_push_value=0x1234,
            ),
        )
        self.assertEqual(result.state, SequencerStacksState())
        self.assertEqual(result.state.sstat_fragment, 0x45)

    def test_pc_stack_has_sixteen_lifo_entries(self) -> None:
        state = SequencerStacksState()
        values = tuple((index * 0x101) & 0x3FFF for index in range(16))
        for value in values:
            result = apply_sequencer_stacks_cycle(
                state,
                SequencerStacksInputs(pc_push=True, pc_push_value=value),
            )
            self.assertTrue(result.pc_push_accepted)
            state = result.state
        self.assertEqual(len(state.pc_entries), PC_STACK_DEPTH)

        popped: list[int] = []
        for _ in values:
            result = apply_sequencer_stacks_cycle(
                state,
                SequencerStacksInputs(pc_pop=True),
            )
            self.assertIsNotNone(result.pc_pop_value)
            popped.append(result.pc_pop_value)
            state = result.state
        self.assertEqual(popped, list(reversed(values)))

    def test_count_and_loop_stacks_have_exact_width_and_depth(self) -> None:
        state = SequencerStacksState()
        count_values = (0, 1, 0x2000, 0x3FFF)
        loop_values = (0, 0x3FFF, 0x30000, 0x3FFFF)
        for count_value, loop_value in zip(count_values, loop_values):
            state = apply_sequencer_stacks_cycle(
                state,
                SequencerStacksInputs(
                    count_push=True,
                    count_push_value=count_value,
                    loop_push=True,
                    loop_push_value=loop_value,
                ),
            ).state
        self.assertEqual(len(state.count_entries), COUNT_STACK_DEPTH)
        self.assertEqual(len(state.loop_entries), LOOP_STACK_DEPTH)

        for count_value, loop_value in zip(
            reversed(count_values),
            reversed(loop_values),
        ):
            result = apply_sequencer_stacks_cycle(
                state,
                SequencerStacksInputs(count_pop=True, loop_pop=True),
            )
            self.assertEqual(result.count_pop_value, count_value)
            self.assertEqual(result.loop_pop_value, loop_value)
            state = result.state

    def test_each_overflow_drops_newest_and_sticks(self) -> None:
        state = SequencerStacksState(
            pc_entries=tuple(range(PC_STACK_DEPTH)),
            count_entries=tuple(range(COUNT_STACK_DEPTH)),
            loop_entries=tuple(range(LOOP_STACK_DEPTH)),
        )
        result = apply_sequencer_stacks_cycle(
            state,
            SequencerStacksInputs(
                pc_push=True,
                pc_push_value=0x3FFF,
                count_push=True,
                count_push_value=0x3FFF,
                loop_push=True,
                loop_push_value=0x3FFFF,
            ),
        )
        self.assertEqual(result.state.pc_entries, state.pc_entries)
        self.assertEqual(result.state.count_entries, state.count_entries)
        self.assertEqual(result.state.loop_entries, state.loop_entries)
        self.assertTrue(result.pc_overflow_event)
        self.assertTrue(result.count_overflow_event)
        self.assertTrue(result.loop_overflow_event)
        self.assertEqual(result.state.sstat_fragment, 0x8A)

        state = result.state
        for _ in range(PC_STACK_DEPTH):
            state = apply_sequencer_stacks_cycle(
                state,
                SequencerStacksInputs(
                    pc_pop=True,
                    count_pop=bool(state.count_entries),
                    loop_pop=bool(state.loop_entries),
                ),
            ).state
        self.assertEqual(state.sstat_fragment, 0xCF)

    def test_independent_stack_actions_are_atomic(self) -> None:
        pushed = apply_sequencer_stacks_cycle(
            SequencerStacksState(),
            SequencerStacksInputs(
                pc_push=True,
                pc_push_value=0x1234,
                count_push=True,
                count_push_value=0x2345,
                loop_push=True,
                loop_push_value=0x34567,
            ),
        )
        self.assertTrue(pushed.pc_push_accepted)
        self.assertTrue(pushed.count_push_accepted)
        self.assertTrue(pushed.loop_push_accepted)

        popped = apply_sequencer_stacks_cycle(
            pushed.state,
            SequencerStacksInputs(
                pc_pop=True,
                count_pop=True,
                loop_pop=True,
            ),
        )
        self.assertEqual(popped.pc_pop_value, 0x1234)
        self.assertEqual(popped.count_pop_value, 0x2345)
        self.assertEqual(popped.loop_pop_value, 0x34567)
        self.assertEqual(popped.state, SequencerStacksState())

    def test_same_stack_push_pop_conflict_suppresses_every_stack(self) -> None:
        state = SequencerStacksState(
            pc_entries=(0x1234,),
            count_entries=(0x2345,),
            loop_entries=(0x34567,),
        )
        result = apply_sequencer_stacks_cycle(
            state,
            SequencerStacksInputs(
                pc_push=True,
                pc_pop=True,
                count_pop=True,
                loop_push=True,
                loop_push_value=0x11111,
            ),
        )
        self.assertTrue(result.write_conflict)
        self.assertEqual(result.state, state)
        self.assertIsNone(result.count_pop_value)
        self.assertFalse(result.loop_push_accepted)

    def test_empty_pop_is_invalid_and_preserves_state(self) -> None:
        state = SequencerStacksState()
        result = apply_sequencer_stacks_cycle(
            state,
            SequencerStacksInputs(
                pc_pop=True,
                count_pop=True,
                loop_pop=True,
            ),
        )
        self.assertEqual(result.state, state)
        self.assertTrue(result.pc_empty_pop)
        self.assertTrue(result.count_empty_pop)
        self.assertTrue(result.loop_empty_pop)
        self.assertIsNone(result.pc_pop_value)
        self.assertIsNone(result.count_pop_value)
        self.assertIsNone(result.loop_pop_value)

    def test_width_and_depth_violations_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            SequencerStacksInputs(pc_push_value=0x4000)
        with self.assertRaises(ValueError):
            SequencerStacksInputs(count_push_value=-1)
        with self.assertRaises(ValueError):
            SequencerStacksInputs(loop_push_value=0x40000)
        with self.assertRaises(ValueError):
            SequencerStacksState(pc_entries=tuple(range(17)))
        with self.assertRaises(ValueError):
            SequencerStacksState(count_entries=tuple(range(5)))
        with self.assertRaises(ValueError):
            SequencerStacksState(loop_entries=tuple(range(5)))

    def test_randomized_depth_and_sticky_overflow_invariants(self) -> None:
        rng = random.Random(0x210015)
        state = SequencerStacksState()
        overflow_seen = [False, False, False]
        for _ in range(20_000):
            operations = [rng.randrange(3) for _ in range(3)]
            inputs = SequencerStacksInputs(
                pc_push=operations[0] == 1,
                pc_pop=operations[0] == 2,
                pc_push_value=rng.randrange(1 << 14),
                count_push=operations[1] == 1,
                count_pop=operations[1] == 2,
                count_push_value=rng.randrange(1 << 14),
                loop_push=operations[2] == 1,
                loop_pop=operations[2] == 2,
                loop_push_value=rng.randrange(1 << 18),
            )
            result = apply_sequencer_stacks_cycle(state, inputs)
            state = result.state
            self.assertLessEqual(len(state.pc_entries), PC_STACK_DEPTH)
            self.assertLessEqual(len(state.count_entries), COUNT_STACK_DEPTH)
            self.assertLessEqual(len(state.loop_entries), LOOP_STACK_DEPTH)
            overflow_seen[0] |= result.pc_overflow_event
            overflow_seen[1] |= result.count_overflow_event
            overflow_seen[2] |= result.loop_overflow_event
            self.assertGreaterEqual(int(state.pc_overflow), int(overflow_seen[0]))
            self.assertGreaterEqual(
                int(state.count_overflow),
                int(overflow_seen[1]),
            )
            self.assertGreaterEqual(
                int(state.loop_overflow),
                int(overflow_seen[2]),
            )


if __name__ == "__main__":
    unittest.main()
