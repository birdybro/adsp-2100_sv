from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    BusControlMode,
    DataBusRequest,
    ExactWord,
    HaltControlMode,
    LinearDMWaitControlState,
    LogicalPhase,
    UNKNOWN,
    apply_linear_dm_wait_control_cycle,
)


def _type7(register_code: int, value: int) -> int:
    return (
        0x300000
        | ((register_code >> 4) << 18)
        | ((value & 0x3FFF) << 4)
        | (register_code & 0xF)
    )


def _type2(*, immediate: int, dag: int, i_local: int, m_local: int) -> int:
    return (
        0xA00000
        | ((dag & 1) << 20)
        | ((immediate & 0xFFFF) << 4)
        | ((i_local & 3) << 2)
        | (m_local & 3)
    )


def _type3(*, write: bool, address: int, register_code: int) -> int:
    return (
        0x800000
        | (int(write) << 20)
        | ((register_code >> 4) << 18)
        | ((address & 0x3FFF) << 4)
        | (register_code & 0xF)
    )


def _type4(
    *,
    dag: int = 0,
    write: bool = False,
    z: int = 0,
    amf: int = 0,
    yop: int = 0,
    xop: int = 0,
    dreg: int = 0,
    i: int = 0,
    m: int = 0,
) -> int:
    return (
        0x600000
        | ((dag & 1) << 20)
        | (int(write) << 19)
        | ((z & 1) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 3) << 11)
        | ((xop & 7) << 8)
        | ((dreg & 0xF) << 4)
        | ((i & 3) << 2)
        | (m & 3)
    )


def _type12(
    *,
    dag: int = 0,
    write: bool = False,
    sf: int = 0,
    xop: int = 0,
    dreg: int = 0,
    i: int = 0,
    m: int = 0,
) -> int:
    return (
        0x120000
        | ((dag & 1) << 16)
        | (int(write) << 15)
        | ((sf & 0xF) << 11)
        | ((xop & 7) << 8)
        | ((dreg & 0xF) << 4)
        | ((i & 3) << 2)
        | (m & 3)
    )


def _type6(register: int, value: int) -> int:
    return 0x400000 | ((value & 0xFFFF) << 4) | (register & 0xF)


def _setup(
    state: LinearDMWaitControlState,
    pc: int,
    opcode: int,
) -> LinearDMWaitControlState:
    result = apply_linear_dm_wait_control_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        instruction_setup=(ExactWord(14, pc), ExactWord(24, opcode)),
    )
    assert result.core.instruction_setup_accepted
    return result.state


def _issue_and_retire(
    state: LinearDMWaitControlState,
    next_opcode: int,
) -> LinearDMWaitControlState:
    issue = apply_linear_dm_wait_control_cycle(
        state,
        phase=LogicalPhase.STATE_8,
    )
    assert issue.core.instruction_issue
    retire = apply_linear_dm_wait_control_cycle(
        issue.state,
        phase=LogicalPhase.STATE_7,
        pmd_read_data=ExactWord(24, next_opcode),
    )
    assert retire.core.retire_event
    return retire.state


def _irq2_edge_configuration() -> LinearDMWaitControlState:
    state = _setup(
        LinearDMWaitControlState.reset(),
        0x100,
        _type7(0x34, 0x04),
    )
    state = _issue_and_retire(state, _type7(0x33, 0x04))
    state = _issue_and_retire(state, 0x000000)
    assert state.core.architecture.icntl.value == 0x04
    assert state.core.architecture.imask.value == 0x04
    assert state.core.interrupt.sample_history_valid
    return state


class LinearDMWaitControlTests(unittest.TestCase):
    def test_machine_readable_composition_contract(self) -> None:
        contract = json.loads(
            Path(
                "docs/generated/adsp2100_linear_dm_wait_control.yaml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(
            contract["dm_owner"],
            "FETCHED_TYPE2_TYPE3_TYPE4_TYPE12_PLUS_RAW_STRUCTURAL_COMPANION",
        )
        self.assertEqual(
            contract["fetched_instruction_owner"],
            "ALL_TYPE2_ALL_LEGAL_TYPE3_ALL_SUPPORTED_TYPE4_AND_TYPE12_WORDS",
        )
        self.assertEqual(
            contract["bus_request_during_dm"],
            "RECOGNIZED_AT_PHYSICAL_STATE_3_BUT_GRANT_SERVICE_DEFERRED_UNTIL_DM_COMPLETION",
        )
        self.assertEqual(
            contract["raw_descriptor_collision"],
            "ATOMIC_PREFLIGHT_REJECTS_BOTH_FETCHED_AND_RAW_REQUESTS_BEFORE_EITHER_PM_OR_DM_CONTROLLER_ACCEPTS_AND_RETAINS_THE_FETCHED_INSTRUCTION_FOR_A_LATER_RETRY",
        )
        self.assertIn(
            "PAIRED_PM_DM_COMPLETION",
            contract["halt_during_dm"],
        )
        self.assertIn("DMACK_HIGH", contract["halt_release"])
        self.assertIn("FAIL_CLOSED", contract["br_halt_collision"])
        self.assertIn("ACTIVE_HALT_OR_NORMAL_BUS", contract["br_halt_active_owner"])

    def test_br_waits_for_fetched_dm_then_masks_both_buses(self) -> None:
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0100,
            _type7(0x10, 0x0200),
        )
        state = _issue_and_retire(state, _type7(0x14, 1))
        state = _issue_and_retire(
            state,
            _type2(immediate=0xBEEF, dag=0, i_local=0, m_local=0),
        )
        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.fetched_dm_accepted)
        state = issue.state

        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = apply_linear_dm_wait_control_cycle(
                state, phase=phase
            ).state
        recognized = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(recognized.control.request_recognized)
        self.assertEqual(
            recognized.state.control.mode,
            BusControlMode.REQUEST_DELAY,
        )
        self.assertFalse(recognized.control.bus_relinquished)
        state = recognized.state

        for phase in (LogicalPhase.STATE_4, LogicalPhase.STATE_5):
            state = apply_linear_dm_wait_control_cycle(
                state, phase=phase, br_n=False
            ).state
        low_ack = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            br_n=False,
            dm_ack=False,
        )
        self.assertTrue(low_ack.dm_bus.wait_extension_event)
        state = low_ack.state
        for phase in (
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            held = apply_linear_dm_wait_control_cycle(
                state, phase=phase, br_n=False
            )
            self.assertFalse(held.control.grant_assert_event)
            state = held.state
        deferred = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(deferred.control.state_three_boundary)
        self.assertFalse(deferred.control.grant_assert_event)
        self.assertEqual(
            deferred.state.control.mode,
            BusControlMode.REQUEST_DELAY,
        )
        state = deferred.state
        for phase in (LogicalPhase.STATE_4, LogicalPhase.STATE_5):
            state = apply_linear_dm_wait_control_cycle(
                state, phase=phase, br_n=False
            ).state
        accepted = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            br_n=False,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            accepted.state,
            phase=LogicalPhase.STATE_7,
            br_n=False,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.dm_bus.completion_event)
        self.assertTrue(completed.core.retire_event)
        state = completed.state

        for phase in (
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            blocked = apply_linear_dm_wait_control_cycle(
                state, phase=phase, br_n=False
            )
            self.assertFalse(blocked.core.instruction_issue)
            state = blocked.state
        grant = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(grant.control.grant_assert_event)
        self.assertEqual(grant.state.control.mode, BusControlMode.GRANTED)
        visible = apply_linear_dm_wait_control_cycle(
            grant.state,
            phase=LogicalPhase.STATE_4,
            br_n=False,
        )
        self.assertTrue(visible.native_bus_relinquished)
        self.assertFalse(visible.native_bg_n)
        self.assertFalse(visible.core.bus.address_output_enable)
        self.assertFalse(visible.core.bus.control_output_enable)
        self.assertFalse(visible.core.bus.data_output_enable)
        self.assertFalse(visible.dm_bus.address_output_enable)
        self.assertFalse(visible.dm_bus.control_output_enable)
        self.assertFalse(visible.dm_bus.data_output_enable)

    def test_br_first_sampled_during_wait_is_latched(self) -> None:
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0200,
            _type7(0x10, 0x0300),
        )
        state = _issue_and_retire(state, _type7(0x14, 1))
        state = _issue_and_retire(
            state,
            _type2(immediate=0xCAFE, dag=0, i_local=0, m_local=0),
        )
        state = apply_linear_dm_wait_control_cycle(
            state, phase=LogicalPhase.STATE_8
        ).state
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            state = apply_linear_dm_wait_control_cycle(
                state, phase=phase
            ).state
        state = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        ).state
        for phase in (
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            state = apply_linear_dm_wait_control_cycle(
                state, phase=phase
            ).state
        recognized = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(recognized.dm_bus.waiting)
        self.assertTrue(recognized.control.request_recognized)
        self.assertFalse(recognized.control.grant_assert_event)
        self.assertEqual(
            recognized.state.control.mode,
            BusControlMode.REQUEST_DELAY,
        )

    def test_halt_during_dm_wait_completes_then_holds_state_eight(self) -> None:
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0280,
            _type7(0x10, 0x0340),
        )
        state = _issue_and_retire(state, _type7(0x14, 1))
        state = _issue_and_retire(
            state,
            _type2(immediate=0x5AA5, dag=0, i_local=0, m_local=0),
        )
        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.fetched_dm_accepted)
        state = issue.state

        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = apply_linear_dm_wait_control_cycle(
                state, phase=phase
            ).state
        recognized = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            halt_n=False,
        )
        self.assertTrue(recognized.halt.halt_recognized)
        self.assertEqual(
            recognized.state.halt.mode,
            HaltControlMode.STOP_PENDING,
        )
        state = recognized.state

        for phase in (LogicalPhase.STATE_4, LogicalPhase.STATE_5):
            state = apply_linear_dm_wait_control_cycle(
                state, phase=phase, halt_n=False
            ).state
        low_ack = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            halt_n=False,
            dm_ack=False,
        )
        self.assertTrue(low_ack.dm_bus.wait_extension_event)
        deferred = apply_linear_dm_wait_control_cycle(
            low_ack.state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
        )
        self.assertFalse(deferred.halt.halt_stop_event)
        self.assertTrue(deferred.effective_phase_advance)
        self.assertFalse(deferred.architectural_phase_advance)
        self.assertFalse(deferred.core.retire_event)
        state = deferred.state

        for phase in (
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held_instruction = apply_linear_dm_wait_control_cycle(
                state, phase=phase, halt_n=False
            )
            self.assertFalse(held_instruction.core.retire_event)
            state = held_instruction.state
        accepted = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            halt_n=False,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            accepted.state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.dm_bus.completion_event)
        self.assertTrue(completed.core.retire_event)
        self.assertTrue(completed.halt.halt_stop_event)
        self.assertEqual(
            completed.state.halt.mode,
            HaltControlMode.HALTED,
        )
        self.assertFalse(completed.integration_conflict)

        stopped = apply_linear_dm_wait_control_cycle(
            completed.state,
            phase=LogicalPhase.STATE_8,
            halt_n=False,
        )
        self.assertTrue(stopped.halt.halted)
        self.assertTrue(stopped.halt.phase_hold)
        self.assertFalse(stopped.effective_phase_advance)
        self.assertFalse(stopped.core.instruction_issue)
        self.assertTrue(stopped.core.bus.control_output_enable)
        self.assertTrue(stopped.dm_bus.control_output_enable)

        blocked = apply_linear_dm_wait_control_cycle(
            stopped.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dm_ack=False,
        )
        self.assertTrue(blocked.halt.release_blocked)
        self.assertFalse(blocked.effective_phase_advance)
        resumed = apply_linear_dm_wait_control_cycle(
            blocked.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dm_ack=True,
        )
        self.assertTrue(resumed.halt.resume_event)
        self.assertTrue(resumed.effective_phase_advance)
        self.assertTrue(resumed.core.instruction_issue)
        self.assertEqual(
            resumed.state.halt.mode,
            HaltControlMode.RUNNING,
        )

    def test_simultaneous_br_and_halt_fail_closed(self) -> None:
        state = _setup(LinearDMWaitControlState.reset(), 0x02C0, 0)
        state = apply_linear_dm_wait_control_cycle(
            state, phase=LogicalPhase.STATE_8
        ).state
        overlap = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
            halt_n=False,
        )
        self.assertTrue(overlap.halt_br_conflict)
        self.assertTrue(overlap.integration_conflict)
        self.assertFalse(overlap.halt.halt_recognized)
        self.assertFalse(overlap.control.request_recognized)
        self.assertEqual(
            overlap.state.halt.mode,
            HaltControlMode.RUNNING,
        )
        self.assertEqual(
            overlap.state.control.mode,
            BusControlMode.IDLE,
        )

    def test_cross_request_preserves_active_halt_or_bus_owner(self) -> None:
        state = _setup(LinearDMWaitControlState.reset(), 0x02D0, 0)
        state = apply_linear_dm_wait_control_cycle(
            state, phase=LogicalPhase.STATE_8
        ).state
        recognized_halt = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            halt_n=False,
        )
        self.assertTrue(recognized_halt.halt.halt_recognized)
        stopped = apply_linear_dm_wait_control_cycle(
            recognized_halt.state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(stopped.halt.halt_stop_event)
        halted_cross_request = apply_linear_dm_wait_control_cycle(
            stopped.state,
            phase=LogicalPhase.STATE_8,
            br_n=False,
            halt_n=False,
        )
        self.assertTrue(halted_cross_request.halt_br_conflict)
        self.assertTrue(halted_cross_request.halt.halted)
        self.assertFalse(halted_cross_request.halt.resume_event)
        self.assertEqual(
            halted_cross_request.state.control.mode,
            BusControlMode.IDLE,
        )

        state = _setup(LinearDMWaitControlState.reset(), 0x02E0, 0)
        state = apply_linear_dm_wait_control_cycle(
            state, phase=LogicalPhase.STATE_8
        ).state
        recognized_br = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(recognized_br.control.request_recognized)
        bus_cross_request = apply_linear_dm_wait_control_cycle(
            recognized_br.state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
            halt_n=False,
        )
        self.assertTrue(bus_cross_request.halt_br_conflict)
        self.assertTrue(bus_cross_request.control.grant_assert_event)
        self.assertFalse(bus_cross_request.control.request_withdrawn)
        self.assertEqual(
            bus_cross_request.state.control.mode,
            BusControlMode.GRANTED,
        )
        self.assertEqual(
            bus_cross_request.state.halt.mode,
            HaltControlMode.RUNNING,
        )

    def test_fetched_type12_waited_write_uses_old_dreg_then_shifts(self) -> None:
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0E00,
            _type6(8, 0x1234),
        )
        for opcode in (
            _type6(9, 0),
            _type6(14, 0x5678),
            _type6(15, 0x9ABC),
            _type7(0x30, 0),
            _type7(0x10, 0x0100),
            _type7(0x14, 1),
            _type7(0x18, 0),
            _type12(write=True, dreg=14),
        ):
            state = _issue_and_retire(state, opcode)

        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.fetched_dm_accepted)
        self.assertTrue(issue.state.dm_bus.write)
        self.assertEqual(issue.state.dm_bus.address.value, 0x0100)
        self.assertEqual(issue.state.dm_bus.write_data.value, 0x5678)
        self.assertEqual(issue.state.core.architecture.primary.sr[0].value, 0x5678)

        low_ack = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        self.assertTrue(low_ack.dm_bus.wait_extension_event)
        self.assertEqual(low_ack.state.core.architecture.primary.sr[0].value, 0x5678)

        state = low_ack.state
        for phase in (
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held = apply_linear_dm_wait_control_cycle(state, phase=phase)
            self.assertFalse(held.core.retire_event)
            self.assertEqual(held.state.core.architecture.primary.sr[0].value, 0x5678)
            state = held.state

        qualified = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.core.retire_event)
        self.assertEqual(completed.state.core.architecture.primary.sr[0].value, 0)
        self.assertEqual(completed.state.core.architecture.primary.sr[1].value, 0x1234)
        self.assertEqual(completed.state.core.architecture.dag.i[0].value, 0x0101)
        self.assertFalse(completed.integration_conflict)

    def test_fetched_type12_read_commits_shift_load_and_i_together(self) -> None:
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0F00,
            _type6(8, 0x2468),
        )
        for opcode in (
            _type6(9, 0),
            _type6(0, 0x1111),
            _type7(0x30, 0),
            _type7(0x10, 0x0200),
            _type7(0x14, 0x3FFF),
            _type7(0x18, 0),
            _type12(dreg=0),
        ):
            state = _issue_and_retire(state, opcode)

        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.fetched_dm_accepted)
        self.assertFalse(issue.state.dm_bus.write)
        self.assertEqual(issue.state.core.architecture.primary.ax[0].value, 0x1111)
        self.assertIs(issue.state.core.architecture.primary.sr[0], UNKNOWN)

        qualified = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xBEEF),
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.core.retire_event)
        self.assertEqual(completed.state.core.architecture.primary.ax[0].value, 0xBEEF)
        self.assertEqual(completed.state.core.architecture.primary.sr[0].value, 0)
        self.assertEqual(completed.state.core.architecture.primary.sr[1].value, 0x2468)
        self.assertEqual(completed.state.core.architecture.dag.i[0].value, 0x01FF)
        self.assertFalse(completed.integration_conflict)

    def test_fetched_type12_read_collision_fails_closed(self) -> None:
        collision = _type12(dreg=14)
        state = _setup(LinearDMWaitControlState.reset(), 0x1000, collision)
        result = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(result.core.reserved_subencoding)
        self.assertFalse(result.core.instruction_issue)
        self.assertFalse(result.fetched_dm_accepted)

    def test_fetched_type4_waited_write_uses_old_dreg_then_commits_alu(self) -> None:
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0B00,
            _type6(0, 2),
        )
        for opcode in (
            _type6(4, 3),
            _type6(10, 0x7777),
            _type7(0x30, 0),
            _type7(0x10, 0x0120),
            _type7(0x14, 1),
            _type7(0x18, 0),
            0x6A60A0,
        ):
            state = _issue_and_retire(state, opcode)

        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.fetched_dm_accepted)
        self.assertTrue(issue.state.dm_bus.write)
        self.assertEqual(issue.state.dm_bus.address.value, 0x0120)
        self.assertEqual(issue.state.dm_bus.write_data.value, 0x7777)
        self.assertEqual(issue.state.core.architecture.primary.ar.value, 0x7777)

        low_ack = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        self.assertTrue(low_ack.dm_bus.wait_extension_event)
        self.assertEqual(low_ack.state.core.architecture.primary.ar.value, 0x7777)

        state = low_ack.state
        for phase in (
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held = apply_linear_dm_wait_control_cycle(state, phase=phase)
            self.assertFalse(held.core.retire_event)
            self.assertEqual(held.state.core.architecture.primary.ar.value, 0x7777)
            state = held.state

        qualified = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.core.retire_event)
        self.assertEqual(completed.state.core.architecture.primary.ar.value, 5)
        self.assertEqual(completed.state.core.architecture.dag.i[0].value, 0x0121)
        self.assertFalse(completed.integration_conflict)

    def test_fetched_type4_read_commits_compute_load_and_i_together(self) -> None:
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0C00,
            _type6(0, 2),
        )
        for opcode in (
            _type6(4, 3),
            _type7(0x30, 0),
            _type7(0x10, 0x0080),
            _type7(0x17, 0x3FFF),
            _type7(0x18, 0),
            0x626003,
        ):
            state = _issue_and_retire(state, opcode)

        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.fetched_dm_accepted)
        self.assertFalse(issue.state.dm_bus.write)
        self.assertEqual(issue.state.core.architecture.primary.ax[0].value, 2)
        self.assertEqual(issue.state.core.architecture.primary.ar, UNKNOWN)

        qualified = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xCAFE),
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertEqual(completed.state.core.architecture.primary.ar.value, 5)
        self.assertEqual(completed.state.core.architecture.primary.ax[0].value, 0xCAFE)
        self.assertEqual(completed.state.core.architecture.dag.i[0].value, 0x007F)
        self.assertFalse(completed.integration_conflict)

    def test_fetched_type4_read_collision_fails_closed(self) -> None:
        collision = _type4(amf=0x13, dreg=10)
        state = _setup(LinearDMWaitControlState.reset(), 0x0D00, collision)
        result = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(result.core.reserved_subencoding)
        self.assertFalse(result.core.instruction_issue)
        self.assertFalse(result.fetched_dm_accepted)

    def test_fetched_type3_write_captures_old_register_and_waits(self) -> None:
        type3_write = _type3(
            write=True,
            address=0x3FFF,
            register_code=0x00,
        )
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0600,
            _type6(0, 0xCAFE),
        )
        state = _issue_and_retire(state, type3_write)

        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.fetched_dm_accepted)
        self.assertTrue(issue.state.dm_bus.write)
        self.assertEqual(issue.state.dm_bus.address.value, 0x3FFF)
        self.assertEqual(issue.state.dm_bus.write_data.value, 0xCAFE)

        low_ack = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        self.assertTrue(low_ack.dm_bus.wait_extension_event)
        self.assertEqual(
            low_ack.state.core.architecture.primary.ax[0].value,
            0xCAFE,
        )

        state = low_ack.state
        for phase in (
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held = apply_linear_dm_wait_control_cycle(state, phase=phase)
            self.assertFalse(held.core.retire_event)
            state = held.state

        qualified = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.dm_bus.completion_event)
        self.assertTrue(completed.core.retire_event)
        self.assertEqual(completed.state.core.architecture.pc.value, 0x0602)

    def test_fetched_type3_read_commits_only_at_completion(self) -> None:
        type3_read = _type3(
            write=False,
            address=0x0000,
            register_code=0x00,
        )
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0700,
            _type6(0, 0x1111),
        )
        state = _issue_and_retire(state, type3_read)
        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.fetched_dm_accepted)
        self.assertFalse(issue.state.dm_bus.write)
        self.assertEqual(
            issue.state.core.architecture.primary.ax[0].value,
            0x1111,
        )

        qualified = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xBEEF),
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.dm_bus.read_sample_event)
        self.assertEqual(
            completed.state.core.architecture.primary.ax[0].value,
            0xBEEF,
        )
        self.assertFalse(completed.integration_conflict)

    def test_fetched_type3_cntr_read_pushes_old_value(self) -> None:
        type3_cntr_read = _type3(
            write=False,
            address=0x1234,
            register_code=0x35,
        )
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0800,
            _type7(0x35, 0x0033),
        )
        state = _issue_and_retire(state, type3_cntr_read)
        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        qualified = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0x0044),
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertEqual(completed.state.core.architecture.cntr.value, 0x44)
        self.assertEqual(
            completed.state.core.architecture.count_stack[-1].value,
            0x33,
        )

    def test_fetched_type3_reserved_destination_fails_closed(self) -> None:
        read_sstat = _type3(
            write=False,
            address=0x0100,
            register_code=0x32,
        )
        state = _setup(LinearDMWaitControlState.reset(), 0x0900, read_sstat)
        result = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(result.core.reserved_subencoding)
        self.assertFalse(result.core.instruction_issue)
        self.assertFalse(result.fetched_dm_accepted)

    def test_fetched_type3_narrow_source_remains_provisional(self) -> None:
        type3_astat_write = _type3(
            write=True,
            address=0x0020,
            register_code=0x30,
        )
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0A00,
            _type7(0x30, 0x00A5),
        )
        state = _issue_and_retire(state, type3_astat_write)
        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        qualified = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.core.provisional_source_extension)
        self.assertEqual(completed.dm_bus.state.write_data.value, 0x00A5)

    def test_fetched_type2_waits_and_postmodifies_only_at_completion(self) -> None:
        type2 = _type2(immediate=0xBEEF, dag=0, i_local=0, m_local=0)
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0200,
            _type7(0x10, 0x0120),
        )
        state = _issue_and_retire(state, _type7(0x14, 0x0003))
        state = _issue_and_retire(state, _type7(0x18, 0x0000))
        state = _issue_and_retire(state, type2)

        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issue.core.instruction_issue)
        self.assertTrue(issue.fetched_dm_accepted)
        self.assertTrue(issue.dm_bus.request_accepted)
        self.assertEqual(issue.state.dm_bus.address.value, 0x0120)
        self.assertEqual(issue.state.dm_bus.write_data.value, 0xBEEF)
        self.assertEqual(issue.state.core.architecture.dag.i[0].value, 0x0120)

        low_ack = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        self.assertTrue(low_ack.dm_bus.wait_extension_event)
        self.assertEqual(
            low_ack.state.core.architecture.dag.i[0].value,
            0x0120,
        )

        state = low_ack.state
        for phase in (
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held = apply_linear_dm_wait_control_cycle(state, phase=phase)
            self.assertFalse(held.core.retire_event)
            self.assertEqual(
                held.state.core.architecture.dag.i[0].value,
                0x0120,
            )
            state = held.state

        qualified = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        completed = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.dm_bus.completion_event)
        self.assertTrue(completed.core.retire_event)
        self.assertEqual(
            completed.state.core.architecture.dag.i[0].value,
            0x0123,
        )
        self.assertEqual(completed.state.core.architecture.pc.value, 0x0204)
        self.assertFalse(completed.integration_conflict)

    def test_raw_and_fetched_descriptors_fail_closed_before_pm_issue(self) -> None:
        type2 = _type2(immediate=0xCAFE, dag=1, i_local=0, m_local=0)
        state = _setup(
            LinearDMWaitControlState.reset(),
            0x0300,
            _type7(0x20, 0x0444),
        )
        state = _issue_and_retire(state, _type7(0x24, 0x0001))
        state = _issue_and_retire(state, _type7(0x28, 0x0000))
        state = _issue_and_retire(state, type2)

        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            dm_request=DataBusRequest.write_word(0x0111, 0x2222),
        )
        self.assertFalse(issue.core.instruction_issue)
        self.assertFalse(issue.core.bus.request_accepted)
        self.assertFalse(issue.dm_bus.request_accepted)
        self.assertFalse(issue.fetched_dm_accepted)
        self.assertFalse(issue.dm_companion_accepted)
        self.assertTrue(issue.dm_owner_bus.request_conflict)
        self.assertFalse(issue.state.core.pending)
        self.assertTrue(issue.state.core.instruction_valid)
        self.assertTrue(issue.attachment_conflict)
        self.assertTrue(issue.integration_conflict)

        retry = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(retry.core.instruction_issue)
        self.assertTrue(retry.fetched_dm_accepted)
        self.assertEqual(retry.state.dm_bus.address.value, 0x0444)
        self.assertEqual(retry.state.dm_bus.write_data.value, 0xCAFE)

    def test_paired_read_completes_with_the_ordinary_fetch(self) -> None:
        state = _setup(LinearDMWaitControlState.reset(), 0x20, 0)
        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            dm_request=DataBusRequest.read(0x1234),
        )
        self.assertTrue(issue.core.instruction_issue)
        self.assertTrue(issue.dm_companion_accepted)
        self.assertFalse(issue.integration_conflict)

        qualified = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        done = apply_linear_dm_wait_control_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xCAFE),
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(done.core.retire_event)
        self.assertTrue(done.core.bus.completion_event)
        self.assertTrue(done.dm_bus.completion_event)
        self.assertTrue(done.dm_bus.read_sample_event)
        self.assertFalse(done.integration_conflict)

    def test_edge_irq_is_latched_but_not_serviced_during_dm_wait(self) -> None:
        state = _irq2_edge_configuration()
        issue = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            dm_request=DataBusRequest.read(0x0555),
        )
        low_ack = apply_linear_dm_wait_control_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        self.assertTrue(low_ack.dm_bus.wait_extension_event)

        sampled = apply_linear_dm_wait_control_cycle(
            low_ack.state,
            phase=LogicalPhase.STATE_7,
            irq_n=0xB,
        )
        self.assertTrue(sampled.interrupt_wait_sample)
        self.assertFalse(sampled.architectural_phase_advance)
        self.assertEqual(sampled.state.core.interrupt.edge_pending, 0x4)
        self.assertFalse(sampled.core.interrupt_recognition_event)
        self.assertFalse(sampled.core.retire_event)

        state = sampled.state
        for phase in (
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held = apply_linear_dm_wait_control_cycle(
                state,
                phase=phase,
                irq_n=0xF,
            )
            self.assertFalse(held.architectural_phase_advance)
            self.assertFalse(held.core.retire_event)
            self.assertFalse(held.core.interrupt_recognition_event)
            self.assertEqual(held.state.core.interrupt.edge_pending, 0x4)
            state = held.state

        acknowledged = apply_linear_dm_wait_control_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
            irq_n=0xF,
        )
        self.assertTrue(acknowledged.dm_bus.dmack_accepted)
        self.assertFalse(acknowledged.architectural_phase_advance)

        completed = apply_linear_dm_wait_control_cycle(
            acknowledged.state,
            phase=LogicalPhase.STATE_7,
            irq_n=0xF,
            dmd_read_data=ExactWord(16, 0x1357),
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(completed.architectural_phase_advance)
        self.assertTrue(completed.core.retire_event)
        self.assertTrue(completed.dm_bus.completion_event)
        self.assertTrue(completed.core.interrupt_recognition_event)
        self.assertEqual(completed.core.interrupt_level, 2)
        self.assertTrue(completed.state.core.interrupt_vectoring)
        self.assertEqual(completed.state.core.interrupt.edge_pending, 0)
        self.assertFalse(completed.integration_conflict)

        entry = apply_linear_dm_wait_control_cycle(
            completed.state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(entry.core.interrupt_entry_event)
        self.assertTrue(entry.core.interrupt_vector_issue_event)
        self.assertFalse(entry.dm_companion_accepted)
        self.assertEqual(len(entry.state.core.architecture.pc_stack), 1)
        self.assertEqual(len(entry.state.core.architecture.status_stack), 1)

    def test_raw_dm_descriptor_fails_closed_without_fetch_partner(self) -> None:
        idle = apply_linear_dm_wait_control_cycle(
            LinearDMWaitControlState.reset(),
            phase=LogicalPhase.STATE_8,
            dm_request=DataBusRequest.read(0x123),
        )
        self.assertFalse(idle.dm_companion_accepted)
        self.assertTrue(idle.attachment_conflict)
        self.assertTrue(idle.integration_conflict)

        off_phase = apply_linear_dm_wait_control_cycle(
            LinearDMWaitControlState.reset(),
            phase=LogicalPhase.STATE_4,
            dm_request=DataBusRequest.read(0x123),
        )
        self.assertFalse(off_phase.dm_companion_accepted)
        self.assertTrue(off_phase.phase_conflict)
        self.assertTrue(off_phase.integration_conflict)


if __name__ == "__main__":
    unittest.main()
