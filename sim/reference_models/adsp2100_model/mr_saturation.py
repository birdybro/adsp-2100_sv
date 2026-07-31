"""Independent exact decoder for original ADSP-2100 Type 25."""

from __future__ import annotations


MR_SATURATION_OPCODE = 0x050000


def decode_mr_saturation(opcode: int) -> bool:
    """Return true only for the source-verified exact Type 25 word."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode == MR_SATURATION_OPCODE
