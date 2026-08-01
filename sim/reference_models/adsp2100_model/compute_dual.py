"""Independent original ADSP-2100 Type 1 action decoder.

Type 1 performs an unconditional ALU/MAC operation, or the documented
AMF-zero no-operation, together with one DAG1 data-memory read and one DAG2
program-memory read.  This module deliberately stops at the source-closed
parallel-action boundary; cache recovery and simultaneous native-bus wait
behavior remain separate integration work.
"""

from __future__ import annotations

from dataclasses import dataclass

from .compute_move import ALU_X_DREG, MAC_X_DREG
from .registers import DREG


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
