#!/usr/bin/env python3
"""Generate exhaustive expected IF-condition results for RTL simulation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model.conditions import (  # noqa: E402
    ConditionInputs,
    evaluate_if_condition,
)


def generate_lines() -> list[str]:
    lines: list[str] = []
    for code in range(16):
        for flags in range(128):
            inputs = ConditionInputs(
                az=bool(flags & 0x40),
                an=bool(flags & 0x20),
                av=bool(flags & 0x10),
                ac=bool(flags & 0x08),
                as_flag=bool(flags & 0x04),
                mv=bool(flags & 0x02),
                counter_nonzero=bool(flags & 0x01),
            )
            lines.append("1" if evaluate_if_condition(code, inputs) else "0")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(generate_lines()) + "\n", encoding="ascii")
    print(f"PASS wrote 2048 condition vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
