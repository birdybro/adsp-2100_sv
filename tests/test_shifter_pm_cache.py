from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    ShifterPMCacheState,
    UNKNOWN,
    apply_shifter_pm_cache_cycle,
    lookup_instruction_cache,
)


def _opcode(*, write: bool = False, dreg: DREG = DREG.AX0) -> int:
    return 0x110000 | (int(write) << 15) | (int(dreg) << 4)


def _cycle(state: ShifterPMCacheState, **kwargs: object) -> ShifterPMCacheState:
    return apply_shifter_pm_cache_cycle(state, **kwargs).state


def _known_state() -> ShifterPMCacheState:
    state = ShifterPMCacheState.reset()
    state = _cycle(
        state,
        setup_dreg=DREGWrite(DREG.AX0, ExactWord(16, 0x1234)),
    )
    state = _cycle(
        state,
        setup_dreg=DREGWrite(DREG.SI, ExactWord(16, 0x0101)),
    )
    state = _cycle(
        state,
        setup_dreg=DREGWrite(DREG.SE, ExactWord(16, 0)),
    )
    for kind, value in (
        (DAGRegisterKind.I, 0x0100),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 0),
    ):
        state = _cycle(
            state,
            setup_dag=DAGRegisterSetup(kind, 4, value),
        )
    return _cycle(state, setup_px=ExactWord(8, 0x5A))


def _fill(
    state: ShifterPMCacheState,
    address: int,
    instruction: int,
    *,
    known: bool = True,
) -> ShifterPMCacheState:
    return _cycle(
        state,
        external_fetch_fill=True,
        external_fetch_address=ExactWord(14, address),
        external_fetch_instruction=(
            ExactWord(24, instruction) if known else UNKNOWN
        ),
    )


class ShifterPMCacheTests(unittest.TestCase):
    def test_prefilled_hit_supplies_next_instruction_without_recovery(self):
        state = _fill(_known_state(), 0x0222, 0xABCDEF)
        result = apply_shifter_pm_cache_cycle(
            state,
            execute=True,
            opcode=_opcode(),
            pm_read_data=ExactWord(24, 0xCAFE55),
            next_fetch_address=ExactWord(14, 0x0222),
        )
        self.assertTrue(result.lookup_address_hit)
        self.assertTrue(result.lookup_instruction_known)
        self.assertTrue(result.core.cache_instruction_selected)
        self.assertTrue(result.core.instruction_complete)
        self.assertFalse(result.core.recovery_required)
        self.assertTrue(result.instruction_from_cache)
        self.assertFalse(result.instruction_from_external)
        self.assertTrue(result.next_instruction_known)
        self.assertEqual(result.next_instruction, 0xABCDEF)

    def test_miss_recovery_fills_cache_and_later_hit_uses_same_word(self):
        state = _known_state()
        issued = apply_shifter_pm_cache_cycle(
            state,
            execute=True,
            opcode=_opcode(),
            pm_read_data=ExactWord(24, 0xCAFE55),
            next_fetch_address=ExactWord(14, 0x0222),
        )
        self.assertTrue(issued.core.recovery_required)
        self.assertFalse(issued.core.instruction_complete)
        self.assertFalse(issued.cache_fill)

        recovered = apply_shifter_pm_cache_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0x123456),
            next_fetch_address=ExactWord(14, 0x0222),
        )
        self.assertTrue(recovered.core.recovery_fetch)
        self.assertTrue(recovered.cache_fill_from_recovery)
        self.assertTrue(recovered.cache_fill_accepted)
        self.assertTrue(recovered.instruction_from_external)
        self.assertEqual(recovered.next_instruction, 0x123456)
        lookup = lookup_instruction_cache(
            recovered.state.cache, ExactWord(14, 0x0222)
        )
        self.assertTrue(lookup.instruction_valid)
        self.assertEqual(lookup.instruction, ExactWord(24, 0x123456))

        hit = apply_shifter_pm_cache_cycle(
            recovered.state,
            execute=True,
            opcode=_opcode(write=True),
            next_fetch_address=ExactWord(14, 0x0222),
        )
        self.assertTrue(hit.core.cache_instruction_selected)
        self.assertFalse(hit.core.recovery_required)
        self.assertEqual(hit.next_instruction, 0x123456)

    def test_force_fetch_overrides_real_hit_and_refreshes_cache(self):
        state = _fill(_known_state(), 0x0101, 0x111111)
        issued = apply_shifter_pm_cache_cycle(
            state,
            execute=True,
            opcode=_opcode(write=True),
            next_fetch_address=ExactWord(14, 0x0101),
            force_instruction_fetch=True,
        )
        self.assertTrue(issued.lookup_instruction_known)
        self.assertFalse(issued.instruction_from_cache)
        self.assertTrue(issued.core.recovery_required)
        recovered = apply_shifter_pm_cache_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0x222222),
        )
        self.assertTrue(recovered.instruction_from_external)
        lookup = lookup_instruction_cache(
            recovered.state.cache, ExactWord(14, 0x0101)
        )
        self.assertEqual(lookup.instruction, ExactWord(24, 0x222222))

    def test_address_hit_with_unknown_data_still_requires_recovery(self):
        state = _fill(_known_state(), 0x0033, 0, known=False)
        result = apply_shifter_pm_cache_cycle(
            state,
            execute=True,
            opcode=_opcode(),
            pm_read_data=ExactWord(24, 0),
            next_fetch_address=ExactWord(14, 0x0033),
        )
        self.assertTrue(result.lookup_address_hit)
        self.assertFalse(result.lookup_instruction_known)
        self.assertTrue(result.core.recovery_required)

    def test_external_fill_conflict_has_fill_priority_and_is_atomic(self):
        state = _known_state()
        result = apply_shifter_pm_cache_cycle(
            state,
            execute=True,
            opcode=_opcode(),
            pm_read_data=ExactWord(24, 0xABCD00),
            next_fetch_address=ExactWord(14, 0x0100),
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, 0x0200),
            external_fetch_instruction=ExactWord(24, 0xFEDCBA),
        )
        self.assertTrue(result.external_fill_conflict)
        self.assertTrue(result.integration_conflict)
        self.assertTrue(result.external_fill_selected)
        self.assertFalse(result.core.accepted or result.core.pm_select)
        self.assertEqual(result.state.core, state.core)
        lookup = lookup_instruction_cache(
            result.state.cache, ExactWord(14, 0x0200)
        )
        self.assertEqual(lookup.instruction, ExactWord(24, 0xFEDCBA))

    def test_recovery_has_priority_over_conflicting_external_fill(self):
        issued = apply_shifter_pm_cache_cycle(
            _known_state(),
            execute=True,
            opcode=_opcode(),
            pm_read_data=ExactWord(24, 0),
            next_fetch_address=ExactWord(14, 0x0123),
        )
        recovered = apply_shifter_pm_cache_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0xAAAAAA),
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, 0x0300),
            external_fetch_instruction=ExactWord(24, 0xBBBBBB),
        )
        self.assertTrue(recovered.external_fill_conflict)
        self.assertFalse(recovered.external_fill_selected)
        self.assertTrue(recovered.cache_fill_from_recovery)
        self.assertTrue(
            lookup_instruction_cache(
                recovered.state.cache, ExactWord(14, 0x0123)
            ).instruction_valid
        )
        self.assertFalse(
            lookup_instruction_cache(
                recovered.state.cache, ExactWord(14, 0x0300)
            ).address_hit
        )

    def test_sequential_external_fills_and_oldest_replacement_feed_hits(self):
        state = _known_state()
        for offset in range(17):
            state = _fill(state, 0x0100 + offset, 0x800000 + offset)
        self.assertEqual(state.cache.region_start, 0x0101)
        self.assertEqual(state.cache.region_count, 16)
        self.assertFalse(
            lookup_instruction_cache(state.cache, ExactWord(14, 0x0100)).address_hit
        )
        newest = apply_shifter_pm_cache_cycle(
            state,
            execute=True,
            opcode=_opcode(write=True),
            next_fetch_address=ExactWord(14, 0x0110),
        )
        self.assertTrue(newest.instruction_from_cache)
        self.assertEqual(newest.next_instruction, 0x800010)

    def test_unknown_recovery_address_invalidates_monitor(self):
        state = _fill(_known_state(), 0x0010, 0x123456)
        issued = apply_shifter_pm_cache_cycle(
            state,
            execute=True,
            opcode=_opcode(),
            pm_read_data=ExactWord(24, 0),
            next_fetch_address=UNKNOWN,
        )
        recovered = apply_shifter_pm_cache_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0xFFFFFF),
        )
        self.assertTrue(recovered.cache_region_restarted)
        self.assertFalse(recovered.cache_fill_accepted)
        self.assertEqual(recovered.state.cache.region_count, 0)
        self.assertFalse(recovered.next_instruction_known)

    def test_reset_clears_core_recovery_and_cache_monitor(self):
        state = _fill(_known_state(), 1, 0x123456)
        reset = apply_shifter_pm_cache_cycle(
            state,
            reset=True,
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, 2),
            external_fetch_instruction=ExactWord(24, 0x654321),
        )
        self.assertEqual(reset.state, ShifterPMCacheState.reset())
        self.assertFalse(reset.cache_fill or reset.integration_conflict)

    def test_width_contracts_fail_closed(self):
        with self.assertRaises(ValueError):
            apply_shifter_pm_cache_cycle(
                ShifterPMCacheState.reset(),
                next_fetch_address=ExactWord(16, 0),
            )
        with self.assertRaises(ValueError):
            apply_shifter_pm_cache_cycle(
                ShifterPMCacheState.reset(),
                external_fetch_fill=True,
                external_fetch_address=ExactWord(16, 0),
                external_fetch_instruction=ExactWord(24, 0),
            )


if __name__ == "__main__":
    unittest.main()
