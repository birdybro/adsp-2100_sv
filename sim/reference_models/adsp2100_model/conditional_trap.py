"""Independent phase-aware original ADSP-2100 Type 22 TRAP model.

The boundary accepts an instruction in logical state 1, preserves the
condition decision through the cycle, and commits PC+1 at the state-7/state-8
transition.  A taken TRAP asserts the output and holds state 8 until an
externally recognized HALT completes the documented handshake.  General HALT,
BR/BG, interrupts, and program-memory strobes remain outside this slice.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import IntEnum

from .counter import CounterState
from .flow_condition import evaluate_flow_condition
from .model import ExactWord, UNKNOWN
from .sequencer import PROGRAM_ADDRESS_MASK
from .status import ASTATState


CONDITIONAL_TRAP_CLASS_MASK = 0xFFFFF0
CONDITIONAL_TRAP_CLASS_VALUE = 0x080000
RESET_PC = 0x0004


class LogicalPhase(IntEnum):
    STATE_1 = 0
    STATE_2 = 1
    STATE_3 = 2
    STATE_4 = 3
    STATE_5 = 4
    STATE_6 = 5
    STATE_7 = 6
    STATE_8 = 7


@dataclass(frozen=True)
class ConditionalTrapAction:
    condition: int


def is_conditional_trap_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & CONDITIONAL_TRAP_CLASS_MASK == CONDITIONAL_TRAP_CLASS_VALUE


def decode_conditional_trap(opcode: int) -> ConditionalTrapAction | None:
    if not is_conditional_trap_class(opcode):
        return None
    return ConditionalTrapAction(condition=opcode & 0xF)


@dataclass(frozen=True)
class ConditionalTrapState:
    pc: int = RESET_PC
    astat: ASTATState = field(default_factory=ASTATState)
    counter: CounterState = field(default_factory=CounterState)
    pending: bool = False
    pending_taken: bool = False
    trap_asserted: bool = False
    halted: bool = False
    halt_handoff: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.pc <= PROGRAM_ADDRESS_MASK:
            raise ValueError("PC must fit 14 bits")


@dataclass(frozen=True)
class ConditionalTrapCycleResult:
    state: ConditionalTrapState
    action: ConditionalTrapAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    instruction_accepted: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    invalid_condition_state: bool = False
    integration_conflict: bool = False
    phase_mismatch: bool = False
    condition_known: bool = False
    condition_true: bool = False
    pc_write: bool = False
    trap_event: bool = False
    resume_event: bool = False
    phase_hold: bool = False
    counter_test: bool = False
    counter_decremented: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def apply_conditional_trap_cycle(
    state: ConditionalTrapState,
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
) -> ConditionalTrapCycleResult:
    """Apply one FPGA clock at the bounded Type 22 phase interface."""

    phase = LogicalPhase(phase)
    if setup_pc is not None and not 0 <= setup_pc <= PROGRAM_ADDRESS_MASK:
        raise ValueError("PC setup must fit 14 bits")
    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly 8 bits")
    if setup_counter is not None and not 0 <= setup_counter <= PROGRAM_ADDRESS_MASK:
        raise ValueError("CNTR setup must fit 14 bits")

    action = decode_conditional_trap(opcode)
    class_valid = action is not None
    setup_count = sum(value is not None for value in (setup_pc, setup_astat, setup_counter))
    conflict = bool(not reset and ((execute and setup_count) or setup_count > 1))
    phase_mismatch = bool(
        not reset
        and execute
        and not state.halted
        and phase_advance
        and phase != LogicalPhase.STATE_1
    )
    invalid_opcode = bool(
        not reset
        and execute
        and not state.halted
        and phase_advance
        and phase == LogicalPhase.STATE_1
        and action is None
    )
    common = {
        "action": action,
        "class_valid": class_valid,
        "action_valid": class_valid,
    }

    if reset:
        reset_state = ConditionalTrapState()
        return ConditionalTrapCycleResult(
            reset_state,
            phase_hold=False,
            **common,
        )
    if conflict:
        return ConditionalTrapCycleResult(
            state,
            integration_conflict=True,
            phase_hold=state.halted,
            **common,
        )

    next_state = state
    if setup_pc is not None:
        next_state = replace(next_state, pc=setup_pc)
    elif setup_astat is not None:
        next_state = replace(next_state, astat=ASTATState.from_word(setup_astat))
    elif setup_counter is not None:
        next_state = replace(next_state, counter=CounterState(setup_counter))

    resume_event = False
    if state.trap_asserted and halt_recognized:
        next_state = replace(
            next_state,
            trap_asserted=False,
            halted=True,
            halt_handoff=True,
        )
    elif state.halt_handoff and not halt_recognized:
        next_state = replace(next_state, halted=False, halt_handoff=False)
        resume_event = True

    instruction_accepted = False
    boundary_valid = False
    condition_known = False
    condition_true = False
    if (
        execute
        and not state.halted
        and phase_advance
        and phase == LogicalPhase.STATE_1
        and action is not None
        and setup_count == 0
    ):
        condition = evaluate_flow_condition(action.condition, state.astat, state.counter)
        condition_known = condition is not UNKNOWN
        if condition_known:
            condition_true = bool(condition)
            instruction_accepted = True
            next_state = replace(
                next_state,
                pending=True,
                pending_taken=condition_true,
            )

    pc_write = False
    trap_event = False
    if (
        state.pending
        and not state.halted
        and phase_advance
        and phase == LogicalPhase.STATE_7
    ):
        pc_write = True
        boundary_valid = True
        trap_event = state.pending_taken
        next_state = replace(
            next_state,
            pc=(state.pc + 1) & PROGRAM_ADDRESS_MASK,
            pending=False,
            pending_taken=False,
            trap_asserted=state.pending_taken,
            halted=state.pending_taken,
            halt_handoff=False,
        )

    invalid_condition_state = bool(
        execute
        and not state.halted
        and phase_advance
        and phase == LogicalPhase.STATE_1
        and action is not None
        and not condition_known
    )
    return ConditionalTrapCycleResult(
        next_state,
        instruction_accepted=instruction_accepted,
        boundary_valid=boundary_valid,
        invalid_opcode=invalid_opcode,
        invalid_condition_state=invalid_condition_state,
        phase_mismatch=phase_mismatch,
        condition_known=condition_known,
        condition_true=condition_true,
        pc_write=pc_write,
        trap_event=trap_event,
        resume_event=resume_event,
        phase_hold=next_state.halted,
        **common,
    )
