from __future__ import annotations

import random
import unittest

from sim.reference_models.adsp2100_model.shifter import compute_shifter


class ShifterModelTests(unittest.TestCase):
    def test_bad_widths_fail_closed(self) -> None:
        for arguments in (
            (0x10, 0, 0, 0, 0),
            (0, 0x10000, 0, 0, 0),
            (0, 0, 0x100, 0, 0),
            (0, 0, 0, 0x100000000, 0),
            (0, 0, 0, 0, 0x20),
        ):
            with self.assertRaises(ValueError):
                compute_shifter(*arguments)

    def test_logical_hi_lo_placements_and_off_scale_counts(self) -> None:
        self.assertEqual(compute_shifter(0x00, 0xA55A, 0, 0, 0).sr_result, 0xA55A0000)
        self.assertEqual(compute_shifter(0x02, 0xA55A, 0, 0, 0).sr_result, 0x0000A55A)
        self.assertEqual(compute_shifter(0x00, 0xA55A, 0xF0, 0, 0).sr_result, 0x0000A55A)
        self.assertEqual(compute_shifter(0x02, 0xA55A, 16, 0, 0).sr_result, 0xA55A0000)
        self.assertEqual(compute_shifter(0x00, 0xA55A, 16, 0, 0).sr_result, 0)
        self.assertEqual(compute_shifter(0x02, 0xA55A, 0xF0, 0, 0).sr_result, 0)

    def test_arithmetic_extension_comes_from_input_msb(self) -> None:
        high = compute_shifter(0x04, 0x8001, 0xFF, 0, 0)
        low = compute_shifter(0x06, 0x8001, 0, 0, 0)
        self.assertEqual(high.sr_result, 0xC0008000)
        self.assertEqual(low.sr_result, 0xFFFF8001)
        self.assertEqual(compute_shifter(0x06, 0x7FFF, 0, 0, 0).sr_result, 0x00007FFF)

    def test_or_functions_preserve_existing_bits(self) -> None:
        passed = compute_shifter(0x02, 0x00F0, 0, 0xAA550F00, 0)
        combined = compute_shifter(0x03, 0x00F0, 0, 0xAA550F00, 0)
        self.assertEqual(passed.sr_result, 0x000000F0)
        self.assertEqual(combined.sr_result, 0xAA550FF0)

    def test_norm_negates_se_and_uses_documented_extensions(self) -> None:
        ordinary = compute_shifter(0x08, 0xF6D4, 0xFD, 0, 0, ac=False)
        self.assertEqual(ordinary.sr_result, 0xB6A00000)
        hix_positive = compute_shifter(0x08, 0xFA32, 1, 0, 0, ac=False)
        hix_negative = compute_shifter(0x08, 0x0532, 1, 0, 0, ac=True)
        self.assertEqual(hix_positive.sr_result, 0x7D190000)
        self.assertEqual(hix_negative.sr_result, 0x82990000)
        low = compute_shifter(0x0A, 0xFFFF, 1, 0, 0, ac=True)
        self.assertEqual(low.sr_result, 0x00007FFF)

    def test_exp_hi_extremes_and_sign_status(self) -> None:
        positive = compute_shifter(0x0C, 0x4000, 0, 0, 0, ss=True)
        negative = compute_shifter(0x0C, 0xFFFF, 0, 0, 0)
        self.assertEqual((positive.se_result, positive.ss_result), (0, False))
        self.assertEqual((negative.se_result, negative.ss_result), (0xF1, True))
        self.assertTrue(positive.se_write and positive.ss_write)

    def test_exp_hix_overflow_forces_plus_one_and_inverts_sign(self) -> None:
        overflow = compute_shifter(0x0D, 0xFA32, 0, 0, 0, av=True)
        ordinary = compute_shifter(0x0D, 0xE35B, 0, 0, 0, av=False)
        self.assertEqual((overflow.se_result, overflow.ss_result), (1, False))
        self.assertEqual((ordinary.se_result, ordinary.ss_result), (0xFE, True))

    def test_exp_lo_updates_only_after_all_sign_upper_half(self) -> None:
        held = compute_shifter(0x0E, 0xF6D4, 0xFC, 0, 0, ss=True)
        first_non_sign = compute_shifter(0x0E, 0x76D4, 0xF1, 0, 0, ss=True)
        four_signs = compute_shifter(0x0E, 0xF6D4, 0xF1, 0, 0, ss=True)
        all_signs = compute_shifter(0x0E, 0xFFFF, 0xF1, 0, 0, ss=True)
        self.assertFalse(held.se_write)
        self.assertEqual(held.se_result, 0xFC)
        self.assertEqual(first_non_sign.se_result, 0xF1)
        self.assertEqual(four_signs.se_result, 0xED)
        self.assertEqual(all_signs.se_result, 0xE1)
        self.assertFalse(all_signs.ss_write)

    def test_expadj_uses_signed_five_bit_comparison(self) -> None:
        updated = compute_shifter(0x0F, 0xF800, 0, 0, 0x10)
        held = compute_shifter(0x0F, 0x0100, 0, 0, updated.sb_result)
        self.assertTrue(updated.sb_write)
        self.assertEqual(updated.sb_result, 0x1C)
        self.assertFalse(held.sb_write)
        self.assertEqual(held.sb_result, 0x1C)

    def test_random_logical_duality_between_references(self) -> None:
        rng = random.Random(0x2100)
        for _ in range(1000):
            x = rng.randrange(0x10000)
            count = rng.randrange(-128, 112)
            high = compute_shifter(0x00, x, count & 0xFF, 0, 0)
            low = compute_shifter(0x02, x, (count + 16) & 0xFF, 0, 0)
            self.assertEqual(high.sr_result, low.sr_result)


if __name__ == "__main__":
    unittest.main()
