"""Independent original ADSP-2100 Type 5 action decoder.

Type 5 combines one unconditional ALU/MAC operation (or the documented
AMF-zero no-operation) with one DAG2-addressed program-memory read or write.
This module intentionally stops at the action boundary; cache/fetch recovery
and architectural state execution are modeled separately.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .alu import ALUResult
from .compute_move import ALU_X_DREG, MAC_X_DREG
from .compute_move import (
    _apply_actions,
    _invalidate_compute_result,
    _invalidate_dreg,
    _known_alu_result,
    _known_mac_result,
)
from .dag import compute_dag
from .mac import MACResult
from .model import ComputationalBank, ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup, DAGRegisterState, _apply_setup
from .registers import (
    ALURegisterWrite,
    DREG,
    DREGWrite,
    MACRegisterWrite,
    apply_computational_cycle,
    apply_dreg_cycle,
    read_dreg,
)
from .status import (
    ALUStatusUpdate,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
)


COMPUTE_PM_CLASS_MASK = 0xF00000
COMPUTE_PM_CLASS_VALUE = 0x500000


@dataclass(frozen=True)
class ComputePMAction:
    write: bool
    z: int
    amf: int
    yop: int
    xop: int
    memory_dreg: DREG
    i_local: int
    m_local: int
    i_address: int
    m_address: int

    @property
    def computation_enabled(self) -> bool:
        return self.amf != 0

    @property
    def is_mac(self) -> bool:
        return self.computation_enabled and self.amf < 0x10

    @property
    def destination_feedback(self) -> bool:
        return bool(self.z)

    @property
    def x_source(self) -> DREG | None:
        if not self.computation_enabled:
            return None
        return (MAC_X_DREG if self.is_mac else ALU_X_DREG)[self.xop]

    @property
    def y_source(self) -> DREG | None:
        if not self.computation_enabled or self.yop >= 2:
            return None
        base = DREG.MY0 if self.is_mac else DREG.AY0
        return DREG(int(base) + self.yop)


def is_compute_pm_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & COMPUTE_PM_CLASS_MASK == COMPUTE_PM_CLASS_VALUE


def _destination_collision(
    *, write: bool, z: int, amf: int, destination: DREG
) -> bool:
    if write or z or amf == 0:
        return False
    if amf >= 0x10:
        return destination == DREG.AR
    return destination in (DREG.MR0, DREG.MR1, DREG.MR2)


def compute_pm_unsupported_reason(opcode: int) -> str | None:
    if not is_compute_pm_class(opcode):
        return None
    if _destination_collision(
        write=bool((opcode >> 19) & 1),
        z=(opcode >> 18) & 1,
        amf=(opcode >> 13) & 0x1F,
        destination=DREG((opcode >> 4) & 0xF),
    ):
        return "UNSUPPORTED_DESTINATION_COLLISION"
    return None


def decode_compute_pm(opcode: int) -> ComputePMAction | None:
    if not is_compute_pm_class(opcode):
        return None
    if compute_pm_unsupported_reason(opcode) is not None:
        return None
    return ComputePMAction(
        write=bool((opcode >> 19) & 1),
        z=(opcode >> 18) & 1,
        amf=(opcode >> 13) & 0x1F,
        yop=(opcode >> 11) & 3,
        xop=(opcode >> 8) & 7,
        memory_dreg=DREG((opcode >> 4) & 0xF),
        i_local=(opcode >> 2) & 3,
        m_local=opcode & 3,
        i_address=4 | ((opcode >> 2) & 3),
        m_address=4 | (opcode & 3),
    )


@dataclass(frozen=True)
class ComputePMRecovery:
    next_fetch_address: ExactWord | object


@dataclass(frozen=True)
class _PreparedDataAction:
    action: ComputePMAction
    address: ExactWord | object
    write_data: ExactWord | object
    next_i: int | None
    dag_configuration_valid: bool
    compute_result: ALUResult | MACResult | None


@dataclass(frozen=True)
class ComputePMPending:
    prepared: _PreparedDataAction
    next_fetch_address: ExactWord | object
    recovery_required: bool


@dataclass(frozen=True)
class ComputePMState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    dag: DAGRegisterState = field(default_factory=DAGRegisterState)
    px: ExactWord | object = UNKNOWN
    recovery: ComputePMRecovery | None = None
    pending: ComputePMPending | None = None

    @classmethod
    def reset(cls) -> "ComputePMState":
        return cls()


@dataclass(frozen=True)
class ComputePMCycleResult:
    state: ComputePMState
    action: ComputePMAction | None = None
    unsupported_reason: str | None = None
    class_valid: bool = False
    action_valid: bool = False
    unsupported_subencoding: bool = False
    boundary_valid: bool = False
    accepted: bool = False
    data_action_complete: bool = False
    instruction_complete: bool = False
    transaction_active: bool = False
    held_transaction: bool = False
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
    active_computation_enabled: bool = False
    active_is_mac: bool = False
    compute_result_known: bool = False
    dag_configuration_valid: bool = False
    i_write: bool = False
    i_write_known: bool = False
    dreg_write: bool = False
    dreg_write_known: bool = False
    px_write: bool = False
    px_write_known: bool = False
    alu_write: bool = False
    mac_write: bool = False
    alu_status_write: bool = False
    mac_status_write: bool = False
    alu_result: int = 0
    mac_result: int = 0
    dm_data_access: bool = False


@dataclass(frozen=True)
class _ComputeStateView:
    primary: ComputationalBank
    alternate: ComputationalBank
    status: StatusRegisters


@dataclass(frozen=True)
class _ComputeReadAction:
    z: int
    amf: int
    yop: int
    xop: int
    move_destination: DREG

    @property
    def is_mac(self) -> bool:
        return self.amf < 0x10

    @property
    def destination_feedback(self) -> bool:
        return bool(self.z)


def _selected_bank(state: ComputePMState) -> ComputationalBank:
    return state.alternate if state.status.alternate_bank else state.primary


def _replace_selected_bank(
    state: ComputePMState,
    bank: ComputationalBank,
) -> ComputePMState:
    if state.status.alternate_bank:
        return replace(state, alternate=bank)
    return replace(state, primary=bank)


def _replace_i(
    dag: DAGRegisterState,
    address: int,
    value: int | None,
) -> DAGRegisterState:
    values = list(dag.i)
    values[address] = value
    return DAGRegisterState(tuple(values), dag.m, dag.l)


def _prepare_data_action(
    state: ComputePMState,
    action: ComputePMAction,
) -> _PreparedDataAction:
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

    bank = _selected_bank(state)
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

    view = _ComputeStateView(state.primary, state.alternate, state.status)
    compute_result: ALUResult | MACResult | None = None
    if action.computation_enabled:
        compute_result = (
            _known_mac_result(view, action)
            if action.is_mac
            else _known_alu_result(view, action)
        )
    return _PreparedDataAction(
        action=action,
        address=address,
        write_data=write_data,
        next_i=next_i,
        dag_configuration_valid=configuration_valid,
        compute_result=compute_result,
    )


def _commit_compute_write(
    state: ComputePMState,
    action: ComputePMAction,
    compute: ALUResult | MACResult | None,
) -> ComputePMState:
    view = _ComputeStateView(state.primary, state.alternate, state.status)
    alu_write = None
    mac_write = None
    status_inputs = StatusCycleInputs()
    if isinstance(compute, ALUResult):
        alu_write = ALURegisterWrite(
            action.destination_feedback,
            ExactWord(16, compute.destination_result),
        )
        status_inputs = StatusCycleInputs(
            alu=ALUStatusUpdate(
                compute.az,
                compute.an,
                compute.av,
                compute.ac,
                compute.as_value if compute.as_write else None,
            )
        )
    elif isinstance(compute, MACResult):
        mac_write = MACRegisterWrite(
            action.destination_feedback,
            ExactWord(40, compute.result),
        )
        status_inputs = StatusCycleInputs(mac_mv=compute.mv)
    registers = apply_computational_cycle(
        state.primary,
        state.alternate,
        alternate_selected=state.status.alternate_bank,
        alu_write=alu_write,
        mac_write=mac_write,
    )
    status = apply_status_cycle(state.status, status_inputs).state
    updated = replace(
        state,
        primary=registers.primary,
        alternate=registers.alternate,
        status=status,
    )
    if compute is None:
        invalid = _invalidate_compute_result(view, action)
        updated = replace(
            updated,
            primary=invalid.primary,
            alternate=invalid.alternate,
            status=invalid.status,
        )
    return updated


def _commit_data_action(
    state: ComputePMState,
    prepared: _PreparedDataAction,
    pm_read_data: ExactWord | object,
) -> ComputePMState:
    action = prepared.action
    if isinstance(pm_read_data, ExactWord) and pm_read_data.width != 24:
        raise ValueError("PM read data must be exactly 24 bits")
    move_data = (
        ExactWord(16, pm_read_data.value >> 8)
        if not action.write and isinstance(pm_read_data, ExactWord)
        else None
    )
    px: ExactWord | object = state.px
    if not action.write:
        px = (
            ExactWord(8, pm_read_data.value & 0xFF)
            if isinstance(pm_read_data, ExactWord)
            else UNKNOWN
        )

    updated = state
    if action.computation_enabled and not action.write:
        view = _ComputeStateView(
            state.primary,
            state.alternate,
            state.status,
        )
        committed = _apply_actions(
            view,
            _ComputeReadAction(
                action.z,
                action.amf,
                action.yop,
                action.xop,
                action.memory_dreg,
            ),
            move_data,
            prepared.compute_result,
        )
        updated = replace(
            updated,
            primary=committed.primary,
            alternate=committed.alternate,
            status=committed.status,
        )
    elif action.computation_enabled:
        updated = _commit_compute_write(
            updated,
            action,
            prepared.compute_result,
        )
    elif not action.write:
        if move_data is not None:
            registers = apply_dreg_cycle(
                state.primary,
                state.alternate,
                alternate_selected=state.status.alternate_bank,
                writes=(DREGWrite(action.memory_dreg, move_data),),
            )
            updated = replace(
                updated,
                primary=registers.primary,
                alternate=registers.alternate,
            )
        else:
            updated = _replace_selected_bank(
                updated,
                _invalidate_dreg(_selected_bank(updated), action.memory_dreg),
            )

    return replace(
        updated,
        dag=_replace_i(updated.dag, action.i_address, prepared.next_i),
        px=px,
        pending=None,
    )


def _idle_result(
    state: ComputePMState,
    *,
    action: ComputePMAction | None,
    reason: str | None,
    class_valid: bool,
    invalid: bool = False,
    conflict: bool = False,
) -> ComputePMCycleResult:
    return ComputePMCycleResult(
        state=state,
        action=action,
        unsupported_reason=reason,
        class_valid=class_valid,
        action_valid=action is not None,
        unsupported_subencoding=class_valid and action is None,
        held_transaction=state.pending is not None or state.recovery is not None,
        busy=state.pending is not None or state.recovery is not None,
        invalid_opcode=invalid,
        integration_conflict=conflict,
    )


def _data_result(
    state: ComputePMState,
    prepared: _PreparedDataAction,
    *,
    pm_read_data: ExactWord | object,
    recovery_required: bool,
    boundary_valid: bool,
    accepted: bool,
    complete: bool,
    held_transaction: bool = False,
    conflict: bool = False,
) -> ComputePMCycleResult:
    action = prepared.action
    address_known = isinstance(prepared.address, ExactWord)
    write_known = isinstance(prepared.write_data, ExactWord)
    read_known = isinstance(pm_read_data, ExactWord)
    compute = prepared.compute_result
    return ComputePMCycleResult(
        state=state,
        action=action,
        class_valid=True,
        action_valid=True,
        boundary_valid=boundary_valid,
        accepted=accepted,
        data_action_complete=complete,
        instruction_complete=complete and not recovery_required,
        transaction_active=True,
        held_transaction=held_transaction,
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
        cache_instruction_selected=boundary_valid and not recovery_required,
        recovery_required=boundary_valid and recovery_required,
        event_boundary=complete and not recovery_required,
        active_computation_enabled=action.computation_enabled,
        active_is_mac=action.is_mac,
        compute_result_known=(
            action.computation_enabled and compute is not None
        ),
        dag_configuration_valid=prepared.dag_configuration_valid,
        i_write=complete,
        i_write_known=complete and prepared.next_i is not None,
        dreg_write=complete and not action.write,
        dreg_write_known=complete and not action.write and read_known,
        px_write=complete and not action.write,
        px_write_known=complete and not action.write and read_known,
        alu_write=complete and action.computation_enabled and not action.is_mac,
        mac_write=complete and action.computation_enabled and action.is_mac,
        alu_status_write=(
            complete and action.computation_enabled and not action.is_mac
        ),
        mac_status_write=(
            complete and action.computation_enabled and action.is_mac
        ),
        alu_result=(
            compute.destination_result if isinstance(compute, ALUResult) else 0
        ),
        mac_result=(compute.result if isinstance(compute, MACResult) else 0),
    )


def apply_compute_pm_cycle(
    state: ComputePMState,
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
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    setup_px: ExactWord | None = None,
) -> ComputePMCycleResult:
    """Apply one setup, Type 5 PM-data cycle, or recovery fetch."""

    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly eight bits")
    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    if setup_af is not None and setup_af.width != 16:
        raise ValueError("AF setup must be exactly 16 bits")
    if setup_mf is not None and setup_mf.width != 16:
        raise ValueError("MF setup must be exactly 16 bits")
    if setup_px is not None and setup_px.width != 8:
        raise ValueError("PX setup must be exactly eight bits")
    if isinstance(pm_read_data, ExactWord) and pm_read_data.width != 24:
        raise ValueError("PM read data must be exactly 24 bits")
    if (
        isinstance(next_fetch_address, ExactWord)
        and next_fetch_address.width != 14
    ):
        raise ValueError("next fetch address must be exactly 14 bits")

    class_valid = is_compute_pm_class(opcode)
    reason = compute_pm_unsupported_reason(opcode)
    action = decode_compute_pm(opcode)
    setups = (
        setup_astat,
        setup_mstat,
        setup_dreg,
        setup_af,
        setup_mf,
        setup_dag,
        setup_px,
    )
    setup_count = sum(value is not None for value in setups)

    if reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        reset_state = ComputePMState(
            primary=ComputationalBank(),
            alternate=ComputationalBank(),
            status=status,
            dag=DAGRegisterState(),
            px=UNKNOWN,
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
        completed = replace(state, recovery=None) if pm_cycle_complete else state
        return ComputePMCycleResult(
            state=completed,
            action=action,
            unsupported_reason=reason,
            class_valid=class_valid,
            action_valid=action is not None,
            unsupported_subencoding=class_valid and action is None,
            instruction_complete=pm_cycle_complete,
            transaction_active=True,
            held_transaction=True,
            busy=not pm_cycle_complete,
            integration_conflict=conflict,
            pm_select=True,
            pm_read=True,
            pm_address=(
                recovery.next_fetch_address.value if address_known else 0
            ),
            pm_address_known=address_known,
            recovery_fetch=True,
            fetched_instruction=pm_read_data.value if fetched_known else 0,
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
                held_transaction=True,
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
                recovery=ComputePMRecovery(pending.next_fetch_address),
            )
        completed = _data_result(
            committed,
            pending.prepared,
            pm_read_data=pm_read_data,
            recovery_required=pending.recovery_required,
            boundary_valid=False,
            accepted=False,
            complete=True,
            held_transaction=True,
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
    if setup_af is not None or setup_mf is not None:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            alu_write=(
                None
                if setup_af is None
                else ALURegisterWrite(True, setup_af)
            ),
            mac_write=(
                None
                if setup_mf is None
                else MACRegisterWrite(True, ExactWord(40, setup_mf.value << 16))
            ),
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
                recovery=ComputePMRecovery(next_fetch_address),
            )
    else:
        committed = replace(
            state,
            pending=ComputePMPending(
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
