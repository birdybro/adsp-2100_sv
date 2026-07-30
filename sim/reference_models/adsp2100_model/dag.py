"""Original ADSP-2100 data-address-generator arithmetic model."""

from __future__ import annotations

from dataclasses import dataclass


ADDRESS_MASK = 0x3FFF


@dataclass(frozen=True)
class DAGResult:
    address: int
    next_i: int
    base: int
    circular: bool
    configuration_valid: bool


def _require_address(value: int, name: str) -> None:
    if not 0 <= value <= ADDRESS_MASK:
        raise ValueError(f"{name} must fit 14 bits")


def _signed_modify(value: int) -> int:
    return value - 0x4000 if value & 0x2000 else value


def reverse_address(address: int) -> int:
    """Reverse all fourteen original DM address bits."""

    _require_address(address, "address")
    result = 0
    for bit_index in range(14):
        if address & (1 << bit_index):
            result |= 1 << (13 - bit_index)
    return result


def original_base_mask(length: int) -> int:
    """Return the original ADSP-2100 circular-base mask.

    Unlike later ADSP-21xx devices, an exact power-of-two length requires one
    additional zero address bit. The uniform original rule is therefore based
    on the number of bits needed to represent the unsigned length itself.
    """

    _require_address(length, "length")
    if length == 0:
        return ADDRESS_MASK
    low_bits = length.bit_length()
    return (ADDRESS_MASK << low_bits) & ADDRESS_MASK


def compute_dag(
    i_value: int,
    m_value: int,
    l_value: int,
    *,
    dag1: bool,
    bit_reverse_enabled: bool = False,
) -> DAGResult:
    """Generate the old-I address and one post-modified I value.

    Results with ``configuration_valid=False`` are deterministic diagnostics,
    not claims about undocumented operation outside the circular-buffer
    placement and modify restrictions.
    """

    _require_address(i_value, "i_value")
    _require_address(m_value, "m_value")
    _require_address(l_value, "l_value")

    address = (
        reverse_address(i_value)
        if dag1 and bit_reverse_enabled
        else i_value
    )
    modify = _signed_modify(m_value)

    if l_value == 0:
        return DAGResult(
            address=address,
            next_i=(i_value + modify) & ADDRESS_MASK,
            base=0,
            circular=False,
            configuration_valid=True,
        )

    base = i_value & original_base_mask(l_value)
    upper_bound = base + l_value
    configuration_valid = (
        base <= i_value < upper_bound
        and abs(modify) <= l_value
        and upper_bound <= ADDRESS_MASK + 1
    )

    next_value = i_value + modify
    if next_value < base:
        next_value += l_value
    elif next_value >= upper_bound:
        next_value -= l_value

    return DAGResult(
        address=address,
        next_i=next_value & ADDRESS_MASK,
        base=base,
        circular=True,
        configuration_valid=configuration_valid,
    )
