"""Independent bounded original ADSP-2100 Type 19 execution model.

The model closes conditional DAG2-indirect JUMP/CALL outside active hardware
loops and external fetch phases. Conditional CALL with NOT CE remains excluded
under OQ-012, identically to the direct form.
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
from .status import ASTATState


INDIRECT_JUMP_CLASS_MASK = 0xFFFF20
INDIRECT_JUMP_CLASS_VALUE = 0x0B0000
RESET_PC = 0x0004
_UNKNOWN_I4_I7 = (None, None, None, None)


@dataclass(frozen=True)
class IndirectJumpAction:
    call: bool
    i_local: int
    i_address: int
    condition: int
    supported: bool


def is_indirect_jump_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & INDIRECT_JUMP_CLASS_MASK == INDIRECT_JUMP_CLASS_VALUE


def decode_indirect_jump(opcode: int) -> IndirectJumpAction | None:
    if not is_indirect_jump_class(opcode):
        return None
    i_local = (opcode >> 6) & 0x3
    call = bool((opcode >> 4) & 1)
    condition = opcode & 0xF
    return IndirectJumpAction(
        call=call,
        i_local=i_local,
        i_address=4 + i_local,
        condition=condition,
        supported=not (call and condition == 0xE),
    )


@dataclass(frozen=True)
class IndirectJumpState:
    pc: int = RESET_PC
    astat: ASTATState = field(default_factory=ASTATState)
    counter: CounterState = field(default_factory=CounterState)
    stacks: SequencerStacksState = field(default_factory=SequencerStacksState)
    i4_i7: tuple[int | None, ...] = _UNKNOWN_I4_I7

    def __post_init__(self) -> None:
        if not 0 <= self.pc <= PROGRAM_ADDRESS_MASK:
            raise ValueError("PC must fit 14 bits")
        if len(self.i4_i7) != 4:
            raise ValueError("DAG2 indirect state must contain I4 through I7")
        for value in self.i4_i7:
            if value is not None and not 0 <= value <= PROGRAM_ADDRESS_MASK:
                raise ValueError("DAG2 I register must fit 14 bits")

    @classmethod
    def reset(cls) -> "IndirectJumpState":
        return cls()


@dataclass(frozen=True)
class IndirectJumpCycleResult:
    state: IndirectJumpState
    action: IndirectJumpAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    unsupported_call_ce: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    condition_known: bool = False
    condition_true: bool = False
    invalid_condition_state: bool = False
    indirect_address: int = 0
    indirect_address_valid: bool = False
    invalid_target_state: bool = False
    pc_write: bool = False
    explicit_transfer: bool = False
    pc_stack_push: bool = False
    pc_stack_push_accepted: bool = False
    counter_test: bool = False
    counter_decremented: bool = False
    counter_restored: bool = False
    counter_empty_invalidated: bool = False
    count_stack_push: bool = False
    count_stack_pop: bool = False
    pma_indirect_drive: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def _replace_i(
    values: tuple[int | None, ...],
    local: int,
    value: int,
) -> tuple[int | None, ...]:
    updated = list(values)
    updated[local] = value
    return tuple(updated)


def apply_indirect_jump_cycle(
    state: IndirectJumpState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup_pc: int | None = None,
    setup_astat: ExactWord | None = None,
    setup_counter: int | None = None,
    setup_i: tuple[int, int] | None = None,
) -> IndirectJumpCycleResult:
    """Apply one reset, deterministic setup, or bounded Type 19 cycle."""

    if setup_pc is not None and not 0 <= setup_pc <= PROGRAM_ADDRESS_MASK:
        raise ValueError("PC setup must fit 14 bits")
    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly 8 bits")
    if setup_counter is not None and not 0 <= setup_counter <= PROGRAM_ADDRESS_MASK:
        raise ValueError("CNTR setup must fit 14 bits")
    if setup_i is not None:
        local, value = setup_i
        if not 0 <= local < 4:
            raise ValueError("indirect I setup must select I4 through I7")
        if not 0 <= value <= PROGRAM_ADDRESS_MASK:
            raise ValueError("indirect I setup must fit 14 bits")

    action = decode_indirect_jump(opcode)
    class_valid = action is not None
    action_valid = action is not None and action.supported
    unsupported_call_ce = bool(action is not None and not action.supported)
    setup_count = sum(
        value is not None
        for value in (setup_pc, setup_astat, setup_counter, setup_i)
    )
    conflict = bool(
        not reset and ((execute and setup_count != 0) or setup_count > 1)
    )
    invalid = bool(not reset and execute and action is None)
    common = {
        "action": action,
        "class_valid": class_valid,
        "action_valid": action_valid,
        "unsupported_call_ce": unsupported_call_ce,
    }

    if reset:
        return IndirectJumpCycleResult(IndirectJumpState.reset(), **common)
    if conflict or invalid or (execute and unsupported_call_ce):
        return IndirectJumpCycleResult(
            state,
            invalid_opcode=invalid,
            integration_conflict=conflict,
            **common,
        )
    if setup_pc is not None:
        return IndirectJumpCycleResult(replace(state, pc=setup_pc), **common)
    if setup_astat is not None:
        return IndirectJumpCycleResult(
            replace(state, astat=ASTATState.from_word(setup_astat)),
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
        return IndirectJumpCycleResult(
            replace(state, counter=counter.state, stacks=stacks.state),
            count_stack_push=counter.count_stack_push,
            **common,
        )
    if setup_i is not None:
        local, value = setup_i
        return IndirectJumpCycleResult(
            replace(state, i4_i7=_replace_i(state.i4_i7, local, value)),
            **common,
        )
    if not execute:
        return IndirectJumpCycleResult(state, **common)

    assert action is not None and action.supported
    condition = evaluate_flow_condition(
        action.condition,
        state.astat,
        state.counter,
    )
    if condition is UNKNOWN:
        return IndirectJumpCycleResult(
            state,
            condition_known=False,
            invalid_condition_state=True,
            **common,
        )

    taken = bool(condition)
    target = state.i4_i7[action.i_local]
    target_valid = target is not None
    if taken and not target_valid:
        return IndirectJumpCycleResult(
            state,
            condition_known=True,
            indirect_address_valid=False,
            invalid_target_state=True,
            **common,
        )

    counter_test = bool(not action.call and action.condition == 14)
    count_top_valid = bool(state.stacks.count_entries)
    count_top = state.stacks.count_entries[-1] if count_top_valid else 0
    counter = apply_counter_cycle(
        state.counter,
        CounterInputs(
            ce_test=counter_test,
            count_stack_top=count_top,
            count_stack_top_valid=count_top_valid,
        ),
    )
    pc_push = bool(action.call and taken)
    stacks = apply_sequencer_stacks_cycle(
        state.stacks,
        SequencerStacksInputs(
            pc_push=pc_push,
            pc_push_value=(state.pc + 1) & PROGRAM_ADDRESS_MASK,
            count_pop=counter.count_stack_pop,
        ),
    )
    target_value = 0 if target is None else target
    next_pc = target_value if taken else (state.pc + 1) & PROGRAM_ADDRESS_MASK
    next_state = IndirectJumpState(
        next_pc,
        state.astat,
        counter.state,
        stacks.state,
        state.i4_i7,
    )
    return IndirectJumpCycleResult(
        next_state,
        boundary_valid=True,
        condition_known=True,
        condition_true=taken,
        indirect_address=target_value,
        indirect_address_valid=target_valid,
        pc_write=True,
        explicit_transfer=taken,
        pc_stack_push=pc_push,
        pc_stack_push_accepted=stacks.pc_push_accepted,
        counter_test=counter_test,
        counter_decremented=counter.decremented,
        counter_restored=counter.restored,
        counter_empty_invalidated=counter.empty_ce_invalidated,
        count_stack_pop=counter.count_stack_pop,
        pma_indirect_drive=taken,
        **common,
    )
