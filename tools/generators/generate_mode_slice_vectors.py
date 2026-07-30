#!/usr/bin/env python3
"""Generate deterministic MSTAT-consumer integration cycle vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ASTATState,
    DREG,
    DREGWrite,
    ExactWord,
    ModeControl,
    ModeSliceInputs,
    ModeSliceState,
    UNKNOWN,
    apply_mode_slice_cycle,
    read_dreg,
)


def _append(packed: int, value: int, width: int) -> int:
    return (packed << width) | int(value)


def _pack_stimulus(inputs: ModeSliceInputs) -> int:
    packed = int(inputs.reset)
    packed = _append(packed, inputs.astat_move is not None, 1)
    packed = _append(
        packed,
        0 if inputs.astat_move is None else inputs.astat_move.value,
        8,
    )
    packed = _append(packed, inputs.mstat_move is not None, 1)
    packed = _append(
        packed,
        0 if inputs.mstat_move is None else inputs.mstat_move.value,
        4,
    )
    for control in inputs.mode_controls:
        packed = _append(packed, control, 2)
    packed = _append(packed, inputs.read_address, 4)
    packed = _append(packed, inputs.dreg_write is not None, 1)
    packed = _append(
        packed,
        0 if inputs.dreg_write is None else inputs.dreg_write.address,
        4,
    )
    packed = _append(
        packed,
        0 if inputs.dreg_write is None else inputs.dreg_write.data.value,
        16,
    )
    packed = _append(packed, inputs.alu_execute, 1)
    packed = _append(packed, inputs.alu_amf, 5)
    packed = _append(packed, inputs.alu_x, 16)
    packed = _append(packed, inputs.alu_y, 16)
    packed = _append(packed, inputs.alu_feedback, 1)
    packed = _append(packed, inputs.dag_i, 14)
    packed = _append(packed, inputs.dag_m, 14)
    return _append(packed, inputs.dag_l, 14)


def _pack_expected(
    result: object,
    *,
    current_astat: ASTATState,
    current_mstat: ExactWord,
    compare_astat: bool,
    compare_read: bool,
    compare_alu: bool,
    compare_modes: bool,
    compare_dag: bool,
    register_conflict: bool,
) -> int:
    observation = result.observation
    packed = int(compare_astat)
    for flag in (
        compare_read,
        compare_alu,
        compare_modes,
        compare_dag,
        result.status_write_conflict,
        register_conflict,
    ):
        packed = _append(packed, flag, 1)
    packed = _append(
        packed,
        current_astat.to_word().value if compare_astat else 0,
        8,
    )
    packed = _append(packed, current_mstat.value, 4)
    packed = _append(packed, observation.alternate_bank, 1)
    packed = _append(packed, observation.bit_reverse, 1)
    packed = _append(packed, observation.overflow_latch, 1)
    packed = _append(packed, observation.saturate_ar, 1)
    packed = _append(
        packed,
        observation.read_data.value if compare_read else 0,
        16,
    )
    alu = observation.alu
    packed = _append(packed, alu is not None, 1)
    packed = _append(
        packed,
        0 if alu is None else alu.raw_result,
        16,
    )
    packed = _append(
        packed,
        0 if alu is None else alu.destination_result,
        16,
    )
    packed = _append(packed, observation.dag.address, 14)
    return _append(packed, observation.dag.next_i, 14)


def _dreg(address: DREG, value: int) -> DREGWrite:
    return DREGWrite(address, ExactWord(16, value))


def generate_lines(random_count: int, seed: int) -> list[str]:
    state = ModeSliceState()
    lines: list[str] = []

    def emit(
        inputs: ModeSliceInputs,
        *,
        compare_astat: bool | None = None,
        compare_read: bool | None = None,
        compare_modes: bool = True,
        compare_dag: bool = True,
    ) -> None:
        nonlocal state
        astat_known = state.status.astat.is_fully_known
        selected = (
            state.alternate
            if state.status.alternate_bank
            else state.primary
        )
        read_value = read_dreg(selected, inputs.read_address)
        read_known = read_value is not UNKNOWN
        do_compare_astat = (
            astat_known if compare_astat is None else compare_astat
        )
        do_compare_read = (
            read_known if compare_read is None else compare_read
        )
        result = apply_mode_slice_cycle(state, inputs)
        register_conflict = bool(
            inputs.alu_execute
            and inputs.dreg_write is not None
            and not inputs.alu_feedback
            and inputs.dreg_write.address == DREG.AR
        )
        expected = _pack_expected(
            result,
            current_astat=state.status.astat,
            current_mstat=state.status.mstat,
            compare_astat=do_compare_astat,
            compare_read=do_compare_read,
            compare_alu=inputs.alu_execute and astat_known,
            compare_modes=compare_modes,
            compare_dag=compare_dag,
            register_conflict=register_conflict,
        )
        lines.append(
            f"{_pack_stimulus(inputs):033x} {expected:026x}"
        )
        state = result.state

    emit(
        ModeSliceInputs(reset=True),
        compare_astat=False,
        compare_read=False,
        compare_modes=False,
        compare_dag=False,
    )
    emit(ModeSliceInputs(), compare_astat=False, compare_read=False)
    emit(
        ModeSliceInputs(
            astat_move=ExactWord(8, 0),
            mstat_move=ExactWord(4, 0),
        ),
        compare_astat=False,
        compare_read=False,
    )
    emit(ModeSliceInputs(), compare_read=False)

    # Initialize every DREG in both banks with distinguishable known values.
    for alternate in (False, True):
        emit(
            ModeSliceInputs(mstat_move=ExactWord(4, int(alternate))),
            compare_read=False,
        )
        emit(ModeSliceInputs(), compare_read=False)
        for address in DREG:
            value = (
                (0xA000 if alternate else 0x1000)
                | (int(address) << 4)
                | int(address)
            )
            emit(
                ModeSliceInputs(
                    read_address=address,
                    dreg_write=_dreg(address, value),
                ),
                compare_read=False,
            )
            emit(ModeSliceInputs(read_address=address))

    # Exhaust direct MSTAT values and observe each only on the following cycle.
    for value in range(16):
        emit(ModeSliceInputs(mstat_move=ExactWord(4, value)))
        emit(ModeSliceInputs(dag_i=0x0003))

    # Directed ALU saturation and sticky-overflow visibility.
    emit(ModeSliceInputs(astat_move=ExactWord(8, 0)))
    emit(ModeSliceInputs(mstat_move=ExactWord(4, 0x8)))
    emit(
        ModeSliceInputs(
            read_address=DREG.AR,
            alu_execute=True,
            alu_amf=0x13,
            alu_x=0x7FFF,
            alu_y=1,
        )
    )
    emit(ModeSliceInputs(read_address=DREG.AR))
    emit(ModeSliceInputs(mstat_move=ExactWord(4, 0x4)))
    emit(
        ModeSliceInputs(
            alu_execute=True,
            alu_amf=0x10,
            alu_y=0,
        )
    )
    emit(ModeSliceInputs())

    rng = random.Random(seed)
    controls = tuple(ModeControl)
    for _ in range(random_count):
        action = rng.randrange(6)
        common = {
            "read_address": DREG(rng.randrange(16)),
            "dag_i": rng.randrange(1 << 14),
            "dag_m": rng.randrange(1 << 14),
            "dag_l": 0,
        }
        if action == 0:
            inputs = ModeSliceInputs(**common)
        elif action == 1:
            inputs = ModeSliceInputs(
                **common,
                mstat_move=ExactWord(4, rng.randrange(16)),
            )
        elif action == 2:
            inputs = ModeSliceInputs(
                **common,
                mode_controls=tuple(
                    rng.choice(controls) for _ in range(4)
                ),
            )
        elif action == 3:
            inputs = ModeSliceInputs(
                **common,
                astat_move=ExactWord(8, rng.randrange(256)),
            )
        elif action == 4:
            inputs = ModeSliceInputs(
                **common,
                dreg_write=_dreg(
                    DREG(rng.randrange(16)),
                    rng.randrange(1 << 16),
                ),
            )
        else:
            inputs = ModeSliceInputs(
                **common,
                alu_execute=True,
                alu_amf=rng.randrange(0x10, 0x20),
                alu_x=rng.randrange(1 << 16),
                alu_y=rng.randrange(1 << 16),
                alu_feedback=bool(rng.getrandbits(1)),
            )
        emit(inputs)

    emit(ModeSliceInputs())
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=0x210017)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"wrote {len(lines)} MSTAT-consumer vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
