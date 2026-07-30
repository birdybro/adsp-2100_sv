from __future__ import annotations

import random
import unittest

from sim.reference_models.adsp2100_model.dag import (
    compute_dag,
    original_base_mask,
    reverse_address,
)


class DAGModelTests(unittest.TestCase):
    def test_bad_widths_fail_closed(self) -> None:
        for values in ((0x4000, 0, 0), (0, 0x4000, 0), (0, 0, 0x4000)):
            with self.assertRaises(ValueError):
                compute_dag(*values, dag1=True)

    def test_linear_post_modify_and_address_wrap(self) -> None:
        positive = compute_dag(0x1234, 3, 0, dag1=True)
        negative = compute_dag(0, 0x3FFF, 0, dag1=True)
        high_wrap = compute_dag(0x3FFF, 1, 0, dag1=False)
        self.assertEqual((positive.address, positive.next_i), (0x1234, 0x1237))
        self.assertEqual(negative.next_i, 0x3FFF)
        self.assertEqual(high_wrap.next_i, 0)
        self.assertFalse(positive.circular)
        self.assertTrue(positive.configuration_valid)

    def test_original_power_of_two_base_rule(self) -> None:
        self.assertEqual(original_base_mask(7), 0x3FF8)
        self.assertEqual(original_base_mask(8), 0x3FF0)
        valid = compute_dag(7, 1, 8, dag1=True)
        later_family_placement = compute_dag(8, 1, 8, dag1=True)
        self.assertEqual((valid.base, valid.next_i), (0, 0))
        self.assertFalse(later_family_placement.configuration_valid)

    def test_non_power_of_two_wraps_both_directions(self) -> None:
        upward = compute_dag(12, 3, 5, dag1=True)
        downward = compute_dag(8, 0x3FFE, 5, dag1=True)
        self.assertEqual((upward.base, upward.next_i), (8, 10))
        self.assertEqual(downward.next_i, 11)
        self.assertTrue(upward.configuration_valid)
        self.assertTrue(downward.configuration_valid)

    def test_original_manual_sequences(self) -> None:
        current = 5
        ascending = []
        for _ in range(7):
            ascending.append(current)
            current = compute_dag(current, 1, 3, dag1=True).next_i
        self.assertEqual(ascending, [5, 6, 4, 5, 6, 4, 5])

        current = 9
        stride = []
        for _ in range(6):
            stride.append(current)
            current = compute_dag(current, 0x3FFE, 5, dag1=True).next_i
        self.assertEqual(stride, [9, 12, 10, 8, 11, 9])

    def test_modify_equal_to_length_is_one_documented_wrap(self) -> None:
        result = compute_dag(5, 3, 3, dag1=True)
        self.assertTrue(result.configuration_valid)
        self.assertEqual(result.next_i, 5)

    def test_invalid_circular_configuration_is_exposed(self) -> None:
        too_large_modify = compute_dag(5, 4, 3, dag1=True)
        outside_buffer = compute_dag(15, 1, 5, dag1=True)
        self.assertFalse(too_large_modify.configuration_valid)
        self.assertFalse(outside_buffer.configuration_valid)

    def test_dag1_reverses_output_but_not_stored_i(self) -> None:
        result = compute_dag(
            0x0001,
            1,
            0,
            dag1=True,
            bit_reverse_enabled=True,
        )
        self.assertEqual(result.address, 0x2000)
        self.assertEqual(result.next_i, 2)
        self.assertEqual(reverse_address(0x1234), 0x0B12)

    def test_dag2_ignores_global_bit_reverse_mode(self) -> None:
        result = compute_dag(
            0x0001,
            1,
            0,
            dag1=False,
            bit_reverse_enabled=True,
        )
        self.assertEqual(result.address, 1)

    def test_random_valid_circular_results_remain_in_buffer(self) -> None:
        rng = random.Random(0x2100)
        for _ in range(10000):
            length = rng.randrange(1, 0x2000)
            alignment = 1 << length.bit_length()
            base = rng.randrange(0, 0x4000 - alignment + 1, alignment)
            i_value = base + rng.randrange(length)
            modify = rng.randrange(-length, length + 1)
            if not -0x2000 <= modify <= 0x1FFF:
                continue
            result = compute_dag(
                i_value,
                modify & 0x3FFF,
                length,
                dag1=bool(rng.getrandbits(1)),
                bit_reverse_enabled=bool(rng.getrandbits(1)),
            )
            self.assertTrue(result.configuration_valid)
            self.assertGreaterEqual(result.next_i, base)
            self.assertLess(result.next_i, base + length)


if __name__ == "__main__":
    unittest.main()
