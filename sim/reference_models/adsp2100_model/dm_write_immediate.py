"""Independent original ADSP-2100 Type 2 action decoder."""

from __future__ import annotations

from dataclasses import dataclass


DM_WRITE_IMMEDIATE_MASK = 0xE00000
DM_WRITE_IMMEDIATE_VALUE = 0xA00000


@dataclass(frozen=True)
class DMWriteImmediateAction:
    immediate: int
    dag: int
    i_local: int
    m_local: int
    i_address: int
    m_address: int
    l_address: int


def decode_dm_write_immediate(opcode: int) -> DMWriteImmediateAction | None:
    """Decode every field-defined original Type 2 word.

    Type 2 has no reserved payload bits: G selects one complete DAG, DATA is
    the sixteen-bit value driven on DMD, and I/M select registers within that
    DAG.  Transaction timing and DAG writeback are intentionally outside this
    action-only decoder.
    """

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if opcode & DM_WRITE_IMMEDIATE_MASK != DM_WRITE_IMMEDIATE_VALUE:
        return None
    dag = (opcode >> 20) & 1
    i_local = (opcode >> 2) & 3
    m_local = opcode & 3
    i_address = (dag << 2) | i_local
    return DMWriteImmediateAction(
        immediate=(opcode >> 4) & 0xFFFF,
        dag=dag,
        i_local=i_local,
        m_local=m_local,
        i_address=i_address,
        m_address=(dag << 2) | m_local,
        l_address=i_address,
    )
