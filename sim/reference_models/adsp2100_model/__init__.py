"""Independent, deliberately partial ADSP-2100 architectural model."""

from .conditions import (
    ConditionInputs,
    DO_TERMINATION_MNEMONICS,
    IF_CONDITION_MNEMONICS,
    evaluate_do_termination,
    evaluate_if_condition,
)
from .model import (
    ADSP2100Model,
    ArchitecturalState,
    ExactWord,
    MemorySpace,
    MemoryTransaction,
    ReservedOpcode,
    TransactionKind,
    TraceFrame,
    UNKNOWN,
    UnsupportedFeature,
    UnsupportedOpcode,
    mask_to_width,
    sign_extend,
)

__all__ = [
    "ADSP2100Model",
    "ArchitecturalState",
    "ConditionInputs",
    "DO_TERMINATION_MNEMONICS",
    "ExactWord",
    "IF_CONDITION_MNEMONICS",
    "MemorySpace",
    "MemoryTransaction",
    "ReservedOpcode",
    "TransactionKind",
    "TraceFrame",
    "UNKNOWN",
    "UnsupportedFeature",
    "UnsupportedOpcode",
    "evaluate_do_termination",
    "evaluate_if_condition",
    "mask_to_width",
    "sign_extend",
]
