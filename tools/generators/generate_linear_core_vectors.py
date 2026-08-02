#!/usr/bin/env python3
"""Generate deterministic bounded linear-core model/RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DREG,
    ExactWord,
    INTERNAL_MOVE_VALUE,
    LinearCoreState,
    LogicalPhase,
    MODE_CONTROL_VALUE,
    UNKNOWN,
    apply_linear_core_cycle,
    read_dreg,
    register_code_by_name,
)


LEGAL_TYPE7_CODES = tuple(
    list(range(0x10, 0x1C))
    + list(range(0x20, 0x2C))
    + [0x30, 0x31, 0x33, 0x34, 0x35, 0x36, 0x37]
)
READABLE_CODES = tuple(
    list(range(0x00, 0x10))
    + list(range(0x10, 0x1C))
    + list(range(0x20, 0x2C))
    + list(range(0x30, 0x38))
)
LEGAL_SHIFTER_XOPS = (0, 2, 3, 4, 5, 6, 7)
DIVIDE_X_DREG = (
    DREG.AX0,
    DREG.AX1,
    DREG.AR,
    DREG.MR0,
    DREG.MR1,
    DREG.MR2,
    DREG.SR0,
    DREG.SR1,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _type6(destination: int, data: int) -> int:
    return 0x400000 | ((data & 0xFFFF) << 4) | destination


def _type7(code: int, data: int) -> int:
    return 0x300000 | ((code >> 4) << 18) | ((data & 0x3FFF) << 4) | (code & 0xF)


def _type17(destination: int, source: int) -> int:
    return (
        INTERNAL_MOVE_VALUE
        | ((destination >> 4) << 10)
        | ((source >> 4) << 8)
        | ((destination & 0xF) << 4)
        | (source & 0xF)
    )


def _type21(*, dag: int, i_local: int, m_local: int) -> int:
    return (
        0x090000
        | ((dag & 1) << 4)
        | ((i_local & 3) << 2)
        | (m_local & 3)
    )


def _type26(payload: int) -> int:
    return 0x040000 | (payload & 0x1F)


def _type10(*, call: bool, address: int, condition: int) -> int:
    return (
        0x180000
        | (int(call) << 18)
        | ((address & 0x3FFF) << 4)
        | (condition & 0xF)
    )


def _type11(*, end_address: int, termination: int) -> int:
    return (
        0x140000
        | ((end_address & 0x3FFF) << 4)
        | (termination & 0xF)
    )


def _type20(*, interrupt_return: bool, condition: int) -> int:
    return 0x0A0000 | (int(interrupt_return) << 4) | (condition & 0xF)


def _type22(condition: int) -> int:
    return 0x080000 | (condition & 0xF)


def _type19(*, call: bool, i_local: int, condition: int) -> int:
    return (
        0x0B0000
        | ((i_local & 3) << 6)
        | (int(call) << 4)
        | (condition & 0xF)
    )


def _type9(
    *,
    z: int,
    amf: int,
    yop: int,
    xop: int,
    condition: int,
) -> int:
    return (
        0x200000
        | ((z & 1) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 0x3) << 11)
        | ((xop & 0x7) << 8)
        | (condition & 0xF)
    )


def _type8(
    *, z: int, amf: int, yop: int, xop: int, destination: int, source: int
) -> int:
    return (
        0x280000
        | ((z & 1) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 0x3) << 11)
        | ((xop & 0x7) << 8)
        | ((destination & 0xF) << 4)
        | (source & 0xF)
    )


def _type14(*, sf: int, xop: int, destination: int, source: int) -> int:
    return (
        0x100000
        | ((sf & 0xF) << 11)
        | ((xop & 0x7) << 8)
        | ((destination & 0xF) << 4)
        | (source & 0xF)
    )


def _type23(xop: int) -> int:
    return 0x071000 | ((xop & 0x7) << 8)


def _type24(yop: int, xop: int) -> int:
    return 0x060000 | ((yop & 0x3) << 11) | ((xop & 0x7) << 8)


def _type14_destination_legal(sf: int, destination: int) -> bool:
    return not (
        (sf <= 0xB and destination in (int(DREG.SR0), int(DREG.SR1)))
        or (0xC <= sf <= 0xE and destination == int(DREG.SE))
    )


def _type15(*, sf: int, xop: int, exponent: int) -> int:
    return (
        0x0F0000
        | ((sf & 0xF) << 11)
        | ((xop & 0x7) << 8)
        | (exponent & 0xFF)
    )


def _type16(*, sf: int, xop: int, condition: int) -> int:
    return (
        0x0E0000
        | ((sf & 0xF) << 11)
        | ((xop & 0x7) << 8)
        | (condition & 0xF)
    )


def _directed_opcodes() -> tuple[int, ...]:
    readable = register_code_by_name(writable=False)
    writable = register_code_by_name(writable=True)
    # Start at PC 4 and exercise fetched DO setup plus automatic loop flow.
    # The first loop exits immediately, the second proves the terminal
    # instruction's ASTAT write is not visible until the following terminal
    # decision, and the CE loop decrements 2 -> 1 before its final exit.
    opcodes = [
        _type7(writable["ASTAT"], 1),
        _type11(end_address=6, termination=1),
        0,
        _type7(writable["ASTAT"], 0),
        _type11(end_address=9, termination=1),
        _type7(writable["ASTAT"], 1),
        0,
        _type7(writable["CNTR"], 2),
        _type11(end_address=12, termination=0xE),
        0,
        0,
    ]
    opcodes.extend(
        MODE_CONTROL_VALUE | (payload << 4) for payload in range(256)
    )

    opcodes.append(_type7(writable["MSTAT"], 0))
    opcodes.extend(_type6(destination, 0x1100 + destination) for destination in range(16))
    opcodes.append(_type7(writable["SB"], 0x0007))
    opcodes.append(_type7(writable["MSTAT"], 1))
    opcodes.extend(_type6(destination, 0xA100 + destination) for destination in range(16))
    opcodes.append(_type7(writable["SB"], 0x0017))
    opcodes.extend(
        _type7(code, (code * 0x91 + 0x123) & 0x3FFF)
        for code in LEGAL_TYPE7_CODES
        if code not in (writable["MSTAT"], writable["SB"])
    )
    opcodes.append(_type7(writable["MSTAT"], 1))
    opcodes.extend(
        _type17(destination, source)
        for destination in sorted(writable.values())
        for source in sorted(readable.values())
    )
    # Traverse all 32 Type 21 selectors with known I/M/L inputs. Alternate
    # linear and circular configurations, including positive and negative M,
    # so fetched retirement observes selection, arithmetic, and validity.
    for dag in (0, 1):
        group_base = 0x10 if dag == 0 else 0x20
        for i_local in range(4):
            for m_local in range(4):
                circular = bool((dag + i_local + m_local) & 1)
                if circular:
                    old_i = 0x0101 if m_local & 1 else 0x0102
                    modify = 0x3FFD if m_local & 1 else 0x0003
                    length = 0x0005
                else:
                    old_i = 0x0200 + (i_local << 4) + m_local
                    modify = 0x3FFF if m_local & 1 else 0x0002
                    length = 0
                opcodes.extend(
                    (
                        _type7(group_base + i_local, old_i),
                        _type7(group_base + 4 + m_local, modify),
                        _type7(group_base + 8 + i_local, length),
                        _type21(
                            dag=dag,
                            i_local=i_local,
                            m_local=m_local,
                        ),
                    )
                )
    # Establish valid status, count, PC, and loop contexts, then atomically pop
    # all four with one nonterminal Type 26 word. The following all-payload
    # traversal retains the complete fetched-decode attachment coverage while
    # empty contexts remain governed by OQ-013 rather than invented effects.
    opcodes.extend(
        (
            _type7(0x30, 0x00A5),
            _type7(0x31, 0x0006),
            _type7(0x33, 0x0009),
            _type26(0x02),
            _type7(0x30, 0x0012),
            _type7(0x31, 0x0003),
            _type7(0x33, 0x0004),
            _type7(0x35, 0x0123),
            _type7(0x35, 0x0234),
            _type11(end_address=0x0030, termination=0xF),
            _type26(0x1F),
        )
    )
    # Exercise every fetched Type 22 predicate with both low and high ASTAT
    # inputs. The two CNTR contexts also cover both NOT CE outcomes; Type 22
    # observes but never post-decrements the live counter.
    for astat, cntr in ((0x00, 7), (0xFF, 1)):
        opcodes.extend(
            (
                _type7(writable["ASTAT"], astat),
                _type7(writable["CNTR"], cntr),
            )
        )
        opcodes.extend(_type22(condition) for condition in range(16))
    opcodes.extend(_type26(payload) for payload in range(32))
    # Direct transfers select the same-cycle instruction-fetch address. Cover
    # true/false JUMP/CALL, wrapped return stacking, all predicates, and the
    # sourced JUMP NOT CE decrement/outer-count restoration.
    opcodes.extend(
        (
            _type7(writable["ASTAT"], 0x0000),
            _type10(call=False, address=0x2345, condition=0xF),
            _type10(call=False, address=0x1234, condition=0x0),
            _type10(call=True, address=0x3456, condition=0xF),
            _type26(0x10),
            _type10(call=True, address=0x2222, condition=0x0),
            _type7(writable["CNTR"], 0x0007),
            _type7(writable["CNTR"], 0x0001),
            _type10(call=False, address=0x1111, condition=0xE),
            _type10(call=False, address=0x1111, condition=0xE),
        )
    )
    for astat in (0x00, 0xFF):
        opcodes.append(_type7(writable["ASTAT"], astat))
        for condition in range(16):
            opcodes.append(
                _type10(
                    call=False,
                    address=(0x0800 + (astat << 2) + condition) & 0x3FFF,
                    condition=condition,
                )
            )
            if condition != 0xE:
                opcodes.append(
                    _type10(
                        call=True,
                        address=(0x1800 + (astat << 2) + condition) & 0x3FFF,
                        condition=condition,
                    )
                )
    # Conditional returns consume the live PC-stack top as the same-cycle
    # fetch address. Pair every predicate with a sourced CALL context, then
    # exercise RTI's simultaneous status restore through the shared owner.
    opcodes.append(_type7(writable["ASTAT"], 0x0000))
    opcodes.append(_type7(writable["CNTR"], 0x0007))
    for condition in range(16):
        opcodes.extend(
            (
                _type10(
                    call=True,
                    address=(0x2800 + condition) & 0x3FFF,
                    condition=0xF,
                ),
                _type20(interrupt_return=False, condition=condition),
            )
        )
    opcodes.extend(
        (
            _type7(writable["ASTAT"], 0x00A5),
            _type7(writable["MSTAT"], 0x000B),
            _type7(writable["IMASK"], 0x000C),
            _type26(0x02),
            _type7(writable["ASTAT"], 0x0000),
            _type7(writable["MSTAT"], 0x0000),
            _type7(writable["IMASK"], 0x0000),
            _type10(call=True, address=0x3000, condition=0xF),
            _type20(interrupt_return=True, condition=0xF),
        )
    )
    # DAG2-indirect transfers use the cycle-start I4-I7 value as the selected
    # same-cycle fetch address without modifying it. Prove each target through
    # CALL/RTS context, then traverse every IF predicate through JUMP while
    # refreshing NOT CE's live counter context.
    opcodes.append(_type7(writable["ASTAT"], 0x0000))
    for i_local in range(4):
        opcodes.extend(
            (
                _type7(writable[f"I{4 + i_local}"], 0x3200 + i_local),
                _type19(call=True, i_local=i_local, condition=0xF),
                _type20(interrupt_return=False, condition=0xF),
            )
        )
    for astat in (0x00, 0xFF):
        opcodes.append(_type7(writable["ASTAT"], astat))
        for i_local in range(4):
            for condition in range(16):
                if condition == 0xE:
                    opcodes.append(_type7(writable["CNTR"], 0x0007))
                opcodes.append(
                    _type19(
                        call=False,
                        i_local=i_local,
                        condition=condition,
                    )
                )
    # Establish known feedback registers in both banks, then traverse every
    # Type 9 AMF/condition combination through the fetched retirement path.
    opcodes.extend(
        (
            _type7(writable["MSTAT"], 0),
            _type7(writable["ASTAT"], 0),
            _type9(z=1, amf=0x10, yop=0, xop=0, condition=0xF),
            _type9(z=1, amf=0x04, yop=0, xop=0, condition=0xF),
            _type7(writable["MSTAT"], 1),
            _type7(writable["ASTAT"], 0),
            _type9(z=1, amf=0x10, yop=0, xop=0, condition=0xF),
            _type9(z=1, amf=0x04, yop=0, xop=0, condition=0xF),
        )
    )
    opcodes.extend(
        _type9(
            z=(amf ^ condition) & 1,
            amf=amf,
            yop=(amf + condition) & 3,
            xop=(amf * 3 + condition) & 7,
            condition=condition,
        )
        for amf in range(32)
        for condition in range(16)
    )
    # Traverse both banks and every Type 8 compute field combination through
    # fetched retirement. The standalone exhaustive slice covers every legal
    # 24-bit packet; the additional all-pairs pass below closes the attachment's
    # independent move-source and move-destination routing.
    for bank in (0, 1):
        opcodes.append(_type7(writable["MSTAT"], bank))
        for z in (0, 1):
            for amf in range(1, 32):
                for yop in range(4):
                    for xop in range(8):
                        destination = (amf + yop + xop + z) & 0xF
                        if not z and (
                            (amf >= 0x10 and destination == int(DREG.AR))
                            or (
                                amf < 0x10
                                and destination in (
                                    int(DREG.MR0),
                                    int(DREG.MR1),
                                    int(DREG.MR2),
                                )
                            )
                        ):
                            destination = int(DREG.AX0)
                        source = (amf * 3 + yop * 5 + xop + z) & 0xF
                        opcodes.append(
                            _type8(
                                z=z,
                                amf=amf,
                                yop=yop,
                                xop=xop,
                                destination=destination,
                                source=source,
                            )
                        )
        opcodes.extend(
            _type8(
                z=1,
                amf=0x10,
                yop=3,
                xop=0,
                destination=destination,
                source=source,
            )
            for destination in range(16)
            for source in range(16)
        )
    # Exercise exact Type 25 through both banks, both saturation signs, and a
    # false MV predicate. The standalone slice remains the exhaustive opcode
    # and unknown-state reference; these sequences prove fetched retirement.
    opcodes.extend(
        (
            _type7(writable["MSTAT"], 0),
            _type7(writable["ASTAT"], 0x40),
            _type6(int(DREG.MR0), 0x1357),
            _type6(int(DREG.MR1), 0x2468),
            _type6(int(DREG.MR2), 0x0000),
            0x050000,
            _type7(writable["MSTAT"], 1),
            _type7(writable["ASTAT"], 0x40),
            _type6(int(DREG.MR0), 0x89AB),
            _type6(int(DREG.MR1), 0xCDEF),
            _type6(int(DREG.MR2), 0x00FF),
            0x050000,
            _type7(writable["ASTAT"], 0x00),
            _type6(int(DREG.MR2), 0x005A),
            0x050000,
        )
    )
    # Exercise every DIVQ divisor in both banks and both old-AQ paths. Each
    # packet receives newly initialized divisor, AY0, and AF state so the
    # fetched comparison observes only sourced cycle-start dependencies.
    for bank, old_aq, af_seed in ((0, 0, 0x0003), (1, 1, 0xFFFF)):
        opcodes.append(_type7(writable["MSTAT"], bank))
        for xop, source in enumerate(DIVIDE_X_DREG):
            opcodes.extend(
                (
                    _type6(int(source), (0x1111 * (xop + 1)) & 0xFFFF),
                    _type6(int(DREG.AY0), 0x8001),
                    _type6(int(DREG.AY1), af_seed),
                    _type9(z=1, amf=0x10, yop=1, xop=0, condition=0xF),
                    _type7(writable["ASTAT"], old_aq << 5),
                    _type23(xop),
                )
            )
    # Exercise both sourced DIVS upper operands with all divisors in both
    # banks. AF is initialized from AY1, after which AY1 is overwritten so the
    # two YOP forms cannot accidentally alias in the fetched comparison.
    for bank in (0, 1):
        opcodes.append(_type7(writable["MSTAT"], bank))
        for yop in (1, 2):
            for xop, source in enumerate(DIVIDE_X_DREG):
                opcodes.extend(
                    (
                        _type6(int(source), (0x2221 * (xop + 1)) & 0xFFFF),
                        _type6(int(DREG.AY0), 0x8001),
                        _type6(int(DREG.AY1), 0xC001),
                        _type9(z=1, amf=0x10, yop=1, xop=0, condition=0xF),
                        _type6(int(DREG.AY1), 0x4001),
                        _type7(writable["ASTAT"], 0xD5),
                        _type24(yop, xop),
                    )
                )
    # Type 14 executes its shifter and move in parallel. Traverse every
    # canonical, source-backed, noncolliding packet through fetched retirement;
    # the current known register bank makes both old-value results observable.
    opcodes.append(_type7(writable["MSTAT"], 0))
    opcodes.extend(
        _type14(sf=sf, xop=xop, destination=destination, source=source)
        for sf in range(16)
        for xop in LEGAL_SHIFTER_XOPS
        for destination in range(16)
        if _type14_destination_legal(sf, destination)
        for source in range(16)
    )
    # Traverse every source-backed Type 15 and Type 16 word through the real
    # fetched retirement path. Standalone state tests already execute both
    # banks exhaustively; mode changes and random tail traffic vary the bank
    # again here without duplicating the complete opcode traversal.
    opcodes.append(_type7(writable["MSTAT"], 0))
    opcodes.extend(
        _type15(sf=sf, xop=xop, exponent=exponent)
        for sf in range(8)
        for xop in LEGAL_SHIFTER_XOPS
        for exponent in range(256)
    )
    opcodes.append(_type7(writable["MSTAT"], 1))
    opcodes.extend(
        _type16(sf=sf, xop=xop, condition=condition)
        for sf in range(16)
        for xop in LEGAL_SHIFTER_XOPS
        for condition in range(16)
    )
    return tuple(opcodes)


def _legal_opcode(rng: random.Random) -> int:
    choice = rng.randrange(31)
    if choice == 0:
        return 0
    if choice < 5:
        return _type6(rng.randrange(16), rng.randrange(1 << 16))
    if choice < 9:
        return _type7(rng.choice(LEGAL_TYPE7_CODES), rng.randrange(1 << 14))
    if choice < 11:
        return MODE_CONTROL_VALUE | (rng.randrange(256) << 4)
    if choice < 14:
        return _type9(
            z=rng.randrange(2),
            amf=rng.randrange(32),
            yop=rng.randrange(4),
            xop=rng.randrange(8),
            condition=rng.randrange(16),
        )
    if choice < 16:
        return _type15(
            sf=rng.randrange(8),
            xop=rng.choice(LEGAL_SHIFTER_XOPS),
            exponent=rng.randrange(256),
        )
    if choice < 18:
        return _type16(
            sf=rng.randrange(16),
            xop=rng.choice(LEGAL_SHIFTER_XOPS),
            condition=rng.randrange(16),
        )
    if choice < 21:
        sf = rng.randrange(16)
        legal_destinations = tuple(
            destination
            for destination in range(16)
            if _type14_destination_legal(sf, destination)
        )
        return _type14(
            sf=sf,
            xop=rng.choice(LEGAL_SHIFTER_XOPS),
            destination=rng.choice(legal_destinations),
            source=rng.randrange(16),
        )
    if choice == 21:
        return _type21(
            dag=rng.randrange(2),
            i_local=rng.randrange(4),
            m_local=rng.randrange(4),
        )
    if choice == 22:
        return 0x050000
    if choice == 23:
        return _type23(rng.randrange(8))
    if choice == 24:
        return _type24(rng.choice((1, 2)), rng.randrange(8))
    if choice == 25:
        return _type26(rng.randrange(32))
    if choice == 26:
        call = bool(rng.randrange(2))
        condition = rng.randrange(16)
        if call and condition == 0xE:
            condition = 0xF
        return _type10(
            call=call,
            address=rng.randrange(1 << 14),
            condition=condition,
        )
    if choice == 27:
        call = bool(rng.randrange(2))
        condition = rng.randrange(16)
        if call and condition == 0xE:
            condition = 0xF
        return _type19(
            call=call,
            i_local=rng.randrange(4),
            condition=condition,
        )
    if choice == 28:
        return _type20(
            interrupt_return=bool(rng.randrange(2)),
            condition=rng.randrange(16),
        )
    if choice == 29:
        return _type22(rng.randrange(16))
    z = rng.randrange(2)
    amf = rng.randrange(1, 32)
    destination = rng.randrange(16)
    if not z and (
        (amf >= 0x10 and destination == int(DREG.AR))
        or (
            amf < 0x10
            and destination in (int(DREG.MR0), int(DREG.MR1), int(DREG.MR2))
        )
    ):
        destination = int(DREG.AX0)
    return _type8(
        z=z,
        amf=amf,
        yop=rng.randrange(4),
        xop=rng.randrange(8),
        destination=destination,
        source=rng.randrange(16),
    )


def _exact(value: object) -> tuple[bool, int]:
    return (
        (True, value.value)
        if isinstance(value, ExactWord)
        else (False, 0)
    )


def _probe(state: LinearCoreState, code: int) -> tuple[bool, int]:
    arch = state.architecture
    group = code >> 4
    index = code & 0xF
    if group == 0:
        bank = arch.alternate if arch.mstat.value & 1 else arch.primary
        return _exact(read_dreg(bank, DREG(index)))
    if group in (1, 2):
        address = ((group - 1) << 2) | (index & 3)
        if index < 4:
            return _exact(arch.dag.i[address])
        if index < 8:
            valid, value = _exact(arch.dag.m[address])
            if valid and value & 0x2000:
                value |= 0xC000
            return (valid, value)
        return _exact(arch.dag.l[address])
    if index == 0:
        return _exact(arch.astat)
    if index == 1:
        return (True, arch.mstat.value)
    if index == 2:
        return (True, arch.sstat.value)
    if index == 3:
        return (True, arch.imask.value)
    if index == 4:
        return _exact(arch.icntl)
    if index == 5:
        return _exact(arch.cntr)
    if index == 6:
        bank = arch.alternate if arch.mstat.value & 1 else arch.primary
        valid, value = _exact(bank.sb)
        if valid and value & 0x10:
            value |= 0xFFE0
        return (valid, value)
    return _exact(arch.px)


def generate_lines(instruction_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = LinearCoreState.reset()
    lines: list[str] = []
    directed_opcodes = _directed_opcodes()
    if instruction_count < len(directed_opcodes):
        raise ValueError(
            f"instruction count must be at least {len(directed_opcodes)}"
        )

    def emit(
        phase: LogicalPhase,
        *,
        reset: bool = False,
        advance: bool = True,
        issue_inhibit: bool = False,
        relinquished: bool = False,
        setup: tuple[int, int] | None = None,
        pmd: int = 0,
        pmd_valid: bool = True,
        irq_n: int = 0xF,
        probe: int | None = None,
    ) -> None:
        nonlocal state
        if probe is None:
            probe = rng.choice(READABLE_CODES)
        setup_value = (
            None
            if setup is None
            else (ExactWord(14, setup[0]), ExactWord(24, setup[1]))
        )
        result = apply_linear_core_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            instruction_issue_inhibit=issue_inhibit,
            bus_relinquished=relinquished,
            instruction_setup=setup_value,
            pmd_read_data=ExactWord(24, pmd) if pmd_valid else UNKNOWN,
            irq_n=irq_n,
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(phase), 3),
            (advance, 1),
            (issue_inhibit, 1),
            (relinquished, 1),
            (setup is not None, 1),
            (0 if setup is None else setup[0], 14),
            (0 if setup is None else setup[1], 24),
            (pmd, 24),
            (pmd_valid, 1),
            (irq_n, 4),
            (probe, 6),
        ):
            stimulus = _append(stimulus, value, width)

        bus = result.bus
        pre = 0
        for value, width in (
            (result.issue_boundary, 1),
            (result.instruction_setup_accepted, 1),
            (result.instruction_issue, 1),
            (result.retire_event, 1),
            (result.trap_event, 1),
            (result.interrupt_recognition_event, 1),
            (result.interrupt_entry_event, 1),
            (result.interrupt_vector_issue_event, 1),
            (result.interrupt_vector_fetch_event, 1),
            (result.interrupt_level, 2),
            (result.interrupt_vector.value, 14),
            (state.interrupt.edge_pending, 4),
            (state.interrupt_vectoring, 1),
            (result.interrupt_configuration_invalid, 1),
            (result.interrupt_reset_baseline_provisional, 1),
            (result.interrupt_adjacent_control_conflict, 1),
            (state.instruction_valid, 1),
            (state.pending, 1),
            (result.unsupported_instruction, 1),
            (result.reserved_subencoding, 1),
            (result.phase_conflict, 1),
            (result.integration_conflict, 1),
            (result.internal_conflict, 1),
            (result.provisional_source_extension, 1),
            (state.architecture.pc.value, 14),
            (
                state.instruction.value
                if isinstance(state.instruction, ExactWord)
                else 0,
                24,
            ),
            (bus.request_accepted, 1),
            (bus.completion_event, 1),
            (bus.read_sample_event, 1),
            (state.bus.active, 1),
            (bus.address_output_enable, 1),
            (bus.control_output_enable, 1),
            (bus.data_output_enable, 1),
            (bus.address_known, 1),
            (bus.address if bus.address_known else 0, 14),
            (bus.pmda, 1),
            (bus.control_output_enable, 1),
            (bus.pms_n, 1),
            (bus.pmrd_n, 1),
            (bus.pmwr_n, 1),
            (bus.write_data_known, 1),
            (bus.write_data if bus.write_data_known else 0, 24),
        ):
            pre = _append(pre, value, width)

        post_state = result.state
        probe_valid, probe_value = _probe(post_state, probe)
        astat_valid, astat_value = _exact(post_state.architecture.astat)
        icntl_valid, icntl_value = _exact(post_state.architecture.icntl)
        cntr_valid, cntr_value = _exact(post_state.architecture.cntr)
        px_valid, px_value = _exact(post_state.architecture.px)
        post = 0
        for value, width in (
            (post_state.instruction_valid, 1),
            (post_state.pending, 1),
            (post_state.architecture.pc.value, 14),
            (
                post_state.instruction.value
                if isinstance(post_state.instruction, ExactWord)
                else pmd,
                24,
            ),
            (probe_valid, 1),
            (probe_value, 16),
            (astat_valid, 1),
            (astat_value, 8),
            (post_state.architecture.mstat.value, 4),
            (icntl_valid, 1),
            (icntl_value, 5),
            (post_state.architecture.imask.value, 4),
            (cntr_valid, 1),
            (cntr_value, 14),
            (px_valid, 1),
            (px_value, 8),
            (post_state.architecture.sstat.value, 8),
            (bool(post_state.architecture.mstat.value & 1), 1),
            (len(post_state.architecture.count_stack), 3),
            (bool(post_state.architecture.sstat.value & 0x08), 1),
            (post_state.bus.active, 1),
            (post_state.interrupt_vectoring, 1),
            (post_state.interrupt.edge_pending, 4),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:021x} {pre:033x} {post:031x}")
        state = post_state

    emit(LogicalPhase.STATE_8, reset=True, pmd_valid=False)

    # Retire a normal NOP while level-sensitive IRQ2 is recognized, discard
    # its overlapped fetch, fetch vector 2 during the inserted NOP cycle, then
    # execute a vector-resident RTI and refetch the discarded word.
    writable = register_code_by_name(writable=True)
    emit(
        LogicalPhase.STATE_8,
        setup=(0x0100, _type7(writable["ICNTL"], 0x10)),
    )
    for next_opcode, completion_irq in (
        (_type7(writable["IMASK"], 0xF), 0xF),
        (0, 0xF),
        (_type6(int(DREG.AX0), 0xDEAD), 0xB),
    ):
        emit(LogicalPhase.STATE_8)
        for phase in range(6):
            emit(LogicalPhase(phase), irq_n=completion_irq)
        emit(
            LogicalPhase.STATE_7,
            pmd=next_opcode,
            irq_n=completion_irq,
        )
    emit(LogicalPhase.STATE_8)
    for phase in range(6):
        emit(LogicalPhase(phase))
    emit(
        LogicalPhase.STATE_7,
        pmd=_type20(interrupt_return=True, condition=0xF),
    )
    emit(LogicalPhase.STATE_8)
    for phase in range(6):
        emit(LogicalPhase(phase))
    emit(
        LogicalPhase.STATE_7,
        pmd=_type6(int(DREG.AX0), 0xDEAD),
    )

    # OQ-015 is not assigned an ordering. A serviceable request adjacent to
    # active MODE CONTROL is retained, entry is deferred, and the conflict is
    # observable before a following ordinary instruction admits it.
    emit(LogicalPhase.STATE_5, reset=True, pmd_valid=False)
    emit(
        LogicalPhase.STATE_8,
        setup=(0x0200, _type7(writable["ICNTL"], 0)),
    )
    for next_opcode, completion_irq in (
        (_type7(writable["IMASK"], 1), 0xF),
        (MODE_CONTROL_VALUE | (0x03 << 4), 0xF),
        (0, 0xE),
        (0, 0xE),
    ):
        emit(LogicalPhase.STATE_8)
        for phase in range(6):
            emit(LogicalPhase(phase), irq_n=completion_irq)
        emit(
            LogicalPhase.STATE_7,
            pmd=next_opcode,
            irq_n=completion_irq,
        )

    emit(LogicalPhase.STATE_5, reset=True, pmd_valid=False)
    current_opcode = directed_opcodes[0]
    emit(LogicalPhase.STATE_8, setup=(4, current_opcode))

    completed = 0
    while completed < instruction_count:
        if not state.instruction_valid:
            emit(LogicalPhase.STATE_8, reset=True, pmd_valid=False)
            current_opcode = _legal_opcode(rng)
            emit(
                LogicalPhase.STATE_8,
                setup=(rng.randrange(1 << 14), current_opcode),
            )

        if rng.randrange(23) == 0:
            emit(
                LogicalPhase.STATE_8,
                advance=False,
                setup=(0, 0) if rng.randrange(2) else None,
            )
        if rng.randrange(31) == 0:
            emit(LogicalPhase.STATE_8, relinquished=True)
        if rng.randrange(19) == 0:
            emit(LogicalPhase.STATE_8, issue_inhibit=True)

        issued = state.instruction_valid
        emit(LogicalPhase.STATE_8)
        if not issued or not state.pending:
            emit(LogicalPhase.STATE_8, reset=True, pmd_valid=False)
            continue

        for phase in range(6):
            logical_phase = LogicalPhase(phase)
            if rng.randrange(17) == 0:
                emit(logical_phase, advance=False)
            if rng.randrange(47) == 0:
                emit(logical_phase, relinquished=True)
            if rng.randrange(43) == 0:
                emit(logical_phase, issue_inhibit=True)
            emit(logical_phase)

        if rng.randrange(13) == 0:
            emit(LogicalPhase.STATE_7, advance=False)
        if rng.randrange(41) == 0:
            emit(LogicalPhase.STATE_7, relinquished=True)

        choice = rng.randrange(100)
        if completed + 1 < len(directed_opcodes):
            next_opcode = directed_opcodes[completed + 1]
            next_valid = True
        elif choice < 93:
            next_opcode = _legal_opcode(rng)
            next_valid = True
        elif choice < 96:
            next_opcode = _type7(0x32, rng.randrange(1 << 14))
            next_valid = True
        elif choice < 99:
            next_opcode = 0x000001
            next_valid = True
        else:
            next_opcode = rng.randrange(1 << 24)
            next_valid = False
        emit(
            LogicalPhase.STATE_7,
            pmd=next_opcode,
            pmd_valid=next_valid,
        )
        completed += 1

    emit(LogicalPhase.STATE_5, reset=True, pmd_valid=False)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    # The class-complete Type 14/15/16 attachment traversals and directed
    # source-closed control transfers require 50,184 instructions. Phase
    # holds, relinquishment, fetch validity, and probes remain deterministically
    # randomized across that complete corpus; do not append unconstrained
    # context-dependent return instructions after the final directed word.
    parser.add_argument("--instructions", type=int, default=50_184)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210067)
    args = parser.parse_args()
    lines = generate_lines(args.instructions, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"PASS generated {len(lines)} linear-core clocks "
        f"seed=0x{args.seed:x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
