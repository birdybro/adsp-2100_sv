import unittest

from sim.reference_models.adsp2100_model import (
    DirectDMNativeState,
    ExactWord,
    InternalMoveSetup,
    LogicalPhase,
    UNKNOWN,
    apply_direct_dm_native_cycle,
    read_internal_move_register,
    register_code_by_name,
)


READABLE = register_code_by_name(writable=False)
WRITABLE = register_code_by_name(writable=True)


def _opcode(register: str, address: int, *, write: bool) -> int:
    code = (READABLE if write else WRITABLE)[register]
    return (
        0x800000
        | (int(write) << 20)
        | ((code >> 4) << 18)
        | (address << 4)
        | (code & 0xF)
    )


def _step(state: DirectDMNativeState, **kwargs: object) -> DirectDMNativeState:
    return apply_direct_dm_native_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        **kwargs,
    ).state


class DirectDMNativeTests(unittest.TestCase):
    def test_read_commits_only_at_native_state_seven_completion(self):
        state = _step(
            DirectDMNativeState.reset(),
            setup=InternalMoveSetup(WRITABLE["AX0"], 0x1111),
        )
        issue = apply_direct_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode("AX0", 0x1234, write=False),
        )
        self.assertTrue(issue.core.accepted and issue.bus.request_accepted)
        before, _ = read_internal_move_register(
            issue.state.core.registers,
            WRITABLE["AX0"],
        )
        self.assertEqual(before, ExactWord(16, 0x1111))

        qualified = apply_direct_dm_native_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        done = apply_direct_dm_native_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0xCAFE),
        )
        after, _ = read_internal_move_register(
            done.state.core.registers,
            WRITABLE["AX0"],
        )
        self.assertTrue(done.bus.read_sample_event)
        self.assertTrue(done.core.instruction_complete)
        self.assertEqual(after, ExactWord(16, 0xCAFE))

    def test_write_descriptor_and_drive_window_use_cycle_start_source(self):
        state = _step(
            DirectDMNativeState.reset(),
            setup=InternalMoveSetup(WRITABLE["AY0"], 0x2468),
        )
        issue = apply_direct_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode("AY0", 0x3ABC, write=True),
        )
        self.assertEqual(issue.core.dm_write_data, 0x2468)
        self.assertEqual(issue.bus.state.address.value, 0x3ABC)
        for phase in LogicalPhase:
            pins = apply_direct_dm_native_cycle(
                issue.state,
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
                self.assertEqual(pins.bus.write_data, 0x2468)

    def test_wait_extension_holds_read_destination(self):
        state = _step(
            DirectDMNativeState.reset(),
            setup=InternalMoveSetup(WRITABLE["MR1"], 0x1234),
        )
        issue = apply_direct_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode("MR1", 0x20, write=False),
        )
        low = apply_direct_dm_native_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        self.assertTrue(low.bus.wait_extension_event)
        held_state = low.state
        for phase in (
            LogicalPhase.STATE_7,
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
        ):
            held = apply_direct_dm_native_cycle(
                held_state,
                phase=phase,
                dmd_read_data=ExactWord(16, 0xAAAA),
            )
            value, _ = read_internal_move_register(
                held.state.core.registers,
                WRITABLE["MR1"],
            )
            self.assertTrue(held.core.stalled)
            self.assertFalse(held.core.instruction_complete)
            self.assertEqual(value, ExactWord(16, 0x1234))
            held_state = held.state
        high = apply_direct_dm_native_cycle(
            held_state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        done = apply_direct_dm_native_cycle(
            high.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=ExactWord(16, 0x8001),
        )
        value, _ = read_internal_move_register(
            done.state.core.registers,
            WRITABLE["MR1"],
        )
        self.assertEqual(value, ExactWord(16, 0x8001))
        self.assertEqual(
            done.state.core.registers.primary.mr[2],
            ExactWord(8, 0xFF),
        )

    def test_off_boundary_relinquishment_and_late_ack_fail_closed(self):
        state = DirectDMNativeState.reset()
        off = apply_direct_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_4,
            execute=True,
            opcode=_opcode("AX0", 0, write=False),
            setup=InternalMoveSetup(WRITABLE["AX1"], 1),
        )
        self.assertTrue(off.phase_conflict)
        self.assertFalse(off.core.accepted or off.bus.request_accepted)
        self.assertEqual(off.state, state)

        issue = apply_direct_dm_native_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode("AX0", 0, write=False),
        )
        low = apply_direct_dm_native_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=False,
        )
        late = apply_direct_dm_native_cycle(
            low.state,
            phase=LogicalPhase.STATE_7,
            dm_ack=True,
            dmd_read_data=ExactWord(16, 0x9999),
        )
        self.assertFalse(late.core.instruction_complete)

        masked = apply_direct_dm_native_cycle(
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

    def test_invalid_read_data_and_reset_remain_explicit(self):
        issue = apply_direct_dm_native_cycle(
            DirectDMNativeState.reset(),
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode("AX0", 0, write=False),
        )
        qualified = apply_direct_dm_native_cycle(
            issue.state,
            phase=LogicalPhase.STATE_6,
            dm_ack=True,
        )
        done = apply_direct_dm_native_cycle(
            qualified.state,
            phase=LogicalPhase.STATE_7,
            dmd_read_data=UNKNOWN,
        )
        value, _ = read_internal_move_register(
            done.state.core.registers,
            WRITABLE["AX0"],
        )
        self.assertTrue(done.core.dreg_write)
        self.assertFalse(done.core.dreg_write_known)
        self.assertIs(value, UNKNOWN)

        reset = apply_direct_dm_native_cycle(
            issue.state,
            reset=True,
            phase=LogicalPhase.STATE_4,
        )
        self.assertIsNone(reset.state.core.pending)
        self.assertFalse(reset.state.bus.active)
        self.assertFalse(reset.core.transaction_active)


if __name__ == "__main__":
    unittest.main()
