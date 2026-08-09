#!/usr/bin/env python3
"""Generate deterministic shared-DM-owner model/RTL differential vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model.data_bus import DataBusRequest  # noqa: E402
from sim.reference_models.adsp2100_model.data_owner_bus import (  # noqa: E402
    DataOwnerBusState,
    apply_data_owner_bus_cycle,
)
from sim.reference_models.adsp2100_model.model import ExactWord, UNKNOWN  # noqa: E402
from sim.reference_models.adsp2100_model.phase import LogicalPhase  # noqa: E402


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _word(value: ExactWord | object) -> tuple[int, bool]:
    if isinstance(value, ExactWord):
        return value.value, True
    return 0, False


def generate_lines(
    random_count: int, seed: int
) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = DataOwnerBusState.reset()
    phase = LogicalPhase.STATE_8
    lines: list[str] = []
    coverage = {
        name: 0
        for name in (
            "fetched",
            "companion",
            "conflict",
            "out_of_phase",
            "dmack_low",
            "dmack_high",
            "completion",
            "read",
            "write",
            "owner_switch",
            "relinquished",
            "unknown_address",
            "unknown_write_data",
        )
    }

    def emit(
        *,
        reset: bool = False,
        phase_override: LogicalPhase | None = None,
        advance: bool = True,
        valids: tuple[bool, bool] = (False, False),
        addresses: tuple[int, int] = (0, 0),
        address_known: tuple[bool, bool] = (True, True),
        writes: tuple[bool, bool] = (False, False),
        write_data: tuple[int, int] = (0, 0),
        write_known: tuple[bool, bool] = (True, True),
        dm_ack: bool = True,
        read_data: int = 0,
        read_known: bool = True,
        relinquished: bool = False,
    ) -> None:
        nonlocal state, phase
        use_phase = phase if phase_override is None else phase_override
        requests: list[DataBusRequest | None] = []
        for index in range(2):
            if not valids[index]:
                requests.append(None)
                continue
            requests.append(
                DataBusRequest(
                    address=(
                        ExactWord(14, addresses[index])
                        if address_known[index]
                        else UNKNOWN
                    ),
                    write=writes[index],
                    write_data=(
                        ExactWord(16, write_data[index])
                        if write_known[index]
                        else UNKNOWN
                    ),
                )
            )
        result = apply_data_owner_bus_cycle(
            state,
            reset=reset,
            phase=use_phase,
            phase_advance=advance,
            fetched_request=requests[0],
            companion_request=requests[1],
            dm_ack=dm_ack,
            dmd_read_data=(ExactWord(16, read_data) if read_known else UNKNOWN),
            bus_relinquished=relinquished,
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(use_phase), 3),
            (advance, 1),
            (valids[0], 1),
            (addresses[0], 14),
            (address_known[0], 1),
            (writes[0], 1),
            (write_data[0], 16),
            (write_known[0], 1),
            (valids[1], 1),
            (addresses[1], 14),
            (address_known[1], 1),
            (writes[1], 1),
            (write_data[1], 16),
            (write_known[1], 1),
            (dm_ack, 1),
            (read_data, 16),
            (read_known, 1),
            (relinquished, 1),
        ):
            stimulus = _append(stimulus, value, width)

        bus = result.bus
        accepted = result.fetched_accepted | (result.companion_accepted << 1)
        dmack_sample = result.fetched_dmack_sample | (
            result.companion_dmack_sample << 1
        )
        dmack_accepted = result.fetched_dmack_accepted | (
            result.companion_dmack_accepted << 1
        )
        wait_extension = result.fetched_wait_extension | (
            result.companion_wait_extension << 1
        )
        completion = result.fetched_completion | (
            result.companion_completion << 1
        )
        read_sample = result.fetched_read_sample | (
            result.companion_read_sample << 1
        )
        response_data, response_data_known = _word(state.bus.read_data)
        response_data_valid = bool(
            state.bus.response_valid
            and not state.bus.response_write
            and response_data_known
        )
        pre = 0
        for value, width in (
            (bus.request_ready, 1),
            (result.request_conflict, 1),
            (result.request_out_of_phase, 1),
            (accepted, 2),
            (dmack_sample, 2),
            (dmack_accepted, 2),
            (wait_extension, 2),
            (completion, 2),
            (read_sample, 2),
            (int(state.owner), 2),
            (state.bus.active, 1),
            (bus.waiting, 1),
            (bus.address_output_enable, 1),
            (bus.control_output_enable, 1),
            (bus.data_output_enable, 1),
            (bus.address, 14),
            (bus.address_known, 1),
            (bus.dms_n, 1),
            (bus.dmrd_n, 1),
            (bus.dmwr_n, 1),
            (bus.write_data, 16),
            (bus.write_data_known, 1),
            (state.bus.response_valid, 1),
            (state.bus.response_write, 1),
            (response_data, 16),
            (response_data_valid, 1),
        ):
            pre = _append(pre, value, width)

        post_address, post_address_known = _word(result.state.bus.address)
        post_write_data, post_write_data_known = _word(
            result.state.bus.write_data
        )
        post_read_data, post_read_data_known = _word(
            result.state.bus.read_data
        )
        post = 0
        for value, width in (
            (int(result.state.owner), 2),
            (result.state.bus.active, 1),
            (post_address, 14),
            (post_address_known, 1),
            (result.state.bus.write, 1),
            (post_write_data, 16),
            (post_write_data_known, 1),
            (result.state.bus.waiting, 1),
            (result.state.bus.acknowledged, 1),
            (result.state.bus.response_valid, 1),
            (result.state.bus.response_write, 1),
            (post_read_data, 16),
            (post_read_data_known, 1),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:023x} {pre:019x} {post:015x}")

        old_owner = state.owner
        state = result.state
        coverage["fetched"] += int(result.fetched_accepted)
        coverage["companion"] += int(result.companion_accepted)
        coverage["conflict"] += int(result.request_conflict)
        coverage["out_of_phase"] += int(result.request_out_of_phase)
        coverage["dmack_low"] += int(bus.wait_extension_event)
        coverage["dmack_high"] += int(bus.dmack_accepted)
        coverage["completion"] += int(bus.completion_event)
        coverage["read"] += int(bus.completion_event and not state.bus.write)
        coverage["write"] += int(bus.completion_event and state.bus.write)
        coverage["owner_switch"] += int(
            old_owner != state.owner and bool(state.owner)
        )
        coverage["relinquished"] += int(relinquished and state.bus.active)
        coverage["unknown_address"] += int(
            any(valids[index] and not address_known[index] for index in range(2))
        )
        coverage["unknown_write_data"] += int(
            any(
                valids[index] and writes[index] and not write_known[index]
                for index in range(2)
            )
        )
        if phase_override is None and advance and not relinquished:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True)
    emit(valids=(True, False), addresses=(1, 0))
    emit(phase_override=LogicalPhase.STATE_8, valids=(True, True))
    emit(
        phase_override=LogicalPhase.STATE_8,
        valids=(False, True),
        writes=(False, True),
        write_data=(0, 0xCAFE),
    )
    emit(
        phase_override=LogicalPhase.STATE_6,
        dm_ack=False,
        valids=(True, False),
    )
    emit(phase_override=LogicalPhase.STATE_8, valids=(True, False))
    emit(phase_override=LogicalPhase.STATE_6, dm_ack=True)
    emit(phase_override=LogicalPhase.STATE_7)
    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    phase = LogicalPhase.STATE_8

    for _ in range(random_count):
        advance = rng.randrange(9) != 0
        relinquished = rng.randrange(127) == 0
        ready = bool(
            phase == LogicalPhase.STATE_8
            and advance
            and not relinquished
            and (not state.bus.active or state.bus.response_valid)
        )
        if ready:
            mode = rng.randrange(10)
            if mode < 7:
                selected = rng.randrange(2)
                valids = (selected == 0, selected == 1)
            elif mode < 9:
                valids = (False, False)
            else:
                valids = (True, True)
        else:
            valids = (
                rng.randrange(257) == 0,
                rng.randrange(257) == 0,
            )
        emit(
            advance=advance,
            valids=valids,
            addresses=(rng.randrange(1 << 14), rng.randrange(1 << 14)),
            address_known=(rng.randrange(17) != 0, rng.randrange(17) != 0),
            writes=(bool(rng.randrange(2)), bool(rng.randrange(2))),
            write_data=(rng.randrange(1 << 16), rng.randrange(1 << 16)),
            write_known=(rng.randrange(13) != 0, rng.randrange(13) != 0),
            dm_ack=rng.randrange(5) != 0,
            read_data=rng.randrange(1 << 16),
            read_known=rng.randrange(11) != 0,
            relinquished=relinquished,
        )
    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0xDADA2101
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} shared-DM-owner vectors "
        f"seed=0x{args.seed:x} "
        + " ".join(f"{key}={value}" for key, value in coverage.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
