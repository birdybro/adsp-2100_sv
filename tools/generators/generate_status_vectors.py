#!/usr/bin/env python3
"""Generate deterministic ASTAT/MSTAT model-versus-RTL cycle vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ALUStatusUpdate,
    ExactWord,
    ModeControl,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
    status_write_conflict,
)


def _append(packed: int, value: int, width: int) -> int:
    if not 0 <= value < (1 << width):
        raise ValueError(f"value {value} does not fit {width} bits")
    return (packed << width) | value


def _pack_stimulus(inputs: StatusCycleInputs) -> int:
    controls = tuple(int(control) for control in inputs.mode_controls)
    alu = inputs.alu
    packed = int(inputs.reset)
    packed = _append(packed, int(inputs.astat_move is not None), 1)
    packed = _append(
        packed,
        0 if inputs.astat_move is None else inputs.astat_move.value,
        8,
    )
    packed = _append(packed, int(inputs.mstat_move is not None), 1)
    packed = _append(
        packed,
        0 if inputs.mstat_move is None else inputs.mstat_move.value,
        4,
    )
    for control in controls:
        packed = _append(packed, control, 2)
    packed = _append(packed, int(alu is not None), 1)
    packed = _append(packed, 0 if alu is None else int(alu.az), 1)
    packed = _append(packed, 0 if alu is None else int(alu.an), 1)
    packed = _append(packed, 0 if alu is None else int(alu.av), 1)
    packed = _append(packed, 0 if alu is None else int(alu.ac), 1)
    packed = _append(
        packed,
        int(alu is not None and alu.as_value is not None),
        1,
    )
    packed = _append(
        packed,
        0 if alu is None or alu.as_value is None else int(alu.as_value),
        1,
    )
    packed = _append(packed, int(inputs.divide_aq is not None), 1)
    packed = _append(
        packed,
        0 if inputs.divide_aq is None else int(inputs.divide_aq),
        1,
    )
    packed = _append(packed, int(inputs.mac_mv is not None), 1)
    packed = _append(
        packed,
        0 if inputs.mac_mv is None else int(inputs.mac_mv),
        1,
    )
    packed = _append(packed, int(inputs.shifter_ss is not None), 1)
    return _append(
        packed,
        0 if inputs.shifter_ss is None else int(inputs.shifter_ss),
        1,
    )


def _pack_expected(
    state: StatusRegisters,
    *,
    compare_astat: bool,
    compare_mstat: bool,
    conflict: bool,
) -> int:
    packed = int(compare_astat)
    packed = _append(packed, int(compare_mstat), 1)
    packed = _append(packed, int(conflict), 1)
    packed = _append(
        packed,
        state.astat.to_word().value if compare_astat else 0,
        8,
    )
    return _append(packed, state.mstat.value if compare_mstat else 0, 4)


def generate_lines(random_count: int, seed: int) -> list[str]:
    state = StatusRegisters.reset()
    lines: list[str] = []

    def emit(
        inputs: StatusCycleInputs,
        *,
        compare_astat: bool | None = None,
        compare_mstat: bool = True,
    ) -> None:
        nonlocal state
        astat_known = state.astat.is_fully_known
        do_compare_astat = (
            astat_known if compare_astat is None else compare_astat
        )
        conflict = status_write_conflict(inputs)
        stimulus = _pack_stimulus(inputs)
        expected = _pack_expected(
            state,
            compare_astat=do_compare_astat,
            compare_mstat=compare_mstat,
            conflict=conflict,
        )
        lines.append(f"{stimulus:09x} {expected:04x}")
        state = apply_status_cycle(state, inputs).state

    # The first sampled reset establishes MSTAT. Neither pre-edge state is
    # compared because synthesizable RTL intentionally has no initialization.
    emit(
        StatusCycleInputs(reset=True),
        compare_astat=False,
        compare_mstat=False,
    )
    emit(StatusCycleInputs(), compare_astat=False)
    emit(
        StatusCycleInputs(
            astat_move=ExactWord(8, 0xA5),
            mstat_move=ExactWord(4, 0xA),
        ),
        compare_astat=False,
    )
    emit(StatusCycleInputs())

    for code in ModeControl:
        emit(StatusCycleInputs(mode_controls=(code, code, code, code)))
        emit(StatusCycleInputs())
    for bit in range(4):
        controls = [ModeControl.NO_CHANGE_ZERO] * 4
        controls[bit] = ModeControl.ACTIVATE
        emit(StatusCycleInputs(mode_controls=tuple(controls)))
        emit(StatusCycleInputs())
        controls[bit] = ModeControl.DEACTIVATE
        emit(StatusCycleInputs(mode_controls=tuple(controls)))
        emit(StatusCycleInputs())

    for value in (0x00, 0x01, 0x55, 0x80, 0xAA, 0xFE, 0xFF):
        emit(StatusCycleInputs(astat_move=ExactWord(8, value)))
        emit(StatusCycleInputs())
    for value in range(16):
        emit(StatusCycleInputs(mstat_move=ExactWord(4, value)))
        emit(StatusCycleInputs())

    for bits in range(32):
        emit(
            StatusCycleInputs(
                alu=ALUStatusUpdate(
                    bool(bits & 0x01),
                    bool(bits & 0x02),
                    bool(bits & 0x04),
                    bool(bits & 0x08),
                    bool(bits & 0x10),
                )
            )
        )
        emit(StatusCycleInputs())
    for value in (False, True):
        emit(StatusCycleInputs(divide_aq=value))
        emit(StatusCycleInputs(mac_mv=value))
        emit(StatusCycleInputs(shifter_ss=value))
        emit(StatusCycleInputs())

    # Explicit collision vectors prove that state is unchanged at the next
    # cycle after every detected class.
    collisions = (
        StatusCycleInputs(astat_move=ExactWord(8, 0), mac_mv=True),
        StatusCycleInputs(
            alu=ALUStatusUpdate(False, False, False, False),
            divide_aq=True,
        ),
        StatusCycleInputs(divide_aq=True, shifter_ss=True),
        StatusCycleInputs(mac_mv=True, shifter_ss=True),
        StatusCycleInputs(
            mstat_move=ExactWord(4, 0),
            mode_controls=(
                ModeControl.ACTIVATE,
                ModeControl.NO_CHANGE_ZERO,
                ModeControl.NO_CHANGE_ZERO,
                ModeControl.NO_CHANGE_ZERO,
            ),
        ),
    )
    for collision in collisions:
        emit(collision)
        emit(StatusCycleInputs())

    rng = random.Random(seed)
    controls = list(ModeControl)
    for index in range(random_count):
        if index != 0 and index % 9973 == 0:
            emit(StatusCycleInputs(reset=True))
            continue
        action = rng.randrange(10)
        if action == 0:
            inputs = StatusCycleInputs()
        elif action == 1:
            inputs = StatusCycleInputs(
                astat_move=ExactWord(8, rng.randrange(1 << 8))
            )
        elif action == 2:
            inputs = StatusCycleInputs(
                mstat_move=ExactWord(4, rng.randrange(1 << 4))
            )
        elif action == 3:
            inputs = StatusCycleInputs(
                mode_controls=tuple(rng.choice(controls) for _ in range(4))
            )
        elif action == 4:
            inputs = StatusCycleInputs(
                alu=ALUStatusUpdate(
                    bool(rng.getrandbits(1)),
                    bool(rng.getrandbits(1)),
                    bool(rng.getrandbits(1)),
                    bool(rng.getrandbits(1)),
                    (
                        bool(rng.getrandbits(1))
                        if rng.randrange(4) == 0
                        else None
                    ),
                )
            )
        elif action == 5:
            inputs = StatusCycleInputs(divide_aq=bool(rng.getrandbits(1)))
        elif action == 6:
            inputs = StatusCycleInputs(mac_mv=bool(rng.getrandbits(1)))
        elif action == 7:
            inputs = StatusCycleInputs(shifter_ss=bool(rng.getrandbits(1)))
        elif action == 8:
            inputs = StatusCycleInputs(
                astat_move=ExactWord(8, rng.randrange(1 << 8)),
                shifter_ss=bool(rng.getrandbits(1)),
            )
        else:
            active = [ModeControl.NO_CHANGE_ZERO] * 4
            active[rng.randrange(4)] = rng.choice(
                (ModeControl.DEACTIVATE, ModeControl.ACTIVATE)
            )
            inputs = StatusCycleInputs(
                mstat_move=ExactWord(4, rng.randrange(1 << 4)),
                mode_controls=tuple(active),
            )
        emit(inputs)

    emit(StatusCycleInputs())
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=0x210017)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"wrote {len(lines)} status-register vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
