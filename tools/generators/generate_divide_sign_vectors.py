#!/usr/bin/env python3
"""Generate deterministic original Type 24 model-versus-RTL vectors."""

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
    DivideSignInputs,
    DivideSignState,
    ExactWord,
    apply_divide_sign_cycle,
)


X_DREG_CODES = (0, 1, 10, 11, 12, 13, 14, 15)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _astat(state: DivideSignState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def _opcode(yop: int, xop: int) -> int:
    return 0x060000 | (yop << 11) | (xop << 8)


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DivideSignState()
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
        inputs = DivideSignInputs(
            reset=reset,
            execute=execute,
            opcode=opcode,
            astat_write=astat,
            mstat_write=mstat,
            dreg_write=dreg,
            af_write=af,
        )
        result = apply_divide_sign_cycle(state, inputs)

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
        yop = action.yop if action is not None else 0
        xop = action.xop if action is not None else 0
        x_source = X_DREG_CODES[xop]
        upper_feedback = bool(result.action_valid and yop == 2)
        upper_source = 5 if result.action_valid and yop == 1 else 0
        quotient = bool(result.quotient_sign) if result.result_known else False
        divisor_known, divisor_value = _exact(result.divisor_before)
        upper_known, upper_value = _exact(result.af_before)
        ay0_known, ay0_value = _exact(result.ay0_before)
        compare_values = result.source_known and divisor_known and upper_known and ay0_known
        af_result = ((upper_value << 1) & 0xFFFF) | (ay0_value >> 15)
        ay0_result = ((ay0_value << 1) & 0xFFFF) | int(quotient)
        events = 0
        for item, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.unsupported_subencoding, 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (result.source_known, 1),
            (result.result_known, 1),
            (quotient, 1),
            (result.af_write, 1),
            (result.ay0_write, 1),
            (result.aq_write, 1),
            (result.pm_data_access, 1),
            (result.dm_access, 1),
            (yop, 2),
            (xop, 3),
            (x_source, 4),
            (upper_source, 4),
            (upper_feedback, 1),
            (compare_values, 1),
            (divisor_value, 16),
            (upper_value, 16),
            (ay0_value, 16),
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
        lines.append(f"{stimulus:020x} {events:028x} {post:014x}")
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
    # The validity sideband must preserve authentic unknown reset state.
    emit(execute=True, opcode=_opcode(1, 0))
    emit(astat=ExactWord(8, 0xD5))
    initialize_bank(0)
    initialize_bank(1)

    execution_count = 0
    for bank in (0, 1):
        emit(mstat=ExactWord(4, bank))
        for yop in range(4):
            for xop in range(8):
                emit(execute=True, opcode=_opcode(yop, xop))
                execution_count += 1
    if execution_count != 64:
        raise AssertionError("unexpected exhaustive Type 24 action count")

    emit(execute=True, opcode=0x071000)
    emit(execute=True, opcode=_opcode(1, 0), astat=ExactWord(8, 0))
    emit(astat=ExactWord(8, 0), mstat=ExactWord(4, 0))

    for _ in range(random_count):
        choice = rng.randrange(13)
        if choice < 6:
            emit(
                execute=True,
                opcode=_opcode(rng.randrange(4), rng.randrange(8)),
            )
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
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210024)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS generated {len(lines)} Type 24 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
