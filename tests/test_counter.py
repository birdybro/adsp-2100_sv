from __future__ import annotations

import json
from pathlib import Path
import random
import unittest

from sim.reference_models.adsp2100_model import (
    COUNTER_MASK,
    CounterInputs,
    CounterState,
    apply_counter_cycle,
)


ROOT = Path(__file__).resolve().parents[1]


class CounterMetadataTests(unittest.TestCase):
    def test_original_counter_contract_is_machine_readable(self) -> None:
        metadata = json.loads(
            (ROOT / "docs/generated/adsp2100_counter.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(metadata["device"], "ADSP-2100")
        self.assertEqual(metadata["counter"]["width"], 14)
        self.assertEqual(metadata["counter"]["reset_valid"], False)
        self.assertEqual(metadata["counter"]["ce_asserted_value"], 1)
        self.assertEqual(
            metadata["counter"]["condition_sample_boundary"],
            "BEGINNING_OF_PROCESSOR_CYCLE",
        )
        self.assertEqual(
            metadata["counter"]["update_boundary"],
            "END_OF_PROCESSOR_CYCLE",
        )
        self.assertEqual(
            metadata["test_contexts"]["CONDITIONAL_CALL"],
            "UNRESOLVED_OQ_012",
        )


class CounterModelTests(unittest.TestCase):
    def test_reset_invalidates_without_inventing_a_value(self) -> None:
        result = apply_counter_cycle(
            CounterState(0x1234),
            CounterInputs(reset=True, load=True, load_value=7),
        )
        self.assertIsNone(result.state.value)
        self.assertFalse(result.condition_valid)
        self.assertFalse(result.count_stack_push)

    def test_first_load_does_not_push_invalid_reset_count(self) -> None:
        result = apply_counter_cycle(
            CounterState(),
            CounterInputs(load=True, load_value=3),
        )
        self.assertEqual(result.state.value, 3)
        self.assertFalse(result.count_stack_push)

        nested = apply_counter_cycle(
            result.state,
            CounterInputs(load=True, load_value=9),
        )
        self.assertEqual(nested.state.value, 9)
        self.assertTrue(nested.count_stack_push)
        self.assertEqual(nested.count_stack_push_value, 3)

    def test_ce_samples_before_post_decrement_for_exact_n_iterations(self) -> None:
        state = CounterState(3)
        observations: list[tuple[bool, bool, int | None]] = []
        for _ in range(3):
            result = apply_counter_cycle(state, CounterInputs(ce_test=True))
            observations.append(
                (
                    result.counter_expired,
                    result.not_counter_expired,
                    result.state.value,
                )
            )
            state = result.state
        self.assertEqual(
            observations,
            [
                (False, True, 2),
                (False, True, 1),
                (True, False, None),
            ],
        )

    def test_true_ce_restores_outer_count_and_requests_pop(self) -> None:
        result = apply_counter_cycle(
            CounterState(1),
            CounterInputs(
                ce_test=True,
                count_stack_top=0x2345,
                count_stack_top_valid=True,
            ),
        )
        self.assertTrue(result.counter_expired)
        self.assertTrue(result.count_stack_pop)
        self.assertTrue(result.restored)
        self.assertEqual(result.state.value, 0x2345)

    def test_true_ce_with_empty_stack_invalidates_counter(self) -> None:
        result = apply_counter_cycle(
            CounterState(1),
            CounterInputs(ce_test=True),
        )
        self.assertTrue(result.count_stack_pop)
        self.assertTrue(result.empty_ce_invalidated)
        self.assertIsNone(result.state.value)

    def test_zero_is_not_expired_and_decrements_at_register_width(self) -> None:
        result = apply_counter_cycle(
            CounterState(0),
            CounterInputs(ce_test=True),
        )
        self.assertTrue(result.not_counter_expired)
        self.assertTrue(result.decremented)
        self.assertEqual(result.state.value, COUNTER_MASK)

    def test_manual_valid_pop_restores_and_empty_pop_stays_unresolved(self) -> None:
        restored = apply_counter_cycle(
            CounterState(7),
            CounterInputs(
                manual_pop=True,
                count_stack_top=0x3456,
                count_stack_top_valid=True,
            ),
        )
        self.assertTrue(restored.count_stack_pop)
        self.assertTrue(restored.restored)
        self.assertEqual(restored.state.value, 0x3456)

        unresolved = apply_counter_cycle(
            restored.state,
            CounterInputs(manual_pop=True),
        )
        self.assertTrue(unresolved.count_stack_pop)
        self.assertTrue(unresolved.empty_manual_pop)
        self.assertEqual(unresolved.state, restored.state)

    def test_invalid_ce_test_is_flagged_without_a_condition_claim(self) -> None:
        result = apply_counter_cycle(
            CounterState(),
            CounterInputs(ce_test=True),
        )
        self.assertFalse(result.condition_valid)
        self.assertFalse(result.counter_expired)
        self.assertFalse(result.not_counter_expired)
        self.assertTrue(result.invalid_ce_test)
        self.assertFalse(result.count_stack_pop)

    def test_multiple_counter_actions_fail_closed(self) -> None:
        state = CounterState(0x1234)
        result = apply_counter_cycle(
            state,
            CounterInputs(
                load=True,
                load_value=2,
                ce_test=True,
                manual_pop=True,
                count_stack_top=4,
                count_stack_top_valid=True,
            ),
        )
        self.assertTrue(result.write_conflict)
        self.assertEqual(result.state, state)
        self.assertFalse(result.count_stack_push)
        self.assertFalse(result.count_stack_pop)

    def test_width_violations_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            CounterState(0x4000)
        with self.assertRaises(ValueError):
            CounterInputs(load_value=-1)
        with self.assertRaises(ValueError):
            CounterInputs(count_stack_top=0x4000)

    def test_randomized_state_and_event_invariants(self) -> None:
        rng = random.Random(0x2100CE)
        state = CounterState()
        for index in range(20_000):
            if index and index % 4093 == 0:
                inputs = CounterInputs(reset=True)
            else:
                action = rng.randrange(4)
                inputs = CounterInputs(
                    load=action == 1,
                    load_value=rng.randrange(1 << 14),
                    ce_test=action == 2,
                    manual_pop=action == 3,
                    count_stack_top=rng.randrange(1 << 14),
                    count_stack_top_valid=bool(rng.getrandbits(1)),
                )
            result = apply_counter_cycle(state, inputs)
            if result.state.value is not None:
                self.assertLessEqual(result.state.value, COUNTER_MASK)
            self.assertFalse(
                result.counter_expired and result.not_counter_expired
            )
            self.assertEqual(
                result.condition_valid,
                result.counter_expired or result.not_counter_expired,
            )
            self.assertFalse(result.decremented and result.restored)
            state = result.state


if __name__ == "__main__":
    unittest.main()
