"""Independent bounded model for ordinary linear fetch/execute integration."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .load_dreg_immediate import decode_load_dreg_immediate
from .load_non_dreg_immediate import decode_load_non_dreg_immediate
from .internal_move import decode_internal_move
from .conditional_compute import decode_conditional_compute
from .conditional_shift import (
    decode_conditional_shift,
    is_conditional_shift_class,
)
from .immediate_shift import decode_immediate_shift, is_immediate_shift_class
from .shift_move import decode_shift_move, is_shift_move_class
from .compute_move import decode_compute_move, is_compute_move_class
from .divide_quotient import decode_divide_quotient
from .divide_sign import decode_divide_sign, is_divide_sign_class
from .direct_jump import decode_direct_jump
from .do_until import decode_do_until
from .indirect_jump import decode_indirect_jump
from .conditional_return import decode_conditional_return
from .conditional_trap import decode_conditional_trap
from .counter import CounterState
from .flow_condition import evaluate_flow_condition
from .mr_saturation import decode_mr_saturation
from .mode_control import decode_mode_control
from .modify_address import decode_modify_address
from .stack_control import decode_stack_control
from .model import (
    ADSP2100Model,
    ArchitecturalState,
    ExactWord,
    UNKNOWN,
    _UnknownValue,
)
from .phase import LogicalPhase
from .interrupt import (
    InterruptCycleResult,
    InterruptState,
    apply_interrupt_cycle,
)
from .sequencer import ExplicitFlow, select_sequencer_flow
from .status import ASTATState
from .program_bus import (
    ProgramBusCycleResult,
    ProgramBusRequest,
    ProgramBusState,
    apply_program_bus_cycle,
)


@dataclass(frozen=True)
class LinearCoreState:
    """State retained by the bounded steady-state instruction owner."""

    architecture: ArchitecturalState = field(default_factory=ArchitecturalState.reset)
    instruction: ExactWord | _UnknownValue = UNKNOWN
    instruction_valid: bool = False
    pending: bool = False
    interrupt: InterruptState = field(default_factory=InterruptState.reset)
    interrupt_vectoring: bool = False
    interrupt_level: int | None = None
    bus: ProgramBusState = field(default_factory=ProgramBusState.reset)

    @classmethod
    def reset(cls) -> "LinearCoreState":
        return cls()


@dataclass(frozen=True)
class LinearCoreCycleResult:
    state: LinearCoreState
    bus: ProgramBusCycleResult
    issue_boundary: bool = False
    instruction_setup_accepted: bool = False
    instruction_issue: bool = False
    retire_event: bool = False
    trap_event: bool = False
    interrupt_recognition_event: bool = False
    interrupt_entry_event: bool = False
    interrupt_vector_issue_event: bool = False
    interrupt_vector_fetch_event: bool = False
    interrupt_level: int = 0
    interrupt_vector: ExactWord = ExactWord(14, 0)
    interrupt_configuration_invalid: bool = False
    interrupt_reset_baseline_provisional: bool = False
    interrupt_adjacent_control_conflict: bool = False
    supported_instruction: bool = False
    unsupported_instruction: bool = False
    reserved_subencoding: bool = False
    provisional_source_extension: bool = False
    phase_conflict: bool = False
    integration_conflict: bool = False
    internal_conflict: bool = False


@dataclass(frozen=True)
class LinearFetchClientCycleResult:
    """One external-owner boundary for the retained linear-fetch client."""

    state: LinearCoreState
    issue_boundary: bool = False
    instruction_setup_accepted: bool = False
    fetch_request_presented: bool = False
    fetch_address: ExactWord = ExactWord(14, 0)
    instruction_issue: bool = False
    retire_event: bool = False
    pm_instruction_sequential_allowed: bool = False
    pm_instruction_flow_blocked: bool = False
    trap_event: bool = False
    interrupt: InterruptCycleResult = field(
        default_factory=lambda: InterruptCycleResult(InterruptState.reset())
    )
    interrupt_entry_event: bool = False
    interrupt_vector_issue_event: bool = False
    interrupt_vector_fetch_event: bool = False
    interrupt_adjacent_control_conflict: bool = False
    supported_instruction: bool = False
    unsupported_instruction: bool = False
    reserved_subencoding: bool = False
    provisional_source_extension: bool = False
    phase_conflict: bool = False
    integration_conflict: bool = False
    internal_conflict: bool = False


def _instruction_class(
    instruction: ExactWord | _UnknownValue,
    valid: bool,
) -> tuple[bool, bool]:
    """Return (supported, reserved bounded-owner subencoding)."""

    if not valid or not isinstance(instruction, ExactWord):
        return (False, False)
    if instruction.value == 0:
        return (True, False)
    if decode_load_dreg_immediate(instruction.value) is not None:
        return (True, False)
    if decode_mode_control(instruction.value) is not None:
        return (True, False)
    if decode_modify_address(instruction.value) is not None:
        return (True, False)
    if decode_stack_control(instruction.value) is not None:
        return (True, False)
    type10 = decode_direct_jump(instruction.value)
    if type10 is not None:
        return (type10.supported, False)
    if decode_do_until(instruction.value) is not None:
        return (True, False)
    type19 = decode_indirect_jump(instruction.value)
    if type19 is not None:
        return (type19.supported, False)
    if decode_conditional_return(instruction.value) is not None:
        return (True, False)
    if decode_conditional_trap(instruction.value) is not None:
        return (True, False)
    if decode_conditional_compute(instruction.value) is not None:
        return (True, False)
    if decode_divide_quotient(instruction.value) is not None:
        return (True, False)
    if is_compute_move_class(instruction.value):
        action = decode_compute_move(instruction.value)
        return (action is not None, action is None)
    if is_divide_sign_class(instruction.value):
        action = decode_divide_sign(instruction.value)
        assert action is not None
        return (action.supported, not action.supported)
    if decode_mr_saturation(instruction.value):
        return (True, False)
    if is_shift_move_class(instruction.value):
        return (
            decode_shift_move(instruction.value) is not None,
            decode_shift_move(instruction.value) is None,
        )
    if is_immediate_shift_class(instruction.value):
        return (
            decode_immediate_shift(instruction.value) is not None,
            decode_immediate_shift(instruction.value) is None,
        )
    if is_conditional_shift_class(instruction.value):
        return (
            decode_conditional_shift(instruction.value) is not None,
            decode_conditional_shift(instruction.value) is None,
        )
    type17 = decode_internal_move(instruction.value)
    if type17 is not None:
        return (type17.legal, not type17.legal)
    type7 = decode_load_non_dreg_immediate(instruction.value)
    if type7 is not None:
        return (type7.legal, not type7.legal)
    return (False, False)


def _mstat_dependency_invalid(
    architecture: ArchitecturalState,
    instruction: ExactWord | _UnknownValue,
) -> bool:
    """Reject bank/mode consumers until every required MSTAT bit is known."""

    if not isinstance(instruction, ExactWord):
        return False
    opcode = instruction.value
    type7 = decode_load_non_dreg_immediate(opcode)
    type17 = decode_internal_move(opcode)
    bank_required = bool(
        decode_load_dreg_immediate(opcode) is not None
        or (type7 is not None and type7.legal and type7.register == "SB")
        or decode_compute_move(opcode) is not None
        or decode_conditional_compute(opcode) is not None
        or decode_shift_move(opcode) is not None
        or decode_immediate_shift(opcode) is not None
        or decode_conditional_shift(opcode) is not None
        or decode_divide_quotient(opcode) is not None
        or (
            (action := decode_divide_sign(opcode)) is not None
            and action.supported
        )
        or decode_mr_saturation(opcode)
        or (
            type17 is not None
            and type17.legal
            and (
                type17.source_group == 0
                or type17.source_register == "SB"
                or type17.destination_group == 0
                or type17.destination_register == "SB"
            )
        )
    )
    full_mode_required = bool(
        decode_compute_move(opcode) is not None
        or decode_conditional_compute(opcode) is not None
    )
    return bool(
        (bank_required and not architecture.mstat_valid_mask & 1)
        or (full_mode_required and architecture.mstat_valid_mask != 0xF)
    )


def _apply_interrupt_entry(
    architecture: ArchitecturalState,
    level: int,
) -> ArchitecturalState:
    """Push the post-instruction context during the vectoring NOP cycle."""

    if not 0 <= level <= 3:
        raise ValueError("interrupt level must be IRQ0 through IRQ3")
    if not isinstance(architecture.icntl, ExactWord):
        raise ValueError("interrupt entry requires known ICNTL")

    pc_stack = architecture.pc_stack
    status_stack = architecture.status_stack
    sstat = architecture.sstat.value & 0xAA
    if len(pc_stack) < 16:
        pc_stack += (architecture.pc,)
    else:
        sstat |= 1 << 1
    if len(status_stack) < 4:
        status_stack += (
            (
                architecture.astat,
                architecture.mstat,
                architecture.mstat_valid_mask,
                architecture.imask,
            ),
        )
    else:
        sstat |= 1 << 5

    if not pc_stack:
        sstat |= 1 << 0
    if not architecture.count_stack:
        sstat |= 1 << 2
    if not status_stack:
        sstat |= 1 << 4
    if not architecture.loop_stack:
        sstat |= 1 << 6

    imask = ExactWord(
        4,
        (
            ((0xF << (level + 1)) & 0xF)
            if architecture.icntl.value & 0x10
            else 0
        ),
    )
    return replace(
        architecture,
        pc_stack=pc_stack,
        status_stack=status_stack,
        imask=imask,
        sstat=ExactWord(8, sstat),
    )


def apply_linear_fetch_client_cycle(
    state: LinearCoreState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    interrupt_sample_advance: bool = False,
    instruction_issue_inhibit: bool = False,
    bus_relinquished: bool = False,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    pm_request_accepted: bool = False,
    pm_completion_event: bool = False,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
    irq_n: int = 0xF,
    pm_instruction_active: bool = False,
    pm_instruction_complete: bool = False,
    pm_instruction_next_opcode: ExactWord | _UnknownValue = UNKNOWN,
) -> LinearFetchClientCycleResult:
    """Apply one clock to the architectural client without a PM controller."""

    phase = LogicalPhase(phase)
    if instruction_setup is not None:
        pc, opcode = instruction_setup
        if pc.width != 14 or opcode.width != 24:
            raise ValueError("instruction setup requires exact PC14/opcode24")
    if pmd_read_data is not UNKNOWN and (
        not isinstance(pmd_read_data, ExactWord) or pmd_read_data.width != 24
    ):
        raise ValueError("PM read data must be UNKNOWN or exactly 24 bits")
    if pm_instruction_next_opcode is not UNKNOWN and (
        not isinstance(pm_instruction_next_opcode, ExactWord)
        or pm_instruction_next_opcode.width != 24
    ):
        raise ValueError(
            "PM instruction next opcode must be UNKNOWN or exactly 24 bits"
        )

    issue_boundary = bool(
        not reset
        and not instruction_issue_inhibit
        and not bus_relinquished
        and phase_advance
        and phase == LogicalPhase.STATE_8
    )
    setup_accepted = bool(
        issue_boundary
        and instruction_setup is not None
        and not state.instruction_valid
        and not state.pending
    )
    phase_conflict = bool(
        not reset and instruction_setup is not None and not issue_boundary
    )
    integration_conflict = bool(
        not reset
        and instruction_setup is not None
        and (
            state.instruction_valid
            or state.pending
            or state.interrupt_vectoring
        )
    )
    mstat_dependency_invalid = _mstat_dependency_invalid(
        state.architecture,
        state.instruction,
    )
    integration_conflict = bool(
        integration_conflict
        or (issue_boundary and mstat_dependency_invalid)
    )
    supported, reserved = _instruction_class(
        state.instruction,
        state.instruction_valid,
    )
    supported = bool(supported or pm_instruction_active)
    reserved_event = bool(
        issue_boundary and state.instruction_valid and reserved
    )
    unsupported_event = bool(
        issue_boundary
        and state.instruction_valid
        and not supported
        and not reserved_event
    )
    type10_condition = None
    type10 = None
    if (
        supported
        and state.instruction_valid
        and isinstance(state.instruction, ExactWord)
    ):
        type10 = decode_direct_jump(state.instruction.value)
        if type10 is not None:
            astat = (
                ASTATState()
                if state.architecture.astat is UNKNOWN
                else ASTATState.from_word(state.architecture.astat)
            )
            type10_condition = evaluate_flow_condition(
                type10.condition,
                astat,
                CounterState(
                    None
                    if state.architecture.cntr is UNKNOWN
                    else state.architecture.cntr.value
                ),
            )
    type11 = None
    if (
        supported
        and state.instruction_valid
        and isinstance(state.instruction, ExactWord)
    ):
        type11 = decode_do_until(state.instruction.value)
    type20_condition = None
    type20 = None
    if (
        supported
        and state.instruction_valid
        and isinstance(state.instruction, ExactWord)
    ):
        type20 = decode_conditional_return(state.instruction.value)
        if type20 is not None:
            astat = (
                ASTATState()
                if state.architecture.astat is UNKNOWN
                else ASTATState.from_word(state.architecture.astat)
            )
            type20_condition = evaluate_flow_condition(
                type20.condition,
                astat,
                CounterState(
                    None
                    if state.architecture.cntr is UNKNOWN
                    else state.architecture.cntr.value
                ),
            )
    type19_condition = None
    type19 = None
    if (
        supported
        and state.instruction_valid
        and isinstance(state.instruction, ExactWord)
    ):
        type19 = decode_indirect_jump(state.instruction.value)
        if type19 is not None:
            astat = (
                ASTATState()
                if state.architecture.astat is UNKNOWN
                else ASTATState.from_word(state.architecture.astat)
            )
            type19_condition = evaluate_flow_condition(
                type19.condition,
                astat,
                CounterState(
                    None
                    if state.architecture.cntr is UNKNOWN
                    else state.architecture.cntr.value
                ),
            )
    type22_condition = None
    type22 = None
    if (
        supported
        and state.instruction_valid
        and isinstance(state.instruction, ExactWord)
    ):
        type22 = decode_conditional_trap(state.instruction.value)
        if type22 is not None:
            astat = (
                ASTATState()
                if state.architecture.astat is UNKNOWN
                else ASTATState.from_word(state.architecture.astat)
            )
            type22_condition = evaluate_flow_condition(
                type22.condition,
                astat,
                CounterState(
                    None
                    if state.architecture.cntr is UNKNOWN
                    else state.architecture.cntr.value
                ),
            )
    architecture = state.architecture
    astat = (
        ASTATState()
        if architecture.astat is UNKNOWN
        else ASTATState.from_word(architecture.astat)
    )
    counter = CounterState(
        None if architecture.cntr is UNKNOWN else architecture.cntr.value
    )
    loop_active = bool(architecture.loop_stack)
    loop_end = 0
    loop_termination = 0
    loop_condition: bool | object = False
    if loop_active:
        loop_end_word, loop_termination_word = architecture.loop_stack[-1]
        loop_end = loop_end_word.value
        loop_termination = loop_termination_word.value
        loop_condition = evaluate_flow_condition(
            loop_termination,
            astat,
            counter,
        )
    loop_at_end = bool(loop_active and architecture.pc.value == loop_end)

    invalid_condition_state = bool(
        issue_boundary
        and (
            type10_condition is UNKNOWN
            or type20_condition is UNKNOWN
            or type19_condition is UNKNOWN
            or type22_condition is UNKNOWN
            or (loop_at_end and loop_condition is UNKNOWN)
        )
    )
    invalid_return_context = bool(
        issue_boundary
        and type20 is not None
        and type20_condition is not None
        and type20_condition is not UNKNOWN
        and bool(type20_condition)
        and (
            not state.architecture.pc_stack
            or (
                type20.interrupt_return
                and not state.architecture.status_stack
            )
        )
    )
    invalid_indirect_target = bool(
        issue_boundary
        and type19 is not None
        and type19_condition is not None
        and type19_condition is not UNKNOWN
        and bool(type19_condition)
        and not isinstance(
            state.architecture.dag.i[type19.i_address],
            ExactWord,
        )
    )
    invalid_loop_context = bool(
        issue_boundary
        and loop_active
        and (
            not architecture.pc_stack
            or (loop_termination == 0xE and architecture.cntr is UNKNOWN)
        )
    )
    unsupported_do_at_loop_end = bool(
        issue_boundary and type11 is not None and loop_at_end
    )
    unsupported_nested_same_end = bool(
        issue_boundary
        and type11 is not None
        and loop_active
        and type11.end_address == loop_end
    )

    explicit_flow = ExplicitFlow.NONE
    explicit_taken = False
    explicit_target = 0
    if type10 is not None:
        explicit_flow = ExplicitFlow.CALL if type10.call else ExplicitFlow.JUMP
        explicit_taken = bool(
            type10_condition is not UNKNOWN and type10_condition
        )
        explicit_target = type10.address
    elif type19 is not None:
        explicit_flow = ExplicitFlow.CALL if type19.call else ExplicitFlow.JUMP
        explicit_taken = bool(
            type19_condition is not UNKNOWN and type19_condition
        )
        target = architecture.dag.i[type19.i_address]
        if isinstance(target, ExactWord):
            explicit_target = target.value
    elif type20 is not None:
        explicit_flow = ExplicitFlow.RETURN
        explicit_taken = bool(
            type20_condition is not UNKNOWN and type20_condition
        )
        if architecture.pc_stack:
            explicit_target = architecture.pc_stack[-1].value
    elif type22 is not None:
        explicit_flow = ExplicitFlow.JUMP
        explicit_taken = bool(
            type22_condition is not UNKNOWN and type22_condition
        )
        explicit_target = (architecture.pc.value + 1) & 0x3FFF

    flow = select_sequencer_flow(
        pc=architecture.pc.value,
        explicit_flow=explicit_flow,
        explicit_taken=explicit_taken,
        explicit_target=explicit_target,
        loop_active=loop_active,
        loop_end=loop_end,
        loop_start=(
            architecture.pc_stack[-1].value
            if architecture.pc_stack
            else 0
        ),
        loop_termination_true=bool(
            loop_condition is not UNKNOWN and not loop_condition
        ),
        loop_uses_counter=loop_termination == 0xE,
    )
    automatic_loop_flow = bool(
        loop_at_end
        and not (explicit_taken and explicit_flow is not ExplicitFlow.NONE)
    )
    type26 = (
        decode_stack_control(state.instruction.value)
        if isinstance(state.instruction, ExactWord)
        else None
    )
    type7 = (
        decode_load_non_dreg_immediate(state.instruction.value)
        if isinstance(state.instruction, ExactWord)
        else None
    )
    type17 = (
        decode_internal_move(state.instruction.value)
        if isinstance(state.instruction, ExactWord)
        else None
    )
    instruction_writes_cntr = bool(
        (type7 is not None and type7.legal and type7.register == "CNTR")
        or (
            type17 is not None
            and type17.legal
            and type17.destination_register == "CNTR"
        )
    )
    mode_control = (
        decode_mode_control(state.instruction.value)
        if isinstance(state.instruction, ExactWord)
        else None
    )
    interrupt_adjacent_control_write = bool(
        (
            type7 is not None
            and type7.legal
            and type7.register in {"MSTAT", "ICNTL", "IMASK"}
        )
        or (
            type17 is not None
            and type17.legal
            and type17.destination_register in {"MSTAT", "ICNTL", "IMASK"}
        )
        or (mode_control is not None and mode_control.has_effect)
    )
    automatic_manual_conflict = bool(
        issue_boundary
        and automatic_loop_flow
        and (
            (type26 is not None and type26.pc_pop and flow.pc_stack_pop)
            or (type26 is not None and type26.loop_pop and flow.loop_stack_pop)
            or (
                flow.loop_counter_test
                and (
                    (type26 is not None and type26.count_pop)
                    or instruction_writes_cntr
                )
            )
        )
    )
    pm_instruction_sequential_allowed = bool(
        not loop_active
        and not state.pending
        and not state.interrupt_vectoring
        and instruction_setup is None
    )
    pm_instruction_flow_blocked = bool(
        not reset
        and issue_boundary
        and state.instruction_valid
        and pm_instruction_active
        and not pm_instruction_sequential_allowed
    )
    ordinary_fetch_request = bool(
        issue_boundary
        and state.instruction_valid
        and supported
        and not state.pending
        and not state.interrupt_vectoring
        and instruction_setup is None
        and not pm_instruction_active
        and not invalid_condition_state
        and not invalid_return_context
        and not invalid_indirect_target
        and not invalid_loop_context
        and not unsupported_do_at_loop_end
        and not unsupported_nested_same_end
        and not automatic_manual_conflict
    )
    vector_fetch_request = bool(
        issue_boundary
        and state.interrupt_vectoring
        and not state.pending
        and state.interrupt_level is not None
        and instruction_setup is None
    )
    fetch_request = ordinary_fetch_request or vector_fetch_request
    fetch_address = ExactWord(
        14,
        (
            state.interrupt_level
            if state.interrupt_vectoring
            and state.interrupt_level is not None
            else flow.next_pc
        ),
    )
    linear_fetch_retire = bool(
        state.pending
        and pm_completion_event
        and not state.interrupt_vectoring
    )
    pm_instruction_retire = bool(
        pm_instruction_complete
        and state.instruction_valid
        and pm_instruction_active
        and pm_instruction_sequential_allowed
        and phase_advance
        and phase == LogicalPhase.STATE_7
    )
    retire_event = linear_fetch_retire or pm_instruction_retire
    pm_instruction_completion_conflict = bool(
        not reset and pm_instruction_complete and not pm_instruction_retire
    )
    trap_event = bool(
        retire_event
        and type22 is not None
        and type22_condition is not UNKNOWN
        and type22_condition
    )
    interrupt_service_allowed = bool(
        retire_event
        and state.instruction_valid
        and supported
        and not trap_event
        and not interrupt_adjacent_control_write
    )
    interrupt = apply_interrupt_cycle(
        state.interrupt,
        reset=reset,
        phase=phase,
        phase_advance=bool(
            phase_advance or interrupt_sample_advance
        ),
        irq_n=irq_n,
        icntl=state.architecture.icntl,
        imask=state.architecture.imask,
        service_allowed=interrupt_service_allowed,
    )
    interrupt_adjacent_control_conflict = bool(
        retire_event
        and interrupt_adjacent_control_write
        and interrupt.enabled_requests
    )
    interrupt_vector_issue_event = bool(
        vector_fetch_request and pm_request_accepted
    )
    interrupt_vector_fetch_event = bool(
        state.interrupt_vectoring
        and state.pending
        and pm_completion_event
    )
    provisional_source_extension = False

    if reset:
        reset_state = LinearCoreState.reset()
        next_state = replace(reset_state, bus=state.bus)
    else:
        next_state = replace(state, interrupt=interrupt.state)
        if pm_request_accepted:
            next_state = replace(next_state, pending=True)
        if interrupt_vector_issue_event:
            assert state.interrupt_level is not None
            architecture = _apply_interrupt_entry(
                state.architecture,
                state.interrupt_level,
            )
            next_state = replace(next_state, architecture=architecture)
        if retire_event:
            assert isinstance(state.instruction, ExactWord)
            type17 = decode_internal_move(state.instruction.value)
            provisional_source_extension = bool(
                type17 is not None
                and type17.legal
                and type17.source_group == 3
                and type17.source_index <= 4
            )
            if pm_instruction_retire:
                retired_architecture = replace(
                    state.architecture,
                    pc=ExactWord(14, flow.next_pc),
                )
            elif mstat_dependency_invalid:
                retired_architecture = replace(
                    state.architecture,
                    pc=ExactWord(14, flow.next_pc),
                )
            else:
                executor = ADSP2100Model(state=state.architecture)
                executor.step(state.instruction.value)
                retired_architecture = executor.state
            if interrupt.recognition_event:
                next_state = replace(
                    next_state,
                    architecture=retired_architecture,
                    instruction=UNKNOWN,
                    instruction_valid=False,
                    pending=False,
                    interrupt_vectoring=True,
                    interrupt_level=interrupt.recognized_level,
                )
            else:
                next_state = replace(
                    next_state,
                    architecture=retired_architecture,
                    instruction=(
                        pm_instruction_next_opcode
                        if pm_instruction_retire else pmd_read_data
                    ),
                    instruction_valid=isinstance(
                        pm_instruction_next_opcode
                        if pm_instruction_retire else pmd_read_data,
                        ExactWord,
                    ),
                    pending=False,
                )
        if interrupt_vector_fetch_event:
            assert state.interrupt_level is not None
            next_state = replace(
                next_state,
                architecture=replace(
                    next_state.architecture,
                    pc=ExactWord(14, state.interrupt_level),
                ),
                instruction=pmd_read_data,
                instruction_valid=isinstance(pmd_read_data, ExactWord),
                pending=False,
                interrupt_vectoring=False,
                interrupt_level=None,
            )
        if setup_accepted:
            assert instruction_setup is not None
            pc, opcode = instruction_setup
            next_state = replace(
                next_state,
                architecture=replace(state.architecture, pc=pc),
                instruction=opcode,
                instruction_valid=True,
                pending=False,
            )

    return LinearFetchClientCycleResult(
        state=next_state,
        issue_boundary=issue_boundary,
        instruction_setup_accepted=setup_accepted,
        fetch_request_presented=fetch_request,
        fetch_address=fetch_address,
        instruction_issue=pm_request_accepted,
        retire_event=retire_event,
        pm_instruction_sequential_allowed=(
            pm_instruction_sequential_allowed
        ),
        pm_instruction_flow_blocked=pm_instruction_flow_blocked,
        trap_event=trap_event,
        interrupt=interrupt,
        interrupt_entry_event=interrupt_vector_issue_event,
        interrupt_vector_issue_event=interrupt_vector_issue_event,
        interrupt_vector_fetch_event=interrupt_vector_fetch_event,
        interrupt_adjacent_control_conflict=(
            interrupt_adjacent_control_conflict
        ),
        supported_instruction=supported,
        unsupported_instruction=unsupported_event,
        reserved_subencoding=reserved_event,
        provisional_source_extension=provisional_source_extension,
        phase_conflict=phase_conflict,
        integration_conflict=integration_conflict,
        internal_conflict=(
            invalid_condition_state
            or invalid_return_context
            or invalid_indirect_target
            or invalid_loop_context
            or unsupported_do_at_loop_end
            or unsupported_nested_same_end
            or automatic_manual_conflict
            or interrupt_adjacent_control_conflict
            or pm_instruction_flow_blocked
            or pm_instruction_completion_conflict
        ),
    )


def apply_linear_core_cycle(
    state: LinearCoreState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    interrupt_sample_advance: bool = False,
    instruction_issue_inhibit: bool = False,
    bus_relinquished: bool = False,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
    irq_n: int = 0xF,
) -> LinearCoreCycleResult:
    """Apply one logical-phase clock to the bounded linear owner.

    ``instruction_setup`` is a deterministic verification preload containing
    ``(PC14, opcode24)``. It is admitted only at an idle state-8 boundary and
    is not an architectural host-loading claim.
    """

    phase = LogicalPhase(phase)
    preview = apply_linear_fetch_client_cycle(
        state,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        interrupt_sample_advance=interrupt_sample_advance,
        instruction_issue_inhibit=instruction_issue_inhibit,
        bus_relinquished=bus_relinquished,
        instruction_setup=instruction_setup,
        pmd_read_data=pmd_read_data,
        irq_n=irq_n,
    )
    request = (
        ProgramBusRequest.fetch(preview.fetch_address.value)
        if preview.fetch_request_presented
        else None
    )
    bus_result = apply_program_bus_cycle(
        state.bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        request=request,
        pmd_read_data=pmd_read_data,
        bus_relinquished=bus_relinquished,
    )
    client = apply_linear_fetch_client_cycle(
        state,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        interrupt_sample_advance=interrupt_sample_advance,
        instruction_issue_inhibit=instruction_issue_inhibit,
        bus_relinquished=bus_relinquished,
        instruction_setup=instruction_setup,
        pm_request_accepted=bus_result.request_accepted,
        pm_completion_event=bus_result.completion_event,
        pmd_read_data=pmd_read_data,
        irq_n=irq_n,
    )
    next_state = replace(client.state, bus=bus_result.state)

    return LinearCoreCycleResult(
        state=next_state,
        bus=bus_result,
        issue_boundary=client.issue_boundary,
        instruction_setup_accepted=client.instruction_setup_accepted,
        instruction_issue=client.instruction_issue,
        retire_event=client.retire_event,
        trap_event=client.trap_event,
        interrupt_recognition_event=client.interrupt.recognition_event,
        interrupt_entry_event=client.interrupt_entry_event,
        interrupt_vector_issue_event=client.interrupt_vector_issue_event,
        interrupt_vector_fetch_event=client.interrupt_vector_fetch_event,
        interrupt_level=(
            client.interrupt.recognized_level
            if client.interrupt.recognition_event
            else (state.interrupt_level or 0)
        ),
        interrupt_vector=client.interrupt.vector_address,
        interrupt_configuration_invalid=(
            client.interrupt.configuration_invalid
        ),
        interrupt_reset_baseline_provisional=(
            client.interrupt.reset_baseline_provisional
        ),
        interrupt_adjacent_control_conflict=(
            client.interrupt_adjacent_control_conflict
        ),
        supported_instruction=client.supported_instruction,
        unsupported_instruction=client.unsupported_instruction,
        reserved_subencoding=client.reserved_subencoding,
        provisional_source_extension=client.provisional_source_extension,
        phase_conflict=client.phase_conflict,
        integration_conflict=client.integration_conflict,
        internal_conflict=client.internal_conflict,
    )
