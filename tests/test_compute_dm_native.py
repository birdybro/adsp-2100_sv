from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    ComputeDMNativeState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    LogicalPhase,
    UNKNOWN,
    apply_compute_dm_native_cycle,
    read_dreg,
)


def _opcode(
    *,
    write: bool = False,
    dag: int = 0,
    z: int = 0,
    amf: int = 0,
    yop: int = 0,
    xop: int = 0,
    dreg: DREG = DREG.AX0,
    i: int = 0,
    m: int = 0,
) -> int:
    return (
        0x600000
        | (dag << 20)
        | (int(write) << 19)
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (int(dreg) << 4)
        | (i << 2)
        | m
    )


def _step(state: ComputeDMNativeState, **kwargs: object) -> ComputeDMNativeState:
    return apply_compute_dm_native_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        **kwargs,
    ).state


def _known_state() -> ComputeDMNativeState:
    state = ComputeDMNativeState.reset()
    state = _step(state, setup_astat=ExactWord(8, 0))
    for register, value in (
        (DREG.AX0, 2),
        (DREG.AY0, 3),
        (DREG.AR, 0x7777),
        (DREG.MX0, 2),
        (DREG.MY0, 3),
    ):
        state = _step(
            state,
            setup_dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        state = _step(
            state,
            setup_dag=DAGRegisterSetup(kind, 0, value),
        )
    return state


class ComputeDMNativeTests(unittest.TestCase):
    def test_compute_read_commits_only_at_native_completion(self) -> None:
        issue = apply_compute_dm_native_cycle(
            _known_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(amf=0x13, dreg=DREG.AX0),
        )
        self.assertTrue(issue.core.accepted and issue.bus.request_accepted)
        self.assertFalse(issue.core.instruction_complete)
        self.assertEqual(read_dreg(issue.state.core.primary, DREG.AR).value, 0x7777)
        self.assertEqual(read_dreg(issue.state.core.primary, DREG.AX0).value, 2)
        self.assertEqual(issue.state.core.dag.i[0], 0x100)

        state = issue.state
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            state = apply_compute_dm_native_cycle(state, phase=phase).state
        qualified = apply_compute_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        self.assertTrue(qualified.bus.dmack_accepted)
        done = apply_compute_dm_native_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xCAFE),
        )
        self.assertTrue(done.bus.read_sample_event)
        self.assertTrue(done.core.instruction_complete)
        self.assertEqual(read_dreg(done.state.core.primary, DREG.AR).value, 5)
        self.assertEqual(read_dreg(done.state.core.primary, DREG.AX0).value, 0xCAFE)
        self.assertEqual(done.state.core.dag.i[0], 0x101)
        self.assertFalse(done.state.core.status.astat.bit(ASTATBit.AZ))

    def test_compute_write_drives_old_destination_value(self) -> None:
        issue = apply_compute_dm_native_cycle(
            _known_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(write=True, amf=0x13, dreg=DREG.AR),
        )
        self.assertEqual(issue.core.dm_write_data, 0x7777)
        state = issue.state
        for phase in LogicalPhase:
            pins = apply_compute_dm_native_cycle(
                state,
                phase=phase,
                phase_advance=False,
            )
            expected_drive = phase in (
                LogicalPhase.STATE_5,
                LogicalPhase.STATE_6,
                LogicalPhase.STATE_7,
                LogicalPhase.STATE_8,
            )
            self.assertEqual(pins.bus.data_output_enable, expected_drive)
            if expected_drive:
                self.assertEqual(pins.bus.write_data, 0x7777)

    def test_wait_extension_holds_compute_read_and_dag_destinations(self) -> None:
        issue = apply_compute_dm_native_cycle(
            _known_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(amf=0x13, dreg=DREG.AX1),
        )
        low = apply_compute_dm_native_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
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
            held = apply_compute_dm_native_cycle(
                state,
                phase=phase,
                dm_ack=True,
                dmd_read_data=ExactWord(16, 0xAAAA),
            )
            self.assertTrue(held.core.stalled)
            self.assertFalse(held.core.instruction_complete)
            self.assertEqual(read_dreg(held.state.core.primary, DREG.AR).value, 0x7777)
            self.assertIs(read_dreg(held.state.core.primary, DREG.AX1), UNKNOWN)
            self.assertEqual(held.state.core.dag.i[0], 0x100)
            state = held.state
        high = apply_compute_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        done = apply_compute_dm_native_cycle(
            high.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0x1357),
        )
        self.assertEqual(read_dreg(done.state.core.primary, DREG.AR).value, 5)
        self.assertEqual(read_dreg(done.state.core.primary, DREG.AX1).value, 0x1357)
        self.assertEqual(done.state.core.dag.i[0], 0x101)

    def test_memory_only_read_has_no_compute_effect(self) -> None:
        state = _known_state()
        issue = apply_compute_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(z=1, yop=3, xop=7, dreg=DREG.SI),
        )
        qualified = apply_compute_dm_native_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        done = apply_compute_dm_native_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0x2468),
        )
        self.assertFalse(done.core.alu_write or done.core.mac_write)
        self.assertEqual(read_dreg(done.state.core.primary, DREG.SI).value, 0x2468)
        self.assertEqual(read_dreg(done.state.core.primary, DREG.AR).value, 0x7777)

    def test_late_ack_off_boundary_and_relinquishment_fail_closed(self) -> None:
        state = _known_state()
        off_phase = apply_compute_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_4,
            execute=True,
            opcode=_opcode(),
            setup_astat=ExactWord(8, 0xFF),
        )
        self.assertTrue(off_phase.phase_conflict)
        self.assertFalse(off_phase.core.accepted or off_phase.bus.request_accepted)
        self.assertEqual(off_phase.state, state)

        issue = apply_compute_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(dreg=DREG.AX1),
        )
        low = apply_compute_dm_native_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        late = apply_compute_dm_native_cycle(
            low.state,
            phase=LogicalPhase.STATE_7,
            dm_ack=True,
            dmd_read_data=ExactWord(16, 0x9999),
        )
        self.assertFalse(late.core.instruction_complete)

        masked = apply_compute_dm_native_cycle(
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

    def test_reset_cancels_core_and_native_descriptors(self) -> None:
        issue = apply_compute_dm_native_cycle(
            _known_state(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(write=True, amf=0x13, dreg=DREG.AR),
        )
        reset = apply_compute_dm_native_cycle(
            issue.state,
            reset=True,
            phase=LogicalPhase.STATE_4,
        )
        self.assertIsNone(reset.state.core.pending)
        self.assertFalse(reset.state.bus.active)
        self.assertFalse(reset.core.transaction_active)
        self.assertFalse(reset.bus.address_output_enable)


if __name__ == "__main__":
    unittest.main()
