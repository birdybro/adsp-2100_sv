#!/usr/bin/env python3
"""Generate deterministic ordinary-fetch/native-DM wait vectors."""

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
    ExactWord,
    LinearDMWaitControlState,
    LogicalPhase,
    UNKNOWN,
    apply_linear_dm_wait_control_cycle,
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


def _random_opcode(rng: random.Random) -> int:
    choice = rng.randrange(5)
    if choice == 0:
        return 0
    if choice == 1:
        return _type6(rng.randrange(16), rng.randrange(1 << 16))
    if choice == 2:
        return (
            0x0F0000
            | (rng.randrange(8) << 11)
            | (rng.choice(LEGAL_SHIFTER_XOPS) << 8)
            | rng.randrange(256)
        )
    if choice == 3:
        return (
            0x0E0000
            | (rng.randrange(16) << 11)
            | (rng.choice(LEGAL_SHIFTER_XOPS) << 8)
            | rng.randrange(16)
        )
    return 0


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return (True, value.value)
    return (False, 0)


def generate_lines(
    clock_count: int,
    seed: int,
) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = LinearDMWaitControlState.reset()
    phase = LogicalPhase.STATE_8
    lines: list[str] = []
    coverage = {
        "dm_companion_accept": 0,
        "wait_extension": 0,
        "interrupt_wait_sample": 0,
        "irq_pending_during_wait": 0,
        "irq_recognition_after_wait": 0,
        "aligned_completion": 0,
        "held_architectural_clock": 0,
        "dm_read": 0,
        "dm_write": 0,
    }

    def emit(
        *,
        reset: bool = False,
        advance: bool = True,
        irq_n: int = 0xF,
        setup: tuple[int, int] | None = None,
        dm_request: DataBusRequest | None = None,
        dm_ack: bool = True,
        dmd: int = 0,
        dmd_valid: bool = True,
        pmd: int = 0,
        pmd_valid: bool = True,
        probe: int = 0,
    ) -> None:
        nonlocal state, phase
        setup_value = (
            None
            if setup is None
            else (ExactWord(14, setup[0]), ExactWord(24, setup[1]))
        )
        result = apply_linear_dm_wait_control_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            irq_n=irq_n,
            instruction_setup=setup_value,
            dm_request=dm_request,
            dm_ack=dm_ack,
            dmd_read_data=(
                ExactWord(16, dmd) if dmd_valid else UNKNOWN
            ),
            pmd_read_data=(
                ExactWord(24, pmd) if pmd_valid else UNKNOWN
            ),
        )

        coverage["dm_companion_accept"] += int(
            result.dm_companion_accepted
        )
        coverage["wait_extension"] += int(
            result.dm_bus.wait_extension_event
        )
        coverage["interrupt_wait_sample"] += int(
            result.interrupt_wait_sample
        )
        coverage["irq_pending_during_wait"] += int(
            result.interrupt_wait_sample
            and result.state.core.interrupt.edge_pending != 0
        )
        coverage["irq_recognition_after_wait"] += int(
            result.core.interrupt_recognition_event
            and result.dm_bus.completion_event
        )
        coverage["aligned_completion"] += int(
            result.dm_bus.completion_event
            and result.core.bus.completion_event
            and result.core.retire_event
        )
        coverage["held_architectural_clock"] += int(
            advance and not result.architectural_phase_advance
        )
        coverage["dm_read"] += int(
            result.dm_companion_accepted
            and dm_request is not None
            and not dm_request.write
        )
        coverage["dm_write"] += int(
            result.dm_companion_accepted
            and dm_request is not None
            and dm_request.write
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(phase), 3),
            (advance, 1),
            (irq_n, 4),
            (setup is not None, 1),
            (0 if setup is None else setup[0], 14),
            (0 if setup is None else setup[1], 24),
            (dm_request is not None, 1),
            (
                0
                if dm_request is None
                or not isinstance(dm_request.address, ExactWord)
                else dm_request.address.value,
                14,
            ),
            (
                dm_request is not None
                and isinstance(dm_request.address, ExactWord),
                1,
            ),
            (False if dm_request is None else dm_request.write, 1),
            (
                0
                if dm_request is None
                or not isinstance(dm_request.write_data, ExactWord)
                else dm_request.write_data.value,
                16,
            ),
            (
                dm_request is not None
                and isinstance(dm_request.write_data, ExactWord),
                1,
            ),
            (dm_ack, 1),
            (dmd, 16),
            (dmd_valid, 1),
            (pmd, 24),
            (pmd_valid, 1),
            (probe, 6),
        ):
            stimulus = _append(stimulus, value, width)

        pm = result.core.bus
        dm = result.dm_bus
        expected_pre = 0
        for value, width in (
            (result.architectural_phase_advance, 1),
            (result.interrupt_wait_sample, 1),
            (result.dm_companion_accepted, 1),
            (result.phase_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (result.core.issue_boundary, 1),
            (result.core.instruction_setup_accepted, 1),
            (result.core.instruction_issue, 1),
            (result.core.retire_event, 1),
            (result.core.interrupt_recognition_event, 1),
            (result.core.interrupt_entry_event, 1),
            (result.core.interrupt_vector_issue_event, 1),
            (result.core.interrupt_vector_fetch_event, 1),
            (result.core.interrupt_level, 2),
            (result.core.interrupt_vector.value, 14),
            (state.core.interrupt.edge_pending, 4),
            (state.core.interrupt_vectoring, 1),
            (result.core.interrupt_configuration_invalid, 1),
            (result.core.interrupt_reset_baseline_provisional, 1),
            (state.core.instruction_valid, 1),
            (state.core.pending, 1),
            (result.core.phase_conflict, 1),
            (result.core.integration_conflict, 1),
            (result.core.internal_conflict, 1),
            (0 if reset else state.core.architecture.pc.value, 14),
            (
                state.core.instruction.value
                if isinstance(state.core.instruction, ExactWord)
                else 0,
                24,
            ),
            (pm.request_accepted, 1),
            (pm.completion_event, 1),
            (pm.read_sample_event, 1),
            (state.core.bus.active, 1),
            (pm.address_output_enable, 1),
            (pm.control_output_enable, 1),
            (pm.data_output_enable, 1),
            (pm.address_known, 1),
            (pm.address, 14),
            (pm.pmda, 1),
            (pm.control_output_enable, 1),
            (pm.pms_n, 1),
            (pm.pmrd_n, 1),
            (pm.pmwr_n, 1),
            (dm.request_accepted, 1),
            (dm.dmack_sample_event, 1),
            (dm.dmack_accepted, 1),
            (dm.wait_extension_event, 1),
            (dm.completion_event, 1),
            (dm.read_sample_event, 1),
            (state.dm_bus.active, 1),
            (dm.waiting, 1),
            (state.dm_bus.response_valid, 1),
            (state.dm_bus.response_write, 1),
            (isinstance(state.dm_bus.read_data, ExactWord), 1),
            (
                state.dm_bus.read_data.value
                if isinstance(state.dm_bus.read_data, ExactWord)
                else 0,
                16,
            ),
            (dm.address_output_enable, 1),
            (dm.control_output_enable, 1),
            (dm.data_output_enable, 1),
            (dm.address_known, 1),
            (dm.address, 14),
            (dm.dms_n, 1),
            (dm.dmrd_n, 1),
            (dm.dmwr_n, 1),
            (dm.write_data_known, 1),
            (dm.write_data, 16),
        ):
            expected_pre = _append(expected_pre, value, width)

        next_core = result.state.core
        next_dm = result.state.dm_bus
        _, icntl = _exact(next_core.architecture.icntl)
        next_instruction = (
            next_core.instruction.value
            if isinstance(next_core.instruction, ExactWord)
            else 0
        )
        expected_post = 0
        for value, width in (
            (next_core.instruction_valid, 1),
            (next_core.pending, 1),
            (next_core.architecture.pc.value, 14),
            (next_instruction, 24),
            (next_core.interrupt.edge_pending, 4),
            (next_core.interrupt_vectoring, 1),
            (next_core.interrupt_level or 0, 2),
            (next_core.bus.active, 1),
            (next_dm.active, 1),
            (
                next_dm.active
                and not next_dm.response_valid
                and next_dm.waiting,
                1,
            ),
            (next_dm.response_valid, 1),
            (next_dm.response_write, 1),
            (isinstance(next_dm.read_data, ExactWord), 1),
            (
                next_dm.read_data.value
                if isinstance(next_dm.read_data, ExactWord)
                else 0,
                16,
            ),
            (icntl, 5),
            (next_core.architecture.imask.value, 4),
            (next_core.architecture.sstat.value, 8),
        ):
            expected_post = _append(expected_post, value, width)

        lines.append(
            f"{stimulus:033x} {expected_pre:043x} "
            f"{expected_post:022x}"
        )
        state = result.state
        if advance:
            phase = LogicalPhase((int(phase) + 1) & 0x7)

    def advance_to(target: LogicalPhase) -> None:
        while phase is not target:
            emit()

    def retire_with(opcode: int) -> None:
        nonlocal phase
        if phase is not LogicalPhase.STATE_8:
            raise AssertionError("retirement helper requires state 8")
        emit()
        advance_to(LogicalPhase.STATE_7)
        emit(pmd=opcode)

    # Directed original-device IRQ/DMACK interaction. ICNTL and IMASK select
    # edge-sensitive IRQ2, then a paired NOP/DM read receives one full-cycle
    # wait. The edge occurs only at the first repeated physical state 7.
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)
    emit(setup=(0x0100, _type7(0x34, 0x04)))
    advance_to(LogicalPhase.STATE_8)
    retire_with(_type7(0x33, 0x04))
    retire_with(0)
    emit(dm_request=DataBusRequest.read(0x0555))
    advance_to(LogicalPhase.STATE_6)
    emit(dm_ack=False)
    emit(irq_n=0xB)
    advance_to(LogicalPhase.STATE_6)
    emit(dm_ack=True)
    emit(
        irq_n=0xF,
        dmd=0x1357,
        pmd=0,
    )
    emit()
    advance_to(LogicalPhase.STATE_7)
    emit(pmd=0)

    while len(lines) < clock_count:
        advance = rng.randrange(20) != 0
        setup = None
        dm_request = None
        if (
            phase is LogicalPhase.STATE_8
            and not state.core.instruction_valid
            and not state.core.pending
            and not state.core.interrupt_vectoring
        ):
            setup = (rng.randrange(1 << 14), _random_opcode(rng))
        elif (
            phase is LogicalPhase.STATE_8
            and state.core.instruction_valid
            and not state.core.pending
            and not state.core.interrupt_vectoring
            and rng.randrange(4) == 0
        ):
            if rng.randrange(2):
                dm_request = DataBusRequest.read(rng.randrange(1 << 14))
            else:
                dm_request = DataBusRequest.write_word(
                    rng.randrange(1 << 14),
                    rng.randrange(1 << 16),
                )
        dm_ack = True
        if (
            phase is LogicalPhase.STATE_6
            and state.dm_bus.active
            and not state.dm_bus.response_valid
        ):
            dm_ack = rng.randrange(4) != 0
        emit(
            advance=advance,
            setup=setup,
            dm_request=dm_request,
            dm_ack=dm_ack,
            dmd=rng.randrange(1 << 16),
            pmd=_random_opcode(rng),
            probe=rng.randrange(64),
        )

    required = (
        "dm_companion_accept",
        "wait_extension",
        "interrupt_wait_sample",
        "irq_pending_during_wait",
        "irq_recognition_after_wait",
        "aligned_completion",
        "held_architectural_clock",
        "dm_read",
        "dm_write",
    )
    missing = [name for name in required if coverage[name] == 0]
    if missing:
        raise RuntimeError(f"missing required coverage: {', '.join(missing)}")
    return (lines[:clock_count], coverage)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clocks", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=0x2100_D025)
    args = parser.parse_args()
    lines, coverage = generate_lines(args.clocks, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"generated {len(lines)} linear/native-DM clocks; "
        + ", ".join(f"{name}={count}" for name, count in coverage.items())
    )


if __name__ == "__main__":
    main()
