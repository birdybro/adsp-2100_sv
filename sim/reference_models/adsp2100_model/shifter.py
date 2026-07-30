"""Exact-width original ADSP-2100 barrel-shifter function model."""

from __future__ import annotations

from dataclasses import dataclass


SR_MASK = 0xFFFFFFFF


@dataclass(frozen=True)
class ShifterResult:
    sr_result: int
    sr_write: bool
    se_result: int
    se_write: bool
    sb_result: int
    sb_write: bool
    ss_result: bool
    ss_write: bool


def _require_width(value: int, width: int, name: str) -> None:
    if not 0 <= value < (1 << width):
        raise ValueError(f"{name} must fit {width} bits")


def _signed(value: int, width: int) -> int:
    sign = 1 << (width - 1)
    return value - (1 << width) if value & sign else value


def _shift_array(
    operand: int,
    shift: int,
    *,
    high_reference: bool,
    extension: bool,
) -> int:
    """Map the 16-bit input through the documented 16-by-32 array."""

    reference = 16 if high_reference else 0
    result = 0
    for output_bit in range(32):
        source_bit = output_bit - reference - shift
        if 0 <= source_bit < 16:
            bit = bool(operand & (1 << source_bit))
        elif source_bit >= 16:
            bit = extension
        else:
            bit = False
        if bit:
            result |= 1 << output_bit
    return result


def _hi_exponent(operand: int) -> int:
    sign = bool(operand & 0x8000)
    redundant = 0
    for bit_index in range(14, -1, -1):
        if bool(operand & (1 << bit_index)) != sign:
            break
        redundant += 1
    return (-redundant) & 0xFF


def _lo_exponent(operand: int, ss: bool) -> int:
    matching = 0
    for bit_index in range(15, -1, -1):
        if bool(operand & (1 << bit_index)) != ss:
            break
        matching += 1
    return (-15 - matching) & 0xFF


def compute_shifter(
    sf: int,
    x: int,
    shift_or_se: int,
    sr: int,
    sb: int,
    *,
    av: bool = False,
    ac: bool = False,
    ss: bool = False,
) -> ShifterResult:
    """Execute one original four-bit shifter function.

    For LSHIFT and ASHIFT, ``shift_or_se`` is either SE or the instruction's
    immediate eight-bit shift field. NORM and EXP LO always interpret it as
    the current SE value.
    """

    _require_width(sf, 4, "sf")
    _require_width(x, 16, "x")
    _require_width(shift_or_se, 8, "shift_or_se")
    _require_width(sr, 32, "sr")
    _require_width(sb, 5, "sb")

    sr_result = sr
    sr_write = False
    se_result = shift_or_se
    se_write = False
    sb_result = sb
    sb_write = False
    ss_result = ss
    ss_write = False

    if sf <= 0x0B:
        high_reference = not bool(sf & 0x02)
        combine_or = bool(sf & 0x01)
        if sf <= 0x03:
            shift = _signed(shift_or_se, 8)
            extension = False
        elif sf <= 0x07:
            shift = _signed(shift_or_se, 8)
            extension = bool(x & 0x8000)
        else:
            # OQ-011: treat negated SE=-128 as mathematical +128. This agrees
            # with pinned MAME; original hardware/tool confirmation is open.
            shift = -_signed(shift_or_se, 8)
            extension = ac if high_reference else False
        shifted = _shift_array(
            x,
            shift,
            high_reference=high_reference,
            extension=extension,
        )
        sr_result = (sr | shifted) if combine_or else shifted
        sr_result &= SR_MASK
        sr_write = True
    elif sf == 0x0C:
        se_result = _hi_exponent(x)
        se_write = True
        ss_result = bool(x & 0x8000)
        ss_write = True
    elif sf == 0x0D:
        se_result = 1 if av else _hi_exponent(x)
        se_write = True
        ss_result = not bool(x & 0x8000) if av else bool(x & 0x8000)
        ss_write = True
    elif sf == 0x0E:
        if _signed(shift_or_se, 8) == -15:
            se_result = _lo_exponent(x, ss)
            se_write = True
    else:
        detected = _signed(_hi_exponent(x), 8)
        if detected > _signed(sb, 5):
            sb_result = detected & 0x1F
            sb_write = True

    return ShifterResult(
        sr_result=sr_result,
        sr_write=sr_write,
        se_result=se_result,
        se_write=se_write,
        sb_result=sb_result,
        sb_write=sb_write,
        ss_result=ss_result,
        ss_write=ss_write,
    )
