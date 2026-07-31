"""Independent bounded original ADSP-2100 Type 9 execution model."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .alu import ALUResult, compute_alu
from .conditions import ConditionInputs, evaluate_if_condition
from .mac import MACResult, compute_mac
from .model import ComputationalBank, ExactWord, UNKNOWN
from .registers import (
    ALURegisterWrite,
    DREG,
    DREGWrite,
    MACRegisterWrite,
    apply_computational_cycle,
    apply_dreg_cycle,
    read_dreg,
)
from .status import (
    ALUStatusUpdate,
    ASTATBit,
    ASTATState,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
)


CONDITIONAL_COMPUTE_CLASS_MASK = 0xF800F0
CONDITIONAL_COMPUTE_CLASS_VALUE = 0x200000

ALU_X_DREG = (
    DREG.AX0,
    DREG.AX1,
    DREG.AR,
    DREG.MR0,
    DREG.MR1,
    DREG.MR2,
    DREG.SR0,
    DREG.SR1,
)
MAC_X_DREG = (
    DREG.MX0,
    DREG.MX1,
    DREG.AR,
    DREG.MR0,
    DREG.MR1,
    DREG.MR2,
    DREG.SR0,
    DREG.SR1,
)


@dataclass(frozen=True)
class ConditionalComputeAction:
    z: int
    amf: int
    yop: int
    xop: int
    condition: int

    @property
    def is_nop(self) -> bool:
        return self.amf == 0

    @property
    def is_mac(self) -> bool:
        return 0 < self.amf < 0x10

    @property
    def is_alu(self) -> bool:
        return self.amf >= 0x10

    @property
    def destination_feedback(self) -> bool:
        return bool(self.z)


def is_conditional_compute_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return (
        opcode & CONDITIONAL_COMPUTE_CLASS_MASK
        == CONDITIONAL_COMPUTE_CLASS_VALUE
    )


def decode_conditional_compute(opcode: int) -> ConditionalComputeAction | None:
    """Decode every field-defined original Type 9 word."""

    if not is_conditional_compute_class(opcode):
        return None
    return ConditionalComputeAction(
        z=(opcode >> 18) & 1,
        amf=(opcode >> 13) & 0x1F,
        yop=(opcode >> 11) & 0x3,
        xop=(opcode >> 8) & 0x7,
        condition=opcode & 0xF,
    )


@dataclass(frozen=True)
class ConditionalComputeState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)

    @classmethod
    def reset(cls) -> "ConditionalComputeState":
        return cls()


@dataclass(frozen=True)
class ConditionalComputeCycleResult:
    state: ConditionalComputeState
    action: ConditionalComputeAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    condition_known: bool = False
    condition_true: bool = False
    result_known: bool = False
    nop_action: bool = False
    alu_write: bool = False
    mac_write: bool = False
    alu_status_write: bool = False
    mac_status_write: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def _selected_bank(state: ConditionalComputeState) -> ComputationalBank:
    return state.alternate if state.status.alternate_bank else state.primary


def _replace_selected_bank(
    state: ConditionalComputeState,
    bank: ComputationalBank,
) -> ConditionalComputeState:
    if state.status.alternate_bank:
        return replace(state, alternate=bank)
    return replace(state, primary=bank)


def _condition_value(
    condition: int,
    astat: ASTATState,
    not_counter_expired: bool,
) -> bool | object:
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
    if any(astat.bit(bit) is UNKNOWN for bit in required):
        return UNKNOWN

    def known_or_false(bit: ASTATBit) -> bool:
        value = astat.bit(bit)
        return False if value is UNKNOWN else bool(value)

    return evaluate_if_condition(
        condition,
        ConditionInputs(
            az=known_or_false(ASTATBit.AZ),
            an=known_or_false(ASTATBit.AN),
            av=known_or_false(ASTATBit.AV),
            ac=known_or_false(ASTATBit.AC),
            as_flag=known_or_false(ASTATBit.AS),
            mv=known_or_false(ASTATBit.MV),
            not_counter_expired=not_counter_expired,
        ),
    )


def _invalidate_astat(
    status: StatusRegisters,
    bits_to_invalidate: tuple[ASTATBit, ...],
) -> StatusRegisters:
    bits = list(status.astat.bits)
    for bit in bits_to_invalidate:
        bits[int(bit)] = UNKNOWN
    return replace(status, astat=ASTATState(tuple(bits)))


def _invalidate_possible_result(
    state: ConditionalComputeState,
    action: ConditionalComputeAction,
) -> ConditionalComputeState:
    if action.is_nop:
        return state
    bank = _selected_bank(state)
    if action.is_mac:
        if action.destination_feedback:
            bank = replace(bank, mf=UNKNOWN)
        else:
            bank = replace(bank, mr=(UNKNOWN, UNKNOWN, UNKNOWN))
        status = _invalidate_astat(state.status, (ASTATBit.MV,))
    else:
        if action.destination_feedback:
            bank = replace(bank, af=UNKNOWN)
        else:
            bank = replace(bank, ar=UNKNOWN)
        affected = (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV, ASTATBit.AC)
        if action.amf == 0x1F:
            affected += (ASTATBit.AS,)
        status = _invalidate_astat(state.status, affected)
    return replace(_replace_selected_bank(state, bank), status=status)


def _known_mr(bank: ComputationalBank) -> ExactWord | None:
    mr0, mr1, mr2 = bank.mr
    if not all(isinstance(value, ExactWord) for value in (mr0, mr1, mr2)):
        return None
    assert isinstance(mr0, ExactWord)
    assert isinstance(mr1, ExactWord)
    assert isinstance(mr2, ExactWord)
    return ExactWord(40, (mr2.value << 32) | (mr1.value << 16) | mr0.value)


def _read_y(bank: ComputationalBank, action: ConditionalComputeAction) -> object:
    if action.yop == 3:
        return ExactWord(16, 0)
    if action.is_mac:
        return bank.mf if action.yop == 2 else bank.my[action.yop]
    return bank.af if action.yop == 2 else bank.ay[action.yop]


def _known_alu_result(
    state: ConditionalComputeState,
    action: ConditionalComputeAction,
) -> ALUResult | None:
    bank = _selected_bank(state)
    x = read_dreg(bank, ALU_X_DREG[action.xop])
    y = _read_y(bank, action)
    needs_x = action.amf not in (0x10, 0x11, 0x14, 0x15, 0x18)
    needs_y = action.amf not in (0x1B, 0x1F)
    needs_carry = action.amf in (0x12, 0x16, 0x1A)
    if needs_x and not isinstance(x, ExactWord):
        return None
    if needs_y and not isinstance(y, ExactWord):
        return None
    carry = state.status.astat.bit(ASTATBit.AC)
    previous_av = state.status.astat.bit(ASTATBit.AV)
    if needs_carry and carry is UNKNOWN:
        return None
    if state.status.overflow_latch and previous_av is UNKNOWN:
        return None
    return compute_alu(
        action.amf,
        0 if not isinstance(x, ExactWord) else x.value,
        0 if not isinstance(y, ExactWord) else y.value,
        carry_in=False if carry is UNKNOWN else bool(carry),
        previous_av=False if previous_av is UNKNOWN else bool(previous_av),
        sticky_av=state.status.overflow_latch,
        saturate_ar=state.status.saturate_ar,
        destination_is_ar=not action.destination_feedback,
    )


def _known_mac_result(
    state: ConditionalComputeState,
    action: ConditionalComputeAction,
) -> MACResult | None:
    bank = _selected_bank(state)
    x = read_dreg(bank, MAC_X_DREG[action.xop])
    y = _read_y(bank, action)
    if not isinstance(x, ExactWord) or not isinstance(y, ExactWord):
        return None
    mr = _known_mr(bank)
    needs_mr = action.amf in (0x02, 0x03) or action.amf >= 0x08
    if needs_mr and mr is None:
        return None
    return compute_mac(action.amf, x.value, y.value, 0 if mr is None else mr.value)


def _apply_compute_result(
    state: ConditionalComputeState,
    action: ConditionalComputeAction,
    compute: ALUResult | MACResult,
) -> ConditionalComputeState:
    alu_write = None
    mac_write = None
    status_inputs = StatusCycleInputs()
    if isinstance(compute, ALUResult):
        alu_write = ALURegisterWrite(
            action.destination_feedback,
            ExactWord(16, compute.destination_result),
        )
        status_inputs = StatusCycleInputs(
            alu=ALUStatusUpdate(
                compute.az,
                compute.an,
                compute.av,
                compute.ac,
                compute.as_value if compute.as_write else None,
            )
        )
    else:
        mac_write = MACRegisterWrite(
            action.destination_feedback,
            ExactWord(40, compute.result),
        )
        status_inputs = StatusCycleInputs(mac_mv=compute.mv)
    registers = apply_computational_cycle(
        state.primary,
        state.alternate,
        alternate_selected=state.status.alternate_bank,
        alu_write=alu_write,
        mac_write=mac_write,
    )
    status = apply_status_cycle(state.status, status_inputs).state
    return ConditionalComputeState(registers.primary, registers.alternate, status)


def apply_conditional_compute_cycle(
    state: ConditionalComputeState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    not_counter_expired: bool = False,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
) -> ConditionalComputeCycleResult:
    """Apply one reset, deterministic setup, or Type 9 instruction boundary."""

    for name, value, width in (
        ("ASTAT", setup_astat, 8),
        ("MSTAT", setup_mstat, 4),
        ("AF", setup_af, 16),
        ("MF", setup_mf, 16),
    ):
        if value is not None and value.width != width:
            raise ValueError(f"{name} setup must be exactly {width} bits")
    class_valid = is_conditional_compute_class(opcode)
    action = decode_conditional_compute(opcode)
    setup_count = sum(
        value is not None
        for value in (setup_astat, setup_mstat, setup_dreg, setup_af, setup_mf)
    )
    conflict = bool(
        not reset and ((execute and setup_count != 0) or setup_count > 1)
    )
    invalid = bool(not reset and execute and action is None)
    boundary = bool(
        not reset and execute and action is not None and setup_count == 0
    )
    condition = (
        UNKNOWN
        if action is None
        else _condition_value(
            action.condition,
            state.status.astat,
            not_counter_expired,
        )
    )
    common = {
        "action": action,
        "class_valid": class_valid,
        "action_valid": action is not None,
        "condition_known": condition is not UNKNOWN,
        "condition_true": condition is True,
        "nop_action": action is not None and action.is_nop,
    }
    if reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        return ConditionalComputeCycleResult(replace(state, status=status), **common)
    if conflict or invalid:
        return ConditionalComputeCycleResult(
            state,
            invalid_opcode=invalid,
            integration_conflict=conflict,
            **common,
        )
    if setup_astat is not None or setup_mstat is not None:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(astat_move=setup_astat, mstat_move=setup_mstat),
        ).state
        return ConditionalComputeCycleResult(replace(state, status=status), **common)
    if setup_dreg is not None:
        registers = apply_dreg_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            writes=(setup_dreg,),
        )
        return ConditionalComputeCycleResult(
            ConditionalComputeState(
                registers.primary,
                registers.alternate,
                state.status,
            ),
            **common,
        )
    if setup_af is not None or setup_mf is not None:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            alu_write=None if setup_af is None else ALURegisterWrite(True, setup_af),
            mac_write=None if setup_mf is None else MACRegisterWrite(
                True,
                ExactWord(40, setup_mf.value << 16),
            ),
        )
        return ConditionalComputeCycleResult(
            ConditionalComputeState(
                registers.primary,
                registers.alternate,
                state.status,
            ),
            **common,
        )
    if not boundary:
        return ConditionalComputeCycleResult(state, **common)

    assert action is not None
    if action.is_nop:
        return ConditionalComputeCycleResult(
            state,
            boundary_valid=True,
            result_known=True,
            **common,
        )
    if condition is UNKNOWN:
        return ConditionalComputeCycleResult(
            _invalidate_possible_result(state, action),
            boundary_valid=True,
            **common,
        )
    if condition is False:
        return ConditionalComputeCycleResult(
            state,
            boundary_valid=True,
            result_known=True,
            **common,
        )

    compute = (
        _known_mac_result(state, action)
        if action.is_mac
        else _known_alu_result(state, action)
    )
    if compute is None:
        return ConditionalComputeCycleResult(
            _invalidate_possible_result(state, action),
            boundary_valid=True,
            **common,
        )
    updated = _apply_compute_result(state, action, compute)
    return ConditionalComputeCycleResult(
        updated,
        boundary_valid=True,
        result_known=True,
        alu_write=action.is_alu,
        mac_write=action.is_mac,
        alu_status_write=action.is_alu,
        mac_status_write=action.is_mac,
        **common,
    )
