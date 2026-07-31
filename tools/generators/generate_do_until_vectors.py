#!/usr/bin/env python3
"""Generate deterministic bounded original Type 11 model/RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DoUntilState,
    apply_do_until_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(end_address: int, termination: int) -> int:
    return 0x140000 | (end_address << 4) | termination


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DoUntilState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup_pc: int | None = None,
        setup_counter: int | None = None,
    ) -> None:
        nonlocal state
        result = apply_do_until_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup_pc=setup_pc,
            setup_counter=setup_counter,
        )
        stimulus = 0
        for value, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (setup_pc is not None, 1),
            (0 if setup_pc is None else setup_pc, 14),
            (setup_counter is not None, 1),
            (0 if setup_counter is None else setup_counter, 14),
        ):
            stimulus = _append(stimulus, value, width)

        action = result.action
        events = 0
        for value, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (0 if action is None else action.end_address, 14),
            (0 if action is None else action.termination, 4),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (result.invalid_loop_context, 1),
            (result.unsupported_do_at_loop_end, 1),
            (result.unsupported_nested_same_end, 1),
            (False, 1),
            (result.pc_write, 1),
            (result.pc_stack_push, 1),
            (result.pc_stack_push_accepted, 1),
            (result.pc_stack_overflow_event, 1),
            (result.loop_stack_push, 1),
            (result.loop_stack_push_accepted, 1),
            (result.loop_stack_overflow_event, 1),
            (result.count_stack_push, 1),
            (result.pm_data_access, 1),
            (result.dm_access, 1),
        ):
            events = _append(events, value, width)

        counter_valid = result.state.counter.value is not None
        counter = result.state.counter.value if counter_valid else 0
        pc_top_valid = bool(result.state.stacks.pc_entries)
        pc_top = result.state.stacks.pc_entries[-1] if pc_top_valid else 0
        loop_top_valid = bool(result.state.stacks.loop_entries)
        loop_top = result.state.stacks.loop_entries[-1] if loop_top_valid else 0
        count_top_valid = bool(result.state.stacks.count_entries)
        count_top = result.state.stacks.count_entries[-1] if count_top_valid else 0
        post_state = 0
        for value, width in (
            (result.state.pc, 14),
            (counter_valid, 1),
            (counter, 14),
            (pc_top_valid, 1),
            (pc_top, 14),
            (len(result.state.stacks.pc_entries), 5),
            (result.state.stacks.pc_overflow, 1),
            (loop_top_valid, 1),
            (loop_top, 18),
            (len(result.state.stacks.loop_entries), 3),
            (result.state.stacks.loop_overflow, 1),
            (count_top_valid, 1),
            (count_top, 14),
            (len(result.state.stacks.count_entries), 3),
            (result.state.stacks.count_overflow, 1),
            (result.state.stacks.sstat_fragment, 8),
        ):
            post_state = _append(post_state, value, width)
        lines.append(f"{stimulus:014x} {events:010x} {post_state:025x}")
        state = result.state

    # Directed nesting, documented same-end rejection, OQ-018, CE context,
    # overflow, invalid opcode, and integration-conflict coverage.
    emit(reset=True)
    emit(execute=True, opcode=_opcode(12, 15))
    emit(execute=True, opcode=_opcode(10, 1))
    emit(execute=True, opcode=_opcode(10, 2))
    emit(setup_pc=10)
    emit(execute=True, opcode=_opcode(9, 3))
    emit(reset=True)
    emit(execute=True, opcode=_opcode(12, 14))
    emit(execute=True, opcode=_opcode(10, 15))
    emit(setup_counter=3)
    emit(execute=True, opcode=_opcode(10, 15))
    emit(reset=True)
    for address in (12, 11, 10, 9, 8):
        emit(execute=True, opcode=_opcode(address, 15))
    emit(execute=True, opcode=0)
    emit(execute=True, opcode=_opcode(7, 15), setup_pc=7)
    emit(setup_pc=7, setup_counter=2)

    execution_count = 0
    for end_address in range(1 << 14):
        for termination in range(16):
            emit(reset=True)
            emit(execute=True, opcode=_opcode(end_address, termination))
            execution_count += 1
    if execution_count != 262_144:
        raise AssertionError(f"unexpected execution count {execution_count}")

    for _ in range(random_count):
        choice = rng.randrange(10)
        if choice < 5:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.randrange(1 << 14),
                    rng.randrange(16),
                ),
            )
        elif choice == 5:
            emit(reset=True)
        elif choice == 6:
            emit(setup_pc=rng.randrange(1 << 14))
        elif choice == 7:
            emit(setup_counter=rng.randrange(1 << 14))
        elif choice == 8:
            emit(execute=True, opcode=0)
        else:
            emit(
                execute=True,
                opcode=_opcode(rng.randrange(1 << 14), rng.randrange(16)),
                setup_pc=rng.randrange(1 << 14),
            )

    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=30_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210011)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 11 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
