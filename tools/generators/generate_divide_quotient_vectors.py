#!/usr/bin/env python3
"""Generate deterministic original Type 23 model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ASTATBit,
    DREG,
    DREGWrite,
    DivideQuotientInputs,
    DivideQuotientState,
    ExactWord,
    apply_divide_quotient_cycle,
)


X_DREG_CODES = (0, 1, 10, 11, 12, 13, 14, 15)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _astat(state: DivideQuotientState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def _opcode(xop: int) -> int:
    return 0x071000 | (xop << 8)


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DivideQuotientState()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        astat: ExactWord | None = None,
        mstat: ExactWord | None = None,
        dreg: DREGWrite | None = None,
        af: ExactWord | None = None,
    ) -> None:
        nonlocal state
        inputs = DivideQuotientInputs(
            reset=reset,
            execute=execute,
            opcode=opcode,
            astat_write=astat,
            mstat_write=mstat,
            dreg_write=dreg,
            af_write=af,
        )
        result = apply_divide_quotient_cycle(state, inputs)

        stimulus = 0
        for item, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (astat is not None, 1),
            (astat.value if astat else 0, 8),
            (mstat is not None, 1),
            (mstat.value if mstat else 0, 4),
            (dreg is not None, 1),
            (int(dreg.address) if dreg else 0, 4),
            (dreg.data.value if dreg else 0, 16),
            (af is not None, 1),
            (af.value if af else 0, 16),
        ):
            stimulus = _append(stimulus, item, width)

        action = result.action
        xop = action.xop if action is not None else 0
        x_source = X_DREG_CODES[xop]
        old_aq = bool(result.old_aq) if isinstance(result.old_aq, bool) else False
        add_divisor = (
            bool(result.add_divisor)
            if isinstance(result.add_divisor, bool)
            else False
        )
        new_aq = bool(result.new_aq) if isinstance(result.new_aq, bool) else False
        quotient = (
            bool(result.quotient_bit)
            if isinstance(result.quotient_bit, bool)
            else False
        )
        divisor_known, divisor_value = _exact(result.divisor_before)
        partial_known, partial_value = _exact(result.partial_remainder_before)
        ay0_known, ay0_value = _exact(result.ay0_before)
        alu_known, alu_value = _exact(result.alu_result)
        compare_values = (
            result.source_known
            and divisor_known
            and partial_known
            and ay0_known
            and alu_known
        )
        af_result = ((alu_value << 1) & 0xFFFF) | (ay0_value >> 15)
        ay0_result = ((ay0_value << 1) & 0xFFFF) | int(quotient)
        events = 0
        for item, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (result.source_known, 1),
            (result.result_known, 1),
            (old_aq, 1),
            (add_divisor, 1),
            (new_aq, 1),
            (quotient, 1),
            (result.af_write, 1),
            (result.ay0_write, 1),
            (result.aq_write, 1),
            (result.pm_data_access, 1),
            (result.dm_access, 1),
            (xop, 3),
            (x_source, 4),
            (compare_values, 1),
            (divisor_value, 16),
            (partial_value, 16),
            (ay0_value, 16),
            (alu_value, 16),
            (af_result, 16),
            (ay0_result, 16),
        ):
            events = _append(events, item, width)

        selected = (
            result.state.alternate
            if result.state.status.alternate_bank
            else result.state.primary
        )
        af_known, af_value = _exact(selected.af)
        ay0_known, ay0_value = _exact(selected.ay[0])
        astat_mask, astat_value = _astat(result.state)
        post = 0
        for item, width in (
            (af_known, 1),
            (af_value, 16),
            (ay0_known, 1),
            (ay0_value, 16),
            (astat_mask, 8),
            (astat_value, 8),
            (result.state.status.mstat.value, 4),
            (result.state.status.alternate_bank, 1),
        ):
            post = _append(post, item, width)
        lines.append(f"{stimulus:020x} {events:031x} {post:014x}")
        state = result.state

    def initialize_bank(bank: int) -> None:
        emit(mstat=ExactWord(4, bank))
        for code in DREG:
            emit(
                dreg=DREGWrite(
                    code,
                    ExactWord(16, (0x1100 * (bank + 1) + 0x101 * int(code)) & 0xFFFF),
                )
            )
        emit(af=ExactWord(16, 0xA100 + bank))

    emit(reset=True)
    emit(execute=True, opcode=_opcode(0))
    emit(astat=ExactWord(8, 0xD5))
    initialize_bank(0)
    initialize_bank(1)

    execution_count = 0
    for bank in (0, 1):
        emit(mstat=ExactWord(4, bank))
        for aq in (0, 1):
            emit(astat=ExactWord(8, 0x95 | (aq << 5)))
            for xop in range(8):
                emit(execute=True, opcode=_opcode(xop))
                execution_count += 1
    if execution_count != 32:
        raise AssertionError("unexpected exhaustive Type 23 action count")

    emit(execute=True, opcode=0x060800)
    emit(execute=True, opcode=_opcode(0), astat=ExactWord(8, 0))
    emit(astat=ExactWord(8, 0), mstat=ExactWord(4, 0))

    for _ in range(random_count):
        choice = rng.randrange(13)
        if choice < 6:
            emit(execute=True, opcode=_opcode(rng.randrange(8)))
        elif choice == 6:
            emit(execute=True, opcode=rng.randrange(1 << 24))
        elif choice == 7:
            emit(astat=ExactWord(8, rng.randrange(256)))
        elif choice == 8:
            emit(mstat=ExactWord(4, rng.randrange(16)))
        elif choice < 12:
            emit(
                dreg=DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                )
            )
        else:
            emit(af=ExactWord(16, rng.randrange(1 << 16)))

    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210023)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS generated {len(lines)} Type 23 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
