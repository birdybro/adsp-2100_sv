from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model.model import ExactWord, UNKNOWN
from sim.reference_models.adsp2100_model.phase import LogicalPhase
from sim.reference_models.adsp2100_model.program_bus import (
    ProgramBusRequest,
    ProgramBusState,
    apply_program_bus_cycle,
)


def _issue(
    state: ProgramBusState,
    request: ProgramBusRequest,
) -> ProgramBusState:
    result = apply_program_bus_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        request=request,
    )
    assert result.request_accepted
    return result.state


class ProgramBusTests(unittest.TestCase):
    def test_machine_readable_phase_contract(self) -> None:
        contract = json.loads(
            Path("docs/generated/adsp2100_program_bus.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(
            contract["request_capture"],
            "ENABLED_STATE_8_TO_STATE_1_EDGE",
        )
        self.assertEqual(
            contract["phase_encoding"],
            {f"STATE_{index + 1}": index for index in range(8)},
        )
        self.assertEqual(
            contract["logical_pin_map"]["PMRD_N"],
            "LOW_STATES_4_THROUGH_7_FOR_READ_OR_FETCH",
        )
        self.assertEqual(contract["confidence"], "VERIFIED_PRIMARY")

    def test_read_pin_map_and_state_seven_sample(self) -> None:
        state = _issue(ProgramBusState.reset(), ProgramBusRequest.fetch(0x1234))
        for phase in LogicalPhase:
            data = ExactWord(24, 0xA55AA5)
            result = apply_program_bus_cycle(
                state,
                phase=phase,
                pmd_read_data=data,
                phase_advance=phase == LogicalPhase.STATE_7,
            )
            self.assertFalse(result.pms_n)
            self.assertEqual(result.address, 0x1234)
            self.assertTrue(result.address_known)
            self.assertFalse(result.pmda)
            self.assertEqual(
                result.pmrd_n,
                phase
                not in (
                    LogicalPhase.STATE_4,
                    LogicalPhase.STATE_5,
                    LogicalPhase.STATE_6,
                    LogicalPhase.STATE_7,
                ),
            )
            self.assertTrue(result.pmwr_n)
            self.assertFalse(result.data_output_enable)
            if phase == LogicalPhase.STATE_7:
                self.assertTrue(result.completion_event)
                self.assertTrue(result.read_sample_event)
                self.assertTrue(result.state.response_valid)
                self.assertEqual(result.state.read_data, data)

    def test_write_data_drives_only_states_five_through_eight(self) -> None:
        state = _issue(
            ProgramBusState.reset(),
            ProgramBusRequest.data_write(0x2222, 0xABCDEF),
        )
        for phase in LogicalPhase:
            result = apply_program_bus_cycle(
                state,
                phase=phase,
                phase_advance=phase == LogicalPhase.STATE_7,
            )
            self.assertTrue(result.pmrd_n)
            self.assertEqual(
                result.pmwr_n,
                phase
                not in (
                    LogicalPhase.STATE_4,
                    LogicalPhase.STATE_5,
                    LogicalPhase.STATE_6,
                    LogicalPhase.STATE_7,
                ),
            )
            expected_drive = phase in (
                LogicalPhase.STATE_5,
                LogicalPhase.STATE_6,
                LogicalPhase.STATE_7,
                LogicalPhase.STATE_8,
            )
            self.assertEqual(result.data_output_enable, expected_drive)
            self.assertEqual(result.write_data_known, expected_drive)
            self.assertEqual(result.write_data, 0xABCDEF)
            if phase == LogicalPhase.STATE_7:
                self.assertTrue(result.completion_event)
                self.assertFalse(result.read_sample_event)
                self.assertTrue(result.state.response_write)

    def test_pmda_distinguishes_fetch_and_data_read(self) -> None:
        fetch = _issue(ProgramBusState.reset(), ProgramBusRequest.fetch(1))
        data = _issue(ProgramBusState.reset(), ProgramBusRequest.data_read(1))
        self.assertFalse(apply_program_bus_cycle(fetch).pmda)
        self.assertTrue(apply_program_bus_cycle(data).pmda)

    def test_state_seven_hold_extends_strobes_without_completion(self) -> None:
        state = _issue(
            ProgramBusState.reset(), ProgramBusRequest.data_write(3, 4)
        )
        held = apply_program_bus_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            phase_advance=False,
        )
        self.assertEqual(held.state, state)
        self.assertFalse(held.pmwr_n)
        self.assertTrue(held.data_output_enable)
        self.assertFalse(held.completion_event)
        completed = apply_program_bus_cycle(
            held.state,
            phase=LogicalPhase.STATE_7,
            phase_advance=True,
        )
        self.assertTrue(completed.completion_event)

    def test_back_to_back_requests_keep_pms_asserted_and_replace_descriptor(self) -> None:
        state = _issue(ProgramBusState.reset(), ProgramBusRequest.fetch(0x0010))
        state = apply_program_bus_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0x123456),
        ).state
        boundary = apply_program_bus_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            request=ProgramBusRequest.data_read(0x0020),
        )
        self.assertFalse(boundary.pms_n)
        self.assertTrue(boundary.request_accepted)
        self.assertTrue(boundary.state.active)
        self.assertEqual(boundary.state.address, ExactWord(14, 0x0020))
        next_cycle = apply_program_bus_cycle(
            boundary.state, phase=LogicalPhase.STATE_1
        )
        self.assertFalse(next_cycle.pms_n)
        self.assertEqual(next_cycle.address, 0x0020)
        self.assertTrue(next_cycle.pmda)

    def test_idle_after_state_eight_deasserts_select_and_invalidates_address(self) -> None:
        state = _issue(ProgramBusState.reset(), ProgramBusRequest.fetch(2))
        idle = apply_program_bus_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            request=None,
        )
        self.assertFalse(idle.pms_n)
        after = apply_program_bus_cycle(
            idle.state, phase=LogicalPhase.STATE_1
        )
        self.assertTrue(after.pms_n)
        self.assertFalse(after.address_output_enable)
        self.assertFalse(after.state.active)

    def test_bus_relinquish_masks_all_output_enables_and_preserves_state(self) -> None:
        state = _issue(
            ProgramBusState.reset(), ProgramBusRequest.data_write(5, 6)
        )
        masked = apply_program_bus_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            bus_relinquished=True,
        )
        self.assertEqual(masked.state, state)
        self.assertFalse(masked.address_output_enable)
        self.assertFalse(masked.control_output_enable)
        self.assertFalse(masked.data_output_enable)
        self.assertTrue(masked.pms_n)
        self.assertTrue(masked.pmrd_n)
        self.assertTrue(masked.pmwr_n)

    def test_unknown_address_data_and_read_sample_remain_explicit(self) -> None:
        request = ProgramBusRequest(
            address=UNKNOWN,
            data_access=True,
            write=True,
            write_data=UNKNOWN,
        )
        state = _issue(ProgramBusState.reset(), request)
        pins = apply_program_bus_cycle(state, phase=LogicalPhase.STATE_5)
        self.assertFalse(pins.address_known)
        self.assertFalse(pins.write_data_known)
        read_state = _issue(
            ProgramBusState.reset(),
            ProgramBusRequest(address=UNKNOWN, data_access=True),
        )
        sampled = apply_program_bus_cycle(
            read_state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertTrue(sampled.state.response_valid)
        self.assertIs(sampled.state.read_data, UNKNOWN)

    def test_reset_cancels_transaction_and_response(self) -> None:
        state = ProgramBusState(
            active=True,
            address=ExactWord(14, 1),
            response_valid=True,
            read_data=ExactWord(24, 2),
        )
        result = apply_program_bus_cycle(
            state,
            reset=True,
            phase=LogicalPhase.STATE_5,
        )
        self.assertEqual(result.state, ProgramBusState.reset())
        self.assertTrue(result.pms_n)
        self.assertFalse(result.control_output_enable)

    def test_width_and_phase_errors_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            ProgramBusRequest(address=ExactWord(13, 0))
        with self.assertRaises(ValueError):
            ProgramBusRequest(write_data=ExactWord(23, 0))
        with self.assertRaises(ValueError):
            apply_program_bus_cycle(
                ProgramBusState.reset(), pmd_read_data=ExactWord(16, 0)
            )
        with self.assertRaises(ValueError):
            apply_program_bus_cycle(ProgramBusState.reset(), phase=8)


if __name__ == "__main__":
    unittest.main()
