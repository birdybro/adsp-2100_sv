#!/usr/bin/env python3
"""Generate deterministic original Type 13 model-versus-RTL vectors."""

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
    ShifterPMState,
    UNKNOWN,
    apply_shifter_pm_cycle,
    decode_shifter_pm,
    read_dreg,
    shifter_pm_unsupported_reason,
)


X_DREG_CODES = (8, 0, 10, 11, 12, 13, 14, 15)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _astat(state: ShifterPMState) -> tuple[int, int]:
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
    i_local: int,
    m_local: int,
) -> int:
    return (
        0x110000
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
            i_local=rng.randrange(4),
            m_local=rng.randrange(4),
        )
        if decode_shifter_pm(opcode) is not None:
            return opcode


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ShifterPMState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        read_data: int = 0,
        read_valid: bool = True,
        next_address: int = 0,
        next_address_valid: bool = True,
        cache_valid: bool = True,
        force_fetch: bool = False,
        astat: ExactWord | None = None,
        mstat: ExactWord | None = None,
        dreg: DREGWrite | None = None,
        sb: ExactWord | None = None,
        dag_setup: DAGRegisterSetup | None = None,
        px: ExactWord | None = None,
        probe_dreg: int | None = None,
        probe_dag: int | None = None,
    ) -> None:
        nonlocal state
        if probe_dreg is None:
            probe_dreg = rng.randrange(16)
        if probe_dag is None:
            probe_dag = rng.randrange(8)
        result = apply_shifter_pm_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            pm_read_data=(
                ExactWord(24, read_data) if read_valid else UNKNOWN
            ),
            next_fetch_address=(
                ExactWord(14, next_address)
                if next_address_valid else UNKNOWN
            ),
            cache_next_instruction_valid=cache_valid,
            force_instruction_fetch=force_fetch,
            setup_astat=astat,
            setup_mstat=mstat,
            setup_dreg=dreg,
            setup_sb=sb,
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
            (sb is not None, 1),
            (sb.value if sb else 0, 5),
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

        live_action = decode_shifter_pm(opcode)
        live_class = (opcode & 0xFF0000) == 0x110000
        reason = shifter_pm_unsupported_reason(opcode)
        if not live_class:
            write = sf = xop = memory_dreg = 0
            i_address = m_address = shifter_source = 0
        else:
            write = bool((opcode >> 15) & 1)
            sf = (opcode >> 11) & 0xF
            xop = (opcode >> 8) & 7
            memory_dreg = (opcode >> 4) & 0xF
            i_address = 4 | ((opcode >> 2) & 3)
            m_address = 4 | (opcode & 3)
            shifter_source = 0 if live_action is None else X_DREG_CODES[xop]
        compare_result = (
            result.shifter_result_known
            and (result.sr_write or result.se_write or result.sb_write)
        )
        events = 0
        for item, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.unsupported_subencoding, 1),
            (reason == "UNAVAILABLE_SHIFTER_XOP", 1),
            (reason == "UNSUPPORTED_DESTINATION_COLLISION", 1),
            (write, 1),
            (sf, 4),
            (xop, 3),
            (shifter_source, 4),
            (memory_dreg, 4),
            (i_address, 3),
            (m_address, 3),
            (result.boundary_valid, 1),
            (result.accepted, 1),
            (result.data_action_complete, 1),
            (result.instruction_complete, 1),
            (result.pm_select, 1),
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
            (result.shifter_result_known, 1),
            (result.dag_configuration_valid, 1),
            (result.i_write, 1),
            (result.i_write_known, 1),
            (result.dreg_write, 1),
            (result.dreg_write_known, 1),
            (result.px_write, 1),
            (result.px_write_known, 1),
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
        px_known, px_value = _exact(result.state.px)
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
            (px_known, 1),
            (px_value, 8),
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
        lines.append(f"{stimulus:037x} {events:043x} {post:035x}")
        state = result.state

    emit(reset=True)
    for bank in (0, 1):
        emit(mstat=ExactWord(4, bank))
        emit(astat=ExactWord(8, 0x5A))
        for code in DREG:
            emit(
                dreg=DREGWrite(
                    code,
                    ExactWord(16, (bank << 15) | (int(code) * 0x421)),
                )
            )
        emit(sb=ExactWord(5, 0x0D + bank))
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

    emit(
        execute=True,
        opcode=_opcode(0, 0, 0, write=False, i_local=0, m_local=0),
        read_data=0xCAFE55,
        next_address=0x123,
    )
    emit(
        execute=True,
        opcode=_opcode(0, 0, 14, write=True, i_local=3, m_local=2),
        next_address=0x222,
        cache_valid=False,
    )
    emit(read_data=0x123456)
    emit(
        execute=True,
        opcode=_opcode(0, 0, 0, write=True, i_local=1, m_local=1),
        next_address=0x333,
        force_fetch=True,
    )
    emit(read_data=0x654321)

    for _ in range(random_count):
        if state.recovery is not None:
            if rng.randrange(12) == 0:
                emit(
                    execute=True,
                    opcode=_random_legal_opcode(rng),
                    read_data=rng.randrange(1 << 24),
                    read_valid=rng.randrange(10) != 0,
                )
            else:
                emit(
                    read_data=rng.randrange(1 << 24),
                    read_valid=rng.randrange(10) != 0,
                )
            continue
        choice = rng.randrange(25)
        if choice < 13:
            emit(
                execute=True,
                opcode=_random_legal_opcode(rng),
                read_data=rng.randrange(1 << 24),
                read_valid=rng.randrange(10) != 0,
                next_address=rng.randrange(1 << 14),
                next_address_valid=rng.randrange(20) != 0,
                cache_valid=rng.randrange(4) != 0,
                force_fetch=rng.randrange(32) == 0,
            )
        elif choice == 13:
            emit(execute=True, opcode=rng.randrange(1 << 24))
        elif choice == 14:
            emit(astat=ExactWord(8, rng.randrange(256)))
        elif choice == 15:
            emit(mstat=ExactWord(4, rng.randrange(16)))
        elif choice < 20:
            emit(
                dreg=DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                )
            )
        elif choice == 20:
            emit(sb=ExactWord(5, rng.randrange(32)))
        elif choice < 24:
            emit(
                dag_setup=DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8),
                    rng.randrange(1 << 14),
                )
            )
        else:
            emit(px=ExactWord(8, rng.randrange(256)))
    while state.recovery is not None:
        emit(read_data=rng.randrange(1 << 24))
    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x210013,
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS generated {len(lines)} Type 13 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
