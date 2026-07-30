from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from tools.generators.validate_register_codes import (
    RegisterCodeError,
    load_and_validate,
)


class RegisterMetadataTests(unittest.TestCase):
    def test_original_general_move_table_is_complete(self) -> None:
        data = load_and_validate()
        groups = data["groups"]
        self.assertEqual(groups["00"]["codes"]["0"]["register"], "AX0")
        self.assertEqual(groups["00"]["codes"]["13"]["register"], "MR2")
        self.assertEqual(groups["01"]["codes"]["0"]["register"], "I0")
        self.assertEqual(groups["10"]["codes"]["11"]["register"], "L7")
        self.assertEqual(groups["11"]["codes"]["2"]["register"], "SSTAT")
        self.assertEqual(groups["11"]["codes"]["7"]["register"], "PX")

    def test_reserved_register_codes_are_explicit(self) -> None:
        data = load_and_validate()
        self.assertEqual(data["groups"]["01"]["reserved_codes"], [12, 13, 14, 15])
        self.assertEqual(data["groups"]["10"]["reserved_codes"], [12, 13, 14, 15])
        self.assertEqual(
            data["groups"]["11"]["reserved_codes"],
            [8, 9, 10, 11, 12, 13, 14, 15],
        )

    def test_signed_narrow_read_behavior_is_recorded(self) -> None:
        data = load_and_validate()
        self.assertEqual(
            data["groups"]["00"]["codes"]["13"],
            {
                "register": "MR2",
                "storage_width": 8,
                "move_access": "read_write_sign_extended",
            },
        )
        self.assertEqual(
            data["groups"]["11"]["codes"]["6"]["move_access"],
            "read_write_sign_extended",
        )

    def test_missing_reserved_code_is_rejected(self) -> None:
        data = copy.deepcopy(load_and_validate())
        data["groups"]["11"]["reserved_codes"].remove(15)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "registers.yaml"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(RegisterCodeError):
                load_and_validate(path)


if __name__ == "__main__":
    unittest.main()
