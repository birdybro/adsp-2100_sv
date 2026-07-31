from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    STACK_CONTROL_VALUE,
    StackControlStatusOperation,
    decode_stack_control,
)
from tools.generators.validate_stack_control import (
    StackControlValidationError,
    decode_actions,
    load_database,
    validate_database,
)


ROOT = Path(__file__).resolve().parents[1]


class StackControlSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = load_database()
        cls.fixture = json.loads(
            (
                ROOT / "tests/vectors/stack_control_fixtures.json"
            ).read_text(encoding="utf-8")
        )

    def test_machine_readable_semantics_validate(self) -> None:
        validate_database(self.database)
        self.assertIn("ADI-UM-1989", self.fixture["source"])

    def test_independent_source_fixture_matches_model(self) -> None:
        for case in self.fixture["hand_checked_cases"]:
            opcode = int(case["opcode"], 16)
            decoded = decode_stack_control(opcode)
            self.assertIsNotNone(decoded)
            assert decoded is not None
            self.assertEqual(
                decoded.status_operation.name,
                case["status_operation"],
            )
            self.assertEqual(decoded.count_pop, case["count_pop"])
            self.assertEqual(decoded.loop_pop, case["loop_pop"])
            self.assertEqual(decoded.pc_pop, case["pc_pop"])
            self.assertEqual(decoded.has_effect, case["has_effect"])
            self.assertEqual(
                list(decoded.assembly_components),
                case["assembly_components"],
            )

    def test_all_32_field_defined_encodings_decode(self) -> None:
        distinct_behaviors: set[tuple[object, ...]] = set()
        for payload in range(32):
            decoded = decode_stack_control(STACK_CONTROL_VALUE | payload)
            self.assertIsNotNone(decoded)
            assert decoded is not None
            self.assertEqual(int(decoded.status_operation), payload & 0x3)
            self.assertEqual(decoded.count_pop, bool(payload & 0x4))
            self.assertEqual(decoded.loop_pop, bool(payload & 0x8))
            self.assertEqual(decoded.pc_pop, bool(payload & 0x10))
            self.assertEqual(decoded.has_effect, bool(payload & 0x1E))
            normalized_status = (
                "NO_CHANGE"
                if decoded.status_operation
                in {
                    StackControlStatusOperation.NO_CHANGE_ZERO,
                    StackControlStatusOperation.NO_CHANGE_ONE,
                }
                else decoded.status_operation.name
            )
            distinct_behaviors.add(
                (
                    normalized_status,
                    decoded.count_pop,
                    decoded.loop_pop,
                    decoded.pc_pop,
                )
            )
        self.assertEqual(len(distinct_behaviors), 24)

    def test_non_type_26_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x03FFFF, 0x040020, 0xFFFFFF):
            self.assertIsNone(decode_stack_control(opcode))
            self.assertIsNone(decode_actions(self.database, opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_stack_control(opcode)
            with self.assertRaises(ValueError):
                decode_actions(self.database, opcode)

    def test_no_change_aliases_preserve_raw_encoding(self) -> None:
        zero = decode_stack_control(0x040000)
        one = decode_stack_control(0x040001)
        assert zero is not None and one is not None
        self.assertNotEqual(zero.status_operation, one.status_operation)
        self.assertFalse(zero.has_effect)
        self.assertFalse(one.has_effect)
        self.assertEqual(zero.assembly_components, one.assembly_components)

    def test_corrupt_semantics_fail_validation(self) -> None:
        wrong_mask = copy.deepcopy(self.database)
        wrong_mask["instruction"]["opcode_mask"] = "0xfffff0"
        with self.assertRaises(StackControlValidationError):
            validate_database(wrong_mask)

        invented_underflow = copy.deepcopy(self.database)
        invented_underflow["instruction"][
            "underflow_rule"
        ] = "PRESERVE_STATE"
        with self.assertRaises(StackControlValidationError):
            validate_database(invented_underflow)

        wrong_action = copy.deepcopy(self.database)
        wrong_action["fields"][2]["actions"]["1"] = "NO_CHANGE"
        with self.assertRaises(StackControlValidationError):
            validate_database(wrong_action)


if __name__ == "__main__":
    unittest.main()
