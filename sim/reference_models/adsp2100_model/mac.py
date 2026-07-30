"""Exact-width original ADSP-2100 multiplier/accumulator model."""

from __future__ import annotations

from dataclasses import dataclass


WORD_MASK = 0xFFFF
MR_MASK = (1 << 40) - 1
POSITIVE_SATURATION = 0x007FFFFFFF
NEGATIVE_SATURATION = 0xFF80000000


@dataclass(frozen=True)
class MACResult:
    aligned_product: int
    unrounded_result: int
    result: int
    mf_result: int
    mv: bool
    rounded: bool


def _require_width(value: int, width: int, name: str) -> None:
    if not 0 <= value < (1 << width):
        raise ValueError(f"{name} must fit {width} bits")


def _signed_word(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def _round_to_even(value: int) -> int:
    lower = value & WORD_MASK
    upper = value >> 16
    increment = lower > 0x8000 or (lower == 0x8000 and bool(upper & 1))
    return (((upper + int(increment)) & 0xFFFFFF) << 16) & MR_MASK


def _mac_overflow(value: int) -> bool:
    upper_nine = (value >> 31) & 0x1FF
    return upper_nine not in (0x000, 0x1FF)


def saturate_mr(mr: int, mv: bool) -> int:
    """Apply the one-cycle SAT MR operation to a current MR value."""

    _require_width(mr, 40, "mr")
    if not mv:
        return mr
    return NEGATIVE_SATURATION if mr & (1 << 39) else POSITIVE_SATURATION


def compute_mac(amf: int, x: int, y: int, mr: int) -> MACResult:
    """Execute one original fractional multiply or multiply/accumulate AMF."""

    if not 0x01 <= amf <= 0x0F:
        raise ValueError("amf must select an original MAC function")
    _require_width(x, 16, "x")
    _require_width(y, 16, "y")
    _require_width(mr, 40, "mr")

    rounded = amf <= 0x03
    if rounded:
        x_signed = True
        y_signed = True
        operation = amf
    else:
        data_format = amf & 0x03
        x_signed = not bool(data_format & 0x02)
        y_signed = not bool(data_format & 0x01)
        operation = amf >> 2

    x_value = _signed_word(x) if x_signed else x
    y_value = _signed_word(y) if y_signed else y
    aligned_product = (x_value * y_value * 2) & MR_MASK

    if operation == 1:
        unrounded = aligned_product
    elif operation == 2:
        unrounded = (mr + aligned_product) & MR_MASK
    else:
        unrounded = (mr - aligned_product) & MR_MASK

    result = _round_to_even(unrounded) if rounded else unrounded
    return MACResult(
        aligned_product=aligned_product,
        unrounded_result=unrounded,
        result=result,
        mf_result=(result >> 16) & WORD_MASK,
        mv=_mac_overflow(result),
        rounded=rounded,
    )
