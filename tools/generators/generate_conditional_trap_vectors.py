#!/usr/bin/env python3
"""Generate deterministic phase-aware original Type 22 model/RTL vectors."""

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
    ConditionalTrapState,
    ExactWord,
    LogicalPhase,
    apply_conditional_trap_cycle,
    evaluate_if_condition,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(condition: int) -> int:
    return 0x080000 | condition


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
    state = ConditionalTrapState()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        phase: LogicalPhase | int = LogicalPhase.STATE_1,
        phase_advance: bool = True,
        execute: bool = False,
        opcode: int = 0,
        halt_recognized: bool = False,
        setup_pc: int | None = None,
        setup_astat: ExactWord | None = None,
        setup_counter: int | None = None,
    ) -> None:
        nonlocal state
        result = apply_conditional_trap_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=phase_advance,
            execute=execute,
            opcode=opcode,
            halt_recognized=halt_recognized,
            setup_pc=setup_pc,
            setup_astat=setup_astat,
            setup_counter=setup_counter,
        )
        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(phase), 3),
            (phase_advance, 1),
            (execute, 1),
            (opcode, 24),
            (halt_recognized, 1),
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
            (0 if action is None else action.condition, 4),
            (result.instruction_accepted, 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.invalid_condition_state, 1),
            (result.integration_conflict, 1),
            (result.phase_mismatch, 1),
            (result.condition_known, 1),
            (result.condition_true, 1),
            (result.pc_write, 1),
            (result.trap_event, 1),
            (result.resume_event, 1),
            (result.counter_test, 1),
            (result.counter_decremented, 1),
            (result.pm_data_access, 1),
            (result.dm_access, 1),
        ):
            events = _append(events, value, width)

        astat_valid = result.state.astat.is_fully_known
        astat = result.state.astat.to_word().value if astat_valid else 0
        counter_valid = result.state.counter.value is not None
        counter = result.state.counter.value if counter_valid else 0
        post_state = 0
        for value, width in (
            (result.state.pc, 14),
            (astat_valid, 1),
            (astat, 8),
            (counter_valid, 1),
            (counter, 14),
            (result.state.pending, 1),
            (result.state.pending_taken, 1),
            (result.state.trap_asserted, 1),
            (result.state.halted, 1),
            (result.state.halt_handoff, 1),
            (result.phase_hold, 1),
            (result.state.pc, 14),
            (result.state.halted, 1),
        ):
            post_state = _append(post_state, value, width)
        lines.append(f"{stimulus:018x} {events:06x} {post_state:015x}")
        state = result.state

    def complete_pending(*, stall_state_7: bool = False) -> None:
        if stall_state_7:
            emit(phase=LogicalPhase.STATE_7, phase_advance=False)
        emit(phase=LogicalPhase.STATE_7)
        if state.trap_asserted:
            emit(phase=LogicalPhase.STATE_8)
            emit(phase=LogicalPhase.STATE_8, halt_recognized=True)
            emit(phase=LogicalPhase.STATE_8, halt_recognized=True)
            emit(phase=LogicalPhase.STATE_8, halt_recognized=False)

    emit(reset=True)
    emit(setup_pc=0x3FFE)
    emit(setup_astat=ExactWord(8, 0x5D))
    emit(setup_counter=2)

    outcomes = [_condition_outcomes(condition) for condition in range(14)]
    for condition in range(14):
        for expected, astat in outcomes[condition].items():
            emit(setup_astat=ExactWord(8, astat))
            emit(execute=True, opcode=_opcode(condition))
            if state.pending_taken != expected:
                raise AssertionError("condition outcome mismatch")
            complete_pending(stall_state_7=(condition == 0 and expected))

    for counter in (1, 2):
        emit(setup_counter=counter)
        emit(execute=True, opcode=_opcode(14))
        complete_pending()
    emit(execute=True, opcode=_opcode(15))
    complete_pending()

    emit(reset=True)
    emit(execute=True, opcode=_opcode(0))
    emit(phase=LogicalPhase.STATE_2, execute=True, opcode=_opcode(15))
    emit(execute=True, opcode=0)
    emit(execute=True, opcode=_opcode(15), setup_pc=1)
    emit(setup_pc=1, setup_astat=ExactWord(8, 2))

    for _ in range(random_count):
        if state.trap_asserted:
            emit(
                phase=LogicalPhase.STATE_8,
                halt_recognized=bool(rng.randrange(3) == 0),
            )
            continue
        if state.halt_handoff:
            emit(
                phase=LogicalPhase.STATE_8,
                halt_recognized=bool(rng.randrange(3) != 0),
            )
            continue
        if state.pending:
            phase = rng.randrange(1, 7)
            emit(
                phase=phase,
                phase_advance=bool(phase != LogicalPhase.STATE_7 or rng.randrange(3)),
            )
            continue

        choice = rng.randrange(14)
        if choice < 5:
            emit(execute=True, opcode=_opcode(rng.randrange(16)))
        elif choice == 5:
            emit(setup_pc=rng.randrange(1 << 14))
        elif choice == 6:
            emit(setup_astat=ExactWord(8, rng.randrange(256)))
        elif choice == 7:
            emit(setup_counter=rng.randrange(1 << 14))
        elif choice == 8:
            emit(execute=True, opcode=0)
        elif choice == 9:
            emit(phase=rng.randrange(1, 8), execute=True, opcode=_opcode(15))
        elif choice == 10:
            emit(execute=True, opcode=_opcode(15), setup_pc=1)
        elif choice == 11:
            emit(setup_pc=1, setup_astat=ExactWord(8, 0))
        elif choice == 12:
            emit(reset=True)
        else:
            emit(phase=rng.randrange(8), phase_advance=bool(rng.randrange(2)))

    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x210022
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 22 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
