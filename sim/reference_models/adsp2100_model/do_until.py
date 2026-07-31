"""Independent bounded original ADSP-2100 Type 11 DO UNTIL model.

Type 11 establishes a zero-overhead hardware loop by pushing the first loop
address (cycle-start PC plus one) on the PC stack and the encoded termination
condition and last loop address on the loop stack in the same instruction
cycle.  Loop-terminal execution is owned by the separate sequencer model.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .counter import CounterInputs, CounterState, apply_counter_cycle
from .sequencer import PROGRAM_ADDRESS_MASK
from .sequencer_stacks import (
    SequencerStacksInputs,
    SequencerStacksState,
    apply_sequencer_stacks_cycle,
)


DO_UNTIL_CLASS_MASK = 0xFC0000
DO_UNTIL_CLASS_VALUE = 0x140000
RESET_PC = 0x0004


@dataclass(frozen=True)
class DoUntilAction:
    end_address: int
    termination: int


def is_do_until_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & DO_UNTIL_CLASS_MASK == DO_UNTIL_CLASS_VALUE


def decode_do_until(opcode: int) -> DoUntilAction | None:
    if not is_do_until_class(opcode):
        return None
    return DoUntilAction(
        end_address=(opcode >> 4) & PROGRAM_ADDRESS_MASK,
        termination=opcode & 0xF,
    )


@dataclass(frozen=True)
class DoUntilState:
    pc: int = RESET_PC
    counter: CounterState = field(default_factory=CounterState)
    stacks: SequencerStacksState = field(default_factory=SequencerStacksState)

    def __post_init__(self) -> None:
        if not 0 <= self.pc <= PROGRAM_ADDRESS_MASK:
            raise ValueError("PC must fit 14 bits")

    @classmethod
    def reset(cls) -> "DoUntilState":
        return cls()


@dataclass(frozen=True)
class DoUntilCycleResult:
    state: DoUntilState
    action: DoUntilAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    invalid_loop_context: bool = False
    unsupported_do_at_loop_end: bool = False
    unsupported_nested_same_end: bool = False
    pc_write: bool = False
    pc_stack_push: bool = False
    pc_stack_push_accepted: bool = False
    pc_stack_overflow_event: bool = False
    loop_stack_push: bool = False
    loop_stack_push_accepted: bool = False
    loop_stack_overflow_event: bool = False
    count_stack_push: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def apply_do_until_cycle(
    state: DoUntilState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup_pc: int | None = None,
    setup_counter: int | None = None,
) -> DoUntilCycleResult:
    """Apply one reset, deterministic setup, or bounded Type 11 boundary."""

    if setup_pc is not None and not 0 <= setup_pc <= PROGRAM_ADDRESS_MASK:
        raise ValueError("PC setup must fit 14 bits")
    if setup_counter is not None and not 0 <= setup_counter <= PROGRAM_ADDRESS_MASK:
        raise ValueError("CNTR setup must fit 14 bits")

    action = decode_do_until(opcode)
    class_valid = action is not None
    action_valid = class_valid
    setup_count = sum(value is not None for value in (setup_pc, setup_counter))
    conflict = bool(
        not reset and ((execute and setup_count != 0) or setup_count > 1)
    )
    invalid_opcode = bool(not reset and execute and not class_valid)
    common = {
        "action": action,
        "class_valid": class_valid,
        "action_valid": action_valid,
        "invalid_opcode": invalid_opcode,
        "integration_conflict": conflict,
    }

    if reset:
        return DoUntilCycleResult(DoUntilState.reset(), **common)
    if conflict or invalid_opcode:
        return DoUntilCycleResult(state, **common)
    if setup_pc is not None:
        return DoUntilCycleResult(replace(state, pc=setup_pc), **common)
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
        return DoUntilCycleResult(
            replace(state, counter=counter.state, stacks=stacks.state),
            count_stack_push=counter.count_stack_push,
            **common,
        )
    if not execute:
        return DoUntilCycleResult(state, **common)

    assert action is not None
    loop_active = bool(state.stacks.loop_entries)
    pc_top_valid = bool(state.stacks.pc_entries)
    outer_descriptor = state.stacks.loop_entries[-1] if loop_active else 0
    outer_end = outer_descriptor & PROGRAM_ADDRESS_MASK
    outer_termination = (outer_descriptor >> 14) & 0xF
    invalid_loop_context = bool(
        loop_active
        and (
            not pc_top_valid
            or (outer_termination == 0xE and state.counter.value is None)
        )
    )
    unsupported_at_end = bool(loop_active and state.pc == outer_end)
    unsupported_same_end = bool(loop_active and action.end_address == outer_end)
    if invalid_loop_context or unsupported_at_end or unsupported_same_end:
        return DoUntilCycleResult(
            state,
            invalid_loop_context=invalid_loop_context,
            unsupported_do_at_loop_end=unsupported_at_end,
            unsupported_nested_same_end=unsupported_same_end,
            **common,
        )

    sequential_pc = (state.pc + 1) & PROGRAM_ADDRESS_MASK
    descriptor = (action.termination << 14) | action.end_address
    stacks = apply_sequencer_stacks_cycle(
        state.stacks,
        SequencerStacksInputs(
            pc_push=True,
            pc_push_value=sequential_pc,
            loop_push=True,
            loop_push_value=descriptor,
        ),
    )
    return DoUntilCycleResult(
        state=replace(state, pc=sequential_pc, stacks=stacks.state),
        boundary_valid=True,
        pc_write=True,
        pc_stack_push=True,
        pc_stack_push_accepted=stacks.pc_push_accepted,
        pc_stack_overflow_event=stacks.pc_overflow_event,
        loop_stack_push=True,
        loop_stack_push_accepted=stacks.loop_push_accepted,
        loop_stack_overflow_event=stacks.loop_overflow_event,
        **common,
    )
