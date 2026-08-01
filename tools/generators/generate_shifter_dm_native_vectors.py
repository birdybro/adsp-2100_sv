#!/usr/bin/env python3
"""Generate deterministic Type 12/native-DM model/RTL vectors."""

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
    ShifterDMNativeState,
    UNKNOWN,
    apply_shifter_dm_native_cycle,
    decode_shifter_dm,
    read_dreg,
)


def _append(word: int, value: int | bool, width: int) -> int:
    return (word << width) | (int(value) & ((1 << width) - 1))


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _astat(state: ShifterDMNativeState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.core.status.astat.bit(bit)
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
    state = ShifterDMNativeState.reset()
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
        ack: bool = True,
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
        nonlocal state, phase
        selected_phase = phase if phase_override is None else phase_override
        if probe_dreg is None:
            probe_dreg = rng.randrange(16)
        if probe_dag is None:
            probe_dag = rng.randrange(8)
        read_word = ExactWord(16, read_data) if read_valid else UNKNOWN
        result = apply_shifter_dm_native_cycle(
            state,
            reset=reset,
            phase=selected_phase,
            phase_advance=advance,
            bus_relinquished=relinquished,
            execute=execute,
            opcode=opcode,
            dm_ack=ack,
            dmd_read_data=read_word,
            setup_astat=astat,
            setup_mstat=mstat,
            setup_dreg=dreg,
            setup_sb=sb,
            setup_dag=dag_setup,
        )

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(selected_phase), 3),
            (advance, 1),
            (relinquished, 1),
            (execute, 1),
            (opcode, 24),
            (ack, 1),
            (read_data, 16),
            (read_valid, 1),
            (astat is not None, 1),
            (0 if astat is None else astat.value, 8),
            (mstat is not None, 1),
            (0 if mstat is None else mstat.value, 4),
            (dreg is not None, 1),
            (0 if dreg is None else int(dreg.address), 4),
            (0 if dreg is None else dreg.data.value, 16),
            (sb is not None, 1),
            (0 if sb is None else sb.value, 5),
            (dag_setup is not None, 1),
            (0 if dag_setup is None else int(dag_setup.kind), 2),
            (0 if dag_setup is None else dag_setup.address, 3),
            (0 if dag_setup is None else dag_setup.value, 14),
            (probe_dreg, 4),
            (probe_dag, 3),
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
            (result.core.unsupported_subencoding, 1),
            (result.core.accepted, 1),
            (result.core.instruction_complete, 1),
            (result.core.transaction_active, 1),
            (result.core.stalled, 1),
            (result.core.busy, 1),
            (result.core.invalid_opcode, 1),
            (result.core.dm_select, 1),
            (result.core.dm_read, 1),
            (result.core.dm_write, 1),
            (result.core.dm_address_known, 1),
            (result.core.dm_address, 14),
            (result.core.dm_write_data_known, 1),
            (result.core.dm_write_data, 16),
            (result.core.shifter_result_known, 1),
            (result.core.dag_configuration_valid, 1),
            (result.core.i_write, 1),
            (result.core.i_write_known, 1),
            (result.core.dreg_write, 1),
            (result.core.dreg_write_known, 1),
            (result.core.sr_write, 1),
            (result.core.se_write, 1),
            (result.core.sb_write, 1),
            (result.core.ss_write, 1),
            (result.bus.request_accepted, 1),
            (result.bus.dmack_sample_event, 1),
            (result.bus.dmack_accepted, 1),
            (result.bus.wait_extension_event, 1),
            (result.bus.completion_event, 1),
            (result.bus.read_sample_event, 1),
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

        core = result.state.core
        selected = (
            core.alternate if core.status.alternate_bank else core.primary
        )
        dreg_known, dreg_value = _exact(
            read_dreg(selected, DREG(probe_dreg))
        )
        i_value = core.dag.i[probe_dag]
        m_value = core.dag.m[probe_dag]
        l_value = core.dag.l[probe_dag]
        sr0_known, sr0_value = _exact(selected.sr[0])
        sr1_known, sr1_value = _exact(selected.sr[1])
        sr_known = sr0_known and sr1_known
        se_known, se_value = _exact(selected.se)
        sb_known, sb_value = _exact(selected.sb)
        astat_mask, astat_value = _astat(result.state)
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
            (sr_known, 1),
            ((sr1_value << 16) | sr0_value, 32),
            (se_known, 1),
            (se_value, 8),
            (sb_known, 1),
            (sb_value, 5),
            (astat_mask, 8),
            (astat_value, 8),
            (core.status.mstat.value, 4),
            (core.status.alternate_bank, 1),
            (core.pending is not None, 1),
            (result.state.bus.active, 1),
            (result.state.bus.waiting, 1),
            (result.state.bus.acknowledged, 1),
            (result.state.bus.response_valid, 1),
        ):
            post = _append(post, value, width)
        lines.append(f"{stimulus:030x} {pre:026x} {post:034x}")
        state = result.state
        if phase_override is None and advance and not relinquished:
            phase = LogicalPhase((int(phase) + 1) & 7)

    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for bank in (0, 1):
        emit(
            phase_override=LogicalPhase.STATE_8,
            mstat=ExactWord(4, bank),
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
                    ExactWord(16, (bank << 15) | (int(code) * 0x421)),
                ),
            )
        emit(
            phase_override=LogicalPhase.STATE_8,
            sb=ExactWord(5, 0x0D + bank),
        )
    for address in range(8):
        for kind, value in (
            (DAGRegisterKind.I, 0x100 + address * 0x20),
            (DAGRegisterKind.M, 1),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag_setup=DAGRegisterSetup(kind, address, value),
            )

    phase = LogicalPhase.STATE_8
    for _ in range(random_count):
        advance = rng.randrange(10) != 0
        relinquished = rng.randrange(149) == 0
        controls: dict[str, object] = {}
        idle = state.core.pending is None
        boundary = (
            phase == LogicalPhase.STATE_8 and advance and not relinquished
        )
        if boundary and idle:
            choice = rng.randrange(36)
            if choice < 23:
                controls.update(execute=True, opcode=_random_legal_opcode(rng))
            elif choice == 23:
                controls.update(execute=True, opcode=rng.randrange(1 << 24))
            elif choice == 24:
                controls["astat"] = ExactWord(8, rng.randrange(256))
            elif choice == 25:
                controls["mstat"] = ExactWord(4, rng.randrange(16))
            elif choice < 31:
                controls["dreg"] = DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                )
            elif choice == 31:
                controls["sb"] = ExactWord(5, rng.randrange(32))
            elif choice < 35:
                controls["dag_setup"] = DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8),
                    rng.randrange(1 << 14),
                )
        elif rng.randrange(557) == 0:
            controls.update(execute=True, opcode=_random_legal_opcode(rng))
        ack = not (
            phase == LogicalPhase.STATE_6 and rng.randrange(5) == 0
        )
        emit(
            advance=advance,
            relinquished=relinquished,
            ack=ack,
            read_data=rng.randrange(1 << 16),
            read_valid=rng.randrange(11) != 0,
            **controls,
        )

    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x2112DA
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(
        f"PASS generated {len(lines)} Type 12/native-DM clocks "
        f"seed=0x{args.seed:x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
