"""Stateful original ADSP-2100 Type 25 MR-saturation boundary."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .mac import NEGATIVE_SATURATION, POSITIVE_SATURATION
from .model import ComputationalBank, ExactWord, KnownOrUnknown, UNKNOWN
from .mr_saturation import decode_mr_saturation
from .registers import MACRegisterWrite, apply_computational_cycle
from .status import (
    ASTATBit,
    StatusBit,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
)


@dataclass(frozen=True)
class MRSaturationSliceState:
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)


@dataclass(frozen=True)
class MRSaturationSliceInputs:
    reset: bool = False
    execute: bool = False
    opcode: int = 0
    astat_write: ExactWord | None = None
    mstat_write: ExactWord | None = None
    mr_setup_write: ExactWord | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.opcode <= 0xFFFFFF:
            raise ValueError("opcode must fit 24 bits")
        if self.astat_write is not None and self.astat_write.width != 8:
            raise ValueError("ASTAT write must be exactly 8 bits")
        if self.mstat_write is not None and self.mstat_write.width != 4:
            raise ValueError("MSTAT write must be exactly 4 bits")
        if self.mr_setup_write is not None and self.mr_setup_write.width != 40:
            raise ValueError("MR setup write must be exactly 40 bits")

    @property
    def setup_action(self) -> bool:
        return (
            self.astat_write is not None
            or self.mstat_write is not None
            or self.mr_setup_write is not None
        )


@dataclass(frozen=True)
class MRSaturationSliceResult:
    state: MRSaturationSliceState
    boundary_valid: bool
    invalid_opcode: bool
    integration_conflict: bool
    internal_conflict: bool
    condition: StatusBit
    selected_bank_alternate: bool
    mr_before: KnownOrUnknown
    mr_write: StatusBit


def _mr_word(bank: ComputationalBank) -> KnownOrUnknown:
    mr0, mr1, mr2 = bank.mr
    if not all(isinstance(value, ExactWord) for value in (mr0, mr1, mr2)):
        return UNKNOWN
    assert isinstance(mr0, ExactWord)
    assert isinstance(mr1, ExactWord)
    assert isinstance(mr2, ExactWord)
    if (mr0.width, mr1.width, mr2.width) != (16, 16, 8):
        raise ValueError("MR segments have invalid architectural widths")
    return ExactWord(40, (mr2.value << 32) | (mr1.value << 16) | mr0.value)


def _write_unknown_mr(
    primary: ComputationalBank,
    alternate: ComputationalBank,
    *,
    alternate_selected: bool,
) -> tuple[ComputationalBank, ComputationalBank]:
    selected = alternate if alternate_selected else primary
    selected = replace(selected, mr=(UNKNOWN, UNKNOWN, UNKNOWN))
    if alternate_selected:
        return primary, selected
    return selected, alternate


def apply_mr_saturation_slice_cycle(
    state: MRSaturationSliceState,
    inputs: MRSaturationSliceInputs,
) -> MRSaturationSliceResult:
    """Sample MV/bank/MR at cycle start and commit the Type 25 action."""

    valid_opcode = decode_mr_saturation(inputs.opcode)
    alternate_selected = state.status.alternate_bank
    selected = state.alternate if alternate_selected else state.primary
    mr_before = _mr_word(selected)
    condition = state.status.astat.bit(ASTATBit.MV)

    if inputs.reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        )
        return MRSaturationSliceResult(
            MRSaturationSliceState(
                status.state,
                state.primary,
                state.alternate,
            ),
            False,
            False,
            False,
            False,
            condition,
            alternate_selected,
            mr_before,
            False,
        )

    invalid_opcode = inputs.execute and not valid_opcode
    integration_conflict = inputs.execute and inputs.setup_action
    if integration_conflict:
        return MRSaturationSliceResult(
            state,
            False,
            invalid_opcode,
            True,
            False,
            condition,
            alternate_selected,
            mr_before,
            False,
        )

    boundary_valid = inputs.execute and valid_opcode
    status = apply_status_cycle(
        state.status,
        StatusCycleInputs(
            astat_move=inputs.astat_write,
            mstat_move=inputs.mstat_write,
        ),
    )
    primary = state.primary
    alternate = state.alternate
    mr_write: StatusBit = False
    mac_write: MACRegisterWrite | None = None

    if inputs.mr_setup_write is not None:
        mac_write = MACRegisterWrite(False, inputs.mr_setup_write)
    elif boundary_valid:
        if condition is UNKNOWN:
            mr_write = UNKNOWN
            primary, alternate = _write_unknown_mr(
                primary,
                alternate,
                alternate_selected=alternate_selected,
            )
        elif bool(condition):
            mr_write = True
            mr2 = selected.mr[2]
            if mr2 is UNKNOWN:
                primary, alternate = _write_unknown_mr(
                    primary,
                    alternate,
                    alternate_selected=alternate_selected,
                )
            else:
                assert isinstance(mr2, ExactWord)
                saturation = (
                    NEGATIVE_SATURATION
                    if mr2.value & 0x80
                    else POSITIVE_SATURATION
                )
                mac_write = MACRegisterWrite(False, ExactWord(40, saturation))

    if mac_write is not None:
        registers = apply_computational_cycle(
            primary,
            alternate,
            alternate_selected=alternate_selected,
            mac_write=mac_write,
        )
        primary = registers.primary
        alternate = registers.alternate

    next_state = MRSaturationSliceState(
        status.state,
        primary,
        alternate,
    )
    return MRSaturationSliceResult(
        next_state,
        boundary_valid,
        invalid_opcode,
        False,
        status.write_conflict,
        condition,
        alternate_selected,
        mr_before,
        mr_write,
    )
