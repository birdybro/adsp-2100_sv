#!/usr/bin/env python3
"""Generate deterministic shared-PM-owner plus BR/BG differential vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    BusControlMode,
    ExactWord,
    LogicalPhase,
    ProgramBusRequest,
    ProgramOwnerBusControlState,
    UNKNOWN,
    apply_bus_control_cycle,
    apply_program_owner_bus_control_cycle,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def generate_lines(clock_count: int, seed: int) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = ProgramOwnerBusControlState.reset()
    phase = LogicalPhase.STATE_8
    br_n = True
    lines: list[str] = []
    coverage = {name: 0 for name in (
        "fetch", "type5", "type13", "recognized", "completion_delay",
        "blocked", "grant", "release", "resume", "resume_accept",
        "masked", "conflict",
    )}

    def emit(
        *,
        reset: bool = False,
        advance: bool = True,
        valids: tuple[bool, bool, bool] = (False,) * 3,
        addresses: tuple[int, int, int] = (0, 0, 0),
        address_known: tuple[bool, bool, bool] = (True,) * 3,
        writes: tuple[bool, bool, bool] = (False,) * 3,
        write_data: tuple[int, int, int] = (0, 0, 0),
        write_known: tuple[bool, bool, bool] = (True,) * 3,
        read_data: int = 0,
        read_known: bool = True,
    ) -> None:
        nonlocal state, phase
        requests: list[ProgramBusRequest | None] = []
        for index in range(3):
            if not valids[index]:
                requests.append(None)
                continue
            requests.append(ProgramBusRequest(
                address=(ExactWord(14, addresses[index])
                         if address_known[index] else UNKNOWN),
                data_access=index != 0,
                write=writes[index] if index else False,
                write_data=(ExactWord(24, write_data[index])
                            if write_known[index] else UNKNOWN),
            ))
        pre_mode = state.control.mode
        result = apply_program_owner_bus_control_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            br_n=br_n,
            fetch_request=requests[0],
            type5_request=requests[1],
            type13_request=requests[2],
            pmd_read_data=(ExactWord(24, read_data) if read_known else UNKNOWN),
        )

        stimulus = 0
        for value, width in (
            (reset, 1), (int(phase), 3), (advance, 1), (br_n, 1),
        ):
            stimulus = _append(stimulus, value, width)
        for index in range(3):
            fields = [
                (valids[index], 1), (addresses[index], 14),
                (address_known[index], 1),
            ]
            if index != 0:
                fields.extend((
                    (writes[index], 1), (write_data[index], 24),
                    (write_known[index], 1),
                ))
            for value, width in fields:
                stimulus = _append(stimulus, value, width)
        stimulus = _append(stimulus, read_data, 24)
        stimulus = _append(stimulus, read_known, 1)

        control = result.control
        control_pre = 0
        for value, width in (
            (int(state.control.mode), 3),
            (control.state_three_boundary, 1),
            (control.request_recognized, 1),
            (control.grant_assert_event, 1),
            (control.release_recognized, 1),
            (control.grant_release_event, 1),
            (control.resume_event, 1),
            (control.request_withdrawn, 1),
            (control.release_cancelled, 1),
            (control.instruction_issue_inhibit, 1),
            (control.bus_relinquished, 1),
            (control.bg_n, 1),
            (control.reset_br_request, 1),
            (result.native_bg_n, 1),
            (result.native_bus_relinquished, 1),
            (result.request_blocked, 1),
        ):
            control_pre = _append(control_pre, value, width)

        owner = result.owner_bus
        bus = owner.bus
        owner_pre = 0
        for value, width in (
            (result.request_ready, 1), (owner.request_conflict, 1),
            (owner.request_out_of_phase, 1),
            (owner.fetch_accepted | (owner.type5_accepted << 1)
             | (owner.type13_accepted << 2), 3),
            (owner.fetch_completion | (owner.type5_completion << 1)
             | (owner.type13_completion << 2), 3),
            ((owner.fetch_completion and bus.read_sample_event)
             | ((owner.type5_completion and bus.read_sample_event) << 1)
             | ((owner.type13_completion and bus.read_sample_event) << 2), 3),
            (int(state.owner_bus.owner), 2),
            (state.owner_bus.bus.active, 1),
            (state.owner_bus.bus.response_valid, 1),
            (state.owner_bus.bus.response_write, 1),
            (state.owner_bus.bus.read_data.value
             if isinstance(state.owner_bus.bus.read_data, ExactWord) else 0, 24),
            (isinstance(state.owner_bus.bus.read_data, ExactWord), 1),
            (bus.address_output_enable, 1),
            (bus.control_output_enable, 1),
            (bus.data_output_enable, 1),
            (bus.address, 14), (bus.address_known, 1),
            (bus.pmda, 1), (bus.control_output_enable, 1),
            (bus.pms_n, 1), (bus.pmrd_n, 1), (bus.pmwr_n, 1),
            (bus.write_data, 24), (bus.write_data_known, 1),
        ):
            owner_pre = _append(owner_pre, value, width)

        next_bus = result.state.owner_bus.bus
        post = 0
        for value, width in (
            (int(result.state.control.mode), 3),
            (int(result.state.owner_bus.owner), 2),
            (next_bus.active, 1),
            (next_bus.response_valid, 1),
            (next_bus.response_write, 1),
            (next_bus.read_data.value
             if isinstance(next_bus.read_data, ExactWord) else 0, 24),
            (isinstance(next_bus.read_data, ExactWord), 1),
        ):
            post = _append(post, value, width)
        lines.append(
            f"{stimulus:033x} {control_pre:05x} {owner_pre:023x} {post:09x}"
        )

        for key, hit in (
            ("fetch", owner.fetch_accepted),
            ("type5", owner.type5_accepted),
            ("type13", owner.type13_accepted),
            ("recognized", control.request_recognized),
            ("completion_delay", bus.completion_event
             and pre_mode is BusControlMode.REQUEST_DELAY),
            ("blocked", result.request_blocked),
            ("grant", not result.native_bg_n),
            ("release", control.grant_release_event),
            ("resume", control.resume_event),
            ("resume_accept", control.resume_event
             and owner.accepted_owner.value != 0),
            ("masked", result.native_bus_relinquished
             and not bus.address_output_enable
             and not bus.control_output_enable
             and not bus.data_output_enable),
            ("conflict", owner.request_conflict),
        ):
            coverage[key] += int(hit)
        state = result.state
        if advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True)
    phase = LogicalPhase.STATE_8
    for _ in range(clock_count):
        mode = state.control.mode
        if mode is BusControlMode.IDLE:
            if phase is LogicalPhase.STATE_1 and rng.randrange(48) == 0:
                br_n = False
            elif br_n is False:
                br_n = False
        elif mode is BusControlMode.REQUEST_DELAY:
            br_n = False
        elif mode is BusControlMode.GRANTED:
            if phase is LogicalPhase.STATE_1 and rng.randrange(3) == 0:
                br_n = True
        else:
            br_n = True

        advance = rng.randrange(13) != 0
        preview = apply_bus_control_cycle(
            state.control,
            phase=phase,
            phase_advance=advance,
            br_n=br_n,
        )
        if phase is LogicalPhase.STATE_8 and advance:
            mode_choice = rng.randrange(10)
            if mode_choice < 7:
                selected = rng.randrange(3)
                valids = tuple(index == selected for index in range(3))
            elif mode_choice < 9:
                valids = (False, False, False)
            else:
                first = rng.randrange(3)
                second = (first + 1 + rng.randrange(2)) % 3
                valids = tuple(index in (first, second) for index in range(3))
        elif preview.instruction_issue_inhibit and rng.randrange(5) == 0:
            selected = rng.randrange(3)
            valids = tuple(index == selected for index in range(3))
        else:
            valids = tuple(rng.randrange(151) == 0 for _ in range(3))
        emit(
            advance=advance,
            valids=valids,
            addresses=tuple(rng.randrange(1 << 14) for _ in range(3)),
            address_known=tuple(rng.randrange(23) != 0 for _ in range(3)),
            writes=(False, bool(rng.randrange(2)), bool(rng.randrange(2))),
            write_data=tuple(rng.randrange(1 << 24) for _ in range(3)),
            write_known=tuple(rng.randrange(19) != 0 for _ in range(3)),
            read_data=rng.randrange(1 << 24),
            read_known=rng.randrange(17) != 0,
        )
    br_n = False
    emit(reset=True)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clocks", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x2100B9
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.clocks, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} shared-PM-owner/BR-BG clocks "
        f"seed={args.seed:#x} "
        + " ".join(f"{key}={value}" for key, value in coverage.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
