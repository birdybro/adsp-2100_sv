"""Exact-width original ADSP-2100 standard ALU function model."""

from __future__ import annotations

from dataclasses import dataclass


WORD_MASK = 0xFFFF
ALU_AMF_MIN = 0x10
ALU_AMF_MAX = 0x1F


@dataclass(frozen=True)
class ALUResult:
    raw_result: int
    destination_result: int
    az: bool
    an: bool
    av: bool
    ac: bool
    as_value: bool
    as_write: bool


def _require_word(value: int, name: str) -> None:
    if not 0 <= value <= WORD_MASK:
        raise ValueError(f"{name} must fit 16 bits")


def _add16(left: int, right: int, carry_in: bool) -> tuple[int, bool, bool]:
    total = left + right + int(carry_in)
    low_total = (left & 0x7FFF) + (right & 0x7FFF) + int(carry_in)
    carry_into_sign = bool((low_total >> 15) & 1)
    carry_out = bool((total >> 16) & 1)
    return total & WORD_MASK, carry_out, carry_into_sign != carry_out


def compute_alu(
    amf: int,
    x: int,
    y: int,
    *,
    carry_in: bool = False,
    previous_av: bool = False,
    sticky_av: bool = False,
    saturate_ar: bool = False,
    destination_is_ar: bool = True,
) -> ALUResult:
    """Execute one standard non-division ALU function.

    `amf` is the original five-bit Appendix A function code. MAC codes and
    division primitives are deliberately rejected.
    """

    if not ALU_AMF_MIN <= amf <= ALU_AMF_MAX:
        raise ValueError("amf must select an original standard ALU function")
    _require_word(x, "x")
    _require_word(y, "y")

    ac = False
    av_generated = False
    as_value = False
    as_write = False

    if amf == 0x10:
        raw = y
    elif amf == 0x11:
        raw, ac, av_generated = _add16(y, 0, True)
    elif amf == 0x12:
        raw, ac, av_generated = _add16(x, y, carry_in)
    elif amf == 0x13:
        raw, ac, av_generated = _add16(x, y, False)
    elif amf == 0x14:
        raw = (~y) & WORD_MASK
    elif amf == 0x15:
        raw, ac, av_generated = _add16(0, (~y) & WORD_MASK, True)
    elif amf == 0x16:
        raw, ac, av_generated = _add16(x, (~y) & WORD_MASK, carry_in)
    elif amf == 0x17:
        raw, ac, av_generated = _add16(x, (~y) & WORD_MASK, True)
    elif amf == 0x18:
        raw, ac, av_generated = _add16(y, WORD_MASK, False)
    elif amf == 0x19:
        raw, ac, av_generated = _add16(y, (~x) & WORD_MASK, True)
    elif amf == 0x1A:
        raw, ac, av_generated = _add16(y, (~x) & WORD_MASK, carry_in)
    elif amf == 0x1B:
        raw = (~x) & WORD_MASK
    elif amf == 0x1C:
        raw = x & y
    elif amf == 0x1D:
        raw = x | y
    elif amf == 0x1E:
        raw = x ^ y
    else:
        as_value = bool(x & 0x8000)
        as_write = True
        if as_value:
            raw = (-x) & WORD_MASK
        else:
            raw = x
        av_generated = x == 0x8000

    az = raw == 0
    an = bool(raw & 0x8000)
    av = av_generated or (sticky_av and previous_av)

    destination = raw
    if destination_is_ar and saturate_ar and av_generated:
        destination = 0x8000 if ac else 0x7FFF

    return ALUResult(
        raw_result=raw,
        destination_result=destination,
        az=az,
        an=an,
        av=av,
        ac=ac,
        as_value=as_value,
        as_write=as_write,
    )
