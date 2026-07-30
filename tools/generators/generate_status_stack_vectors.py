#!/usr/bin/env python3
"""Generate deterministic status-stack model-versus-RTL cycle vectors."""

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
    StatusStackCycleInputs,
    StatusStackEntry,
    StatusStackOperation,
    StatusStackState,
    apply_status_stack_cycle,
)


def _entry(value: int) -> StatusStackEntry:
    return StatusStackEntry.from_word(ExactWord(16, value))


def _pack_stimulus(inputs: StatusStackCycleInputs) -> int:
    push_data = (
        inputs.push_entry.to_word().value
        if inputs.push_entry is not None
        else 0
    )
    return (
        (int(inputs.reset) << 18)
        | (int(inputs.operation) << 16)
        | push_data
    )


def _pack_expected(
    state: StatusStackState,
    inputs: StatusStackCycleInputs,
    *,
    compare_state: bool,
) -> int:
    pop_valid = (
        not inputs.reset
        and inputs.operation is StatusStackOperation.POP
        and not state.empty
    )
    pop_data = state.entries[-1].to_word().value if pop_valid else 0
    push_accepted = (
        not inputs.reset
        and inputs.operation is StatusStackOperation.PUSH
        and state.depth < 4
    )
    overflow_event = (
        not inputs.reset
        and inputs.operation is StatusStackOperation.PUSH
        and state.depth == 4
    )
    empty_pop = (
        not inputs.reset
        and inputs.operation is StatusStackOperation.POP
        and state.empty
    )
    packed = int(compare_state)
    for value, width in (
        (state.empty if compare_state else False, 1),
        (state.overflow if compare_state else False, 1),
        (state.depth if compare_state else 0, 3),
        (pop_valid, 1),
        (pop_valid, 1),
        (pop_data, 16),
        (push_accepted, 1),
        (overflow_event, 1),
        (empty_pop, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def generate_lines(random_count: int, seed: int) -> list[str]:
    state = StatusStackState()
    lines: list[str] = []

    def emit(
        inputs: StatusStackCycleInputs,
        *,
        compare_state: bool = True,
    ) -> None:
        nonlocal state
        stimulus = _pack_stimulus(inputs)
        expected = _pack_expected(
            state,
            inputs,
            compare_state=compare_state,
        )
        lines.append(f"{stimulus:05x} {expected:07x}")
        state = apply_status_stack_cycle(state, inputs).state

    emit(StatusStackCycleInputs(reset=True), compare_state=False)
    emit(StatusStackCycleInputs())

    for operation in (
        StatusStackOperation.NO_CHANGE_ZERO,
        StatusStackOperation.NO_CHANGE_ONE,
    ):
        emit(StatusStackCycleInputs(operation=operation))

    values = (0x0000, 0x1234, 0x800F, 0xFFFF)
    for value in values:
        emit(
            StatusStackCycleInputs(
                operation=StatusStackOperation.PUSH,
                push_entry=_entry(value),
            )
        )
        emit(StatusStackCycleInputs())
    for _ in values:
        emit(StatusStackCycleInputs(operation=StatusStackOperation.POP))
        emit(StatusStackCycleInputs())
    emit(StatusStackCycleInputs(operation=StatusStackOperation.POP))
    emit(StatusStackCycleInputs())

    # Prove oldest data survives saturation and empty/overflow can coexist.
    for value in values:
        emit(
            StatusStackCycleInputs(
                operation=StatusStackOperation.PUSH,
                push_entry=_entry(value),
            )
        )
    emit(
        StatusStackCycleInputs(
            operation=StatusStackOperation.PUSH,
            push_entry=_entry(0xDEAD),
        )
    )
    emit(StatusStackCycleInputs())
    for _ in values:
        emit(StatusStackCycleInputs(operation=StatusStackOperation.POP))
        emit(StatusStackCycleInputs())

    rng = random.Random(seed)
    operations = tuple(StatusStackOperation)
    for index in range(random_count):
        if index != 0 and index % 9973 == 0:
            emit(StatusStackCycleInputs(reset=True))
            continue
        operation = rng.choice(operations)
        emit(
            StatusStackCycleInputs(
                operation=operation,
                push_entry=(
                    _entry(rng.randrange(1 << 16))
                    if operation is StatusStackOperation.PUSH
                    else None
                ),
            )
        )

    emit(StatusStackCycleInputs())
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=0x210021)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"wrote {len(lines)} status-stack vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
