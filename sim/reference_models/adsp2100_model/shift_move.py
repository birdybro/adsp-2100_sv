"""Independent bounded original ADSP-2100 Type 14 execution model."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

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


SHIFT_MOVE_CLASS_MASK = 0xFF0000
SHIFT_MOVE_CLASS_VALUE = 0x100000
SHIFT_MOVE_CANONICAL_MASK = 0xFF8000
SHIFT_MOVE_CANONICAL_VALUE = 0x100000

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
class ShiftMoveAction:
    sf: int
    xop: int
    shifter_source: DREG
    move_destination: DREG
    move_source: DREG


def is_shift_move_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & SHIFT_MOVE_CLASS_MASK == SHIFT_MOVE_CLASS_VALUE


def shift_move_unsupported_reason(opcode: int) -> str | None:
    """Classify source-unclosed or unsupported Type 14 subencodings."""

    if not is_shift_move_class(opcode):
        return None
    if opcode & 0x008000:
        return "UNVERIFIED_UNUSED_X"
    xop = (opcode >> 8) & 0x7
    if xop not in SHIFTER_XOP_DREG:
        return "UNAVAILABLE_SHIFTER_XOP"
    sf = (opcode >> 11) & 0xF
    destination = DREG((opcode >> 4) & 0xF)
    if sf <= 0xB and destination in (DREG.SR0, DREG.SR1):
        return "UNSUPPORTED_DESTINATION_COLLISION"
    if sf in (0xC, 0xD, 0xE) and destination == DREG.SE:
        return "UNSUPPORTED_DESTINATION_COLLISION"
    return None


def decode_shift_move(opcode: int) -> ShiftMoveAction | None:
    """Decode the canonical, source-backed Type 14 action subset."""

    if not is_shift_move_class(opcode):
        return None
    if shift_move_unsupported_reason(opcode) is not None:
        return None
    xop = (opcode >> 8) & 0x7
    return ShiftMoveAction(
        sf=(opcode >> 11) & 0xF,
        xop=xop,
        shifter_source=SHIFTER_XOP_DREG[xop],
        move_destination=DREG((opcode >> 4) & 0xF),
        move_source=DREG(opcode & 0xF),
    )


@dataclass(frozen=True)
class ShiftMoveState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)

    @classmethod
    def reset(cls) -> "ShiftMoveState":
        return cls()


@dataclass(frozen=True)
class ShiftMoveCycleResult:
    state: ShiftMoveState
    action: ShiftMoveAction | None = None
    unsupported_reason: str | None = None
    class_valid: bool = False
    action_valid: bool = False
    unsupported_subencoding: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    move_result_known: bool = False
    shifter_result_known: bool = False
    move_write: bool = False
    sr_write: bool = False
    se_write: bool = False
    sb_write: bool = False
    ss_write: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def _selected_bank(state: ShiftMoveState) -> ComputationalBank:
    return state.alternate if state.status.alternate_bank else state.primary


def _replace_selected_bank(
    state: ShiftMoveState,
    bank: ComputationalBank,
) -> ShiftMoveState:
    if state.status.alternate_bank:
        return replace(state, alternate=bank)
    return replace(state, primary=bank)


def _known_sr(bank: ComputationalBank) -> ExactWord | None:
    sr0, sr1 = bank.sr
    if not isinstance(sr0, ExactWord) or not isinstance(sr1, ExactWord):
        return None
    return ExactWord(32, (sr1.value << 16) | sr0.value)


def _replace_pair(
    pair: tuple[object, object],
    index: int,
    value: object,
) -> tuple[object, object]:
    updated = list(pair)
    updated[index] = value
    return (updated[0], updated[1])


def _invalidate_dreg(bank: ComputationalBank, destination: DREG) -> ComputationalBank:
    if destination in (DREG.AX0, DREG.AX1):
        return replace(
            bank,
            ax=_replace_pair(bank.ax, int(destination) - int(DREG.AX0), UNKNOWN),
        )
    if destination in (DREG.MX0, DREG.MX1):
        return replace(
            bank,
            mx=_replace_pair(bank.mx, int(destination) - int(DREG.MX0), UNKNOWN),
        )
    if destination in (DREG.AY0, DREG.AY1):
        return replace(
            bank,
            ay=_replace_pair(bank.ay, int(destination) - int(DREG.AY0), UNKNOWN),
        )
    if destination in (DREG.MY0, DREG.MY1):
        return replace(
            bank,
            my=_replace_pair(bank.my, int(destination) - int(DREG.MY0), UNKNOWN),
        )
    if destination == DREG.SI:
        return replace(bank, si=UNKNOWN)
    if destination == DREG.SE:
        return replace(bank, se=UNKNOWN)
    if destination == DREG.AR:
        return replace(bank, ar=UNKNOWN)
    if destination == DREG.MR0:
        return replace(bank, mr=(UNKNOWN, bank.mr[1], bank.mr[2]))
    if destination == DREG.MR1:
        return replace(bank, mr=(bank.mr[0], UNKNOWN, UNKNOWN))
    if destination == DREG.MR2:
        return replace(bank, mr=(bank.mr[0], bank.mr[1], UNKNOWN))
    if destination in (DREG.SR0, DREG.SR1):
        return replace(
            bank,
            sr=_replace_pair(bank.sr, int(destination) - int(DREG.SR0), UNKNOWN),
        )
    raise AssertionError("exhaustive DREG destination")


def _invalidate_ss(status: StatusRegisters) -> StatusRegisters:
    bits = list(status.astat.bits)
    bits[int(ASTATBit.SS)] = UNKNOWN
    return replace(status, astat=ASTATState(tuple(bits)))


def _invalidate_shifter_result(state: ShiftMoveState, sf: int) -> ShiftMoveState:
    bank = _selected_bank(state)
    status = state.status
    if sf <= 0xB:
        bank = replace(bank, sr=(UNKNOWN, UNKNOWN))
    elif sf in (0xC, 0xD):
        bank = replace(bank, se=UNKNOWN)
        status = _invalidate_ss(status)
    elif sf == 0xE:
        if not isinstance(bank.se, ExactWord) or bank.se.value == 0xF1:
            bank = replace(bank, se=UNKNOWN)
    else:
        bank = replace(bank, sb=UNKNOWN)
    return replace(_replace_selected_bank(state, bank), status=status)


def _compute_known_shifter(
    state: ShiftMoveState,
    action: ShiftMoveAction,
) -> ShifterResult | None:
    bank = _selected_bank(state)
    source = read_dreg(bank, action.shifter_source)
    if not isinstance(source, ExactWord):
        return None
    se = bank.se
    sb = bank.sb
    sr = _known_sr(bank)
    av = state.status.astat.bit(ASTATBit.AV)
    ac = state.status.astat.bit(ASTATBit.AC)
    ss = state.status.astat.bit(ASTATBit.SS)

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
        if se.value == 0xF1 and ss is UNKNOWN:
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


def _shifter_write(result: ShifterResult) -> ShifterRegisterWrite | None:
    if result.sr_write:
        return ShifterRegisterWrite(sr=ExactWord(32, result.sr_result))
    if result.se_write:
        return ShifterRegisterWrite(se=ExactWord(8, result.se_result))
    if result.sb_write:
        return ShifterRegisterWrite(sb=ExactWord(5, result.sb_result))
    return None


def _apply_actions(
    state: ShiftMoveState,
    action: ShiftMoveAction,
    move_data: ExactWord | None,
    shifter: ShifterResult | None,
) -> ShiftMoveState:
    dreg_writes = (
        ()
        if move_data is None
        else (DREGWrite(action.move_destination, move_data),)
    )
    writeback = None if shifter is None else _shifter_write(shifter)
    registers = apply_computational_cycle(
        state.primary,
        state.alternate,
        alternate_selected=state.status.alternate_bank,
        dreg_writes=dreg_writes,
        shifter_write=writeback,
    )
    status = state.status
    if shifter is not None:
        status = apply_status_cycle(
            status,
            StatusCycleInputs(
                shifter_ss=shifter.ss_result if shifter.ss_write else None,
            ),
        ).state
    updated = ShiftMoveState(registers.primary, registers.alternate, status)
    if move_data is None:
        selected = _invalidate_dreg(
            _selected_bank(updated),
            action.move_destination,
        )
        updated = _replace_selected_bank(updated, selected)
    if shifter is None:
        updated = _invalidate_shifter_result(updated, action.sf)
    return updated


def apply_shift_move_cycle(
    state: ShiftMoveState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_sb: ExactWord | None = None,
) -> ShiftMoveCycleResult:
    """Apply one reset, deterministic setup, or Type 14 instruction boundary."""

    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly eight bits")
    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    if setup_sb is not None and setup_sb.width != 5:
        raise ValueError("SB setup must be exactly five bits")

    class_valid = is_shift_move_class(opcode)
    unsupported_reason = shift_move_unsupported_reason(opcode)
    action = decode_shift_move(opcode)
    setups = (setup_astat, setup_mstat, setup_dreg, setup_sb)
    setup_count = sum(value is not None for value in setups)
    conflict = bool(
        not reset and ((execute and setup_count != 0) or setup_count > 1)
    )
    invalid = bool(not reset and execute and action is None)
    boundary = bool(
        not reset and execute and action is not None and setup_count == 0
    )
    common = {
        "action": action,
        "unsupported_reason": unsupported_reason,
        "class_valid": class_valid,
        "action_valid": action is not None,
        "unsupported_subencoding": class_valid and action is None,
    }

    if reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        return ShiftMoveCycleResult(replace(state, status=status), **common)
    if conflict or invalid:
        return ShiftMoveCycleResult(
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
        return ShiftMoveCycleResult(replace(state, status=status), **common)
    if setup_dreg is not None:
        registers = apply_dreg_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            writes=(setup_dreg,),
        )
        return ShiftMoveCycleResult(
            ShiftMoveState(registers.primary, registers.alternate, state.status),
            **common,
        )
    if setup_sb is not None:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            shifter_write=ShifterRegisterWrite(sb=setup_sb),
        )
        return ShiftMoveCycleResult(
            ShiftMoveState(registers.primary, registers.alternate, state.status),
            **common,
        )
    if not boundary:
        return ShiftMoveCycleResult(state, **common)

    assert action is not None
    bank = _selected_bank(state)
    move_source = read_dreg(bank, action.move_source)
    move_data = move_source if isinstance(move_source, ExactWord) else None
    shifter = _compute_known_shifter(state, action)
    updated = _apply_actions(state, action, move_data, shifter)
    return ShiftMoveCycleResult(
        updated,
        boundary_valid=True,
        move_result_known=move_data is not None,
        shifter_result_known=shifter is not None,
        move_write=True,
        sr_write=False if shifter is None else shifter.sr_write,
        se_write=False if shifter is None else shifter.se_write,
        sb_write=False if shifter is None else shifter.sb_write,
        ss_write=False if shifter is None else shifter.ss_write,
        **common,
    )
