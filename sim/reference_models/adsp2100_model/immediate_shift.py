"""Independent original ADSP-2100 Type 15 immediate-shift model."""

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
from .shifter import compute_shifter


IMMEDIATE_SHIFT_MASK = 0xFF8000
IMMEDIATE_SHIFT_VALUE = 0x0F0000

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
class ImmediateShiftAction:
    sf: int
    xop: int
    source: DREG
    exponent: ExactWord


def is_immediate_shift_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & IMMEDIATE_SHIFT_MASK == IMMEDIATE_SHIFT_VALUE


def decode_immediate_shift(opcode: int) -> ImmediateShiftAction | None:
    """Decode only source-backed Type 15 LSHIFT/ASHIFT subencodings."""

    if not is_immediate_shift_class(opcode):
        return None
    sf = (opcode >> 11) & 0xF
    xop = (opcode >> 8) & 0x7
    if sf > 0x7 or xop not in SHIFTER_XOP_DREG:
        return None
    return ImmediateShiftAction(
        sf=sf,
        xop=xop,
        source=SHIFTER_XOP_DREG[xop],
        exponent=ExactWord(8, opcode & 0xFF),
    )


@dataclass(frozen=True)
class ImmediateShiftState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    mstat: ExactWord = field(default_factory=lambda: ExactWord(4, 0))

    @classmethod
    def reset(cls) -> "ImmediateShiftState":
        return cls()


@dataclass(frozen=True)
class ImmediateShiftCycleResult:
    state: ImmediateShiftState
    action: ImmediateShiftAction | None = None
    class_valid: bool = False
    unsupported_subencoding: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    result_known: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def _selected_bank(state: ImmediateShiftState) -> ComputationalBank:
    return state.alternate if state.mstat.value & 1 else state.primary


def _known_sr(bank: ComputationalBank) -> ExactWord | None:
    sr0, sr1 = bank.sr
    if not isinstance(sr0, ExactWord) or not isinstance(sr1, ExactWord):
        return None
    return ExactWord(32, (sr1.value << 16) | sr0.value)


def _invalidate_sr(state: ImmediateShiftState) -> ImmediateShiftState:
    selected = replace(_selected_bank(state), sr=(UNKNOWN, UNKNOWN))
    if state.mstat.value & 1:
        return replace(state, alternate=selected)
    return replace(state, primary=selected)


def apply_immediate_shift_cycle(
    state: ImmediateShiftState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
) -> ImmediateShiftCycleResult:
    """Apply one reset, deterministic setup, or Type 15 instruction boundary."""

    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    class_valid = is_immediate_shift_class(opcode)
    action = decode_immediate_shift(opcode)
    unsupported = class_valid and action is None
    setup_count = int(setup_mstat is not None) + int(setup_dreg is not None)
    conflict = bool(
        not reset
        and ((execute and setup_count != 0) or setup_count > 1)
    )
    invalid = bool(not reset and execute and action is None)
    boundary = bool(
        not reset and execute and action is not None and setup_count == 0
    )
    if reset:
        return ImmediateShiftCycleResult(
            replace(state, mstat=ExactWord(4, 0)),
            action,
            class_valid=class_valid,
            unsupported_subencoding=unsupported,
        )
    if conflict or invalid:
        return ImmediateShiftCycleResult(
            state,
            action,
            class_valid=class_valid,
            unsupported_subencoding=unsupported,
            invalid_opcode=invalid,
            integration_conflict=conflict,
        )
    if setup_mstat is not None:
        return ImmediateShiftCycleResult(
            replace(state, mstat=setup_mstat),
            action,
            class_valid=class_valid,
            unsupported_subencoding=unsupported,
        )
    if setup_dreg is not None:
        registers = apply_dreg_cycle(
            state.primary,
            state.alternate,
            alternate_selected=bool(state.mstat.value & 1),
            writes=(setup_dreg,),
        )
        return ImmediateShiftCycleResult(
            ImmediateShiftState(
                registers.primary,
                registers.alternate,
                state.mstat,
            ),
            action,
            class_valid=class_valid,
            unsupported_subencoding=unsupported,
        )
    if not boundary:
        return ImmediateShiftCycleResult(
            state,
            action,
            class_valid=class_valid,
            unsupported_subencoding=unsupported,
        )

    assert action is not None
    selected = _selected_bank(state)
    source = read_dreg(selected, action.source)
    old_sr = _known_sr(selected)
    requires_old_sr = bool(action.sf & 1)
    if not isinstance(source, ExactWord) or (requires_old_sr and old_sr is None):
        return ImmediateShiftCycleResult(
            _invalidate_sr(state),
            action,
            class_valid=True,
            boundary_valid=True,
        )
    shifter = compute_shifter(
        action.sf,
        source.value,
        action.exponent.value,
        0 if old_sr is None else old_sr.value,
        0,
    )
    assert shifter.sr_write
    registers = apply_computational_cycle(
        state.primary,
        state.alternate,
        alternate_selected=bool(state.mstat.value & 1),
        shifter_write=ShifterRegisterWrite(
            sr=ExactWord(32, shifter.sr_result),
        ),
    )
    return ImmediateShiftCycleResult(
        ImmediateShiftState(
            registers.primary,
            registers.alternate,
            state.mstat,
        ),
        action,
        class_valid=True,
        boundary_valid=True,
        result_known=True,
    )
