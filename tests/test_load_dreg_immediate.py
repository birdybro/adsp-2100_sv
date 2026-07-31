from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DREG,
    DREGWrite,
    ExactWord,
    LoadDregImmediateState,
    UNKNOWN,
    apply_load_dreg_immediate_cycle,
    decode_load_dreg_immediate,
    read_dreg,
)


def _opcode(destination: DREG, data: int) -> int:
    return 0x400000 | ((data & 0xFFFF) << 4) | int(destination)


class LoadDregImmediateTests(unittest.TestCase):
    def test_all_field_defined_words_decode_exactly(self) -> None:
        count = 0
        for destination in DREG:
            for data in range(0x10000):
                action = decode_load_dreg_immediate(_opcode(destination, data))
                self.assertIsNotNone(action)
                assert action is not None
                self.assertEqual(action.destination, destination)
                self.assertEqual(action.data, ExactWord(16, data))
                count += 1
        self.assertEqual(count, 1_048_576)

    def test_non_type_6_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x3FFFFF, 0x500000, 0xFFFFFF):
            self.assertIsNone(decode_load_dreg_immediate(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_load_dreg_immediate(opcode)

    def test_reset_selects_primary_without_initializing_banks(self) -> None:
        state = LoadDregImmediateState.reset()
        self.assertEqual(state.mstat, ExactWord(4, 0))
        self.assertIs(read_dreg(state.primary, DREG.AX0), UNKNOWN)
        self.assertIs(read_dreg(state.alternate, DREG.AX0), UNKNOWN)

    def test_every_destination_writes_only_selected_bank(self) -> None:
        state = LoadDregImmediateState.reset()
        for bank in (0, 1):
            state = apply_load_dreg_immediate_cycle(
                state,
                setup_mstat=ExactWord(4, bank),
            ).state
            for destination in DREG:
                data = 0x8100 | (bank << 7) | int(destination)
                result = apply_load_dreg_immediate_cycle(
                    state,
                    execute=True,
                    opcode=_opcode(destination, data),
                )
                self.assertTrue(result.boundary_valid)
                self.assertFalse(result.pm_data_access)
                self.assertFalse(result.dm_access)
                selected = result.state.alternate if bank else result.state.primary
                expected = data
                if destination in (DREG.SE, DREG.MR2):
                    narrow = data & 0xFF
                    expected = narrow | (0xFF00 if narrow & 0x80 else 0)
                self.assertEqual(
                    read_dreg(selected, destination),
                    ExactWord(16, expected),
                )
                state = result.state

    def test_mr1_load_sign_fills_mr2(self) -> None:
        state = LoadDregImmediateState.reset()
        for value, expected_mr2 in ((0x7FFF, 0x0000), (0x8000, 0xFFFF)):
            result = apply_load_dreg_immediate_cycle(
                state,
                execute=True,
                opcode=_opcode(DREG.MR1, value),
            )
            self.assertEqual(
                read_dreg(result.state.primary, DREG.MR2),
                ExactWord(16, expected_mr2),
            )
            state = result.state

    def test_invalid_and_conflicting_cycles_preserve_state(self) -> None:
        state = apply_load_dreg_immediate_cycle(
            LoadDregImmediateState.reset(),
            setup_dreg=DREGWrite(DREG.AX0, ExactWord(16, 0x1234)),
        ).state
        invalid = apply_load_dreg_immediate_cycle(
            state,
            execute=True,
            opcode=0,
        )
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)
        conflict = apply_load_dreg_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(DREG.AX0, 0x5678),
            setup_dreg=DREGWrite(DREG.AX1, ExactWord(16, 0x9ABC)),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)


if __name__ == "__main__":
    unittest.main()
