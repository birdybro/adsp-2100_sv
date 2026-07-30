from __future__ import annotations

import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model import (
    ALUStatusUpdate,
    ASTATBit,
    ASTATState,
    ExactWord,
    ModeControl,
    StatusCycleInputs,
    StatusRegisters,
    StatusStackEntry,
    UNKNOWN,
    apply_status_cycle,
    compute_alu,
)


ROOT = Path(__file__).resolve().parents[1]


class StatusMetadataTests(unittest.TestCase):
    def test_machine_readable_fields_match_original_registers(self) -> None:
        data = json.loads(
            (ROOT / "docs/generated/adsp2100_status_registers.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["device"], "ADSP-2100")
        self.assertEqual(
            [field["name"] for field in data["registers"]["ASTAT"]["fields"]],
            ["AZ", "AN", "AV", "AC", "AS", "AQ", "MV", "SS"],
        )
        self.assertEqual(
            [field["name"] for field in data["registers"]["MSTAT"]["fields"]],
            [
                "SECONDARY_REGISTER_BANK",
                "BIT_REVERSE",
                "OVERFLOW_LATCH",
                "AR_SATURATE",
            ],
        )
        self.assertEqual(data["registers"]["ASTAT"]["reset"], "UNKNOWN")
        self.assertEqual(data["registers"]["MSTAT"]["reset"], 0)
        self.assertEqual(data["registers"]["SSTAT"]["reset"], 0x55)
        self.assertEqual(data["registers"]["ICNTL"]["reset"], "UNKNOWN")
        self.assertEqual(data["registers"]["IMASK"]["reset"], 0)
        self.assertEqual(
            data["registers"]["IMASK"]["nested_entry_masks_by_irq"],
            [0xE, 0xC, 0x8, 0x0],
        )
        self.assertEqual(
            [entry["action"] for entry in data["mode_control_codes"]],
            ["NO_CHANGE", "NO_CHANGE", "DEACTIVATE", "ACTIVATE"],
        )


class StatusModelTests(unittest.TestCase):
    def test_reset_clears_mstat_without_inventing_astat(self) -> None:
        before = StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, 0xA5)),
            mstat=ExactWord(4, 0xF),
        )
        result = apply_status_cycle(
            before,
            StatusCycleInputs(
                reset=True,
                astat_move=ExactWord(8, 0x00),
                mstat_move=ExactWord(4, 0xF),
            ),
        )
        self.assertEqual(result.state.mstat, ExactWord(4, 0))
        self.assertEqual(result.state.imask, ExactWord(4, 0))
        self.assertIs(result.state.icntl, UNKNOWN)
        self.assertTrue(all(bit is UNKNOWN for bit in result.state.astat.bits))
        self.assertFalse(result.write_conflict)

    def test_exact_move_widths_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            StatusCycleInputs(astat_move=ExactWord(16, 0))
        with self.assertRaises(ValueError):
            StatusCycleInputs(mstat_move=ExactWord(8, 0))
        with self.assertRaises(ValueError):
            StatusCycleInputs(icntl_move=ExactWord(4, 0))
        with self.assertRaises(ValueError):
            StatusCycleInputs(imask_move=ExactWord(5, 0))
        with self.assertRaises(ValueError):
            StatusCycleInputs(interrupt_entry=4)

    def test_direct_moves_replace_exact_storage(self) -> None:
        result = apply_status_cycle(
            StatusRegisters.reset(),
            StatusCycleInputs(
                astat_move=ExactWord(8, 0x96),
                mstat_move=ExactWord(4, 0xD),
                icntl_move=ExactWord(5, 0x15),
                imask_move=ExactWord(4, 0xB),
            ),
        )
        self.assertEqual(result.state.astat.to_word(), ExactWord(8, 0x96))
        self.assertEqual(result.state.mstat, ExactWord(4, 0xD))
        self.assertEqual(result.state.icntl, ExactWord(5, 0x15))
        self.assertEqual(result.state.imask, ExactWord(4, 0xB))
        self.assertTrue(result.state.alternate_bank)
        self.assertFalse(result.state.bit_reverse)
        self.assertTrue(result.state.overflow_latch)
        self.assertTrue(result.state.saturate_ar)

    def test_both_no_change_mode_codes_preserve_every_bit(self) -> None:
        initial = StatusRegisters(mstat=ExactWord(4, 0xA))
        for code in (ModeControl.NO_CHANGE_ZERO, ModeControl.NO_CHANGE_ONE):
            result = apply_status_cycle(
                initial,
                StatusCycleInputs(mode_controls=(code, code, code, code)),
            )
            self.assertEqual(result.state.mstat, initial.mstat)

    def test_mode_controls_independently_clear_and_set_all_bits(self) -> None:
        for bit in range(4):
            controls = [ModeControl.NO_CHANGE_ZERO] * 4
            controls[bit] = ModeControl.ACTIVATE
            set_result = apply_status_cycle(
                StatusRegisters.reset(),
                StatusCycleInputs(mode_controls=tuple(controls)),
            )
            self.assertEqual(set_result.state.mstat, ExactWord(4, 1 << bit))
            controls[bit] = ModeControl.DEACTIVATE
            clear_result = apply_status_cycle(
                set_result.state,
                StatusCycleInputs(mode_controls=tuple(controls)),
            )
            self.assertEqual(clear_result.state.mstat, ExactWord(4, 0))

    def test_standard_alu_updates_only_documented_fields(self) -> None:
        initial = StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, 0xF0)),
        )
        update = ALUStatusUpdate(
            az=True,
            an=False,
            av=True,
            ac=False,
        )
        result = apply_status_cycle(initial, StatusCycleInputs(alu=update))
        self.assertEqual(result.state.astat.to_word(), ExactWord(8, 0xF5))

        abs_result = apply_status_cycle(
            result.state,
            StatusCycleInputs(
                alu=ALUStatusUpdate(
                    az=False,
                    an=True,
                    av=False,
                    ac=True,
                    as_value=False,
                )
            ),
        )
        self.assertEqual(abs_result.state.astat.to_word(), ExactWord(8, 0xEA))

    def test_divide_mac_and_shifter_update_only_their_bits(self) -> None:
        state = StatusRegisters(astat=ASTATState.from_word(ExactWord(8, 0)))
        state = apply_status_cycle(
            state, StatusCycleInputs(divide_aq=True)
        ).state
        state = apply_status_cycle(state, StatusCycleInputs(mac_mv=True)).state
        state = apply_status_cycle(
            state, StatusCycleInputs(shifter_ss=True)
        ).state
        self.assertEqual(state.astat.to_word(), ExactWord(8, 0xE0))
        state = apply_status_cycle(
            state, StatusCycleInputs(divide_aq=False)
        ).state
        state = apply_status_cycle(state, StatusCycleInputs(mac_mv=False)).state
        state = apply_status_cycle(
            state, StatusCycleInputs(shifter_ss=False)
        ).state
        self.assertEqual(state.astat.to_word(), ExactWord(8, 0))

    def test_automatic_updates_preserve_unrelated_unknown_bits(self) -> None:
        result = apply_status_cycle(
            StatusRegisters.reset(),
            StatusCycleInputs(
                alu=ALUStatusUpdate(
                    az=True,
                    an=False,
                    av=False,
                    ac=True,
                )
            ),
        )
        self.assertEqual(
            result.state.astat.bits[:4],
            (True, False, False, True),
        )
        self.assertTrue(all(bit is UNKNOWN for bit in result.state.astat.bits[4:]))
        with self.assertRaises(ValueError):
            result.state.astat.to_word()

    def test_sticky_av_uses_mstat_and_direct_write_is_able_to_clear(self) -> None:
        state = StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, 1 << ASTATBit.AV)),
            mstat=ExactWord(4, 0x4),
        )
        alu = compute_alu(
            0x10,
            0,
            1,
            previous_av=bool(state.astat.bit(ASTATBit.AV)),
            sticky_av=state.overflow_latch,
        )
        state = apply_status_cycle(
            state,
            StatusCycleInputs(
                alu=ALUStatusUpdate(
                    alu.az,
                    alu.an,
                    alu.av,
                    alu.ac,
                    alu.as_value if alu.as_write else None,
                )
            ),
        ).state
        self.assertIs(state.astat.bit(ASTATBit.AV), True)
        state = apply_status_cycle(
            state, StatusCycleInputs(astat_move=ExactWord(8, 0))
        ).state
        self.assertIs(state.astat.bit(ASTATBit.AV), False)

    def test_conflicting_astat_sources_suppress_all_writes(self) -> None:
        initial = StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, 0x3C)),
            mstat=ExactWord(4, 0x5),
        )
        cases = (
            StatusCycleInputs(
                astat_move=ExactWord(8, 0),
                mac_mv=True,
                mstat_move=ExactWord(4, 0xF),
            ),
            StatusCycleInputs(
                divide_aq=True,
                shifter_ss=True,
                mstat_move=ExactWord(4, 0xF),
            ),
        )
        for inputs in cases:
            result = apply_status_cycle(initial, inputs)
            self.assertTrue(result.write_conflict)
            self.assertEqual(result.state, initial)

    def test_move_and_active_mode_control_conflict_but_no_change_does_not(self) -> None:
        initial = StatusRegisters(mstat=ExactWord(4, 0xA))
        conflict = apply_status_cycle(
            initial,
            StatusCycleInputs(
                mstat_move=ExactWord(4, 0x5),
                mode_controls=(
                    ModeControl.ACTIVATE,
                    ModeControl.NO_CHANGE_ZERO,
                    ModeControl.NO_CHANGE_ZERO,
                    ModeControl.NO_CHANGE_ZERO,
                ),
            ),
        )
        self.assertTrue(conflict.write_conflict)
        self.assertEqual(conflict.state, initial)

        legal = apply_status_cycle(
            initial,
            StatusCycleInputs(
                mstat_move=ExactWord(4, 0x5),
                mode_controls=(ModeControl.NO_CHANGE_ONE,) * 4,
            ),
        )
        self.assertFalse(legal.write_conflict)
        self.assertEqual(legal.state.mstat, ExactWord(4, 0x5))

    def test_interrupt_entry_pushes_old_state_and_applies_nesting_masks(self) -> None:
        for nesting, expected_masks in (
            (False, (0, 0, 0, 0)),
            (True, (0xE, 0xC, 0x8, 0x0)),
        ):
            for level, expected_mask in enumerate(expected_masks):
                state = StatusRegisters(
                    astat=ASTATState.from_word(ExactWord(8, 0xA5)),
                    mstat=ExactWord(4, 0x9),
                    icntl=ExactWord(5, 0x10 if nesting else 0),
                    imask=ExactWord(4, 0xF),
                )
                result = apply_status_cycle(
                    state,
                    StatusCycleInputs(interrupt_entry=level),
                )
                self.assertEqual(
                    result.status_push,
                    StatusStackEntry(
                        state.astat,
                        ExactWord(4, 0x9),
                        ExactWord(4, 0xF),
                    ),
                )
                self.assertEqual(result.state.imask, ExactWord(4, expected_mask))
                self.assertEqual(result.state.astat, state.astat)
                self.assertEqual(result.state.mstat, state.mstat)
                self.assertEqual(result.state.icntl, state.icntl)

    def test_unknown_icntl_makes_interrupt_entry_mask_unknown(self) -> None:
        state = StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, 0)),
            imask=ExactWord(4, 0xF),
        )
        result = apply_status_cycle(
            state,
            StatusCycleInputs(interrupt_entry=2),
        )
        self.assertIs(result.state.imask, UNKNOWN)
        self.assertEqual(result.status_push.imask, ExactWord(4, 0xF))

    def test_status_restore_restores_three_stacked_registers_only(self) -> None:
        state = StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, 0x12)),
            mstat=ExactWord(4, 0x3),
            icntl=ExactWord(5, 0x1F),
            imask=ExactWord(4, 0x4),
        )
        entry = StatusStackEntry(
            ASTATState.from_word(ExactWord(8, 0xA6)),
            ExactWord(4, 0xC),
            ExactWord(4, 0xB),
        )
        result = apply_status_cycle(
            state,
            StatusCycleInputs(status_restore=entry),
        )
        self.assertEqual(result.state.astat, entry.astat)
        self.assertEqual(result.state.mstat, entry.mstat)
        self.assertEqual(result.state.imask, entry.imask)
        self.assertEqual(result.state.icntl, state.icntl)

    def test_interrupt_entry_aborts_ordinary_status_writes(self) -> None:
        state = StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, 0x5A)),
            mstat=ExactWord(4, 0x3),
            icntl=ExactWord(5, 0x10),
            imask=ExactWord(4, 0xF),
        )
        result = apply_status_cycle(
            state,
            StatusCycleInputs(
                astat_move=ExactWord(8, 0),
                mstat_move=ExactWord(4, 0xF),
                icntl_move=ExactWord(5, 0),
                imask_move=ExactWord(4, 0),
                interrupt_entry=1,
            ),
        )
        self.assertFalse(result.write_conflict)
        self.assertEqual(result.status_push.astat, state.astat)
        self.assertEqual(result.state.astat, state.astat)
        self.assertEqual(result.state.mstat, state.mstat)
        self.assertEqual(result.state.icntl, state.icntl)
        self.assertEqual(result.state.imask, ExactWord(4, 0xC))

    def test_restore_collision_suppresses_all_state_changes(self) -> None:
        state = StatusRegisters(
            astat=ASTATState.from_word(ExactWord(8, 0x5A)),
            mstat=ExactWord(4, 0x3),
            icntl=ExactWord(5, 0x10),
            imask=ExactWord(4, 0xF),
        )
        entry = StatusStackEntry(
            ASTATState.from_word(ExactWord(8, 0)),
            ExactWord(4, 0),
            ExactWord(4, 0),
        )
        for inputs in (
            StatusCycleInputs(
                status_restore=entry,
                imask_move=ExactWord(4, 1),
            ),
            StatusCycleInputs(status_restore=entry, interrupt_entry=0),
        ):
            result = apply_status_cycle(state, inputs)
            self.assertTrue(result.write_conflict)
            self.assertEqual(result.state, state)
            self.assertIsNone(result.status_push)


if __name__ == "__main__":
    unittest.main()
