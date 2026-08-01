from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ComputePMCacheState,
    DAGRegisterKind,
    DAGRegisterSetup,
    DREG,
    DREGWrite,
    ExactWord,
    UNKNOWN,
    apply_compute_pm_cache_cycle,
    lookup_instruction_cache,
)


def _cycle(state: ComputePMCacheState, **kwargs: object) -> ComputePMCacheState:
    return apply_compute_pm_cache_cycle(state, **kwargs).state


def _known_state() -> ComputePMCacheState:
    state = ComputePMCacheState.reset()
    state = _cycle(
        state,
        setup_dreg=DREGWrite(DREG.AX0, ExactWord(16, 2)),
    )
    state = _cycle(
        state,
        setup_dreg=DREGWrite(DREG.AY0, ExactWord(16, 3)),
    )
    state = _cycle(state, setup_astat=ExactWord(8, 0))
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
    state: ComputePMCacheState,
    address: int,
    instruction: int | object,
) -> ComputePMCacheState:
    return _cycle(
        state,
        external_fetch_fill=True,
        external_fetch_address=ExactWord(14, address),
        external_fetch_instruction=(
            ExactWord(24, instruction)
            if isinstance(instruction, int)
            else instruction
        ),
    )


class ComputePMCacheTests(unittest.TestCase):
    def test_prefilled_hit_supplies_instruction_with_compute_read(self) -> None:
        state = _fill(_known_state(), 0x222, 0xABCDEF)
        result = apply_compute_pm_cache_cycle(
            state,
            execute=True,
            opcode=0x526000,
            pm_read_data=ExactWord(24, 0xCAFE55),
            next_fetch_address=ExactWord(14, 0x222),
        )
        self.assertTrue(result.lookup_instruction_known)
        self.assertTrue(result.core.cache_instruction_selected)
        self.assertTrue(result.core.instruction_complete)
        self.assertTrue(result.instruction_from_cache)
        self.assertEqual(result.next_instruction, 0xABCDEF)

    def test_delayed_hit_is_latched_until_data_completion(self) -> None:
        state = _fill(_known_state(), 0x222, 0xABCDEF)
        issued = apply_compute_pm_cache_cycle(
            state,
            execute=True,
            opcode=0x526000,
            next_fetch_address=ExactWord(14, 0x222),
            pm_cycle_complete=False,
        )
        self.assertEqual(
            issued.state.pending_cache_instruction,
            ExactWord(24, 0xABCDEF),
        )
        held = apply_compute_pm_cache_cycle(
            issued.state,
            next_fetch_address=ExactWord(14, 0x333),
            pm_cycle_complete=False,
        )
        completed = apply_compute_pm_cache_cycle(
            held.state,
            pm_read_data=ExactWord(24, 0xCAFE55),
            next_fetch_address=ExactWord(14, 0x333),
        )
        self.assertTrue(completed.instruction_from_cache)
        self.assertEqual(completed.next_instruction, 0xABCDEF)
        self.assertIsNone(completed.state.pending_cache_instruction)

    def test_miss_recovery_fills_monitor_and_is_later_hit(self) -> None:
        issued = apply_compute_pm_cache_cycle(
            _known_state(),
            execute=True,
            opcode=0x526000,
            pm_read_data=ExactWord(24, 0xCAFE55),
            next_fetch_address=ExactWord(14, 0x222),
        )
        self.assertTrue(issued.core.recovery_required)
        recovered = apply_compute_pm_cache_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0x123456),
        )
        self.assertTrue(recovered.cache_fill_from_recovery)
        self.assertTrue(recovered.instruction_from_external)
        self.assertEqual(recovered.next_instruction, 0x123456)
        lookup = lookup_instruction_cache(
            recovered.state.cache,
            ExactWord(14, 0x222),
        )
        self.assertEqual(lookup.instruction, ExactWord(24, 0x123456))

    def test_unknown_cache_word_and_forced_fetch_require_recovery(self) -> None:
        unknown = _fill(_known_state(), 0x33, UNKNOWN)
        miss = apply_compute_pm_cache_cycle(
            unknown,
            execute=True,
            opcode=0x580000,
            next_fetch_address=ExactWord(14, 0x33),
        )
        self.assertTrue(miss.lookup_address_hit)
        self.assertFalse(miss.lookup_instruction_known)
        self.assertTrue(miss.core.recovery_required)

        known = _fill(_known_state(), 0x44, 0x111111)
        forced = apply_compute_pm_cache_cycle(
            known,
            execute=True,
            opcode=0x580000,
            next_fetch_address=ExactWord(14, 0x44),
            force_instruction_fetch=True,
        )
        self.assertTrue(forced.lookup_instruction_known)
        self.assertFalse(forced.instruction_from_cache)
        self.assertTrue(forced.core.recovery_required)

    def test_external_fill_priority_and_recovery_priority_are_explicit(self) -> None:
        state = _known_state()
        fill = apply_compute_pm_cache_cycle(
            state,
            execute=True,
            opcode=0x526000,
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, 0x200),
            external_fetch_instruction=ExactWord(24, 0xFEDCBA),
        )
        self.assertTrue(fill.external_fill_conflict)
        self.assertTrue(fill.external_fill_selected)
        self.assertFalse(fill.core.accepted)

        issued = apply_compute_pm_cache_cycle(
            fill.state,
            execute=True,
            opcode=0x526000,
            next_fetch_address=ExactWord(14, 0x123),
        )
        recovered = apply_compute_pm_cache_cycle(
            issued.state,
            pm_read_data=ExactWord(24, 0xAAAAAA),
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, 0x300),
            external_fetch_instruction=ExactWord(24, 0xBBBBBB),
        )
        self.assertTrue(recovered.external_fill_conflict)
        self.assertFalse(recovered.external_fill_selected)
        self.assertTrue(recovered.cache_fill_from_recovery)

    def test_reset_clears_core_cache_and_pending_instruction(self) -> None:
        state = _fill(_known_state(), 1, 0x123456)
        reset = apply_compute_pm_cache_cycle(
            state,
            reset=True,
            external_fetch_fill=True,
            external_fetch_address=ExactWord(14, 2),
            external_fetch_instruction=ExactWord(24, 0x654321),
        )
        self.assertEqual(reset.state, ComputePMCacheState.reset())
        self.assertFalse(reset.cache_fill or reset.integration_conflict)


if __name__ == "__main__":
    unittest.main()
