"""Independent bounded original ADSP-2100 Type 24 DIVS model."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

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


DIVIDE_SIGN_CLASS_MASK = 0xFFE0FF
DIVIDE_SIGN_CLASS_VALUE = 0x060000

# Appendix B and the contemporary assembler manual define the divisor as any
# ALU X operand.  The exact-device DIVS prose restricts the upper dividend to
# AY1 or AF; the other two field-defined Y codes fail closed.
DIVIDE_X_DREG = (
    DREG.AX0,
    DREG.AX1,
    DREG.AR,
    DREG.MR0,
    DREG.MR1,
    DREG.MR2,
    DREG.SR0,
    DREG.SR1,
)


@dataclass(frozen=True)
class DivideSignAction:
    yop: int
    xop: int

    @property
    def supported(self) -> bool:
        return self.yop in (1, 2)

    @property
    def upper_dividend_name(self) -> str | None:
        return {1: "AY1", 2: "AF"}.get(self.yop)


def is_divide_sign_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & DIVIDE_SIGN_CLASS_MASK == DIVIDE_SIGN_CLASS_VALUE


def decode_divide_sign(opcode: int) -> DivideSignAction | None:
    """Decode every field-defined Type 24 word, including unsupported YOPs."""

    if not is_divide_sign_class(opcode):
        return None
    return DivideSignAction(yop=(opcode >> 11) & 0x3, xop=(opcode >> 8) & 0x7)


@dataclass(frozen=True)
class DivideSignState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)


@dataclass(frozen=True)
class DivideSignInputs:
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
class DivideSignCycleResult:
    state: DivideSignState
    action: DivideSignAction | None
    class_valid: bool
    action_valid: bool
    unsupported_subencoding: bool
    boundary_valid: bool
    invalid_opcode: bool
    integration_conflict: bool
    source_known: bool
    result_known: bool
    quotient_sign: bool | object
    af_before: object
    ay0_before: object
    divisor_before: object
    af_write: bool
    ay0_write: bool
    aq_write: bool
    pm_data_access: bool = False
    dm_access: bool = False


def _replace_selected_bank(
    state: DivideSignState,
    bank: ComputationalBank,
) -> DivideSignState:
    if state.status.alternate_bank:
        return replace(state, alternate=bank)
    return replace(state, primary=bank)


def _invalidate_divide_destinations(state: DivideSignState) -> DivideSignState:
    selected = state.alternate if state.status.alternate_bank else state.primary
    selected = replace(selected, ay=(UNKNOWN, selected.ay[1]), af=UNKNOWN)
    bits = list(state.status.astat.bits)
    bits[int(ASTATBit.AQ)] = UNKNOWN
    status = replace(state.status, astat=ASTATState(tuple(bits)))
    return replace(_replace_selected_bank(state, selected), status=status)


def apply_divide_sign_cycle(
    state: DivideSignState,
    inputs: DivideSignInputs,
) -> DivideSignCycleResult:
    """Apply one atomic Type 24 cycle-start-read/cycle-end-write boundary."""

    action = decode_divide_sign(inputs.opcode)
    class_valid = action is not None
    action_valid = bool(action is not None and action.supported)
    unsupported = bool(class_valid and not action_valid)
    selected = state.alternate if state.status.alternate_bank else state.primary
    ay0 = read_dreg(selected, DREG.AY0)
    upper = UNKNOWN
    divisor = UNKNOWN
    if action is not None:
        if action.yop == 1:
            upper = read_dreg(selected, DREG.AY1)
        elif action.yop == 2:
            upper = selected.af
        divisor = read_dreg(selected, DIVIDE_X_DREG[action.xop])

    common = {
        "action": action,
        "class_valid": class_valid,
        "action_valid": action_valid,
        "unsupported_subencoding": unsupported,
        "af_before": upper,
        "ay0_before": ay0,
        "divisor_before": divisor,
    }
    if inputs.reset:
        reset_status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        return DivideSignCycleResult(
            DivideSignState(status=reset_status),
            boundary_valid=False,
            invalid_opcode=False,
            integration_conflict=False,
            source_known=False,
            result_known=False,
            quotient_sign=UNKNOWN,
            af_write=False,
            ay0_write=False,
            aq_write=False,
            **common,
        )

    conflict = bool(
        (inputs.execute and inputs.setup_count != 0) or inputs.setup_count > 1
    )
    if conflict:
        return DivideSignCycleResult(
            state,
            boundary_valid=False,
            invalid_opcode=bool(inputs.execute and not action_valid),
            integration_conflict=True,
            source_known=False,
            result_known=False,
            quotient_sign=UNKNOWN,
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
        and isinstance(upper, ExactWord)
        and isinstance(ay0, ExactWord)
        and isinstance(divisor, ExactWord)
    )
    quotient_sign: bool | object = UNKNOWN
    if boundary_valid:
        if source_known:
            assert isinstance(upper, ExactWord)
            assert isinstance(ay0, ExactWord)
            assert isinstance(divisor, ExactWord)
            quotient_sign = bool(((divisor.value ^ upper.value) >> 15) & 1)
            af_result = ExactWord(
                16,
                ((upper.value << 1) & 0xFFFF) | (ay0.value >> 15),
            )
            ay0_result = ExactWord(
                16,
                ((ay0.value << 1) & 0xFFFF) | int(quotient_sign),
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
                StatusCycleInputs(divide_aq=bool(quotient_sign)),
            ).state
            next_state = DivideSignState(
                register_result.primary,
                register_result.alternate,
                status,
            )
        else:
            next_state = _invalidate_divide_destinations(state)

    return DivideSignCycleResult(
        next_state,
        boundary_valid=boundary_valid,
        invalid_opcode=bool(inputs.execute and not action_valid),
        integration_conflict=False,
        source_known=source_known,
        result_known=source_known,
        quotient_sign=quotient_sign,
        af_write=boundary_valid,
        ay0_write=boundary_valid,
        aq_write=boundary_valid,
        **common,
    )
