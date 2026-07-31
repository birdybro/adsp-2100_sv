from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.assembler.adsp2100_assembler import AssemblyError, assemble_statement
from tools.disassembler.adsp2100_disassembler import disassemble_word


ROOT = Path(__file__).resolve().parents[1]


class AssemblerDisassemblerTests(unittest.TestCase):
    def test_independent_hand_fixture_round_trip(self) -> None:
        fixture_data = json.loads(
            (ROOT / "tests/vectors/opcode_fixtures.json").read_text(encoding="utf-8")
        )
        for fixture in fixture_data["fixtures"]:
            assembled = assemble_statement(fixture["source"])
            self.assertEqual(assembled.value, int(fixture["opcode"], 16))
            self.assertEqual(
                assembled.to_bytes().hex(),
                fixture["program_word_bytes_big_endian"],
            )
            disassembly = disassemble_word(assembled.value)
            self.assertTrue(disassembly.implemented)
            self.assertEqual(disassembly.text, fixture["source"])
            self.assertEqual(assemble_statement(disassembly.text), assembled)

    def test_normalization_is_deterministic(self) -> None:
        self.assertEqual(assemble_statement("  nop ; // comment").value, 0)
        self.assertEqual(assemble_statement("NOP").value, 0)

    def test_unsupported_assembly_fails_closed(self) -> None:
        with self.assertRaises(AssemblyError):
            assemble_statement("IDLE;")
        with self.assertRaises(AssemblyError):
            assemble_statement("AR = AX0 + AY0;")

    def test_original_reserved_bytes_are_not_disassembled_as_later_features(self) -> None:
        result = disassemble_word(0x010000)
        self.assertFalse(result.implemented)
        self.assertEqual(result.classification, "RESERVED_TYPE_29")
        self.assertEqual(result.text, ".WORD 0x010000;")

    def test_unshown_reserved_and_unimplemented_legal_class_are_distinct(self) -> None:
        self.assertEqual(
            disassemble_word(0x0B0020).classification,
            "RESERVED_UNSHOWN",
        )
        self.assertEqual(
            disassemble_word(0x400000).classification,
            "UNIMPLEMENTED_TYPE_06",
        )


if __name__ == "__main__":
    unittest.main()
