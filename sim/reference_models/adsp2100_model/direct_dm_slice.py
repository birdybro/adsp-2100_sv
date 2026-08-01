"""Waited architectural execution for original ADSP-2100 Type 3.

The direct address is carried by the instruction and therefore has no DAG
side effect.  A write captures its general-register source at issue.  A read
commits its general-register destination only when the logical DM transaction
completes.  The shared Type 17 register-state helpers keep narrowing, bank
selection, MR1 sign fill, and CNTR/count-stack behavior identical.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .direct_dm import DirectDMAction, decode_direct_dm
from .internal_move_slice import (
    InternalMoveSetup,
    InternalMoveSliceState,
    apply_internal_move_cycle,
    read_internal_move_register,
    write_internal_move_register,
)
from .model import ExactWord, KnownOrUnknown, UNKNOWN


@dataclass(frozen=True)
class DirectDMPending:
    action: DirectDMAction
    write_data: KnownOrUnknown = UNKNOWN
    source_extension_provisional: bool = False


@dataclass(frozen=True)
class DirectDMSliceState:
    registers: InternalMoveSliceState = field(
        default_factory=InternalMoveSliceState.reset
    )
    pending: DirectDMPending | None = None

    @classmethod
    def reset(cls) -> "DirectDMSliceState":
        return cls()


@dataclass(frozen=True)
class DirectDMCycleResult:
    state: DirectDMSliceState
    action: DirectDMAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    invalid_subencoding: bool = False
    boundary_valid: bool = False
    accepted: bool = False
    instruction_complete: bool = False
    transaction_active: bool = False
    stalled: bool = False
    busy: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    bank_selection_unknown: bool = False
    dm_select: bool = False
    dm_read: bool = False
    dm_write: bool = False
    dm_address: int = 0
    dm_address_known: bool = False
    dm_write_data: int = 0
    dm_write_data_known: bool = False
    dreg_write: bool = False
    dreg_write_known: bool = False
    source_extension_provisional: bool = False
    count_stack_push: bool = False
    count_stack_push_value: int = 0
    pm_data_access: bool = False
    dm_access: bool = False


def _capture_pending(
    state: DirectDMSliceState,
    action: DirectDMAction,
) -> DirectDMPending:
    write_data: KnownOrUnknown = UNKNOWN
    provisional = False
    if action.write:
        write_data, provisional = read_internal_move_register(
            state.registers,
            action.register_code,
        )
    return DirectDMPending(
        action=action,
        write_data=write_data,
        source_extension_provisional=provisional,
    )


def _result(
    state: DirectDMSliceState,
    active: DirectDMPending | None,
    *,
    action: DirectDMAction | None,
    boundary_valid: bool = False,
    accepted: bool = False,
    complete: bool = False,
    stalled: bool = False,
    invalid_opcode: bool = False,
    invalid_subencoding: bool = False,
    integration_conflict: bool = False,
    bank_selection_unknown: bool = False,
    dreg_write_known: bool = False,
    count_stack_push: bool = False,
    count_stack_push_value: int = 0,
) -> DirectDMCycleResult:
    transaction_active = active is not None
    active_action = active.action if active is not None else None
    write = bool(active_action is not None and active_action.write)
    write_known = bool(
        write and active is not None and active.write_data is not UNKNOWN
    )
    return DirectDMCycleResult(
        state=state,
        action=action,
        class_valid=action is not None,
        action_valid=bool(action is not None and action.legal),
        invalid_subencoding=invalid_subencoding,
        boundary_valid=boundary_valid,
        accepted=accepted,
        instruction_complete=complete,
        transaction_active=transaction_active,
        stalled=stalled,
        busy=state.pending is not None and stalled,
        invalid_opcode=invalid_opcode,
        integration_conflict=integration_conflict,
        bank_selection_unknown=bank_selection_unknown,
        dm_select=transaction_active,
        dm_read=transaction_active and not write,
        dm_write=transaction_active and write,
        dm_address=(active_action.address if active_action is not None else 0),
        dm_address_known=transaction_active,
        dm_write_data=(
            active.write_data.value
            if active is not None and isinstance(active.write_data, ExactWord)
            else 0
        ),
        dm_write_data_known=write_known,
        dreg_write=complete and not write,
        dreg_write_known=complete and not write and dreg_write_known,
        source_extension_provisional=bool(
            active is not None and active.source_extension_provisional
        ),
        count_stack_push=count_stack_push,
        count_stack_push_value=count_stack_push_value,
        pm_data_access=False,
        dm_access=transaction_active,
    )


def apply_direct_dm_cycle(
    state: DirectDMSliceState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    dm_ack: bool = False,
    dm_read_data: KnownOrUnknown = UNKNOWN,
    setup: InternalMoveSetup | None = None,
) -> DirectDMCycleResult:
    """Apply one setup, Type 3 issue, wait, or completion boundary."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if dm_read_data is not UNKNOWN and (
        not isinstance(dm_read_data, ExactWord) or dm_read_data.width != 16
    ):
        raise ValueError("DM read data must be exactly 16 bits")

    action = decode_direct_dm(opcode)
    if reset:
        return _result(DirectDMSliceState.reset(), None, action=action)

    if state.pending is not None:
        conflict = execute or setup is not None
        if not dm_ack:
            return _result(
                state,
                state.pending,
                action=action,
                stalled=True,
                integration_conflict=conflict,
            )
        pending = state.pending
        registers = state.registers
        bank_unknown = False
        pushed = False
        push_value = 0
        if not pending.action.write:
            updated, pushed, push_value = write_internal_move_register(
                registers,
                pending.action.register_code,
                dm_read_data,
            )
            bank_unknown = updated is None
            if updated is not None:
                registers = updated
        completed = DirectDMSliceState(registers=registers)
        return _result(
            completed,
            pending,
            action=action,
            complete=True,
            integration_conflict=conflict,
            bank_selection_unknown=bank_unknown,
            dreg_write_known=dm_read_data is not UNKNOWN,
            count_stack_push=pushed,
            count_stack_push_value=push_value,
        )

    conflict = execute and setup is not None
    invalid_opcode = execute and action is None
    invalid_subencoding = bool(
        execute and action is not None and not action.legal
    )
    if conflict or invalid_opcode or invalid_subencoding:
        return _result(
            state,
            None,
            action=action,
            invalid_opcode=invalid_opcode,
            invalid_subencoding=invalid_subencoding,
            integration_conflict=conflict,
        )

    if setup is not None:
        setup_result = apply_internal_move_cycle(
            state.registers,
            setup=setup,
        )
        return _result(
            replace(state, registers=setup_result.state),
            None,
            action=action,
            bank_selection_unknown=setup_result.bank_selection_unknown,
            count_stack_push=setup_result.count_stack_push,
            count_stack_push_value=setup_result.count_stack_push_value,
        )
    if not execute:
        return _result(state, None, action=action)

    assert action is not None and action.legal
    pending = _capture_pending(state, action)
    issued = replace(state, pending=pending)
    if not dm_ack:
        return _result(
            issued,
            pending,
            action=action,
            boundary_valid=True,
            accepted=True,
            stalled=True,
        )

    registers = state.registers
    bank_unknown = False
    pushed = False
    push_value = 0
    if not action.write:
        updated, pushed, push_value = write_internal_move_register(
            registers,
            action.register_code,
            dm_read_data,
        )
        bank_unknown = updated is None
        if updated is not None:
            registers = updated
    completed = DirectDMSliceState(registers=registers)
    return _result(
        completed,
        pending,
        action=action,
        boundary_valid=True,
        accepted=True,
        complete=True,
        bank_selection_unknown=bank_unknown,
        dreg_write_known=dm_read_data is not UNKNOWN,
        count_stack_push=pushed,
        count_stack_push_value=push_value,
    )
