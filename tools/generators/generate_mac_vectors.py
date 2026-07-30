#!/usr/bin/env python3
"""Generate deterministic original ADSP-2100 MAC vectors for RTL comparison."""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model.mac import (  # noqa: E402
    compute_mac,
    saturate_mr,
)


WORD_BOUNDARIES = (
    0x0000,
    0x0001,
    0x7FFF,
    0x8000,
    0x8001,
    0xFFFE,
    0xFFFF,
)
MR_BOUNDARIES = (
    0x0000000000,
    0x0000027FFF,
    0x0000028000,
    0x007FFFFFFF,
    0x0080000000,
    0xFF7FFFFFFF,
    0xFF80000000,
    0xFFFFFFFFFF,
)


def _pack_stimulus(amf: int, x: int, y: int, mr: int, saturation_mv: bool) -> int:
    packed = amf
    for value, width in ((x, 16), (y, 16), (mr, 40), (saturation_mv, 1)):
        packed = (packed << width) | int(value)
    return packed


def _pack_expected(amf: int, x: int, y: int, mr: int, saturation_mv: bool) -> int:
    result = compute_mac(amf, x, y, mr)
    packed = 1
    for value, width in (
        (result.unrounded_result, 40),
        (result.result, 40),
        (result.mf_result, 16),
        (result.mv, 1),
        (saturate_mr(mr, saturation_mv), 40),
    ):
        packed = (packed << width) | int(value)
    return packed


def _line(parameters: tuple[int, int, int, int, bool]) -> str:
    stimulus = _pack_stimulus(*parameters)
    expected = _pack_expected(*parameters)
    return f"{stimulus:020x} {expected:035x}"


def generate_lines(random_count: int, seed: int) -> list[str]:
    lines = [
        _line(parameters)
        for parameters in product(
            range(0x01, 0x10),
            WORD_BOUNDARIES,
            WORD_BOUNDARIES,
            MR_BOUNDARIES,
            (False, True),
        )
    ]
    rng = random.Random(seed)
    for _ in range(random_count):
        parameters = (
            rng.randrange(0x01, 0x10),
            rng.randrange(0x10000),
            rng.randrange(0x10000),
            rng.randrange(1 << 40),
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
    print(f"PASS wrote {len(lines)} MAC vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
