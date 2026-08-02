from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    BusControlMode,
    BusControlState,
    ExactWord,
    LinearBusControlState,
    LogicalPhase,
    apply_linear_bus_control_cycle,
    register_code_by_name,
)


ROOT = Path(__file__).resolve().parents[1]


def _type7(code: int, data: int) -> int:
    return (
        0x300000
        | ((code >> 4) << 18)
        | ((data & 0x3FFF) << 4)
        | (code & 0xF)
    )


def _setup(opcode: int = 0, pc: int = 4) -> LinearBusControlState:
    result = apply_linear_bus_control_cycle(
        LinearBusControlState.reset(),
        phase=LogicalPhase.STATE_8,
        instruction_setup=(ExactWord(14, pc), ExactWord(24, opcode)),
    )
    assert result.core.instruction_setup_accepted
    return result.state


class LinearBusControlTests(unittest.TestCase):
    def test_machine_readable_composition_contract(self) -> None:
        contract = json.loads(
            (ROOT / "docs/generated/adsp2100_linear_bus_control.yaml")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertIn("CURRENT_PM_FETCH_COMPLETES", contract["request_effect"])
        self.assertIn("STATE_8", contract["resume_effect"])
        self.assertIn("RETAINED", contract["interrupt_effect"])
        self.assertIn(
            "ANALOG_BR_BG_OR_MEMORY_PIN_TIMING",
            contract["excluded_claims"],
        )

    def test_request_finishes_current_fetch_and_blocks_the_next(self) -> None:
        state = _setup()
        issued = apply_linear_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
        )
        self.assertTrue(issued.core.instruction_issue)
        state = issued.state

        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=False
            ).state
        recognized = apply_linear_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            br_n=False,
        )
        self.assertTrue(recognized.control.request_recognized)
        self.assertTrue(recognized.control.instruction_issue_inhibit)
        self.assertFalse(recognized.native_bus_relinquished)
        state = recognized.state

        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            active = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=False
            )
            self.assertTrue(active.core.bus.address_output_enable)
            self.assertTrue(active.core.bus.control_output_enable)
            state = active.state
        retired = apply_linear_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            br_n=False,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(retired.core.retire_event)
        self.assertEqual(retired.state.core.architecture.pc, ExactWord(14, 5))
        state = retired.state

        stopped = apply_linear_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            br_n=False,
        )
        self.assertFalse(stopped.core.instruction_issue)
        self.assertFalse(stopped.state.core.pending)
        self.assertTrue(stopped.state.core.instruction_valid)

    def test_grant_masks_every_linear_pm_driver(self) -> None:
        state = _setup()
        state = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=False
        ).state
        for phase in range(3, 8):
            state = apply_linear_bus_control_cycle(
                state, phase=LogicalPhase(phase), br_n=False
            ).state
        for phase in range(2):
            state = apply_linear_bus_control_cycle(
                state, phase=LogicalPhase(phase), br_n=False
            ).state
        grant = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=False
        )
        self.assertTrue(grant.control.grant_assert_event)
        visible = apply_linear_bus_control_cycle(
            grant.state, phase=LogicalPhase.STATE_4, br_n=False
        )
        self.assertFalse(visible.native_bg_n)
        self.assertTrue(visible.native_bus_relinquished)
        self.assertFalse(visible.core.bus.address_output_enable)
        self.assertFalse(visible.core.bus.control_output_enable)
        self.assertFalse(visible.core.bus.data_output_enable)

    def test_recognized_irq_waits_for_bus_grant_release(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            _type7(writable["ICNTL"], 0x10),
            pc=0x0100,
        )
        for next_opcode in (_type7(writable["IMASK"], 0xF), 0):
            state = apply_linear_bus_control_cycle(
                state, phase=LogicalPhase.STATE_8
            ).state
            for phase in range(6):
                state = apply_linear_bus_control_cycle(
                    state, phase=LogicalPhase(phase)
                ).state
            state = apply_linear_bus_control_cycle(
                state,
                phase=LogicalPhase.STATE_7,
                pmd_read_data=ExactWord(24, next_opcode),
            ).state

        state = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_8
        ).state
        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=False
            ).state
        state = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=False
        ).state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=False
            ).state
        interrupted = apply_linear_bus_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            br_n=False,
            irq_n=0xB,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(interrupted.core.interrupt_recognition_event)
        self.assertTrue(interrupted.state.core.interrupt_vectoring)
        state = interrupted.state

        for phase in (
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            step = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=False
            )
            self.assertFalse(step.core.interrupt_vector_issue_event)
            state = step.state
        granted = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=False
        )
        self.assertTrue(granted.control.grant_assert_event)
        state = granted.state

        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            state = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=True
            ).state
        state = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=True
        ).state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            held = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=True
            )
            self.assertFalse(held.core.interrupt_vector_issue_event)
            state = held.state
        released = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=True
        )
        self.assertTrue(released.control.grant_release_event)
        state = released.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
        ):
            state = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=True
            ).state
        resumed = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_8, br_n=True
        )
        self.assertTrue(resumed.control.resume_event)
        self.assertTrue(resumed.core.interrupt_entry_event)
        self.assertTrue(resumed.core.interrupt_vector_issue_event)
        self.assertEqual(
            resumed.state.core.bus.address,
            ExactWord(14, 2),
        )

    def test_release_restarts_fetch_on_state_one_boundary(self) -> None:
        initial = _setup()
        state = LinearBusControlState(
            core=initial.core,
            control=BusControlState(BusControlMode.GRANTED),
        )
        release = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=True
        )
        self.assertTrue(release.control.release_recognized)
        state = release.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
        ):
            state = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=True
            ).state
        released = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_3, br_n=True
        )
        self.assertTrue(released.control.grant_release_event)
        state = released.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
        ):
            held = apply_linear_bus_control_cycle(
                state, phase=phase, br_n=True
            )
            self.assertFalse(held.core.instruction_issue)
            state = held.state
        resumed = apply_linear_bus_control_cycle(
            state, phase=LogicalPhase.STATE_8, br_n=True
        )
        self.assertTrue(resumed.control.resume_event)
        self.assertFalse(resumed.control.instruction_issue_inhibit)
        self.assertTrue(resumed.core.instruction_issue)
        self.assertTrue(resumed.state.core.pending)

    def test_reset_time_native_grant_never_drives_pm(self) -> None:
        reset = apply_linear_bus_control_cycle(
            _setup(),
            reset=True,
            phase=LogicalPhase.STATE_4,
            br_n=False,
        )
        self.assertFalse(reset.native_bg_n)
        self.assertTrue(reset.native_bus_relinquished)
        self.assertFalse(reset.core.bus.address_output_enable)
        self.assertFalse(reset.core.bus.control_output_enable)
        self.assertFalse(reset.core.bus.data_output_enable)
        self.assertFalse(reset.state.core.instruction_valid)


if __name__ == "__main__":
    unittest.main()
