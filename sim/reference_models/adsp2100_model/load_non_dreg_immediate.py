"""Independent original ADSP-2100 Type 7 immediate-register model."""

from __future__ import annotations

from dataclasses import dataclass, field

from .internal_move import register_code_by_name
from .internal_move_slice import (
    InternalMoveSetup,
    InternalMoveSliceState,
    apply_internal_move_cycle,
    write_internal_move_register,
)
from .model import ExactWord


LOAD_NON_DREG_IMMEDIATE_MASK = 0xF00000
LOAD_NON_DREG_IMMEDIATE_VALUE = 0x300000


@dataclass(frozen=True)
class LoadNonDregImmediateAction:
    register_group: int
    register_index: int
    register_code: int
    register: str | None
    data: ExactWord
    legal: bool
    invalid_reason: str | None


def decode_load_non_dreg_immediate(
    opcode: int,
) -> LoadNonDregImmediateAction | None:
    """Decode Type 7 and reject DREG, blank, and read-only destinations."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if opcode & LOAD_NON_DREG_IMMEDIATE_MASK != LOAD_NON_DREG_IMMEDIATE_VALUE:
        return None
    group = (opcode >> 18) & 0x3
    index = opcode & 0xF
    code = (group << 4) | index
    all_registers = register_code_by_name(writable=False)
    by_code = {value: name for name, value in all_registers.items()}
    register = by_code.get(code)
    invalid_reason: str | None = None
    if group == 0:
        invalid_reason = "DATA_REGISTER_DESTINATION"
    elif register is None:
        invalid_reason = "RESERVED_DESTINATION_SELECTOR"
    elif register == "SSTAT":
        invalid_reason = "READ_ONLY_SSTAT_DESTINATION"
    return LoadNonDregImmediateAction(
        register_group=group,
        register_index=index,
        register_code=code,
        register=register,
        data=ExactWord(14, (opcode >> 4) & 0x3FFF),
        legal=invalid_reason is None,
        invalid_reason=invalid_reason,
    )


@dataclass(frozen=True)
class LoadNonDregImmediateState:
    registers: InternalMoveSliceState = field(
        default_factory=InternalMoveSliceState.reset
    )

    @classmethod
    def reset(cls) -> "LoadNonDregImmediateState":
        return cls()


@dataclass(frozen=True)
class LoadNonDregImmediateCycleResult:
    state: LoadNonDregImmediateState
    action: LoadNonDregImmediateAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    invalid_subencoding: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    invalid_setup: bool = False
    integration_conflict: bool = False
    bank_selection_unknown: bool = False
    count_stack_push: bool = False
    count_stack_push_value: int = 0
    pm_data_access: bool = False
    dm_access: bool = False


def apply_load_non_dreg_immediate_cycle(
    state: LoadNonDregImmediateState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup: InternalMoveSetup | None = None,
) -> LoadNonDregImmediateCycleResult:
    """Apply one reset, setup, or Type 7 cycle-end write boundary."""

    action = decode_load_non_dreg_immediate(opcode)
    if reset:
        return LoadNonDregImmediateCycleResult(
            LoadNonDregImmediateState.reset(),
            action,
            class_valid=action is not None,
            action_valid=bool(action is not None and action.legal),
        )
    conflict = execute and setup is not None
    invalid_opcode = execute and action is None
    invalid_subencoding = bool(
        execute and action is not None and not action.legal
    )
    if conflict or invalid_opcode or invalid_subencoding:
        return LoadNonDregImmediateCycleResult(
            state,
            action,
            class_valid=action is not None,
            action_valid=bool(action is not None and action.legal),
            invalid_subencoding=invalid_subencoding,
            invalid_opcode=invalid_opcode,
            integration_conflict=conflict,
        )
    if setup is not None:
        setup_result = apply_internal_move_cycle(
            state.registers,
            setup=setup,
        )
        return LoadNonDregImmediateCycleResult(
            LoadNonDregImmediateState(setup_result.state),
            action,
            class_valid=action is not None,
            action_valid=bool(action is not None and action.legal),
            bank_selection_unknown=setup_result.bank_selection_unknown,
            count_stack_push=setup_result.count_stack_push,
            count_stack_push_value=setup_result.count_stack_push_value,
        )
    if not execute:
        return LoadNonDregImmediateCycleResult(
            state,
            action,
            class_valid=action is not None,
            action_valid=bool(action is not None and action.legal),
        )
    assert action is not None and action.legal
    updated, pushed, push_value = write_internal_move_register(
        state.registers,
        action.register_code,
        ExactWord(16, action.data.value),
    )
    return LoadNonDregImmediateCycleResult(
        state if updated is None else LoadNonDregImmediateState(updated),
        action,
        class_valid=True,
        action_valid=True,
        boundary_valid=updated is not None,
        bank_selection_unknown=updated is None,
        count_stack_push=pushed,
        count_stack_push_value=push_value,
    )
