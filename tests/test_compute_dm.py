from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    COMPUTE_DM_CLASS_MASK,
    COMPUTE_DM_CLASS_VALUE,
    ComputeDMState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_compute_dm_cycle,
    compute_dm_unsupported_reason,
    decode_compute_dm,
    is_compute_dm_class,
    read_dreg,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/vectors/compute_dm_fixtures.json"


def _opcode(
    *,
    dag: int = 0,
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
        0x600000
        | (dag << 20)
        | (int(write) << 19)
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (int(dreg) << 4)
        | (i << 2)
        | m
    )


class ComputeDMTests(unittest.TestCase):
    def _initialized_dag(
        self,
        state: ComputeDMState,
        *,
        i_address: int,
        m_address: int,
        i_value: int,
        m_value: int,
        l_value: int = 0,
    ) -> ComputeDMState:
        for setup in (
            DAGRegisterSetup(DAGRegisterKind.I, i_address, i_value),
            DAGRegisterSetup(DAGRegisterKind.M, m_address, m_value),
            DAGRegisterSetup(DAGRegisterKind.L, i_address, l_value),
        ):
            state = apply_compute_dm_cycle(state, setup_dag=setup).state
        return state

    def test_complete_type_4_partition_and_fields(self) -> None:
        supported = 0
        collision = 0
        for payload in range(1 << 21):
            opcode = 0x600000 | payload
            self.assertTrue(is_compute_dm_class(opcode))
            action = decode_compute_dm(opcode)
            reason = compute_dm_unsupported_reason(opcode)
            if action is None:
                self.assertEqual(reason, "UNSUPPORTED_DESTINATION_COLLISION")
                collision += 1
                continue
            self.assertIsNone(reason)
            self.assertEqual(action.dag, (payload >> 20) & 1)
            self.assertEqual(action.write, bool((payload >> 19) & 1))
            self.assertEqual(action.z, (payload >> 18) & 1)
            self.assertEqual(action.amf, (payload >> 13) & 0x1F)
            self.assertEqual(action.yop, (payload >> 11) & 3)
            self.assertEqual(action.xop, (payload >> 8) & 7)
            self.assertEqual(action.memory_dreg, DREG((payload >> 4) & 0xF))
            self.assertEqual(
                action.i_address,
                ((payload >> 20) & 1) * 4 + ((payload >> 2) & 3),
            )
            self.assertEqual(
                action.m_address,
                ((payload >> 20) & 1) * 4 + (payload & 3),
            )
            supported += 1
        self.assertEqual(COMPUTE_DM_CLASS_MASK, 0xE00000)
        self.assertEqual(COMPUTE_DM_CLASS_VALUE, 0x600000)
        self.assertEqual(supported, 2_034_688)
        self.assertEqual(collision, 62_464)

    def test_hand_transcribed_examples(self) -> None:
        data = json.loads(FIXTURES.read_text(encoding="utf-8"))
        self.assertEqual(data["device"], "ADSP-2100")
        self.assertIn("not assembler-generated", data["derivation"])
        for fixture in data["fixtures"]:
            opcode = int(fixture["opcode"], 16)
            action = decode_compute_dm(opcode)
            self.assertIsNotNone(action, fixture["id"])
            assert action is not None
            fields = fixture["fields"]
            self.assertEqual(action.dag, fields["G"])
            self.assertEqual(action.write, bool(fields["D"]))
            self.assertEqual(action.z, fields["Z"])
            self.assertEqual(action.amf, fields["AMF"])
            self.assertEqual(action.yop, fields["YOP"])
            self.assertEqual(action.xop, fields["XOP"])
            self.assertEqual(int(action.memory_dreg), fields["DREG"])
            self.assertEqual(action.i_local, fields["I"])
            self.assertEqual(action.m_local, fields["M"])

    def test_memory_only_amf_zero_ignores_compute_fields(self) -> None:
        for dag in range(2):
            for write in (False, True):
                for z in range(2):
                    for yop in range(4):
                        for xop in range(8):
                            action = decode_compute_dm(
                                _opcode(
                                    dag=dag,
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

    def test_read_collisions_rejected_and_same_writes_legal(self) -> None:
        cases = (
            (0x13, DREG.AR),
            (0x08, DREG.MR0),
            (0x08, DREG.MR1),
            (0x08, DREG.MR2),
        )
        for amf, dreg in cases:
            read = _opcode(amf=amf, dreg=dreg)
            self.assertIsNone(decode_compute_dm(read))
            self.assertEqual(
                compute_dm_unsupported_reason(read),
                "UNSUPPORTED_DESTINATION_COLLISION",
            )
            self.assertIsNotNone(
                decode_compute_dm(_opcode(write=True, amf=amf, dreg=dreg))
            )
            self.assertIsNotNone(
                decode_compute_dm(_opcode(z=1, amf=amf, dreg=dreg))
            )

    def test_operand_and_same_dag_mapping(self) -> None:
        alu = decode_compute_dm(_opcode(amf=0x13, xop=1, yop=1))
        mac = decode_compute_dm(
            _opcode(dag=1, amf=0x08, xop=1, yop=1, i=2, m=3)
        )
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
            action = decode_compute_dm(_opcode(amf=0x13, yop=yop))
            self.assertIsNotNone(action)
            assert action is not None
            self.assertIsNone(action.y_source)

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x5FFFFF, 0x800000, 0xFFFFFF):
            self.assertFalse(is_compute_dm_class(opcode))
            self.assertIsNone(decode_compute_dm(opcode))
            self.assertIsNone(compute_dm_unsupported_reason(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_compute_dm(opcode)

    def test_waited_write_holds_old_dreg_and_commits_compute_and_i(self) -> None:
        state = ComputeDMState.reset()
        state = self._initialized_dag(
            state,
            i_address=0,
            m_address=0,
            i_value=0x120,
            m_value=1,
        )
        for destination, value in (
            (DREG.AX0, 2),
            (DREG.AY0, 3),
            (DREG.AR, 0x7777),
        ):
            state = apply_compute_dm_cycle(
                state,
                setup_dreg=DREGWrite(destination, ExactWord(16, value)),
            ).state
        state = apply_compute_dm_cycle(
            state,
            setup_astat=ExactWord(8, 0xA0),
        ).state

        opcode = 0x6A60A0
        issued = apply_compute_dm_cycle(
            state,
            execute=True,
            opcode=opcode,
            dm_ack=False,
        )
        self.assertTrue(issued.accepted)
        self.assertTrue(issued.stalled)
        self.assertEqual(issued.dm_address, 0x120)
        self.assertEqual(issued.dm_write_data, 0x7777)
        self.assertEqual(read_dreg(issued.state.primary, DREG.AR).value, 0x7777)
        self.assertEqual(issued.state.dag.i[0], 0x120)

        held = apply_compute_dm_cycle(
            issued.state,
            execute=True,
            opcode=0,
            dm_ack=False,
            setup_dreg=DREGWrite(DREG.AR, ExactWord(16, 0x9999)),
        )
        self.assertTrue(held.integration_conflict)
        self.assertEqual(held.dm_address, 0x120)
        self.assertEqual(held.dm_write_data, 0x7777)
        self.assertEqual(read_dreg(held.state.primary, DREG.AR).value, 0x7777)

        completed = apply_compute_dm_cycle(held.state, dm_ack=True)
        self.assertTrue(completed.instruction_complete)
        self.assertTrue(completed.alu_write)
        self.assertFalse(completed.dreg_write)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AR).value, 5)
        self.assertEqual(completed.state.dag.i[0], 0x121)
        self.assertFalse(completed.state.status.astat.bit(ASTATBit.AZ))

    def test_compute_plus_read_uses_old_operand_then_loads_dreg(self) -> None:
        state = ComputeDMState.reset()
        state = self._initialized_dag(
            state,
            i_address=0,
            m_address=3,
            i_value=0x80,
            m_value=0x3FFF,
        )
        for destination, value in ((DREG.AX0, 2), (DREG.AY0, 3)):
            state = apply_compute_dm_cycle(
                state,
                setup_dreg=DREGWrite(destination, ExactWord(16, value)),
            ).state
        state = apply_compute_dm_cycle(
            state,
            setup_astat=ExactWord(8, 0),
        ).state

        completed = apply_compute_dm_cycle(
            state,
            execute=True,
            opcode=0x626003,
            dm_ack=True,
            dm_read_data=ExactWord(16, 0xCAFE),
        )
        self.assertTrue(completed.instruction_complete)
        self.assertTrue(completed.alu_write)
        self.assertTrue(completed.dreg_write)
        self.assertTrue(completed.dreg_write_known)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AR).value, 5)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AX0).value, 0xCAFE)
        self.assertEqual(completed.state.dag.i[0], 0x7F)

    def test_memory_only_alias_and_dag1_bit_reverse(self) -> None:
        state = ComputeDMState.reset()
        state = self._initialized_dag(
            state,
            i_address=2,
            m_address=1,
            i_value=1,
            m_value=1,
        )
        state = apply_compute_dm_cycle(
            state,
            setup_mstat=ExactWord(4, 0x2),
        ).state
        opcode = _opcode(
            z=1,
            yop=3,
            xop=7,
            dreg=DREG.SI,
            i=2,
            m=1,
        )
        issued = apply_compute_dm_cycle(
            state,
            execute=True,
            opcode=opcode,
            dm_ack=False,
        )
        self.assertFalse(issued.action.computation_enabled)
        self.assertFalse(issued.compute_result_known)
        self.assertEqual(issued.dm_address, 0x2000)
        completed = apply_compute_dm_cycle(
            issued.state,
            dm_ack=True,
            dm_read_data=ExactWord(16, 0x1357),
        )
        self.assertFalse(completed.alu_write)
        self.assertFalse(completed.mac_write)
        self.assertEqual(read_dreg(completed.state.primary, DREG.SI).value, 0x1357)
        self.assertEqual(completed.state.dag.i[2], 2)

    def test_alternate_bank_mac_and_primary_bank_preservation(self) -> None:
        state = ComputeDMState.reset()
        state = self._initialized_dag(
            state,
            i_address=4,
            m_address=4,
            i_value=0x200,
            m_value=2,
        )
        state = apply_compute_dm_cycle(
            state,
            setup_dreg=DREGWrite(DREG.MX0, ExactWord(16, 2)),
        ).state
        state = apply_compute_dm_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        for destination, value in ((DREG.MX0, 2), (DREG.MY0, 3)):
            state = apply_compute_dm_cycle(
                state,
                setup_dreg=DREGWrite(destination, ExactWord(16, value)),
            ).state
        state = apply_compute_dm_cycle(
            state,
            setup_astat=ExactWord(8, 0),
        ).state
        opcode = _opcode(
            dag=1,
            write=True,
            amf=4,
            dreg=DREG.MX0,
        )
        completed = apply_compute_dm_cycle(
            state,
            execute=True,
            opcode=opcode,
            dm_ack=True,
        )
        self.assertTrue(completed.mac_write)
        self.assertEqual(completed.dm_write_data, 2)
        self.assertEqual(completed.state.alternate.mr[0].value, 12)
        self.assertEqual(completed.state.primary.mr[0], UNKNOWN)
        self.assertEqual(completed.state.dag.i[4], 0x202)

    def test_unknown_inputs_invalidate_only_acknowledged_destinations(self) -> None:
        state = ComputeDMState.reset()
        state = self._initialized_dag(
            state,
            i_address=0,
            m_address=0,
            i_value=0x20,
            m_value=1,
        )
        state = apply_compute_dm_cycle(
            state,
            setup_dreg=DREGWrite(DREG.AR, ExactWord(16, 0x1234)),
        ).state
        state = apply_compute_dm_cycle(
            state,
            setup_astat=ExactWord(8, 0xFF),
        ).state
        opcode = _opcode(amf=0x13, dreg=DREG.AX0)
        issued = apply_compute_dm_cycle(
            state,
            execute=True,
            opcode=opcode,
            dm_ack=False,
        )
        self.assertEqual(read_dreg(issued.state.primary, DREG.AR).value, 0x1234)
        completed = apply_compute_dm_cycle(
            issued.state,
            dm_ack=True,
            dm_read_data=UNKNOWN,
        )
        self.assertEqual(read_dreg(completed.state.primary, DREG.AR), UNKNOWN)
        self.assertEqual(read_dreg(completed.state.primary, DREG.AX0), UNKNOWN)
        for bit in (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV, ASTATBit.AC):
            self.assertEqual(completed.state.status.astat.bit(bit), UNKNOWN)
        self.assertEqual(completed.state.dag.i[0], 0x21)

    def test_reset_invalid_and_setup_conflicts_fail_closed(self) -> None:
        state = ComputeDMState.reset()
        invalid = apply_compute_dm_cycle(state, execute=True, opcode=0)
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_compute_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(),
            setup_mstat=ExactWord(4, 1),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        inspect_conflict = apply_compute_dm_cycle(
            state,
            execute=True,
            opcode=_opcode(write=True),
            dm_ack=True,
            inspect_probe=True,
        )
        self.assertTrue(inspect_conflict.integration_conflict)
        self.assertFalse(inspect_conflict.accepted)
        self.assertFalse(inspect_conflict.transaction_active)
        self.assertEqual(inspect_conflict.state, state)
        reset = apply_compute_dm_cycle(
            state,
            reset=True,
            execute=True,
            opcode=_opcode(),
            dm_ack=True,
        )
        self.assertFalse(reset.transaction_active)
        self.assertIsNone(reset.state.pending)
        self.assertEqual(reset.state.status.mstat.value, 0)

        with self.assertRaises(ValueError):
            apply_compute_dm_cycle(state, setup_af=ExactWord(15, 0))
        with self.assertRaises(ValueError):
            apply_compute_dm_cycle(state, dm_read_data=ExactWord(15, 0))


if __name__ == "__main__":
    unittest.main()
