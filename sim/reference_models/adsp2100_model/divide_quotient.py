"""Independent bounded original ADSP-2100 Type 23 DIVQ model."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .divide_sign import DIVIDE_X_DREG
from .model import ComputationalBank, ExactWord, UNKNOWN
from .registers import (
    ALURegisterWrite,
    DREG,
    DREGWrite,
    apply_computational_cycle,
    read_dreg,
)
from .status import (
    ASTATBit,
    ASTATState,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
)


DIVIDE_QUOTIENT_CLASS_MASK = 0xFFF8FF
DIVIDE_QUOTIENT_CLASS_VALUE = 0x071000


@dataclass(frozen=True)
class DivideQuotientAction:
    xop: int

    @property
    def divisor_name(self) -> str:
        return ("AX0", "AX1", "AR", "MR0", "MR1", "MR2", "SR0", "SR1")[
            self.xop
        ]


def is_divide_quotient_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & DIVIDE_QUOTIENT_CLASS_MASK == DIVIDE_QUOTIENT_CLASS_VALUE


def decode_divide_quotient(opcode: int) -> DivideQuotientAction | None:
    """Decode all eight original Type 23 divisor selections."""

    if not is_divide_quotient_class(opcode):
        return None
    return DivideQuotientAction(xop=(opcode >> 8) & 0x7)


@dataclass(frozen=True)
class DivideQuotientState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)


@dataclass(frozen=True)
class DivideQuotientInputs:
    reset: bool = False
    execute: bool = False
    opcode: int = 0
    astat_write: ExactWord | None = None
    mstat_write: ExactWord | None = None
    dreg_write: DREGWrite | None = None
    af_write: ExactWord | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.opcode <= 0xFFFFFF:
            raise ValueError("opcode must fit 24 bits")
        if self.astat_write is not None and self.astat_write.width != 8:
            raise ValueError("ASTAT setup must be exactly 8 bits")
        if self.mstat_write is not None and self.mstat_write.width != 4:
            raise ValueError("MSTAT setup must be exactly 4 bits")
        if self.af_write is not None and self.af_write.width != 16:
            raise ValueError("AF setup must be exactly 16 bits")

    @property
    def setup_count(self) -> int:
        return sum(
            item is not None
            for item in (
                self.astat_write,
                self.mstat_write,
                self.dreg_write,
                self.af_write,
            )
        )


@dataclass(frozen=True)
class DivideQuotientCycleResult:
    state: DivideQuotientState
    action: DivideQuotientAction | None
    class_valid: bool
    action_valid: bool
    boundary_valid: bool
    invalid_opcode: bool
    integration_conflict: bool
    source_known: bool
    result_known: bool
    old_aq: bool | object
    add_divisor: bool | object
    new_aq: bool | object
    quotient_bit: bool | object
    divisor_before: object
    partial_remainder_before: object
    ay0_before: object
    alu_result: object
    af_write: bool
    ay0_write: bool
    aq_write: bool
    pm_data_access: bool = False
    dm_access: bool = False


def _replace_selected_bank(
    state: DivideQuotientState,
    bank: ComputationalBank,
) -> DivideQuotientState:
    if state.status.alternate_bank:
        return replace(state, alternate=bank)
    return replace(state, primary=bank)


def _invalidate_divide_destinations(
    state: DivideQuotientState,
) -> DivideQuotientState:
    selected = state.alternate if state.status.alternate_bank else state.primary
    selected = replace(selected, ay=(UNKNOWN, selected.ay[1]), af=UNKNOWN)
    bits = list(state.status.astat.bits)
    bits[int(ASTATBit.AQ)] = UNKNOWN
    status = replace(state.status, astat=ASTATState(tuple(bits)))
    return replace(_replace_selected_bank(state, selected), status=status)


def apply_divide_quotient_cycle(
    state: DivideQuotientState,
    inputs: DivideQuotientInputs,
) -> DivideQuotientCycleResult:
    """Apply one atomic Type 23 quotient-bit iteration."""

    action = decode_divide_quotient(inputs.opcode)
    class_valid = action is not None
    action_valid = class_valid
    selected = state.alternate if state.status.alternate_bank else state.primary
    divisor = (
        read_dreg(selected, DIVIDE_X_DREG[action.xop])
        if action is not None
        else UNKNOWN
    )
    partial = selected.af
    ay0 = read_dreg(selected, DREG.AY0)
    old_aq = state.status.astat.bit(ASTATBit.AQ)
    common = {
        "action": action,
        "class_valid": class_valid,
        "action_valid": action_valid,
        "old_aq": old_aq,
        "divisor_before": divisor,
        "partial_remainder_before": partial,
        "ay0_before": ay0,
    }

    if inputs.reset:
        reset_status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        return DivideQuotientCycleResult(
            DivideQuotientState(status=reset_status),
            boundary_valid=False,
            invalid_opcode=False,
            integration_conflict=False,
            source_known=False,
            result_known=False,
            add_divisor=UNKNOWN,
            new_aq=UNKNOWN,
            quotient_bit=UNKNOWN,
            alu_result=UNKNOWN,
            af_write=False,
            ay0_write=False,
            aq_write=False,
            **common,
        )

    conflict = bool(
        (inputs.execute and inputs.setup_count != 0) or inputs.setup_count > 1
    )
    if conflict:
        return DivideQuotientCycleResult(
            state,
            boundary_valid=False,
            invalid_opcode=bool(inputs.execute and not action_valid),
            integration_conflict=True,
            source_known=False,
            result_known=False,
            add_divisor=UNKNOWN,
            new_aq=UNKNOWN,
            quotient_bit=UNKNOWN,
            alu_result=UNKNOWN,
            af_write=False,
            ay0_write=False,
            aq_write=False,
            **common,
        )

    next_state = state
    if inputs.astat_write is not None or inputs.mstat_write is not None:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(
                astat_move=inputs.astat_write,
                mstat_move=inputs.mstat_write,
            ),
        ).state
        next_state = replace(next_state, status=status)
    elif inputs.dreg_write is not None or inputs.af_write is not None:
        register_result = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            dreg_writes=(inputs.dreg_write,) if inputs.dreg_write else (),
            alu_write=(
                ALURegisterWrite(True, inputs.af_write)
                if inputs.af_write is not None
                else None
            ),
        )
        next_state = replace(
            next_state,
            primary=register_result.primary,
            alternate=register_result.alternate,
        )

    boundary_valid = bool(inputs.execute and action_valid)
    source_known = bool(
        boundary_valid
        and isinstance(divisor, ExactWord)
        and isinstance(partial, ExactWord)
        and isinstance(ay0, ExactWord)
        and isinstance(old_aq, bool)
    )
    add_divisor: bool | object = UNKNOWN
    new_aq: bool | object = UNKNOWN
    quotient_bit: bool | object = UNKNOWN
    alu_result: ExactWord | object = UNKNOWN
    if boundary_valid:
        if source_known:
            assert isinstance(divisor, ExactWord)
            assert isinstance(partial, ExactWord)
            assert isinstance(ay0, ExactWord)
            assert isinstance(old_aq, bool)
            add_divisor = old_aq
            raw_result = (
                partial.value + divisor.value
                if old_aq
                else partial.value - divisor.value
            ) & 0xFFFF
            alu_result = ExactWord(16, raw_result)
            new_aq = bool(((divisor.value ^ raw_result) >> 15) & 1)
            quotient_bit = not new_aq
            af_result = ExactWord(
                16,
                ((raw_result << 1) & 0xFFFF) | (ay0.value >> 15),
            )
            ay0_result = ExactWord(
                16,
                ((ay0.value << 1) & 0xFFFF) | int(quotient_bit),
            )
            register_result = apply_computational_cycle(
                state.primary,
                state.alternate,
                alternate_selected=state.status.alternate_bank,
                dreg_writes=(DREGWrite(DREG.AY0, ay0_result),),
                alu_write=ALURegisterWrite(True, af_result),
            )
            status = apply_status_cycle(
                state.status,
                StatusCycleInputs(divide_aq=bool(new_aq)),
            ).state
            next_state = DivideQuotientState(
                register_result.primary,
                register_result.alternate,
                status,
            )
        else:
            next_state = _invalidate_divide_destinations(state)

    return DivideQuotientCycleResult(
        next_state,
        boundary_valid=boundary_valid,
        invalid_opcode=bool(inputs.execute and not action_valid),
        integration_conflict=False,
        source_known=source_known,
        result_known=source_known,
        add_divisor=add_divisor,
        new_aq=new_aq,
        quotient_bit=quotient_bit,
        alu_result=alu_result,
        af_write=boundary_valid,
        ay0_write=boundary_valid,
        aq_write=boundary_valid,
        **common,
    )
