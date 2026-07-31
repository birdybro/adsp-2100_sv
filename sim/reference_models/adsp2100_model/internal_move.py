"""Independent original ADSP-2100 Type 17 action decode."""

from __future__ import annotations

from dataclasses import dataclass


INTERNAL_MOVE_MASK = 0xFFF000
INTERNAL_MOVE_VALUE = 0x0D0000

_REGISTER_ROWS: tuple[tuple[str | None, ...], ...] = (
    (
        "AX0", "AX1", "MX0", "MX1",
        "AY0", "AY1", "MY0", "MY1",
        "SI", "SE", "AR", "MR0",
        "MR1", "MR2", "SR0", "SR1",
    ),
    (
        "I0", "I1", "I2", "I3",
        "M0", "M1", "M2", "M3",
        "L0", "L1", "L2", "L3",
        None, None, None, None,
    ),
    (
        "I4", "I5", "I6", "I7",
        "M4", "M5", "M6", "M7",
        "L4", "L5", "L6", "L7",
        None, None, None, None,
    ),
    (
        "ASTAT", "MSTAT", "SSTAT", "IMASK",
        "ICNTL", "CNTR", "SB", "PX",
        None, None, None, None,
        None, None, None, None,
    ),
)


@dataclass(frozen=True)
class InternalMoveSelection:
    """Raw selectors and legal original-register action, if any."""

    destination_group: int
    source_group: int
    destination_index: int
    source_index: int
    destination_code: int
    source_code: int
    destination_register: str | None
    source_register: str | None
    legal: bool
    invalid_reason: str | None


def decode_internal_move(opcode: int) -> InternalMoveSelection | None:
    """Decode Type 17 and reject reserved/read-only destinations."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if opcode & INTERNAL_MOVE_MASK != INTERNAL_MOVE_VALUE:
        return None

    destination_group = (opcode >> 10) & 0x3
    source_group = (opcode >> 8) & 0x3
    destination_index = (opcode >> 4) & 0xF
    source_index = opcode & 0xF
    destination_register = _REGISTER_ROWS[destination_group][
        destination_index
    ]
    source_register = _REGISTER_ROWS[source_group][source_index]

    invalid_reason: str | None = None
    if source_register is None:
        invalid_reason = "RESERVED_SOURCE_SELECTOR"
    elif destination_register is None:
        invalid_reason = "RESERVED_DESTINATION_SELECTOR"
    elif destination_register == "SSTAT":
        invalid_reason = "READ_ONLY_SSTAT_DESTINATION"

    return InternalMoveSelection(
        destination_group=destination_group,
        source_group=source_group,
        destination_index=destination_index,
        source_index=source_index,
        destination_code=(destination_group << 4) | destination_index,
        source_code=(source_group << 4) | source_index,
        destination_register=destination_register,
        source_register=source_register,
        legal=invalid_reason is None,
        invalid_reason=invalid_reason,
    )


def register_code_by_name(*, writable: bool) -> dict[str, int]:
    """Return independently transcribed source or destination name mapping."""

    result: dict[str, int] = {}
    for group, row in enumerate(_REGISTER_ROWS):
        for index, register in enumerate(row):
            if register is None:
                continue
            if writable and register == "SSTAT":
                continue
            result[register] = (group << 4) | index
    return result
