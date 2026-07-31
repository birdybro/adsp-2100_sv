#!/usr/bin/env python3
"""Generate deterministic Type 25 stateful model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ExactWord,
    MR_SATURATION_OPCODE,
    MRSaturationSliceInputs,
    MRSaturationSliceState,
    apply_mr_saturation_slice_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _pack_stimulus(inputs: MRSaturationSliceInputs) -> int:
    packed = 0
    for value, width in (
        (inputs.reset, 1),
        (inputs.execute, 1),
        (inputs.opcode, 24),
        (inputs.astat_write is not None, 1),
        (
            inputs.astat_write.value
            if inputs.astat_write is not None
            else 0,
            8,
        ),
        (inputs.mstat_write is not None, 1),
        (
            inputs.mstat_write.value
            if inputs.mstat_write is not None
            else 0,
            4,
        ),
        (inputs.mr_setup_write is not None, 1),
        (
            inputs.mr_setup_write.value
            if inputs.mr_setup_write is not None
            else 0,
            40,
        ),
    ):
        packed = _append(packed, value, width)
    return packed


def _bank_mr(state: MRSaturationSliceState, alternate: bool) -> int:
    bank = state.alternate if alternate else state.primary
    mr0, mr1, mr2 = bank.mr
    assert isinstance(mr0, ExactWord)
    assert isinstance(mr1, ExactWord)
    assert isinstance(mr2, ExactWord)
    return (mr2.value << 32) | (mr1.value << 16) | mr0.value


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = MRSaturationSliceState()
    astat_known = False
    bank_known = [False, False]
    mstat_known = False
    lines: list[str] = []

    def emit(inputs: MRSaturationSliceInputs) -> None:
        nonlocal state, astat_known, mstat_known
        pre_astat_known = astat_known
        pre_mstat_known = mstat_known
        result = apply_mr_saturation_slice_cycle(state, inputs)

        selected_before = state.status.alternate_bank
        condition = (
            bool(state.status.astat.bits[6])
            if pre_astat_known
            else False
        )
        events = 0
        for value, width in (
            (pre_astat_known, 1),
            (pre_mstat_known, 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (result.internal_conflict, 1),
            (condition, 1),
            (selected_before, 1),
            (bool(result.mr_write) if pre_astat_known else False, 1),
        ):
            events = _append(events, value, width)

        if inputs.reset:
            astat_known = False
            mstat_known = True
        elif not result.integration_conflict:
            if inputs.astat_write is not None:
                astat_known = True
            if inputs.mstat_write is not None:
                mstat_known = True
            if inputs.mr_setup_write is not None:
                bank_known[int(selected_before)] = True

        selected_after = result.state.status.alternate_bank
        compare_mr = bank_known[int(selected_after)]
        post_state = 0
        for value, width in (
            (astat_known, 1),
            (
                result.state.status.astat.to_word().value
                if astat_known
                else 0,
                8,
            ),
            (result.state.status.mstat.value, 4),
            (compare_mr, 1),
            (
                _bank_mr(result.state, selected_after)
                if compare_mr
                else 0,
                40,
            ),
        ):
            post_state = _append(post_state, value, width)

        lines.append(
            f"{_pack_stimulus(inputs):021x} {events:03x} {post_state:014x}"
        )
        state = result.state

    emit(MRSaturationSliceInputs(reset=True))
    emit(
        MRSaturationSliceInputs(
            astat_write=ExactWord(8, 0x40),
            mr_setup_write=ExactWord(40, 0x0012345678),
        )
    )
    emit(
        MRSaturationSliceInputs(
            execute=True,
            opcode=MR_SATURATION_OPCODE,
        )
    )
    emit(MRSaturationSliceInputs(mstat_write=ExactWord(4, 1)))
    emit(
        MRSaturationSliceInputs(
            mr_setup_write=ExactWord(40, 0xFF12345678),
        )
    )
    emit(
        MRSaturationSliceInputs(
            execute=True,
            opcode=MR_SATURATION_OPCODE,
        )
    )
    emit(MRSaturationSliceInputs(mstat_write=ExactWord(4, 0)))
    emit(MRSaturationSliceInputs(astat_write=ExactWord(8, 0)))
    emit(
        MRSaturationSliceInputs(
            mr_setup_write=ExactWord(40, 0x123456789A),
        )
    )
    emit(
        MRSaturationSliceInputs(
            execute=True,
            opcode=MR_SATURATION_OPCODE,
        )
    )
    emit(
        MRSaturationSliceInputs(
            execute=True,
            opcode=0x050001,
        )
    )
    emit(
        MRSaturationSliceInputs(
            execute=True,
            opcode=MR_SATURATION_OPCODE,
            mr_setup_write=ExactWord(40, 0x5555555555),
        )
    )

    for index in range(random_count):
        choice = rng.randrange(10)
        if choice == 0:
            inputs = MRSaturationSliceInputs(
                astat_write=ExactWord(8, rng.randrange(1 << 8)),
            )
        elif choice == 1:
            inputs = MRSaturationSliceInputs(
                mstat_write=ExactWord(4, rng.randrange(1 << 4)),
            )
        elif choice == 2:
            inputs = MRSaturationSliceInputs(
                mr_setup_write=ExactWord(40, rng.randrange(1 << 40)),
            )
        elif choice < 7:
            inputs = MRSaturationSliceInputs(
                execute=True,
                opcode=MR_SATURATION_OPCODE,
            )
        elif choice == 7:
            inputs = MRSaturationSliceInputs(
                execute=True,
                opcode=0x050001,
            )
        elif choice == 8:
            inputs = MRSaturationSliceInputs(
                execute=True,
                opcode=MR_SATURATION_OPCODE,
                astat_write=ExactWord(8, rng.randrange(1 << 8)),
            )
        else:
            inputs = MRSaturationSliceInputs()
        emit(inputs)
        if index != 0 and index % 997 == 0:
            emit(MRSaturationSliceInputs(reset=True))
            emit(
                MRSaturationSliceInputs(
                    astat_write=ExactWord(8, rng.randrange(1 << 8)),
                )
            )

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210025)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"wrote {len(lines)} Type 25 stateful vectors to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
