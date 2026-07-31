"""Independent original ADSP-2100 Type 6 immediate-DREG execution model."""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import ComputationalBank, ExactWord
from .registers import DREG, DREGWrite, apply_dreg_cycle


LOAD_DREG_IMMEDIATE_MASK = 0xF00000
LOAD_DREG_IMMEDIATE_VALUE = 0x400000


@dataclass(frozen=True)
class LoadDregImmediateAction:
    destination: DREG
    data: ExactWord


def decode_load_dreg_immediate(opcode: int) -> LoadDregImmediateAction | None:
    """Decode Type 6 DATA[19:4] and DREG[3:0], failing closed otherwise."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if opcode & LOAD_DREG_IMMEDIATE_MASK != LOAD_DREG_IMMEDIATE_VALUE:
        return None
    return LoadDregImmediateAction(
        destination=DREG(opcode & 0xF),
        data=ExactWord(16, (opcode >> 4) & 0xFFFF),
    )


@dataclass(frozen=True)
class LoadDregImmediateState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    mstat: ExactWord = field(default_factory=lambda: ExactWord(4, 0))

    @classmethod
    def reset(cls) -> "LoadDregImmediateState":
        return cls()


@dataclass(frozen=True)
class LoadDregImmediateCycleResult:
    state: LoadDregImmediateState
    action: LoadDregImmediateAction | None = None
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def apply_load_dreg_immediate_cycle(
    state: LoadDregImmediateState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
) -> LoadDregImmediateCycleResult:
    """Apply one reset, deterministic setup, or Type 6 instruction boundary."""

    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    action = decode_load_dreg_immediate(opcode)
    setup_count = int(setup_mstat is not None) + int(setup_dreg is not None)
    integration_conflict = bool(
        not reset
        and ((execute and setup_count != 0) or setup_count > 1)
    )
    invalid_opcode = bool(not reset and execute and action is None)
    boundary_valid = bool(
        not reset
        and execute
        and action is not None
        and setup_count == 0
    )
    if reset:
        return LoadDregImmediateCycleResult(
            LoadDregImmediateState.reset(), action
        )
    if integration_conflict or invalid_opcode:
        return LoadDregImmediateCycleResult(
            state,
            action,
            invalid_opcode=invalid_opcode,
            integration_conflict=integration_conflict,
        )
    if setup_mstat is not None:
        return LoadDregImmediateCycleResult(
            LoadDregImmediateState(
                state.primary,
                state.alternate,
                setup_mstat,
            ),
            action,
        )
    write = setup_dreg
    if boundary_valid:
        assert action is not None
        write = DREGWrite(action.destination, action.data)
    if write is None:
        return LoadDregImmediateCycleResult(state, action)
    registers = apply_dreg_cycle(
        state.primary,
        state.alternate,
        alternate_selected=bool(state.mstat.value & 1),
        writes=(write,),
    )
    return LoadDregImmediateCycleResult(
        LoadDregImmediateState(
            registers.primary,
            registers.alternate,
            state.mstat,
        ),
        action,
        boundary_valid=boundary_valid,
    )
