import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    DM_WRITE_IMMEDIATE_VALUE,
    decode_dm_write_immediate,
)


ROOT = Path(__file__).resolve().parents[1]


class DMWriteImmediateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(
            (ROOT / "docs/generated/adsp2100_dm_write_immediate.yaml").read_text(
                encoding="utf-8"
            )
        )
        cls.fixtures = json.loads(
            (ROOT / "tests/vectors/dm_write_immediate_fixtures.json").read_text(
                encoding="utf-8"
            )
        )

    def test_machine_readable_contract_is_original_type_2(self):
        instruction = self.contract["instruction"]
        self.assertEqual(self.contract["device"], "ADSP-2100")
        self.assertEqual(instruction["original_type"], 2)
        self.assertEqual(instruction["opcode_mask"], "0xe00000")
        self.assertEqual(instruction["opcode_value"], "0xa00000")
        self.assertEqual(instruction["field_defined_encoding_count"], 1 << 21)
        self.assertEqual(
            self.contract["implementation_boundary"]["execution"],
            "BOUNDED_LOGICAL_DMACK_TRANSACTION",
        )

    def test_hand_derived_fixtures(self):
        for fixture in self.fixtures["hand_checked_cases"]:
            action = decode_dm_write_immediate(int(fixture["opcode"], 16))
            self.assertIsNotNone(action)
            assert action is not None
            self.assertEqual(action.immediate, int(fixture["data"], 16))
            self.assertEqual(action.dag, fixture["dag"])
            self.assertEqual(action.i_address, fixture["i"])
            self.assertEqual(action.m_address, fixture["m"])
            self.assertEqual(action.l_address, fixture["i"])

    def test_every_field_combination_decodes(self):
        count = 0
        for dag in range(2):
            for data in (0, 1, 0x7FFF, 0x8000, 0xFFFF):
                for i_local in range(4):
                    for m_local in range(4):
                        opcode = (
                            DM_WRITE_IMMEDIATE_VALUE
                            | (dag << 20)
                            | (data << 4)
                            | (i_local << 2)
                            | m_local
                        )
                        action = decode_dm_write_immediate(opcode)
                        self.assertIsNotNone(action)
                        assert action is not None
                        self.assertEqual(action.immediate, data)
                        self.assertEqual(action.i_address, dag * 4 + i_local)
                        self.assertEqual(action.m_address, dag * 4 + m_local)
                        count += 1
        self.assertEqual(count, 160)

    def test_class_boundaries_and_other_types_fail_closed(self):
        for opcode in (0, 0x9FFFFF, 0xC00000, 0xFFFFFF):
            self.assertIsNone(decode_dm_write_immediate(opcode))
        self.assertIsNotNone(decode_dm_write_immediate(0xA00000))
        self.assertIsNotNone(decode_dm_write_immediate(0xBFFFFF))

    def test_width_errors_are_rejected(self):
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_dm_write_immediate(opcode)

    def test_raw_immediate_has_no_signedness_conversion(self):
        action = decode_dm_write_immediate(0xB80000)
        self.assertIsNotNone(action)
        assert action is not None
        self.assertEqual(action.immediate, 0x8000)


if __name__ == "__main__":
    unittest.main()
