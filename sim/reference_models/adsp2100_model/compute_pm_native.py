"""Independent Type 5/cache composition with native PM logical phases."""

from __future__ import annotations

from dataclasses import dataclass, field

from .compute_pm_cache import (
    ComputePMCacheCycleResult,
    ComputePMCacheState,
    apply_compute_pm_cache_cycle,
)
from .model import ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup
from .phase import LogicalPhase
from .program_bus import (
    ProgramBusCycleResult,
    ProgramBusRequest,
    ProgramBusState,
    apply_program_bus_cycle,
)
from .registers import DREGWrite


@dataclass(frozen=True)
class ComputePMNativeState:
    core: ComputePMCacheState = field(default_factory=ComputePMCacheState.reset)
    bus: ProgramBusState = field(default_factory=ProgramBusState.reset)

    @classmethod
    def reset(cls) -> "ComputePMNativeState":
        return cls()


@dataclass(frozen=True)
class ComputePMNativeCycleResult:
    state: ComputePMNativeState
    core: ComputePMCacheCycleResult
    bus: ProgramBusCycleResult
    issue_boundary: bool = False
    phase_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_compute_pm_native_cycle(
    state: ComputePMNativeState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    bus_relinquished: bool = False,
    execute: bool = False,
    opcode: int = 0,
    pmd_read_data: ExactWord | object = UNKNOWN,
    next_fetch_address: ExactWord | object = UNKNOWN,
    force_instruction_fetch: bool = False,
    external_fetch_fill: bool = False,
    external_fetch_address: ExactWord | object = UNKNOWN,
    external_fetch_instruction: ExactWord | object = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    setup_px: ExactWord | None = None,
) -> ComputePMNativeCycleResult:
    """Apply one FPGA clock of the bounded Type 5/native-PM attachment."""

    phase = LogicalPhase(phase)
    issue_boundary = bool(
        not reset
        and not bus_relinquished
        and phase == LogicalPhase.STATE_8
        and phase_advance
    )
    controls_present = bool(
        execute
        or external_fetch_fill
        or setup_astat is not None
        or setup_mstat is not None
        or setup_dreg is not None
        or setup_af is not None
        or setup_mf is not None
        or setup_dag is not None
        or setup_px is not None
    )
    phase_conflict = not reset and controls_present and not issue_boundary
    bus_completion = bool(
        not reset
        and not bus_relinquished
        and state.bus.active
        and phase == LogicalPhase.STATE_7
        and phase_advance
    )

    core_result = apply_compute_pm_cache_cycle(
        state.core,
        reset=reset,
        execute=execute and issue_boundary,
        opcode=opcode,
        pm_read_data=pmd_read_data,
        next_fetch_address=next_fetch_address,
        force_instruction_fetch=force_instruction_fetch,
        pm_cycle_complete=bus_completion,
        external_fetch_fill=external_fetch_fill and issue_boundary,
        external_fetch_address=external_fetch_address,
        external_fetch_instruction=external_fetch_instruction,
        setup_astat=setup_astat if issue_boundary else None,
        setup_mstat=setup_mstat if issue_boundary else None,
        setup_dreg=setup_dreg if issue_boundary else None,
        setup_af=setup_af if issue_boundary else None,
        setup_mf=setup_mf if issue_boundary else None,
        setup_dag=setup_dag if issue_boundary else None,
        setup_px=setup_px if issue_boundary else None,
    )

    request: ProgramBusRequest | None = None
    if core_result.core.pm_select:
        request = ProgramBusRequest(
            address=(
                ExactWord(14, core_result.core.pm_address)
                if core_result.core.pm_address_known
                else UNKNOWN
            ),
            data_access=core_result.core.pm_data_access,
            write=core_result.core.pm_write,
            write_data=(
                ExactWord(24, core_result.core.pm_write_data)
                if core_result.core.pm_write_data_known
                else UNKNOWN
            ),
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
    attachment_conflict = bool(
        bus_result.request_accepted
        != (issue_boundary and core_result.core.pm_select)
        or core_result.core.accepted
        != (
            bus_result.request_accepted
            and core_result.core.pm_data_access
        )
        or core_result.core.data_action_complete
        != (
            bus_result.completion_event
            and core_result.core.pm_data_access
        )
    )
    return ComputePMNativeCycleResult(
        state=ComputePMNativeState(core_result.state, bus_result.state),
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
