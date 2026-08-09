from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    ExactWord,
    HaltControlMode,
    HaltControlState,
    LinearHaltControlState,
    LogicalPhase,
    apply_halt_control_cycle,
    apply_linear_halt_control_cycle,
    register_code_by_name,
)


ROOT = Path(__file__).resolve().parents[1]


def _type22(condition: int) -> int:
    return 0x080000 | (condition & 0xF)


def _type7(code: int, data: int) -> int:
    return (
        0x300000
        | ((code >> 4) << 18)
        | ((data & 0x3FFF) << 4)
        | (code & 0xF)
    )


def _setup(opcode: int = 0, pc: int = 4) -> LinearHaltControlState:
    result = apply_linear_halt_control_cycle(
        LinearHaltControlState.reset(),
        phase=LogicalPhase.STATE_8,
        instruction_setup=(ExactWord(14, pc), ExactWord(24, opcode)),
    )
    assert result.core.instruction_setup_accepted
    return result.state


class HaltControlTests(unittest.TestCase):
    def test_machine_readable_halt_contract(self) -> None:
        contract = json.loads(
            (ROOT / "docs/generated/adsp2100_halt_control.yaml")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(contract["pin_polarity"]["HALT"], "ACTIVE_LOW")
        self.assertIn("STATE_3", contract["recognition"])
        self.assertIn("DMACK_HIGH", contract["release_requirement"])
        self.assertIn(
            "FORCED_EXTERNAL_INSTRUCTION_FETCH",
            contract["pm_data_effect"],
        )
        self.assertIn(
            "TYPE_5_COMPUTE_PM_NATIVE_OWNER",
            contract["implemented_attachments"],
        )
        self.assertNotIn(
            "TYPE_5_PROGRAM_MEMORY_DATA_OWNER_ATTACHMENT",
            contract["excluded_claims"],
        )
        self.assertIn(
            "TYPE_13_SHIFTER_PM_NATIVE_OWNER",
            contract["implemented_attachments"],
        )
        self.assertIn(
            "FETCHED_TYPE_22_TRAP_HANDOFF_ON_THE_ORDINARY_LINEAR_OWNER",
            contract["implemented_attachments"],
        )
        self.assertIn(
            "RETAINED_STATE_7_IRQ_SERVICE_DEFERRAL_AND_VECTOR_ENTRY_ON_ORDINARY_HALT_RESUME",
            contract["implemented_attachments"],
        )
        self.assertIn(
            "FETCHED_TYPE2_TYPE3_TYPE4_TYPE12_NATIVE_DM_WAIT_OWNER",
            contract["implemented_attachments"],
        )
        self.assertNotIn(
            "HALT_DURING_DMACK_WAIT",
            contract["excluded_claims"],
        )
        self.assertNotIn(
            "TRAP_TO_HALT_HANDOFF",
            contract["excluded_claims"],
        )
        self.assertIn(
            "IRQ_PULSE_CAPTURE_WITHOUT_A_STATE_7_SAMPLE",
            contract["excluded_claims"],
        )

    def test_pm_data_halt_forces_one_external_fetch_before_stop(self) -> None:
        recognized = apply_halt_control_cycle(
            HaltControlState(),
            phase=LogicalPhase.STATE_3,
            halt_n=False,
            pm_data_cycle=True,
        )
        self.assertTrue(recognized.halt_recognized)
        self.assertEqual(
            recognized.state.mode,
            HaltControlMode.FORCE_FETCH_PENDING,
        )
        data_completion = apply_halt_control_cycle(
            recognized.state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
        )
        self.assertFalse(data_completion.halt_stop_event)
        self.assertFalse(data_completion.force_fetch_issue)
        forced = apply_halt_control_cycle(
            data_completion.state,
            phase=LogicalPhase.STATE_8,
            halt_n=False,
        )
        self.assertTrue(forced.force_fetch_issue)
        self.assertFalse(forced.instruction_issue_inhibit)
        self.assertEqual(forced.state.mode, HaltControlMode.STOP_PENDING)
        stopped = apply_halt_control_cycle(
            forced.state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
        )
        self.assertTrue(stopped.halt_stop_event)
        self.assertEqual(stopped.state.mode, HaltControlMode.HALTED)

    def test_halt_is_recognized_only_at_enabled_state_three(self) -> None:
        state = HaltControlState()
        for phase, advance in (
            (LogicalPhase.STATE_2, True),
            (LogicalPhase.STATE_3, False),
        ):
            result = apply_halt_control_cycle(
                state,
                phase=phase,
                phase_advance=advance,
                halt_n=False,
            )
            self.assertFalse(result.halt_recognized)
            self.assertEqual(result.state, state)
        recognized = apply_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            halt_n=False,
        )
        self.assertTrue(recognized.halt_recognized)
        self.assertTrue(recognized.instruction_issue_inhibit)
        self.assertEqual(
            recognized.state.mode,
            HaltControlMode.STOP_PENDING,
        )

    def test_stop_waits_for_composed_service_completion(self) -> None:
        pending = HaltControlState(HaltControlMode.STOP_PENDING)
        deferred = apply_halt_control_cycle(
            pending,
            phase=LogicalPhase.STATE_7,
            service_inhibit=True,
        )
        self.assertFalse(deferred.halt_stop_event)
        self.assertTrue(deferred.effective_phase_advance)
        self.assertEqual(deferred.state, pending)

        completed = apply_halt_control_cycle(
            deferred.state,
            phase=LogicalPhase.STATE_7,
            service_inhibit=False,
        )
        self.assertTrue(completed.halt_stop_event)
        self.assertEqual(completed.state.mode, HaltControlMode.HALTED)

    def test_current_fetch_retires_before_state_eight_stop(self) -> None:
        state = _setup()
        issued = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issued.core.instruction_issue)
        state = issued.state
        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = apply_linear_halt_control_cycle(
                state, phase=phase, halt_n=False
            ).state
        recognized = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            halt_n=False,
        )
        self.assertTrue(recognized.control.halt_recognized)
        state = recognized.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            active = apply_linear_halt_control_cycle(
                state, phase=phase, halt_n=False
            )
            self.assertTrue(active.core.bus.address_output_enable)
            self.assertTrue(active.core.bus.control_output_enable)
            state = active.state
        stopped = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(stopped.control.halt_stop_event)
        self.assertTrue(stopped.core.retire_event)
        self.assertEqual(stopped.state.core.architecture.pc, ExactWord(14, 5))
        self.assertEqual(stopped.state.control.mode, HaltControlMode.HALTED)

    def test_halted_state_keeps_state_eight_pm_outputs_static(self) -> None:
        state = _setup()
        state = apply_linear_halt_control_cycle(
            state, phase=LogicalPhase.STATE_8
        ).state
        state = apply_linear_halt_control_cycle(
            state, phase=LogicalPhase.STATE_3, halt_n=False
        ).state
        state = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0),
        ).state

        observations = []
        for _ in range(4):
            held = apply_linear_halt_control_cycle(
                state,
                phase=LogicalPhase.STATE_8,
                halt_n=False,
            )
            self.assertTrue(held.control.halted)
            self.assertTrue(held.control.phase_hold)
            self.assertFalse(held.control.effective_phase_advance)
            self.assertFalse(held.core.instruction_issue)
            self.assertTrue(held.core.bus.state.active)
            observations.append(
                (
                    held.core.bus.address,
                    held.core.bus.pms_n,
                    held.core.bus.pmrd_n,
                    held.core.bus.control_output_enable,
                )
            )
            state = held.state
        self.assertTrue(all(item == observations[0] for item in observations))

    def test_release_requires_dmack_then_resumes_at_state_one(self) -> None:
        state = LinearHaltControlState(
            core=_setup().core,
            control=HaltControlState(HaltControlMode.HALTED),
        )
        blocked = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=False,
        )
        self.assertTrue(blocked.control.release_blocked)
        self.assertTrue(blocked.control.phase_hold)
        self.assertFalse(blocked.core.instruction_issue)
        resumed = apply_linear_halt_control_cycle(
            blocked.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=True,
        )
        self.assertTrue(resumed.control.resume_event)
        self.assertFalse(resumed.control.instruction_issue_inhibit)
        self.assertTrue(resumed.control.effective_phase_advance)
        self.assertTrue(resumed.core.instruction_issue)
        self.assertEqual(resumed.state.control.mode, HaltControlMode.RUNNING)

    def test_taken_fetched_trap_holds_acknowledges_and_resumes_pc_plus_one(self) -> None:
        state = _setup(_type22(0xF), pc=0x0200)
        issued = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issued.core.instruction_issue)
        state = issued.state
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = apply_linear_halt_control_cycle(
                state,
                phase=phase,
            ).state
        retired = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(retired.core.retire_event)
        self.assertTrue(retired.trap_event)
        self.assertEqual(retired.state.core.architecture.pc, ExactWord(14, 0x0201))
        self.assertTrue(retired.state.trap_asserted)

        held = apply_linear_halt_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(held.trap_asserted)
        self.assertTrue(held.control.phase_hold)
        self.assertTrue(held.control.halted)
        self.assertFalse(held.core.instruction_issue)

        acknowledged = apply_linear_halt_control_cycle(
            held.state,
            phase=LogicalPhase.STATE_8,
            halt_n=False,
        )
        self.assertTrue(acknowledged.trap_halt_recognized)
        self.assertFalse(acknowledged.state.trap_asserted)
        self.assertTrue(acknowledged.state.trap_handoff)

        handoff = apply_linear_halt_control_cycle(
            acknowledged.state,
            phase=LogicalPhase.STATE_8,
            halt_n=False,
        )
        self.assertTrue(handoff.trap_handoff)
        self.assertTrue(handoff.control.phase_hold)

        blocked = apply_linear_halt_control_cycle(
            handoff.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=False,
        )
        self.assertTrue(blocked.trap_release_blocked)
        self.assertTrue(blocked.control.release_blocked)
        self.assertTrue(blocked.control.phase_hold)

        resumed = apply_linear_halt_control_cycle(
            blocked.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=True,
        )
        self.assertTrue(resumed.trap_resume_event)
        self.assertTrue(resumed.control.resume_event)
        self.assertFalse(resumed.control.phase_hold)
        self.assertTrue(resumed.core.instruction_issue)
        self.assertFalse(resumed.state.trap_handoff)

    def test_fetched_trap_and_ordinary_halt_overlap_is_flagged(self) -> None:
        state = _setup(_type22(0xF), pc=0x0300)
        state = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        ).state
        state = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            halt_n=False,
        ).state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = apply_linear_halt_control_cycle(
                state,
                phase=phase,
                halt_n=False,
            ).state
        retired = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(retired.trap_event)
        self.assertTrue(retired.trap_halt_conflict)
        self.assertTrue(retired.control.phase_conflict)

    def test_recognized_irq_is_deferred_until_halt_resume(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            _type7(writable["ICNTL"], 0x10),
            pc=0x0100,
        )
        for next_opcode in (_type7(writable["IMASK"], 0xF), 0):
            state = apply_linear_halt_control_cycle(
                state, phase=LogicalPhase.STATE_8
            ).state
            for phase in range(6):
                state = apply_linear_halt_control_cycle(
                    state, phase=LogicalPhase(phase)
                ).state
            state = apply_linear_halt_control_cycle(
                state,
                phase=LogicalPhase.STATE_7,
                pmd_read_data=ExactWord(24, next_opcode),
            ).state

        state = apply_linear_halt_control_cycle(
            state, phase=LogicalPhase.STATE_8
        ).state
        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = apply_linear_halt_control_cycle(
                state, phase=phase, halt_n=False
            ).state
        recognized_halt = apply_linear_halt_control_cycle(
            state, phase=LogicalPhase.STATE_3, halt_n=False
        )
        self.assertTrue(recognized_halt.control.halt_recognized)
        state = recognized_halt.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = apply_linear_halt_control_cycle(
                state, phase=phase, halt_n=False
            ).state
        interrupted = apply_linear_halt_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            irq_n=0xB,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(interrupted.control.halt_stop_event)
        self.assertTrue(interrupted.core.interrupt_recognition_event)
        self.assertTrue(interrupted.state.core.interrupt_vectoring)
        self.assertFalse(interrupted.state.core.instruction_valid)

        held = apply_linear_halt_control_cycle(
            interrupted.state,
            phase=LogicalPhase.STATE_8,
            halt_n=False,
        )
        self.assertTrue(held.control.phase_hold)
        self.assertFalse(held.core.interrupt_entry_event)
        self.assertFalse(held.core.interrupt_vector_issue_event)
        self.assertTrue(held.state.core.interrupt_vectoring)

        blocked = apply_linear_halt_control_cycle(
            held.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=False,
        )
        self.assertTrue(blocked.control.release_blocked)
        self.assertFalse(blocked.core.interrupt_entry_event)

        resumed = apply_linear_halt_control_cycle(
            blocked.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=True,
        )
        self.assertTrue(resumed.control.resume_event)
        self.assertTrue(resumed.core.interrupt_entry_event)
        self.assertTrue(resumed.core.interrupt_vector_issue_event)
        self.assertEqual(
            resumed.state.core.bus.address,
            ExactWord(14, 2),
        )
        self.assertEqual(
            resumed.state.core.architecture.pc_stack[-1],
            ExactWord(14, 0x0103),
        )

    def test_recognized_short_pulse_is_latched_until_stop(self) -> None:
        recognized = apply_halt_control_cycle(
            HaltControlState(),
            phase=LogicalPhase.STATE_3,
            halt_n=False,
        )
        stopped = apply_halt_control_cycle(
            recognized.state,
            phase=LogicalPhase.STATE_7,
            halt_n=True,
        )
        self.assertTrue(stopped.halt_stop_event)
        self.assertEqual(stopped.state.mode, HaltControlMode.HALTED)
        resumed = apply_halt_control_cycle(
            stopped.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
        )
        self.assertTrue(resumed.resume_event)

    def test_reset_clears_pending_or_halted_control_state(self) -> None:
        for mode in (
            HaltControlMode.STOP_PENDING,
            HaltControlMode.HALTED,
            HaltControlMode.FORCE_FETCH_PENDING,
        ):
            result = apply_halt_control_cycle(
                HaltControlState(mode),
                reset=True,
                phase=LogicalPhase.STATE_8,
                halt_n=False,
            )
            self.assertEqual(result.state.mode, HaltControlMode.RUNNING)
            self.assertFalse(result.instruction_issue_inhibit)
            self.assertFalse(result.halted)


if __name__ == "__main__":
    unittest.main()
