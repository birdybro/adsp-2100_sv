from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    COMPUTE_DUAL_CLASS_MASK,
    COMPUTE_DUAL_CLASS_VALUE,
    DREG,
    decode_compute_dual,
    is_compute_dual_class,
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
        self.assertEqual(data["decode"]["original_type"], 1)
        self.assertEqual(data["decode"]["class_words"], 4_194_304)
        self.assertEqual(data["decode"]["source_closed_words"], 4_194_304)
        self.assertEqual(data["decode"]["unsupported_words"], 0)
        self.assertEqual(
            data["parallel_actions"]["memory_directions"],
            "DM_READ_AND_PM_READ_ONLY",
        )
        self.assertIn(
            "OQ_023_NATIVE_PM_BEHAVIOR_DURING_DMACK_EXTENSION",
            data["unresolved"],
        )

    def test_nonclass_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x7FFFFF, 0x800000, 0xBFFFFF):
            self.assertFalse(is_compute_dual_class(opcode))
            self.assertIsNone(decode_compute_dual(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_compute_dual(opcode)


if __name__ == "__main__":
    unittest.main()
