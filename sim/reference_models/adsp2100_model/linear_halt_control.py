"""Composition model for bounded linear fetch ownership and HALT control."""

from __future__ import annotations

from dataclasses import dataclass, field

from .halt_control import (
    HaltControlCycleResult,
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

    @classmethod
    def reset(cls) -> "LinearHaltControlState":
        return cls()


@dataclass(frozen=True)
class LinearHaltControlCycleResult:
    state: LinearHaltControlState
    core: LinearCoreCycleResult
    control: HaltControlCycleResult


def apply_linear_halt_control_cycle(
    state: LinearHaltControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    halt_n: bool = True,
    dmack: bool = True,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
) -> LinearHaltControlCycleResult:
    """Apply one shared phase boundary to the bounded HALT/linear owners."""

    control = apply_halt_control_cycle(
        state.control,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        halt_n=halt_n,
        dmack=dmack,
        pm_data_cycle=False,
    )
    core = apply_linear_core_cycle(
        state.core,
        reset=reset,
        phase=phase,
        phase_advance=control.effective_phase_advance,
        instruction_issue_inhibit=control.instruction_issue_inhibit,
        instruction_setup=instruction_setup,
        pmd_read_data=pmd_read_data,
    )
    return LinearHaltControlCycleResult(
        state=LinearHaltControlState(core=core.state, control=control.state),
        core=core,
        control=control,
    )
