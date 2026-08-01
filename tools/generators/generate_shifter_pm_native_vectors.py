#!/usr/bin/env python3
"""Generate deterministic Type 13/cache/native-PM integration vectors."""

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
    LogicalPhase,
    ShifterPMNativeState,
    UNKNOWN,
    apply_shifter_pm_native_cycle,
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


def _astat(state: ShifterPMNativeState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.core.core.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ShifterPMNativeState.reset()
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
        pmd: int = 0,
        pmd_valid: bool = True,
        next_address: int = 0,
        next_valid: bool = True,
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
        dag: DAGRegisterSetup | None = None,
        px: ExactWord | None = None,
        probe_dreg: int | None = None,
        probe_dag: int | None = None,
    ) -> None:
        nonlocal state, phase
        use_phase = phase if phase_override is None else phase_override
        if probe_dreg is None:
            probe_dreg = rng.randrange(16)
        if probe_dag is None:
            probe_dag = rng.randrange(8)
        result = apply_shifter_pm_native_cycle(
            state,
            reset=reset,
            phase=use_phase,
            phase_advance=advance,
            bus_relinquished=relinquished,
            execute=execute,
            opcode=opcode,
            pmd_read_data=ExactWord(24, pmd) if pmd_valid else UNKNOWN,
            next_fetch_address=(
                ExactWord(14, next_address) if next_valid else UNKNOWN
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
            setup_dag=dag,
            setup_px=px,
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(use_phase), 3),
            (advance, 1),
            (relinquished, 1),
            (execute, 1),
            (opcode, 24),
            (pmd, 24),
            (pmd_valid, 1),
            (next_address, 14),
            (next_valid, 1),
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
            (dag is not None, 1),
            (int(dag.kind) if dag else 0, 2),
            (dag.address if dag else 0, 3),
            (dag.value if dag else 0, 14),
            (px is not None, 1),
            (px.value if px else 0, 8),
            (probe_dreg, 4),
            (probe_dag, 3),
        ):
            stimulus = _append(stimulus, value, width)

        pre_cache = state.core.cache
        events = 0
        for value, width in (
            (result.issue_boundary, 1),
            (result.phase_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (result.core.core.class_valid, 1),
            (result.core.core.action_valid, 1),
            (result.core.core.unsupported_subencoding, 1),
            (result.core.core.accepted, 1),
            (result.core.core.data_action_complete, 1),
            (result.core.core.instruction_complete, 1),
            (result.core.core.pm_select, 1),
            (result.core.core.busy, 1),
            (result.core.core.cache_instruction_selected, 1),
            (result.core.core.recovery_required, 1),
            (result.core.core.recovery_fetch, 1),
            (result.core.core.event_boundary, 1),
            (result.core.next_instruction_known, 1),
            (result.core.next_instruction, 24),
            (result.core.instruction_from_cache, 1),
            (result.core.instruction_from_external, 1),
            (result.core.cache_fill, 1),
            (result.core.cache_fill_from_recovery, 1),
            (result.core.cache_fill_accepted, 1),
            (pre_cache.region_count != 0 and not reset, 1),
            (pre_cache.region_start, 14),
            (pre_cache.region_count if not reset else 0, 5),
            (result.bus.request_accepted, 1),
            (result.bus.completion_event, 1),
            (result.bus.read_sample_event, 1),
            (state.bus.active, 1),
            (result.bus.address_output_enable, 1),
            (result.bus.control_output_enable, 1),
            (result.bus.data_output_enable, 1),
            (result.bus.address_known, 1),
            (result.bus.address if result.bus.address_known else 0, 14),
            (result.bus.pmda, 1),
            (result.bus.control_output_enable, 1),
            (result.bus.pms_n, 1),
            (result.bus.pmrd_n, 1),
            (result.bus.pmwr_n, 1),
            (result.bus.write_data_known, 1),
            (
                result.bus.write_data
                if result.bus.write_data_known else 0,
                24,
            ),
        ):
            events = _append(events, value, width)

        core_state = result.state.core.core
        bank = (
            core_state.alternate
            if core_state.status.alternate_bank else core_state.primary
        )
        dreg_known, dreg_value = _exact(read_dreg(bank, DREG(probe_dreg)))
        i_value = core_state.dag.i[probe_dag]
        m_value = core_state.dag.m[probe_dag]
        l_value = core_state.dag.l[probe_dag]
        px_known, px_value = _exact(core_state.px)
        sr0_known, sr0_value = _exact(bank.sr[0])
        sr1_known, sr1_value = _exact(bank.sr[1])
        sr_known = sr0_known and sr1_known
        sr_value = ((sr1_value << 16) | sr0_value) if sr_known else 0
        se_known, se_value = _exact(bank.se)
        sb_known, sb_value = _exact(bank.sb)
        astat_mask, astat_value = _astat(result.state)
        cache = result.state.core.cache
        post = 0
        for value, width in (
            (dreg_known, 1),
            (dreg_value, 16),
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
            (core_state.status.mstat.value, 4),
            (core_state.status.alternate_bank, 1),
            (cache.region_count != 0, 1),
            (cache.region_start, 14),
            (cache.region_count, 5),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:048x} {events:030x} {post:040x}")
        state = result.state
        if phase_override is None and advance and not relinquished:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for bank in (0, 1):
        emit(phase_override=LogicalPhase.STATE_8, mstat=ExactWord(4, bank))
        emit(phase_override=LogicalPhase.STATE_8, astat=ExactWord(8, 0x5A))
        for code in DREG:
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(
                    code,
                    ExactWord(16, (bank << 15) | (int(code) * 0x421)),
                ),
            )
        emit(phase_override=LogicalPhase.STATE_8, sb=ExactWord(5, 0x0D))
    for address in range(8):
        for kind, value in (
            (DAGRegisterKind.I, 0x100 + address * 0x20),
            (DAGRegisterKind.M, 1),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag=DAGRegisterSetup(kind, address, value),
            )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0xA5))
    for offset in range(16):
        emit(
            phase_override=LogicalPhase.STATE_8,
            external_fill=True,
            external_address=0x200 + offset,
            external_instruction=0x800000 + offset,
        )

    phase = LogicalPhase.STATE_8
    sequential_fill = 0x500
    for _ in range(random_count):
        advance = rng.randrange(10) != 0
        relinquished = rng.randrange(101) == 0
        controls: dict[str, object] = {}
        held_core = (
            state.core.core.pending is not None
            or state.core.core.recovery is not None
        )
        if phase == LogicalPhase.STATE_8 and advance and not relinquished:
            if not held_core:
                choice = rng.randrange(32)
                if choice < 15:
                    controls.update(
                        execute=True,
                        opcode=_random_legal_opcode(rng),
                        next_address=rng.randrange(1 << 14),
                        next_valid=rng.randrange(20) != 0,
                        force_fetch=rng.randrange(32) == 0,
                    )
                elif choice == 15:
                    controls.update(execute=True, opcode=rng.randrange(1 << 24))
                elif choice == 16:
                    controls["astat"] = ExactWord(8, rng.randrange(256))
                elif choice == 17:
                    controls["mstat"] = ExactWord(4, rng.randrange(16))
                elif choice < 21:
                    controls["dreg"] = DREGWrite(
                        DREG(rng.randrange(16)),
                        ExactWord(16, rng.randrange(1 << 16)),
                    )
                elif choice == 21:
                    controls["sb"] = ExactWord(5, rng.randrange(32))
                elif choice < 25:
                    controls["dag"] = DAGRegisterSetup(
                        DAGRegisterKind(rng.randrange(3)),
                        rng.randrange(8),
                        rng.randrange(1 << 14),
                    )
                elif choice == 25:
                    controls["px"] = ExactWord(8, rng.randrange(256))
                elif choice < 30:
                    address = sequential_fill & 0x3FFF
                    sequential_fill += 1
                    controls.update(
                        external_fill=True,
                        external_address=address,
                        external_instruction=rng.randrange(1 << 24),
                        external_instruction_valid=rng.randrange(12) != 0,
                    )
        elif rng.randrange(503) == 0:
            controls.update(execute=True, opcode=_random_legal_opcode(rng))
        emit(
            advance=advance,
            relinquished=relinquished,
            pmd=rng.randrange(1 << 24),
            pmd_valid=rng.randrange(11) != 0,
            **controls,
        )

    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x21C0B5
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} Type 13/native-PM clocks "
        f"seed=0x{args.seed:x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
