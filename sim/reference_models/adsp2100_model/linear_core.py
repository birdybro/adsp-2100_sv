"""Independent bounded model for ordinary linear fetch/execute integration."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .load_dreg_immediate import decode_load_dreg_immediate
from .load_non_dreg_immediate import decode_load_non_dreg_immediate
from .internal_move import decode_internal_move
from .mode_control import decode_mode_control
from .model import (
    ADSP2100Model,
    ArchitecturalState,
    ExactWord,
    UNKNOWN,
    _UnknownValue,
)
from .phase import LogicalPhase
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
    type17 = decode_internal_move(instruction.value)
    if type17 is not None:
        return (type17.legal, not type17.legal)
    type7 = decode_load_non_dreg_immediate(instruction.value)
    if type7 is not None:
        return (type7.legal, not type7.legal)
    return (False, False)


def apply_linear_core_cycle(
    state: LinearCoreState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
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
    fetch_request = bool(
        issue_boundary
        and state.instruction_valid
        and supported
        and not state.pending
        and instruction_setup is None
    )
    fetch_address = state.architecture.pc.incremented()
    request = (
        ProgramBusRequest.fetch(fetch_address.value)
        if fetch_request
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
    retire_event = bool(state.pending and bus_result.completion_event)
    provisional_source_extension = False

    if reset:
        next_state = LinearCoreState.reset()
    else:
        next_state = replace(state, bus=bus_result.state)
        if bus_result.request_accepted:
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

    return LinearCoreCycleResult(
        state=next_state,
        bus=bus_result,
        issue_boundary=issue_boundary,
        instruction_setup_accepted=setup_accepted,
        instruction_issue=bus_result.request_accepted,
        retire_event=retire_event,
        supported_instruction=supported,
        unsupported_instruction=unsupported_event,
        reserved_subencoding=reserved_event,
        provisional_source_extension=provisional_source_extension,
        phase_conflict=phase_conflict,
        integration_conflict=integration_conflict,
    )
