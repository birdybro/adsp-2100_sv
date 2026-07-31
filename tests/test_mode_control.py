from __future__ import annotations

import copy
import json
from pathlib import Path
import random
import unittest

from sim.reference_models.adsp2100_model import (
    MODE_CONTROL_VALUE,
    ExactWord,
    ModeControl,
    apply_mode_control,
    apply_mode_control_slice_cycle,
    decode_mode_control,
)
from tools.generators.validate_mode_control import (
    ModeControlValidationError,
    decode_actions,
    load_database,
    validate_database,
)


ROOT = Path(__file__).resolve().parents[1]


class ModeControlSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = load_database()
        cls.fixture = json.loads(
            (
                ROOT / "tests/vectors/mode_control_fixtures.json"
            ).read_text(encoding="utf-8")
        )

    def test_machine_readable_semantics_validate(self) -> None:
        validate_database(self.database)
        self.assertIn("ADI-UM-1989", self.fixture["source"])

    def test_independent_hand_fixtures_match_model(self) -> None:
        for case in self.fixture["hand_checked_cases"]:
            opcode = int(case["opcode"], 16)
            actions = decode_mode_control(opcode)
            self.assertIsNotNone(actions)
            assert actions is not None
            self.assertEqual(actions.sr.name, case["sr"])
            self.assertEqual(actions.br.name, case["br"])
            self.assertEqual(actions.ol.name, case["ol"])
            self.assertEqual(actions.ar.name, case["ar"])
            result = apply_mode_control(
                ExactWord(4, int(case["input_mstat"], 16)),
                actions,
            )
            self.assertEqual(result.value, int(case["expected_mstat"], 16))

    def test_all_256_encodings_and_all_initial_states(self) -> None:
        distinct_actions: set[tuple[str, ...]] = set()
        actionless = 0
        for payload in range(256):
            opcode = MODE_CONTROL_VALUE | (payload << 4)
            actions = decode_mode_control(opcode)
            self.assertIsNotNone(actions)
            assert actions is not None
            expected_codes = tuple((payload >> shift) & 0x3 for shift in range(0, 8, 2))
            self.assertEqual(
                tuple(int(control) for control in actions.controls),
                expected_codes,
            )
            normalized = tuple(
                "NO_CHANGE"
                if control in {
                    ModeControl.NO_CHANGE_ZERO,
                    ModeControl.NO_CHANGE_ONE,
                }
                else control.name
                for control in actions.controls
            )
            distinct_actions.add(normalized)
            actionless += int(not actions.has_effect)
            for initial in range(16):
                expected = initial
                for bit, code in enumerate(expected_codes):
                    if code == ModeControl.DEACTIVATE:
                        expected &= ~(1 << bit)
                    elif code == ModeControl.ACTIVATE:
                        expected |= 1 << bit
                self.assertEqual(
                    apply_mode_control(ExactWord(4, initial), actions).value,
                    expected,
                )
        self.assertEqual(len(distinct_actions), 81)
        self.assertEqual(actionless, 16)

    def test_no_change_aliases_remain_distinguishable(self) -> None:
        zero = decode_mode_control(0x0C0000)
        one = decode_mode_control(0x0C0550)
        assert zero is not None and one is not None
        self.assertEqual(
            zero.controls,
            (ModeControl.NO_CHANGE_ZERO,) * 4,
        )
        self.assertEqual(
            one.controls,
            (ModeControl.NO_CHANGE_ONE,) * 4,
        )
        self.assertFalse(zero.has_effect)
        self.assertFalse(one.has_effect)
        self.assertFalse(zero.has_no_change_one_alias)
        self.assertTrue(one.has_no_change_one_alias)

    def test_non_type_18_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x0BFFFF, 0x0C0001, 0x0D0000, 0xFFFFFF):
            self.assertIsNone(decode_mode_control(opcode))
            self.assertIsNone(decode_actions(self.database, opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_mode_control(opcode)
            with self.assertRaises(ValueError):
                decode_actions(self.database, opcode)

    def test_slice_reset_setup_execution_and_conflict(self) -> None:
        state = ExactWord(4, 0xF)
        reset = apply_mode_control_slice_cycle(state, reset=True)
        self.assertEqual(reset.mstat.value, 0)

        setup = apply_mode_control_slice_cycle(
            reset.mstat,
            setup_mstat=ExactWord(4, 0xA),
        )
        self.assertEqual(setup.mstat.value, 0xA)

        execute = apply_mode_control_slice_cycle(
            setup.mstat,
            execute=True,
            opcode=0x0C0BB0,
        )
        self.assertTrue(execute.boundary_valid)
        self.assertEqual(execute.mstat.value, 0x5)

        invalid = apply_mode_control_slice_cycle(
            execute.mstat,
            execute=True,
            opcode=0x0D0000,
        )
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.mstat, execute.mstat)

        conflict = apply_mode_control_slice_cycle(
            invalid.mstat,
            execute=True,
            opcode=0x0C0030,
            setup_mstat=ExactWord(4, 0),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertFalse(conflict.boundary_valid)
        self.assertEqual(conflict.mstat, invalid.mstat)

    def test_deterministic_random_slice_transitions(self) -> None:
        rng = random.Random(0x210018)
        state = ExactWord(4, 0)
        for cycle in range(20_000):
            reset = cycle == 0 or rng.randrange(251) == 0
            execute = bool(rng.getrandbits(1))
            valid = rng.randrange(4) != 0
            opcode = (
                MODE_CONTROL_VALUE | (rng.randrange(256) << 4)
                if valid
                else rng.randrange(0x1000000)
            )
            if not valid and opcode & 0xFFF00F == MODE_CONTROL_VALUE:
                opcode ^= 1
            setup = (
                ExactWord(4, rng.randrange(16))
                if rng.randrange(5) == 0
                else None
            )
            result = apply_mode_control_slice_cycle(
                state,
                reset=reset,
                execute=execute,
                opcode=opcode,
                setup_mstat=setup,
            )
            self.assertLess(result.mstat.value, 16)
            state = result.mstat

    def test_corrupt_semantics_fail_validation(self) -> None:
        wrong_mask = copy.deepcopy(self.database)
        wrong_mask["instruction"]["opcode_mask"] = "0xfff01f"
        with self.assertRaises(ModeControlValidationError):
            validate_database(wrong_mask)

        later_mode = copy.deepcopy(self.database)
        later_mode["instruction"]["later_device_exclusion"] = "NONE"
        with self.assertRaises(ModeControlValidationError):
            validate_database(later_mode)

        wrong_field = copy.deepcopy(self.database)
        wrong_field["fields"][0]["lsb"] = 9
        with self.assertRaises(ModeControlValidationError):
            validate_database(wrong_field)


if __name__ == "__main__":
    unittest.main()
