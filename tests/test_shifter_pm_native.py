from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    LogicalPhase,
    ShifterPMNativeState,
    apply_shifter_pm_native_cycle,
    read_dreg,
)


def _opcode(*, write: bool = False, dreg: DREG = DREG.AX0) -> int:
    return 0x110000 | (int(write) << 15) | (int(dreg) << 4)


def _cycle(
    state: ShifterPMNativeState,
    phase: LogicalPhase,
    **kwargs: object,
) -> ShifterPMNativeState:
    return apply_shifter_pm_native_cycle(
        state,
        phase=phase,
        **kwargs,
    ).state


def _setup_state() -> ShifterPMNativeState:
    state = ShifterPMNativeState.reset()
    for register, value in (
        (DREG.AX0, 0x1234),
        (DREG.SI, 0x0101),
        (DREG.SE, 0),
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


class ShifterPMNativeTests(unittest.TestCase):
    def test_read_commits_only_at_native_state_seven_completion(self) -> None:
        state = _setup_state()
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, 0x0222),
            external_fetch_instruction=ExactWord(24, 0xABCDEF),
        )
        initial_core = state.core.core
        issued = apply_shifter_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
            next_fetch_address=ExactWord(14, 0x0222),
            pmd_read_data=ExactWord(24, 0x111111),
        )
        self.assertTrue(issued.issue_boundary)
        self.assertTrue(issued.core.core.accepted)
        self.assertTrue(issued.bus.request_accepted)
        self.assertFalse(issued.core.core.data_action_complete)
        self.assertEqual(issued.state.core.core.primary, initial_core.primary)
        self.assertEqual(issued.state.core.core.dag, initial_core.dag)

        state = issued.state
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            held = apply_shifter_pm_native_cycle(
                state,
                phase=phase,
                pmd_read_data=ExactWord(24, 0x222222),
            )
            self.assertFalse(held.core.core.data_action_complete)
            self.assertEqual(held.state.core.core.primary, initial_core.primary)
            state = held.state

        wait = apply_shifter_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            phase_advance=False,
            pmd_read_data=ExactWord(24, 0x333333),
        )
        self.assertFalse(wait.bus.completion_event)
        self.assertFalse(wait.core.core.data_action_complete)
        done = apply_shifter_pm_native_cycle(
            wait.state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xCAFE55),
        )
        self.assertTrue(done.bus.read_sample_event)
        self.assertTrue(done.core.core.data_action_complete)
        self.assertTrue(done.core.core.instruction_complete)
        self.assertTrue(done.core.instruction_from_cache)
        self.assertEqual(done.core.next_instruction, 0xABCDEF)
        self.assertEqual(
            read_dreg(done.state.core.core.primary, DREG.AX1),
            ExactWord(16, 0xCAFE),
        )
        self.assertEqual(done.state.core.core.px, ExactWord(8, 0x55))
        self.assertEqual(done.state.core.core.dag.i[4], 0x0101)
        self.assertFalse(done.integration_conflict)

    def test_cache_miss_issues_back_to_back_recovery_fetch(self) -> None:
        issued = apply_shifter_pm_native_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
            next_fetch_address=ExactWord(14, 0x0333),
        )
        state = issued.state
        for phase in range(6):
            state = _cycle(state, LogicalPhase(phase))
        data_done = apply_shifter_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xBEEF12),
        )
        self.assertTrue(data_done.core.core.recovery_required is False)
        self.assertFalse(data_done.core.core.instruction_complete)
        self.assertIsNotNone(data_done.state.core.core.recovery)
        self.assertFalse(data_done.bus.pms_n)

        recovery_issue = apply_shifter_pm_native_cycle(
            data_done.state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(recovery_issue.bus.request_accepted)
        self.assertFalse(recovery_issue.bus.state.data_access)
        self.assertFalse(recovery_issue.bus.pms_n)
        state = recovery_issue.state
        for phase in range(6):
            state = _cycle(state, LogicalPhase(phase))
        recovered = apply_shifter_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0x654321),
        )
        self.assertTrue(recovered.core.core.recovery_fetch)
        self.assertTrue(recovered.core.core.instruction_complete)
        self.assertTrue(recovered.core.instruction_from_external)
        self.assertEqual(recovered.core.next_instruction, 0x654321)
        self.assertTrue(recovered.core.cache_fill_accepted)
        self.assertFalse(recovered.integration_conflict)

    def test_write_descriptor_and_drive_window_use_cycle_start_values(self) -> None:
        issued = apply_shifter_pm_native_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(write=True, dreg=DREG.AX0),
            next_fetch_address=ExactWord(14, 0),
        )
        self.assertTrue(issued.bus.state.write)
        self.assertEqual(issued.bus.state.write_data, ExactWord(24, 0x12345A))
        state = issued.state
        for phase in LogicalPhase:
            if phase == LogicalPhase.STATE_8:
                continue
            result = apply_shifter_pm_native_cycle(state, phase=phase)
            expected_drive = phase in (
                LogicalPhase.STATE_5,
                LogicalPhase.STATE_6,
                LogicalPhase.STATE_7,
            )
            self.assertEqual(result.bus.data_output_enable, expected_drive)
            state = result.state

    def test_off_boundary_controls_fail_closed(self) -> None:
        state = _setup_state()
        result = apply_shifter_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            execute=True,
            opcode=_opcode(),
        )
        self.assertTrue(result.phase_conflict)
        self.assertTrue(result.integration_conflict)
        self.assertFalse(result.core.core.accepted)
        self.assertFalse(result.bus.request_accepted)
        self.assertEqual(result.state, state)

    def test_relinquishment_masks_and_holds_both_boundaries(self) -> None:
        issued = apply_shifter_pm_native_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(),
            next_fetch_address=ExactWord(14, 0),
        )
        held = apply_shifter_pm_native_cycle(
            issued.state,
            phase=LogicalPhase.STATE_4,
            bus_relinquished=True,
        )
        self.assertFalse(held.bus.address_output_enable)
        self.assertFalse(held.bus.control_output_enable)
        self.assertEqual(held.state, issued.state)
        resumed = apply_shifter_pm_native_cycle(
            held.state,
            phase=LogicalPhase.STATE_4,
        )
        self.assertFalse(resumed.bus.pmrd_n)
        self.assertFalse(resumed.integration_conflict)


if __name__ == "__main__":
    unittest.main()
