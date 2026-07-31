#!/usr/bin/env python3
"""Generate deterministic original Type 12 model-versus-RTL vectors."""

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
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    ShifterDMState,
    UNKNOWN,
    apply_shifter_dm_cycle,
    decode_shifter_dm,
    read_dreg,
    shifter_dm_unsupported_reason,
)


X_DREG_CODES = (8, 0, 10, 11, 12, 13, 14, 15)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _astat(state: ShifterDMState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def _opcode(
    sf: int,
    xop: int,
    dreg: int,
    *,
    write: bool,
    dag: int,
    i_local: int,
    m_local: int,
) -> int:
    return (
        0x120000
        | (dag << 16)
        | (int(write) << 15)
        | (sf << 11)
        | (xop << 8)
        | (dreg << 4)
        | (i_local << 2)
        | m_local
    )


def _random_legal_opcode(rng: random.Random) -> int:
    while True:
        opcode = _opcode(
            rng.randrange(16),
            rng.choice((0, 2, 3, 4, 5, 6, 7)),
            rng.randrange(16),
            write=bool(rng.randrange(2)),
            dag=rng.randrange(2),
            i_local=rng.randrange(4),
            m_local=rng.randrange(4),
        )
        if decode_shifter_dm(opcode) is not None:
            return opcode


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ShifterDMState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        ack: bool = False,
        read_data: int = 0,
        read_valid: bool = True,
        astat: ExactWord | None = None,
        mstat: ExactWord | None = None,
        dreg: DREGWrite | None = None,
        sb: ExactWord | None = None,
        dag_setup: DAGRegisterSetup | None = None,
        probe_dreg: int | None = None,
        probe_dag: int | None = None,
    ) -> None:
        nonlocal state
        if probe_dreg is None:
            probe_dreg = rng.randrange(16)
        if probe_dag is None:
            probe_dag = rng.randrange(8)
        result = apply_shifter_dm_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            dm_ack=ack,
            dm_read_data=ExactWord(16, read_data) if read_valid else UNKNOWN,
            setup_astat=astat,
            setup_mstat=mstat,
            setup_dreg=dreg,
            setup_sb=sb,
            setup_dag=dag_setup,
        )

        stimulus = 0
        for item, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (ack, 1),
            (read_data, 16),
            (read_valid, 1),
            (astat is not None, 1),
            (astat.value if astat else 0, 8),
            (mstat is not None, 1),
            (mstat.value if mstat else 0, 4),
            (dreg is not None, 1),
            (int(dreg.address) if dreg else 0, 4),
            (dreg.data.value if dreg else 0, 16),
            (sb is not None, 1),
            (sb.value if sb else 0, 5),
            (dag_setup is not None, 1),
            (int(dag_setup.kind) if dag_setup else 0, 2),
            (dag_setup.address if dag_setup else 0, 3),
            (dag_setup.value if dag_setup else 0, 14),
            (probe_dreg, 4),
            (probe_dag, 3),
        ):
            stimulus = _append(stimulus, item, width)

        live_action = decode_shifter_dm(opcode)
        live_class = (opcode & 0xFE0000) == 0x120000
        reason = shifter_dm_unsupported_reason(opcode)
        if not live_class:
            dag_select = write = sf = xop = memory_dreg = 0
            i_address = m_address = shifter_source = 0
        else:
            dag_select = (opcode >> 16) & 1
            write = bool((opcode >> 15) & 1)
            sf = (opcode >> 11) & 0xF
            xop = (opcode >> 8) & 7
            memory_dreg = (opcode >> 4) & 0xF
            i_address = (dag_select << 2) | ((opcode >> 2) & 3)
            m_address = (dag_select << 2) | (opcode & 3)
            shifter_source = 0 if live_action is None else X_DREG_CODES[xop]
        compare_result = (
            result.shifter_result_known
            and result.instruction_complete
            and (result.sr_write or result.se_write or result.sb_write)
        )
        events = 0
        for item, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.unsupported_subencoding, 1),
            (reason == "UNAVAILABLE_SHIFTER_XOP", 1),
            (reason == "UNSUPPORTED_DESTINATION_COLLISION", 1),
            (dag_select, 1),
            (write, 1),
            (sf, 4),
            (xop, 3),
            (shifter_source, 4),
            (memory_dreg, 4),
            (i_address, 3),
            (m_address, 3),
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
            (result.pm_data_access, 1),
            (result.dm_access, 1),
            (result.shifter_result_known, 1),
            (result.dag_configuration_valid, 1),
            (result.i_write, 1),
            (result.i_write_known, 1),
            (result.dreg_write, 1),
            (result.dreg_write_known, 1),
            (result.sr_write, 1),
            (result.se_write, 1),
            (result.sb_write, 1),
            (result.ss_write, 1),
            (compare_result, 1),
            (result.sr_result if result.sr_write else 0, 32),
            (result.se_result if result.se_write else 0, 8),
            (result.sb_result if result.sb_write else 0, 5),
            (result.ss_result if result.ss_write else False, 1),
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
        sr0_known, sr0_value = _exact(selected.sr[0])
        sr1_known, sr1_value = _exact(selected.sr[1])
        sr_known = sr0_known and sr1_known
        sr_value = (sr1_value << 16) | sr0_value
        se_known, se_value = _exact(selected.se)
        sb_known, sb_value = _exact(selected.sb)
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
            (sr_known, 1),
            (sr_value, 32),
            (se_known, 1),
            (se_value, 8),
            (sb_known, 1),
            (sb_value, 5),
            (astat_mask, 8),
            (astat_value, 8),
            (result.state.status.mstat.value, 4),
            (result.state.status.alternate_bank, 1),
        ):
            post = _append(post, item, width)
        lines.append(f"{stimulus:028x} {events:033x} {post:033x}")
        state = result.state

    emit(reset=True)
    for bank in (0, 1):
        emit(mstat=ExactWord(4, bank))
        emit(astat=ExactWord(8, 0x5A))
        for code in DREG:
            emit(dreg=DREGWrite(code, ExactWord(16, (bank << 15) | (int(code) * 0x421))))
        emit(sb=ExactWord(5, 0x0D + bank))
    for address in range(8):
        emit(dag_setup=DAGRegisterSetup(DAGRegisterKind.I, address, 0x100 + address * 0x20))
        emit(dag_setup=DAGRegisterSetup(DAGRegisterKind.M, address, 1))
        emit(dag_setup=DAGRegisterSetup(DAGRegisterKind.L, address, 0))

    # Directed same-cycle and multiply-extended reads/writes precede random work.
    emit(execute=True, opcode=_opcode(0, 0, 0, write=False, dag=0, i_local=0, m_local=0), ack=True, read_data=0xCAFE)
    emit(execute=True, opcode=_opcode(0, 0, 14, write=True, dag=1, i_local=3, m_local=2), ack=False)
    emit(ack=False, read_data=0x1111)
    emit(ack=False, read_data=0x2222)
    emit(ack=True, read_data=0x3333)

    for _ in range(random_count):
        if state.pending is not None:
            emit(
                ack=rng.randrange(4) == 0,
                read_data=rng.randrange(1 << 16),
                read_valid=rng.randrange(10) != 0,
            )
            continue
        choice = rng.randrange(24)
        if choice < 12:
            emit(
                execute=True,
                opcode=_random_legal_opcode(rng),
                ack=rng.randrange(3) == 0,
                read_data=rng.randrange(1 << 16),
                read_valid=rng.randrange(10) != 0,
            )
        elif choice == 12:
            emit(execute=True, opcode=rng.randrange(1 << 24), ack=bool(rng.randrange(2)))
        elif choice == 13:
            emit(astat=ExactWord(8, rng.randrange(256)))
        elif choice == 14:
            emit(mstat=ExactWord(4, rng.randrange(16)))
        elif choice < 19:
            emit(dreg=DREGWrite(DREG(rng.randrange(16)), ExactWord(16, rng.randrange(1 << 16))))
        elif choice == 19:
            emit(sb=ExactWord(5, rng.randrange(32)))
        elif choice < 23:
            emit(
                dag_setup=DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8),
                    rng.randrange(1 << 14),
                )
            )
        else:
            emit(reset=True)
    while state.pending is not None:
        emit(ack=True, read_data=rng.randrange(1 << 16))
    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210012)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS generated {len(lines)} Type 12 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
