#!/usr/bin/env python3
"""Generate deterministic boundary and random ALU vectors for RTL comparison."""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model.alu import compute_alu  # noqa: E402


BOUNDARIES = (0x0000, 0x0001, 0x0002, 0x7FFE, 0x7FFF, 0x8000, 0x8001, 0xFFFE, 0xFFFF)


def _pack_stimulus(
    amf: int,
    x: int,
    y: int,
    carry: bool,
    previous_av: bool,
    sticky: bool,
    saturate: bool,
    destination_is_ar: bool,
) -> int:
    packed = amf
    for value, width in (
        (x, 16),
        (y, 16),
        (carry, 1),
        (previous_av, 1),
        (sticky, 1),
        (saturate, 1),
        (destination_is_ar, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def _pack_expected(result: object) -> int:
    packed = 1
    for value, width in (
        (result.raw_result, 16),
        (result.destination_result, 16),
        (result.az, 1),
        (result.an, 1),
        (result.av, 1),
        (result.ac, 1),
        (result.as_value, 1),
        (result.as_write, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def _line(parameters: tuple[int, int, int, bool, bool, bool, bool, bool]) -> str:
    amf, x, y, carry, previous_av, sticky, saturate, destination_is_ar = parameters
    result = compute_alu(
        amf,
        x,
        y,
        carry_in=carry,
        previous_av=previous_av,
        sticky_av=sticky,
        saturate_ar=saturate,
        destination_is_ar=destination_is_ar,
    )
    stimulus = _pack_stimulus(*parameters)
    return f"{stimulus:011x} {_pack_expected(result):010x}"


def generate_lines(random_count: int, seed: int) -> list[str]:
    lines = [
        _line(parameters)
        for parameters in product(
            range(0x10, 0x20),
            BOUNDARIES,
            BOUNDARIES,
            (False, True),
            (False, True),
            (False, True),
            (False, True),
            (False, True),
        )
    ]
    rng = random.Random(seed)
    for _ in range(random_count):
        parameters = (
            rng.randrange(0x10, 0x20),
            rng.randrange(0x10000),
            rng.randrange(0x10000),
            bool(rng.getrandbits(1)),
            bool(rng.getrandbits(1)),
            bool(rng.getrandbits(1)),
            bool(rng.getrandbits(1)),
            bool(rng.getrandbits(1)),
        )
        lines.append(_line(parameters))
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0x2100)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS wrote {len(lines)} ALU vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
