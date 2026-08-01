from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model.direct_dm import (
    DIRECT_DM_VALUE,
    decode_direct_dm as decode_model,
)
from tools.generators.validate_direct_dm import (
    DirectDMValidationError,
    decode_direct_dm as decode_database,
    load_database,
    validate_database,
)


ROOT = Path(__file__).resolve().parents[1]


class DirectDMActionDecodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = load_database()
        cls.fixture = json.loads(
            (ROOT / "tests/vectors/direct_dm_fixtures.json").read_text(
                encoding="utf-8"
            )
        )

    def test_machine_readable_semantics_validate(self) -> None:
        validate_database(self.database)
        instruction = self.database["instruction"]
        self.assertEqual(instruction["legal_read_count"], 770_048)
        self.assertEqual(instruction["legal_write_count"], 786_432)
        self.assertEqual(
            instruction["illegal_or_reserved_subencoding_count"], 540_672
        )

    def test_hand_checked_fixtures_match_independent_decoders(self) -> None:
        for case in self.fixture["hand_checked_cases"]:
            opcode = int(case["opcode"], 16)
            model = decode_model(opcode)
            database = decode_database(self.database, opcode)
            self.assertIsNotNone(model)
            self.assertIsNotNone(database)
            assert model is not None and database is not None
            self.assertEqual(model.write, case["write"])
            self.assertEqual(model.address, int(case["address"], 16))
            self.assertEqual(model.register, case["register"])
            self.assertEqual(model.legal, case["legal"])
            self.assertEqual(database["write"], case["write"])
            self.assertEqual(database["address"], int(case["address"], 16))
            self.assertEqual(database["register"], case["register"])
            self.assertEqual(database["legal"], case["legal"])
            if not case["legal"]:
                self.assertEqual(model.invalid_reason, case["invalid_reason"])
                self.assertEqual(database["invalid_reason"], case["invalid_reason"])

    def test_all_direction_selectors_and_address_boundaries_match(self) -> None:
        legal_reads = 0
        legal_writes = 0
        invalid_selectors = 0
        for write in range(2):
            for code in range(64):
                for address in (0, 1, 0x1FFF, 0x2000, 0x3FFF):
                    opcode = (
                        DIRECT_DM_VALUE | (write << 20)
                        | ((code >> 4) << 18) | (address << 4) | (code & 0xF)
                    )
                    model = decode_model(opcode)
                    database = decode_database(self.database, opcode)
                    self.assertIsNotNone(model)
                    self.assertIsNotNone(database)
                    assert model is not None and database is not None
                    self.assertEqual(model.write, database["write"])
                    self.assertEqual(model.address, database["address"])
                    self.assertEqual(model.register_code, database["register_code"])
                    self.assertEqual(model.register, database["register"])
                    self.assertEqual(model.legal, database["legal"])
                    self.assertEqual(model.invalid_reason, database["invalid_reason"])
                if model.legal:
                    if write:
                        legal_writes += 1
                    else:
                        legal_reads += 1
                else:
                    invalid_selectors += 1
        self.assertEqual((legal_reads, legal_writes, invalid_selectors), (47, 48, 33))

    def test_non_type_3_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x7FFFFF, 0xA00000, 0xFFFFFF):
            self.assertIsNone(decode_model(opcode))
            self.assertIsNone(decode_database(self.database, opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_model(opcode)
            with self.assertRaises(ValueError):
                decode_database(self.database, opcode)

    def test_corrupt_semantics_fail_validation(self) -> None:
        wrong_count = copy.deepcopy(self.database)
        wrong_count["instruction"]["legal_action_count"] += 1
        with self.assertRaises(DirectDMValidationError):
            validate_database(wrong_count)

        hidden_execution = copy.deepcopy(self.database)
        hidden_execution["implementation_boundary"]["state_execution"] = "COMPLETE"
        with self.assertRaises(DirectDMValidationError):
            validate_database(hidden_execution)


if __name__ == "__main__":
    unittest.main()
