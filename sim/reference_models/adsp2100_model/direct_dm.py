"""Independent original ADSP-2100 Type 3 direct-DM action decoder."""

from __future__ import annotations

from dataclasses import dataclass

from .internal_move import register_code_by_name


DIRECT_DM_MASK = 0xE00000
DIRECT_DM_VALUE = 0x800000


@dataclass(frozen=True)
class DirectDMAction:
    """Raw direct-DM fields plus the legal register action, if any."""

    write: bool
    address: int
    register_group: int
    register_index: int
    register_code: int
    register: str | None
    legal: bool
    invalid_reason: str | None


def decode_direct_dm(opcode: int) -> DirectDMAction | None:
    """Decode Type 3 without assigning behavior to blank REG selectors."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if opcode & DIRECT_DM_MASK != DIRECT_DM_VALUE:
        return None

    write = bool((opcode >> 20) & 1)
    register_group = (opcode >> 18) & 0x3
    register_index = opcode & 0xF
    register_code = (register_group << 4) | register_index
    readable = register_code_by_name(writable=False)
    writable = register_code_by_name(writable=True)
    source_by_code = {code: name for name, code in readable.items()}
    destination_by_code = {code: name for name, code in writable.items()}

    invalid_reason: str | None = None
    if write:
        register = source_by_code.get(register_code)
        if register is None:
            invalid_reason = "RESERVED_SOURCE_SELECTOR"
    else:
        register = destination_by_code.get(register_code)
        if register is None:
            if source_by_code.get(register_code) == "SSTAT":
                invalid_reason = "READ_ONLY_SSTAT_DESTINATION"
                register = "SSTAT"
            else:
                invalid_reason = "RESERVED_DESTINATION_SELECTOR"

    return DirectDMAction(
        write=write,
        address=(opcode >> 4) & 0x3FFF,
        register_group=register_group,
        register_index=register_index,
        register_code=register_code,
        register=register,
        legal=invalid_reason is None,
        invalid_reason=invalid_reason,
    )
