"""Original Type 3 state slice attached to native ADSP-2100 DM phases."""

from __future__ import annotations

from dataclasses import dataclass, field

from .data_bus import (
    DataBusCycleResult,
    DataBusRequest,
    DataBusState,
    apply_data_bus_cycle,
)
from .direct_dm_slice import (
    DirectDMCycleResult,
    DirectDMSliceState,
    apply_direct_dm_cycle,
)
from .internal_move_slice import InternalMoveSetup
from .model import ExactWord, UNKNOWN
from .phase import LogicalPhase


@dataclass(frozen=True)
class DirectDMNativeState:
    core: DirectDMSliceState = field(default_factory=DirectDMSliceState.reset)
    bus: DataBusState = field(default_factory=DataBusState.reset)

    @classmethod
    def reset(cls) -> "DirectDMNativeState":
        return cls()


@dataclass(frozen=True)
class DirectDMNativeCycleResult:
    state: DirectDMNativeState
    core: DirectDMCycleResult
    bus: DataBusCycleResult
    issue_boundary: bool = False
    phase_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_direct_dm_native_cycle(
    state: DirectDMNativeState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    bus_relinquished: bool = False,
    execute: bool = False,
    opcode: int = 0,
    dm_ack: bool = True,
    dmd_read_data: ExactWord | object = UNKNOWN,
    setup: InternalMoveSetup | None = None,
) -> DirectDMNativeCycleResult:
    """Apply one FPGA clock of the bounded Type 3/native-DM attachment."""

    phase = LogicalPhase(phase)
    issue_boundary = bool(
        not reset
        and not bus_relinquished
        and phase_advance
        and phase == LogicalPhase.STATE_8
    )
    controls_present = execute or setup is not None
    phase_conflict = not reset and controls_present and not issue_boundary

    bus_preview = apply_data_bus_cycle(
        state.bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        dm_ack=dm_ack,
        dmd_read_data=dmd_read_data,
        bus_relinquished=bus_relinquished,
    )
    core_result = apply_direct_dm_cycle(
        state.core,
        reset=reset,
        execute=execute and issue_boundary,
        opcode=opcode,
        dm_ack=bus_preview.completion_event,
        dm_read_data=dmd_read_data,
        setup=setup if issue_boundary else None,
    )

    request: DataBusRequest | None = None
    if core_result.dm_select:
        request = DataBusRequest(
            address=ExactWord(14, core_result.dm_address),
            write=core_result.dm_write,
            write_data=(
                ExactWord(16, core_result.dm_write_data)
                if core_result.dm_write_data_known else UNKNOWN
            ),
        )
    bus_result = apply_data_bus_cycle(
        state.bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        request=request,
        dm_ack=dm_ack,
        dmd_read_data=dmd_read_data,
        bus_relinquished=bus_relinquished,
    )
    attachment_conflict = bool(
        core_result.accepted != bus_result.request_accepted
        or (
            core_result.accepted
            and not (issue_boundary and core_result.dm_select)
        )
        or core_result.instruction_complete
        != (bus_result.completion_event and core_result.dm_select)
        or bus_result.read_sample_event
        != (bus_result.completion_event and core_result.dm_read)
    )
    return DirectDMNativeCycleResult(
        state=DirectDMNativeState(
            core=core_result.state,
            bus=bus_result.state,
        ),
        core=core_result,
        bus=bus_result,
        issue_boundary=issue_boundary,
        phase_conflict=phase_conflict,
        attachment_conflict=attachment_conflict,
        integration_conflict=(
            phase_conflict
            or attachment_conflict
            or core_result.integration_conflict
        ),
    )
