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
)


ROOT = Path(__file__).resolve().parents[1]


def _type6(destination: DREG, data: int) -> int:
    return 0x400000 | ((data & 0xFFFF) << 4) | int(destination)


def _type7(code: int, data: int) -> int:
    return 0x300000 | ((code >> 4) << 18) | ((data & 0x3FFF) << 4) | (code & 0xF)


def _type18(payload: int) -> int:
    return 0x0C0000 | ((payload & 0xFF) << 4)


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
            (_type7(0x32, 1), True),
            (_type17(0x32, 0x00), True),
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
