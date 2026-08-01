#!/usr/bin/env python3
"""Generate deterministic original ADSP-2100 native DM phase vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DataBusRequest,
    DataBusState,
    ExactWord,
    LogicalPhase,
    UNKNOWN,
    apply_data_bus_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _word_value(value: ExactWord | object) -> tuple[int, bool]:
    if isinstance(value, ExactWord):
        return value.value, True
    return 0, False


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DataBusState.reset()
    phase = LogicalPhase.STATE_8
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        phase_override: LogicalPhase | int | None = None,
        phase_advance: bool = True,
        request_valid: bool = False,
        address: int = 0,
        address_valid: bool = True,
        write: bool = False,
        write_data: int = 0,
        write_data_valid: bool = True,
        dm_ack: bool = True,
        read_data: int = 0,
        read_data_valid: bool = True,
        bus_relinquished: bool = False,
    ) -> None:
        nonlocal state, phase
        use_phase = (
            phase if phase_override is None else LogicalPhase(phase_override)
        )
        request = None
        if request_valid:
            request = DataBusRequest(
                address=(
                    ExactWord(14, address) if address_valid else UNKNOWN
                ),
                write=write,
                write_data=(
                    ExactWord(16, write_data)
                    if write_data_valid else UNKNOWN
                ),
            )
        dmd = ExactWord(16, read_data) if read_data_valid else UNKNOWN
        result = apply_data_bus_cycle(
            state,
            reset=reset,
            phase=use_phase,
            phase_advance=phase_advance,
            request=request,
            dm_ack=dm_ack,
            dmd_read_data=dmd,
            bus_relinquished=bus_relinquished,
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(use_phase), 3),
            (phase_advance, 1),
            (request_valid, 1),
            (address, 14),
            (address_valid, 1),
            (write, 1),
            (write_data, 16),
            (write_data_valid, 1),
            (dm_ack, 1),
            (read_data, 16),
            (read_data_valid, 1),
            (bus_relinquished, 1),
        ):
            stimulus = _append(stimulus, value, width)

        pre = 0
        for value, width in (
            (result.request_ready, 1),
            (result.request_accepted, 1),
            (result.dmack_sample_event, 1),
            (result.dmack_accepted, 1),
            (result.wait_extension_event, 1),
            (result.completion_event, 1),
            (result.read_sample_event, 1),
            (state.active, 1),
            (result.waiting, 1),
            (result.address_output_enable, 1),
            (result.control_output_enable, 1),
            (result.data_output_enable, 1),
            (result.address, 14),
            (result.address_known, 1),
            (result.dms_n, 1),
            (result.dmrd_n, 1),
            (result.dmwr_n, 1),
            (result.write_data, 16),
            (result.write_data_known, 1),
        ):
            pre = _append(pre, value, width)

        post_address, post_address_known = _word_value(result.state.address)
        post_write_data, post_write_data_known = _word_value(
            result.state.write_data
        )
        post_read_data, post_read_data_known = _word_value(
            result.state.read_data
        )
        post = 0
        for value, width in (
            (result.state.active, 1),
            (post_address, 14),
            (post_address_known, 1),
            (result.state.write, 1),
            (post_write_data, 16),
            (post_write_data_known, 1),
            (result.state.waiting, 1),
            (result.state.acknowledged, 1),
            (result.state.response_valid, 1),
            (result.state.response_write, 1),
            (post_read_data, 16),
            (post_read_data_known, 1),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:015x} {pre:012x} {post:014x}")
        state = result.state
        if phase_override is None and phase_advance and not bus_relinquished:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, phase_override=LogicalPhase.STATE_8)

    # One read with two low samples, completion, and a back-to-back write.
    emit(request_valid=True, address=0x1234, write=False)
    for _ in range(5):
        emit(read_data=0x1111)
    emit(dm_ack=False)
    emit(dm_ack=True, read_data=0x2222)
    for _ in range(6):
        emit(dm_ack=True, read_data=0x3333)
    emit(dm_ack=False)
    emit(dm_ack=True, read_data=0x4444)
    for _ in range(6):
        emit(dm_ack=True, read_data=0x5555)
    emit(dm_ack=True)
    emit(dm_ack=True, read_data=0xCAFE)
    emit(
        request_valid=True,
        address=0x2345,
        write=True,
        write_data=0xBEEF,
    )
    for _ in range(5):
        emit()
    emit(dm_ack=True)
    emit()
    emit()

    # Unknown descriptor fields, phase hold, relinquishment, and reset.
    emit(
        phase_override=LogicalPhase.STATE_8,
        request_valid=True,
        address_valid=False,
        write=True,
        write_data_valid=False,
    )
    emit(
        phase_override=LogicalPhase.STATE_6,
        phase_advance=False,
        dm_ack=True,
    )
    emit(
        phase_override=LogicalPhase.STATE_6,
        bus_relinquished=True,
        dm_ack=True,
    )
    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    phase = LogicalPhase.STATE_8

    for _ in range(random_count):
        advance = rng.randrange(9) != 0
        relinquished = rng.randrange(127) == 0
        ready_slot = (
            phase == LogicalPhase.STATE_8
            and advance
            and not relinquished
            and (not state.active or state.response_valid)
        )
        request_valid = ready_slot and rng.randrange(5) != 0
        # Occasionally present a request while not ready to check rejection.
        if not ready_slot and rng.randrange(257) == 0:
            request_valid = True
        emit(
            phase_advance=advance,
            request_valid=request_valid,
            address=rng.randrange(1 << 14),
            address_valid=bool(rng.randrange(17)),
            write=bool(rng.randrange(2)),
            write_data=rng.randrange(1 << 16),
            write_data_valid=bool(rng.randrange(13)),
            dm_ack=rng.randrange(5) != 0,
            read_data=rng.randrange(1 << 16),
            read_data_valid=bool(rng.randrange(11)),
            bus_relinquished=relinquished,
        )

    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0xDADA2100
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} original DM-bus phase vectors "
        f"seed=0x{args.seed:x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
