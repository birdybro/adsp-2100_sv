"""Independent original ADSP-2100 Type 16 conditional-shifter model."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .conditions import ConditionInputs, evaluate_if_condition
from .model import ComputationalBank, ExactWord, UNKNOWN
from .registers import (
    DREG,
    DREGWrite,
    ShifterRegisterWrite,
    apply_computational_cycle,
    apply_dreg_cycle,
    read_dreg,
)
from .shifter import ShifterResult, compute_shifter
from .status import (
    ASTATBit,
    ASTATState,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
)


CONDITIONAL_SHIFT_MASK = 0xFF80F0
CONDITIONAL_SHIFT_VALUE = 0x0E0000

SHIFTER_XOP_DREG = {
    0: DREG.SI,
    2: DREG.AR,
    3: DREG.MR0,
    4: DREG.MR1,
    5: DREG.MR2,
    6: DREG.SR0,
    7: DREG.SR1,
}


@dataclass(frozen=True)
class ConditionalShiftAction:
    sf: int
    xop: int
    source: DREG
    condition: int


def is_conditional_shift_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & CONDITIONAL_SHIFT_MASK == CONDITIONAL_SHIFT_VALUE


def decode_conditional_shift(opcode: int) -> ConditionalShiftAction | None:
    """Decode every field-defined Type 16 action except absent XOP code 001."""

    if not is_conditional_shift_class(opcode):
        return None
    xop = (opcode >> 8) & 0x7
    if xop not in SHIFTER_XOP_DREG:
        return None
    return ConditionalShiftAction(
        sf=(opcode >> 11) & 0xF,
        xop=xop,
        source=SHIFTER_XOP_DREG[xop],
        condition=opcode & 0xF,
    )


@dataclass(frozen=True)
class ConditionalShiftState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)

    @classmethod
    def reset(cls) -> "ConditionalShiftState":
        return cls()


@dataclass(frozen=True)
class ConditionalShiftCycleResult:
    state: ConditionalShiftState
    action: ConditionalShiftAction | None = None
    class_valid: bool = False
    unsupported_subencoding: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    condition_known: bool = False
    condition_true: bool = False
    result_known: bool = False
    sr_write: bool = False
    se_write: bool = False
    sb_write: bool = False
    ss_write: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def _selected_bank(state: ConditionalShiftState) -> ComputationalBank:
    return state.alternate if state.status.alternate_bank else state.primary


def _known_sr(bank: ComputationalBank) -> ExactWord | None:
    sr0, sr1 = bank.sr
    if not isinstance(sr0, ExactWord) or not isinstance(sr1, ExactWord):
        return None
    return ExactWord(32, (sr1.value << 16) | sr0.value)


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


def _replace_selected_bank(
    state: ConditionalShiftState,
    bank: ComputationalBank,
) -> ConditionalShiftState:
    if state.status.alternate_bank:
        return replace(state, alternate=bank)
    return replace(state, primary=bank)


def _invalidate_ss(status: StatusRegisters) -> StatusRegisters:
    bits = list(status.astat.bits)
    bits[int(ASTATBit.SS)] = UNKNOWN
    return replace(status, astat=ASTATState(tuple(bits)))


def _invalidate_possible_result(
    state: ConditionalShiftState,
    action: ConditionalShiftAction,
) -> ConditionalShiftState:
    bank = _selected_bank(state)
    status = state.status
    if action.sf <= 0xB:
        bank = replace(bank, sr=(UNKNOWN, UNKNOWN))
    elif action.sf in (0xC, 0xD):
        bank = replace(bank, se=UNKNOWN)
        status = _invalidate_ss(status)
    elif action.sf == 0xE:
        if not isinstance(bank.se, ExactWord) or bank.se.value == 0xF1:
            bank = replace(bank, se=UNKNOWN)
    else:
        bank = replace(bank, sb=UNKNOWN)
    return replace(_replace_selected_bank(state, bank), status=status)


def _compute_known_action(
    state: ConditionalShiftState,
    action: ConditionalShiftAction,
) -> ShifterResult | None:
    bank = _selected_bank(state)
    source = read_dreg(bank, action.source)
    if not isinstance(source, ExactWord):
        return None

    se = bank.se
    sb = bank.sb
    sr = _known_sr(bank)
    astat = state.status.astat
    av = astat.bit(ASTATBit.AV)
    ac = astat.bit(ASTATBit.AC)
    ss = astat.bit(ASTATBit.SS)

    if action.sf <= 0xB:
        if not isinstance(se, ExactWord):
            return None
        if action.sf & 1 and sr is None:
            return None
        if action.sf in (0x8, 0x9) and ac is UNKNOWN:
            return None
    elif action.sf == 0xD and av is UNKNOWN:
        return None
    elif action.sf == 0xE:
        if not isinstance(se, ExactWord):
            return None
        if se.value != 0xF1:
            return compute_shifter(
                action.sf,
                source.value,
                se.value,
                0 if sr is None else sr.value,
                0 if not isinstance(sb, ExactWord) else sb.value,
            )
        if ss is UNKNOWN:
            return None
    elif action.sf == 0xF and not isinstance(sb, ExactWord):
        return None

    return compute_shifter(
        action.sf,
        source.value,
        0 if not isinstance(se, ExactWord) else se.value,
        0 if sr is None else sr.value,
        0 if not isinstance(sb, ExactWord) else sb.value,
        av=False if av is UNKNOWN else bool(av),
        ac=False if ac is UNKNOWN else bool(ac),
        ss=False if ss is UNKNOWN else bool(ss),
    )


def _apply_shifter_result(
    state: ConditionalShiftState,
    result: ShifterResult,
) -> ConditionalShiftState:
    write = None
    if result.sr_write:
        write = ShifterRegisterWrite(sr=ExactWord(32, result.sr_result))
    elif result.se_write:
        write = ShifterRegisterWrite(se=ExactWord(8, result.se_result))
    elif result.sb_write:
        write = ShifterRegisterWrite(sb=ExactWord(5, result.sb_result))

    primary = state.primary
    alternate = state.alternate
    if write is not None:
        registers = apply_computational_cycle(
            primary,
            alternate,
            alternate_selected=state.status.alternate_bank,
            shifter_write=write,
        )
        primary = registers.primary
        alternate = registers.alternate
    status = apply_status_cycle(
        state.status,
        StatusCycleInputs(
            shifter_ss=result.ss_result if result.ss_write else None,
        ),
    ).state
    return ConditionalShiftState(primary, alternate, status)


def apply_conditional_shift_cycle(
    state: ConditionalShiftState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    not_counter_expired: bool = False,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_sb: ExactWord | None = None,
) -> ConditionalShiftCycleResult:
    """Apply one reset, deterministic setup, or Type 16 instruction boundary."""

    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly eight bits")
    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    if setup_sb is not None and setup_sb.width != 5:
        raise ValueError("SB setup must be exactly five bits")

    class_valid = is_conditional_shift_class(opcode)
    action = decode_conditional_shift(opcode)
    unsupported = class_valid and action is None
    setups = (setup_astat, setup_mstat, setup_dreg, setup_sb)
    setup_count = sum(value is not None for value in setups)
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
        "unsupported_subencoding": unsupported,
        "condition_known": condition is not UNKNOWN,
        "condition_true": condition is True,
    }

    if reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        return ConditionalShiftCycleResult(
            replace(state, status=status),
            **common,
        )
    if conflict or invalid:
        return ConditionalShiftCycleResult(
            state,
            invalid_opcode=invalid,
            integration_conflict=conflict,
            **common,
        )
    if setup_astat is not None or setup_mstat is not None:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(
                astat_move=setup_astat,
                mstat_move=setup_mstat,
            ),
        ).state
        return ConditionalShiftCycleResult(
            replace(state, status=status),
            **common,
        )
    if setup_dreg is not None:
        registers = apply_dreg_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            writes=(setup_dreg,),
        )
        return ConditionalShiftCycleResult(
            ConditionalShiftState(
                registers.primary,
                registers.alternate,
                state.status,
            ),
            **common,
        )
    if setup_sb is not None:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            shifter_write=ShifterRegisterWrite(sb=setup_sb),
        )
        return ConditionalShiftCycleResult(
            ConditionalShiftState(
                registers.primary,
                registers.alternate,
                state.status,
            ),
            **common,
        )
    if not boundary:
        return ConditionalShiftCycleResult(state, **common)

    assert action is not None
    if condition is UNKNOWN:
        return ConditionalShiftCycleResult(
            _invalidate_possible_result(state, action),
            boundary_valid=True,
            **common,
        )
    if condition is False:
        return ConditionalShiftCycleResult(
            state,
            boundary_valid=True,
            result_known=True,
            **common,
        )

    shifter = _compute_known_action(state, action)
    if shifter is None:
        return ConditionalShiftCycleResult(
            _invalidate_possible_result(state, action),
            boundary_valid=True,
            **common,
        )
    updated = _apply_shifter_result(state, shifter)
    return ConditionalShiftCycleResult(
        updated,
        boundary_valid=True,
        result_known=True,
        sr_write=shifter.sr_write,
        se_write=shifter.se_write,
        sb_write=shifter.sb_write,
        ss_write=shifter.ss_write,
        **common,
    )
