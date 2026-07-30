from __future__ import annotations

import copy
import unittest

from tools.generators.validate_isa import (
    ISAValidationError,
    classify_opcode,
    decode_classification,
    load_database,
    validate_database,
)


class ISADatabaseTests(unittest.TestCase):
    def test_seed_database_is_valid_and_explicitly_partial(self) -> None:
        database = load_database()
        validate_database(database)
        self.assertFalse(database["completeness_claim"])
        self.assertEqual(database["status"], "PARTIAL_RESEARCH_SEED")

    def test_original_encoding_classes_are_all_listed(self) -> None:
        database = load_database()
        self.assertEqual(
            [entry["original_type"] for entry in database["encoding_classes"]],
            list(range(1, 31)),
        )
        self.assertTrue(
            all(
                entry["status"] not in {"MASK_UNVERIFIED", "RESERVED_MASK_UNVERIFIED"}
                for entry in database["encoding_classes"]
            )
        )

    def test_representative_class_boundaries_decode_uniquely(self) -> None:
        database = load_database()
        fixtures = {
            0xC00000: 1,
            0xFFFFFF: 1,
            0xA00000: 2,
            0x800000: 3,
            0x600000: 4,
            0x500000: 5,
            0x400000: 6,
            0x300000: 7,
            0x280000: 8,
            0x200000: 9,
            0x180000: 10,
            0x140000: 11,
            0x120000: 12,
            0x110000: 13,
            0x100000: 14,
            0x0F0000: 15,
            0x0E0000: 16,
            0x0D0000: 17,
            0x0C0000: 18,
            0x0B0000: 19,
            0x0A0000: 20,
            0x090000: 21,
            0x080000: 22,
            0x071000: 23,
            0x060000: 24,
            0x050000: 25,
            0x040000: 26,
            0x030000: 27,
            0x020000: 28,
            0x010000: 29,
            0x000000: 30,
        }
        for opcode, expected_type in fixtures.items():
            matches = classify_opcode(database, opcode)
            self.assertEqual(
                [entry["original_type"] for entry in matches],
                [expected_type],
                f"opcode 0x{opcode:06x}",
            )

    def test_original_reserved_top_bytes_do_not_decode_as_later_features(self) -> None:
        database = load_database()
        for opcode, expected_type in (
            (0x010000, 29),
            (0x020000, 28),
            (0x030000, 27),
            (0x03FFFF, 27),
        ):
            matches = classify_opcode(database, opcode)
            self.assertEqual(matches[0]["name"], "reserved")
            self.assertEqual(matches[0]["original_type"], expected_type)

    def test_unshown_special_opcodes_remain_unclassified(self) -> None:
        database = load_database()
        for opcode in (0x0C0001, 0x0B0020, 0x000001):
            self.assertEqual(classify_opcode(database, opcode), [])
            self.assertEqual(decode_classification(database, opcode), "RESERVED_UNSHOWN")
        self.assertEqual(
            database["unshown_encoding_policy"]["architectural_behavior"],
            "UNDOCUMENTED",
        )

    def test_hand_verified_nop_is_exactly_all_zero(self) -> None:
        database = load_database()
        nop = next(item for item in database["instructions"] if item["id"] == "NOP-000000")
        self.assertEqual(nop["encoding_pattern"], "0" * 24)
        self.assertEqual(nop["opcode_mask"], "0xffffff")
        self.assertEqual(nop["opcode_value"], "0x000000")
        self.assertEqual(nop["confidence"], "VERIFIED_PRIMARY")

    def test_missing_required_semantic_field_is_rejected(self) -> None:
        database = copy.deepcopy(load_database())
        del database["instructions"][0]["old_value_new_value_semantics"]
        with self.assertRaises(ISAValidationError):
            validate_database(database)

    def test_class_overlap_is_rejected(self) -> None:
        database = copy.deepcopy(load_database())
        database["encoding_classes"][29]["opcode_mask"] = "0xff0000"
        database["encoding_classes"][29]["opcode_value"] = "0x010000"
        database["encoding_classes"][29]["encoding_pattern"] = "00000001xxxxxxxxxxxxxxxx"
        with self.assertRaises(ISAValidationError):
            validate_database(database)


if __name__ == "__main__":
    unittest.main()
