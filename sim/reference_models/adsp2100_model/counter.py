"""Independent state model for the original ADSP-2100 CNTR register.

CNTR validity is architectural sequencer state that is not represented by the
14-bit register value alone. A counter-expired (CE) test observes the
cycle-start value and the post-decrement or outer-count restore occurs at the
cycle boundary.
"""

from __future__ import annotations

from dataclasses import dataclass


COUNTER_MASK = 0x3FFF


def _require_counter(value: int, name: str) -> None:
    if not 0 <= value <= COUNTER_MASK:
        raise ValueError(f"{name} must fit 14 bits")


@dataclass(frozen=True)
class CounterState:
    """The 14-bit CNTR value, or ``None`` when CNTR has no valid value."""

    value: int | None = None

    def __post_init__(self) -> None:
        if self.value is not None:
            _require_counter(self.value, "counter value")


@dataclass(frozen=True)
class CounterInputs:
    reset: bool = False
    load: bool = False
    load_value: int = 0
    ce_test: bool = False
    manual_pop: bool = False
    count_stack_top: int = 0
    count_stack_top_valid: bool = False

    def __post_init__(self) -> None:
        _require_counter(self.load_value, "counter load value")
        _require_counter(self.count_stack_top, "count-stack top")


@dataclass(frozen=True)
class CounterCycleResult:
    state: CounterState
    condition_valid: bool = False
    counter_expired: bool = False
    not_counter_expired: bool = False
    count_stack_push: bool = False
    count_stack_push_value: int = 0
    count_stack_pop: bool = False
    decremented: bool = False
    restored: bool = False
    empty_ce_invalidated: bool = False
    invalid_ce_test: bool = False
    empty_manual_pop: bool = False
    write_conflict: bool = False


def apply_counter_cycle(
    state: CounterState,
    inputs: CounterInputs,
) -> CounterCycleResult:
    """Apply one instruction-boundary CNTR operation.

    ``ce_test`` is valid only for the sourced decrementing contexts: a
    counter-terminated loop end or a qualifying conditional jump. Conditional
    CALL remains outside this boundary under OQ-012. Empty manual-pop behavior
    remains OQ-013; the model flags it and preserves state instead of assigning
    invented architectural data.
    """

    if inputs.reset:
        return CounterCycleResult(CounterState())

    action_count = sum((inputs.load, inputs.ce_test, inputs.manual_pop))
    if action_count > 1:
        return CounterCycleResult(state, write_conflict=True)

    valid = state.value is not None
    value = state.value if valid else 0
    expired = bool(valid and value == 1)
    not_expired = bool(valid and value != 1)

    common = {
        "condition_valid": valid,
        "counter_expired": expired,
        "not_counter_expired": not_expired,
    }

    if inputs.load:
        return CounterCycleResult(
            CounterState(inputs.load_value),
            count_stack_push=valid,
            count_stack_push_value=value,
            **common,
        )

    if inputs.manual_pop:
        if inputs.count_stack_top_valid:
            return CounterCycleResult(
                CounterState(inputs.count_stack_top),
                count_stack_pop=True,
                restored=True,
                **common,
            )
        return CounterCycleResult(
            state,
            count_stack_pop=True,
            empty_manual_pop=True,
            **common,
        )

    if inputs.ce_test:
        if not valid:
            return CounterCycleResult(
                state,
                invalid_ce_test=True,
                **common,
            )
        if expired:
            if inputs.count_stack_top_valid:
                return CounterCycleResult(
                    CounterState(inputs.count_stack_top),
                    count_stack_pop=True,
                    restored=True,
                    **common,
                )
            return CounterCycleResult(
                CounterState(),
                count_stack_pop=True,
                empty_ce_invalidated=True,
                **common,
            )
        return CounterCycleResult(
            CounterState((value - 1) & COUNTER_MASK),
            decremented=True,
            **common,
        )

    return CounterCycleResult(state, **common)
