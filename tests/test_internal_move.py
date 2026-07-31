from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model.internal_move import (
    INTERNAL_MOVE_VALUE,
    decode_internal_move as decode_model,
    register_code_by_name,
)
from tools.generators.validate_internal_move import (
    InternalMoveValidationError,
    decode_internal_move as decode_database,
    load_database,
    validate_database,
)


ROOT = Path(__file__).resolve().parents[1]


class InternalMoveActionDecodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = load_database()
        cls.fixture = json.loads(
            (
                ROOT / "tests/vectors/internal_move_fixtures.json"
            ).read_text(encoding="utf-8")
        )

    def test_machine_readable_semantics_validate(self) -> None:
        validate_database(self.database)
        self.assertIn("ADI-UM-1989", self.fixture["source"])

    def test_hand_checked_fixtures_match_independent_decoders(self) -> None:
        for case in self.fixture["hand_checked_cases"]:
            opcode = int(case["opcode"], 16)
            model = decode_model(opcode)
            database = decode_database(self.database, opcode)
            self.assertIsNotNone(model)
            self.assertIsNotNone(database)
            assert model is not None and database is not None
            self.assertEqual(model.destination_register, case["destination"])
            self.assertEqual(model.source_register, case["source_register"])
            self.assertEqual(model.legal, case["legal"])
            self.assertEqual(
                database["destination_register"],
                case["destination"],
            )
            self.assertEqual(
                database["source_register"],
                case["source_register"],
            )
            self.assertEqual(database["legal"], case["legal"])
            if not case["legal"]:
                self.assertEqual(
                    model.invalid_reason,
                    case["invalid_reason"],
                )
                self.assertEqual(
                    database["invalid_reason"],
                    case["invalid_reason"],
                )

    def test_all_4096_selectors_match_and_counts_are_exact(self) -> None:
        legal = 0
        invalid = 0
        for payload in range(0x1000):
            opcode = INTERNAL_MOVE_VALUE | payload
            model = decode_model(opcode)
            database = decode_database(self.database, opcode)
            self.assertIsNotNone(model)
            self.assertIsNotNone(database)
            assert model is not None and database is not None
            self.assertEqual(model.destination_code,
                             database["destination_code"])
            self.assertEqual(model.source_code, database["source_code"])
            self.assertEqual(model.destination_register,
                             database["destination_register"])
            self.assertEqual(model.source_register,
                             database["source_register"])
            self.assertEqual(model.legal, database["legal"])
            self.assertEqual(model.invalid_reason,
                             database["invalid_reason"])
            if model.legal:
                legal += 1
            else:
                invalid += 1
        self.assertEqual(legal, 2256)
        self.assertEqual(invalid, 1840)

    def test_register_direction_sets_are_exact(self) -> None:
        readable = register_code_by_name(writable=False)
        writable = register_code_by_name(writable=True)
        self.assertEqual(len(readable), 48)
        self.assertEqual(len(writable), 47)
        self.assertIn("SSTAT", readable)
        self.assertNotIn("SSTAT", writable)
        self.assertNotIn("AF", readable)
        self.assertNotIn("MF", readable)
        self.assertNotIn("PC", readable)

    def test_non_type_17_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x0CFFFF, 0x0D1000, 0x0E0000, 0xFFFFFF):
            self.assertIsNone(decode_model(opcode))
            self.assertIsNone(decode_database(self.database, opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_model(opcode)
            with self.assertRaises(ValueError):
                decode_database(self.database, opcode)

    def test_corrupt_semantics_fail_validation(self) -> None:
        wrong_mask = copy.deepcopy(self.database)
        wrong_mask["instruction"]["opcode_mask"] = "0xfff100"
        with self.assertRaises(InternalMoveValidationError):
            validate_database(wrong_mask)

        wrong_count = copy.deepcopy(self.database)
        wrong_count["instruction"]["legal_action_count"] = 2257
        with self.assertRaises(InternalMoveValidationError):
            validate_database(wrong_count)

        memory_access = copy.deepcopy(self.database)
        memory_access["instruction"]["dm_transfer"] = "READ"
        with self.assertRaises(InternalMoveValidationError):
            validate_database(memory_access)


if __name__ == "__main__":
    unittest.main()
