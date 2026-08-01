#!/usr/bin/env python3
"""Generate deterministic Type 13/native-PM/HALT composition vectors."""

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
    HaltControlMode,
    LogicalPhase,
    ShifterPMHaltState,
    UNKNOWN,
    apply_shifter_pm_halt_cycle,
    read_dreg,
)
from tools.generators.generate_shifter_pm_vectors import (  # noqa: E402
    _random_legal_opcode,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _astat(state: ShifterPMHaltState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.native.core.core.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def generate_lines(
    random_count: int,
    seed: int,
) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = ShifterPMHaltState.reset()
    phase = LogicalPhase.STATE_8
    lines: list[str] = []
    coverage = {
        "pm_data_recognized": 0,
        "recovery_recognized": 0,
        "force_fetch_issued": 0,
        "late_hit_overridden": 0,
        "data_completed": 0,
        "stopped": 0,
        "resumed": 0,
        "dmack_blocked": 0,
        "held": 0,
    }

    def emit(
        *,
        reset: bool = False,
        phase_override: LogicalPhase | None = None,
        advance: bool = True,
        relinquished: bool = False,
        halt_n: bool = True,
        dmack: bool = True,
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
        result = apply_shifter_pm_halt_cycle(
            state,
            reset=reset,
            phase=use_phase,
            phase_advance=advance,
            halt_n=halt_n,
            dmack=dmack,
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
            (halt_n, 1),
            (dmack, 1),
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

        pre_cache = state.native.core.cache
        native = result.native
        core = native.core.core
        bus = native.bus
        events = 0
        for value, width in (
            (int(state.control.mode), 2),
            (result.control.halt_recognized, 1),
            (result.control.halt_stop_event, 1),
            (result.control.force_fetch_issue, 1),
            (result.control.resume_event, 1),
            (result.control.release_blocked, 1),
            (result.control.instruction_issue_inhibit, 1),
            (result.control.phase_hold, 1),
            (result.control.effective_phase_advance, 1),
            (result.control.halted, 1),
            (result.pm_data_cycle, 1),
            (result.late_force_request, 1),
            (result.execute_suppressed, 1),
            (result.owner_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (native.issue_boundary, 1),
            (core.accepted, 1),
            (core.data_action_complete, 1),
            (core.instruction_complete, 1),
            (core.pm_select, 1),
            (core.busy, 1),
            (core.cache_instruction_selected, 1),
            (core.recovery_fetch, 1),
            (native.core.next_instruction_known, 1),
            (native.core.next_instruction, 24),
            (native.core.instruction_from_cache, 1),
            (native.core.instruction_from_external, 1),
            (native.core.cache_fill, 1),
            (native.core.cache_fill_from_recovery, 1),
            (native.core.cache_fill_accepted, 1),
            (pre_cache.region_count != 0 and not reset, 1),
            (pre_cache.region_start, 14),
            (pre_cache.region_count if not reset else 0, 5),
            (bus.request_accepted, 1),
            (bus.completion_event, 1),
            (bus.read_sample_event, 1),
            (state.native.bus.active, 1),
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
            events = _append(events, value, width)

        core_state = result.state.native.core.core
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
        cache = result.state.native.core.cache
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

        coverage["pm_data_recognized"] += int(
            result.control.halt_recognized and result.pm_data_cycle
        )
        coverage["recovery_recognized"] += int(
            result.control.halt_recognized
            and not result.pm_data_cycle
            and core.recovery_fetch
        )
        coverage["force_fetch_issued"] += int(
            result.control.force_fetch_issue
        )
        coverage["late_hit_overridden"] += int(
            result.late_force_request
            and core.data_action_complete
            and not native.core.instruction_from_cache
        )
        coverage["data_completed"] += int(core.data_action_complete)
        coverage["stopped"] += int(result.control.halt_stop_event)
        coverage["resumed"] += int(result.control.resume_event)
        coverage["dmack_blocked"] += int(result.control.release_blocked)
        coverage["held"] += int(result.control.phase_hold)

        lines.append(f"{stimulus:048x} {events:032x} {post:040x}")
        state = result.state
        if phase_override is None and result.control.effective_phase_advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for bank_index in (0, 1):
        emit(
            phase_override=LogicalPhase.STATE_8,
            mstat=ExactWord(4, bank_index),
        )
        emit(
            phase_override=LogicalPhase.STATE_8,
            astat=ExactWord(8, 0x5A),
        )
        for code in DREG:
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(
                    code,
                    ExactWord(
                        16,
                        (bank_index << 15) | (int(code) * 0x421),
                    ),
                ),
            )
        emit(
            phase_override=LogicalPhase.STATE_8,
            sb=ExactWord(5, 0x0D),
        )
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
    emit(
        phase_override=LogicalPhase.STATE_8,
        px=ExactWord(8, 0xA5),
    )
    for offset in range(16):
        emit(
            phase_override=LogicalPhase.STATE_8,
            external_fill=True,
            external_address=0x200 + offset,
            external_instruction=0x800000 + offset,
        )

    # Directed cache-hit PM-data HALT: the hit must be replaced by a real fetch.
    phase = LogicalPhase.STATE_8
    emit(
        execute=True,
        opcode=0x118000,
        next_address=0x200,
    )
    while phase != LogicalPhase.STATE_3:
        emit()
    emit(halt_n=False)
    while phase != LogicalPhase.STATE_7:
        emit(halt_n=False)
    emit(halt_n=False, pmd=0x123456)
    emit(halt_n=False)
    while phase != LogicalPhase.STATE_7:
        emit(halt_n=False)
    emit(halt_n=False, pmd=0xABCDEF)
    emit(halt_n=True, dmack=False)
    emit(halt_n=True, dmack=True)

    # Directed miss followed by HALT during the already-required recovery.
    while phase != LogicalPhase.STATE_8:
        emit()
    emit(
        execute=True,
        opcode=0x110010,
        next_address=0x333,
        pmd=0xCAFE55,
    )
    while phase != LogicalPhase.STATE_7:
        emit(pmd=0xCAFE55)
    emit(pmd=0xCAFE55)
    emit()
    while phase != LogicalPhase.STATE_3:
        emit()
    emit(halt_n=False)
    while phase != LogicalPhase.STATE_7:
        emit(halt_n=False)
    emit(halt_n=False, pmd=0x654321)
    emit(halt_n=True, dmack=False)
    emit(halt_n=True, dmack=True)

    sequential_fill = 0x500
    for _ in range(random_count):
        reset = rng.randrange(8192) == 0
        advance = rng.randrange(12) != 0
        halt_n = True
        dmack = True
        controls: dict[str, object] = {}
        core_state = state.native.core.core
        held_core = (
            core_state.pending is not None
            or core_state.recovery is not None
        )

        if state.control.mode is HaltControlMode.HALTED:
            halt_n = rng.randrange(3) != 0
            dmack = rng.randrange(3) != 0
        elif state.control.mode is not HaltControlMode.RUNNING:
            halt_n = False
        else:
            if (
                phase is LogicalPhase.STATE_3
                and state.native.bus.active
                and rng.randrange(10) == 0
            ):
                halt_n = False
            if phase is LogicalPhase.STATE_8 and advance and not held_core:
                choice = rng.randrange(24)
                if choice < 15:
                    controls.update(
                        execute=True,
                        opcode=_random_legal_opcode(rng),
                        next_address=rng.randrange(1 << 14),
                        next_valid=rng.randrange(20) != 0,
                        force_fetch=rng.randrange(48) == 0,
                    )
                elif choice == 15:
                    controls["astat"] = ExactWord(8, rng.randrange(256))
                elif choice == 16:
                    controls["mstat"] = ExactWord(4, rng.randrange(16))
                elif choice < 19:
                    controls["dreg"] = DREGWrite(
                        DREG(rng.randrange(16)),
                        ExactWord(16, rng.randrange(1 << 16)),
                    )
                elif choice == 19:
                    controls["sb"] = ExactWord(5, rng.randrange(32))
                elif choice < 22:
                    controls["dag"] = DAGRegisterSetup(
                        DAGRegisterKind(rng.randrange(3)),
                        rng.randrange(8),
                        rng.randrange(1 << 14),
                    )
                elif choice == 22:
                    controls["px"] = ExactWord(8, rng.randrange(256))
                else:
                    address = sequential_fill & 0x3FFF
                    sequential_fill += 1
                    controls.update(
                        external_fill=True,
                        external_address=address,
                        external_instruction=rng.randrange(1 << 24),
                    )
            elif rng.randrange(1021) == 0:
                controls.update(
                    execute=True,
                    opcode=_random_legal_opcode(rng),
                )

        emit(
            reset=reset,
            advance=advance,
            halt_n=halt_n,
            dmack=dmack,
            pmd=rng.randrange(1 << 24),
            pmd_valid=rng.randrange(13) != 0,
            **controls,
        )

    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x2100D3,
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.random_count, args.seed)
    if min(coverage.values()) == 0:
        raise RuntimeError(f"insufficient Type 13/HALT coverage: {coverage}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} Type 13/native-PM/HALT clocks "
        f"seed={args.seed:#x} "
        + " ".join(f"{name}={count}" for name, count in coverage.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
