"""Bounded Type 5/native-PM composition with original HALT sequencing.

HALT recognition during a Type 5 PM-data cycle replaces any issue-time cache
hit with the mandatory external instruction fetch.  The captured compute,
memory, PX, and DAG actions commit once at the data-cycle completion; stopping
occurs only after the forced fetch completes.

Ordinary fetch ownership outside an active Type 5 recovery, BR/BG, DM waits,
TRAP, interrupts, reset release, and analog input synchronization are outside
this bounded composition.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .compute_pm_native import (
    ComputePMNativeCycleResult,
    ComputePMNativeState,
    apply_compute_pm_native_cycle,
)
from .halt_control import (
    HaltControlCycleResult,
    HaltControlMode,
    HaltControlState,
    apply_halt_control_cycle,
)
from .model import ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup
from .phase import LogicalPhase
from .registers import DREGWrite


@dataclass(frozen=True)
class ComputePMHaltState:
    native: ComputePMNativeState = field(
        default_factory=ComputePMNativeState.reset
    )
    control: HaltControlState = field(default_factory=HaltControlState)

    @classmethod
    def reset(cls) -> "ComputePMHaltState":
        return cls()


@dataclass(frozen=True)
class ComputePMHaltCycleResult:
    state: ComputePMHaltState
    native: ComputePMNativeCycleResult
    control: HaltControlCycleResult
    pm_data_cycle: bool = False
    late_force_request: bool = False
    execute_suppressed: bool = False
    owner_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_compute_pm_halt_cycle(
    state: ComputePMHaltState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    halt_n: bool = True,
    dmack: bool = True,
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
    bus_relinquished: bool = False,
) -> ComputePMHaltCycleResult:
    """Apply one shared logical phase to the Type 5/HALT composition."""

    phase = LogicalPhase(phase)
    core_state = state.native.core.core
    control_pm_data_cycle = core_state.pending is not None
    active_owner = state.native.bus.active

    control = apply_halt_control_cycle(
        state.control,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        halt_n=halt_n,
        dmack=dmack,
        pm_data_cycle=control_pm_data_cycle,
    )
    late_force_request = bool(
        not reset
        and (
            state.control.mode is HaltControlMode.FORCE_FETCH_PENDING
            or (control.halt_recognized and control_pm_data_cycle)
        )
    )
    owner_execute = bool(
        execute
        and not control.instruction_issue_inhibit
        and not control.force_fetch_issue
    )
    execute_suppressed = execute and not owner_execute
    owner_conflict = bool(
        not reset
        and (
            (control.halt_recognized and not active_owner)
            or execute_suppressed
        )
    )

    native = apply_compute_pm_native_cycle(
        state.native,
        reset=reset,
        phase=phase,
        phase_advance=control.effective_phase_advance,
        bus_relinquished=bus_relinquished,
        execute=owner_execute,
        opcode=opcode,
        pmd_read_data=pmd_read_data,
        next_fetch_address=next_fetch_address,
        force_instruction_fetch=(
            force_instruction_fetch or late_force_request
        ),
        external_fetch_fill=external_fetch_fill,
        external_fetch_address=external_fetch_address,
        external_fetch_instruction=external_fetch_instruction,
        setup_astat=setup_astat,
        setup_mstat=setup_mstat,
        setup_dreg=setup_dreg,
        setup_af=setup_af,
        setup_mf=setup_mf,
        setup_dag=setup_dag,
        setup_px=setup_px,
    )

    attachment_conflict = bool(
        control.force_fetch_issue
        and not (
            native.bus.request_accepted
            and native.core.core.recovery_fetch
            and not native.bus.state.data_access
        )
    )
    return ComputePMHaltCycleResult(
        state=ComputePMHaltState(native=native.state, control=control.state),
        native=native,
        control=control,
        pm_data_cycle=native.core.core.pm_data_access,
        late_force_request=late_force_request,
        execute_suppressed=execute_suppressed,
        owner_conflict=owner_conflict,
        attachment_conflict=attachment_conflict,
        integration_conflict=(
            owner_conflict
            or attachment_conflict
            or native.integration_conflict
            or control.phase_conflict
        ),
    )
