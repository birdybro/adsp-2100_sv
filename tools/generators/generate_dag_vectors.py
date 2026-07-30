#!/usr/bin/env python3
"""Generate deterministic original ADSP-2100 DAG arithmetic vectors."""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model.dag import compute_dag  # noqa: E402


ADDRESS_BOUNDARIES = (
    0x0000,
    0x0001,
    0x0007,
    0x0008,
    0x000F,
    0x0010,
    0x1FFF,
    0x2000,
    0x3FFE,
    0x3FFF,
)
MODIFY_BOUNDARIES = (
    -8192,
    -17,
    -8,
    -1,
    0,
    1,
    7,
    8,
    17,
    8191,
)
LENGTH_BOUNDARIES = (
    0,
    1,
    2,
    3,
    7,
    8,
    9,
    0x1FFF,
    0x2000,
    0x3FFF,
)


def _pack_stimulus(
    i_value: int,
    m_value: int,
    l_value: int,
    dag1: bool,
    bit_reverse: bool,
) -> int:
    packed = i_value
    for value, width in (
        (m_value & 0x3FFF, 14),
        (l_value, 14),
        (dag1, 1),
        (bit_reverse, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def _pack_expected(result: object) -> int:
    packed = 0
    for value, width in (
        (result.address, 14),
        (result.next_i, 14),
        (result.base, 14),
        (result.circular, 1),
        (result.configuration_valid, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def _line(parameters: tuple[int, int, int, bool, bool]) -> str:
    i_value, m_value, l_value, dag1, bit_reverse = parameters
    result = compute_dag(
        i_value,
        m_value & 0x3FFF,
        l_value,
        dag1=dag1,
        bit_reverse_enabled=bit_reverse,
    )
    return (
        f"{_pack_stimulus(*parameters):011x} "
        f"{_pack_expected(result):011x}"
    )


def generate_lines(random_count: int, seed: int) -> list[str]:
    lines = [
        _line(parameters)
        for parameters in product(
            ADDRESS_BOUNDARIES,
            MODIFY_BOUNDARIES,
            LENGTH_BOUNDARIES,
            (False, True),
            (False, True),
        )
    ]
    lines.extend(
        _line((address, 0, 0, True, True))
        for address in range(0x4000)
    )
    for length in range(1, 257):
        for offset in range(length):
            for modify in (-length, -1, 0, 1, length):
                if -0x2000 <= modify <= 0x1FFF:
                    lines.append(
                        _line((offset, modify, length, True, False))
                    )

    rng = random.Random(seed)
    for _ in range(random_count):
        parameters = (
            rng.randrange(0x4000),
            rng.randrange(-0x2000, 0x2000),
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
    print(f"PASS wrote {len(lines)} DAG vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
