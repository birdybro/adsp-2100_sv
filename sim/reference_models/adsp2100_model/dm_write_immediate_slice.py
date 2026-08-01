"""Independent bounded original ADSP-2100 Type 2 execution model.

The model exposes one logical data-memory write transaction.  Instruction
acceptance captures the cycle-start I/M/L values, bit-reverse mode, address,
post-modified I value, and the raw sixteen-bit immediate.  DMACK-low extends
the transaction without architectural changes; the first DMACK-high boundary
commits only the selected I-register post-modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .dag import compute_dag, reverse_address
from .dm_write_immediate import (
    DMWriteImmediateAction,
    decode_dm_write_immediate,
)
from .model import ExactWord
from .modify_address import DAGRegisterSetup, DAGRegisterState, _apply_setup


@dataclass(frozen=True)
class DMWriteImmediatePending:
    action: DMWriteImmediateAction
    address: int | None
    next_i: int | None
    dag_configuration_valid: bool


@dataclass(frozen=True)
class DMWriteImmediateState:
    dag: DAGRegisterState = field(default_factory=DAGRegisterState)
    mstat: int = 0
    pending: DMWriteImmediatePending | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.mstat <= 0xF:
            raise ValueError("MSTAT must fit four bits")

    @classmethod
    def reset(cls) -> "DMWriteImmediateState":
        return cls()


@dataclass(frozen=True)
class DMWriteImmediateCycleResult:
    state: DMWriteImmediateState
    action: DMWriteImmediateAction | None = None
    class_valid: bool = False
    action_valid: bool = False
    boundary_valid: bool = False
    accepted: bool = False
    instruction_complete: bool = False
    transaction_active: bool = False
    stalled: bool = False
    busy: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    dm_select: bool = False
    dm_read: bool = False
    dm_write: bool = False
    dm_address: int = 0
    dm_address_known: bool = False
    dm_write_data: int = 0
    dm_write_data_known: bool = False
    dag_configuration_valid: bool = False
    i_write: bool = False
    i_write_known: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def _capture_pending(
    state: DMWriteImmediateState,
    action: DMWriteImmediateAction,
) -> DMWriteImmediatePending:
    old_i = state.dag.i[action.i_address]
    m_value = state.dag.m[action.m_address]
    l_value = state.dag.l[action.l_address]
    bit_reverse = action.dag == 0 and bool(state.mstat & 0x2)
    address = None
    next_i = None
    configuration_valid = False

    if old_i is not None:
        address = reverse_address(old_i) if bit_reverse else old_i
    if old_i is not None and m_value is not None and l_value is not None:
        dag_result = compute_dag(
            old_i,
            m_value,
            l_value,
            dag1=action.dag == 0,
            bit_reverse_enabled=bit_reverse,
        )
        address = dag_result.address
        configuration_valid = dag_result.configuration_valid
        if configuration_valid:
            next_i = dag_result.next_i

    return DMWriteImmediatePending(
        action=action,
        address=address,
        next_i=next_i,
        dag_configuration_valid=configuration_valid,
    )


def _complete_pending(
    state: DMWriteImmediateState,
    pending: DMWriteImmediatePending,
) -> DMWriteImmediateState:
    values = list(state.dag.i)
    values[pending.action.i_address] = pending.next_i
    return DMWriteImmediateState(
        dag=DAGRegisterState(tuple(values), state.dag.m, state.dag.l),
        mstat=state.mstat,
        pending=None,
    )


def _result(
    state: DMWriteImmediateState,
    active: DMWriteImmediatePending | None,
    *,
    action: DMWriteImmediateAction | None,
    boundary_valid: bool = False,
    accepted: bool = False,
    complete: bool = False,
    stalled: bool = False,
    invalid_opcode: bool = False,
    integration_conflict: bool = False,
) -> DMWriteImmediateCycleResult:
    transaction_active = active is not None
    return DMWriteImmediateCycleResult(
        state=state,
        action=action,
        class_valid=action is not None,
        action_valid=action is not None,
        boundary_valid=boundary_valid,
        accepted=accepted,
        instruction_complete=complete,
        transaction_active=transaction_active,
        stalled=stalled,
        busy=state.pending is not None and stalled,
        invalid_opcode=invalid_opcode,
        integration_conflict=integration_conflict,
        dm_select=transaction_active,
        dm_read=False,
        dm_write=transaction_active,
        dm_address=(
            active.address
            if active is not None and active.address is not None
            else 0
        ),
        dm_address_known=active is not None and active.address is not None,
        dm_write_data=(active.action.immediate if active is not None else 0),
        dm_write_data_known=transaction_active,
        dag_configuration_valid=(
            active.dag_configuration_valid if active is not None else False
        ),
        i_write=complete,
        i_write_known=(
            complete and active is not None and active.next_i is not None
        ),
        pm_data_access=False,
        dm_access=transaction_active,
    )


def apply_dm_write_immediate_cycle(
    state: DMWriteImmediateState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    dm_ack: bool = False,
    setup_mstat: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
) -> DMWriteImmediateCycleResult:
    """Apply one setup, Type 2 issue, wait extension, or completion clock."""

    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    action = decode_dm_write_immediate(opcode)
    setup_count = int(setup_mstat is not None) + int(setup_dag is not None)

    if reset:
        return _result(DMWriteImmediateState.reset(), None, action=action)

    if state.pending is not None:
        conflict = execute or setup_count != 0
        if not dm_ack:
            return _result(
                state,
                state.pending,
                action=action,
                stalled=True,
                integration_conflict=conflict,
            )
        completed = _complete_pending(state, state.pending)
        return _result(
            completed,
            state.pending,
            action=action,
            complete=True,
            integration_conflict=conflict,
        )

    conflict = (execute and setup_count != 0) or setup_count > 1
    invalid = execute and action is None
    if conflict or invalid:
        return _result(
            state,
            None,
            action=action,
            invalid_opcode=invalid,
            integration_conflict=conflict,
        )

    if setup_mstat is not None:
        return _result(
            replace(state, mstat=setup_mstat.value),
            None,
            action=action,
        )
    if setup_dag is not None:
        return _result(
            replace(state, dag=_apply_setup(state.dag, setup_dag)),
            None,
            action=action,
        )
    if not execute:
        return _result(state, None, action=action)

    assert action is not None
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
    completed = _complete_pending(issued, pending)
    return _result(
        completed,
        pending,
        action=action,
        boundary_valid=True,
        accepted=True,
        complete=True,
    )
