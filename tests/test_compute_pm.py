from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    COMPUTE_PM_CLASS_MASK,
    COMPUTE_PM_CLASS_VALUE,
    DREG,
    compute_pm_unsupported_reason,
    decode_compute_pm,
    is_compute_pm_class,
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
        self.assertIn("PM_CACHE_AND_RECOVERY_EXECUTION", data["unresolved"])

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x4FFFFF, 0x600000, 0xFFFFFF):
            self.assertFalse(is_compute_pm_class(opcode))
            self.assertIsNone(decode_compute_pm(opcode))
            self.assertIsNone(compute_pm_unsupported_reason(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_compute_pm(opcode)


if __name__ == "__main__":
    unittest.main()
