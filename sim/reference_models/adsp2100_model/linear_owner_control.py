"""Retained ordinary-fetch client on shared PM ownership and BR/BG."""

from __future__ import annotations

from dataclasses import dataclass, field

from .linear_core import (
    LinearCoreState,
    LinearFetchClientCycleResult,
    apply_linear_fetch_client_cycle,
)
from .model import ExactWord, UNKNOWN, _UnknownValue
from .phase import LogicalPhase
from .program_bus import ProgramBusRequest
from .program_owner_bus import ProgramBusOwner
from .program_owner_bus_control import (
    ProgramOwnerBusControlCycleResult,
    ProgramOwnerBusControlState,
    apply_program_owner_bus_control_cycle,
)


@dataclass(frozen=True)
class LinearOwnerControlState:
    core: LinearCoreState = field(default_factory=LinearCoreState.reset)
    interface: ProgramOwnerBusControlState = field(
        default_factory=ProgramOwnerBusControlState.reset
    )

    @classmethod
    def reset(cls) -> "LinearOwnerControlState":
        return cls()


@dataclass(frozen=True)
class LinearOwnerControlCycleResult:
    state: LinearOwnerControlState
    core: LinearFetchClientCycleResult
    interface: ProgramOwnerBusControlCycleResult
    fetch_retry_pending: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_linear_owner_control_cycle(
    state: LinearOwnerControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    br_n: bool = True,
    irq_n: int = 0xF,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    type5_request: ProgramBusRequest | None = None,
    type13_request: ProgramBusRequest | None = None,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
) -> LinearOwnerControlCycleResult:
    """Apply one bounded linear-fetch/shared-PM/BR-BG clock."""

    phase = LogicalPhase(phase)
    preview = apply_program_owner_bus_control_cycle(
        state.interface,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        br_n=br_n,
        pmd_read_data=pmd_read_data,
    )
    client_preview = apply_linear_fetch_client_cycle(
        state.core,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        instruction_issue_inhibit=preview.control.instruction_issue_inhibit,
        bus_relinquished=preview.native_bus_relinquished,
        irq_n=irq_n,
        instruction_setup=instruction_setup,
        pm_completion_event=preview.owner_bus.fetch_completion,
        pmd_read_data=pmd_read_data,
    )
    fetch_request = (
        ProgramBusRequest.fetch(client_preview.fetch_address.value)
        if client_preview.fetch_request_presented
        else None
    )
    interface = apply_program_owner_bus_control_cycle(
        state.interface,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        br_n=br_n,
        fetch_request=fetch_request,
        type5_request=type5_request,
        type13_request=type13_request,
        pmd_read_data=pmd_read_data,
    )
    client = apply_linear_fetch_client_cycle(
        state.core,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        instruction_issue_inhibit=preview.control.instruction_issue_inhibit,
        bus_relinquished=preview.native_bus_relinquished,
        irq_n=irq_n,
        instruction_setup=instruction_setup,
        pm_request_accepted=interface.owner_bus.fetch_accepted,
        pm_completion_event=preview.owner_bus.fetch_completion,
        pmd_read_data=pmd_read_data,
    )
    retry = bool(
        client.fetch_request_presented
        and not interface.owner_bus.fetch_accepted
    )
    attachment_conflict = bool(
        interface.owner_bus.completion_owner
        != preview.owner_bus.completion_owner
        or interface.owner_bus.fetch_accepted
        and interface.owner_bus.accepted_owner != ProgramBusOwner.FETCH
        or preview.owner_bus.fetch_completion and not client.retire_event
    )

    return LinearOwnerControlCycleResult(
        state=LinearOwnerControlState(client.state, interface.state),
        core=client,
        interface=interface,
        fetch_retry_pending=retry,
        attachment_conflict=attachment_conflict,
        integration_conflict=bool(
            client.integration_conflict
            or client.phase_conflict
            or attachment_conflict
            or interface.owner_bus.request_conflict
            or interface.owner_bus.request_out_of_phase
        ),
    )
