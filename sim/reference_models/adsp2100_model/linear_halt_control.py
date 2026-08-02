"""Composition model for bounded linear fetch ownership and HALT control."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .halt_control import (
    HaltControlCycleResult,
    HaltControlMode,
    HaltControlState,
    apply_halt_control_cycle,
)
from .linear_core import (
    LinearCoreCycleResult,
    LinearCoreState,
    apply_linear_core_cycle,
)
from .model import ExactWord, UNKNOWN, _UnknownValue
from .phase import LogicalPhase


@dataclass(frozen=True)
class LinearHaltControlState:
    core: LinearCoreState = field(default_factory=LinearCoreState.reset)
    control: HaltControlState = field(default_factory=HaltControlState)
    trap_asserted: bool = False
    trap_handoff: bool = False

    @classmethod
    def reset(cls) -> "LinearHaltControlState":
        return cls()


@dataclass(frozen=True)
class LinearHaltControlCycleResult:
    state: LinearHaltControlState
    core: LinearCoreCycleResult
    control: HaltControlCycleResult
    trap_asserted: bool = False
    trap_event: bool = False
    trap_halt_recognized: bool = False
    trap_handoff: bool = False
    trap_resume_event: bool = False
    trap_release_blocked: bool = False
    trap_halt_conflict: bool = False


def apply_linear_halt_control_cycle(
    state: LinearHaltControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    halt_n: bool = True,
    dmack: bool = True,
    irq_n: int = 0xF,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
) -> LinearHaltControlCycleResult:
    """Apply one shared phase boundary to the bounded HALT/linear owners."""

    phase = LogicalPhase(phase)
    raw_control = apply_halt_control_cycle(
        state.control,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        halt_n=halt_n,
        dmack=dmack,
        pm_data_cycle=False,
    )
    trap_active = bool(state.trap_asserted or state.trap_handoff)
    trap_halt_recognized = bool(
        not reset
        and state.trap_asserted
        and phase_advance
        and phase is LogicalPhase.STATE_8
        and not halt_n
    )
    trap_resume_event = bool(
        not reset
        and state.trap_handoff
        and phase_advance
        and phase is LogicalPhase.STATE_8
        and halt_n
        and dmack
    )
    trap_release_blocked = bool(
        not reset
        and state.trap_handoff
        and phase_advance
        and phase is LogicalPhase.STATE_8
        and halt_n
        and not dmack
    )
    trap_phase_hold = bool(
        not reset and trap_active and not trap_resume_event
    )
    trap_phase_conflict = bool(
        not reset
        and trap_active
        and phase_advance
        and phase is not LogicalPhase.STATE_8
    )
    combined_phase_hold = bool(raw_control.phase_hold or trap_phase_hold)
    combined_effective_phase_advance = bool(
        phase_advance and not combined_phase_hold
    )
    combined_instruction_issue_inhibit = bool(
        raw_control.instruction_issue_inhibit or trap_phase_hold
    )
    core = apply_linear_core_cycle(
        state.core,
        reset=reset,
        phase=phase,
        phase_advance=combined_effective_phase_advance,
        instruction_issue_inhibit=combined_instruction_issue_inhibit,
        irq_n=irq_n,
        instruction_setup=instruction_setup,
        pmd_read_data=pmd_read_data,
    )
    trap_halt_conflict = bool(
        not reset
        and core.trap_event
        and (
            state.control.mode is not HaltControlMode.RUNNING
            or raw_control.halt_stop_event
        )
    )
    control = replace(
        raw_control,
        resume_event=bool(
            raw_control.resume_event or trap_resume_event
        ),
        release_blocked=bool(
            raw_control.release_blocked or trap_release_blocked
        ),
        instruction_issue_inhibit=combined_instruction_issue_inhibit,
        phase_hold=combined_phase_hold,
        effective_phase_advance=combined_effective_phase_advance,
        halted=bool(raw_control.halted or trap_active),
        phase_conflict=bool(
            raw_control.phase_conflict
            or trap_phase_conflict
            or trap_halt_conflict
        ),
    )
    if reset:
        next_trap_asserted = False
        next_trap_handoff = False
    elif core.trap_event:
        next_trap_asserted = True
        next_trap_handoff = False
    elif trap_halt_recognized:
        next_trap_asserted = False
        next_trap_handoff = True
    elif trap_resume_event:
        next_trap_asserted = False
        next_trap_handoff = False
    else:
        next_trap_asserted = state.trap_asserted
        next_trap_handoff = state.trap_handoff
    return LinearHaltControlCycleResult(
        state=LinearHaltControlState(
            core=core.state,
            control=raw_control.state,
            trap_asserted=next_trap_asserted,
            trap_handoff=next_trap_handoff,
        ),
        core=core,
        control=control,
        trap_asserted=bool(not reset and state.trap_asserted),
        trap_event=core.trap_event,
        trap_halt_recognized=trap_halt_recognized,
        trap_handoff=bool(not reset and state.trap_handoff),
        trap_resume_event=trap_resume_event,
        trap_release_blocked=trap_release_blocked,
        trap_halt_conflict=trap_halt_conflict,
    )
