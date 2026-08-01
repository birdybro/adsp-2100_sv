#!/usr/bin/env python3
"""Generate deterministic Type 2/native-DM model/RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DAGRegisterKind,
    DAGRegisterSetup,
    DMWriteImmediateNativeState,
    ExactWord,
    LogicalPhase,
    apply_dm_write_immediate_native_cycle,
)


def _append(word: int, value: int | bool, width: int) -> int:
    return (word << width) | (int(value) & ((1 << width) - 1))


def _opcode(
    data: int, dag: int = 0, i_local: int = 0, m_local: int = 0
) -> int:
    return (
        0xA00000
        | ((dag & 1) << 20)
        | ((data & 0xFFFF) << 4)
        | ((i_local & 3) << 2)
        | (m_local & 3)
    )


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DMWriteImmediateNativeState.reset()
    phase = LogicalPhase.STATE_8
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        phase_override: LogicalPhase | None = None,
        advance: bool = True,
        relinquished: bool = False,
        execute: bool = False,
        opcode: int = 0,
        dm_ack: bool = True,
        mstat: ExactWord | None = None,
        dag: DAGRegisterSetup | None = None,
        probe: int = 0,
    ) -> None:
        nonlocal state, phase
        selected_phase = phase if phase_override is None else phase_override
        result = apply_dm_write_immediate_native_cycle(
            state,
            reset=reset,
            phase=selected_phase,
            phase_advance=advance,
            bus_relinquished=relinquished,
            execute=execute,
            opcode=opcode,
            dm_ack=dm_ack,
            setup_mstat=mstat,
            setup_dag=dag,
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(selected_phase), 3),
            (advance, 1),
            (relinquished, 1),
            (execute, 1),
            (opcode, 24),
            (dm_ack, 1),
            (mstat is not None, 1),
            (0 if mstat is None else mstat.value, 4),
            (dag is not None, 1),
            (0 if dag is None else int(dag.kind), 2),
            (0 if dag is None else dag.address, 3),
            (0 if dag is None else dag.value, 14),
            (probe, 3),
        ):
            stimulus = _append(stimulus, value, width)

        pre = 0
        for value, width in (
            (result.issue_boundary, 1),
            (result.phase_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (result.core.class_valid, 1),
            (result.core.action_valid, 1),
            (result.core.boundary_valid, 1),
            (result.core.accepted, 1),
            (result.core.instruction_complete, 1),
            (result.core.transaction_active, 1),
            (result.core.stalled, 1),
            (result.core.busy, 1),
            (result.core.invalid_opcode, 1),
            (result.core.dag_configuration_valid, 1),
            (result.core.i_write, 1),
            (result.core.i_write_known, 1),
            (result.core.dm_select, 1),
            (result.core.dm_write, 1),
            (result.core.dm_address_known, 1),
            (result.core.dm_address, 14),
            (result.core.dm_write_data_known, 1),
            (result.core.dm_write_data, 16),
            (result.bus.request_accepted, 1),
            (result.bus.dmack_sample_event, 1),
            (result.bus.dmack_accepted, 1),
            (result.bus.wait_extension_event, 1),
            (result.bus.completion_event, 1),
            (result.bus.transaction_active, 1),
            (result.bus.waiting, 1),
            (result.bus.address_output_enable, 1),
            (result.bus.control_output_enable, 1),
            (result.bus.data_output_enable, 1),
            (result.bus.address_known, 1),
            (result.bus.address, 14),
            (result.bus.dms_n, 1),
            (result.bus.dmrd_n, 1),
            (result.bus.dmwr_n, 1),
            (result.bus.write_data_known, 1),
            (result.bus.write_data, 16),
        ):
            pre = _append(pre, value, width)

        next_core = result.state.core
        next_bus = result.state.bus
        i_value = next_core.dag.i[probe]
        m_value = next_core.dag.m[probe]
        l_value = next_core.dag.l[probe]
        bus_address_known = isinstance(next_bus.address, ExactWord)
        bus_data_known = isinstance(next_bus.write_data, ExactWord)
        post = 0
        for value, width in (
            (i_value is not None, 1),
            (0 if i_value is None else i_value, 14),
            (m_value is not None, 1),
            (0 if m_value is None else m_value, 14),
            (l_value is not None, 1),
            (0 if l_value is None else l_value, 14),
            (next_core.mstat, 4),
            (next_core.pending is not None, 1),
            (next_bus.active, 1),
            (next_bus.waiting, 1),
            (next_bus.acknowledged, 1),
            (next_bus.response_valid, 1),
            (bus_address_known, 1),
            (next_bus.address.value if bus_address_known else 0, 14),
            (bus_data_known, 1),
            (next_bus.write_data.value if bus_data_known else 0, 16),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:015x} {pre:024x} {post:022x}")
        state = result.state
        if phase_override is None and advance and not relinquished:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for address in range(8):
        for kind, value in (
            (DAGRegisterKind.I, 0x100 + address * 0x20),
            (DAGRegisterKind.M, 1 if address & 1 == 0 else 0x3FFF),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag=DAGRegisterSetup(kind, address, value),
                probe=address,
            )
    emit(
        phase_override=LogicalPhase.STATE_8,
        mstat=ExactWord(4, 2),
    )

    phase = LogicalPhase.STATE_8
    for _ in range(random_count):
        advance = rng.randrange(10) != 0
        relinquished = rng.randrange(131) == 0
        controls: dict[str, object] = {}
        idle = state.core.pending is None
        boundary = (
            phase == LogicalPhase.STATE_8 and advance and not relinquished
        )
        if boundary and idle:
            choice = rng.randrange(30)
            if choice < 20:
                controls.update(
                    execute=True,
                    opcode=_opcode(
                        rng.randrange(1 << 16),
                        rng.randrange(2),
                        rng.randrange(4),
                        rng.randrange(4),
                    ),
                )
            elif choice == 20:
                controls.update(execute=True, opcode=rng.randrange(1 << 21))
            elif choice < 24:
                controls["mstat"] = ExactWord(4, rng.randrange(16))
            elif choice < 29:
                controls["dag"] = DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8),
                    rng.randrange(1 << 14),
                )
        elif rng.randrange(499) == 0:
            controls.update(
                execute=True,
                opcode=_opcode(rng.randrange(1 << 16)),
            )
        dm_ack = not (
            phase == LogicalPhase.STATE_6 and rng.randrange(5) == 0
        )
        emit(
            advance=advance,
            relinquished=relinquished,
            dm_ack=dm_ack,
            probe=rng.randrange(8),
            **controls,
        )

    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x2102DA
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} Type 2/native-DM clocks "
        f"seed=0x{args.seed:x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
