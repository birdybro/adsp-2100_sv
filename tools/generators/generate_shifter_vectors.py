#!/usr/bin/env python3
"""Generate deterministic original ADSP-2100 shifter vectors."""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model.shifter import compute_shifter  # noqa: E402


WORD_BOUNDARIES = (
    0x0000,
    0x0001,
    0x3FFF,
    0x4000,
    0x7FFF,
    0x8000,
    0x8001,
    0xC000,
    0xFFFF,
)
SHIFT_BOUNDARIES = (
    -128,
    -127,
    -33,
    -32,
    -31,
    -17,
    -16,
    -15,
    -1,
    0,
    1,
    15,
    16,
    17,
    31,
    32,
    127,
)
SR_BOUNDARIES = (0x00000000, 0x5AA5A55A, 0xFFFFFFFF)
SB_BOUNDARIES = (-16, -15, -1, 0)


def _pack_stimulus(
    sf: int,
    x: int,
    shift_or_se: int,
    sr: int,
    sb: int,
    av: bool,
    ac: bool,
    ss: bool,
) -> int:
    packed = sf
    for value, width in (
        (x, 16),
        (shift_or_se & 0xFF, 8),
        (sr, 32),
        (sb & 0x1F, 5),
        (av, 1),
        (ac, 1),
        (ss, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def _pack_expected(result: object) -> int:
    packed = 0
    for value, width in (
        (result.sr_result, 32),
        (result.sr_write, 1),
        (result.se_result, 8),
        (result.se_write, 1),
        (result.sb_result, 5),
        (result.sb_write, 1),
        (result.ss_result, 1),
        (result.ss_write, 1),
    ):
        packed = (packed << width) | int(value)
    return packed


def _line(parameters: tuple[int, int, int, int, int, bool, bool, bool]) -> str:
    sf, x, shift, sr, sb, av, ac, ss = parameters
    result = compute_shifter(
        sf,
        x,
        shift & 0xFF,
        sr,
        sb & 0x1F,
        av=av,
        ac=ac,
        ss=ss,
    )
    stimulus = _pack_stimulus(*parameters)
    return f"{stimulus:017x} {_pack_expected(result):013x}"


def generate_lines(random_count: int, seed: int) -> list[str]:
    lines = [
        _line(parameters)
        for parameters in product(
            range(0x10),
            WORD_BOUNDARIES,
            SHIFT_BOUNDARIES,
            SR_BOUNDARIES,
            SB_BOUNDARIES,
            (False, True),
            (False, True),
            (False, True),
        )
    ]
    lines.extend(
        _line((sf, x, shift, 0x5AA5A55A, -16, False, True, False))
        for sf, x, shift in product(
            range(0x0C),
            (0x0001, 0x8001),
            range(-128, 128),
        )
    )
    for x in range(0x10000):
        lines.extend(
            (
                _line((0x0C, x, 0, 0, -16, False, False, False)),
                _line((0x0D, x, 0, 0, -16, False, False, False)),
                _line((0x0D, x, 0, 0, -16, True, False, False)),
                _line((0x0E, x, -15, 0, -16, False, False, False)),
                _line((0x0E, x, -15, 0, -16, False, False, True)),
                _line((0x0F, x, 0, 0, -16, False, False, False)),
            )
        )
    rng = random.Random(seed)
    for _ in range(random_count):
        parameters = (
            rng.randrange(0x10),
            rng.randrange(0x10000),
            rng.randrange(-128, 128),
            rng.randrange(1 << 32),
            rng.randrange(-16, 16),
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
    print(f"PASS wrote {len(lines)} shifter vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
