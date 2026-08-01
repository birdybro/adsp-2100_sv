from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    LogicalPhase,
    ResetPhaseState,
    apply_reset_phase_cycle,
)


class ResetPhaseTests(unittest.TestCase):
    def test_machine_readable_original_reset_contract(self) -> None:
        contract = json.loads(
            Path("docs/generated/adsp2100_reset_phase.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(contract["minimum_reset_clkin_cycles"], 4)
        self.assertEqual(contract["reset_hold_phase"], "STATE_4")
        self.assertEqual(len(contract["release_sequence"]), 2)
        self.assertIn("FAIL_CLOSED", contract["short_reset_behavior"])

    def test_reset_is_recognized_only_on_enabled_rising_edge(self) -> None:
        state = ResetPhaseState()
        for enabled, rising in ((False, True), (True, False)):
            result = apply_reset_phase_cycle(
                state,
                edge_enable=enabled,
                clkin_rising=rising,
                reset_pin=True,
            )
            self.assertFalse(result.reset_recognized)
            self.assertFalse(result.phase_valid)
        result = apply_reset_phase_cycle(
            state,
            edge_enable=True,
            clkin_rising=True,
            reset_pin=True,
        )
        self.assertTrue(result.reset_recognized)
        self.assertTrue(result.architectural_reset)
        self.assertEqual(result.phase_after, LogicalPhase.STATE_4)
        self.assertEqual(result.state.asserted_rising_edges, 1)

    def test_four_cycles_and_two_release_edges_are_exact(self) -> None:
        state = ResetPhaseState()
        for count in range(1, 5):
            result = apply_reset_phase_cycle(
                state,
                clkin_rising=True,
                reset_pin=True,
            )
            state = result.state
            self.assertEqual(state.asserted_rising_edges, count)
            self.assertTrue(state.reset_active)
            self.assertEqual(state.phase, LogicalPhase.STATE_4)
            self.assertFalse(result.clkout)
        first = apply_reset_phase_cycle(
            state,
            clkin_rising=True,
            reset_pin=False,
        )
        self.assertTrue(first.release_first_rising)
        self.assertFalse(first.release_event)
        self.assertTrue(first.architectural_reset)
        self.assertFalse(first.phase_advance)
        self.assertEqual(first.phase_after, LogicalPhase.STATE_4)
        second = apply_reset_phase_cycle(
            first.state,
            clkin_rising=True,
            reset_pin=False,
        )
        self.assertFalse(second.architectural_reset)
        self.assertTrue(second.release_event)
        self.assertTrue(second.phase_advance)
        self.assertEqual(second.phase_before, LogicalPhase.STATE_4)
        self.assertEqual(second.phase_after, LogicalPhase.STATE_5)

    def test_short_reset_fails_closed_until_a_new_valid_assertion(self) -> None:
        state = ResetPhaseState()
        for _ in range(3):
            state = apply_reset_phase_cycle(
                state,
                clkin_rising=True,
                reset_pin=True,
            ).state
        short = apply_reset_phase_cycle(
            state,
            clkin_rising=True,
            reset_pin=False,
        )
        self.assertTrue(short.duration_error)
        self.assertTrue(short.architectural_reset)
        self.assertTrue(short.state.reset_active)
        self.assertEqual(short.phase_after, LogicalPhase.STATE_4)
        restarted = apply_reset_phase_cycle(
            short.state,
            clkin_rising=True,
            reset_pin=True,
        )
        self.assertFalse(restarted.duration_error)
        self.assertEqual(restarted.state.asserted_rising_edges, 1)

    def test_normal_phase_and_clkout_sequence_after_release(self) -> None:
        state = ResetPhaseState()
        for _ in range(4):
            state = apply_reset_phase_cycle(
                state,
                clkin_rising=True,
                reset_pin=True,
            ).state
        state = apply_reset_phase_cycle(
            state,
            clkin_rising=True,
            reset_pin=False,
        ).state
        released = apply_reset_phase_cycle(
            state,
            clkin_rising=True,
            reset_pin=False,
        )
        state = released.state
        expected = (
            (LogicalPhase.STATE_5, False),
            (LogicalPhase.STATE_6, False),
            (LogicalPhase.STATE_7, False),
            (LogicalPhase.STATE_8, True),
            (LogicalPhase.STATE_1, True),
            (LogicalPhase.STATE_2, True),
            (LogicalPhase.STATE_3, True),
            (LogicalPhase.STATE_4, False),
        )
        observations = [(state.phase, released.clkout)]
        for _ in range(7):
            result = apply_reset_phase_cycle(state, edge_enable=True)
            state = result.state
            observations.append((state.phase, result.clkout))
        self.assertEqual(tuple(observations), expected)

    def test_assertion_during_running_phase_returns_to_state_four(self) -> None:
        state = ResetPhaseState(
            initialized=True,
            phase=LogicalPhase.STATE_2,
        )
        falling = apply_reset_phase_cycle(
            state,
            clkin_rising=False,
            reset_pin=True,
        )
        self.assertEqual(falling.phase_after, LogicalPhase.STATE_3)
        recognized = apply_reset_phase_cycle(
            falling.state,
            clkin_rising=True,
            reset_pin=True,
        )
        self.assertTrue(recognized.reset_recognized)
        self.assertEqual(recognized.phase_after, LogicalPhase.STATE_4)
        self.assertTrue(recognized.state.reset_active)


if __name__ == "__main__":
    unittest.main()
