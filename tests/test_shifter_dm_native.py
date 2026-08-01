from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    LogicalPhase,
    ShifterDMNativeState,
    UNKNOWN,
    apply_shifter_dm_native_cycle,
    read_dreg,
)


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


def _dreg(
    state: ShifterDMNativeState, register: DREG, value: int
) -> ShifterDMNativeState:
    return apply_shifter_dm_native_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        setup_dreg=DREGWrite(register, ExactWord(16, value)),
    ).state


def _dag(
    state: ShifterDMNativeState,
    kind: DAGRegisterKind,
    address: int,
    value: int,
) -> ShifterDMNativeState:
    return apply_shifter_dm_native_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        setup_dag=DAGRegisterSetup(kind, address, value),
    ).state


def _known_state() -> ShifterDMNativeState:
    state = ShifterDMNativeState.reset()
    state = _dreg(state, DREG.SI, 0x1234)
    state = _dreg(state, DREG.SE, 0)
    state = _dag(state, DAGRegisterKind.I, 0, 0x0100)
    state = _dag(state, DAGRegisterKind.M, 0, 1)
    state = _dag(state, DAGRegisterKind.L, 0, 0)
    return state


def _sr(state: ShifterDMNativeState) -> int | None:
    core = state.core
    bank = core.alternate if core.status.alternate_bank else core.primary
    if not all(isinstance(value, ExactWord) for value in bank.sr):
        return None
    sr0, sr1 = bank.sr
    assert isinstance(sr0, ExactWord) and isinstance(sr1, ExactWord)
    return (sr1.value << 16) | sr0.value


class ShifterDMNativeTests(unittest.TestCase):
    def test_read_commits_all_actions_only_at_native_completion(self) -> None:
        issue = apply_shifter_dm_native_cycle(
            _known_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX0),
        )
        self.assertTrue(issue.core.accepted and issue.bus.request_accepted)
        self.assertFalse(issue.core.instruction_complete)
        self.assertIs(read_dreg(issue.state.core.primary, DREG.AX0), UNKNOWN)
        self.assertIsNone(_sr(issue.state))
        self.assertEqual(issue.state.core.dag.i[0], 0x0100)

        state = issue.state
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            step = apply_shifter_dm_native_cycle(
                state,
                phase=phase,
                dmd_read_data=ExactWord(16, 0x1111),
            )
            self.assertFalse(step.core.instruction_complete)
            state = step.state
        qualified = apply_shifter_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
            dmd_read_data=ExactWord(16, 0x2222),
        )
        self.assertTrue(qualified.bus.dmack_accepted)
        self.assertFalse(qualified.core.instruction_complete)
        done = apply_shifter_dm_native_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xABCD),
        )
        self.assertTrue(done.bus.read_sample_event)
        self.assertTrue(done.core.instruction_complete)
        self.assertTrue(done.core.dreg_write_known)
        self.assertEqual(
            read_dreg(done.state.core.primary, DREG.AX0),
            ExactWord(16, 0xABCD),
        )
        self.assertEqual(_sr(done.state), 0x12340000)
        self.assertEqual(done.state.core.dag.i[0], 0x0101)

    def test_write_uses_cycle_start_dreg_and_native_drive_window(self) -> None:
        state = _known_state()
        state = _dreg(state, DREG.SR0, 0x5678)
        state = _dreg(state, DREG.SR1, 0x9ABC)
        issue = apply_shifter_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(write=True, dreg=DREG.SR0),
        )
        state = issue.state
        for phase in LogicalPhase:
            pins = apply_shifter_dm_native_cycle(
                state, phase=phase, phase_advance=False
            )
            expected_drive = phase in (
                LogicalPhase.STATE_5,
                LogicalPhase.STATE_6,
                LogicalPhase.STATE_7,
                LogicalPhase.STATE_8,
            )
            self.assertEqual(pins.bus.data_output_enable, expected_drive)
            if expected_drive:
                self.assertEqual(pins.bus.write_data, 0x5678)

    def test_wait_extension_holds_parallel_destinations(self) -> None:
        issue = apply_shifter_dm_native_cycle(
            _known_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
        )
        low = apply_shifter_dm_native_cycle(
            issue.state, phase=LogicalPhase.STATE_6, dm_ack=False
        )
        self.assertTrue(low.bus.wait_extension_event)
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
            held = apply_shifter_dm_native_cycle(
                state,
                phase=phase,
                dm_ack=True,
                dmd_read_data=ExactWord(16, 0xAAAA),
            )
            self.assertTrue(held.core.stalled)
            self.assertFalse(held.core.i_write or held.core.dreg_write)
            self.assertEqual(held.state.core.dag.i[0], 0x0100)
            self.assertIs(
                read_dreg(held.state.core.primary, DREG.AX1), UNKNOWN
            )
            self.assertIsNone(_sr(held.state))
            state = held.state
        high = apply_shifter_dm_native_cycle(
            state, phase=LogicalPhase.STATE_6, dm_ack=True
        )
        done = apply_shifter_dm_native_cycle(
            high.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xCAFE),
        )
        self.assertEqual(
            read_dreg(done.state.core.primary, DREG.AX1),
            ExactWord(16, 0xCAFE),
        )
        self.assertEqual(done.state.core.dag.i[0], 0x0101)

    def test_late_ack_and_invalid_read_data_remain_explicit(self) -> None:
        issue = apply_shifter_dm_native_cycle(
            _known_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
        )
        low = apply_shifter_dm_native_cycle(
            issue.state, phase=LogicalPhase.STATE_6, dm_ack=False
        )
        late = apply_shifter_dm_native_cycle(
            low.state,
            phase=LogicalPhase.STATE_7,
            dm_ack=True,
            dmd_read_data=UNKNOWN,
        )
        self.assertFalse(late.core.instruction_complete)
        self.assertIs(read_dreg(late.state.core.primary, DREG.AX1), UNKNOWN)

    def test_off_boundary_controls_fail_closed(self) -> None:
        state = _known_state()
        result = apply_shifter_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_4,
            execute=True,
            opcode=_opcode(),
            setup_astat=ExactWord(8, 0xFF),
        )
        self.assertTrue(result.phase_conflict)
        self.assertTrue(result.integration_conflict)
        self.assertFalse(result.core.accepted or result.bus.request_accepted)
        self.assertEqual(result.state, state)

    def test_relinquishment_masks_and_holds_read(self) -> None:
        issue = apply_shifter_dm_native_cycle(
            _known_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(),
        )
        low = apply_shifter_dm_native_cycle(
            issue.state, phase=LogicalPhase.STATE_6, dm_ack=False
        )
        masked = apply_shifter_dm_native_cycle(
            low.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
            dmd_read_data=ExactWord(16, 0x1234),
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
