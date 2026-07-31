"""Independent original ADSP-2100 Type 18 mode-control semantics."""

from __future__ import annotations

from dataclasses import dataclass

from .model import ExactWord
from .status import ModeControl


MODE_CONTROL_MASK = 0xFFF00F
MODE_CONTROL_VALUE = 0x0C0000


@dataclass(frozen=True)
class ModeControlActions:
    """Raw MCC fields retained in MSTAT bit order, low bit first."""

    sr: ModeControl
    br: ModeControl
    ol: ModeControl
    ar: ModeControl

    @property
    def controls(self) -> tuple[ModeControl, ...]:
        return (self.sr, self.br, self.ol, self.ar)

    @property
    def has_effect(self) -> bool:
        return any(
            control in (ModeControl.DEACTIVATE, ModeControl.ACTIVATE)
            for control in self.controls
        )

    @property
    def has_no_change_one_alias(self) -> bool:
        return ModeControl.NO_CHANGE_ONE in self.controls


def decode_mode_control(opcode: int) -> ModeControlActions | None:
    """Return all four Type 18 fields or ``None`` for any other word."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if opcode & MODE_CONTROL_MASK != MODE_CONTROL_VALUE:
        return None
    return ModeControlActions(
        sr=ModeControl((opcode >> 4) & 0x3),
        br=ModeControl((opcode >> 6) & 0x3),
        ol=ModeControl((opcode >> 8) & 0x3),
        ar=ModeControl((opcode >> 10) & 0x3),
    )


def apply_mode_control(
    mstat: ExactWord,
    actions: ModeControlActions,
) -> ExactWord:
    """Apply all fields atomically to a cycle-start four-bit MSTAT value."""

    if mstat.width != 4:
        raise ValueError("MSTAT must be exactly four bits")
    value = mstat.value
    for bit, control in enumerate(actions.controls):
        if control is ModeControl.DEACTIVATE:
            value &= ~(1 << bit)
        elif control is ModeControl.ACTIVATE:
            value |= 1 << bit
    return ExactWord(4, value)


@dataclass(frozen=True)
class ModeControlSliceResult:
    mstat: ExactWord
    boundary_valid: bool
    invalid_opcode: bool
    integration_conflict: bool


def apply_mode_control_slice_cycle(
    mstat: ExactWord,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup_mstat: ExactWord | None = None,
) -> ModeControlSliceResult:
    """Apply one bounded setup or Type 18 execution cycle."""

    if mstat.width != 4:
        raise ValueError("MSTAT must be exactly four bits")
    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup value must be exactly four bits")
    actions = decode_mode_control(opcode)
    invalid_opcode = bool(not reset and execute and actions is None)
    integration_conflict = bool(not reset and execute and setup_mstat is not None)
    boundary_valid = bool(
        not reset
        and execute
        and actions is not None
        and setup_mstat is None
    )
    if reset:
        next_mstat = ExactWord(4, 0)
    elif integration_conflict:
        next_mstat = mstat
    elif setup_mstat is not None:
        next_mstat = setup_mstat
    elif boundary_valid:
        assert actions is not None
        next_mstat = apply_mode_control(mstat, actions)
    else:
        next_mstat = mstat
    return ModeControlSliceResult(
        mstat=next_mstat,
        boundary_valid=boundary_valid,
        invalid_opcode=invalid_opcode,
        integration_conflict=integration_conflict,
    )
