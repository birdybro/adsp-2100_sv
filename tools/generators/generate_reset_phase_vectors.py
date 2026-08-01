#!/usr/bin/env python3
"""Generate deterministic original ADSP-2100 reset/phase vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    LogicalPhase,
    ResetPhaseState,
    apply_reset_phase_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _clkout(state: ResetPhaseState) -> bool:
    return bool(
        state.initialized
        and not state.reset_active
        and state.phase
        in (
            LogicalPhase.STATE_8,
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
        )
    )


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    recognized = apply_reset_phase_cycle(
        ResetPhaseState(),
        edge_enable=True,
        clkin_rising=True,
        reset_pin=True,
    )
    state = recognized.state
    next_rising = False
    lines: list[str] = []

    def emit(
        *,
        edge_enable: bool = True,
        clkin_rising: bool | None = None,
        reset_pin: bool = False,
    ) -> None:
        nonlocal state, next_rising
        rising = next_rising if clkin_rising is None else clkin_rising
        result = apply_reset_phase_cycle(
            state,
            edge_enable=edge_enable,
            clkin_rising=rising,
            reset_pin=reset_pin,
        )
        stimulus = 0
        for value in (edge_enable, rising, reset_pin):
            stimulus = _append(stimulus, value, 1)
        expected_pre = 0
        for value, width in (
            (int(state.phase), 3),
            (state.initialized, 1),
            (result.phase_advance, 1),
            (result.reset_recognized, 1),
            (result.architectural_reset, 1),
            (state.reset_active, 1),
            (state.asserted_rising_edges, 3),
            (result.release_first_rising, 1),
            (result.release_event, 1),
            (state.duration_error, 1),
            (_clkout(state), 1),
        ):
            expected_pre = _append(expected_pre, value, width)
        expected_post = 0
        for value, width in (
            (int(result.state.phase), 3),
            (result.state.initialized, 1),
            (result.state.reset_active, 1),
            (result.state.asserted_rising_edges, 3),
            (result.state.release_rising_seen, 1),
            (result.state.duration_error, 1),
            (_clkout(result.state), 1),
        ):
            expected_post = _append(expected_post, value, width)
        lines.append(
            f"{stimulus:01x} {expected_pre:04x} {expected_post:03x}"
        )
        state = result.state
        if edge_enable:
            next_rising = not rising

    # Complete a valid four-cycle reset and exact two-rising-edge release.
    emit(reset_pin=True)
    for _ in range(3):
        emit(reset_pin=True)
        emit(reset_pin=True)
    emit(reset_pin=False)
    emit(reset_pin=False)
    emit(reset_pin=False)
    for _ in range(16):
        emit(reset_pin=False)

    # A new short reset must fail closed; reassertion restarts the count.
    while next_rising:
        emit(reset_pin=False)
    emit(reset_pin=True)
    emit(reset_pin=True)
    emit(reset_pin=True)
    emit(reset_pin=True)
    emit(reset_pin=False)
    emit(reset_pin=False)
    emit(reset_pin=False)
    while not next_rising:
        emit(reset_pin=False)
    emit(reset_pin=True)

    reset_pin = True
    remaining_high_rises = 4
    release_rises = 0
    for _ in range(random_count):
        enabled = rng.randrange(8) != 0
        rising = next_rising
        if enabled and rising:
            if reset_pin:
                remaining_high_rises -= 1
                if remaining_high_rises <= 0:
                    reset_pin = False
                    release_rises = 0
            elif state.reset_active and not state.duration_error:
                release_rises += 1
            elif not state.reset_active and rng.randrange(64) == 0:
                reset_pin = True
                remaining_high_rises = rng.randrange(1, 8)
            elif state.duration_error and rng.randrange(4) == 0:
                reset_pin = True
                remaining_high_rises = 4
            if release_rises >= 2:
                release_rises = 0
        emit(
            edge_enable=enabled,
            clkin_rising=rising,
            reset_pin=reset_pin,
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x2100E5)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} reset/phase clocks seed={args.seed:#x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
