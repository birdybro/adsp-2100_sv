from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model.data_bus import DataBusRequest
from sim.reference_models.adsp2100_model.data_owner_bus import (
    DataBusOwner,
    DataOwnerBusState,
    apply_data_owner_bus_cycle,
)
from sim.reference_models.adsp2100_model.model import ExactWord, UNKNOWN
from sim.reference_models.adsp2100_model.phase import LogicalPhase


class DataOwnerBusTests(unittest.TestCase):
    def test_machine_readable_contract_is_fail_closed(self) -> None:
        contract = json.loads(
            Path("docs/generated/adsp2100_data_owner_bus.yaml").read_text()
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(
            contract["selection_policy"], "ACCEPT_EXACTLY_ONE_REQUEST"
        )
        self.assertEqual(
            contract["collision_policy"], "FAIL_CLOSED_NO_PRIORITY_CLAIM"
        )
        self.assertIn("FETCHED_CLIENT_ATTACHMENT", contract["excluded_claims"])

    def test_each_requester_can_own_the_single_bus(self) -> None:
        cases = (
            ("fetched_request", DataBusOwner.FETCHED),
            ("companion_request", DataBusOwner.COMPANION),
        )
        for argument, owner in cases:
            with self.subTest(owner=owner):
                result = apply_data_owner_bus_cycle(
                    DataOwnerBusState.reset(),
                    phase=LogicalPhase.STATE_8,
                    **{argument: DataBusRequest.read(int(owner))},
                )
                self.assertEqual(result.accepted_owner, owner)
                self.assertEqual(result.state.owner, owner)
                self.assertTrue(result.state.bus.active)

    def test_collision_rejects_both_without_priority(self) -> None:
        result = apply_data_owner_bus_cycle(
            DataOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            fetched_request=DataBusRequest.read(1),
            companion_request=DataBusRequest.write_word(2, 3),
        )
        self.assertTrue(result.request_conflict)
        self.assertEqual(result.accepted_owner, DataBusOwner.NONE)
        self.assertFalse(result.bus.request_accepted)
        self.assertFalse(result.state.bus.active)

    def test_wait_extension_retains_owner_and_routes_ack_events(self) -> None:
        state = apply_data_owner_bus_cycle(
            DataOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            fetched_request=DataBusRequest.read(0x123),
        ).state
        low = apply_data_owner_bus_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=False
        )
        self.assertTrue(low.fetched_dmack_sample)
        self.assertTrue(low.fetched_wait_extension)
        self.assertFalse(low.companion_wait_extension)
        self.assertEqual(low.state.owner, DataBusOwner.FETCHED)
        blocked = apply_data_owner_bus_cycle(
            low.state,
            phase=LogicalPhase.STATE_8,
            companion_request=DataBusRequest.read(4),
        )
        self.assertTrue(blocked.request_out_of_phase)
        self.assertEqual(blocked.state.owner, DataBusOwner.FETCHED)
        high = apply_data_owner_bus_cycle(
            blocked.state, phase=LogicalPhase.STATE_6, dm_ack=True
        )
        self.assertTrue(high.fetched_dmack_accepted)
        self.assertEqual(high.state.owner, DataBusOwner.FETCHED)

    def test_only_retained_owner_receives_completion_and_read_sample(self) -> None:
        state = apply_data_owner_bus_cycle(
            DataOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            companion_request=DataBusRequest.read(0x234),
        ).state
        state = apply_data_owner_bus_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=True
        ).state
        done = apply_data_owner_bus_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xA55A),
        )
        self.assertTrue(done.companion_completion)
        self.assertTrue(done.companion_read_sample)
        self.assertFalse(done.fetched_completion)
        self.assertFalse(done.fetched_read_sample)
        self.assertEqual(done.state.bus.read_data, ExactWord(16, 0xA55A))

    def test_write_completion_has_no_read_sample(self) -> None:
        state = apply_data_owner_bus_cycle(
            DataOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            fetched_request=DataBusRequest.write_word(0x55, 0xCAFE),
        ).state
        state = apply_data_owner_bus_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=True
        ).state
        done = apply_data_owner_bus_cycle(
            state, phase=LogicalPhase.STATE_7
        )
        self.assertTrue(done.fetched_completion)
        self.assertFalse(done.fetched_read_sample)
        self.assertTrue(done.state.bus.response_write)

    def test_relinquish_masks_bus_and_preserves_owner(self) -> None:
        state = apply_data_owner_bus_cycle(
            DataOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            companion_request=DataBusRequest.write_word(4, 5),
        ).state
        result = apply_data_owner_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            bus_relinquished=True,
            fetched_request=DataBusRequest.read(8),
        )
        self.assertEqual(result.state, state)
        self.assertTrue(result.request_out_of_phase)
        self.assertFalse(result.bus.control_output_enable)
        self.assertTrue(result.bus.dms_n)

    def test_back_to_back_boundary_can_change_owner(self) -> None:
        state = apply_data_owner_bus_cycle(
            DataOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            fetched_request=DataBusRequest.read(1),
        ).state
        state = apply_data_owner_bus_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=True
        ).state
        state = apply_data_owner_bus_cycle(
            state, phase=LogicalPhase.STATE_7, dmd_read_data=ExactWord(16, 7)
        ).state
        result = apply_data_owner_bus_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            companion_request=DataBusRequest.read(2),
        )
        self.assertTrue(result.companion_accepted)
        self.assertEqual(result.state.owner, DataBusOwner.COMPANION)
        self.assertEqual(result.state.bus.address, ExactWord(14, 2))

    def test_unknown_descriptor_and_reset_remain_explicit(self) -> None:
        issued = apply_data_owner_bus_cycle(
            DataOwnerBusState.reset(),
            phase=LogicalPhase.STATE_8,
            companion_request=DataBusRequest(
                address=UNKNOWN, write=True, write_data=UNKNOWN
            ),
        )
        self.assertIs(issued.state.bus.address, UNKNOWN)
        self.assertIs(issued.state.bus.write_data, UNKNOWN)
        reset = apply_data_owner_bus_cycle(
            issued.state, reset=True, phase=LogicalPhase.STATE_5
        )
        self.assertEqual(reset.state, DataOwnerBusState.reset())


if __name__ == "__main__":
    unittest.main()
