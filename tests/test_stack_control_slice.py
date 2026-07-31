from __future__ import annotations

import json
from pathlib import Path
import random
import unittest

from sim.reference_models.adsp2100_model import (
    ASTATState,
    CounterState,
    ExactWord,
    SequencerStacksState,
    StackControlSliceInputs,
    StackControlSliceState,
    StatusRegisters,
    StatusStackEntry,
    StatusStackState,
    apply_stack_control_slice_cycle,
)


def _known_status(astat: int, mstat: int, imask: int) -> StatusRegisters:
    return StatusRegisters(
        astat=ASTATState.from_word(ExactWord(8, astat)),
        mstat=ExactWord(4, mstat),
        imask=ExactWord(4, imask),
    )


def _status_entry(astat: int, mstat: int, imask: int) -> StatusStackEntry:
    return StatusStackEntry.from_word(
        ExactWord(16, (astat << 8) | (mstat << 4) | imask)
    )


class StackControlSliceModelTests(unittest.TestCase):
    def test_machine_readable_boundary_records_scope_and_limits(self) -> None:
        database = json.loads(
            Path(
                "docs/generated/adsp2100_stack_control_slice.yaml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(database["device"], "ADSP-2100")
        self.assertEqual(
            database["scope"],
            "BOUNDED_TYPE_26_STATEFUL_STACK_CONTROL_INTEGRATION",
        )
        self.assertEqual(
            database["cycle_boundary"]["source_reads"],
            "CYCLE_START",
        )
        self.assertEqual(
            database["cycle_boundary"]["state_commits"],
            "CYCLE_END",
        )
        self.assertEqual(
            database["fail_closed_boundaries"]["EMPTY_POP"],
            "OQ-013_EVENT_FLAG_AND_STATE_PRESERVATION",
        )
        self.assertIn(
            "INTERRUPT_ENTRY_OR_RTI_DECODE",
            database["not_implemented"],
        )

    def test_combined_pop_uses_all_cycle_start_tops(self) -> None:
        saved = _status_entry(0xA5, 0x6, 0x9)
        state = StackControlSliceState(
            status=_known_status(0x3C, 0x1, 0x2),
            status_stack=StatusStackState((saved,)),
            sequencer_stacks=SequencerStacksState(
                pc_entries=(0x1234,),
                count_entries=(0x2345,),
                loop_entries=(0x34567,),
            ),
            counter=CounterState(0x0777),
        )
        result = apply_stack_control_slice_cycle(
            state,
            StackControlSliceInputs(execute=True, opcode=0x04001F),
        )
        self.assertTrue(result.boundary_valid)
        self.assertEqual(result.state.status, _known_status(0xA5, 0x6, 0x9))
        self.assertEqual(result.state.counter, CounterState(0x2345))
        self.assertEqual(result.state.status_stack.entries, ())
        self.assertEqual(result.state.sequencer_stacks.pc_entries, ())
        self.assertEqual(result.state.sequencer_stacks.count_entries, ())
        self.assertEqual(result.state.sequencer_stacks.loop_entries, ())
        self.assertEqual(result.state.sstat, 0x55)

    def test_push_sts_captures_preinstruction_status(self) -> None:
        status = _known_status(0x81, 0xA, 0x5)
        result = apply_stack_control_slice_cycle(
            StackControlSliceState(status=status),
            StackControlSliceInputs(execute=True, opcode=0x040002),
        )
        self.assertTrue(result.status_stack.push_accepted)
        self.assertEqual(
            result.state.status_stack.entries,
            (_status_entry(0x81, 0xA, 0x5),),
        )
        self.assertEqual(result.state.status, status)

    def test_both_no_effect_aliases_preserve_all_state(self) -> None:
        state = StackControlSliceState(
            status=_known_status(0x55, 0x3, 0xC),
            sequencer_stacks=SequencerStacksState(pc_entries=(7,)),
            counter=CounterState(9),
        )
        for opcode in (0x040000, 0x040001):
            result = apply_stack_control_slice_cycle(
                state,
                StackControlSliceInputs(execute=True, opcode=opcode),
            )
            self.assertTrue(result.boundary_valid)
            self.assertEqual(result.state, state)

    def test_empty_pops_are_flagged_and_fail_closed(self) -> None:
        state = StackControlSliceState(
            status=_known_status(0x12, 0x3, 0x4),
            counter=CounterState(8),
        )
        result = apply_stack_control_slice_cycle(
            state,
            StackControlSliceInputs(execute=True, opcode=0x04001F),
        )
        self.assertEqual(result.state, state)
        self.assertTrue(result.status_stack.empty_pop)
        self.assertTrue(result.counter.empty_manual_pop)
        self.assertTrue(result.sequencer_stacks.pc_empty_pop)
        self.assertTrue(result.sequencer_stacks.count_empty_pop)
        self.assertTrue(result.sequencer_stacks.loop_empty_pop)

    def test_external_setup_and_type_26_collision_is_atomic(self) -> None:
        state = StackControlSliceState(
            status=_known_status(0x33, 0x4, 0x5),
            sequencer_stacks=SequencerStacksState(pc_entries=(4,)),
        )
        result = apply_stack_control_slice_cycle(
            state,
            StackControlSliceInputs(
                execute=True,
                opcode=0x040010,
                pc_push=True,
                pc_push_value=9,
            ),
        )
        self.assertTrue(result.integration_conflict)
        self.assertFalse(result.boundary_valid)
        self.assertEqual(result.state, state)

    def test_non_type_26_execute_is_invalid_and_action_free(self) -> None:
        state = StackControlSliceState(
            status=_known_status(0x77, 0x8, 0x9),
            counter=CounterState(3),
        )
        for opcode in (0, 0x040020, 0xFFFFFF):
            result = apply_stack_control_slice_cycle(
                state,
                StackControlSliceInputs(execute=True, opcode=opcode),
            )
            self.assertTrue(result.invalid_opcode)
            self.assertFalse(result.boundary_valid)
            self.assertEqual(result.state, state)

    def test_setup_traffic_populates_every_state_class(self) -> None:
        state = StackControlSliceState()
        state = apply_stack_control_slice_cycle(
            state,
            StackControlSliceInputs(
                astat_write=ExactWord(8, 0x11),
                mstat_write=ExactWord(4, 0x2),
                imask_write=ExactWord(4, 0x3),
                counter_load=5,
                pc_push=True,
                pc_push_value=0x0100,
                loop_push=True,
                loop_push_value=0x20100,
            ),
        ).state
        state = apply_stack_control_slice_cycle(
            state,
            StackControlSliceInputs(counter_load=7),
        ).state
        state = apply_stack_control_slice_cycle(
            state,
            StackControlSliceInputs(execute=True, opcode=0x040002),
        ).state
        self.assertEqual(state.status, _known_status(0x11, 0x2, 0x3))
        self.assertEqual(state.counter, CounterState(7))
        self.assertEqual(state.sequencer_stacks.pc_entries, (0x0100,))
        self.assertEqual(state.sequencer_stacks.count_entries, (5,))
        self.assertEqual(state.sequencer_stacks.loop_entries, (0x20100,))
        self.assertEqual(state.status_stack.depth, 1)

    def test_deterministic_random_state_invariants(self) -> None:
        rng = random.Random(0x210026)
        state = StackControlSliceState(status=_known_status(0, 0, 0))
        for index in range(20_000):
            choice = rng.randrange(10)
            if choice < 4:
                inputs = StackControlSliceInputs(
                    execute=True,
                    opcode=0x040000 | rng.randrange(32),
                )
            elif choice == 4:
                inputs = StackControlSliceInputs(
                    counter_load=rng.randrange(1 << 14)
                )
            elif choice == 5:
                inputs = StackControlSliceInputs(
                    pc_push=True,
                    pc_push_value=rng.randrange(1 << 14),
                )
            elif choice == 6:
                inputs = StackControlSliceInputs(
                    loop_push=True,
                    loop_push_value=rng.randrange(1 << 18),
                )
            elif choice == 7:
                inputs = StackControlSliceInputs(
                    astat_write=ExactWord(8, rng.randrange(1 << 8)),
                    mstat_write=ExactWord(4, rng.randrange(1 << 4)),
                    imask_write=ExactWord(4, rng.randrange(1 << 4)),
                )
            elif choice == 8:
                inputs = StackControlSliceInputs(
                    execute=True,
                    opcode=0x04001F,
                    pc_push=True,
                    pc_push_value=rng.randrange(1 << 14),
                )
            else:
                inputs = StackControlSliceInputs(
                    execute=True,
                    opcode=0x040020,
                )
            before = state
            result = apply_stack_control_slice_cycle(state, inputs)
            state = result.state
            self.assertLessEqual(len(state.status_stack.entries), 4)
            self.assertLessEqual(len(state.sequencer_stacks.pc_entries), 16)
            self.assertLessEqual(
                len(state.sequencer_stacks.count_entries),
                4,
            )
            self.assertLessEqual(
                len(state.sequencer_stacks.loop_entries),
                4,
            )
            self.assertFalse(result.internal_conflict)
            if result.integration_conflict or result.invalid_opcode:
                self.assertEqual(state, before)
            if index % 997 == 0:
                state = apply_stack_control_slice_cycle(
                    state,
                    StackControlSliceInputs(reset=True),
                ).state
                state = apply_stack_control_slice_cycle(
                    state,
                    StackControlSliceInputs(
                        astat_write=ExactWord(8, 0),
                        mstat_write=ExactWord(4, 0),
                        imask_write=ExactWord(4, 0),
                    ),
                ).state


if __name__ == "__main__":
    unittest.main()
