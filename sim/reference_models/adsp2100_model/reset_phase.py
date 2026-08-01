"""Independent original ADSP-2100 RESET and logical-phase model.

The original RESET input is recognized only on a rising CLKIN edge.  This
bounded digital contract requires four sampled asserted rising edges, holds
the processor in state 4, and leaves state 4 for state 5 on the second rising
edge after release.
Short assertions fail closed because the original manual does not define the
result of violating the minimum duration.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .phase import LogicalPhase


MINIMUM_RESET_CLKIN_CYCLES = 4


@dataclass(frozen=True)
class ResetPhaseState:
    """Retained reset synchronizer and externally visible phase state."""

    initialized: bool = False
    phase: LogicalPhase = LogicalPhase.STATE_4
    reset_active: bool = False
    asserted_rising_edges: int = 0
    release_rising_seen: bool = False
    duration_error: bool = False


@dataclass(frozen=True)
class ResetPhaseCycleResult:
    state: ResetPhaseState
    phase_before: LogicalPhase = LogicalPhase.STATE_4
    phase_after: LogicalPhase = LogicalPhase.STATE_4
    phase_valid: bool = False
    phase_advance: bool = False
    reset_recognized: bool = False
    architectural_reset: bool = False
    release_first_rising: bool = False
    release_event: bool = False
    duration_error: bool = False
    clkout: bool = False


def _clkout_for_phase(phase: LogicalPhase) -> bool:
    return phase in (
        LogicalPhase.STATE_8,
        LogicalPhase.STATE_1,
        LogicalPhase.STATE_2,
        LogicalPhase.STATE_3,
    )


def apply_reset_phase_cycle(
    state: ResetPhaseState,
    *,
    edge_enable: bool = True,
    clkin_rising: bool = False,
    reset_pin: bool = False,
) -> ResetPhaseCycleResult:
    """Apply one represented CLKIN edge on the single FPGA clock.

    ``clkin_rising`` is meaningful only when ``edge_enable`` is true.  The
    wrapper supplies alternating CLKIN edge polarity; no internal or gated
    clock is created.
    """

    phase_before = state.phase
    reset_recognized = bool(edge_enable and clkin_rising and reset_pin)
    release_first_rising = False
    release_event = False
    phase_advance = False
    next_state = state

    if reset_recognized:
        asserted = (
            min(
                state.asserted_rising_edges + 1,
                MINIMUM_RESET_CLKIN_CYCLES,
            )
            if (
                state.reset_active
                and not state.duration_error
                and not state.release_rising_seen
            )
            else 1
        )
        next_state = ResetPhaseState(
            initialized=True,
            phase=LogicalPhase.STATE_4,
            reset_active=True,
            asserted_rising_edges=asserted,
            release_rising_seen=False,
            duration_error=False,
        )
    elif state.reset_active:
        if edge_enable and clkin_rising and not reset_pin:
            if state.asserted_rising_edges < MINIMUM_RESET_CLKIN_CYCLES:
                next_state = replace(state, duration_error=True)
            elif not state.release_rising_seen:
                release_first_rising = True
                next_state = replace(state, release_rising_seen=True)
            else:
                release_event = True
                phase_advance = True
                next_state = replace(
                    state,
                    phase=LogicalPhase.STATE_5,
                    reset_active=False,
                    release_rising_seen=False,
                )
    elif state.initialized and edge_enable:
        phase_advance = True
        next_state = replace(
            state,
            phase=LogicalPhase((int(state.phase) + 1) & 7),
        )

    architectural_reset = bool(
        reset_recognized or (state.reset_active and not release_event)
    )
    phase_after = next_state.phase
    phase_valid = next_state.initialized
    clkout = bool(
        phase_valid
        and not next_state.reset_active
        and _clkout_for_phase(phase_after)
    )
    return ResetPhaseCycleResult(
        state=next_state,
        phase_before=phase_before,
        phase_after=phase_after,
        phase_valid=phase_valid,
        phase_advance=phase_advance,
        reset_recognized=reset_recognized,
        architectural_reset=architectural_reset,
        release_first_rising=release_first_rising,
        release_event=release_event,
        duration_error=next_state.duration_error,
        clkout=clkout,
    )
