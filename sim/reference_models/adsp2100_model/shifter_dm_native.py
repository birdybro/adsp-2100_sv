"""Type 12 shifter-plus-DM attached to the original native DM phases."""

from __future__ import annotations

from dataclasses import dataclass, field

from .data_bus import (
    DataBusCycleResult,
    DataBusRequest,
    DataBusState,
    apply_data_bus_cycle,
)
from .model import ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup
from .phase import LogicalPhase
from .registers import DREGWrite
from .shifter_dm import (
    ShifterDMCycleResult,
    ShifterDMState,
    apply_shifter_dm_cycle,
)


@dataclass(frozen=True)
class ShifterDMNativeState:
    core: ShifterDMState = field(default_factory=ShifterDMState.reset)
    bus: DataBusState = field(default_factory=DataBusState.reset)

    @classmethod
    def reset(cls) -> "ShifterDMNativeState":
        return cls()


@dataclass(frozen=True)
class ShifterDMNativeCycleResult:
    state: ShifterDMNativeState
    core: ShifterDMCycleResult
    bus: DataBusCycleResult
    issue_boundary: bool = False
    phase_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_shifter_dm_native_cycle(
    state: ShifterDMNativeState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    bus_relinquished: bool = False,
    execute: bool = False,
    opcode: int = 0,
    dm_ack: bool = True,
    dmd_read_data: ExactWord | object = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_sb: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
) -> ShifterDMNativeCycleResult:
    """Apply one FPGA clock of the bounded Type 12/native-DM attachment."""

    phase = LogicalPhase(phase)
    issue_boundary = bool(
        not reset
        and not bus_relinquished
        and phase_advance
        and phase == LogicalPhase.STATE_8
    )
    controls_present = bool(
        execute
        or setup_astat is not None
        or setup_mstat is not None
        or setup_dreg is not None
        or setup_sb is not None
        or setup_dag is not None
    )
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
    core_result = apply_shifter_dm_cycle(
        state.core,
        reset=reset,
        execute=execute and issue_boundary,
        opcode=opcode,
        dm_ack=bus_preview.completion_event,
        dm_read_data=dmd_read_data,
        setup_astat=setup_astat if issue_boundary else None,
        setup_mstat=setup_mstat if issue_boundary else None,
        setup_dreg=setup_dreg if issue_boundary else None,
        setup_sb=setup_sb if issue_boundary else None,
        setup_dag=setup_dag if issue_boundary else None,
    )

    request: DataBusRequest | None = None
    if core_result.dm_select:
        request = DataBusRequest(
            address=(
                ExactWord(14, core_result.dm_address)
                if core_result.dm_address_known
                else UNKNOWN
            ),
            write=core_result.dm_write,
            write_data=(
                ExactWord(16, core_result.dm_write_data)
                if core_result.dm_write_data_known
                else UNKNOWN
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
    return ShifterDMNativeCycleResult(
        state=ShifterDMNativeState(
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
