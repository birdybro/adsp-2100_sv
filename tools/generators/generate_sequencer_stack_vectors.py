#!/usr/bin/env python3
"""Generate deterministic PC/count/loop stack model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    SequencerStacksInputs,
    SequencerStacksState,
    apply_sequencer_stacks_cycle,
)


def _append(packed: int, value: int, width: int) -> int:
    return (packed << width) | int(value)


def _pack_stimulus(inputs: SequencerStacksInputs) -> int:
    packed = int(inputs.reset)
    for value, width in (
        (inputs.pc_push, 1),
        (inputs.pc_pop, 1),
        (inputs.pc_push_value, 14),
        (inputs.count_push, 1),
        (inputs.count_pop, 1),
        (inputs.count_push_value, 14),
        (inputs.loop_push, 1),
        (inputs.loop_pop, 1),
        (inputs.loop_push_value, 18),
    ):
        packed = _append(packed, value, width)
    return packed


def _pack_expected(
    state: SequencerStacksState,
    inputs: SequencerStacksInputs,
    *,
    compare_state: bool,
) -> int:
    conflict = bool(
        not inputs.reset
        and (
            (inputs.pc_push and inputs.pc_pop)
            or (inputs.count_push and inputs.count_pop)
            or (inputs.loop_push and inputs.loop_pop)
        )
    )
    pc_valid = bool(state.pc_entries)
    count_valid = bool(state.count_entries)
    loop_valid = bool(state.loop_entries)
    packed = int(compare_state)
    packed = _append(
        packed,
        state.sstat_fragment if compare_state else 0,
        8,
    )

    for entries, valid, push, pop, depth, depth_width, data_width in (
        (
            state.pc_entries,
            pc_valid,
            inputs.pc_push,
            inputs.pc_pop,
            16,
            5,
            14,
        ),
        (
            state.count_entries,
            count_valid,
            inputs.count_push,
            inputs.count_pop,
            4,
            3,
            14,
        ),
        (
            state.loop_entries,
            loop_valid,
            inputs.loop_push,
            inputs.loop_pop,
            4,
            3,
            18,
        ),
    ):
        pop_valid = bool(
            pop
            and valid
            and not inputs.reset
            and not conflict
        )
        push_accepted = bool(
            push
            and len(entries) < depth
            and not inputs.reset
            and not conflict
        )
        overflow_event = bool(
            push
            and len(entries) == depth
            and not inputs.reset
            and not conflict
        )
        empty_pop = bool(
            pop
            and not valid
            and not inputs.reset
            and not conflict
        )
        for value, width in (
            (len(entries) if compare_state else 0, depth_width),
            (valid if compare_state else False, 1),
            (entries[-1] if compare_state and valid else 0, data_width),
            (pop_valid, 1),
            (push_accepted, 1),
            (overflow_event, 1),
            (empty_pop, 1),
        ):
            packed = _append(packed, value, width)
    return _append(packed, conflict, 1)


def generate_lines(random_count: int, seed: int) -> list[str]:
    state = SequencerStacksState()
    lines: list[str] = []

    def emit(
        inputs: SequencerStacksInputs,
        *,
        compare_state: bool = True,
    ) -> None:
        nonlocal state
        lines.append(
            f"{_pack_stimulus(inputs):014x} "
            f"{_pack_expected(state, inputs, compare_state=compare_state):021x}"
        )
        state = apply_sequencer_stacks_cycle(state, inputs).state

    emit(SequencerStacksInputs(reset=True), compare_state=False)
    emit(SequencerStacksInputs())

    for index in range(16):
        emit(
            SequencerStacksInputs(
                pc_push=True,
                pc_push_value=(index * 0x101) & 0x3FFF,
            )
        )
    emit(SequencerStacksInputs())
    emit(SequencerStacksInputs(pc_push=True, pc_push_value=0x3FFF))
    for _ in range(16):
        emit(SequencerStacksInputs(pc_pop=True))
    emit(SequencerStacksInputs(pc_pop=True))

    for index in range(4):
        emit(
            SequencerStacksInputs(
                count_push=True,
                count_push_value=(index * 0x111) & 0x3FFF,
            )
        )
    emit(SequencerStacksInputs(count_push=True, count_push_value=0x3FFF))
    for _ in range(4):
        emit(SequencerStacksInputs(count_pop=True))
    emit(SequencerStacksInputs(count_pop=True))

    for index in range(4):
        emit(
            SequencerStacksInputs(
                loop_push=True,
                loop_push_value=(index * 0x11111) & 0x3FFFF,
            )
        )
    emit(SequencerStacksInputs(loop_push=True, loop_push_value=0x3FFFF))
    for _ in range(4):
        emit(SequencerStacksInputs(loop_pop=True))
    emit(SequencerStacksInputs(loop_pop=True))

    emit(
        SequencerStacksInputs(
            pc_push=True,
            pc_push_value=0x1234,
            count_push=True,
            count_push_value=0x2345,
            loop_push=True,
            loop_push_value=0x34567,
        )
    )
    emit(
        SequencerStacksInputs(
            pc_pop=True,
            count_pop=True,
            loop_pop=True,
        )
    )
    emit(
        SequencerStacksInputs(
            pc_push=True,
            pc_pop=True,
            count_push=True,
            count_push_value=0x1000,
        )
    )
    emit(SequencerStacksInputs())

    rng = random.Random(seed)
    for index in range(random_count):
        if index != 0 and index % 9973 == 0:
            emit(SequencerStacksInputs(reset=True))
            continue
        operations = [rng.randrange(3) for _ in range(3)]
        pc_push = operations[0] == 1
        pc_pop = operations[0] == 2
        if index % 2003 == 0:
            pc_push = True
            pc_pop = True
        emit(
            SequencerStacksInputs(
                pc_push=pc_push,
                pc_pop=pc_pop,
                pc_push_value=rng.randrange(1 << 14),
                count_push=operations[1] == 1,
                count_pop=operations[1] == 2,
                count_push_value=rng.randrange(1 << 14),
                loop_push=operations[2] == 1,
                loop_pop=operations[2] == 2,
                loop_push_value=rng.randrange(1 << 18),
            )
        )

    emit(SequencerStacksInputs())
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=0x210015)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"wrote {len(lines)} sequencer-stack vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
