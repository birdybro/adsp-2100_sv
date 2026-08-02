from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    DREG,
    ExactWord,
    LinearCoreState,
    LogicalPhase,
    UNKNOWN,
    apply_linear_core_cycle,
    read_dreg,
    register_code_by_name,
)


ROOT = Path(__file__).resolve().parents[1]


def _type6(destination: DREG, data: int) -> int:
    return 0x400000 | ((data & 0xFFFF) << 4) | int(destination)


def _type7(code: int, data: int) -> int:
    return 0x300000 | ((code >> 4) << 18) | ((data & 0x3FFF) << 4) | (code & 0xF)


def _type18(payload: int) -> int:
    return 0x0C0000 | ((payload & 0xFF) << 4)


def _type21(*, dag: int, i_local: int, m_local: int) -> int:
    return (
        0x090000
        | ((dag & 1) << 4)
        | ((i_local & 3) << 2)
        | (m_local & 3)
    )


def _type26(payload: int) -> int:
    return 0x040000 | (payload & 0x1F)


def _type10(*, call: bool, address: int, condition: int) -> int:
    return (
        0x180000
        | (int(call) << 18)
        | ((address & 0x3FFF) << 4)
        | (condition & 0xF)
    )


def _type11(*, end_address: int, termination: int) -> int:
    return (
        0x140000
        | ((end_address & 0x3FFF) << 4)
        | (termination & 0xF)
    )


def _type20(*, interrupt_return: bool, condition: int) -> int:
    return 0x0A0000 | (int(interrupt_return) << 4) | (condition & 0xF)


def _type22(condition: int) -> int:
    return 0x080000 | (condition & 0xF)


def _type19(*, call: bool, i_local: int, condition: int) -> int:
    return (
        0x0B0000
        | ((i_local & 3) << 6)
        | (int(call) << 4)
        | (condition & 0xF)
    )


def _type17(destination: int, source: int) -> int:
    return (
        0x0D0000
        | ((destination >> 4) << 10)
        | ((source >> 4) << 8)
        | ((destination & 0xF) << 4)
        | (source & 0xF)
    )


def _type9(
    *,
    z: int,
    amf: int,
    yop: int,
    xop: int,
    condition: int,
) -> int:
    return (
        0x200000
        | ((z & 1) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 0x3) << 11)
        | ((xop & 0x7) << 8)
        | (condition & 0xF)
    )


def _type8(
    *, z: int, amf: int, yop: int, xop: int, destination: DREG, source: DREG
) -> int:
    return (
        0x280000
        | ((z & 1) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 0x3) << 11)
        | ((xop & 0x7) << 8)
        | (int(destination) << 4)
        | int(source)
    )


def _type14(
    *, sf: int, xop: int, destination: DREG, source: DREG
) -> int:
    return (
        0x100000
        | ((sf & 0xF) << 11)
        | ((xop & 0x7) << 8)
        | (int(destination) << 4)
        | int(source)
    )


def _type25() -> int:
    return 0x050000


def _type23(xop: int) -> int:
    return 0x071000 | ((xop & 0x7) << 8)


def _type24(yop: int, xop: int) -> int:
    return 0x060000 | ((yop & 0x3) << 11) | ((xop & 0x7) << 8)


def _type15(*, sf: int, xop: int, exponent: int) -> int:
    return 0x0F0000 | ((sf & 0xF) << 11) | ((xop & 0x7) << 8) | (exponent & 0xFF)


def _type16(*, sf: int, xop: int, condition: int) -> int:
    return 0x0E0000 | ((sf & 0xF) << 11) | ((xop & 0x7) << 8) | (condition & 0xF)


def _setup(state: LinearCoreState, opcode: int, *, pc: int = 4) -> LinearCoreState:
    result = apply_linear_core_cycle(
        state,
        phase=LogicalPhase.STATE_8,
        instruction_setup=(ExactWord(14, pc), ExactWord(24, opcode)),
    )
    assert result.instruction_setup_accepted
    return result.state


def _issue(state: LinearCoreState):
    return apply_linear_core_cycle(state, phase=LogicalPhase.STATE_8)


def _complete(state: LinearCoreState, next_opcode: int | None):
    for phase in range(6):
        state = apply_linear_core_cycle(
            state,
            phase=LogicalPhase(phase),
        ).state
    return apply_linear_core_cycle(
        state,
        phase=LogicalPhase.STATE_7,
        pmd_read_data=(
            UNKNOWN if next_opcode is None else ExactWord(24, next_opcode)
        ),
    )


def _complete_with_irq(
    state: LinearCoreState,
    next_opcode: int | None,
    *,
    irq_n: int,
):
    for phase in range(6):
        state = apply_linear_core_cycle(
            state,
            phase=LogicalPhase(phase),
            irq_n=irq_n,
        ).state
    return apply_linear_core_cycle(
        state,
        phase=LogicalPhase.STATE_7,
        pmd_read_data=(
            UNKNOWN if next_opcode is None else ExactWord(24, next_opcode)
        ),
        irq_n=irq_n,
    )


class LinearCoreTests(unittest.TestCase):
    def test_machine_readable_contract_matches_bounded_owner(self) -> None:
        contract = json.loads(
            (ROOT / "docs/generated/adsp2100_linear_core.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(
            contract["issue_boundary"],
            "ENABLED_STATE_8_TO_STATE_1_EDGE",
        )
        self.assertEqual(
            contract["retire_boundary"],
            "ENABLED_STATE_7_TO_STATE_8_EDGE",
        )
        self.assertIn(
            "RESET_RELEASE_AND_FIRST_FETCH_WAVEFORM",
            contract["excluded_claims"],
        )
        self.assertIn(
            "ALL_TYPE_18_MODE_CONTROL_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_2256_LEGAL_TYPE_17_INTERNAL_MOVES",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_TYPE_9_CONDITIONAL_ALU_MAC_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_25648_CANONICAL_TYPE_14_SHIFT_MOVE_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "EXACT_TYPE_25_MR_SATURATION_WORD",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_8_TYPE_23_DIVQ_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_476672_SOURCE_CLOSED_TYPE_8_COMPUTE_MOVE_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_16_SOURCE_CLOSED_TYPE_24_DIVS_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_32_TYPE_21_MODIFY_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_32_TYPE_26_STACK_CONTROL_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_507904_SOURCE_CLOSED_TYPE_10_DIRECT_TRANSFERS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_262144_TYPE_11_DO_UNTIL_WORDS_WITH_BOUNDED_LOOP_FLOW",
            contract["supported_current_instructions"],
        )
        self.assertEqual(
            contract["ordinary_fetch_address"],
            "SELECTED_NEXT_PC_INCLUDES_SEQUENTIAL_EXPLICIT_TRANSFER_AND_AUTOMATIC_LOOP_FLOW",
        )
        self.assertIn(
            "ALL_124_SOURCE_CLOSED_TYPE_19_INDIRECT_TRANSFERS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_32_TYPE_20_CONDITIONAL_RETURN_WORDS_WITH_VALID_TAKEN_CONTEXT",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_16_TYPE_22_CONDITIONAL_TRAP_WORDS_WITH_RETIREMENT_EVENT",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_14336_SUPPORTED_TYPE_15_IMMEDIATE_SHIFT_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertIn(
            "ALL_1792_SUPPORTED_TYPE_16_CONDITIONAL_SHIFT_WORDS",
            contract["supported_current_instructions"],
        )
        self.assertEqual(
            contract["type26_valid_combined_context"],
            "STATUS_COUNT_PC_LOOP_POP_ATOMIC_AT_NATIVE_RETIREMENT_AWAY_FROM_LOOP_TERMINAL",
        )
        self.assertIn("OQ_016", contract["provisional_behavior"])

    def test_nop_fetches_pc_plus_one_and_retires_at_state_seven(self) -> None:
        state = _setup(LinearCoreState.reset(), 0)
        issued = _issue(state)
        self.assertTrue(issued.instruction_issue)
        self.assertEqual(issued.state.bus.address, ExactWord(14, 5))
        self.assertFalse(issued.bus.pmda)
        self.assertFalse(issued.retire_event)
        done = _complete(issued.state, _type6(DREG.AX0, 0x1234))
        self.assertTrue(done.retire_event)
        self.assertTrue(done.bus.read_sample_event)
        self.assertEqual(done.state.architecture.pc, ExactWord(14, 5))
        self.assertEqual(done.state.instruction, ExactWord(24, _type6(DREG.AX0, 0x1234)))
        self.assertTrue(done.state.instruction_valid)

    def test_level_interrupt_discards_fetch_and_vectors_through_nop_cycle(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ICNTL"], 0x10),
            pc=0x0100,
        )
        configured_icntl = _complete_with_irq(
            _issue(state).state,
            _type7(writable["IMASK"], 0xF),
            irq_n=0xF,
        )
        configured_mask = _complete_with_irq(
            _issue(configured_icntl.state).state,
            0,
            irq_n=0xF,
        )
        interrupted = _complete_with_irq(
            _issue(configured_mask.state).state,
            _type6(DREG.AX0, 0xDEAD),
            irq_n=0xB,
        )
        self.assertTrue(interrupted.retire_event)
        self.assertTrue(interrupted.interrupt_recognition_event)
        self.assertEqual(interrupted.interrupt_level, 2)
        self.assertEqual(interrupted.state.architecture.pc, ExactWord(14, 0x0103))
        self.assertFalse(interrupted.state.instruction_valid)
        self.assertTrue(interrupted.state.interrupt_vectoring)

        vector_issue = apply_linear_core_cycle(
            interrupted.state,
            phase=LogicalPhase.STATE_8,
            irq_n=0xF,
        )
        self.assertTrue(vector_issue.interrupt_entry_event)
        self.assertTrue(vector_issue.interrupt_vector_issue_event)
        self.assertEqual(vector_issue.state.bus.address, ExactWord(14, 2))
        self.assertEqual(
            vector_issue.state.architecture.pc_stack[-1],
            ExactWord(14, 0x0103),
        )
        self.assertEqual(len(vector_issue.state.architecture.status_stack), 1)
        self.assertEqual(vector_issue.state.architecture.imask, ExactWord(4, 0x8))

        vector_loaded = _complete_with_irq(
            vector_issue.state,
            _type20(interrupt_return=True, condition=0xF),
            irq_n=0xF,
        )
        self.assertTrue(vector_loaded.interrupt_vector_fetch_event)
        self.assertFalse(vector_loaded.retire_event)
        self.assertEqual(vector_loaded.state.architecture.pc, ExactWord(14, 2))
        self.assertTrue(vector_loaded.state.instruction_valid)

        rti_issue = _issue(vector_loaded.state)
        self.assertEqual(rti_issue.state.bus.address, ExactWord(14, 0x0103))
        returned = _complete_with_irq(
            rti_issue.state,
            _type6(DREG.AX0, 0xDEAD),
            irq_n=0xF,
        )
        self.assertTrue(returned.retire_event)
        self.assertEqual(returned.state.architecture.pc, ExactWord(14, 0x0103))
        self.assertEqual(returned.state.architecture.imask, ExactWord(4, 0xF))
        self.assertFalse(returned.state.architecture.pc_stack)
        self.assertFalse(returned.state.architecture.status_stack)

    def test_interrupt_adjacent_mode_write_fails_closed_under_oq015(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ICNTL"], 0),
            pc=0x0200,
        )
        first = _complete_with_irq(
            _issue(state).state,
            _type7(writable["IMASK"], 1),
            irq_n=0xF,
        )
        second = _complete_with_irq(
            _issue(first.state).state,
            _type18(0x03),
            irq_n=0xF,
        )
        blocked = _complete_with_irq(
            _issue(second.state).state,
            0,
            irq_n=0xE,
        )
        self.assertTrue(blocked.retire_event)
        self.assertFalse(blocked.interrupt_recognition_event)
        self.assertTrue(blocked.interrupt_adjacent_control_conflict)
        self.assertTrue(blocked.internal_conflict)
        self.assertFalse(blocked.state.interrupt_vectoring)

        recognized = _complete_with_irq(
            _issue(blocked.state).state,
            0,
            irq_n=0xE,
        )
        self.assertTrue(recognized.interrupt_recognition_event)
        self.assertTrue(recognized.state.interrupt_vectoring)

    def test_type7_bank_switch_controls_following_type6(self) -> None:
        state = _setup(LinearCoreState.reset(), _type7(0x31, 1))
        first = _complete(_issue(state).state, _type6(DREG.AX0, 0xA55A))
        self.assertEqual(first.state.architecture.mstat, ExactWord(4, 1))
        second = _complete(_issue(first.state).state, 0)
        self.assertEqual(
            read_dreg(second.state.architecture.alternate, DREG.AX0),
            ExactWord(16, 0xA55A),
        )
        self.assertIs(
            read_dreg(second.state.architecture.primary, DREG.AX0),
            UNKNOWN,
        )

    def test_type18_bank_switch_controls_following_type6(self) -> None:
        state = _setup(LinearCoreState.reset(), _type18(0xBB))
        first = _complete(_issue(state).state, _type6(DREG.AX0, 0xA55A))
        self.assertEqual(first.state.architecture.mstat, ExactWord(4, 0x5))
        second = _complete(_issue(first.state).state, 0)
        self.assertEqual(
            read_dreg(second.state.architecture.alternate, DREG.AX0),
            ExactWord(16, 0xA55A),
        )
        self.assertIs(
            read_dreg(second.state.architecture.primary, DREG.AX0),
            UNKNOWN,
        )

    def test_type17_move_commits_before_following_bank_selected_load(self) -> None:
        state = _setup(LinearCoreState.reset(), _type6(DREG.AX0, 1))
        loaded = _complete(_issue(state).state, _type17(0x31, int(DREG.AX0)))
        moved = _complete(
            _issue(loaded.state).state,
            _type6(DREG.AX1, 0xA55A),
        )
        self.assertEqual(moved.state.architecture.mstat, ExactWord(4, 1))
        self.assertFalse(moved.provisional_source_extension)
        written = _complete(_issue(moved.state).state, 0)
        self.assertEqual(
            read_dreg(written.state.architecture.alternate, DREG.AX1),
            ExactWord(16, 0xA55A),
        )
        self.assertIs(
            read_dreg(written.state.architecture.primary, DREG.AX1),
            UNKNOWN,
        )

    def test_type17_provisional_narrow_source_is_observable(self) -> None:
        state = _setup(LinearCoreState.reset(), _type7(0x31, 0xB))
        loaded = _complete(_issue(state).state, _type17(0x00, 0x31))
        moved = _complete(_issue(loaded.state).state, 0)
        self.assertTrue(moved.provisional_source_extension)
        self.assertEqual(
            read_dreg(moved.state.architecture.alternate, DREG.AX0),
            ExactWord(16, 0x000B),
        )

    def test_type21_modify_samples_old_dag_state_and_commits_at_retirement(
        self,
    ) -> None:
        state = _setup(LinearCoreState.reset(), _type7(0x10, 0x0102))
        for opcode in (
            _type7(0x14, 0x0003),
            _type7(0x18, 0x0005),
            _type21(dag=0, i_local=0, m_local=0),
        ):
            state = _complete(_issue(state).state, opcode).state

        issued = _issue(state)
        self.assertTrue(issued.instruction_issue)
        self.assertEqual(
            issued.state.architecture.dag.i[0],
            ExactWord(14, 0x0102),
        )
        retired = _complete(issued.state, 0)
        self.assertEqual(
            retired.state.architecture.dag.i[0],
            ExactWord(14, 0x0100),
        )
        self.assertEqual(
            retired.state.architecture.dag.m[0],
            ExactWord(14, 0x0003),
        )
        self.assertEqual(
            retired.state.architecture.dag.l[0],
            ExactWord(14, 0x0005),
        )
        self.assertEqual(retired.state.architecture.astat, UNKNOWN)

    def test_type26_stack_actions_commit_at_retirement(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0xA5),
        )
        for opcode in (
            _type7(writable["MSTAT"], 0x6),
            _type7(writable["IMASK"], 0x9),
            _type26(0x02),
            _type7(writable["ASTAT"], 0x12),
            _type7(writable["MSTAT"], 0x3),
            _type7(writable["IMASK"], 0x4),
            _type26(0x03),
            _type7(writable["CNTR"], 0x123),
            _type7(writable["CNTR"], 0x234),
            _type26(0x04),
        ):
            state = _complete(_issue(state).state, opcode).state

        issued = _issue(state)
        self.assertEqual(issued.state.architecture.cntr, ExactWord(14, 0x234))
        retired = _complete(issued.state, 0)
        architecture = retired.state.architecture
        self.assertEqual(architecture.astat, ExactWord(8, 0xA5))
        self.assertEqual(architecture.mstat, ExactWord(4, 0x6))
        self.assertEqual(architecture.imask, ExactWord(4, 0x9))
        self.assertEqual(architecture.cntr, ExactWord(14, 0x123))
        self.assertEqual(architecture.status_stack, ())
        self.assertEqual(architecture.count_stack, ())
        self.assertEqual(architecture.sstat.value & 0x54, 0x54)

    def test_type26_combined_valid_stack_pops_commit_atomically(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0xA5),
            pc=0x0680,
        )
        for opcode in (
            _type7(writable["MSTAT"], 0x6),
            _type7(writable["IMASK"], 0x9),
            _type26(0x02),
            _type7(writable["ASTAT"], 0x12),
            _type7(writable["MSTAT"], 0x3),
            _type7(writable["IMASK"], 0x4),
            _type7(writable["CNTR"], 0x123),
            _type7(writable["CNTR"], 0x234),
            _type11(end_address=0x06A0, termination=0xF),
            _type26(0x1F),
        ):
            state = _complete(_issue(state).state, opcode).state

        architecture = state.architecture
        self.assertEqual(architecture.astat, ExactWord(8, 0x12))
        self.assertEqual(architecture.mstat, ExactWord(4, 0x3))
        self.assertEqual(architecture.imask, ExactWord(4, 0x4))
        self.assertEqual(architecture.cntr, ExactWord(14, 0x234))
        self.assertEqual(len(architecture.status_stack), 1)
        self.assertEqual(len(architecture.count_stack), 1)
        self.assertEqual(len(architecture.pc_stack), 1)
        self.assertEqual(len(architecture.loop_stack), 1)

        issued = _issue(state)
        self.assertTrue(issued.instruction_issue)
        self.assertFalse(issued.internal_conflict)
        self.assertEqual(issued.state.bus.address, ExactWord(14, 0x068B))
        retired = _complete(issued.state, 0)
        architecture = retired.state.architecture
        self.assertTrue(retired.retire_event)
        self.assertEqual(architecture.pc, ExactWord(14, 0x068B))
        self.assertEqual(architecture.astat, ExactWord(8, 0xA5))
        self.assertEqual(architecture.mstat, ExactWord(4, 0x6))
        self.assertEqual(architecture.imask, ExactWord(4, 0x9))
        self.assertEqual(architecture.cntr, ExactWord(14, 0x123))
        self.assertEqual(architecture.status_stack, ())
        self.assertEqual(architecture.count_stack, ())
        self.assertEqual(architecture.pc_stack, ())
        self.assertEqual(architecture.loop_stack, ())
        self.assertEqual(architecture.sstat.value, 0x55)

    def test_type10_redirects_fetch_and_connects_call_stack(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0100,
        )
        state = _complete(
            _issue(state).state,
            _type10(call=False, address=0x2345, condition=0xF),
        ).state

        jumped = _issue(state)
        self.assertEqual(jumped.state.bus.address, ExactWord(14, 0x2345))
        state = _complete(
            jumped.state,
            _type10(call=True, address=0x3456, condition=0xF),
        ).state
        self.assertEqual(state.architecture.pc, ExactWord(14, 0x2345))

        called = _issue(state)
        self.assertEqual(called.state.bus.address, ExactWord(14, 0x3456))
        state = _complete(called.state, _type26(0x10)).state
        self.assertEqual(state.architecture.pc, ExactWord(14, 0x3456))
        self.assertEqual(state.architecture.pc_stack, (ExactWord(14, 0x2346),))
        self.assertEqual(state.architecture.sstat.value & 0x01, 0)

        popped = _complete(_issue(state).state, 0)
        self.assertEqual(popped.state.architecture.pc_stack, ())
        self.assertEqual(popped.state.architecture.sstat.value & 0x01, 1)

    def test_type10_false_and_not_ce_fetch_paths(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0200,
        )
        state = _complete(
            _issue(state).state,
            _type10(call=False, address=0x1234, condition=0x0),
        ).state
        false_jump = _issue(state)
        self.assertEqual(false_jump.state.bus.address, ExactWord(14, 0x0202))
        state = _complete(
            false_jump.state,
            _type7(writable["CNTR"], 7),
        ).state
        state = _complete(
            _issue(state).state,
            _type7(writable["CNTR"], 1),
        ).state
        state = _complete(
            _issue(state).state,
            _type10(call=False, address=0x1111, condition=0xE),
        ).state

        expired = _issue(state)
        self.assertEqual(
            expired.state.bus.address,
            state.architecture.pc.incremented(),
        )
        state = _complete(
            expired.state,
            _type10(call=False, address=0x1111, condition=0xE),
        ).state
        self.assertEqual(state.architecture.cntr, ExactWord(14, 7))
        self.assertEqual(state.architecture.count_stack, ())

        not_expired = _issue(state)
        self.assertEqual(not_expired.state.bus.address, ExactWord(14, 0x1111))
        retired = _complete(not_expired.state, 0)
        self.assertEqual(retired.state.architecture.pc, ExactWord(14, 0x1111))
        self.assertEqual(retired.state.architecture.cntr, ExactWord(14, 6))

    def test_type10_unknown_ce_context_fails_closed(self) -> None:
        state = _setup(
            LinearCoreState.reset(),
            _type10(call=False, address=0x1234, condition=0xE),
        )
        result = _issue(state)
        self.assertTrue(result.supported_instruction)
        self.assertTrue(result.internal_conflict)
        self.assertFalse(result.instruction_issue)
        self.assertFalse(result.state.pending)
        self.assertEqual(result.state.architecture.pc, ExactWord(14, 4))

    def test_type11_setup_and_non_counter_exit_retire_atomically(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0100,
        )
        state = _complete(
            _issue(state).state,
            _type11(end_address=0x0102, termination=0),
        ).state

        setup = _issue(state)
        self.assertEqual(setup.state.bus.address, ExactWord(14, 0x0102))
        state = _complete(setup.state, 0).state
        self.assertEqual(state.architecture.pc_stack, (ExactWord(14, 0x0102),))
        self.assertEqual(
            state.architecture.loop_stack,
            ((ExactWord(14, 0x0102), ExactWord(4, 0)),),
        )

        terminal = _issue(state)
        self.assertEqual(terminal.state.bus.address, ExactWord(14, 0x0103))
        retired = _complete(terminal.state, 0)
        self.assertEqual(retired.state.architecture.pc, ExactWord(14, 0x0103))
        self.assertEqual(retired.state.architecture.pc_stack, ())
        self.assertEqual(retired.state.architecture.loop_stack, ())
        self.assertEqual(retired.state.architecture.sstat.value & 0x41, 0x41)

    def test_loop_terminal_uses_cycle_start_status_before_writeback(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0200,
        )
        for opcode in (
            _type11(end_address=0x0202, termination=1),
            _type7(writable["ASTAT"], 1),
        ):
            state = _complete(_issue(state).state, opcode).state

        first_terminal = _issue(state)
        self.assertEqual(
            first_terminal.state.bus.address,
            ExactWord(14, 0x0202),
        )
        state = _complete(first_terminal.state, 0).state
        self.assertEqual(state.architecture.astat, ExactWord(8, 1))
        self.assertEqual(len(state.architecture.loop_stack), 1)

        second_terminal = _issue(state)
        self.assertEqual(
            second_terminal.state.bus.address,
            ExactWord(14, 0x0203),
        )
        retired = _complete(second_terminal.state, 0)
        self.assertEqual(retired.state.architecture.loop_stack, ())
        self.assertEqual(retired.state.architecture.pc_stack, ())

    def test_ce_loop_decrements_then_exits_and_invalidates_cntr(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["CNTR"], 2),
            pc=0x0300,
        )
        for opcode in (
            _type11(end_address=0x0302, termination=0xE),
            0,
        ):
            state = _complete(_issue(state).state, opcode).state

        first_terminal = _issue(state)
        self.assertEqual(
            first_terminal.state.bus.address,
            ExactWord(14, 0x0302),
        )
        state = _complete(first_terminal.state, 0).state
        self.assertEqual(state.architecture.cntr, ExactWord(14, 1))
        self.assertEqual(len(state.architecture.loop_stack), 1)

        final_terminal = _issue(state)
        self.assertEqual(
            final_terminal.state.bus.address,
            ExactWord(14, 0x0303),
        )
        retired = _complete(final_terminal.state, 0)
        self.assertIs(retired.state.architecture.cntr, UNKNOWN)
        self.assertEqual(retired.state.architecture.count_stack, ())
        self.assertEqual(retired.state.architecture.pc_stack, ())
        self.assertEqual(retired.state.architecture.loop_stack, ())

    def test_taken_transfer_suppresses_loop_and_false_transfer_loops(self) -> None:
        writable = register_code_by_name(writable=True)

        def terminal_state() -> LinearCoreState:
            state = _setup(
                LinearCoreState.reset(),
                _type7(writable["ASTAT"], 0),
                pc=0x0400,
            )
            for opcode in (
                _type11(end_address=0x0402, termination=0xF),
                _type10(call=False, address=0x2345, condition=0xF),
            ):
                state = _complete(_issue(state).state, opcode).state
            return state

        state = terminal_state()
        taken = _issue(state)
        self.assertEqual(taken.state.bus.address, ExactWord(14, 0x2345))
        retired = _complete(taken.state, 0)
        self.assertEqual(len(retired.state.architecture.loop_stack), 1)
        self.assertEqual(len(retired.state.architecture.pc_stack), 1)

        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0480,
        )
        for opcode in (
            _type11(end_address=0x0482, termination=0xF),
            _type10(call=False, address=0x2345, condition=0),
        ):
            state = _complete(_issue(state).state, opcode).state
        false_transfer = _issue(state)
        self.assertEqual(
            false_transfer.state.bus.address,
            ExactWord(14, 0x0482),
        )

    def test_type22_true_retires_with_sequential_fetch_and_trap_event(self) -> None:
        state = _setup(
            LinearCoreState.reset(),
            _type22(0xF),
            pc=0x0600,
        )
        issued = _issue(state)
        self.assertTrue(issued.supported_instruction)
        self.assertEqual(issued.state.bus.address, ExactWord(14, 0x0601))
        retired = _complete(issued.state, 0)
        self.assertTrue(retired.retire_event)
        self.assertTrue(retired.trap_event)
        self.assertEqual(retired.state.architecture.pc, ExactWord(14, 0x0601))

    def test_type22_false_and_unknown_condition_paths(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0680,
        )
        state = _complete(_issue(state).state, _type22(0)).state
        issued = _issue(state)
        self.assertEqual(issued.state.bus.address, ExactWord(14, 0x0682))
        retired = _complete(issued.state, 0)
        self.assertFalse(retired.trap_event)

        unknown = _setup(LinearCoreState.reset(), _type22(0xE))
        rejected = _issue(unknown)
        self.assertTrue(rejected.supported_instruction)
        self.assertTrue(rejected.internal_conflict)
        self.assertFalse(rejected.instruction_issue)

    def test_taken_type22_suppresses_automatic_loop_flow(self) -> None:
        state = _setup(
            LinearCoreState.reset(),
            _type11(end_address=0x0701, termination=0xF),
            pc=0x0700,
        )
        state = _complete(_issue(state).state, _type22(0xF)).state
        terminal = _issue(state)
        self.assertEqual(terminal.state.bus.address, ExactWord(14, 0x0702))
        retired = _complete(terminal.state, 0)
        self.assertTrue(retired.trap_event)
        self.assertEqual(len(retired.state.architecture.loop_stack), 1)
        self.assertEqual(len(retired.state.architecture.pc_stack), 1)

        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0780,
        )
        for opcode in (
            _type11(end_address=0x0782, termination=0xF),
            _type22(0),
        ):
            state = _complete(_issue(state).state, opcode).state
        false_terminal = _issue(state)
        self.assertEqual(
            false_terminal.state.bus.address,
            ExactWord(14, 0x0782),
        )
        retired = _complete(false_terminal.state, _type22(0xF))
        self.assertFalse(retired.trap_event)
        self.assertEqual(len(retired.state.architecture.loop_stack), 1)

    def test_type11_and_automatic_manual_oq018_conflicts_fail_closed(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0500,
        )
        state = _complete(
            _issue(state).state,
            _type11(end_address=0x0504, termination=0xF),
        ).state
        state = _complete(
            _issue(state).state,
            _type11(end_address=0x0504, termination=0),
        ).state
        same_end = _issue(state)
        self.assertTrue(same_end.internal_conflict)
        self.assertFalse(same_end.instruction_issue)

        terminal = _setup(
            LinearCoreState.reset(),
            _type7(writable["CNTR"], 2),
            pc=0x0580,
        )
        for opcode in (
            _type11(end_address=0x0582, termination=0xE),
            _type7(writable["CNTR"], 9),
        ):
            terminal = _complete(_issue(terminal).state, opcode).state
        counter_collision = _issue(terminal)
        self.assertTrue(counter_collision.internal_conflict)
        self.assertFalse(counter_collision.instruction_issue)
        self.assertEqual(
            counter_collision.state.architecture.cntr,
            ExactWord(14, 2),
        )

    def test_fetched_do_supplies_valid_manual_loop_pop_context(self) -> None:
        state = _setup(
            LinearCoreState.reset(),
            _type11(end_address=0x0608, termination=0xF),
            pc=0x0600,
        )
        state = _complete(_issue(state).state, _type26(0x08)).state
        self.assertEqual(len(state.architecture.loop_stack), 1)
        popped = _complete(_issue(state).state, _type26(0x10))
        self.assertEqual(popped.state.architecture.loop_stack, ())
        self.assertEqual(len(popped.state.architecture.pc_stack), 1)
        cleared = _complete(_issue(popped.state).state, 0)
        self.assertEqual(cleared.state.architecture.pc_stack, ())
        self.assertEqual(cleared.state.architecture.sstat.value & 0x41, 0x41)

    def test_type20_rts_fetches_and_consumes_type10_return(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0100,
        )
        state = _complete(
            _issue(state).state,
            _type10(call=True, address=0x2345, condition=0xF),
        ).state
        state = _complete(
            _issue(state).state,
            _type20(interrupt_return=False, condition=0xF),
        ).state
        returned = _issue(state)
        self.assertEqual(returned.state.bus.address, ExactWord(14, 0x0102))
        retired = _complete(returned.state, 0)
        self.assertEqual(retired.state.architecture.pc, ExactWord(14, 0x0102))
        self.assertEqual(retired.state.architecture.pc_stack, ())
        self.assertEqual(retired.state.architecture.sstat.value & 0x01, 1)

    def test_type20_rti_restores_status_at_fetch_retirement(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0xA5),
            pc=0x0200,
        )
        for opcode in (
            _type7(writable["MSTAT"], 0xB),
            _type7(writable["IMASK"], 0xC),
            _type26(0x02),
            _type7(writable["ASTAT"], 0x00),
            _type7(writable["MSTAT"], 0x0),
            _type7(writable["IMASK"], 0x0),
            _type10(call=True, address=0x3000, condition=0xF),
            _type20(interrupt_return=True, condition=0xF),
        ):
            state = _complete(_issue(state).state, opcode).state

        returned = _issue(state)
        self.assertEqual(returned.state.bus.address, ExactWord(14, 0x0208))
        retired = _complete(returned.state, 0)
        architecture = retired.state.architecture
        self.assertEqual(architecture.pc, ExactWord(14, 0x0208))
        self.assertEqual(architecture.astat, ExactWord(8, 0xA5))
        self.assertEqual(architecture.mstat, ExactWord(4, 0xB))
        self.assertEqual(architecture.imask, ExactWord(4, 0xC))
        self.assertEqual(architecture.pc_stack, ())
        self.assertEqual(architecture.status_stack, ())
        self.assertEqual(architecture.sstat.value & 0x11, 0x11)

    def test_type20_not_ce_does_not_change_counter_state(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["CNTR"], 7),
            pc=0x0280,
        )
        state = _complete(
            _issue(state).state,
            _type10(call=True, address=0x3200, condition=0xF),
        ).state
        state = _complete(
            _issue(state).state,
            _type20(interrupt_return=False, condition=0xE),
        ).state
        returned = _issue(state)
        self.assertEqual(returned.state.bus.address, ExactWord(14, 0x0282))
        retired = _complete(returned.state, 0)
        self.assertEqual(retired.state.architecture.cntr, ExactWord(14, 7))
        self.assertEqual(retired.state.architecture.count_stack, ())

    def test_type20_false_and_missing_context_paths_fail_closed(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0300,
        )
        state = _complete(
            _issue(state).state,
            _type20(interrupt_return=True, condition=0x0),
        ).state
        false_return = _issue(state)
        self.assertEqual(false_return.state.bus.address, ExactWord(14, 0x0302))
        state = _complete(
            false_return.state,
            _type20(interrupt_return=False, condition=0xF),
        ).state
        missing = _issue(state)
        self.assertTrue(missing.supported_instruction)
        self.assertTrue(missing.internal_conflict)
        self.assertFalse(missing.instruction_issue)
        self.assertFalse(missing.state.pending)
        self.assertEqual(missing.state.architecture.pc, ExactWord(14, 0x0302))

        rti_state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0380,
        )
        rti_state = _complete(
            _issue(rti_state).state,
            _type10(call=True, address=0x3500, condition=0xF),
        ).state
        rti_state = _complete(
            _issue(rti_state).state,
            _type20(interrupt_return=True, condition=0xF),
        ).state
        missing_status = _issue(rti_state)
        self.assertTrue(missing_status.internal_conflict)
        self.assertFalse(missing_status.instruction_issue)
        self.assertEqual(
            missing_status.state.architecture.pc_stack,
            (ExactWord(14, 0x0382),),
        )

    def test_type19_taken_jump_reads_dag2_target_without_modifying_it(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0400,
        )
        state = _complete(
            _issue(state).state,
            _type7(writable["I4"], 0x2345),
        ).state
        state = _complete(
            _issue(state).state,
            _type19(call=False, i_local=0, condition=0xF),
        ).state

        jumped = _issue(state)
        self.assertEqual(jumped.state.bus.address, ExactWord(14, 0x2345))
        retired = _complete(jumped.state, 0)
        self.assertEqual(retired.state.architecture.pc, ExactWord(14, 0x2345))
        self.assertEqual(
            retired.state.architecture.dag.i[4],
            ExactWord(14, 0x2345),
        )

    def test_type19_false_flow_does_not_require_known_dag_target(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0480,
        )
        state = _complete(
            _issue(state).state,
            _type19(call=False, i_local=3, condition=0x0),
        ).state
        issued = _issue(state)
        self.assertFalse(issued.internal_conflict)
        self.assertEqual(issued.state.bus.address, ExactWord(14, 0x0482))
        retired = _complete(issued.state, 0)
        self.assertEqual(retired.state.architecture.pc, ExactWord(14, 0x0482))

    def test_type19_call_context_is_consumed_by_fetched_rts(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["ASTAT"], 0),
            pc=0x0500,
        )
        for opcode in (
            _type7(writable["I5"], 0x2A00),
            _type19(call=True, i_local=1, condition=0xF),
            _type20(interrupt_return=False, condition=0xF),
        ):
            state = _complete(_issue(state).state, opcode).state

        returned = _issue(state)
        self.assertEqual(returned.state.bus.address, ExactWord(14, 0x0503))
        retired = _complete(returned.state, 0)
        self.assertEqual(retired.state.architecture.pc, ExactWord(14, 0x0503))
        self.assertEqual(retired.state.architecture.pc_stack, ())

    def test_type19_not_ce_and_invalid_target_paths(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["CNTR"], 7),
            pc=0x0580,
        )
        for opcode in (
            _type7(writable["I6"], 0x2B00),
            _type19(call=False, i_local=2, condition=0xE),
        ):
            state = _complete(_issue(state).state, opcode).state
        issued = _issue(state)
        self.assertEqual(issued.state.bus.address, ExactWord(14, 0x2B00))
        retired = _complete(issued.state, 0)
        self.assertEqual(retired.state.architecture.cntr, ExactWord(14, 6))

        invalid = _setup(
            LinearCoreState.reset(),
            _type19(call=False, i_local=0, condition=0xF),
        )
        rejected = _issue(invalid)
        self.assertTrue(rejected.supported_instruction)
        self.assertTrue(rejected.internal_conflict)
        self.assertFalse(rejected.instruction_issue)
        self.assertFalse(rejected.state.pending)

    def test_type9_alu_retires_with_next_fetch_and_false_form_preserves(self) -> None:
        state = _setup(LinearCoreState.reset(), _type7(0x30, 0))
        state = _complete(
            _issue(state).state,
            _type6(DREG.AX0, 3),
        ).state
        state = _complete(
            _issue(state).state,
            _type6(DREG.AY0, 4),
        ).state
        state = _complete(
            _issue(state).state,
            _type9(z=0, amf=0x13, yop=0, xop=0, condition=0xF),
        ).state
        added = _complete(_issue(state).state, _type6(DREG.AR, 0x1234))
        self.assertEqual(
            read_dreg(added.state.architecture.primary, DREG.AR),
            ExactWord(16, 7),
        )
        self.assertEqual(added.state.architecture.astat, ExactWord(8, 0))

        loaded = _complete(
            _issue(added.state).state,
            _type9(z=0, amf=0x13, yop=0, xop=0, condition=0),
        )
        self.assertEqual(
            read_dreg(loaded.state.architecture.primary, DREG.AR),
            ExactWord(16, 0x1234),
        )
        preserved = _complete(_issue(loaded.state).state, 0)
        self.assertEqual(
            read_dreg(preserved.state.architecture.primary, DREG.AR),
            ExactWord(16, 0x1234),
        )
        self.assertEqual(preserved.state.architecture.astat, ExactWord(8, 0))

    def test_type8_compute_and_move_sample_cycle_start_state(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["MSTAT"], 0),
        )
        for opcode in (
            _type6(DREG.AX0, 3),
            _type6(DREG.AY0, 4),
            _type6(DREG.AR, 0x1234),
            _type7(writable["ASTAT"], 0),
            _type8(
                z=0,
                amf=0x13,
                yop=0,
                xop=0,
                destination=DREG.AX0,
                source=DREG.AR,
            ),
        ):
            state = _complete(_issue(state).state, opcode).state

        retired = _complete(_issue(state).state, 0)
        self.assertEqual(
            read_dreg(retired.state.architecture.primary, DREG.AR),
            ExactWord(16, 7),
        )
        self.assertEqual(
            read_dreg(retired.state.architecture.primary, DREG.AX0),
            ExactWord(16, 0x1234),
        )
        self.assertEqual(retired.state.architecture.astat, ExactWord(8, 0))

    def test_type15_and_type16_retire_shifter_actions_atomically(self) -> None:
        state = _setup(LinearCoreState.reset(), _type7(0x31, 0))
        for opcode in (
            _type6(DREG.SI, 0xB6A3),
            _type6(DREG.SE, 0),
            _type15(sf=0, xop=0, exponent=-5),
        ):
            state = _complete(_issue(state).state, opcode).state

        shifted = _complete(_issue(state).state, _type7(0x30, 0))
        self.assertEqual(
            read_dreg(shifted.state.architecture.primary, DREG.SR0),
            ExactWord(16, 0x1800),
        )
        self.assertEqual(
            read_dreg(shifted.state.architecture.primary, DREG.SR1),
            ExactWord(16, 0x05B5),
        )

        state = _complete(
            _issue(shifted.state).state,
            _type6(DREG.SI, 0x1234),
        ).state
        state = _complete(
            _issue(state).state,
            _type16(sf=0, xop=0, condition=0),
        ).state
        false_shift = _complete(
            _issue(state).state,
            _type16(sf=0, xop=0, condition=0xF),
        )
        self.assertEqual(
            read_dreg(false_shift.state.architecture.primary, DREG.SR0),
            ExactWord(16, 0x1800),
        )
        self.assertEqual(
            read_dreg(false_shift.state.architecture.primary, DREG.SR1),
            ExactWord(16, 0x05B5),
        )

        true_shift = _complete(_issue(false_shift.state).state, 0)
        self.assertEqual(
            read_dreg(true_shift.state.architecture.primary, DREG.SR0),
            ExactWord(16, 0x0000),
        )
        self.assertEqual(
            read_dreg(true_shift.state.architecture.primary, DREG.SR1),
            ExactWord(16, 0x1234),
        )
        self.assertEqual(true_shift.state.architecture.astat, ExactWord(8, 0))

    def test_type14_parallel_actions_use_cycle_start_values(self) -> None:
        state = _setup(LinearCoreState.reset(), _type7(0x30, 0))
        for opcode in (
            _type6(DREG.SI, 0x1234),
            _type6(DREG.SE, 0),
            _type6(DREG.MR0, 0xABCD),
            _type14(
                sf=0,
                xop=0,
                destination=DREG.SI,
                source=DREG.MR0,
            ),
        ):
            state = _complete(_issue(state).state, opcode).state

        retired = _complete(_issue(state).state, 0)
        bank = retired.state.architecture.primary
        self.assertEqual(read_dreg(bank, DREG.SI), ExactWord(16, 0xABCD))
        self.assertEqual(read_dreg(bank, DREG.SR0), ExactWord(16, 0x0000))
        self.assertEqual(read_dreg(bank, DREG.SR1), ExactWord(16, 0x1234))
        self.assertEqual(retired.state.architecture.astat, ExactWord(8, 0))

    def test_type25_saturates_selected_mr_and_preserves_astat(self) -> None:
        for mstat, mr2, expected in (
            (0, 0x00, (0xFFFF, 0x7FFF, 0x00)),
            (1, 0xFF, (0x0000, 0x8000, 0xFF)),
        ):
            state = _setup(LinearCoreState.reset(), _type7(0x30, 0x40))
            for opcode in (
                _type7(0x31, mstat),
                _type6(DREG.MR0, 0x1357),
                _type6(DREG.MR1, 0x2468),
                _type6(DREG.MR2, mr2),
                _type25(),
            ):
                state = _complete(_issue(state).state, opcode).state

            retired = _complete(_issue(state).state, 0)
            architecture = retired.state.architecture
            selected = (
                architecture.alternate if mstat else architecture.primary
            )
            self.assertEqual(
                tuple(segment.value for segment in selected.mr),
                expected,
            )
            self.assertEqual(architecture.astat, ExactWord(8, 0x40))

    def test_type25_mv_false_retires_without_mr_write(self) -> None:
        state = _setup(LinearCoreState.reset(), _type7(0x30, 0))
        for opcode in (
            _type7(0x31, 0),
            _type6(DREG.MR0, 0x1357),
            _type6(DREG.MR1, 0x2468),
            _type6(DREG.MR2, 0xA5),
            _type25(),
        ):
            state = _complete(_issue(state).state, opcode).state

        retired = _complete(_issue(state).state, 0)
        self.assertTrue(retired.retire_event)
        self.assertEqual(
            tuple(
                segment.value
                for segment in retired.state.architecture.primary.mr
            ),
            (0x1357, 0x2468, 0xA5),
        )
        self.assertEqual(retired.state.architecture.astat, ExactWord(8, 0))

    def test_type23_all_sources_banks_and_old_aq_paths(self) -> None:
        sources = (
            (DREG.AX0, 0x0002),
            (DREG.AX1, 0x8002),
            (DREG.AR, 0x7FFF),
            (DREG.MR0, 0x8000),
            (DREG.MR1, 0x0001),
            (DREG.MR2, 0xFFFE),
            (DREG.SR0, 0xFFFF),
            (DREG.SR1, 0x0000),
        )
        writable = register_code_by_name(writable=True)
        for mstat, old_aq, af_before in ((0, 0, 0x0003), (1, 1, 0xFFFF)):
            for xop, (source, divisor) in enumerate(sources):
                state = _setup(
                    LinearCoreState.reset(),
                    _type7(writable["MSTAT"], mstat),
                )
                for opcode in (
                    _type6(source, divisor),
                    _type6(DREG.AY0, 0x8001),
                    _type6(DREG.AY1, af_before),
                    _type9(z=1, amf=0x10, yop=1, xop=0, condition=0xF),
                    _type7(writable["ASTAT"], 0xD5 | (old_aq << 5)),
                    _type23(xop),
                ):
                    state = _complete(_issue(state).state, opcode).state

                retired = _complete(_issue(state).state, 0)
                selected = (
                    retired.state.architecture.alternate
                    if mstat else retired.state.architecture.primary
                )
                raw = (
                    af_before + divisor if old_aq else af_before - divisor
                ) & 0xFFFF
                new_aq = ((divisor ^ raw) >> 15) & 1
                self.assertEqual(
                    selected.af,
                    ExactWord(16, ((raw << 1) & 0xFFFF) | 1),
                )
                self.assertEqual(
                    selected.ay[0],
                    ExactWord(16, 0x0002 | (new_aq ^ 1)),
                )
                self.assertEqual(
                    retired.state.architecture.astat,
                    ExactWord(8, (0xD5 & ~0x20) | (new_aq << 5)),
                )

    def test_type23_following_iteration_reads_retired_divide_state(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["MSTAT"], 0),
        )
        for opcode in (
            _type6(DREG.AX0, 0x0002),
            _type6(DREG.AY0, 0x8001),
            _type6(DREG.AY1, 0x0003),
            _type9(z=1, amf=0x10, yop=1, xop=0, condition=0xF),
            _type7(writable["ASTAT"], 0x00),
            _type23(0),
            _type23(0),
        ):
            state = _complete(_issue(state).state, opcode).state

        retired = _complete(_issue(state).state, 0)
        self.assertEqual(retired.state.architecture.primary.af, ExactWord(16, 0x0002))
        self.assertEqual(
            retired.state.architecture.primary.ay[0], ExactWord(16, 0x0007)
        )
        self.assertEqual(retired.state.architecture.astat, ExactWord(8, 0x00))

    def test_type24_all_sources_upper_forms_and_banks(self) -> None:
        sources = (
            (DREG.AX0, 0x0002),
            (DREG.AX1, 0x8002),
            (DREG.AR, 0x7FFF),
            (DREG.MR0, 0x8000),
            (DREG.MR1, 0x0001),
            (DREG.MR2, 0xFFFE),
            (DREG.SR0, 0xFFFF),
            (DREG.SR1, 0x0000),
        )
        writable = register_code_by_name(writable=True)
        for mstat in (0, 1):
            for yop, upper in ((1, 0x4001), (2, 0xC001)):
                for xop, (source, divisor) in enumerate(sources):
                    state = _setup(
                        LinearCoreState.reset(),
                        _type7(writable["MSTAT"], mstat),
                    )
                    for opcode in (
                        _type6(source, divisor),
                        _type6(DREG.AY0, 0x8001),
                        _type6(DREG.AY1, 0xC001),
                        _type9(z=1, amf=0x10, yop=1, xop=0, condition=0xF),
                        _type6(DREG.AY1, 0x4001),
                        _type7(writable["ASTAT"], 0xD5),
                        _type24(yop, xop),
                    ):
                        state = _complete(_issue(state).state, opcode).state

                    retired = _complete(_issue(state).state, 0)
                    selected = (
                        retired.state.architecture.alternate
                        if mstat else retired.state.architecture.primary
                    )
                    quotient_sign = ((divisor ^ upper) >> 15) & 1
                    self.assertEqual(
                        selected.af,
                        ExactWord(16, ((upper << 1) & 0xFFFF) | 1),
                    )
                    self.assertEqual(
                        selected.ay[0],
                        ExactWord(16, 0x0002 | quotient_sign),
                    )
                    self.assertEqual(
                        retired.state.architecture.astat,
                        ExactWord(8, (0xD5 & ~0x20) | (quotient_sign << 5)),
                    )

    def test_fetched_divs_then_divq_reads_retired_state(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _setup(
            LinearCoreState.reset(),
            _type7(writable["MSTAT"], 0),
        )
        for opcode in (
            _type6(DREG.AX0, 0x0002),
            _type6(DREG.AY0, 0x8001),
            _type6(DREG.AY1, 0xC001),
            _type7(writable["ASTAT"], 0x15),
            _type24(1, 0),
            _type23(0),
        ):
            state = _complete(_issue(state).state, opcode).state

        retired = _complete(_issue(state).state, 0)
        # DIVS produces AF=0x8003, AY0=0x0003, AQ=1. DIVQ then adds AX0,
        # shifts the new remainder with old AY0[15]=0, and appends quotient 0.
        self.assertEqual(retired.state.architecture.primary.af, ExactWord(16, 0x000A))
        self.assertEqual(
            retired.state.architecture.primary.ay[0], ExactWord(16, 0x0006)
        )
        self.assertEqual(retired.state.architecture.astat, ExactWord(8, 0x35))

    def test_type7_cntr_pushes_and_saturates_count_stack(self) -> None:
        state = _setup(LinearCoreState.reset(), _type7(0x35, 0))
        for value in range(1, 7):
            done = _complete(_issue(state).state, _type7(0x35, value))
            state = done.state
        self.assertEqual(state.architecture.cntr, ExactWord(14, 5))
        self.assertEqual(len(state.architecture.count_stack), 4)
        self.assertEqual(state.architecture.sstat.value & 0x0C, 0x08)

    def test_unsupported_and_reserved_words_never_start_fetch(self) -> None:
        for opcode, reserved in (
            (0x000001, False),
            (0x050001, False),
            (0x071001, False),
            (_type10(call=True, address=0x1234, condition=0xE), False),
            (_type19(call=True, i_local=0, condition=0xE), False),
            (_type19(call=False, i_local=0, condition=0xF) | 0x20, False),
            (_type24(0, 0), True),
            (_type24(3, 7), True),
            (
                _type8(
                    z=1,
                    amf=0,
                    yop=0,
                    xop=0,
                    destination=DREG.AX0,
                    source=DREG.AX1,
                ),
                True,
            ),
            (
                _type8(
                    z=0,
                    amf=0x13,
                    yop=0,
                    xop=0,
                    destination=DREG.AR,
                    source=DREG.AX1,
                ),
                True,
            ),
            (
                _type8(
                    z=0,
                    amf=0x04,
                    yop=0,
                    xop=0,
                    destination=DREG.MR1,
                    source=DREG.AX1,
                ),
                True,
            ),
            (_type7(0x32, 1), True),
            (_type17(0x32, 0x00), True),
            (
                _type14(
                    sf=0,
                    xop=0,
                    destination=DREG.AX0,
                    source=DREG.AX1,
                )
                | 0x008000,
                True,
            ),
            (
                _type14(
                    sf=0,
                    xop=1,
                    destination=DREG.AX0,
                    source=DREG.AX1,
                ),
                True,
            ),
            (
                _type14(
                    sf=0,
                    xop=0,
                    destination=DREG.SR0,
                    source=DREG.AX1,
                ),
                True,
            ),
            (_type15(sf=8, xop=0, exponent=0), True),
            (_type16(sf=0, xop=1, condition=0xF), True),
        ):
            state = _setup(LinearCoreState.reset(), opcode)
            result = _issue(state)
            self.assertEqual(result.reserved_subencoding, reserved)
            self.assertEqual(result.unsupported_instruction, not reserved)
            self.assertFalse(result.instruction_issue)
            self.assertFalse(result.state.pending)
            self.assertEqual(result.state.architecture.pc, ExactWord(14, 4))

    def test_phase_hold_and_relinquishment_preserve_pending_transaction(self) -> None:
        issued = _issue(_setup(LinearCoreState.reset(), 0))
        held = apply_linear_core_cycle(
            issued.state,
            phase=LogicalPhase.STATE_4,
            phase_advance=False,
        )
        self.assertTrue(held.state.pending)
        self.assertFalse(held.retire_event)
        relinquished = apply_linear_core_cycle(
            held.state,
            phase=LogicalPhase.STATE_5,
            bus_relinquished=True,
        )
        self.assertFalse(relinquished.bus.address_output_enable)
        self.assertFalse(relinquished.bus.control_output_enable)
        self.assertEqual(relinquished.state, held.state)

    def test_issue_inhibit_stops_only_new_fetch(self) -> None:
        ready = _setup(LinearCoreState.reset(), 0)
        inhibited = apply_linear_core_cycle(
            ready,
            phase=LogicalPhase.STATE_8,
            instruction_issue_inhibit=True,
        )
        self.assertFalse(inhibited.issue_boundary)
        self.assertFalse(inhibited.instruction_issue)
        self.assertEqual(inhibited.state, ready)

        issued = _issue(inhibited.state)
        self.assertTrue(issued.instruction_issue)
        active = apply_linear_core_cycle(
            issued.state,
            phase=LogicalPhase.STATE_4,
            instruction_issue_inhibit=True,
        )
        self.assertTrue(active.state.pending)
        self.assertTrue(active.bus.address_output_enable)
        self.assertTrue(active.bus.control_output_enable)

    def test_invalid_fetched_word_does_not_erase_retiring_effects(self) -> None:
        state = _setup(LinearCoreState.reset(), _type6(DREG.SE, 0x0180))
        done = _complete(_issue(state).state, None)
        self.assertEqual(
            read_dreg(done.state.architecture.primary, DREG.SE),
            ExactWord(16, 0xFF80),
        )
        self.assertEqual(done.state.architecture.pc, ExactWord(14, 5))
        self.assertFalse(done.state.instruction_valid)

    def test_wrapped_fetch_address_becomes_wrapped_pc(self) -> None:
        state = _setup(LinearCoreState.reset(), 0, pc=0x3FFF)
        issued = _issue(state)
        self.assertEqual(issued.state.bus.address, ExactWord(14, 0))
        done = _complete(issued.state, 0)
        self.assertEqual(done.state.architecture.pc, ExactWord(14, 0))

    def test_setup_contract_fails_closed_off_boundary_or_when_busy(self) -> None:
        setup = (ExactWord(14, 4), ExactWord(24, 0))
        off_phase = apply_linear_core_cycle(
            LinearCoreState.reset(),
            phase=LogicalPhase.STATE_3,
            instruction_setup=setup,
        )
        self.assertTrue(off_phase.phase_conflict)
        self.assertFalse(off_phase.instruction_setup_accepted)
        state = _setup(LinearCoreState.reset(), 0)
        occupied = apply_linear_core_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            instruction_setup=setup,
        )
        self.assertTrue(occupied.integration_conflict)
        self.assertFalse(occupied.instruction_setup_accepted)


if __name__ == "__main__":
    unittest.main()
