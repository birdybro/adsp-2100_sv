from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ComputePMNativeState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    LogicalPhase,
    apply_compute_pm_native_cycle,
    read_dreg,
)


def _cycle(
    state: ComputePMNativeState,
    phase: LogicalPhase,
    **kwargs: object,
) -> ComputePMNativeState:
    return apply_compute_pm_native_cycle(
        state,
        phase=phase,
        **kwargs,
    ).state


def _setup_state() -> ComputePMNativeState:
    state = ComputePMNativeState.reset()
    for register, value in (
        (DREG.AX0, 2),
        (DREG.AY0, 3),
        (DREG.AR, 0x1234),
    ):
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            setup_dreg=DREGWrite(register, ExactWord(16, value)),
        )
    state = _cycle(
        state,
        LogicalPhase.STATE_8,
        setup_astat=ExactWord(8, 0),
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


class ComputePMNativeTests(unittest.TestCase):
    def test_compute_read_commits_only_at_state_seven_completion(self) -> None:
        state = _setup_state()
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, 0x222),
            external_fetch_instruction=ExactWord(24, 0xABCDEF),
        )
        initial = state.core.core
        issued = apply_compute_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=0x526000,
            next_fetch_address=ExactWord(14, 0x222),
        )
        self.assertTrue(issued.issue_boundary)
        self.assertTrue(issued.core.core.accepted)
        self.assertTrue(issued.bus.request_accepted)
        self.assertEqual(issued.state.core.core.primary, initial.primary)

        state = issued.state
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            held = apply_compute_pm_native_cycle(state, phase=phase)
            self.assertFalse(held.core.core.data_action_complete)
            state = held.state
        wait = apply_compute_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            phase_advance=False,
        )
        self.assertFalse(wait.bus.completion_event)
        done = apply_compute_pm_native_cycle(
            wait.state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xCAFE55),
        )
        self.assertTrue(done.bus.read_sample_event)
        self.assertTrue(done.core.core.data_action_complete)
        self.assertTrue(done.core.instruction_from_cache)
        self.assertEqual(done.core.next_instruction, 0xABCDEF)
        self.assertEqual(
            read_dreg(done.state.core.core.primary, DREG.AR),
            ExactWord(16, 5),
        )
        self.assertEqual(
            read_dreg(done.state.core.core.primary, DREG.AX0),
            ExactWord(16, 0xCAFE),
        )
        self.assertEqual(done.state.core.core.px, ExactWord(8, 0x55))
        self.assertEqual(done.state.core.core.dag.i[4], 0x101)
        self.assertFalse(done.integration_conflict)

    def test_cache_miss_issues_back_to_back_recovery_fetch(self) -> None:
        issued = apply_compute_pm_native_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=0x526000,
            next_fetch_address=ExactWord(14, 0x333),
        )
        state = issued.state
        for phase in range(6):
            state = _cycle(state, LogicalPhase(phase))
        data_done = apply_compute_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xBEEF12),
        )
        self.assertFalse(data_done.core.core.instruction_complete)
        self.assertIsNotNone(data_done.state.core.core.recovery)
        self.assertFalse(data_done.bus.pms_n)

        recovery_issue = apply_compute_pm_native_cycle(
            data_done.state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(recovery_issue.bus.request_accepted)
        self.assertFalse(recovery_issue.bus.state.data_access)
        state = recovery_issue.state
        for phase in range(6):
            state = _cycle(state, LogicalPhase(phase))
        recovered = apply_compute_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0x654321),
        )
        self.assertTrue(recovered.core.core.recovery_fetch)
        self.assertTrue(recovered.core.instruction_from_external)
        self.assertEqual(recovered.core.next_instruction, 0x654321)
        self.assertTrue(recovered.core.cache_fill_accepted)
        self.assertFalse(recovered.integration_conflict)

    def test_compute_write_descriptor_uses_cycle_start_dreg_and_px(self) -> None:
        issued = apply_compute_pm_native_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=0x5A60A0,
            next_fetch_address=ExactWord(14, 0),
        )
        self.assertTrue(issued.bus.state.write)
        self.assertEqual(issued.bus.state.write_data, ExactWord(24, 0x12345A))
        state = issued.state
        for phase in LogicalPhase:
            if phase == LogicalPhase.STATE_8:
                continue
            result = apply_compute_pm_native_cycle(state, phase=phase)
            expected_drive = phase in (
                LogicalPhase.STATE_5,
                LogicalPhase.STATE_6,
                LogicalPhase.STATE_7,
            )
            self.assertEqual(result.bus.data_output_enable, expected_drive)
            state = result.state

    def test_off_boundary_controls_fail_closed(self) -> None:
        state = _setup_state()
        result = apply_compute_pm_native_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            execute=True,
            opcode=0x526000,
        )
        self.assertTrue(result.phase_conflict)
        self.assertTrue(result.integration_conflict)
        self.assertFalse(result.core.core.accepted)
        self.assertFalse(result.bus.request_accepted)
        self.assertEqual(result.state, state)

    def test_relinquishment_masks_and_holds_active_transaction(self) -> None:
        issued = apply_compute_pm_native_cycle(
            _setup_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=0x526000,
            next_fetch_address=ExactWord(14, 0),
        )
        held = apply_compute_pm_native_cycle(
            issued.state,
            phase=LogicalPhase.STATE_4,
            bus_relinquished=True,
        )
        self.assertFalse(held.bus.address_output_enable)
        self.assertFalse(held.bus.control_output_enable)
        self.assertEqual(held.state, issued.state)
        resumed = apply_compute_pm_native_cycle(
            held.state,
            phase=LogicalPhase.STATE_4,
        )
        self.assertFalse(resumed.bus.pmrd_n)
        self.assertFalse(resumed.integration_conflict)


if __name__ == "__main__":
    unittest.main()
