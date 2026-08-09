#!/usr/bin/env python3
"""Generate deterministic original ADSP-2100 BR/BG vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    BusControlMode,
    BusControlState,
    LogicalPhase,
    apply_bus_control_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = BusControlState()
    phase = LogicalPhase.STATE_1
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        advance: bool = True,
        br_n: bool = True,
        service_inhibit: bool = False,
        phase_override: LogicalPhase | None = None,
    ) -> None:
        nonlocal state, phase
        active_phase = phase if phase_override is None else phase_override
        result = apply_bus_control_cycle(
            state,
            reset=reset,
            phase=active_phase,
            phase_advance=advance,
            br_n=br_n,
            service_inhibit=service_inhibit,
        )
        native_bg_n = br_n if reset else result.bg_n
        native_relinquished = (not br_n) if reset else result.bus_relinquished
        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(active_phase), 3),
            (advance, 1),
            (br_n, 1),
            (service_inhibit, 1),
        ):
            stimulus = _append(stimulus, value, width)
        expected_pre = 0
        for value, width in (
            (int(state.mode), 3),
            (result.state_three_boundary, 1),
            (result.request_recognized, 1),
            (result.grant_assert_event, 1),
            (result.release_recognized, 1),
            (result.grant_release_event, 1),
            (result.resume_event, 1),
            (result.request_withdrawn, 1),
            (result.release_cancelled, 1),
            (result.instruction_issue_inhibit, 1),
            (result.bus_relinquished, 1),
            (result.bg_n, 1),
            (result.reset_br_request, 1),
            (native_bg_n, 1),
            (native_relinquished, 1),
        ):
            expected_pre = _append(expected_pre, value, width)
        lines.append(
            f"{stimulus:02x} {expected_pre:05x} "
            f"{int(result.state.mode):01x}"
        )
        state = result.state
        if phase_override is None and advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    # Reset-time asynchronous wrapper truth table and normal reset handoff.
    emit(reset=True, br_n=True)
    emit(reset=True, br_n=False)
    emit(reset=True, br_n=True)

    # Complete request, grant, release, reacquire, and state-one resume.
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=True)
    emit(br_n=False)

    # Request recognition remains live during a service-inhibited state 3,
    # while the follow-up grant/withdrawal transition is deferred.
    emit(reset=True, br_n=True)
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=True)
    emit(br_n=False, service_inhibit=True)
    for _ in range(8):
        emit(br_n=False, service_inhibit=True)
    emit(br_n=False)
    for _ in range(7):
        emit(br_n=False)
    emit(br_n=False)
    for _ in range(7):
        emit(br_n=False)
    emit(br_n=True)
    for _ in range(7):
        emit(br_n=True)
    emit(br_n=True)
    for _ in range(5):
        emit(br_n=True)

    # Disabled state-three sample, early withdrawal, and release cancel.
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=True)
    emit(advance=False, br_n=False)
    emit(br_n=False)
    for _ in range(7):
        emit(br_n=True)
    emit(br_n=True)
    while state.mode is not BusControlMode.GRANTED:
        if state.mode is BusControlMode.IDLE:
            while phase is not LogicalPhase.STATE_3:
                emit(br_n=True)
            emit(br_n=False)
        else:
            emit(br_n=False)
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=False)
    emit(br_n=True)
    for _ in range(7):
        emit(br_n=False)
    emit(br_n=False)

    br_n = False
    for _ in range(random_count):
        reset = rng.randrange(1024) == 0
        advance = rng.randrange(8) != 0
        if reset:
            br_n = bool(rng.randrange(2))
        elif state.mode is BusControlMode.IDLE:
            if rng.randrange(128) == 0:
                br_n = False
            elif br_n is False and rng.randrange(32) == 0:
                br_n = True
        elif state.mode is BusControlMode.REQUEST_DELAY:
            if rng.randrange(64) == 0:
                br_n = True
            else:
                br_n = False
        elif state.mode is BusControlMode.GRANTED:
            if rng.randrange(96) == 0:
                br_n = True
            else:
                br_n = False
        elif state.mode is BusControlMode.RELEASE_DELAY:
            if rng.randrange(64) == 0:
                br_n = False
            else:
                br_n = True
        else:
            br_n = True
        service_inhibit = bool(
            state.mode is BusControlMode.REQUEST_DELAY
            and rng.randrange(32) == 0
        )
        emit(
            reset=reset,
            advance=advance,
            br_n=br_n,
            service_inhibit=service_inhibit,
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x2100B6)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} BR/BG clocks seed={args.seed:#x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
