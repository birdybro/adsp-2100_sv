from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model.model import ExactWord, UNKNOWN
from sim.reference_models.adsp2100_model.phase import LogicalPhase
from sim.reference_models.adsp2100_model.program_bus import ProgramBusRequest
from sim.reference_models.adsp2100_model.program_owner_bus import (
    ProgramBusOwner,
    ProgramOwnerBusState,
    apply_program_owner_bus_cycle,
)


class ProgramOwnerBusTests(unittest.TestCase):
    def test_machine_readable_contract_is_fail_closed(self) -> None:
        contract = json.loads(
            Path("docs/generated/adsp2100_program_owner_bus.yaml").read_text()
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(
            contract["selection_policy"], "ACCEPT_EXACTLY_ONE_REQUEST"
        )
        self.assertEqual(
            contract["collision_policy"], "FAIL_CLOSED_NO_PRIORITY_CLAIM"
        )
        self.assertIn("FULL_CORE_ATTACHMENT", contract["excluded_claims"])

    def test_each_requester_can_own_the_single_bus(self) -> None:
        cases = (
            ("fetch_request", ProgramBusOwner.FETCH, False),
            ("type5_request", ProgramBusOwner.TYPE5_PM_DATA, True),
            ("type13_request", ProgramBusOwner.TYPE13_PM_DATA, True),
        )
        for argument, owner, data_access in cases:
            with self.subTest(owner=owner):
                result = apply_program_owner_bus_cycle(
                    ProgramOwnerBusState.reset(),
                    phase=LogicalPhase.STATE_8,
                    **{argument: ProgramBusRequest(ExactWord(14, int(owner)), data_access)},
                )
                self.assertEqual(result.accepted_owner, owner)
                self.assertEqual(result.state.owner, owner)
                self.assertTrue(result.state.bus.active)
                self.assertEqual(result.state.bus.data_access, data_access)

    def test_collision_rejects_all_requesters_without_priority(self) -> None:
        result = apply_program_owner_bus_cycle(
            ProgramOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            fetch_request=ProgramBusRequest.fetch(1),
            type5_request=ProgramBusRequest.data_read(2),
        )
        self.assertTrue(result.request_conflict)
        self.assertEqual(result.accepted_owner, ProgramBusOwner.NONE)
        self.assertFalse(result.bus.request_accepted)
        self.assertFalse(result.state.bus.active)
        self.assertEqual(result.state.owner, ProgramBusOwner.NONE)

    def test_owner_is_retained_and_only_it_receives_completion(self) -> None:
        issued = apply_program_owner_bus_cycle(
            ProgramOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            type5_request=ProgramBusRequest.data_read(0x123),
        ).state
        held = apply_program_owner_bus_cycle(
            issued, phase=LogicalPhase.STATE_7, phase_advance=False
        )
        self.assertEqual(held.state.owner, ProgramBusOwner.TYPE5_PM_DATA)
        self.assertFalse(held.type5_completion)
        done = apply_program_owner_bus_cycle(
            held.state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xA5A5A5),
        )
        self.assertTrue(done.type5_completion)
        self.assertFalse(done.fetch_completion)
        self.assertFalse(done.type13_completion)
        self.assertEqual(done.completion_owner, ProgramBusOwner.TYPE5_PM_DATA)

    def test_out_of_phase_request_is_rejected_and_cannot_replace_owner(self) -> None:
        issued = apply_program_owner_bus_cycle(
            ProgramOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            fetch_request=ProgramBusRequest.fetch(7),
        ).state
        result = apply_program_owner_bus_cycle(
            issued,
            phase=LogicalPhase.STATE_3,
            type13_request=ProgramBusRequest.data_read(9),
        )
        self.assertTrue(result.request_out_of_phase)
        self.assertFalse(result.type13_accepted)
        self.assertEqual(result.state.owner, ProgramBusOwner.FETCH)
        self.assertEqual(result.state.bus.address, ExactWord(14, 7))

    def test_relinquish_masks_bus_and_preserves_owner(self) -> None:
        issued = apply_program_owner_bus_cycle(
            ProgramOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            type13_request=ProgramBusRequest.data_write(4, 5),
        ).state
        result = apply_program_owner_bus_cycle(
            issued,
            phase=LogicalPhase.STATE_6,
            bus_relinquished=True,
            type5_request=ProgramBusRequest.data_read(8),
        )
        self.assertEqual(result.state, issued)
        self.assertTrue(result.request_out_of_phase)
        self.assertFalse(result.bus.control_output_enable)
        self.assertTrue(result.bus.pms_n)

    def test_back_to_back_boundary_can_change_owner(self) -> None:
        first = apply_program_owner_bus_cycle(
            ProgramOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            fetch_request=ProgramBusRequest.fetch(1),
        ).state
        second = apply_program_owner_bus_cycle(
            first,
            phase=LogicalPhase.STATE_8,
            type5_request=ProgramBusRequest.data_read(2),
        )
        self.assertFalse(second.bus.pms_n)
        self.assertTrue(second.type5_accepted)
        self.assertEqual(second.state.owner, ProgramBusOwner.TYPE5_PM_DATA)
        self.assertEqual(second.state.bus.address, ExactWord(14, 2))

    def test_unknown_descriptor_and_reset_remain_explicit(self) -> None:
        issued = apply_program_owner_bus_cycle(
            ProgramOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            type13_request=ProgramBusRequest(
                address=UNKNOWN,
                data_access=True,
                write=True,
                write_data=UNKNOWN,
            ),
        )
        self.assertIs(issued.state.bus.address, UNKNOWN)
        self.assertIs(issued.state.bus.write_data, UNKNOWN)
        reset = apply_program_owner_bus_cycle(
            issued.state, reset=True, phase=LogicalPhase.STATE_5
        )
        self.assertEqual(reset.state, ProgramOwnerBusState.reset())
        self.assertEqual(reset.state.owner, ProgramBusOwner.NONE)


if __name__ == "__main__":
    unittest.main()
