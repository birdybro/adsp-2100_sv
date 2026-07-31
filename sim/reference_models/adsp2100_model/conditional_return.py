"""Independent bounded original ADSP-2100 Type 20 execution model.

The model closes conditional RTS/RTI state changes outside active hardware
loops, interrupt recognition, and external fetch phases. Taken returns require
valid cycle-start stack context; empty pops remain fail-closed under OQ-013.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .counter import CounterInputs, CounterState, apply_counter_cycle
from .flow_condition import evaluate_flow_condition
from .model import ExactWord, UNKNOWN
from .sequencer import PROGRAM_ADDRESS_MASK
from .sequencer_stacks import (
    SequencerStacksInputs,
    SequencerStacksState,
    apply_sequencer_stacks_cycle,
)
from .status import (
    StatusCycleInputs,
    StatusRegisters,
    StatusStackEntry,
    apply_status_cycle,
)
from .status_stack import (
    StatusStackCycleInputs,
    StatusStackOperation,
    StatusStackState,
    apply_status_stack_cycle,
)


CONDITIONAL_RETURN_CLASS_MASK = 0xFFFFE0
CONDITIONAL_RETURN_CLASS_VALUE = 0x0A0000
RESET_PC = 0x0004


@dataclass(frozen=True)
class ConditionalReturnAction:
    interrupt_return: bool
    condition: int


def is_conditional_return_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & CONDITIONAL_RETURN_CLASS_MASK == CONDITIONAL_RETURN_CLASS_VALUE


def decode_conditional_return(opcode: int) -> ConditionalReturnAction | None:
    if not is_conditional_return_class(opcode):
        return None
    return ConditionalReturnAction(
        interrupt_return=bool((opcode >> 4) & 1),
        condition=opcode & 0xF,
    )


@dataclass(frozen=True)
class ConditionalReturnState:
    pc: int = RESET_PC
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    counter: CounterState = field(default_factory=CounterState)
    stacks: SequencerStacksState = field(default_factory=SequencerStacksState)
    status_stack: StatusStackState = field(default_factory=StatusStackState)

    def __post_init__(self) -> None:
        if not 0 <= self.pc <= PROGRAM_ADDRESS_MASK:
            raise ValueError("PC must fit 14 bits")

    @classmethod
    def reset(cls) -> "ConditionalReturnState":
        return cls()

    @property
    def sstat(self) -> int:
        return self.stacks.sstat_fragment | self.status_stack.sstat_fragment


@dataclass(frozen=True)
class ConditionalReturnCycleResult:
    state: ConditionalReturnState
    action: ConditionalReturnAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    internal_conflict: bool = False
    condition_known: bool = False
    condition_true: bool = False
    invalid_condition_state: bool = False
    invalid_return_context: bool = False
    pc_write: bool = False
    explicit_transfer: bool = False
    pc_stack_pop: bool = False
    pc_stack_pop_valid: bool = False
    status_stack_pop: bool = False
    status_stack_pop_valid: bool = False
    status_restored: bool = False
    count_stack_push: bool = False
    counter_test: bool = False
    counter_decremented: bool = False
    counter_restored: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def apply_conditional_return_cycle(
    state: ConditionalReturnState,
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
) -> ConditionalReturnCycleResult:
    """Apply one reset, deterministic setup, or bounded Type 20 cycle."""

    if setup_pc is not None and not 0 <= setup_pc <= PROGRAM_ADDRESS_MASK:
        raise ValueError("PC setup must fit 14 bits")
    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly 8 bits")
    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly 4 bits")
    if setup_imask is not None and setup_imask.width != 4:
        raise ValueError("IMASK setup must be exactly 4 bits")
    if setup_counter is not None and not 0 <= setup_counter <= PROGRAM_ADDRESS_MASK:
        raise ValueError("CNTR setup must fit 14 bits")
    if setup_pc_stack_push is not None and not 0 <= setup_pc_stack_push <= PROGRAM_ADDRESS_MASK:
        raise ValueError("PC-stack setup data must fit 14 bits")
    if setup_status_stack_push is not None and setup_status_stack_push.width != 16:
        raise ValueError("status-stack setup data must be exactly 16 bits")

    action = decode_conditional_return(opcode)
    class_valid = action is not None
    setup_count = sum(
        value is not None
        for value in (
            setup_pc,
            setup_astat,
            setup_mstat,
            setup_imask,
            setup_counter,
            setup_pc_stack_push,
            setup_status_stack_push,
        )
    )
    conflict = bool(
        not reset and ((execute and setup_count != 0) or setup_count > 1)
    )
    invalid = bool(not reset and execute and action is None)
    common = {
        "action": action,
        "class_valid": class_valid,
        "action_valid": class_valid,
    }

    if reset:
        return ConditionalReturnCycleResult(ConditionalReturnState.reset(), **common)
    if conflict or invalid:
        return ConditionalReturnCycleResult(
            state,
            invalid_opcode=invalid,
            integration_conflict=conflict,
            **common,
        )
    if setup_pc is not None:
        return ConditionalReturnCycleResult(replace(state, pc=setup_pc), **common)
    if setup_astat is not None or setup_mstat is not None or setup_imask is not None:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(
                astat_move=setup_astat,
                mstat_move=setup_mstat,
                imask_move=setup_imask,
            ),
        )
        return ConditionalReturnCycleResult(
            replace(state, status=status.state),
            internal_conflict=status.write_conflict,
            **common,
        )
    if setup_counter is not None:
        counter = apply_counter_cycle(
            state.counter,
            CounterInputs(load=True, load_value=setup_counter),
        )
        stacks = apply_sequencer_stacks_cycle(
            state.stacks,
            SequencerStacksInputs(
                count_push=counter.count_stack_push,
                count_push_value=counter.count_stack_push_value,
            ),
        )
        return ConditionalReturnCycleResult(
            replace(state, counter=counter.state, stacks=stacks.state),
            internal_conflict=counter.write_conflict or stacks.write_conflict,
            count_stack_push=counter.count_stack_push,
            **common,
        )
    if setup_pc_stack_push is not None:
        stacks = apply_sequencer_stacks_cycle(
            state.stacks,
            SequencerStacksInputs(
                pc_push=True,
                pc_push_value=setup_pc_stack_push,
            ),
        )
        return ConditionalReturnCycleResult(
            replace(state, stacks=stacks.state),
            internal_conflict=stacks.write_conflict,
            **common,
        )
    if setup_status_stack_push is not None:
        status_stack = apply_status_stack_cycle(
            state.status_stack,
            StatusStackCycleInputs(
                operation=StatusStackOperation.PUSH,
                push_entry=StatusStackEntry.from_word(setup_status_stack_push),
            ),
        )
        return ConditionalReturnCycleResult(
            replace(state, status_stack=status_stack.state),
            **common,
        )
    if not execute:
        return ConditionalReturnCycleResult(state, **common)

    assert action is not None
    condition = evaluate_flow_condition(
        action.condition,
        state.status.astat,
        state.counter,
    )
    if condition is UNKNOWN:
        return ConditionalReturnCycleResult(
            state,
            invalid_condition_state=True,
            **common,
        )

    taken = bool(condition)
    pc_top_valid = bool(state.stacks.pc_entries)
    status_top_valid = bool(state.status_stack.entries)
    invalid_context = bool(
        taken
        and (
            not pc_top_valid
            or (action.interrupt_return and not status_top_valid)
        )
    )
    if invalid_context:
        return ConditionalReturnCycleResult(
            state,
            condition_known=True,
            invalid_return_context=True,
            **common,
        )

    pc_pop = taken
    status_pop = taken and action.interrupt_return
    stacks = apply_sequencer_stacks_cycle(
        state.stacks,
        SequencerStacksInputs(pc_pop=pc_pop),
    )
    status_stack = apply_status_stack_cycle(
        state.status_stack,
        StatusStackCycleInputs(
            operation=(
                StatusStackOperation.POP
                if status_pop
                else StatusStackOperation.NO_CHANGE_ZERO
            ),
        ),
    )
    status = apply_status_cycle(
        state.status,
        StatusCycleInputs(status_restore=status_stack.pop_entry),
    )
    internal_conflict = stacks.write_conflict or status.write_conflict
    if internal_conflict:
        return ConditionalReturnCycleResult(
            state,
            condition_known=True,
            condition_true=taken,
            internal_conflict=True,
            **common,
        )

    next_pc = (
        stacks.pc_pop_value
        if taken
        else (state.pc + 1) & PROGRAM_ADDRESS_MASK
    )
    assert next_pc is not None
    next_state = ConditionalReturnState(
        pc=next_pc,
        status=status.state,
        counter=state.counter,
        stacks=stacks.state,
        status_stack=status_stack.state,
    )
    return ConditionalReturnCycleResult(
        state=next_state,
        boundary_valid=True,
        condition_known=True,
        condition_true=taken,
        pc_write=True,
        explicit_transfer=taken,
        pc_stack_pop=pc_pop,
        pc_stack_pop_valid=stacks.pc_pop_value is not None,
        status_stack_pop=status_pop,
        status_stack_pop_valid=status_stack.pop_entry is not None,
        status_restored=status_stack.pop_entry is not None,
        **common,
    )
