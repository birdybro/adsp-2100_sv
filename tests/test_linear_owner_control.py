from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    BusControlMode,
    DREG,
    ExactWord,
    LinearOwnerControlState,
    LogicalPhase,
    ProgramBusOwner,
    ProgramBusRequest,
    apply_linear_owner_control_cycle,
    read_dreg,
)


ROOT = Path(__file__).resolve().parents[1]


def _type6(destination: DREG, data: int) -> int:
    return 0x400000 | ((data & 0xFFFF) << 4) | int(destination)


def _cycle(
    state: LinearOwnerControlState,
    phase: LogicalPhase,
    **kwargs: object,
) -> LinearOwnerControlState:
    return apply_linear_owner_control_cycle(
        state, phase=phase, **kwargs
    ).state


def _setup(
    opcode: int = 0,
    *,
    pc: int = 4,
) -> LinearOwnerControlState:
    result = apply_linear_owner_control_cycle(
        LinearOwnerControlState.reset(),
        phase=LogicalPhase.STATE_8,
        instruction_setup=(ExactWord(14, pc), ExactWord(24, opcode)),
    )
    assert result.core.instruction_setup_accepted
    return result.state


def _advance_to_seven(
    state: LinearOwnerControlState,
    **kwargs: object,
) -> LinearOwnerControlState:
    for phase in (
        LogicalPhase.STATE_1,
        LogicalPhase.STATE_2,
        LogicalPhase.STATE_3,
        LogicalPhase.STATE_4,
        LogicalPhase.STATE_5,
        LogicalPhase.STATE_6,
    ):
        state = _cycle(state, phase, **kwargs)
    return state


class LinearOwnerControlTests(unittest.TestCase):
    def test_machine_readable_attachment_contract(self) -> None:
        contract = json.loads(
            (ROOT / "docs/generated/adsp2100_linear_owner_control.yaml")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertIn("RETRIES", contract["collision_effect"])
        self.assertIn(
            "TYPE5_ARCHITECTURAL_CLIENT", contract["excluded_claims"]
        )

    def test_fetch_completion_retires_only_routed_client(self) -> None:
        issued = apply_linear_owner_control_cycle(
            _setup(_type6(DREG.AX0, 0x1234)),
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issued.core.fetch_request_presented)
        self.assertTrue(issued.interface.owner_bus.fetch_accepted)
        self.assertTrue(issued.state.core.pending)
        done = apply_linear_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(done.interface.owner_bus.fetch_completion)
        self.assertTrue(done.core.retire_event)
        self.assertEqual(done.state.core.architecture.pc, ExactWord(14, 5))
        self.assertEqual(
            read_dreg(done.state.core.architecture.primary, DREG.AX0),
            ExactWord(16, 0x1234),
        )

    def test_collision_retries_without_retiring_current_instruction(self) -> None:
        state = _setup()
        collision = apply_linear_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type5_request=ProgramBusRequest.data_read(0x0100),
        )
        self.assertTrue(collision.core.fetch_request_presented)
        self.assertTrue(collision.interface.owner_bus.request_conflict)
        self.assertTrue(collision.fetch_retry_pending)
        self.assertFalse(collision.state.core.pending)
        self.assertEqual(collision.state.core.architecture.pc, ExactWord(14, 4))

        retry = apply_linear_owner_control_cycle(
            collision.state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(retry.interface.owner_bus.fetch_accepted)
        self.assertFalse(retry.fetch_retry_pending)
        self.assertEqual(
            retry.interface.owner_bus.bus.state.address,
            ExactWord(14, 5),
        )

    def test_raw_pm_data_completion_cannot_retire_fetch_client(self) -> None:
        issued = apply_linear_owner_control_cycle(
            LinearOwnerControlState.reset(),
            phase=LogicalPhase.STATE_8,
            type13_request=ProgramBusRequest.data_read(0x0222),
        )
        before = issued.state.core
        done = apply_linear_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xABCDEF),
        )
        self.assertTrue(done.interface.owner_bus.type13_completion)
        self.assertFalse(done.core.retire_event)
        self.assertEqual(done.state.core, before)

    def test_both_raw_pm_data_owners_remain_available_when_fetch_idle(self) -> None:
        state = LinearOwnerControlState.reset()
        for owner, request in (
            (ProgramBusOwner.TYPE5_PM_DATA, "type5_request"),
            (ProgramBusOwner.TYPE13_PM_DATA, "type13_request"),
        ):
            result = apply_linear_owner_control_cycle(
                state,
                phase=LogicalPhase.STATE_8,
                **{request: ProgramBusRequest.data_write(0x0300, 0x123456)},
            )
            self.assertEqual(result.interface.owner_bus.accepted_owner, owner)
            state = apply_linear_owner_control_cycle(
                _advance_to_seven(result.state),
                phase=LogicalPhase.STATE_7,
            ).state

    def test_br_completes_fetch_then_masks_shared_pins(self) -> None:
        issued = apply_linear_owner_control_cycle(
            _setup(),
            phase=LogicalPhase.STATE_8,
        )
        state = issued.state
        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = _cycle(state, phase, br_n=False)
        recognized = apply_linear_owner_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=False
        )
        self.assertTrue(recognized.interface.control.request_recognized)
        self.assertTrue(recognized.interface.owner_bus.bus.address_output_enable)
        state = recognized.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = _cycle(state, phase, br_n=False)
        done = apply_linear_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            br_n=False,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(done.core.retire_event)

        state = done.state
        for phase in (
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            state = _cycle(state, phase, br_n=False)
        granted = apply_linear_owner_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=False
        )
        self.assertEqual(
            granted.interface.control.state.mode, BusControlMode.GRANTED
        )
        masked = apply_linear_owner_control_cycle(
            granted.state, phase=LogicalPhase.STATE_4, br_n=False
        )
        self.assertTrue(masked.interface.native_bus_relinquished)
        self.assertFalse(masked.interface.owner_bus.bus.address_output_enable)
        self.assertFalse(masked.interface.owner_bus.bus.control_output_enable)
        self.assertFalse(masked.interface.owner_bus.bus.data_output_enable)


if __name__ == "__main__":
    unittest.main()
