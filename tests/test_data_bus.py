from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    DataBusRequest,
    DataBusState,
    ExactWord,
    LogicalPhase,
    UNKNOWN,
    apply_data_bus_cycle,
)


def _issue(state: DataBusState, request: DataBusRequest) -> DataBusState:
    result = apply_data_bus_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        request=request,
    )
    assert result.request_accepted
    return result.state


class DataBusTests(unittest.TestCase):
    def test_machine_readable_phase_contract(self) -> None:
        contract = json.loads(
            Path("docs/generated/adsp2100_data_bus.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(
            contract["logical_pin_map"]["DMACK_SAMPLE"],
            "ENABLED_STATE_6_TO_STATE_7_EDGE",
        )
        self.assertEqual(
            contract["wait_extension"]["duration"],
            "ONE_COMPLETE_EIGHT_SUBSTATE_CYCLE_PER_LOW_SAMPLE",
        )
        self.assertEqual(contract["confidence"], "VERIFIED_PRIMARY")

    def test_read_qualifies_ack_at_six_and_samples_data_at_seven(self) -> None:
        state = _issue(DataBusState.reset(), DataBusRequest.read(0x1234))
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            result = apply_data_bus_cycle(state, phase=phase, dm_ack=True)
            self.assertFalse(result.completion_event)
            self.assertFalse(result.dms_n)
            self.assertEqual(
                result.dmrd_n,
                phase not in (LogicalPhase.STATE_4, LogicalPhase.STATE_5),
            )
            state = result.state

        acknowledged = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        self.assertTrue(acknowledged.dmack_sample_event)
        self.assertTrue(acknowledged.dmack_accepted)
        self.assertFalse(acknowledged.wait_extension_event)
        self.assertFalse(acknowledged.dmrd_n)
        self.assertTrue(acknowledged.state.acknowledged)

        done = apply_data_bus_cycle(
            acknowledged.state,
            phase=LogicalPhase.STATE_7,
            dm_ack=False,
            dmd_read_data=ExactWord(16, 0xCAFE),
        )
        self.assertTrue(done.completion_event)
        self.assertTrue(done.read_sample_event)
        self.assertTrue(done.state.response_valid)
        self.assertEqual(done.state.read_data, ExactWord(16, 0xCAFE))

    def test_write_strobe_and_data_drive_windows(self) -> None:
        state = _issue(
            DataBusState.reset(),
            DataBusRequest.write_word(0x2345, 0xBEEF),
        )
        for phase in LogicalPhase:
            result = apply_data_bus_cycle(
                state,
                phase=phase,
                phase_advance=False,
            )
            expected_strobe = phase in (
                LogicalPhase.STATE_4,
                LogicalPhase.STATE_5,
                LogicalPhase.STATE_6,
                LogicalPhase.STATE_7,
            )
            expected_drive = phase in (
                LogicalPhase.STATE_5,
                LogicalPhase.STATE_6,
                LogicalPhase.STATE_7,
                LogicalPhase.STATE_8,
            )
            self.assertEqual(result.dmwr_n, not expected_strobe)
            self.assertTrue(result.dmrd_n)
            self.assertEqual(result.data_output_enable, expected_drive)
            self.assertEqual(result.write_data_known, expected_drive)
            self.assertEqual(result.write_data, 0xBEEF)

    def test_low_ack_extends_state_seven_by_a_complete_substate_cycle(self) -> None:
        state = _issue(DataBusState.reset(), DataBusRequest.read(0x3456))
        low = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        self.assertTrue(low.wait_extension_event)
        self.assertTrue(low.state.waiting)

        first_seven = apply_data_bus_cycle(
            low.state,
            phase=LogicalPhase.STATE_7,
            dm_ack=True,
            dmd_read_data=ExactWord(16, 0x1111),
        )
        self.assertFalse(first_seven.completion_event)
        state = first_seven.state
        descriptor = (state.address, state.write, state.write_data)

        for phase in (
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held = apply_data_bus_cycle(
                state,
                phase=phase,
                dm_ack=True,
                request=DataBusRequest.read(1),
            )
            self.assertTrue(held.waiting)
            self.assertFalse(held.dmrd_n)
            self.assertFalse(held.request_ready)
            self.assertEqual(
                (held.state.address, held.state.write, held.state.write_data),
                descriptor,
            )
            state = held.state

        high = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        self.assertTrue(high.dmack_accepted)
        self.assertFalse(high.state.waiting)
        done = apply_data_bus_cycle(
            high.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xABCD),
        )
        self.assertTrue(done.completion_event)
        self.assertEqual(done.state.read_data, ExactWord(16, 0xABCD))

    def test_late_ack_is_ignored_until_the_next_state_six_sample(self) -> None:
        state = _issue(DataBusState.reset(), DataBusRequest.read(7))
        low = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        late = apply_data_bus_cycle(
            low.state,
            phase=LogicalPhase.STATE_7,
            dm_ack=True,
        )
        self.assertFalse(late.completion_event)
        self.assertTrue(late.state.waiting)

    def test_disabled_state_six_edge_does_not_sample_ack(self) -> None:
        state = _issue(DataBusState.reset(), DataBusRequest.read(8))
        held = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            phase_advance=False,
            dm_ack=True,
        )
        self.assertFalse(held.dmack_sample_event)
        self.assertFalse(held.state.acknowledged)
        premature = apply_data_bus_cycle(
            held.state,
            phase=LogicalPhase.STATE_7,
        )
        self.assertFalse(premature.completion_event)

    def test_back_to_back_request_preserves_dms_and_replaces_descriptor(self) -> None:
        state = _issue(DataBusState.reset(), DataBusRequest.read(0x10))
        state = apply_data_bus_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=True
        ).state
        state = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0x1234),
        ).state
        boundary = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            request=DataBusRequest.write_word(0x20, 0x5678),
        )
        self.assertFalse(boundary.dms_n)
        self.assertTrue(boundary.request_accepted)
        self.assertEqual(boundary.state.address, ExactWord(14, 0x20))
        next_cycle = apply_data_bus_cycle(
            boundary.state,
            phase=LogicalPhase.STATE_1,
        )
        self.assertFalse(next_cycle.dms_n)
        self.assertTrue(next_cycle.state.write)

    def test_relinquishment_masks_outputs_and_holds_wait_state(self) -> None:
        state = _issue(
            DataBusState.reset(), DataBusRequest.write_word(3, 4)
        )
        state = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        ).state
        masked = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
            bus_relinquished=True,
        )
        self.assertEqual(masked.state, state)
        self.assertFalse(masked.dmack_sample_event)
        self.assertFalse(masked.address_output_enable)
        self.assertFalse(masked.control_output_enable)
        self.assertFalse(masked.data_output_enable)
        self.assertTrue(masked.dms_n and masked.dmrd_n and masked.dmwr_n)

    def test_unknowns_reset_and_width_errors_remain_explicit(self) -> None:
        state = _issue(
            DataBusState.reset(),
            DataBusRequest(address=UNKNOWN, write=True, write_data=UNKNOWN),
        )
        pins = apply_data_bus_cycle(
            state,
            phase=LogicalPhase.STATE_5,
            phase_advance=False,
        )
        self.assertFalse(pins.address_known)
        self.assertFalse(pins.write_data_known)
        reset = apply_data_bus_cycle(
            state,
            reset=True,
            phase=LogicalPhase.STATE_5,
        )
        self.assertEqual(reset.state, DataBusState.reset())
        self.assertTrue(reset.dms_n)
        with self.assertRaises(ValueError):
            DataBusRequest(address=ExactWord(13, 0))
        with self.assertRaises(ValueError):
            DataBusRequest(write_data=ExactWord(15, 0))
        with self.assertRaises(ValueError):
            apply_data_bus_cycle(
                DataBusState.reset(), dmd_read_data=ExactWord(24, 0)
            )
        with self.assertRaises(ValueError):
            apply_data_bus_cycle(DataBusState.reset(), phase=8)


if __name__ == "__main__":
    unittest.main()
