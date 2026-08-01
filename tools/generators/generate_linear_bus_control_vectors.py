#!/usr/bin/env python3
"""Generate deterministic linear-fetch plus BR/BG composition vectors."""

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
    DREG,
    ExactWord,
    LinearBusControlState,
    LogicalPhase,
    UNKNOWN,
    apply_linear_bus_control_cycle,
    read_dreg,
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


def _type14(rng: random.Random) -> int:
    sf = rng.randrange(16)
    destinations = tuple(
        destination
        for destination in range(16)
        if not (
            (sf <= 0xB and destination in (0xE, 0xF))
            or (0xC <= sf <= 0xE and destination == 0x9)
        )
    )
    return (
        0x100000
        | (sf << 11)
        | (rng.choice(LEGAL_SHIFTER_XOPS) << 8)
        | (rng.choice(destinations) << 4)
        | rng.randrange(16)
    )


def _legal_opcode(rng: random.Random) -> int:
    choice = rng.randrange(18)
    if choice < 2:
        return 0
    if choice < 7:
        return _type6(rng.randrange(16), rng.randrange(1 << 16))
    if choice < 9:
        return _type7(rng.choice(LEGAL_TYPE7_CODES), rng.randrange(1 << 14))
    if choice < 11:
        return 0x0C0000 | (rng.randrange(256) << 4)
    if choice < 12:
        return _type9_nop(rng)
    if choice < 14:
        return _type15(rng)
    if choice < 16:
        return _type16(rng)
    return _type14(rng)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return (True, value.value)
    return (False, 0)


def _probe(state: LinearBusControlState, code: int) -> tuple[bool, int]:
    arch = state.core.architecture
    group = code >> 4
    index = code & 0xF
    if group == 0:
        bank = arch.alternate if arch.mstat.value & 1 else arch.primary
        return _exact(read_dreg(bank, DREG(index)))
    if group in (1, 2):
        address = ((group - 1) << 2) | (index & 3)
        if index < 4:
            return _exact(arch.dag.i[address])
        if index < 8:
            valid, value = _exact(arch.dag.m[address])
            if valid and value & 0x2000:
                value |= 0xC000
            return (valid, value)
        return _exact(arch.dag.l[address])
    if index == 0:
        return _exact(arch.astat)
    if index == 1:
        return (True, arch.mstat.value)
    if index == 2:
        return (True, arch.sstat.value)
    if index == 3:
        return (True, arch.imask.value)
    if index == 4:
        return _exact(arch.icntl)
    if index == 5:
        return _exact(arch.cntr)
    if index == 6:
        bank = arch.alternate if arch.mstat.value & 1 else arch.primary
        valid, value = _exact(bank.sb)
        if valid and value & 0x10:
            value |= 0xFFE0
        return (valid, value)
    return _exact(arch.px)


def generate_lines(clock_count: int, seed: int) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = LinearBusControlState.reset()
    phase = LogicalPhase.STATE_8
    br_n = True
    lines: list[str] = []
    coverage = {key: 0 for key in (
        "recognized", "grant_assert", "grant_release", "resume",
        "retire", "issue", "masked", "type9_retire",
        "type14_retire", "type15_retire", "type16_retire",
    )}

    def emit(
        *,
        reset: bool = False,
        advance: bool = True,
        setup: tuple[int, int] | None = None,
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
        result = apply_linear_bus_control_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            br_n=br_n,
            instruction_setup=setup_value,
            pmd_read_data=ExactWord(24, pmd) if pmd_valid else UNKNOWN,
        )
        coverage["type9_retire"] += int(
            result.core.retire_event
            and isinstance(state.core.instruction, ExactWord)
            and state.core.instruction.value & 0xF800F0 == 0x200000
        )
        coverage["type14_retire"] += int(
            result.core.retire_event
            and isinstance(state.core.instruction, ExactWord)
            and state.core.instruction.value & 0xFF0000 == 0x100000
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
        coverage["recognized"] += int(result.control.request_recognized)
        coverage["grant_assert"] += int(result.control.grant_assert_event)
        coverage["grant_release"] += int(
            result.control.grant_release_event
        )
        coverage["resume"] += int(result.control.resume_event)
        coverage["retire"] += int(result.core.retire_event)
        coverage["issue"] += int(result.core.instruction_issue)
        coverage["masked"] += int(
            result.native_bus_relinquished
            and not result.core.bus.address_output_enable
            and not result.core.bus.control_output_enable
            and not result.core.bus.data_output_enable
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(phase), 3),
            (advance, 1),
            (br_n, 1),
            (setup is not None, 1),
            (0 if setup is None else setup[0], 14),
            (0 if setup is None else setup[1], 24),
            (pmd, 24),
            (pmd_valid, 1),
            (probe, 6),
        ):
            stimulus = _append(stimulus, value, width)

        control = result.control
        bus_pre = 0
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
        ):
            bus_pre = _append(bus_pre, value, width)

        core = result.core
        bus = core.bus
        core_pre = 0
        for value, width in (
            (core.issue_boundary, 1),
            (core.instruction_setup_accepted, 1),
            (core.instruction_issue, 1),
            (core.retire_event, 1),
            (state.core.instruction_valid, 1),
            (state.core.pending, 1),
            (core.unsupported_instruction, 1),
            (core.reserved_subencoding, 1),
            (core.phase_conflict, 1),
            (core.integration_conflict, 1),
            (False, 1),
            (core.provisional_source_extension, 1),
            (state.core.architecture.pc.value, 14),
            (
                state.core.instruction.value
                if isinstance(state.core.instruction, ExactWord)
                else 0,
                24,
            ),
            (bus.request_accepted, 1),
            (bus.completion_event, 1),
            (bus.read_sample_event, 1),
            (state.core.bus.active, 1),
            (bus.address_output_enable, 1),
            (bus.control_output_enable, 1),
            (bus.data_output_enable, 1),
            (bus.address_known, 1),
            (bus.address if bus.address_known else 0, 14),
            (bus.pmda, 1),
            (bus.control_output_enable, 1),
            (bus.pms_n, 1),
            (bus.pmrd_n, 1),
            (bus.pmwr_n, 1),
            (bus.write_data_known, 1),
            (bus.write_data if bus.write_data_known else 0, 24),
        ):
            core_pre = _append(core_pre, value, width)

        post_state = result.state
        probe_valid, probe_value = _probe(post_state, probe)
        astat_valid, astat_value = _exact(post_state.core.architecture.astat)
        icntl_valid, icntl_value = _exact(post_state.core.architecture.icntl)
        cntr_valid, cntr_value = _exact(post_state.core.architecture.cntr)
        px_valid, px_value = _exact(post_state.core.architecture.px)
        post = 0
        for value, width in (
            (int(post_state.control.mode), 3),
            (post_state.core.instruction_valid, 1),
            (post_state.core.pending, 1),
            (post_state.core.architecture.pc.value, 14),
            (
                post_state.core.instruction.value
                if isinstance(post_state.core.instruction, ExactWord)
                else pmd,
                24,
            ),
            (probe_valid, 1),
            (probe_value, 16),
            (astat_valid, 1),
            (astat_value, 8),
            (post_state.core.architecture.mstat.value, 4),
            (icntl_valid, 1),
            (icntl_value, 5),
            (post_state.core.architecture.imask.value, 4),
            (cntr_valid, 1),
            (cntr_value, 14),
            (px_valid, 1),
            (px_value, 8),
            (post_state.core.architecture.sstat.value, 8),
            (bool(post_state.core.architecture.mstat.value & 1), 1),
            (len(post_state.core.architecture.count_stack), 3),
            (bool(post_state.core.architecture.sstat.value & 0x08), 1),
            (post_state.core.bus.active, 1),
        ):
            post = _append(post, value, width)
        lines.append(
            f"{stimulus:019x} {bus_pre:05x} "
            f"{core_pre:026x} {post:031x}"
        )
        state = post_state
        if advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, pmd_valid=False)
    phase = LogicalPhase.STATE_8
    emit(setup=(4, 0))

    for _ in range(clock_count):
        mode = state.control.mode
        if mode is BusControlMode.IDLE:
            if not br_n:
                br_n = False
            elif phase is LogicalPhase.STATE_1 and rng.randrange(64) == 0:
                br_n = False
        elif mode is BusControlMode.REQUEST_DELAY:
            br_n = False
        elif mode is BusControlMode.GRANTED:
            if br_n:
                br_n = True
            elif phase is LogicalPhase.STATE_1 and rng.randrange(3) == 0:
                br_n = True
            else:
                br_n = False
        else:
            br_n = True

        advance = rng.randrange(16) != 0
        pmd = 0
        pmd_valid = True
        if (
            phase is LogicalPhase.STATE_7
            and advance
            and state.core.bus.active
            and not result_native_relinquished(state, reset=False, br_n=br_n)
        ):
            pmd = _legal_opcode(rng)
        emit(advance=advance, pmd=pmd, pmd_valid=pmd_valid)

    br_n = False
    emit(reset=True, pmd_valid=False)
    return lines, coverage


def result_native_relinquished(
    state: LinearBusControlState,
    *,
    reset: bool,
    br_n: bool,
) -> bool:
    if reset:
        return not br_n
    return state.control.mode in (
        BusControlMode.GRANTED,
        BusControlMode.RELEASE_DELAY,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clocks", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x2100B7,
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.clocks, args.seed)
    if min(coverage.values()) == 0:
        raise RuntimeError(f"insufficient BR/BG coverage: {coverage}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} linear-BR/BG clocks "
        f"seed={args.seed:#x} "
        + " ".join(f"{name}={count}" for name, count in coverage.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
