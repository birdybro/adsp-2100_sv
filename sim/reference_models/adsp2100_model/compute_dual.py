"""Independent original ADSP-2100 Type 1 action decoder.

Type 1 performs an unconditional ALU/MAC operation, or the documented
AMF-zero no-operation, together with one DAG1 data-memory read and one DAG2
program-memory read.  This module deliberately stops at the source-closed
parallel-action boundary; cache recovery and simultaneous native-bus wait
behavior remain separate integration work.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .alu import ALUResult
from .compute_move import (
    ALU_X_DREG,
    MAC_X_DREG,
    _invalidate_compute_result,
    _invalidate_dreg,
    _known_alu_result,
    _known_mac_result,
)
from .dag import compute_dag, reverse_address
from .mac import MACResult
from .model import ComputationalBank, ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup, DAGRegisterState, _apply_setup
from .registers import DREG
from .registers import (
    ALURegisterWrite,
    DREGWrite,
    MACRegisterWrite,
    apply_computational_cycle,
    apply_dreg_cycle,
)
from .status import (
    ALUStatusUpdate,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
)


COMPUTE_DUAL_CLASS_MASK = 0xC00000
COMPUTE_DUAL_CLASS_VALUE = 0xC00000


@dataclass(frozen=True)
class ComputeDualAction:
    pm_destination: DREG
    dm_destination: DREG
    amf: int
    yop: int
    xop: int
    pm_i_local: int
    pm_m_local: int
    dm_i_local: int
    dm_m_local: int
    pm_i_address: int
    pm_m_address: int
    dm_i_address: int
    dm_m_address: int

    @property
    def computation_enabled(self) -> bool:
        return self.amf != 0

    @property
    def is_mac(self) -> bool:
        return self.computation_enabled and self.amf < 0x10

    @property
    def destination_feedback(self) -> bool:
        """Type 1 forces a computation result to AR or MR, never AF or MF."""

        return False

    @property
    def computation_destination(self) -> str | None:
        if not self.computation_enabled:
            return None
        return "MR" if self.is_mac else "AR"

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


def is_compute_dual_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & COMPUTE_DUAL_CLASS_MASK == COMPUTE_DUAL_CLASS_VALUE


def decode_compute_dual(opcode: int) -> ComputeDualAction | None:
    """Decode every field-defined Type 1 word.

    PD and DD select disjoint Y- and X-input register sets, while the implicit
    computation destination is AR or MR.  The primary format therefore has no
    same-destination collision partition.
    """

    if not is_compute_dual_class(opcode):
        return None
    pm_i_local = (opcode >> 6) & 3
    pm_m_local = (opcode >> 4) & 3
    dm_i_local = (opcode >> 2) & 3
    dm_m_local = opcode & 3
    return ComputeDualAction(
        pm_destination=DREG(int(DREG.AY0) + ((opcode >> 20) & 3)),
        dm_destination=DREG((opcode >> 18) & 3),
        amf=(opcode >> 13) & 0x1F,
        yop=(opcode >> 11) & 3,
        xop=(opcode >> 8) & 7,
        pm_i_local=pm_i_local,
        pm_m_local=pm_m_local,
        dm_i_local=dm_i_local,
        dm_m_local=dm_m_local,
        pm_i_address=4 | pm_i_local,
        pm_m_address=4 | pm_m_local,
        dm_i_address=dm_i_local,
        dm_m_address=dm_m_local,
    )


@dataclass(frozen=True)
class ComputeDualPending:
    """Cycle-start Type 1 values retained to one logical completion."""

    action: ComputeDualAction
    dm_address: ExactWord | object
    pm_address: ExactWord | object
    dm_next_i: int | None
    pm_next_i: int | None
    dm_dag_configuration_valid: bool
    pm_dag_configuration_valid: bool
    compute_result: ALUResult | MACResult | None


@dataclass(frozen=True)
class ComputeDualState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    dag: DAGRegisterState = field(default_factory=DAGRegisterState)
    px: ExactWord | object = UNKNOWN
    pending: ComputeDualPending | None = None

    @classmethod
    def reset(cls) -> "ComputeDualState":
        return cls()


@dataclass(frozen=True)
class ComputeDualCycleResult:
    state: ComputeDualState
    action: ComputeDualAction | None = None
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
    dm_address: int = 0
    dm_address_known: bool = False
    pm_select: bool = False
    pm_data_access: bool = False
    pm_read: bool = False
    pm_address: int = 0
    pm_address_known: bool = False
    active_computation_enabled: bool = False
    active_is_mac: bool = False
    compute_result_known: bool = False
    dm_dag_configuration_valid: bool = False
    pm_dag_configuration_valid: bool = False
    dm_i_write: bool = False
    dm_i_write_known: bool = False
    pm_i_write: bool = False
    pm_i_write_known: bool = False
    dm_dreg_write: bool = False
    dm_dreg_write_known: bool = False
    pm_dreg_write: bool = False
    pm_dreg_write_known: bool = False
    px_write: bool = False
    px_write_known: bool = False
    alu_write: bool = False
    mac_write: bool = False
    alu_status_write: bool = False
    mac_status_write: bool = False
    alu_result: int = 0
    mac_result: int = 0


@dataclass(frozen=True)
class _ComputeStateView:
    primary: ComputationalBank
    alternate: ComputationalBank
    status: StatusRegisters


def _selected_bank(state: ComputeDualState) -> ComputationalBank:
    return state.alternate if state.status.alternate_bank else state.primary


def _replace_selected_bank(
    state: ComputeDualState,
    bank: ComputationalBank,
) -> ComputeDualState:
    if state.status.alternate_bank:
        return replace(state, alternate=bank)
    return replace(state, primary=bank)


def _replace_i_pair(
    dag: DAGRegisterState,
    dm_address: int,
    dm_value: int | None,
    pm_address: int,
    pm_value: int | None,
) -> DAGRegisterState:
    values = list(dag.i)
    values[dm_address] = dm_value
    values[pm_address] = pm_value
    return DAGRegisterState(tuple(values), dag.m, dag.l)


def _prepare_dag(
    state: ComputeDualState,
    *,
    i_address: int,
    m_address: int,
    dag1: bool,
) -> tuple[ExactWord | object, int | None, bool]:
    old_i = state.dag.i[i_address]
    m_value = state.dag.m[m_address]
    l_value = state.dag.l[i_address]
    address: ExactWord | object = UNKNOWN
    next_i: int | None = None
    configuration_valid = False
    if old_i is not None:
        address_value = (
            reverse_address(old_i)
            if dag1 and bool(state.status.mstat.value & 0x2)
            else old_i
        )
        address = ExactWord(14, address_value)
    if old_i is not None and m_value is not None and l_value is not None:
        result = compute_dag(
            old_i,
            m_value,
            l_value,
            dag1=dag1,
            bit_reverse_enabled=(
                dag1 and bool(state.status.mstat.value & 0x2)
            ),
        )
        address = ExactWord(14, result.address)
        configuration_valid = result.configuration_valid
        if configuration_valid:
            next_i = result.next_i
    return address, next_i, configuration_valid


def _pending_from_state(
    state: ComputeDualState,
    action: ComputeDualAction,
) -> ComputeDualPending:
    dm_address, dm_next_i, dm_valid = _prepare_dag(
        state,
        i_address=action.dm_i_address,
        m_address=action.dm_m_address,
        dag1=True,
    )
    pm_address, pm_next_i, pm_valid = _prepare_dag(
        state,
        i_address=action.pm_i_address,
        m_address=action.pm_m_address,
        dag1=False,
    )
    view = _ComputeStateView(state.primary, state.alternate, state.status)
    compute_result: ALUResult | MACResult | None = None
    if action.computation_enabled:
        compute_result = (
            _known_mac_result(view, action)
            if action.is_mac
            else _known_alu_result(view, action)
        )
    return ComputeDualPending(
        action=action,
        dm_address=dm_address,
        pm_address=pm_address,
        dm_next_i=dm_next_i,
        pm_next_i=pm_next_i,
        dm_dag_configuration_valid=dm_valid,
        pm_dag_configuration_valid=pm_valid,
        compute_result=compute_result,
    )


def _complete_pending(
    state: ComputeDualState,
    pending: ComputeDualPending,
    dm_read_data: ExactWord | object,
    pm_read_data: ExactWord | object,
) -> ComputeDualState:
    if isinstance(dm_read_data, ExactWord) and dm_read_data.width != 16:
        raise ValueError("DM read data must be exactly 16 bits")
    if isinstance(pm_read_data, ExactWord) and pm_read_data.width != 24:
        raise ValueError("PM read data must be exactly 24 bits")

    action = pending.action
    writes: list[DREGWrite] = []
    if isinstance(dm_read_data, ExactWord):
        writes.append(DREGWrite(action.dm_destination, dm_read_data))
    if isinstance(pm_read_data, ExactWord):
        writes.append(
            DREGWrite(
                action.pm_destination,
                ExactWord(16, pm_read_data.value >> 8),
            )
        )

    alu_write = None
    mac_write = None
    status_inputs = StatusCycleInputs()
    compute = pending.compute_result
    if isinstance(compute, ALUResult):
        alu_write = ALURegisterWrite(
            False,
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
        mac_write = MACRegisterWrite(False, ExactWord(40, compute.result))
        status_inputs = StatusCycleInputs(mac_mv=compute.mv)

    registers = apply_computational_cycle(
        state.primary,
        state.alternate,
        alternate_selected=state.status.alternate_bank,
        dreg_writes=tuple(writes),
        alu_write=alu_write,
        mac_write=mac_write,
    )
    updated = replace(
        state,
        primary=registers.primary,
        alternate=registers.alternate,
        status=apply_status_cycle(state.status, status_inputs).state,
    )
    if action.computation_enabled and compute is None:
        invalid = _invalidate_compute_result(updated, action)
        updated = replace(
            updated,
            primary=invalid.primary,
            alternate=invalid.alternate,
            status=invalid.status,
        )
    if not isinstance(dm_read_data, ExactWord):
        updated = _replace_selected_bank(
            updated,
            _invalidate_dreg(_selected_bank(updated), action.dm_destination),
        )
    if not isinstance(pm_read_data, ExactWord):
        updated = _replace_selected_bank(
            updated,
            _invalidate_dreg(_selected_bank(updated), action.pm_destination),
        )

    px: ExactWord | object = (
        ExactWord(8, pm_read_data.value & 0xFF)
        if isinstance(pm_read_data, ExactWord)
        else UNKNOWN
    )
    dag = _replace_i_pair(
        updated.dag,
        action.dm_i_address,
        pending.dm_next_i,
        action.pm_i_address,
        pending.pm_next_i,
    )
    return replace(updated, dag=dag, px=px, pending=None)


def _result(
    state: ComputeDualState,
    pending: ComputeDualPending | None,
    *,
    action: ComputeDualAction | None,
    class_valid: bool,
    boundary_valid: bool = False,
    accepted: bool = False,
    complete: bool = False,
    stalled: bool = False,
    invalid: bool = False,
    conflict: bool = False,
    dm_read_known: bool = False,
    pm_read_known: bool = False,
) -> ComputeDualCycleResult:
    active = pending is not None
    current_action = pending.action if pending is not None else action
    dm_address_known = (
        pending is not None and isinstance(pending.dm_address, ExactWord)
    )
    pm_address_known = (
        pending is not None and isinstance(pending.pm_address, ExactWord)
    )
    compute = pending.compute_result if pending is not None else None
    computation_enabled = bool(
        current_action is not None and current_action.computation_enabled
    )
    is_mac = bool(current_action is not None and current_action.is_mac)
    return ComputeDualCycleResult(
        state=state,
        action=action,
        class_valid=class_valid,
        action_valid=action is not None,
        boundary_valid=boundary_valid,
        accepted=accepted,
        instruction_complete=complete,
        transaction_active=active,
        stalled=stalled,
        busy=state.pending is not None,
        invalid_opcode=invalid,
        integration_conflict=conflict,
        dm_select=active,
        dm_read=active,
        dm_address=(pending.dm_address.value if dm_address_known else 0),
        dm_address_known=dm_address_known,
        pm_select=active,
        pm_data_access=active,
        pm_read=active,
        pm_address=(pending.pm_address.value if pm_address_known else 0),
        pm_address_known=pm_address_known,
        active_computation_enabled=computation_enabled,
        active_is_mac=is_mac,
        compute_result_known=computation_enabled and compute is not None,
        dm_dag_configuration_valid=(
            pending is not None and pending.dm_dag_configuration_valid
        ),
        pm_dag_configuration_valid=(
            pending is not None and pending.pm_dag_configuration_valid
        ),
        dm_i_write=complete,
        dm_i_write_known=(
            complete and pending is not None and pending.dm_next_i is not None
        ),
        pm_i_write=complete,
        pm_i_write_known=(
            complete and pending is not None and pending.pm_next_i is not None
        ),
        dm_dreg_write=complete,
        dm_dreg_write_known=complete and dm_read_known,
        pm_dreg_write=complete,
        pm_dreg_write_known=complete and pm_read_known,
        px_write=complete,
        px_write_known=complete and pm_read_known,
        alu_write=complete and computation_enabled and not is_mac,
        mac_write=complete and computation_enabled and is_mac,
        alu_status_write=complete and computation_enabled and not is_mac,
        mac_status_write=complete and computation_enabled and is_mac,
        alu_result=(
            compute.destination_result if isinstance(compute, ALUResult) else 0
        ),
        mac_result=(compute.result if isinstance(compute, MACResult) else 0),
    )


def apply_compute_dual_cycle(
    state: ComputeDualState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    transaction_complete: bool = False,
    dm_read_data: ExactWord | object = UNKNOWN,
    pm_read_data: ExactWord | object = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    setup_px: ExactWord | None = None,
    inspect_probe: bool = False,
) -> ComputeDualCycleResult:
    """Apply one bounded logical Type 1 transaction or setup cycle.

    ``transaction_complete`` is deliberately an implementation/test boundary.
    It does not specify native PM pin behavior while DMACK extends state seven;
    that external timing question remains OQ-023.
    """

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
    if isinstance(dm_read_data, ExactWord) and dm_read_data.width != 16:
        raise ValueError("DM read data must be exactly 16 bits")
    if isinstance(pm_read_data, ExactWord) and pm_read_data.width != 24:
        raise ValueError("PM read data must be exactly 24 bits")

    class_valid = is_compute_dual_class(opcode)
    action = decode_compute_dual(opcode)
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
        reset_state = ComputeDualState(status=status)
        return _result(
            reset_state,
            None,
            action=action,
            class_valid=class_valid,
        )

    if state.pending is not None:
        conflict = execute or setup_count != 0
        pending = state.pending
        if not transaction_complete:
            return _result(
                state,
                pending,
                action=action,
                class_valid=class_valid,
                stalled=True,
                conflict=conflict,
            )
        completed = _complete_pending(
            state,
            pending,
            dm_read_data,
            pm_read_data,
        )
        result = _result(
            completed,
            pending,
            action=action,
            class_valid=class_valid,
            complete=True,
            conflict=conflict,
            dm_read_known=isinstance(dm_read_data, ExactWord),
            pm_read_known=isinstance(pm_read_data, ExactWord),
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
            class_valid=class_valid,
        )
    if setup_dag is not None:
        return _result(
            replace(state, dag=_apply_setup(state.dag, setup_dag)),
            None,
            action=action,
            class_valid=class_valid,
        )
    if setup_px is not None:
        return _result(
            replace(state, px=setup_px),
            None,
            action=action,
            class_valid=class_valid,
        )
    if not execute:
        return _result(
            state,
            None,
            action=action,
            class_valid=class_valid,
        )

    assert action is not None
    pending = _pending_from_state(state, action)
    issued = replace(state, pending=pending)
    if not transaction_complete:
        return _result(
            issued,
            pending,
            action=action,
            class_valid=class_valid,
            boundary_valid=True,
            accepted=True,
            stalled=True,
        )
    completed = _complete_pending(
        issued,
        pending,
        dm_read_data,
        pm_read_data,
    )
    result = _result(
        completed,
        pending,
        action=action,
        class_valid=class_valid,
        boundary_valid=True,
        accepted=True,
        complete=True,
        dm_read_known=isinstance(dm_read_data, ExactWord),
        pm_read_known=isinstance(pm_read_data, ExactWord),
    )
    return replace(result, busy=False)
