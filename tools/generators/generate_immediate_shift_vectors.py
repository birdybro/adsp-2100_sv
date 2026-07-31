#!/usr/bin/env python3
"""Generate deterministic Type 15 stateful model-versus-RTL vectors."""

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
    ImmediateShiftState,
    apply_immediate_shift_cycle,
    read_dreg,
)


LEGAL_XOPS = (0, 2, 3, 4, 5, 6, 7)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(sf: int, xop: int, exponent: int) -> int:
    return 0x0F0000 | (sf << 11) | (xop << 8) | (exponent & 0xFF)


def _exact_or_zero(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _sr(bank: object) -> tuple[bool, int]:
    sr0, sr1 = bank.sr
    if not isinstance(sr0, ExactWord) or not isinstance(sr1, ExactWord):
        return False, 0
    return True, (sr1.value << 16) | sr0.value


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ImmediateShiftState.reset()
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
        nonlocal state
        result = apply_immediate_shift_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup_mstat=setup_mstat,
            setup_dreg=setup_dreg,
        )
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
        class_sf = (opcode >> 11) & 0xF if result.class_valid else 0
        class_xop = (opcode >> 8) & 0x7 if result.class_valid else 0
        class_exponent = opcode & 0xFF if result.class_valid else 0
        events = 0
        for value, width in (
            (result.class_valid, 1),
            (action is not None, 1),
            (result.unsupported_subencoding, 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (class_sf, 4),
            (class_xop, 3),
            (class_exponent, 8),
            (int(action.source) if action is not None else 0, 4),
            (result.boundary_valid, 1),
            (False, 1),
            (False, 1),
        ):
            events = _append(events, value, width)

        selected = (
            result.state.alternate
            if result.state.mstat.value & 1
            else result.state.primary
        )
        probe_known, probe_value = _exact_or_zero(read_dreg(selected, probe))
        sr_known, sr_value = _sr(selected)
        se_known, se_value = _exact_or_zero(read_dreg(selected, DREG.SE))
        post_state = 0
        for value, width in (
            (probe_known, 1),
            (probe_value, 16),
            (sr_known, 1),
            (sr_value, 32),
            (se_known, 1),
            (se_value, 16),
            (result.state.mstat.value, 4),
            (result.state.mstat.value & 1, 1),
        ):
            post_state = _append(post_state, value, width)
        lines.append(f"{stimulus:014x} {events:08x} {post_state:018x}")
        state = result.state

    emit(reset=True)
    for bank in (0, 1):
        emit(setup_mstat=ExactWord(4, bank))
        for destination in DREG:
            emit(
                setup_dreg=DREGWrite(
                    destination,
                    ExactWord(
                        16,
                        (0x1100 * (bank + 1) + 0x101 * int(destination))
                        & 0xFFFF,
                    ),
                ),
                probe=destination,
            )

    for bank in (0, 1):
        emit(setup_mstat=ExactWord(4, bank))
        for sf in range(8):
            for xop in LEGAL_XOPS:
                for exponent in range(256):
                    emit(
                        execute=True,
                        opcode=_opcode(sf, xop, exponent),
                        probe=DREG((sf + xop + exponent) & 0xF),
                    )

    for _ in range(random_count):
        choice = rng.randrange(17)
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
        elif choice < 12:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.randrange(8),
                    rng.choice(LEGAL_XOPS),
                    rng.randrange(256),
                ),
                probe=probe,
            )
        elif choice == 12:
            emit(
                execute=True,
                opcode=_opcode(rng.randrange(8), 1, rng.randrange(256)),
                probe=probe,
            )
        elif choice == 13:
            emit(
                execute=True,
                opcode=_opcode(rng.randrange(8, 16), rng.randrange(8), 0),
                probe=probe,
            )
        elif choice == 14:
            emit(execute=True, opcode=rng.choice((0, 0x0E0000, 0x100000)), probe=probe)
        elif choice == 15:
            emit(reset=True, probe=probe)
        else:
            destination = DREG(rng.randrange(16))
            emit(
                execute=True,
                opcode=_opcode(0, 0, rng.randrange(256)),
                setup_dreg=DREGWrite(
                    destination,
                    ExactWord(16, rng.randrange(1 << 16)),
                ),
                probe=destination,
            )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=30_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210015)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} Type 15 stateful vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
