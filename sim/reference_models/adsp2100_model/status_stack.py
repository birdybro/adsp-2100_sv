"""Original ADSP-2100 four-entry status-stack state model.

The original stack stores one 16-bit ASTAT/MSTAT/IMASK context per entry.
Overflow saturates the stack pointer, drops the newest push, and sticks until
reset. The value produced by an empty pop is undocumented, so this model
returns no valid pop value rather than inventing architectural state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .status import StatusStackEntry


STATUS_STACK_DEPTH = 4


class StatusStackOperation(IntEnum):
    """Original Appendix A Spp status-stack control field."""

    NO_CHANGE_ZERO = 0
    NO_CHANGE_ONE = 1
    PUSH = 2
    POP = 3


@dataclass(frozen=True)
class StatusStackState:
    """Bottom-to-top accepted entries and sticky overflow state."""

    entries: tuple[StatusStackEntry, ...] = ()
    overflow: bool = False

    def __post_init__(self) -> None:
        if len(self.entries) > STATUS_STACK_DEPTH:
            raise ValueError("status stack cannot exceed four accepted entries")

    @property
    def empty(self) -> bool:
        return not self.entries

    @property
    def depth(self) -> int:
        return len(self.entries)

    @property
    def sstat_fragment(self) -> int:
        """Return status-stack SSTAT bits in their architectural positions."""

        return (int(self.overflow) << 5) | (int(self.empty) << 4)


@dataclass(frozen=True)
class StatusStackCycleInputs:
    reset: bool = False
    operation: StatusStackOperation = StatusStackOperation.NO_CHANGE_ZERO
    push_entry: StatusStackEntry | None = None

    def __post_init__(self) -> None:
        try:
            operation = StatusStackOperation(self.operation)
        except ValueError as error:
            raise ValueError("invalid status-stack operation") from error
        object.__setattr__(self, "operation", operation)
        if operation is StatusStackOperation.PUSH:
            if self.push_entry is None:
                raise ValueError("status-stack PUSH requires an entry")
        elif self.push_entry is not None:
            raise ValueError("push entry is only legal with status-stack PUSH")


@dataclass(frozen=True)
class StatusStackCycleResult:
    state: StatusStackState
    pop_entry: StatusStackEntry | None = None
    push_accepted: bool = False
    overflow_event: bool = False
    empty_pop: bool = False


def apply_status_stack_cycle(
    state: StatusStackState,
    inputs: StatusStackCycleInputs,
) -> StatusStackCycleResult:
    """Apply one status-stack operation at an instruction boundary."""

    if inputs.reset:
        return StatusStackCycleResult(StatusStackState())

    if inputs.operation is StatusStackOperation.PUSH:
        if state.depth == STATUS_STACK_DEPTH:
            return StatusStackCycleResult(
                StatusStackState(state.entries, True),
                overflow_event=True,
            )
        assert inputs.push_entry is not None
        return StatusStackCycleResult(
            StatusStackState(
                state.entries + (inputs.push_entry,),
                state.overflow,
            ),
            push_accepted=True,
        )

    if inputs.operation is StatusStackOperation.POP:
        if state.empty:
            return StatusStackCycleResult(state, empty_pop=True)
        return StatusStackCycleResult(
            StatusStackState(state.entries[:-1], state.overflow),
            pop_entry=state.entries[-1],
        )

    return StatusStackCycleResult(state)
