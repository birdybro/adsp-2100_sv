"""Instruction-boundary flow selection for the original ADSP-2100."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


PROGRAM_ADDRESS_MASK = 0x3FFF


class ExplicitFlow(IntEnum):
    """Explicit control-transfer class presented to the flow selector."""

    NONE = 0
    JUMP = 1
    CALL = 2
    RETURN = 3


@dataclass(frozen=True)
class SequencerFlowResult:
    next_pc: int
    pc_stack_push: bool
    pc_stack_push_value: int
    pc_stack_pop: bool
    loop_stack_pop: bool
    count_stack_pop: bool
    loop_counter_test: bool
    loop_back: bool
    loop_exit: bool
    explicit_transfer: bool


def _require_address(value: int, name: str) -> None:
    if not 0 <= value <= PROGRAM_ADDRESS_MASK:
        raise ValueError(f"{name} must fit 14 bits")


def select_sequencer_flow(
    *,
    pc: int,
    explicit_flow: ExplicitFlow | int,
    explicit_taken: bool,
    explicit_target: int,
    loop_active: bool,
    loop_end: int,
    loop_start: int,
    loop_termination_true: bool,
    loop_uses_counter: bool,
) -> SequencerFlowResult:
    """Select the next PC and requested stack actions.

    This is an instruction-boundary function. Interrupt recognition, DO UNTIL
    setup, stack storage, counter post-decrement arithmetic, fetch/cache
    overlap, and bus phases belong to separate stateful mechanisms.
    """

    for value, name in (
        (pc, "pc"),
        (explicit_target, "explicit_target"),
        (loop_end, "loop_end"),
        (loop_start, "loop_start"),
    ):
        _require_address(value, name)
    try:
        flow = ExplicitFlow(explicit_flow)
    except ValueError as error:
        raise ValueError("explicit_flow must be a defined ExplicitFlow") from error

    sequential_pc = (pc + 1) & PROGRAM_ADDRESS_MASK
    transfer = bool(explicit_taken and flow is not ExplicitFlow.NONE)

    if transfer:
        return SequencerFlowResult(
            next_pc=explicit_target,
            pc_stack_push=flow is ExplicitFlow.CALL,
            pc_stack_push_value=sequential_pc,
            pc_stack_pop=flow is ExplicitFlow.RETURN,
            loop_stack_pop=False,
            count_stack_pop=False,
            loop_counter_test=False,
            loop_back=False,
            loop_exit=False,
            explicit_transfer=True,
        )

    at_loop_end = bool(loop_active and pc == loop_end)
    if not at_loop_end:
        return SequencerFlowResult(
            next_pc=sequential_pc,
            pc_stack_push=False,
            pc_stack_push_value=sequential_pc,
            pc_stack_pop=False,
            loop_stack_pop=False,
            count_stack_pop=False,
            loop_counter_test=False,
            loop_back=False,
            loop_exit=False,
            explicit_transfer=False,
        )

    counter_test = bool(loop_uses_counter)
    if loop_termination_true:
        return SequencerFlowResult(
            next_pc=sequential_pc,
            pc_stack_push=False,
            pc_stack_push_value=sequential_pc,
            pc_stack_pop=True,
            loop_stack_pop=True,
            count_stack_pop=counter_test,
            loop_counter_test=counter_test,
            loop_back=False,
            loop_exit=True,
            explicit_transfer=False,
        )

    return SequencerFlowResult(
        next_pc=loop_start,
        pc_stack_push=False,
        pc_stack_push_value=sequential_pc,
        pc_stack_pop=False,
        loop_stack_pop=False,
        count_stack_pop=False,
        loop_counter_test=counter_test,
        loop_back=True,
        loop_exit=False,
        explicit_transfer=False,
    )
