"""Composition model for shared PM ownership and original BR/BG control."""

from __future__ import annotations

from dataclasses import dataclass, field

from .bus_control import (
    BusControlCycleResult,
    BusControlState,
    apply_bus_control_cycle,
)
from .model import ExactWord, UNKNOWN, _UnknownValue
from .phase import LogicalPhase
from .program_bus import ProgramBusRequest
from .program_owner_bus import (
    ProgramOwnerBusCycleResult,
    ProgramOwnerBusState,
    apply_program_owner_bus_cycle,
)


@dataclass(frozen=True)
class ProgramOwnerBusControlState:
    owner_bus: ProgramOwnerBusState = field(
        default_factory=ProgramOwnerBusState.reset
    )
    control: BusControlState = field(default_factory=BusControlState)

    @classmethod
    def reset(cls) -> "ProgramOwnerBusControlState":
        return cls()


@dataclass(frozen=True)
class ProgramOwnerBusControlCycleResult:
    state: ProgramOwnerBusControlState
    owner_bus: ProgramOwnerBusCycleResult
    control: BusControlCycleResult
    native_bg_n: bool
    native_bus_relinquished: bool
    request_ready: bool
    request_blocked: bool


def apply_program_owner_bus_control_cycle(
    state: ProgramOwnerBusControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    br_n: bool = True,
    fetch_request: ProgramBusRequest | None = None,
    type5_request: ProgramBusRequest | None = None,
    type13_request: ProgramBusRequest | None = None,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
) -> ProgramOwnerBusControlCycleResult:
    """Apply one shared phase boundary to the two independent controllers."""

    phase = LogicalPhase(phase)
    control = apply_bus_control_cycle(
        state.control,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        br_n=br_n,
    )
    native_bg_n = br_n if reset else control.bg_n
    native_bus_relinquished = (
        not br_n if reset else control.bus_relinquished
    )
    issue_enabled = not control.instruction_issue_inhibit
    requester_present = any(
        request is not None
        for request in (fetch_request, type5_request, type13_request)
    )
    owner_bus = apply_program_owner_bus_cycle(
        state.owner_bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        fetch_request=fetch_request if issue_enabled else None,
        type5_request=type5_request if issue_enabled else None,
        type13_request=type13_request if issue_enabled else None,
        pmd_read_data=pmd_read_data,
        bus_relinquished=native_bus_relinquished,
    )
    return ProgramOwnerBusControlCycleResult(
        state=ProgramOwnerBusControlState(
            owner_bus=owner_bus.state,
            control=control.state,
        ),
        owner_bus=owner_bus,
        control=control,
        native_bg_n=native_bg_n,
        native_bus_relinquished=native_bus_relinquished,
        request_ready=bool(
            owner_bus.bus.request_ready and issue_enabled
        ),
        request_blocked=bool(
            requester_present and control.instruction_issue_inhibit
        ),
    )
