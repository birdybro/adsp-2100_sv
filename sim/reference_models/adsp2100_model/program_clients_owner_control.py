"""Three PM clients on one cache/native owner and one architectural state.

The retained fetch sequencer remains the PC/opcode owner, while Type 5 and
Type 13 consume and update the same computational, status, DAG, and PX image.
An optional sequential-only mode issues either PM class from the retained
opcode and installs its cache-hit or miss-recovery PC+1 successor.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .bus_control import BusControlMode
from .compute_pm import (
    ComputePMCycleResult,
    ComputePMState,
    apply_compute_pm_cycle,
    decode_compute_pm,
)
from .instruction_cache import (
    InstructionCacheCycleResult,
    InstructionCacheState,
    apply_instruction_cache_cycle,
    lookup_instruction_cache,
)
from .halt_control import (
    HaltControlCycleResult,
    HaltControlMode,
    HaltControlState,
    apply_halt_control_cycle,
)
from .linear_core import (
    LinearCoreState,
    LinearFetchClientCycleResult,
    apply_linear_fetch_client_cycle,
)
from .model import (
    ArchitecturalState,
    DAGRegisters,
    ExactWord,
    UNKNOWN,
    _UnknownValue,
)
from .modify_address import DAGRegisterSetup, DAGRegisterState
from .phase import LogicalPhase
from .program_bus import ProgramBusRequest
from .program_owner_bus_control import (
    ProgramOwnerBusControlCycleResult,
    ProgramOwnerBusControlState,
    apply_program_owner_bus_control_cycle,
)
from .registers import DREGWrite
from .shifter_pm import (
    ShifterPMCycleResult,
    ShifterPMState,
    apply_shifter_pm_cycle,
    decode_shifter_pm,
)
from .status import ASTATState, StatusRegisters


@dataclass(frozen=True)
class ProgramClientsOwnerControlState:
    linear: LinearCoreState = field(default_factory=LinearCoreState.reset)
    type5: ComputePMState = field(default_factory=ComputePMState.reset)
    type13: ShifterPMState = field(default_factory=ShifterPMState.reset)
    cache: InstructionCacheState = field(default_factory=InstructionCacheState.reset)
    interface: ProgramOwnerBusControlState = field(
        default_factory=ProgramOwnerBusControlState.reset
    )
    halt: HaltControlState = field(default_factory=HaltControlState)
    type5_cache_instruction: ExactWord | _UnknownValue = UNKNOWN
    type5_cache_instruction_valid: bool = False
    type13_cache_instruction: ExactWord | _UnknownValue = UNKNOWN
    type13_cache_instruction_valid: bool = False

    @classmethod
    def reset(cls) -> "ProgramClientsOwnerControlState":
        return cls()


def _share_pm_architecture(
    type5: ComputePMState,
    type13: ShifterPMState,
    *,
    source: ComputePMState | ShifterPMState,
) -> tuple[ComputePMState, ShifterPMState]:
    """Copy one selected PM architectural image into both retained clients."""

    common = dict(
        primary=source.primary,
        alternate=source.alternate,
        status=source.status,
        dag=source.dag,
        px=source.px,
    )
    return (
        ComputePMState(
            **common,
            recovery=type5.recovery,
            pending=type5.pending,
        ),
        ShifterPMState(
            **common,
            recovery=type13.recovery,
            pending=type13.pending,
        ),
    )


def _pm_status_from_architecture(
    architecture: ArchitecturalState,
) -> StatusRegisters:
    return StatusRegisters(
        astat=(
            ASTATState.from_word(architecture.astat)
            if isinstance(architecture.astat, ExactWord)
            else ASTATState()
        ),
        mstat=architecture.mstat,
        icntl=architecture.icntl,
        imask=architecture.imask,
    )


def _pm_dag_from_architecture(
    architecture: ArchitecturalState,
) -> DAGRegisterState:
    def bounded(values: tuple[object, ...]) -> tuple[int | None, ...]:
        return tuple(
            value.value if isinstance(value, ExactWord) else None
            for value in values
        )

    return DAGRegisterState(
        i=bounded(architecture.dag.i),
        m=bounded(architecture.dag.m),
        l=bounded(architecture.dag.l),
    )


def _share_linear_architecture(
    type5: ComputePMState,
    type13: ShifterPMState,
    *,
    architecture: ArchitecturalState,
) -> tuple[ComputePMState, ShifterPMState]:
    common = dict(
        primary=architecture.primary,
        alternate=architecture.alternate,
        status=_pm_status_from_architecture(architecture),
        dag=_pm_dag_from_architecture(architecture),
        px=architecture.px,
    )
    return (
        ComputePMState(
            **common,
            recovery=type5.recovery,
            pending=type5.pending,
        ),
        ShifterPMState(
            **common,
            recovery=type13.recovery,
            pending=type13.pending,
        ),
    )


def _architecture_from_pm(
    architecture: ArchitecturalState,
    source: ComputePMState | ShifterPMState,
    *,
    mstat_valid_mask: int,
) -> ArchitecturalState:
    def architectural(
        values: tuple[int | None, ...],
    ) -> tuple[ExactWord | _UnknownValue, ...]:
        return tuple(
            UNKNOWN if value is None else ExactWord(14, value)
            for value in values
        )

    astat = (
        source.status.astat.to_word()
        if source.status.astat.is_fully_known
        else UNKNOWN
    )
    return replace(
        architecture,
        primary=source.primary,
        alternate=source.alternate,
        dag=DAGRegisters(
            i=architectural(source.dag.i),
            m=architectural(source.dag.m),
            l=architectural(source.dag.l),
        ),
        px=source.px,
        astat=astat,
        mstat=source.status.mstat,
        mstat_valid_mask=mstat_valid_mask,
        imask=source.status.imask,
        icntl=source.status.icntl,
    )


@dataclass(frozen=True)
class ProgramClientsOwnerControlCycleResult:
    state: ProgramClientsOwnerControlState
    linear: LinearFetchClientCycleResult
    type5: ComputePMCycleResult
    type13: ShifterPMCycleResult
    cache: InstructionCacheCycleResult
    interface: ProgramOwnerBusControlCycleResult
    halt: HaltControlCycleResult
    issue_boundary: bool = False
    client_execute_conflict: bool = False
    automatic_pm_instruction_issue: bool = False
    automatic_pm_instruction_retire: bool = False
    automatic_pm_flow_blocked: bool = False
    halt_pm_data_cycle: bool = False
    halt_late_force_request: bool = False
    halt_br_conflict: bool = False
    halt_owner_conflict: bool = False
    halt_attachment_conflict: bool = False
    cache_fill: bool = False
    type5_request_presented: bool = False
    type5_retry_pending: bool = False
    type13_request_presented: bool = False
    type13_retry_pending: bool = False
    type5_next_instruction: ExactWord | _UnknownValue = UNKNOWN
    type5_next_instruction_valid: bool = False
    type13_next_instruction: ExactWord | _UnknownValue = UNKNOWN
    type13_next_instruction_valid: bool = False
    integration_conflict: bool = False


def _request(result: ComputePMCycleResult | ShifterPMCycleResult) -> ProgramBusRequest:
    return ProgramBusRequest(
        address=(
            ExactWord(14, result.pm_address)
            if result.pm_address_known
            else UNKNOWN
        ),
        data_access=result.pm_data_access,
        write=result.pm_write,
        write_data=(
            ExactWord(24, result.pm_write_data)
            if result.pm_write_data_known
            else UNKNOWN
        ),
    )


def apply_program_clients_owner_control_cycle(
    state: ProgramClientsOwnerControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    br_n: bool = True,
    halt_n: bool = True,
    dmack: bool = True,
    irq_n: int = 0xF,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    automatic_pm_flow: bool = False,
    type5_execute: bool = False,
    type5_opcode: int = 0,
    type5_next_fetch_address: ExactWord | _UnknownValue = UNKNOWN,
    type13_execute: bool = False,
    type13_opcode: int = 0,
    type13_next_fetch_address: ExactWord | _UnknownValue = UNKNOWN,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
    setup_sb: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    setup_px: ExactWord | None = None,
) -> ProgramClientsOwnerControlCycleResult:
    """Apply one physical phase clock to the bounded three-client/HALT owner."""

    phase = LogicalPhase(phase)
    halt_br_conflict = bool(
        not reset
        and (
            (not halt_n and not br_n)
            or (
                not halt_n
                and state.interface.control.mode is not BusControlMode.IDLE
            )
            or (
                not br_n
                and state.halt.mode is not HaltControlMode.RUNNING
            )
        )
    )
    effective_halt_n = bool(
        True if reset else (
            halt_n
            or state.interface.control.mode is not BusControlMode.IDLE
            or not br_n
        )
    )
    effective_br_n = bool(
        br_n if reset else (
            br_n
            or state.halt.mode is not HaltControlMode.RUNNING
            or not halt_n
        )
    )
    retained_bus = state.interface.owner_bus.bus
    halt_pm_data_cycle = bool(
        retained_bus.active and retained_bus.data_access
    )
    halt = apply_halt_control_cycle(
        state.halt,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        halt_n=effective_halt_n,
        dmack=dmack,
        pm_data_cycle=halt_pm_data_cycle,
    )
    halt_late_force_request = bool(
        not reset
        and (
            state.halt.mode is HaltControlMode.FORCE_FETCH_PENDING
            or (halt.halt_recognized and halt_pm_data_cycle)
        )
    )
    halt_owner_conflict = bool(
        halt.halt_recognized and not retained_bus.active
    )

    preview = apply_program_owner_bus_control_cycle(
        state.interface,
        reset=reset,
        phase=phase,
        phase_advance=halt.effective_phase_advance,
        br_n=effective_br_n,
        pmd_read_data=pmd_read_data,
    )
    issue_boundary = bool(
        not reset
        and not preview.control.instruction_issue_inhibit
        and not preview.native_bus_relinquished
        and phase == LogicalPhase.STATE_8
        and halt.effective_phase_advance
    )
    execute_conflict = bool(
        not reset
        and not automatic_pm_flow
        and type5_execute
        and type13_execute
    )
    automatic_control_conflict = bool(
        not reset
        and automatic_pm_flow
        and (type5_execute or type13_execute)
    )
    retained_opcode = (
        state.linear.instruction.value
        if state.linear.instruction_valid
        and isinstance(state.linear.instruction, ExactWord)
        else 0
    )
    selected_type5_opcode = (
        retained_opcode if automatic_pm_flow else type5_opcode
    )
    selected_type13_opcode = (
        retained_opcode if automatic_pm_flow else type13_opcode
    )
    automatic_type5_instruction = bool(
        automatic_pm_flow
        and state.linear.instruction_valid
        and decode_compute_pm(retained_opcode) is not None
    )
    automatic_type13_instruction = bool(
        automatic_pm_flow
        and state.linear.instruction_valid
        and decode_shifter_pm(retained_opcode) is not None
    )
    automatic_pm_instruction_active = bool(
        automatic_type5_instruction or automatic_type13_instruction
    )
    mstat_client_conflict = bool(
        not reset
        and issue_boundary
        and state.linear.architecture.mstat_valid_mask != 0xF
        and (
            (automatic_pm_flow and automatic_pm_instruction_active)
            or (not automatic_pm_flow and (type5_execute or type13_execute))
        )
    )
    automatic_sequential_allowed = bool(
        not state.linear.architecture.loop_stack
        and not state.linear.pending
        and not state.linear.interrupt_vectoring
        and instruction_setup is None
    )
    selected_type5_next = (
        ExactWord(14, (state.linear.architecture.pc.value + 1) & 0x3FFF)
        if automatic_pm_flow else type5_next_fetch_address
    )
    selected_type13_next = (
        ExactWord(14, (state.linear.architecture.pc.value + 1) & 0x3FFF)
        if automatic_pm_flow else type13_next_fetch_address
    )
    execute_type5 = bool(
        automatic_type5_instruction
        and automatic_sequential_allowed
        and issue_boundary
        and state.type5.pending is None
        and state.type5.recovery is None
        and state.type13.pending is None
        and state.type13.recovery is None
        and not mstat_client_conflict
    ) if automatic_pm_flow else bool(
        type5_execute and not execute_conflict and issue_boundary
        and not mstat_client_conflict
    )
    execute_type13 = bool(
        automatic_type13_instruction
        and automatic_sequential_allowed
        and issue_boundary
        and state.type5.pending is None
        and state.type5.recovery is None
        and state.type13.pending is None
        and state.type13.recovery is None
        and not mstat_client_conflict
    ) if automatic_pm_flow else bool(
        type13_execute and not execute_conflict and issue_boundary
        and not mstat_client_conflict
    )

    lookup_address: ExactWord | _UnknownValue = UNKNOWN
    if execute_type5 and not execute_type13:
        lookup_address = selected_type5_next
    elif execute_type13 and not execute_type5:
        lookup_address = selected_type13_next
    lookup = lookup_instruction_cache(state.cache, lookup_address)

    cache_fill = bool(
        any(
            (
                preview.owner_bus.fetch_completion,
                preview.owner_bus.type5_completion,
                preview.owner_bus.type13_completion,
            )
        )
        and retained_bus.active
        and not retained_bus.data_access
    )
    cache_result = apply_instruction_cache_cycle(
        state.cache,
        reset=reset,
        fill=cache_fill,
        fetch_address=retained_bus.address,
        fetch_instruction=pmd_read_data,
    )

    common = dict(
        reset=reset,
        pm_read_data=pmd_read_data,
        cache_next_instruction_valid=lookup.instruction_valid,
        setup_astat=setup_astat if issue_boundary else None,
        setup_mstat=setup_mstat if issue_boundary else None,
        setup_dreg=setup_dreg if issue_boundary else None,
        setup_dag=setup_dag if issue_boundary else None,
        setup_px=setup_px if issue_boundary else None,
        force_instruction_fetch=halt_late_force_request,
    )
    type5 = apply_compute_pm_cycle(
        state.type5,
        execute=execute_type5,
        opcode=selected_type5_opcode,
        next_fetch_address=selected_type5_next,
        pm_cycle_complete=preview.owner_bus.type5_completion,
        setup_af=setup_af if issue_boundary else None,
        setup_mf=setup_mf if issue_boundary else None,
        **common,
    )
    type13 = apply_shifter_pm_cycle(
        state.type13,
        execute=execute_type13,
        opcode=selected_type13_opcode,
        next_fetch_address=selected_type13_next,
        pm_cycle_complete=preview.owner_bus.type13_completion,
        setup_sb=setup_sb if issue_boundary else None,
        **common,
    )

    type5_external_valid = type5.fetched_instruction_known
    type5_cached_valid = bool(
        type5.data_action_complete
        and type5.instruction_complete
        and state.type5_cache_instruction_valid
    )
    type5_next_valid = type5_external_valid or type5_cached_valid
    type5_next = (
        ExactWord(24, type5.fetched_instruction)
        if type5_external_valid
        else state.type5_cache_instruction
    )
    type13_external_valid = type13.fetched_instruction_known
    type13_cached_valid = bool(
        type13.data_action_complete
        and type13.instruction_complete
        and state.type13_cache_instruction_valid
    )
    type13_next_valid = type13_external_valid or type13_cached_valid
    type13_next = (
        ExactWord(24, type13.fetched_instruction)
        if type13_external_valid
        else state.type13_cache_instruction
    )
    automatic_pm_completion = bool(
        automatic_pm_flow
        and (type5.instruction_complete or type13.instruction_complete)
    )
    automatic_pm_next = (
        type5_next if type5.instruction_complete else type13_next
    )

    linear_preview = apply_linear_fetch_client_cycle(
        state.linear,
        reset=reset,
        phase=phase,
        phase_advance=halt.effective_phase_advance,
        instruction_issue_inhibit=(
            preview.control.instruction_issue_inhibit
            or halt.instruction_issue_inhibit
        ),
        bus_relinquished=preview.native_bus_relinquished,
        instruction_setup=instruction_setup,
        pm_completion_event=preview.owner_bus.fetch_completion,
        pmd_read_data=pmd_read_data,
        irq_n=irq_n,
        pm_instruction_active=automatic_pm_instruction_active,
        pm_instruction_complete=automatic_pm_completion,
        pm_instruction_next_opcode=(
            automatic_pm_next
            if (type5_next_valid or type13_next_valid) else UNKNOWN
        ),
    )
    fetch_request = (
        ProgramBusRequest.fetch(linear_preview.fetch_address.value)
        if linear_preview.fetch_request_presented
        else None
    )
    type5_request = (
        _request(type5) if issue_boundary and type5.pm_select else None
    )
    type13_request = (
        _request(type13) if issue_boundary and type13.pm_select else None
    )
    interface = apply_program_owner_bus_control_cycle(
        state.interface,
        reset=reset,
        phase=phase,
        phase_advance=halt.effective_phase_advance,
        br_n=effective_br_n,
        fetch_request=fetch_request,
        type5_request=type5_request,
        type13_request=type13_request,
        pmd_read_data=pmd_read_data,
    )
    linear = apply_linear_fetch_client_cycle(
        state.linear,
        reset=reset,
        phase=phase,
        phase_advance=halt.effective_phase_advance,
        instruction_issue_inhibit=(
            preview.control.instruction_issue_inhibit
            or halt.instruction_issue_inhibit
        ),
        bus_relinquished=preview.native_bus_relinquished,
        instruction_setup=instruction_setup,
        pm_request_accepted=interface.owner_bus.fetch_accepted,
        pm_completion_event=preview.owner_bus.fetch_completion,
        pmd_read_data=pmd_read_data,
        irq_n=irq_n,
        pm_instruction_active=automatic_pm_instruction_active,
        pm_instruction_complete=automatic_pm_completion,
        pm_instruction_next_opcode=(
            automatic_pm_next
            if (type5_next_valid or type13_next_valid) else UNKNOWN
        ),
    )

    type5_cache_word = state.type5_cache_instruction
    type5_cache_valid = state.type5_cache_instruction_valid
    if reset:
        type5_cache_word = UNKNOWN
        type5_cache_valid = False
    elif type5.accepted:
        type5_cache_word = lookup.instruction
        type5_cache_valid = lookup.instruction_valid
    elif type5.instruction_complete:
        type5_cache_valid = False

    type13_cache_word = state.type13_cache_instruction
    type13_cache_valid = state.type13_cache_instruction_valid
    if reset:
        type13_cache_word = UNKNOWN
        type13_cache_valid = False
    elif type13.accepted:
        type13_cache_word = lookup.instruction
        type13_cache_valid = lookup.instruction_valid
    elif type13.instruction_complete:
        type13_cache_valid = False

    shared_source: ComputePMState | ShifterPMState = state.type5
    pm_architecture_changed = False
    if reset:
        shared_source = type5.state
        pm_architecture_changed = True
    elif type5.data_action_complete or setup_af is not None or setup_mf is not None:
        shared_source = type5.state
        pm_architecture_changed = True
    elif type13.data_action_complete or setup_sb is not None:
        shared_source = type13.state
        pm_architecture_changed = True
    elif any(
        item is not None
        for item in (
            setup_astat,
            setup_mstat,
            setup_dreg,
            setup_dag,
            setup_px,
        )
    ):
        shared_source = type5.state
        pm_architecture_changed = True

    shared_linear_state = linear.state
    if pm_architecture_changed:
        shared_linear_state = replace(
            linear.state,
            architecture=_architecture_from_pm(
                linear.state.architecture,
                shared_source,
                mstat_valid_mask=(
                    0xF
                    if reset or setup_mstat is not None
                    else linear.state.architecture.mstat_valid_mask
                ),
            ),
        )
        shared_type5, shared_type13 = _share_pm_architecture(
            type5.state,
            type13.state,
            source=shared_source,
        )
    elif (
        linear.interrupt_entry_event
        or (
            linear.retire_event
            and isinstance(state.linear.instruction, ExactWord)
            and state.linear.instruction.value != 0
        )
    ):
        shared_type5, shared_type13 = _share_linear_architecture(
            type5.state,
            type13.state,
            architecture=linear.state.architecture,
        )
    else:
        shared_type5, shared_type13 = _share_pm_architecture(
            type5.state,
            type13.state,
            source=state.type5 if not reset else type5.state,
        )
    linear = replace(linear, state=shared_linear_state)

    next_state = ProgramClientsOwnerControlState(
        linear=shared_linear_state,
        type5=shared_type5,
        type13=shared_type13,
        cache=cache_result.state,
        interface=interface.state,
        halt=halt.state,
        type5_cache_instruction=type5_cache_word,
        type5_cache_instruction_valid=type5_cache_valid,
        type13_cache_instruction=type13_cache_word,
        type13_cache_instruction_valid=type13_cache_valid,
    )
    halt_attachment_conflict = bool(
        halt.force_fetch_issue
        and not (
            (interface.owner_bus.type5_accepted and type5.recovery_fetch)
            or (interface.owner_bus.type13_accepted and type13.recovery_fetch)
        )
    )
    integration_conflict = bool(
        execute_conflict
        or automatic_control_conflict
        or mstat_client_conflict
        or linear.phase_conflict
        or linear.integration_conflict
        or linear.internal_conflict
        or type5.integration_conflict
        or type13.integration_conflict
        or interface.owner_bus.request_conflict
        or interface.owner_bus.request_out_of_phase
        or halt.phase_conflict
        or halt_br_conflict
        or halt_owner_conflict
        or halt_attachment_conflict
    )
    return ProgramClientsOwnerControlCycleResult(
        state=next_state,
        linear=linear,
        type5=type5,
        type13=type13,
        cache=cache_result,
        interface=interface,
        halt=halt,
        issue_boundary=issue_boundary,
        client_execute_conflict=execute_conflict,
        automatic_pm_instruction_issue=bool(
            automatic_pm_flow
            and (
                (type5.accepted and interface.owner_bus.type5_accepted)
                or (type13.accepted and interface.owner_bus.type13_accepted)
            )
        ),
        automatic_pm_instruction_retire=bool(
            automatic_pm_completion and linear.retire_event
        ),
        automatic_pm_flow_blocked=bool(
            automatic_pm_flow and linear.pm_instruction_flow_blocked
        ),
        halt_pm_data_cycle=halt_pm_data_cycle,
        halt_late_force_request=halt_late_force_request,
        halt_br_conflict=halt_br_conflict,
        halt_owner_conflict=halt_owner_conflict,
        halt_attachment_conflict=halt_attachment_conflict,
        cache_fill=cache_fill,
        type5_request_presented=type5_request is not None,
        type5_retry_pending=bool(
            type5_request is not None and not interface.owner_bus.type5_accepted
        ),
        type13_request_presented=type13_request is not None,
        type13_retry_pending=bool(
            type13_request is not None and not interface.owner_bus.type13_accepted
        ),
        type5_next_instruction=type5_next,
        type5_next_instruction_valid=type5_next_valid,
        type13_next_instruction=type13_next,
        type13_next_instruction_valid=type13_next_valid,
        integration_conflict=integration_conflict,
    )
