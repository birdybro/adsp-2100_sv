from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model.conditions import (
    ConditionInputs,
    DO_TERMINATION_MNEMONICS,
    IF_CONDITION_MNEMONICS,
    evaluate_do_termination,
    evaluate_if_condition,
)
from tools.generators.validate_condition_codes import (
    load_database,
    validate_database,
)


class ConditionLogicTests(unittest.TestCase):
    def test_machine_readable_tables_are_complete(self) -> None:
        validate_database(load_database())

    def test_primary_mnemonic_order_is_independently_fixed(self) -> None:
        self.assertEqual(
            IF_CONDITION_MNEMONICS,
            (
                "EQ", "NE", "GT", "LE", "LT", "GE", "AV", "NOT AV",
                "AC", "NOT AC", "NEG", "POS", "MV", "NOT MV", "NOT CE", "TRUE",
            ),
        )
        self.assertEqual(
            DO_TERMINATION_MNEMONICS,
            (
                "NE", "EQ", "LE", "GT", "GE", "LT", "NOT AV", "AV",
                "NOT AC", "AC", "POS", "NEG", "NOT MV", "MV", "CE", "FOREVER",
            ),
        )

    def test_signed_compare_uses_an_xor_av_and_az(self) -> None:
        negative_without_overflow = ConditionInputs(an=True)
        negative_with_overflow = ConditionInputs(an=True, av=True)
        zero = ConditionInputs(az=True)
        self.assertTrue(evaluate_if_condition(4, negative_without_overflow))
        self.assertFalse(evaluate_if_condition(4, negative_with_overflow))
        self.assertTrue(evaluate_if_condition(2, ConditionInputs()))
        self.assertFalse(evaluate_if_condition(2, zero))
        self.assertTrue(evaluate_if_condition(3, zero))

    def test_neg_uses_as_not_an(self) -> None:
        inputs = ConditionInputs(an=True, as_flag=False)
        self.assertFalse(evaluate_if_condition(10, inputs))
        self.assertTrue(evaluate_if_condition(11, inputs))

    def test_counter_and_unconditional_codes(self) -> None:
        self.assertFalse(evaluate_if_condition(14, ConditionInputs()))
        self.assertTrue(
            evaluate_if_condition(14, ConditionInputs(counter_nonzero=True))
        )
        self.assertTrue(evaluate_if_condition(15, ConditionInputs()))

    def test_do_termination_is_inverse_for_every_input(self) -> None:
        for code in range(16):
            for flags in range(128):
                inputs = ConditionInputs(
                    az=bool(flags & 0x40),
                    an=bool(flags & 0x20),
                    av=bool(flags & 0x10),
                    ac=bool(flags & 0x08),
                    as_flag=bool(flags & 0x04),
                    mv=bool(flags & 0x02),
                    counter_nonzero=bool(flags & 0x01),
                )
                self.assertEqual(
                    evaluate_do_termination(code, inputs),
                    not evaluate_if_condition(code, inputs),
                )

        self.assertFalse(evaluate_do_termination(15, ConditionInputs()))

    def test_invalid_condition_code_fails_closed(self) -> None:
        for code in (-1, 16):
            with self.assertRaises(ValueError):
                evaluate_if_condition(code, ConditionInputs())
            with self.assertRaises(ValueError):
                evaluate_do_termination(code, ConditionInputs())


if __name__ == "__main__":
    unittest.main()
