"""Original ADSP-2100 computational DREG access and bank semantics.

This module covers the sixteen general computational data registers encoded by
the Appendix A DREG field. AF, MF, and SB are banked architectural registers
but are intentionally outside this field and this verified slice.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Iterable

from .model import ComputationalBank, ExactWord, KnownOrUnknown, UNKNOWN


class DREG(IntEnum):
    AX0 = 0
    AX1 = 1
    MX0 = 2
    MX1 = 3
    AY0 = 4
    AY1 = 5
    MY0 = 6
    MY1 = 7
    SI = 8
    SE = 9
    AR = 10
    MR0 = 11
    MR1 = 12
    MR2 = 13
    SR0 = 14
    SR1 = 15


class DREGWriteConflict(ValueError):
    """Two same-cycle writes affect the same architectural storage."""


@dataclass(frozen=True)
class DREGWrite:
    address: DREG
    data: ExactWord

    def __post_init__(self) -> None:
        object.__setattr__(self, "address", DREG(self.address))
        if self.data.width != 16:
            raise ValueError("DREG write data must be exactly 16 bits")


@dataclass(frozen=True)
class DREGCycleResult:
    """Cycle-start reads plus cycle-end bank state."""

    reads: tuple[KnownOrUnknown, ...]
    primary: ComputationalBank
    alternate: ComputationalBank


def _replace_pair(
    pair: tuple[KnownOrUnknown, KnownOrUnknown],
    index: int,
    value: KnownOrUnknown,
) -> tuple[KnownOrUnknown, KnownOrUnknown]:
    updated = list(pair)
    updated[index] = value
    return (updated[0], updated[1])


def _sign_extended_word(value: KnownOrUnknown) -> KnownOrUnknown:
    if value is UNKNOWN:
        return UNKNOWN
    if not isinstance(value, ExactWord) or value.width != 8:
        raise ValueError("narrow signed register must be an exact 8-bit word")
    return ExactWord(16, value.signed & 0xFFFF)


def read_dreg(bank: ComputationalBank, address: DREG | int) -> KnownOrUnknown:
    """Read one DREG as the original 16-bit data/result buses observe it."""

    code = DREG(address)
    if code in (DREG.AX0, DREG.AX1):
        return bank.ax[int(code) - int(DREG.AX0)]
    if code in (DREG.MX0, DREG.MX1):
        return bank.mx[int(code) - int(DREG.MX0)]
    if code in (DREG.AY0, DREG.AY1):
        return bank.ay[int(code) - int(DREG.AY0)]
    if code in (DREG.MY0, DREG.MY1):
        return bank.my[int(code) - int(DREG.MY0)]
    if code == DREG.SI:
        return bank.si
    if code == DREG.SE:
        return _sign_extended_word(bank.se)
    if code == DREG.AR:
        return bank.ar
    if code in (DREG.MR0, DREG.MR1):
        return bank.mr[int(code) - int(DREG.MR0)]
    if code == DREG.MR2:
        return _sign_extended_word(bank.mr[2])
    if code in (DREG.SR0, DREG.SR1):
        return bank.sr[int(code) - int(DREG.SR0)]
    raise AssertionError("exhaustive DREG enum handling")


def _write_dreg(
    bank: ComputationalBank,
    write: DREGWrite,
) -> ComputationalBank:
    code = write.address
    data = write.data
    if code in (DREG.AX0, DREG.AX1):
        return replace(
            bank,
            ax=_replace_pair(bank.ax, int(code) - int(DREG.AX0), data),
        )
    if code in (DREG.MX0, DREG.MX1):
        return replace(
            bank,
            mx=_replace_pair(bank.mx, int(code) - int(DREG.MX0), data),
        )
    if code in (DREG.AY0, DREG.AY1):
        return replace(
            bank,
            ay=_replace_pair(bank.ay, int(code) - int(DREG.AY0), data),
        )
    if code in (DREG.MY0, DREG.MY1):
        return replace(
            bank,
            my=_replace_pair(bank.my, int(code) - int(DREG.MY0), data),
        )
    if code == DREG.SI:
        return replace(bank, si=data)
    if code == DREG.SE:
        return replace(bank, se=ExactWord(8, data.value & 0xFF))
    if code == DREG.AR:
        return replace(bank, ar=data)
    if code == DREG.MR0:
        return replace(bank, mr=(data, bank.mr[1], bank.mr[2]))
    if code == DREG.MR1:
        mr2 = ExactWord(8, 0xFF if data.value & 0x8000 else 0x00)
        return replace(bank, mr=(bank.mr[0], data, mr2))
    if code == DREG.MR2:
        return replace(
            bank,
            mr=(bank.mr[0], bank.mr[1], ExactWord(8, data.value & 0xFF)),
        )
    if code == DREG.SR0:
        return replace(bank, sr=(data, bank.sr[1]))
    if code == DREG.SR1:
        return replace(bank, sr=(bank.sr[0], data))
    raise AssertionError("exhaustive DREG enum handling")


def _effective_destinations(address: DREG) -> frozenset[DREG]:
    if address == DREG.MR1:
        return frozenset((DREG.MR1, DREG.MR2))
    return frozenset((address,))


def validate_dreg_writes(writes: Iterable[DREGWrite]) -> tuple[DREGWrite, ...]:
    """Reject same-cycle collisions rather than assigning undocumented priority."""

    materialized = tuple(writes)
    occupied: set[DREG] = set()
    for write in materialized:
        destinations = _effective_destinations(write.address)
        conflict = occupied.intersection(destinations)
        if conflict:
            names = ", ".join(sorted(destination.name for destination in conflict))
            raise DREGWriteConflict(f"same-cycle DREG write collision: {names}")
        occupied.update(destinations)
    return materialized


def apply_dreg_cycle(
    primary: ComputationalBank,
    alternate: ComputationalBank,
    *,
    alternate_selected: bool,
    read_addresses: Iterable[DREG | int] = (),
    writes: Iterable[DREGWrite] = (),
) -> DREGCycleResult:
    """Read the selected bank before atomically applying selected-bank writes."""

    selected = alternate if alternate_selected else primary
    reads = tuple(read_dreg(selected, address) for address in read_addresses)
    validated_writes = validate_dreg_writes(writes)
    updated = selected
    for write in validated_writes:
        updated = _write_dreg(updated, write)
    if alternate_selected:
        alternate = updated
    else:
        primary = updated
    return DREGCycleResult(
        reads=reads,
        primary=primary,
        alternate=alternate,
    )
