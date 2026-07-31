#!/usr/bin/env python3
"""Generate deterministic original-CNTR model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    CounterInputs,
    CounterState,
    apply_counter_cycle,
)


def _append(packed: int, value: int, width: int) -> int:
    return (packed << width) | int(value)


def _pack_stimulus(inputs: CounterInputs) -> int:
    packed = int(inputs.reset)
    for value, width in (
        (inputs.load, 1),
        (inputs.load_value, 14),
        (inputs.ce_test, 1),
        (inputs.manual_pop, 1),
        (inputs.count_stack_top, 14),
        (inputs.count_stack_top_valid, 1),
    ):
        packed = _append(packed, value, width)
    return packed


def _pack_expected(
    state: CounterState,
    inputs: CounterInputs,
    *,
    compare_state: bool,
) -> int:
    result = apply_counter_cycle(state, inputs)
    state_valid = state.value is not None
    packed = int(compare_state)
    for value, width in (
        (state_valid if compare_state else False, 1),
        (state.value if compare_state and state_valid else 0, 14),
        (result.condition_valid, 1),
        (result.counter_expired, 1),
        (result.not_counter_expired, 1),
        (result.count_stack_push, 1),
        (
            result.count_stack_push_value
            if result.count_stack_push
            else 0,
            14,
        ),
        (result.count_stack_pop, 1),
        (result.decremented, 1),
        (result.restored, 1),
        (result.empty_ce_invalidated, 1),
        (result.invalid_ce_test, 1),
        (result.empty_manual_pop, 1),
        (result.write_conflict, 1),
    ):
        packed = _append(packed, value, width)
    return packed


def generate_lines(random_count: int, seed: int) -> list[str]:
    state = CounterState()
    lines: list[str] = []

    def emit(inputs: CounterInputs, *, compare_state: bool = True) -> None:
        nonlocal state
        lines.append(
            f"{_pack_stimulus(inputs):09x} "
            f"{_pack_expected(state, inputs, compare_state=compare_state):011x}"
        )
        state = apply_counter_cycle(state, inputs).state

    emit(CounterInputs(reset=True), compare_state=False)
    emit(CounterInputs())
    emit(CounterInputs(ce_test=True))
    emit(CounterInputs(load=True, load_value=3))
    emit(CounterInputs())
    emit(CounterInputs(load=True, load_value=9))
    emit(CounterInputs())
    emit(CounterInputs(ce_test=True))
    emit(CounterInputs(load=True, load_value=1))
    emit(
        CounterInputs(
            ce_test=True,
            count_stack_top=0x2345,
            count_stack_top_valid=True,
        )
    )
    emit(CounterInputs())
    emit(CounterInputs(load=True, load_value=1))
    emit(CounterInputs(ce_test=True))
    emit(CounterInputs())
    emit(CounterInputs(load=True, load_value=0))
    emit(CounterInputs(ce_test=True))
    emit(CounterInputs())
    emit(
        CounterInputs(
            manual_pop=True,
            count_stack_top=0x3456,
            count_stack_top_valid=True,
        )
    )
    emit(CounterInputs(manual_pop=True))
    emit(
        CounterInputs(
            load=True,
            load_value=2,
            ce_test=True,
            manual_pop=True,
            count_stack_top=4,
            count_stack_top_valid=True,
        )
    )
    emit(CounterInputs())

    rng = random.Random(seed)
    for index in range(random_count):
        if index and index % 9973 == 0:
            emit(CounterInputs(reset=True))
            continue
        action = rng.randrange(4)
        load = action == 1
        ce_test = action == 2
        manual_pop = action == 3
        if index % 2003 == 0:
            load = True
            ce_test = True
        emit(
            CounterInputs(
                load=load,
                load_value=rng.randrange(1 << 14),
                ce_test=ce_test,
                manual_pop=manual_pop,
                count_stack_top=rng.randrange(1 << 14),
                count_stack_top_valid=bool(rng.getrandbits(1)),
            )
        )

    emit(CounterInputs())
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=0x2100CE)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"wrote {len(lines)} counter vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
