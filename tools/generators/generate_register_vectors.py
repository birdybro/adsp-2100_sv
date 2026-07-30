#!/usr/bin/env python3
"""Generate deterministic stateful ADSP-2100 DREG-bank vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ComputationalBank,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_dreg_cycle,
    read_dreg,
)


def _pack_stimulus(
    alternate_selected: bool,
    reads: tuple[DREG, DREG, DREG],
    writes: tuple[DREGWrite, ...],
) -> int:
    packed = int(alternate_selected)
    for address in reads:
        packed = (packed << 4) | int(address)
    for port in range(3):
        if port < len(writes):
            write = writes[port]
            fields = (1, int(write.address), write.data.value)
        else:
            fields = (0, 0, 0)
        for value, width in zip(fields, (1, 4, 16), strict=True):
            packed = (packed << width) | value
    return packed


def _pack_expected(
    reads: tuple[object, ...],
    *,
    compare_reads: bool,
    conflict: bool = False,
) -> int:
    packed = (int(compare_reads) << 1) | int(conflict)
    for value in reads:
        packed <<= 16
        if value is not UNKNOWN:
            if not isinstance(value, ExactWord) or value.width != 16:
                raise ValueError("known DREG read must be exactly 16 bits")
            packed |= value.value
    return packed


def _write(address: DREG, value: int) -> DREGWrite:
    return DREGWrite(address, ExactWord(16, value))


def _destinations(address: DREG) -> frozenset[DREG]:
    if address == DREG.MR1:
        return frozenset((DREG.MR1, DREG.MR2))
    return frozenset((address,))


def generate_lines(random_count: int, seed: int) -> list[str]:
    primary = ComputationalBank()
    alternate = ComputationalBank()
    lines: list[str] = []

    def emit(
        alternate_selected: bool,
        reads: tuple[DREG, DREG, DREG],
        writes: tuple[DREGWrite, ...] = (),
        *,
        compare_reads: bool = True,
    ) -> None:
        nonlocal primary, alternate
        result = apply_dreg_cycle(
            primary,
            alternate,
            alternate_selected=alternate_selected,
            read_addresses=reads,
            writes=writes,
        )
        lines.append(
            f"{_pack_stimulus(alternate_selected, reads, writes):019x} "
            f"{_pack_expected(result.reads, compare_reads=compare_reads):013x}"
        )
        primary, alternate = result.primary, result.alternate

    # Establish deterministic state without pretending that device reset does.
    for alternate_selected in (False, True):
        for address in DREG:
            value = (
                (0x1000 if not alternate_selected else 0xA000)
                | (int(address) << 4)
                | int(address)
            )
            emit(
                alternate_selected,
                (DREG.AX0, DREG.AX0, DREG.AX0),
                (_write(address, value),),
                compare_reads=False,
            )

    # Exhaust every combination of the three independent combinational reads.
    for alternate_selected in (False, True):
        for read_0 in DREG:
            for read_1 in DREG:
                for read_2 in DREG:
                    emit(alternate_selected, (read_0, read_1, read_2))

    # Each write is observed as old data in its own cycle and new data next.
    for alternate_selected in (False, True):
        for address in DREG:
            new_value = (
                (0x5000 if not alternate_selected else 0xD000)
                | (int(address) << 4)
                | int(address)
            )
            emit(
                alternate_selected,
                (address, address, address),
                (_write(address, new_value),),
            )
            emit(alternate_selected, (address, address, address))

    # Directed narrow and MR1-to-MR2 sign-extension boundaries.
    for value in (0x007F, 0x0080, 0xFF7F, 0xFF80):
        emit(
            False,
            (DREG.SE, DREG.MR2, DREG.AX0),
            (_write(DREG.SE, value), _write(DREG.MR2, value)),
        )
        emit(False, (DREG.SE, DREG.MR2, DREG.AX0))
    for value in (0x0000, 0x7FFF, 0x8000, 0xFFFF):
        emit(
            False,
            (DREG.MR0, DREG.MR1, DREG.MR2),
            (_write(DREG.MR1, value),),
        )
        emit(False, (DREG.MR0, DREG.MR1, DREG.MR2))

    rng = random.Random(seed)
    all_addresses = list(DREG)
    for _ in range(random_count):
        alternate_selected = bool(rng.getrandbits(1))
        reads = tuple(rng.choice(all_addresses) for _ in range(3))
        writes: list[DREGWrite] = []
        occupied: set[DREG] = set()
        candidates = all_addresses.copy()
        rng.shuffle(candidates)
        wanted = rng.randrange(4)
        if wanted:
            for address in candidates:
                destinations = _destinations(address)
                if occupied.isdisjoint(destinations):
                    writes.append(_write(address, rng.randrange(0x10000)))
                    occupied.update(destinations)
                    if len(writes) == wanted:
                        break
        emit(alternate_selected, reads, tuple(writes))

    # Conflict vectors are clocked; the following vector proves that all
    # architectural writes were suppressed.
    known_read = read_dreg(primary, DREG.AX0)
    known_reads = (known_read,) * 3
    for writes in (
        (_write(DREG.AX0, 1), _write(DREG.AX0, 2)),
        (_write(DREG.MR1, 1), _write(DREG.MR2, 2)),
    ):
        lines.append(
            f"{_pack_stimulus(False, (DREG.AX0,) * 3, writes):019x} "
            f"{_pack_expected(known_reads, compare_reads=True, conflict=True):013x}"
        )
    emit(False, (DREG.AX0,) * 3)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=0x2100)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS wrote {len(lines)} register-bank vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
