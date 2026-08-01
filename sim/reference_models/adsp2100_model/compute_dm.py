"""Independent action decoder for original ADSP-2100 Type 4.

This module closes field legality and parallel-action selection only.  The
waited execution transaction is deliberately left to a later, separately
verified state model.
"""

from __future__ import annotations

from dataclasses import dataclass

from .compute_move import ALU_X_DREG, MAC_X_DREG
from .registers import DREG


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
