"""Type 4 ALU/MAC-plus-DM attached to the original native DM phases."""

from __future__ import annotations

from dataclasses import dataclass, field

from .compute_dm import (
    ComputeDMCycleResult,
    ComputeDMState,
    apply_compute_dm_cycle,
)
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


@dataclass(frozen=True)
class ComputeDMNativeState:
    core: ComputeDMState = field(default_factory=ComputeDMState.reset)
    bus: DataBusState = field(default_factory=DataBusState.reset)

    @classmethod
    def reset(cls) -> "ComputeDMNativeState":
        return cls()


@dataclass(frozen=True)
class ComputeDMNativeCycleResult:
    state: ComputeDMNativeState
    core: ComputeDMCycleResult
    bus: DataBusCycleResult
    issue_boundary: bool = False
    phase_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_compute_dm_native_cycle(
    state: ComputeDMNativeState,
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
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    inspect_probe: bool = False,
) -> ComputeDMNativeCycleResult:
    """Apply one FPGA clock of the bounded Type 4/native-DM attachment."""

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
        or setup_af is not None
        or setup_mf is not None
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
    core_result = apply_compute_dm_cycle(
        state.core,
        reset=reset,
        execute=execute and issue_boundary,
        opcode=opcode,
        dm_ack=bus_preview.completion_event,
        dm_read_data=dmd_read_data,
        setup_astat=setup_astat if issue_boundary else None,
        setup_mstat=setup_mstat if issue_boundary else None,
        setup_dreg=setup_dreg if issue_boundary else None,
        setup_af=setup_af if issue_boundary else None,
        setup_mf=setup_mf if issue_boundary else None,
        setup_dag=setup_dag if issue_boundary else None,
        inspect_probe=inspect_probe,
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
    return ComputeDMNativeCycleResult(
        state=ComputeDMNativeState(
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
