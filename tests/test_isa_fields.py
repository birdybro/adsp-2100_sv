from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.generators.validate_isa_fields import load_database, validate_database


class ISAFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = load_database()
        cls.tables = {table["id"]: table for table in cls.database["tables"]}

    def test_all_tables_validate(self) -> None:
        validate_database(self.database)

    def test_every_code_matches_independent_review_fixture(self) -> None:
        fixture_path = (
            Path(__file__).resolve().parent / "vectors/isa_field_fixtures.json"
        )
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertIn("ADI-UM-1989", fixture["source"])
        self.assertEqual(set(fixture["tables"]), set(self.tables))
        for table_id, expected_names in fixture["tables"].items():
            actual_names = [
                entry["name"] for entry in self.tables[table_id]["values"]
            ]
            self.assertEqual(actual_names, expected_names, table_id)

    def test_amf_order_is_primary_fixed(self) -> None:
        names = tuple(entry["name"] for entry in self.tables["AMF"]["values"])
        self.assertEqual(
            names,
            (
                "NO_OPERATION", "MUL_RND", "MAC_ADD_RND", "MAC_SUB_RND",
                "MUL_SS", "MUL_SU", "MUL_US", "MUL_UU",
                "MAC_ADD_SS", "MAC_ADD_SU", "MAC_ADD_US", "MAC_ADD_UU",
                "MAC_SUB_SS", "MAC_SUB_SU", "MAC_SUB_US", "MAC_SUB_UU",
                "PASS_Y", "Y_PLUS_ONE", "X_PLUS_Y_PLUS_C", "X_PLUS_Y",
                "NOT_Y", "NEGATE_Y", "X_MINUS_Y_PLUS_C_MINUS_ONE", "X_MINUS_Y",
                "Y_MINUS_ONE", "Y_MINUS_X", "Y_MINUS_X_PLUS_C_MINUS_ONE",
                "NOT_X", "X_AND_Y", "X_OR_Y", "X_XOR_Y", "ABS_X",
            ),
        )

    def test_data_register_order_is_primary_fixed(self) -> None:
        names = tuple(entry["name"] for entry in self.tables["DREG"]["values"])
        self.assertEqual(
            names,
            (
                "AX0", "AX1", "MX0", "MX1", "AY0", "AY1", "MY0", "MY1",
                "SI", "SE", "AR", "MR0", "MR1", "MR2", "SR0", "SR1",
            ),
        )

    def test_dag_context_selectors_cover_all_registers(self) -> None:
        self.assertEqual(
            [entry["name"] for entry in self.tables["G_I"]["values"]],
            [f"I{index}" for index in range(8)],
        )
        self.assertEqual(
            [entry["name"] for entry in self.tables["G_M"]["values"]],
            [f"M{index}" for index in range(8)],
        )

    def test_mode_and_status_controls_preserve_duplicate_no_change_codes(self) -> None:
        self.assertEqual(
            [target["id"] for target in self.database["mcc_targets"]],
            ["SR", "BR", "OL", "AS"],
        )
        self.assertEqual(
            [entry["name"] for entry in self.tables["MCC"]["values"]],
            ["NO_CHANGE_0", "NO_CHANGE_1", "DEACTIVATE", "ACTIVATE"],
        )
        self.assertEqual(
            [entry["name"] for entry in self.tables["SPP"]["values"]],
            ["NO_CHANGE_0", "NO_CHANGE_1", "PUSH", "POP"],
        )

    def test_shifter_function_order_is_primary_fixed(self) -> None:
        self.assertEqual(
            [entry["name"] for entry in self.tables["SF"]["values"]],
            [
                "LSHIFT_HI_PASS", "LSHIFT_HI_OR", "LSHIFT_LO_PASS",
                "LSHIFT_LO_OR", "ASHIFT_HI_PASS", "ASHIFT_HI_OR",
                "ASHIFT_LO_PASS", "ASHIFT_LO_OR", "NORM_HI_PASS",
                "NORM_HI_OR", "NORM_LO_PASS", "NORM_LO_OR", "EXP_HI",
                "EXP_HIX", "EXP_LO", "BLOCK_EXPONENT_ADJUST",
            ],
        )


if __name__ == "__main__":
    unittest.main()
