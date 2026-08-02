from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    DataBusRequest,
    ExactWord,
    LinearDMWaitControlState,
    LogicalPhase,
    apply_linear_dm_wait_control_cycle,
)


def _type7(register_code: int, value: int) -> int:
    return (
        0x300000
        | ((register_code >> 4) << 18)
        | ((value & 0x3FFF) << 4)
        | (register_code & 0xF)
    )


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
            "RAW_STRUCTURAL_COMPANION_DESCRIPTOR",
        )
        self.assertIn(
            "FETCHED_DM_INSTRUCTION_OWNERSHIP",
            contract["excluded_claims"],
        )

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
