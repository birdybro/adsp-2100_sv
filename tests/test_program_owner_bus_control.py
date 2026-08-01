from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    BusControlMode,
    BusControlState,
    ExactWord,
    LogicalPhase,
    ProgramBusOwner,
    ProgramBusRequest,
    ProgramOwnerBusControlState,
    apply_program_owner_bus_control_cycle,
)


ROOT = Path(__file__).resolve().parents[1]


class ProgramOwnerBusControlTests(unittest.TestCase):
    def test_machine_readable_composition_contract(self) -> None:
        contract = json.loads(
            (ROOT / "docs/generated/adsp2100_program_owner_bus_control.yaml")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertIn("COMPLETES", contract["request_effect"])
        self.assertIn("STATE_8", contract["resume_effect"])
        self.assertIn(
            "ARCHITECTURAL_CLIENT_ATTACHMENT",
            contract["excluded_claims"],
        )

    def test_recognized_br_finishes_active_owner_and_blocks_next_issue(
        self,
    ) -> None:
        issued = apply_program_owner_bus_control_cycle(
            ProgramOwnerBusControlState.reset(),
            phase=LogicalPhase.STATE_8,
            type13_request=ProgramBusRequest.data_read(0x123),
        )
        self.assertTrue(issued.owner_bus.type13_accepted)
        state = issued.state
        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = apply_program_owner_bus_control_cycle(
                state, phase=phase, br_n=False
            ).state
        recognized = apply_program_owner_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(recognized.control.request_recognized)
        self.assertTrue(recognized.owner_bus.bus.address_output_enable)
        self.assertTrue(recognized.owner_bus.bus.control_output_enable)
        state = recognized.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = apply_program_owner_bus_control_cycle(
                state, phase=phase, br_n=False
            ).state
        completed = apply_program_owner_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            br_n=False,
            pmd_read_data=ExactWord(24, 0x123456),
        )
        self.assertTrue(completed.owner_bus.type13_completion)
        blocked = apply_program_owner_bus_control_cycle(
            completed.state,
            phase=LogicalPhase.STATE_8,
            br_n=False,
            fetch_request=ProgramBusRequest.fetch(0x124),
        )
        self.assertTrue(blocked.request_blocked)
        self.assertFalse(blocked.request_ready)
        self.assertEqual(
            blocked.owner_bus.accepted_owner, ProgramBusOwner.NONE
        )
        self.assertFalse(blocked.state.owner_bus.bus.active)

    def test_grant_masks_all_shared_pm_drivers(self) -> None:
        state = ProgramOwnerBusControlState(
            control=BusControlState(BusControlMode.GRANTED)
        )
        visible = apply_program_owner_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_4,
            br_n=False,
            type5_request=ProgramBusRequest.data_write(2, 3),
        )
        self.assertFalse(visible.native_bg_n)
        self.assertTrue(visible.native_bus_relinquished)
        self.assertTrue(visible.request_blocked)
        self.assertFalse(visible.owner_bus.bus.address_output_enable)
        self.assertFalse(visible.owner_bus.bus.control_output_enable)
        self.assertFalse(visible.owner_bus.bus.data_output_enable)

    def test_release_accepts_one_held_owner_at_resume_boundary(self) -> None:
        state = ProgramOwnerBusControlState(
            control=BusControlState(BusControlMode.GRANTED)
        )
        release = apply_program_owner_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=True
        )
        self.assertTrue(release.control.release_recognized)
        state = release.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            held = apply_program_owner_bus_control_cycle(
                state,
                phase=phase,
                br_n=True,
                type5_request=ProgramBusRequest.data_read(7),
            )
            self.assertTrue(held.request_blocked)
            state = held.state
        released = apply_program_owner_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=True
        )
        self.assertTrue(released.control.grant_release_event)
        state = released.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
        ):
            held = apply_program_owner_bus_control_cycle(
                state,
                phase=phase,
                br_n=True,
                type5_request=ProgramBusRequest.data_read(7),
            )
            self.assertTrue(held.request_blocked)
            state = held.state
        resumed = apply_program_owner_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            br_n=True,
            type5_request=ProgramBusRequest.data_read(7),
        )
        self.assertTrue(resumed.control.resume_event)
        self.assertFalse(resumed.control.instruction_issue_inhibit)
        self.assertTrue(resumed.request_ready)
        self.assertTrue(resumed.owner_bus.type5_accepted)

    def test_resume_collision_remains_fail_closed(self) -> None:
        state = ProgramOwnerBusControlState(
            control=BusControlState(BusControlMode.REACQUIRE)
        )
        result = apply_program_owner_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            br_n=True,
            fetch_request=ProgramBusRequest.fetch(1),
            type13_request=ProgramBusRequest.data_read(2),
        )
        self.assertTrue(result.control.resume_event)
        self.assertTrue(result.owner_bus.request_conflict)
        self.assertEqual(result.owner_bus.accepted_owner, ProgramBusOwner.NONE)

    def test_reset_time_native_grant_masks_pm_and_clears_state(self) -> None:
        state = apply_program_owner_bus_control_cycle(
            ProgramOwnerBusControlState.reset(),
            phase=LogicalPhase.STATE_8,
            fetch_request=ProgramBusRequest.fetch(4),
        ).state
        reset = apply_program_owner_bus_control_cycle(
            state,
            reset=True,
            phase=LogicalPhase.STATE_4,
            br_n=False,
        )
        self.assertFalse(reset.native_bg_n)
        self.assertTrue(reset.native_bus_relinquished)
        self.assertFalse(reset.owner_bus.bus.address_output_enable)
        self.assertFalse(reset.owner_bus.bus.control_output_enable)
        self.assertEqual(reset.state, ProgramOwnerBusControlState.reset())


if __name__ == "__main__":
    unittest.main()
