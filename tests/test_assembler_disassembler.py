from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.assembler.adsp2100_assembler import (
    AssemblyError,
    _dreg_name_to_code,
    _format_compute_operation,
    assemble_statement,
)
from tools.disassembler.adsp2100_disassembler import disassemble_word
from tools.generators.validate_internal_move import register_map
from tools.generators.validate_load_non_dreg_immediate import (
    register_map as non_dreg_register_map,
)
from tools.generators.validate_condition_codes import EXPECTED_IF_MNEMONICS


ROOT = Path(__file__).resolve().parents[1]


class AssemblerDisassemblerTests(unittest.TestCase):
    def test_type_7_non_data_immediate_forms_round_trip(self) -> None:
        fixture_data = json.loads(
            (
                ROOT / "tests/vectors/load_non_dreg_immediate_fixtures.json"
            ).read_text(encoding="utf-8")
        )
        for fixture in fixture_data["hand_checked_cases"]:
            opcode = int(fixture["opcode"], 16)
            decoded = disassemble_word(opcode)
            if fixture["legal"]:
                self.assertEqual(
                    assemble_statement(fixture["statement"]).value,
                    opcode,
                )
                self.assertTrue(decoded.implemented)
                self.assertEqual(
                    decoded.classification,
                    "TYPE_07_BOUNDED_EXECUTION",
                )
                self.assertEqual(decoded.text, fixture["statement"])
            else:
                self.assertFalse(decoded.implemented)
                self.assertEqual(
                    decoded.classification,
                    f"UNSUPPORTED_TYPE_07_{fixture['invalid_reason']}",
                )

        count = 0
        for code, metadata in non_dreg_register_map().items():
            if code >> 4 == 0 or metadata["register"] == "SSTAT":
                continue
            for data in (0, 1, 0x1FFF, 0x2000, 0x3FFF):
                statement = f"{metadata['register']} = 0x{data:04x};"
                opcode = (
                    0x300000 | ((code >> 4) << 18)
                    | (data << 4) | (code & 0xF)
                )
                self.assertEqual(assemble_statement(statement).value, opcode)
                decoded = disassemble_word(opcode)
                self.assertTrue(decoded.implemented)
                self.assertEqual(decoded.text, statement)
                self.assertEqual(
                    assemble_statement(decoded.text).value,
                    opcode,
                )
                count += 1
        self.assertEqual(count, 155)
        self.assertEqual(assemble_statement("M0 = -1;").value, 0x37FFF4)
        with self.assertRaises(AssemblyError):
            assemble_statement("SSTAT = 0;")
        with self.assertRaises(AssemblyError):
            assemble_statement("I0 = 0x4000;")

    def test_type_3_direct_dm_forms_round_trip(self) -> None:
        fixture_data = json.loads(
            (ROOT / "tests/vectors/direct_dm_fixtures.json").read_text(
                encoding="utf-8"
            )
        )
        for fixture in fixture_data["hand_checked_cases"]:
            if not fixture["legal"]:
                continue
            opcode = int(fixture["opcode"], 16)
            statement = fixture["statement"]
            self.assertEqual(assemble_statement(statement).value, opcode)
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(decoded.classification, "TYPE_03_SOURCE_CLOSED_ACTION")
            self.assertEqual(decoded.text, statement)

        registers = register_map()
        count = 0
        for direction in range(2):
            for code, metadata in registers.items():
                name = metadata["register"]
                if not direction and name == "SSTAT":
                    continue
                for address in (0, 1, 0x1FFF, 0x2000, 0x3FFF):
                    memory = f"DM(0x{address:04x})"
                    statement = (
                        f"{memory} = {name};"
                        if direction else f"{name} = {memory};"
                    )
                    opcode = (
                        0x800000 | (direction << 20)
                        | ((code >> 4) << 18) | (address << 4) | (code & 0xF)
                    )
                    self.assertEqual(assemble_statement(statement).value, opcode)
                    decoded = disassemble_word(opcode)
                    self.assertEqual(decoded.text, statement)
                    self.assertEqual(decoded.classification, "TYPE_03_SOURCE_CLOSED_ACTION")
                    count += 1
        self.assertEqual(count, 475)

        with self.assertRaises(AssemblyError):
            assemble_statement("SSTAT = DM(0x0000);")
        with self.assertRaises(AssemblyError):
            assemble_statement("AX0 = DM(0x4000);")
        self.assertFalse(disassemble_word(0x8C0002).implemented)
        self.assertEqual(
            disassemble_word(0x8C0002).classification,
            "UNSUPPORTED_TYPE_03_READ_ONLY_SSTAT_DESTINATION",
        )

    def test_type_2_immediate_dm_write_forms_round_trip(self) -> None:
        count = 0
        for dag in range(2):
            for data in (0, 1, 0x7FFF, 0x8000, 0xFFFF):
                for i_local in range(4):
                    for m_local in range(4):
                        i_address = dag * 4 + i_local
                        m_address = dag * 4 + m_local
                        source = (
                            f"DM(I{i_address}, M{m_address}) = 0x{data:04x};"
                        )
                        opcode = (
                            0xA00000
                            | (dag << 20)
                            | (data << 4)
                            | (i_local << 2)
                            | m_local
                        )
                        assembled = assemble_statement(source)
                        self.assertEqual(assembled.value, opcode)
                        disassembled = disassemble_word(opcode)
                        self.assertTrue(disassembled.implemented)
                        self.assertEqual(
                            disassembled.classification,
                            "TYPE_02_ACTION_DECODE",
                        )
                        self.assertEqual(disassembled.text, source)
                        self.assertEqual(
                            assemble_statement(disassembled.text), assembled
                        )
                        count += 1
        self.assertEqual(count, 160)
        with self.assertRaises(AssemblyError):
            assemble_statement("DM(I0, M4) = 1;")

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

    def test_all_bounded_shift_move_forms_round_trip(self) -> None:
        xops = {0: "SI", 2: "AR", 3: "MR0", 4: "MR1", 5: "MR2", 6: "SR0", 7: "SR1"}
        dregs = [
            "AX0", "AX1", "MX0", "MX1", "AY0", "AY1", "MY0", "MY1",
            "SI", "SE", "AR", "MR0", "MR1", "MR2", "SR0", "SR1",
        ]
        count = 0
        for sf in range(16):
            for xop, shifter_source in xops.items():
                for destination, destination_name in enumerate(dregs):
                    if (sf <= 0xB and destination >= 14) or (
                        0xC <= sf <= 0xE and destination == 9
                    ):
                        continue
                    for move_source, move_source_name in enumerate(dregs):
                        if sf <= 0xB:
                            operation = ("LSHIFT", "ASHIFT", "NORM")[sf >> 2]
                            reference = "LO" if sf & 2 else "HI"
                            combine = "SR OR " if sf & 1 else ""
                            computation = (
                                f"SR = {combine}{operation} {shifter_source} "
                                f"({reference})"
                            )
                        elif sf <= 0xE:
                            reference = ("HI", "HIX", "LO")[sf - 0xC]
                            computation = f"SE = EXP {shifter_source} ({reference})"
                        else:
                            computation = f"SB = EXPADJ {shifter_source}"
                        statement = (
                            f"{computation}, {destination_name} = "
                            f"{move_source_name};"
                        )
                        opcode = (
                            0x100000
                            | (sf << 11)
                            | (xop << 8)
                            | (destination << 4)
                            | move_source
                        )
                        self.assertEqual(assemble_statement(statement).value, opcode)
                        decoded = disassemble_word(opcode)
                        self.assertTrue(decoded.implemented)
                        self.assertEqual(
                            decoded.classification,
                            "TYPE_14_BOUNDED_EXECUTION",
                        )
                        self.assertEqual(decoded.text, statement)
                        count += 1
        self.assertEqual(count, 25_648)

    def test_all_source_closed_shifter_dm_forms_round_trip(self) -> None:
        count = 0
        for payload in range(1 << 17):
            opcode = 0x120000 | payload
            decoded = disassemble_word(opcode)
            if not decoded.implemented:
                continue
            self.assertEqual(decoded.classification, "TYPE_12_BOUNDED_EXECUTION")
            self.assertEqual(assemble_statement(decoded.text).value, opcode)
            count += 1
        self.assertEqual(count, 108_640)

    def test_all_source_closed_shifter_pm_forms_round_trip(self) -> None:
        count = 0
        for payload in range(1 << 16):
            opcode = 0x110000 | payload
            decoded = disassemble_word(opcode)
            if not decoded.implemented:
                continue
            self.assertEqual(decoded.classification, "TYPE_13_BOUNDED_EXECUTION")
            self.assertEqual(assemble_statement(decoded.text).value, opcode)
            count += 1
        self.assertEqual(count, 54_320)

    def test_all_canonical_compute_operations_round_trip(self) -> None:
        from tools.assembler.adsp2100_assembler import _format_compute_operation

        dregs = [
            "AX0", "AX1", "MX0", "MX1", "AY0", "AY1", "MY0", "MY1",
            "SI", "SE", "AR", "MR0", "MR1", "MR2", "SR0", "SR1",
        ]
        count = 0
        for z in range(2):
            for amf in range(1, 32):
                for yop in range(4):
                    for xop in range(8):
                        computation = _format_compute_operation(z, amf, yop, xop)
                        if computation is None:
                            continue
                        for destination, destination_name in enumerate(dregs):
                            collision = not z and (
                                (amf >= 0x10 and destination == 0xA)
                                or (amf < 0x10 and destination in (0xB, 0xC, 0xD))
                            )
                            if collision:
                                continue
                            source = (z + amf + yop + xop + destination) & 0xF
                            statement = (
                                f"{computation}, {destination_name} = "
                                f"{dregs[source]};"
                            )
                            opcode = (
                                0x280000 | (z << 18) | (amf << 13)
                                | (yop << 11) | (xop << 8)
                                | (destination << 4) | source
                            )
                            self.assertEqual(assemble_statement(statement).value, opcode)
                            decoded = disassemble_word(opcode)
                            self.assertTrue(decoded.implemented)
                            self.assertEqual(
                                decoded.classification,
                                "TYPE_08_BOUNDED_EXECUTION",
                            )
                            self.assertEqual(decoded.text, statement)
                            count += 1
        self.assertEqual(count, 20_513)

    def test_type_4_hand_fixtures_and_memory_only_forms_round_trip(self) -> None:
        fixture_data = json.loads(
            (ROOT / "tests/vectors/compute_dm_fixtures.json").read_text(
                encoding="utf-8"
            )
        )
        for fixture in fixture_data["fixtures"]:
            opcode = int(fixture["opcode"], 16)
            self.assertEqual(
                assemble_statement(fixture["statement"]).value,
                opcode,
            )
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(decoded.classification, "TYPE_04_BOUNDED_ACTION")
            self.assertEqual(decoded.text, fixture["statement"])

        dregs = [
            name
            for name, _ in sorted(
                _dreg_name_to_code().items(),
                key=lambda item: item[1],
            )
        ]
        count = 0
        for dag in range(2):
            for i_local in range(4):
                for m_local in range(4):
                    i_address = dag * 4 + i_local
                    m_address = dag * 4 + m_local
                    memory = f"DM(I{i_address}, M{m_address})"
                    for register, name in enumerate(dregs):
                        for write in range(2):
                            statement = (
                                f"{memory} = {name};"
                                if write
                                else f"{name} = {memory};"
                            )
                            opcode = (
                                0x600000
                                | (dag << 20)
                                | (write << 19)
                                | (register << 4)
                                | (i_local << 2)
                                | m_local
                            )
                            self.assertEqual(
                                assemble_statement(statement).value,
                                opcode,
                            )
                            decoded = disassemble_word(opcode)
                            self.assertEqual(decoded.text, statement)
                            self.assertEqual(
                                decoded.classification,
                                "TYPE_04_BOUNDED_ACTION",
                            )
                            count += 1
        self.assertEqual(count, 1_024)

    def test_type_4_canonical_compute_forms_and_aliases(self) -> None:
        dregs = [
            name
            for name, _ in sorted(
                _dreg_name_to_code().items(),
                key=lambda item: item[1],
            )
        ]
        count = 0
        for z in range(2):
            for amf in range(1, 32):
                for yop in range(4):
                    for xop in range(8):
                        computation = _format_compute_operation(z, amf, yop, xop)
                        if computation is None:
                            continue
                        for write in range(2):
                            register = (z + amf + yop + xop + write) & 0xF
                            collision = not write and not z and (
                                (amf >= 0x10 and register == 0xA)
                                or (amf < 0x10 and register in (0xB, 0xC, 0xD))
                            )
                            if collision:
                                continue
                            memory = "DM(I4, M7)"
                            statement = (
                                f"{memory} = {dregs[register]}, {computation};"
                                if write
                                else f"{computation}, {dregs[register]} = {memory};"
                            )
                            opcode = (
                                0x700003
                                | (write << 19)
                                | (z << 18)
                                | (amf << 13)
                                | (yop << 11)
                                | (xop << 8)
                                | (register << 4)
                            )
                            self.assertEqual(
                                assemble_statement(statement).value,
                                opcode,
                            )
                            decoded = disassemble_word(opcode)
                            self.assertEqual(decoded.text, statement)
                            count += 1
        self.assertEqual(count, 2_649)

        aliases = (0x640100, 0x620100)
        for opcode in aliases:
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(decoded.classification, "TYPE_04_BOUNDED_ALIAS")
            self.assertEqual(assemble_statement(decoded.text).value, opcode)

        with self.assertRaises(AssemblyError):
            assemble_statement("AR = AX0 + AY0, AR = DM(I0, M0);")
        with self.assertRaises(AssemblyError):
            assemble_statement("AX0 = DM(I0, M4);")

    def test_type_1_hand_fixtures_and_dual_read_forms_round_trip(self) -> None:
        fixture_data = json.loads(
            (ROOT / "tests/vectors/compute_dual_fixtures.json").read_text(
                encoding="utf-8"
            )
        )
        for fixture in fixture_data["fixtures"]:
            opcode = int(fixture["opcode"], 16)
            self.assertEqual(
                assemble_statement(fixture["statement"]).value,
                opcode,
            )
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(
                decoded.classification,
                "TYPE_01_SOURCE_CLOSED_ACTION",
            )
            self.assertEqual(decoded.text, fixture["statement"])

        dm_names = ("AX0", "AX1", "MX0", "MX1")
        pm_names = ("AY0", "AY1", "MY0", "MY1")
        count = 0
        for pd, pm_name in enumerate(pm_names):
            for dd, dm_name in enumerate(dm_names):
                for pm_i in range(4):
                    for pm_m in range(4):
                        for dm_i in range(4):
                            dm_m = (pd + dd + pm_i + pm_m + dm_i) & 3
                            statement = (
                                f"{dm_name} = DM(I{dm_i}, M{dm_m}), "
                                f"{pm_name} = PM(I{4 + pm_i}, M{4 + pm_m});"
                            )
                            opcode = (
                                0xC00000
                                | (pd << 20)
                                | (dd << 18)
                                | (pm_i << 6)
                                | (pm_m << 4)
                                | (dm_i << 2)
                                | dm_m
                            )
                            self.assertEqual(
                                assemble_statement(statement).value,
                                opcode,
                            )
                            decoded = disassemble_word(opcode)
                            self.assertEqual(decoded.text, statement)
                            self.assertEqual(
                                decoded.classification,
                                "TYPE_01_SOURCE_CLOSED_ACTION",
                            )
                            count += 1
        self.assertEqual(count, 1_024)

        self.assertEqual(
            assemble_statement(
                "MR = 0, MY0 = PM(I4, M4), MX0 = DM(I0, M0);"
            ).value,
            0xE89800,
        )

    def test_type_1_canonical_compute_forms_and_aliases(self) -> None:
        count = 0
        for amf in range(1, 32):
            for yop in range(4):
                for xop in range(8):
                    computation = _format_compute_operation(0, amf, yop, xop)
                    if computation is None:
                        continue
                    pd = (amf + yop) & 3
                    dd = (amf + xop) & 3
                    pm_name = ("AY0", "AY1", "MY0", "MY1")[pd]
                    dm_name = ("AX0", "AX1", "MX0", "MX1")[dd]
                    statement = (
                        f"{computation}, {dm_name} = DM(I3, M2), "
                        f"{pm_name} = PM(I5, M7);"
                    )
                    opcode = (
                        0xC00000
                        | (pd << 20)
                        | (dd << 18)
                        | (amf << 13)
                        | (yop << 11)
                        | (xop << 8)
                        | (1 << 6)
                        | (3 << 4)
                        | (3 << 2)
                        | 2
                    )
                    self.assertEqual(assemble_statement(statement).value, opcode)
                    decoded = disassemble_word(opcode)
                    self.assertEqual(decoded.text, statement)
                    self.assertEqual(
                        decoded.classification,
                        "TYPE_01_SOURCE_CLOSED_ACTION",
                    )
                    count += 1
        self.assertEqual(count, 685)

        for opcode in (0xC00100, 0xC00800, 0xC01800):
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(
                decoded.classification,
                "TYPE_01_SOURCE_CLOSED_ALIAS",
            )
            self.assertEqual(assemble_statement(decoded.text).value, opcode)

        with self.assertRaises(AssemblyError):
            assemble_statement(
                "AF = AX0 + AY0, AX0 = DM(I0, M0), AY0 = PM(I4, M4);"
            )
        with self.assertRaises(AssemblyError):
            assemble_statement("AY0 = DM(I0, M0), AX0 = PM(I4, M4);")

    def test_type_5_hand_fixtures_and_memory_only_forms_round_trip(self) -> None:
        fixture_data = json.loads(
            (ROOT / "tests/vectors/compute_pm_fixtures.json").read_text(
                encoding="utf-8"
            )
        )
        for fixture in fixture_data["fixtures"]:
            opcode = int(fixture["opcode"], 16)
            self.assertEqual(
                assemble_statement(fixture["statement"]).value,
                opcode,
            )
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(decoded.classification, "TYPE_05_BOUNDED_ACTION")
            self.assertEqual(decoded.text, fixture["statement"])

        dregs = [
            name
            for name, _ in sorted(
                _dreg_name_to_code().items(),
                key=lambda item: item[1],
            )
        ]
        count = 0
        for i_local in range(4):
            for m_local in range(4):
                memory = f"PM(I{4 + i_local}, M{4 + m_local})"
                for register, name in enumerate(dregs):
                    for write in range(2):
                        statement = (
                            f"{memory} = {name};"
                            if write
                            else f"{name} = {memory};"
                        )
                        opcode = (
                            0x500000
                            | (write << 19)
                            | (register << 4)
                            | (i_local << 2)
                            | m_local
                        )
                        self.assertEqual(
                            assemble_statement(statement).value,
                            opcode,
                        )
                        decoded = disassemble_word(opcode)
                        self.assertEqual(decoded.text, statement)
                        self.assertEqual(
                            decoded.classification,
                            "TYPE_05_BOUNDED_ACTION",
                        )
                        count += 1
        self.assertEqual(count, 512)

    def test_type_5_canonical_compute_forms_and_aliases(self) -> None:
        dregs = [
            name
            for name, _ in sorted(
                _dreg_name_to_code().items(),
                key=lambda item: item[1],
            )
        ]
        count = 0
        for z in range(2):
            for amf in range(1, 32):
                for yop in range(4):
                    for xop in range(8):
                        computation = _format_compute_operation(z, amf, yop, xop)
                        if computation is None:
                            continue
                        for write in range(2):
                            register = (z + amf + yop + xop + write) & 0xF
                            collision = not write and not z and (
                                (amf >= 0x10 and register == 0xA)
                                or (amf < 0x10 and register in (0xB, 0xC, 0xD))
                            )
                            if collision:
                                continue
                            memory = "PM(I4, M7)"
                            statement = (
                                f"{memory} = {dregs[register]}, {computation};"
                                if write
                                else f"{computation}, {dregs[register]} = {memory};"
                            )
                            opcode = (
                                0x500003
                                | (write << 19)
                                | (z << 18)
                                | (amf << 13)
                                | (yop << 11)
                                | (xop << 8)
                                | (register << 4)
                            )
                            self.assertEqual(
                                assemble_statement(statement).value,
                                opcode,
                            )
                            decoded = disassemble_word(opcode)
                            self.assertEqual(decoded.text, statement)
                            count += 1
        self.assertEqual(count, 2_649)

        for opcode in (0x540100, 0x520100):
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(decoded.classification, "TYPE_05_BOUNDED_ALIAS")
            self.assertEqual(assemble_statement(decoded.text).value, opcode)

        with self.assertRaises(AssemblyError):
            assemble_statement("AR = AX0 + AY0, AR = PM(I4, M4);")
        self.assertFalse(disassemble_word(0x5260A0).implemented)
        self.assertEqual(
            disassemble_word(0x5260A0).classification,
            "UNSUPPORTED_TYPE_05_DESTINATION_COLLISION",
        )

    def test_all_canonical_conditional_compute_forms_round_trip(self) -> None:
        from tools.assembler.adsp2100_assembler import _format_compute_operation

        count = 0
        for z in range(2):
            for amf in range(1, 32):
                for yop in range(4):
                    for xop in range(8):
                        computation = _format_compute_operation(z, amf, yop, xop)
                        if computation is None:
                            continue
                        for condition, mnemonic in enumerate(EXPECTED_IF_MNEMONICS):
                            prefix = "" if condition == 15 else f"IF {mnemonic} "
                            statement = f"{prefix}{computation};"
                            opcode = (
                                0x200000 | (z << 18) | (amf << 13)
                                | (yop << 11) | (xop << 8) | condition
                            )
                            assembled = assemble_statement(statement)
                            self.assertEqual(assembled.value, opcode)
                            decoded = disassemble_word(opcode)
                            self.assertTrue(decoded.implemented)
                            self.assertEqual(
                                decoded.classification,
                                "TYPE_09_BOUNDED_EXECUTION",
                            )
                            self.assertEqual(decoded.text, statement)
                            self.assertEqual(assemble_statement(decoded.text), assembled)
                            count += 1
        self.assertEqual(count, 21_920)

    def test_conditional_compute_aliases_preserve_binary_round_trip(self) -> None:
        cases = {
            0x200000: "TYPE_09_BOUNDED_NOP_ALIAS",
            0x22010F: "TYPE_09_BOUNDED_ALIAS",
        }
        for opcode, classification in cases.items():
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(decoded.classification, classification)
            self.assertTrue(decoded.text.startswith(".WORD"))
            self.assertEqual(assemble_statement(decoded.text).value, opcode)

    def test_all_bounded_direct_jump_call_forms_round_trip(self) -> None:
        count = 0
        for call in (False, True):
            operation = "CALL" if call else "JUMP"
            for address in range(1 << 14):
                for condition, mnemonic in enumerate(EXPECTED_IF_MNEMONICS):
                    if call and condition == 14:
                        continue
                    prefix = "" if condition == 15 else f"IF {mnemonic} "
                    statement = f"{prefix}{operation} 0x{address:04x};"
                    opcode = (
                        0x180000 | (int(call) << 18)
                        | (address << 4) | condition
                    )
                    assembled = assemble_statement(statement)
                    self.assertEqual(assembled.value, opcode)
                    decoded = disassemble_word(opcode)
                    self.assertTrue(decoded.implemented)
                    self.assertEqual(decoded.classification, "TYPE_10_BOUNDED_EXECUTION")
                    self.assertEqual(decoded.text, statement)
                    self.assertEqual(assemble_statement(decoded.text), assembled)
                    count += 1
        self.assertEqual(count, 507_904)

    def test_direct_call_not_ce_remains_fail_closed(self) -> None:
        opcode = 0x1C000E
        decoded = disassemble_word(opcode)
        self.assertFalse(decoded.implemented)
        self.assertEqual(
            decoded.classification,
            "UNVERIFIED_TYPE_10_CALL_NOT_CE_OQ_012",
        )
        self.assertEqual(assemble_statement(decoded.text).value, opcode)

    def test_all_bounded_indirect_jump_call_forms_round_trip(self) -> None:
        count = 0
        for i_address in range(4, 8):
            for call in (False, True):
                operation = "CALL" if call else "JUMP"
                for condition, mnemonic in enumerate(EXPECTED_IF_MNEMONICS):
                    if call and condition == 14:
                        continue
                    prefix = "" if condition == 15 else f"IF {mnemonic} "
                    statement = f"{prefix}{operation} (I{i_address});"
                    opcode = (
                        0x0B0000 | ((i_address - 4) << 6)
                        | (int(call) << 4) | condition
                    )
                    assembled = assemble_statement(statement)
                    self.assertEqual(assembled.value, opcode)
                    decoded = disassemble_word(opcode)
                    self.assertTrue(decoded.implemented)
                    self.assertEqual(
                        decoded.classification,
                        "TYPE_19_BOUNDED_EXECUTION",
                    )
                    self.assertEqual(decoded.text, statement)
                    self.assertEqual(assemble_statement(decoded.text), assembled)
                    count += 1
        self.assertEqual(count, 124)

    def test_indirect_fixed_bit_and_call_not_ce_fail_closed(self) -> None:
        call_not_ce = disassemble_word(0x0B001E)
        self.assertFalse(call_not_ce.implemented)
        self.assertEqual(
            call_not_ce.classification,
            "UNVERIFIED_TYPE_19_CALL_NOT_CE_OQ_012",
        )
        self.assertEqual(
            assemble_statement(call_not_ce.text).value,
            call_not_ce.opcode,
        )
        fixed_bit = disassemble_word(0x0B0020)
        self.assertFalse(fixed_bit.implemented)
        self.assertEqual(fixed_bit.classification, "RESERVED_UNSHOWN")
        with self.assertRaises(AssemblyError):
            assemble_statement("IF NOT CE CALL (I4);")
        with self.assertRaises(AssemblyError):
            assemble_statement("JUMP (I3);")

    def test_all_conditional_return_forms_round_trip(self) -> None:
        count = 0
        for interrupt_return in (False, True):
            operation = "RTI" if interrupt_return else "RTS"
            for condition, mnemonic in enumerate(EXPECTED_IF_MNEMONICS):
                prefix = "" if condition == 15 else f"IF {mnemonic} "
                statement = f"{prefix}{operation};"
                opcode = (
                    0x0A0000 | (int(interrupt_return) << 4) | condition
                )
                assembled = assemble_statement(statement)
                self.assertEqual(assembled.value, opcode)
                decoded = disassemble_word(opcode)
                self.assertTrue(decoded.implemented)
                self.assertEqual(
                    decoded.classification,
                    "TYPE_20_BOUNDED_EXECUTION",
                )
                self.assertEqual(decoded.text, statement)
                self.assertEqual(assemble_statement(decoded.text), assembled)
                count += 1
        self.assertEqual(count, 32)

    def test_all_conditional_trap_forms_round_trip(self) -> None:
        for condition, mnemonic in enumerate(EXPECTED_IF_MNEMONICS):
            prefix = "" if condition == 15 else f"IF {mnemonic} "
            statement = f"{prefix}TRAP;"
            opcode = 0x080000 | condition
            assembled = assemble_statement(statement)
            self.assertEqual(assembled.value, opcode)
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(
                decoded.classification,
                "TYPE_22_PHASE_AWARE_EXECUTION",
            )
            self.assertEqual(decoded.text, statement)
            self.assertEqual(assemble_statement(decoded.text), assembled)

    def test_all_source_closed_divide_sign_forms_round_trip(self) -> None:
        x_names = ("AX0", "AX1", "AR", "MR0", "MR1", "MR2", "SR0", "SR1")
        count = 0
        for yop, upper in ((1, "AY1"), (2, "AF")):
            for xop, divisor in enumerate(x_names):
                statement = f"DIVS {upper}, {divisor};"
                opcode = 0x060000 | (yop << 11) | (xop << 8)
                assembled = assemble_statement(statement)
                self.assertEqual(assembled.value, opcode)
                decoded = disassemble_word(opcode)
                self.assertTrue(decoded.implemented)
                self.assertEqual(decoded.classification, "TYPE_24_BOUNDED_EXECUTION")
                self.assertEqual(decoded.text, statement)
                self.assertEqual(assemble_statement(decoded.text), assembled)
                count += 1
        self.assertEqual(count, 16)

    def test_all_source_closed_divide_quotient_forms_round_trip(self) -> None:
        x_names = ("AX0", "AX1", "AR", "MR0", "MR1", "MR2", "SR0", "SR1")
        for xop, divisor in enumerate(x_names):
            statement = f"DIVQ {divisor};"
            opcode = 0x071000 | (xop << 8)
            assembled = assemble_statement(statement)
            self.assertEqual(assembled.value, opcode)
            decoded = disassemble_word(opcode)
            self.assertTrue(decoded.implemented)
            self.assertEqual(decoded.classification, "TYPE_23_BOUNDED_EXECUTION")
            self.assertEqual(decoded.text, statement)
            self.assertEqual(assemble_statement(decoded.text), assembled)

    def test_unsupported_divide_sign_y_operands_fail_closed(self) -> None:
        for yop in (0, 3):
            for xop in range(8):
                opcode = 0x060000 | (yop << 11) | (xop << 8)
                decoded = disassemble_word(opcode)
                self.assertFalse(decoded.implemented)
                self.assertEqual(decoded.classification, "UNSUPPORTED_TYPE_24_YOP")
                self.assertEqual(decoded.text, f".WORD 0x{opcode:06x};")

    def test_all_type_11_do_until_forms_round_trip(self) -> None:
        count = 0
        for address in range(1 << 14):
            for termination in range(16):
                opcode = 0x140000 | (address << 4) | termination
                decoded = disassemble_word(opcode)
                self.assertTrue(decoded.implemented)
                self.assertEqual(decoded.classification, "TYPE_11_BOUNDED_EXECUTION")
                self.assertEqual(assemble_statement(decoded.text).value, opcode)
                count += 1
        self.assertEqual(count, 262_144)
        self.assertEqual(assemble_statement("DO 0x0008;").value, 0x14008F)
        self.assertEqual(
            assemble_statement("DO H#0123 UNTIL CE;").value,
            0x14123E,
        )
        with self.assertRaises(AssemblyError):
            assemble_statement("DO 0x4000;")
        with self.assertRaises(AssemblyError):
            assemble_statement("DO 8 UNTIL MAYBE;")
        with self.assertRaises(AssemblyError):
            assemble_statement("IF NOT CE CALL 0x0000;")
        with self.assertRaises(AssemblyError):
            assemble_statement("JUMP 0x4000;")

    def test_compute_move_aliases_and_unsupported_forms_fail_closed(self) -> None:
        alias = disassemble_word(0x2A010D)
        self.assertTrue(alias.implemented)
        self.assertEqual(alias.classification, "TYPE_08_BOUNDED_ALIAS")
        self.assertEqual(assemble_statement(alias.text).value, alias.opcode)
        cases = {
            0x280000: "UNVERIFIED_TYPE_08_AMF_ZERO",
            0x2A60A0: "UNSUPPORTED_TYPE_08_DESTINATION_COLLISION",
            0x2880B0: "UNSUPPORTED_TYPE_08_DESTINATION_COLLISION",
        }
        for opcode, classification in cases.items():
            decoded = disassemble_word(opcode)
            self.assertFalse(decoded.implemented)
            self.assertEqual(decoded.classification, classification)
        with self.assertRaises(AssemblyError):
            assemble_statement("AR = AX0 + AY0, AR = AX0;")
        with self.assertRaises(AssemblyError):
            assemble_statement("MR = MX0 * MY0 (SS), MR0 = AX0;")

    def test_shift_move_unsupported_forms_fail_closed(self) -> None:
        cases = {
            0x108000: "UNVERIFIED_TYPE_14_UNUSED_X",
            0x100100: "UNVERIFIED_TYPE_14_XOP",
            0x1000E0: "UNSUPPORTED_TYPE_14_DESTINATION_COLLISION",
            0x106890: "UNSUPPORTED_TYPE_14_DESTINATION_COLLISION",
        }
        for opcode, classification in cases.items():
            decoded = disassemble_word(opcode)
            self.assertFalse(decoded.implemented)
            self.assertEqual(decoded.classification, classification)
        with self.assertRaises(AssemblyError):
            assemble_statement("SR = LSHIFT SI (HI), SR0 = AX0;")
        with self.assertRaises(AssemblyError):
            assemble_statement("SE = EXP SI (HI), SE = AX0;")

    def test_shifter_dm_unsupported_forms_fail_closed(self) -> None:
        cases = {
            0x120100: "UNVERIFIED_TYPE_12_XOP",
            0x1200E0: "UNSUPPORTED_TYPE_12_DESTINATION_COLLISION",
            0x126890: "UNSUPPORTED_TYPE_12_DESTINATION_COLLISION",
        }
        for opcode, classification in cases.items():
            decoded = disassemble_word(opcode)
            self.assertFalse(decoded.implemented)
            self.assertEqual(decoded.classification, classification)
        with self.assertRaises(AssemblyError):
            assemble_statement("SR = LSHIFT SI (HI), SR0 = DM(I0, M0);")
        with self.assertRaises(AssemblyError):
            assemble_statement("SR = LSHIFT SI (HI), AX0 = DM(I0, M4);")

    def test_shifter_pm_unsupported_forms_fail_closed(self) -> None:
        cases = {
            0x110100: "UNVERIFIED_TYPE_13_XOP",
            0x1100E0: "UNSUPPORTED_TYPE_13_DESTINATION_COLLISION",
            0x116890: "UNSUPPORTED_TYPE_13_DESTINATION_COLLISION",
        }
        for opcode, classification in cases.items():
            decoded = disassemble_word(opcode)
            self.assertFalse(decoded.implemented)
            self.assertEqual(decoded.classification, classification)
        with self.assertRaises(AssemblyError):
            assemble_statement("SR = LSHIFT SI (HI), SR0 = PM(I4, M4);")
        with self.assertRaises(AssemblyError):
            assemble_statement("SR = LSHIFT SI (HI), AX0 = PM(I0, M4);")
        with self.assertRaises(AssemblyError):
            assemble_statement("SR = LSHIFT SI (HI), AX0 = PM(I4, M0);")

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
            assemble_statement("AR = AX0 * AY0;")

    def test_original_reserved_bytes_are_not_disassembled_as_later_features(self) -> None:
        result = disassemble_word(0x010000)
        self.assertFalse(result.implemented)
        self.assertEqual(result.classification, "RESERVED_TYPE_29")
        self.assertEqual(result.text, ".WORD 0x010000;")

    def test_unshown_reserved_and_unsupported_legal_class_are_distinct(self) -> None:
        self.assertEqual(
            disassemble_word(0x0B0020).classification,
            "RESERVED_UNSHOWN",
        )
        self.assertEqual(
            disassemble_word(0x8C0008).classification,
            "UNSUPPORTED_TYPE_03_RESERVED_DESTINATION_SELECTOR",
        )


if __name__ == "__main__":
    unittest.main()
