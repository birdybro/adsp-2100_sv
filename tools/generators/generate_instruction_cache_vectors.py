#!/usr/bin/env python3
"""Generate deterministic original ADSP-2100 cache model/RTL vectors."""

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
    InstructionCacheState,
    UNKNOWN,
    apply_instruction_cache_cycle,
    lookup_instruction_cache,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def generate_lines(random_count: int, seed: int) -> list[str]:
    state = InstructionCacheState.reset()
    rng = random.Random(seed)
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        fill: bool = False,
        fill_address: int = 0,
        fill_address_valid: bool = True,
        fill_instruction: int = 0,
        fill_instruction_valid: bool = True,
        lookup_address: int = 0,
        lookup_address_valid: bool = True,
        compare_state: bool = True,
    ) -> None:
        nonlocal state
        address = (
            ExactWord(14, fill_address) if fill_address_valid else UNKNOWN
        )
        instruction = (
            ExactWord(24, fill_instruction)
            if fill_instruction_valid else UNKNOWN
        )
        lookup = lookup_instruction_cache(
            state,
            ExactWord(14, lookup_address)
            if lookup_address_valid else UNKNOWN,
        )
        result = apply_instruction_cache_cycle(
            state,
            reset=reset,
            fill=fill,
            fetch_address=address,
            fetch_instruction=instruction,
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (fill, 1),
            (fill_address, 14),
            (fill_address_valid, 1),
            (fill_instruction, 24),
            (fill_instruction_valid, 1),
            (lookup_address, 14),
            (lookup_address_valid, 1),
        ):
            stimulus = _append(stimulus, value, width)

        expected = 0
        known_instruction = (
            lookup.instruction.value if lookup.instruction_valid else 0
        )
        for value, width in (
            (compare_state, 1),
            (lookup.address_hit, 1),
            (lookup.instruction_valid, 1),
            (known_instruction, 24),
            (result.fill_accepted, 1),
            (result.region_restarted, 1),
            (result.oldest_replaced, 1),
            (state.region_count != 0, 1),
            (state.region_start if compare_state else 0, 14),
            (state.region_count if compare_state else 0, 5),
        ):
            expected = _append(expected, value, width)
        lines.append(f"{stimulus:015x} {expected:013x}")
        state = result.state

    emit(reset=True, compare_state=False)
    for address in range(0x120, 0x132):
        emit(
            fill=True,
            fill_address=address & 0x3FFF,
            fill_instruction=(0xA00000 | address),
            lookup_address=(address - 1) & 0x3FFF,
        )
    emit(
        fill=True,
        fill_address=0x128,
        fill_instruction=0xFEDCBA,
        lookup_address=0x128,
    )
    emit(
        fill=True,
        fill_address=0x333,
        fill_instruction=0x112233,
        lookup_address=0x129,
    )
    emit(
        fill=True,
        fill_address=0x334,
        fill_instruction=0,
        fill_instruction_valid=False,
        lookup_address=0x334,
    )
    emit(
        fill=True,
        fill_address_valid=False,
        lookup_address=0x333,
    )
    for address in (0x3FFE, 0x3FFF, 0x0000, 0x0001):
        emit(
            fill=True,
            fill_address=address,
            fill_instruction=address,
            lookup_address=address,
        )

    next_sequential = 2
    for index in range(random_count):
        if index and index % 9973 == 0:
            emit(reset=True, compare_state=False)
            next_sequential = rng.randrange(1 << 14)
            continue
        choice = rng.randrange(20)
        if choice < 11:
            fill_address = next_sequential
            next_sequential = (next_sequential + 1) & 0x3FFF
            emit(
                fill=True,
                fill_address=fill_address,
                fill_instruction=rng.randrange(1 << 24),
                fill_instruction_valid=rng.randrange(20) != 0,
                lookup_address=rng.randrange(1 << 14),
                lookup_address_valid=rng.randrange(20) != 0,
            )
        elif choice < 15 and state.region_count:
            offset = rng.randrange(state.region_count)
            fill_address = (state.region_start + offset) & 0x3FFF
            emit(
                fill=True,
                fill_address=fill_address,
                fill_instruction=rng.randrange(1 << 24),
                lookup_address=fill_address,
            )
        elif choice == 15:
            emit(
                fill=True,
                fill_address_valid=False,
                lookup_address=rng.randrange(1 << 14),
            )
        elif choice < 18:
            fill_address = rng.randrange(1 << 14)
            next_sequential = (fill_address + 1) & 0x3FFF
            emit(
                fill=True,
                fill_address=fill_address,
                fill_instruction=rng.randrange(1 << 24),
                lookup_address=rng.randrange(1 << 14),
            )
        else:
            emit(
                lookup_address=rng.randrange(1 << 14),
                lookup_address_valid=rng.randrange(10) != 0,
            )
    emit(reset=True, compare_state=False)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x2100CA)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} instruction-cache vectors "
        f"seed=0x{args.seed:x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
