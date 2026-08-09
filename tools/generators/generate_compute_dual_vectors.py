#!/usr/bin/env python3
"""Generate deterministic bounded Type 1 model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ASTATBit,
    ComputeDualState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_compute_dual_cycle,
    read_dreg,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _mr(bank: object) -> tuple[bool, int]:
    mr0, mr1, mr2 = bank.mr
    if not all(isinstance(item, ExactWord) for item in (mr0, mr1, mr2)):
        return False, 0
    return True, (mr2.value << 32) | (mr1.value << 16) | mr0.value


def _astat(state: ComputeDualState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def _opcode(
    *,
    pd: int = 0,
    dd: int = 0,
    amf: int = 0,
    yop: int = 0,
    xop: int = 0,
    pm_i: int = 0,
    pm_m: int = 0,
    dm_i: int = 0,
    dm_m: int = 0,
) -> int:
    return (
        0xC00000
        | (pd << 20)
        | (dd << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (pm_i << 6)
        | (pm_m << 4)
        | (dm_i << 2)
        | dm_m
    )


def generate_lines(random_count: int, seed: int) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = ComputeDualState.reset()
    lines: list[str] = []
    counts = {
        "accepted": 0,
        "completed": 0,
        "stalled": 0,
        "alu": 0,
        "mac": 0,
        "dual_only": 0,
        "dm_unknown": 0,
        "pm_unknown": 0,
        "alternate": 0,
        "bit_reverse": 0,
        "conflict": 0,
        "reset": 0,
    }

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        complete: bool = False,
        dm_data: int = 0,
        dm_valid: bool = True,
        pm_data: int = 0,
        pm_valid: bool = True,
        astat: ExactWord | None = None,
        mstat: ExactWord | None = None,
        dreg: DREGWrite | None = None,
        af: ExactWord | None = None,
        mf: ExactWord | None = None,
        dag_setup: DAGRegisterSetup | None = None,
        px: ExactWord | None = None,
        inspect: bool = False,
        probe_dreg: int | None = None,
        probe_dag: int | None = None,
    ) -> None:
        nonlocal state
        if probe_dreg is None:
            probe_dreg = rng.randrange(16)
        if probe_dag is None:
            probe_dag = rng.randrange(8)
        result = apply_compute_dual_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            transaction_complete=complete,
            dm_read_data=ExactWord(16, dm_data) if dm_valid else UNKNOWN,
            pm_read_data=ExactWord(24, pm_data) if pm_valid else UNKNOWN,
            setup_astat=astat,
            setup_mstat=mstat,
            setup_dreg=dreg,
            setup_af=af,
            setup_mf=mf,
            setup_dag=dag_setup,
            setup_px=px,
            inspect_probe=inspect,
        )

        stimulus = 0
        for item, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (complete, 1),
            (dm_data, 16),
            (dm_valid, 1),
            (pm_data, 24),
            (pm_valid, 1),
            (astat is not None, 1),
            (astat.value if astat is not None else 0, 8),
            (mstat is not None, 1),
            (mstat.value if mstat is not None else 0, 4),
            (dreg is not None, 1),
            (int(dreg.address) if dreg is not None else 0, 4),
            (dreg.data.value if dreg is not None else 0, 16),
            (af is not None, 1),
            (af.value if af is not None else 0, 16),
            (mf is not None, 1),
            (mf.value if mf is not None else 0, 16),
            (dag_setup is not None, 1),
            (int(dag_setup.kind) if dag_setup is not None else 0, 2),
            (dag_setup.address if dag_setup is not None else 0, 3),
            (dag_setup.value if dag_setup is not None else 0, 14),
            (px is not None, 1),
            (px.value if px is not None else 0, 8),
            (inspect, 1),
            (probe_dreg, 4),
            (probe_dag, 3),
        ):
            stimulus = _append(stimulus, item, width)

        action = result.action
        x_source = (
            0 if action is None or action.x_source is None
            else int(action.x_source)
        )
        y_source = (
            0 if action is None or action.y_source is None
            else int(action.y_source)
        )
        compare_result = result.compute_result_known
        events = 0
        for item, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.unsupported_subencoding, 1),
            (action.computation_enabled if action is not None else False, 1),
            (action.is_mac if action is not None else False, 1),
            (action.amf if action is not None else 0, 5),
            (action.yop if action is not None else 0, 2),
            (action.xop if action is not None else 0, 3),
            (x_source, 4),
            (y_source, 4),
            (int(action.pm_destination) if action is not None else 0, 4),
            (int(action.dm_destination) if action is not None else 0, 4),
            (action.pm_i_address if action is not None else 0, 3),
            (action.pm_m_address if action is not None else 0, 3),
            (action.dm_i_address if action is not None else 0, 3),
            (action.dm_m_address if action is not None else 0, 3),
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
            (result.dm_address_known, 1),
            (result.dm_address, 14),
            (result.pm_select, 1),
            (result.pm_data_access, 1),
            (result.pm_read, 1),
            (result.pm_address_known, 1),
            (result.pm_address, 14),
            (result.compute_result_known, 1),
            (result.dm_dag_configuration_valid, 1),
            (result.pm_dag_configuration_valid, 1),
            (result.dm_i_write, 1),
            (result.dm_i_write_known, 1),
            (result.pm_i_write, 1),
            (result.pm_i_write_known, 1),
            (result.dm_dreg_write, 1),
            (result.dm_dreg_write_known, 1),
            (result.pm_dreg_write, 1),
            (result.pm_dreg_write_known, 1),
            (result.px_write, 1),
            (result.px_write_known, 1),
            (result.alu_write, 1),
            (result.mac_write, 1),
            (result.alu_status_write, 1),
            (result.mac_status_write, 1),
            (compare_result, 1),
            (
                result.alu_result
                if compare_result and not result.active_is_mac else 0,
                16,
            ),
            (
                result.mac_result
                if compare_result and result.active_is_mac else 0,
                40,
            ),
        ):
            events = _append(events, item, width)

        bank = (
            result.state.alternate
            if result.state.status.alternate_bank
            else result.state.primary
        )
        probe_dreg_known, probe_dreg_data = _exact(
            read_dreg(bank, DREG(probe_dreg))
        )
        probe_i = result.state.dag.i[probe_dag]
        probe_m = result.state.dag.m[probe_dag]
        probe_l = result.state.dag.l[probe_dag]
        px_known, px_data = _exact(result.state.px)
        af_known, af_data = _exact(bank.af)
        mf_known, mf_data = _exact(bank.mf)
        mr_known, mr_data = _mr(bank)
        astat_mask, astat_data = _astat(result.state)
        post = 0
        for item, width in (
            (probe_dreg_known, 1),
            (probe_dreg_data, 16),
            (probe_i is not None, 1),
            (probe_i if probe_i is not None else 0, 14),
            (probe_m is not None, 1),
            (probe_m if probe_m is not None else 0, 14),
            (probe_l is not None, 1),
            (probe_l if probe_l is not None else 0, 14),
            (px_known, 1),
            (px_data, 8),
            (af_known, 1),
            (af_data, 16),
            (mf_known, 1),
            (mf_data, 16),
            (mr_known, 1),
            (mr_data, 40),
            (astat_mask, 8),
            (astat_data, 8),
            (result.state.status.mstat.value, 4),
            (result.state.status.alternate_bank, 1),
        ):
            post = _append(post, item, width)

        lines.append(f"{stimulus:044x} {events:041x} {post:042x}")
        counts["accepted"] += int(result.accepted)
        counts["completed"] += int(result.instruction_complete)
        counts["stalled"] += int(result.stalled)
        counts["alu"] += int(result.alu_write)
        counts["mac"] += int(result.mac_write)
        counts["dual_only"] += int(
            result.instruction_complete
            and not result.alu_write and not result.mac_write
        )
        counts["dm_unknown"] += int(
            result.dm_dreg_write and not result.dm_dreg_write_known
        )
        counts["pm_unknown"] += int(
            result.pm_dreg_write and not result.pm_dreg_write_known
        )
        counts["alternate"] += int(
            result.instruction_complete and result.state.status.alternate_bank
        )
        counts["bit_reverse"] += int(
            result.transaction_active
            and bool(result.state.status.mstat.value & 0x2)
        )
        counts["conflict"] += int(result.integration_conflict)
        counts["reset"] += int(reset)
        state = result.state

    emit(reset=True, dm_valid=False, pm_valid=False)
    for address in range(8):
        for kind, value in (
            (DAGRegisterKind.I, 0x100 + 0x20 * address),
            (DAGRegisterKind.M, 1 + address),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                dag_setup=DAGRegisterSetup(kind, address, value),
                probe_dag=address,
            )
    emit(astat=ExactWord(8, 0))
    emit(af=ExactWord(16, 0x1111))
    emit(mf=ExactWord(16, 0x2222))
    emit(px=ExactWord(8, 0x33))
    for code in DREG:
        emit(dreg=DREGWrite(code, ExactWord(16, 0x1000 + int(code))))

    # Deterministically traverse every compute tuple and rotate every dual
    # destination/DAG selector before the randomized stateful tail.
    tuple_index = 0
    for amf in range(32):
        for yop in range(4):
            for xop in range(8):
                selector = tuple_index & 3
                emit(
                    execute=True,
                    opcode=_opcode(
                        pd=(tuple_index >> 2) & 3,
                        dd=(tuple_index >> 4) & 3,
                        amf=amf,
                        yop=yop,
                        xop=xop,
                        pm_i=selector,
                        pm_m=(selector + 1) & 3,
                        dm_i=(selector + 2) & 3,
                        dm_m=(selector + 3) & 3,
                    ),
                    complete=True,
                    dm_data=rng.randrange(1 << 16),
                    pm_data=rng.randrange(1 << 24),
                )
                tuple_index += 1

    for _ in range(random_count):
        if state.pending is not None:
            if rng.randrange(4) == 0:
                emit(
                    complete=True,
                    dm_data=rng.randrange(1 << 16),
                    dm_valid=rng.randrange(10) != 0,
                    pm_data=rng.randrange(1 << 24),
                    pm_valid=rng.randrange(10) != 0,
                )
            elif rng.randrange(8) == 0:
                emit(
                    execute=True,
                    opcode=rng.randrange(1 << 24),
                    dreg=DREGWrite(
                        DREG(rng.randrange(16)),
                        ExactWord(16, rng.randrange(1 << 16)),
                    ),
                )
            else:
                emit()
            continue

        choice = rng.randrange(100)
        if choice < 2:
            emit(reset=True, dm_valid=False, pm_valid=False)
        elif choice < 12:
            emit(
                dag_setup=DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8),
                    rng.randrange(1 << 14),
                )
            )
        elif choice < 22:
            emit(
                dreg=DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                )
            )
        elif choice < 25:
            emit(astat=ExactWord(8, rng.randrange(1 << 8)))
        elif choice < 28:
            emit(mstat=ExactWord(4, rng.randrange(1 << 4)))
        elif choice < 30:
            emit(af=ExactWord(16, rng.randrange(1 << 16)))
        elif choice < 32:
            emit(mf=ExactWord(16, rng.randrange(1 << 16)))
        elif choice < 34:
            emit(px=ExactWord(8, rng.randrange(1 << 8)))
        elif choice < 94:
            emit(
                execute=True,
                opcode=_opcode(
                    pd=rng.randrange(4),
                    dd=rng.randrange(4),
                    amf=rng.randrange(32),
                    yop=rng.randrange(4),
                    xop=rng.randrange(8),
                    pm_i=rng.randrange(4),
                    pm_m=rng.randrange(4),
                    dm_i=rng.randrange(4),
                    dm_m=rng.randrange(4),
                ),
                complete=bool(rng.randrange(2)),
                dm_data=rng.randrange(1 << 16),
                dm_valid=rng.randrange(12) != 0,
                pm_data=rng.randrange(1 << 24),
                pm_valid=rng.randrange(12) != 0,
            )
        elif choice < 97:
            emit(execute=True, opcode=rng.randrange(0xC00000))
        else:
            emit(inspect=True)

    while state.pending is not None:
        emit(
            complete=True,
            dm_data=rng.randrange(1 << 16),
            pm_data=rng.randrange(1 << 24),
        )

    required = (
        "accepted",
        "completed",
        "stalled",
        "alu",
        "mac",
        "dual_only",
        "dm_unknown",
        "pm_unknown",
        "alternate",
        "bit_reverse",
        "conflict",
        "reset",
    )
    missing = [name for name in required if counts[name] == 0]
    if missing:
        raise RuntimeError(f"missing Type 1 coverage: {', '.join(missing)}")
    return lines, counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210001)
    args = parser.parse_args()
    lines, counts = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    summary = " ".join(f"{name}={value}" for name, value in counts.items())
    print(f"generated {len(lines)} Type 1 vectors seed={args.seed:#x} {summary}")


if __name__ == "__main__":
    main()
