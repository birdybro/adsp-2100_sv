"""Independent, deliberately partial ADSP-2100 architectural model."""

from .alu import ALUResult, compute_alu
from .conditions import (
    ConditionInputs,
    DO_TERMINATION_MNEMONICS,
    IF_CONDITION_MNEMONICS,
    evaluate_do_termination,
    evaluate_if_condition,
)
from .dag import DAGResult, compute_dag, original_base_mask, reverse_address
from .mac import MACResult, compute_mac, saturate_mr
from .shifter import ShifterResult, compute_shifter
from .sequencer import (
    ExplicitFlow,
    SequencerFlowResult,
    select_sequencer_flow,
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
    "ALUResult",
    "ArchitecturalState",
    "ConditionInputs",
    "DO_TERMINATION_MNEMONICS",
    "DAGResult",
    "ExplicitFlow",
    "ExactWord",
    "IF_CONDITION_MNEMONICS",
    "MemorySpace",
    "MemoryTransaction",
    "MACResult",
    "ShifterResult",
    "SequencerFlowResult",
    "ReservedOpcode",
    "TransactionKind",
    "TraceFrame",
    "UNKNOWN",
    "UnsupportedFeature",
    "UnsupportedOpcode",
    "evaluate_do_termination",
    "evaluate_if_condition",
    "compute_alu",
    "compute_dag",
    "compute_mac",
    "compute_shifter",
    "mask_to_width",
    "original_base_mask",
    "reverse_address",
    "select_sequencer_flow",
    "sign_extend",
    "saturate_mr",
]
