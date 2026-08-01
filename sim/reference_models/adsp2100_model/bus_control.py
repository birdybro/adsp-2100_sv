"""Independent original ADSP-2100 normal-operation BR/BG model.

The digital boundary assumes BR meets the original setup requirement at an
enabled end-of-state-three sample.  Analog resynchronization uncertainty and
the separately documented asynchronous RESET-time path are outside this
normal-operation state machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .phase import LogicalPhase


class BusControlMode(IntEnum):
    IDLE = 0
    REQUEST_DELAY = 1
    GRANTED = 2
    RELEASE_DELAY = 3
    REACQUIRE = 4


@dataclass(frozen=True)
class BusControlState:
    mode: BusControlMode = BusControlMode.IDLE


@dataclass(frozen=True)
class BusControlCycleResult:
    state: BusControlState
    state_three_boundary: bool = False
    request_recognized: bool = False
    grant_assert_event: bool = False
    release_recognized: bool = False
    grant_release_event: bool = False
    resume_event: bool = False
    request_withdrawn: bool = False
    release_cancelled: bool = False
    instruction_issue_inhibit: bool = False
    bus_relinquished: bool = False
    bg_n: bool = True
    reset_br_request: bool = False


def apply_bus_control_cycle(
    state: BusControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    br_n: bool = True,
) -> BusControlCycleResult:
    """Apply one logical-phase boundary to the normal BR/BG controller."""

    phase = LogicalPhase(phase)
    state_three_boundary = bool(
        not reset
        and phase_advance
        and phase == LogicalPhase.STATE_3
    )
    request_recognized = bool(
        state.mode is BusControlMode.IDLE
        and state_three_boundary
        and not br_n
    )
    grant_assert_event = bool(
        state.mode is BusControlMode.REQUEST_DELAY
        and state_three_boundary
        and not br_n
    )
    request_withdrawn = bool(
        state.mode is BusControlMode.REQUEST_DELAY
        and state_three_boundary
        and br_n
    )
    release_recognized = bool(
        state.mode is BusControlMode.GRANTED
        and state_three_boundary
        and br_n
    )
    grant_release_event = bool(
        state.mode is BusControlMode.RELEASE_DELAY
        and state_three_boundary
        and br_n
    )
    release_cancelled = bool(
        state.mode is BusControlMode.RELEASE_DELAY
        and state_three_boundary
        and not br_n
    )
    resume_event = bool(
        not reset
        and state.mode is BusControlMode.REACQUIRE
        and phase_advance
        and phase == LogicalPhase.STATE_8
    )

    if reset:
        next_state = BusControlState()
    elif request_recognized:
        next_state = BusControlState(BusControlMode.REQUEST_DELAY)
    elif grant_assert_event:
        next_state = BusControlState(BusControlMode.GRANTED)
    elif request_withdrawn:
        next_state = BusControlState(BusControlMode.IDLE)
    elif release_recognized:
        next_state = BusControlState(BusControlMode.RELEASE_DELAY)
    elif grant_release_event:
        next_state = BusControlState(BusControlMode.REACQUIRE)
    elif release_cancelled:
        next_state = BusControlState(BusControlMode.GRANTED)
    elif resume_event:
        next_state = BusControlState(BusControlMode.IDLE)
    else:
        next_state = state

    granted = bool(
        not reset
        and state.mode
        in (BusControlMode.GRANTED, BusControlMode.RELEASE_DELAY)
    )
    issue_inhibit = bool(
        not reset
        and (
            (
                state.mode is not BusControlMode.IDLE
                and not resume_event
            )
            or request_recognized
        )
    )
    return BusControlCycleResult(
        state=next_state,
        state_three_boundary=state_three_boundary,
        request_recognized=request_recognized,
        grant_assert_event=grant_assert_event,
        release_recognized=release_recognized,
        grant_release_event=grant_release_event,
        resume_event=resume_event,
        request_withdrawn=request_withdrawn,
        release_cancelled=release_cancelled,
        instruction_issue_inhibit=issue_inhibit,
        bus_relinquished=granted,
        bg_n=not granted,
        reset_br_request=bool(reset and not br_n),
    )
