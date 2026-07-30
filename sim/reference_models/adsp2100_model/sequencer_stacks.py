"""State model for the original ADSP-2100 PC, count, and loop stacks.

All three stacks saturate their pointers, drop the newest overflowing push,
and retain sticky overflow until reset. Empty-pop data is undocumented, so
the model reports no pop value instead of inventing architectural state.
"""

from __future__ import annotations

from dataclasses import dataclass


PC_STACK_DEPTH = 16
COUNT_STACK_DEPTH = 4
LOOP_STACK_DEPTH = 4
PC_STACK_WIDTH = 14
COUNT_STACK_WIDTH = 14
LOOP_STACK_WIDTH = 18


def _require_width(value: int, width: int, name: str) -> None:
    if not 0 <= value < (1 << width):
        raise ValueError(f"{name} must fit {width} bits")


def _validate_entries(
    entries: tuple[int, ...],
    depth: int,
    width: int,
    name: str,
) -> None:
    if len(entries) > depth:
        raise ValueError(f"{name} stack cannot exceed {depth} entries")
    for value in entries:
        _require_width(value, width, f"{name} entry")


@dataclass(frozen=True)
class SequencerStacksState:
    """Bottom-to-top accepted entries and independent sticky overflow bits."""

    pc_entries: tuple[int, ...] = ()
    count_entries: tuple[int, ...] = ()
    loop_entries: tuple[int, ...] = ()
    pc_overflow: bool = False
    count_overflow: bool = False
    loop_overflow: bool = False

    def __post_init__(self) -> None:
        _validate_entries(
            self.pc_entries,
            PC_STACK_DEPTH,
            PC_STACK_WIDTH,
            "PC",
        )
        _validate_entries(
            self.count_entries,
            COUNT_STACK_DEPTH,
            COUNT_STACK_WIDTH,
            "count",
        )
        _validate_entries(
            self.loop_entries,
            LOOP_STACK_DEPTH,
            LOOP_STACK_WIDTH,
            "loop",
        )

    @property
    def sstat_fragment(self) -> int:
        """Return the PC/count/loop sources in architectural SSTAT positions."""

        return (
            int(not self.pc_entries)
            | (int(self.pc_overflow) << 1)
            | (int(not self.count_entries) << 2)
            | (int(self.count_overflow) << 3)
            | (int(not self.loop_entries) << 6)
            | (int(self.loop_overflow) << 7)
        )


@dataclass(frozen=True)
class SequencerStacksInputs:
    reset: bool = False
    pc_push: bool = False
    pc_pop: bool = False
    pc_push_value: int = 0
    count_push: bool = False
    count_pop: bool = False
    count_push_value: int = 0
    loop_push: bool = False
    loop_pop: bool = False
    loop_push_value: int = 0

    def __post_init__(self) -> None:
        _require_width(self.pc_push_value, PC_STACK_WIDTH, "PC push value")
        _require_width(
            self.count_push_value,
            COUNT_STACK_WIDTH,
            "count push value",
        )
        _require_width(
            self.loop_push_value,
            LOOP_STACK_WIDTH,
            "loop push value",
        )


@dataclass(frozen=True)
class SequencerStacksCycleResult:
    state: SequencerStacksState
    pc_pop_value: int | None = None
    count_pop_value: int | None = None
    loop_pop_value: int | None = None
    pc_push_accepted: bool = False
    count_push_accepted: bool = False
    loop_push_accepted: bool = False
    pc_overflow_event: bool = False
    count_overflow_event: bool = False
    loop_overflow_event: bool = False
    pc_empty_pop: bool = False
    count_empty_pop: bool = False
    loop_empty_pop: bool = False
    write_conflict: bool = False


@dataclass(frozen=True)
class _StackCycle:
    entries: tuple[int, ...]
    overflow: bool
    pop_value: int | None = None
    push_accepted: bool = False
    overflow_event: bool = False
    empty_pop: bool = False


def _apply_stack(
    entries: tuple[int, ...],
    overflow: bool,
    *,
    depth: int,
    push: bool,
    pop: bool,
    push_value: int,
) -> _StackCycle:
    if push:
        if len(entries) == depth:
            return _StackCycle(
                entries,
                True,
                overflow_event=True,
            )
        return _StackCycle(
            entries + (push_value,),
            overflow,
            push_accepted=True,
        )
    if pop:
        if not entries:
            return _StackCycle(entries, overflow, empty_pop=True)
        return _StackCycle(
            entries[:-1],
            overflow,
            pop_value=entries[-1],
        )
    return _StackCycle(entries, overflow)


def apply_sequencer_stacks_cycle(
    state: SequencerStacksState,
    inputs: SequencerStacksInputs,
) -> SequencerStacksCycleResult:
    """Apply one instruction-boundary operation to all three stack classes."""

    if inputs.reset:
        return SequencerStacksCycleResult(SequencerStacksState())

    conflict = (
        (inputs.pc_push and inputs.pc_pop)
        or (inputs.count_push and inputs.count_pop)
        or (inputs.loop_push and inputs.loop_pop)
    )
    if conflict:
        return SequencerStacksCycleResult(state, write_conflict=True)

    pc = _apply_stack(
        state.pc_entries,
        state.pc_overflow,
        depth=PC_STACK_DEPTH,
        push=inputs.pc_push,
        pop=inputs.pc_pop,
        push_value=inputs.pc_push_value,
    )
    count = _apply_stack(
        state.count_entries,
        state.count_overflow,
        depth=COUNT_STACK_DEPTH,
        push=inputs.count_push,
        pop=inputs.count_pop,
        push_value=inputs.count_push_value,
    )
    loop = _apply_stack(
        state.loop_entries,
        state.loop_overflow,
        depth=LOOP_STACK_DEPTH,
        push=inputs.loop_push,
        pop=inputs.loop_pop,
        push_value=inputs.loop_push_value,
    )
    next_state = SequencerStacksState(
        pc.entries,
        count.entries,
        loop.entries,
        pc.overflow,
        count.overflow,
        loop.overflow,
    )
    return SequencerStacksCycleResult(
        state=next_state,
        pc_pop_value=pc.pop_value,
        count_pop_value=count.pop_value,
        loop_pop_value=loop.pop_value,
        pc_push_accepted=pc.push_accepted,
        count_push_accepted=count.push_accepted,
        loop_push_accepted=loop.push_accepted,
        pc_overflow_event=pc.overflow_event,
        count_overflow_event=count.overflow_event,
        loop_overflow_event=loop.overflow_event,
        pc_empty_pop=pc.empty_pop,
        count_empty_pop=count.empty_pop,
        loop_empty_pop=loop.empty_pop,
    )
