"""Independent bounded original ADSP-2100 Type 12 execution model.

The boundary models one logical DM transaction.  An accepted instruction
captures all cycle-start computational and DAG values.  A deasserted DMACK
extends that transaction without changing architectural state; completion
atomically commits the shifter result, optional DM read, and I-register
post-modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .dag import compute_dag, reverse_address
from .model import ComputationalBank, ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup, DAGRegisterState, _apply_setup
from .registers import (
    DREG,
    DREGWrite,
    ShifterRegisterWrite,
    apply_computational_cycle,
    apply_dreg_cycle,
    read_dreg,
)
from .shift_move import (
    SHIFTER_XOP_DREG,
    _apply_actions,
    _compute_known_shifter,
    _invalidate_shifter_result,
    _shifter_write,
)
from .shifter import ShifterResult
from .status import StatusCycleInputs, StatusRegisters, apply_status_cycle


SHIFTER_DM_CLASS_MASK = 0xFE0000
SHIFTER_DM_CLASS_VALUE = 0x120000


@dataclass(frozen=True)
class ShifterDMAction:
    write: bool
    dag: int
    sf: int
    xop: int
    shifter_source: DREG
    memory_dreg: DREG
    i_local: int
    m_local: int
    i_address: int
    m_address: int


def is_shifter_dm_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & SHIFTER_DM_CLASS_MASK == SHIFTER_DM_CLASS_VALUE


def _destination_collision(sf: int, destination: DREG) -> bool:
    if sf <= 0xB:
        return destination in (DREG.SR0, DREG.SR1)
    return sf <= 0xE and destination == DREG.SE


def shifter_dm_unsupported_reason(opcode: int) -> str | None:
    if not is_shifter_dm_class(opcode):
        return None
    xop = (opcode >> 8) & 0x7
    if xop not in SHIFTER_XOP_DREG:
        return "UNAVAILABLE_SHIFTER_XOP"
    write = bool((opcode >> 15) & 1)
    sf = (opcode >> 11) & 0xF
    memory_dreg = DREG((opcode >> 4) & 0xF)
    if not write and _destination_collision(sf, memory_dreg):
        return "UNSUPPORTED_DESTINATION_COLLISION"
    return None


def decode_shifter_dm(opcode: int) -> ShifterDMAction | None:
    if not is_shifter_dm_class(opcode):
        return None
    if shifter_dm_unsupported_reason(opcode) is not None:
        return None
    dag = (opcode >> 16) & 1
    xop = (opcode >> 8) & 0x7
    return ShifterDMAction(
        write=bool((opcode >> 15) & 1),
        dag=dag,
        sf=(opcode >> 11) & 0xF,
        xop=xop,
        shifter_source=SHIFTER_XOP_DREG[xop],
        memory_dreg=DREG((opcode >> 4) & 0xF),
        i_local=(opcode >> 2) & 0x3,
        m_local=opcode & 0x3,
        i_address=(dag << 2) | ((opcode >> 2) & 0x3),
        m_address=(dag << 2) | (opcode & 0x3),
    )


@dataclass(frozen=True)
class ShifterDMPending:
    action: ShifterDMAction
    address: ExactWord | object
    write_data: ExactWord | object
    next_i: int | None
    dag_configuration_valid: bool
    shifter_result: ShifterResult | None


@dataclass(frozen=True)
class ShifterDMState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    dag: DAGRegisterState = field(default_factory=DAGRegisterState)
    pending: ShifterDMPending | None = None

    @classmethod
    def reset(cls) -> "ShifterDMState":
        return cls()


@dataclass(frozen=True)
class ShifterDMCycleResult:
    state: ShifterDMState
    action: ShifterDMAction | None = None
    unsupported_reason: str | None = None
    class_valid: bool = False
    action_valid: bool = False
    unsupported_subencoding: bool = False
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
    shifter_result_known: bool = False
    dag_configuration_valid: bool = False
    i_write: bool = False
    i_write_known: bool = False
    dreg_write: bool = False
    dreg_write_known: bool = False
    sr_write: bool = False
    se_write: bool = False
    sb_write: bool = False
    ss_write: bool = False
    sr_result: int = 0
    se_result: int = 0
    sb_result: int = 0
    ss_result: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def _pending_from_state(
    state: ShifterDMState,
    action: ShifterDMAction,
) -> ShifterDMPending:
    old_i = state.dag.i[action.i_address]
    m_value = state.dag.m[action.m_address]
    l_value = state.dag.l[action.i_address]
    address: ExactWord | object = UNKNOWN
    next_i: int | None = None
    configuration_valid = False
    if old_i is not None:
        address_value = (
            reverse_address(old_i)
            if action.dag == 0 and bool(state.status.mstat.value & 0x2)
            else old_i
        )
        address = ExactWord(14, address_value)
    if old_i is not None and m_value is not None and l_value is not None:
        dag_result = compute_dag(
            old_i,
            m_value,
            l_value,
            dag1=action.dag == 0,
            bit_reverse_enabled=bool(state.status.mstat.value & 0x2),
        )
        address = ExactWord(14, dag_result.address)
        configuration_valid = dag_result.configuration_valid
        if configuration_valid:
            next_i = dag_result.next_i

    bank = state.alternate if state.status.alternate_bank else state.primary
    memory_source = read_dreg(bank, action.memory_dreg)
    write_data = (
        memory_source
        if action.write and isinstance(memory_source, ExactWord)
        else UNKNOWN
    )
    # Reuse only the independently specified shifter computation; commit is
    # deliberately separate so memory completion controls atomic visibility.
    shift_compatible = _ShiftCompatibleState(
        state.primary,
        state.alternate,
        state.status,
    )
    shifter_result = _compute_known_shifter(shift_compatible, action)
    return ShifterDMPending(
        action=action,
        address=address,
        write_data=write_data,
        next_i=next_i,
        dag_configuration_valid=configuration_valid,
        shifter_result=shifter_result,
    )


@dataclass(frozen=True)
class _ShiftCompatibleState:
    primary: ComputationalBank
    alternate: ComputationalBank
    status: StatusRegisters


def _replace_i(
    dag: DAGRegisterState,
    address: int,
    value: int | None,
) -> DAGRegisterState:
    values = list(dag.i)
    values[address] = value
    return DAGRegisterState(tuple(values), dag.m, dag.l)


def _complete_pending(
    state: ShifterDMState,
    pending: ShifterDMPending,
    dm_read_data: ExactWord | object,
) -> ShifterDMState:
    action = pending.action
    move_data: ExactWord | None = None
    if not action.write and isinstance(dm_read_data, ExactWord):
        if dm_read_data.width != 16:
            raise ValueError("DM read data must be exactly 16 bits")
        move_data = dm_read_data
    shift_state = _ShiftCompatibleState(
        state.primary,
        state.alternate,
        state.status,
    )
    # Type 12 writes a DREG only for a memory read.  Type 14's action shape is
    # duck-compatible for the shared, old-value-safe commit helper.
    if action.write:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            shifter_write=(
                None
                if pending.shifter_result is None
                else _shifter_write(pending.shifter_result)
            ),
        )
        status = state.status
        if (
            pending.shifter_result is not None
            and pending.shifter_result.ss_write
        ):
            status = apply_status_cycle(
                status,
                StatusCycleInputs(shifter_ss=pending.shifter_result.ss_result),
            ).state
        shifted = _ShiftCompatibleState(
            registers.primary,
            registers.alternate,
            status,
        )
        if pending.shifter_result is None:
            shifted = _invalidate_shifter_result(shifted, action.sf)
    else:
        commit_action = _CommitAction(
            action.sf,
            action.memory_dreg,
        )
        shifted = _apply_actions(
            shift_state,
            commit_action,
            move_data,
            pending.shifter_result,
        )
    dag = _replace_i(state.dag, action.i_address, pending.next_i)
    return ShifterDMState(
        shifted.primary,
        shifted.alternate,
        shifted.status,
        dag,
        None,
    )


@dataclass(frozen=True)
class _CommitAction:
    sf: int
    move_destination: DREG


def _result(
    state: ShifterDMState,
    pending: ShifterDMPending | None,
    *,
    action: ShifterDMAction | None,
    unsupported_reason: str | None,
    class_valid: bool,
    boundary_valid: bool = False,
    accepted: bool = False,
    complete: bool = False,
    stalled: bool = False,
    invalid: bool = False,
    conflict: bool = False,
    read_data_known: bool = False,
) -> ShifterDMCycleResult:
    active = pending is not None
    current = pending
    current_action = current.action if current is not None else action
    address_known = current is not None and isinstance(current.address, ExactWord)
    write_known = current is not None and isinstance(current.write_data, ExactWord)
    shifter = None if current is None else current.shifter_result
    sr_write = complete and shifter is not None and shifter.sr_write
    se_write = complete and shifter is not None and shifter.se_write
    sb_write = complete and shifter is not None and shifter.sb_write
    ss_write = complete and shifter is not None and shifter.ss_write
    return ShifterDMCycleResult(
        state=state,
        action=action,
        unsupported_reason=unsupported_reason,
        class_valid=class_valid,
        action_valid=action is not None,
        unsupported_subencoding=class_valid and action is None,
        boundary_valid=boundary_valid,
        accepted=accepted,
        instruction_complete=complete,
        transaction_active=active,
        stalled=stalled,
        busy=state.pending is not None,
        invalid_opcode=invalid,
        integration_conflict=conflict,
        dm_select=active,
        dm_read=active and not current_action.write,
        dm_write=active and current_action.write,
        dm_address=current.address.value if address_known else 0,
        dm_address_known=address_known,
        dm_write_data=current.write_data.value if write_known else 0,
        dm_write_data_known=write_known,
        shifter_result_known=shifter is not None,
        dag_configuration_valid=(
            False if current is None else current.dag_configuration_valid
        ),
        i_write=complete,
        i_write_known=complete and current is not None and current.next_i is not None,
        dreg_write=complete and current_action is not None and not current_action.write,
        dreg_write_known=(
            complete and current_action is not None and not current_action.write
            and read_data_known
        ),
        sr_write=sr_write,
        se_write=se_write,
        sb_write=sb_write,
        ss_write=ss_write,
        sr_result=shifter.sr_result if sr_write else 0,
        se_result=shifter.se_result if se_write else 0,
        sb_result=shifter.sb_result if sb_write else 0,
        ss_result=shifter.ss_result if ss_write else False,
        pm_data_access=False,
        dm_access=active,
    )


def apply_shifter_dm_cycle(
    state: ShifterDMState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    dm_ack: bool = False,
    dm_read_data: ExactWord | object = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_sb: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
) -> ShifterDMCycleResult:
    """Apply one setup, accepted transaction, wait extension, or completion."""

    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly eight bits")
    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    if setup_sb is not None and setup_sb.width != 5:
        raise ValueError("SB setup must be exactly five bits")
    if isinstance(dm_read_data, ExactWord) and dm_read_data.width != 16:
        raise ValueError("DM read data must be exactly 16 bits")

    class_valid = is_shifter_dm_class(opcode)
    reason = shifter_dm_unsupported_reason(opcode)
    action = decode_shifter_dm(opcode)
    setups = (setup_astat, setup_mstat, setup_dreg, setup_sb, setup_dag)
    setup_count = sum(value is not None for value in setups)

    if reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        reset_state = ShifterDMState(
            ComputationalBank(),
            ComputationalBank(),
            status,
            DAGRegisterState(),
            None,
        )
        return _result(
            reset_state,
            None,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
        )

    if state.pending is not None:
        conflict = execute or setup_count != 0 or setup_count > 1
        pending = state.pending
        if not dm_ack:
            return _result(
                state,
                pending,
                action=action,
                unsupported_reason=reason,
                class_valid=class_valid,
                stalled=True,
                conflict=conflict,
            )
        completed = _complete_pending(state, pending, dm_read_data)
        # Pass read validity explicitly after constructing the common result.
        result = _result(
            completed,
            pending,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
            complete=True,
            conflict=conflict,
            read_data_known=isinstance(dm_read_data, ExactWord),
        )
        return replace(result, busy=False)

    conflict = (execute and setup_count != 0) or setup_count > 1
    invalid = execute and action is None
    if conflict or invalid:
        return _result(
            state,
            None,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
            invalid=invalid,
            conflict=conflict,
        )

    if setup_astat is not None or setup_mstat is not None:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(
                astat_move=setup_astat,
                mstat_move=setup_mstat,
            ),
        ).state
        return _result(
            replace(state, status=status),
            None,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
        )
    if setup_dreg is not None:
        registers = apply_dreg_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            writes=(setup_dreg,),
        )
        return _result(
            ShifterDMState(
                registers.primary,
                registers.alternate,
                state.status,
                state.dag,
                None,
            ),
            None,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
        )
    if setup_sb is not None:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            shifter_write=ShifterRegisterWrite(sb=setup_sb),
        )
        return _result(
            ShifterDMState(
                registers.primary,
                registers.alternate,
                state.status,
                state.dag,
                None,
            ),
            None,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
        )
    if setup_dag is not None:
        return _result(
            replace(state, dag=_apply_setup(state.dag, setup_dag)),
            None,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
        )
    if not execute:
        return _result(
            state,
            None,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
        )

    assert action is not None
    pending = _pending_from_state(state, action)
    issued = replace(state, pending=pending)
    if not dm_ack:
        return _result(
            issued,
            pending,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
            boundary_valid=True,
            accepted=True,
            stalled=True,
        )
    completed = _complete_pending(issued, pending, dm_read_data)
    result = _result(
        completed,
        pending,
        action=action,
        unsupported_reason=reason,
        class_valid=class_valid,
        boundary_valid=True,
        accepted=True,
        complete=True,
        read_data_known=isinstance(dm_read_data, ExactWord),
    )
    return replace(result, busy=False)
