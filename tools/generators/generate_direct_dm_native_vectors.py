#!/usr/bin/env python3
"""Generate deterministic Type 3/native-DM model-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DirectDMNativeState,
    ExactWord,
    InternalMoveSetup,
    LogicalPhase,
    UNKNOWN,
    apply_direct_dm_native_cycle,
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
    state = DirectDMNativeState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        phase: LogicalPhase = LogicalPhase.STATE_1,
        advance: bool = True,
        relinquished: bool = False,
        execute: bool = False,
        opcode: int = 0,
        ack: bool = True,
        read_data: ExactWord | object = UNKNOWN,
        setup: InternalMoveSetup | None = None,
        probe: int | None = None,
    ) -> None:
        nonlocal state
        if probe is None:
            probe = rng.choice(READABLE_CODES)
        result = apply_direct_dm_native_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            bus_relinquished=relinquished,
            execute=execute,
            opcode=opcode,
            dm_ack=ack,
            dmd_read_data=read_data,
            setup=setup,
        )
        action = decode_direct_dm(opcode)

        stimulus = 0
        for item, width in (
            (reset, 1),
            (int(phase), 3),
            (advance, 1),
            (relinquished, 1),
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

        core = result.core
        bus = result.bus
        events = 0
        for item, width in (
            (result.issue_boundary, 1),
            (result.phase_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (core.class_valid, 1),
            (core.action_valid, 1),
            (core.invalid_subencoding, 1),
            (action.write if action is not None else False, 1),
            (action.address if action is not None else 0, 14),
            (action.register_code if action is not None else 0, 6),
            (core.boundary_valid, 1),
            (core.accepted, 1),
            (core.instruction_complete, 1),
            (core.transaction_active, 1),
            (core.stalled, 1),
            (core.busy, 1),
            (core.invalid_opcode, 1),
            (False, 1),
            (False, 1),
            (core.source_extension_provisional, 1),
            (core.dreg_write, 1),
            (core.dreg_write_known, 1),
            (core.count_stack_push, 1),
            (core.count_stack_push_value, 14),
            (bus.request_accepted, 1),
            (bus.dmack_sample_event, 1),
            (bus.dmack_accepted, 1),
            (bus.wait_extension_event, 1),
            (bus.completion_event, 1),
            (bus.read_sample_event, 1),
            (bus.transaction_active, 1),
            (bus.waiting, 1),
            (bus.address_output_enable, 1),
            (bus.control_output_enable, 1),
            (bus.data_output_enable, 1),
            (bus.address, 14),
            (bus.address_known, 1),
            (bus.dms_n, 1),
            (bus.dmrd_n, 1),
            (bus.dmwr_n, 1),
            (bus.write_data, 16),
            (bus.write_data_known, 1),
        ):
            events = _append(events, item, width)

        registers = result.state.core.registers
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
            f"{stimulus:020x} {events:026x} {post:019x} {post_mask:019x}"
        )
        state = result.state

    emit(reset=True)
    for register, code in WRITABLE.items():
        emit(
            phase=LogicalPhase.STATE_8,
            setup=InternalMoveSetup(code, (code * 0x101) & 0xFFFF),
        )
    for write, code in ((True, READABLE["AX0"]), (False, WRITABLE["AY0"])):
        emit(
            phase=LogicalPhase.STATE_8,
            execute=True,
            opcode=_opcode(code, 0x1234, write),
        )
        for phase in (
            LogicalPhase.STATE_1,
            LogicalPhase.STATE_2,
            LogicalPhase.STATE_3,
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
            LogicalPhase.STATE_7,
        ):
            emit(
                phase=phase,
                ack=True,
                read_data=ExactWord(16, 0xCAFE),
            )
    emit(
        phase=LogicalPhase.STATE_8,
        execute=True,
        opcode=_opcode(WRITABLE["MR1"], 0x2345, False),
    )
    emit(phase=LogicalPhase.STATE_6, ack=False)
    for phase in LogicalPhase:
        emit(phase=phase, ack=True, read_data=ExactWord(16, 0xAAAA))
    emit(phase=LogicalPhase.STATE_6, ack=True)
    emit(
        phase=LogicalPhase.STATE_7,
        read_data=ExactWord(16, 0x8001),
    )
    emit(reset=True, phase=LogicalPhase.STATE_4)

    phase_values = tuple(LogicalPhase)
    for _ in range(random_count):
        phase = rng.choice(phase_values)
        advance = rng.randrange(8) != 0
        relinquished = rng.randrange(32) == 0
        known = rng.randrange(5) != 0
        read_data = (
            ExactWord(16, rng.randrange(1 << 16)) if known else UNKNOWN
        )
        if state.core.pending is not None or state.bus.active:
            choice = rng.randrange(16)
            if choice == 0:
                emit(
                    phase=phase,
                    advance=advance,
                    relinquished=relinquished,
                    execute=True,
                    opcode=_opcode(
                        rng.choice(READABLE_CODES),
                        rng.randrange(1 << 14),
                        True,
                    ),
                    ack=bool(rng.randrange(2)),
                    read_data=read_data,
                )
            elif choice == 1:
                emit(
                    phase=phase,
                    advance=advance,
                    setup=InternalMoveSetup(
                        rng.choice(WRITABLE_CODES),
                        rng.randrange(1 << 16),
                    ),
                    ack=bool(rng.randrange(2)),
                    read_data=read_data,
                )
            elif choice == 2:
                emit(reset=True, phase=phase)
            else:
                emit(
                    phase=phase,
                    advance=advance,
                    relinquished=relinquished,
                    ack=rng.randrange(3) != 0,
                    read_data=read_data,
                )
            continue

        choice = rng.randrange(28)
        if choice < 12:
            write = bool(rng.randrange(2))
            codes = READABLE_CODES if write else WRITABLE_CODES
            emit(
                phase=phase,
                advance=advance,
                relinquished=relinquished,
                execute=True,
                opcode=_opcode(
                    rng.choice(codes),
                    rng.randrange(1 << 14),
                    write,
                ),
                ack=bool(rng.randrange(2)),
                read_data=read_data,
            )
        elif choice < 18:
            emit(
                phase=phase,
                advance=advance,
                relinquished=relinquished,
                setup=InternalMoveSetup(
                    rng.choice(WRITABLE_CODES),
                    rng.randrange(1 << 16),
                ),
            )
        elif choice == 18:
            emit(reset=True, phase=phase)
        elif choice == 19:
            emit(
                phase=phase,
                advance=advance,
                execute=True,
                opcode=_opcode(0x3F, rng.randrange(1 << 14), True),
            )
        else:
            emit(
                phase=phase,
                advance=advance,
                relinquished=relinquished,
                ack=bool(rng.randrange(2)),
                read_data=read_data,
            )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda text: int(text, 0), default=0x2103DA)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 3/native-DM clocks seed={args.seed:#x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
