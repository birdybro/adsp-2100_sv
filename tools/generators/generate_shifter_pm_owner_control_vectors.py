#!/usr/bin/env python3
"""Generate Type 13/shared-PM/BR-BG differential vectors."""

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
    BusControlMode,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    LogicalPhase,
    ProgramBusRequest,
    ShifterPMOwnerControlState,
    UNKNOWN,
    apply_shifter_pm_owner_control_cycle,
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


def _astat(state: ShifterPMOwnerControlState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.core.core.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def generate_lines(
    random_count: int, seed: int
) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = ShifterPMOwnerControlState.reset()
    phase = LogicalPhase.STATE_8
    br_n = True
    lines: list[str] = []
    coverage = {name: 0 for name in (
        "type13_accept", "type13_retry", "data_complete", "recovery",
        "fetch_fill", "type5_complete", "collision", "recognized",
        "grant", "resume", "masked",
    )}

    def emit(
        *,
        reset: bool = False,
        phase_override: LogicalPhase | None = None,
        advance: bool = True,
        fetch: bool = False,
        fetch_address: int = 0,
        fetch_address_valid: bool = True,
        type5: bool = False,
        type5_address: int = 0,
        type5_address_valid: bool = True,
        type5_write: bool = False,
        type5_data: int = 0,
        type5_data_valid: bool = True,
        execute: bool = False,
        opcode: int = 0,
        pmd: int = 0,
        pmd_valid: bool = True,
        next_address: int = 0,
        next_valid: bool = True,
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
        fetch_request = (
            ProgramBusRequest(
                address=(ExactWord(14, fetch_address)
                         if fetch_address_valid else UNKNOWN)
            )
            if fetch else None
        )
        type5_request = (
            ProgramBusRequest(
                address=(ExactWord(14, type5_address)
                         if type5_address_valid else UNKNOWN),
                data_access=True,
                write=type5_write,
                write_data=(ExactWord(24, type5_data)
                            if type5_data_valid else UNKNOWN),
            )
            if type5 else None
        )
        result = apply_shifter_pm_owner_control_cycle(
            state,
            reset=reset,
            phase=use_phase,
            phase_advance=advance,
            br_n=br_n,
            fetch_request=fetch_request,
            type5_request=type5_request,
            execute=execute,
            opcode=opcode,
            pmd_read_data=ExactWord(24, pmd) if pmd_valid else UNKNOWN,
            next_fetch_address=(
                ExactWord(14, next_address) if next_valid else UNKNOWN
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
            (reset, 1), (int(use_phase), 3), (advance, 1), (br_n, 1),
            (fetch, 1), (fetch_address, 14), (fetch_address_valid, 1),
            (type5, 1), (type5_address, 14), (type5_address_valid, 1),
            (type5_write, 1), (type5_data, 24), (type5_data_valid, 1),
            (execute, 1), (opcode, 24), (pmd, 24), (pmd_valid, 1),
            (next_address, 14), (next_valid, 1),
            (astat is not None, 1), (astat.value if astat else 0, 8),
            (mstat is not None, 1), (mstat.value if mstat else 0, 4),
            (dreg is not None, 1), (int(dreg.address) if dreg else 0, 4),
            (dreg.data.value if dreg else 0, 16),
            (sb is not None, 1), (sb.value if sb else 0, 5),
            (dag is not None, 1), (int(dag.kind) if dag else 0, 2),
            (dag.address if dag else 0, 3), (dag.value if dag else 0, 14),
            (px is not None, 1), (px.value if px else 0, 8),
            (probe_dreg, 4), (probe_dag, 3),
        ):
            stimulus = _append(stimulus, value, width)

        interface = result.interface
        owner = interface.owner_bus
        bus = owner.bus
        events = 0
        for value, width in (
            (result.issue_boundary, 1), (result.phase_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (result.core.core.class_valid, 1),
            (result.core.core.action_valid, 1),
            (result.core.core.unsupported_subencoding, 1),
            (result.core.core.accepted, 1),
            (result.core.core.data_action_complete, 1),
            (result.core.core.instruction_complete, 1),
            (result.core.core.pm_select, 1), (result.core.core.busy, 1),
            (result.core.core.recovery_fetch, 1),
            (result.fetch_cache_fill, 1),
            (result.core.cache_fill_accepted, 1),
            (result.type13_request_presented, 1),
            (result.type13_request_accepted, 1),
            (result.type13_retry_pending, 1),
            (result.core.next_instruction_known, 1),
            (result.core.next_instruction, 24),
            (result.core.instruction_from_cache, 1),
            (result.core.instruction_from_external, 1),
            (int(state.interface.control.mode), 3),
            (interface.control.request_recognized, 1),
            (interface.control.grant_assert_event, 1),
            (interface.control.release_recognized, 1),
            (interface.control.grant_release_event, 1),
            (interface.control.resume_event, 1),
            (interface.control.instruction_issue_inhibit, 1),
            (interface.native_bg_n, 1),
            (interface.native_bus_relinquished, 1),
            (interface.request_blocked, 1),
            (owner.request_conflict, 1), (owner.request_out_of_phase, 1),
            (owner.fetch_accepted | (owner.type5_accepted << 1)
             | (owner.type13_accepted << 2), 3),
            (owner.fetch_completion | (owner.type5_completion << 1)
             | (owner.type13_completion << 2), 3),
            (int(state.interface.owner_bus.owner), 2),
            (state.interface.owner_bus.bus.active, 1),
            (bus.address_output_enable, 1),
            (bus.control_output_enable, 1),
            (bus.data_output_enable, 1),
            (bus.address_known, 1),
            (bus.address if bus.address_known else 0, 14),
            (bus.pmda, 1), (bus.control_output_enable, 1),
            (bus.pms_n, 1), (bus.pmrd_n, 1), (bus.pmwr_n, 1),
            (bus.write_data_known, 1),
            (bus.write_data if bus.write_data_known else 0, 24),
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
            (dreg_known, 1), (dreg_value, 16),
            (i_value is not None, 1), (0 if i_value is None else i_value, 14),
            (m_value is not None, 1), (0 if m_value is None else m_value, 14),
            (l_value is not None, 1), (0 if l_value is None else l_value, 14),
            (px_known, 1), (px_value, 8), (sr_known, 1), (sr_value, 32),
            (se_known, 1), (se_value, 8), (sb_known, 1), (sb_value, 5),
            (astat_mask, 8), (astat_value, 8),
            (core_state.status.mstat.value, 4),
            (core_state.status.alternate_bank, 1),
            (cache.region_count != 0, 1), (cache.region_start, 14),
            (cache.region_count, 5),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:052x} {events:029x} {post:040x}")

        for key, hit in (
            ("type13_accept", result.type13_request_accepted),
            ("type13_retry", result.type13_retry_pending),
            ("data_complete", result.core.core.data_action_complete),
            ("recovery", result.core.core.recovery_fetch),
            ("fetch_fill", result.fetch_cache_fill),
            ("type5_complete", owner.type5_completion),
            ("collision", owner.request_conflict),
            ("recognized", interface.control.request_recognized),
            ("grant", not interface.native_bg_n),
            ("resume", interface.control.resume_event),
            ("masked", interface.native_bus_relinquished
             and not bus.address_output_enable
             and not bus.control_output_enable
             and not bus.data_output_enable),
        ):
            coverage[key] += int(hit)
        state = result.state
        if phase_override is None and advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for bank in (0, 1):
        emit(phase_override=LogicalPhase.STATE_8, mstat=ExactWord(4, bank))
        for code in DREG:
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(code, ExactWord(16, int(code) * 0x421)),
            )
    for address in range(8):
        for kind, value in (
            (DAGRegisterKind.I, 0x100 + address * 0x20),
            (DAGRegisterKind.M, 1), (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag=DAGRegisterSetup(kind, address, value),
            )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0xA5))

    phase = LogicalPhase.STATE_8
    for _ in range(random_count):
        mode = state.interface.control.mode
        if mode is BusControlMode.IDLE:
            if phase is LogicalPhase.STATE_1 and rng.randrange(64) == 0:
                br_n = False
        elif mode is BusControlMode.REQUEST_DELAY:
            br_n = False
        elif mode is BusControlMode.GRANTED:
            if phase is LogicalPhase.STATE_1 and rng.randrange(3) == 0:
                br_n = True
        else:
            br_n = True

        advance = rng.randrange(11) != 0
        controls: dict[str, object] = {}
        core_held = (
            state.core.core.pending is not None
            or state.core.core.recovery is not None
        )
        enabled_eight = (
            phase is LogicalPhase.STATE_8
            and advance
            and mode in (BusControlMode.IDLE, BusControlMode.REACQUIRE)
        )
        if enabled_eight:
            choice = rng.randrange(32)
            if not core_held and choice < 14:
                controls.update(
                    execute=True,
                    opcode=_random_legal_opcode(rng),
                    next_address=rng.randrange(1 << 14),
                    next_valid=rng.randrange(20) != 0,
                )
            elif not core_held and choice == 14:
                controls.update(execute=True, opcode=rng.randrange(1 << 24))
            elif not core_held and choice == 15:
                controls["mstat"] = ExactWord(4, rng.randrange(16))
            elif not core_held and choice == 16:
                controls["dreg"] = DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                )
            if choice in (4, 17, 18, 19):
                controls.update(
                    fetch=True, fetch_address=rng.randrange(1 << 14),
                    fetch_address_valid=rng.randrange(17) != 0,
                )
            if choice in (7, 20, 21, 22):
                controls.update(
                    type5=True, type5_address=rng.randrange(1 << 14),
                    type5_address_valid=rng.randrange(17) != 0,
                    type5_write=bool(rng.randrange(2)),
                    type5_data=rng.randrange(1 << 24),
                    type5_data_valid=rng.randrange(17) != 0,
                )
        elif rng.randrange(601) == 0:
            controls.update(fetch=True, fetch_address=rng.randrange(1 << 14))
        emit(
            advance=advance,
            pmd=rng.randrange(1 << 24),
            pmd_valid=rng.randrange(13) != 0,
            **controls,
        )

    br_n = False
    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x21A13B
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} Type 13/shared-PM/BR-BG clocks "
        f"seed={args.seed:#x} "
        + " ".join(f"{key}={value}" for key, value in coverage.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
