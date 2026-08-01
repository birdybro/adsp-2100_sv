from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    BusControlMode,
    BusControlState,
    LogicalPhase,
    apply_bus_control_cycle,
)


class BusControlTests(unittest.TestCase):
    def test_machine_readable_normal_bus_grant_contract(self) -> None:
        contract = json.loads(
            Path("docs/generated/adsp2100_bus_control.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(contract["pin_polarity"]["BR"], "ACTIVE_LOW")
        self.assertEqual(contract["pin_polarity"]["BG"], "ACTIVE_LOW")
        self.assertIn("STATE_3", contract["normal_request_recognition"])
        self.assertEqual(
            contract["reset_time_path"],
            "SEPARATE_ASYNCHRONOUS_NATIVE_PIN_WRAPPER",
        )

    def test_request_is_recognized_only_at_enabled_state_three(self) -> None:
        state = BusControlState()
        for phase, advance in (
            (LogicalPhase.STATE_2, True),
            (LogicalPhase.STATE_3, False),
        ):
            result = apply_bus_control_cycle(
                state,
                phase=phase,
                phase_advance=advance,
                br_n=False,
            )
            self.assertFalse(result.request_recognized)
            self.assertEqual(result.state, state)
        result = apply_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(result.request_recognized)
        self.assertTrue(result.instruction_issue_inhibit)
        self.assertEqual(result.state.mode, BusControlMode.REQUEST_DELAY)
        self.assertTrue(result.bg_n)

    def test_grant_asserts_one_full_cycle_after_request_recognition(self) -> None:
        recognized = apply_bus_control_cycle(
            BusControlState(),
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        state = recognized.state
        phase = LogicalPhase.STATE_4
        for _ in range(7):
            result = apply_bus_control_cycle(
                state,
                phase=phase,
                br_n=False,
            )
            state = result.state
            self.assertFalse(result.grant_assert_event)
            self.assertFalse(result.bus_relinquished)
            phase = LogicalPhase((int(phase) + 1) & 7)
        grant = apply_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(grant.grant_assert_event)
        self.assertEqual(grant.state.mode, BusControlMode.GRANTED)
        visible = apply_bus_control_cycle(
            grant.state,
            phase=LogicalPhase.STATE_4,
            br_n=False,
        )
        self.assertTrue(visible.bus_relinquished)
        self.assertFalse(visible.bg_n)

    def test_release_waits_full_cycle_then_resumes_at_state_one(self) -> None:
        state = BusControlState(BusControlMode.GRANTED)
        recognized = apply_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=True,
        )
        self.assertTrue(recognized.release_recognized)
        self.assertEqual(recognized.state.mode, BusControlMode.RELEASE_DELAY)
        self.assertTrue(recognized.bus_relinquished)
        state = recognized.state
        phase = LogicalPhase.STATE_4
        for _ in range(7):
            result = apply_bus_control_cycle(
                state,
                phase=phase,
                br_n=True,
            )
            state = result.state
            self.assertFalse(result.grant_release_event)
            phase = LogicalPhase((int(phase) + 1) & 7)
        released = apply_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=True,
        )
        self.assertTrue(released.grant_release_event)
        self.assertEqual(released.state.mode, BusControlMode.REACQUIRE)
        after = apply_bus_control_cycle(
            released.state,
            phase=LogicalPhase.STATE_4,
            br_n=True,
        )
        self.assertTrue(after.bg_n)
        self.assertFalse(after.bus_relinquished)
        self.assertTrue(after.instruction_issue_inhibit)
        state = after.state
        for phase in (
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
        ):
            state = apply_bus_control_cycle(
                state, phase=phase, br_n=True
            ).state
        resumed = apply_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            br_n=True,
        )
        self.assertTrue(resumed.resume_event)
        self.assertFalse(resumed.instruction_issue_inhibit)
        self.assertEqual(resumed.state.mode, BusControlMode.IDLE)

    def test_phase_holds_preserve_every_handshake_state(self) -> None:
        for mode in BusControlMode:
            state = BusControlState(mode)
            held = apply_bus_control_cycle(
                state,
                phase=LogicalPhase.STATE_3,
                phase_advance=False,
                br_n=False,
            )
            self.assertEqual(held.state, state)
            self.assertFalse(held.state_three_boundary)

    def test_invalid_early_withdrawal_and_release_cancel_fail_closed(self) -> None:
        withdrawn = apply_bus_control_cycle(
            BusControlState(BusControlMode.REQUEST_DELAY),
            phase=LogicalPhase.STATE_3,
            br_n=True,
        )
        self.assertTrue(withdrawn.request_withdrawn)
        self.assertEqual(withdrawn.state.mode, BusControlMode.IDLE)
        cancelled = apply_bus_control_cycle(
            BusControlState(BusControlMode.RELEASE_DELAY),
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(cancelled.release_cancelled)
        self.assertEqual(cancelled.state.mode, BusControlMode.GRANTED)

    def test_reset_clears_normal_state_and_flags_async_path_request(self) -> None:
        result = apply_bus_control_cycle(
            BusControlState(BusControlMode.GRANTED),
            reset=True,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertEqual(result.state.mode, BusControlMode.IDLE)
        self.assertTrue(result.bg_n)
        self.assertFalse(result.bus_relinquished)
        self.assertTrue(result.reset_br_request)
        self.assertFalse(result.request_recognized)


if __name__ == "__main__":
    unittest.main()
