"""Independent bounded original ADSP-2100 HALT control model.

This boundary covers a HALT recognized while the current processor cycle is
an external program-memory instruction fetch.  Program-memory data cycles,
bus grant, DMACK waits, TRAP handoff, and analog resynchronization remain
outside this state machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .phase import LogicalPhase


class HaltControlMode(IntEnum):
    RUNNING = 0
    STOP_PENDING = 1
    HALTED = 2


@dataclass(frozen=True)
class HaltControlState:
    mode: HaltControlMode = HaltControlMode.RUNNING


@dataclass(frozen=True)
class HaltControlCycleResult:
    state: HaltControlState
    state_three_boundary: bool = False
    halt_recognized: bool = False
    halt_stop_event: bool = False
    resume_event: bool = False
    release_blocked: bool = False
    instruction_issue_inhibit: bool = False
    phase_hold: bool = False
    effective_phase_advance: bool = False
    halted: bool = False
    phase_conflict: bool = False


def apply_halt_control_cycle(
    state: HaltControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    halt_n: bool = True,
    dmack: bool = True,
) -> HaltControlCycleResult:
    """Apply one logical-phase boundary to the bounded HALT controller."""

    phase = LogicalPhase(phase)
    state_three_boundary = bool(
        not reset
        and phase_advance
        and phase == LogicalPhase.STATE_3
    )
    halt_recognized = bool(
        state.mode is HaltControlMode.RUNNING
        and state_three_boundary
        and not halt_n
    )
    halt_stop_event = bool(
        not reset
        and state.mode is HaltControlMode.STOP_PENDING
        and phase_advance
        and phase == LogicalPhase.STATE_7
    )
    resume_boundary = bool(
        not reset
        and state.mode is HaltControlMode.HALTED
        and phase_advance
        and phase == LogicalPhase.STATE_8
        and halt_n
    )
    resume_event = bool(resume_boundary and dmack)
    release_blocked = bool(resume_boundary and not dmack)
    phase_hold = bool(
        not reset
        and state.mode is HaltControlMode.HALTED
        and not resume_event
    )
    effective_phase_advance = bool(phase_advance and not phase_hold)
    instruction_issue_inhibit = bool(
        not reset
        and (
            halt_recognized
            or state.mode is HaltControlMode.STOP_PENDING
            or (
                state.mode is HaltControlMode.HALTED
                and not resume_event
            )
        )
    )
    phase_conflict = bool(
        not reset
        and state.mode is HaltControlMode.HALTED
        and phase_advance
        and phase != LogicalPhase.STATE_8
    )

    if reset:
        next_state = HaltControlState()
    elif halt_recognized:
        next_state = HaltControlState(HaltControlMode.STOP_PENDING)
    elif halt_stop_event:
        next_state = HaltControlState(HaltControlMode.HALTED)
    elif resume_event:
        next_state = HaltControlState(HaltControlMode.RUNNING)
    else:
        next_state = state

    return HaltControlCycleResult(
        state=next_state,
        state_three_boundary=state_three_boundary,
        halt_recognized=halt_recognized,
        halt_stop_event=halt_stop_event,
        resume_event=resume_event,
        release_blocked=release_blocked,
        instruction_issue_inhibit=instruction_issue_inhibit,
        phase_hold=phase_hold,
        effective_phase_advance=effective_phase_advance,
        halted=bool(not reset and state.mode is HaltControlMode.HALTED),
        phase_conflict=phase_conflict,
    )
