"""Composed state model for original ADSP-2100 Type 26 stack control.

The action decoder remains independent from the stateful stack, status, and
counter models. This composition samples all source values from cycle-start
state and commits the selected independent actions at one cycle boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .counter import (
    CounterCycleResult,
    CounterInputs,
    CounterState,
    apply_counter_cycle,
)
from .model import ExactWord
from .sequencer_stacks import (
    SequencerStacksCycleResult,
    SequencerStacksInputs,
    SequencerStacksState,
    apply_sequencer_stacks_cycle,
)
from .stack_control import (
    StackControlActions,
    StackControlStatusOperation,
    decode_stack_control,
)
from .status import (
    StatusCycleInputs,
    StatusCycleResult,
    StatusRegisters,
    StatusStackEntry,
    apply_status_cycle,
)
from .status_stack import (
    StatusStackCycleInputs,
    StatusStackCycleResult,
    StatusStackOperation,
    StatusStackState,
    apply_status_stack_cycle,
)


@dataclass(frozen=True)
class StackControlSliceState:
    """Live status/CNTR and all four architectural stack classes."""

    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    status_stack: StatusStackState = field(
        default_factory=StatusStackState
    )
    sequencer_stacks: SequencerStacksState = field(
        default_factory=SequencerStacksState
    )
    counter: CounterState = field(default_factory=CounterState)

    @property
    def sstat(self) -> int:
        return (
            self.status_stack.sstat_fragment
            | self.sequencer_stacks.sstat_fragment
        )


@dataclass(frozen=True)
class StackControlSliceInputs:
    """One cycle of Type 26 execution or non-overlapping setup traffic."""

    reset: bool = False
    execute: bool = False
    opcode: int = 0
    astat_write: ExactWord | None = None
    mstat_write: ExactWord | None = None
    imask_write: ExactWord | None = None
    counter_load: int | None = None
    pc_push: bool = False
    pc_push_value: int = 0
    loop_push: bool = False
    loop_push_value: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.opcode <= 0xFFFFFF:
            raise ValueError("opcode must fit 24 bits")
        if self.astat_write is not None and self.astat_write.width != 8:
            raise ValueError("ASTAT write must be exactly 8 bits")
        if self.mstat_write is not None and self.mstat_write.width != 4:
            raise ValueError("MSTAT write must be exactly 4 bits")
        if self.imask_write is not None and self.imask_write.width != 4:
            raise ValueError("IMASK write must be exactly 4 bits")
        if self.counter_load is not None and not 0 <= self.counter_load < (1 << 14):
            raise ValueError("counter load must fit 14 bits")
        if not 0 <= self.pc_push_value < (1 << 14):
            raise ValueError("PC push value must fit 14 bits")
        if not 0 <= self.loop_push_value < (1 << 18):
            raise ValueError("loop push value must fit 18 bits")

    @property
    def setup_action(self) -> bool:
        return (
            self.astat_write is not None
            or self.mstat_write is not None
            or self.imask_write is not None
            or self.counter_load is not None
            or self.pc_push
            or self.loop_push
        )


@dataclass(frozen=True)
class StackControlSliceResult:
    state: StackControlSliceState
    actions: StackControlActions | None
    boundary_valid: bool
    invalid_opcode: bool
    integration_conflict: bool
    internal_conflict: bool
    status: StatusCycleResult
    status_stack: StatusStackCycleResult
    sequencer_stacks: SequencerStacksCycleResult
    counter: CounterCycleResult


def _idle_result(
    state: StackControlSliceState,
    *,
    actions: StackControlActions | None = None,
    invalid_opcode: bool = False,
    integration_conflict: bool = False,
) -> StackControlSliceResult:
    return StackControlSliceResult(
        state=state,
        actions=actions,
        boundary_valid=False,
        invalid_opcode=invalid_opcode,
        integration_conflict=integration_conflict,
        internal_conflict=False,
        status=StatusCycleResult(state.status, False),
        status_stack=StatusStackCycleResult(state.status_stack),
        sequencer_stacks=SequencerStacksCycleResult(
            state.sequencer_stacks
        ),
        counter=CounterCycleResult(state.counter),
    )


def apply_stack_control_slice_cycle(
    state: StackControlSliceState,
    inputs: StackControlSliceInputs,
) -> StackControlSliceResult:
    """Apply one stateful Type 26 boundary using cycle-start source values."""

    actions = decode_stack_control(inputs.opcode) if inputs.execute else None

    if inputs.reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        )
        status_stack = apply_status_stack_cycle(
            state.status_stack,
            StatusStackCycleInputs(reset=True),
        )
        counter = apply_counter_cycle(
            state.counter,
            CounterInputs(reset=True),
        )
        sequencer_stacks = apply_sequencer_stacks_cycle(
            state.sequencer_stacks,
            SequencerStacksInputs(reset=True),
        )
        next_state = StackControlSliceState(
            status.state,
            status_stack.state,
            sequencer_stacks.state,
            counter.state,
        )
        return StackControlSliceResult(
            state=next_state,
            actions=actions,
            boundary_valid=False,
            invalid_opcode=False,
            integration_conflict=False,
            internal_conflict=False,
            status=status,
            status_stack=status_stack,
            sequencer_stacks=sequencer_stacks,
            counter=counter,
        )

    invalid_opcode = inputs.execute and actions is None
    integration_conflict = inputs.execute and inputs.setup_action
    if integration_conflict:
        return _idle_result(
            state,
            actions=actions,
            invalid_opcode=invalid_opcode,
            integration_conflict=True,
        )

    boundary_valid = bool(inputs.execute and actions is not None)
    if boundary_valid:
        assert actions is not None
        status_operation = StatusStackOperation(
            int(actions.status_operation)
        )
        status_push_entry = (
            StatusStackEntry(
                state.status.astat,
                state.status.mstat,
                state.status.imask,
            )
            if actions.status_operation
            is StackControlStatusOperation.PUSH
            else None
        )
        pc_pop = actions.pc_pop
        loop_pop = actions.loop_pop
        count_manual_pop = actions.count_pop
    else:
        status_operation = StatusStackOperation.NO_CHANGE_ZERO
        status_push_entry = None
        pc_pop = False
        loop_pop = False
        count_manual_pop = False

    status_stack = apply_status_stack_cycle(
        state.status_stack,
        StatusStackCycleInputs(
            operation=status_operation,
            push_entry=status_push_entry,
        ),
    )
    count_top_valid = bool(state.sequencer_stacks.count_entries)
    count_top = (
        state.sequencer_stacks.count_entries[-1]
        if count_top_valid
        else 0
    )
    counter = apply_counter_cycle(
        state.counter,
        CounterInputs(
            load=inputs.counter_load is not None,
            load_value=(
                inputs.counter_load
                if inputs.counter_load is not None
                else 0
            ),
            manual_pop=count_manual_pop,
            count_stack_top=count_top,
            count_stack_top_valid=count_top_valid,
        ),
    )
    sequencer_stacks = apply_sequencer_stacks_cycle(
        state.sequencer_stacks,
        SequencerStacksInputs(
            pc_push=inputs.pc_push,
            pc_pop=pc_pop,
            pc_push_value=inputs.pc_push_value,
            count_push=counter.count_stack_push,
            count_pop=counter.count_stack_pop,
            count_push_value=counter.count_stack_push_value,
            loop_push=inputs.loop_push,
            loop_pop=loop_pop,
            loop_push_value=inputs.loop_push_value,
        ),
    )
    status = apply_status_cycle(
        state.status,
        StatusCycleInputs(
            astat_move=inputs.astat_write,
            mstat_move=inputs.mstat_write,
            imask_move=inputs.imask_write,
            status_restore=status_stack.pop_entry,
        ),
    )

    internal_conflict = (
        status.write_conflict
        or sequencer_stacks.write_conflict
        or counter.write_conflict
    )
    if internal_conflict:
        return StackControlSliceResult(
            state=state,
            actions=actions,
            boundary_valid=False,
            invalid_opcode=invalid_opcode,
            integration_conflict=False,
            internal_conflict=True,
            status=status,
            status_stack=status_stack,
            sequencer_stacks=sequencer_stacks,
            counter=counter,
        )

    next_state = StackControlSliceState(
        status.state,
        status_stack.state,
        sequencer_stacks.state,
        counter.state,
    )
    return StackControlSliceResult(
        state=next_state,
        actions=actions,
        boundary_valid=boundary_valid,
        invalid_opcode=invalid_opcode,
        integration_conflict=False,
        internal_conflict=False,
        status=status,
        status_stack=status_stack,
        sequencer_stacks=sequencer_stacks,
        counter=counter,
    )
