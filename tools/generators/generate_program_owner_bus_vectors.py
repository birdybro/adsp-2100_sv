#!/usr/bin/env python3
"""Generate deterministic shared-PM-owner model/RTL differential vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model.model import ExactWord, UNKNOWN  # noqa: E402
from sim.reference_models.adsp2100_model.phase import LogicalPhase  # noqa: E402
from sim.reference_models.adsp2100_model.program_bus import ProgramBusRequest  # noqa: E402
from sim.reference_models.adsp2100_model.program_owner_bus import (  # noqa: E402
    ProgramOwnerBusState,
    apply_program_owner_bus_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def generate_lines(random_count: int, seed: int) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = ProgramOwnerBusState.reset()
    phase = LogicalPhase.STATE_8
    lines: list[str] = []
    coverage = {name: 0 for name in (
        "fetch", "type5", "type13", "conflict", "out_of_phase",
        "completion", "owner_switch", "relinquished", "nondata_owner",
    )}

    def emit(
        *, reset: bool = False, phase_override: LogicalPhase | None = None,
        advance: bool = True, valids: tuple[bool, bool, bool] = (False,) * 3,
        addresses: tuple[int, int, int] = (0, 0, 0),
        address_known: tuple[bool, bool, bool] = (True,) * 3,
        data_access: tuple[bool, bool, bool] = (False, True, True),
        writes: tuple[bool, bool, bool] = (False,) * 3,
        write_data: tuple[int, int, int] = (0, 0, 0),
        write_known: tuple[bool, bool, bool] = (True,) * 3,
        read_data: int = 0, read_known: bool = True,
        relinquished: bool = False,
    ) -> None:
        nonlocal state, phase
        use_phase = phase if phase_override is None else phase_override
        requests: list[ProgramBusRequest | None] = []
        for index in range(3):
            if not valids[index]:
                requests.append(None)
                continue
            requests.append(ProgramBusRequest(
                address=(ExactWord(14, addresses[index])
                         if address_known[index] else UNKNOWN),
                data_access=data_access[index],
                write=writes[index] if index else False,
                write_data=(ExactWord(24, write_data[index])
                            if write_known[index] else UNKNOWN),
            ))
        result = apply_program_owner_bus_cycle(
            state, reset=reset, phase=use_phase, phase_advance=advance,
            fetch_request=requests[0], type5_request=requests[1],
            type13_request=requests[2],
            pmd_read_data=(ExactWord(24, read_data) if read_known else UNKNOWN),
            bus_relinquished=relinquished,
        )
        stimulus = 0
        stimulus = _append(stimulus, reset, 1)
        stimulus = _append(stimulus, int(use_phase), 3)
        stimulus = _append(stimulus, advance, 1)
        for index in range(3):
            fields = [
                (valids[index], 1), (addresses[index], 14),
                (address_known[index], 1),
            ]
            if index != 0:
                fields.extend(((data_access[index], 1),
                               (writes[index], 1),
                               (write_data[index], 24),
                               (write_known[index], 1)))
            for value, width in fields:
                stimulus = _append(stimulus, value, width)
        stimulus = _append(stimulus, read_data, 24)
        stimulus = _append(stimulus, read_known, 1)
        stimulus = _append(stimulus, relinquished, 1)

        bus = result.bus
        pre = 0
        for value, width in (
            (bus.request_ready, 1), (result.request_conflict, 1),
            (result.request_out_of_phase, 1),
            (result.fetch_accepted | (result.type5_accepted << 1)
             | (result.type13_accepted << 2), 3),
            (result.fetch_completion | (result.type5_completion << 1)
             | (result.type13_completion << 2), 3),
            ((result.fetch_completion and bus.read_sample_event)
             | ((result.type5_completion and bus.read_sample_event) << 1)
             | ((result.type13_completion and bus.read_sample_event) << 2), 3),
            (int(state.owner), 2), (state.bus.active, 1),
            (state.bus.response_valid, 1), (state.bus.response_write, 1),
            (state.bus.read_data.value if isinstance(state.bus.read_data, ExactWord) else 0, 24),
            (isinstance(state.bus.read_data, ExactWord), 1),
            (bus.address_output_enable, 1), (bus.control_output_enable, 1),
            (bus.data_output_enable, 1), (bus.address, 14),
            (bus.address_known, 1), (bus.pmda, 1),
            (bus.control_output_enable, 1), (bus.pms_n, 1),
            (bus.pmrd_n, 1), (bus.pmwr_n, 1), (bus.write_data, 24),
            (bus.write_data_known, 1),
        ):
            pre = _append(pre, value, width)
        post = 0
        next_read = result.state.bus.read_data
        for value, width in (
            (int(result.state.owner), 2), (result.state.bus.active, 1),
            (result.state.bus.response_valid, 1),
            (result.state.bus.response_write, 1),
            (next_read.value if isinstance(next_read, ExactWord) else 0, 24),
            (isinstance(next_read, ExactWord), 1),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:034x} {pre:023x} {post:08x}")

        old_owner = state.owner
        state = result.state
        for key, hit in (
            ("fetch", result.fetch_accepted), ("type5", result.type5_accepted),
            ("type13", result.type13_accepted),
            ("conflict", result.request_conflict),
            ("out_of_phase", result.request_out_of_phase),
            ("completion", result.bus.completion_event),
            ("owner_switch", old_owner != state.owner and bool(state.owner)),
            ("relinquished", relinquished and state.bus.active),
            ("nondata_owner", (result.type5_accepted or result.type13_accepted)
             and not data_access[int(result.accepted_owner) - 1]),
        ):
            coverage[key] += int(hit)
        if phase_override is None and advance and not relinquished:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True)
    emit(valids=(True, False, False), addresses=(1, 0, 0))
    emit(phase_override=LogicalPhase.STATE_8, valids=(True, True, False))
    emit(phase_override=LogicalPhase.STATE_8, valids=(False, True, False),
         addresses=(0, 2, 0))
    emit(phase_override=LogicalPhase.STATE_7, advance=False,
         valids=(False, False, True), relinquished=True)
    emit(phase_override=LogicalPhase.STATE_7, read_data=0x123456)

    for _ in range(random_count):
        ready_boundary = phase == LogicalPhase.STATE_8
        advance = rng.randrange(9) != 0
        relinquished = rng.randrange(47) == 0
        if ready_boundary and advance and not relinquished:
            mode = rng.randrange(10)
            if mode < 6:
                selected = rng.randrange(3)
                valids = tuple(index == selected for index in range(3))
            elif mode < 8:
                valids = (False, False, False)
            else:
                first = rng.randrange(3)
                second = (first + 1 + rng.randrange(2)) % 3
                valids = tuple(index in (first, second) for index in range(3))
        else:
            valids = tuple(rng.randrange(97) == 0 for _ in range(3))
        emit(
            advance=advance, valids=valids,
            addresses=tuple(rng.randrange(1 << 14) for _ in range(3)),
            address_known=tuple(rng.randrange(19) != 0 for _ in range(3)),
            data_access=(False, bool(rng.randrange(2)), bool(rng.randrange(2))),
            writes=(False, bool(rng.randrange(2)), bool(rng.randrange(2))),
            write_data=tuple(rng.randrange(1 << 24) for _ in range(3)),
            write_known=tuple(rng.randrange(17) != 0 for _ in range(3)),
            read_data=rng.randrange(1 << 24), read_known=rng.randrange(13) != 0,
            relinquished=relinquished,
        )
    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x2100A3)
    args = parser.parse_args()
    lines, coverage = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} shared-PM-owner vectors seed=0x{args.seed:x} "
          + " ".join(f"{key}={value}" for key, value in coverage.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
