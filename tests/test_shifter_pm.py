from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    SHIFTER_PM_CLASS_MASK,
    SHIFTER_PM_CLASS_VALUE,
    ShifterPMState,
    UNKNOWN,
    apply_shifter_pm_cycle,
    decode_shifter_pm,
    is_shifter_pm_class,
    read_dreg,
    shifter_pm_unsupported_reason,
)


def _opcode(
    *,
    write: bool = False,
    sf: int = 0,
    xop: int = 0,
    dreg: DREG = DREG.AX0,
    i: int = 0,
    m: int = 0,
) -> int:
    return (
        0x110000
        | (int(write) << 15)
        | (sf << 11)
        | (xop << 8)
        | (int(dreg) << 4)
        | (i << 2)
        | m
    )


def _dreg(state: ShifterPMState, register: DREG, value: int) -> ShifterPMState:
    return apply_shifter_pm_cycle(
        state,
        setup_dreg=DREGWrite(register, ExactWord(16, value)),
    ).state


def _dag(
    state: ShifterPMState,
    kind: DAGRegisterKind,
    address: int,
    value: int,
) -> ShifterPMState:
    return apply_shifter_pm_cycle(
        state,
        setup_dag=DAGRegisterSetup(kind, address, value),
    ).state


def _known_state() -> ShifterPMState:
    state = ShifterPMState.reset()
    state = _dreg(state, DREG.SI, 0x1234)
    state = _dreg(state, DREG.SE, 0)
    state = _dag(state, DAGRegisterKind.I, 4, 0x0100)
    state = _dag(state, DAGRegisterKind.M, 4, 1)
    state = _dag(state, DAGRegisterKind.L, 4, 0)
    return apply_shifter_pm_cycle(
        state,
        setup_px=ExactWord(8, 0x5A),
    ).state


def _sr(state: ShifterPMState) -> int | None:
    bank = state.alternate if state.status.alternate_bank else state.primary
    if not all(isinstance(value, ExactWord) for value in bank.sr):
        return None
    sr0, sr1 = bank.sr
    assert isinstance(sr0, ExactWord) and isinstance(sr1, ExactWord)
    return (sr1.value << 16) | sr0.value


class ShifterPMTests(unittest.TestCase):
    def test_complete_type_13_partition_and_fields(self) -> None:
        supported = 0
        unavailable = 0
        collision = 0
        for payload in range(1 << 16):
            opcode = 0x110000 | payload
            self.assertTrue(is_shifter_pm_class(opcode))
            action = decode_shifter_pm(opcode)
            reason = shifter_pm_unsupported_reason(opcode)
            if action is not None:
                self.assertIsNone(reason)
                self.assertEqual(action.write, bool((payload >> 15) & 1))
                self.assertEqual(action.sf, (payload >> 11) & 0xF)
                self.assertEqual(action.xop, (payload >> 8) & 7)
                self.assertEqual(action.memory_dreg, DREG((payload >> 4) & 0xF))
                self.assertEqual(action.i_address, 4 + ((payload >> 2) & 3))
                self.assertEqual(action.m_address, 4 + (payload & 3))
                supported += 1
            elif reason == "UNAVAILABLE_SHIFTER_XOP":
                unavailable += 1
            elif reason == "UNSUPPORTED_DESTINATION_COLLISION":
                collision += 1
            else:
                self.fail(f"unclassified Type 13 payload 0x{payload:04x}")
        self.assertEqual(SHIFTER_PM_CLASS_MASK, 0xFF0000)
        self.assertEqual(SHIFTER_PM_CLASS_VALUE, 0x110000)
        self.assertEqual(supported, 54_320)
        self.assertEqual(unavailable, 8_192)
        self.assertEqual(collision, 3_024)

    def test_nonclass_and_out_of_range_words_fail_closed(self) -> None:
        for opcode in (0, 0x10FFFF, 0x120000, 0xFFFFFF):
            self.assertFalse(is_shifter_pm_class(opcode))
            self.assertIsNone(decode_shifter_pm(opcode))
            self.assertIsNone(shifter_pm_unsupported_reason(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_shifter_pm(opcode)

    def test_pm_read_splits_upper_word_and_px_and_commits_parallel_actions(self) -> None:
        result = apply_shifter_pm_cycle(
            _known_state(),
            execute=True,
            opcode=_opcode(dreg=DREG.AX0),
            pm_read_data=ExactWord(24, 0xABCD7E),
            next_fetch_address=ExactWord(14, 0x0042),
            cache_next_instruction_valid=True,
        )
        self.assertTrue(result.accepted)
        self.assertTrue(result.data_action_complete)
        self.assertTrue(result.instruction_complete)
        self.assertTrue(result.event_boundary)
        self.assertTrue(result.pm_data_access)
        self.assertTrue(result.pm_read)
        self.assertEqual(result.pm_address, 0x0100)
        self.assertEqual(read_dreg(result.state.primary, DREG.AX0), ExactWord(16, 0xABCD))
        self.assertEqual(result.state.px, ExactWord(8, 0x7E))
        self.assertEqual(_sr(result.state), 0x12340000)
        self.assertEqual(result.state.dag.i[4], 0x0101)

    def test_pm_write_combines_old_dreg_and_px_and_allows_overlap(self) -> None:
        state = _known_state()
        state = _dreg(state, DREG.SR0, 0x5678)
        state = _dreg(state, DREG.SR1, 0x9ABC)
        result = apply_shifter_pm_cycle(
            state,
            execute=True,
            opcode=_opcode(write=True, dreg=DREG.SR0),
            cache_next_instruction_valid=True,
        )
        self.assertTrue(result.pm_write)
        self.assertTrue(result.pm_write_data_known)
        self.assertEqual(result.pm_write_data, 0x56785A)
        self.assertEqual(_sr(result.state), 0x12340000)
        self.assertEqual(result.state.px, ExactWord(8, 0x5A))

    def test_cache_miss_adds_fetch_cycle_without_repeating_data_actions(self) -> None:
        issued = apply_shifter_pm_cycle(
            _known_state(),
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
            pm_read_data=ExactWord(24, 0xCAFE55),
            next_fetch_address=ExactWord(14, 0x0222),
            cache_next_instruction_valid=False,
        )
        self.assertTrue(issued.data_action_complete)
        self.assertFalse(issued.instruction_complete)
        self.assertTrue(issued.recovery_required)
        self.assertTrue(issued.busy)
        self.assertEqual(issued.state.dag.i[4], 0x0101)
        self.assertEqual(read_dreg(issued.state.primary, DREG.AX1), ExactWord(16, 0xCAFE))

        recovered = apply_shifter_pm_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0x123456),
        )
        self.assertTrue(recovered.recovery_fetch)
        self.assertTrue(recovered.pm_read)
        self.assertFalse(recovered.pm_data_access)
        self.assertEqual(recovered.pm_address, 0x0222)
        self.assertTrue(recovered.fetched_instruction_known)
        self.assertEqual(recovered.fetched_instruction, 0x123456)
        self.assertTrue(recovered.instruction_complete)
        self.assertTrue(recovered.event_boundary)
        self.assertFalse(recovered.busy)
        self.assertEqual(recovered.state.dag.i[4], 0x0101)
        self.assertEqual(read_dreg(recovered.state.primary, DREG.AX1), ExactWord(16, 0xCAFE))

    def test_forced_fetch_overrides_valid_cache_for_halt_handoff(self) -> None:
        issued = apply_shifter_pm_cycle(
            _known_state(),
            execute=True,
            opcode=_opcode(write=True),
            next_fetch_address=ExactWord(14, 0x0333),
            cache_next_instruction_valid=True,
            force_instruction_fetch=True,
        )
        self.assertFalse(issued.cache_instruction_selected)
        self.assertTrue(issued.recovery_required)
        recovered = apply_shifter_pm_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0),
        )
        self.assertEqual(recovered.pm_address, 0x0333)

    def test_read_collision_rejected_and_matching_write_legal(self) -> None:
        read_opcode = _opcode(dreg=DREG.SR0)
        write_opcode = _opcode(write=True, dreg=DREG.SR0)
        self.assertIsNone(decode_shifter_pm(read_opcode))
        self.assertEqual(
            shifter_pm_unsupported_reason(read_opcode),
            "UNSUPPORTED_DESTINATION_COLLISION",
        )
        self.assertIsNotNone(decode_shifter_pm(write_opcode))

    def test_alternate_bank_and_dag2_selection(self) -> None:
        state = _known_state()
        state = apply_shifter_pm_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        state = _dreg(state, DREG.SI, 0x7777)
        state = _dreg(state, DREG.SE, 0)
        state = _dag(state, DAGRegisterKind.I, 7, 0x0222)
        state = _dag(state, DAGRegisterKind.M, 4, 0x3FFF)
        state = _dag(state, DAGRegisterKind.L, 7, 0)
        result = apply_shifter_pm_cycle(
            state,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1, i=3, m=0),
            pm_read_data=ExactWord(24, 0xBEEF12),
        )
        self.assertIs(result.state.primary.ax[1], UNKNOWN)
        self.assertEqual(result.state.alternate.ax[1], ExactWord(16, 0xBEEF))
        self.assertEqual(result.state.dag.i[7], 0x0221)
        self.assertEqual(_sr(result.state), 0x77770000)

    def test_unknowns_reset_and_recovery_conflicts_fail_closed(self) -> None:
        state = ShifterPMState.reset()
        state = _dag(state, DAGRegisterKind.I, 4, 0x0100)
        result = apply_shifter_pm_cycle(
            state,
            execute=True,
            opcode=_opcode(dreg=DREG.AX0),
            pm_read_data=UNKNOWN,
            next_fetch_address=ExactWord(14, 0x0005),
            cache_next_instruction_valid=False,
        )
        self.assertTrue(result.pm_address_known)
        self.assertFalse(result.dreg_write_known)
        self.assertFalse(result.px_write_known)
        self.assertIs(read_dreg(result.state.primary, DREG.AX0), UNKNOWN)
        self.assertIs(result.state.px, UNKNOWN)
        self.assertIsNone(result.state.dag.i[4])

        conflict = apply_shifter_pm_cycle(
            result.state,
            execute=True,
            opcode=_opcode(write=True),
            pm_read_data=ExactWord(24, 0),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertTrue(conflict.instruction_complete)
        reset = apply_shifter_pm_cycle(conflict.state, reset=True)
        self.assertIsNone(reset.state.recovery)
        self.assertIs(reset.state.px, UNKNOWN)
        self.assertEqual(reset.state.dag.i, (None,) * 8)


if __name__ == "__main__":
    unittest.main()
