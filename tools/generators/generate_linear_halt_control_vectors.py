#!/usr/bin/env python3
"""Generate deterministic linear-fetch plus HALT composition vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DREG,
    ExactWord,
    HaltControlMode,
    LinearHaltControlState,
    LogicalPhase,
    UNKNOWN,
    apply_linear_halt_control_cycle,
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


def _legal_opcode(rng: random.Random) -> int:
    choice = rng.randrange(10)
    if choice < 2:
        return 0
    if choice < 7:
        return _type6(rng.randrange(16), rng.randrange(1 << 16))
    if choice < 9:
        return _type7(rng.choice(LEGAL_TYPE7_CODES), rng.randrange(1 << 14))
    return 0x0C0000 | (rng.randrange(256) << 4)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return (True, value.value)
    return (False, 0)


def _probe(state: LinearHaltControlState, code: int) -> tuple[bool, int]:
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


def generate_lines(
    clock_count: int,
    seed: int,
) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = LinearHaltControlState.reset()
    phase = LogicalPhase.STATE_8
    halt_n = True
    dmack = True
    lines: list[str] = []
    coverage = {
        "recognized": 0,
        "stopped": 0,
        "resumed": 0,
        "dmack_blocked": 0,
        "held_clocks": 0,
    }

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
        result = apply_linear_halt_control_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            halt_n=halt_n,
            dmack=dmack,
            instruction_setup=setup_value,
            pmd_read_data=ExactWord(24, pmd) if pmd_valid else UNKNOWN,
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(phase), 3),
            (advance, 1),
            (halt_n, 1),
            (dmack, 1),
            (setup is not None, 1),
            (0 if setup is None else setup[0], 14),
            (0 if setup is None else setup[1], 24),
            (pmd, 24),
            (pmd_valid, 1),
            (probe, 6),
        ):
            stimulus = _append(stimulus, value, width)

        control = result.control
        coverage["recognized"] += int(control.halt_recognized)
        coverage["stopped"] += int(control.halt_stop_event)
        coverage["resumed"] += int(control.resume_event)
        coverage["dmack_blocked"] += int(control.release_blocked)
        coverage["held_clocks"] += int(control.phase_hold)
        control_pre = 0
        for value, width in (
            (int(state.control.mode), 2),
            (control.state_three_boundary, 1),
            (control.halt_recognized, 1),
            (control.halt_stop_event, 1),
            (control.resume_event, 1),
            (control.release_blocked, 1),
            (control.instruction_issue_inhibit, 1),
            (control.phase_hold, 1),
            (control.effective_phase_advance, 1),
            (control.halted, 1),
            (control.phase_conflict, 1),
        ):
            control_pre = _append(control_pre, value, width)

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
            (int(post_state.control.mode), 2),
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
            f"{stimulus:020x} {control_pre:03x} "
            f"{core_pre:026x} {post:030x}"
        )
        state = post_state
        if control.effective_phase_advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, pmd_valid=False)
    phase = LogicalPhase.STATE_8
    emit(setup=(4, 0))

    for _ in range(clock_count):
        mode = state.control.mode
        if mode is HaltControlMode.RUNNING:
            dmack = True
            if halt_n and state.core.pending and phase is LogicalPhase.STATE_1:
                if rng.randrange(8) == 0:
                    halt_n = False
        elif mode is HaltControlMode.STOP_PENDING:
            dmack = True
            if not halt_n and rng.randrange(3) == 0:
                halt_n = True
        else:
            if not halt_n and rng.randrange(5) == 0:
                halt_n = True
                dmack = rng.randrange(3) != 0
            elif halt_n and not dmack and rng.randrange(3) == 0:
                dmack = True

        advance = rng.randrange(16) != 0
        pmd = 0
        if (
            phase is LogicalPhase.STATE_7
            and advance
            and state.core.bus.active
        ):
            pmd = _legal_opcode(rng)
        emit(advance=advance, pmd=pmd)

    halt_n = False
    dmack = True
    emit(reset=True, pmd_valid=False)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clocks", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x2100A7,
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.clocks, args.seed)
    if min(coverage.values()) == 0:
        raise RuntimeError(f"insufficient HALT event coverage: {coverage}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} linear-HALT clocks "
        f"seed={args.seed:#x} "
        + " ".join(f"{name}={count}" for name, count in coverage.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
