from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    COMPUTE_DUAL_CLASS_MASK,
    COMPUTE_DUAL_CLASS_VALUE,
    ComputeDualState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_compute_dual_cycle,
    decode_compute_dual,
    is_compute_dual_class,
    read_dreg,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/vectors/compute_dual_fixtures.json"
SEMANTICS = ROOT / "docs/generated/adsp2100_compute_dual.yaml"


def _opcode(
    *,
    pd: int = 0,
    dd: int = 0,
    amf: int = 0,
    yop: int = 0,
    xop: int = 0,
    pm_i: int = 0,
    pm_m: int = 0,
    dm_i: int = 0,
    dm_m: int = 0,
) -> int:
    return (
        0xC00000
        | (pd << 20)
        | (dd << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (pm_i << 6)
        | (pm_m << 4)
        | (dm_i << 2)
        | dm_m
    )


class ComputeDualTests(unittest.TestCase):
    def _setup_dag(
        self,
        state: ComputeDualState,
        *,
        i_address: int,
        m_address: int,
        i_value: int,
        m_value: int,
        l_value: int = 0,
    ) -> ComputeDualState:
        for setup in (
            DAGRegisterSetup(DAGRegisterKind.I, i_address, i_value),
            DAGRegisterSetup(DAGRegisterKind.M, m_address, m_value),
            DAGRegisterSetup(DAGRegisterKind.L, i_address, l_value),
        ):
            state = apply_compute_dual_cycle(state, setup_dag=setup).state
        return state

    def test_complete_type_1_partition_and_fields(self) -> None:
        count = 0
        for payload in range(1 << 22):
            opcode = 0xC00000 | payload
            self.assertTrue(is_compute_dual_class(opcode))
            action = decode_compute_dual(opcode)
            self.assertIsNotNone(action)
            assert action is not None
            self.assertEqual(int(action.pm_destination), 4 + ((payload >> 20) & 3))
            self.assertEqual(int(action.dm_destination), (payload >> 18) & 3)
            self.assertEqual(action.amf, (payload >> 13) & 0x1F)
            self.assertEqual(action.yop, (payload >> 11) & 3)
            self.assertEqual(action.xop, (payload >> 8) & 7)
            self.assertEqual(action.pm_i_address, 4 | ((payload >> 6) & 3))
            self.assertEqual(action.pm_m_address, 4 | ((payload >> 4) & 3))
            self.assertEqual(action.dm_i_address, (payload >> 2) & 3)
            self.assertEqual(action.dm_m_address, payload & 3)
            count += 1
        self.assertEqual(COMPUTE_DUAL_CLASS_MASK, 0xC00000)
        self.assertEqual(COMPUTE_DUAL_CLASS_VALUE, 0xC00000)
        self.assertEqual(count, 4_194_304)

    def test_hand_derived_primary_fixtures(self) -> None:
        data = json.loads(FIXTURES.read_text(encoding="utf-8"))
        self.assertEqual(data["device"], "ADSP-2100")
        self.assertIn("not assembler-generated", data["derivation"])
        for fixture in data["fixtures"]:
            action = decode_compute_dual(int(fixture["opcode"], 16))
            self.assertIsNotNone(action, fixture["id"])
            assert action is not None
            fields = fixture["fields"]
            self.assertEqual(int(action.pm_destination), 4 + fields["PD"])
            self.assertEqual(int(action.dm_destination), fields["DD"])
            self.assertEqual(action.amf, fields["AMF"])
            self.assertEqual(action.yop, fields["YOP"])
            self.assertEqual(action.xop, fields["XOP"])
            self.assertEqual(action.pm_i_local, fields["PM_I"])
            self.assertEqual(action.pm_m_local, fields["PM_M"])
            self.assertEqual(action.dm_i_local, fields["DM_I"])
            self.assertEqual(action.dm_m_local, fields["DM_M"])

    def test_amf_zero_is_dual_read_only_for_every_alias(self) -> None:
        for pd in range(4):
            for dd in range(4):
                for yop in range(4):
                    for xop in range(8):
                        action = decode_compute_dual(
                            _opcode(pd=pd, dd=dd, yop=yop, xop=xop)
                        )
                        self.assertIsNotNone(action)
                        assert action is not None
                        self.assertFalse(action.computation_enabled)
                        self.assertFalse(action.is_mac)
                        self.assertIsNone(action.computation_destination)
                        self.assertIsNone(action.x_source)
                        self.assertIsNone(action.y_source)

    def test_operand_result_and_fixed_dag_mapping(self) -> None:
        alu = decode_compute_dual(
            _opcode(pd=1, dd=1, amf=0x13, yop=1, xop=1, pm_i=2, pm_m=3)
        )
        mac = decode_compute_dual(
            _opcode(pd=3, dd=3, amf=0x08, yop=1, xop=1, dm_i=2, dm_m=3)
        )
        self.assertIsNotNone(alu)
        self.assertIsNotNone(mac)
        assert alu is not None and mac is not None
        self.assertEqual(alu.x_source, DREG.AX1)
        self.assertEqual(alu.y_source, DREG.AY1)
        self.assertEqual(alu.computation_destination, "AR")
        self.assertEqual(alu.pm_destination, DREG.AY1)
        self.assertEqual(alu.dm_destination, DREG.AX1)
        self.assertEqual((alu.pm_i_address, alu.pm_m_address), (6, 7))
        self.assertEqual(mac.x_source, DREG.MX1)
        self.assertEqual(mac.y_source, DREG.MY1)
        self.assertEqual(mac.computation_destination, "MR")
        self.assertEqual(mac.pm_destination, DREG.MY1)
        self.assertEqual(mac.dm_destination, DREG.MX1)
        self.assertEqual((mac.dm_i_address, mac.dm_m_address), (2, 3))
        self.assertFalse(alu.destination_feedback)
        self.assertFalse(mac.destination_feedback)

    def test_machine_readable_action_contract(self) -> None:
        data = json.loads(SEMANTICS.read_text(encoding="utf-8"))
        self.assertEqual(data["device"], "ADSP-2100")
        self.assertEqual(
            data["scope"],
            "SOURCE_CLOSED_TYPE_1_ALU_MAC_PLUS_DM_AND_PM_READ_BOUNDED_LOGICAL_EXECUTION",
        )
        self.assertEqual(data["decode"]["original_type"], 1)
        self.assertEqual(data["decode"]["class_words"], 4_194_304)
        self.assertEqual(data["decode"]["source_closed_words"], 4_194_304)
        self.assertEqual(data["decode"]["unsupported_words"], 0)
        self.assertEqual(
            data["parallel_actions"]["memory_directions"],
            "DM_READ_AND_PM_READ_ONLY",
        )
        self.assertEqual(
            data["logical_execution"]["native_attachment"],
            "WITHHELD_UNDER_OQ_023",
        )
        self.assertIn("rtl_state", data["tests"])
        self.assertIn("formal_state", data["tests"])
        self.assertIn("quartus_state", data["tests"])
        self.assertIn(
            "OQ_023_NATIVE_PM_BEHAVIOR_DURING_DMACK_EXTENSION",
            data["unresolved"],
        )
        self.assertNotIn(
            "ATOMIC_DUAL_BUS_EXECUTION_STATE_AND_NATIVE_ATTACHMENT",
            data["unresolved"],
        )

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x7FFFFF, 0x800000, 0xBFFFFF):
            self.assertFalse(is_compute_dual_class(opcode))
            self.assertIsNone(decode_compute_dual(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_compute_dual(opcode)

    def test_dual_read_only_commits_both_inputs_px_and_both_dags(self) -> None:
        state = ComputeDualState.reset()
        state = self._setup_dag(
            state,
            i_address=2,
            m_address=1,
            i_value=0x100,
            m_value=0x3FFF,
        )
        state = self._setup_dag(
            state,
            i_address=7,
            m_address=4,
            i_value=0x200,
            m_value=2,
        )
        result = apply_compute_dual_cycle(
            state,
            execute=True,
            opcode=_opcode(pd=3, dd=1, pm_i=3, pm_m=0, dm_i=2, dm_m=1),
            transaction_complete=True,
            dm_read_data=ExactWord(16, 0x1234),
            pm_read_data=ExactWord(24, 0xABCDEF),
        )
        self.assertTrue(result.instruction_complete)
        self.assertFalse(result.alu_write)
        self.assertFalse(result.mac_write)
        self.assertTrue(result.dm_dreg_write_known)
        self.assertTrue(result.pm_dreg_write_known)
        self.assertTrue(result.px_write_known)
        self.assertEqual(read_dreg(result.state.primary, DREG.AX1).value, 0x1234)
        self.assertEqual(read_dreg(result.state.primary, DREG.MY1).value, 0xABCD)
        self.assertEqual(result.state.px.value, 0xEF)
        self.assertEqual(result.state.dag.i[2], 0xFF)
        self.assertEqual(result.state.dag.i[7], 0x202)

    def test_waited_alu_uses_old_inputs_and_commits_atomically(self) -> None:
        state = ComputeDualState.reset()
        state = self._setup_dag(
            state,
            i_address=0,
            m_address=0,
            i_value=0x120,
            m_value=1,
        )
        state = self._setup_dag(
            state,
            i_address=4,
            m_address=4,
            i_value=0x220,
            m_value=2,
        )
        for destination, value in ((DREG.AX0, 2), (DREG.AY0, 3)):
            state = apply_compute_dual_cycle(
                state,
                setup_dreg=DREGWrite(destination, ExactWord(16, value)),
            ).state
        state = apply_compute_dual_cycle(
            state,
            setup_astat=ExactWord(8, 0xA0),
        ).state
        opcode = _opcode(amf=0x13)
        issued = apply_compute_dual_cycle(
            state,
            execute=True,
            opcode=opcode,
            transaction_complete=False,
        )
        self.assertTrue(issued.accepted)
        self.assertTrue(issued.stalled)
        self.assertEqual(issued.dm_address, 0x120)
        self.assertEqual(issued.pm_address, 0x220)
        self.assertEqual(read_dreg(issued.state.primary, DREG.AR), UNKNOWN)
        self.assertEqual(issued.state.dag.i[0], 0x120)
        self.assertEqual(issued.state.dag.i[4], 0x220)

        held = apply_compute_dual_cycle(
            issued.state,
            execute=True,
            opcode=0,
            setup_dreg=DREGWrite(DREG.AX0, ExactWord(16, 0x9999)),
        )
        self.assertTrue(held.integration_conflict)
        self.assertEqual(held.dm_address, 0x120)
        self.assertEqual(held.pm_address, 0x220)
        self.assertEqual(read_dreg(held.state.primary, DREG.AX0).value, 2)

        completed = apply_compute_dual_cycle(
            held.state,
            transaction_complete=True,
            dm_read_data=ExactWord(16, 0xCAFE),
            pm_read_data=ExactWord(24, 0x13579B),
        )
        self.assertTrue(completed.instruction_complete)
        self.assertTrue(completed.alu_write)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AR).value, 5)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AX0).value, 0xCAFE)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AY0).value, 0x1357)
        self.assertEqual(completed.state.px.value, 0x9B)
        self.assertEqual(completed.state.dag.i[0], 0x121)
        self.assertEqual(completed.state.dag.i[4], 0x222)
        self.assertFalse(completed.state.status.astat.bit(ASTATBit.AZ))

    def test_dag1_bit_reverse_is_independent_of_dag2(self) -> None:
        state = ComputeDualState.reset()
        state = self._setup_dag(
            state,
            i_address=1,
            m_address=3,
            i_value=1,
            m_value=1,
        )
        state = self._setup_dag(
            state,
            i_address=6,
            m_address=5,
            i_value=1,
            m_value=1,
        )
        state = apply_compute_dual_cycle(
            state,
            setup_mstat=ExactWord(4, 0x2),
        ).state
        issued = apply_compute_dual_cycle(
            state,
            execute=True,
            opcode=_opcode(pm_i=2, pm_m=1, dm_i=1, dm_m=3),
        )
        self.assertEqual(issued.dm_address, 0x2000)
        self.assertEqual(issued.pm_address, 1)
        completed = apply_compute_dual_cycle(
            issued.state,
            transaction_complete=True,
            dm_read_data=ExactWord(16, 0),
            pm_read_data=ExactWord(24, 0),
        )
        self.assertEqual(completed.state.dag.i[1], 2)
        self.assertEqual(completed.state.dag.i[6], 2)

    def test_alternate_bank_mac_and_unknown_read_validity(self) -> None:
        state = ComputeDualState.reset()
        state = self._setup_dag(
            state,
            i_address=0,
            m_address=0,
            i_value=0x10,
            m_value=1,
        )
        state = self._setup_dag(
            state,
            i_address=4,
            m_address=4,
            i_value=0x20,
            m_value=1,
        )
        state = apply_compute_dual_cycle(
            state,
            setup_dreg=DREGWrite(DREG.MX0, ExactWord(16, 0x7777)),
        ).state
        state = apply_compute_dual_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        for destination, value in ((DREG.MX0, 2), (DREG.MY0, 3)):
            state = apply_compute_dual_cycle(
                state,
                setup_dreg=DREGWrite(destination, ExactWord(16, value)),
            ).state
        state = apply_compute_dual_cycle(
            state,
            setup_astat=ExactWord(8, 0),
        ).state
        result = apply_compute_dual_cycle(
            state,
            execute=True,
            opcode=_opcode(pd=2, dd=2, amf=4),
            transaction_complete=True,
            dm_read_data=UNKNOWN,
            pm_read_data=ExactWord(24, 0x2468AC),
        )
        self.assertTrue(result.mac_write)
        self.assertEqual(result.state.alternate.mr[0].value, 12)
        self.assertEqual(result.state.primary.mr[0], UNKNOWN)
        self.assertEqual(read_dreg(result.state.alternate, DREG.MX0), UNKNOWN)
        self.assertEqual(read_dreg(result.state.alternate, DREG.MY0).value, 0x2468)
        self.assertEqual(result.state.px.value, 0xAC)
        self.assertFalse(result.dm_dreg_write_known)
        self.assertTrue(result.pm_dreg_write_known)

    def test_unknown_compute_invalidates_result_but_known_loads_commit(self) -> None:
        state = ComputeDualState.reset()
        state = self._setup_dag(
            state,
            i_address=0,
            m_address=0,
            i_value=0x10,
            m_value=1,
        )
        state = self._setup_dag(
            state,
            i_address=4,
            m_address=4,
            i_value=0x20,
            m_value=1,
        )
        state = apply_compute_dual_cycle(
            state,
            setup_dreg=DREGWrite(DREG.AR, ExactWord(16, 0x5555)),
        ).state
        state = apply_compute_dual_cycle(
            state,
            setup_astat=ExactWord(8, 0xFF),
        ).state
        result = apply_compute_dual_cycle(
            state,
            execute=True,
            opcode=_opcode(amf=0x13),
            transaction_complete=True,
            dm_read_data=ExactWord(16, 0x1111),
            pm_read_data=ExactWord(24, 0x222233),
        )
        self.assertFalse(result.compute_result_known)
        self.assertEqual(read_dreg(result.state.primary, DREG.AR), UNKNOWN)
        self.assertEqual(read_dreg(result.state.primary, DREG.AX0).value, 0x1111)
        self.assertEqual(read_dreg(result.state.primary, DREG.AY0).value, 0x2222)
        for bit in (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV, ASTATBit.AC):
            self.assertEqual(result.state.status.astat.bit(bit), UNKNOWN)

    def test_reset_invalid_and_setup_conflicts_fail_closed(self) -> None:
        state = ComputeDualState.reset()
        invalid = apply_compute_dual_cycle(state, execute=True, opcode=0)
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_compute_dual_cycle(
            state,
            execute=True,
            opcode=_opcode(),
            setup_px=ExactWord(8, 0x12),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        reset = apply_compute_dual_cycle(
            state,
            reset=True,
            execute=True,
            opcode=_opcode(),
            transaction_complete=True,
        )
        self.assertFalse(reset.transaction_active)
        self.assertIsNone(reset.state.pending)
        self.assertEqual(reset.state.status.mstat.value, 0)
        self.assertEqual(reset.state.px, UNKNOWN)
        with self.assertRaises(ValueError):
            apply_compute_dual_cycle(state, dm_read_data=ExactWord(15, 0))
        with self.assertRaises(ValueError):
            apply_compute_dual_cycle(state, pm_read_data=ExactWord(23, 0))


if __name__ == "__main__":
    unittest.main()
