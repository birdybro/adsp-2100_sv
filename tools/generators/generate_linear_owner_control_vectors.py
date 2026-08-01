#!/usr/bin/env python3
"""Generate deterministic retained-fetch/shared-PM/BR-BG vectors."""

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
    LinearOwnerControlState,
    LogicalPhase,
    ProgramBusOwner,
    ProgramBusRequest,
    UNKNOWN,
    apply_linear_owner_control_cycle,
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


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _type6(destination: int, data: int) -> int:
    return 0x400000 | ((data & 0xFFFF) << 4) | destination


def _type7(code: int, data: int) -> int:
    return (
        0x300000
        | ((code >> 4) << 18)
        | ((data & 0x3FFF) << 4)
        | (code & 0xF)
    )


def _type9_nop(rng: random.Random) -> int:
    """Return a legal Type 9 AMF-zero word with no architectural write."""
    return (
        0x200000
        | (rng.randrange(2) << 18)
        | (rng.randrange(4) << 11)
        | (rng.randrange(8) << 8)
        | rng.randrange(16)
    )


def _type15(rng: random.Random) -> int:
    return (
        0x0F0000
        | (rng.randrange(8) << 11)
        | (rng.choice(LEGAL_SHIFTER_XOPS) << 8)
        | rng.randrange(256)
    )


def _type16(rng: random.Random) -> int:
    return (
        0x0E0000
        | (rng.randrange(16) << 11)
        | (rng.choice(LEGAL_SHIFTER_XOPS) << 8)
        | rng.randrange(16)
    )


def _legal_opcode(rng: random.Random) -> int:
    choice = rng.randrange(17)
    if choice < 2:
        return 0
    if choice < 7:
        return _type6(rng.randrange(16), rng.randrange(1 << 16))
    if choice < 10:
        return _type7(rng.choice(LEGAL_TYPE7_CODES), rng.randrange(1 << 14))
    if choice < 12:
        return 0x0C0000 | (rng.randrange(256) << 4)
    if choice < 13:
        return _type9_nop(rng)
    if choice < 15:
        return _type15(rng)
    return _type16(rng)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return (True, value.value)
    return (False, 0)


def generate_lines(clock_count: int, seed: int) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = LinearOwnerControlState.reset()
    phase = LogicalPhase.STATE_8
    br_n = True
    lines: list[str] = []
    coverage = {key: 0 for key in (
        "fetch_accept", "fetch_retry", "fetch_complete", "type5_accept",
        "type13_accept", "collision", "recognized", "grant", "resume",
        "masked",
        "type9_retire",
        "type15_retire", "type16_retire",
    )}

    def emit(
        *,
        reset: bool = False,
        advance: bool = True,
        setup: tuple[int, int] | None = None,
        type5: ProgramBusRequest | None = None,
        type13: ProgramBusRequest | None = None,
        pmd: int = 0,
        pmd_valid: bool = True,
        probe: int | None = None,
    ) -> None:
        nonlocal state, phase
        if probe is None:
            probe = rng.choice(READABLE_CODES)
        setup_value = (
            None
            if setup is None
            else (ExactWord(14, setup[0]), ExactWord(24, setup[1]))
        )
        result = apply_linear_owner_control_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            br_n=br_n,
            instruction_setup=setup_value,
            type5_request=type5,
            type13_request=type13,
            pmd_read_data=ExactWord(24, pmd) if pmd_valid else UNKNOWN,
        )
        coverage["type9_retire"] += int(
            result.core.retire_event
            and isinstance(state.core.instruction, ExactWord)
            and state.core.instruction.value & 0xF800F0 == 0x200000
        )
        coverage["type15_retire"] += int(
            result.core.retire_event
            and isinstance(state.core.instruction, ExactWord)
            and state.core.instruction.value & 0xFF8000 == 0x0F0000
        )
        coverage["type16_retire"] += int(
            result.core.retire_event
            and isinstance(state.core.instruction, ExactWord)
            and state.core.instruction.value & 0xFF80F0 == 0x0E0000
        )

        stimulus = 0
        values: list[tuple[int | bool, int]] = [
            (reset, 1), (int(phase), 3), (advance, 1), (br_n, 1),
            (setup is not None, 1),
            (0 if setup is None else setup[0], 14),
            (0 if setup is None else setup[1], 24),
        ]
        for request in (type5, type13):
            address_known = bool(
                request is not None
                and isinstance(request.address, ExactWord)
            )
            data_known = bool(
                request is not None
                and isinstance(request.write_data, ExactWord)
            )
            values.extend((
                (request is not None, 1),
                (
                    request.address.value
                    if address_known and isinstance(request.address, ExactWord)
                    else 0,
                    14,
                ),
                (address_known, 1),
                (False if request is None else request.data_access, 1),
                (False if request is None else request.write, 1),
                (
                    request.write_data.value
                    if data_known and isinstance(request.write_data, ExactWord)
                    else 0,
                    24,
                ),
                (data_known, 1),
            ))
        values.extend(((pmd, 24), (pmd_valid, 1), (probe, 6)))
        for value, width in values:
            stimulus = _append(stimulus, value, width)

        owner = result.interface.owner_bus
        bus = owner.bus
        core = result.core
        opcode_known, opcode_value = _exact(state.core.instruction)
        events = 0
        for value, width in (
            (core.issue_boundary, 1),
            (core.instruction_setup_accepted, 1),
            (core.fetch_request_presented, 1),
            (owner.fetch_accepted, 1),
            (result.fetch_retry_pending, 1),
            (core.instruction_issue, 1),
            (core.retire_event, 1),
            (state.core.instruction_valid, 1),
            (state.core.pending, 1),
            (core.unsupported_instruction, 1),
            (core.reserved_subencoding, 1),
            (core.phase_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (core.provisional_source_extension, 1),
            (0 if reset else state.core.architecture.pc.value, 14),
            (opcode_known, 1), (opcode_value, 24),
            (int(state.interface.control.mode), 3),
            (result.interface.control.request_recognized, 1),
            (result.interface.control.grant_assert_event, 1),
            (result.interface.control.release_recognized, 1),
            (result.interface.control.grant_release_event, 1),
            (result.interface.control.resume_event, 1),
            (result.interface.control.instruction_issue_inhibit, 1),
            (result.interface.native_bg_n, 1),
            (result.interface.native_bus_relinquished, 1),
            (result.interface.request_blocked, 1),
            (owner.request_conflict, 1), (owner.request_out_of_phase, 1),
            (owner.fetch_accepted | (owner.type5_accepted << 1)
             | (owner.type13_accepted << 2), 3),
            (owner.fetch_completion | (owner.type5_completion << 1)
             | (owner.type13_completion << 2), 3),
            (int(state.interface.owner_bus.owner), 2),
            (state.interface.owner_bus.bus.active, 1),
            (bus.address_output_enable, 1),
            (bus.control_output_enable, 1),
            (bus.data_output_enable, 1),
            (bus.address_known, 1),
            (bus.address if bus.address_known else 0, 14),
            (bus.pmda, 1), (bus.control_output_enable, 1),
            (bus.pms_n, 1), (bus.pmrd_n, 1), (bus.pmwr_n, 1),
            (bus.write_data_known, 1),
            (bus.write_data if bus.write_data_known else 0, 24),
        ):
            events = _append(events, value, width)

        post_state = result.state
        post_opcode_known, post_opcode = _exact(post_state.core.instruction)
        cntr_valid, cntr_value = _exact(post_state.core.architecture.cntr)
        post = 0
        for value, width in (
            (int(post_state.interface.control.mode), 3),
            (post_state.core.instruction_valid, 1),
            (post_state.core.pending, 1),
            (post_state.core.architecture.pc.value, 14),
            (post_opcode_known, 1), (post_opcode, 24),
            (post_state.core.architecture.mstat.value, 4),
            (post_state.core.architecture.imask.value, 4),
            (cntr_valid, 1), (cntr_value, 14),
            (post_state.core.architecture.sstat.value, 8),
            (bool(post_state.core.architecture.mstat.value & 1), 1),
            (len(post_state.core.architecture.count_stack), 3),
            (bool(post_state.core.architecture.sstat.value & 0x08), 1),
            (int(post_state.interface.owner_bus.owner), 2),
            (post_state.interface.owner_bus.bus.active, 1),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:041x} {events:064x} {post:048x}")

        for key, hit in (
            ("fetch_accept", owner.fetch_accepted),
            ("fetch_retry", result.fetch_retry_pending),
            ("fetch_complete", owner.fetch_completion),
            ("type5_accept", owner.type5_accepted),
            ("type13_accept", owner.type13_accepted),
            ("collision", owner.request_conflict),
            ("recognized", result.interface.control.request_recognized),
            ("grant", not result.interface.native_bg_n),
            ("resume", result.interface.control.resume_event),
            ("masked", result.interface.native_bus_relinquished
             and not bus.address_output_enable
             and not bus.control_output_enable
             and not bus.data_output_enable),
        ):
            coverage[key] += int(hit)
        state = post_state
        if advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, pmd_valid=False)
    phase = LogicalPhase.STATE_8
    emit(setup=(4, 0))

    for _ in range(clock_count):
        mode = state.interface.control.mode
        if mode is BusControlMode.IDLE:
            if br_n and phase is LogicalPhase.STATE_1 and rng.randrange(64) == 0:
                br_n = False
        elif mode is BusControlMode.REQUEST_DELAY:
            br_n = False
        elif mode is BusControlMode.GRANTED:
            if not br_n and phase is LogicalPhase.STATE_1 and rng.randrange(3) == 0:
                br_n = True
            elif not br_n:
                br_n = False
        else:
            br_n = True

        advance = rng.randrange(16) != 0
        type5 = None
        type13 = None
        setup = None
        ready = (
            phase is LogicalPhase.STATE_8
            and advance
            and mode is BusControlMode.IDLE
            and br_n
        )
        if ready:
            choice = rng.randrange(20)
            if state.core.instruction_valid and not state.core.pending:
                if choice < 3:
                    request = ProgramBusRequest.data_read(rng.randrange(1 << 14))
                    if choice & 1:
                        type5 = request
                    else:
                        type13 = request
            elif not state.core.instruction_valid and not state.core.pending:
                if choice < 5:
                    setup = (
                        state.core.architecture.pc.value,
                        _legal_opcode(rng),
                    )
                elif choice < 10:
                    request = (
                        ProgramBusRequest.data_write(
                            rng.randrange(1 << 14), rng.randrange(1 << 24)
                        )
                        if choice & 1
                        else ProgramBusRequest.data_read(rng.randrange(1 << 14))
                    )
                    if choice < 8:
                        type5 = request
                    else:
                        type13 = request

        pmd = rng.randrange(1 << 24)
        if (
            phase is LogicalPhase.STATE_7
            and advance
            and state.interface.owner_bus.bus.active
            and state.interface.owner_bus.owner is ProgramBusOwner.FETCH
        ):
            pmd = _legal_opcode(rng)
        emit(
            advance=advance,
            setup=setup,
            type5=type5,
            type13=type13,
            pmd=pmd,
            pmd_valid=rng.randrange(64) != 0,
        )

    br_n = False
    emit(reset=True, pmd_valid=False)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clocks", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x2100F3
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.clocks, args.seed)
    required = (
        "fetch_accept", "fetch_retry", "fetch_complete", "type5_accept",
        "type13_accept", "collision", "recognized", "grant", "resume",
        "masked",
        "type9_retire",
        "type15_retire", "type16_retire",
    )
    missing = [key for key in required if coverage[key] == 0]
    if missing:
        raise RuntimeError(f"missing coverage: {', '.join(missing)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    summary = " ".join(f"{key}={coverage[key]}" for key in required)
    print(
        f"PASS generated {len(lines)} linear/shared-PM/BR-BG clocks "
        f"seed={args.seed:#x} {summary}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
