#!/usr/bin/env python3
"""Generate deterministic Type 17 stateful model-versus-RTL vectors."""

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
    InternalMoveSetup,
    InternalMoveSliceState,
    UNKNOWN,
    apply_internal_move_cycle,
    decode_internal_move,
    read_internal_move_register,
    register_code_by_name,
)


READABLE = register_code_by_name(writable=False)
WRITABLE = register_code_by_name(writable=True)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(destination_code: int, source_code: int) -> int:
    return (
        0x0D0000
        | ((destination_code >> 4) << 10)
        | ((source_code >> 4) << 8)
        | ((destination_code & 0xF) << 4)
        | (source_code & 0xF)
    )


def _known(value: int | None, width: int) -> tuple[int, int]:
    if value is None:
        return (0, 0)
    return (value, (1 << width) - 1)


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = InternalMoveSliceState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup_code: int | None = None,
        setup_data: int = 0,
        probe_code: int = 0,
    ) -> None:
        nonlocal state
        setup = (
            InternalMoveSetup(setup_code, setup_data)
            if setup_code is not None
            else None
        )
        result = apply_internal_move_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup=setup,
        )
        decoded = decode_internal_move(opcode)
        class_valid = decoded is not None

        stimulus = 0
        for value, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (setup is not None, 1),
            (setup_code if setup_code is not None else 0, 6),
            (setup_data, 16),
            (probe_code, 6),
        ):
            stimulus = _append(stimulus, value, width)

        events = 0
        for value, width in (
            (class_valid, 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.invalid_subencoding, 1),
            (False, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (decoded.source_code if decoded is not None else 0, 6),
            (decoded.destination_code if decoded is not None else 0, 6),
            (result.source_extension_provisional, 1),
            (result.count_stack_push, 1),
            (result.count_stack_push_value, 14),
            (False, 1),
            (False, 1),
        ):
            events = _append(events, value, width)

        source_data = result.source_data if result.boundary_valid else 0
        source_mask = 0xFFFF if result.boundary_valid and result.source_valid else 0

        probe, _ = read_internal_move_register(result.state, probe_code)
        probe_value = 0 if probe is UNKNOWN else probe.value
        probe_mask = 0 if probe is UNKNOWN else 0xFFFF
        astat, astat_mask = _known(result.state.astat, 8)
        mstat, mstat_mask = _known(result.state.mstat, 4)
        icntl, icntl_mask = _known(result.state.icntl, 5)
        imask, imask_mask = _known(result.state.imask, 4)
        cntr, cntr_mask = _known(result.state.cntr, 14)
        px, px_mask = _known(result.state.px, 8)

        post = 0
        post_mask = 0
        post_fields = (
            (probe_value, probe_mask, 16),
            (astat, astat_mask, 8),
            (mstat, mstat_mask, 4),
            (icntl, icntl_mask, 5),
            (imask, imask_mask, 4),
            (cntr, cntr_mask, 14),
            (result.state.cntr is not None, 1, 1),
            (px, px_mask, 8),
            (result.state.sstat, 0xFF, 8),
            (len(result.state.stacks.count_entries), 0x7, 3),
            (result.state.stacks.count_overflow, 1, 1),
        )
        for value, mask, width in post_fields:
            post = _append(post, value, width)
            post_mask = _append(post_mask, mask, width)

        lines.append(
            f"{stimulus:014x} {events:010x} "
            f"{source_data:04x} {source_mask:04x} "
            f"{post:018x} {post_mask:018x}"
        )
        state = result.state

    def setup_register(code: int, value: int) -> None:
        emit(setup_code=code, setup_data=value, probe_code=code)

    def initialize_known_state() -> None:
        emit(reset=True, probe_code=READABLE["SSTAT"])
        for name, code in sorted(WRITABLE.items(), key=lambda item: item[1]):
            if code >> 4 and name != "MSTAT":
                setup_register(code, (code * 0x421 + 0x1357) & 0xFFFF)
        for name, code in sorted(WRITABLE.items(), key=lambda item: item[1]):
            if code >> 4 == 0:
                setup_register(code, (code * 0x811 + 0x2468) & 0xFFFF)
        setup_register(WRITABLE["SB"], 0x0007)
        setup_register(WRITABLE["MSTAT"], 1)
        for name, code in sorted(WRITABLE.items(), key=lambda item: item[1]):
            if code >> 4 == 0:
                setup_register(code, (code * 0x911 + 0xA468) & 0xFFFF)
        setup_register(WRITABLE["SB"], 0x0017)
        setup_register(WRITABLE["MSTAT"], 0)

    initialize_known_state()

    # Every legal register pair executes in both cycle-start banks.
    for bank in (0, 1):
        for destination_code in sorted(WRITABLE.values()):
            for source_code in sorted(READABLE.values()):
                setup_register(WRITABLE["MSTAT"], bank)
                emit(
                    execute=True,
                    opcode=_opcode(destination_code, source_code),
                    probe_code=destination_code,
                )

    # Fail-closed nonclass, reserved, read-only, and setup collision cases.
    emit(execute=True, opcode=0x000000, probe_code=READABLE["AR"])
    emit(execute=True, opcode=0x0D04C0, probe_code=READABLE["AR"])
    emit(execute=True, opcode=0x0D0C20, probe_code=READABLE["AR"])
    emit(
        execute=True,
        opcode=_opcode(WRITABLE["AR"], READABLE["AX0"]),
        setup_code=WRITABLE["AX1"],
        setup_data=0xCAFE,
        probe_code=READABLE["AR"],
    )

    legal_pairs = tuple(
        (destination, source)
        for destination in WRITABLE.values()
        for source in READABLE.values()
    )
    writable_codes = tuple(WRITABLE.values())
    readable_codes = tuple(READABLE.values())
    for index in range(random_count):
        choice = rng.randrange(12)
        if choice < 2:
            code = rng.choice(writable_codes)
            setup_register(code, rng.randrange(0x10000))
        elif choice < 10:
            destination, source = rng.choice(legal_pairs)
            emit(
                execute=True,
                opcode=_opcode(destination, source),
                probe_code=destination,
            )
        elif choice == 10:
            opcode = rng.randrange(0x1000000)
            if opcode & 0xFFF000 == 0x0D0000:
                opcode ^= 0x001000
            emit(
                execute=True,
                opcode=opcode,
                probe_code=rng.choice(readable_codes),
            )
        else:
            emit(probe_code=rng.choice(readable_codes))
        if index != 0 and index % 9973 == 0:
            initialize_known_state()

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x210017,
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} Type 17 stateful vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
