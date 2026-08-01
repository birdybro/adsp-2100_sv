"""Independent bounded original ADSP-2100 Type 13 execution model.

The data-transfer cycle always completes at the fixed program-memory timing
boundary.  A valid cache entry supplies the simultaneously needed next
instruction.  An invalid entry schedules one additional instruction-fetch
cycle without repeating the shifter, PM data transfer, PX update, or DAG
post-modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .dag import compute_dag
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


SHIFTER_PM_CLASS_MASK = 0xFF0000
SHIFTER_PM_CLASS_VALUE = 0x110000


@dataclass(frozen=True)
class ShifterPMAction:
    write: bool
    sf: int
    xop: int
    shifter_source: DREG
    memory_dreg: DREG
    i_local: int
    m_local: int
    i_address: int
    m_address: int


def is_shifter_pm_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & SHIFTER_PM_CLASS_MASK == SHIFTER_PM_CLASS_VALUE


def _destination_collision(sf: int, destination: DREG) -> bool:
    if sf <= 0xB:
        return destination in (DREG.SR0, DREG.SR1)
    return sf <= 0xE and destination == DREG.SE


def shifter_pm_unsupported_reason(opcode: int) -> str | None:
    if not is_shifter_pm_class(opcode):
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


def decode_shifter_pm(opcode: int) -> ShifterPMAction | None:
    if not is_shifter_pm_class(opcode):
        return None
    if shifter_pm_unsupported_reason(opcode) is not None:
        return None
    xop = (opcode >> 8) & 0x7
    return ShifterPMAction(
        write=bool((opcode >> 15) & 1),
        sf=(opcode >> 11) & 0xF,
        xop=xop,
        shifter_source=SHIFTER_XOP_DREG[xop],
        memory_dreg=DREG((opcode >> 4) & 0xF),
        i_local=(opcode >> 2) & 0x3,
        m_local=opcode & 0x3,
        i_address=4 | ((opcode >> 2) & 0x3),
        m_address=4 | (opcode & 0x3),
    )


@dataclass(frozen=True)
class ShifterPMRecovery:
    next_fetch_address: ExactWord | object


@dataclass(frozen=True)
class ShifterPMPending:
    """Cycle-start Type 13 action held until the PM cycle completes."""

    prepared: "_DataAction"
    next_fetch_address: ExactWord | object
    recovery_required: bool


@dataclass(frozen=True)
class ShifterPMState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    dag: DAGRegisterState = field(default_factory=DAGRegisterState)
    px: ExactWord | object = UNKNOWN
    recovery: ShifterPMRecovery | None = None
    pending: ShifterPMPending | None = None

    @classmethod
    def reset(cls) -> "ShifterPMState":
        return cls()


@dataclass(frozen=True)
class _DataAction:
    action: ShifterPMAction
    address: ExactWord | object
    write_data: ExactWord | object
    next_i: int | None
    dag_configuration_valid: bool
    shifter_result: ShifterResult | None


@dataclass(frozen=True)
class ShifterPMCycleResult:
    state: ShifterPMState
    action: ShifterPMAction | None = None
    unsupported_reason: str | None = None
    class_valid: bool = False
    action_valid: bool = False
    unsupported_subencoding: bool = False
    boundary_valid: bool = False
    accepted: bool = False
    data_action_complete: bool = False
    instruction_complete: bool = False
    busy: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    pm_select: bool = False
    pm_data_access: bool = False
    pm_read: bool = False
    pm_write: bool = False
    pm_address: int = 0
    pm_address_known: bool = False
    pm_write_data: int = 0
    pm_write_data_known: bool = False
    cache_instruction_selected: bool = False
    recovery_required: bool = False
    recovery_fetch: bool = False
    fetched_instruction: int = 0
    fetched_instruction_known: bool = False
    event_boundary: bool = False
    shifter_result_known: bool = False
    dag_configuration_valid: bool = False
    i_write: bool = False
    i_write_known: bool = False
    dreg_write: bool = False
    dreg_write_known: bool = False
    px_write: bool = False
    px_write_known: bool = False
    sr_write: bool = False
    se_write: bool = False
    sb_write: bool = False
    ss_write: bool = False
    sr_result: int = 0
    se_result: int = 0
    sb_result: int = 0
    ss_result: bool = False
    dm_data_access: bool = False


@dataclass(frozen=True)
class _ShiftCompatibleState:
    primary: ComputationalBank
    alternate: ComputationalBank
    status: StatusRegisters


@dataclass(frozen=True)
class _CommitAction:
    sf: int
    move_destination: DREG


def _replace_i(
    dag: DAGRegisterState,
    address: int,
    value: int | None,
) -> DAGRegisterState:
    values = list(dag.i)
    values[address] = value
    return DAGRegisterState(tuple(values), dag.m, dag.l)


def _prepare_data_action(
    state: ShifterPMState,
    action: ShifterPMAction,
) -> _DataAction:
    old_i = state.dag.i[action.i_address]
    m_value = state.dag.m[action.m_address]
    l_value = state.dag.l[action.i_address]
    address: ExactWord | object = UNKNOWN
    next_i: int | None = None
    configuration_valid = False
    if old_i is not None:
        address = ExactWord(14, old_i)
    if old_i is not None and m_value is not None and l_value is not None:
        dag_result = compute_dag(
            old_i,
            m_value,
            l_value,
            dag1=False,
            bit_reverse_enabled=False,
        )
        address = ExactWord(14, dag_result.address)
        configuration_valid = dag_result.configuration_valid
        if configuration_valid:
            next_i = dag_result.next_i

    bank = state.alternate if state.status.alternate_bank else state.primary
    memory_source = read_dreg(bank, action.memory_dreg)
    write_data: ExactWord | object = UNKNOWN
    if (
        action.write
        and isinstance(memory_source, ExactWord)
        and isinstance(state.px, ExactWord)
    ):
        write_data = ExactWord(
            24,
            (memory_source.value << 8) | state.px.value,
        )
    shift_state = _ShiftCompatibleState(
        state.primary,
        state.alternate,
        state.status,
    )
    return _DataAction(
        action=action,
        address=address,
        write_data=write_data,
        next_i=next_i,
        dag_configuration_valid=configuration_valid,
        shifter_result=_compute_known_shifter(shift_state, action),
    )


def _commit_data_action(
    state: ShifterPMState,
    prepared: _DataAction,
    pm_read_data: ExactWord | object,
) -> ShifterPMState:
    action = prepared.action
    if action.write:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            shifter_write=(
                None
                if prepared.shifter_result is None
                else _shifter_write(prepared.shifter_result)
            ),
        )
        status = state.status
        if (
            prepared.shifter_result is not None
            and prepared.shifter_result.ss_write
        ):
            status = apply_status_cycle(
                status,
                StatusCycleInputs(
                    shifter_ss=prepared.shifter_result.ss_result,
                ),
            ).state
        shifted = _ShiftCompatibleState(
            registers.primary,
            registers.alternate,
            status,
        )
        if prepared.shifter_result is None:
            shifted = _invalidate_shifter_result(shifted, action.sf)
        px = state.px
    else:
        move_data = None
        px: ExactWord | object = UNKNOWN
        if isinstance(pm_read_data, ExactWord):
            if pm_read_data.width != 24:
                raise ValueError("PM read data must be exactly 24 bits")
            move_data = ExactWord(16, pm_read_data.value >> 8)
            px = ExactWord(8, pm_read_data.value & 0xFF)
        shifted = _apply_actions(
            _ShiftCompatibleState(
                state.primary,
                state.alternate,
                state.status,
            ),
            _CommitAction(action.sf, action.memory_dreg),
            move_data,
            prepared.shifter_result,
        )
    return ShifterPMState(
        primary=shifted.primary,
        alternate=shifted.alternate,
        status=shifted.status,
        dag=_replace_i(state.dag, action.i_address, prepared.next_i),
        px=px,
        recovery=state.recovery,
        pending=state.pending,
    )


def _idle_result(
    state: ShifterPMState,
    *,
    action: ShifterPMAction | None,
    reason: str | None,
    class_valid: bool,
    invalid: bool = False,
    conflict: bool = False,
) -> ShifterPMCycleResult:
    return ShifterPMCycleResult(
        state=state,
        action=action,
        unsupported_reason=reason,
        class_valid=class_valid,
        action_valid=action is not None,
        unsupported_subencoding=class_valid and action is None,
        busy=state.recovery is not None or state.pending is not None,
        invalid_opcode=invalid,
        integration_conflict=conflict,
    )


def _data_result(
    state: ShifterPMState,
    prepared: _DataAction,
    *,
    pm_read_data: ExactWord | object,
    recovery_required: bool,
    boundary_valid: bool,
    accepted: bool,
    complete: bool,
    conflict: bool = False,
) -> ShifterPMCycleResult:
    """Describe an active Type 13 data cycle at issue, hold, or completion."""

    action = prepared.action
    address_known = isinstance(prepared.address, ExactWord)
    write_known = isinstance(prepared.write_data, ExactWord)
    read_known = isinstance(pm_read_data, ExactWord)
    shifter = prepared.shifter_result
    sr_write = complete and shifter is not None and shifter.sr_write
    se_write = complete and shifter is not None and shifter.se_write
    sb_write = complete and shifter is not None and shifter.sb_write
    ss_write = complete and shifter is not None and shifter.ss_write
    return ShifterPMCycleResult(
        state=state,
        action=action,
        class_valid=True,
        action_valid=True,
        boundary_valid=boundary_valid,
        accepted=accepted,
        data_action_complete=complete,
        instruction_complete=complete and not recovery_required,
        busy=not complete or recovery_required,
        integration_conflict=conflict,
        pm_select=True,
        pm_data_access=True,
        pm_read=not action.write,
        pm_write=action.write,
        pm_address=prepared.address.value if address_known else 0,
        pm_address_known=address_known,
        pm_write_data=prepared.write_data.value if write_known else 0,
        pm_write_data_known=write_known,
        cache_instruction_selected=(
            boundary_valid and not recovery_required
        ),
        recovery_required=boundary_valid and recovery_required,
        event_boundary=complete and not recovery_required,
        shifter_result_known=complete and shifter is not None,
        dag_configuration_valid=prepared.dag_configuration_valid,
        i_write=complete,
        i_write_known=complete and prepared.next_i is not None,
        dreg_write=complete and not action.write,
        dreg_write_known=complete and not action.write and read_known,
        px_write=complete and not action.write,
        px_write_known=complete and not action.write and read_known,
        sr_write=sr_write,
        se_write=se_write,
        sb_write=sb_write,
        ss_write=ss_write,
        sr_result=shifter.sr_result if sr_write else 0,
        se_result=shifter.se_result if se_write else 0,
        sb_result=shifter.sb_result if sb_write else 0,
        ss_result=shifter.ss_result if ss_write else False,
    )


def apply_shifter_pm_cycle(
    state: ShifterPMState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    pm_read_data: ExactWord | object = UNKNOWN,
    next_fetch_address: ExactWord | object = UNKNOWN,
    cache_next_instruction_valid: bool = True,
    force_instruction_fetch: bool = False,
    pm_cycle_complete: bool = True,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_sb: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    setup_px: ExactWord | None = None,
) -> ShifterPMCycleResult:
    """Apply one setup, PM-data cycle, or cache-miss recovery fetch."""

    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly eight bits")
    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    if setup_sb is not None and setup_sb.width != 5:
        raise ValueError("SB setup must be exactly five bits")
    if setup_px is not None and setup_px.width != 8:
        raise ValueError("PX setup must be exactly eight bits")
    if isinstance(pm_read_data, ExactWord) and pm_read_data.width != 24:
        raise ValueError("PM read data must be exactly 24 bits")
    if (
        isinstance(next_fetch_address, ExactWord)
        and next_fetch_address.width != 14
    ):
        raise ValueError("next fetch address must be exactly 14 bits")

    class_valid = is_shifter_pm_class(opcode)
    reason = shifter_pm_unsupported_reason(opcode)
    action = decode_shifter_pm(opcode)
    setups = (
        setup_astat,
        setup_mstat,
        setup_dreg,
        setup_sb,
        setup_dag,
        setup_px,
    )
    setup_count = sum(value is not None for value in setups)

    if reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        reset_state = ShifterPMState(
            primary=ComputationalBank(),
            alternate=ComputationalBank(),
            status=status,
            dag=DAGRegisterState(),
            px=UNKNOWN,
            recovery=None,
            pending=None,
        )
        return _idle_result(
            reset_state,
            action=action,
            reason=reason,
            class_valid=class_valid,
        )

    if state.recovery is not None:
        conflict = execute or setup_count != 0
        recovery = state.recovery
        address_known = isinstance(recovery.next_fetch_address, ExactWord)
        fetched_known = (
            pm_cycle_complete
            and address_known
            and isinstance(pm_read_data, ExactWord)
        )
        completed = (
            replace(state, recovery=None)
            if pm_cycle_complete
            else state
        )
        return ShifterPMCycleResult(
            state=completed,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
            action_valid=action is not None,
            unsupported_subencoding=class_valid and action is None,
            instruction_complete=pm_cycle_complete,
            busy=not pm_cycle_complete,
            integration_conflict=conflict,
            pm_select=True,
            pm_read=True,
            pm_address=(
                recovery.next_fetch_address.value if address_known else 0
            ),
            pm_address_known=address_known,
            recovery_fetch=True,
            fetched_instruction=(pm_read_data.value if fetched_known else 0),
            fetched_instruction_known=fetched_known,
            event_boundary=pm_cycle_complete,
        )

    if state.pending is not None:
        conflict = execute or setup_count != 0
        pending = state.pending
        if not pm_cycle_complete:
            held = _data_result(
                state,
                pending.prepared,
                pm_read_data=pm_read_data,
                recovery_required=pending.recovery_required,
                boundary_valid=False,
                accepted=False,
                complete=False,
                conflict=conflict,
            )
            return replace(
                held,
                action=action,
                unsupported_reason=reason,
                class_valid=class_valid,
                action_valid=action is not None,
                unsupported_subencoding=class_valid and action is None,
            )
        committed = _commit_data_action(
            replace(state, pending=None),
            pending.prepared,
            pm_read_data,
        )
        if pending.recovery_required:
            committed = replace(
                committed,
                recovery=ShifterPMRecovery(pending.next_fetch_address),
            )
        completed = _data_result(
            committed,
            pending.prepared,
            pm_read_data=pm_read_data,
            recovery_required=pending.recovery_required,
            boundary_valid=False,
            accepted=False,
            complete=True,
            conflict=conflict,
        )
        return replace(
            completed,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
            action_valid=action is not None,
            unsupported_subencoding=class_valid and action is None,
        )

    conflict = (execute and setup_count != 0) or setup_count > 1
    invalid = execute and action is None
    if conflict or invalid:
        return _idle_result(
            state,
            action=action,
            reason=reason,
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
        return _idle_result(
            replace(state, status=status),
            action=action,
            reason=reason,
            class_valid=class_valid,
        )
    if setup_dreg is not None:
        registers = apply_dreg_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            writes=(setup_dreg,),
        )
        return _idle_result(
            replace(
                state,
                primary=registers.primary,
                alternate=registers.alternate,
            ),
            action=action,
            reason=reason,
            class_valid=class_valid,
        )
    if setup_sb is not None:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            shifter_write=ShifterRegisterWrite(sb=setup_sb),
        )
        return _idle_result(
            replace(
                state,
                primary=registers.primary,
                alternate=registers.alternate,
            ),
            action=action,
            reason=reason,
            class_valid=class_valid,
        )
    if setup_dag is not None:
        return _idle_result(
            replace(state, dag=_apply_setup(state.dag, setup_dag)),
            action=action,
            reason=reason,
            class_valid=class_valid,
        )
    if setup_px is not None:
        return _idle_result(
            replace(state, px=setup_px),
            action=action,
            reason=reason,
            class_valid=class_valid,
        )
    if not execute:
        return _idle_result(
            state,
            action=action,
            reason=reason,
            class_valid=class_valid,
        )

    assert action is not None
    prepared = _prepare_data_action(state, action)
    recovery_required = (
        force_instruction_fetch or not cache_next_instruction_valid
    )
    if pm_cycle_complete:
        committed = _commit_data_action(state, prepared, pm_read_data)
        if recovery_required:
            committed = replace(
                committed,
                recovery=ShifterPMRecovery(next_fetch_address),
            )
    else:
        committed = replace(
            state,
            pending=ShifterPMPending(
                prepared=prepared,
                next_fetch_address=next_fetch_address,
                recovery_required=recovery_required,
            ),
        )
    return _data_result(
        committed,
        prepared,
        pm_read_data=pm_read_data,
        recovery_required=recovery_required,
        boundary_valid=True,
        accepted=True,
        complete=pm_cycle_complete,
    )
