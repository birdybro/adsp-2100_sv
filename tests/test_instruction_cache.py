import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    CACHE_WORDS,
    ExactWord,
    InstructionCacheState,
    UNKNOWN,
    apply_instruction_cache_cycle,
    cache_region_contains,
    lookup_instruction_cache,
)


def _fill(state, address, instruction, *, address_known=True, data_known=True):
    return apply_instruction_cache_cycle(
        state,
        fill=True,
        fetch_address=(ExactWord(14, address) if address_known else UNKNOWN),
        fetch_instruction=(
            ExactWord(24, instruction) if data_known else UNKNOWN
        ),
    )


class InstructionCacheTests(unittest.TestCase):
    def test_machine_readable_contract_matches_implemented_boundary(self):
        path = Path("docs/generated/adsp2100_instruction_cache.yaml")
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(contract["device"], "ADSP-2100")
        self.assertEqual(contract["organization"]["entries"], CACHE_WORDS)
        self.assertEqual(contract["organization"]["instruction_width"], 24)
        self.assertEqual(contract["organization"]["address_width"], 14)
        self.assertEqual(
            contract["monitor_contract"]["maximum_valid_words"],
            CACHE_WORDS,
        )
        self.assertEqual(contract["open_question"], "OQ-008")

    def test_reset_invalidates_monitor_without_fabricating_data(self):
        state = _fill(InstructionCacheState.reset(), 0x123, 0xABCDEF).state
        reset = apply_instruction_cache_cycle(state, reset=True)
        self.assertEqual(reset.state.region_count, 0)
        self.assertEqual(reset.state.data_valid, (False,) * CACHE_WORDS)
        self.assertFalse(
            lookup_instruction_cache(reset.state, ExactWord(14, 0x123)).address_hit
        )

    def test_first_fill_uses_low_four_address_bits(self):
        result = _fill(InstructionCacheState.reset(), 0x123, 0xABCDEF)
        self.assertTrue(result.fill_accepted)
        self.assertTrue(result.region_restarted)
        self.assertEqual(result.state.region_start, 0x123)
        self.assertEqual(result.state.region_count, 1)
        lookup = lookup_instruction_cache(result.state, ExactWord(14, 0x123))
        self.assertTrue(lookup.address_hit)
        self.assertTrue(lookup.instruction_valid)
        self.assertEqual(lookup.instruction, ExactWord(24, 0xABCDEF))

    def test_sequential_fills_make_one_contiguous_sixteen_word_region(self):
        state = InstructionCacheState.reset()
        for offset in range(16):
            result = _fill(state, 0x200 + offset, 0x800000 + offset)
            state = result.state
        self.assertEqual(state.region_start, 0x200)
        self.assertEqual(state.region_count, 16)
        for offset in range(16):
            lookup = lookup_instruction_cache(
                state, ExactWord(14, 0x200 + offset)
            )
            self.assertEqual(lookup.instruction, ExactWord(24, 0x800000 + offset))
        self.assertFalse(cache_region_contains(state, 0x210))

    def test_seventeenth_sequential_fill_replaces_oldest_modulo_sixteen(self):
        state = InstructionCacheState.reset()
        for offset in range(17):
            result = _fill(state, 0x300 + offset, 0x900000 + offset)
            state = result.state
        self.assertTrue(result.oldest_replaced)
        self.assertEqual(state.region_start, 0x301)
        self.assertEqual(state.region_count, 16)
        self.assertFalse(
            lookup_instruction_cache(state, ExactWord(14, 0x300)).address_hit
        )
        newest = lookup_instruction_cache(state, ExactWord(14, 0x310))
        self.assertEqual(newest.instruction, ExactWord(24, 0x900010))

    def test_refetch_inside_region_preserves_monitor_and_updates_word(self):
        state = InstructionCacheState.reset()
        for offset in range(6):
            state = _fill(state, 0x100 + offset, offset).state
        result = _fill(state, 0x102, 0xFEDCBA)
        self.assertFalse(result.region_restarted)
        self.assertFalse(result.oldest_replaced)
        self.assertEqual(result.state.region_start, 0x100)
        self.assertEqual(result.state.region_count, 6)
        lookup = lookup_instruction_cache(result.state, ExactWord(14, 0x102))
        self.assertEqual(lookup.instruction, ExactWord(24, 0xFEDCBA))

    def test_discontinuous_fetch_discards_old_region(self):
        state = InstructionCacheState.reset()
        for offset in range(8):
            state = _fill(state, 0x80 + offset, offset).state
        result = _fill(state, 0x222, 0x112233)
        self.assertTrue(result.region_restarted)
        self.assertEqual(result.state.region_start, 0x222)
        self.assertEqual(result.state.region_count, 1)
        self.assertFalse(
            lookup_instruction_cache(result.state, ExactWord(14, 0x84)).address_hit
        )
        self.assertTrue(
            lookup_instruction_cache(result.state, ExactWord(14, 0x222)).address_hit
        )

    def test_program_address_wrap_is_contiguous(self):
        state = InstructionCacheState.reset()
        for address in (0x3FFE, 0x3FFF, 0x0000, 0x0001):
            state = _fill(state, address, address).state
        self.assertEqual(state.region_start, 0x3FFE)
        self.assertEqual(state.region_count, 4)
        for address in (0x3FFE, 0x3FFF, 0x0000, 0x0001):
            self.assertTrue(cache_region_contains(state, address))

    def test_unknown_address_invalidates_and_unknown_data_fails_closed(self):
        state = _fill(InstructionCacheState.reset(), 0x10, 0x123456).state
        unknown_data = _fill(state, 0x11, 0, data_known=False)
        lookup = lookup_instruction_cache(
            unknown_data.state, ExactWord(14, 0x11)
        )
        self.assertTrue(lookup.address_hit)
        self.assertFalse(lookup.instruction_valid)
        self.assertIs(lookup.instruction, UNKNOWN)
        unknown_address = _fill(
            unknown_data.state,
            0,
            0,
            address_known=False,
        )
        self.assertFalse(unknown_address.fill_accepted)
        self.assertTrue(unknown_address.region_restarted)
        self.assertEqual(unknown_address.state.region_count, 0)

    def test_width_errors_fail_closed(self):
        with self.assertRaises(ValueError):
            lookup_instruction_cache(
                InstructionCacheState.reset(), ExactWord(16, 0)
            )
        with self.assertRaises(ValueError):
            apply_instruction_cache_cycle(
                InstructionCacheState.reset(),
                fill=True,
                fetch_address=ExactWord(14, 0),
                fetch_instruction=ExactWord(16, 0),
            )


if __name__ == "__main__":
    unittest.main()
