"""Bounded original-ADSP-2100 sequencer integration model.

This slice composes already independent condition, flow, CNTR, and stack
models at one instruction boundary. It deliberately rejects unresolved
conditional-CALL CE and competing automatic/manual state actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .conditions import (
    ConditionInputs,
    evaluate_do_termination,
    evaluate_if_condition,
)
from .counter import CounterInputs, CounterState, apply_counter_cycle
from .sequencer import (
    PROGRAM_ADDRESS_MASK,
    ExplicitFlow,
    SequencerFlowResult,
    select_sequencer_flow,
)
from .sequencer_stacks import (
    SequencerStacksInputs,
    SequencerStacksState,
    apply_sequencer_stacks_cycle,
)


@dataclass(frozen=True)
class SequencerSliceState:
    counter: CounterState = field(default_factory=CounterState)
    stacks: SequencerStacksState = field(default_factory=SequencerStacksState)


@dataclass(frozen=True)
class SequencerSliceInputs:
    reset: bool = False
    pc: int = 0
    do_until: bool = False
    do_end: int = 0
    do_condition: int = 0
    explicit_flow: ExplicitFlow | int = ExplicitFlow.NONE
    explicit_condition: int = 15
    explicit_target: int = 0
    counter_load: bool = False
    counter_load_value: int = 0
    pc_manual_pop: bool = False
    count_manual_pop: bool = False
    loop_manual_pop: bool = False
    az: bool = False
    an: bool = False
    av: bool = False
    ac: bool = False
    as_flag: bool = False
    mv: bool = False

    def __post_init__(self) -> None:
        for value, name in (
            (self.pc, "pc"),
            (self.do_end, "do_end"),
            (self.explicit_target, "explicit_target"),
            (self.counter_load_value, "counter_load_value"),
        ):
            if not 0 <= value <= PROGRAM_ADDRESS_MASK:
                raise ValueError(f"{name} must fit 14 bits")
        for value, name in (
            (self.do_condition, "do_condition"),
            (self.explicit_condition, "explicit_condition"),
        ):
            if not 0 <= value <= 0xF:
                raise ValueError(f"{name} must fit 4 bits")
        try:
            ExplicitFlow(self.explicit_flow)
        except ValueError as error:
            raise ValueError(
                "explicit_flow must be a defined ExplicitFlow"
            ) from error


@dataclass(frozen=True)
class SequencerSliceResult:
    state: SequencerSliceState
    next_pc: int
    boundary_valid: bool
    integration_conflict: bool
    unsupported_call_ce: bool
    invalid_counter_condition: bool
    invalid_loop_context: bool
    invalid_return_context: bool
    unsupported_do_at_loop_end: bool
    explicit_condition_true: bool
    loop_termination_true: bool
    explicit_transfer: bool
    loop_back: bool
    loop_exit: bool
    counter_test: bool
    counter_decremented: bool
    counter_restored: bool
    counter_empty_invalidated: bool
    pc_stack_push: bool
    pc_stack_pop: bool
    count_stack_push: bool
    count_stack_pop: bool
    loop_stack_push: bool
    loop_stack_pop: bool


def _idle_flow(pc: int) -> SequencerFlowResult:
    sequential_pc = (pc + 1) & PROGRAM_ADDRESS_MASK
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


def apply_sequencer_slice_cycle(
    state: SequencerSliceState,
    inputs: SequencerSliceInputs,
) -> SequencerSliceResult:
    """Apply one bounded sequencer instruction boundary.

    The loop stack's internal 18-bit packing is ``condition[3:0]`` above
    ``end_address[13:0]``. That packing is an implementation interface, not a
    claim about an externally readable register.
    """

    flow_kind = ExplicitFlow(inputs.explicit_flow)
    sequential_pc = (inputs.pc + 1) & PROGRAM_ADDRESS_MASK
    condition_inputs = ConditionInputs(
        az=inputs.az,
        an=inputs.an,
        av=inputs.av,
        ac=inputs.ac,
        as_flag=inputs.as_flag,
        mv=inputs.mv,
        not_counter_expired=bool(
            state.counter.value is not None
            and state.counter.value != 1
        ),
    )
    explicit_condition_true = evaluate_if_condition(
        inputs.explicit_condition,
        condition_inputs,
    )

    loop_active = bool(state.stacks.loop_entries)
    pc_top_valid = bool(state.stacks.pc_entries)
    loop_top = state.stacks.loop_entries[-1] if loop_active else 0
    loop_end = loop_top & PROGRAM_ADDRESS_MASK
    loop_condition = (loop_top >> 14) & 0xF
    loop_start = state.stacks.pc_entries[-1] if pc_top_valid else 0
    loop_termination_true = evaluate_do_termination(
        loop_condition,
        condition_inputs,
    )
    loop_uses_counter = loop_condition == 14

    explicit_uses_counter = (
        flow_kind is not ExplicitFlow.NONE
        and inputs.explicit_condition == 14
    )
    unsupported_call_ce = bool(
        flow_kind is ExplicitFlow.CALL
        and inputs.explicit_condition == 14
    )
    invalid_counter_condition = bool(
        state.counter.value is None
        and (
            explicit_uses_counter
            or (loop_active and loop_uses_counter)
        )
    )
    invalid_loop_context = bool(
        loop_active
        and (
            not pc_top_valid
            or (loop_uses_counter and state.counter.value is None)
        )
    )
    unsupported_do_at_loop_end = bool(
        inputs.do_until
        and loop_active
        and inputs.pc == loop_end
    )
    instruction_class_conflict = bool(
        inputs.do_until
        and flow_kind is not ExplicitFlow.NONE
    )
    manual_control_conflict = bool(
        (
            inputs.pc_manual_pop
            or inputs.count_manual_pop
            or inputs.loop_manual_pop
        )
        and (
            inputs.do_until
            or flow_kind is not ExplicitFlow.NONE
        )
    )
    empty_taken_return = bool(
        flow_kind is ExplicitFlow.RETURN
        and explicit_condition_true
        and not pc_top_valid
    )
    unsupported = bool(
        unsupported_call_ce
        or invalid_counter_condition
        or invalid_loop_context
        or unsupported_do_at_loop_end
        or instruction_class_conflict
        or manual_control_conflict
        or empty_taken_return
    )

    if inputs.reset or unsupported:
        raw_flow = _idle_flow(inputs.pc)
    else:
        raw_flow = select_sequencer_flow(
            pc=inputs.pc,
            explicit_flow=flow_kind,
            explicit_taken=explicit_condition_true,
            explicit_target=(
                loop_start
                if flow_kind is ExplicitFlow.RETURN
                else inputs.explicit_target
            ),
            loop_active=loop_active,
            loop_end=loop_end,
            loop_start=loop_start,
            loop_termination_true=loop_termination_true,
            loop_uses_counter=loop_uses_counter,
        )

    jump_counter_test = bool(
        not unsupported
        and flow_kind is ExplicitFlow.JUMP
        and inputs.explicit_condition == 14
    )
    counter_test = bool(
        jump_counter_test or raw_flow.loop_counter_test
    )
    raw_counter_action_count = sum(
        (
            inputs.counter_load,
            inputs.count_manual_pop,
            counter_test,
        )
    )

    do_push = bool(inputs.do_until and not unsupported)
    raw_pc_push = bool(raw_flow.pc_stack_push or do_push)
    raw_pc_pop = bool(raw_flow.pc_stack_pop or inputs.pc_manual_pop)
    raw_loop_push = do_push
    raw_loop_pop = bool(
        raw_flow.loop_stack_pop or inputs.loop_manual_pop
    )
    counter_valid = state.counter.value is not None
    counter_expired = bool(counter_valid and state.counter.value == 1)
    raw_count_push = bool(inputs.counter_load and counter_valid)
    raw_count_pop = bool(
        inputs.count_manual_pop
        or (counter_test and counter_expired)
    )
    integration_conflict = bool(
        not inputs.reset
        and (
            instruction_class_conflict
            or manual_control_conflict
            or raw_counter_action_count > 1
            or (raw_pc_push and raw_pc_pop)
            or (raw_count_push and raw_count_pop)
            or (raw_loop_push and raw_loop_pop)
        )
    )
    boundary_valid = bool(
        not inputs.reset
        and not unsupported
        and not integration_conflict
    )

    if not boundary_valid:
        next_state = (
            SequencerSliceState()
            if inputs.reset
            else state
        )
        return SequencerSliceResult(
            state=next_state,
            next_pc=sequential_pc,
            boundary_valid=False,
            integration_conflict=integration_conflict,
            unsupported_call_ce=unsupported_call_ce,
            invalid_counter_condition=invalid_counter_condition,
            invalid_loop_context=invalid_loop_context,
            invalid_return_context=empty_taken_return,
            unsupported_do_at_loop_end=unsupported_do_at_loop_end,
            explicit_condition_true=explicit_condition_true,
            loop_termination_true=loop_termination_true,
            explicit_transfer=False,
            loop_back=False,
            loop_exit=False,
            counter_test=False,
            counter_decremented=False,
            counter_restored=False,
            counter_empty_invalidated=False,
            pc_stack_push=False,
            pc_stack_pop=False,
            count_stack_push=False,
            count_stack_pop=False,
            loop_stack_push=False,
            loop_stack_pop=False,
        )

    count_top_valid = bool(state.stacks.count_entries)
    count_top = (
        state.stacks.count_entries[-1]
        if count_top_valid
        else 0
    )
    counter_result = apply_counter_cycle(
        state.counter,
        CounterInputs(
            load=inputs.counter_load,
            load_value=inputs.counter_load_value,
            ce_test=counter_test,
            manual_pop=inputs.count_manual_pop,
            count_stack_top=count_top,
            count_stack_top_valid=count_top_valid,
        ),
    )
    stack_result = apply_sequencer_stacks_cycle(
        state.stacks,
        SequencerStacksInputs(
            pc_push=raw_pc_push,
            pc_pop=raw_pc_pop,
            pc_push_value=raw_flow.pc_stack_push_value,
            count_push=counter_result.count_stack_push,
            count_pop=counter_result.count_stack_pop,
            count_push_value=counter_result.count_stack_push_value,
            loop_push=raw_loop_push,
            loop_pop=raw_loop_pop,
            loop_push_value=(
                (inputs.do_condition << 14) | inputs.do_end
            ),
        ),
    )
    return SequencerSliceResult(
        state=SequencerSliceState(
            counter=counter_result.state,
            stacks=stack_result.state,
        ),
        next_pc=raw_flow.next_pc,
        boundary_valid=True,
        integration_conflict=False,
        unsupported_call_ce=False,
        invalid_counter_condition=False,
        invalid_loop_context=False,
        invalid_return_context=False,
        unsupported_do_at_loop_end=False,
        explicit_condition_true=explicit_condition_true,
        loop_termination_true=loop_termination_true,
        explicit_transfer=raw_flow.explicit_transfer,
        loop_back=raw_flow.loop_back,
        loop_exit=raw_flow.loop_exit,
        counter_test=counter_test,
        counter_decremented=counter_result.decremented,
        counter_restored=counter_result.restored,
        counter_empty_invalidated=counter_result.empty_ce_invalidated,
        pc_stack_push=raw_pc_push,
        pc_stack_pop=raw_pc_pop,
        count_stack_push=counter_result.count_stack_push,
        count_stack_pop=counter_result.count_stack_pop,
        loop_stack_push=raw_loop_push,
        loop_stack_pop=raw_loop_pop,
    )
