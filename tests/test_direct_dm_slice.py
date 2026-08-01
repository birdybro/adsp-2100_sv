import unittest

from sim.reference_models.adsp2100_model import (
    DirectDMSliceState,
    ExactWord,
    InternalMoveSetup,
    UNKNOWN,
    apply_direct_dm_cycle,
    read_internal_move_register,
    register_code_by_name,
)


READABLE = register_code_by_name(writable=False)
WRITABLE = register_code_by_name(writable=True)


def _opcode(register_code: int, address: int, *, write: bool) -> int:
    return (
        0x800000
        | (int(write) << 20)
        | ((register_code >> 4) << 18)
        | (address << 4)
        | (register_code & 0xF)
    )


def _setup(
    state: DirectDMSliceState,
    register: str,
    value: int,
) -> DirectDMSliceState:
    return apply_direct_dm_cycle(
        state,
        setup=InternalMoveSetup(WRITABLE[register], value),
    ).state


class DirectDMSliceTests(unittest.TestCase):
    def test_write_captures_cycle_start_source_and_direct_address(self):
        state = _setup(DirectDMSliceState.reset(), "AX0", 0x1234)
        issue = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(READABLE["AX0"], 0x3ABC, write=True),
            dm_ack=False,
        )
        self.assertTrue(issue.accepted and issue.stalled and issue.busy)
        self.assertTrue(issue.dm_select and issue.dm_write)
        self.assertFalse(issue.dm_read)
        self.assertEqual(issue.dm_address, 0x3ABC)
        self.assertTrue(issue.dm_address_known)
        self.assertEqual(issue.dm_write_data, 0x1234)
        self.assertTrue(issue.dm_write_data_known)

        held = apply_direct_dm_cycle(
            issue.state,
            dm_ack=False,
            setup=InternalMoveSetup(WRITABLE["AX0"], 0x5678),
        )
        self.assertTrue(held.integration_conflict and held.stalled)
        self.assertEqual(held.dm_write_data, 0x1234)
        done = apply_direct_dm_cycle(held.state, dm_ack=True)
        self.assertTrue(done.instruction_complete)
        self.assertEqual(done.dm_write_data, 0x1234)
        self.assertEqual(done.state.registers, state.registers)

    def test_read_commits_only_on_ack_and_preserves_direct_address(self):
        state = _setup(DirectDMSliceState.reset(), "AY1", 0x1111)
        issue = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(WRITABLE["AY1"], 0x0123, write=False),
            dm_ack=False,
            dm_read_data=ExactWord(16, 0xAAAA),
        )
        before, _ = read_internal_move_register(
            issue.state.registers,
            WRITABLE["AY1"],
        )
        self.assertEqual(before, ExactWord(16, 0x1111))
        self.assertTrue(issue.dm_read and issue.stalled)
        self.assertEqual(issue.dm_address, 0x0123)

        done = apply_direct_dm_cycle(
            issue.state,
            dm_ack=True,
            dm_read_data=ExactWord(16, 0xBEEF),
        )
        after, _ = read_internal_move_register(
            done.state.registers,
            WRITABLE["AY1"],
        )
        self.assertTrue(done.instruction_complete and done.dreg_write)
        self.assertTrue(done.dreg_write_known)
        self.assertEqual(after, ExactWord(16, 0xBEEF))

    def test_every_legal_selector_executes_both_applicable_directions(self):
        state = DirectDMSliceState.reset()
        executions = 0
        for register, code in READABLE.items():
            if register in WRITABLE:
                state = _setup(state, register, (code * 0x101) & 0xFFFF)
            write = apply_direct_dm_cycle(
                state,
                execute=True,
                opcode=_opcode(code, code & 0x3FFF, write=True),
                dm_ack=True,
            )
            self.assertTrue(write.instruction_complete and write.dm_write)
            self.assertEqual(write.dm_address, code)
            state = write.state
            executions += 1

        for register, code in WRITABLE.items():
            value = (0xA000 | code) & 0xFFFF
            read = apply_direct_dm_cycle(
                state,
                execute=True,
                opcode=_opcode(code, 0x3FFF - code, write=False),
                dm_ack=True,
                dm_read_data=ExactWord(16, value),
            )
            self.assertTrue(read.instruction_complete and read.dm_read)
            observed, _ = read_internal_move_register(read.state.registers, code)
            self.assertIsNot(observed, UNKNOWN)
            state = read.state
            executions += 1
        self.assertEqual(executions, 95)

    def test_status_source_extension_is_visible_and_read_does_not_generate_it(self):
        state = _setup(DirectDMSliceState.reset(), "ASTAT", 0x00A5)
        write = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(READABLE["ASTAT"], 7, write=True),
            dm_ack=False,
        )
        self.assertTrue(write.source_extension_provisional)
        self.assertEqual(write.dm_write_data, 0x00A5)
        done = apply_direct_dm_cycle(write.state, dm_ack=True)
        self.assertTrue(done.source_extension_provisional)

        read = apply_direct_dm_cycle(
            done.state,
            execute=True,
            opcode=_opcode(WRITABLE["ASTAT"], 8, write=False),
            dm_ack=True,
            dm_read_data=ExactWord(16, 0xFF5A),
        )
        self.assertFalse(read.source_extension_provisional)
        astat, provisional = read_internal_move_register(
            read.state.registers,
            WRITABLE["ASTAT"],
        )
        self.assertEqual(astat, ExactWord(16, 0x005A))
        self.assertTrue(provisional)

    def test_read_cntr_uses_load_push_side_effect(self):
        state = _setup(DirectDMSliceState.reset(), "CNTR", 3)
        result = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(WRITABLE["CNTR"], 0x20, write=False),
            dm_ack=True,
            dm_read_data=ExactWord(16, 7),
        )
        self.assertTrue(result.count_stack_push)
        self.assertEqual(result.count_stack_push_value, 3)
        self.assertEqual(result.state.registers.cntr, 7)
        self.assertEqual(result.state.registers.stacks.count_entries, (3,))

    def test_read_mr1_sign_fills_mr2_in_selected_bank(self):
        state = apply_direct_dm_cycle(
            DirectDMSliceState.reset(),
            setup=InternalMoveSetup(WRITABLE["MSTAT"], 1),
        ).state
        result = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(WRITABLE["MR1"], 0, write=False),
            dm_ack=True,
            dm_read_data=ExactWord(16, 0x8001),
        )
        self.assertEqual(result.state.registers.alternate.mr[1], ExactWord(16, 0x8001))
        self.assertEqual(result.state.registers.alternate.mr[2], ExactWord(8, 0xFF))
        self.assertIs(result.state.registers.primary.mr[1], UNKNOWN)

    def test_unknown_write_source_and_read_data_remain_explicit(self):
        write = apply_direct_dm_cycle(
            DirectDMSliceState.reset(),
            execute=True,
            opcode=_opcode(READABLE["AX0"], 0, write=True),
            dm_ack=True,
        )
        self.assertFalse(write.dm_write_data_known)
        read = apply_direct_dm_cycle(
            write.state,
            execute=True,
            opcode=_opcode(WRITABLE["AX1"], 1, write=False),
            dm_ack=True,
            dm_read_data=UNKNOWN,
        )
        self.assertTrue(read.dreg_write)
        self.assertFalse(read.dreg_write_known)
        value, _ = read_internal_move_register(
            read.state.registers,
            WRITABLE["AX1"],
        )
        self.assertIs(value, UNKNOWN)

    def test_invalid_setup_conflict_and_reset_are_atomic(self):
        state = _setup(DirectDMSliceState.reset(), "AX0", 0x1357)
        invalid = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(0x3F, 0, write=True),
            dm_ack=True,
        )
        self.assertTrue(invalid.invalid_subencoding)
        self.assertEqual(invalid.state, state)

        nonclass = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=0,
            dm_ack=True,
        )
        self.assertTrue(nonclass.invalid_opcode)
        self.assertEqual(nonclass.state, state)

        conflict = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(READABLE["AX0"], 0, write=True),
            dm_ack=True,
            setup=InternalMoveSetup(WRITABLE["AY0"], 0x2468),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertFalse(conflict.accepted)
        self.assertEqual(conflict.state, state)

        pending = apply_direct_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(READABLE["AX0"], 0, write=True),
            dm_ack=False,
        )
        reset = apply_direct_dm_cycle(pending.state, reset=True, dm_ack=True)
        self.assertIsNone(reset.state.pending)
        self.assertFalse(reset.transaction_active or reset.instruction_complete)
        self.assertEqual(reset.state.registers.mstat, 0)

    def test_width_contracts_fail_closed(self):
        with self.assertRaises(ValueError):
            apply_direct_dm_cycle(DirectDMSliceState.reset(), opcode=0x1000000)
        with self.assertRaises(ValueError):
            apply_direct_dm_cycle(
                DirectDMSliceState.reset(),
                dm_read_data=ExactWord(8, 0),
            )


if __name__ == "__main__":
    unittest.main()
