from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ADSP2100Model,
    ArchitecturalState,
    ExactWord,
    MemorySpace,
    ReservedOpcode,
    TransactionKind,
    UNKNOWN,
    UnsupportedFeature,
    UnsupportedOpcode,
    mask_to_width,
    sign_extend,
)


class ExactWidthTests(unittest.TestCase):
    def test_exact_word_rejects_truncation(self) -> None:
        with self.assertRaises(ValueError):
            ExactWord(16, 0x10000)
        with self.assertRaises(ValueError):
            ExactWord(16, -1)

    def test_explicit_truncation_and_signed_interpretation(self) -> None:
        self.assertEqual(mask_to_width(0x10000, 16), 0)
        self.assertEqual(sign_extend(0x7FFF, 16), 32767)
        self.assertEqual(sign_extend(0x8000, 16), -32768)
        self.assertEqual(sign_extend(0xFFFF, 16), -1)


class ArchitecturalFoundationTests(unittest.TestCase):
    def test_reset_preserves_documented_unknowns(self) -> None:
        state = ArchitecturalState.reset()
        self.assertEqual(state.pc, ExactWord(14, 4))
        self.assertEqual(state.mstat, ExactWord(4, 0))
        self.assertEqual(state.imask, ExactWord(4, 0))
        self.assertEqual(state.sstat, ExactWord(8, 0x55))
        self.assertIs(state.icntl, UNKNOWN)
        self.assertIs(state.astat, UNKNOWN)
        self.assertIs(state.primary.ax[0], UNKNOWN)
        self.assertEqual(state.pc_stack, ())
        self.assertEqual(state.loop_stack, ())

    def test_randomized_state_is_replayable(self) -> None:
        self.assertEqual(ArchitecturalState.randomized(2100), ArchitecturalState.randomized(2100))
        self.assertNotEqual(ArchitecturalState.randomized(2100), ArchitecturalState.randomized(2101))

    def test_nop_has_exact_pc_cycle_and_fetch_trace(self) -> None:
        model = ADSP2100Model()
        frame = model.step(0x000000)
        self.assertEqual(frame.pc_before, ExactWord(14, 4))
        self.assertEqual(frame.pc_after, ExactWord(14, 5))
        self.assertEqual(frame.instruction_cycles, 1)
        self.assertEqual(frame.transactions[0].space, MemorySpace.PROGRAM)
        self.assertEqual(frame.transactions[0].kind, TransactionKind.INSTRUCTION_FETCH)
        self.assertEqual(frame.transactions[0].width, 24)
        self.assertEqual(model.state.total_instruction_cycles, 1)

    def test_fetch_wait_extension_is_traced(self) -> None:
        model = ADSP2100Model()
        frame = model.step(0, fetch_wait_instruction_cycles=3)
        self.assertEqual(frame.instruction_cycles, 4)
        self.assertEqual(frame.transactions[0].wait_instruction_cycles, 3)
        self.assertEqual(model.state.total_instruction_cycles, 4)

    def test_trace_serialization_is_deterministic(self) -> None:
        left = ADSP2100Model().step(0).to_json()
        right = ADSP2100Model().step(0).to_json()
        self.assertEqual(left, right)
        self.assertIn('"opcode":"0x000000"', left)

    def test_unsupported_opcode_fails_without_state_change(self) -> None:
        model = ADSP2100Model()
        before = model.state
        with self.assertRaises(UnsupportedOpcode):
            model.step(1)
        self.assertEqual(model.state, before)
        self.assertEqual(model.trace, [])

    def test_reserved_original_and_unshown_words_fail_distinctly(self) -> None:
        for opcode in (0x010000, 0x020000, 0x030000, 0x0B0020, 0x000001):
            model = ADSP2100Model()
            with self.assertRaises(ReservedOpcode):
                model.step(opcode)
            self.assertEqual(model.trace, [])

    def test_loaded_program_supports_deterministic_single_step(self) -> None:
        model = ADSP2100Model()
        model.load_program([0, 0], origin=4)
        first = model.step_program()
        second = model.step_program(fetch_wait_instruction_cycles=1)
        self.assertEqual((first.pc_before.value, first.pc_after.value), (4, 5))
        self.assertEqual((second.pc_before.value, second.pc_after.value), (5, 6))
        self.assertEqual(model.state.total_instruction_cycles, 3)

    def test_program_and_data_image_widths_fail_closed(self) -> None:
        model = ADSP2100Model()
        with self.assertRaises(ValueError):
            model.load_program([0x1000000])
        with self.assertRaises(ValueError):
            model.load_data([0x10000])
        with self.assertRaises(UnsupportedFeature):
            model.step_program()


if __name__ == "__main__":
    unittest.main()
