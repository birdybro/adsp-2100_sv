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


def apply_linear_fetch_client_cycle(
    state: LinearCoreState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    instruction_issue_inhibit: bool = False,
    bus_relinquished: bool = False,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    pm_request_accepted: bool = False,
    pm_completion_event: bool = False,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
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
        and (state.instruction_valid or state.pending)
    )
    supported, reserved = _instruction_class(
        state.instruction,
        state.instruction_valid,
    )
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
    invalid_condition_state = bool(
        issue_boundary and type10_condition is UNKNOWN
    )
    fetch_request = bool(
        issue_boundary
        and state.instruction_valid
        and supported
        and not state.pending
        and instruction_setup is None
        and not invalid_condition_state
    )
    fetch_address = state.architecture.pc.incremented()
    if type10_condition is not None and type10_condition is not UNKNOWN:
        assert isinstance(state.instruction, ExactWord)
        type10 = decode_direct_jump(state.instruction.value)
        assert type10 is not None
        if bool(type10_condition):
            fetch_address = ExactWord(14, type10.address)
    retire_event = bool(state.pending and pm_completion_event)
    provisional_source_extension = False

    if reset:
        reset_state = LinearCoreState.reset()
        next_state = replace(reset_state, bus=state.bus)
    else:
        next_state = state
        if pm_request_accepted:
            next_state = replace(next_state, pending=True)
        if retire_event:
            assert isinstance(state.instruction, ExactWord)
            type17 = decode_internal_move(state.instruction.value)
            provisional_source_extension = bool(
                type17 is not None
                and type17.legal
                and type17.source_group == 3
                and type17.source_index <= 4
            )
            executor = ADSP2100Model(state=state.architecture)
            executor.step(state.instruction.value)
            next_state = replace(
                next_state,
                architecture=executor.state,
                instruction=pmd_read_data,
                instruction_valid=isinstance(pmd_read_data, ExactWord),
                pending=False,
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
        supported_instruction=supported,
        unsupported_instruction=unsupported_event,
        reserved_subencoding=reserved_event,
        provisional_source_extension=provisional_source_extension,
        phase_conflict=phase_conflict,
        integration_conflict=integration_conflict,
        internal_conflict=invalid_condition_state,
    )


def apply_linear_core_cycle(
    state: LinearCoreState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    instruction_issue_inhibit: bool = False,
    bus_relinquished: bool = False,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
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
        instruction_issue_inhibit=instruction_issue_inhibit,
        bus_relinquished=bus_relinquished,
        instruction_setup=instruction_setup,
        pmd_read_data=pmd_read_data,
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
        instruction_issue_inhibit=instruction_issue_inhibit,
        bus_relinquished=bus_relinquished,
        instruction_setup=instruction_setup,
        pm_request_accepted=bus_result.request_accepted,
        pm_completion_event=bus_result.completion_event,
        pmd_read_data=pmd_read_data,
    )
    next_state = replace(client.state, bus=bus_result.state)

    return LinearCoreCycleResult(
        state=next_state,
        bus=bus_result,
        issue_boundary=client.issue_boundary,
        instruction_setup_accepted=client.instruction_setup_accepted,
        instruction_issue=client.instruction_issue,
        retire_event=client.retire_event,
        supported_instruction=client.supported_instruction,
        unsupported_instruction=client.unsupported_instruction,
        reserved_subencoding=client.reserved_subencoding,
        provisional_source_extension=client.provisional_source_extension,
        phase_conflict=client.phase_conflict,
        integration_conflict=client.integration_conflict,
        internal_conflict=client.internal_conflict,
    )
