#!/usr/bin/env python3
"""Generate deterministic sequencer-slice model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ExplicitFlow,
    SequencerSliceInputs,
    SequencerSliceState,
    apply_sequencer_slice_cycle,
)


def _append(packed: int, value: int, width: int) -> int:
    return (packed << width) | int(value)


def _pack_stimulus(inputs: SequencerSliceInputs) -> int:
    packed = 0
    for value, width in (
        (inputs.reset, 1),
        (inputs.pc, 14),
        (inputs.do_until, 1),
        (inputs.do_end, 14),
        (inputs.do_condition, 4),
        (int(inputs.explicit_flow), 2),
        (inputs.explicit_condition, 4),
        (inputs.explicit_target, 14),
        (inputs.counter_load, 1),
        (inputs.counter_load_value, 14),
        (inputs.pc_manual_pop, 1),
        (inputs.count_manual_pop, 1),
        (inputs.loop_manual_pop, 1),
        (inputs.az, 1),
        (inputs.an, 1),
        (inputs.av, 1),
        (inputs.ac, 1),
        (inputs.as_flag, 1),
        (inputs.mv, 1),
    ):
        packed = _append(packed, value, width)
    return packed


def _top(entries: tuple[int, ...]) -> tuple[bool, int]:
    return (bool(entries), entries[-1] if entries else 0)


def _pack_expected(
    state: SequencerSliceState,
    inputs: SequencerSliceInputs,
    *,
    compare_state: bool,
) -> int:
    result = apply_sequencer_slice_cycle(state, inputs)
    cntr_valid = state.counter.value is not None
    pc_valid, pc_top = _top(state.stacks.pc_entries)
    count_valid, count_top = _top(state.stacks.count_entries)
    loop_valid, loop_top = _top(state.stacks.loop_entries)
    boundary = result.boundary_valid

    pc_pop_valid = boundary and result.pc_stack_pop and pc_valid
    count_pop_valid = (
        boundary and result.count_stack_pop and count_valid
    )
    loop_pop_valid = boundary and result.loop_stack_pop and loop_valid
    pc_push_accepted = (
        boundary
        and result.pc_stack_push
        and len(state.stacks.pc_entries) < 16
    )
    count_push_accepted = (
        boundary
        and result.count_stack_push
        and len(state.stacks.count_entries) < 4
    )
    loop_push_accepted = (
        boundary
        and result.loop_stack_push
        and len(state.stacks.loop_entries) < 4
    )
    pc_overflow_event = (
        boundary
        and result.pc_stack_push
        and len(state.stacks.pc_entries) == 16
    )
    count_overflow_event = (
        boundary
        and result.count_stack_push
        and len(state.stacks.count_entries) == 4
    )
    loop_overflow_event = (
        boundary
        and result.loop_stack_push
        and len(state.stacks.loop_entries) == 4
    )
    pc_empty_pop = boundary and result.pc_stack_pop and not pc_valid
    count_empty_pop = (
        boundary and result.count_stack_pop and not count_valid
    )
    loop_empty_pop = (
        boundary and result.loop_stack_pop and not loop_valid
    )
    counter_condition_valid = bool(cntr_valid and not inputs.reset)
    counter_expired = bool(
        counter_condition_valid and state.counter.value == 1
    )
    not_counter_expired = bool(
        counter_condition_valid and state.counter.value != 1
    )
    counter_empty_manual_pop = bool(
        boundary and inputs.count_manual_pop and not count_valid
    )

    packed = int(compare_state)
    for value, width in (
        (cntr_valid if compare_state else False, 1),
        (
            state.counter.value
            if compare_state and cntr_valid
            else 0,
            14,
        ),
        (pc_valid if compare_state else False, 1),
        (pc_top if compare_state else 0, 14),
        (count_valid if compare_state else False, 1),
        (count_top if compare_state else 0, 14),
        (loop_valid if compare_state else False, 1),
        (loop_top if compare_state else 0, 18),
        (
            len(state.stacks.pc_entries) if compare_state else 0,
            5,
        ),
        (
            len(state.stacks.count_entries) if compare_state else 0,
            3,
        ),
        (
            len(state.stacks.loop_entries) if compare_state else 0,
            3,
        ),
        (state.stacks.pc_overflow if compare_state else False, 1),
        (state.stacks.count_overflow if compare_state else False, 1),
        (state.stacks.loop_overflow if compare_state else False, 1),
        (state.stacks.sstat_fragment if compare_state else 0, 8),
        (result.next_pc, 14),
        (result.boundary_valid, 1),
        (result.integration_conflict, 1),
        (result.unsupported_call_ce, 1),
        (result.invalid_counter_condition, 1),
        (result.invalid_loop_context, 1),
        (result.invalid_return_context, 1),
        (result.unsupported_do_at_loop_end, 1),
        (result.explicit_condition_true, 1),
        (result.loop_termination_true, 1),
        (result.explicit_transfer, 1),
        (result.loop_back, 1),
        (result.loop_exit, 1),
        (counter_condition_valid, 1),
        (counter_expired, 1),
        (not_counter_expired, 1),
        (result.counter_test, 1),
        (result.counter_decremented, 1),
        (result.counter_restored, 1),
        (result.counter_empty_invalidated, 1),
        (False, 1),
        (counter_empty_manual_pop, 1),
        (result.pc_stack_push, 1),
        (result.pc_stack_pop, 1),
        (result.count_stack_push, 1),
        (result.count_stack_pop, 1),
        (result.loop_stack_push, 1),
        (result.loop_stack_pop, 1),
        (
            (
                int(loop_pop_valid) << 2
                | int(count_pop_valid) << 1
                | int(pc_pop_valid)
            ),
            3,
        ),
        (
            (
                int(loop_push_accepted) << 2
                | int(count_push_accepted) << 1
                | int(pc_push_accepted)
            ),
            3,
        ),
        (
            (
                int(loop_overflow_event) << 2
                | int(count_overflow_event) << 1
                | int(pc_overflow_event)
            ),
            3,
        ),
        (
            (
                int(loop_empty_pop) << 2
                | int(count_empty_pop) << 1
                | int(pc_empty_pop)
            ),
            3,
        ),
        (False, 1),
    ):
        packed = _append(packed, value, width)
    return packed


def generate_lines(random_count: int, seed: int) -> list[str]:
    state = SequencerSliceState()
    pc = 0
    lines: list[str] = []

    def emit(
        inputs: SequencerSliceInputs,
        *,
        compare_state: bool = True,
    ) -> None:
        nonlocal state, pc
        result = apply_sequencer_slice_cycle(state, inputs)
        lines.append(
            f"{_pack_stimulus(inputs):020x} "
            f"{_pack_expected(state, inputs, compare_state=compare_state):036x}"
        )
        state = result.state
        pc = result.next_pc

    emit(SequencerSliceInputs(reset=True), compare_state=False)
    emit(
        SequencerSliceInputs(
            pc=0,
            counter_load=True,
            counter_load_value=3,
        )
    )
    emit(
        SequencerSliceInputs(
            pc=1,
            do_until=True,
            do_end=4,
            do_condition=14,
        )
    )
    emit(SequencerSliceInputs(pc=4))
    emit(SequencerSliceInputs(pc=4))
    emit(SequencerSliceInputs(pc=4))
    emit(
        SequencerSliceInputs(
            pc=5,
            explicit_flow=ExplicitFlow.CALL,
            explicit_condition=14,
            explicit_target=0x1000,
        )
    )
    emit(
        SequencerSliceInputs(
            pc=6,
            explicit_flow=ExplicitFlow.CALL,
            explicit_condition=15,
            explicit_target=0x1000,
        )
    )
    emit(
        SequencerSliceInputs(
            pc=0x1000,
            explicit_flow=ExplicitFlow.RETURN,
            explicit_condition=15,
        )
    )
    emit(SequencerSliceInputs(count_manual_pop=True))

    rng = random.Random(seed)
    for index in range(random_count):
        if index and index % 9973 == 0:
            emit(SequencerSliceInputs(reset=True, pc=pc))
            continue
        instruction = rng.randrange(12)
        flow = ExplicitFlow.NONE
        do_until = False
        counter_load = False
        pc_pop = False
        count_pop = False
        loop_pop = False
        if instruction == 1:
            counter_load = True
        elif instruction == 2:
            do_until = True
        elif instruction == 3:
            flow = ExplicitFlow.JUMP
        elif instruction == 4:
            flow = ExplicitFlow.CALL
        elif instruction == 5:
            flow = ExplicitFlow.RETURN
        elif instruction == 6:
            pc_pop = bool(rng.getrandbits(1))
            count_pop = bool(rng.getrandbits(1))
            loop_pop = bool(rng.getrandbits(1))
        if index % 2003 == 0:
            counter_load = True
            count_pop = True
        end_offset = rng.randrange(1, 7)
        emit(
            SequencerSliceInputs(
                pc=pc,
                do_until=do_until,
                do_end=(pc + end_offset) & 0x3FFF,
                do_condition=rng.randrange(16),
                explicit_flow=flow,
                explicit_condition=rng.randrange(16),
                explicit_target=rng.randrange(1 << 14),
                counter_load=counter_load,
                counter_load_value=rng.randrange(1 << 14),
                pc_manual_pop=pc_pop,
                count_manual_pop=count_pop,
                loop_manual_pop=loop_pop,
                az=bool(rng.getrandbits(1)),
                an=bool(rng.getrandbits(1)),
                av=bool(rng.getrandbits(1)),
                ac=bool(rng.getrandbits(1)),
                as_flag=bool(rng.getrandbits(1)),
                mv=bool(rng.getrandbits(1)),
            )
        )

    emit(SequencerSliceInputs(pc=pc))
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=0x21005E)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"wrote {len(lines)} sequencer-slice vectors to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
