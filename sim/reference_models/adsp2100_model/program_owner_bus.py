"""Independent fail-closed owner selector for the native program bus.

The original device has one external PM interface shared by instruction fetch
and PM data transfers.  This bounded composition establishes mutual exclusion
without assigning an undocumented priority when requesters collide.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .model import ExactWord, UNKNOWN
from .phase import LogicalPhase
from .program_bus import (
    ProgramBusCycleResult,
    ProgramBusRequest,
    ProgramBusState,
    apply_program_bus_cycle,
)


class ProgramBusOwner(IntEnum):
    NONE = 0
    FETCH = 1
    TYPE5_PM_DATA = 2
    TYPE13_PM_DATA = 3


@dataclass(frozen=True)
class ProgramOwnerBusState:
    bus: ProgramBusState = ProgramBusState()
    owner: ProgramBusOwner = ProgramBusOwner.NONE

    @classmethod
    def reset(cls) -> "ProgramOwnerBusState":
        return cls()


@dataclass(frozen=True)
class ProgramOwnerBusCycleResult:
    state: ProgramOwnerBusState
    bus: ProgramBusCycleResult
    request_conflict: bool
    request_out_of_phase: bool
    accepted_owner: ProgramBusOwner
    completion_owner: ProgramBusOwner
    fetch_accepted: bool
    type5_accepted: bool
    type13_accepted: bool
    fetch_completion: bool
    type5_completion: bool
    type13_completion: bool


def apply_program_owner_bus_cycle(
    state: ProgramOwnerBusState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    fetch_request: ProgramBusRequest | None = None,
    type5_request: ProgramBusRequest | None = None,
    type13_request: ProgramBusRequest | None = None,
    pmd_read_data: ExactWord | object = UNKNOWN,
    bus_relinquished: bool = False,
) -> ProgramOwnerBusCycleResult:
    """Apply one clock to the selector and its single native PM controller."""

    phase = LogicalPhase(phase)
    requests = (
        (ProgramBusOwner.FETCH, fetch_request),
        (ProgramBusOwner.TYPE5_PM_DATA, type5_request),
        (ProgramBusOwner.TYPE13_PM_DATA, type13_request),
    )
    asserted = [(owner, request) for owner, request in requests if request]
    ready = bool(
        not reset
        and not bus_relinquished
        and phase == LogicalPhase.STATE_8
        and phase_advance
    )
    conflict = ready and len(asserted) > 1
    out_of_phase = bool(asserted) and not ready
    selected_owner = (
        asserted[0][0] if ready and len(asserted) == 1 else ProgramBusOwner.NONE
    )
    selected_request = asserted[0][1] if selected_owner else None

    bus_result = apply_program_bus_cycle(
        state.bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        request=selected_request,
        pmd_read_data=pmd_read_data,
        bus_relinquished=bus_relinquished,
    )
    accepted_owner = (
        selected_owner if bus_result.request_accepted else ProgramBusOwner.NONE
    )
    completion_owner = (
        state.owner if bus_result.completion_event else ProgramBusOwner.NONE
    )

    next_owner = state.owner
    if reset:
        next_owner = ProgramBusOwner.NONE
    elif (
        phase == LogicalPhase.STATE_8
        and phase_advance
        and not bus_relinquished
    ):
        next_owner = accepted_owner
    next_state = ProgramOwnerBusState(bus=bus_result.state, owner=next_owner)

    return ProgramOwnerBusCycleResult(
        state=next_state,
        bus=bus_result,
        request_conflict=conflict,
        request_out_of_phase=out_of_phase,
        accepted_owner=accepted_owner,
        completion_owner=completion_owner,
        fetch_accepted=accepted_owner == ProgramBusOwner.FETCH,
        type5_accepted=accepted_owner == ProgramBusOwner.TYPE5_PM_DATA,
        type13_accepted=accepted_owner == ProgramBusOwner.TYPE13_PM_DATA,
        fetch_completion=completion_owner == ProgramBusOwner.FETCH,
        type5_completion=completion_owner == ProgramBusOwner.TYPE5_PM_DATA,
        type13_completion=completion_owner == ProgramBusOwner.TYPE13_PM_DATA,
    )
