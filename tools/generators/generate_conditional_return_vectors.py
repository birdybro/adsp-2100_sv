#!/usr/bin/env python3
"""Generate deterministic bounded original Type 20 model/RTL vectors."""

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
    ConditionalReturnState,
    ExactWord,
    UNKNOWN,
    apply_conditional_return_cycle,
    evaluate_if_condition,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(interrupt_return: bool, condition: int) -> int:
    return 0x0A0000 | (int(interrupt_return) << 4) | condition


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
    state = ConditionalReturnState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup_pc: int | None = None,
        setup_astat: ExactWord | None = None,
        setup_mstat: ExactWord | None = None,
        setup_imask: ExactWord | None = None,
        setup_counter: int | None = None,
        setup_pc_stack_push: int | None = None,
        setup_status_stack_push: ExactWord | None = None,
    ) -> None:
        nonlocal state
        result = apply_conditional_return_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup_pc=setup_pc,
            setup_astat=setup_astat,
            setup_mstat=setup_mstat,
            setup_imask=setup_imask,
            setup_counter=setup_counter,
            setup_pc_stack_push=setup_pc_stack_push,
            setup_status_stack_push=setup_status_stack_push,
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
            (setup_mstat is not None, 1),
            (0 if setup_mstat is None else setup_mstat.value, 4),
            (setup_imask is not None, 1),
            (0 if setup_imask is None else setup_imask.value, 4),
            (setup_counter is not None, 1),
            (0 if setup_counter is None else setup_counter, 14),
            (setup_pc_stack_push is not None, 1),
            (0 if setup_pc_stack_push is None else setup_pc_stack_push, 14),
            (setup_status_stack_push is not None, 1),
            (
                0
                if setup_status_stack_push is None
                else setup_status_stack_push.value,
                16,
            ),
        ):
            stimulus = _append(stimulus, value, width)

        action = result.action
        events = 0
        for value, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (False if action is None else action.interrupt_return, 1),
            (0 if action is None else action.condition, 4),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (result.internal_conflict, 1),
            (result.invalid_condition_state, 1),
            (result.invalid_return_context, 1),
            (result.condition_known, 1),
            (result.condition_true, 1),
            (result.pc_write, 1),
            (result.explicit_transfer, 1),
            (result.pc_stack_pop, 1),
            (result.pc_stack_pop_valid, 1),
            (result.status_stack_pop, 1),
            (result.status_stack_pop_valid, 1),
            (result.status_restored, 1),
            (result.count_stack_push, 1),
            (result.counter_test, 1),
            (result.counter_decremented, 1),
            (result.counter_restored, 1),
            (result.pm_data_access, 1),
            (result.dm_access, 1),
        ):
            events = _append(events, value, width)

        astat_valid = result.state.status.astat.is_fully_known
        astat = (
            result.state.status.astat.to_word().value if astat_valid else 0
        )
        imask = result.state.status.imask
        imask_value = 0 if imask is UNKNOWN else imask.value
        counter_valid = result.state.counter.value is not None
        counter = result.state.counter.value if counter_valid else 0
        pc_top_valid = bool(result.state.stacks.pc_entries)
        pc_top = result.state.stacks.pc_entries[-1] if pc_top_valid else 0
        status_top_valid = bool(result.state.status_stack.entries)
        status_top = (
            result.state.status_stack.entries[-1].to_word().value
            if status_top_valid
            else 0
        )
        count_top_valid = bool(result.state.stacks.count_entries)
        count_top = (
            result.state.stacks.count_entries[-1] if count_top_valid else 0
        )
        post_state = 0
        for value, width in (
            (result.state.pc, 14),
            (astat_valid, 1),
            (astat, 8),
            (result.state.status.mstat.value, 4),
            (imask_value, 4),
            (counter_valid, 1),
            (counter, 14),
            (pc_top_valid, 1),
            (pc_top, 14),
            (len(result.state.stacks.pc_entries), 5),
            (result.state.stacks.pc_overflow, 1),
            (status_top_valid, 1),
            (status_top, 16),
            (len(result.state.status_stack.entries), 3),
            (result.state.status_stack.overflow, 1),
            (count_top_valid, 1),
            (count_top, 14),
            (len(result.state.stacks.count_entries), 3),
            (result.state.stacks.count_overflow, 1),
            (result.state.sstat, 8),
        ):
            post_state = _append(post_state, value, width)
        lines.append(f"{stimulus:027x} {events:07x} {post_state:029x}")
        state = result.state

    emit(reset=True)
    emit(setup_astat=ExactWord(8, 0x5D))
    emit(setup_mstat=ExactWord(4, 0x6))
    emit(setup_imask=ExactWord(4, 0x9))

    for interrupt_return in (False, True):
        for condition in range(16):
            emit(setup_pc_stack_push=(0x1000 + condition))
            if interrupt_return:
                emit(
                    setup_status_stack_push=ExactWord(
                        16,
                        (condition << 8) | 0x5A,
                    )
                )
            if condition == 14:
                emit(setup_counter=2)
            emit(execute=True, opcode=_opcode(interrupt_return, condition))

    outcomes = [_condition_outcomes(condition) for condition in range(14)]
    for interrupt_return in (False, True):
        for condition in range(14):
            for expected, astat in outcomes[condition].items():
                emit(setup_astat=ExactWord(8, astat))
                if expected:
                    emit(setup_pc_stack_push=0x2345)
                    if interrupt_return:
                        emit(setup_status_stack_push=ExactWord(16, 0xA5BC))
                emit(execute=True, opcode=_opcode(interrupt_return, condition))

    emit(reset=True)
    emit(setup_astat=ExactWord(8, 0))
    emit(setup_pc=0x3FFF)
    emit(execute=True, opcode=_opcode(False, 0))
    emit(execute=True, opcode=_opcode(True, 0))
    emit(execute=True, opcode=_opcode(False, 15))
    emit(setup_pc_stack_push=0x1111)
    emit(execute=True, opcode=_opcode(True, 15))
    emit(reset=True)
    emit(setup_status_stack_push=ExactWord(16, 0x1234))
    emit(execute=True, opcode=_opcode(True, 15))
    emit(setup_pc_stack_push=0x2222)
    emit(execute=True, opcode=_opcode(True, 15))

    for index in range(random_count):
        choice = rng.randrange(18)
        if choice < 5:
            emit(
                execute=True,
                opcode=_opcode(bool(rng.randrange(2)), rng.randrange(16)),
            )
        elif choice == 5:
            emit(setup_pc=rng.randrange(1 << 14))
        elif choice == 6:
            emit(setup_astat=ExactWord(8, rng.randrange(256)))
        elif choice == 7:
            emit(setup_mstat=ExactWord(4, rng.randrange(16)))
        elif choice == 8:
            emit(setup_imask=ExactWord(4, rng.randrange(16)))
        elif choice == 9:
            emit(setup_counter=rng.randrange(1 << 14))
        elif choice == 10:
            emit(setup_pc_stack_push=rng.randrange(1 << 14))
        elif choice == 11:
            emit(setup_status_stack_push=ExactWord(16, rng.randrange(1 << 16)))
        elif choice == 12:
            emit(execute=True, opcode=0)
        elif choice == 13:
            emit(execute=True, opcode=0x0A0020)
        elif choice == 14:
            emit(
                execute=True,
                opcode=_opcode(False, 15),
                setup_pc_stack_push=1,
            )
        elif choice == 15:
            emit(setup_pc=1, setup_astat=ExactWord(8, 0))
        elif choice == 16:
            emit(reset=True)
        else:
            emit()

    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x210020
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 20 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
