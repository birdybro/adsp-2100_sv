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
        self.assertEqual(
            assemble_statement(" ena sec_reg,  dis bit_rev ;").value,
            0x0C00B0,
        )

    def test_mode_control_aliases_preserve_binary_round_trip(self) -> None:
        for opcode in (0x0C0000, 0x0C0010, 0x0C0550, 0x0C0DF0):
            disassembly = disassemble_word(opcode)
            self.assertTrue(disassembly.implemented)
            self.assertEqual(disassembly.classification, "TYPE_18")
            self.assertTrue(disassembly.text.startswith(".WORD"))
            self.assertEqual(assemble_statement(disassembly.text).value, opcode)

    def test_mode_control_rejects_duplicate_or_later_targets(self) -> None:
        with self.assertRaises(AssemblyError):
            assemble_statement("ENA SEC_REG, DIS SEC_REG;")
        with self.assertRaises(AssemblyError):
            assemble_statement("ENA TIMER;")
        with self.assertRaises(AssemblyError):
            assemble_statement(".WORD 0x1000000;")

    def test_all_modify_selections_round_trip(self) -> None:
        for dag in range(2):
            for i_local in range(4):
                for m_local in range(4):
                    i_address = dag * 4 + i_local
                    m_address = dag * 4 + m_local
                    source = f"MODIFY (I{i_address}, M{m_address});"
                    opcode = (
                        0x090000
                        | (dag << 4)
                        | (i_local << 2)
                        | m_local
                    )
                    self.assertEqual(
                        assemble_statement(source).value,
                        opcode,
                    )
                    self.assertEqual(
                        disassemble_word(opcode).text,
                        source,
                    )

    def test_modify_rejects_cross_dag_or_out_of_range_registers(self) -> None:
        with self.assertRaises(AssemblyError):
            assemble_statement("MODIFY (I3, M4);")
        with self.assertRaises(AssemblyError):
            assemble_statement("MODIFY (I4, M3);")
        with self.assertRaises(AssemblyError):
            assemble_statement("MODIFY (I8, M0);")

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
