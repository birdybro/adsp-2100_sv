from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ComputationalBank,
    DREG,
    DREGWrite,
    DREGWriteConflict,
    ExactWord,
    UNKNOWN,
    apply_dreg_cycle,
    read_dreg,
)


def write(address: DREG, value: int) -> DREGWrite:
    return DREGWrite(address, ExactWord(16, value))


class RegisterBankModelTests(unittest.TestCase):
    def test_reset_unknowns_remain_independent_by_segment(self) -> None:
        bank = ComputationalBank()
        for address in DREG:
            self.assertIs(read_dreg(bank, address), UNKNOWN)

        result = apply_dreg_cycle(
            bank,
            ComputationalBank(),
            alternate_selected=False,
            writes=(write(DREG.MR0, 0x1234),),
        )
        self.assertEqual(read_dreg(result.primary, DREG.MR0), ExactWord(16, 0x1234))
        self.assertIs(read_dreg(result.primary, DREG.MR1), UNKNOWN)
        self.assertIs(read_dreg(result.primary, DREG.MR2), UNKNOWN)

    def test_all_dreg_codes_round_trip_in_both_banks(self) -> None:
        primary = ComputationalBank()
        alternate = ComputationalBank()
        for alternate_selected in (False, True):
            for code in DREG:
                value = 0x8080 | int(code)
                result = apply_dreg_cycle(
                    primary,
                    alternate,
                    alternate_selected=alternate_selected,
                    writes=(write(code, value),),
                )
                primary, alternate = result.primary, result.alternate

            selected = alternate if alternate_selected else primary
            for code in DREG:
                expected = 0x8080 | int(code)
                if code in (DREG.SE, DREG.MR2):
                    expected = 0xFF80 | int(code)
                self.assertEqual(read_dreg(selected, code), ExactWord(16, expected))

    def test_bank_switch_is_immediate_and_preserves_inactive_bank(self) -> None:
        primary = ComputationalBank()
        alternate = ComputationalBank()
        primary_result = apply_dreg_cycle(
            primary,
            alternate,
            alternate_selected=False,
            writes=(write(DREG.AX0, 0x1111),),
        )
        alternate_result = apply_dreg_cycle(
            primary_result.primary,
            primary_result.alternate,
            alternate_selected=True,
            writes=(write(DREG.AX0, 0xAAAA),),
        )
        primary_read = apply_dreg_cycle(
            alternate_result.primary,
            alternate_result.alternate,
            alternate_selected=False,
            read_addresses=(DREG.AX0,),
        )
        alternate_read = apply_dreg_cycle(
            alternate_result.primary,
            alternate_result.alternate,
            alternate_selected=True,
            read_addresses=(DREG.AX0,),
        )
        self.assertEqual(primary_read.reads, (ExactWord(16, 0x1111),))
        self.assertEqual(alternate_read.reads, (ExactWord(16, 0xAAAA),))

    def test_reads_observe_cycle_start_values(self) -> None:
        initialized = apply_dreg_cycle(
            ComputationalBank(),
            ComputationalBank(),
            alternate_selected=False,
            writes=(write(DREG.AX0, 0x1234),),
        )
        cycle = apply_dreg_cycle(
            initialized.primary,
            initialized.alternate,
            alternate_selected=False,
            read_addresses=(DREG.AX0,),
            writes=(write(DREG.AX0, 0x5678),),
        )
        self.assertEqual(cycle.reads, (ExactWord(16, 0x1234),))
        self.assertEqual(read_dreg(cycle.primary, DREG.AX0), ExactWord(16, 0x5678))

    def test_narrow_register_writes_truncate_and_reads_sign_extend(self) -> None:
        positive = apply_dreg_cycle(
            ComputationalBank(),
            ComputationalBank(),
            alternate_selected=False,
            writes=(
                write(DREG.SE, 0xAA7F),
                write(DREG.MR2, 0x5580),
            ),
        )
        self.assertEqual(read_dreg(positive.primary, DREG.SE), ExactWord(16, 0x007F))
        self.assertEqual(read_dreg(positive.primary, DREG.MR2), ExactWord(16, 0xFF80))

    def test_mr1_write_sign_extends_mr2_without_changing_mr0(self) -> None:
        initialized = apply_dreg_cycle(
            ComputationalBank(),
            ComputationalBank(),
            alternate_selected=False,
            writes=(write(DREG.MR0, 0xCAFE),),
        )
        negative = apply_dreg_cycle(
            initialized.primary,
            initialized.alternate,
            alternate_selected=False,
            writes=(write(DREG.MR1, 0x8000),),
        )
        self.assertEqual(read_dreg(negative.primary, DREG.MR0), ExactWord(16, 0xCAFE))
        self.assertEqual(read_dreg(negative.primary, DREG.MR1), ExactWord(16, 0x8000))
        self.assertEqual(read_dreg(negative.primary, DREG.MR2), ExactWord(16, 0xFFFF))

        positive = apply_dreg_cycle(
            negative.primary,
            negative.alternate,
            alternate_selected=False,
            writes=(write(DREG.MR1, 0x7FFF),),
        )
        self.assertEqual(read_dreg(positive.primary, DREG.MR2), ExactWord(16, 0x0000))

    def test_three_independent_same_cycle_writes_are_atomic(self) -> None:
        result = apply_dreg_cycle(
            ComputationalBank(),
            ComputationalBank(),
            alternate_selected=False,
            writes=(
                write(DREG.AX0, 0x1111),
                write(DREG.MX0, 0x2222),
                write(DREG.SI, 0x3333),
            ),
        )
        self.assertEqual(
            tuple(read_dreg(result.primary, code) for code in (DREG.AX0, DREG.MX0, DREG.SI)),
            (
                ExactWord(16, 0x1111),
                ExactWord(16, 0x2222),
                ExactWord(16, 0x3333),
            ),
        )

    def test_same_destination_and_mr1_mr2_collisions_fail_closed(self) -> None:
        for writes in (
            (write(DREG.AX0, 1), write(DREG.AX0, 2)),
            (write(DREG.MR1, 1), write(DREG.MR2, 2)),
            (write(DREG.MR2, 1), write(DREG.MR1, 2)),
        ):
            with self.assertRaises(DREGWriteConflict):
                apply_dreg_cycle(
                    ComputationalBank(),
                    ComputationalBank(),
                    alternate_selected=False,
                    writes=writes,
                )

    def test_wrong_write_width_and_code_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            DREGWrite(DREG.AX0, ExactWord(8, 0))
        with self.assertRaises(ValueError):
            DREGWrite(16, ExactWord(16, 0))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            read_dreg(ComputationalBank(), 16)


if __name__ == "__main__":
    unittest.main()
