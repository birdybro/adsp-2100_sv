#!/usr/bin/env python3
"""Generate deterministic Type 7 stateful model-versus-RTL vectors."""

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
    LoadNonDregImmediateState,
    UNKNOWN,
    apply_load_non_dreg_immediate_cycle,
    decode_load_non_dreg_immediate,
    read_internal_move_register,
    register_code_by_name,
)


READABLE_CODES = tuple(register_code_by_name(writable=False).values())
WRITABLE_CODES = tuple(register_code_by_name(writable=True).values())
LEGAL_TYPE_7_CODES = tuple(code for code in WRITABLE_CODES if code >> 4 != 0)
INVALID_TYPE_7_CODES = tuple(
    code for code in range(64) if code not in LEGAL_TYPE_7_CODES
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(code: int, data: int) -> int:
    return (
        0x300000 | ((code >> 4) << 18)
        | ((data & 0x3FFF) << 4) | (code & 0xF)
    )


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = LoadNonDregImmediateState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup: InternalMoveSetup | None = None,
        probe: int | None = None,
    ) -> None:
        nonlocal state
        if probe is None:
            probe = rng.choice(READABLE_CODES)
        result = apply_load_non_dreg_immediate_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup=setup,
        )
        action = decode_load_non_dreg_immediate(opcode)

        stimulus = 0
        for item, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (setup is not None, 1),
            (setup.code if setup is not None else 0, 6),
            (setup.value if setup is not None else 0, 16),
            (probe, 6),
        ):
            stimulus = _append(stimulus, item, width)

        events = 0
        for item, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.invalid_subencoding, 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (False, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (action.register_group if action is not None else 0, 2),
            (action.register_index if action is not None else 0, 4),
            (action.register_code if action is not None else 0, 6),
            (action.data.value if action is not None else 0, 14),
            (
                action is not None
                and action.invalid_reason == "DATA_REGISTER_DESTINATION",
                1,
            ),
            (
                action is not None
                and action.invalid_reason == "RESERVED_DESTINATION_SELECTOR",
                1,
            ),
            (
                action is not None
                and action.invalid_reason == "READ_ONLY_SSTAT_DESTINATION",
                1,
            ),
            (result.count_stack_push, 1),
            (result.count_stack_push_value, 14),
            (result.pm_data_access, 1),
            (result.dm_access, 1),
        ):
            events = _append(events, item, width)

        registers = result.state.registers
        probe_value, _ = read_internal_move_register(registers, probe)
        post = 0
        post_mask = 0

        def add_optional(value: int | None, width: int) -> None:
            nonlocal post, post_mask
            post = _append(post, 0 if value is None else value, width)
            post_mask = _append(
                post_mask,
                0 if value is None else (1 << width) - 1,
                width,
            )

        if probe_value is UNKNOWN:
            add_optional(None, 16)
        else:
            assert isinstance(probe_value, ExactWord)
            add_optional(probe_value.value, 16)
        add_optional(registers.astat, 8)
        add_optional(registers.mstat, 4)
        add_optional(registers.icntl, 5)
        add_optional(registers.imask, 4)
        add_optional(registers.cntr, 14)
        post = _append(post, registers.cntr is not None, 1)
        post_mask = _append(post_mask, 1, 1)
        add_optional(registers.px, 8)
        post = _append(post, registers.sstat, 8)
        post_mask = _append(post_mask, 0xFF, 8)
        post = _append(post, len(registers.stacks.count_entries), 3)
        post_mask = _append(post_mask, 0x7, 3)
        post = _append(post, registers.stacks.count_overflow, 1)
        post_mask = _append(post_mask, 1, 1)

        lines.append(
            f"{stimulus:014x} {events:014x} {post:018x} {post_mask:018x}"
        )
        state = result.state

    emit(reset=True)
    for code in WRITABLE_CODES:
        emit(
            setup=InternalMoveSetup(code, (0x1100 + code * 0x101) & 0xFFFF),
            probe=code,
        )
    for code in LEGAL_TYPE_7_CODES:
        for data in (0, 1, 0x1F, 0xFF, 0x1FFF, 0x2000, 0x3FFF):
            emit(execute=True, opcode=_opcode(code, data), probe=code)
    for code in INVALID_TYPE_7_CODES:
        emit(execute=True, opcode=_opcode(code, code), probe=0x35)
    emit(reset=True)

    for index in range(random_count):
        choice = rng.randrange(24)
        probe = rng.choice(READABLE_CODES)
        if choice < 11:
            code = rng.choice(LEGAL_TYPE_7_CODES)
            emit(
                execute=True,
                opcode=_opcode(code, rng.randrange(1 << 14)),
                probe=code,
            )
        elif choice < 15:
            code = rng.choice(WRITABLE_CODES)
            emit(
                setup=InternalMoveSetup(code, rng.randrange(1 << 16)),
                probe=code,
            )
        elif choice < 18:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.choice(INVALID_TYPE_7_CODES),
                    rng.randrange(1 << 14),
                ),
                probe=probe,
            )
        elif choice == 18:
            emit(execute=True, opcode=rng.randrange(0x300000), probe=probe)
        elif choice == 19:
            code = rng.choice(LEGAL_TYPE_7_CODES)
            emit(
                execute=True,
                opcode=_opcode(code, rng.randrange(1 << 14)),
                setup=InternalMoveSetup(
                    rng.choice(WRITABLE_CODES), rng.randrange(1 << 16)
                ),
                probe=probe,
            )
        elif choice == 20 or (index != 0 and index % 5003 == 0):
            emit(reset=True, probe=probe)
        else:
            emit(probe=probe)

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda text: int(text, 0), default=0x210007)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 7 state vectors seed={args.seed:#x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
