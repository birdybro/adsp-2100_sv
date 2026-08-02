#!/usr/bin/env python3
"""Generate deterministic model/RTL vectors for external IRQ recognition."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ExactWord,
    InterruptState,
    LogicalPhase,
    UNKNOWN,
    apply_interrupt_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _pack_stimulus(
    *,
    reset: bool,
    phase: int,
    phase_advance: bool,
    irq_n: int,
    icntl: int,
    icntl_valid: bool,
    imask: int,
    imask_valid: bool,
    service_allowed: bool,
) -> int:
    packed = 0
    for value, width in (
        (reset, 1),
        (phase, 3),
        (phase_advance, 1),
        (irq_n, 4),
        (icntl, 5),
        (icntl_valid, 1),
        (imask, 4),
        (imask_valid, 1),
        (service_allowed, 1),
    ):
        packed = _append(packed, value, width)
    return packed


def _pack_expected_pre(state: InterruptState, result) -> int:
    packed = 0
    for value, width in (
        (result.sample_event, 1),
        (result.sampled_requests, 4),
        (result.enabled_requests, 4),
        (result.recognition_event, 1),
        (result.recognized_level, 2),
        (result.vector_address.value, 14),
        (state.edge_pending, 4),
        (state.sample_history_valid, 1),
        (result.configuration_invalid, 1),
        (result.reset_baseline_provisional, 1),
    ):
        packed = _append(packed, value, width)
    return packed


def _pack_expected_post(state: InterruptState) -> int:
    return (state.edge_pending << 1) | int(state.sample_history_valid)


def generate(output: Path, *, cycles: int, seed: int) -> None:
    rng = random.Random(seed)
    state = InterruptState.reset()
    rows: list[str] = []
    directed = [
        # Reset, baseline high, blocked IRQ0 edge, then service after release.
        (True, 6, True, 0xF, 0x01, True, 0x1, True, True),
        (False, 6, True, 0xF, 0x01, True, 0x1, True, True),
        (False, 6, True, 0xE, 0x01, True, 0x1, True, False),
        (False, 6, True, 0xF, 0x01, True, 0x1, True, True),
        # All level requests prove fixed IRQ3 priority.
        (False, 6, True, 0x0, 0x00, True, 0xF, True, True),
        # Unknown configuration fails closed.
        (False, 6, True, 0x0, 0x00, False, 0xF, True, True),
    ]
    for index in range(cycles):
        if index < len(directed):
            values = directed[index]
        else:
            reset = rng.randrange(701) == 0
            phase = rng.randrange(8)
            advance = rng.randrange(9) != 0
            irq_n = rng.randrange(16)
            icntl = rng.randrange(32)
            icntl_valid = rng.randrange(23) != 0
            imask = rng.randrange(16)
            imask_valid = rng.randrange(37) != 0
            service_allowed = rng.randrange(5) != 0
            values = (
                reset,
                phase,
                advance,
                irq_n,
                icntl,
                icntl_valid,
                imask,
                imask_valid,
                service_allowed,
            )
        (
            reset,
            phase,
            advance,
            irq_n,
            icntl,
            icntl_valid,
            imask,
            imask_valid,
            service_allowed,
        ) = values
        result = apply_interrupt_cycle(
            state,
            reset=reset,
            phase=LogicalPhase(phase),
            phase_advance=advance,
            irq_n=irq_n,
            icntl=ExactWord(5, icntl) if icntl_valid else UNKNOWN,
            imask=ExactWord(4, imask) if imask_valid else UNKNOWN,
            service_allowed=service_allowed,
        )
        stimulus = _pack_stimulus(
            reset=reset,
            phase=phase,
            phase_advance=advance,
            irq_n=irq_n,
            icntl=icntl,
            icntl_valid=icntl_valid,
            imask=imask,
            imask_valid=imask_valid,
            service_allowed=service_allowed,
        )
        rows.append(
            f"{stimulus:06x} {_pack_expected_pre(state, result):09x} "
            f"{_pack_expected_post(result.state):02x}\n"
        )
        state = result.state
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=50027)
    parser.add_argument("--seed", type=int, default=2100022)
    args = parser.parse_args()
    generate(args.output, cycles=args.cycles, seed=args.seed)


if __name__ == "__main__":
    main()
