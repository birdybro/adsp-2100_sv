#!/usr/bin/env python3
"""Generate deterministic bounded original Type 10 model/RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ConditionInputs,
    DirectJumpState,
    ExactWord,
    apply_direct_jump_cycle,
    evaluate_if_condition,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(call: bool, address: int, condition: int) -> int:
    return 0x180000 | (int(call) << 18) | (address << 4) | condition


def _condition_outcomes(condition: int) -> dict[bool, int]:
    outcomes: dict[bool, int] = {}
    for astat in range(256):
        value = evaluate_if_condition(
            condition,
            ConditionInputs(
                az=bool(astat & 0x01),
                an=bool(astat & 0x02),
                av=bool(astat & 0x04),
                ac=bool(astat & 0x08),
                as_flag=bool(astat & 0x10),
                mv=bool(astat & 0x40),
            ),
        )
        outcomes.setdefault(value, astat)
    return outcomes


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DirectJumpState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup_pc: int | None = None,
        setup_astat: ExactWord | None = None,
        setup_counter: int | None = None,
    ) -> None:
        nonlocal state
        result = apply_direct_jump_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup_pc=setup_pc,
            setup_astat=setup_astat,
            setup_counter=setup_counter,
        )
        stimulus = 0
        for value, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (setup_pc is not None, 1),
            (0 if setup_pc is None else setup_pc, 14),
            (setup_astat is not None, 1),
            (0 if setup_astat is None else setup_astat.value, 8),
            (setup_counter is not None, 1),
            (0 if setup_counter is None else setup_counter, 14),
        ):
            stimulus = _append(stimulus, value, width)

        action = result.action
        events = 0
        for value, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.unsupported_call_ce, 1),
            (False if action is None else action.call, 1),
            (0 if action is None else action.address, 14),
            (0 if action is None else action.condition, 4),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (result.invalid_condition_state, 1),
            (result.condition_known, 1),
            (result.condition_true, 1),
            (result.pc_write, 1),
            (result.explicit_transfer, 1),
            (result.pc_stack_push, 1),
            (result.pc_stack_push_accepted, 1),
            (result.counter_test, 1),
            (result.counter_decremented, 1),
            (result.counter_restored, 1),
            (result.counter_empty_invalidated, 1),
            (result.count_stack_push, 1),
            (result.count_stack_pop, 1),
            (False, 1),
            (False, 1),
            (False, 1),
        ):
            events = _append(events, value, width)

        astat_valid = result.state.astat.is_fully_known
        astat = result.state.astat.to_word().value if astat_valid else 0
        counter_valid = result.state.counter.value is not None
        counter = result.state.counter.value if counter_valid else 0
        pc_top_valid = bool(result.state.stacks.pc_entries)
        pc_top = result.state.stacks.pc_entries[-1] if pc_top_valid else 0
        count_top_valid = bool(result.state.stacks.count_entries)
        count_top = result.state.stacks.count_entries[-1] if count_top_valid else 0
        post_state = 0
        for value, width in (
            (result.state.pc, 14),
            (astat_valid, 1),
            (astat, 8),
            (counter_valid, 1),
            (counter, 14),
            (pc_top_valid, 1),
            (pc_top, 14),
            (count_top_valid, 1),
            (count_top, 14),
            (len(result.state.stacks.pc_entries), 5),
            (len(result.state.stacks.count_entries), 3),
            (result.state.stacks.pc_overflow, 1),
            (result.state.stacks.count_overflow, 1),
            (result.state.stacks.sstat_fragment, 8),
        ):
            post_state = _append(post_state, value, width)
        lines.append(f"{stimulus:017x} {events:011x} {post_state:022x}")
        state = result.state

    emit(reset=True)
    emit(setup_astat=ExactWord(8, 0x5D))
    execution_count = 0
    for call in (False, True):
        for address in range(1 << 14):
            for condition in range(16):
                if call and condition == 14:
                    continue
                if condition == 14:
                    emit(setup_counter=2)
                emit(execute=True, opcode=_opcode(call, address, condition))
                execution_count += 1
    if execution_count != 507_904:
        raise AssertionError(f"unexpected supported execution count {execution_count}")

    outcomes = [_condition_outcomes(condition) for condition in range(14)]
    for call in (False, True):
        for condition in range(14):
            for astat in outcomes[condition].values():
                emit(setup_astat=ExactWord(8, astat))
                emit(execute=True, opcode=_opcode(call, 0x2345, condition))
    for counter in (1, 2):
        emit(setup_counter=counter)
        emit(execute=True, opcode=_opcode(False, 0x2345, 14))

    emit(reset=True)
    emit(setup_counter=7)
    emit(setup_counter=1)
    emit(execute=True, opcode=_opcode(False, 0x1234, 14))
    emit(setup_astat=ExactWord(8, 0x55))

    for _ in range(random_count):
        choice = rng.randrange(12)
        if choice < 6:
            emit(
                execute=True,
                opcode=_opcode(
                    bool(rng.randrange(2)),
                    rng.randrange(1 << 14),
                    rng.randrange(16),
                ),
            )
        elif choice == 6:
            emit(setup_pc=rng.randrange(1 << 14))
        elif choice == 7:
            emit(setup_astat=ExactWord(8, rng.randrange(256)))
        elif choice == 8:
            emit(setup_counter=rng.randrange(1 << 14))
        elif choice == 9:
            emit(execute=True, opcode=0)
        elif choice == 10:
            emit(
                execute=True,
                opcode=_opcode(False, rng.randrange(1 << 14), 15),
                setup_pc=rng.randrange(1 << 14),
            )
        else:
            emit(
                setup_pc=rng.randrange(1 << 14),
                setup_astat=ExactWord(8, rng.randrange(256)),
            )

    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=30_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210010)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 10 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
