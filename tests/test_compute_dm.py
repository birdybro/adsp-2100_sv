from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    COMPUTE_DM_CLASS_MASK,
    COMPUTE_DM_CLASS_VALUE,
    DREG,
    compute_dm_unsupported_reason,
    decode_compute_dm,
    is_compute_dm_class,
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


if __name__ == "__main__":
    unittest.main()
