"""Independent, deliberately partial ADSP-2100 architectural model."""

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
    "ExactWord",
    "MemorySpace",
    "MemoryTransaction",
    "ReservedOpcode",
    "TransactionKind",
    "TraceFrame",
    "UNKNOWN",
    "UnsupportedFeature",
    "UnsupportedOpcode",
    "mask_to_width",
    "sign_extend",
]
