from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    HaltControlMode,
    LogicalPhase,
    ShifterPMHaltState,
    apply_shifter_pm_halt_cycle,
    lookup_instruction_cache,
    read_dreg,
)


def _opcode(*, write: bool = False, dreg: DREG = DREG.AX0) -> int:
    return 0x110000 | (int(write) << 15) | (int(dreg) << 4)


def _cycle(
    state: ShifterPMHaltState,
    phase: LogicalPhase,
    **kwargs: object,
) -> ShifterPMHaltState:
    return apply_shifter_pm_halt_cycle(state, phase=phase, **kwargs).state


def _setup_state(*, cache_address: int | None = None) -> ShifterPMHaltState:
    state = ShifterPMHaltState.reset()
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
    state = _cycle(
        state,
        LogicalPhase.STATE_8,
        setup_px=ExactWord(8, 0x5A),
    )
    if cache_address is not None:
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, cache_address),
            external_fetch_instruction=ExactWord(24, 0x111111),
        )
    return state


class ShifterPMHaltTests(unittest.TestCase):
    def test_pm_data_halt_overrides_hit_and_stops_after_real_fetch(self) -> None:
        state = _setup_state(cache_address=0x0222)
        issued = apply_shifter_pm_halt_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(write=True),
            next_fetch_address=ExactWord(14, 0x0222),
        )
        self.assertTrue(issued.native.core.core.cache_instruction_selected)
        self.assertTrue(issued.native.bus.request_accepted)
        state = issued.state

        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = _cycle(state, phase, halt_n=False)
        recognized = apply_shifter_pm_halt_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            halt_n=False,
        )
        self.assertTrue(recognized.control.halt_recognized)
        self.assertTrue(recognized.pm_data_cycle)
        self.assertTrue(recognized.late_force_request)
        self.assertEqual(
            recognized.state.control.mode,
            HaltControlMode.FORCE_FETCH_PENDING,
        )
        state = recognized.state

        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = _cycle(state, phase, halt_n=False)
        data_done = apply_shifter_pm_halt_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0xAAAAAA),
        )
        self.assertTrue(data_done.native.core.core.data_action_complete)
        self.assertFalse(data_done.native.core.core.instruction_complete)
        self.assertFalse(data_done.native.core.instruction_from_cache)
        self.assertFalse(data_done.control.halt_stop_event)
        self.assertEqual(data_done.state.native.core.core.dag.i[4], 0x0101)
        self.assertIsNotNone(data_done.state.native.core.core.recovery)

        forced = apply_shifter_pm_halt_cycle(
            data_done.state,
            phase=LogicalPhase.STATE_8,
            halt_n=False,
        )
        self.assertTrue(forced.control.force_fetch_issue)
        self.assertTrue(forced.native.bus.request_accepted)
        self.assertTrue(forced.native.core.core.recovery_fetch)
        self.assertFalse(forced.native.bus.state.data_access)
        self.assertFalse(forced.attachment_conflict)
        state = forced.state

        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = _cycle(state, phase, halt_n=False)
        stopped = apply_shifter_pm_halt_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0x222222),
        )
        self.assertTrue(stopped.control.halt_stop_event)
        self.assertTrue(stopped.native.core.core.instruction_complete)
        self.assertTrue(stopped.native.core.instruction_from_external)
        self.assertEqual(stopped.native.core.next_instruction, 0x222222)
        self.assertEqual(stopped.state.control.mode, HaltControlMode.HALTED)
        self.assertEqual(stopped.state.native.core.core.dag.i[4], 0x0101)
        self.assertEqual(
            lookup_instruction_cache(
                stopped.state.native.core.cache,
                ExactWord(14, 0x0222),
            ).instruction,
            ExactWord(24, 0x222222),
        )

    def test_halted_state_holds_forced_fetch_bus_until_dmack_release(self) -> None:
        state = _setup_state()
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(),
            next_fetch_address=ExactWord(14, 0x0333),
        )
        for phase in LogicalPhase:
            if phase == LogicalPhase.STATE_8:
                continue
            state = _cycle(state, phase)
        state = _cycle(state, LogicalPhase.STATE_8)
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            state = _cycle(state, phase, halt_n=False)
        state = _cycle(state, LogicalPhase.STATE_3, halt_n=False)
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = _cycle(state, phase, halt_n=False)
        state = _cycle(
            state,
            LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0x654321),
        )
        self.assertEqual(state.control.mode, HaltControlMode.HALTED)

        blocked = apply_shifter_pm_halt_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=False,
        )
        self.assertTrue(blocked.control.release_blocked)
        self.assertTrue(blocked.control.phase_hold)
        self.assertTrue(blocked.native.bus.address_output_enable)
        resumed = apply_shifter_pm_halt_cycle(
            blocked.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=True,
        )
        self.assertTrue(resumed.control.resume_event)
        self.assertFalse(resumed.control.phase_hold)
        self.assertEqual(resumed.state.control.mode, HaltControlMode.RUNNING)

    def test_data_read_and_dag_commit_only_once_across_forced_fetch(self) -> None:
        state = _setup_state(cache_address=0x0200)
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
            next_fetch_address=ExactWord(14, 0x0200),
        )
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            state = _cycle(state, phase, halt_n=False)
        state = _cycle(state, LogicalPhase.STATE_3, halt_n=False)
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = _cycle(state, phase, halt_n=False)
        state = _cycle(
            state,
            LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0xCAFE55),
        )
        self.assertEqual(
            read_dreg(state.native.core.core.primary, DREG.AX1),
            ExactWord(16, 0xCAFE),
        )
        self.assertEqual(state.native.core.core.dag.i[4], 0x0101)
        state = _cycle(state, LogicalPhase.STATE_8, halt_n=False)
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = _cycle(state, phase, halt_n=False)
        state = _cycle(
            state,
            LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0x987654),
        )
        self.assertEqual(
            read_dreg(state.native.core.core.primary, DREG.AX1),
            ExactWord(16, 0xCAFE),
        )
        self.assertEqual(state.native.core.core.px, ExactWord(8, 0x55))
        self.assertEqual(state.native.core.core.dag.i[4], 0x0101)

    def test_idle_halt_is_explicitly_outside_this_owner(self) -> None:
        result = apply_shifter_pm_halt_cycle(
            ShifterPMHaltState.reset(),
            phase=LogicalPhase.STATE_3,
            halt_n=False,
        )
        self.assertTrue(result.control.halt_recognized)
        self.assertTrue(result.owner_conflict)
        self.assertTrue(result.integration_conflict)

    def test_reset_clears_native_and_control_state(self) -> None:
        state = ShifterPMHaltState(
            native=_setup_state().native,
            control=apply_shifter_pm_halt_cycle(
                ShifterPMHaltState.reset(),
                phase=LogicalPhase.STATE_3,
                halt_n=False,
            ).state.control,
        )
        result = apply_shifter_pm_halt_cycle(
            state,
            reset=True,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
        )
        self.assertEqual(result.state, ShifterPMHaltState.reset())
        self.assertFalse(result.integration_conflict)


if __name__ == "__main__":
    unittest.main()
