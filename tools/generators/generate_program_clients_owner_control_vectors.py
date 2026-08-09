#!/usr/bin/env python3
"""Generate three-client/shared-cache/native-PM differential vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    BusControlMode,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    HaltControlMode,
    LogicalPhase,
    ProgramBusOwner,
    ProgramClientsOwnerControlState,
    UNKNOWN,
    apply_program_clients_owner_control_cycle,
    read_dreg,
    register_code_by_name,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _type5(rng: random.Random, *, write: bool | None = None) -> int:
    while True:
        opcode = (
            0x500000
            | (int(rng.randrange(2) if write is None else write) << 19)
            | (rng.randrange(2) << 18)
            | (rng.choice((0, 0x10, 0x13)) << 13)
            | (rng.randrange(4) << 11)
            | (rng.randrange(8) << 8)
            | (rng.randrange(16) << 4)
            | rng.randrange(16)
        )
        from sim.reference_models.adsp2100_model import decode_compute_pm

        if decode_compute_pm(opcode) is not None:
            return opcode


def _type13(rng: random.Random, *, write: bool | None = None) -> int:
    while True:
        opcode = (
            0x110000
            | (int(rng.randrange(2) if write is None else write) << 15)
            | (rng.randrange(16) << 11)
            | (rng.choice((0, 2, 3, 4, 5, 6, 7)) << 8)
            | (rng.randrange(16) << 4)
            | rng.randrange(16)
        )
        from sim.reference_models.adsp2100_model import decode_shifter_pm

        if decode_shifter_pm(opcode) is not None:
            return opcode


def _type17(destination: int, source: int) -> int:
    return (
        0x0D0000
        | ((destination >> 4) << 10)
        | ((source >> 4) << 8)
        | ((destination & 0xF) << 4)
        | (source & 0xF)
    )


def _type7(code: int, value: int) -> int:
    return (
        0x300000
        | ((code >> 4) << 18)
        | ((value & 0x3FFF) << 4)
        | (code & 0xF)
    )


def _type6(destination: int, value: int) -> int:
    return 0x400000 | ((value & 0xFFFF) << 4) | (destination & 0xF)


def _type26(payload: int) -> int:
    return 0x040000 | (payload & 0x1F)


def _type2(*, immediate: int) -> int:
    return 0xB00000 | ((immediate & 0xFFFF) << 4)


def _type3(
    *, write: bool, address: int = 0x0123, register_code: int = 0
) -> int:
    return (
        0x800000
        | (int(write) << 20)
        | ((register_code >> 4) << 18)
        | ((address & 0x3FFF) << 4)
        | (register_code & 0xF)
    )


def _type4(
    *,
    write: bool,
    dag: int = 1,
    destination_feedback: bool = False,
    amf: int = 0,
    yop: int = 0,
    xop: int = 0,
    dreg: DREG = DREG.AX0,
) -> int:
    return (
        0x600000
        | ((dag & 1) << 20)
        | (int(write) << 19)
        | (int(destination_feedback) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 0x3) << 11)
        | ((xop & 0x7) << 8)
        | (int(dreg) << 4)
    )


def _type12(
    *,
    write: bool,
    dag: int = 1,
    sf: int = 0,
    xop: int = 2,
    dreg: DREG = DREG.AX0,
) -> int:
    return (
        0x120000
        | ((dag & 1) << 16)
        | (int(write) << 15)
        | ((sf & 0xF) << 11)
        | ((xop & 0x7) << 8)
        | (int(dreg) << 4)
    )


def _type20(*, interrupt_return: bool, condition: int = 0xF) -> int:
    return (
        0x0A0000
        | (int(interrupt_return) << 4)
        | (condition & 0xF)
    )


def generate_lines(
    random_count: int, seed: int
) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = ProgramClientsOwnerControlState.reset()
    phase = LogicalPhase.STATE_8
    br_n = True
    lines: list[str] = []
    coverage = {name: 0 for name in (
        "linear_accept", "type5_accept", "type13_accept", "type5_retry",
        "type13_retry", "cache_fill", "type5_complete", "type13_complete",
        "type5_external", "type13_external", "collision", "client_conflict",
        "grant", "resume", "masked", "fetch_to_pm", "pm_to_fetch",
        "fetched_compute_to_pm", "fetched_type9_to_pm",
        "fetched_unknown_condition_invalid",
        "fetched_type14_shift_to_pm", "fetched_type14_move_to_pm",
        "fetched_type15_to_pm", "fetched_type16_to_pm",
        "fetched_type16_unknown_invalid",
        "fetched_type16_exp_lo_preserve",
        "fetched_type16_exp_lo_invalid",
        "fetched_type21_to_pm", "fetched_type21_unknown_invalid",
        "fetched_type17_dag_unknown_invalid",
        "fetched_type17_px_unknown_invalid",
        "fetched_type17_status_unknown_invalid",
        "fetched_type17_mstat_unknown_conflict",
        "fetched_type17_sstat_transitions",
        "status_stack_astat_validity_restore",
        "status_stack_mstat_validity_restore",
        "status_stack_imask_validity_restore",
        "interrupt_rti_astat_validity_restore",
        "interrupt_rti_mstat_validity_restore",
        "fetched_type23_to_pm", "fetched_type23_unknown_invalid",
        "fetched_type24_to_pm", "fetched_type24_unknown_invalid",
        "fetched_type25_true_to_pm", "fetched_type25_false_preserve",
        "fetched_type25_unknown_invalid",
        "automatic_type5_issue", "automatic_type13_issue",
        "automatic_hit_retire", "automatic_recovery_retire",
        "automatic_following_fetch", "automatic_flow_blocked",
        "automatic_irq_deferred", "automatic_irq_recognized",
        "automatic_irq_vector_issue",
        "halt_recognized", "halt_force_fetch", "halt_stop", "halt_resume",
        "halt_release_blocked", "halt_hold", "halt_br_conflict",
        "halt_attachment_conflict", "halt_type5_force",
        "halt_type13_force", "halt_ordinary_stop",
        "dm_type2_accept", "dm_type3_accept", "dm_type4_accept",
        "dm_type12_accept", "dm_wait", "dm_completion",
        "paired_pm_dm_completion",
        "fetched_type3_invalid_dmd",
        "fetched_type4_compute_valid_dmd_invalid",
        "fetched_type4_compute_invalid_dmd_valid",
        "fetched_type12_shift_valid_dmd_invalid",
        "fetched_type12_shift_invalid_dmd_valid",
    )}

    def emit(
        *,
        reset: bool = False,
        phase_override: LogicalPhase | None = None,
        advance: bool = True,
        halt_n: bool = True,
        dmack: bool = True,
        instruction_setup: tuple[int, int] | None = None,
        irq_n: int = 0xF,
        automatic_pm_flow: bool = False,
        type5_execute: bool = False,
        type5_opcode: int = 0,
        type5_next: int = 0,
        type5_next_valid: bool = True,
        type13_execute: bool = False,
        type13_opcode: int = 0,
        type13_next: int = 0,
        type13_next_valid: bool = True,
        pmd: int = 0,
        pmd_valid: bool = True,
        dmd: int = 0,
        dmd_valid: bool = True,
        astat: ExactWord | None = None,
        mstat: ExactWord | None = None,
        dreg: DREGWrite | None = None,
        af: ExactWord | None = None,
        mf: ExactWord | None = None,
        sb: ExactWord | None = None,
        dag: DAGRegisterSetup | None = None,
        px: ExactWord | None = None,
        linear_probe: int = 0,
        pm_probe_dreg: int = 0,
        pm_probe_dag: int = 0,
    ) -> None:
        nonlocal state, phase
        use_phase = phase if phase_override is None else phase_override
        # The retained Type 5 slice keeps its inspection mux disabled, so its
        # data and validity observations are coherent only when the external
        # selector follows the opcode memory-DREG field.
        pm_probe_dreg = (type5_opcode >> 4) & 0xF
        # The shared architectural owner also exposes an independent retained
        # fetch probe. Keep it on the same DREG so fail-closed dual-client
        # execute vectors remain observable even though neither PM decoder is
        # admitted to provide a live selector.
        linear_probe = pm_probe_dreg
        setup_value = (
            (
                ExactWord(14, instruction_setup[0]),
                ExactWord(24, instruction_setup[1]),
            )
            if instruction_setup is not None
            else None
        )
        result = apply_program_clients_owner_control_cycle(
            state,
            reset=reset,
            phase=use_phase,
            phase_advance=advance,
            br_n=br_n,
            halt_n=halt_n,
            dmack=dmack,
            irq_n=irq_n,
            instruction_setup=setup_value,
            automatic_pm_flow=automatic_pm_flow,
            type5_execute=type5_execute,
            type5_opcode=type5_opcode,
            type5_next_fetch_address=(
                ExactWord(14, type5_next) if type5_next_valid else UNKNOWN
            ),
            type13_execute=type13_execute,
            type13_opcode=type13_opcode,
            type13_next_fetch_address=(
                ExactWord(14, type13_next) if type13_next_valid else UNKNOWN
            ),
            pmd_read_data=ExactWord(24, pmd) if pmd_valid else UNKNOWN,
            dmd_read_data=ExactWord(16, dmd) if dmd_valid else UNKNOWN,
            setup_astat=astat,
            setup_mstat=mstat,
            setup_dreg=dreg,
            setup_af=af,
            setup_mf=mf,
            setup_sb=sb,
            setup_dag=dag,
            setup_px=px,
        )

        stimulus = 0
        setup_pc = instruction_setup[0] if instruction_setup else 0
        setup_opcode = instruction_setup[1] if instruction_setup else 0
        for value, width in (
            (reset, 1), (int(use_phase), 3), (advance, 1), (br_n, 1),
            (halt_n, 1), (dmack, 1),
            (instruction_setup is not None, 1), (setup_pc, 14),
            (setup_opcode, 24), (irq_n, 4),
            (automatic_pm_flow, 1),
            (type5_execute, 1), (type5_opcode, 24), (type5_next, 14),
            (type5_next_valid, 1),
            (type13_execute, 1), (type13_opcode, 24), (type13_next, 14),
            (type13_next_valid, 1), (pmd, 24), (pmd_valid, 1),
            (astat is not None, 1), (astat.value if astat else 0, 8),
            (mstat is not None, 1), (mstat.value if mstat else 0, 4),
            (dreg is not None, 1), (int(dreg.address) if dreg else 0, 4),
            (dreg.data.value if dreg else 0, 16),
            (af is not None, 1), (af.value if af else 0, 16),
            (mf is not None, 1), (mf.value if mf else 0, 16),
            (sb is not None, 1), (sb.value if sb else 0, 5),
            (dag is not None, 1), (int(dag.kind) if dag else 0, 2),
            (dag.address if dag else 0, 3), (dag.value if dag else 0, 14),
            (px is not None, 1), (px.value if px else 0, 8),
            (linear_probe, 6), (pm_probe_dreg, 4), (pm_probe_dag, 3),
            (dmd, 16), (dmd_valid, 1),
        ):
            stimulus = _append(stimulus, value, width)

        interface = result.interface
        owner = interface.owner_bus
        bus = owner.bus
        type5_word_known, type5_word = _exact(result.type5_next_instruction)
        type13_word_known, type13_word = _exact(result.type13_next_instruction)
        events = 0
        for value, width in (
            (result.issue_boundary, 1), (result.client_execute_conflict, 1),
            (result.integration_conflict, 1),
            (result.automatic_pm_instruction_issue, 1),
            (result.automatic_pm_instruction_retire, 1),
            (result.automatic_pm_flow_blocked, 1),
            (int(state.halt.mode), 2),
            (result.halt.halt_recognized, 1),
            (result.halt.halt_stop_event, 1),
            (result.halt.force_fetch_issue, 1),
            (result.halt.resume_event, 1),
            (result.halt.release_blocked, 1),
            (result.halt.phase_hold, 1),
            (result.halt.effective_phase_advance, 1),
            (result.halt.halted, 1),
            (result.halt_br_conflict, 1),
            (result.halt_attachment_conflict, 1),
            (result.linear.fetch_request_presented, 1),
            (result.linear.instruction_issue, 1), (result.linear.retire_event, 1),
            (result.type5_request_presented, 1), (owner.type5_accepted, 1),
            (result.type5_retry_pending, 1),
            (result.type5.data_action_complete, 1),
            (result.type5.instruction_complete, 1),
            (result.type5_next_instruction_valid and type5_word_known, 1),
            (type5_word
             if result.type5_next_instruction_valid and type5_word_known
             else 0, 24),
            (result.type13_request_presented, 1), (owner.type13_accepted, 1),
            (result.type13_retry_pending, 1),
            (result.type13.data_action_complete, 1),
            (result.type13.instruction_complete, 1),
            (result.type13_next_instruction_valid and type13_word_known, 1),
            (type13_word
             if result.type13_next_instruction_valid and type13_word_known
             else 0, 24),
            (result.cache_fill, 1), (result.cache.fill_accepted, 1),
            (int(state.interface.control.mode), 3),
            (interface.control.instruction_issue_inhibit
             or result.halt.instruction_issue_inhibit, 1),
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
            (bus.address_output_enable, 1), (bus.control_output_enable, 1),
            (bus.data_output_enable, 1), (bus.address_known, 1),
            (bus.address if bus.address_known else 0, 14),
            (bus.pmda, 1), (bus.control_output_enable, 1),
            (bus.pms_n, 1), (bus.pmrd_n, 1), (bus.pmwr_n, 1),
            (bus.write_data_known, 1),
            (bus.write_data if bus.write_data_known else 0, 24),
        ):
            events = _append(events, value, width)

        dm_bus = result.dm.bus
        for value, width in (
            (result.architectural_phase_advance, 1),
            (result.interrupt_wait_sample, 1),
            (result.dm.fetched_accepted, 1),
            (result.dm.fetched_dmack_sample, 1),
            (result.dm.fetched_dmack_accepted, 1),
            (result.dm.fetched_wait_extension, 1),
            (result.dm.fetched_completion, 1),
            (result.dm.fetched_read_sample, 1),
            (dm_bus.transaction_active, 1), (dm_bus.waiting, 1),
            (dm_bus.address_output_enable, 1),
            (dm_bus.control_output_enable, 1),
            (dm_bus.data_output_enable, 1),
            (dm_bus.address_known, 1),
            (dm_bus.address if dm_bus.address_known else 0, 14),
            (dm_bus.dms_n, 1), (dm_bus.dmrd_n, 1), (dm_bus.dmwr_n, 1),
            (dm_bus.write_data_known, 1),
            (dm_bus.write_data if dm_bus.write_data_known else 0, 16),
        ):
            events = _append(events, value, width)

        type5_bank = (
            result.state.type5.alternate
            if result.state.type5.status.alternate_bank
            else result.state.type5.primary
        )
        type13_bank = (
            result.state.type13.alternate
            if result.state.type13.status.alternate_bank
            else result.state.type13.primary
        )
        t5_dreg_known, t5_dreg = _exact(
            read_dreg(type5_bank, DREG(pm_probe_dreg))
        )
        t13_dreg_known, t13_dreg = _exact(
            read_dreg(type13_bank, DREG(pm_probe_dreg))
        )
        bank_selection_known = bool(
            result.state.linear.architecture.mstat_valid_mask & 1
        )
        if not bank_selection_known:
            t5_dreg_known, t5_dreg = False, 0
            t13_dreg_known, t13_dreg = False, 0
        t5_px_known, t5_px = _exact(result.state.type5.px)
        t13_px_known, t13_px = _exact(result.state.type13.px)
        post = 0
        cache = result.state.cache
        for value, width in (
            (result.state.linear.architecture.pc.value, 14),
            (result.state.linear.instruction.value
             if result.state.linear.instruction_valid
             and isinstance(result.state.linear.instruction, ExactWord)
             else 0, 24),
            (t5_dreg_known, 1), (t5_dreg, 16),
            (t5_px_known, 1), (t5_px, 8),
            (t13_dreg_known, 1), (t13_dreg, 16),
            (t13_px_known, 1), (t13_px, 8),
            (cache.region_count != 0, 1), (cache.region_start, 14),
            (cache.region_count, 5),
        ):
            post = _append(post, value, width)

        for key, hit in (
            ("linear_accept", owner.fetch_accepted),
            ("type5_accept", owner.type5_accepted),
            ("type13_accept", owner.type13_accepted),
            ("type5_retry", result.type5_retry_pending),
            ("type13_retry", result.type13_retry_pending),
            ("cache_fill", result.cache_fill),
            ("type5_complete", result.type5.instruction_complete),
            ("type13_complete", result.type13.instruction_complete),
            ("type5_external", result.type5.fetched_instruction_known),
            ("type13_external", result.type13.fetched_instruction_known),
            ("collision", owner.request_conflict),
            ("client_conflict", result.client_execute_conflict),
            ("grant", not interface.native_bg_n),
            ("resume", interface.control.resume_event),
            ("masked", interface.native_bus_relinquished
             and not bus.address_output_enable
             and not bus.control_output_enable
             and not bus.data_output_enable),
            ("automatic_type5_issue",
             result.automatic_pm_instruction_issue
             and owner.type5_accepted),
            ("automatic_type13_issue",
             result.automatic_pm_instruction_issue
             and owner.type13_accepted),
            ("automatic_hit_retire",
             result.automatic_pm_instruction_retire
             and (result.type5.data_action_complete
                  or result.type13.data_action_complete)),
            ("automatic_recovery_retire",
             result.automatic_pm_instruction_retire
             and (result.type5.fetched_instruction_known
                  or result.type13.fetched_instruction_known)),
            ("automatic_following_fetch",
             automatic_pm_flow and owner.fetch_accepted),
            ("automatic_flow_blocked", result.automatic_pm_flow_blocked),
            ("automatic_irq_deferred",
             automatic_pm_flow
             and (result.type5.data_action_complete
                  or result.type13.data_action_complete)
             and not result.automatic_pm_instruction_retire
             and bool(result.linear.interrupt.enabled_requests)),
            ("automatic_irq_recognized",
             result.automatic_pm_instruction_retire
             and result.linear.interrupt.recognition_event),
            ("automatic_irq_vector_issue",
             automatic_pm_flow and result.linear.interrupt_entry_event),
            ("halt_recognized", result.halt.halt_recognized),
            ("halt_force_fetch", result.halt.force_fetch_issue),
            ("halt_stop", result.halt.halt_stop_event),
            ("halt_resume", result.halt.resume_event),
            ("halt_release_blocked", result.halt.release_blocked),
            ("halt_hold", result.halt.phase_hold),
            ("halt_br_conflict", result.halt_br_conflict),
            ("halt_attachment_conflict", result.halt_attachment_conflict),
            ("halt_type5_force",
             result.halt.force_fetch_issue
             and owner.type5_accepted),
            ("halt_type13_force",
             result.halt.force_fetch_issue
             and owner.type13_accepted),
            ("halt_ordinary_stop",
             result.halt.halt_stop_event
             and state.halt.mode is HaltControlMode.STOP_PENDING
             and state.interface.owner_bus.owner is ProgramBusOwner.FETCH),
            ("dm_type2_accept", result.dm.fetched_accepted
             and state.linear.instruction_valid
             and isinstance(state.linear.instruction, ExactWord)
             and (state.linear.instruction.value & 0xE00000) == 0xA00000),
            ("dm_type3_accept", result.dm.fetched_accepted
             and state.linear.instruction_valid
             and isinstance(state.linear.instruction, ExactWord)
             and (state.linear.instruction.value & 0xE00000) == 0x800000),
            ("dm_type4_accept", result.dm.fetched_accepted
             and state.linear.instruction_valid
             and isinstance(state.linear.instruction, ExactWord)
             and (state.linear.instruction.value & 0xE00000) == 0x600000),
            ("dm_type12_accept", result.dm.fetched_accepted
             and state.linear.instruction_valid
             and isinstance(state.linear.instruction, ExactWord)
             and (state.linear.instruction.value & 0xFE0000) == 0x120000),
            ("dm_wait", result.dm.fetched_wait_extension),
            ("dm_completion", result.dm.fetched_completion),
            ("paired_pm_dm_completion", result.dm.fetched_completion
             and owner.fetch_completion),
        ):
            coverage[key] += int(hit)

        lines.append(f"{stimulus:073x} {events:050x} {post:032x}")
        state = result.state
        if phase_override is None and advance:
            phase = LogicalPhase((int(phase) + 1) & 7)

    def bus_cycle(
        *, pmd: int, pmd_valid: bool = True, **controls: object
    ) -> None:
        for use_phase in (
            LogicalPhase.STATE_1, LogicalPhase.STATE_2,
            LogicalPhase.STATE_3, LogicalPhase.STATE_4,
            LogicalPhase.STATE_5, LogicalPhase.STATE_6,
        ):
            emit(
                phase_override=use_phase,
                pmd=pmd,
                pmd_valid=pmd_valid,
                **controls,
            )
        emit(
            phase_override=LogicalPhase.STATE_7,
            pmd=pmd,
            pmd_valid=pmd_valid,
            **controls,
        )

    def reset_pm_operands() -> None:
        emit(reset=True, phase_override=LogicalPhase.STATE_8)
        for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(register, ExactWord(16, value)),
            )
        for kind, value in (
            (DAGRegisterKind.I, 0x0100),
            (DAGRegisterKind.M, 1),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag=DAGRegisterSetup(kind, 4, value),
            )
        emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))

    # Exercise the four fetched DM classes through the same retained
    # architectural owner as the three PM clients. Type 2 repeats one full
    # physical cycle before its paired PM/DM completion.
    for index, opcode in enumerate((
        _type2(immediate=0xBEEF),
        _type3(write=True),
        _type4(write=True),
        _type12(write=True),
    )):
        reset_pm_operands()
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(0x1200 + index, opcode),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        if index == 0:
            for use_phase in (
                LogicalPhase.STATE_1, LogicalPhase.STATE_2,
                LogicalPhase.STATE_3, LogicalPhase.STATE_4,
                LogicalPhase.STATE_5,
            ):
                emit(phase_override=use_phase)
            emit(phase_override=LogicalPhase.STATE_6, dmack=False)
            for use_phase in (
                LogicalPhase.STATE_7, LogicalPhase.STATE_8,
                LogicalPhase.STATE_1, LogicalPhase.STATE_2,
                LogicalPhase.STATE_3, LogicalPhase.STATE_4,
                LogicalPhase.STATE_5,
            ):
                emit(phase_override=use_phase)
            emit(phase_override=LogicalPhase.STATE_6, dmack=True)
            emit(
                phase_override=LogicalPhase.STATE_7,
                pmd=0, dmd=0xCAFE,
            )
        else:
            bus_cycle(pmd=0, dmd=0xCAFE)

    # The combined owner carries exact validity beside the two-state fetched
    # Type 3/4/12 data path.  Each case observes the completed memory
    # destination through the shared DREG probe and the independent compute or
    # shifter destination through a following Type 5 PM store.
    reset_pm_operands()
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x1240,
            _type3(
                write=False,
                address=0x0123,
                register_code=int(DREG.AX1),
            ),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(
        pmd=0,
        pmd_valid=False,
        dmd=0,
        dmd_valid=False,
        type5_opcode=0x500000 | (int(DREG.AX1) << 4),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000 | (int(DREG.AX1) << 4),
        type5_next=0x1241,
    )
    coverage["fetched_type3_invalid_dmd"] += 1

    reset_pm_operands()
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x1250,
            _type4(write=False, amf=0x13, dreg=DREG.AX1),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(
        pmd=0,
        pmd_valid=False,
        dmd=0,
        dmd_valid=False,
        type5_opcode=0x500000 | (int(DREG.AX1) << 4),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000 | (int(DREG.AR) << 4),
        type5_next=0x1251,
    )
    coverage["fetched_type4_compute_valid_dmd_invalid"] += 1

    reset_pm_operands()
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x1260,
            _type4(
                write=False,
                amf=0x13,
                xop=2,
                dreg=DREG.AX1,
            ),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(
        pmd=0,
        pmd_valid=False,
        dmd=0xBEEF,
        dmd_valid=True,
        type5_opcode=0x500000 | (int(DREG.AX1) << 4),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000 | (int(DREG.AR) << 4),
        type5_next=0x1261,
    )
    coverage["fetched_type4_compute_invalid_dmd_valid"] += 1

    reset_pm_operands()
    for register, value in ((DREG.AR, 0x1234), (DREG.SE, 0)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x1270,
            _type12(write=False, dreg=DREG.AX1),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(
        pmd=0,
        pmd_valid=False,
        dmd=0,
        dmd_valid=False,
        type5_opcode=0x500000 | (int(DREG.AX1) << 4),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000 | (int(DREG.SR1) << 4),
        type5_next=0x1271,
    )
    coverage["fetched_type12_shift_valid_dmd_invalid"] += 1

    reset_pm_operands()
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x1280,
            _type12(write=False, dreg=DREG.AX1),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(
        pmd=0,
        pmd_valid=False,
        dmd=0xCAFE,
        dmd_valid=True,
        type5_opcode=0x500000 | (int(DREG.AX1) << 4),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000 | (int(DREG.SR1) << 4),
        type5_next=0x1281,
    )
    coverage["fetched_type12_shift_invalid_dmd_valid"] += 1

    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
            pm_probe_dreg=int(register),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(phase_override=LogicalPhase.STATE_8, instruction_setup=(0x0220, 0))
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0xC00000)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x500010,
        type5_next=0x0221,
        pm_probe_dreg=int(DREG.AX1),
    )
    bus_cycle(pmd=0xCAFE55)
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True, type5_opcode=0x500000, type5_next=1,
        type13_execute=True, type13_opcode=0x110000, type13_next=1,
    )
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x0100, 0),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True, type5_opcode=0x500000, type5_next=0x0200,
    )
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x0100, 0),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True, type13_opcode=0x110000, type13_next=0x0200,
    )
    emit(reset=True, phase_override=LogicalPhase.STATE_8)

    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True, type5_opcode=0x500000, type5_next=0x0333,
    )
    bus_cycle(pmd=0x101122)
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0x334455)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True, type13_opcode=0x110000, type13_next=0x0444,
    )
    bus_cycle(pmd=0x202233)
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0x445566)

    # Directed shared-state visibility in both PM-client directions.  A read
    # loads one shared {DREG,PX} pair and the following other-class store must
    # drive that exact 24-bit value.
    for first_is_type5, base, read_word in (
        (True, 0x0600, 0xC0DE77),
        (False, 0x0700, 0xBEEF66),
    ):
        emit(reset=True, phase_override=LogicalPhase.STATE_8)
        for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(register, ExactWord(16, value)),
            )
        for kind, value in (
            (DAGRegisterKind.I, 0x0100),
            (DAGRegisterKind.M, 1),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag=DAGRegisterSetup(kind, 4, value),
            )
        emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(base, 0),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0xABCDEF)
        if first_is_type5:
            emit(
                phase_override=LogicalPhase.STATE_8,
                type5_execute=True,
                type5_opcode=0x500010,
                type5_next=base + 1,
            )
        else:
            emit(
                phase_override=LogicalPhase.STATE_8,
                type13_execute=True,
                type13_opcode=0x110010,
                type13_next=base + 1,
            )
        bus_cycle(pmd=read_word)
        if first_is_type5:
            emit(
                phase_override=LogicalPhase.STATE_8,
                type13_execute=True,
                type13_opcode=0x118010,
                type13_next=base + 2,
            )
        else:
            emit(
                phase_override=LogicalPhase.STATE_8,
                type5_execute=True,
                type5_opcode=0x580010,
                type5_next=base + 2,
            )
        bus_cycle(pmd=0)

    # Fetched Type 6 -> Type 13 and Type 5 -> fetched Type 17 prove that the
    # retained fetch path and both PM clients now use one register image.  A
    # deliberately invalid returned instruction leaves the preload boundary
    # available without claiming automatic PM-client opcode installation.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x0800,
            0x400000 | (0xC0DE << 4) | int(DREG.AX1),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True,
        type13_opcode=0x118010,
        type13_next=0x0801,
    )
    bus_cycle(pmd=0)
    coverage["fetch_to_pm"] += 1

    # Fetched Type 8 computes AR from known cycle-start AX0/AY0, then a Type
    # 5 PM store consumes that result. This explicitly checks the fetched
    # compute validity sidecar rather than relying on two-state RTL data.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x0880,
            0x280000
            | (0x13 << 13)
            | (int(DREG.AX1) << 4)
            | int(DREG.AX0),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000 | (int(DREG.AR) << 4),
        type5_next=0x0881,
        pm_probe_dreg=int(DREG.AR),
    )
    bus_cycle(pmd=0)
    coverage["fetched_compute_to_pm"] += 1

    # A condition-true Type 9 uses the same fetched compute retirement
    # boundary, and its AR result must be known to a following Type 13 store.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x0890,
            0x200000 | (0x13 << 13) | 0xF,
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True,
        type13_opcode=0x118000 | (int(DREG.AR) << 4),
        type13_next=0x0891,
        pm_probe_dreg=int(DREG.AR),
    )
    bus_cycle(pmd=0)
    coverage["fetched_type9_to_pm"] += 1

    # Reset leaves ASTAT.AZ invalid. A conditional Type 9 EQ can therefore
    # either preserve or replace AR, so the validity sidecar must invalidate
    # AR before a following Type 5 store even though RTL data is two-state.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in (
        (DREG.AX0, 0x1234),
        (DREG.AY0, 3),
        (DREG.AR, 0x7777),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x0898,
            0x200000 | (0x13 << 13),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000 | (int(DREG.AR) << 4),
        type5_next=0x0899,
        pm_probe_dreg=int(DREG.AR),
    )
    bus_cycle(pmd=0)
    coverage["fetched_unknown_condition_invalid"] += 1

    # Canonical Type 14 LSHIFT HI writes known SR from AR/SE while its
    # independent move writes AX1 from AX0. Exercise each sidecar through a
    # following PM store in separate clean instruction contexts.
    for probe_move in (False, True):
        emit(reset=True, phase_override=LogicalPhase.STATE_8)
        for register, value in (
            (DREG.AX0, 0x1234),
            (DREG.AY0, 3),
            (DREG.AR, 0x1234),
            (DREG.SE, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(register, ExactWord(16, value)),
            )
        for kind, value in (
            (DAGRegisterKind.I, 0x0100),
            (DAGRegisterKind.M, 1),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag=DAGRegisterSetup(kind, 4, value),
            )
        emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(
                0x08A0 + int(probe_move),
                0x100000
                | (2 << 8)
                | (int(DREG.AX1) << 4)
                | int(DREG.AX0),
            ),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0, pmd_valid=False)
        probe = DREG.AX1 if probe_move else DREG.SR1
        emit(
            phase_override=LogicalPhase.STATE_8,
            type5_execute=not probe_move,
            type5_opcode=(
                0x580000 | (int(probe) << 4)
                if not probe_move else 0
            ),
            type5_next=0x08A2,
            type13_execute=probe_move,
            type13_opcode=(
                0x118000 | (int(probe) << 4)
                if probe_move else 0
            ),
            type13_next=0x08A2,
            pm_probe_dreg=int(probe),
        )
        bus_cycle(pmd=0)
        coverage[
            "fetched_type14_move_to_pm"
            if probe_move else "fetched_type14_shift_to_pm"
        ] += 1

    # Type 15 uses an immediate zero exponent and needs no SE validity.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in (
        (DREG.AX0, 0x1234),
        (DREG.AY0, 3),
        (DREG.AR, 0x1234),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x08B0, 0x0F0000 | (2 << 8)),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True,
        type13_opcode=0x118000 | (int(DREG.SR1) << 4),
        type13_next=0x08B1,
        pm_probe_dreg=int(DREG.SR1),
    )
    bus_cycle(pmd=0)
    coverage["fetched_type15_to_pm"] += 1

    # Type 16 condition F writes a known SR result; reset-time EQ has an
    # unknown predicate and must invalidate the possible SR destination.
    for unknown_condition in (False, True):
        emit(reset=True, phase_override=LogicalPhase.STATE_8)
        for register, value in (
            (DREG.AX0, 0x1234),
            (DREG.AY0, 3),
            (DREG.AR, 0x1234),
            (DREG.SE, 0),
            (DREG.SR1, 0x7777),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(register, ExactWord(16, value)),
            )
        for kind, value in (
            (DAGRegisterKind.I, 0x0100),
            (DAGRegisterKind.M, 1),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag=DAGRegisterSetup(kind, 4, value),
            )
        emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(
                0x08C0 + int(unknown_condition),
                0x0E0000 | (2 << 8)
                | (0 if unknown_condition else 0xF),
            ),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0, pmd_valid=False)
        emit(
            phase_override=LogicalPhase.STATE_8,
            type5_execute=not unknown_condition,
            type5_opcode=(
                0x580000 | (int(DREG.SR1) << 4)
                if not unknown_condition else 0
            ),
            type5_next=0x08C2,
            type13_execute=unknown_condition,
            type13_opcode=(
                0x118000 | (int(DREG.SR1) << 4)
                if unknown_condition else 0
            ),
            type13_next=0x08C2,
            pm_probe_dreg=int(DREG.SR1),
        )
        bus_cycle(pmd=0)
        coverage[
            "fetched_type16_unknown_invalid"
            if unknown_condition else "fetched_type16_to_pm"
        ] += 1

    # EXP LO is conditional even after a true predicate: old SE other than
    # -15 suppresses the write. Therefore an unknown outer predicate preserves
    # a known non--15 SE, while old SE=-15 leaves a possible write and becomes
    # invalid.
    for se_value in (0x00, 0xF1):
        emit(reset=True, phase_override=LogicalPhase.STATE_8)
        for register, value in (
            (DREG.AX0, 0x1234),
            (DREG.AY0, 3),
            (DREG.AR, 0x1234),
            (DREG.SE, se_value),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(register, ExactWord(16, value)),
            )
        for kind, value in (
            (DAGRegisterKind.I, 0x0100),
            (DAGRegisterKind.M, 1),
            (DAGRegisterKind.L, 0),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dag=DAGRegisterSetup(kind, 4, value),
            )
        emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(
                0x08D0 + int(se_value == 0xF1),
                0x0E0000 | (0xE << 11) | (2 << 8),
            ),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0, pmd_valid=False)
        emit(
            phase_override=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=0x580000 | (int(DREG.SE) << 4),
            type5_next=0x08D2,
            pm_probe_dreg=int(DREG.SE),
        )
        bus_cycle(pmd=0)
        coverage[
            "fetched_type16_exp_lo_invalid"
            if se_value == 0xF1
            else "fetched_type16_exp_lo_preserve"
        ] += 1

    # Type 21 updates only the selected I at ordinary-fetch retirement. A
    # following PM client must observe the known modified address, while an
    # unknown selected M makes the stored I and the next PM address invalid.
    for m_local, coverage_key in (
        (0, "fetched_type21_to_pm"),
        (1, "fetched_type21_unknown_invalid"),
    ):
        reset_pm_operands()
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(
                0x08D8 + m_local,
                0x090010 | m_local,
            ),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0, pmd_valid=False)
        emit(
            phase_override=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=0x118000,
            type13_next=0x08DA,
        )
        bus_cycle(pmd=0)
        coverage[coverage_key] += 1

    # Type 17 reads the selected source at cycle start. Reset-unknown AX1
    # therefore invalidates a DAG-I or PX destination, and an unknown MSTAT
    # blocks the following PM client because bank selection is no longer
    # defined by the bounded composition.
    reset_pm_operands()
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x08DC,
            _type17(0x20, int(DREG.AX1)),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000,
        type5_next=0x08DD,
    )
    bus_cycle(pmd=0)
    coverage["fetched_type17_dag_unknown_invalid"] += 1

    reset_pm_operands()
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x08DE,
            _type17(0x37, int(DREG.AX1)),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True,
        type13_opcode=0x118000,
        type13_next=0x08DF,
    )
    bus_cycle(pmd=0)
    coverage["fetched_type17_px_unknown_invalid"] += 1

    for code in (0x30, 0x33, 0x34, 0x35, 0x36):
        reset_pm_operands()
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(
                0x08E0 + (code & 0xF),
                _type17(code, int(DREG.AX1)),
            ),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(
            pmd=_type17(int(DREG.AR), code),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0, pmd_valid=False)
        emit(
            phase_override=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=0x580000 | (int(DREG.AR) << 4),
            type5_next=0x08F0,
        )
        bus_cycle(pmd=0)
        coverage["fetched_type17_status_unknown_invalid"] += 1

    reset_pm_operands()
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x08E0,
            _type17(0x31, int(DREG.AX1)),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True,
        type13_opcode=0x118000,
        type13_next=0x08E1,
    )
    coverage["fetched_type17_mstat_unknown_conflict"] += 1
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x08E1,
            0x400000 | (1 << 4) | int(DREG.AX0),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)

    # The status stack must restore the known-state snapshot accepted with
    # its 16-bit entry. Invalidate ASTAT, IMASK, and MSTAT from reset-unknown
    # AX1, push once, overwrite all three with known immediates, then pop.
    # The restored MSTAT blocks a PM client; after making only MSTAT known,
    # restored ASTAT and IMASK each invalidate a following DREG move.
    reset_pm_operands()
    status_sequence = (
        _type17(0x30, int(DREG.AX1)),
        _type17(0x33, int(DREG.AX1)),
        _type17(0x31, int(DREG.AX1)),
        _type26(0x02),
        _type7(0x30, 0x00A5),
        _type7(0x33, 0x0009),
        _type7(0x31, 0x0000),
        _type26(0x03),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x08E8, status_sequence[0]),
    )
    for next_opcode in status_sequence[1:]:
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=next_opcode)
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True,
        type13_opcode=0x118000,
        type13_next=0x08F0,
    )
    coverage["status_stack_mstat_validity_restore"] += 1

    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x08F0, _type7(0x31, 0)),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=_type17(int(DREG.AR), 0x30))
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_opcode=0x580000 | (int(DREG.AR) << 4),
    )
    coverage["status_stack_astat_validity_restore"] += 1

    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(
            0x08F2,
            _type17(int(DREG.AY1), 0x33),
        ),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_opcode=0x580000 | (int(DREG.AY1) << 4),
    )
    coverage["status_stack_imask_validity_restore"] += 1

    # Read the live composed SSTAT value through fetched Type 17 while the
    # status stack moves empty -> nonempty -> full/overflow -> empty with
    # sticky overflow. The low eight bits are architectural; the observed
    # upper-byte zero extension remains the explicit OQ-016 provisional rule.
    reset_pm_operands()
    sstat_sequence = (
        _type17(int(DREG.AR), 0x32),
        _type26(0x02),
        _type17(int(DREG.AY1), 0x32),
        _type26(0x02),
        _type26(0x02),
        _type26(0x02),
        _type26(0x02),
        _type17(int(DREG.SI), 0x32),
        _type26(0x03),
        _type26(0x03),
        _type26(0x03),
        _type26(0x03),
        _type17(int(DREG.SR0), 0x32),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x08F8, sstat_sequence[0]),
    )
    for index, opcode in enumerate(sstat_sequence):
        probe = (
            (opcode >> 4) & 0xF
            if opcode & 0xFF0000 == 0x0D0000
            else int(DREG.AX0)
        )
        emit(
            phase_override=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            type5_opcode=0x500000 | (probe << 4),
        )
        bus_cycle(
            pmd=(sstat_sequence[index + 1]
                 if index + 1 < len(sstat_sequence) else 0),
            pmd_valid=index + 1 < len(sstat_sequence),
            automatic_pm_flow=True,
            type5_opcode=0x500000 | (probe << 4),
        )
    coverage["fetched_type17_sstat_transitions"] += 1

    # DIVQ samples the divisor, AF, AY0, and old AQ at issue. A following
    # Type 5 PM store observes both a fully known quotient step and the
    # fail-closed result when reset-time AQ remains unknown.
    for aq_known in (True, False):
        reset_pm_operands()
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(DREG.AX0, ExactWord(16, 1)),
        )
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(DREG.AY0, ExactWord(16, 0x8000)),
        )
        emit(phase_override=LogicalPhase.STATE_8, af=ExactWord(16, 2))
        if aq_known:
            emit(phase_override=LogicalPhase.STATE_8, astat=ExactWord(8, 0))
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(
                0x08E0 + int(not aq_known),
                0x071000,
            ),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0, pmd_valid=False)
        emit(
            phase_override=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=0x580000 | (int(DREG.AY0) << 4),
            type5_next=0x08E2,
        )
        bus_cycle(pmd=0)
        coverage[
            "fetched_type23_to_pm"
            if aq_known else "fetched_type23_unknown_invalid"
        ] += 1

    # DIVS has no ASTAT dependency. XOP 0 consumes the initialized AX0 and
    # produces a known AY0; XOP 1 consumes reset-unknown AX1 and invalidates
    # all three division destinations before the PM observation.
    for xop in (0, 1):
        reset_pm_operands()
        for register, value in (
            (DREG.AX0, 1),
            (DREG.AY0, 3),
            (DREG.AY1, 2),
        ):
            emit(
                phase_override=LogicalPhase.STATE_8,
                dreg=DREGWrite(register, ExactWord(16, value)),
            )
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(
                0x08F0 + xop,
                0x060000 | (1 << 11) | (xop << 8),
            ),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0, pmd_valid=False)
        emit(
            phase_override=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=0x580000 | (int(DREG.AY0) << 4),
            type5_next=0x08F2,
        )
        bus_cycle(pmd=0)
        coverage[
            "fetched_type24_to_pm"
            if xop == 0 else "fetched_type24_unknown_invalid"
        ] += 1

    # Exact Type 25 uses implicit MV. Known true replaces all MR segments
    # from the old MR2 sign, known false preserves the prior value, and an
    # unknown MV makes the possible MR write invalid to the next PM client.
    for astat_value, mr1_value, coverage_key in (
        (0x40, 0x0000, "fetched_type25_true_to_pm"),
        (0x00, 0x1234, "fetched_type25_false_preserve"),
        (None, 0x1234, "fetched_type25_unknown_invalid"),
    ):
        reset_pm_operands()
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(DREG.MR1, ExactWord(16, mr1_value)),
        )
        if astat_value is not None:
            emit(
                phase_override=LogicalPhase.STATE_8,
                astat=ExactWord(8, astat_value),
            )
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(0x0900, 0x050000),
        )
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=0, pmd_valid=False)
        emit(
            phase_override=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=0x580000 | (int(DREG.MR1) << 4),
            type5_next=0x0901,
        )
        bus_cycle(pmd=0)
        coverage[coverage_key] += 1

    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x500010,
        type5_next=0x0900,
    )
    bus_cycle(pmd=0xBEEF66)
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x0900, 0x0D0001),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, pmd_valid=False)
    coverage["pm_to_fetch"] += 1

    # Automatic fetched Type 5 miss: the data action commits once, PC/opcode
    # stay frozen through recovery, the returned Type 6 installs at PC+1,
    # and that instruction then executes through the ordinary-fetch client.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x3FFF, 0x500010),
    )
    emit(phase_override=LogicalPhase.STATE_8, automatic_pm_flow=True)
    bus_cycle(pmd=0xBEEF77, automatic_pm_flow=True)
    emit(phase_override=LogicalPhase.STATE_8, automatic_pm_flow=True)
    bus_cycle(
        pmd=0x400000 | (0xA55A << 4) | int(DREG.SI),
        automatic_pm_flow=True,
    )
    emit(phase_override=LogicalPhase.STATE_8, automatic_pm_flow=True)
    bus_cycle(pmd=0, automatic_pm_flow=True)

    # A level IRQ sampled during an automatic Type 5 miss remains pending at
    # data completion, is recognized only when recovery retires the whole
    # instruction, discards the returned sequential word, and issues the
    # retained fetch client's vectoring NOP on the following state 8.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    writable = register_code_by_name(writable=True)
    icntl_opcode = (
        0x300000
        | ((writable["ICNTL"] >> 4) << 18)
        | (0x10 << 4)
        | (writable["ICNTL"] & 0xF)
    )
    imask_opcode = (
        0x300000
        | ((writable["IMASK"] >> 4) << 18)
        | (0xF << 4)
        | (writable["IMASK"] & 0xF)
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x0E00, icntl_opcode),
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    bus_cycle(
        pmd=imask_opcode,
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    bus_cycle(
        pmd=0x500010,
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    bus_cycle(
        pmd=0xCAFE66,
        automatic_pm_flow=True,
        irq_n=0xB,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
        irq_n=0xB,
    )
    bus_cycle(
        pmd=0,
        automatic_pm_flow=True,
        irq_n=0xB,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
        irq_n=0xF,
    )

    # Drive reset-unknown AX1 into ASTAT and MSTAT before IRQ2 recognition.
    # The accepted interrupt entry must snapshot those validity states; the
    # vector-resident RTI must restore them after the known interrupt mask is
    # installed. A PM client is rejected while restored MSTAT is invalid.
    # After fetched Type 7 makes only MSTAT known, a fetched ASTAT-to-AR move
    # leaves the PM store source invalid and exposes the restored ASTAT state.
    reset_pm_operands()
    writable = register_code_by_name(writable=True)
    interrupt_status_sequence = (
        _type7(writable["ICNTL"], 0x10),
        _type7(writable["IMASK"], 0xF),
        _type17(writable["ASTAT"], int(DREG.AX1)),
        _type17(writable["MSTAT"], int(DREG.AX1)),
        0,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x0E20, interrupt_status_sequence[0]),
    )
    for next_opcode in interrupt_status_sequence[1:]:
        emit(
            phase_override=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            irq_n=0xF,
        )
        bus_cycle(
            pmd=next_opcode,
            automatic_pm_flow=True,
            irq_n=0xF,
        )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    bus_cycle(
        pmd=_type6(int(DREG.AX0), 0xDEAD),
        automatic_pm_flow=True,
        irq_n=0xB,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    bus_cycle(
        pmd=_type20(interrupt_return=True),
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    bus_cycle(
        pmd=_type7(writable["MSTAT"], 0),
        automatic_pm_flow=True,
        irq_n=0xF,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True,
        type13_opcode=0x118000,
        type13_next=0x0E26,
    )
    coverage["interrupt_rti_mstat_validity_restore"] += 1
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
    )
    bus_cycle(
        pmd=_type17(int(DREG.AR), writable["ASTAT"]),
        automatic_pm_flow=True,
    )
    emit(
        phase_override=LogicalPhase.STATE_8,
        automatic_pm_flow=True,
    )
    bus_cycle(pmd=0, pmd_valid=False, automatic_pm_flow=True)
    emit(
        phase_override=LogicalPhase.STATE_8,
        type5_execute=True,
        type5_opcode=0x580000 | (int(DREG.AR) << 4),
        type5_next=0x0E27,
    )
    coverage["interrupt_rti_astat_validity_restore"] += 1

    # Seed the shared cache through an external Type 13 miss, then execute a
    # fetched Type 13 whose PC+1 lookup hits that word and retires at the data
    # completion without a recovery fetch.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        emit(
            phase_override=LogicalPhase.STATE_8,
            dag=DAGRegisterSetup(kind, 4, value),
        )
    emit(phase_override=LogicalPhase.STATE_8, px=ExactWord(8, 0x5A))
    emit(
        phase_override=LogicalPhase.STATE_8,
        type13_execute=True,
        type13_opcode=0x110010,
        type13_next=0x0B01,
    )
    bus_cycle(pmd=0x111122)
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0x400000 | (0x1357 << 4) | int(DREG.SI))
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x0B00, 0x110010),
    )
    emit(phase_override=LogicalPhase.STATE_8, automatic_pm_flow=True)
    bus_cycle(pmd=0xCAFE66, automatic_pm_flow=True)
    emit(phase_override=LogicalPhase.STATE_8, automatic_pm_flow=True)
    bus_cycle(pmd=0, automatic_pm_flow=True)

    # A fetched DO establishes an active loop before returning a legal Type
    # 5 word.  The sequential-only automatic PM boundary must report and
    # reject that context instead of recomputing loop termination after a
    # possible miss recovery.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x0C00, 0x140000 | (0x0C05 << 4)),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0x500000)
    emit(phase_override=LogicalPhase.STATE_8, automatic_pm_flow=True)

    # Ordinary-fetch HALT recognizes in state 3, lets the current fetch
    # complete, holds driven state-8 PM outputs, qualifies release with
    # DMACK, and issues the installed NOP's following fetch on resume.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x1200, 0),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    bus_cycle(pmd=0, halt_n=False)
    emit(phase_override=LogicalPhase.STATE_8, halt_n=False)
    emit(
        phase_override=LogicalPhase.STATE_8,
        halt_n=True,
        dmack=False,
    )
    emit(phase_override=LogicalPhase.STATE_8, halt_n=True, dmack=True)

    # A state-3 HALT during a fetched Type 5 or Type 13 PM-data action must
    # invalidate an issue-time hit, commit the data action once, force one
    # external recovery for the same client, and stop only after recovery.
    for use_type5, current_pc, next_opcode in (
        (True, 0x1300, 0x400000 | (0x55AA << 4) | int(DREG.SI)),
        (False, 0x1400, 0x400000 | (0xAA55 << 4) | int(DREG.SI)),
    ):
        reset_pm_operands()
        if use_type5:
            emit(
                phase_override=LogicalPhase.STATE_8,
                type13_execute=True,
                type13_opcode=0x110010,
                type13_next=current_pc + 1,
            )
        else:
            emit(
                phase_override=LogicalPhase.STATE_8,
                type5_execute=True,
                type5_opcode=0x500010,
                type5_next=current_pc + 1,
            )
        bus_cycle(pmd=0x111122)
        emit(phase_override=LogicalPhase.STATE_8)
        bus_cycle(pmd=next_opcode)
        emit(
            phase_override=LogicalPhase.STATE_8,
            instruction_setup=(
                current_pc,
                0x500010 if use_type5 else 0x110010,
            ),
        )
        emit(
            phase_override=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
        )
        bus_cycle(
            pmd=0xBEEF77,
            automatic_pm_flow=True,
            halt_n=False,
        )
        emit(
            phase_override=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            halt_n=False,
        )
        bus_cycle(
            pmd=next_opcode,
            automatic_pm_flow=True,
            halt_n=False,
        )
        emit(
            phase_override=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            halt_n=False,
        )
        emit(
            phase_override=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            halt_n=True,
        )

    # No original-device source closes a BR/HALT priority.  A simultaneous
    # initial assertion is therefore rejected and reported without either
    # controller recognizing the request.
    emit(reset=True, phase_override=LogicalPhase.STATE_8)
    emit(
        phase_override=LogicalPhase.STATE_8,
        instruction_setup=(0x1500, 0),
    )
    emit(phase_override=LogicalPhase.STATE_8)
    emit(phase_override=LogicalPhase.STATE_1)
    emit(phase_override=LogicalPhase.STATE_2)
    br_n = False
    emit(phase_override=LogicalPhase.STATE_3, halt_n=False)
    br_n = True

    phase = LogicalPhase.STATE_8
    for index in range(random_count):
        mode = state.interface.control.mode
        if mode is BusControlMode.IDLE:
            if phase is LogicalPhase.STATE_1 and rng.randrange(96) == 0:
                br_n = False
        elif mode is BusControlMode.REQUEST_DELAY:
            br_n = False
        elif mode is BusControlMode.GRANTED:
            if phase is LogicalPhase.STATE_1 and rng.randrange(3) == 0:
                br_n = True
        else:
            br_n = True

        controls: dict[str, object] = {}
        advance = rng.randrange(13) != 0
        enabled_eight = (
            phase is LogicalPhase.STATE_8
            and advance
            and mode in (BusControlMode.IDLE, BusControlMode.REACQUIRE)
        )
        type5_held = state.type5.pending is not None or state.type5.recovery is not None
        type13_held = state.type13.pending is not None or state.type13.recovery is not None
        linear_idle = not state.linear.instruction_valid and not state.linear.pending
        if enabled_eight and not type5_held and not type13_held:
            choice = rng.randrange(32)
            if index % 4096 == 0:
                controls.update(
                    type5_execute=True, type5_opcode=_type5(rng),
                    type5_next=rng.randrange(1 << 14),
                    type13_execute=True, type13_opcode=_type13(rng),
                    type13_next=rng.randrange(1 << 14),
                )
            elif linear_idle and choice < 3:
                controls["instruction_setup"] = (
                    rng.randrange(1 << 14), 0
                )
            elif linear_idle and choice < 13:
                controls.update(
                    type5_execute=True,
                    type5_opcode=_type5(rng),
                    type5_next=rng.randrange(1 << 14),
                    type5_next_valid=rng.randrange(19) != 0,
                )
            elif linear_idle and choice < 23:
                controls.update(
                    type13_execute=True,
                    type13_opcode=_type13(rng),
                    type13_next=rng.randrange(1 << 14),
                    type13_next_valid=rng.randrange(19) != 0,
                )
            elif choice == 23:
                controls["dreg"] = DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                )
            elif choice == 24:
                controls["dag"] = DAGRegisterSetup(
                    DAGRegisterKind(rng.randrange(3)),
                    rng.randrange(8), rng.randrange(1 << 14),
                )
            elif choice == 25:
                controls["px"] = ExactWord(8, rng.randrange(256))
            elif choice == 26:
                controls["mstat"] = ExactWord(4, rng.randrange(16))
        if index % 8191 == 0 and index != 0:
            controls = {"reset": True}

        random_pmd = rng.randrange(1 << 24)
        if (
            state.interface.owner_bus.owner is ProgramBusOwner.FETCH
            and state.interface.owner_bus.bus.active
            and phase is LogicalPhase.STATE_7
            and advance
        ):
            # Linear instruction semantics have their own exhaustive/random
            # differential. Keep this ownership/cache composition focused by
            # terminating a random ordinary stream with a known unsupported
            # word after its real external fetch and shared-cache fill.
            random_pmd = 0xFFFFFF
        emit(
            advance=advance,
            pmd=random_pmd,
            pmd_valid=rng.randrange(17) != 0,
            irq_n=0xF,
            pm_probe_dreg=rng.randrange(16),
            pm_probe_dag=rng.randrange(8),
            **controls,
        )

    emit(reset=True, phase_override=LogicalPhase.STATE_5)
    return lines, coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed", type=lambda value: int(value, 0), default=0x2100C113
    )
    args = parser.parse_args()
    lines, coverage = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    missing = [
        name for name, count in coverage.items()
        if count == 0 and name != "halt_attachment_conflict"
    ]
    if missing:
        raise SystemExit(f"missing coverage: {', '.join(missing)}")
    if coverage["halt_attachment_conflict"] != 0:
        raise SystemExit(
            "unexpected HALT attachment conflict: "
            f"{coverage['halt_attachment_conflict']}"
        )
    print(
        f"PASS generated {len(lines)} three-client/shared-cache clocks "
        f"seed={args.seed:#x} "
        + " ".join(f"{key}={value}" for key, value in coverage.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
