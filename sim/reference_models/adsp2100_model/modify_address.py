"""Independent original ADSP-2100 Type 21 MODIFY semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .dag import ADDRESS_MASK, compute_dag


MODIFY_ADDRESS_MASK = 0xFFFFE0
MODIFY_ADDRESS_VALUE = 0x090000
_UNKNOWN_DAG_REGISTERS = (None,) * 8


class DAGRegisterKind(IntEnum):
    I = 0
    M = 1
    L = 2


def _validate_register_value(value: int | None, name: str) -> None:
    if value is not None and not 0 <= value <= ADDRESS_MASK:
        raise ValueError(f"{name} must fit 14 bits")


def _validate_register_tuple(
    values: tuple[int | None, ...],
    name: str,
) -> None:
    if len(values) != 8:
        raise ValueError(f"{name} must contain exactly eight registers")
    for value in values:
        _validate_register_value(value, name)


@dataclass(frozen=True)
class DAGRegisterState:
    """All original I/M/L registers with authentic reset unknowns."""

    i: tuple[int | None, ...] = _UNKNOWN_DAG_REGISTERS
    m: tuple[int | None, ...] = _UNKNOWN_DAG_REGISTERS
    l: tuple[int | None, ...] = _UNKNOWN_DAG_REGISTERS

    def __post_init__(self) -> None:
        _validate_register_tuple(self.i, "I registers")
        _validate_register_tuple(self.m, "M registers")
        _validate_register_tuple(self.l, "L registers")


@dataclass(frozen=True)
class DAGRegisterSetup:
    kind: DAGRegisterKind
    address: int
    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", DAGRegisterKind(self.kind))
        if not 0 <= self.address < 8:
            raise ValueError("DAG register address must be in range 0..7")
        _validate_register_value(self.value, "DAG register setup value")


@dataclass(frozen=True)
class ModifyAddressSelection:
    dag: int
    i_local: int
    m_local: int
    i_address: int
    m_address: int


@dataclass(frozen=True)
class ModifyAddressCycleResult:
    state: DAGRegisterState
    selection: ModifyAddressSelection | None = None
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    operands_valid: bool = False
    configuration_valid: bool = False
    writeback_valid: bool = False
    old_i: int = 0
    m_value: int = 0
    l_value: int = 0
    next_i: int = 0
    pm_data_access: bool = False
    dm_access: bool = False


def decode_modify_address(opcode: int) -> ModifyAddressSelection | None:
    """Decode all 32 original Type 21 G/I/M selections."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if opcode & MODIFY_ADDRESS_MASK != MODIFY_ADDRESS_VALUE:
        return None
    dag = (opcode >> 4) & 0x1
    i_local = (opcode >> 2) & 0x3
    m_local = opcode & 0x3
    return ModifyAddressSelection(
        dag=dag,
        i_local=i_local,
        m_local=m_local,
        i_address=(dag << 2) | i_local,
        m_address=(dag << 2) | m_local,
    )


def _replace_register(
    values: tuple[int | None, ...],
    address: int,
    value: int | None,
) -> tuple[int | None, ...]:
    updated = list(values)
    updated[address] = value
    return tuple(updated)


def _apply_setup(
    state: DAGRegisterState,
    setup: DAGRegisterSetup,
) -> DAGRegisterState:
    if setup.kind is DAGRegisterKind.I:
        return DAGRegisterState(
            i=_replace_register(state.i, setup.address, setup.value),
            m=state.m,
            l=state.l,
        )
    if setup.kind is DAGRegisterKind.M:
        return DAGRegisterState(
            i=state.i,
            m=_replace_register(state.m, setup.address, setup.value),
            l=state.l,
        )
    return DAGRegisterState(
        i=state.i,
        m=state.m,
        l=_replace_register(state.l, setup.address, setup.value),
    )


def apply_modify_address_cycle(
    state: DAGRegisterState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup: DAGRegisterSetup | None = None,
) -> ModifyAddressCycleResult:
    """Apply one bounded Type 21 or deterministic setup cycle."""

    selection = decode_modify_address(opcode)
    invalid_opcode = bool(not reset and execute and selection is None)
    integration_conflict = bool(not reset and execute and setup is not None)
    boundary_valid = bool(
        not reset
        and execute
        and selection is not None
        and setup is None
    )

    if reset:
        return ModifyAddressCycleResult(DAGRegisterState(), selection=selection)
    if integration_conflict:
        return ModifyAddressCycleResult(
            state,
            selection=selection,
            invalid_opcode=invalid_opcode,
            integration_conflict=True,
        )
    if setup is not None:
        return ModifyAddressCycleResult(
            _apply_setup(state, setup),
            selection=selection,
        )
    if not boundary_valid:
        return ModifyAddressCycleResult(
            state,
            selection=selection,
            invalid_opcode=invalid_opcode,
        )

    assert selection is not None
    old_i = state.i[selection.i_address]
    m_value = state.m[selection.m_address]
    l_value = state.l[selection.i_address]
    operands_valid = all(
        value is not None for value in (old_i, m_value, l_value)
    )
    if not operands_valid:
        next_state = DAGRegisterState(
            i=_replace_register(state.i, selection.i_address, None),
            m=state.m,
            l=state.l,
        )
        return ModifyAddressCycleResult(
            next_state,
            selection=selection,
            boundary_valid=True,
        )

    assert old_i is not None and m_value is not None and l_value is not None
    dag_result = compute_dag(
        old_i,
        m_value,
        l_value,
        dag1=selection.dag == 0,
        bit_reverse_enabled=False,
    )
    result_valid = dag_result.configuration_valid
    next_state = DAGRegisterState(
        i=_replace_register(
            state.i,
            selection.i_address,
            dag_result.next_i if result_valid else None,
        ),
        m=state.m,
        l=state.l,
    )
    return ModifyAddressCycleResult(
        next_state,
        selection=selection,
        boundary_valid=True,
        operands_valid=True,
        configuration_valid=result_valid,
        writeback_valid=result_valid,
        old_i=old_i,
        m_value=m_value,
        l_value=l_value,
        next_i=dag_result.next_i,
    )
