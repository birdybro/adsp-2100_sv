from __future__ import annotations

import copy
import json
from pathlib import Path
import random
import unittest

from sim.reference_models.adsp2100_model import (
    ASTATState,
    ComputationalBank,
    ExactWord,
    MR_SATURATION_OPCODE,
    MRSaturationSliceInputs,
    MRSaturationSliceState,
    StatusRegisters,
    UNKNOWN,
    apply_mr_saturation_slice_cycle,
    decode_mr_saturation,
    saturate_mr,
)
from tools.generators.validate_mr_saturation import (
    MRSaturationValidationError,
    load_database,
    validate_database,
)


ROOT = Path(__file__).resolve().parents[1]


def _known_status(astat: int, mstat: int) -> StatusRegisters:
    return StatusRegisters(
        astat=ASTATState.from_word(ExactWord(8, astat)),
        mstat=ExactWord(4, mstat),
    )


def _bank(mr: int) -> ComputationalBank:
    return ComputationalBank(
        mr=(
            ExactWord(16, mr & 0xFFFF),
            ExactWord(16, (mr >> 16) & 0xFFFF),
            ExactWord(8, (mr >> 32) & 0xFF),
        )
    )


def _mr_value(bank: ComputationalBank) -> int | None:
    if not all(isinstance(value, ExactWord) for value in bank.mr):
        return None
    mr0, mr1, mr2 = bank.mr
    assert isinstance(mr0, ExactWord)
    assert isinstance(mr1, ExactWord)
    assert isinstance(mr2, ExactWord)
    return (mr2.value << 32) | (mr1.value << 16) | mr0.value


class MRSaturationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = load_database()
        cls.fixture = json.loads(
            (
                ROOT / "tests/vectors/mr_saturation_fixtures.json"
            ).read_text(encoding="utf-8")
        )

    def test_machine_readable_semantics_validate(self) -> None:
        validate_database(self.database)
        self.assertEqual(
            self.database["instruction"]["opcode_value"],
            "0x050000",
        )
        self.assertEqual(
            self.database["instruction"]["status_flags_written"],
            [],
        )
        integration = json.loads(
            (
                ROOT
                / "docs/generated/adsp2100_mr_saturation_slice.yaml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            integration["scope"],
            "BOUNDED_TYPE_25_STATEFUL_MR_SATURATION_INTEGRATION",
        )
        self.assertEqual(
            integration["cycle_boundary"]["source_reads"],
            "CYCLE_START",
        )
        self.assertEqual(
            integration["fail_closed_boundaries"][
                "TYPE_25_WITH_SETUP_ACTION"
            ],
            "OQ-018_INTEGRATION_CONFLICT",
        )

    def test_exact_decode_and_hand_checked_fixture(self) -> None:
        instruction = self.fixture["instruction"]
        self.assertEqual(
            int(instruction["opcode"], 16),
            MR_SATURATION_OPCODE,
        )
        self.assertEqual(
            MR_SATURATION_OPCODE.to_bytes(3, "big").hex(),
            instruction["program_word_bytes_big_endian"],
        )
        self.assertTrue(decode_mr_saturation(MR_SATURATION_OPCODE))
        for opcode in self.fixture["invalid_neighbors"]:
            self.assertFalse(decode_mr_saturation(int(opcode, 16)))
        for case in self.fixture["hand_checked_cases"]:
            self.assertEqual(
                saturate_mr(int(case["mr"], 16), case["mv"]),
                int(case["result"], 16),
            )

    def test_mv_clear_is_one_cycle_boundary_without_state_change(self) -> None:
        state = MRSaturationSliceState(
            status=_known_status(0x00, 0),
            primary=_bank(0x123456789A),
            alternate=_bank(0xABCDEF0123),
        )
        result = apply_mr_saturation_slice_cycle(
            state,
            MRSaturationSliceInputs(
                execute=True,
                opcode=MR_SATURATION_OPCODE,
            ),
        )
        self.assertTrue(result.boundary_valid)
        self.assertFalse(result.condition)
        self.assertFalse(result.mr_write)
        self.assertEqual(result.state, state)

    def test_mv_set_saturates_both_signs_without_changing_astat(self) -> None:
        for mr, expected in (
            (0x0012345678, 0x007FFFFFFF),
            (0xFF12345678, 0xFF80000000),
        ):
            state = MRSaturationSliceState(
                status=_known_status(0x40, 0),
                primary=_bank(mr),
                alternate=_bank(0x13579BDF02),
            )
            result = apply_mr_saturation_slice_cycle(
                state,
                MRSaturationSliceInputs(
                    execute=True,
                    opcode=MR_SATURATION_OPCODE,
                ),
            )
            self.assertTrue(result.mr_write)
            self.assertEqual(_mr_value(result.state.primary), expected)
            self.assertEqual(result.state.alternate, state.alternate)
            self.assertEqual(result.state.status, state.status)

    def test_cycle_start_bank_selection_isolated_to_alternate(self) -> None:
        state = MRSaturationSliceState(
            status=_known_status(0x40, 1),
            primary=_bank(0x0011111111),
            alternate=_bank(0xFF22222222),
        )
        result = apply_mr_saturation_slice_cycle(
            state,
            MRSaturationSliceInputs(
                execute=True,
                opcode=MR_SATURATION_OPCODE,
            ),
        )
        self.assertTrue(result.selected_bank_alternate)
        self.assertEqual(result.state.primary, state.primary)
        self.assertEqual(
            _mr_value(result.state.alternate),
            0xFF80000000,
        )

    def test_reset_and_unknown_sources_are_not_coerced_to_zero(self) -> None:
        state = MRSaturationSliceState(
            status=_known_status(0x40, 1),
            primary=_bank(0x0011111111),
            alternate=_bank(0xFF22222222),
        )
        reset = apply_mr_saturation_slice_cycle(
            state,
            MRSaturationSliceInputs(reset=True),
        )
        self.assertEqual(reset.state.status.mstat.value, 0)
        self.assertEqual(reset.state.primary, state.primary)
        self.assertEqual(reset.state.alternate, state.alternate)

        unknown = apply_mr_saturation_slice_cycle(
            MRSaturationSliceState(),
            MRSaturationSliceInputs(
                execute=True,
                opcode=MR_SATURATION_OPCODE,
            ),
        )
        self.assertIs(unknown.condition, UNKNOWN)
        self.assertIs(unknown.mr_write, UNKNOWN)
        self.assertEqual(unknown.state.primary.mr, (UNKNOWN,) * 3)

    def test_invalid_and_setup_collision_fail_closed(self) -> None:
        state = MRSaturationSliceState(
            status=_known_status(0x40, 0),
            primary=_bank(0x0012345678),
            alternate=_bank(0xFF12345678),
        )
        invalid = apply_mr_saturation_slice_cycle(
            state,
            MRSaturationSliceInputs(execute=True, opcode=0x050001),
        )
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)

        collision = apply_mr_saturation_slice_cycle(
            state,
            MRSaturationSliceInputs(
                execute=True,
                opcode=MR_SATURATION_OPCODE,
                mr_setup_write=ExactWord(40, 0x5555555555),
            ),
        )
        self.assertTrue(collision.integration_conflict)
        self.assertFalse(collision.boundary_valid)
        self.assertEqual(collision.state, state)

    def test_deterministic_random_bank_and_status_invariants(self) -> None:
        rng = random.Random(0x210025)
        state = MRSaturationSliceState(
            status=_known_status(0, 0),
            primary=_bank(0),
            alternate=_bank(0),
        )
        for _ in range(20_000):
            choice = rng.randrange(8)
            if choice == 0:
                inputs = MRSaturationSliceInputs(
                    astat_write=ExactWord(8, rng.randrange(1 << 8)),
                )
            elif choice == 1:
                inputs = MRSaturationSliceInputs(
                    mstat_write=ExactWord(4, rng.randrange(1 << 4)),
                )
            elif choice == 2:
                inputs = MRSaturationSliceInputs(
                    mr_setup_write=ExactWord(
                        40,
                        rng.randrange(1 << 40),
                    ),
                )
            elif choice < 6:
                inputs = MRSaturationSliceInputs(
                    execute=True,
                    opcode=MR_SATURATION_OPCODE,
                )
            elif choice == 6:
                inputs = MRSaturationSliceInputs(
                    execute=True,
                    opcode=0x050001,
                )
            else:
                inputs = MRSaturationSliceInputs(
                    execute=True,
                    opcode=MR_SATURATION_OPCODE,
                    astat_write=ExactWord(
                        8,
                        rng.randrange(1 << 8),
                    ),
                )
            before = state
            result = apply_mr_saturation_slice_cycle(state, inputs)
            state = result.state
            self.assertFalse(result.internal_conflict)
            if result.invalid_opcode or result.integration_conflict:
                self.assertEqual(state, before)
            if result.boundary_valid:
                self.assertEqual(state.status, before.status)
                untouched = (
                    state.primary
                    if result.selected_bank_alternate
                    else state.alternate
                )
                old_untouched = (
                    before.primary
                    if result.selected_bank_alternate
                    else before.alternate
                )
                self.assertEqual(untouched, old_untouched)

    def test_corrupt_semantics_fail_validation(self) -> None:
        wrong_opcode = copy.deepcopy(self.database)
        wrong_opcode["instruction"]["opcode_value"] = "0x050001"
        with self.assertRaises(MRSaturationValidationError):
            validate_database(wrong_opcode)

        invented_flag = copy.deepcopy(self.database)
        invented_flag["instruction"]["status_flags_written"] = ["MV"]
        with self.assertRaises(MRSaturationValidationError):
            validate_database(invented_flag)


if __name__ == "__main__":
    unittest.main()
