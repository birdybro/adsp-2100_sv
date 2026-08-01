#!/usr/bin/env python3
"""Generate deterministic Type 13 plus instruction-cache integration vectors."""

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
    ShifterPMCacheState,
    UNKNOWN,
    apply_shifter_pm_cache_cycle,
    read_dreg,
)
from tools.generators.generate_shifter_pm_vectors import (  # noqa: E402
    _opcode,
    _random_legal_opcode,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _astat(state: ShifterPMCacheState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.core.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ShifterPMCacheState.reset()
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
        force_fetch: bool = False,
        external_fill: bool = False,
        external_address: int = 0,
        external_address_valid: bool = True,
        external_instruction: int = 0,
        external_instruction_valid: bool = True,
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
        result = apply_shifter_pm_cache_cycle(
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
            force_instruction_fetch=force_fetch,
            external_fetch_fill=external_fill,
            external_fetch_address=(
                ExactWord(14, external_address)
                if external_address_valid else UNKNOWN
            ),
            external_fetch_instruction=(
                ExactWord(24, external_instruction)
                if external_instruction_valid else UNKNOWN
            ),
            setup_astat=astat,
            setup_mstat=mstat,
            setup_dreg=dreg,
            setup_sb=sb,
            setup_dag=dag_setup,
            setup_px=px,
        )
        core = result.core

        stimulus = 0
        for item, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (read_data, 24),
            (read_valid, 1),
            (next_address, 14),
            (next_address_valid, 1),
            (force_fetch, 1),
            (external_fill, 1),
            (external_address, 14),
            (external_address_valid, 1),
            (external_instruction, 24),
            (external_instruction_valid, 1),
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

        events = 0
        for item, width in (
            (core.class_valid, 1),
            (core.action_valid, 1),
            (core.unsupported_subencoding, 1),
            (core.boundary_valid, 1),
            (core.accepted, 1),
            (core.data_action_complete, 1),
            (core.instruction_complete, 1),
            (core.pm_select, 1),
            (core.busy, 1),
            (core.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (core.cache_instruction_selected, 1),
            (core.recovery_required, 1),
            (core.recovery_fetch, 1),
            (core.event_boundary, 1),
            (core.pm_select, 1),
            (core.pm_data_access, 1),
            (core.pm_read, 1),
            (core.pm_write, 1),
            (core.pm_address_known, 1),
            (core.pm_address, 14),
            (core.pm_write_data_known, 1),
            (core.pm_write_data, 24),
            (core.fetched_instruction_known, 1),
            (core.fetched_instruction, 24),
            (result.lookup_address_hit, 1),
            (result.lookup_instruction_known, 1),
            (result.lookup_instruction, 24),
            (result.cache_fill, 1),
            (result.cache_fill_from_recovery, 1),
            (result.external_fill_selected, 1),
            (result.cache_fill_accepted, 1),
            (result.cache_region_restarted, 1),
            (result.cache_oldest_replaced, 1),
            (result.external_fill_conflict, 1),
            (state.cache.region_count != 0 and not reset, 1),
            (state.cache.region_start, 14),
            (state.cache.region_count if not reset else 0, 5),
            (result.next_instruction_known, 1),
            (result.next_instruction, 24),
            (result.instruction_from_cache, 1),
            (result.instruction_from_external, 1),
        ):
            events = _append(events, item, width)

        selected = (
            result.state.core.alternate
            if result.state.core.status.alternate_bank
            else result.state.core.primary
        )
        probe_known, probe_value = _exact(
            read_dreg(selected, DREG(probe_dreg))
        )
        i_value = result.state.core.dag.i[probe_dag]
        m_value = result.state.core.dag.m[probe_dag]
        l_value = result.state.core.dag.l[probe_dag]
        px_known, px_value = _exact(result.state.core.px)
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
            (result.state.core.status.mstat.value, 4),
            (result.state.core.status.alternate_bank, 1),
            (result.state.cache.region_count != 0, 1),
            (result.state.cache.region_start, 14),
            (result.state.cache.region_count, 5),
        ):
            post = _append(post, item, width)
        lines.append(f"{stimulus:x} {events:x} {post:x}")
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
                DAGRegisterKind.I, address, 0x100 + address * 0x20
            )
        )
        emit(dag_setup=DAGRegisterSetup(DAGRegisterKind.M, address, 1))
        emit(dag_setup=DAGRegisterSetup(DAGRegisterKind.L, address, 0))
    emit(px=ExactWord(8, 0xA5))
    for offset in range(16):
        emit(
            external_fill=True,
            external_address=0x200 + offset,
            external_instruction=0x800000 + offset,
            next_address=0x200 + offset,
        )
    emit(
        execute=True,
        opcode=_opcode(0, 0, 0, write=False, i_local=0, m_local=0),
        read_data=0xCAFE55,
        next_address=0x208,
    )
    emit(
        execute=True,
        opcode=_opcode(0, 0, 14, write=True, i_local=3, m_local=2),
        next_address=0x333,
    )
    emit(read_data=0x123456)
    emit(
        execute=True,
        opcode=_opcode(0, 0, 0, write=True, i_local=1, m_local=1),
        next_address=0x333,
        force_fetch=True,
    )
    emit(read_data=0x654321)

    sequential_fill = 0x500
    for _ in range(random_count):
        if state.core.recovery is not None:
            if rng.randrange(16) == 0:
                emit(
                    read_data=rng.randrange(1 << 24),
                    external_fill=True,
                    external_address=rng.randrange(1 << 14),
                    external_instruction=rng.randrange(1 << 24),
                )
            else:
                emit(
                    read_data=rng.randrange(1 << 24),
                    read_valid=rng.randrange(10) != 0,
                )
            continue
        choice = rng.randrange(32)
        if choice < 14:
            emit(
                execute=True,
                opcode=_random_legal_opcode(rng),
                read_data=rng.randrange(1 << 24),
                read_valid=rng.randrange(10) != 0,
                next_address=rng.randrange(1 << 14),
                next_address_valid=rng.randrange(20) != 0,
                force_fetch=rng.randrange(32) == 0,
            )
        elif choice == 14:
            emit(execute=True, opcode=rng.randrange(1 << 24))
        elif choice == 15:
            emit(astat=ExactWord(8, rng.randrange(256)))
        elif choice == 16:
            emit(mstat=ExactWord(4, rng.randrange(16)))
        elif choice < 21:
            emit(
                dreg=DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                )
            )
        elif choice == 21:
            emit(sb=ExactWord(5, rng.randrange(32)))
        elif choice < 25:
            emit(
                dag_setup=DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8),
                    rng.randrange(1 << 14),
                )
            )
        elif choice == 25:
            emit(px=ExactWord(8, rng.randrange(256)))
        elif choice < 30:
            if rng.randrange(4) != 0:
                address = sequential_fill & 0x3FFF
                sequential_fill = (sequential_fill + 1) & 0x3FFF
            else:
                address = rng.randrange(1 << 14)
            emit(
                external_fill=True,
                external_address=address,
                external_address_valid=rng.randrange(20) != 0,
                external_instruction=rng.randrange(1 << 24),
                external_instruction_valid=rng.randrange(10) != 0,
                next_address=rng.randrange(1 << 14),
            )
        elif choice == 30:
            emit(
                execute=True,
                opcode=_random_legal_opcode(rng),
                external_fill=True,
                external_address=rng.randrange(1 << 14),
                external_instruction=rng.randrange(1 << 24),
            )
        else:
            emit(reset=True)
    while state.core.recovery is not None:
        emit(read_data=rng.randrange(1 << 24))
    emit(reset=True)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x21C013
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"PASS generated {len(lines)} Type 13/cache integration vectors "
        f"seed=0x{args.seed:x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
