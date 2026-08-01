import unittest

from sim.reference_models.adsp2100_model import (
    DAGRegisterKind,
    DAGRegisterSetup,
    DMWriteImmediateState,
    ExactWord,
    apply_dm_write_immediate_cycle,
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
    state: DMWriteImmediateState,
    kind: DAGRegisterKind,
    address: int,
    value: int,
) -> DMWriteImmediateState:
    return apply_dm_write_immediate_cycle(
        state,
        setup_dag=DAGRegisterSetup(kind, address, value),
    ).state


class DMWriteImmediateSliceTests(unittest.TestCase):
    def test_same_clock_ack_writes_immediate_and_postmodifies_i(self):
        state = DMWriteImmediateState.reset()
        state = _setup(state, DAGRegisterKind.I, 0, 0x123)
        state = _setup(state, DAGRegisterKind.M, 1, 3)
        state = _setup(state, DAGRegisterKind.L, 0, 0)
        result = apply_dm_write_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(0xBEEF, i_local=0, m_local=1),
            dm_ack=True,
        )
        self.assertTrue(result.accepted)
        self.assertTrue(result.instruction_complete)
        self.assertTrue(result.dm_select and result.dm_write)
        self.assertFalse(result.dm_read)
        self.assertEqual(result.dm_address, 0x123)
        self.assertTrue(result.dm_address_known)
        self.assertEqual(result.dm_write_data, 0xBEEF)
        self.assertTrue(result.dm_write_data_known)
        self.assertTrue(result.i_write and result.i_write_known)
        self.assertEqual(result.state.dag.i[0], 0x126)
        self.assertFalse(result.busy)

    def test_dm_ack_wait_holds_descriptor_and_defers_i_write(self):
        state = DMWriteImmediateState.reset()
        state = _setup(state, DAGRegisterKind.I, 6, 0x345)
        state = _setup(state, DAGRegisterKind.M, 7, 0x3FFF)
        state = _setup(state, DAGRegisterKind.L, 6, 0)
        issue = apply_dm_write_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(0x8001, dag=1, i_local=2, m_local=3),
            dm_ack=False,
        )
        self.assertTrue(issue.accepted and issue.stalled and issue.busy)
        self.assertFalse(issue.instruction_complete or issue.i_write)
        self.assertEqual(issue.state.dag.i[6], 0x345)
        held = issue
        for _ in range(4):
            held = apply_dm_write_immediate_cycle(held.state, dm_ack=False)
            self.assertTrue(held.stalled and held.transaction_active)
            self.assertEqual(held.dm_address, 0x345)
            self.assertEqual(held.dm_write_data, 0x8001)
            self.assertEqual(held.state.dag.i[6], 0x345)
        done = apply_dm_write_immediate_cycle(held.state, dm_ack=True)
        self.assertTrue(done.instruction_complete and done.i_write_known)
        self.assertEqual(done.dm_address, 0x345)
        self.assertEqual(done.dm_write_data, 0x8001)
        self.assertEqual(done.state.dag.i[6], 0x344)
        self.assertFalse(done.busy)

    def test_dag1_bit_reverse_changes_address_not_stored_i(self):
        state = DMWriteImmediateState.reset()
        state = apply_dm_write_immediate_cycle(
            state,
            setup_mstat=ExactWord(4, 0x2),
        ).state
        state = _setup(state, DAGRegisterKind.I, 0, 0x0001)
        state = _setup(state, DAGRegisterKind.M, 0, 1)
        state = _setup(state, DAGRegisterKind.L, 0, 0)
        result = apply_dm_write_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(0x1357),
            dm_ack=True,
        )
        self.assertEqual(result.dm_address, 0x2000)
        self.assertEqual(result.state.dag.i[0], 0x0002)

    def test_dag2_ignores_bit_reverse_mode(self):
        state = DMWriteImmediateState.reset()
        state = apply_dm_write_immediate_cycle(
            state,
            setup_mstat=ExactWord(4, 0x2),
        ).state
        state = _setup(state, DAGRegisterKind.I, 4, 0x0001)
        state = _setup(state, DAGRegisterKind.M, 4, 1)
        state = _setup(state, DAGRegisterKind.L, 4, 0)
        result = apply_dm_write_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(0x2468, dag=1),
            dm_ack=True,
        )
        self.assertEqual(result.dm_address, 0x0001)
        self.assertEqual(result.state.dag.i[4], 0x0002)

    def test_all_same_dag_i_m_selections_complete(self):
        state = DMWriteImmediateState.reset()
        count = 0
        for dag in range(2):
            for i_local in range(4):
                i_address = dag * 4 + i_local
                for m_local in range(4):
                    m_address = dag * 4 + m_local
                    state = _setup(
                        state, DAGRegisterKind.I, i_address, 0x100 + count
                    )
                    state = _setup(state, DAGRegisterKind.M, m_address, 1)
                    state = _setup(state, DAGRegisterKind.L, i_address, 0)
                    result = apply_dm_write_immediate_cycle(
                        state,
                        execute=True,
                        opcode=_opcode(
                            count,
                            dag=dag,
                            i_local=i_local,
                            m_local=m_local,
                        ),
                        dm_ack=True,
                    )
                    self.assertTrue(result.instruction_complete)
                    self.assertEqual(result.dm_address, 0x100 + count)
                    self.assertEqual(result.dm_write_data, count)
                    self.assertEqual(result.state.dag.i[i_address], 0x101 + count)
                    state = result.state
                    count += 1
        self.assertEqual(count, 32)

    def test_unknown_i_has_unknown_address_but_known_immediate(self):
        result = apply_dm_write_immediate_cycle(
            DMWriteImmediateState.reset(),
            execute=True,
            opcode=_opcode(0xFFFF),
            dm_ack=True,
        )
        self.assertTrue(result.instruction_complete)
        self.assertFalse(result.dm_address_known)
        self.assertEqual(result.dm_address, 0)
        self.assertTrue(result.dm_write_data_known)
        self.assertEqual(result.dm_write_data, 0xFFFF)
        self.assertTrue(result.i_write)
        self.assertFalse(result.i_write_known)
        self.assertIsNone(result.state.dag.i[0])

    def test_invalid_circular_configuration_invalidates_i_on_completion(self):
        state = DMWriteImmediateState.reset()
        state = _setup(state, DAGRegisterKind.I, 0, 0x0100)
        state = _setup(state, DAGRegisterKind.M, 0, 2)
        state = _setup(state, DAGRegisterKind.L, 0, 1)
        result = apply_dm_write_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(0x1234),
            dm_ack=True,
        )
        self.assertTrue(result.dm_address_known)
        self.assertEqual(result.dm_address, 0x0100)
        self.assertFalse(result.dag_configuration_valid)
        self.assertTrue(result.i_write)
        self.assertFalse(result.i_write_known)
        self.assertIsNone(result.state.dag.i[0])

    def test_pending_conflicts_do_not_replace_transaction(self):
        state = DMWriteImmediateState.reset()
        state = _setup(state, DAGRegisterKind.I, 0, 0x100)
        state = _setup(state, DAGRegisterKind.M, 0, 1)
        state = _setup(state, DAGRegisterKind.L, 0, 0)
        issue = apply_dm_write_immediate_cycle(
            state, execute=True, opcode=_opcode(0x1111), dm_ack=False
        )
        conflict = apply_dm_write_immediate_cycle(
            issue.state,
            execute=True,
            opcode=_opcode(0x2222, dag=1),
            dm_ack=False,
            setup_mstat=ExactWord(4, 0x2),
        )
        self.assertTrue(conflict.integration_conflict and conflict.stalled)
        self.assertEqual(conflict.dm_write_data, 0x1111)
        self.assertEqual(conflict.state.mstat, 0)
        done = apply_dm_write_immediate_cycle(conflict.state, dm_ack=True)
        self.assertEqual(done.dm_write_data, 0x1111)
        self.assertEqual(done.state.dag.i[0], 0x101)

    def test_reset_cancels_pending_without_writeback(self):
        state = DMWriteImmediateState.reset()
        state = _setup(state, DAGRegisterKind.I, 0, 0x100)
        state = _setup(state, DAGRegisterKind.M, 0, 1)
        state = _setup(state, DAGRegisterKind.L, 0, 0)
        issue = apply_dm_write_immediate_cycle(
            state, execute=True, opcode=_opcode(0xAAAA), dm_ack=False
        )
        reset = apply_dm_write_immediate_cycle(
            issue.state, reset=True, dm_ack=True
        )
        self.assertFalse(reset.transaction_active or reset.i_write)
        self.assertIsNone(reset.state.pending)
        self.assertIsNone(reset.state.dag.i[0])
        self.assertEqual(reset.state.mstat, 0)

    def test_invalid_opcode_and_setup_conflicts_are_atomic(self):
        state = DMWriteImmediateState.reset()
        invalid = apply_dm_write_immediate_cycle(
            state, execute=True, opcode=0x000000, dm_ack=True
        )
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_dm_write_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(1),
            setup_mstat=ExactWord(4, 2),
            dm_ack=True,
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertFalse(conflict.accepted or conflict.dm_select)
        self.assertEqual(conflict.state, state)
        two_setups = apply_dm_write_immediate_cycle(
            state,
            setup_mstat=ExactWord(4, 2),
            setup_dag=DAGRegisterSetup(DAGRegisterKind.I, 0, 1),
        )
        self.assertTrue(two_setups.integration_conflict)
        self.assertEqual(two_setups.state, state)

    def test_exact_width_contracts_fail_closed(self):
        with self.assertRaises(ValueError):
            apply_dm_write_immediate_cycle(
                DMWriteImmediateState.reset(),
                setup_mstat=ExactWord(8, 0),
            )
        with self.assertRaises(ValueError):
            apply_dm_write_immediate_cycle(
                DMWriteImmediateState.reset(), opcode=0x1000000
            )


if __name__ == "__main__":
    unittest.main()
