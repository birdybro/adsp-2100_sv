#!/usr/bin/env python3
"""Generate deterministic standalone original ADSP-2100 HALT vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    HaltControlMode,
    HaltControlState,
    LogicalPhase,
    apply_halt_control_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def generate_lines(
    random_count: int,
    seed: int,
) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = HaltControlState()
    phase = LogicalPhase.STATE_8
    lines: list[str] = []
    coverage = {
        "ordinary_recognized": 0,
        "pm_data_recognized": 0,
        "force_fetch_issued": 0,
        "stopped": 0,
        "resumed": 0,
        "dmack_blocked": 0,
        "held_clocks": 0,
    }

    def emit(
        *,
        reset: bool = False,
        advance: bool = True,
        halt_n: bool = True,
        dmack: bool = True,
        pm_data_cycle: bool = False,
    ) -> None:
        nonlocal state, phase
        result = apply_halt_control_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            halt_n=halt_n,
            dmack=dmack,
            pm_data_cycle=pm_data_cycle,
        )
        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(phase), 3),
            (advance, 1),
            (halt_n, 1),
            (dmack, 1),
            (pm_data_cycle, 1),
        ):
            stimulus = _append(stimulus, value, width)

        expected_pre = 0
        for value, width in (
            (int(state.mode), 2),
            (result.state_three_boundary, 1),
            (result.halt_recognized, 1),
            (result.halt_stop_event, 1),
            (result.force_fetch_issue, 1),
            (result.resume_event, 1),
            (result.release_blocked, 1),
            (result.instruction_issue_inhibit, 1),
            (result.phase_hold, 1),
            (result.effective_phase_advance, 1),
            (result.halted, 1),
            (result.phase_conflict, 1),
        ):
            expected_pre = _append(expected_pre, value, width)

        coverage["ordinary_recognized"] += int(
            result.halt_recognized and not pm_data_cycle
        )
        coverage["pm_data_recognized"] += int(
            result.halt_recognized and pm_data_cycle
        )
        coverage["force_fetch_issued"] += int(result.force_fetch_issue)
        coverage["stopped"] += int(result.halt_stop_event)
        coverage["resumed"] += int(result.resume_event)
        coverage["dmack_blocked"] += int(result.release_blocked)
        coverage["held_clocks"] += int(result.phase_hold)

        lines.append(
            f"{stimulus:02x} {expected_pre:04x} "
            f"{int(result.state.mode):01x}"
        )
        state = result.state
        if result.effective_phase_advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    # Establish reset without advancing the externally owned phase.
    emit(reset=True, advance=False)

    # Ordinary fetch: current cycle completes, then state eight is held.
    emit()
    while phase is not LogicalPhase.STATE_3:
        emit()
    emit(halt_n=False)
    while phase is not LogicalPhase.STATE_7:
        emit(halt_n=False)
    emit(halt_n=False)
    emit(halt_n=True, dmack=False)
    emit(halt_n=True, dmack=True)

    # PM data: complete data, force one fetch, then stop after that fetch.
    while phase is not LogicalPhase.STATE_3:
        emit()
    emit(halt_n=False, pm_data_cycle=True)
    while phase is not LogicalPhase.STATE_8:
        emit(halt_n=False)
    emit(halt_n=False)
    while phase is not LogicalPhase.STATE_7:
        emit(halt_n=False)
    emit(halt_n=False)
    emit(halt_n=False)
    emit(halt_n=True, dmack=True)

    # A disabled state-three sample must not recognize a short assertion.
    while phase is not LogicalPhase.STATE_3:
        emit()
    emit(advance=False, halt_n=False, pm_data_cycle=True)
    emit(halt_n=True)

    for _ in range(random_count):
        reset = rng.randrange(4096) == 0
        advance = rng.randrange(16) != 0
        pm_data_cycle = bool(rng.randrange(2))
        if state.mode is HaltControlMode.RUNNING:
            halt_n = not (
                phase is LogicalPhase.STATE_3 and rng.randrange(8) == 0
            )
            dmack = True
        elif state.mode in (
            HaltControlMode.STOP_PENDING,
            HaltControlMode.FORCE_FETCH_PENDING,
        ):
            halt_n = False
            dmack = True
        else:
            halt_n = rng.randrange(3) == 0
            dmack = rng.randrange(3) != 0
        emit(
            reset=reset,
            advance=advance,
            halt_n=halt_n,
            dmack=dmack,
            pm_data_cycle=pm_data_cycle,
        )

    emit(reset=True, advance=False)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x2100A8,
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.random_count, args.seed)
    if min(coverage.values()) == 0:
        raise RuntimeError(f"insufficient HALT event coverage: {coverage}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} HALT-controller clocks "
        f"seed={args.seed:#x} "
        + " ".join(f"{name}={count}" for name, count in coverage.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
