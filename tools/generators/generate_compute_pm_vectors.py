#!/usr/bin/env python3
"""Generate deterministic original Type 5 state/cache-boundary vectors."""

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
    ComputePMState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_compute_pm_cycle,
    decode_compute_pm,
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


def _astat(state: ComputePMState) -> tuple[int, int]:
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
    write: bool = False,
    z: int = 0,
    amf: int = 0,
    yop: int = 0,
    xop: int = 0,
    dreg: int = 0,
    i_local: int = 0,
    m_local: int = 0,
) -> int:
    return (
        0x500000
        | (int(write) << 19)
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (dreg << 4)
        | (i_local << 2)
        | m_local
    )


def _random_legal_opcode(rng: random.Random) -> int:
    while True:
        opcode = _opcode(
            write=bool(rng.randrange(2)),
            z=rng.randrange(2),
            amf=rng.randrange(32),
            yop=rng.randrange(4),
            xop=rng.randrange(8),
            dreg=rng.randrange(16),
            i_local=rng.randrange(4),
            m_local=rng.randrange(4),
        )
        if decode_compute_pm(opcode) is not None:
            return opcode


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ComputePMState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        read_data: int = 0,
        read_valid: bool = True,
        complete: bool = True,
        next_address: int = 0,
        next_address_valid: bool = True,
        cache_valid: bool = True,
        force_fetch: bool = False,
        astat: ExactWord | None = None,
        mstat: ExactWord | None = None,
        dreg: DREGWrite | None = None,
        af: ExactWord | None = None,
        mf: ExactWord | None = None,
        dag_setup: DAGRegisterSetup | None = None,
        px: ExactWord | None = None,
        probe_dreg: int | None = None,
        probe_dag: int | None = None,
    ) -> None:
        nonlocal state
        if probe_dreg is None:
            probe_dreg = (opcode >> 4) & 0xF
        if probe_dag is None:
            probe_dag = rng.randrange(8)
        result = apply_compute_pm_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            pm_read_data=ExactWord(24, read_data) if read_valid else UNKNOWN,
            next_fetch_address=(
                ExactWord(14, next_address) if next_address_valid else UNKNOWN
            ),
            cache_next_instruction_valid=cache_valid,
            force_instruction_fetch=force_fetch,
            pm_cycle_complete=complete,
            setup_astat=astat,
            setup_mstat=mstat,
            setup_dreg=dreg,
            setup_af=af,
            setup_mf=mf,
            setup_dag=dag_setup,
            setup_px=px,
        )

        stimulus = 0
        for item, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (read_data, 24),
            (read_valid, 1),
            (complete, 1),
            (next_address, 14),
            (next_address_valid, 1),
            (cache_valid, 1),
            (force_fetch, 1),
            (astat is not None, 1),
            (astat.value if astat else 0, 8),
            (mstat is not None, 1),
            (mstat.value if mstat else 0, 4),
            (dreg is not None, 1),
            (int(dreg.address) if dreg else 0, 4),
            (dreg.data.value if dreg else 0, 16),
            (af is not None, 1),
            (af.value if af else 0, 16),
            (mf is not None, 1),
            (mf.value if mf else 0, 16),
            (dag_setup is not None, 1),
            (int(dag_setup.kind) if dag_setup else 0, 2),
            (dag_setup.address if dag_setup else 0, 3),
            (dag_setup.value if dag_setup else 0, 14),
            (px is not None, 1),
            (px.value if px else 0, 8),
            (probe_dreg, 4),
            (probe_dag, 3),
        ):
            stimulus = _append(stimulus, item, width)

        class_valid = (opcode & 0xF00000) == 0x500000
        class_write = (opcode >> 19) & 1 if class_valid else 0
        class_z = (opcode >> 18) & 1 if class_valid else 0
        class_amf = (opcode >> 13) & 0x1F if class_valid else 0
        class_yop = (opcode >> 11) & 3 if class_valid else 0
        class_xop = (opcode >> 8) & 7 if class_valid else 0
        class_dreg = (opcode >> 4) & 0xF if class_valid else 0
        class_i = 4 | ((opcode >> 2) & 3) if class_valid else 0
        class_m = 4 | (opcode & 3) if class_valid else 0
        compute_enable = class_valid and class_amf != 0
        is_mac = compute_enable and class_amf < 0x10
        action = decode_compute_pm(opcode)
        x_source = (
            0 if action is None or action.x_source is None
            else int(action.x_source)
        )
        y_source = (
            0 if action is None or action.y_source is None
            else int(action.y_source)
        )
        events = 0
        for item, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.unsupported_subencoding, 1),
            (result.unsupported_reason == "UNSUPPORTED_DESTINATION_COLLISION", 1),
            (compute_enable, 1),
            (is_mac, 1),
            (class_z, 1),
            (class_write, 1),
            (class_amf, 5),
            (class_yop, 2),
            (class_xop, 3),
            (x_source, 4),
            (y_source, 4),
            (class_dreg, 4),
            (class_i, 3),
            (class_m, 3),
            (result.boundary_valid, 1),
            (result.accepted, 1),
            (result.data_action_complete, 1),
            (result.instruction_complete, 1),
            (result.transaction_active, 1),
            (result.held_transaction, 1),
            (result.busy, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (result.cache_instruction_selected, 1),
            (result.recovery_required, 1),
            (result.recovery_fetch, 1),
            (result.event_boundary, 1),
            (result.pm_select, 1),
            (result.pm_data_access, 1),
            (result.pm_read, 1),
            (result.pm_write, 1),
            (result.pm_address_known, 1),
            (result.pm_address, 14),
            (result.pm_write_data_known, 1),
            (result.pm_write_data, 24),
            (result.fetched_instruction_known, 1),
            (result.fetched_instruction, 24),
            (result.dm_data_access, 1),
            (result.compute_result_known, 1),
            (result.dag_configuration_valid, 1),
            (result.i_write, 1),
            (result.i_write_known, 1),
            (result.dreg_write, 1),
            (result.dreg_write_known, 1),
            (result.px_write, 1),
            (result.px_write_known, 1),
            (result.alu_write, 1),
            (result.mac_write, 1),
            (result.alu_status_write, 1),
            (result.mac_status_write, 1),
            (
                result.alu_result
                if result.compute_result_known and not result.active_is_mac
                else 0,
                16,
            ),
            (
                result.mac_result
                if result.compute_result_known and result.active_is_mac
                else 0,
                40,
            ),
        ):
            events = _append(events, item, width)

        selected = (
            result.state.alternate
            if result.state.status.alternate_bank
            else result.state.primary
        )
        probe_known, probe_value = _exact(read_dreg(selected, DREG(probe_dreg)))
        i_value = result.state.dag.i[probe_dag]
        m_value = result.state.dag.m[probe_dag]
        l_value = result.state.dag.l[probe_dag]
        px_known, px_value = _exact(result.state.px)
        af_known, af_value = _exact(selected.af)
        mf_known, mf_value = _exact(selected.mf)
        mr_known, mr_value = _mr(selected)
        astat_mask, astat_value = _astat(result.state)
        post = 0
        for item, width in (
            (probe_known, 1),
            (probe_value, 16),
            (i_value is not None, 1),
            (0 if i_value is None else i_value, 14),
            (m_value is not None, 1),
            (0 if m_value is None else m_value, 14),
            (l_value is not None, 1),
            (0 if l_value is None else l_value, 14),
            (px_known, 1),
            (px_value, 8),
            (af_known, 1),
            (af_value, 16),
            (mf_known, 1),
            (mf_value, 16),
            (mr_known, 1),
            (mr_value, 40),
            (astat_mask, 8),
            (astat_value, 8),
            (result.state.status.mstat.value, 4),
            (result.state.status.alternate_bank, 1),
        ):
            post = _append(post, item, width)
        lines.append(f"{stimulus:044x} {events:047x} {post:042x}")
        state = result.state

    emit(reset=True)
    for bank in (0, 1):
        emit(mstat=ExactWord(4, bank))
        emit(astat=ExactWord(8, 0x5A ^ bank))
        for code in DREG:
            emit(
                dreg=DREGWrite(
                    code,
                    ExactWord(16, (bank << 15) | (int(code) * 0x421 + 3)),
                )
            )
        emit(af=ExactWord(16, 0xA100 + bank))
        emit(mf=ExactWord(16, 0xB100 + bank))
    for address in range(8):
        emit(
            dag_setup=DAGRegisterSetup(
                DAGRegisterKind.I,
                address,
                0x100 + address * 0x20,
            )
        )
        emit(dag_setup=DAGRegisterSetup(DAGRegisterKind.M, address, 1))
        emit(dag_setup=DAGRegisterSetup(DAGRegisterKind.L, address, 0))
    emit(px=ExactWord(8, 0xA5))

    emit(execute=True, opcode=0x526003, read_data=0xCAFE55)
    emit(
        execute=True,
        opcode=0x5A60AC,
        complete=False,
        next_address=0x222,
        cache_valid=False,
    )
    emit(complete=False, next_address=0x777)
    emit(complete=True, next_address=0x777)
    emit(read_data=0x123456)

    for _ in range(random_count):
        if state.recovery is not None:
            emit(
                execute=rng.randrange(15) == 0,
                opcode=_random_legal_opcode(rng),
                read_data=rng.randrange(1 << 24),
                read_valid=rng.randrange(12) != 0,
                complete=rng.randrange(4) != 0,
            )
            continue
        if state.pending is not None:
            emit(
                execute=rng.randrange(15) == 0,
                opcode=_random_legal_opcode(rng),
                read_data=rng.randrange(1 << 24),
                read_valid=rng.randrange(12) != 0,
                complete=rng.randrange(4) != 0,
                next_address=rng.randrange(1 << 14),
            )
            continue

        choice = rng.randrange(30)
        if choice < 17:
            emit(
                execute=True,
                opcode=_random_legal_opcode(rng),
                read_data=rng.randrange(1 << 24),
                read_valid=rng.randrange(12) != 0,
                complete=rng.randrange(5) != 0,
                next_address=rng.randrange(1 << 14),
                next_address_valid=rng.randrange(20) != 0,
                cache_valid=rng.randrange(5) != 0,
                force_fetch=rng.randrange(30) == 0,
            )
        elif choice == 17:
            emit(execute=True, opcode=rng.randrange(1 << 24))
        elif choice < 20:
            emit(astat=ExactWord(8, rng.randrange(256)))
        elif choice < 22:
            emit(mstat=ExactWord(4, rng.randrange(16)))
        elif choice < 25:
            emit(
                dreg=DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                )
            )
        elif choice == 25:
            emit(af=ExactWord(16, rng.randrange(1 << 16)))
        elif choice == 26:
            emit(mf=ExactWord(16, rng.randrange(1 << 16)))
        elif choice < 29:
            emit(
                dag_setup=DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8),
                    rng.randrange(1 << 14),
                )
            )
        else:
            emit(px=ExactWord(8, rng.randrange(256)))

    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210005)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 5 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
