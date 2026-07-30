from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    DREG,
    DREGWrite,
    ExactWord,
    ModeSliceInputs,
    ModeSliceState,
    StatusRegisters,
    apply_mode_slice_cycle,
    reverse_address,
)


def initialized_state() -> ModeSliceState:
    state = ModeSliceState()
    state = apply_mode_slice_cycle(
        state,
        ModeSliceInputs(
            astat_move=ExactWord(8, 0),
            mstat_move=ExactWord(4, 0),
        ),
    ).state
    return state


class ModeIntegrationModelTests(unittest.TestCase):
    def test_all_mstat_bits_reach_named_consumers_next_cycle(self) -> None:
        state = initialized_state()
        for value in range(16):
            write_cycle = apply_mode_slice_cycle(
                state,
                ModeSliceInputs(mstat_move=ExactWord(4, value)),
            )
            self.assertEqual(write_cycle.observation.alternate_bank, bool(state.status.mstat.value & 1))
            state = write_cycle.state
            observation = apply_mode_slice_cycle(state, ModeSliceInputs()).observation
            self.assertEqual(observation.alternate_bank, bool(value & 1))
            self.assertEqual(observation.bit_reverse, bool(value & 2))
            self.assertEqual(observation.overflow_latch, bool(value & 4))
            self.assertEqual(observation.saturate_ar, bool(value & 8))

    def test_bank_selection_preserves_both_computational_banks(self) -> None:
        state = initialized_state()
        state = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(
                dreg_write=DREGWrite(DREG.AX0, ExactWord(16, 0x1111))
            ),
        ).state
        state = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(mstat_move=ExactWord(4, 1)),
        ).state
        state = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(
                dreg_write=DREGWrite(DREG.AX0, ExactWord(16, 0xAAAA))
            ),
        ).state
        alternate = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(read_address=DREG.AX0),
        )
        self.assertEqual(alternate.observation.read_data, ExactWord(16, 0xAAAA))
        state = apply_mode_slice_cycle(
            alternate.state,
            ModeSliceInputs(mstat_move=ExactWord(4, 0)),
        ).state
        primary = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(read_address=DREG.AX0),
        )
        self.assertEqual(primary.observation.read_data, ExactWord(16, 0x1111))

    def test_bit_reverse_mode_changes_only_following_cycle_address(self) -> None:
        state = initialized_state()
        write_cycle = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(
                mstat_move=ExactWord(4, 2),
                dag_i=0x0003,
            ),
        )
        self.assertEqual(write_cycle.observation.dag.address, 0x0003)
        next_cycle = apply_mode_slice_cycle(
            write_cycle.state,
            ModeSliceInputs(dag_i=0x0003),
        )
        self.assertEqual(
            next_cycle.observation.dag.address,
            reverse_address(0x0003),
        )

    def test_saturation_and_sticky_av_use_current_mstat(self) -> None:
        state = initialized_state()
        state = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(mstat_move=ExactWord(4, 8)),
        ).state
        saturated = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(
                alu_execute=True,
                alu_amf=0x13,
                alu_x=0x7FFF,
                alu_y=1,
            ),
        )
        self.assertEqual(saturated.observation.alu.raw_result, 0x8000)
        self.assertEqual(saturated.observation.alu.destination_result, 0x7FFF)

        state = apply_mode_slice_cycle(
            saturated.state,
            ModeSliceInputs(mstat_move=ExactWord(4, 4)),
        ).state
        sticky = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(
                alu_execute=True,
                alu_amf=0x10,
                alu_y=0,
            ),
        )
        self.assertTrue(sticky.observation.alu.av)

    def test_reset_clears_modes_without_initializing_banks(self) -> None:
        state = ModeSliceState(status=StatusRegisters(
            mstat=ExactWord(4, 0xF),
            imask=ExactWord(4, 0),
        ))
        result = apply_mode_slice_cycle(
            state,
            ModeSliceInputs(reset=True),
        )
        self.assertEqual(result.state.status.mstat, ExactWord(4, 0))
        self.assertEqual(result.state.primary, state.primary)
        self.assertEqual(result.state.alternate, state.alternate)


if __name__ == "__main__":
    unittest.main()
