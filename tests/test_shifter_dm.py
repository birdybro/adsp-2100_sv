from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    SHIFTER_DM_CLASS_MASK,
    SHIFTER_DM_CLASS_VALUE,
    ShifterDMState,
    UNKNOWN,
    apply_shifter_dm_cycle,
    decode_shifter_dm,
    is_shifter_dm_class,
    read_dreg,
    shifter_dm_unsupported_reason,
)


LEGAL_XOPS = (0, 2, 3, 4, 5, 6, 7)


def _opcode(
    *,
    write: bool = False,
    dag: int = 0,
    sf: int = 0,
    xop: int = 0,
    dreg: DREG = DREG.AX0,
    i: int = 0,
    m: int = 0,
) -> int:
    return (
        0x120000
        | (dag << 16)
        | (int(write) << 15)
        | (sf << 11)
        | (xop << 8)
        | (int(dreg) << 4)
        | (i << 2)
        | m
    )


def _dreg(state: ShifterDMState, register: DREG, value: int) -> ShifterDMState:
    return apply_shifter_dm_cycle(
        state,
        setup_dreg=DREGWrite(register, ExactWord(16, value)),
    ).state


def _dag(
    state: ShifterDMState,
    kind: DAGRegisterKind,
    address: int,
    value: int,
) -> ShifterDMState:
    return apply_shifter_dm_cycle(
        state,
        setup_dag=DAGRegisterSetup(kind, address, value),
    ).state


def _known_linear_state() -> ShifterDMState:
    state = ShifterDMState.reset()
    state = _dreg(state, DREG.SI, 0x1234)
    state = _dreg(state, DREG.SE, 0)
    state = _dag(state, DAGRegisterKind.I, 0, 0x0100)
    state = _dag(state, DAGRegisterKind.M, 0, 1)
    state = _dag(state, DAGRegisterKind.L, 0, 0)
    return state


def _sr(state: ShifterDMState) -> int | None:
    bank = state.alternate if state.status.alternate_bank else state.primary
    if not all(isinstance(value, ExactWord) for value in bank.sr):
        return None
    sr0, sr1 = bank.sr
    assert isinstance(sr0, ExactWord) and isinstance(sr1, ExactWord)
    return (sr1.value << 16) | sr0.value


class ShifterDMTests(unittest.TestCase):
    def test_complete_type_12_partition_and_fields(self) -> None:
        supported = 0
        unavailable = 0
        collision = 0
        for payload in range(1 << 17):
            opcode = 0x120000 | payload
            self.assertTrue(is_shifter_dm_class(opcode))
            action = decode_shifter_dm(opcode)
            reason = shifter_dm_unsupported_reason(opcode)
            if action is not None:
                self.assertIsNone(reason)
                self.assertEqual(action.write, bool((payload >> 15) & 1))
                self.assertEqual(action.dag, (payload >> 16) & 1)
                self.assertEqual(action.sf, (payload >> 11) & 0xF)
                self.assertEqual(action.xop, (payload >> 8) & 7)
                self.assertEqual(action.memory_dreg, DREG((payload >> 4) & 0xF))
                self.assertEqual(action.i_address, ((payload >> 16) & 1) * 4 + ((payload >> 2) & 3))
                self.assertEqual(action.m_address, ((payload >> 16) & 1) * 4 + (payload & 3))
                supported += 1
            elif reason == "UNAVAILABLE_SHIFTER_XOP":
                unavailable += 1
            elif reason == "UNSUPPORTED_DESTINATION_COLLISION":
                collision += 1
            else:
                self.fail(f"unclassified Type 12 payload 0x{payload:05x}")
        self.assertEqual(SHIFTER_DM_CLASS_MASK, 0xFE0000)
        self.assertEqual(SHIFTER_DM_CLASS_VALUE, 0x120000)
        self.assertEqual(supported, 108_640)
        self.assertEqual(unavailable, 16_384)
        self.assertEqual(collision, 6_048)

    def test_nonclass_and_out_of_range_words_fail_closed(self) -> None:
        for opcode in (0, 0x11FFFF, 0x140000, 0xFFFFFF):
            self.assertFalse(is_shifter_dm_class(opcode))
            self.assertIsNone(decode_shifter_dm(opcode))
            self.assertIsNone(shifter_dm_unsupported_reason(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_shifter_dm(opcode)

    def test_waited_read_holds_bus_and_commits_all_actions_atomically(self) -> None:
        state = _known_linear_state()
        opcode = _opcode(dreg=DREG.AX0)
        issued = apply_shifter_dm_cycle(
            state,
            execute=True,
            opcode=opcode,
            dm_ack=False,
            dm_read_data=ExactWord(16, 0x1111),
        )
        self.assertTrue(issued.accepted)
        self.assertTrue(issued.stalled)
        self.assertTrue(issued.dm_read)
        self.assertEqual(issued.dm_address, 0x0100)
        self.assertEqual(issued.state.dag.i[0], 0x0100)
        self.assertIs(read_dreg(issued.state.primary, DREG.AX0), UNKNOWN)
        self.assertIsNone(_sr(issued.state))

        waited = apply_shifter_dm_cycle(
            issued.state,
            dm_ack=False,
            dm_read_data=ExactWord(16, 0x2222),
        )
        self.assertFalse(waited.class_valid)
        self.assertFalse(waited.action_valid)
        self.assertIsNone(waited.action)
        self.assertEqual(waited.state, issued.state)
        self.assertEqual(waited.dm_address, issued.dm_address)
        self.assertEqual(waited.dm_read, issued.dm_read)
        self.assertTrue(waited.stalled)
        self.assertEqual(waited.sr_result, 0)
        self.assertEqual(waited.se_result, 0)
        self.assertEqual(waited.sb_result, 0)
        self.assertFalse(waited.ss_result)

        completed = apply_shifter_dm_cycle(
            waited.state,
            dm_ack=True,
            dm_read_data=ExactWord(16, 0xABCD),
        )
        self.assertTrue(completed.instruction_complete)
        self.assertFalse(completed.busy)
        self.assertTrue(completed.dreg_write)
        self.assertTrue(completed.dreg_write_known)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AX0), ExactWord(16, 0xABCD))
        self.assertEqual(_sr(completed.state), 0x12340000)
        self.assertEqual(completed.state.dag.i[0], 0x0101)

    def test_same_cycle_write_uses_old_data_and_allows_output_overlap(self) -> None:
        state = _known_linear_state()
        state = _dreg(state, DREG.SR0, 0x5678)
        state = _dreg(state, DREG.SR1, 0x9ABC)
        completed = apply_shifter_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(write=True, dreg=DREG.SR0),
            dm_ack=True,
        )
        self.assertTrue(completed.instruction_complete)
        self.assertTrue(completed.dm_write)
        self.assertTrue(completed.dm_write_data_known)
        self.assertEqual(completed.dm_write_data, 0x5678)
        self.assertEqual(_sr(completed.state), 0x12340000)
        self.assertEqual(completed.state.dag.i[0], 0x0101)

    def test_read_collision_is_rejected_but_matching_write_is_legal(self) -> None:
        read_opcode = _opcode(dreg=DREG.SR0)
        write_opcode = _opcode(write=True, dreg=DREG.SR0)
        self.assertIsNone(decode_shifter_dm(read_opcode))
        self.assertEqual(
            shifter_dm_unsupported_reason(read_opcode),
            "UNSUPPORTED_DESTINATION_COLLISION",
        )
        self.assertIsNotNone(decode_shifter_dm(write_opcode))

    def test_dag2_selection_and_dag1_bit_reversal(self) -> None:
        state = _known_linear_state()
        state = apply_shifter_dm_cycle(
            state,
            setup_mstat=ExactWord(4, 0x2),
        ).state
        reversed_cycle = apply_shifter_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(),
            dm_ack=False,
        )
        self.assertEqual(reversed_cycle.dm_address, 0x0020)

        state = _dreg(state, DREG.SI, 0x1111)
        state = _dag(state, DAGRegisterKind.I, 7, 0x0222)
        state = _dag(state, DAGRegisterKind.M, 4, 0x3FFF)
        state = _dag(state, DAGRegisterKind.L, 7, 0)
        dag2 = apply_shifter_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(dag=1, i=3, m=0),
            dm_ack=True,
            dm_read_data=ExactWord(16, 0),
        )
        self.assertEqual(dag2.dm_address, 0x0222)
        self.assertEqual(dag2.state.dag.i[7], 0x0221)

    def test_unknown_sources_invalidate_only_documented_destinations(self) -> None:
        state = ShifterDMState.reset()
        state = _dag(state, DAGRegisterKind.I, 0, 0x0100)
        result = apply_shifter_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(dreg=DREG.AX0),
            dm_ack=True,
            dm_read_data=UNKNOWN,
        )
        self.assertTrue(result.dm_address_known)
        self.assertFalse(result.dreg_write_known)
        self.assertIs(read_dreg(result.state.primary, DREG.AX0), UNKNOWN)
        self.assertIsNone(_sr(result.state))
        self.assertIsNone(result.state.dag.i[0])

    def test_reset_aborts_wait_and_busy_inputs_are_reported(self) -> None:
        issued = apply_shifter_dm_cycle(
            _known_linear_state(),
            execute=True,
            opcode=_opcode(),
            dm_ack=False,
        )
        conflict = apply_shifter_dm_cycle(
            issued.state,
            execute=True,
            opcode=_opcode(write=True),
            dm_ack=False,
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertTrue(conflict.stalled)
        self.assertEqual(conflict.dm_read, issued.dm_read)
        reset = apply_shifter_dm_cycle(conflict.state, reset=True)
        self.assertIsNone(reset.state.pending)
        self.assertFalse(reset.dm_select)
        self.assertEqual(reset.state.dag.i, (None,) * 8)

    def test_alternate_bank_is_selected_for_both_parallel_actions(self) -> None:
        state = _known_linear_state()
        state = apply_shifter_dm_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        state = _dreg(state, DREG.SI, 0x7777)
        state = _dreg(state, DREG.SE, 0)
        completed = apply_shifter_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
            dm_ack=True,
            dm_read_data=ExactWord(16, 0xCAFE),
        )
        self.assertIs(completed.state.primary.ax[1], UNKNOWN)
        self.assertEqual(completed.state.alternate.ax[1], ExactWord(16, 0xCAFE))
        self.assertEqual(_sr(completed.state), 0x77770000)


if __name__ == "__main__":
    unittest.main()
