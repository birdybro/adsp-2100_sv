from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    ExactWord,
    InterruptState,
    LogicalPhase,
    UNKNOWN,
    apply_interrupt_cycle,
)


ROOT = Path(__file__).resolve().parents[1]


def _sample(
    state: InterruptState,
    *,
    irq_n: int,
    icntl: int | None,
    imask: int | None,
    service_allowed: bool = True,
):
    return apply_interrupt_cycle(
        state,
        phase=LogicalPhase.STATE_7,
        irq_n=irq_n,
        icntl=UNKNOWN if icntl is None else ExactWord(5, icntl),
        imask=UNKNOWN if imask is None else ExactWord(4, imask),
        service_allowed=service_allowed,
    )


class InterruptTests(unittest.TestCase):
    def test_contract_is_original_four_pin_boundary(self) -> None:
        contract = json.loads(
            (ROOT / "docs/generated/adsp2100_interrupts.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(contract["pins"], ["IRQ0_n", "IRQ1_n", "IRQ2_n", "IRQ3_n"])
        self.assertEqual(contract["priority_high_to_low"], [3, 2, 1, 0])
        self.assertEqual(contract["vectors"], [0, 1, 2, 3])
        self.assertTrue(
            any(
                boundary.startswith("OQ-025")
                for boundary in contract["provisional_boundaries"]
            )
        )

    def test_only_enabled_state_seven_samples(self) -> None:
        state = InterruptState.reset()
        for phase in LogicalPhase:
            if phase is LogicalPhase.STATE_7:
                continue
            result = apply_interrupt_cycle(
                state,
                phase=phase,
                irq_n=0,
                icntl=ExactWord(5, 0),
                imask=ExactWord(4, 0xF),
            )
            self.assertFalse(result.sample_event)
            self.assertEqual(result.state, state)
        held = apply_interrupt_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            phase_advance=False,
            irq_n=0,
            icntl=ExactWord(5, 0),
            imask=ExactWord(4, 0xF),
        )
        self.assertFalse(held.sample_event)
        self.assertEqual(held.state, state)

    def test_level_request_must_remain_active_until_service(self) -> None:
        baseline = _sample(
            InterruptState.reset(), irq_n=0xF, icntl=0, imask=1
        )
        blocked = _sample(
            baseline.state,
            irq_n=0xE,
            icntl=0,
            imask=1,
            service_allowed=False,
        )
        self.assertEqual(blocked.sampled_requests, 1)
        self.assertFalse(blocked.recognition_event)
        removed = _sample(blocked.state, irq_n=0xF, icntl=0, imask=1)
        self.assertFalse(removed.recognition_event)
        active = _sample(removed.state, irq_n=0xE, icntl=0, imask=1)
        self.assertTrue(active.recognition_event)
        self.assertEqual(active.recognized_level, 0)
        self.assertEqual(active.vector_address, ExactWord(14, 0))

    def test_edge_request_latches_while_service_is_blocked(self) -> None:
        baseline = _sample(
            InterruptState.reset(), irq_n=0xF, icntl=1, imask=1
        )
        edge = _sample(
            baseline.state,
            irq_n=0xE,
            icntl=1,
            imask=1,
            service_allowed=False,
        )
        self.assertEqual(edge.state.edge_pending, 1)
        released = _sample(edge.state, irq_n=0xF, icntl=1, imask=1)
        self.assertTrue(released.recognition_event)
        self.assertEqual(released.state.edge_pending, 0)

    def test_masked_edge_remains_pending_until_enabled(self) -> None:
        baseline = _sample(
            InterruptState.reset(), irq_n=0xF, icntl=4, imask=0
        )
        masked = _sample(baseline.state, irq_n=0xB, icntl=4, imask=0)
        self.assertFalse(masked.recognition_event)
        self.assertEqual(masked.state.edge_pending, 4)
        enabled = _sample(masked.state, irq_n=0xF, icntl=4, imask=4)
        self.assertTrue(enabled.recognition_event)
        self.assertEqual(enabled.recognized_level, 2)
        self.assertEqual(enabled.vector_address, ExactWord(14, 2))

    def test_irq3_has_fixed_highest_priority(self) -> None:
        baseline = _sample(
            InterruptState.reset(), irq_n=0xF, icntl=0, imask=0xF
        )
        first = _sample(baseline.state, irq_n=0, icntl=0, imask=0xF)
        self.assertTrue(first.recognition_event)
        self.assertEqual(first.recognized_level, 3)
        second = _sample(first.state, irq_n=0x7, icntl=0, imask=0xF)
        self.assertEqual(second.recognized_level, 3)

    def test_mixed_edge_and_level_priority_preserves_lower_edge(self) -> None:
        # IRQ0 edge, IRQ2 level. Both become active together; IRQ2 wins while
        # the lower edge remains latched for the next eligible sample.
        baseline = _sample(
            InterruptState.reset(), irq_n=0xF, icntl=1, imask=0x5
        )
        first = _sample(baseline.state, irq_n=0xA, icntl=1, imask=0x5)
        self.assertEqual(first.recognized_level, 2)
        self.assertEqual(first.state.edge_pending, 1)
        second = _sample(first.state, irq_n=0xF, icntl=1, imask=1)
        self.assertEqual(second.recognized_level, 0)
        self.assertEqual(second.state.edge_pending, 0)

    def test_unknown_configuration_fails_closed(self) -> None:
        result = _sample(
            InterruptState.reset(), irq_n=0, icntl=None, imask=0xF
        )
        self.assertTrue(result.configuration_invalid)
        self.assertFalse(result.recognition_event)
        self.assertEqual(result.sampled_requests, 0)

    def test_first_post_reset_sample_is_a_provisional_baseline(self) -> None:
        first = _sample(
            InterruptState.reset(), irq_n=0xE, icntl=1, imask=1
        )
        self.assertTrue(first.reset_baseline_provisional)
        self.assertFalse(first.recognition_event)
        self.assertEqual(first.state.edge_pending, 0)
        high = _sample(first.state, irq_n=0xF, icntl=1, imask=1)
        low = _sample(high.state, irq_n=0xE, icntl=1, imask=1)
        self.assertTrue(low.recognition_event)


if __name__ == "__main__":
    unittest.main()
