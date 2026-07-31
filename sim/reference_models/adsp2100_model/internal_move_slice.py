"""Independent state model for original ADSP-2100 Type 17 internal MOVE.

The original manual closes register widths, direction, and all extensions
except the unused upper DMD bits of the five narrow status registers.  This
bounded model uses the OQ-016 provisional hypothesis that those bits are zero.
The hypothesis is deliberately reported on every affected read and is not
promoted to primary-verified behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .internal_move import (
    InternalMoveSelection,
    decode_internal_move,
    register_code_by_name,
)
from .model import ComputationalBank, ExactWord, KnownOrUnknown, UNKNOWN
from .modify_address import DAGRegisterState
from .registers import DREG, DREGWrite, apply_dreg_cycle, read_dreg
from .sequencer_stacks import (
    SequencerStacksInputs,
    SequencerStacksState,
    apply_sequencer_stacks_cycle,
)
from .status_stack import StatusStackState


_READABLE_CODES = {
    code: name
    for name, code in register_code_by_name(writable=False).items()
}
_WRITABLE_CODES = {
    code: name
    for name, code in register_code_by_name(writable=True).items()
}


def _optional_width(value: int | None, width: int, name: str) -> None:
    if value is not None and not 0 <= value < (1 << width):
        raise ValueError(f"{name} must fit {width} bits")


@dataclass(frozen=True)
class InternalMoveSetup:
    """Deterministic verification write using normal destination semantics."""

    code: int
    value: int

    def __post_init__(self) -> None:
        if self.code not in _WRITABLE_CODES:
            raise ValueError("setup code must select a writable original register")
        if not 0 <= self.value <= 0xFFFF:
            raise ValueError("setup value must fit 16 bits")


@dataclass(frozen=True)
class InternalMoveSliceState:
    """Type-17-visible state, including the CNTR count-stack side effect."""

    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    dag: DAGRegisterState = field(default_factory=DAGRegisterState)
    astat: int | None = None
    mstat: int | None = 0
    imask: int | None = 0
    icntl: int | None = None
    cntr: int | None = None
    px: int | None = None
    stacks: SequencerStacksState = field(default_factory=SequencerStacksState)
    status_stack: StatusStackState = field(default_factory=StatusStackState)

    def __post_init__(self) -> None:
        _optional_width(self.astat, 8, "ASTAT")
        _optional_width(self.mstat, 4, "MSTAT")
        _optional_width(self.imask, 4, "IMASK")
        _optional_width(self.icntl, 5, "ICNTL")
        _optional_width(self.cntr, 14, "CNTR")
        _optional_width(self.px, 8, "PX")

    @classmethod
    def reset(cls) -> "InternalMoveSliceState":
        return cls()

    @property
    def sstat(self) -> int:
        return self.stacks.sstat_fragment | self.status_stack.sstat_fragment


@dataclass(frozen=True)
class InternalMoveCycleResult:
    state: InternalMoveSliceState
    selection: InternalMoveSelection | None = None
    boundary_valid: bool = False
    invalid_opcode: bool = False
    invalid_subencoding: bool = False
    integration_conflict: bool = False
    bank_selection_unknown: bool = False
    source_data: int = 0
    source_valid: bool = False
    source_extension_provisional: bool = False
    count_stack_push: bool = False
    count_stack_push_value: int = 0
    pm_data_access: bool = False
    dm_access: bool = False


def _selected_bank(
    state: InternalMoveSliceState,
) -> ComputationalBank | None:
    if state.mstat is None:
        return None
    return state.alternate if state.mstat & 1 else state.primary


def _known_word(value: int | None) -> KnownOrUnknown:
    return UNKNOWN if value is None else ExactWord(16, value)


def _sign_extend(value: int | None, width: int) -> KnownOrUnknown:
    if value is None:
        return UNKNOWN
    sign = 1 << (width - 1)
    signed = value - (1 << width) if value & sign else value
    return ExactWord(16, signed & 0xFFFF)


def _dag_value(state: InternalMoveSliceState, code: int) -> int | None:
    group = code >> 4
    index = code & 0xF
    address = ((group - 1) << 2) | (index & 0x3)
    if index < 4:
        return state.dag.i[address]
    if index < 8:
        return state.dag.m[address]
    return state.dag.l[address]


def read_internal_move_register(
    state: InternalMoveSliceState,
    code: int,
) -> tuple[KnownOrUnknown, bool]:
    """Return a 16-bit DMD value and whether OQ-016 zero fill was used."""

    if code not in _READABLE_CODES:
        raise ValueError("code is not an original readable register")
    group = code >> 4
    index = code & 0xF
    if group == 0:
        bank = _selected_bank(state)
        return (UNKNOWN if bank is None else read_dreg(bank, index), False)
    if group in (1, 2):
        value = _dag_value(state, code)
        if index < 4 or index >= 8:
            return (_known_word(value), False)
        return (_sign_extend(value, 14), False)

    if index == 0:
        return (_known_word(state.astat), True)
    if index == 1:
        return (_known_word(state.mstat), True)
    if index == 2:
        return (ExactWord(16, state.sstat), True)
    if index == 3:
        return (_known_word(state.imask), True)
    if index == 4:
        return (_known_word(state.icntl), True)
    if index == 5:
        return (_known_word(state.cntr), False)
    if index == 6:
        bank = _selected_bank(state)
        if bank is None or bank.sb is UNKNOWN:
            return (UNKNOWN, False)
        assert isinstance(bank.sb, ExactWord)
        return (_sign_extend(bank.sb.value, 5), False)
    if index == 7:
        return (_known_word(state.px), False)
    raise AssertionError("validated group-three register was not handled")


def _replace_tuple(
    values: tuple[int | None, ...],
    index: int,
    value: int | None,
) -> tuple[int | None, ...]:
    updated = list(values)
    updated[index] = value
    return tuple(updated)


def _unknown_dreg(bank: ComputationalBank, code: DREG) -> ComputationalBank:
    """Apply an unknown 16-bit bus write without inventing stored bits."""

    if code in (DREG.AX0, DREG.AX1):
        values = list(bank.ax)
        values[int(code)] = UNKNOWN
        return replace(bank, ax=(values[0], values[1]))
    if code in (DREG.MX0, DREG.MX1):
        values = list(bank.mx)
        values[int(code) - 2] = UNKNOWN
        return replace(bank, mx=(values[0], values[1]))
    if code in (DREG.AY0, DREG.AY1):
        values = list(bank.ay)
        values[int(code) - 4] = UNKNOWN
        return replace(bank, ay=(values[0], values[1]))
    if code in (DREG.MY0, DREG.MY1):
        values = list(bank.my)
        values[int(code) - 6] = UNKNOWN
        return replace(bank, my=(values[0], values[1]))
    if code == DREG.SI:
        return replace(bank, si=UNKNOWN)
    if code == DREG.SE:
        return replace(bank, se=UNKNOWN)
    if code == DREG.AR:
        return replace(bank, ar=UNKNOWN)
    if code == DREG.MR0:
        return replace(bank, mr=(UNKNOWN, bank.mr[1], bank.mr[2]))
    if code == DREG.MR1:
        return replace(bank, mr=(bank.mr[0], UNKNOWN, UNKNOWN))
    if code == DREG.MR2:
        return replace(bank, mr=(bank.mr[0], bank.mr[1], UNKNOWN))
    if code == DREG.SR0:
        return replace(bank, sr=(UNKNOWN, bank.sr[1]))
    if code == DREG.SR1:
        return replace(bank, sr=(bank.sr[0], UNKNOWN))
    raise AssertionError("exhaustive DREG handling")


def _write_banked(
    state: InternalMoveSliceState,
    code: int,
    value: KnownOrUnknown,
) -> InternalMoveSliceState | None:
    if state.mstat is None:
        return None
    alternate_selected = bool(state.mstat & 1)
    if code == 0x36:
        bank = state.alternate if alternate_selected else state.primary
        stored = (
            UNKNOWN
            if value is UNKNOWN
            else ExactWord(5, value.value & 0x1F)
        )
        bank = replace(bank, sb=stored)
        return replace(
            state,
            alternate=bank if alternate_selected else state.alternate,
            primary=state.primary if alternate_selected else bank,
        )

    dreg = DREG(code & 0xF)
    if value is UNKNOWN:
        bank = state.alternate if alternate_selected else state.primary
        bank = _unknown_dreg(bank, dreg)
        return replace(
            state,
            alternate=bank if alternate_selected else state.alternate,
            primary=state.primary if alternate_selected else bank,
        )
    result = apply_dreg_cycle(
        state.primary,
        state.alternate,
        alternate_selected=alternate_selected,
        writes=(DREGWrite(dreg, value),),
    )
    return replace(state, primary=result.primary, alternate=result.alternate)


def _write_register(
    state: InternalMoveSliceState,
    code: int,
    value: KnownOrUnknown,
) -> tuple[InternalMoveSliceState | None, bool, int]:
    group = code >> 4
    index = code & 0xF
    if group == 0 or code == 0x36:
        return (_write_banked(state, code, value), False, 0)
    raw = None if value is UNKNOWN else value.value
    if group in (1, 2):
        address = ((group - 1) << 2) | (index & 0x3)
        stored = None if raw is None else raw & 0x3FFF
        if index < 4:
            dag = replace(state.dag, i=_replace_tuple(state.dag.i, address, stored))
        elif index < 8:
            dag = replace(state.dag, m=_replace_tuple(state.dag.m, address, stored))
        else:
            dag = replace(state.dag, l=_replace_tuple(state.dag.l, address, stored))
        return (replace(state, dag=dag), False, 0)

    if index == 0:
        return (replace(state, astat=None if raw is None else raw & 0xFF), False, 0)
    if index == 1:
        return (replace(state, mstat=None if raw is None else raw & 0xF), False, 0)
    if index == 3:
        return (replace(state, imask=None if raw is None else raw & 0xF), False, 0)
    if index == 4:
        return (replace(state, icntl=None if raw is None else raw & 0x1F), False, 0)
    if index == 5:
        pushed = state.cntr is not None
        push_value = state.cntr if pushed else 0
        stacks = state.stacks
        if pushed:
            stacks = apply_sequencer_stacks_cycle(
                stacks,
                SequencerStacksInputs(
                    count_push=True,
                    count_push_value=push_value,
                ),
            ).state
        return (
            replace(state, cntr=None if raw is None else raw & 0x3FFF, stacks=stacks),
            pushed,
            push_value,
        )
    if index == 7:
        return (replace(state, px=None if raw is None else raw & 0xFF), False, 0)
    raise AssertionError("validated writable group-three register not handled")


def apply_internal_move_cycle(
    state: InternalMoveSliceState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup: InternalMoveSetup | None = None,
) -> InternalMoveCycleResult:
    """Apply one Type 17 or deterministic setup instruction boundary."""

    selection = decode_internal_move(opcode)
    invalid_opcode = bool(not reset and execute and selection is None)
    invalid_subencoding = bool(
        not reset
        and execute
        and selection is not None
        and not selection.legal
    )
    integration_conflict = bool(not reset and execute and setup is not None)
    boundary_valid = bool(
        not reset
        and execute
        and selection is not None
        and selection.legal
        and setup is None
    )
    if reset:
        return InternalMoveCycleResult(InternalMoveSliceState.reset(), selection)
    if integration_conflict or invalid_opcode or invalid_subencoding:
        return InternalMoveCycleResult(
            state,
            selection,
            invalid_opcode=invalid_opcode,
            invalid_subencoding=invalid_subencoding,
            integration_conflict=integration_conflict,
        )

    if setup is not None:
        next_state, pushed, push_value = _write_register(
            state,
            setup.code,
            ExactWord(16, setup.value),
        )
        return InternalMoveCycleResult(
            state if next_state is None else next_state,
            selection,
            bank_selection_unknown=next_state is None,
            count_stack_push=pushed,
            count_stack_push_value=push_value,
        )

    if not boundary_valid:
        return InternalMoveCycleResult(state, selection)

    assert selection is not None
    source, provisional = read_internal_move_register(
        state,
        selection.source_code,
    )
    next_state, pushed, push_value = _write_register(
        state,
        selection.destination_code,
        source,
    )
    return InternalMoveCycleResult(
        state if next_state is None else next_state,
        selection,
        boundary_valid=True,
        bank_selection_unknown=next_state is None,
        source_data=0 if source is UNKNOWN else source.value,
        source_valid=source is not UNKNOWN,
        source_extension_provisional=provisional,
        count_stack_push=pushed,
        count_stack_push_value=push_value,
    )
