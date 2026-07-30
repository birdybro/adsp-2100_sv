from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model.mac import (
    NEGATIVE_SATURATION,
    POSITIVE_SATURATION,
    compute_mac,
    saturate_mr,
)


class MACModelTests(unittest.TestCase):
    def test_non_mac_codes_and_bad_widths_fail_closed(self) -> None:
        for amf in (0x00, 0x10, 0x1F):
            with self.assertRaises(ValueError):
                compute_mac(amf, 0, 0, 0)
        with self.assertRaises(ValueError):
            compute_mac(0x04, 0, 0, 1 << 40)

    def test_signed_fractional_product_alignment(self) -> None:
        positive = compute_mac(0x04, 0x4000, 0x4000, 0)
        negative = compute_mac(0x04, 0x8000, 0x4000, 0)
        self.assertEqual(positive.result, 0x0020000000)
        self.assertEqual(positive.mf_result, 0x2000)
        self.assertEqual(negative.result, 0xFFC0000000)
        self.assertEqual(negative.mf_result, 0xC000)

    def test_all_four_signedness_modes(self) -> None:
        signed_unsigned = compute_mac(0x05, 0xFFFF, 0xFFFF, 0)
        unsigned_signed = compute_mac(0x06, 0xFFFF, 0xFFFF, 0)
        unsigned_unsigned = compute_mac(0x07, 0xFFFF, 0xFFFF, 0)
        self.assertEqual(signed_unsigned.result, (-(0xFFFF * 2)) & ((1 << 40) - 1))
        self.assertEqual(unsigned_signed.result, signed_unsigned.result)
        self.assertEqual(unsigned_unsigned.result, 0x01FFFC0002)

    def test_accumulate_and_subtract(self) -> None:
        added = compute_mac(0x08, 0x4000, 0x4000, 0x0001000000)
        subtracted = compute_mac(0x0C, 0x4000, 0x4000, 0x0001000000)
        self.assertEqual(added.result, 0x0021000000)
        self.assertEqual(subtracted.result, 0xFFE1000000)

    def test_unbiased_rounding_ties_to_even(self) -> None:
        even = compute_mac(0x02, 0, 0, 0x0000028000)
        odd = compute_mac(0x02, 0, 0, 0x0000038000)
        below = compute_mac(0x02, 0, 0, 0x0000027FFF)
        above = compute_mac(0x02, 0, 0, 0x0000028001)
        self.assertEqual(even.result, 0x0000020000)
        self.assertEqual(odd.result, 0x0000040000)
        self.assertEqual(below.result, 0x0000020000)
        self.assertEqual(above.result, 0x0000030000)
        self.assertTrue(even.rounded and odd.rounded)

    def test_mv_detects_32_bit_sign_extension_boundary(self) -> None:
        positive_limit = compute_mac(0x08, 0, 0, 0x007FFFFFFF)
        positive_overflow = compute_mac(0x08, 0, 0, 0x0080000000)
        negative_limit = compute_mac(0x08, 0, 0, 0xFF80000000)
        negative_overflow = compute_mac(0x08, 0, 0, 0xFF7FFFFFFF)
        self.assertFalse(positive_limit.mv or negative_limit.mv)
        self.assertTrue(positive_overflow.mv and negative_overflow.mv)

    def test_saturation_uses_existing_mv_and_mr2_sign(self) -> None:
        self.assertEqual(saturate_mr(0x0012345678, False), 0x0012345678)
        self.assertEqual(saturate_mr(0x0012345678, True), POSITIVE_SATURATION)
        self.assertEqual(saturate_mr(0xFF12345678, True), NEGATIVE_SATURATION)

    def test_rounding_operation_codes_use_signed_operands(self) -> None:
        multiplied = compute_mac(0x01, 0xFFFE, 0x4000, 0)
        accumulated = compute_mac(0x02, 0xFFFE, 0x4000, 0x0001000000)
        subtracted = compute_mac(0x03, 0xFFFE, 0x4000, 0x0001000000)
        self.assertEqual(multiplied.result, 0xFFFFFF0000)
        self.assertEqual(accumulated.result, 0x0000FF0000)
        self.assertEqual(subtracted.result, 0x0001010000)


if __name__ == "__main__":
    unittest.main()
