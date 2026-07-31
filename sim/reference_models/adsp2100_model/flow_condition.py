"""Shared independent-model evaluation for program-flow IF conditions."""

from __future__ import annotations

from .conditions import ConditionInputs, evaluate_if_condition
from .counter import CounterState
from .model import UNKNOWN
from .status import ASTATBit, ASTATState


def evaluate_flow_condition(
    condition: int,
    astat: ASTATState,
    counter: CounterState,
) -> bool | object:
    """Evaluate one original IF field while preserving unknown inputs."""

    required = {
        0: (ASTATBit.AZ,),
        1: (ASTATBit.AZ,),
        2: (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV),
        3: (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV),
        4: (ASTATBit.AN, ASTATBit.AV),
        5: (ASTATBit.AN, ASTATBit.AV),
        6: (ASTATBit.AV,),
        7: (ASTATBit.AV,),
        8: (ASTATBit.AC,),
        9: (ASTATBit.AC,),
        10: (ASTATBit.AS,),
        11: (ASTATBit.AS,),
        12: (ASTATBit.MV,),
        13: (ASTATBit.MV,),
        14: (),
        15: (),
    }[condition]
    if condition == 14:
        return UNKNOWN if counter.value is None else counter.value != 1
    if any(astat.bit(bit) is UNKNOWN for bit in required):
        return UNKNOWN

    def known(bit: ASTATBit) -> bool:
        value = astat.bit(bit)
        assert value is not UNKNOWN
        return bool(value)

    return evaluate_if_condition(
        condition,
        ConditionInputs(
            az=known(ASTATBit.AZ) if ASTATBit.AZ in required else False,
            an=known(ASTATBit.AN) if ASTATBit.AN in required else False,
            av=known(ASTATBit.AV) if ASTATBit.AV in required else False,
            ac=known(ASTATBit.AC) if ASTATBit.AC in required else False,
            as_flag=known(ASTATBit.AS) if ASTATBit.AS in required else False,
            mv=known(ASTATBit.MV) if ASTATBit.MV in required else False,
            not_counter_expired=False,
        ),
    )
