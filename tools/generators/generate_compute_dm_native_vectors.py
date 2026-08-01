#!/usr/bin/env python3
"""Generate deterministic Type 4/native-DM model-versus-RTL vectors."""

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
    ComputeDMNativeState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    LogicalPhase,
    UNKNOWN,
    apply_compute_dm_native_cycle,
    decode_compute_dm,
    read_dreg,
)


def _append(word: int, value: int | bool, width: int) -> int:
    return (word << width) | (int(value) & ((1 << width) - 1))


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _mr(state: ComputeDMNativeState) -> tuple[bool, int]:
    core = state.core
    bank = core.alternate if core.status.alternate_bank else core.primary
    mr0, mr1, mr2 = bank.mr
    if not all(isinstance(item, ExactWord) for item in (mr0, mr1, mr2)):
        return False, 0
    return True, (mr2.value << 32) | (mr1.value << 16) | mr0.value


def _astat(state: ComputeDMNativeState) -> tuple[int, int]:
    mask = 0
    value = 0
    for bit in ASTATBit:
        item = state.core.status.astat.bit(bit)
        if isinstance(item, bool):
            mask |= 1 << int(bit)
            value |= int(item) << int(bit)
    return mask, value


def _opcode(
    *,
    dag: int = 0,
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
        0x600000
        | (dag << 20)
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
            dag=rng.randrange(2),
            write=bool(rng.randrange(2)),
            z=rng.randrange(2),
            amf=rng.randrange(32),
            yop=rng.randrange(4),
            xop=rng.randrange(8),
            dreg=rng.randrange(16),
            i_local=rng.randrange(4),
            m_local=rng.randrange(4),
        )
        if decode_compute_dm(opcode) is not None:
            return opcode


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ComputeDMNativeState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        phase: LogicalPhase = LogicalPhase.STATE_1,
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
        af: ExactWord | None = None,
        mf: ExactWord | None = None,
        dag_setup: DAGRegisterSetup | None = None,
        inspect: bool = False,
        probe_dreg: int | None = None,
        probe_dag: int | None = None,
    ) -> None:
        nonlocal state
        if probe_dreg is None:
            probe_dreg = rng.randrange(16)
        if probe_dag is None:
            probe_dag = rng.randrange(8)
        result = apply_compute_dm_native_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            bus_relinquished=relinquished,
            execute=execute,
            opcode=opcode,
            dm_ack=ack,
            dmd_read_data=(
                ExactWord(16, read_data) if read_valid else UNKNOWN
            ),
            setup_astat=astat,
            setup_mstat=mstat,
            setup_dreg=dreg,
            setup_af=af,
            setup_mf=mf,
            setup_dag=dag_setup,
            inspect_probe=inspect,
        )

        stimulus = 0
        for item, width in (
            (reset, 1),
            (int(phase), 3),
            (advance, 1),
            (relinquished, 1),
            (execute, 1),
            (opcode, 24),
            (ack, 1),
            (read_data, 16),
            (read_valid, 1),
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
            (inspect, 1),
            (probe_dreg, 4),
            (probe_dag, 3),
        ):
            stimulus = _append(stimulus, item, width)

        core = result.core
        bus = result.bus
        pre = 0
        for item, width in (
            (result.issue_boundary, 1),
            (result.phase_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (core.class_valid, 1),
            (core.action_valid, 1),
            (core.unsupported_subencoding, 1),
            (core.accepted, 1),
            (core.instruction_complete, 1),
            (core.transaction_active, 1),
            (core.stalled, 1),
            (core.busy, 1),
            (core.invalid_opcode, 1),
            (core.dm_select, 1),
            (core.dm_read, 1),
            (core.dm_write, 1),
            (core.dm_address_known, 1),
            (core.dm_address, 14),
            (core.dm_write_data_known, 1),
            (core.dm_write_data, 16),
            (core.compute_result_known, 1),
            (core.dag_configuration_valid, 1),
            (core.i_write, 1),
            (core.i_write_known, 1),
            (core.dreg_write, 1),
            (core.dreg_write_known, 1),
            (core.alu_write, 1),
            (core.mac_write, 1),
            (core.alu_status_write, 1),
            (core.mac_status_write, 1),
            (bus.request_accepted, 1),
            (bus.dmack_sample_event, 1),
            (bus.dmack_accepted, 1),
            (bus.wait_extension_event, 1),
            (bus.completion_event, 1),
            (bus.read_sample_event, 1),
            (bus.transaction_active, 1),
            (bus.waiting, 1),
            (bus.address_output_enable, 1),
            (bus.control_output_enable, 1),
            (bus.data_output_enable, 1),
            (bus.address_known, 1),
            (bus.address, 14),
            (bus.write_data_known, 1),
            (bus.write_data, 16),
            (bus.dms_n, 1),
            (bus.dmrd_n, 1),
            (bus.dmwr_n, 1),
        ):
            pre = _append(pre, item, width)

        selected = (
            result.state.core.alternate
            if result.state.core.status.alternate_bank
            else result.state.core.primary
        )
        probe_known, probe_value = _exact(
            read_dreg(selected, DREG(probe_dreg))
        )
        af_known, af_value = _exact(selected.af)
        mf_known, mf_value = _exact(selected.mf)
        mr_known, mr_value = _mr(result.state)
        i_value = result.state.core.dag.i[probe_dag]
        m_value = result.state.core.dag.m[probe_dag]
        l_value = result.state.core.dag.l[probe_dag]
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
            (af_known, 1),
            (af_value, 16),
            (mf_known, 1),
            (mf_value, 16),
            (mr_known, 1),
            (mr_value, 40),
            (astat_mask, 8),
            (astat_value, 8),
            (result.state.core.status.mstat.value, 4),
            (result.state.core.status.alternate_bank, 1),
            (result.state.core.pending is not None, 1),
            (result.state.bus.active, 1),
            (result.state.bus.waiting, 1),
            (result.state.bus.acknowledged, 1),
            (result.state.bus.response_valid, 1),
        ):
            post = _append(post, item, width)
        lines.append(f"{stimulus:037x} {pre:026x} {post:041x}")
        state = result.state

    emit(reset=True)
    for bank in (0, 1):
        emit(phase=LogicalPhase.STATE_8, mstat=ExactWord(4, bank))
        emit(phase=LogicalPhase.STATE_8, astat=ExactWord(8, 0x5A ^ bank))
        for code in DREG:
            emit(
                phase=LogicalPhase.STATE_8,
                dreg=DREGWrite(
                    code,
                    ExactWord(16, (bank << 15) | (int(code) * 0x421 + 3)),
                ),
            )
        emit(phase=LogicalPhase.STATE_8, af=ExactWord(16, 0xA100 + bank))
        emit(phase=LogicalPhase.STATE_8, mf=ExactWord(16, 0xB100 + bank))
    for address in range(8):
        for kind, value in (
            (DAGRegisterKind.I, 0x100 + address * 0x20),
            (DAGRegisterKind.M, 1),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase=LogicalPhase.STATE_8,
                dag_setup=DAGRegisterSetup(kind, address, value),
            )

    read_opcode = _opcode(amf=0x13, dreg=int(DREG.AX0))
    emit(phase=LogicalPhase.STATE_8, execute=True, opcode=read_opcode)
    for phase in (
        LogicalPhase.STATE_1,
        LogicalPhase.STATE_2,
        LogicalPhase.STATE_3,
        LogicalPhase.STATE_4,
        LogicalPhase.STATE_5,
        LogicalPhase.STATE_6,
        LogicalPhase.STATE_7,
    ):
        emit(phase=phase, ack=True, read_data=0xCAFE)

    write_opcode = _opcode(
        write=True,
        amf=0x13,
        dreg=int(DREG.AR),
    )
    emit(phase=LogicalPhase.STATE_8, execute=True, opcode=write_opcode)
    for phase in LogicalPhase:
        if phase != LogicalPhase.STATE_8:
            emit(phase=phase, ack=True)

    phase = LogicalPhase.STATE_8
    for _ in range(random_count):
        reset = rng.randrange(2000) == 0
        advance = rng.randrange(10) != 0
        relinquished = rng.randrange(80) == 0
        kwargs: dict[str, object] = {
            "reset": reset,
            "phase": phase,
            "advance": advance,
            "relinquished": relinquished,
            "ack": rng.randrange(4) != 0,
            "read_data": rng.randrange(1 << 16),
            "read_valid": rng.randrange(12) != 0,
        }
        if not reset:
            if phase == LogicalPhase.STATE_8 and state.core.pending is None:
                choice = rng.randrange(24)
                if choice < 15:
                    kwargs["execute"] = True
                    kwargs["opcode"] = _random_legal_opcode(rng)
                    kwargs["inspect"] = choice == 0
                elif choice == 15:
                    kwargs["execute"] = True
                    kwargs["opcode"] = _opcode(
                        amf=0x13,
                        dreg=int(DREG.AR),
                    )
                elif choice == 16:
                    kwargs["astat"] = ExactWord(8, rng.randrange(256))
                elif choice == 17:
                    kwargs["mstat"] = ExactWord(4, rng.randrange(16))
                elif choice < 21:
                    kwargs["dreg"] = DREGWrite(
                        DREG(rng.randrange(16)),
                        ExactWord(16, rng.randrange(1 << 16)),
                    )
                elif choice == 21:
                    kwargs["af"] = ExactWord(16, rng.randrange(1 << 16))
                elif choice == 22:
                    kwargs["mf"] = ExactWord(16, rng.randrange(1 << 16))
                else:
                    kwargs["dag_setup"] = DAGRegisterSetup(
                        DAGRegisterKind(rng.randrange(3)),
                        rng.randrange(8),
                        rng.randrange(1 << 14),
                    )
            elif state.core.pending is None and rng.randrange(100) == 0:
                kwargs["execute"] = True
                kwargs["opcode"] = _random_legal_opcode(rng)
        emit(**kwargs)
        if advance:
            phase = LogicalPhase((int(phase) + 1) & 7)
    emit(reset=True, phase=phase)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x2104DA,
    )
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"PASS generated {len(lines)} Type 4/native-DM clocks "
        f"seed=0x{args.seed:x}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
