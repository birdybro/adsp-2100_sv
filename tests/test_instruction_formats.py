from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.generators.validate_instruction_formats import (
    InstructionFormatValidationError,
    extract_fields,
    load_database as load_format_database,
    validate_database as validate_format_database,
)
from tools.generators.validate_isa import (
    classify_opcode,
    load_database as load_isa_database,
)


ROOT = Path(__file__).resolve().parents[1]


class InstructionFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.formats = load_format_database()
        cls.isa = load_isa_database()
        cls.classes = {
            item["original_type"]: item
            for item in cls.isa["encoding_classes"]
        }

    def test_all_original_formats_validate(self) -> None:
        validate_format_database(self.formats)
        self.assertEqual(
            self.isa["instruction_format_database"],
            "docs/generated/adsp2100_instruction_formats.yaml",
        )

    def test_every_field_position_matches_independent_visual_fixture(
        self,
    ) -> None:
        fixture = json.loads(
            (
                ROOT
                / "tests/vectors/instruction_format_fixtures.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("ADI-UM-1989", fixture["source"])
        actual = {
            str(record["original_type"]): [
                [field["id"], field["msb"], field["lsb"]]
                for field in record["fields"]
            ]
            for record in self.formats["formats"]
        }
        self.assertEqual(actual, fixture["formats"])

    def test_variable_and_fixed_bits_match_classification_masks(self) -> None:
        for original_type, encoding_class in self.classes.items():
            base = int(encoding_class["opcode_value"], 16)
            fixed_mask = int(encoding_class["opcode_mask"], 16)
            record = self.formats["formats"][original_type - 1]
            variable_mask = 0
            for field in record["fields"]:
                width = field["msb"] - field["lsb"] + 1
                variable_mask |= (
                    ((1 << width) - 1) << field["lsb"]
                )
            self.assertEqual(
                variable_mask,
                (~fixed_mask) & 0xFFFFFF,
                f"type {original_type}",
            )
            for bit in range(24):
                candidate = base ^ (1 << bit)
                matched_types = [
                    item["original_type"]
                    for item in classify_opcode(self.isa, candidate)
                ]
                if variable_mask & (1 << bit):
                    self.assertIn(
                        original_type,
                        matched_types,
                        f"type {original_type} variable bit {bit}",
                    )
                else:
                    self.assertNotIn(
                        original_type,
                        matched_types,
                        f"type {original_type} fixed bit {bit}",
                    )

    def test_field_extraction_uses_exact_inclusive_ranges(self) -> None:
        for record in self.formats["formats"]:
            original_type = record["original_type"]
            base = int(
                self.classes[original_type]["opcode_value"],
                16,
            )
            opcode = base
            expected: dict[str, int] = {}
            for field in record["fields"]:
                width = field["msb"] - field["lsb"] + 1
                value = (1 << width) - 1
                opcode |= value << field["lsb"]
                expected[field["id"]] = value
            self.assertEqual(
                extract_fields(self.formats, original_type, opcode),
                expected,
                f"type {original_type}",
            )
            self.assertEqual(
                [
                    item["original_type"]
                    for item in classify_opcode(self.isa, opcode)
                ],
                [original_type],
            )

    def test_type_26_pc_pop_bit_is_not_reserved(self) -> None:
        for opcode in (0x040010, 0x04001F):
            self.assertEqual(
                [
                    item["original_type"]
                    for item in classify_opcode(self.isa, opcode)
                ],
                [26],
            )
        self.assertEqual(
            extract_fields(self.formats, 26, 0x04001F),
            {"PP": 1, "LP": 1, "CP": 1, "SPP": 3},
        )
        self.assertEqual(classify_opcode(self.isa, 0x040020), [])

    def test_corrected_shown_encoding_count_is_stable(self) -> None:
        shown = sum(
            1 << (
                24
                - int(item["opcode_mask"], 16).bit_count()
            )
            for item in self.isa["encoding_classes"]
        )
        self.assertEqual(shown, 15_473_178)
        self.assertEqual((1 << 24) - shown, 1_304_038)

    def test_gap_overlap_and_table_width_corruption_fail_closed(self) -> None:
        gap = copy.deepcopy(self.formats)
        gap["formats"][25]["fields"].pop()
        with self.assertRaises(InstructionFormatValidationError):
            validate_format_database(gap)

        overlap = copy.deepcopy(self.formats)
        overlap["formats"][25]["fields"][1]["msb"] = 4
        with self.assertRaises(InstructionFormatValidationError):
            validate_format_database(overlap)

        wrong_table = copy.deepcopy(self.formats)
        wrong_table["formats"][25]["fields"][0][
            "code_table"
        ] = "ISA_FIELDS:SPP"
        with self.assertRaises(InstructionFormatValidationError):
            validate_format_database(wrong_table)


if __name__ == "__main__":
    unittest.main()
