"""Independent Type 13/cache composition with native PM logical phases.

The model joins three separately testable boundaries without assigning
whole-core fetch ownership: the Type 13 architectural action, the original
instruction-cache monitor, and the eight-state program-memory pin controller.
Architectural operands are captured on the enabled state-8-to-state-1 issue
edge and commit only on the corresponding state-7-to-state-8 completion edge.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .interrupt import (
    InterruptCycleResult,
    InterruptState,
    apply_interrupt_cycle,
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
from .shifter_pm_cache import (
    ShifterPMCacheCycleResult,
    ShifterPMCacheState,
    apply_shifter_pm_cache_cycle,
)


@dataclass(frozen=True)
class ShifterPMNativeState:
    core: ShifterPMCacheState = field(default_factory=ShifterPMCacheState.reset)
    bus: ProgramBusState = field(default_factory=ProgramBusState.reset)
    interrupt: InterruptState = field(default_factory=InterruptState.reset)

    @classmethod
    def reset(cls) -> "ShifterPMNativeState":
        return cls()


@dataclass(frozen=True)
class ShifterPMNativeCycleResult:
    state: ShifterPMNativeState
    core: ShifterPMCacheCycleResult
    bus: ProgramBusCycleResult
    interrupt: InterruptCycleResult
    issue_boundary: bool = False
    interrupt_interval_block: bool = False
    phase_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_shifter_pm_native_cycle(
    state: ShifterPMNativeState,
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
    irq_n: int = 0xF,
    icntl: ExactWord | object = UNKNOWN,
    imask: ExactWord | object = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_sb: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    setup_px: ExactWord | None = None,
) -> ShifterPMNativeCycleResult:
    """Apply one FPGA clock of the bounded Type 13/native-PM attachment."""

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
        or setup_sb is not None
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

    core_result = apply_shifter_pm_cache_cycle(
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
        setup_sb=setup_sb if issue_boundary else None,
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
    interrupt_result = apply_interrupt_cycle(
        state.interrupt,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        irq_n=irq_n,
        icntl=icntl,
        imask=imask,
        service_allowed=core_result.core.instruction_complete,
    )
    interrupt_interval_block = bool(
        interrupt_result.sample_event
        and core_result.core.data_action_complete
        and not core_result.core.instruction_complete
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
    return ShifterPMNativeCycleResult(
        state=ShifterPMNativeState(
            core_result.state,
            bus_result.state,
            interrupt_result.state,
        ),
        core=core_result,
        bus=bus_result,
        interrupt=interrupt_result,
        issue_boundary=issue_boundary,
        interrupt_interval_block=interrupt_interval_block,
        phase_conflict=phase_conflict,
        attachment_conflict=attachment_conflict,
        integration_conflict=(
            phase_conflict
            or attachment_conflict
            or core_result.integration_conflict
        ),
    )
