"""Deterministic one-minimal reduction for replayable failing programs."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Callable, Generic, Hashable, Iterable, TypeVar


Item = TypeVar("Item", bound=Hashable)


@dataclass(frozen=True)
class ReductionResult(Generic[Item]):
    original_length: int
    items: tuple[Item, ...]
    evaluations: int


def reduce_failing_sequence(
    items: Iterable[Item],
    preserves_failure: Callable[[tuple[Item, ...]], bool],
) -> ReductionResult[Item]:
    """Return a deterministic one-minimal subsequence preserving a failure.

    The callback defines failure identity, so an adapter can require the same
    mismatch path/signature rather than accepting an unrelated crash.  The
    reducer never reorders or changes an item.
    """

    original = tuple(items)
    evaluations = 0
    cache: dict[tuple[Item, ...], bool] = {}

    def evaluate(candidate: tuple[Item, ...]) -> bool:
        nonlocal evaluations
        if candidate not in cache:
            cache[candidate] = bool(preserves_failure(candidate))
            evaluations += 1
        return cache[candidate]

    if not evaluate(original):
        raise ValueError("initial sequence does not preserve the requested failure")

    current = original
    granularity = 2
    while current:
        chunk_size = ceil(len(current) / granularity)
        reduced = False
        for start in range(0, len(current), chunk_size):
            candidate = current[:start] + current[start + chunk_size :]
            if evaluate(candidate):
                current = candidate
                granularity = max(2, granularity - 1)
                reduced = True
                break
        if reduced:
            continue
        if granularity >= len(current):
            break
        granularity = min(len(current), granularity * 2)

    # Delta debugging is one-minimal at unit granularity, but an explicit
    # fixed point keeps that property obvious if the chunk strategy changes.
    index = 0
    while index < len(current):
        candidate = current[:index] + current[index + 1 :]
        if evaluate(candidate):
            current = candidate
        else:
            index += 1

    return ReductionResult(
        original_length=len(original), items=current, evaluations=evaluations
    )
