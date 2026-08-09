"""Independent-model adapter for the common differential trace schema."""

from __future__ import annotations

from typing import Final

from sim.reference_models.adsp2100_model.model import (
    ArchitecturalState,
    ComputationalBank,
    ExactWord,
    MemoryTransaction,
    TraceFrame,
    UNKNOWN,
)
from tools.trace.adsp2100_trace import (
    DifferentialTraceFrame,
    TraceTransaction,
    TraceWord,
)


_BANK_FIELDS: Final = (
    ("ax0", "ax", 0, 16),
    ("ax1", "ax", 1, 16),
    ("ay0", "ay", 0, 16),
    ("ay1", "ay", 1, 16),
    ("ar", "ar", None, 16),
    ("af", "af", None, 16),
    ("mx0", "mx", 0, 16),
    ("mx1", "mx", 1, 16),
    ("my0", "my", 0, 16),
    ("my1", "my", 1, 16),
    ("mf", "mf", None, 16),
    ("mr0", "mr", 0, 16),
    ("mr1", "mr", 1, 16),
    ("mr2", "mr", 2, 8),
    ("si", "si", None, 16),
    ("se", "se", None, 8),
    ("sb", "sb", None, 5),
    ("sr0", "sr", 0, 16),
    ("sr1", "sr", 1, 16),
)


def _trace_word(value: object, width: int) -> TraceWord:
    if value is UNKNOWN:
        return TraceWord.unknown(width)
    if not isinstance(value, ExactWord):
        raise TypeError(f"expected ExactWord or UNKNOWN, received {type(value)!r}")
    if value.width != width:
        raise ValueError(
            f"model word width {value.width} differs from trace width {width}"
        )
    return TraceWord.known(width, value.value)


def _snapshot_bank(
    state: dict[str, TraceWord], prefix: str, bank: ComputationalBank
) -> None:
    for name, attribute, index, width in _BANK_FIELDS:
        value = getattr(bank, attribute)
        if index is not None:
            value = value[index]
        state[f"{prefix}.{name}"] = _trace_word(value, width)


def snapshot_architectural_state(
    state: ArchitecturalState,
) -> dict[str, TraceWord]:
    """Flatten all currently represented architectural state after retirement."""

    snapshot: dict[str, TraceWord] = {
        "pc": _trace_word(state.pc, 14),
        "px": _trace_word(state.px, 8),
        "astat": _trace_word(state.astat, 8),
        "sstat": _trace_word(state.sstat, 8),
        "mstat": TraceWord(
            width=4,
            value=state.mstat.value & state.mstat_valid_mask,
            known_mask=state.mstat_valid_mask,
        ),
        "imask": _trace_word(state.imask, 4),
        "icntl": _trace_word(state.icntl, 5),
        "cntr": _trace_word(state.cntr, 14),
        "pc_stack.depth": TraceWord.known(5, len(state.pc_stack)),
        "loop_stack.depth": TraceWord.known(3, len(state.loop_stack)),
        "count_stack.depth": TraceWord.known(3, len(state.count_stack)),
        "status_stack.depth": TraceWord.known(3, len(state.status_stack)),
    }
    _snapshot_bank(snapshot, "primary", state.primary)
    _snapshot_bank(snapshot, "alternate", state.alternate)

    for kind, values in (("i", state.dag.i), ("m", state.dag.m), ("l", state.dag.l)):
        for index, value in enumerate(values):
            snapshot[f"dag.{kind}{index}"] = _trace_word(value, 14)

    for index, value in enumerate(state.pc_stack):
        snapshot[f"pc_stack.{index}"] = _trace_word(value, 14)
    for index, (end, termination) in enumerate(state.loop_stack):
        snapshot[f"loop_stack.{index}.end"] = _trace_word(end, 14)
        snapshot[f"loop_stack.{index}.termination"] = _trace_word(
            termination, 4
        )
    for index, value in enumerate(state.count_stack):
        snapshot[f"count_stack.{index}"] = _trace_word(value, 14)
    for index, (astat, mstat, mstat_valid_mask, imask) in enumerate(
        state.status_stack
    ):
        snapshot[f"status_stack.{index}.astat"] = _trace_word(astat, 8)
        snapshot[f"status_stack.{index}.mstat"] = TraceWord(
            width=4,
            value=mstat.value & mstat_valid_mask,
            known_mask=mstat_valid_mask,
        )
        snapshot[f"status_stack.{index}.imask"] = _trace_word(imask, 4)
    return snapshot


def adapt_memory_transaction(transaction: MemoryTransaction) -> TraceTransaction:
    data = transaction.data
    return TraceTransaction(
        space=transaction.space.value,
        kind=transaction.kind.value,
        address=_trace_word(transaction.address, 14),
        width=transaction.width,
        data=None if data is None else _trace_word(data, transaction.width),
        wait_instruction_cycles=transaction.wait_instruction_cycles,
    )

def adapt_model_trace_frame(
    frame: TraceFrame,
    state_after: ArchitecturalState,
    *,
    producer: str = "independent-model",
) -> DifferentialTraceFrame:
    """Adapt one model retirement and its post-retirement state."""

    if frame.pc_after != state_after.pc:
        raise ValueError("model frame PC and supplied post-retirement state differ")
    return DifferentialTraceFrame.create(
        producer=producer,
        retirement_index=frame.retirement_index,
        pc_before=_trace_word(frame.pc_before, 14),
        pc_after=_trace_word(frame.pc_after, 14),
        opcode=_trace_word(frame.opcode, 24),
        instruction_cycles=frame.instruction_cycles,
        state=snapshot_architectural_state(state_after),
        transactions=tuple(
            adapt_memory_transaction(transaction)
            for transaction in frame.transactions
        ),
    )
