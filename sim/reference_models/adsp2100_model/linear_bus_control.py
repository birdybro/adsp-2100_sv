"""Composition model for bounded linear fetch ownership and BR/BG control."""

from __future__ import annotations

from dataclasses import dataclass, field

from .bus_control import (
    BusControlCycleResult,
    BusControlState,
    apply_bus_control_cycle,
)
from .linear_core import (
    LinearCoreCycleResult,
    LinearCoreState,
    apply_linear_core_cycle,
)
from .model import ExactWord, UNKNOWN, _UnknownValue
from .phase import LogicalPhase


@dataclass(frozen=True)
class LinearBusControlState:
    core: LinearCoreState = field(default_factory=LinearCoreState.reset)
    control: BusControlState = field(default_factory=BusControlState)

    @classmethod
    def reset(cls) -> "LinearBusControlState":
        return cls()


@dataclass(frozen=True)
class LinearBusControlCycleResult:
    state: LinearBusControlState
    core: LinearCoreCycleResult
    control: BusControlCycleResult
    native_bg_n: bool
    native_bus_relinquished: bool


def apply_linear_bus_control_cycle(
    state: LinearBusControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    br_n: bool = True,
    irq_n: int = 0xF,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
) -> LinearBusControlCycleResult:
    """Apply one shared phase boundary to the composed bounded owners."""

    control = apply_bus_control_cycle(
        state.control,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        br_n=br_n,
    )
    native_bg_n = br_n if reset else control.bg_n
    native_bus_relinquished = (
        not br_n if reset else control.bus_relinquished
    )
    core = apply_linear_core_cycle(
        state.core,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        instruction_issue_inhibit=control.instruction_issue_inhibit,
        bus_relinquished=native_bus_relinquished,
        irq_n=irq_n,
        instruction_setup=instruction_setup,
        pmd_read_data=pmd_read_data,
    )
    return LinearBusControlCycleResult(
        state=LinearBusControlState(core=core.state, control=control.state),
        core=core,
        control=control,
        native_bg_n=native_bg_n,
        native_bus_relinquished=native_bus_relinquished,
    )
