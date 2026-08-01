#!/usr/bin/env python3
"""Generate deterministic Type 3 state/transaction differential vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DirectDMSliceState,
    ExactWord,
    InternalMoveSetup,
    UNKNOWN,
    apply_direct_dm_cycle,
    decode_direct_dm,
    read_internal_move_register,
    register_code_by_name,
)


READABLE = register_code_by_name(writable=False)
WRITABLE = register_code_by_name(writable=True)
READABLE_CODES = tuple(READABLE.values())
WRITABLE_CODES = tuple(WRITABLE.values())


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(code: int, address: int, write: bool) -> int:
    return (
        0x800000
        | (int(write) << 20)
        | ((code >> 4) << 18)
        | ((address & 0x3FFF) << 4)
        | (code & 0xF)
    )


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DirectDMSliceState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        ack: bool = False,
        read_data: ExactWord | object = UNKNOWN,
        setup: InternalMoveSetup | None = None,
        probe: int | None = None,
    ) -> None:
        nonlocal state
        if probe is None:
            probe = rng.choice(READABLE_CODES)
        result = apply_direct_dm_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            dm_ack=ack,
            dm_read_data=read_data,
            setup=setup,
        )
        action = decode_direct_dm(opcode)

        stimulus = 0
        for item, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (ack, 1),
            (0 if read_data is UNKNOWN else read_data.value, 16),
            (read_data is not UNKNOWN, 1),
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
            (action.write if action is not None else False, 1),
            (action.address if action is not None else 0, 14),
            (action.register_code if action is not None else 0, 6),
            (result.boundary_valid, 1),
            (result.accepted, 1),
            (result.instruction_complete, 1),
            (result.transaction_active, 1),
            (result.stalled, 1),
            (result.busy, 1),
            (result.invalid_opcode, 1),
            (False, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (result.dm_select, 1),
            (result.dm_read, 1),
            (result.dm_write, 1),
            (result.dm_address_known, 1),
            (result.dm_address, 14),
            (result.dm_write_data_known, 1),
            (result.dm_write_data, 16),
            (result.dreg_write, 1),
            (result.dreg_write_known, 1),
            (result.source_extension_provisional, 1),
            (result.pm_data_access, 1),
            (result.dm_access, 1),
            (result.count_stack_push, 1),
            (result.count_stack_push_value, 14),
        ):
            events = _append(events, item, width)

        # A same-clock completed write leaves execute asserted after the edge;
        # the single physical read port therefore continues to expose its
        # source selector. Pending writes switch the port back to the probe.
        post_probe = probe
        if (
            result.accepted
            and result.instruction_complete
            and action is not None
            and action.write
        ):
            post_probe = action.register_code
        probe_value, _ = read_internal_move_register(
            result.state.registers,
            post_probe,
        )
        registers = result.state.registers
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
            probe_valid = False
        else:
            add_optional(probe_value.value, 16)
            probe_valid = True
        post = _append(post, probe_valid, 1)
        post_mask = _append(post_mask, 1, 1)
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
            f"{stimulus:019x} {events:023x} {post:019x} {post_mask:019x}"
        )
        state = result.state

    emit(reset=True)
    for name, code in WRITABLE.items():
        emit(setup=InternalMoveSetup(code, (code * 0x101) & 0xFFFF))
    for code in READABLE_CODES:
        emit(execute=True, opcode=_opcode(code, code, True), ack=True)
    for code in WRITABLE_CODES:
        emit(
            execute=True,
            opcode=_opcode(code, 0x3FFF - code, False),
            ack=True,
            read_data=ExactWord(16, 0x8000 | code),
        )
    emit(
        execute=True,
        opcode=_opcode(READABLE["ASTAT"], 0x1234, True),
        ack=False,
    )
    emit(ack=False)
    emit(ack=True)
    emit(
        execute=True,
        opcode=_opcode(WRITABLE["CNTR"], 0x2345, False),
        ack=False,
    )
    emit(ack=False, read_data=ExactWord(16, 1))
    emit(ack=True, read_data=ExactWord(16, 7))
    emit(execute=True, opcode=_opcode(0x3F, 0, True), ack=True)
    emit(reset=True)

    for _ in range(random_count):
        if state.pending is not None:
            choice = rng.randrange(12)
            if choice == 0:
                emit(
                    execute=True,
                    opcode=_opcode(
                        rng.randrange(64),
                        rng.randrange(1 << 14),
                        bool(rng.randrange(2)),
                    ),
                    ack=False,
                )
            elif choice == 1:
                emit(
                    setup=InternalMoveSetup(
                        rng.choice(WRITABLE_CODES),
                        rng.randrange(1 << 16),
                    ),
                    ack=False,
                )
            elif choice == 2:
                emit(reset=True, ack=bool(rng.randrange(2)))
            else:
                known = rng.randrange(5) != 0
                emit(
                    ack=rng.randrange(4) == 0,
                    read_data=(
                        ExactWord(16, rng.randrange(1 << 16))
                        if known else UNKNOWN
                    ),
                )
            continue

        choice = rng.randrange(28)
        if choice < 14:
            write = bool(rng.randrange(2))
            choices = READABLE_CODES if write else WRITABLE_CODES
            known = rng.randrange(5) != 0
            emit(
                execute=True,
                opcode=_opcode(
                    rng.choice(choices),
                    rng.randrange(1 << 14),
                    write,
                ),
                ack=rng.randrange(3) == 0,
                read_data=(
                    ExactWord(16, rng.randrange(1 << 16))
                    if known else UNKNOWN
                ),
            )
        elif choice < 20:
            emit(
                setup=InternalMoveSetup(
                    rng.choice(WRITABLE_CODES),
                    rng.randrange(1 << 16),
                )
            )
        elif choice == 20:
            emit(reset=True)
        elif choice == 21:
            emit(execute=True, opcode=rng.randrange(0x800000), ack=True)
        elif choice == 22:
            emit(
                execute=True,
                opcode=_opcode(0x3F, rng.randrange(1 << 14), True),
                ack=True,
            )
        elif choice == 23:
            emit(
                execute=True,
                opcode=_opcode(0x32, rng.randrange(1 << 14), False),
                ack=True,
            )
        elif choice == 24:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.choice(READABLE_CODES),
                    rng.randrange(1 << 14),
                    True,
                ),
                setup=InternalMoveSetup(
                    rng.choice(WRITABLE_CODES),
                    rng.randrange(1 << 16),
                ),
                ack=True,
            )
        else:
            emit()

    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda text: int(text, 0), default=0x210003)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 3 state vectors seed={args.seed:#x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
