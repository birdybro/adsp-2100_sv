from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    BusControlMode,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    LogicalPhase,
    ProgramBusOwner,
    ProgramBusRequest,
    ComputePMOwnerControlState,
    apply_compute_pm_owner_control_cycle,
    read_dreg,
)


ROOT = Path(__file__).resolve().parents[1]


def _opcode(*, write: bool = False, dreg: DREG = DREG.AX0) -> int:
    return 0x500000 | (int(write) << 19) | (int(dreg) << 4)


def _cycle(
    state: ComputePMOwnerControlState,
    phase: LogicalPhase,
    **kwargs: object,
) -> ComputePMOwnerControlState:
    return apply_compute_pm_owner_control_cycle(
        state, phase=phase, **kwargs
    ).state


def _setup_state() -> ComputePMOwnerControlState:
    state = ComputePMOwnerControlState.reset()
    for register, value in (
        (DREG.AX0, 0x1234),
        (DREG.AY0, 3),
        (DREG.AR, 0x0101),
    ):
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            setup_dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            setup_dag=DAGRegisterSetup(kind, 4, value),
        )
    return _cycle(
        state,
        LogicalPhase.STATE_8,
        setup_px=ExactWord(8, 0x5A),
    )


def _advance_to_seven(
    state: ComputePMOwnerControlState,
    **kwargs: object,
) -> ComputePMOwnerControlState:
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


class ComputePMOwnerControlTests(unittest.TestCase):
    def test_machine_readable_attachment_contract(self) -> None:
        contract = json.loads(
            (ROOT / "docs/generated/adsp2100_compute_pm_owner_control.yaml")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertIn("RETRIES", contract["collision_effect"])
        self.assertIn(
            "TYPE13_ARCHITECTURAL_CLIENT", contract["excluded_claims"]
        )

    def test_completed_fetch_populates_type5_cache(self) -> None:
        state = _setup_state()
        issued = apply_compute_pm_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            fetch_request=ProgramBusRequest.fetch(0x0222),
        )
        self.assertTrue(issued.interface.owner_bus.fetch_accepted)
        done = apply_compute_pm_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xABCDEF),
        )
        self.assertTrue(done.fetch_cache_fill)
        self.assertTrue(done.core.cache_fill_accepted)

        type5 = apply_compute_pm_owner_control_cycle(
            done.state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
            next_fetch_address=ExactWord(14, 0x0222),
        )
        self.assertTrue(type5.core.core.accepted)
        self.assertTrue(type5.type5_request_accepted)
        self.assertEqual(
            type5.interface.owner_bus.accepted_owner,
            ProgramBusOwner.TYPE5_PM_DATA,
        )
        complete = apply_compute_pm_owner_control_cycle(
            _advance_to_seven(type5.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xCAFE55),
        )
        self.assertTrue(complete.core.core.data_action_complete)
        self.assertTrue(complete.core.instruction_from_cache)
        self.assertEqual(complete.core.next_instruction, 0xABCDEF)
        self.assertEqual(
            read_dreg(complete.state.core.core.primary, DREG.AX1),
            ExactWord(16, 0xCAFE),
        )

    def test_collision_retains_type5_descriptor_for_retry(self) -> None:
        issued = apply_compute_pm_owner_control_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
            next_fetch_address=ExactWord(14, 0x0333),
            fetch_request=ProgramBusRequest.fetch(0x0444),
        )
        self.assertTrue(issued.core.core.accepted)
        self.assertTrue(issued.interface.owner_bus.request_conflict)
        self.assertTrue(issued.type5_retry_pending)
        self.assertEqual(
            issued.interface.owner_bus.accepted_owner, ProgramBusOwner.NONE
        )
        self.assertIsNotNone(issued.state.core.core.pending)

        retry = apply_compute_pm_owner_control_cycle(
            issued.state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(retry.type5_request_presented)
        self.assertTrue(retry.type5_request_accepted)
        self.assertFalse(retry.type5_retry_pending)
        self.assertEqual(
            retry.interface.owner_bus.bus.state.address,
            ExactWord(14, 0x0100),
        )

    def test_recovery_collision_retries_without_replaying_data_action(
        self,
    ) -> None:
        issued = apply_compute_pm_owner_control_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
            next_fetch_address=ExactWord(14, 0x0555),
        )
        data_done = apply_compute_pm_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xBEEF12),
        )
        self.assertTrue(data_done.core.core.data_action_complete)
        self.assertIsNotNone(data_done.state.core.core.recovery)
        committed = data_done.state.core.core

        collision = apply_compute_pm_owner_control_cycle(
            data_done.state,
            phase=LogicalPhase.STATE_8,
            fetch_request=ProgramBusRequest.fetch(0x0666),
        )
        self.assertTrue(collision.interface.owner_bus.request_conflict)
        self.assertTrue(collision.type5_retry_pending)
        self.assertEqual(collision.state.core.core.primary, committed.primary)
        self.assertEqual(collision.state.core.core.dag, committed.dag)

        retry = apply_compute_pm_owner_control_cycle(
            collision.state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(retry.type5_request_accepted)
        self.assertFalse(retry.interface.owner_bus.bus.state.data_access)
        recovered = apply_compute_pm_owner_control_cycle(
            _advance_to_seven(retry.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0x654321),
        )
        self.assertTrue(recovered.core.core.instruction_complete)
        self.assertFalse(recovered.core.core.data_action_complete)
        self.assertTrue(recovered.core.instruction_from_external)
        self.assertEqual(recovered.core.next_instruction, 0x654321)

    def test_br_completes_type5_then_masks_shared_pins(self) -> None:
        issued = apply_compute_pm_owner_control_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(write=True, dreg=DREG.AX0),
            next_fetch_address=ExactWord(14, 0),
        )
        state = issued.state
        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = _cycle(state, phase, br_n=False)
        recognized = apply_compute_pm_owner_control_cycle(
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
        done = apply_compute_pm_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            br_n=False,
        )
        self.assertTrue(done.core.core.data_action_complete)

        state = done.state
        for phase in (
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            state = _cycle(state, phase, br_n=False)
        granted = apply_compute_pm_owner_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=False
        )
        self.assertEqual(granted.interface.control.state.mode, BusControlMode.GRANTED)
        masked = apply_compute_pm_owner_control_cycle(
            granted.state, phase=LogicalPhase.STATE_4, br_n=False
        )
        self.assertTrue(masked.interface.native_bus_relinquished)
        self.assertFalse(masked.interface.owner_bus.bus.address_output_enable)
        self.assertFalse(masked.interface.owner_bus.bus.control_output_enable)
        self.assertFalse(masked.interface.owner_bus.bus.data_output_enable)

    def test_raw_type13_completion_cannot_advance_type5(self) -> None:
        state = _setup_state()
        issued = apply_compute_pm_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type13_request=ProgramBusRequest.data_read(0x0777),
        )
        before = issued.state.core
        done = apply_compute_pm_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0x111111),
        )
        self.assertTrue(done.interface.owner_bus.type13_completion)
        self.assertFalse(done.core.core.data_action_complete)
        self.assertFalse(done.core.core.instruction_complete)
        self.assertEqual(done.state.core, before)


if __name__ == "__main__":
    unittest.main()
