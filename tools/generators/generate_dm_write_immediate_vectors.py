#!/usr/bin/env python3
"""Generate deterministic original Type 2 logical DM-write vectors."""

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
    DMWriteImmediateState,
    ExactWord,
    apply_dm_write_immediate_cycle,
    decode_dm_write_immediate,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(
    data: int,
    *,
    dag: int,
    i_local: int,
    m_local: int,
) -> int:
    return (
        0xA00000
        | (dag << 20)
        | (data << 4)
        | (i_local << 2)
        | m_local
    )


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DMWriteImmediateState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        ack: bool = False,
        mstat: ExactWord | None = None,
        dag_setup: DAGRegisterSetup | None = None,
        probe: int | None = None,
    ) -> None:
        nonlocal state
        if probe is None:
            probe = rng.randrange(8)
        result = apply_dm_write_immediate_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            dm_ack=ack,
            setup_mstat=mstat,
            setup_dag=dag_setup,
        )

        stimulus = 0
        for item, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (ack, 1),
            (mstat is not None, 1),
            (mstat.value if mstat is not None else 0, 4),
            (dag_setup is not None, 1),
            (int(dag_setup.kind) if dag_setup is not None else 0, 2),
            (dag_setup.address if dag_setup is not None else 0, 3),
            (dag_setup.value if dag_setup is not None else 0, 14),
            (probe, 3),
        ):
            stimulus = _append(stimulus, item, width)

        action = decode_dm_write_immediate(opcode)
        events = 0
        for item, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (action.immediate if action is not None else 0, 16),
            (action.dag if action is not None else 0, 1),
            (action.i_local if action is not None else 0, 2),
            (action.m_local if action is not None else 0, 2),
            (action.i_address if action is not None else 0, 3),
            (action.m_address if action is not None else 0, 3),
            (action.l_address if action is not None else 0, 3),
            (result.boundary_valid, 1),
            (result.accepted, 1),
            (result.instruction_complete, 1),
            (result.transaction_active, 1),
            (result.stalled, 1),
            (result.busy, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (result.dm_select, 1),
            (result.dm_read, 1),
            (result.dm_write, 1),
            (result.dm_address_known, 1),
            (result.dm_address, 14),
            (result.dm_write_data_known, 1),
            (result.dm_write_data, 16),
            (result.dag_configuration_valid, 1),
            (result.i_write, 1),
            (result.i_write_known, 1),
            (result.pm_data_access, 1),
            (result.dm_access, 1),
        ):
            events = _append(events, item, width)

        i_value = result.state.dag.i[probe]
        m_value = result.state.dag.m[probe]
        l_value = result.state.dag.l[probe]
        post = 0
        for item, width in (
            (i_value is not None, 1),
            (0 if i_value is None else i_value, 14),
            (m_value is not None, 1),
            (0 if m_value is None else m_value, 14),
            (l_value is not None, 1),
            (0 if l_value is None else l_value, 14),
            (result.state.mstat, 4),
        ):
            post = _append(post, item, width)
        lines.append(f"{stimulus:014x} {events:021x} {post:013x}")
        state = result.state

    emit(reset=True)
    for address in range(8):
        emit(
            dag_setup=DAGRegisterSetup(
                DAGRegisterKind.I, address, 0x100 + address * 0x20
            )
        )
        emit(
            dag_setup=DAGRegisterSetup(
                DAGRegisterKind.M, address, 1 if address != 7 else 0x3FFF
            )
        )
        emit(dag_setup=DAGRegisterSetup(DAGRegisterKind.L, address, 0))

    emit(
        execute=True,
        opcode=_opcode(0xCAFE, dag=0, i_local=0, m_local=0),
        ack=True,
        probe=0,
    )
    emit(mstat=ExactWord(4, 2))
    emit(
        execute=True,
        opcode=_opcode(0x8000, dag=0, i_local=1, m_local=2),
        ack=False,
        probe=1,
    )
    emit(ack=False, probe=1)
    emit(ack=False, probe=1)
    emit(ack=True, probe=1)
    emit(
        execute=True,
        opcode=_opcode(0xFFFF, dag=1, i_local=3, m_local=3),
        ack=False,
        probe=7,
    )
    emit(reset=True, ack=True, probe=7)

    for _ in range(random_count):
        if state.pending is not None:
            choice = rng.randrange(12)
            if choice == 0:
                emit(
                    execute=True,
                    opcode=_opcode(
                        rng.randrange(1 << 16),
                        dag=rng.randrange(2),
                        i_local=rng.randrange(4),
                        m_local=rng.randrange(4),
                    ),
                    ack=False,
                )
            elif choice == 1:
                emit(
                    ack=False,
                    dag_setup=DAGRegisterSetup(
                        DAGRegisterKind(rng.randrange(3)),
                        rng.randrange(8),
                        rng.randrange(1 << 14),
                    ),
                )
            elif choice == 2:
                emit(reset=True, ack=bool(rng.randrange(2)))
            else:
                emit(ack=rng.randrange(4) == 0)
            continue

        choice = rng.randrange(24)
        if choice < 12:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.randrange(1 << 16),
                    dag=rng.randrange(2),
                    i_local=rng.randrange(4),
                    m_local=rng.randrange(4),
                ),
                ack=rng.randrange(3) == 0,
            )
        elif choice == 12:
            emit(
                execute=True,
                opcode=rng.randrange(1 << 24),
                ack=bool(rng.randrange(2)),
            )
        elif choice < 16:
            emit(mstat=ExactWord(4, rng.randrange(16)))
        elif choice < 22:
            emit(
                dag_setup=DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8),
                    rng.randrange(1 << 14),
                )
            )
        elif choice == 22:
            emit(reset=True)
        else:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.randrange(1 << 16),
                    dag=rng.randrange(2),
                    i_local=rng.randrange(4),
                    m_local=rng.randrange(4),
                ),
                ack=True,
                mstat=ExactWord(4, rng.randrange(16)),
            )

    while state.pending is not None:
        emit(ack=True)
    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x210002
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS generated {len(lines)} Type 2 execution vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
