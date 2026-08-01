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
)


ROOT = Path(__file__).resolve().parents[1]


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
