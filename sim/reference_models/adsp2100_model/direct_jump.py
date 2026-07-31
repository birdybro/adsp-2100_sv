"""Independent bounded original ADSP-2100 Type 10 execution model.

The model closes direct JUMP and direct CALL outside active hardware-loop
sequencing.  Conditional CALL with NOT CE remains excluded under OQ-012.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .conditions import ConditionInputs, evaluate_if_condition
from .counter import CounterInputs, CounterState, apply_counter_cycle
from .model import ExactWord, UNKNOWN
from .sequencer import PROGRAM_ADDRESS_MASK
from .sequencer_stacks import (
    SequencerStacksInputs,
    SequencerStacksState,
    apply_sequencer_stacks_cycle,
)
from .status import ASTATBit, ASTATState


DIRECT_JUMP_CLASS_MASK = 0xF80000
DIRECT_JUMP_CLASS_VALUE = 0x180000
RESET_PC = 0x0004


@dataclass(frozen=True)
class DirectJumpAction:
    call: bool
    address: int
    condition: int
    supported: bool


def is_direct_jump_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & DIRECT_JUMP_CLASS_MASK == DIRECT_JUMP_CLASS_VALUE


def decode_direct_jump(opcode: int) -> DirectJumpAction | None:
    if not is_direct_jump_class(opcode):
        return None
    call = bool((opcode >> 18) & 1)
    condition = opcode & 0xF
    return DirectJumpAction(
        call=call,
        address=(opcode >> 4) & PROGRAM_ADDRESS_MASK,
        condition=condition,
        supported=not (call and condition == 0xE),
    )


@dataclass(frozen=True)
class DirectJumpState:
    pc: int = RESET_PC
    astat: ASTATState = field(default_factory=ASTATState)
    counter: CounterState = field(default_factory=CounterState)
    stacks: SequencerStacksState = field(default_factory=SequencerStacksState)

    def __post_init__(self) -> None:
        if not 0 <= self.pc <= PROGRAM_ADDRESS_MASK:
            raise ValueError("PC must fit 14 bits")

    @classmethod
    def reset(cls) -> "DirectJumpState":
        return cls()


@dataclass(frozen=True)
class DirectJumpCycleResult:
    state: DirectJumpState
    action: DirectJumpAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    unsupported_call_ce: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    condition_known: bool = False
    condition_true: bool = False
    invalid_condition_state: bool = False
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
    pm_data_access: bool = False
    dm_access: bool = False


def _condition_value(
    condition: int,
    astat: ASTATState,
    counter: CounterState,
) -> bool | object:
    required = {
        0: (ASTATBit.AZ,),
        1: (ASTATBit.AZ,),
        2: (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV),
        3: (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV),
        4: (ASTATBit.AN, ASTATBit.AV),
        5: (ASTATBit.AN, ASTATBit.AV),
        6: (ASTATBit.AV,),
        7: (ASTATBit.AV,),
        8: (ASTATBit.AC,),
        9: (ASTATBit.AC,),
        10: (ASTATBit.AS,),
        11: (ASTATBit.AS,),
        12: (ASTATBit.MV,),
        13: (ASTATBit.MV,),
        14: (),
        15: (),
    }[condition]
    if condition == 14:
        return UNKNOWN if counter.value is None else counter.value != 1
    if any(astat.bit(bit) is UNKNOWN for bit in required):
        return UNKNOWN

    def known(bit: ASTATBit) -> bool:
        value = astat.bit(bit)
        assert value is not UNKNOWN
        return bool(value)

    return evaluate_if_condition(
        condition,
        ConditionInputs(
            az=known(ASTATBit.AZ) if ASTATBit.AZ in required else False,
            an=known(ASTATBit.AN) if ASTATBit.AN in required else False,
            av=known(ASTATBit.AV) if ASTATBit.AV in required else False,
            ac=known(ASTATBit.AC) if ASTATBit.AC in required else False,
            as_flag=known(ASTATBit.AS) if ASTATBit.AS in required else False,
            mv=known(ASTATBit.MV) if ASTATBit.MV in required else False,
            not_counter_expired=False,
        ),
    )


def apply_direct_jump_cycle(
    state: DirectJumpState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup_pc: int | None = None,
    setup_astat: ExactWord | None = None,
    setup_counter: int | None = None,
) -> DirectJumpCycleResult:
    """Apply one reset, deterministic setup, or bounded Type 10 boundary."""

    if setup_pc is not None and not 0 <= setup_pc <= PROGRAM_ADDRESS_MASK:
        raise ValueError("PC setup must fit 14 bits")
    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly 8 bits")
    if setup_counter is not None and not 0 <= setup_counter <= PROGRAM_ADDRESS_MASK:
        raise ValueError("CNTR setup must fit 14 bits")

    action = decode_direct_jump(opcode)
    class_valid = action is not None
    action_valid = action is not None and action.supported
    unsupported_call_ce = bool(action is not None and not action.supported)
    setup_count = sum(
        value is not None for value in (setup_pc, setup_astat, setup_counter)
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
        return DirectJumpCycleResult(DirectJumpState.reset(), **common)
    if conflict or invalid or (execute and unsupported_call_ce):
        return DirectJumpCycleResult(
            state,
            invalid_opcode=invalid,
            integration_conflict=conflict,
            **common,
        )
    if setup_pc is not None:
        return DirectJumpCycleResult(replace(state, pc=setup_pc), **common)
    if setup_astat is not None:
        return DirectJumpCycleResult(
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
        return DirectJumpCycleResult(
            replace(state, counter=counter.state, stacks=stacks.state),
            count_stack_push=counter.count_stack_push,
            **common,
        )
    if not execute:
        return DirectJumpCycleResult(state, **common)

    assert action is not None and action.supported
    condition = _condition_value(action.condition, state.astat, state.counter)
    if condition is UNKNOWN:
        return DirectJumpCycleResult(
            state,
            condition_known=False,
            invalid_condition_state=True,
            **common,
        )

    taken = bool(condition)
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
    next_pc = (
        action.address
        if taken
        else (state.pc + 1) & PROGRAM_ADDRESS_MASK
    )
    next_state = DirectJumpState(next_pc, state.astat, counter.state, stacks.state)
    return DirectJumpCycleResult(
        next_state,
        boundary_valid=True,
        condition_known=True,
        condition_true=taken,
        pc_write=True,
        explicit_transfer=taken,
        pc_stack_push=pc_push,
        pc_stack_push_accepted=stacks.pc_push_accepted,
        counter_test=counter_test,
        counter_decremented=counter.decremented,
        counter_restored=counter.restored,
        counter_empty_invalidated=counter.empty_ce_invalidated,
        count_stack_pop=counter.count_stack_pop,
        **common,
    )
