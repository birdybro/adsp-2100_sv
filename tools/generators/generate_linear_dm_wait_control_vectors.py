#!/usr/bin/env python3
"""Generate deterministic ordinary-fetch/native-DM wait vectors."""

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
    DataBusRequest,
    ExactWord,
    HaltControlMode,
    LinearDMWaitControlState,
    LogicalPhase,
    UNKNOWN,
    apply_linear_dm_wait_control_cycle,
)
from sim.reference_models.adsp2100_model.internal_move import (  # noqa: E402
    register_code_by_name,
)


LEGAL_SHIFTER_XOPS = (0, 2, 3, 4, 5, 6, 7)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _type6(destination: int, data: int) -> int:
    return 0x400000 | ((data & 0xFFFF) << 4) | destination


def _type7(code: int, data: int) -> int:
    return (
        0x300000
        | ((code >> 4) << 18)
        | ((data & 0x3FFF) << 4)
        | (code & 0xF)
    )


def _type2(*, immediate: int, dag: int, i_local: int, m_local: int) -> int:
    return (
        0xA00000
        | ((dag & 1) << 20)
        | ((immediate & 0xFFFF) << 4)
        | ((i_local & 3) << 2)
        | (m_local & 3)
    )


def _type3(*, write: bool, address: int, register_code: int) -> int:
    return (
        0x800000
        | (int(write) << 20)
        | ((register_code >> 4) << 18)
        | ((address & 0x3FFF) << 4)
        | (register_code & 0xF)
    )


def _type4(
    *,
    dag: int = 0,
    write: bool = False,
    z: int = 0,
    amf: int = 0,
    yop: int = 0,
    xop: int = 0,
    dreg: int = 0,
    i: int = 0,
    m: int = 0,
) -> int:
    return (
        0x600000
        | ((dag & 1) << 20)
        | (int(write) << 19)
        | ((z & 1) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 3) << 11)
        | ((xop & 7) << 8)
        | ((dreg & 0xF) << 4)
        | ((i & 3) << 2)
        | (m & 3)
    )


def _type12(
    *,
    dag: int = 0,
    write: bool = False,
    sf: int = 0,
    xop: int = 0,
    dreg: int = 0,
    i: int = 0,
    m: int = 0,
) -> int:
    return (
        0x120000
        | ((dag & 1) << 16)
        | (int(write) << 15)
        | ((sf & 0xF) << 11)
        | ((xop & 7) << 8)
        | ((dreg & 0xF) << 4)
        | ((i & 3) << 2)
        | (m & 3)
    )


def _random_opcode(rng: random.Random) -> int:
    choice = rng.randrange(5)
    if choice == 0:
        return 0
    if choice == 1:
        return _type6(rng.randrange(16), rng.randrange(1 << 16))
    if choice == 2:
        return (
            0x0F0000
            | (rng.randrange(8) << 11)
            | (rng.choice(LEGAL_SHIFTER_XOPS) << 8)
            | rng.randrange(256)
        )
    if choice == 3:
        return (
            0x0E0000
            | (rng.randrange(16) << 11)
            | (rng.choice(LEGAL_SHIFTER_XOPS) << 8)
            | rng.randrange(16)
        )
    return 0


def _exact(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return (True, value.value)
    return (False, 0)


def generate_lines(
    clock_count: int,
    seed: int,
) -> tuple[list[str], dict[str, int]]:
    rng = random.Random(seed)
    state = LinearDMWaitControlState.reset()
    phase = LogicalPhase.STATE_8
    lines: list[str] = []
    type2_selectors_seen: set[int] = set()
    type2_immediates_seen: set[int] = set()
    type3_read_selectors_seen: set[int] = set()
    type3_write_selectors_seen: set[int] = set()
    type3_addresses_seen: set[int] = set()
    type4_compute_tuples_seen: set[int] = set()
    type4_selectors_seen: set[int] = set()
    type4_dregs_seen: set[int] = set()
    type4_directions_seen: set[int] = set()
    type12_shifter_tuples_seen: set[int] = set()
    type12_selectors_seen: set[int] = set()
    type12_dregs_seen: set[int] = set()
    type12_directions_seen: set[int] = set()
    coverage = {
        "dm_companion_accept": 0,
        "atomic_preflight_collision": 0,
        "wait_extension": 0,
        "interrupt_wait_sample": 0,
        "irq_pending_during_wait": 0,
        "irq_recognition_after_wait": 0,
        "aligned_completion": 0,
        "held_architectural_clock": 0,
        "dm_read": 0,
        "dm_write": 0,
        "fetched_type2_accept": 0,
        "fetched_type2_wait": 0,
        "fetched_type2_completion": 0,
        "fetched_type2_postmodify_observed": 0,
        "fetched_type2_selectors": 0,
        "fetched_type2_immediate_boundaries": 0,
        "fetched_type2_bit_reverse": 0,
        "fetched_type2_circular_wrap": 0,
        "fetched_type3_accept": 0,
        "fetched_type3_read": 0,
        "fetched_type3_write": 0,
        "fetched_type3_wait": 0,
        "fetched_type3_completion": 0,
        "fetched_type3_read_selectors": 0,
        "fetched_type3_write_selectors": 0,
        "fetched_type3_address_boundaries": 0,
        "fetched_type3_readback_observed": 0,
        "fetched_type3_provisional_extension": 0,
        "fetched_type3_reserved_destination": 0,
        "fetched_type4_accept": 0,
        "fetched_type4_read": 0,
        "fetched_type4_write": 0,
        "fetched_type4_wait": 0,
        "fetched_type4_completion": 0,
        "fetched_type4_compute_tuples": 0,
        "fetched_type4_selectors": 0,
        "fetched_type4_dregs": 0,
        "fetched_type4_directions": 0,
        "fetched_type4_old_store_overlap": 0,
        "fetched_type4_readback": 0,
        "fetched_type4_memory_only": 0,
        "fetched_type4_alternate_mac": 0,
        "fetched_type4_bit_reverse": 0,
        "fetched_type4_circular_wrap": 0,
        "fetched_type4_reserved_collision": 0,
        "fetched_type12_accept": 0,
        "fetched_type12_read": 0,
        "fetched_type12_write": 0,
        "fetched_type12_wait": 0,
        "fetched_type12_completion": 0,
        "fetched_type12_shifter_tuples": 0,
        "fetched_type12_selectors": 0,
        "fetched_type12_dregs": 0,
        "fetched_type12_directions": 0,
        "fetched_type12_old_store_overlap": 0,
        "fetched_type12_readback": 0,
        "fetched_type12_alternate_bank": 0,
        "fetched_type12_bit_reverse": 0,
        "fetched_type12_circular_wrap": 0,
        "fetched_type12_reserved_collision": 0,
        "fetched_type12_unavailable_xop": 0,
        "bus_request_recognized": 0,
        "bus_request_during_dm_wait": 0,
        "dm_completion_before_grant": 0,
        "bus_grant": 0,
        "bus_dual_mask": 0,
        "bus_release_recognized": 0,
        "bus_grant_release": 0,
        "bus_resume": 0,
        "halt_recognized_during_dm_wait": 0,
        "halt_stop_deferred": 0,
        "halt_stop_on_dm_completion": 0,
        "halt_state8_hold": 0,
        "halt_release_blocked": 0,
        "halt_resume": 0,
        "halt_br_collision": 0,
        "halt_owner_preserved_on_br": 0,
        "bus_owner_preserved_on_halt": 0,
    }

    def emit(
        *,
        reset: bool = False,
        advance: bool = True,
        br_n: bool = True,
        halt_n: bool = True,
        irq_n: int = 0xF,
        setup: tuple[int, int] | None = None,
        dm_request: DataBusRequest | None = None,
        dm_ack: bool = True,
        dmd: int = 0,
        dmd_valid: bool = True,
        pmd: int = 0,
        pmd_valid: bool = True,
        probe: int = 0,
    ):
        nonlocal state, phase
        setup_value = (
            None
            if setup is None
            else (ExactWord(14, setup[0]), ExactWord(24, setup[1]))
        )
        result = apply_linear_dm_wait_control_cycle(
            state,
            reset=reset,
            phase=phase,
            phase_advance=advance,
            br_n=br_n,
            halt_n=halt_n,
            irq_n=irq_n,
            instruction_setup=setup_value,
            dm_request=dm_request,
            dm_ack=dm_ack,
            dmd_read_data=(
                ExactWord(16, dmd) if dmd_valid else UNKNOWN
            ),
            pmd_read_data=(
                ExactWord(24, pmd) if pmd_valid else UNKNOWN
            ),
        )

        coverage["dm_companion_accept"] += int(
            result.dm_companion_accepted
        )
        coverage["atomic_preflight_collision"] += int(
            result.dm_owner_bus.request_conflict
            and not result.core.bus.request_accepted
            and not result.dm_bus.request_accepted
        )
        coverage["wait_extension"] += int(
            result.dm_bus.wait_extension_event
        )
        coverage["interrupt_wait_sample"] += int(
            result.interrupt_wait_sample
        )
        coverage["irq_pending_during_wait"] += int(
            result.interrupt_wait_sample
            and result.state.core.interrupt.edge_pending != 0
        )
        coverage["irq_recognition_after_wait"] += int(
            result.core.interrupt_recognition_event
            and result.dm_bus.completion_event
        )
        coverage["aligned_completion"] += int(
            result.dm_bus.completion_event
            and result.core.bus.completion_event
            and result.core.retire_event
        )
        coverage["held_architectural_clock"] += int(
            advance and not result.architectural_phase_advance
        )
        coverage["bus_request_recognized"] += int(
            result.control.request_recognized
        )
        coverage["bus_request_during_dm_wait"] += int(
            result.control.request_recognized and result.dm_bus.waiting
        )
        coverage["dm_completion_before_grant"] += int(
            result.dm_bus.completion_event
            and state.control.mode is BusControlMode.REQUEST_DELAY
            and not result.control.grant_assert_event
        )
        coverage["bus_grant"] += int(result.control.grant_assert_event)
        coverage["bus_dual_mask"] += int(
            result.native_bus_relinquished
            and not result.core.bus.address_output_enable
            and not result.core.bus.control_output_enable
            and not result.core.bus.data_output_enable
            and not result.dm_bus.address_output_enable
            and not result.dm_bus.control_output_enable
            and not result.dm_bus.data_output_enable
        )
        coverage["bus_release_recognized"] += int(
            result.control.release_recognized
        )
        coverage["bus_grant_release"] += int(
            result.control.grant_release_event
        )
        coverage["bus_resume"] += int(result.control.resume_event)
        coverage["halt_recognized_during_dm_wait"] += int(
            result.halt.halt_recognized and result.dm_bus.waiting
        )
        coverage["halt_stop_deferred"] += int(
            state.halt.mode is HaltControlMode.STOP_PENDING
            and phase is LogicalPhase.STATE_7
            and result.dm_bus.waiting
            and not result.halt.halt_stop_event
        )
        coverage["halt_stop_on_dm_completion"] += int(
            result.halt.halt_stop_event
            and result.dm_bus.completion_event
            and result.core.retire_event
        )
        coverage["halt_state8_hold"] += int(
            result.halt.halted
            and result.halt.phase_hold
            and not result.effective_phase_advance
        )
        coverage["halt_release_blocked"] += int(
            result.halt.release_blocked
        )
        coverage["halt_resume"] += int(result.halt.resume_event)
        coverage["halt_br_collision"] += int(result.halt_br_conflict)
        current_instruction = (
            state.core.instruction.value
            if isinstance(state.core.instruction, ExactWord)
            else None
        )
        current_type2 = bool(
            current_instruction is not None
            and current_instruction & 0xE00000 == 0xA00000
        )
        current_type3 = bool(
            current_instruction is not None
            and current_instruction & 0xE00000 == 0x800000
        )
        current_type3_write = bool(
            current_type3 and current_instruction is not None
            and current_instruction & 0x100000
        )
        current_type4 = bool(
            current_instruction is not None
            and current_instruction & 0xE00000 == 0x600000
        )
        current_type4_write = bool(
            current_type4 and current_instruction is not None
            and current_instruction & 0x080000
        )
        current_type12 = bool(
            current_instruction is not None
            and current_instruction & 0xFE0000 == 0x120000
        )
        current_type12_write = bool(
            current_type12 and current_instruction is not None
            and current_instruction & 0x008000
        )
        fetched_type3_accept = bool(
            current_type3 and result.fetched_dm_accepted
        )
        coverage["dm_read"] += int(
            result.dm_bus.request_accepted
            and (
                (fetched_type3_accept and not current_type3_write)
                or (
                    current_type4 and result.fetched_dm_accepted
                    and not current_type4_write
                )
                or (
                    current_type12 and result.fetched_dm_accepted
                    and not current_type12_write
                )
                or (
                    not result.fetched_dm_accepted
                    and dm_request is not None
                    and not dm_request.write
                )
            )
        )
        coverage["dm_write"] += int(
            result.dm_bus.request_accepted
            and (
                (current_type2 and result.fetched_dm_accepted)
                or (fetched_type3_accept and current_type3_write)
                or (
                    current_type4 and result.fetched_dm_accepted
                    and current_type4_write
                )
                or (
                    current_type12 and result.fetched_dm_accepted
                    and current_type12_write
                )
                or (
                    not result.fetched_dm_accepted
                    and dm_request is not None
                    and dm_request.write
                )
            )
        )
        coverage["fetched_type2_accept"] += int(
            current_type2 and result.fetched_dm_accepted
        )
        if current_type2 and result.fetched_dm_accepted:
            assert isinstance(state.core.instruction, ExactWord)
            type2_opcode = state.core.instruction.value
            selector = (
                (((type2_opcode >> 20) & 1) << 4)
                | (((type2_opcode >> 2) & 3) << 2)
                | (type2_opcode & 3)
            )
            type2_selectors_seen.add(selector)
            type2_immediates_seen.add((type2_opcode >> 4) & 0xFFFF)
            coverage["fetched_type2_selectors"] = len(
                type2_selectors_seen
            )
            coverage["fetched_type2_immediate_boundaries"] = len(
                type2_immediates_seen.intersection(
                    {0x0000, 0x0001, 0x8000, 0xFFFF}
                )
            )
        coverage["fetched_type2_wait"] += int(
            current_type2 and result.dm_bus.wait_extension_event
        )
        coverage["fetched_type2_completion"] += int(
            current_type2
            and result.dm_bus.completion_event
            and result.core.retire_event
        )
        coverage["fetched_type3_accept"] += int(fetched_type3_accept)
        coverage["fetched_type3_read"] += int(
            fetched_type3_accept and not current_type3_write
        )
        coverage["fetched_type3_write"] += int(
            fetched_type3_accept and current_type3_write
        )
        if fetched_type3_accept:
            assert current_instruction is not None
            register_code = (
                (((current_instruction >> 18) & 3) << 4)
                | (current_instruction & 0xF)
            )
            address = (current_instruction >> 4) & 0x3FFF
            if current_type3_write:
                type3_write_selectors_seen.add(register_code)
            else:
                type3_read_selectors_seen.add(register_code)
            type3_addresses_seen.add(address)
            coverage["fetched_type3_read_selectors"] = len(
                type3_read_selectors_seen
            )
            coverage["fetched_type3_write_selectors"] = len(
                type3_write_selectors_seen
            )
            coverage["fetched_type3_address_boundaries"] = len(
                type3_addresses_seen.intersection({0x0000, 0x0001, 0x3FFF})
            )
        coverage["fetched_type3_wait"] += int(
            current_type3 and result.dm_bus.wait_extension_event
        )
        coverage["fetched_type3_completion"] += int(
            current_type3
            and result.dm_bus.completion_event
            and result.core.retire_event
        )
        coverage["fetched_type3_provisional_extension"] += int(
            current_type3 and result.core.provisional_source_extension
        )
        coverage["fetched_type3_reserved_destination"] += int(
            current_type3 and result.core.reserved_subencoding
        )
        fetched_type4_accept = bool(
            current_type4 and result.fetched_dm_accepted
        )
        coverage["fetched_type4_accept"] += int(fetched_type4_accept)
        coverage["fetched_type4_read"] += int(
            fetched_type4_accept and not current_type4_write
        )
        coverage["fetched_type4_write"] += int(
            fetched_type4_accept and current_type4_write
        )
        if fetched_type4_accept:
            assert current_instruction is not None
            z = (current_instruction >> 18) & 1
            amf = (current_instruction >> 13) & 0x1F
            yop = (current_instruction >> 11) & 3
            xop = (current_instruction >> 8) & 7
            dag = (current_instruction >> 20) & 1
            i_local = (current_instruction >> 2) & 3
            m_local = current_instruction & 3
            dreg = (current_instruction >> 4) & 0xF
            type4_compute_tuples_seen.add(
                (z << 10) | (amf << 5) | (yop << 3) | xop
            )
            type4_selectors_seen.add(
                (dag << 4) | (i_local << 2) | m_local
            )
            type4_dregs_seen.add(dreg)
            type4_directions_seen.add(int(current_type4_write))
            coverage["fetched_type4_compute_tuples"] = len(
                type4_compute_tuples_seen
            )
            coverage["fetched_type4_selectors"] = len(
                type4_selectors_seen
            )
            coverage["fetched_type4_dregs"] = len(type4_dregs_seen)
            coverage["fetched_type4_directions"] = len(
                type4_directions_seen
            )
        coverage["fetched_type4_wait"] += int(
            current_type4 and result.dm_bus.wait_extension_event
        )
        coverage["fetched_type4_completion"] += int(
            current_type4
            and result.dm_bus.completion_event
            and result.core.retire_event
        )
        coverage["fetched_type4_reserved_collision"] += int(
            current_type4 and result.core.reserved_subencoding
        )
        fetched_type12_accept = bool(
            current_type12 and result.fetched_dm_accepted
        )
        coverage["fetched_type12_accept"] += int(fetched_type12_accept)
        coverage["fetched_type12_read"] += int(
            fetched_type12_accept and not current_type12_write
        )
        coverage["fetched_type12_write"] += int(
            fetched_type12_accept and current_type12_write
        )
        if fetched_type12_accept:
            assert current_instruction is not None
            sf = (current_instruction >> 11) & 0xF
            xop = (current_instruction >> 8) & 7
            dag = (current_instruction >> 16) & 1
            i_local = (current_instruction >> 2) & 3
            m_local = current_instruction & 3
            dreg = (current_instruction >> 4) & 0xF
            type12_shifter_tuples_seen.add((sf << 3) | xop)
            type12_selectors_seen.add(
                (dag << 4) | (i_local << 2) | m_local
            )
            type12_dregs_seen.add(dreg)
            type12_directions_seen.add(int(current_type12_write))
            coverage["fetched_type12_shifter_tuples"] = len(
                type12_shifter_tuples_seen
            )
            coverage["fetched_type12_selectors"] = len(
                type12_selectors_seen
            )
            coverage["fetched_type12_dregs"] = len(type12_dregs_seen)
            coverage["fetched_type12_directions"] = len(
                type12_directions_seen
            )
        coverage["fetched_type12_wait"] += int(
            current_type12 and result.dm_bus.wait_extension_event
        )
        coverage["fetched_type12_completion"] += int(
            current_type12
            and result.dm_bus.completion_event
            and result.core.retire_event
        )
        if current_type12 and result.core.reserved_subencoding:
            if current_instruction is not None and (
                (current_instruction >> 8) & 7
            ) == 1:
                coverage["fetched_type12_unavailable_xop"] += 1
            else:
                coverage["fetched_type12_reserved_collision"] += 1

        stimulus = 0
        for value, width in (
            (reset, 1),
            (int(phase), 3),
            (advance, 1),
            (br_n, 1),
            (halt_n, 1),
            (irq_n, 4),
            (setup is not None, 1),
            (0 if setup is None else setup[0], 14),
            (0 if setup is None else setup[1], 24),
            (dm_request is not None, 1),
            (
                0
                if dm_request is None
                or not isinstance(dm_request.address, ExactWord)
                else dm_request.address.value,
                14,
            ),
            (
                dm_request is not None
                and isinstance(dm_request.address, ExactWord),
                1,
            ),
            (False if dm_request is None else dm_request.write, 1),
            (
                0
                if dm_request is None
                or not isinstance(dm_request.write_data, ExactWord)
                else dm_request.write_data.value,
                16,
            ),
            (
                dm_request is not None
                and isinstance(dm_request.write_data, ExactWord),
                1,
            ),
            (dm_ack, 1),
            (dmd, 16),
            (dmd_valid, 1),
            (pmd, 24),
            (pmd_valid, 1),
            (probe, 6),
        ):
            stimulus = _append(stimulus, value, width)

        pm = result.core.bus
        dm = result.dm_bus
        expected_pre = 0
        for value, width in (
            (result.architectural_phase_advance, 1),
            (result.effective_phase_advance, 1),
            (result.interrupt_wait_sample, 1),
            (result.dm_companion_accepted, 1),
            (result.phase_conflict, 1),
            (result.attachment_conflict, 1),
            (result.integration_conflict, 1),
            (int(state.halt.mode), 2),
            (result.halt.state_three_boundary, 1),
            (result.halt.halt_recognized, 1),
            (result.halt.halt_stop_event, 1),
            (result.halt.resume_event, 1),
            (result.halt.release_blocked, 1),
            (result.halt.instruction_issue_inhibit, 1),
            (result.halt.phase_hold, 1),
            (result.halt.halted, 1),
            (result.halt_br_conflict, 1),
            (result.halt.phase_conflict, 1),
            (int(state.control.mode), 3),
            (result.control.state_three_boundary, 1),
            (result.control.request_recognized, 1),
            (result.control.grant_assert_event, 1),
            (result.control.release_recognized, 1),
            (result.control.grant_release_event, 1),
            (result.control.resume_event, 1),
            (result.control.request_withdrawn, 1),
            (result.control.release_cancelled, 1),
            (result.control.instruction_issue_inhibit, 1),
            (result.control.bus_relinquished, 1),
            (result.control.bg_n, 1),
            (result.control.reset_br_request, 1),
            (result.native_bg_n, 1),
            (result.native_bus_relinquished, 1),
            (result.core.issue_boundary, 1),
            (result.core.instruction_setup_accepted, 1),
            (result.core.instruction_issue, 1),
            (result.core.retire_event, 1),
            (result.core.interrupt_recognition_event, 1),
            (result.core.interrupt_entry_event, 1),
            (result.core.interrupt_vector_issue_event, 1),
            (result.core.interrupt_vector_fetch_event, 1),
            (result.core.interrupt_level, 2),
            (result.core.interrupt_vector.value, 14),
            (state.core.interrupt.edge_pending, 4),
            (state.core.interrupt_vectoring, 1),
            (result.core.interrupt_configuration_invalid, 1),
            (result.core.interrupt_reset_baseline_provisional, 1),
            (state.core.instruction_valid, 1),
            (state.core.pending, 1),
            (result.core.phase_conflict, 1),
            (result.core.integration_conflict, 1),
            (result.core.internal_conflict, 1),
            (result.core.unsupported_instruction, 1),
            (result.core.reserved_subencoding, 1),
            (result.core.provisional_source_extension, 1),
            (result.core.interrupt_adjacent_control_conflict, 1),
            (
                0
                if reset and not lines
                else state.core.architecture.pc.value,
                14,
            ),
            (
                state.core.instruction.value
                if isinstance(state.core.instruction, ExactWord)
                else 0,
                24,
            ),
            (pm.request_accepted, 1),
            (pm.completion_event, 1),
            (pm.read_sample_event, 1),
            (state.core.bus.active, 1),
            (pm.address_output_enable, 1),
            (pm.control_output_enable, 1),
            (pm.data_output_enable, 1),
            (pm.address_known, 1),
            (pm.address, 14),
            (pm.pmda, 1),
            (pm.control_output_enable, 1),
            (pm.pms_n, 1),
            (pm.pmrd_n, 1),
            (pm.pmwr_n, 1),
            (dm.request_accepted, 1),
            (dm.dmack_sample_event, 1),
            (dm.dmack_accepted, 1),
            (dm.wait_extension_event, 1),
            (dm.completion_event, 1),
            (dm.read_sample_event, 1),
            (state.dm_bus.active, 1),
            (dm.waiting, 1),
            (state.dm_bus.response_valid, 1),
            (state.dm_bus.response_write, 1),
            (isinstance(state.dm_bus.read_data, ExactWord), 1),
            (
                state.dm_bus.read_data.value
                if isinstance(state.dm_bus.read_data, ExactWord)
                else 0,
                16,
            ),
            (dm.address_output_enable, 1),
            (dm.control_output_enable, 1),
            (dm.data_output_enable, 1),
            (dm.address_known, 1),
            (dm.address, 14),
            (dm.dms_n, 1),
            (dm.dmrd_n, 1),
            (dm.dmwr_n, 1),
            (dm.write_data_known, 1),
            (dm.write_data, 16),
        ):
            expected_pre = _append(expected_pre, value, width)

        next_core = result.state.core
        next_dm = result.state.dm_bus
        _, icntl = _exact(next_core.architecture.icntl)
        next_instruction = (
            next_core.instruction.value
            if isinstance(next_core.instruction, ExactWord)
            else 0
        )
        expected_post = 0
        for value, width in (
            (next_core.instruction_valid, 1),
            (next_core.pending, 1),
            (next_core.architecture.pc.value, 14),
            (next_instruction, 24),
            (next_core.interrupt.edge_pending, 4),
            (next_core.interrupt_vectoring, 1),
            (next_core.interrupt_level or 0, 2),
            (next_core.bus.active, 1),
            (next_dm.active, 1),
            (
                next_dm.active
                and not next_dm.response_valid
                and next_dm.waiting,
                1,
            ),
            (next_dm.response_valid, 1),
            (next_dm.response_write, 1),
            (isinstance(next_dm.read_data, ExactWord), 1),
            (
                next_dm.read_data.value
                if isinstance(next_dm.read_data, ExactWord)
                else 0,
                16,
            ),
            (icntl, 5),
            (next_core.architecture.imask.value, 4),
            (next_core.architecture.sstat.value, 8),
            (int(result.state.control.mode), 3),
            (int(result.state.halt.mode), 2),
        ):
            expected_post = _append(expected_post, value, width)

        lines.append(
            f"{stimulus:034x} {expected_pre:052x} "
            f"{expected_post:023x}"
        )
        state = result.state
        if result.effective_phase_advance:
            phase = LogicalPhase((int(phase) + 1) & 0x7)
        return result

    def advance_to(target: LogicalPhase) -> None:
        while phase is not target:
            emit()

    def retire_with(opcode: int) -> None:
        nonlocal phase
        if phase is not LogicalPhase.STATE_8:
            raise AssertionError("retirement helper requires state 8")
        emit()
        advance_to(LogicalPhase.STATE_7)
        emit(pmd=opcode)

    def retire_type2_with_wait(opcode: int) -> None:
        if phase is not LogicalPhase.STATE_8:
            raise AssertionError("Type 2 helper requires state 8")
        issue = emit()
        if not issue.fetched_dm_accepted:
            raise AssertionError("fetched Type 2 DM request was not accepted")
        advance_to(LogicalPhase.STATE_6)
        emit(dm_ack=False)
        emit()
        advance_to(LogicalPhase.STATE_6)
        emit(dm_ack=True)
        completed = emit(pmd=opcode)
        if not (
            completed.dm_bus.completion_event
            and completed.core.retire_event
        ):
            raise AssertionError("fetched Type 2 did not retire with DM")

    def retire_type2(opcode: int) -> None:
        if phase is not LogicalPhase.STATE_8:
            raise AssertionError("Type 2 helper requires state 8")
        issue = emit()
        if not issue.fetched_dm_accepted:
            raise AssertionError("fetched Type 2 DM request was not accepted")
        advance_to(LogicalPhase.STATE_6)
        emit(dm_ack=True)
        completed = emit(pmd=opcode)
        if not (
            completed.dm_bus.completion_event
            and completed.core.retire_event
        ):
            raise AssertionError("fetched Type 2 did not retire with DM")

    def retire_type3(
        opcode: int,
        *,
        dmd: int = 0,
        wait: bool = False,
    ):
        if phase is not LogicalPhase.STATE_8:
            raise AssertionError("Type 3 helper requires state 8")
        issue = emit()
        if not issue.fetched_dm_accepted:
            raise AssertionError("fetched Type 3 DM request was not accepted")
        advance_to(LogicalPhase.STATE_6)
        if wait:
            emit(dm_ack=False)
            emit()
            advance_to(LogicalPhase.STATE_6)
        emit(dm_ack=True)
        completed = emit(dmd=dmd, pmd=opcode)
        if not (
            completed.dm_bus.completion_event
            and completed.core.retire_event
        ):
            raise AssertionError("fetched Type 3 did not retire with DM")
        return issue

    def retire_type4(
        opcode: int,
        *,
        dmd: int = 0,
        wait: bool = False,
    ):
        if phase is not LogicalPhase.STATE_8:
            raise AssertionError("Type 4 helper requires state 8")
        issue = emit()
        if not issue.fetched_dm_accepted:
            raise AssertionError("fetched Type 4 DM request was not accepted")
        advance_to(LogicalPhase.STATE_6)
        if wait:
            emit(dm_ack=False)
            emit()
            advance_to(LogicalPhase.STATE_6)
        emit(dm_ack=True)
        completed = emit(dmd=dmd, pmd=opcode)
        if not (
            completed.dm_bus.completion_event
            and completed.core.retire_event
        ):
            raise AssertionError("fetched Type 4 did not retire with DM")
        return issue

    def retire_type12(
        opcode: int,
        *,
        dmd: int = 0,
        wait: bool = False,
    ):
        if phase is not LogicalPhase.STATE_8:
            raise AssertionError("Type 12 helper requires state 8")
        issue = emit()
        if not issue.fetched_dm_accepted:
            raise AssertionError("fetched Type 12 DM request was not accepted")
        advance_to(LogicalPhase.STATE_6)
        if wait:
            emit(dm_ack=False)
            emit()
            advance_to(LogicalPhase.STATE_6)
        emit(dm_ack=True)
        completed = emit(dmd=dmd, pmd=opcode)
        if not (
            completed.dm_bus.completion_event
            and completed.core.retire_event
        ):
            raise AssertionError("fetched Type 12 did not retire with DM")
        return issue

    # Directed original-device IRQ/DMACK interaction. ICNTL and IMASK select
    # edge-sensitive IRQ2, then a paired NOP/DM read receives one full-cycle
    # wait. The edge occurs only at the first repeated physical state 7.
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)
    emit(setup=(0x0100, _type7(0x34, 0x04)))
    advance_to(LogicalPhase.STATE_8)
    retire_with(_type7(0x33, 0x04))
    retire_with(0)
    emit(dm_request=DataBusRequest.read(0x0555))
    advance_to(LogicalPhase.STATE_6)
    emit(dm_ack=False)
    emit(irq_n=0xB)
    advance_to(LogicalPhase.STATE_6)
    emit(dm_ack=True)
    emit(
        irq_n=0xF,
        dmd=0x1357,
        pmd=0,
    )
    emit()
    advance_to(LogicalPhase.STATE_7)
    emit(pmd=0)

    # Directed fetched Type 2 ownership. The first write sees old I0=0x0120,
    # waits one full physical phase cycle, and postmodifies I0 by M0=3 only at
    # paired PM/DM completion. The following Type 2 write must therefore drive
    # DMA=0x0123, independently proving the retirement-only DAG update in RTL.
    first_type2 = _type2(
        immediate=0xBEEF,
        dag=0,
        i_local=0,
        m_local=0,
    )
    second_type2 = _type2(
        immediate=0xCAFE,
        dag=0,
        i_local=0,
        m_local=0,
    )
    retire_with(_type7(0x10, 0x0120))
    retire_with(_type7(0x14, 0x0003))
    retire_with(_type7(0x18, 0x0000))
    retire_with(first_type2)
    blocked_collision = emit(
        dm_request=DataBusRequest.write_word(0x0111, 0x2222)
    )
    if not (
        blocked_collision.dm_owner_bus.request_conflict
        and blocked_collision.attachment_conflict
        and not blocked_collision.core.bus.request_accepted
        and not blocked_collision.dm_bus.request_accepted
        and blocked_collision.state.core.instruction_valid
        and not blocked_collision.state.core.pending
    ):
        raise AssertionError("PM/DM preflight collision did not fail closed")
    advance_to(LogicalPhase.STATE_8)
    retire_type2_with_wait(second_type2)
    second_issue = emit()
    if not (
        second_issue.fetched_dm_accepted
        and isinstance(second_issue.state.dm_bus.address, ExactWord)
        and second_issue.state.dm_bus.address.value == 0x0123
    ):
        raise AssertionError("Type 2 postmodify was not observed on DMA")
    coverage["fetched_type2_postmodify_observed"] += 1
    advance_to(LogicalPhase.STATE_6)
    emit(dm_ack=True)
    emit(pmd=0)

    # Traverse all 32 G/I/M selector combinations. Every first Type 2 uses a
    # boundary immediate and a noncircular postmodify; the second transaction
    # must drive the resulting I value, proving each selected M and I writeback
    # path rather than only the class decoder.
    immediate_boundaries = (0x0000, 0x0001, 0x8000, 0xFFFF)
    selector_index = 0
    for dag in range(2):
        for i_local in range(4):
            for m_local in range(4):
                base = 0x0400 + selector_index * 0x10
                modify = m_local + 1
                first = _type2(
                    immediate=immediate_boundaries[selector_index & 3],
                    dag=dag,
                    i_local=i_local,
                    m_local=m_local,
                )
                second = _type2(
                    immediate=0x5A00 | selector_index,
                    dag=dag,
                    i_local=i_local,
                    m_local=m_local,
                )
                register_base = 0x10 if dag == 0 else 0x20
                retire_with(_type7(register_base + i_local, base))
                retire_with(_type7(register_base + 4 + m_local, modify))
                retire_with(_type7(register_base + 8 + i_local, 0))
                retire_with(first)
                retire_type2(second)
                observed = emit()
                if not (
                    observed.fetched_dm_accepted
                    and isinstance(observed.state.dm_bus.address, ExactWord)
                    and observed.state.dm_bus.address.value
                    == ((base + modify) & 0x3FFF)
                ):
                    raise AssertionError(
                        "Type 2 selector postmodify was not observed on DMA"
                    )
                advance_to(LogicalPhase.STATE_6)
                emit(dm_ack=True)
                emit(pmd=0)
                selector_index += 1

    if len(type2_selectors_seen) != 32:
        raise AssertionError("not every fetched Type 2 selector was covered")
    if not set(immediate_boundaries).issubset(type2_immediates_seen):
        raise AssertionError("Type 2 immediate boundaries were not covered")

    # Exercise the two non-linear DAG address paths through the fetched owner:
    # DAG1 bit reversal changes only the external old-I address, while an
    # original circular buffer wraps the retirement-time I postmodify.
    retire_with(_type7(0x31, 0x0002))
    retire_with(_type7(0x10, 0x0001))
    retire_with(_type7(0x14, 0x0001))
    retire_with(_type7(0x18, 0x0000))
    retire_with(first_type2)
    retire_type2(second_type2)
    bit_reversed = emit()
    if not (
        bit_reversed.fetched_dm_accepted
        and isinstance(bit_reversed.state.dm_bus.address, ExactWord)
        and bit_reversed.state.dm_bus.address.value == 0x1000
    ):
        raise AssertionError("fetched Type 2 bit reversal was not observed")
    coverage["fetched_type2_bit_reverse"] += 1
    advance_to(LogicalPhase.STATE_6)
    emit(dm_ack=True)
    emit(pmd=0)

    # Traverse every legal original Type 3 direct-DM source and destination.
    # Stores observe a value initialized through the existing fetched owner.
    # Each load is followed by a store of the same register, so the RTL bus
    # descriptor independently exposes narrowing, sign fill, bank selection,
    # and completion-only destination visibility without a private probe.
    readable_codes = sorted(register_code_by_name(writable=False).values())
    writable_codes = sorted(register_code_by_name(writable=True).values())
    retire_with(_type7(0x31, 0x0000))
    address_boundaries = (0x0000, 0x0001, 0x3FFF)
    for selector_index, register_code in enumerate(readable_codes):
        if register_code < 0x10:
            initializer = _type6(
                register_code,
                0x4100 | register_code,
            )
            retire_with(initializer)
        elif register_code != 0x32:
            initializer = _type7(
                register_code,
                0x0100 | register_code,
            )
            retire_with(initializer)
        store = _type3(
            write=True,
            address=address_boundaries[selector_index % 3],
            register_code=register_code,
        )
        retire_with(store)
        retire_type3(0, wait=selector_index == 0)

    for selector_index, register_code in enumerate(writable_codes):
        payload = 0x8000 | ((selector_index + 1) * 0x101)
        if register_code == 0x31:
            # Keep the primary computational bank selected so the following
            # source observation remains in the initialized bank.
            payload = 0x000E
        load = _type3(
            write=False,
            address=address_boundaries[selector_index % 3],
            register_code=register_code,
        )
        store = _type3(
            write=True,
            address=(0x0200 + selector_index) & 0x3FFF,
            register_code=register_code,
        )
        retire_with(load)
        retire_type3(store, dmd=payload, wait=selector_index == 0)
        observed = retire_type3(0)
        if not (
            observed.fetched_dm_accepted
            and observed.state.dm_bus.write
            and isinstance(observed.state.dm_bus.write_data, ExactWord)
        ):
            raise AssertionError("Type 3 readback store was not observable")
        coverage["fetched_type3_readback_observed"] += 1

    if type3_write_selectors_seen != set(readable_codes):
        raise AssertionError("not every legal Type 3 write selector was covered")
    if type3_read_selectors_seen != set(writable_codes):
        raise AssertionError("not every legal Type 3 read selector was covered")
    if not set(address_boundaries).issubset(type3_addresses_seen):
        raise AssertionError("Type 3 direct-address boundaries were not covered")

    retire_with(_type7(0x31, 0x0000))
    retire_with(_type7(0x10, 0x1003))
    retire_with(_type7(0x14, 0x0001))
    retire_with(_type7(0x18, 0x0004))
    retire_with(first_type2)
    retire_type2(second_type2)
    wrapped = emit()
    if not (
        wrapped.fetched_dm_accepted
        and isinstance(wrapped.state.dm_bus.address, ExactWord)
        and wrapped.state.dm_bus.address.value == 0x1000
    ):
        raise AssertionError("fetched Type 2 circular wrap was not observed")
    coverage["fetched_type2_circular_wrap"] += 1
    advance_to(LogicalPhase.STATE_6)
    emit(dm_ack=True)
    emit(pmd=0)

    # Preserve the existing Type 3 reserved-destination evidence before the
    # larger Type 4 sequence, then reset into a fully initialized compute/DAG
    # state. The reset is architectural; all later Type 4 operands are loaded
    # explicitly rather than receiving convenience values.
    invalid_type3 = _type3(
        write=False,
        address=0x0100,
        register_code=0x32,
    )
    retire_with(_type7(0x34, 0x0000))
    retire_with(invalid_type3)
    invalid = emit()
    if not (
        invalid.core.reserved_subencoding
        and not invalid.core.instruction_issue
        and not invalid.fetched_dm_accepted
    ):
        raise AssertionError(
            "Type 3 read-only SSTAT destination did not fail closed"
        )
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)

    emit(setup=(0x1200, _type6(0, 2)))
    advance_to(LogicalPhase.STATE_8)
    for dreg in range(1, 16):
        retire_with(_type6(dreg, 0x0100 + dreg))
    retire_with(_type6(4, 3))
    retire_with(_type6(2, 2))
    retire_with(_type6(6, 3))
    retire_with(_type7(0x30, 0))
    retire_with(_type7(0x31, 0))
    for dag in range(2):
        register_base = 0x10 if dag == 0 else 0x20
        for local in range(4):
            retire_with(_type7(register_base + local, 0x0200 + local))
            retire_with(_type7(register_base + 4 + local, local + 1))
            retire_with(_type7(register_base + 8 + local, 0))

    # Establish known AF and MF feedback before the exhaustive fetched field
    # traversal. Both are produced by real Type 4 computations.
    alu_to_af = _type4(
        write=True,
        z=1,
        amf=0x13,
        dreg=10,
    )
    mac_to_mf = _type4(
        write=True,
        z=1,
        amf=4,
        dreg=2,
    )
    retire_with(alu_to_af)
    retire_type4(mac_to_mf)
    retire_type4(0)

    # The manual's old-value overlap: DM observes old AR=0x7777 while the
    # acknowledged ALU result replaces AR with 2+3. A following Type 3 store
    # independently exposes the new value through the physical DM descriptor.
    for opcode in (
        _type6(0, 2),
        _type6(4, 3),
        _type6(10, 0x7777),
        _type7(0x10, 0x0120),
        _type7(0x14, 1),
        _type7(0x18, 0),
        0x6A60A0,
    ):
        retire_with(opcode)
    old_store = retire_type4(
        _type3(write=True, address=0x0300, register_code=0x0A),
        wait=True,
    )
    if not (
        old_store.state.dm_bus.write
        and isinstance(old_store.state.dm_bus.write_data, ExactWord)
        and old_store.state.dm_bus.write_data.value == 0x7777
    ):
        raise AssertionError("Type 4 did not capture old AR store data")
    new_ar = retire_type3(0)
    if not (
        isinstance(new_ar.state.dm_bus.write_data, ExactWord)
        and new_ar.state.dm_bus.write_data.value == 5
    ):
        raise AssertionError("Type 4 ALU result was not visible after retirement")
    coverage["fetched_type4_old_store_overlap"] += 1

    # A read computes from old AX0/AY0, then loads AX0 only at completion. The
    # two following Type 3 stores independently expose AR=5 and AX0=0xCAFE.
    for opcode in (
        _type6(0, 2),
        _type6(4, 3),
        _type7(0x10, 0x0080),
        _type7(0x17, 0x3FFF),
        _type7(0x18, 0),
        0x626003,
    ):
        retire_with(opcode)
    retire_type4(
        _type3(write=True, address=0x0310, register_code=0x0A),
        dmd=0xCAFE,
    )
    read_ar = retire_type3(
        _type3(write=True, address=0x0311, register_code=0x00)
    )
    read_ax0 = retire_type3(0)
    if not (
        isinstance(read_ar.state.dm_bus.write_data, ExactWord)
        and read_ar.state.dm_bus.write_data.value == 5
        and isinstance(read_ax0.state.dm_bus.write_data, ExactWord)
        and read_ax0.state.dm_bus.write_data.value == 0xCAFE
    ):
        raise AssertionError("Type 4 compute/read results were not atomic")
    coverage["fetched_type4_readback"] += 1

    # AMF zero remains a memory-only action. DAG1 bit reversal affects the old
    # external address while the normal-order I value postmodifies once.
    for opcode in (
        _type7(0x31, 2),
        _type7(0x12, 1),
        _type7(0x15, 1),
        _type7(0x1A, 0),
    ):
        retire_with(opcode)
    memory_only = _type4(z=1, yop=3, xop=7, dreg=8, i=2, m=1)
    retire_with(memory_only)
    first_memory = retire_type4(memory_only, dmd=0x1357)
    second_memory = retire_type4(0, dmd=0x2468)
    if not (
        isinstance(first_memory.state.dm_bus.address, ExactWord)
        and first_memory.state.dm_bus.address.value == 0x2000
        and isinstance(second_memory.state.dm_bus.address, ExactWord)
        and second_memory.state.dm_bus.address.value == 0x1000
    ):
        raise AssertionError("Type 4 DAG1 bit reversal/postmodify was not observed")
    coverage["fetched_type4_memory_only"] += 1
    coverage["fetched_type4_bit_reverse"] += 1

    # Original circular postmodify wraps I0 from 0x1003 to 0x1000. The next
    # Type 4 descriptor exposes the wrapped I without adding another observer.
    for opcode in (
        _type7(0x31, 0),
        _type7(0x10, 0x1003),
        _type7(0x14, 1),
        _type7(0x18, 4),
    ):
        retire_with(opcode)
    circular = _type4(write=True, dreg=0, i=0, m=0)
    retire_with(circular)
    retire_type4(circular)
    circular_second = retire_type4(0)
    if not (
        isinstance(circular_second.state.dm_bus.address, ExactWord)
        and circular_second.state.dm_bus.address.value == 0x1000
    ):
        raise AssertionError("Type 4 circular postmodify was not observed")
    coverage["fetched_type4_circular_wrap"] += 1

    # Alternate-bank MAC result and old selected-bank store source.
    for opcode in (
        _type7(0x31, 1),
        _type6(2, 2),
        _type6(6, 3),
        _type7(0x20, 0x0200),
        _type7(0x24, 2),
        _type7(0x28, 0),
        _type4(dag=1, write=True, amf=4, dreg=2),
    ):
        retire_with(opcode)
    retire_type4(
        _type3(write=True, address=0x0320, register_code=0x0B)
    )
    alternate_mr0 = retire_type3(0)
    if not (
        isinstance(alternate_mr0.state.dm_bus.write_data, ExactWord)
        and alternate_mr0.state.dm_bus.write_data.value == 12
    ):
        raise AssertionError("Type 4 alternate-bank MAC result was not observed")
    coverage["fetched_type4_alternate_mac"] += 1

    # Restore and fully initialize the primary bank, then traverse every
    # (Z, AMF, YOP, XOP) tuple while rotating all Type 4 DAG, I/M, DREG, and
    # direction fields. Read collisions are converted to writes, the sourced
    # legal counterpart, so every issued packet remains within the closed set.
    retire_with(_type7(0x31, 0))
    for dreg in range(16):
        retire_with(_type6(dreg, 0x1000 + dreg))
    retire_with(_type7(0x30, 0))
    type4_words: list[int] = []
    tuple_index = 0
    for z in range(2):
        for amf in range(32):
            for yop in range(4):
                for xop in range(8):
                    dreg = tuple_index & 0xF
                    write = bool(tuple_index & 1)
                    collision = bool(
                        not write
                        and not z
                        and amf != 0
                        and (
                            (amf >= 0x10 and dreg == 10)
                            or (amf < 0x10 and 11 <= dreg <= 13)
                        )
                    )
                    if collision:
                        write = True
                    selector = tuple_index & 0x1F
                    type4_words.append(
                        _type4(
                            dag=(selector >> 4) & 1,
                            write=write,
                            z=z,
                            amf=amf,
                            yop=yop,
                            xop=xop,
                            dreg=dreg,
                            i=(selector >> 2) & 3,
                            m=selector & 3,
                        )
                    )
                    tuple_index += 1
    retire_with(type4_words[0])
    for index, opcode in enumerate(type4_words[1:], start=1):
        retire_type4(opcode, dmd=(0x4000 + index) & 0xFFFF)
    retire_type4(0, dmd=0x7E57)
    if len(type4_compute_tuples_seen) != 2048:
        raise AssertionError("not every fetched Type 4 compute tuple was covered")
    if len(type4_selectors_seen) != 32:
        raise AssertionError("not every fetched Type 4 DAG/I/M selector was covered")
    if len(type4_dregs_seen) != 16 or len(type4_directions_seen) != 2:
        raise AssertionError("Type 4 DREG/direction coverage is incomplete")

    collision = _type4(amf=0x13, dreg=10)
    retire_with(collision)
    invalid_type4 = emit()
    if not (
        invalid_type4.core.reserved_subencoding
        and not invalid_type4.core.instruction_issue
        and not invalid_type4.fetched_dm_accepted
    ):
        raise AssertionError("Type 4 read collision did not fail closed")
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)

    # Fetched Type 12 retains the standalone shifter-plus-DM ordering: a
    # waited store drives the old DREG while the shifter result, optional
    # read, and selected-I update remain invisible until paired completion.
    emit(setup=(0x1600, _type6(8, 0x1234)))
    advance_to(LogicalPhase.STATE_8)
    for opcode in (
        _type6(9, 0),
        _type6(14, 0x5678),
        _type6(15, 0x9ABC),
        _type7(0x30, 0),
        _type7(0x31, 0),
        _type7(0x10, 0x0100),
        _type7(0x14, 1),
        _type7(0x18, 0),
        _type12(write=True, dreg=14),
    ):
        retire_with(opcode)
    old_type12_store = retire_type12(
        _type3(write=True, address=0x0340, register_code=0x0F),
        wait=True,
    )
    if not (
        old_type12_store.state.dm_bus.write
        and isinstance(old_type12_store.state.dm_bus.write_data, ExactWord)
        and old_type12_store.state.dm_bus.write_data.value == 0x5678
    ):
        raise AssertionError("Type 12 did not capture old SR0 store data")
    shifted_sr1 = retire_type3(_type12(dreg=0))
    if not (
        isinstance(shifted_sr1.state.dm_bus.write_data, ExactWord)
        and shifted_sr1.state.dm_bus.write_data.value == 0x1234
    ):
        raise AssertionError("Type 12 shifter result was not atomic")
    coverage["fetched_type12_old_store_overlap"] += 1

    retire_type12(
        _type3(write=True, address=0x0341, register_code=0x00),
        dmd=0xBEEF,
    )
    loaded_ax0 = retire_type3(0)
    if not (
        isinstance(loaded_ax0.state.dm_bus.write_data, ExactWord)
        and loaded_ax0.state.dm_bus.write_data.value == 0xBEEF
    ):
        raise AssertionError("Type 12 DM read was not visible after retirement")
    coverage["fetched_type12_readback"] += 1

    # DAG1 bit reversal changes the external old-I address, while postmodify
    # remains in normal I-register order and becomes visible to the following
    # Type 12 descriptor.
    for opcode in (
        _type7(0x31, 2),
        _type7(0x12, 1),
        _type7(0x15, 1),
        _type7(0x1A, 0),
        _type12(write=True, dreg=8, i=2, m=1),
    ):
        retire_with(opcode)
    first_type12_reverse = retire_type12(
        _type12(write=True, dreg=8, i=2, m=1)
    )
    second_type12_reverse = retire_type12(0)
    if not (
        isinstance(first_type12_reverse.state.dm_bus.address, ExactWord)
        and first_type12_reverse.state.dm_bus.address.value == 0x2000
        and isinstance(second_type12_reverse.state.dm_bus.address, ExactWord)
        and second_type12_reverse.state.dm_bus.address.value == 0x1000
    ):
        raise AssertionError("Type 12 DAG1 bit reversal was not observed")
    coverage["fetched_type12_bit_reverse"] += 1

    # Original circular postmodify wraps I0 from 0x1003 to 0x1000.
    for opcode in (
        _type7(0x31, 0),
        _type7(0x10, 0x1003),
        _type7(0x14, 1),
        _type7(0x18, 4),
        _type12(write=True, dreg=8),
    ):
        retire_with(opcode)
    retire_type12(_type12(write=True, dreg=8))
    type12_circular_second = retire_type12(0)
    if not (
        isinstance(type12_circular_second.state.dm_bus.address, ExactWord)
        and type12_circular_second.state.dm_bus.address.value == 0x1000
    ):
        raise AssertionError("Type 12 circular postmodify was not observed")
    coverage["fetched_type12_circular_wrap"] += 1

    # Selected-bank shifter operands and store data both come from the
    # alternate bank when MSTAT bank select is set.
    for opcode in (
        _type7(0x31, 1),
        _type6(8, 0x4321),
        _type6(9, 0),
        _type7(0x20, 0x0200),
        _type7(0x24, 1),
        _type7(0x28, 0),
        _type12(dag=1, write=True, dreg=8),
    ):
        retire_with(opcode)
    alternate_type12 = retire_type12(
        _type3(write=True, address=0x0342, register_code=0x0F)
    )
    if not (
        isinstance(alternate_type12.state.dm_bus.write_data, ExactWord)
        and alternate_type12.state.dm_bus.write_data.value == 0x4321
    ):
        raise AssertionError("Type 12 alternate-bank store was not observed")
    alternate_sr1 = retire_type3(0)
    if not (
        isinstance(alternate_sr1.state.dm_bus.write_data, ExactWord)
        and alternate_sr1.state.dm_bus.write_data.value == 0x4321
    ):
        raise AssertionError("Type 12 alternate-bank shift was not observed")
    coverage["fetched_type12_alternate_bank"] += 1

    # Cover every sourced (SF, XOP) action while rotating all DAG/I/M, DREG,
    # and direction fields. Read collisions are changed to their legal write
    # counterparts; an explicit collision below separately proves fail-close.
    retire_with(_type7(0x31, 0))
    for dreg in range(16):
        retire_with(_type6(dreg, 0x2000 + dreg))
    retire_with(_type7(0x30, 0))
    for dag in range(2):
        register_base = 0x10 if dag == 0 else 0x20
        for local in range(4):
            retire_with(_type7(register_base + local, 0x0800 + local))
            retire_with(_type7(register_base + 4 + local, local + 1))
            retire_with(_type7(register_base + 8 + local, 0))
    type12_words: list[int] = []
    action_index = 0
    for sf in range(16):
        for xop in LEGAL_SHIFTER_XOPS:
            dreg = action_index & 0xF
            write = bool(action_index & 1)
            collision = bool(
                not write
                and (
                    (sf <= 0xB and dreg in (14, 15))
                    or (0xC <= sf <= 0xE and dreg == 9)
                )
            )
            if collision:
                write = True
            selector = action_index & 0x1F
            type12_words.append(
                _type12(
                    dag=(selector >> 4) & 1,
                    write=write,
                    sf=sf,
                    xop=xop,
                    dreg=dreg,
                    i=(selector >> 2) & 3,
                    m=selector & 3,
                )
            )
            action_index += 1
    retire_with(type12_words[0])
    for index, opcode in enumerate(type12_words[1:], start=1):
        retire_type12(opcode, dmd=(0x6000 + index) & 0xFFFF)
    retire_type12(0, dmd=0x12D0)
    if len(type12_shifter_tuples_seen) != 112:
        raise AssertionError("not every fetched Type 12 shifter tuple was covered")
    if len(type12_selectors_seen) != 32:
        raise AssertionError("not every fetched Type 12 DAG/I/M selector was covered")
    if len(type12_dregs_seen) != 16 or len(type12_directions_seen) != 2:
        raise AssertionError("Type 12 DREG/direction coverage is incomplete")

    type12_collision = _type12(dreg=14)
    retire_with(type12_collision)
    invalid_type12 = emit()
    if not (
        invalid_type12.core.reserved_subencoding
        and not invalid_type12.core.instruction_issue
        and not invalid_type12.fetched_dm_accepted
    ):
        raise AssertionError("Type 12 read collision did not fail closed")
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)
    emit(setup=(0x1700, _type12(xop=1, write=True)))
    advance_to(LogicalPhase.STATE_8)
    unavailable_type12 = emit()
    if not (
        unavailable_type12.core.reserved_subencoding
        and not unavailable_type12.core.instruction_issue
        and not unavailable_type12.fetched_dm_accepted
    ):
        raise AssertionError("Type 12 unavailable XOP did not fail closed")
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)

    # Normal BR/BG with a real fetched Type 2 DM owner. BR is recognized
    # before the low DMACK sample; the repeated physical state 3 cannot grant,
    # current PM/DM completion occurs first, then grant masks both buses. The
    # complete release/reacquire sequence proves state-8 restart as well.
    emit(setup=(0x1800, _type7(0x10, 0x0200)))
    advance_to(LogicalPhase.STATE_8)
    retire_with(_type7(0x14, 1))
    retire_with(_type2(immediate=0xA55A, dag=0, i_local=0, m_local=0))
    br_issue = emit()
    if not br_issue.fetched_dm_accepted:
        raise AssertionError("BR/DM Type 2 request was not accepted")
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=True)
    br_recognized = emit(br_n=False)
    if not br_recognized.control.request_recognized:
        raise AssertionError("BR was not recognized during fetched DM")
    while phase is not LogicalPhase.STATE_6:
        emit(br_n=False)
    emit(br_n=False, dm_ack=False)
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=False)
    br_deferred = emit(br_n=False)
    if br_deferred.control.grant_assert_event:
        raise AssertionError("BR grant escaped an active DM wait")
    while phase is not LogicalPhase.STATE_6:
        emit(br_n=False)
    emit(br_n=False, dm_ack=True)
    br_completed = emit(br_n=False, pmd=0)
    if not (
        br_completed.dm_bus.completion_event
        and br_completed.core.retire_event
        and not br_completed.control.grant_assert_event
    ):
        raise AssertionError("BR service preceded paired PM/DM completion")
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=False)
    br_grant = emit(br_n=False)
    if not br_grant.control.grant_assert_event:
        raise AssertionError("BR did not grant after DM completion")
    br_visible = emit(br_n=False)
    if not br_visible.native_bus_relinquished:
        raise AssertionError("BR grant did not reach the native boundary")
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=True)
    br_release = emit(br_n=True)
    if not br_release.control.release_recognized:
        raise AssertionError("BR release was not recognized")
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=True)
    br_reacquire = emit(br_n=True)
    if not br_reacquire.control.grant_release_event:
        raise AssertionError("BG did not release after the sourced delay")
    while phase is not LogicalPhase.STATE_8:
        emit(br_n=True)
    br_resume = emit(br_n=True)
    if not br_resume.control.resume_event:
        raise AssertionError("BR/BG owner did not resume at state 8")

    # HALT first sampled at a repeated physical state 3 remains pending across
    # another low-DMACK state-7 boundary. The first acknowledged paired PM/DM
    # completion then retires the fetched Type 2 and enters the driven state-8
    # stop; release remains blocked until DMACK is high.
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)
    emit(setup=(0x1880, _type7(0x10, 0x0240)))
    advance_to(LogicalPhase.STATE_8)
    retire_with(_type7(0x14, 1))
    retire_with(
        _type2(immediate=0xA55A, dag=0, i_local=0, m_local=0)
    )
    halt_issue = emit()
    if not halt_issue.fetched_dm_accepted:
        raise AssertionError("HALT/DM Type 2 request was not accepted")
    advance_to(LogicalPhase.STATE_6)
    emit(dm_ack=False)
    advance_to(LogicalPhase.STATE_3)
    halt_recognized = emit(halt_n=False)
    if not (
        halt_recognized.halt.halt_recognized
        and halt_recognized.dm_bus.waiting
    ):
        raise AssertionError("HALT was not recognized during the DM wait")
    advance_to(LogicalPhase.STATE_6)
    emit(halt_n=False, dm_ack=False)
    halt_deferred = emit(halt_n=False)
    if halt_deferred.halt.halt_stop_event:
        raise AssertionError("HALT stopped before the DM wait completed")
    advance_to(LogicalPhase.STATE_6)
    emit(halt_n=False, dm_ack=True)
    halt_stopped = emit(halt_n=False, pmd=0)
    if not (
        halt_stopped.halt.halt_stop_event
        and halt_stopped.dm_bus.completion_event
        and halt_stopped.core.retire_event
    ):
        raise AssertionError("HALT did not stop on paired DM completion")
    held_halt = emit(halt_n=False)
    if not (
        held_halt.halt.halted
        and held_halt.halt.phase_hold
        and not held_halt.effective_phase_advance
    ):
        raise AssertionError("HALT did not retain the state-8 boundary")
    blocked_halt_release = emit(halt_n=True, dm_ack=False)
    if not blocked_halt_release.halt.release_blocked:
        raise AssertionError("HALT release ignored the DMACK requirement")
    resumed_halt = emit(halt_n=True, dm_ack=True)
    if not resumed_halt.halt.resume_event:
        raise AssertionError("HALT did not resume with DMACK high")

    # Same-boundary BR/HALT has no sourced priority and therefore admits
    # neither controller while reporting the fail-closed conflict.
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)
    emit(setup=(0x18C0, 0))
    advance_to(LogicalPhase.STATE_8)
    emit()
    advance_to(LogicalPhase.STATE_3)
    halt_br_overlap = emit(br_n=False, halt_n=False)
    if not (
        halt_br_overlap.halt_br_conflict
        and not halt_br_overlap.halt.halt_recognized
        and not halt_br_overlap.control.request_recognized
    ):
        raise AssertionError("BR/HALT overlap did not fail closed")

    # A cross-request cannot release or replace an already active owner. This
    # is the fail-closed implementation rule; it is not an architectural
    # priority claim.
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)
    emit(setup=(0x18D0, 0))
    advance_to(LogicalPhase.STATE_8)
    emit()
    advance_to(LogicalPhase.STATE_3)
    active_halt = emit(halt_n=False)
    if not active_halt.halt.halt_recognized:
        raise AssertionError("HALT owner setup did not recognize")
    advance_to(LogicalPhase.STATE_7)
    stopped_halt = emit(halt_n=False, pmd=0)
    if not stopped_halt.halt.halt_stop_event:
        raise AssertionError("HALT owner setup did not stop")
    halt_cross_request = emit(br_n=False, halt_n=False)
    if not (
        halt_cross_request.halt_br_conflict
        and halt_cross_request.halt.halted
        and not halt_cross_request.halt.resume_event
        and halt_cross_request.control.state.mode is BusControlMode.IDLE
    ):
        raise AssertionError("BR cross-request replaced the HALT owner")
    coverage["halt_owner_preserved_on_br"] += 1
    emit(br_n=True, halt_n=True)

    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)
    emit(setup=(0x18E0, 0))
    advance_to(LogicalPhase.STATE_8)
    emit()
    advance_to(LogicalPhase.STATE_3)
    active_bus = emit(br_n=False)
    if not active_bus.control.request_recognized:
        raise AssertionError("BR owner setup did not recognize")
    advance_to(LogicalPhase.STATE_3)
    bus_cross_request = emit(br_n=False, halt_n=False)
    if not (
        bus_cross_request.halt_br_conflict
        and bus_cross_request.control.grant_assert_event
        and not bus_cross_request.control.request_withdrawn
        and bus_cross_request.control.state.mode is BusControlMode.GRANTED
        and bus_cross_request.halt.state.mode is HaltControlMode.RUNNING
    ):
        raise AssertionError("HALT cross-request replaced the BR owner")
    coverage["bus_owner_preserved_on_halt"] += 1
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)

    # A request first presented at the repeated physical state 3 is retained
    # even though the incomplete DM cycle still inhibits grant service.
    emit(reset=True)
    advance_to(LogicalPhase.STATE_8)
    emit(
        setup=(
            0x1900,
            _type2(immediate=0x5AA5, dag=0, i_local=0, m_local=0),
        )
    )
    advance_to(LogicalPhase.STATE_8)
    emit()
    while phase is not LogicalPhase.STATE_6:
        emit(br_n=True)
    emit(br_n=True, dm_ack=False)
    while phase is not LogicalPhase.STATE_3:
        emit(br_n=True)
    wait_br = emit(br_n=False)
    if not (
        wait_br.dm_bus.waiting
        and wait_br.control.request_recognized
        and not wait_br.control.grant_assert_event
    ):
        raise AssertionError("BR was not retained during the DM wait")
    emit(reset=True, br_n=True)
    advance_to(LogicalPhase.STATE_8)

    br_n = True
    while len(lines) < clock_count:
        advance = rng.randrange(20) != 0
        setup = None
        dm_request = None
        if (
            phase is LogicalPhase.STATE_8
            and not state.core.instruction_valid
            and not state.core.pending
            and not state.core.interrupt_vectoring
        ):
            setup = (rng.randrange(1 << 14), _random_opcode(rng))
        elif (
            phase is LogicalPhase.STATE_8
            and state.core.instruction_valid
            and not state.core.pending
            and not state.core.interrupt_vectoring
            and rng.randrange(4) == 0
        ):
            if rng.randrange(2):
                dm_request = DataBusRequest.read(rng.randrange(1 << 14))
            else:
                dm_request = DataBusRequest.write_word(
                    rng.randrange(1 << 14),
                    rng.randrange(1 << 16),
                )
        dm_ack = True
        if (
            phase is LogicalPhase.STATE_6
            and state.dm_bus.active
            and not state.dm_bus.response_valid
        ):
            dm_ack = rng.randrange(4) != 0
        if state.control.mode is BusControlMode.IDLE:
            if rng.randrange(384) == 0:
                br_n = False
            elif not br_n and rng.randrange(16) == 0:
                br_n = True
        elif state.control.mode is BusControlMode.REQUEST_DELAY:
            br_n = rng.randrange(64) == 0
        elif state.control.mode is BusControlMode.GRANTED:
            if rng.randrange(128) == 0:
                br_n = True
            else:
                br_n = False
        else:
            br_n = True
        emit(
            advance=advance,
            br_n=br_n,
            setup=setup,
            dm_request=dm_request,
            dm_ack=dm_ack,
            dmd=rng.randrange(1 << 16),
            pmd=_random_opcode(rng),
            probe=rng.randrange(64),
        )

    required = (
        "dm_companion_accept",
        "atomic_preflight_collision",
        "wait_extension",
        "interrupt_wait_sample",
        "irq_pending_during_wait",
        "irq_recognition_after_wait",
        "aligned_completion",
        "held_architectural_clock",
        "dm_read",
        "dm_write",
        "fetched_type2_accept",
        "fetched_type2_wait",
        "fetched_type2_completion",
        "fetched_type2_postmodify_observed",
        "fetched_type2_selectors",
        "fetched_type2_immediate_boundaries",
        "fetched_type2_bit_reverse",
        "fetched_type2_circular_wrap",
        "fetched_type3_accept",
        "fetched_type3_read",
        "fetched_type3_write",
        "fetched_type3_wait",
        "fetched_type3_completion",
        "fetched_type3_read_selectors",
        "fetched_type3_write_selectors",
        "fetched_type3_address_boundaries",
        "fetched_type3_readback_observed",
        "fetched_type3_provisional_extension",
        "fetched_type3_reserved_destination",
        "fetched_type4_accept",
        "fetched_type4_read",
        "fetched_type4_write",
        "fetched_type4_wait",
        "fetched_type4_completion",
        "fetched_type4_compute_tuples",
        "fetched_type4_selectors",
        "fetched_type4_dregs",
        "fetched_type4_directions",
        "fetched_type4_old_store_overlap",
        "fetched_type4_readback",
        "fetched_type4_memory_only",
        "fetched_type4_alternate_mac",
        "fetched_type4_bit_reverse",
        "fetched_type4_circular_wrap",
        "fetched_type4_reserved_collision",
        "fetched_type12_accept",
        "fetched_type12_read",
        "fetched_type12_write",
        "fetched_type12_wait",
        "fetched_type12_completion",
        "fetched_type12_shifter_tuples",
        "fetched_type12_selectors",
        "fetched_type12_dregs",
        "fetched_type12_directions",
        "fetched_type12_old_store_overlap",
        "fetched_type12_readback",
        "fetched_type12_alternate_bank",
        "fetched_type12_bit_reverse",
        "fetched_type12_circular_wrap",
        "fetched_type12_reserved_collision",
        "fetched_type12_unavailable_xop",
        "bus_request_recognized",
        "bus_request_during_dm_wait",
        "dm_completion_before_grant",
        "bus_grant",
        "bus_dual_mask",
        "bus_release_recognized",
        "bus_grant_release",
        "bus_resume",
        "halt_recognized_during_dm_wait",
        "halt_stop_deferred",
        "halt_stop_on_dm_completion",
        "halt_state8_hold",
        "halt_release_blocked",
        "halt_resume",
        "halt_br_collision",
        "halt_owner_preserved_on_br",
        "bus_owner_preserved_on_halt",
    )
    missing = [name for name in required if coverage[name] == 0]
    if missing:
        raise RuntimeError(f"missing required coverage: {', '.join(missing)}")
    return (lines[:clock_count], coverage)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clocks", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=0x2100_D025)
    args = parser.parse_args()
    lines, coverage = generate_lines(args.clocks, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"generated {len(lines)} linear/native-DM clocks; "
        + ", ".join(f"{name}={count}" for name, count in coverage.items())
    )


if __name__ == "__main__":
    main()
