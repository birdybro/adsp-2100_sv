"""Original ADSP-2100 external-interrupt recognition boundary.

This model is intentionally limited to the four original active-low IRQ pins.
It samples them only at logical state 7, retains edge-sensitive requests,
applies IMASK, and selects IRQ3 as the highest priority request.  Entry-stack
and vector-fetch effects belong to the fetched-owner composition.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import ExactWord, UNKNOWN, _UnknownValue
from .phase import LogicalPhase


@dataclass(frozen=True)
class InterruptState:
    """State retained by the four-pin interrupt recognizer."""

    previous_irq_n: int = 0xF
    sample_history_valid: bool = False
    edge_pending: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.previous_irq_n <= 0xF:
            raise ValueError("previous IRQ sample must be four bits")
        if not 0 <= self.edge_pending <= 0xF:
            raise ValueError("edge-pending state must be four bits")

    @classmethod
    def reset(cls) -> "InterruptState":
        return cls()


@dataclass(frozen=True)
class InterruptCycleResult:
    state: InterruptState
    sample_event: bool = False
    sampled_requests: int = 0
    enabled_requests: int = 0
    recognition_event: bool = False
    recognized_level: int = 0
    vector_address: ExactWord = ExactWord(14, 0)
    configuration_invalid: bool = False
    reset_baseline_provisional: bool = False


def _known_register_value(
    register: ExactWord | _UnknownValue,
    width: int,
) -> int | None:
    if register is UNKNOWN:
        return None
    if not isinstance(register, ExactWord) or register.width != width:
        raise ValueError(f"register must be UNKNOWN or exactly {width} bits")
    return register.value


def apply_interrupt_cycle(
    state: InterruptState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    irq_n: int = 0xF,
    icntl: ExactWord | _UnknownValue = UNKNOWN,
    imask: ExactWord | _UnknownValue = UNKNOWN,
    service_allowed: bool = True,
) -> InterruptCycleResult:
    """Sample, retain, mask, and prioritize the original four IRQ inputs.

    The first post-reset state-7 sample establishes the edge detector's prior
    level and cannot create an edge request.  The original sources do not
    identify the reset-release comparison sample, so that conservative choice
    remains explicitly provisional under OQ-025.
    """

    phase = LogicalPhase(phase)
    if not 0 <= irq_n <= 0xF:
        raise ValueError("IRQ input must be four bits")
    icntl_value = _known_register_value(icntl, 5)
    imask_value = _known_register_value(imask, 4)
    if reset:
        return InterruptCycleResult(InterruptState.reset())

    sample_event = bool(
        phase_advance and phase is LogicalPhase.STATE_7
    )
    if not sample_event:
        return InterruptCycleResult(state)

    configuration_invalid = bool(
        icntl_value is None or imask_value is None
    )
    reset_baseline_provisional = not state.sample_history_valid
    edge_pending = state.edge_pending
    sampled_requests = 0
    enabled_requests = 0
    recognition_event = False
    recognized_level = 0

    if icntl_value is not None:
        edge_modes = icntl_value & 0xF
        active = (~irq_n) & 0xF
        if state.sample_history_valid:
            falling = state.previous_irq_n & active
            edge_pending |= falling & edge_modes
        sampled_requests = edge_pending | (active & ~edge_modes & 0xF)
        if imask_value is not None:
            enabled_requests = sampled_requests & imask_value
            if service_allowed and enabled_requests:
                recognized_level = max(
                    level
                    for level in range(4)
                    if enabled_requests & (1 << level)
                )
                recognition_event = True
                edge_pending &= ~(1 << recognized_level)

    return InterruptCycleResult(
        state=InterruptState(
            previous_irq_n=irq_n,
            sample_history_valid=True,
            edge_pending=edge_pending,
        ),
        sample_event=True,
        sampled_requests=sampled_requests,
        enabled_requests=enabled_requests,
        recognition_event=recognition_event,
        recognized_level=recognized_level,
        vector_address=ExactWord(14, recognized_level),
        configuration_invalid=configuration_invalid,
        reset_baseline_provisional=reset_baseline_provisional,
    )
