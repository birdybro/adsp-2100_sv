from __future__ import annotations

import random
import unittest

from sim.reference_models.adsp2100_model.alu import compute_alu


class ALUModelTests(unittest.TestCase):
    def test_non_alu_codes_and_bad_operands_fail_closed(self) -> None:
        for amf in (0x00, 0x0F, 0x20):
            with self.assertRaises(ValueError):
                compute_alu(amf, 0, 0)
        with self.assertRaises(ValueError):
            compute_alu(0x10, 0x10000, 0)

    def test_pass_and_logic_clear_carry_and_overflow(self) -> None:
        passed = compute_alu(0x10, 0x1234, 0x8000)
        self.assertEqual(passed.raw_result, 0x8000)
        self.assertTrue(passed.an)
        self.assertFalse(passed.az or passed.av or passed.ac)
        self.assertEqual(compute_alu(0x1C, 0xFF00, 0x0FF0).raw_result, 0x0F00)
        self.assertEqual(compute_alu(0x1D, 0xFF00, 0x0FF0).raw_result, 0xFFF0)
        self.assertEqual(compute_alu(0x1E, 0xFF00, 0x0FF0).raw_result, 0xF0F0)

    def test_add_overflow_carry_and_both_saturation_directions(self) -> None:
        positive = compute_alu(0x13, 0x7FFF, 1, saturate_ar=True)
        self.assertEqual((positive.raw_result, positive.destination_result), (0x8000, 0x7FFF))
        self.assertTrue(positive.av)
        self.assertFalse(positive.ac)

        negative = compute_alu(0x13, 0x8000, 0xFFFF, saturate_ar=True)
        self.assertEqual((negative.raw_result, negative.destination_result), (0x7FFF, 0x8000))
        self.assertTrue(negative.av and negative.ac)

    def test_subtract_with_borrow_uses_carry_as_not_borrow(self) -> None:
        borrowed = compute_alu(0x16, 0, 0, carry_in=False)
        no_borrow = compute_alu(0x16, 0, 0, carry_in=True)
        self.assertEqual((borrowed.raw_result, borrowed.ac), (0xFFFF, False))
        self.assertEqual((no_borrow.raw_result, no_borrow.ac), (0x0000, True))

    def test_negate_zero_and_minimum_flags(self) -> None:
        zero = compute_alu(0x15, 0, 0)
        minimum = compute_alu(0x15, 0, 0x8000, saturate_ar=True)
        self.assertTrue(zero.az and zero.ac)
        self.assertEqual(minimum.raw_result, 0x8000)
        self.assertEqual(minimum.destination_result, 0x7FFF)
        self.assertTrue(minimum.an and minimum.av)
        self.assertFalse(minimum.ac)

    def test_absolute_value_updates_as_and_handles_minimum(self) -> None:
        ordinary = compute_alu(0x1F, 0xFFFF, 0)
        self.assertEqual(ordinary.raw_result, 1)
        self.assertTrue(ordinary.as_write and ordinary.as_value)
        minimum = compute_alu(0x1F, 0x8000, 0, saturate_ar=True)
        self.assertEqual((minimum.raw_result, minimum.destination_result), (0x8000, 0x7FFF))
        self.assertTrue(minimum.an and minimum.av)
        self.assertFalse(minimum.ac)

    def test_sticky_prior_overflow_does_not_trigger_saturation(self) -> None:
        result = compute_alu(
            0x13,
            1,
            1,
            previous_av=True,
            sticky_av=True,
            saturate_ar=True,
        )
        self.assertEqual(result.raw_result, 2)
        self.assertEqual(result.destination_result, 2)
        self.assertTrue(result.av)

    def test_random_logic_and_pass_identities(self) -> None:
        rng = random.Random(0x2100)
        for _ in range(1000):
            x = rng.randrange(0x10000)
            y = rng.randrange(0x10000)
            self.assertEqual(compute_alu(0x10, x, y).raw_result, y)
            self.assertEqual(compute_alu(0x14, x, y).raw_result, (~y) & 0xFFFF)
            self.assertEqual(compute_alu(0x1B, x, y).raw_result, (~x) & 0xFFFF)
            self.assertEqual(compute_alu(0x1C, x, y).raw_result, x & y)
            self.assertEqual(compute_alu(0x1D, x, y).raw_result, x | y)
            self.assertEqual(compute_alu(0x1E, x, y).raw_result, x ^ y)


if __name__ == "__main__":
    unittest.main()
