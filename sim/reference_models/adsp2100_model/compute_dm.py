"""Independent original ADSP-2100 Type 4 action and transaction model.

An accepted instruction captures its cycle-start compute, DREG, and DAG
inputs.  DMACK-low clocks preserve both the descriptor and architectural
state.  The first acknowledged clock commits the computation, optional DM
read, status update, and I-register post-modification atomically.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .alu import ALUResult
from .compute_move import (
    ALU_X_DREG,
    MAC_X_DREG,
    _apply_actions,
    _invalidate_compute_result,
    _invalidate_dreg,
    _known_alu_result,
    _known_mac_result,
)
from .dag import compute_dag, reverse_address
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


COMPUTE_DM_CLASS_MASK = 0xE00000
COMPUTE_DM_CLASS_VALUE = 0x600000


@dataclass(frozen=True)
class ComputeDMAction:
    dag: int
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


def is_compute_dm_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & COMPUTE_DM_CLASS_MASK == COMPUTE_DM_CLASS_VALUE


def _destination_collision(
    *, write: bool, z: int, amf: int, destination: DREG
) -> bool:
    if write or z or amf == 0:
        return False
    if amf >= 0x10:
        return destination == DREG.AR
    return destination in (DREG.MR0, DREG.MR1, DREG.MR2)


def compute_dm_unsupported_reason(opcode: int) -> str | None:
    if not is_compute_dm_class(opcode):
        return None
    if _destination_collision(
        write=bool((opcode >> 19) & 1),
        z=(opcode >> 18) & 1,
        amf=(opcode >> 13) & 0x1F,
        destination=DREG((opcode >> 4) & 0xF),
    ):
        return "UNSUPPORTED_DESTINATION_COLLISION"
    return None


def decode_compute_dm(opcode: int) -> ComputeDMAction | None:
    if not is_compute_dm_class(opcode):
        return None
    if compute_dm_unsupported_reason(opcode) is not None:
        return None
    dag = (opcode >> 20) & 1
    return ComputeDMAction(
        dag=dag,
        write=bool((opcode >> 19) & 1),
        z=(opcode >> 18) & 1,
        amf=(opcode >> 13) & 0x1F,
        yop=(opcode >> 11) & 3,
        xop=(opcode >> 8) & 7,
        memory_dreg=DREG((opcode >> 4) & 0xF),
        i_local=(opcode >> 2) & 3,
        m_local=opcode & 3,
        i_address=(dag << 2) | ((opcode >> 2) & 3),
        m_address=(dag << 2) | (opcode & 3),
    )


@dataclass(frozen=True)
class ComputeDMPending:
    action: ComputeDMAction
    address: ExactWord | object
    write_data: ExactWord | object
    next_i: int | None
    dag_configuration_valid: bool
    compute_result: ALUResult | MACResult | None


@dataclass(frozen=True)
class ComputeDMState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    dag: DAGRegisterState = field(default_factory=DAGRegisterState)
    pending: ComputeDMPending | None = None

    @classmethod
    def reset(cls) -> "ComputeDMState":
        return cls()


@dataclass(frozen=True)
class ComputeDMCycleResult:
    state: ComputeDMState
    action: ComputeDMAction | None = None
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
    active_computation_enabled: bool = False
    active_is_mac: bool = False
    compute_result_known: bool = False
    dag_configuration_valid: bool = False
    i_write: bool = False
    i_write_known: bool = False
    dreg_write: bool = False
    dreg_write_known: bool = False
    alu_write: bool = False
    mac_write: bool = False
    alu_status_write: bool = False
    mac_status_write: bool = False
    alu_result: int = 0
    mac_result: int = 0
    pm_data_access: bool = False
    dm_access: bool = False


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


def _selected_bank(state: ComputeDMState) -> ComputationalBank:
    return state.alternate if state.status.alternate_bank else state.primary


def _replace_selected_bank(
    state: ComputeDMState,
    bank: ComputationalBank,
) -> ComputeDMState:
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


def _pending_from_state(
    state: ComputeDMState,
    action: ComputeDMAction,
) -> ComputeDMPending:
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

    bank = _selected_bank(state)
    memory_source = read_dreg(bank, action.memory_dreg)
    write_data = (
        memory_source
        if action.write and isinstance(memory_source, ExactWord)
        else UNKNOWN
    )
    view = _ComputeStateView(state.primary, state.alternate, state.status)
    compute_result: ALUResult | MACResult | None = None
    if action.computation_enabled:
        compute_result = (
            _known_mac_result(view, action)
            if action.is_mac
            else _known_alu_result(view, action)
        )
    return ComputeDMPending(
        action,
        address,
        write_data,
        next_i,
        configuration_valid,
        compute_result,
    )


def _commit_compute_write(
    state: ComputeDMState,
    action: ComputeDMAction,
    compute: ALUResult | MACResult | None,
) -> ComputeDMState:
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
    updated = ComputeDMState(
        registers.primary,
        registers.alternate,
        status,
        state.dag,
        state.pending,
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


def _complete_pending(
    state: ComputeDMState,
    pending: ComputeDMPending,
    dm_read_data: ExactWord | object,
) -> ComputeDMState:
    action = pending.action
    updated = state
    move_data = (
        dm_read_data
        if not action.write and isinstance(dm_read_data, ExactWord)
        else None
    )
    if isinstance(dm_read_data, ExactWord) and dm_read_data.width != 16:
        raise ValueError("DM read data must be exactly 16 bits")

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
            pending.compute_result,
        )
        updated = replace(
            updated,
            primary=committed.primary,
            alternate=committed.alternate,
            status=committed.status,
        )
    elif action.computation_enabled:
        updated = _commit_compute_write(updated, action, pending.compute_result)
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

    dag = _replace_i(updated.dag, action.i_address, pending.next_i)
    return replace(updated, dag=dag, pending=None)


def _result(
    state: ComputeDMState,
    pending: ComputeDMPending | None,
    *,
    action: ComputeDMAction | None,
    unsupported_reason: str | None,
    class_valid: bool,
    boundary_valid: bool = False,
    accepted: bool = False,
    complete: bool = False,
    stalled: bool = False,
    invalid: bool = False,
    conflict: bool = False,
    read_data_known: bool = False,
) -> ComputeDMCycleResult:
    active = pending is not None
    current_action = pending.action if pending is not None else action
    address_known = pending is not None and isinstance(pending.address, ExactWord)
    write_known = pending is not None and isinstance(pending.write_data, ExactWord)
    compute = None if pending is None else pending.compute_result
    computation_enabled = (
        current_action is not None and current_action.computation_enabled
    )
    is_mac = current_action is not None and current_action.is_mac
    return ComputeDMCycleResult(
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
        dm_read=active and current_action is not None and not current_action.write,
        dm_write=active and current_action is not None and current_action.write,
        dm_address=(pending.address.value if address_known else 0),
        dm_address_known=address_known,
        dm_write_data=(pending.write_data.value if write_known else 0),
        dm_write_data_known=write_known,
        active_computation_enabled=computation_enabled,
        active_is_mac=is_mac,
        compute_result_known=computation_enabled and compute is not None,
        dag_configuration_valid=(
            pending is not None and pending.dag_configuration_valid
        ),
        i_write=complete,
        i_write_known=complete and pending is not None and pending.next_i is not None,
        dreg_write=(
            complete and current_action is not None and not current_action.write
        ),
        dreg_write_known=(
            complete and current_action is not None and not current_action.write
            and read_data_known
        ),
        alu_write=complete and computation_enabled and not is_mac,
        mac_write=complete and computation_enabled and is_mac,
        alu_status_write=complete and computation_enabled and not is_mac,
        mac_status_write=complete and computation_enabled and is_mac,
        alu_result=(
            compute.destination_result if isinstance(compute, ALUResult) else 0
        ),
        mac_result=(compute.result if isinstance(compute, MACResult) else 0),
        pm_data_access=False,
        dm_access=active,
    )


def apply_compute_dm_cycle(
    state: ComputeDMState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    dm_ack: bool = False,
    dm_read_data: ExactWord | object = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    inspect_probe: bool = False,
) -> ComputeDMCycleResult:
    """Apply one setup, accepted Type 4 transaction, wait, or completion."""

    if setup_astat is not None and setup_astat.width != 8:
        raise ValueError("ASTAT setup must be exactly eight bits")
    if setup_mstat is not None and setup_mstat.width != 4:
        raise ValueError("MSTAT setup must be exactly four bits")
    if setup_af is not None and setup_af.width != 16:
        raise ValueError("AF setup must be exactly 16 bits")
    if setup_mf is not None and setup_mf.width != 16:
        raise ValueError("MF setup must be exactly 16 bits")
    if isinstance(dm_read_data, ExactWord) and dm_read_data.width != 16:
        raise ValueError("DM read data must be exactly 16 bits")

    class_valid = is_compute_dm_class(opcode)
    reason = compute_dm_unsupported_reason(opcode)
    action = decode_compute_dm(opcode)
    setups = (
        setup_astat,
        setup_mstat,
        setup_dreg,
        setup_af,
        setup_mf,
        setup_dag,
    )
    setup_count = sum(value is not None for value in setups)

    if reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        reset_state = ComputeDMState(
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
        conflict = execute or setup_count != 0
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

    conflict = (
        (execute and (setup_count != 0 or inspect_probe))
        or setup_count > 1
    )
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
            replace(
                state,
                primary=registers.primary,
                alternate=registers.alternate,
            ),
            None,
            action=action,
            unsupported_reason=reason,
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
        return _result(
            replace(
                state,
                primary=registers.primary,
                alternate=registers.alternate,
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
