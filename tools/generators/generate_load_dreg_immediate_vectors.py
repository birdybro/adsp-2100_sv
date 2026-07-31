#!/usr/bin/env python3
"""Generate deterministic Type 6 stateful model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DREG,
    DREGWrite,
    ExactWord,
    LoadDregImmediateState,
    apply_load_dreg_immediate_cycle,
    read_dreg,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = LoadDregImmediateState.reset()
    known = [[False] * 16 for _ in range(2)]
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup_mstat: ExactWord | None = None,
        setup_dreg: DREGWrite | None = None,
        probe: DREG = DREG.AX0,
    ) -> None:
        nonlocal state, known
        selected_before = state.mstat.value & 1
        result = apply_load_dreg_immediate_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup_mstat=setup_mstat,
            setup_dreg=setup_dreg,
        )
        if reset:
            known = [[False] * 16 for _ in range(2)]
        elif not result.integration_conflict and not result.invalid_opcode:
            if setup_dreg is not None:
                known[selected_before][int(setup_dreg.address)] = True
            if result.boundary_valid and result.action is not None:
                known[selected_before][int(result.action.destination)] = True

        stimulus = 0
        for value, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (setup_mstat is not None, 1),
            (setup_mstat.value if setup_mstat is not None else 0, 4),
            (setup_dreg is not None, 1),
            (int(setup_dreg.address) if setup_dreg is not None else 0, 4),
            (setup_dreg.data.value if setup_dreg is not None else 0, 16),
            (int(probe), 4),
        ):
            stimulus = _append(stimulus, value, width)

        action = result.action
        events = 0
        for value, width in (
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (int(action.destination) if action is not None else 0, 4),
            (action.data.value if action is not None else 0, 16),
            (False, 1),
            (False, 1),
        ):
            events = _append(events, value, width)

        selected_after = result.state.mstat.value & 1
        compare_probe = known[selected_after][int(probe)]
        probe_word = read_dreg(
            result.state.alternate if selected_after else result.state.primary,
            probe,
        )
        probe_value = probe_word.value if compare_probe else 0
        post_state = 0
        for value, width in (
            (compare_probe, 1),
            (probe_value, 16),
            (result.state.mstat.value, 4),
            (selected_after, 1),
        ):
            post_state = _append(post_state, value, width)

        lines.append(f"{stimulus:014x} {events:07x} {post_state:06x}")
        state = result.state

    emit(reset=True)
    for bank in (0, 1):
        emit(setup_mstat=ExactWord(4, bank))
        for destination in DREG:
            emit(
                setup_dreg=DREGWrite(
                    destination,
                    ExactWord(16, 0x1000 * (bank + 1) + int(destination)),
                ),
                probe=destination,
            )
        for destination in DREG:
            for data in (0, 1, 0x7FFF, 0x8000, 0xFFFF):
                emit(
                    execute=True,
                    opcode=(
                        0x400000
                        | (data << 4)
                        | int(destination)
                    ),
                    probe=destination,
                )

    for index in range(random_count):
        choice = rng.randrange(12)
        probe = DREG(rng.randrange(16))
        if choice == 0:
            emit(setup_mstat=ExactWord(4, rng.randrange(16)), probe=probe)
        elif choice < 3:
            destination = DREG(rng.randrange(16))
            emit(
                setup_dreg=DREGWrite(
                    destination,
                    ExactWord(16, rng.randrange(1 << 16)),
                ),
                probe=destination,
            )
        elif choice < 9:
            destination = DREG(rng.randrange(16))
            data = rng.randrange(1 << 16)
            emit(
                execute=True,
                opcode=0x400000 | (data << 4) | int(destination),
                probe=destination,
            )
        elif choice == 9:
            emit(execute=True, opcode=rng.choice((0, 0x300000, 0x500000)), probe=probe)
        elif choice == 10:
            destination = DREG(rng.randrange(16))
            emit(
                execute=True,
                opcode=0x400000 | rng.randrange(1 << 20),
                setup_dreg=DREGWrite(
                    destination,
                    ExactWord(16, rng.randrange(1 << 16)),
                ),
                probe=destination,
            )
        else:
            emit(probe=probe)
        if index != 0 and index % 5003 == 0:
            emit(reset=True)

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210006)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} Type 6 stateful vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
