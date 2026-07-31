#!/usr/bin/env python3
"""Generate deterministic Type 18 stateful model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    MODE_CONTROL_VALUE,
    ExactWord,
    apply_mode_control_slice_cycle,
    decode_mode_control,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ExactWord(4, 0)
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup: int | None = None,
    ) -> None:
        nonlocal state
        actions = decode_mode_control(opcode)
        result = apply_mode_control_slice_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup_mstat=ExactWord(4, setup) if setup is not None else None,
        )
        stimulus = 0
        for value, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (setup is not None, 1),
            (setup if setup is not None else 0, 4),
        ):
            stimulus = _append(stimulus, value, width)

        events = 0
        decoded_controls = (
            tuple(int(control) for control in actions.controls)
            if actions is not None
            else (0, 0, 0, 0)
        )
        for value, width in (
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (decoded_controls[0], 2),
            (decoded_controls[1], 2),
            (decoded_controls[2], 2),
            (decoded_controls[3], 2),
            (actions.has_effect if actions is not None else False, 1),
            (
                actions.has_no_change_one_alias
                if actions is not None
                else False,
                1,
            ),
        ):
            events = _append(events, value, width)
        lines.append(
            f"{stimulus:08x} {events:04x} {result.mstat.value:01x}"
        )
        state = result.mstat

    emit(reset=True)
    emit(setup=0xA)
    emit(execute=True, opcode=0x0C0BB0)
    emit(execute=True, opcode=0x0C0550)
    emit(execute=True, opcode=0x0D0000)
    emit(execute=True, opcode=0x0C0030, setup=0)

    # Exhaust every field combination against every possible cycle-start MSTAT.
    for initial in range(16):
        for payload in range(256):
            emit(setup=initial)
            emit(
                execute=True,
                opcode=MODE_CONTROL_VALUE | (payload << 4),
            )

    for index in range(random_count):
        choice = rng.randrange(10)
        if choice == 0:
            emit(reset=True)
        elif choice < 3:
            emit(setup=rng.randrange(16))
        elif choice < 7:
            emit(
                execute=True,
                opcode=MODE_CONTROL_VALUE | (rng.randrange(256) << 4),
            )
        elif choice == 7:
            opcode = rng.randrange(0x1000000)
            if opcode & 0xFFF00F == MODE_CONTROL_VALUE:
                opcode ^= 1
            emit(execute=True, opcode=opcode)
        elif choice == 8:
            emit(
                execute=True,
                opcode=MODE_CONTROL_VALUE | (rng.randrange(256) << 4),
                setup=rng.randrange(16),
            )
        else:
            emit()
        if index != 0 and index % 997 == 0:
            emit(reset=True)

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x210018,
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"wrote {len(lines)} Type 18 stateful vectors to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
