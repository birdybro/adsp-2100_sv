from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    COMPUTE_PM_CLASS_MASK,
    COMPUTE_PM_CLASS_VALUE,
    ComputePMState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_compute_pm_cycle,
    compute_pm_unsupported_reason,
    decode_compute_pm,
    is_compute_pm_class,
    read_dreg,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/vectors/compute_pm_fixtures.json"
SEMANTICS = ROOT / "docs/generated/adsp2100_compute_pm.yaml"


def _opcode(
    *,
    write: bool = False,
    z: int = 0,
    amf: int = 0,
    yop: int = 0,
    xop: int = 0,
    dreg: DREG = DREG.AX0,
    i: int = 0,
    m: int = 0,
) -> int:
    return (
        0x500000
        | (int(write) << 19)
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (int(dreg) << 4)
        | (i << 2)
        | m
    )


class ComputePMTests(unittest.TestCase):
    def _dag(
        self,
        state: ComputePMState,
        *,
        i_address: int,
        m_address: int,
        i_value: int,
        m_value: int,
        l_value: int = 0,
    ) -> ComputePMState:
        for setup in (
            DAGRegisterSetup(DAGRegisterKind.I, i_address, i_value),
            DAGRegisterSetup(DAGRegisterKind.M, m_address, m_value),
            DAGRegisterSetup(DAGRegisterKind.L, i_address, l_value),
        ):
            state = apply_compute_pm_cycle(state, setup_dag=setup).state
        return state

    def _dreg(
        self,
        state: ComputePMState,
        register: DREG,
        value: int,
    ) -> ComputePMState:
        return apply_compute_pm_cycle(
            state,
            setup_dreg=DREGWrite(register, ExactWord(16, value)),
        ).state

    def test_complete_type_5_partition_and_fields(self) -> None:
        supported = 0
        collision = 0
        for payload in range(1 << 20):
            opcode = 0x500000 | payload
            self.assertTrue(is_compute_pm_class(opcode))
            action = decode_compute_pm(opcode)
            reason = compute_pm_unsupported_reason(opcode)
            if action is None:
                self.assertEqual(reason, "UNSUPPORTED_DESTINATION_COLLISION")
                collision += 1
                continue
            self.assertIsNone(reason)
            self.assertEqual(action.write, bool((payload >> 19) & 1))
            self.assertEqual(action.z, (payload >> 18) & 1)
            self.assertEqual(action.amf, (payload >> 13) & 0x1F)
            self.assertEqual(action.yop, (payload >> 11) & 3)
            self.assertEqual(action.xop, (payload >> 8) & 7)
            self.assertEqual(action.memory_dreg, DREG((payload >> 4) & 0xF))
            self.assertEqual(action.i_address, 4 | ((payload >> 2) & 3))
            self.assertEqual(action.m_address, 4 | (payload & 3))
            supported += 1
        self.assertEqual(COMPUTE_PM_CLASS_MASK, 0xF00000)
        self.assertEqual(COMPUTE_PM_CLASS_VALUE, 0x500000)
        self.assertEqual(supported, 1_017_344)
        self.assertEqual(collision, 31_232)

    def test_hand_transcribed_field_fixtures(self) -> None:
        data = json.loads(FIXTURES.read_text(encoding="utf-8"))
        self.assertEqual(data["device"], "ADSP-2100")
        self.assertIn("not assembler-generated", data["derivation"])
        for fixture in data["fixtures"]:
            action = decode_compute_pm(int(fixture["opcode"], 16))
            self.assertIsNotNone(action, fixture["id"])
            assert action is not None
            fields = fixture["fields"]
            self.assertEqual(action.write, bool(fields["D"]))
            self.assertEqual(action.z, fields["Z"])
            self.assertEqual(action.amf, fields["AMF"])
            self.assertEqual(action.yop, fields["YOP"])
            self.assertEqual(action.xop, fields["XOP"])
            self.assertEqual(int(action.memory_dreg), fields["DREG"])
            self.assertEqual(action.i_local, fields["I"])
            self.assertEqual(action.m_local, fields["M"])

    def test_memory_only_amf_zero_ignores_compute_fields(self) -> None:
        for write in (False, True):
            for z in range(2):
                for yop in range(4):
                    for xop in range(8):
                        action = decode_compute_pm(
                            _opcode(
                                write=write,
                                z=z,
                                yop=yop,
                                xop=xop,
                                dreg=DREG.MR1,
                                i=3,
                                m=2,
                            )
                        )
                        self.assertIsNotNone(action)
                        assert action is not None
                        self.assertFalse(action.computation_enabled)
                        self.assertFalse(action.is_mac)
                        self.assertIsNone(action.x_source)
                        self.assertIsNone(action.y_source)

    def test_read_collisions_rejected_and_same_writes_legal(self) -> None:
        for amf, dreg in (
            (0x13, DREG.AR),
            (0x08, DREG.MR0),
            (0x08, DREG.MR1),
            (0x08, DREG.MR2),
        ):
            read = _opcode(amf=amf, dreg=dreg)
            self.assertIsNone(decode_compute_pm(read))
            self.assertEqual(
                compute_pm_unsupported_reason(read),
                "UNSUPPORTED_DESTINATION_COLLISION",
            )
            self.assertIsNotNone(
                decode_compute_pm(_opcode(write=True, amf=amf, dreg=dreg))
            )
            self.assertIsNotNone(
                decode_compute_pm(_opcode(z=1, amf=amf, dreg=dreg))
            )

    def test_operand_and_dag2_mapping(self) -> None:
        alu = decode_compute_pm(_opcode(amf=0x13, xop=1, yop=1))
        mac = decode_compute_pm(_opcode(amf=0x08, xop=1, yop=1, i=2, m=3))
        self.assertIsNotNone(alu)
        self.assertIsNotNone(mac)
        assert alu is not None and mac is not None
        self.assertEqual(alu.x_source, DREG.AX1)
        self.assertEqual(alu.y_source, DREG.AY1)
        self.assertFalse(alu.is_mac)
        self.assertEqual(mac.x_source, DREG.MX1)
        self.assertEqual(mac.y_source, DREG.MY1)
        self.assertTrue(mac.is_mac)
        self.assertEqual((mac.i_address, mac.m_address), (6, 7))
        for yop in (2, 3):
            action = decode_compute_pm(_opcode(amf=0x13, yop=yop))
            self.assertIsNotNone(action)
            assert action is not None
            self.assertIsNone(action.y_source)

    def test_machine_readable_action_contract(self) -> None:
        data = json.loads(SEMANTICS.read_text(encoding="utf-8"))
        self.assertEqual(data["device"], "ADSP-2100")
        self.assertEqual(data["decode"]["original_type"], 5)
        self.assertEqual(data["decode"]["class_words"], 1_048_576)
        self.assertEqual(data["decode"]["source_closed_words"], 1_017_344)
        self.assertEqual(
            data["parallel_actions"]["pm_write_overlap_rule"],
            "LEGAL_BECAUSE_WRITE_DATA_USES_CYCLE_START_DREG_AND_PX",
        )
        self.assertEqual(
            data["execution_boundary"]["data_completion"],
            "ATOMIC_COMPUTE_STATUS_OPTIONAL_PM_READ_PX_AND_SELECTED_I_WRITEBACK",
        )
        self.assertEqual(
            data["native_pm_attachment"]["commit_edge"],
            "ENABLED_STATE_7_TO_STATE_8",
        )
        self.assertNotIn("PM_CACHE_AND_RECOVERY_EXECUTION", data["unresolved"])
        self.assertIn(
            "WHOLE_CORE_FETCH_PC_LOOP_INTERRUPT_AND_BUS_ARBITRATION",
            data["unresolved"],
        )

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x4FFFFF, 0x600000, 0xFFFFFF):
            self.assertFalse(is_compute_pm_class(opcode))
            self.assertIsNone(decode_compute_pm(opcode))
            self.assertIsNone(compute_pm_unsupported_reason(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_compute_pm(opcode)

    def test_compute_read_uses_old_operands_and_splits_pm_word(self) -> None:
        state = self._dag(
            ComputePMState.reset(),
            i_address=4,
            m_address=7,
            i_value=0x100,
            m_value=1,
        )
        state = self._dreg(state, DREG.AX0, 2)
        state = self._dreg(state, DREG.AY0, 3)
        state = apply_compute_pm_cycle(
            state,
            setup_astat=ExactWord(8, 0),
        ).state

        result = apply_compute_pm_cycle(
            state,
            execute=True,
            opcode=0x526003,
            pm_read_data=ExactWord(24, 0xCAFE55),
            next_fetch_address=ExactWord(14, 0x101),
        )
        self.assertTrue(result.accepted and result.data_action_complete)
        self.assertTrue(result.instruction_complete and result.event_boundary)
        self.assertTrue(result.alu_write and result.dreg_write and result.px_write)
        self.assertEqual(result.pm_address, 0x100)
        self.assertEqual(read_dreg(result.state.primary, DREG.AR), ExactWord(16, 5))
        self.assertEqual(
            read_dreg(result.state.primary, DREG.AX0),
            ExactWord(16, 0xCAFE),
        )
        self.assertEqual(result.state.px, ExactWord(8, 0x55))
        self.assertEqual(result.state.dag.i[4], 0x101)

    def test_compute_write_uses_old_dreg_and_px_then_commits_result(self) -> None:
        state = self._dag(
            ComputePMState.reset(),
            i_address=7,
            m_address=4,
            i_value=0x222,
            m_value=0x3FFF,
        )
        state = self._dreg(state, DREG.AX0, 2)
        state = self._dreg(state, DREG.AY0, 3)
        state = self._dreg(state, DREG.AR, 0x7777)
        state = apply_compute_pm_cycle(
            state,
            setup_astat=ExactWord(8, 0),
        ).state
        state = apply_compute_pm_cycle(
            state,
            setup_px=ExactWord(8, 0x5A),
        ).state

        result = apply_compute_pm_cycle(
            state,
            execute=True,
            opcode=0x5A60AC,
        )
        self.assertTrue(result.pm_write and result.pm_write_data_known)
        self.assertEqual(result.pm_write_data, 0x77775A)
        self.assertTrue(result.alu_write)
        self.assertFalse(result.dreg_write or result.px_write)
        self.assertEqual(read_dreg(result.state.primary, DREG.AR), ExactWord(16, 5))
        self.assertEqual(result.state.px, ExactWord(8, 0x5A))
        self.assertEqual(result.state.dag.i[7], 0x221)

    def test_wait_holds_compute_pm_descriptor_and_commits_atomically(self) -> None:
        state = self._dag(
            ComputePMState.reset(),
            i_address=4,
            m_address=7,
            i_value=0x80,
            m_value=1,
        )
        state = self._dreg(state, DREG.AX0, 2)
        state = self._dreg(state, DREG.AY0, 3)
        state = apply_compute_pm_cycle(
            state,
            setup_astat=ExactWord(8, 0),
        ).state
        issued = apply_compute_pm_cycle(
            state,
            execute=True,
            opcode=0x526003,
            next_fetch_address=ExactWord(14, 0x81),
            pm_cycle_complete=False,
        )
        # Cycle-result flags describe the retained state visible before the
        # accepting edge. The descriptor becomes held in issued.state and is
        # therefore reported on the following clock, not on this issue event.
        self.assertTrue(issued.accepted)
        self.assertFalse(issued.held_transaction)
        self.assertFalse(issued.data_action_complete)
        self.assertEqual(issued.state.primary, state.primary)
        self.assertEqual(issued.state.dag, state.dag)

        held = apply_compute_pm_cycle(
            issued.state,
            execute=True,
            opcode=0x5A60AC,
            pm_cycle_complete=False,
        )
        self.assertTrue(held.integration_conflict)
        self.assertEqual(held.pm_address, 0x80)
        self.assertEqual(held.state, issued.state)

        completed = apply_compute_pm_cycle(
            held.state,
            pm_read_data=ExactWord(24, 0xBEEF7E),
        )
        self.assertTrue(completed.data_action_complete)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AR), ExactWord(16, 5))
        self.assertEqual(
            read_dreg(completed.state.primary, DREG.AX0),
            ExactWord(16, 0xBEEF),
        )
        self.assertEqual(completed.state.px, ExactWord(8, 0x7E))
        self.assertEqual(completed.state.dag.i[4], 0x81)

    def test_cache_miss_recovery_does_not_repeat_data_actions(self) -> None:
        state = self._dag(
            ComputePMState.reset(),
            i_address=4,
            m_address=4,
            i_value=0x100,
            m_value=2,
        )
        state = self._dreg(state, DREG.AX0, 0x1111)
        issued = apply_compute_pm_cycle(
            state,
            execute=True,
            opcode=_opcode(dreg=DREG.AX0),
            pm_read_data=ExactWord(24, 0xCAFE55),
            next_fetch_address=ExactWord(14, 0x333),
            cache_next_instruction_valid=False,
        )
        self.assertTrue(issued.data_action_complete)
        self.assertFalse(issued.instruction_complete)
        self.assertTrue(issued.recovery_required and issued.busy)
        self.assertEqual(issued.state.dag.i[4], 0x102)

        recovered = apply_compute_pm_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0x123456),
        )
        self.assertTrue(recovered.recovery_fetch)
        self.assertFalse(recovered.pm_data_access)
        self.assertEqual(recovered.pm_address, 0x333)
        self.assertEqual(recovered.fetched_instruction, 0x123456)
        self.assertTrue(recovered.instruction_complete and recovered.event_boundary)
        self.assertEqual(recovered.state.dag.i[4], 0x102)

    def test_alternate_bank_mac_and_dag2_are_selected(self) -> None:
        state = self._dag(
            ComputePMState.reset(),
            i_address=6,
            m_address=5,
            i_value=0x200,
            m_value=2,
        )
        state = apply_compute_pm_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        state = self._dreg(state, DREG.MX0, 2)
        state = self._dreg(state, DREG.MY0, 3)
        state = apply_compute_pm_cycle(
            state,
            setup_astat=ExactWord(8, 0),
        ).state
        state = apply_compute_pm_cycle(
            state,
            setup_px=ExactWord(8, 0xAA),
        ).state
        result = apply_compute_pm_cycle(
            state,
            execute=True,
            opcode=_opcode(
                write=True,
                amf=4,
                dreg=DREG.MX0,
                i=2,
                m=1,
            ),
        )
        self.assertTrue(result.mac_write)
        self.assertEqual(result.pm_write_data, 0x0002AA)
        self.assertEqual(result.state.alternate.mr[0], ExactWord(16, 12))
        self.assertIs(result.state.primary.mr[0], UNKNOWN)
        self.assertEqual(result.state.dag.i[6], 0x202)

    def test_unknown_read_invalidates_only_documented_destinations(self) -> None:
        state = self._dag(
            ComputePMState.reset(),
            i_address=4,
            m_address=4,
            i_value=0x20,
            m_value=1,
        )
        state = self._dreg(state, DREG.AR, 0x1234)
        state = apply_compute_pm_cycle(
            state,
            setup_astat=ExactWord(8, 0xFF),
        ).state
        result = apply_compute_pm_cycle(
            state,
            execute=True,
            opcode=_opcode(amf=0x13, dreg=DREG.AX0),
            pm_read_data=UNKNOWN,
        )
        self.assertIs(read_dreg(result.state.primary, DREG.AR), UNKNOWN)
        self.assertIs(read_dreg(result.state.primary, DREG.AX0), UNKNOWN)
        self.assertIs(result.state.px, UNKNOWN)
        for bit in (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV, ASTATBit.AC):
            self.assertIs(result.state.status.astat.bit(bit), UNKNOWN)
        self.assertEqual(result.state.dag.i[4], 0x21)

    def test_reset_invalid_and_control_conflicts_fail_closed(self) -> None:
        state = ComputePMState.reset()
        invalid = apply_compute_pm_cycle(state, execute=True, opcode=0)
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_compute_pm_cycle(
            state,
            execute=True,
            opcode=_opcode(write=True),
            setup_px=ExactWord(8, 1),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        with self.assertRaises(ValueError):
            apply_compute_pm_cycle(state, setup_px=ExactWord(16, 0))


if __name__ == "__main__":
    unittest.main()
