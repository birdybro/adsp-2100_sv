from __future__ import annotations

import json
from pathlib import Path
import random
import unittest

from sim.reference_models.adsp2100_model import (
    CounterState,
    ExplicitFlow,
    SequencerSliceInputs,
    SequencerSliceState,
    SequencerStacksState,
    apply_sequencer_slice_cycle,
)


ROOT = Path(__file__).resolve().parents[1]


class SequencerSliceMetadataTests(unittest.TestCase):
    def test_integration_boundary_is_machine_readable(self) -> None:
        metadata = json.loads(
            (
                ROOT
                / "docs/generated/adsp2100_sequencer_slice.yaml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["device"], "ADSP-2100")
        self.assertEqual(
            metadata["loop_stack_internal_packing"],
            "CONDITION_17_14__END_ADDRESS_13_0",
        )
        self.assertEqual(
            metadata["rejected_boundaries"]["CONDITIONAL_CALL_CE"],
            "OQ-012",
        )
        self.assertEqual(
            metadata["rejected_boundaries"][
                "COMPETING_AUTOMATIC_MANUAL_ACTIONS"
            ],
            "OQ-018",
        )


class SequencerSliceModelTests(unittest.TestCase):
    def test_reset_clears_validity_and_stack_pointers(self) -> None:
        state = SequencerSliceState(
            counter=CounterState(7),
            stacks=SequencerStacksState(
                pc_entries=(1,),
                count_entries=(2,),
                loop_entries=(3,),
            ),
        )
        result = apply_sequencer_slice_cycle(
            state,
            SequencerSliceInputs(
                reset=True,
                pc=0x1234,
                do_until=True,
                do_end=0x2000,
                explicit_flow=ExplicitFlow.JUMP,
                explicit_condition=15,
                explicit_target=0x3000,
                counter_load=True,
                counter_load_value=9,
                pc_manual_pop=True,
            ),
        )
        self.assertEqual(result.state, SequencerSliceState())
        self.assertFalse(result.boundary_valid)
        self.assertFalse(result.integration_conflict)
        self.assertEqual(result.next_pc, 0x1235)

    def test_do_until_pushes_first_address_and_loop_descriptor(self) -> None:
        result = apply_sequencer_slice_cycle(
            SequencerSliceState(),
            SequencerSliceInputs(
                pc=0x0100,
                do_until=True,
                do_end=0x0110,
                do_condition=15,
            ),
        )
        self.assertTrue(result.boundary_valid)
        self.assertEqual(result.next_pc, 0x0101)
        self.assertEqual(result.state.stacks.pc_entries, (0x0101,))
        self.assertEqual(
            result.state.stacks.loop_entries,
            ((15 << 14) | 0x0110,),
        )
        self.assertTrue(result.pc_stack_push)
        self.assertTrue(result.loop_stack_push)

    def test_forever_loop_uses_pc_stack_top_without_popping(self) -> None:
        setup = apply_sequencer_slice_cycle(
            SequencerSliceState(),
            SequencerSliceInputs(
                pc=0x0100,
                do_until=True,
                do_end=0x0103,
                do_condition=15,
            ),
        )
        result = apply_sequencer_slice_cycle(
            setup.state,
            SequencerSliceInputs(pc=0x0103),
        )
        self.assertEqual(result.next_pc, 0x0101)
        self.assertTrue(result.loop_back)
        self.assertFalse(result.loop_exit)
        self.assertEqual(result.state, setup.state)

    def test_non_counter_loop_exit_pops_pc_and_loop_together(self) -> None:
        setup = apply_sequencer_slice_cycle(
            SequencerSliceState(),
            SequencerSliceInputs(
                pc=0x0200,
                do_until=True,
                do_end=0x0202,
                do_condition=0,
            ),
        )
        result = apply_sequencer_slice_cycle(
            setup.state,
            SequencerSliceInputs(
                pc=0x0202,
                az=False,
            ),
        )
        self.assertTrue(result.loop_termination_true)
        self.assertTrue(result.loop_exit)
        self.assertTrue(result.pc_stack_pop)
        self.assertTrue(result.loop_stack_pop)
        self.assertEqual(result.state.stacks.pc_entries, ())
        self.assertEqual(result.state.stacks.loop_entries, ())

    def test_ce_loop_executes_exact_loaded_count(self) -> None:
        state = apply_sequencer_slice_cycle(
            SequencerSliceState(),
            SequencerSliceInputs(
                pc=0,
                counter_load=True,
                counter_load_value=3,
            ),
        ).state
        state = apply_sequencer_slice_cycle(
            state,
            SequencerSliceInputs(
                pc=1,
                do_until=True,
                do_end=4,
                do_condition=14,
            ),
        ).state

        observations: list[tuple[bool, bool, int | None]] = []
        for _ in range(3):
            result = apply_sequencer_slice_cycle(
                state,
                SequencerSliceInputs(pc=4),
            )
            observations.append(
                (
                    result.loop_back,
                    result.loop_exit,
                    result.state.counter.value,
                )
            )
            state = result.state
        self.assertEqual(
            observations,
            [
                (True, False, 2),
                (True, False, 1),
                (False, True, None),
            ],
        )
        self.assertEqual(state.stacks.pc_entries, ())
        self.assertEqual(state.stacks.loop_entries, ())

    def test_nested_ce_loop_restores_outer_count(self) -> None:
        state = SequencerSliceState()
        for inputs in (
            SequencerSliceInputs(
                pc=0,
                counter_load=True,
                counter_load_value=2,
            ),
            SequencerSliceInputs(
                pc=1,
                do_until=True,
                do_end=9,
                do_condition=14,
            ),
            SequencerSliceInputs(
                pc=2,
                counter_load=True,
                counter_load_value=1,
            ),
            SequencerSliceInputs(
                pc=3,
                do_until=True,
                do_end=6,
                do_condition=14,
            ),
        ):
            state = apply_sequencer_slice_cycle(state, inputs).state

        self.assertEqual(state.stacks.count_entries, (2,))
        inner_exit = apply_sequencer_slice_cycle(
            state,
            SequencerSliceInputs(pc=6),
        )
        self.assertTrue(inner_exit.counter_restored)
        self.assertEqual(inner_exit.state.counter.value, 2)
        self.assertEqual(inner_exit.state.stacks.count_entries, ())
        self.assertEqual(len(inner_exit.state.stacks.loop_entries), 1)

        outer_back = apply_sequencer_slice_cycle(
            inner_exit.state,
            SequencerSliceInputs(pc=9),
        )
        self.assertTrue(outer_back.loop_back)
        self.assertEqual(outer_back.state.counter.value, 1)

    def test_conditional_jump_ce_decrements_on_both_outcomes(self) -> None:
        loaded = apply_sequencer_slice_cycle(
            SequencerSliceState(),
            SequencerSliceInputs(
                counter_load=True,
                counter_load_value=2,
            ),
        )
        taken = apply_sequencer_slice_cycle(
            loaded.state,
            SequencerSliceInputs(
                pc=4,
                explicit_flow=ExplicitFlow.JUMP,
                explicit_condition=14,
                explicit_target=0x1234,
            ),
        )
        self.assertTrue(taken.explicit_condition_true)
        self.assertTrue(taken.explicit_transfer)
        self.assertEqual(taken.next_pc, 0x1234)
        self.assertTrue(taken.counter_decremented)
        self.assertEqual(taken.state.counter.value, 1)

        not_taken = apply_sequencer_slice_cycle(
            taken.state,
            SequencerSliceInputs(
                pc=5,
                explicit_flow=ExplicitFlow.JUMP,
                explicit_condition=14,
                explicit_target=0x2345,
            ),
        )
        self.assertFalse(not_taken.explicit_condition_true)
        self.assertFalse(not_taken.explicit_transfer)
        self.assertEqual(not_taken.next_pc, 6)
        self.assertTrue(not_taken.counter_empty_invalidated)
        self.assertIsNone(not_taken.state.counter.value)

    def test_return_ce_checks_without_decrementing(self) -> None:
        loaded = apply_sequencer_slice_cycle(
            SequencerSliceState(),
            SequencerSliceInputs(
                counter_load=True,
                counter_load_value=2,
            ),
        )
        called = apply_sequencer_slice_cycle(
            loaded.state,
            SequencerSliceInputs(
                pc=0x0100,
                explicit_flow=ExplicitFlow.CALL,
                explicit_condition=15,
                explicit_target=0x0200,
            ),
        )
        returned = apply_sequencer_slice_cycle(
            called.state,
            SequencerSliceInputs(
                pc=0x0200,
                explicit_flow=ExplicitFlow.RETURN,
                explicit_condition=14,
            ),
        )
        self.assertTrue(returned.explicit_transfer)
        self.assertEqual(returned.next_pc, 0x0101)
        self.assertEqual(returned.state.counter.value, 2)
        self.assertFalse(returned.counter_test)
        self.assertFalse(returned.counter_decremented)

    def test_conditional_call_ce_is_flagged_and_holds_state(self) -> None:
        state = SequencerSliceState(counter=CounterState(2))
        result = apply_sequencer_slice_cycle(
            state,
            SequencerSliceInputs(
                pc=7,
                explicit_flow=ExplicitFlow.CALL,
                explicit_condition=14,
                explicit_target=0x1000,
            ),
        )
        self.assertFalse(result.boundary_valid)
        self.assertTrue(result.unsupported_call_ce)
        self.assertEqual(result.next_pc, 8)
        self.assertEqual(result.state, state)

    def test_automatic_counter_collision_is_flagged_and_atomic(self) -> None:
        state = SequencerSliceState(
            counter=CounterState(1),
            stacks=SequencerStacksState(
                pc_entries=(3,),
                loop_entries=((14 << 14) | 5,),
            ),
        )
        result = apply_sequencer_slice_cycle(
            state,
            SequencerSliceInputs(
                pc=5,
                counter_load=True,
                counter_load_value=9,
            ),
        )
        self.assertFalse(result.boundary_valid)
        self.assertTrue(result.integration_conflict)
        self.assertEqual(result.state, state)
        self.assertFalse(result.loop_exit)

    def test_empty_manual_count_pop_preserves_unresolved_counter_state(self) -> None:
        state = SequencerSliceState(counter=CounterState(7))
        result = apply_sequencer_slice_cycle(
            state,
            SequencerSliceInputs(count_manual_pop=True),
        )
        self.assertTrue(result.boundary_valid)
        self.assertEqual(result.state, state)
        self.assertTrue(result.count_stack_pop)

    def test_invalid_widths_and_flow_fail_closed(self) -> None:
        for name in (
            "pc",
            "do_end",
            "explicit_target",
            "counter_load_value",
        ):
            values = {name: 0x4000}
            with self.assertRaises(ValueError):
                SequencerSliceInputs(**values)
        with self.assertRaises(ValueError):
            SequencerSliceInputs(do_condition=16)
        with self.assertRaises(ValueError):
            SequencerSliceInputs(explicit_condition=-1)
        with self.assertRaises(ValueError):
            SequencerSliceInputs(explicit_flow=4)

    def test_randomized_state_invariants(self) -> None:
        rng = random.Random(0x21005E)
        state = SequencerSliceState()
        for index in range(20_000):
            flow = ExplicitFlow(rng.randrange(4))
            inputs = SequencerSliceInputs(
                reset=bool(index and index % 4093 == 0),
                pc=rng.randrange(1 << 14),
                do_until=bool(rng.randrange(16) == 0),
                do_end=rng.randrange(1 << 14),
                do_condition=rng.randrange(16),
                explicit_flow=flow,
                explicit_condition=rng.randrange(16),
                explicit_target=rng.randrange(1 << 14),
                counter_load=bool(rng.randrange(12) == 0),
                counter_load_value=rng.randrange(1 << 14),
                pc_manual_pop=bool(rng.randrange(32) == 0),
                count_manual_pop=bool(rng.randrange(32) == 0),
                loop_manual_pop=bool(rng.randrange(32) == 0),
                az=bool(rng.getrandbits(1)),
                an=bool(rng.getrandbits(1)),
                av=bool(rng.getrandbits(1)),
                ac=bool(rng.getrandbits(1)),
                as_flag=bool(rng.getrandbits(1)),
                mv=bool(rng.getrandbits(1)),
            )
            result = apply_sequencer_slice_cycle(state, inputs)
            self.assertLessEqual(len(result.state.stacks.pc_entries), 16)
            self.assertLessEqual(len(result.state.stacks.count_entries), 4)
            self.assertLessEqual(len(result.state.stacks.loop_entries), 4)
            if not result.boundary_valid and not inputs.reset:
                self.assertEqual(result.state, state)
            self.assertFalse(result.loop_back and result.loop_exit)
            state = result.state


if __name__ == "__main__":
    unittest.main()
