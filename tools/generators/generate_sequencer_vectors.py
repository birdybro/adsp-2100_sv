#!/usr/bin/env python3
"""Generate deterministic original ADSP-2100 sequencer-flow vectors."""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model.sequencer import (  # noqa: E402
    ExplicitFlow,
    select_sequencer_flow,
)


ADDRESS_BOUNDARIES = (
    0x0000,
    0x0001,
    0x0002,
    0x0003,
    0x0004,
    0x1FFF,
    0x2000,
    0x3FFE,
    0x3FFF,
)


def _pack_stimulus(parameters: tuple[int, ...]) -> int:
    (
        pc,
        flow,
        taken,
        target,
        loop_active,
        loop_end,
        loop_start,
        termination,
        uses_counter,
    ) = parameters
    packed = pc
    for value, width in (
        (flow, 2),
        (taken, 1),
        (target, 14),
        (loop_active, 1),
        (loop_end, 14),
        (loop_start, 14),
        (termination, 1),
        (uses_counter, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def _pack_expected(result: object) -> int:
    packed = 0
    for value, width in (
        (result.next_pc, 14),
        (result.pc_stack_push, 1),
        (result.pc_stack_push_value, 14),
        (result.pc_stack_pop, 1),
        (result.loop_stack_pop, 1),
        (result.count_stack_pop, 1),
        (result.loop_counter_test, 1),
        (result.loop_back, 1),
        (result.loop_exit, 1),
        (result.explicit_transfer, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def _line(parameters: tuple[int, ...]) -> str:
    (
        pc,
        flow,
        taken,
        target,
        loop_active,
        loop_end,
        loop_start,
        termination,
        uses_counter,
    ) = parameters
    result = select_sequencer_flow(
        pc=pc,
        explicit_flow=flow,
        explicit_taken=bool(taken),
        explicit_target=target,
        loop_active=bool(loop_active),
        loop_end=loop_end,
        loop_start=loop_start,
        loop_termination_true=bool(termination),
        loop_uses_counter=bool(uses_counter),
    )
    return (
        f"{_pack_stimulus(parameters):016x} "
        f"{_pack_expected(result):09x}"
    )


def generate_lines(random_count: int, seed: int) -> list[str]:
    lines = [
        _line(parameters)
        for parameters in product(
            ADDRESS_BOUNDARIES,
            tuple(ExplicitFlow),
            (False, True),
            ADDRESS_BOUNDARIES,
            (False, True),
            ADDRESS_BOUNDARIES,
            ADDRESS_BOUNDARIES,
            (False, True),
            (False, True),
        )
    ]

    for pc in range(0x4000):
        target = pc ^ 0x2AAA
        start = pc ^ 0x1555
        lines.append(
            _line(
                (
                    pc,
                    ExplicitFlow.NONE,
                    False,
                    target,
                    False,
                    pc,
                    start,
                    False,
                    False,
                )
            )
        )
        lines.append(
            _line(
                (
                    pc,
                    ExplicitFlow.CALL,
                    True,
                    target,
                    False,
                    pc,
                    start,
                    False,
                    False,
                )
            )
        )
        for termination, uses_counter in product(
            (False, True),
            (False, True),
        ):
            lines.append(
                _line(
                    (
                        pc,
                        ExplicitFlow.NONE,
                        False,
                        target,
                        True,
                        pc,
                        start,
                        termination,
                        uses_counter,
                    )
                )
            )
        for flow, termination in product(
            (
                ExplicitFlow.JUMP,
                ExplicitFlow.CALL,
                ExplicitFlow.RETURN,
            ),
            (False, True),
        ):
            lines.append(
                _line(
                    (
                        pc,
                        flow,
                        True,
                        target,
                        True,
                        pc,
                        start,
                        termination,
                        True,
                    )
                )
            )

    rng = random.Random(seed)
    for _ in range(random_count):
        parameters = (
            rng.randrange(0x4000),
            rng.randrange(4),
            bool(rng.getrandbits(1)),
            rng.randrange(0x4000),
            bool(rng.getrandbits(1)),
            rng.randrange(0x4000),
            rng.randrange(0x4000),
            bool(rng.getrandbits(1)),
            bool(rng.getrandbits(1)),
        )
        lines.append(_line(parameters))
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=0x2100)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS wrote {len(lines)} sequencer-flow vectors to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
