import unittest

from sim.reference_models.adsp2100_model import (
    DAGRegisterKind,
    DAGRegisterSetup,
    DMWriteImmediateNativeState,
    ExactWord,
    LogicalPhase,
    apply_dm_write_immediate_native_cycle,
)


def _opcode(
    data: int,
    *,
    dag: int = 0,
    i_local: int = 0,
    m_local: int = 0,
) -> int:
    return (
        0xA00000
        | (dag << 20)
        | (data << 4)
        | (i_local << 2)
        | m_local
    )


def _setup(
    state: DMWriteImmediateNativeState,
    kind: DAGRegisterKind,
    address: int,
    value: int,
) -> DMWriteImmediateNativeState:
    return apply_dm_write_immediate_native_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        setup_dag=DAGRegisterSetup(kind, address, value),
    ).state


def _configured_state() -> DMWriteImmediateNativeState:
    state = DMWriteImmediateNativeState.reset()
    state = _setup(state, DAGRegisterKind.I, 0, 0x0123)
    state = _setup(state, DAGRegisterKind.M, 1, 3)
    state = _setup(state, DAGRegisterKind.L, 0, 0)
    return state


class DMWriteImmediateNativeTests(unittest.TestCase):
    def test_write_issues_at_eight_and_commits_only_at_seven(self) -> None:
        state = _configured_state()
        issue = apply_dm_write_immediate_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(0xBEEF, i_local=0, m_local=1),
        )
        self.assertTrue(issue.issue_boundary)
        self.assertTrue(issue.core.accepted)
        self.assertTrue(issue.bus.request_accepted)
        self.assertFalse(issue.core.instruction_complete)
        self.assertEqual(issue.state.core.dag.i[0], 0x0123)

        state = issue.state
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            step = apply_dm_write_immediate_native_cycle(
                state, phase=phase
            )
            self.assertFalse(step.bus.dms_n)
            self.assertFalse(step.core.instruction_complete)
            self.assertEqual(step.state.core.dag.i[0], 0x0123)
            state = step.state

        qualified = apply_dm_write_immediate_native_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=True
        )
        self.assertTrue(qualified.bus.dmack_accepted)
        self.assertFalse(qualified.core.instruction_complete)
        done = apply_dm_write_immediate_native_cycle(
            qualified.state, phase=LogicalPhase.STATE_7
        )
        self.assertTrue(done.bus.completion_event)
        self.assertTrue(done.core.instruction_complete)
        self.assertTrue(done.core.i_write_known)
        self.assertEqual(done.state.core.dag.i[0], 0x0126)
        self.assertFalse(done.attachment_conflict)

    def test_wait_repeats_full_cycle_and_holds_old_descriptor(self) -> None:
        issue = apply_dm_write_immediate_native_cycle(
            _configured_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(0xCAFE, i_local=0, m_local=1),
        )
        state = issue.state
        low = apply_dm_write_immediate_native_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=False
        )
        self.assertTrue(low.bus.wait_extension_event)
        self.assertTrue(low.state.bus.waiting)
        state = low.state

        for phase in (
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held = apply_dm_write_immediate_native_cycle(
                state,
                phase=phase,
                dm_ack=True,
                setup_mstat=ExactWord(4, 2),
            )
            self.assertTrue(held.core.stalled)
            self.assertFalse(held.core.instruction_complete)
            self.assertFalse(held.bus.dmwr_n)
            self.assertTrue(held.bus.data_output_enable)
            self.assertEqual(held.bus.address, 0x0123)
            self.assertEqual(held.bus.write_data, 0xCAFE)
            self.assertEqual(held.state.core.mstat, 0)
            self.assertEqual(held.state.core.dag.i[0], 0x0123)
            state = held.state

        high = apply_dm_write_immediate_native_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=True
        )
        self.assertTrue(high.bus.dmack_accepted)
        done = apply_dm_write_immediate_native_cycle(
            high.state, phase=LogicalPhase.STATE_7
        )
        self.assertTrue(done.core.instruction_complete)
        self.assertEqual(done.state.core.dag.i[0], 0x0126)

    def test_late_ack_cannot_commit_the_dag(self) -> None:
        issue = apply_dm_write_immediate_native_cycle(
            _configured_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(0x1111, i_local=0, m_local=1),
        )
        low = apply_dm_write_immediate_native_cycle(
            issue.state, phase=LogicalPhase.STATE_6, dm_ack=False
        )
        late = apply_dm_write_immediate_native_cycle(
            low.state, phase=LogicalPhase.STATE_7, dm_ack=True
        )
        self.assertFalse(late.bus.completion_event)
        self.assertFalse(late.core.instruction_complete)
        self.assertEqual(late.state.core.dag.i[0], 0x0123)

    def test_off_boundary_controls_fail_closed(self) -> None:
        state = _configured_state()
        result = apply_dm_write_immediate_native_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            execute=True,
            opcode=_opcode(0x2222, i_local=0, m_local=1),
            setup_mstat=ExactWord(4, 2),
        )
        self.assertTrue(result.phase_conflict)
        self.assertTrue(result.integration_conflict)
        self.assertFalse(result.core.accepted)
        self.assertFalse(result.bus.request_accepted)
        self.assertEqual(result.state, state)

    def test_relinquishment_masks_and_holds_both_boundaries(self) -> None:
        issue = apply_dm_write_immediate_native_cycle(
            _configured_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(0x3333, i_local=0, m_local=1),
        )
        low = apply_dm_write_immediate_native_cycle(
            issue.state, phase=LogicalPhase.STATE_6, dm_ack=False
        )
        masked = apply_dm_write_immediate_native_cycle(
            low.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
            bus_relinquished=True,
        )
        self.assertEqual(masked.state, low.state)
        self.assertFalse(masked.bus.dmack_sample_event)
        self.assertFalse(masked.bus.address_output_enable)
        self.assertFalse(masked.bus.control_output_enable)
        self.assertFalse(masked.bus.data_output_enable)
        self.assertTrue(
            masked.bus.dms_n and masked.bus.dmrd_n and masked.bus.dmwr_n
        )


if __name__ == "__main__":
    unittest.main()
