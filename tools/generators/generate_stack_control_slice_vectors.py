#!/usr/bin/env python3
"""Generate deterministic Type 26 stateful model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ExactWord,
    StackControlSliceInputs,
    StackControlSliceState,
    StackControlStatusOperation,
    apply_stack_control_slice_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _pack_stimulus(inputs: StackControlSliceInputs) -> int:
    packed = 0
    for value, width in (
        (inputs.reset, 1),
        (inputs.execute, 1),
        (inputs.opcode, 24),
        (inputs.astat_write is not None, 1),
        (
            inputs.astat_write.value
            if inputs.astat_write is not None
            else 0,
            8,
        ),
        (inputs.mstat_write is not None, 1),
        (
            inputs.mstat_write.value
            if inputs.mstat_write is not None
            else 0,
            4,
        ),
        (inputs.imask_write is not None, 1),
        (
            inputs.imask_write.value
            if inputs.imask_write is not None
            else 0,
            4,
        ),
        (inputs.counter_load is not None, 1),
        (
            inputs.counter_load
            if inputs.counter_load is not None
            else 0,
            14,
        ),
        (inputs.pc_push, 1),
        (inputs.pc_push_value, 14),
        (inputs.loop_push, 1),
        (inputs.loop_push_value, 18),
    ):
        packed = _append(packed, value, width)
    return packed


def _pack_events(
    state: StackControlSliceState,
    inputs: StackControlSliceInputs,
) -> int:
    result = apply_stack_control_slice_cycle(state, inputs)
    actions = result.actions
    status_operation = (
        int(actions.status_operation)
        if result.boundary_valid and actions is not None
        else 0
    )
    has_effect = bool(
        result.boundary_valid
        and actions is not None
        and actions.has_effect
    )
    pop_valid = (
        (int(result.status_stack.pop_entry is not None) << 3)
        | (int(result.sequencer_stacks.loop_pop_value is not None) << 2)
        | (int(result.sequencer_stacks.count_pop_value is not None) << 1)
        | int(result.sequencer_stacks.pc_pop_value is not None)
    )
    push_accepted = (
        (int(result.status_stack.push_accepted) << 3)
        | (int(result.sequencer_stacks.loop_push_accepted) << 2)
        | (int(result.sequencer_stacks.count_push_accepted) << 1)
        | int(result.sequencer_stacks.pc_push_accepted)
    )
    overflow_event = (
        (int(result.status_stack.overflow_event) << 3)
        | (int(result.sequencer_stacks.loop_overflow_event) << 2)
        | (int(result.sequencer_stacks.count_overflow_event) << 1)
        | int(result.sequencer_stacks.pc_overflow_event)
    )
    empty_pop = (
        (int(result.status_stack.empty_pop) << 3)
        | (int(result.sequencer_stacks.loop_empty_pop) << 2)
        | (int(result.sequencer_stacks.count_empty_pop) << 1)
        | int(result.sequencer_stacks.pc_empty_pop)
    )
    packed = 0
    for value, width in (
        (result.boundary_valid, 1),
        (result.invalid_opcode, 1),
        (result.integration_conflict, 1),
        (result.internal_conflict, 1),
        (status_operation, 2),
        (
            result.boundary_valid
            and actions is not None
            and actions.count_pop,
            1,
        ),
        (
            result.boundary_valid
            and actions is not None
            and actions.loop_pop,
            1,
        ),
        (
            result.boundary_valid
            and actions is not None
            and actions.pc_pop,
            1,
        ),
        (has_effect, 1),
        (result.counter.restored, 1),
        (result.counter.empty_manual_pop, 1),
        (pop_valid, 4),
        (push_accepted, 4),
        (overflow_event, 4),
        (empty_pop, 4),
    ):
        packed = _append(packed, value, width)
    return packed


def _top(entries: tuple[int, ...]) -> tuple[bool, int]:
    return bool(entries), entries[-1] if entries else 0


def _pack_state(
    state: StackControlSliceState,
    *,
    compare_astat: bool,
) -> int:
    pc_valid, pc_top = _top(state.sequencer_stacks.pc_entries)
    count_valid, count_top = _top(state.sequencer_stacks.count_entries)
    loop_valid, loop_top = _top(state.sequencer_stacks.loop_entries)
    status_valid = bool(state.status_stack.entries)
    status_top = (
        state.status_stack.entries[-1].to_word().value
        if status_valid
        else 0
    )
    cntr_valid = state.counter.value is not None
    astat = (
        state.status.astat.to_word().value
        if compare_astat
        else 0
    )
    assert isinstance(state.status.imask, ExactWord)
    packed = 0
    for value, width in (
        (compare_astat, 1),
        (astat, 8),
        (state.status.mstat.value, 4),
        (state.status.imask.value, 4),
        (state.status.mstat.value, 4),
        (cntr_valid, 1),
        (state.counter.value if cntr_valid else 0, 14),
        (pc_valid, 1),
        (pc_top, 14),
        (count_valid, 1),
        (count_top, 14),
        (loop_valid, 1),
        (loop_top, 18),
        (status_valid, 1),
        (status_top, 16),
        (len(state.sequencer_stacks.pc_entries), 5),
        (len(state.sequencer_stacks.count_entries), 3),
        (len(state.sequencer_stacks.loop_entries), 3),
        (len(state.status_stack.entries), 3),
        (
            (int(state.status_stack.overflow) << 3)
            | (int(state.sequencer_stacks.loop_overflow) << 2)
            | (int(state.sequencer_stacks.count_overflow) << 1)
            | int(state.sequencer_stacks.pc_overflow),
            4,
        ),
        (
            (int(not state.status_stack.entries) << 3)
            | (int(not state.sequencer_stacks.loop_entries) << 2)
            | (int(not state.sequencer_stacks.count_entries) << 1)
            | int(not state.sequencer_stacks.pc_entries),
            4,
        ),
        (state.sstat, 8),
    ):
        packed = _append(packed, value, width)
    return packed


def generate_lines(random_count: int, seed: int) -> list[str]:
    state = StackControlSliceState()
    compare_astat = False
    lines: list[str] = []

    def emit(inputs: StackControlSliceInputs) -> None:
        nonlocal state, compare_astat
        result = apply_stack_control_slice_cycle(state, inputs)
        if inputs.reset:
            next_compare_astat = False
        elif inputs.astat_write is not None and not result.integration_conflict:
            next_compare_astat = True
        else:
            next_compare_astat = compare_astat
        lines.append(
            f"{_pack_stimulus(inputs):024x} "
            f"{_pack_events(state, inputs):07x} "
            f"{_pack_state(result.state, compare_astat=next_compare_astat):033x}"
        )
        state = result.state
        compare_astat = next_compare_astat

    emit(StackControlSliceInputs(reset=True))
    emit(
        StackControlSliceInputs(
            astat_write=ExactWord(8, 0xA5),
            mstat_write=ExactWord(4, 0x6),
            imask_write=ExactWord(4, 0x9),
            counter_load=0x123,
            pc_push=True,
            pc_push_value=0x234,
            loop_push=True,
            loop_push_value=0x34567,
        )
    )
    emit(StackControlSliceInputs(execute=True, opcode=0x040002))
    emit(
        StackControlSliceInputs(
            astat_write=ExactWord(8, 0x3C),
            mstat_write=ExactWord(4, 0x1),
            imask_write=ExactWord(4, 0x2),
            counter_load=0x456,
        )
    )
    emit(StackControlSliceInputs(execute=True, opcode=0x04001F))
    emit(StackControlSliceInputs(execute=True, opcode=0x040000))
    emit(StackControlSliceInputs(execute=True, opcode=0x040001))
    emit(StackControlSliceInputs(execute=True, opcode=0x040020))
    emit(
        StackControlSliceInputs(
            execute=True,
            opcode=0x040010,
            pc_push=True,
            pc_push_value=9,
        )
    )
    emit(StackControlSliceInputs(execute=True, opcode=0x04001F))

    rng = random.Random(seed)
    for index in range(random_count):
        if index and index % 9973 == 0:
            emit(StackControlSliceInputs(reset=True))
            emit(
                StackControlSliceInputs(
                    astat_write=ExactWord(8, rng.randrange(1 << 8)),
                    mstat_write=ExactWord(4, rng.randrange(1 << 4)),
                    imask_write=ExactWord(4, rng.randrange(1 << 4)),
                )
            )
            continue
        choice = rng.randrange(12)
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
                pc_push=True,
                pc_push_value=rng.randrange(1 << 14),
                loop_push=True,
                loop_push_value=rng.randrange(1 << 18),
            )
        elif choice == 9:
            inputs = StackControlSliceInputs(
                execute=True,
                opcode=0x040000 | rng.randrange(32),
                pc_push=True,
                pc_push_value=rng.randrange(1 << 14),
            )
        elif choice == 10:
            inputs = StackControlSliceInputs(
                execute=True,
                opcode=0x040020 | rng.randrange(32),
            )
        else:
            status_code = rng.choice(
                (
                    StackControlStatusOperation.PUSH,
                    StackControlStatusOperation.POP,
                )
            )
            inputs = StackControlSliceInputs(
                execute=True,
                opcode=0x040000 | int(status_code),
            )
        emit(inputs)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=0x210026)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"wrote {len(lines)} stack-control-slice vectors to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
