"""Independent fail-closed owner selector for the native data bus.

The original device has one external DM interface.  This bounded composition
establishes structural mutual exclusion between two requesters without
assigning an undocumented architectural priority when they collide.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .data_bus import (
    DataBusCycleResult,
    DataBusRequest,
    DataBusState,
    apply_data_bus_cycle,
)
from .model import ExactWord, UNKNOWN
from .phase import LogicalPhase


class DataBusOwner(IntEnum):
    NONE = 0
    FETCHED = 1
    COMPANION = 2


@dataclass(frozen=True)
class DataOwnerBusState:
    bus: DataBusState = DataBusState()
    owner: DataBusOwner = DataBusOwner.NONE

    @classmethod
    def reset(cls) -> "DataOwnerBusState":
        return cls()


@dataclass(frozen=True)
class DataOwnerBusCycleResult:
    state: DataOwnerBusState
    bus: DataBusCycleResult
    request_conflict: bool
    request_out_of_phase: bool
    accepted_owner: DataBusOwner
    completion_owner: DataBusOwner
    fetched_accepted: bool
    companion_accepted: bool
    fetched_completion: bool
    companion_completion: bool
    fetched_read_sample: bool
    companion_read_sample: bool
    fetched_dmack_sample: bool
    companion_dmack_sample: bool
    fetched_dmack_accepted: bool
    companion_dmack_accepted: bool
    fetched_wait_extension: bool
    companion_wait_extension: bool


def apply_data_owner_bus_cycle(
    state: DataOwnerBusState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    fetched_request: DataBusRequest | None = None,
    companion_request: DataBusRequest | None = None,
    dm_ack: bool = True,
    dmd_read_data: ExactWord | object = UNKNOWN,
    bus_relinquished: bool = False,
) -> DataOwnerBusCycleResult:
    """Apply one clock to the selector and its single native DM controller."""

    phase = LogicalPhase(phase)
    requests = (
        (DataBusOwner.FETCHED, fetched_request),
        (DataBusOwner.COMPANION, companion_request),
    )
    asserted = [(owner, request) for owner, request in requests if request]
    ready = bool(
        not reset
        and not bus_relinquished
        and phase == LogicalPhase.STATE_8
        and phase_advance
        and (not state.bus.active or state.bus.response_valid)
    )
    conflict = ready and len(asserted) > 1
    out_of_phase = bool(asserted) and not ready
    selected_owner = (
        asserted[0][0] if ready and len(asserted) == 1 else DataBusOwner.NONE
    )
    selected_request = asserted[0][1] if selected_owner else None

    bus_result = apply_data_bus_cycle(
        state.bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        request=selected_request,
        dm_ack=dm_ack,
        dmd_read_data=dmd_read_data,
        bus_relinquished=bus_relinquished,
    )
    accepted_owner = (
        selected_owner if bus_result.request_accepted else DataBusOwner.NONE
    )
    completion_owner = (
        state.owner if bus_result.completion_event else DataBusOwner.NONE
    )

    next_owner = state.owner
    if reset:
        next_owner = DataBusOwner.NONE
    elif bus_result.request_ready:
        next_owner = accepted_owner
    next_state = DataOwnerBusState(bus=bus_result.state, owner=next_owner)

    fetched_owner = state.owner == DataBusOwner.FETCHED
    companion_owner = state.owner == DataBusOwner.COMPANION
    return DataOwnerBusCycleResult(
        state=next_state,
        bus=bus_result,
        request_conflict=conflict,
        request_out_of_phase=out_of_phase,
        accepted_owner=accepted_owner,
        completion_owner=completion_owner,
        fetched_accepted=accepted_owner == DataBusOwner.FETCHED,
        companion_accepted=accepted_owner == DataBusOwner.COMPANION,
        fetched_completion=completion_owner == DataBusOwner.FETCHED,
        companion_completion=completion_owner == DataBusOwner.COMPANION,
        fetched_read_sample=bus_result.read_sample_event and fetched_owner,
        companion_read_sample=(
            bus_result.read_sample_event and companion_owner
        ),
        fetched_dmack_sample=bus_result.dmack_sample_event and fetched_owner,
        companion_dmack_sample=(
            bus_result.dmack_sample_event and companion_owner
        ),
        fetched_dmack_accepted=(
            bus_result.dmack_accepted and fetched_owner
        ),
        companion_dmack_accepted=(
            bus_result.dmack_accepted and companion_owner
        ),
        fetched_wait_extension=(
            bus_result.wait_extension_event and fetched_owner
        ),
        companion_wait_extension=(
            bus_result.wait_extension_event and companion_owner
        ),
    )
