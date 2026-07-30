from __future__ import annotations

import json
from pathlib import Path
import random
import unittest

from sim.reference_models.adsp2100_model import (
    ExactWord,
    STATUS_STACK_DEPTH,
    StatusStackCycleInputs,
    StatusStackEntry,
    StatusStackOperation,
    StatusStackState,
    apply_status_stack_cycle,
)


ROOT = Path(__file__).resolve().parents[1]


def entry(value: int) -> StatusStackEntry:
    return StatusStackEntry.from_word(ExactWord(16, value))


class StatusStackMetadataTests(unittest.TestCase):
    def test_original_status_stack_is_four_by_sixteen(self) -> None:
        data = json.loads(
            (ROOT / "docs/generated/adsp2100_status_registers.yaml").read_text(
                encoding="utf-8"
            )
        )
        stack = data["stack_architecture"]["STATUS"]
        self.assertEqual(stack["depth"], 4)
        self.assertEqual(stack["width"], 16)
        self.assertEqual(stack["stored_register_order"], ["ASTAT", "MSTAT", "IMASK"])
        self.assertEqual(stack["control_codes"], [0, 1, 2, 3])


class StatusStackModelTests(unittest.TestCase):
    def test_reset_clears_pointer_and_sticky_overflow(self) -> None:
        state = StatusStackState(tuple(entry(index) for index in range(4)), True)
        result = apply_status_stack_cycle(
            state,
            StatusStackCycleInputs(
                reset=True,
                operation=StatusStackOperation.PUSH,
                push_entry=entry(0xFFFF),
            ),
        )
        self.assertEqual(result.state, StatusStackState())
        self.assertTrue(result.state.empty)
        self.assertEqual(result.state.sstat_fragment, 0x10)

    def test_both_no_change_codes_preserve_state(self) -> None:
        state = StatusStackState((entry(0x1234),), True)
        for operation in (
            StatusStackOperation.NO_CHANGE_ZERO,
            StatusStackOperation.NO_CHANGE_ONE,
        ):
            result = apply_status_stack_cycle(
                state,
                StatusStackCycleInputs(operation=operation),
            )
            self.assertEqual(result.state, state)
            self.assertIsNone(result.pop_entry)

    def test_four_entries_pop_in_lifo_order(self) -> None:
        state = StatusStackState()
        values = (0x1234, 0xABCD, 0x5678, 0x9ABC)
        for value in values:
            result = apply_status_stack_cycle(
                state,
                StatusStackCycleInputs(
                    operation=StatusStackOperation.PUSH,
                    push_entry=entry(value),
                ),
            )
            self.assertTrue(result.push_accepted)
            state = result.state
        self.assertEqual(state.depth, STATUS_STACK_DEPTH)

        popped: list[StatusStackEntry] = []
        for _ in values:
            result = apply_status_stack_cycle(
                state,
                StatusStackCycleInputs(operation=StatusStackOperation.POP),
            )
            self.assertIsNotNone(result.pop_entry)
            popped.append(result.pop_entry)
            state = result.state
        self.assertEqual(popped, [entry(value) for value in reversed(values)])
        self.assertTrue(state.empty)

    def test_overflow_drops_newest_and_sticks_until_reset(self) -> None:
        accepted = tuple(entry(index) for index in range(4))
        state = StatusStackState(accepted)
        overflow = apply_status_stack_cycle(
            state,
            StatusStackCycleInputs(
                operation=StatusStackOperation.PUSH,
                push_entry=entry(0xFFFF),
            ),
        )
        self.assertEqual(overflow.state.entries, accepted)
        self.assertTrue(overflow.state.overflow)
        self.assertTrue(overflow.overflow_event)
        self.assertFalse(overflow.push_accepted)

        state = overflow.state
        for _ in range(4):
            state = apply_status_stack_cycle(
                state,
                StatusStackCycleInputs(operation=StatusStackOperation.POP),
            ).state
        self.assertTrue(state.empty)
        self.assertTrue(state.overflow)
        self.assertEqual(state.sstat_fragment, 0x30)

    def test_empty_pop_is_invalid_and_preserves_state(self) -> None:
        state = StatusStackState()
        result = apply_status_stack_cycle(
            state,
            StatusStackCycleInputs(operation=StatusStackOperation.POP),
        )
        self.assertEqual(result.state, state)
        self.assertIsNone(result.pop_entry)
        self.assertTrue(result.empty_pop)

    def test_operation_and_push_entry_contract_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            StatusStackCycleInputs(operation=StatusStackOperation.PUSH)
        with self.assertRaises(ValueError):
            StatusStackCycleInputs(push_entry=entry(0))
        with self.assertRaises(ValueError):
            StatusStackCycleInputs(operation=4)
        with self.assertRaises(ValueError):
            StatusStackState(tuple(entry(index) for index in range(5)))

    def test_randomized_depth_and_overflow_invariants(self) -> None:
        rng = random.Random(0x210021)
        state = StatusStackState()
        overflow_seen = False
        for _ in range(20_000):
            operation = rng.choice(tuple(StatusStackOperation))
            inputs = StatusStackCycleInputs(
                operation=operation,
                push_entry=(
                    entry(rng.randrange(1 << 16))
                    if operation is StatusStackOperation.PUSH
                    else None
                ),
            )
            result = apply_status_stack_cycle(state, inputs)
            self.assertLessEqual(result.state.depth, STATUS_STACK_DEPTH)
            self.assertEqual(result.state.empty, result.state.depth == 0)
            overflow_seen |= result.overflow_event
            if overflow_seen:
                self.assertTrue(result.state.overflow)
            state = result.state


if __name__ == "__main__":
    unittest.main()
