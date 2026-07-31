from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.assembler.adsp2100_assembler import AssemblyError, assemble_statement
from tools.disassembler.adsp2100_disassembler import disassemble_word
from tools.generators.validate_internal_move import register_map
from tools.generators.validate_condition_codes import EXPECTED_IF_MNEMONICS


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

    def test_all_conditional_shifter_forms_round_trip(self) -> None:
        xops = {0: "SI", 2: "AR", 3: "MR0", 4: "MR1", 5: "MR2", 6: "SR0", 7: "SR1"}
        count = 0
        for sf in range(16):
            for xop, source in xops.items():
                for condition, mnemonic in enumerate(EXPECTED_IF_MNEMONICS):
                    prefix = "" if condition == 15 else f"IF {mnemonic} "
                    if sf <= 0xB:
                        operation = ("LSHIFT", "ASHIFT", "NORM")[sf >> 2]
                        reference = "LO" if sf & 2 else "HI"
                        combine = "SR OR " if sf & 1 else ""
                        source_text = (
                            f"{prefix}SR = {combine}{operation} {source} "
                            f"({reference});"
                        )
                    elif sf <= 0xE:
                        reference = ("HI", "HIX", "LO")[sf - 0xC]
                        source_text = f"{prefix}SE = EXP {source} ({reference});"
                    else:
                        source_text = f"{prefix}SB = EXPADJ {source};"
                    opcode = 0x0E0000 | (sf << 11) | (xop << 8) | condition
                    assembled = assemble_statement(source_text)
                    self.assertEqual(assembled.value, opcode)
                    disassembled = disassemble_word(opcode)
                    self.assertTrue(disassembled.implemented)
                    self.assertEqual(disassembled.classification, "TYPE_16_BOUNDED_EXECUTION")
                    self.assertEqual(disassembled.text, source_text)
                    self.assertEqual(assemble_statement(disassembled.text), assembled)
                    count += 1
        self.assertEqual(count, 1_792)

    def test_conditional_shifter_rejects_unavailable_xop_and_bad_condition(self) -> None:
        unavailable = disassemble_word(0x0E010F)
        self.assertFalse(unavailable.implemented)
        self.assertEqual(unavailable.classification, "UNVERIFIED_TYPE_16_SUBENCODING")
        with self.assertRaises(AssemblyError):
            assemble_statement("IF MAYBE SR = LSHIFT SI (HI);")
        with self.assertRaises(AssemblyError):
            assemble_statement("SR = LSHIFT AX0 (HI);")

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

    def test_all_legal_internal_moves_round_trip(self) -> None:
        registers = register_map()
        readable = {
            code: metadata["register"]
            for code, metadata in registers.items()
        }
        writable = {
            code: name
            for code, name in readable.items()
            if name != "SSTAT"
        }
        count = 0
        for destination_code, destination in writable.items():
            for source_code, source in readable.items():
                statement = f"{destination} = {source};"
                opcode = (
                    0x0D0000
                    | ((destination_code >> 4) << 10)
                    | ((source_code >> 4) << 8)
                    | ((destination_code & 0xF) << 4)
                    | (source_code & 0xF)
                )
                assembled = assemble_statement(statement)
                self.assertEqual(assembled.value, opcode)
                disassembly = disassemble_word(opcode)
                self.assertTrue(disassembly.implemented)
                self.assertEqual(
                    disassembly.classification,
                    "TYPE_17_BOUNDED_EXECUTION",
                )
                self.assertEqual(disassembly.text, statement)
                count += 1
        self.assertEqual(count, 2256)

    def test_internal_move_rejects_reserved_and_read_only_destinations(
        self,
    ) -> None:
        with self.assertRaises(AssemblyError):
            assemble_statement("SSTAT = AX0;")
        with self.assertRaises(AssemblyError):
            assemble_statement("AX0 = AF;")
        reserved = disassemble_word(0x0D04C0)
        self.assertFalse(reserved.implemented)
        self.assertEqual(
            reserved.classification,
            "RESERVED_TYPE_17_SUBENCODING",
        )
        self.assertEqual(reserved.text, ".WORD 0x0d04c0;")

    def test_modify_rejects_cross_dag_or_out_of_range_registers(self) -> None:
        with self.assertRaises(AssemblyError):
            assemble_statement("MODIFY (I3, M4);")
        with self.assertRaises(AssemblyError):
            assemble_statement("MODIFY (I4, M3);")
        with self.assertRaises(AssemblyError):
            assemble_statement("MODIFY (I8, M0);")

    def test_type_6_dreg_immediates_round_trip(self) -> None:
        names = [
            "AX0", "AX1", "MX0", "MX1", "AY0", "AY1", "MY0", "MY1",
            "SI", "SE", "AR", "MR0", "MR1", "MR2", "SR0", "SR1",
        ]
        for code, name in enumerate(names):
            for value in (0, 1, 0x7FFF, 0x8000, 0xFFFF):
                opcode = 0x400000 | (value << 4) | code
                assembled = assemble_statement(f"{name} = 0x{value:04x};")
                self.assertEqual(assembled.value, opcode)
                disassembly = disassemble_word(opcode)
                self.assertTrue(disassembly.implemented)
                self.assertEqual(disassembly.classification, "TYPE_06")
                self.assertEqual(assemble_statement(disassembly.text), assembled)
        self.assertEqual(assemble_statement("AX0 = -1;").value, 0x4FFFF0)
        with self.assertRaises(AssemblyError):
            assemble_statement("AX0 = 0x10000;")

    def test_all_verified_type_15_forms_round_trip(self) -> None:
        sources = {0: "SI", 2: "AR", 3: "MR0", 4: "MR1", 5: "MR2", 6: "SR0", 7: "SR1"}
        count = 0
        for sf in range(8):
            operation = "ASHIFT" if sf & 4 else "LSHIFT"
            reference = "LO" if sf & 2 else "HI"
            combine_or = "SR OR " if sf & 1 else ""
            for xop, source in sources.items():
                for exponent in (-128, -1, 0, 1, 127):
                    statement = (
                        f"SR = {combine_or}{operation} {source} BY "
                        f"{exponent} ({reference});"
                    )
                    opcode = (
                        0x0F0000
                        | (sf << 11)
                        | (xop << 8)
                        | (exponent & 0xFF)
                    )
                    self.assertEqual(assemble_statement(statement).value, opcode)
                    decoded = disassemble_word(opcode)
                    self.assertTrue(decoded.implemented)
                    self.assertEqual(
                        decoded.classification,
                        "TYPE_15_BOUNDED_EXECUTION",
                    )
                    self.assertEqual(decoded.text, statement)
                    count += 1
        self.assertEqual(count, 280)
        self.assertEqual(
            assemble_statement("SR = LSHIFT SI BY H#ff (HI);").value,
            0x0F00FF,
        )

    def test_unverified_type_15_subencodings_fail_closed(self) -> None:
        unavailable_xop = disassemble_word(0x0F0100)
        self.assertFalse(unavailable_xop.implemented)
        self.assertEqual(
            unavailable_xop.classification,
            "UNVERIFIED_TYPE_15_SUBENCODING",
        )
        non_immediate_sf = disassemble_word(0x0F4000)
        self.assertFalse(non_immediate_sf.implemented)
        with self.assertRaises(AssemblyError):
            assemble_statement("SR = LSHIFT SI BY 128 (HI);")

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
            disassemble_word(0x500001).classification,
            "UNIMPLEMENTED_TYPE_05",
        )


if __name__ == "__main__":
    unittest.main()
