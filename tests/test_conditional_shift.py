from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ASTATBit,
    ConditionInputs,
    ConditionalShiftState,
    DREG,
    DREGWrite,
    ExactWord,
    IF_CONDITION_MNEMONICS,
    UNKNOWN,
    apply_conditional_shift_cycle,
    decode_conditional_shift,
    evaluate_if_condition,
    is_conditional_shift_class,
    read_dreg,
)


LEGAL_XOPS = {0: DREG.SI, 2: DREG.AR, 3: DREG.MR0, 4: DREG.MR1,
              5: DREG.MR2, 6: DREG.SR0, 7: DREG.SR1}


def _opcode(sf: int, xop: int, condition: int) -> int:
    return 0x0E0000 | (sf << 11) | (xop << 8) | condition


def _setup_dreg(
    state: ConditionalShiftState,
    destination: DREG,
    value: int,
) -> ConditionalShiftState:
    return apply_conditional_shift_cycle(
        state,
        setup_dreg=DREGWrite(destination, ExactWord(16, value)),
    ).state


def _setup_astat(state: ConditionalShiftState, value: int) -> ConditionalShiftState:
    return apply_conditional_shift_cycle(
        state,
        setup_astat=ExactWord(8, value),
    ).state


def _sr(state: ConditionalShiftState, alternate: bool = False) -> int | None:
    bank = state.alternate if alternate else state.primary
    if not all(isinstance(value, ExactWord) for value in bank.sr):
        return None
    sr0, sr1 = bank.sr
    assert isinstance(sr0, ExactWord)
    assert isinstance(sr1, ExactWord)
    return (sr1.value << 16) | sr0.value


class ConditionalShiftTests(unittest.TestCase):
    def test_complete_type_16_partition_and_fields(self) -> None:
        legal = 0
        unsupported = 0
        for sf in range(16):
            for xop in range(8):
                for condition in range(16):
                    opcode = _opcode(sf, xop, condition)
                    self.assertTrue(is_conditional_shift_class(opcode))
                    action = decode_conditional_shift(opcode)
                    if xop in LEGAL_XOPS:
                        self.assertIsNotNone(action)
                        assert action is not None
                        self.assertEqual(action.sf, sf)
                        self.assertEqual(action.xop, xop)
                        self.assertEqual(action.source, LEGAL_XOPS[xop])
                        self.assertEqual(action.condition, condition)
                        legal += 1
                    else:
                        self.assertIsNone(action)
                        unsupported += 1
        self.assertEqual(legal, 1_792)
        self.assertEqual(unsupported, 256)

    def test_fixed_bits_and_nonclass_words_fail_closed(self) -> None:
        for opcode in (0, 0x0DFFFF, 0x0E0010, 0x0E0080, 0x0F0000, 0xFFFFFF):
            self.assertFalse(is_conditional_shift_class(opcode))
            self.assertIsNone(decode_conditional_shift(opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_conditional_shift(opcode)

    def test_all_if_predicates_gate_a_valid_one_cycle_boundary(self) -> None:
        astat_word = 0b01011101
        inputs = ConditionInputs(
            az=True,
            an=False,
            av=True,
            ac=True,
            as_flag=True,
            mv=True,
            not_counter_expired=True,
        )
        for condition, mnemonic in enumerate(IF_CONDITION_MNEMONICS):
            with self.subTest(condition=mnemonic):
                state = _setup_astat(ConditionalShiftState.reset(), astat_word)
                state = _setup_dreg(state, DREG.SI, 0x4000)
                state = _setup_dreg(state, DREG.SE, 0)
                state = _setup_dreg(state, DREG.SR0, 0x5678)
                state = _setup_dreg(state, DREG.SR1, 0x1234)
                before = _sr(state)
                result = apply_conditional_shift_cycle(
                    state,
                    execute=True,
                    opcode=_opcode(0, 0, condition),
                    not_counter_expired=True,
                )
                expected = evaluate_if_condition(condition, inputs)
                self.assertTrue(result.boundary_valid)
                self.assertTrue(result.condition_known)
                self.assertEqual(result.condition_true, expected)
                self.assertEqual(result.sr_write, expected)
                self.assertEqual(_sr(result.state), 0x40000000 if expected else before)

    def test_condition_false_preserves_every_shifter_destination_and_status(self) -> None:
        state = _setup_astat(ConditionalShiftState.reset(), 0x00)
        state = _setup_dreg(state, DREG.SI, 0x8000)
        state = _setup_dreg(state, DREG.SE, 0xFFF1)
        state = _setup_dreg(state, DREG.SR0, 0xAAAA)
        state = _setup_dreg(state, DREG.SR1, 0x5555)
        state = apply_conditional_shift_cycle(state, setup_sb=ExactWord(5, 0x10)).state
        for sf in range(16):
            result = apply_conditional_shift_cycle(
                state,
                execute=True,
                opcode=_opcode(sf, 0, 0),  # IF EQ, with AZ clear
            )
            self.assertTrue(result.boundary_valid)
            self.assertFalse(result.condition_true)
            self.assertEqual(result.state, state)
            self.assertFalse(
                result.sr_write or result.se_write or result.sb_write or result.ss_write
            )

    def test_shift_uses_selected_bank_se_and_cycle_start_sr(self) -> None:
        state = _setup_astat(ConditionalShiftState.reset(), 0x00)
        state = _setup_dreg(state, DREG.SI, 0x1234)
        state = _setup_dreg(state, DREG.SE, 0xFFFF)  # -1
        state = _setup_dreg(state, DREG.SR0, 0x00F0)
        state = _setup_dreg(state, DREG.SR1, 0x8000)
        result = apply_conditional_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(1, 0, 15),
        )
        self.assertEqual(_sr(result.state), 0x891A00F0)
        self.assertEqual(read_dreg(result.state.primary, DREG.SE), ExactWord(16, 0xFFFF))

    def test_exp_hix_exp_lo_and_expadj_write_exact_targets(self) -> None:
        state = _setup_astat(ConditionalShiftState.reset(), 1 << ASTATBit.AV)
        state = _setup_dreg(state, DREG.SI, 0x8000)
        hix = apply_conditional_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(0xD, 0, 15),
        )
        self.assertEqual(read_dreg(hix.state.primary, DREG.SE), ExactWord(16, 1))
        self.assertFalse(hix.state.status.astat.bit(ASTATBit.SS))
        self.assertTrue(hix.se_write)
        self.assertTrue(hix.ss_write)

        lo_state = _setup_dreg(hix.state, DREG.SE, 0xFFF1)
        lo_state = _setup_dreg(lo_state, DREG.SI, 0x0000)
        lo = apply_conditional_shift_cycle(
            lo_state,
            execute=True,
            opcode=_opcode(0xE, 0, 15),
        )
        self.assertEqual(read_dreg(lo.state.primary, DREG.SE), ExactWord(16, 0xFFE1))
        self.assertFalse(lo.ss_write)

        sb_state = apply_conditional_shift_cycle(
            lo.state,
            setup_sb=ExactWord(5, 0x10),
        ).state
        sb_state = _setup_dreg(sb_state, DREG.SI, 0x4000)
        adjusted = apply_conditional_shift_cycle(
            sb_state,
            execute=True,
            opcode=_opcode(0xF, 0, 15),
        )
        self.assertEqual(adjusted.state.primary.sb, ExactWord(5, 0x00))
        self.assertTrue(adjusted.sb_write)

    def test_selected_bank_write_and_inactive_bank_preservation(self) -> None:
        state = _setup_astat(ConditionalShiftState.reset(), 0)
        state = _setup_dreg(state, DREG.SI, 0x1111)
        state = _setup_dreg(state, DREG.SE, 0)
        state = _setup_dreg(state, DREG.SR0, 0xAAAA)
        state = _setup_dreg(state, DREG.SR1, 0xBBBB)
        state = apply_conditional_shift_cycle(
            state,
            setup_mstat=ExactWord(4, 1),
        ).state
        state = _setup_dreg(state, DREG.SI, 0x2222)
        state = _setup_dreg(state, DREG.SE, 0)
        state = _setup_dreg(state, DREG.SR0, 0xCCCC)
        state = _setup_dreg(state, DREG.SR1, 0xDDDD)
        result = apply_conditional_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(2, 0, 15),
        )
        self.assertEqual(_sr(result.state), 0xBBBBAAAA)
        self.assertEqual(_sr(result.state, alternate=True), 0x00002222)

    def test_unknown_predicate_or_operand_never_fabricates_state(self) -> None:
        unknown_condition = apply_conditional_shift_cycle(
            ConditionalShiftState.reset(),
            execute=True,
            opcode=_opcode(0, 0, 0),
        )
        self.assertTrue(unknown_condition.boundary_valid)
        self.assertFalse(unknown_condition.condition_known)
        self.assertIs(unknown_condition.state.primary.sr[0], UNKNOWN)
        self.assertIs(unknown_condition.state.primary.sr[1], UNKNOWN)

        state = _setup_astat(ConditionalShiftState.reset(), 1)
        unknown_source = apply_conditional_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(0xC, 0, 15),
        )
        self.assertIs(unknown_source.state.primary.se, UNKNOWN)
        self.assertIs(unknown_source.state.status.astat.bit(ASTATBit.SS), UNKNOWN)

    def test_reset_invalidates_status_without_erasing_banks(self) -> None:
        state = _setup_astat(ConditionalShiftState.reset(), 0xFF)
        state = _setup_dreg(state, DREG.SI, 0x1234)
        reset = apply_conditional_shift_cycle(state, reset=True)
        self.assertEqual(read_dreg(reset.state.primary, DREG.SI), ExactWord(16, 0x1234))
        self.assertFalse(reset.state.status.astat.is_fully_known)
        self.assertEqual(reset.state.status.mstat, ExactWord(4, 0))

    def test_invalid_and_conflicting_boundaries_are_atomic(self) -> None:
        state = _setup_astat(ConditionalShiftState.reset(), 0xFF)
        unsupported = apply_conditional_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 1, 15),
        )
        self.assertTrue(unsupported.unsupported_subencoding)
        self.assertTrue(unsupported.invalid_opcode)
        self.assertEqual(unsupported.state, state)
        conflict = apply_conditional_shift_cycle(
            state,
            execute=True,
            opcode=_opcode(0, 0, 15),
            setup_astat=ExactWord(8, 0),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)


if __name__ == "__main__":
    unittest.main()
