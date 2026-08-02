from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
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


ROOT = Path(__file__).resolve().parents[1]


def _type5(*, write: bool = False, dreg: DREG = DREG.AX0) -> int:
    return 0x500000 | (int(write) << 19) | (int(dreg) << 4)


def _type13(*, write: bool = False, dreg: DREG = DREG.AX0) -> int:
    return 0x110000 | (int(write) << 15) | (int(dreg) << 4)


def _type6(dreg: DREG, value: int) -> int:
    return 0x400000 | ((value & 0xFFFF) << 4) | int(dreg)


def _type7(code: int, value: int) -> int:
    return (
        0x300000
        | ((code >> 4) << 18)
        | ((value & 0x3FFF) << 4)
        | (code & 0xF)
    )


def _type17(destination: int, source: int) -> int:
    return (
        0x0D0000
        | ((destination >> 4) << 10)
        | ((source >> 4) << 8)
        | ((destination & 0xF) << 4)
        | (source & 0xF)
    )


def _type20(*, interrupt_return: bool, condition: int = 0xF) -> int:
    return (
        0x0A0000
        | (int(interrupt_return) << 4)
        | (condition & 0xF)
    )


def _type8(
    *,
    destination_feedback: bool = False,
    amf: int = 0x13,
    yop: int = 0,
    xop: int = 0,
    move_destination: DREG = DREG.AX1,
    move_source: DREG = DREG.AX0,
) -> int:
    return (
        0x280000
        | (int(destination_feedback) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 0x3) << 11)
        | ((xop & 0x7) << 8)
        | (int(move_destination) << 4)
        | int(move_source)
    )


def _type9(
    *,
    destination_feedback: bool = False,
    amf: int = 0x13,
    yop: int = 0,
    xop: int = 0,
    condition: int = 0xF,
) -> int:
    return (
        0x200000
        | (int(destination_feedback) << 18)
        | ((amf & 0x1F) << 13)
        | ((yop & 0x3) << 11)
        | ((xop & 0x7) << 8)
        | (condition & 0xF)
    )


def _type14(
    *,
    sf: int = 0,
    xop: int = 2,
    move_destination: DREG = DREG.AX1,
    move_source: DREG = DREG.AX0,
) -> int:
    return (
        0x100000
        | ((sf & 0xF) << 11)
        | ((xop & 0x7) << 8)
        | (int(move_destination) << 4)
        | int(move_source)
    )


def _type15(*, sf: int = 0, xop: int = 2, exponent: int = 0) -> int:
    return (
        0x0F0000
        | ((sf & 0xF) << 11)
        | ((xop & 0x7) << 8)
        | (exponent & 0xFF)
    )


def _type16(*, sf: int = 0, xop: int = 2, condition: int = 0xF) -> int:
    return (
        0x0E0000
        | ((sf & 0xF) << 11)
        | ((xop & 0x7) << 8)
        | (condition & 0xF)
    )


def _type21(*, dag: int, i_local: int, m_local: int) -> int:
    return (
        0x090000
        | ((dag & 1) << 4)
        | ((i_local & 3) << 2)
        | (m_local & 3)
    )


def _type23(*, xop: int = 0) -> int:
    return 0x071000 | ((xop & 0x7) << 8)


def _type24(*, yop: int = 1, xop: int = 0) -> int:
    return 0x060000 | ((yop & 0x3) << 11) | ((xop & 0x7) << 8)


def _type25() -> int:
    return 0x050000


def _type26(payload: int) -> int:
    return 0x040000 | (payload & 0x1F)


def _cycle(
    state: ProgramClientsOwnerControlState,
    phase: LogicalPhase,
    **kwargs: object,
) -> ProgramClientsOwnerControlState:
    return apply_program_clients_owner_control_cycle(
        state, phase=phase, **kwargs
    ).state


def _advance_to_seven(
    state: ProgramClientsOwnerControlState,
    **kwargs: object,
) -> ProgramClientsOwnerControlState:
    for phase in (
        LogicalPhase.STATE_1,
        LogicalPhase.STATE_2,
        LogicalPhase.STATE_3,
        LogicalPhase.STATE_4,
        LogicalPhase.STATE_5,
        LogicalPhase.STATE_6,
    ):
        state = _cycle(state, phase, **kwargs)
    return state


def _setup_pm_state() -> ProgramClientsOwnerControlState:
    state = ProgramClientsOwnerControlState.reset()
    for register, value in ((DREG.AX0, 0x1234), (DREG.AY0, 3)):
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            setup_dreg=DREGWrite(register, ExactWord(16, value)),
        )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            setup_dag=DAGRegisterSetup(kind, 4, value),
        )
    return _cycle(
        state,
        LogicalPhase.STATE_8,
        setup_px=ExactWord(8, 0x5A),
    )


def _fill_from_linear_fetch(
    state: ProgramClientsOwnerControlState,
    *,
    pc: int,
    instruction: int,
) -> ProgramClientsOwnerControlState:
    state = _cycle(
        state,
        LogicalPhase.STATE_8,
        instruction_setup=(ExactWord(14, pc), ExactWord(24, 0)),
    )
    issued = apply_program_clients_owner_control_cycle(
        state, phase=LogicalPhase.STATE_8
    )
    assert issued.interface.owner_bus.fetch_accepted
    completed = apply_program_clients_owner_control_cycle(
        _advance_to_seven(issued.state),
        phase=LogicalPhase.STATE_7,
        pmd_read_data=ExactWord(24, instruction),
    )
    assert completed.cache_fill
    assert completed.cache.fill_accepted
    return completed.state


def _execute_fetched_sequence(
    state: ProgramClientsOwnerControlState,
    *,
    pc: int,
    opcodes: tuple[int, ...],
) -> ProgramClientsOwnerControlState:
    if not opcodes:
        raise ValueError("fetched sequence must contain at least one opcode")
    state = _cycle(
        state,
        LogicalPhase.STATE_8,
        instruction_setup=(ExactWord(14, pc), ExactWord(24, opcodes[0])),
    )
    for index in range(len(opcodes)):
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        assert issued.interface.owner_bus.fetch_accepted
        next_opcode = (
            ExactWord(24, opcodes[index + 1])
            if index + 1 < len(opcodes)
            else UNKNOWN
        )
        completed = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=next_opcode,
        )
        assert completed.linear.retire_event
        state = completed.state
    return state


class ProgramClientsOwnerControlTests(unittest.TestCase):
    def test_machine_readable_contract_has_one_cache_and_three_clients(self) -> None:
        contract = json.loads(
            (ROOT / "docs/generated/adsp2100_program_clients_owner_control.yaml")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(contract["device"], "original ADSP-2100")
        self.assertEqual(contract["cache_instances"], 1)
        self.assertEqual(len(contract["architectural_clients"]), 3)
        self.assertEqual(
            contract["collision_policy"], "FAIL_CLOSED_NO_PRIORITY_CLAIM"
        )
        self.assertEqual(
            contract["architectural_state_owners"]
                ["RETAINED_FETCH_TYPE_5_AND_TYPE_13"],
            "ONE_SHARED_ARCHITECTURAL_STATE_OWNER",
        )
        self.assertEqual(
            contract["automatic_fetched_pm_flow"]["TYPE_5"],
            "ISSUE_FROM_RETAINED_OPCODE_AND_INSTALL_PC_PLUS_1_OPCODE",
        )
        self.assertEqual(
            contract["automatic_fetched_pm_flow"]["ACTIVE_LOOP"],
            "FAIL_CLOSED",
        )
        self.assertEqual(
            contract["halt_attachment"]["PM_DATA_RECOGNITION"],
            "FORCE_ONE_EXTERNAL_RECOVERY_THEN_STOP",
        )
        self.assertEqual(
            contract["fetched_validity_sidecars"]["TYPE_21"],
            "SELECTED_I_REQUIRES_VALID_I_M_L_AND_CONFIGURATION",
        )
        self.assertEqual(
            contract["fetched_validity_sidecars"]["TYPE_17"],
            "SOURCE_VALIDITY_PROPAGATES_TO_DREG_DAG_STATUS_CONTROL_SB_AND_PX; "
            "UNKNOWN_MSTAT_BLOCKS_PM_BANK_SELECTION",
        )
        self.assertEqual(
            contract["fetched_validity_sidecars"]["STATUS_STACK"],
            "CAPTURE_AND_RESTORE_ASTAT_MSTAT_IMASK_VALIDITY_WITH_ACCEPTED_ENTRY; "
            "IRQ_ENTRY_TO_FETCHED_RTI_PRESERVES_PRE_ENTRY_VALIDITY",
        )
        self.assertEqual(
            contract["fetched_sstat_read"],
            "LIVE_COMPOSED_LOW_8_BITS; UPPER_EXTENSION_PROVISIONAL_OQ_016",
        )

    def test_ordinary_fetch_fill_supplies_type5_cache_hit(self) -> None:
        cached_word = 0xABCDEF
        state = _fill_from_linear_fetch(
            _setup_pm_state(), pc=0x0220, instruction=cached_word
        )
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(dreg=DREG.AX1),
            type5_next_fetch_address=ExactWord(14, 0x0221),
        )
        self.assertTrue(issued.type5.accepted)
        self.assertTrue(issued.interface.owner_bus.type5_accepted)
        self.assertEqual(
            issued.interface.owner_bus.accepted_owner,
            ProgramBusOwner.TYPE5_PM_DATA,
        )
        completed = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xCAFE55),
        )
        self.assertTrue(completed.type5.data_action_complete)
        self.assertTrue(completed.type5.instruction_complete)
        self.assertTrue(completed.type5_next_instruction_valid)
        self.assertEqual(
            completed.type5_next_instruction, ExactWord(24, cached_word)
        )
        self.assertEqual(
            read_dreg(completed.state.type5.primary, DREG.AX1),
            ExactWord(16, 0xCAFE),
        )

    def test_ordinary_fetch_fill_supplies_type13_cache_hit(self) -> None:
        cached_word = 0xBA9876
        state = _fill_from_linear_fetch(
            _setup_pm_state(), pc=0x0320, instruction=cached_word
        )
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(dreg=DREG.AX1),
            type13_next_fetch_address=ExactWord(14, 0x0321),
        )
        self.assertTrue(issued.type13.accepted)
        self.assertTrue(issued.interface.owner_bus.type13_accepted)
        completed = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xBEEF22),
        )
        self.assertTrue(completed.type13.data_action_complete)
        self.assertTrue(completed.type13.instruction_complete)
        self.assertTrue(completed.type13_next_instruction_valid)
        self.assertEqual(
            completed.type13_next_instruction, ExactWord(24, cached_word)
        )
        self.assertEqual(
            read_dreg(completed.state.type13.primary, DREG.AX1),
            ExactWord(16, 0xBEEF),
        )

    def test_both_pm_execute_controls_fail_closed(self) -> None:
        result = apply_program_clients_owner_control_cycle(
            _setup_pm_state(),
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(),
            type5_next_fetch_address=ExactWord(14, 1),
            type13_execute=True,
            type13_opcode=_type13(),
            type13_next_fetch_address=ExactWord(14, 1),
        )
        self.assertTrue(result.client_execute_conflict)
        self.assertTrue(result.integration_conflict)
        self.assertFalse(result.type5.accepted)
        self.assertFalse(result.type13.accepted)
        self.assertEqual(
            result.interface.owner_bus.accepted_owner, ProgramBusOwner.NONE
        )

    def test_real_linear_and_type5_collision_rejects_both(self) -> None:
        state = _setup_pm_state()
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(ExactWord(14, 0x0100), ExactWord(24, 0)),
        )
        result = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(),
            type5_next_fetch_address=ExactWord(14, 0x0200),
        )
        self.assertTrue(result.linear.fetch_request_presented)
        self.assertTrue(result.type5_request_presented)
        self.assertTrue(result.interface.owner_bus.request_conflict)
        self.assertFalse(result.linear.instruction_issue)
        self.assertTrue(result.type5_retry_pending)
        self.assertEqual(
            result.interface.owner_bus.accepted_owner, ProgramBusOwner.NONE
        )

    def test_type13_miss_recovery_fills_the_same_cache(self) -> None:
        state = _setup_pm_state()
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(dreg=DREG.AX1),
            type13_next_fetch_address=ExactWord(14, 0x0555),
        )
        data_done = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0x111122),
        )
        self.assertTrue(data_done.type13.data_action_complete)
        self.assertFalse(data_done.type13.instruction_complete)
        recovery = apply_program_clients_owner_control_cycle(
            data_done.state, phase=LogicalPhase.STATE_8
        )
        self.assertTrue(recovery.interface.owner_bus.type13_accepted)
        recovered = apply_program_clients_owner_control_cycle(
            _advance_to_seven(recovery.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0x654321),
        )
        self.assertTrue(recovered.type13.instruction_complete)
        self.assertTrue(recovered.cache_fill)
        self.assertTrue(recovered.cache.fill_accepted)
        self.assertEqual(recovered.state.cache.region_start, 0x0555)
        self.assertEqual(recovered.state.cache.region_count, 1)

    def test_type5_pm_read_is_visible_to_following_type13_store(self) -> None:
        state = _fill_from_linear_fetch(
            _setup_pm_state(), pc=0x0600, instruction=0xABCDEF
        )
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(dreg=DREG.AX1),
            type5_next_fetch_address=ExactWord(14, 0x0601),
        )
        completed = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xC0DE77),
        )
        following = apply_program_clients_owner_control_cycle(
            completed.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AX1),
            type13_next_fetch_address=ExactWord(14, 0x0602),
        )
        self.assertTrue(following.type13.pm_write)
        self.assertTrue(following.type13.pm_write_data_known)
        self.assertEqual(following.type13.pm_write_data, 0xC0DE77)

    def test_type13_pm_read_is_visible_to_following_type5_store(self) -> None:
        state = _fill_from_linear_fetch(
            _setup_pm_state(), pc=0x0700, instruction=0xABCDEF
        )
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(dreg=DREG.AX1),
            type13_next_fetch_address=ExactWord(14, 0x0701),
        )
        completed = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xBEEF66),
        )
        following = apply_program_clients_owner_control_cycle(
            completed.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.AX1),
            type5_next_fetch_address=ExactWord(14, 0x0702),
        )
        self.assertTrue(following.type5.pm_write)
        self.assertTrue(following.type5.pm_write_data_known)
        self.assertEqual(following.type5.pm_write_data, 0xBEEF66)

    def test_fetched_type6_result_is_visible_to_type13_store(self) -> None:
        state = _setup_pm_state()
        type6_ax1 = 0x400000 | (0xC0DE << 4) | int(DREG.AX1)
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x0800),
                ExactWord(24, type6_ax1),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        self.assertTrue(issued.interface.owner_bus.fetch_accepted)
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertTrue(retired.linear.retire_event)
        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AX1),
            type13_next_fetch_address=ExactWord(14, 0x0801),
        )
        self.assertTrue(following.type13.pm_write)
        self.assertTrue(following.type13.pm_write_data_known)
        self.assertEqual(following.type13.pm_write_data, 0xC0DE5A)

    def test_fetched_type8_result_is_visible_to_type5_store(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x0880),
                ExactWord(24, _type8()),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        self.assertTrue(issued.interface.owner_bus.fetch_accepted)
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertTrue(retired.linear.retire_event)
        self.assertEqual(
            read_dreg(retired.state.linear.architecture.primary, DREG.AR),
            ExactWord(16, 0x1237),
        )

        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.AR),
            type5_next_fetch_address=ExactWord(14, 0x0881),
        )
        self.assertTrue(following.type5.pm_write)
        self.assertTrue(following.type5.pm_write_data_known)
        self.assertEqual(following.type5.pm_write_data, 0x12375A)

    def test_fetched_type9_result_is_visible_to_type13_store(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x0890),
                ExactWord(24, _type9()),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        self.assertTrue(issued.interface.owner_bus.fetch_accepted)
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertTrue(retired.linear.retire_event)
        self.assertEqual(
            read_dreg(retired.state.linear.architecture.primary, DREG.AR),
            ExactWord(16, 0x1237),
        )

        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AR),
            type13_next_fetch_address=ExactWord(14, 0x0891),
        )
        self.assertTrue(following.type13.pm_write)
        self.assertTrue(following.type13.pm_write_data_known)
        self.assertEqual(following.type13.pm_write_data, 0x12375A)

    def test_fetched_type9_unknown_condition_invalidates_pm_source(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            setup_dreg=DREGWrite(DREG.AR, ExactWord(16, 0x7777)),
        )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x0898),
                ExactWord(24, _type9(condition=0x0)),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        self.assertTrue(issued.interface.owner_bus.fetch_accepted)
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertTrue(retired.linear.retire_event)
        self.assertIs(
            read_dreg(retired.state.linear.architecture.primary, DREG.AR),
            UNKNOWN,
        )

        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.AR),
            type5_next_fetch_address=ExactWord(14, 0x0899),
        )
        self.assertTrue(following.type5.pm_write)
        self.assertFalse(following.type5.pm_write_data_known)

    def test_fetched_type14_results_are_visible_to_pm_stores(self) -> None:
        state = _setup_pm_state()
        for register, value in ((DREG.AR, 0x1234), (DREG.SE, 0)):
            state = _cycle(
                state,
                LogicalPhase.STATE_8,
                setup_dreg=DREGWrite(register, ExactWord(16, value)),
            )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08A0),
                ExactWord(24, _type14()),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertTrue(retired.linear.retire_event)
        self.assertEqual(
            read_dreg(retired.state.linear.architecture.primary, DREG.SR1),
            ExactWord(16, 0x1234),
        )
        self.assertEqual(
            read_dreg(retired.state.linear.architecture.primary, DREG.AX1),
            ExactWord(16, 0x1234),
        )

        shift_store = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.SR1),
            type5_next_fetch_address=ExactWord(14, 0x08A1),
        )
        self.assertTrue(shift_store.type5.pm_write_data_known)
        self.assertEqual(shift_store.type5.pm_write_data, 0x12345A)

        move_store = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AX1),
            type13_next_fetch_address=ExactWord(14, 0x08A1),
        )
        self.assertTrue(move_store.type13.pm_write_data_known)
        self.assertEqual(move_store.type13.pm_write_data, 0x12345A)

    def test_fetched_type15_result_is_visible_to_type13_store(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            setup_dreg=DREGWrite(DREG.AR, ExactWord(16, 0x1234)),
        )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08B0),
                ExactWord(24, _type15()),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.SR1),
            type13_next_fetch_address=ExactWord(14, 0x08B1),
        )
        self.assertTrue(following.type13.pm_write_data_known)
        self.assertEqual(following.type13.pm_write_data, 0x12345A)

    def test_fetched_type16_result_is_visible_to_type5_store(self) -> None:
        state = _setup_pm_state()
        for register, value in ((DREG.AR, 0x1234), (DREG.SE, 0)):
            state = _cycle(
                state,
                LogicalPhase.STATE_8,
                setup_dreg=DREGWrite(register, ExactWord(16, value)),
            )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08C0),
                ExactWord(24, _type16()),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.SR1),
            type5_next_fetch_address=ExactWord(14, 0x08C1),
        )
        self.assertTrue(following.type5.pm_write_data_known)
        self.assertEqual(following.type5.pm_write_data, 0x12345A)

    def test_fetched_type16_unknown_condition_invalidates_pm_source(self) -> None:
        state = _setup_pm_state()
        for register, value in (
            (DREG.AR, 0x1234),
            (DREG.SE, 0),
            (DREG.SR1, 0x7777),
        ):
            state = _cycle(
                state,
                LogicalPhase.STATE_8,
                setup_dreg=DREGWrite(register, ExactWord(16, value)),
            )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08C8),
                ExactWord(24, _type16(condition=0x0)),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertIs(
            read_dreg(retired.state.linear.architecture.primary, DREG.SR1),
            UNKNOWN,
        )
        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.SR1),
            type13_next_fetch_address=ExactWord(14, 0x08C9),
        )
        self.assertFalse(following.type13.pm_write_data_known)

    def test_fetched_type16_unknown_exp_lo_tracks_write_possibility(self) -> None:
        for se_value, expected_known in ((0x00, True), (0xF1, False)):
            with self.subTest(se_value=se_value):
                state = _setup_pm_state()
                for register, value in (
                    (DREG.AR, 0x1234),
                    (DREG.SE, se_value),
                ):
                    state = _cycle(
                        state,
                        LogicalPhase.STATE_8,
                        setup_dreg=DREGWrite(
                            register, ExactWord(16, value)
                        ),
                    )
                state = _cycle(
                    state,
                    LogicalPhase.STATE_8,
                    instruction_setup=(
                        ExactWord(14, 0x08D0 + int(not expected_known)),
                        ExactWord(
                            24,
                            _type16(sf=0xE, condition=0x0),
                        ),
                    ),
                )
                issued = apply_program_clients_owner_control_cycle(
                    state, phase=LogicalPhase.STATE_8
                )
                retired = apply_program_clients_owner_control_cycle(
                    _advance_to_seven(issued.state),
                    phase=LogicalPhase.STATE_7,
                    pmd_read_data=UNKNOWN,
                )
                following = apply_program_clients_owner_control_cycle(
                    retired.state,
                    phase=LogicalPhase.STATE_8,
                    type5_execute=True,
                    type5_opcode=_type5(write=True, dreg=DREG.SE),
                    type5_next_fetch_address=ExactWord(14, 0x08D2),
                )
                self.assertEqual(
                    following.type5.pm_write_data_known,
                    expected_known,
                )

    def test_fetched_type21_result_is_visible_to_pm_address(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08D8),
                ExactWord(
                    24,
                    _type21(dag=1, i_local=0, m_local=0),
                ),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertEqual(
            retired.state.linear.architecture.dag.i[4],
            ExactWord(14, 0x0101),
        )

        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AX0),
            type13_next_fetch_address=ExactWord(14, 0x08D9),
        )
        self.assertTrue(following.type13.pm_address_known)
        self.assertEqual(following.type13.pm_address, 0x0101)
        self.assertTrue(following.interface.owner_bus.type13_accepted)

    def test_fetched_type21_unknown_modify_invalidates_pm_address(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08DA),
                ExactWord(
                    24,
                    _type21(dag=1, i_local=0, m_local=1),
                ),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertIs(retired.state.linear.architecture.dag.i[4], UNKNOWN)

        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.AX0),
            type5_next_fetch_address=ExactWord(14, 0x08DB),
        )
        self.assertFalse(following.type5.pm_address_known)
        self.assertTrue(following.interface.owner_bus.type5_accepted)

    def test_fetched_type17_unknown_source_invalidates_following_pm_address(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08DC),
                ExactWord(24, _type17(0x20, int(DREG.AX1))),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertIs(retired.state.linear.architecture.dag.i[4], UNKNOWN)

        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.AX0),
            type5_next_fetch_address=ExactWord(14, 0x08DD),
        )
        self.assertFalse(following.type5.pm_address_known)
        self.assertTrue(following.interface.owner_bus.type5_accepted)

    def test_fetched_type17_unknown_source_invalidates_shared_px(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08DE),
                ExactWord(24, _type17(0x37, int(DREG.AX1))),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertIs(retired.state.linear.architecture.px, UNKNOWN)
        self.assertIs(retired.state.type5.px, UNKNOWN)
        self.assertIs(retired.state.type13.px, UNKNOWN)

    def test_fetched_type17_unknown_status_sources_invalidate_dreg_chain(self) -> None:
        for code in (0x30, 0x33, 0x34, 0x35, 0x36):
            with self.subTest(code=code):
                state = _cycle(
                    _setup_pm_state(),
                    LogicalPhase.STATE_8,
                    instruction_setup=(
                        ExactWord(14, 0x08E0 + (code & 0xF)),
                        ExactWord(24, _type17(code, int(DREG.AX1))),
                    ),
                )
                issued = apply_program_clients_owner_control_cycle(
                    state, phase=LogicalPhase.STATE_8
                )
                first = apply_program_clients_owner_control_cycle(
                    _advance_to_seven(issued.state),
                    phase=LogicalPhase.STATE_7,
                    pmd_read_data=ExactWord(
                        24, _type17(int(DREG.AR), code)
                    ),
                )
                second_issued = apply_program_clients_owner_control_cycle(
                    first.state, phase=LogicalPhase.STATE_8
                )
                second = apply_program_clients_owner_control_cycle(
                    _advance_to_seven(second_issued.state),
                    phase=LogicalPhase.STATE_7,
                    pmd_read_data=UNKNOWN,
                )
                self.assertIs(
                    read_dreg(
                        second.state.linear.architecture.primary,
                        DREG.AR,
                    ),
                    UNKNOWN,
                )
                following = apply_program_clients_owner_control_cycle(
                    second.state,
                    phase=LogicalPhase.STATE_8,
                    type5_execute=True,
                    type5_opcode=_type5(write=True, dreg=DREG.AR),
                    type5_next_fetch_address=ExactWord(14, 0x08F0),
                )
                self.assertFalse(following.type5.pm_write_data_known)

    def test_fetched_type17_unknown_mstat_blocks_following_pm_client(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08E0),
                ExactWord(24, _type17(0x31, int(DREG.AX1))),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertEqual(
            retired.state.linear.architecture.mstat_valid_mask, 0
        )

        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AX0),
            type13_next_fetch_address=ExactWord(14, 0x08E1),
        )
        self.assertTrue(following.integration_conflict)
        self.assertFalse(following.type13.accepted)
        self.assertEqual(
            following.interface.owner_bus.accepted_owner,
            ProgramBusOwner.NONE,
        )

        loaded = _cycle(
            retired.state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08E1),
                ExactWord(24, _type6(DREG.AX0, 1)),
            ),
        )
        blocked_fetch = apply_program_clients_owner_control_cycle(
            loaded, phase=LogicalPhase.STATE_8
        )
        self.assertTrue(blocked_fetch.integration_conflict)

    def test_status_pop_restores_captured_unknown_validity(self) -> None:
        state = _execute_fetched_sequence(
            _setup_pm_state(),
            pc=0x08E8,
            opcodes=(
                _type17(0x30, int(DREG.AX1)),
                _type17(0x33, int(DREG.AX1)),
                _type17(0x31, int(DREG.AX1)),
                _type26(0x02),
                _type7(0x30, 0x00A5),
                _type7(0x33, 0x0009),
                _type7(0x31, 0x0000),
                _type26(0x03),
            ),
        )
        architecture = state.linear.architecture
        self.assertIs(architecture.astat, UNKNOWN)
        self.assertEqual(architecture.mstat_valid_mask, 0)
        self.assertIs(architecture.imask, UNKNOWN)
        self.assertFalse(architecture.status_stack)

        blocked = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AX0),
            type13_next_fetch_address=ExactWord(14, 0x08F0),
        )
        self.assertTrue(blocked.integration_conflict)
        self.assertFalse(blocked.type13.accepted)

        state = _execute_fetched_sequence(
            state,
            pc=0x08F0,
            opcodes=(_type7(0x31, 0),),
        )
        self.assertEqual(state.linear.architecture.mstat_valid_mask, 0xF)
        state = _execute_fetched_sequence(
            state,
            pc=0x08F1,
            opcodes=(_type17(int(DREG.AR), 0x30),),
        )
        self.assertIs(
            read_dreg(state.linear.architecture.primary, DREG.AR),
            UNKNOWN,
        )
        state = _execute_fetched_sequence(
            state,
            pc=0x08F2,
            opcodes=(_type17(int(DREG.AY1), 0x33),),
        )
        self.assertIs(
            read_dreg(state.linear.architecture.primary, DREG.AY1),
            UNKNOWN,
        )

    def test_fetched_type17_reads_live_composed_sstat(self) -> None:
        state = _execute_fetched_sequence(
            _setup_pm_state(),
            pc=0x08F8,
            opcodes=(
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
            ),
        )
        architecture = state.linear.architecture
        self.assertEqual(
            read_dreg(architecture.primary, DREG.AR),
            ExactWord(16, 0x0055),
        )
        self.assertEqual(
            read_dreg(architecture.primary, DREG.AY1),
            ExactWord(16, 0x0045),
        )
        self.assertEqual(
            read_dreg(architecture.primary, DREG.SI),
            ExactWord(16, 0x0065),
        )
        self.assertEqual(
            read_dreg(architecture.primary, DREG.SR0),
            ExactWord(16, 0x0075),
        )
        self.assertEqual(architecture.sstat, ExactWord(8, 0x75))
        self.assertFalse(architecture.status_stack)

    def test_fetched_type23_result_is_visible_to_pm_store(self) -> None:
        state = _setup_pm_state()
        for register, value in (
            (DREG.AX0, 1),
            (DREG.AY0, 0x8000),
        ):
            state = _cycle(
                state,
                LogicalPhase.STATE_8,
                setup_dreg=DREGWrite(register, ExactWord(16, value)),
            )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            setup_af=ExactWord(16, 2),
        )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            setup_astat=ExactWord(8, 0),
        )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08E0),
                ExactWord(24, _type23()),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertEqual(
            read_dreg(retired.state.linear.architecture.primary, DREG.AY0),
            ExactWord(16, 1),
        )
        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.AY0),
            type5_next_fetch_address=ExactWord(14, 0x08E1),
        )
        self.assertTrue(following.type5.pm_write_data_known)
        self.assertEqual(following.type5.pm_write_data, 0x00015A)

    def test_fetched_type23_unknown_input_invalidates_pm_source(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            setup_af=ExactWord(16, 2),
        )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x08E8),
                ExactWord(24, _type23()),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertIs(
            read_dreg(retired.state.linear.architecture.primary, DREG.AY0),
            UNKNOWN,
        )
        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AY0),
            type13_next_fetch_address=ExactWord(14, 0x08E9),
        )
        self.assertFalse(following.type13.pm_write_data_known)

    def test_fetched_type24_result_and_unknown_input_track_pm_validity(self) -> None:
        for xop, expected_known in ((0, True), (1, False)):
            with self.subTest(xop=xop):
                state = _setup_pm_state()
                for register, value in (
                    (DREG.AX0, 1),
                    (DREG.AY0, 3),
                    (DREG.AY1, 2),
                ):
                    state = _cycle(
                        state,
                        LogicalPhase.STATE_8,
                        setup_dreg=DREGWrite(
                            register, ExactWord(16, value)
                        ),
                    )
                state = _cycle(
                    state,
                    LogicalPhase.STATE_8,
                    instruction_setup=(
                        ExactWord(14, 0x08F0 + xop),
                        ExactWord(24, _type24(xop=xop)),
                    ),
                )
                issued = apply_program_clients_owner_control_cycle(
                    state, phase=LogicalPhase.STATE_8
                )
                retired = apply_program_clients_owner_control_cycle(
                    _advance_to_seven(issued.state),
                    phase=LogicalPhase.STATE_7,
                    pmd_read_data=UNKNOWN,
                )
                following = apply_program_clients_owner_control_cycle(
                    retired.state,
                    phase=LogicalPhase.STATE_8,
                    type5_execute=True,
                    type5_opcode=_type5(write=True, dreg=DREG.AY0),
                    type5_next_fetch_address=ExactWord(14, 0x08F2),
                )
                self.assertEqual(
                    following.type5.pm_write_data_known,
                    expected_known,
                )
                if expected_known:
                    self.assertEqual(following.type5.pm_write_data, 0x00065A)

    def test_fetched_type25_known_conditions_track_pm_validity(self) -> None:
        for astat, mr1, expected in (
            (0x40, 0x0000, 0x7FFF),
            (0x00, 0x1234, 0x1234),
        ):
            with self.subTest(astat=astat):
                state = _cycle(
                    _setup_pm_state(),
                    LogicalPhase.STATE_8,
                    setup_dreg=DREGWrite(DREG.MR1, ExactWord(16, mr1)),
                )
                state = _cycle(
                    state,
                    LogicalPhase.STATE_8,
                    setup_astat=ExactWord(8, astat),
                )
                state = _cycle(
                    state,
                    LogicalPhase.STATE_8,
                    instruction_setup=(
                        ExactWord(14, 0x0900 + int(astat == 0)),
                        ExactWord(24, _type25()),
                    ),
                )
                issued = apply_program_clients_owner_control_cycle(
                    state, phase=LogicalPhase.STATE_8
                )
                retired = apply_program_clients_owner_control_cycle(
                    _advance_to_seven(issued.state),
                    phase=LogicalPhase.STATE_7,
                    pmd_read_data=UNKNOWN,
                )
                following = apply_program_clients_owner_control_cycle(
                    retired.state,
                    phase=LogicalPhase.STATE_8,
                    type13_execute=True,
                    type13_opcode=_type13(write=True, dreg=DREG.MR1),
                    type13_next_fetch_address=ExactWord(14, 0x0902),
                )
                self.assertTrue(following.type13.pm_write_data_known)
                self.assertEqual(
                    following.type13.pm_write_data,
                    (expected << 8) | 0x5A,
                )

    def test_fetched_type25_unknown_condition_invalidates_pm_source(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            setup_dreg=DREGWrite(DREG.MR1, ExactWord(16, 0x1234)),
        )
        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x0908),
                ExactWord(24, _type25()),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertIs(
            read_dreg(retired.state.linear.architecture.primary, DREG.MR1),
            UNKNOWN,
        )
        following = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(write=True, dreg=DREG.MR1),
            type5_next_fetch_address=ExactWord(14, 0x0909),
        )
        self.assertFalse(following.type5.pm_write_data_known)

    def test_type5_result_is_visible_to_fetched_type17(self) -> None:
        state = _setup_pm_state()
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type5_execute=True,
            type5_opcode=_type5(dreg=DREG.AX1),
            type5_next_fetch_address=ExactWord(14, 0x0900),
        )
        data_done = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0xBEEF66),
        )
        recovery = apply_program_clients_owner_control_cycle(
            data_done.state, phase=LogicalPhase.STATE_8
        )
        recovered = apply_program_clients_owner_control_cycle(
            _advance_to_seven(recovery.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertTrue(recovered.type5.instruction_complete)

        # Deterministic instruction preload is verification scaffolding; the
        # fetched Type 17 execution itself consumes the shared PM result.
        type17_ax1_to_ax0 = 0x0D0001
        loaded = _cycle(
            recovered.state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x0900),
                ExactWord(24, type17_ax1_to_ax0),
            ),
        )
        fetched = apply_program_clients_owner_control_cycle(
            loaded, phase=LogicalPhase.STATE_8
        )
        completed = apply_program_clients_owner_control_cycle(
            _advance_to_seven(fetched.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=UNKNOWN,
        )
        self.assertTrue(completed.linear.retire_event)
        self.assertEqual(
            read_dreg(completed.state.linear.architecture.primary, DREG.AX0),
            ExactWord(16, 0xBEEF),
        )
        self.assertEqual(
            read_dreg(completed.state.type13.primary, DREG.AX0),
            ExactWord(16, 0xBEEF),
        )

    def test_automatic_type5_miss_installs_and_executes_next_opcode(self) -> None:
        current_pc = 0x3FFF
        next_opcode = _type6(DREG.SI, 0xA55A)
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, current_pc),
                ExactWord(24, _type5(dreg=DREG.AX1)),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
        )
        self.assertTrue(issued.automatic_pm_instruction_issue)
        self.assertTrue(issued.interface.owner_bus.type5_accepted)
        self.assertFalse(issued.linear.fetch_request_presented)

        data_done = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state, automatic_pm_flow=True),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            pmd_read_data=ExactWord(24, 0xBEEF77),
        )
        self.assertTrue(data_done.type5.data_action_complete)
        self.assertFalse(data_done.automatic_pm_instruction_retire)
        self.assertEqual(
            data_done.state.linear.architecture.pc,
            ExactWord(14, current_pc),
        )

        recovery = apply_program_clients_owner_control_cycle(
            data_done.state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
        )
        self.assertTrue(recovery.interface.owner_bus.type5_accepted)
        self.assertFalse(recovery.automatic_pm_instruction_issue)
        recovered = apply_program_clients_owner_control_cycle(
            _advance_to_seven(recovery.state, automatic_pm_flow=True),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            pmd_read_data=ExactWord(24, next_opcode),
        )
        self.assertTrue(recovered.automatic_pm_instruction_retire)
        self.assertEqual(
            recovered.state.linear.architecture.pc,
            ExactWord(14, 0),
        )
        self.assertEqual(
            recovered.state.linear.instruction,
            ExactWord(24, next_opcode),
        )

        following_issue = apply_program_clients_owner_control_cycle(
            recovered.state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
        )
        self.assertTrue(following_issue.interface.owner_bus.fetch_accepted)
        following_done = apply_program_clients_owner_control_cycle(
            _advance_to_seven(
                following_issue.state,
                automatic_pm_flow=True,
            ),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertEqual(
            read_dreg(
                following_done.state.linear.architecture.primary,
                DREG.SI,
            ),
            ExactWord(16, 0xA55A),
        )

    def test_automatic_type13_cache_hit_installs_next_opcode_once(self) -> None:
        next_pc = 0x0B01
        next_opcode = _type6(DREG.SI, 0x1357)
        state = _setup_pm_state()

        # Populate the one shared cache through an externally directed Type
        # 13 miss while the retained fetch client is idle.
        seed_issue = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(dreg=DREG.AX1),
            type13_next_fetch_address=ExactWord(14, next_pc),
        )
        seed_data = apply_program_clients_owner_control_cycle(
            _advance_to_seven(seed_issue.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, 0x111122),
        )
        seed_recovery = apply_program_clients_owner_control_cycle(
            seed_data.state,
            phase=LogicalPhase.STATE_8,
        )
        seeded = apply_program_clients_owner_control_cycle(
            _advance_to_seven(seed_recovery.state),
            phase=LogicalPhase.STATE_7,
            pmd_read_data=ExactWord(24, next_opcode),
        )
        self.assertTrue(seeded.cache.fill_accepted)

        state = _cycle(
            seeded.state,
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, next_pc - 1),
                ExactWord(24, _type13(dreg=DREG.AX1)),
            ),
        )
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
        )
        self.assertTrue(issued.automatic_pm_instruction_issue)
        completed = apply_program_clients_owner_control_cycle(
            _advance_to_seven(issued.state, automatic_pm_flow=True),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            pmd_read_data=ExactWord(24, 0xCAFE66),
        )
        self.assertTrue(completed.type13.data_action_complete)
        self.assertTrue(completed.automatic_pm_instruction_retire)
        self.assertFalse(completed.type13.recovery_required)
        self.assertEqual(
            completed.state.linear.architecture.pc,
            ExactWord(14, next_pc),
        )
        self.assertEqual(
            completed.state.linear.instruction,
            ExactWord(24, next_opcode),
        )

    def test_automatic_pm_flow_rejects_active_loop_context(self) -> None:
        current_pc = 0x0C00
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, current_pc),
                ExactWord(24, _type5()),
            ),
        )
        architecture = replace(
            state.linear.architecture,
            pc_stack=(ExactWord(14, 0x0BF0),),
            loop_stack=((ExactWord(14, current_pc), ExactWord(4, 0)),),
        )
        state = replace(
            state,
            linear=replace(state.linear, architecture=architecture),
        )
        result = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
        )
        self.assertTrue(result.automatic_pm_flow_blocked)
        self.assertTrue(result.integration_conflict)
        self.assertFalse(result.type5.accepted)
        self.assertFalse(result.linear.fetch_request_presented)

    def test_automatic_pm_flow_rejects_external_execute_controls(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x0D00),
                ExactWord(24, _type5()),
            ),
        )
        result = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            type13_execute=True,
            type13_opcode=_type13(),
            type13_next_fetch_address=ExactWord(14, 0x0D01),
        )
        self.assertTrue(result.integration_conflict)
        self.assertTrue(result.automatic_pm_instruction_issue)
        self.assertFalse(result.type13.accepted)

    def test_automatic_type5_miss_defers_irq_until_instruction_retire(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(
                ExactWord(14, 0x0E00),
                ExactWord(24, _type7(writable["ICNTL"], 0x10)),
            ),
        )
        for next_opcode in (
            _type7(writable["IMASK"], 0xF),
            _type5(dreg=DREG.AX1),
        ):
            issued = apply_program_clients_owner_control_cycle(
                state,
                phase=LogicalPhase.STATE_8,
                automatic_pm_flow=True,
            )
            state = apply_program_clients_owner_control_cycle(
                _advance_to_seven(
                    issued.state,
                    automatic_pm_flow=True,
                    irq_n=0xF,
                ),
                phase=LogicalPhase.STATE_7,
                automatic_pm_flow=True,
                irq_n=0xF,
                pmd_read_data=ExactWord(24, next_opcode),
            ).state

        pm_issue = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            irq_n=0xF,
        )
        data_done = apply_program_clients_owner_control_cycle(
            _advance_to_seven(
                pm_issue.state,
                automatic_pm_flow=True,
                irq_n=0xB,
            ),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            irq_n=0xB,
            pmd_read_data=ExactWord(24, 0xCAFE66),
        )
        self.assertFalse(data_done.linear.interrupt.recognition_event)
        self.assertFalse(data_done.automatic_pm_instruction_retire)

        recovery = apply_program_clients_owner_control_cycle(
            data_done.state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            irq_n=0xB,
        )
        retired = apply_program_clients_owner_control_cycle(
            _advance_to_seven(
                recovery.state,
                automatic_pm_flow=True,
                irq_n=0xB,
            ),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            irq_n=0xB,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(retired.automatic_pm_instruction_retire)
        self.assertTrue(retired.linear.interrupt.recognition_event)
        self.assertTrue(retired.state.linear.interrupt_vectoring)
        self.assertFalse(retired.state.linear.instruction_valid)

        vector_issue = apply_program_clients_owner_control_cycle(
            retired.state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            irq_n=0xF,
        )
        self.assertTrue(vector_issue.linear.interrupt_entry_event)
        self.assertEqual(
            vector_issue.interface.owner_bus.accepted_owner,
            ProgramBusOwner.FETCH,
        )
        self.assertEqual(
            vector_issue.state.interface.owner_bus.bus.address,
            ExactWord(14, 2),
        )

    def test_interrupt_rti_restores_captured_unknown_validity(self) -> None:
        writable = register_code_by_name(writable=True)
        state = _execute_fetched_sequence(
            _setup_pm_state(),
            pc=0x0E20,
            opcodes=(
                _type7(writable["ICNTL"], 0x10),
                _type7(writable["IMASK"], 0xF),
                _type17(writable["ASTAT"], int(DREG.AX1)),
                _type17(writable["MSTAT"], int(DREG.AX1)),
            ),
        )
        self.assertIs(state.linear.architecture.astat, UNKNOWN)
        self.assertEqual(state.linear.architecture.mstat_valid_mask, 0)

        state = _cycle(
            state,
            LogicalPhase.STATE_8,
            instruction_setup=(ExactWord(14, 0x0E24), ExactWord(24, 0)),
        )
        issued = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            irq_n=0xF,
        )
        interrupted = apply_program_clients_owner_control_cycle(
            _advance_to_seven(
                issued.state,
                automatic_pm_flow=True,
                irq_n=0xB,
            ),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            irq_n=0xB,
            pmd_read_data=ExactWord(24, _type6(DREG.AX0, 0xDEAD)),
        )
        self.assertTrue(interrupted.linear.interrupt.recognition_event)
        self.assertTrue(interrupted.state.linear.interrupt_vectoring)

        vector_issue = apply_program_clients_owner_control_cycle(
            interrupted.state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            irq_n=0xF,
        )
        self.assertTrue(vector_issue.linear.interrupt_entry_event)
        self.assertEqual(
            vector_issue.state.interface.owner_bus.bus.address,
            ExactWord(14, 2),
        )
        self.assertEqual(
            vector_issue.state.linear.architecture.imask,
            ExactWord(4, 0x8),
        )

        vector_loaded = apply_program_clients_owner_control_cycle(
            _advance_to_seven(
                vector_issue.state,
                automatic_pm_flow=True,
                irq_n=0xF,
            ),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            irq_n=0xF,
            pmd_read_data=ExactWord(
                24, _type20(interrupt_return=True)
            ),
        )
        self.assertTrue(vector_loaded.linear.interrupt_vector_fetch_event)
        self.assertEqual(
            vector_loaded.state.linear.architecture.pc,
            ExactWord(14, 2),
        )

        rti_issue = apply_program_clients_owner_control_cycle(
            vector_loaded.state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
            irq_n=0xF,
        )
        self.assertEqual(
            rti_issue.state.interface.owner_bus.bus.address,
            ExactWord(14, 0x0E25),
        )
        returned = apply_program_clients_owner_control_cycle(
            _advance_to_seven(
                rti_issue.state,
                automatic_pm_flow=True,
                irq_n=0xF,
            ),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            irq_n=0xF,
            pmd_read_data=ExactWord(24, _type7(writable["MSTAT"], 0)),
        )
        architecture = returned.state.linear.architecture
        self.assertEqual(architecture.pc, ExactWord(14, 0x0E25))
        self.assertIs(architecture.astat, UNKNOWN)
        self.assertEqual(architecture.mstat_valid_mask, 0)
        self.assertEqual(architecture.imask, ExactWord(4, 0xF))
        self.assertFalse(architecture.pc_stack)
        self.assertFalse(architecture.status_stack)

        blocked = apply_program_clients_owner_control_cycle(
            returned.state,
            phase=LogicalPhase.STATE_8,
            type13_execute=True,
            type13_opcode=_type13(write=True, dreg=DREG.AX0),
            type13_next_fetch_address=ExactWord(14, 0x0E26),
        )
        self.assertTrue(blocked.integration_conflict)
        self.assertFalse(blocked.type13.accepted)

        known_mstat = apply_program_clients_owner_control_cycle(
            returned.state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
        )
        moved_astat = apply_program_clients_owner_control_cycle(
            _advance_to_seven(
                known_mstat.state,
                automatic_pm_flow=True,
            ),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            pmd_read_data=ExactWord(
                24, _type17(int(DREG.AR), writable["ASTAT"])
            ),
        )
        astat_move_issue = apply_program_clients_owner_control_cycle(
            moved_astat.state,
            phase=LogicalPhase.STATE_8,
            automatic_pm_flow=True,
        )
        astat_moved = apply_program_clients_owner_control_cycle(
            _advance_to_seven(
                astat_move_issue.state,
                automatic_pm_flow=True,
            ),
            phase=LogicalPhase.STATE_7,
            automatic_pm_flow=True,
            pmd_read_data=UNKNOWN,
        )
        self.assertEqual(
            astat_moved.state.linear.architecture.mstat_valid_mask, 0xF
        )
        self.assertIs(
            read_dreg(
                astat_moved.state.linear.architecture.primary,
                DREG.AR,
            ),
            UNKNOWN,
        )

    def test_combined_ordinary_fetch_halt_holds_and_resumes(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(ExactWord(14, 0x1200), ExactWord(24, 0)),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        self.assertTrue(issued.interface.owner_bus.fetch_accepted)
        state = issued.state
        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = _cycle(state, phase)
        recognized = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_3, halt_n=False
        )
        self.assertTrue(recognized.halt.halt_recognized)
        self.assertFalse(recognized.halt_pm_data_cycle)
        state = recognized.state
        for phase in (
            LogicalPhase.STATE_4,
            LogicalPhase.STATE_5,
            LogicalPhase.STATE_6,
        ):
            state = _cycle(state, phase, halt_n=False)
        stopped = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_7,
            halt_n=False,
            pmd_read_data=ExactWord(24, 0),
        )
        self.assertTrue(stopped.halt.halt_stop_event)
        self.assertTrue(stopped.linear.retire_event)
        self.assertEqual(stopped.state.halt.mode, HaltControlMode.HALTED)

        held = apply_program_clients_owner_control_cycle(
            stopped.state,
            phase=LogicalPhase.STATE_8,
            halt_n=False,
        )
        self.assertTrue(held.halt.phase_hold)
        self.assertFalse(held.halt.effective_phase_advance)
        self.assertFalse(held.linear.fetch_request_presented)

        blocked = apply_program_clients_owner_control_cycle(
            held.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=False,
        )
        self.assertTrue(blocked.halt.release_blocked)
        resumed = apply_program_clients_owner_control_cycle(
            blocked.state,
            phase=LogicalPhase.STATE_8,
            halt_n=True,
            dmack=True,
        )
        self.assertTrue(resumed.halt.resume_event)
        self.assertTrue(resumed.interface.owner_bus.fetch_accepted)

    def test_combined_pm_halt_forces_each_client_and_never_replays(self) -> None:
        for client in (ProgramBusOwner.TYPE5_PM_DATA, ProgramBusOwner.TYPE13_PM_DATA):
            with self.subTest(client=client):
                next_pc = 0x1301 if client is ProgramBusOwner.TYPE5_PM_DATA else 0x1401
                next_opcode = _type6(DREG.SI, 0x55AA)
                state = _fill_from_linear_fetch(
                    _setup_pm_state(), pc=next_pc - 1,
                    instruction=next_opcode,
                )
                # The seed fetch also installs its returned word in the
                # retained fetch client.  Clear only that installed opcode so
                # the following explicit setup cannot present a stale fetch;
                # the shared cache contents and architectural state remain.
                state = replace(
                    state,
                    linear=replace(
                        state.linear,
                        instruction=UNKNOWN,
                        instruction_valid=False,
                    ),
                )
                current_opcode = (
                    _type5(dreg=DREG.AX1)
                    if client is ProgramBusOwner.TYPE5_PM_DATA
                    else _type13(dreg=DREG.AX1)
                )
                state = _cycle(
                    state,
                    LogicalPhase.STATE_8,
                    instruction_setup=(
                        ExactWord(14, next_pc - 1),
                        ExactWord(24, current_opcode),
                    ),
                )
                issued = apply_program_clients_owner_control_cycle(
                    state,
                    phase=LogicalPhase.STATE_8,
                    automatic_pm_flow=True,
                )
                self.assertEqual(
                    issued.interface.owner_bus.accepted_owner, client
                )
                state = issued.state
                for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
                    state = _cycle(
                        state, phase, automatic_pm_flow=True
                    )
                recognized = apply_program_clients_owner_control_cycle(
                    state,
                    phase=LogicalPhase.STATE_3,
                    automatic_pm_flow=True,
                    halt_n=False,
                )
                self.assertTrue(recognized.halt.halt_recognized)
                self.assertTrue(recognized.halt_pm_data_cycle)
                self.assertTrue(recognized.halt_late_force_request)
                state = recognized.state
                for phase in (
                    LogicalPhase.STATE_4,
                    LogicalPhase.STATE_5,
                    LogicalPhase.STATE_6,
                ):
                    state = _cycle(
                        state,
                        phase,
                        automatic_pm_flow=True,
                        halt_n=False,
                    )
                data_done = apply_program_clients_owner_control_cycle(
                    state,
                    phase=LogicalPhase.STATE_7,
                    automatic_pm_flow=True,
                    halt_n=False,
                    pmd_read_data=ExactWord(24, 0xBEEF77),
                )
                self.assertFalse(data_done.automatic_pm_instruction_retire)
                self.assertEqual(
                    read_dreg(
                        data_done.state.linear.architecture.primary,
                        DREG.AX1,
                    ),
                    ExactWord(16, 0xBEEF),
                )
                forced = apply_program_clients_owner_control_cycle(
                    data_done.state,
                    phase=LogicalPhase.STATE_8,
                    automatic_pm_flow=True,
                    halt_n=False,
                )
                self.assertTrue(forced.halt.force_fetch_issue)
                self.assertEqual(
                    forced.interface.owner_bus.accepted_owner, client
                )
                self.assertFalse(forced.halt_attachment_conflict)
                recovered = apply_program_clients_owner_control_cycle(
                    _advance_to_seven(
                        forced.state,
                        automatic_pm_flow=True,
                        halt_n=False,
                    ),
                    phase=LogicalPhase.STATE_7,
                    automatic_pm_flow=True,
                    halt_n=False,
                    pmd_read_data=ExactWord(24, next_opcode),
                )
                self.assertTrue(recovered.automatic_pm_instruction_retire)
                self.assertTrue(recovered.halt.halt_stop_event)
                self.assertEqual(
                    recovered.state.halt.mode, HaltControlMode.HALTED
                )
                self.assertEqual(
                    read_dreg(
                        recovered.state.linear.architecture.primary,
                        DREG.AX1,
                    ),
                    ExactWord(16, 0xBEEF),
                )
                held = apply_program_clients_owner_control_cycle(
                    recovered.state,
                    phase=LogicalPhase.STATE_8,
                    automatic_pm_flow=True,
                    halt_n=False,
                )
                self.assertTrue(held.halt.phase_hold)
                resumed = apply_program_clients_owner_control_cycle(
                    held.state,
                    phase=LogicalPhase.STATE_8,
                    automatic_pm_flow=True,
                    halt_n=True,
                )
                self.assertTrue(resumed.halt.resume_event)
                self.assertTrue(resumed.interface.owner_bus.fetch_accepted)

    def test_simultaneous_halt_and_br_fail_closed(self) -> None:
        state = _cycle(
            _setup_pm_state(),
            LogicalPhase.STATE_8,
            instruction_setup=(ExactWord(14, 0x1500), ExactWord(24, 0)),
        )
        issued = apply_program_clients_owner_control_cycle(
            state, phase=LogicalPhase.STATE_8
        )
        state = issued.state
        for phase in (LogicalPhase.STATE_1, LogicalPhase.STATE_2):
            state = _cycle(state, phase)
        result = apply_program_clients_owner_control_cycle(
            state,
            phase=LogicalPhase.STATE_3,
            halt_n=False,
            br_n=False,
        )
        self.assertTrue(result.halt_br_conflict)
        self.assertTrue(result.integration_conflict)
        self.assertFalse(result.halt.halt_recognized)
        self.assertFalse(result.interface.control.request_recognized)
        self.assertEqual(result.state.halt.mode, HaltControlMode.RUNNING)


if __name__ == "__main__":
    unittest.main()
