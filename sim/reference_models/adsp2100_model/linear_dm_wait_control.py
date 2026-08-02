"""Bounded ordinary-fetch and native-DM wait-state composition.

The DM descriptor is a structural companion to an ordinary PM fetch.  It is
not a claim that a fetched DM instruction class is owned by the linear core.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data_bus import (
    DataBusCycleResult,
    DataBusRequest,
    DataBusState,
    apply_data_bus_cycle,
)
from .linear_core import (
    LinearCoreCycleResult,
    LinearCoreState,
    apply_linear_core_cycle,
)
from .model import ExactWord, UNKNOWN, _UnknownValue
from .phase import LogicalPhase


@dataclass(frozen=True)
class LinearDMWaitControlState:
    """Retained private-PM owner and one paired native-DM transaction."""

    core: LinearCoreState = field(default_factory=LinearCoreState.reset)
    dm_bus: DataBusState = field(default_factory=DataBusState.reset)

    @classmethod
    def reset(cls) -> "LinearDMWaitControlState":
        return cls()


@dataclass(frozen=True)
class LinearDMWaitControlCycleResult:
    state: LinearDMWaitControlState
    core: LinearCoreCycleResult
    dm_bus: DataBusCycleResult
    architectural_phase_advance: bool = False
    interrupt_wait_sample: bool = False
    dm_companion_accepted: bool = False
    phase_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_linear_dm_wait_control_cycle(
    state: LinearDMWaitControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    irq_n: int = 0xF,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    dm_request: DataBusRequest | None = None,
    dm_ack: bool = True,
    dmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
) -> LinearDMWaitControlCycleResult:
    """Apply one physical phase to the paired PM-fetch/native-DM boundary.

    A low DMACK sample at physical state 6 freezes the architectural PM owner
    before its state-7 completion. Physical phases continue to circulate.
    Each physical state-7 boundary still samples IRQ pins, but interrupt
    service is impossible until the later qualified PM/DM completion.
    """

    phase = LogicalPhase(phase)
    dm_waiting = bool(
        state.dm_bus.active
        and not state.dm_bus.response_valid
        and state.dm_bus.waiting
    )
    architectural_phase_advance = bool(
        phase_advance and not dm_waiting
    )
    interrupt_wait_sample = bool(
        phase_advance
        and dm_waiting
        and phase is LogicalPhase.STATE_7
    )

    core = apply_linear_core_cycle(
        state.core,
        reset=reset,
        phase=phase,
        phase_advance=architectural_phase_advance,
        interrupt_sample_advance=interrupt_wait_sample,
        irq_n=irq_n,
        instruction_setup=instruction_setup,
        pmd_read_data=pmd_read_data,
    )
    ordinary_pm_issue = bool(
        core.instruction_issue and not state.core.interrupt_vectoring
    )
    paired_request = (
        dm_request if dm_request is not None and ordinary_pm_issue else None
    )
    dm_bus = apply_data_bus_cycle(
        state.dm_bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        request=paired_request,
        dm_ack=dm_ack,
        dmd_read_data=dmd_read_data,
    )

    controls_present = dm_request is not None
    phase_conflict = bool(
        not reset
        and controls_present
        and not (
            phase_advance
            and phase is LogicalPhase.STATE_8
            and not dm_waiting
        )
    )
    pairing_conflict = bool(
        not reset
        and controls_present
        and not phase_conflict
        and not ordinary_pm_issue
    )
    completion_conflict = bool(
        not reset
        and state.dm_bus.active
        and not state.dm_bus.response_valid
        and (dm_bus.completion_event != core.bus.completion_event)
    )
    attachment_conflict = bool(
        pairing_conflict
        or completion_conflict
        or (dm_bus.request_accepted != (paired_request is not None))
    )

    return LinearDMWaitControlCycleResult(
        state=LinearDMWaitControlState(core.state, dm_bus.state),
        core=core,
        dm_bus=dm_bus,
        architectural_phase_advance=architectural_phase_advance,
        interrupt_wait_sample=interrupt_wait_sample,
        dm_companion_accepted=dm_bus.request_accepted,
        phase_conflict=phase_conflict,
        attachment_conflict=attachment_conflict,
        integration_conflict=bool(
            phase_conflict
            or attachment_conflict
            or core.phase_conflict
            or core.integration_conflict
            or core.internal_conflict
        ),
    )
