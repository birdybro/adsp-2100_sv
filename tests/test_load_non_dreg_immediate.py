from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from sim.reference_models.adsp2100_model.internal_move_slice import (
    InternalMoveSetup,
    read_internal_move_register,
)
from sim.reference_models.adsp2100_model.load_non_dreg_immediate import (
    LOAD_NON_DREG_IMMEDIATE_VALUE,
    LoadNonDregImmediateState,
    apply_load_non_dreg_immediate_cycle,
    decode_load_non_dreg_immediate as decode_model,
)
from sim.reference_models.adsp2100_model.model import ExactWord, UNKNOWN
from tools.generators.validate_load_non_dreg_immediate import (
    LoadNonDregImmediateValidationError,
    decode_load_non_dreg_immediate as decode_database,
    load_database,
    register_map,
    validate_database,
)


ROOT = Path(__file__).resolve().parents[1]


def _opcode(code: int, data: int) -> int:
    return (
        LOAD_NON_DREG_IMMEDIATE_VALUE
        | ((code >> 4) << 18)
        | ((data & 0x3FFF) << 4)
        | (code & 0xF)
    )


class LoadNonDregImmediateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = load_database()
        cls.fixture = json.loads(
            (
                ROOT / "tests/vectors/load_non_dreg_immediate_fixtures.json"
            ).read_text(encoding="utf-8")
        )

    def test_machine_readable_semantics_validate(self) -> None:
        validate_database(self.database)
        instruction = self.database["instruction"]
        self.assertEqual(instruction["legal_action_count"], 507_904)
        self.assertEqual(
            instruction["illegal_or_reserved_subencoding_count"],
            540_672,
        )

    def test_hand_checked_fixtures_match_independent_decoders(self) -> None:
        for case in self.fixture["hand_checked_cases"]:
            opcode = int(case["opcode"], 16)
            model = decode_model(opcode)
            database = decode_database(self.database, opcode)
            self.assertIsNotNone(model)
            self.assertIsNotNone(database)
            assert model is not None and database is not None
            self.assertEqual(model.data.value, int(case["data"], 16))
            self.assertEqual(model.register, case["register"])
            self.assertEqual(model.legal, case["legal"])
            self.assertEqual(database["data"], int(case["data"], 16))
            self.assertEqual(database["register"], case["register"])
            self.assertEqual(database["legal"], case["legal"])
            if not case["legal"]:
                self.assertEqual(model.invalid_reason, case["invalid_reason"])
                self.assertEqual(database["invalid_reason"], case["invalid_reason"])

    def test_entire_type_7_space_partitions_exactly(self) -> None:
        legal = 0
        invalid = 0
        for payload in range(1 << 20):
            opcode = LOAD_NON_DREG_IMMEDIATE_VALUE | payload
            model = decode_model(opcode)
            database = decode_database(self.database, opcode)
            self.assertIsNotNone(model)
            self.assertIsNotNone(database)
            assert model is not None and database is not None
            self.assertEqual(model.register_code, database["register_code"])
            self.assertEqual(model.data.value, database["data"])
            self.assertEqual(model.legal, database["legal"])
            self.assertEqual(model.invalid_reason, database["invalid_reason"])
            if model.legal:
                legal += 1
            else:
                invalid += 1
        self.assertEqual((legal, invalid), (507_904, 540_672))

    def test_non_type_7_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x2FFFFF, 0x400000, 0xFFFFFF):
            self.assertIsNone(decode_model(opcode))
            self.assertIsNone(decode_database(self.database, opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_model(opcode)
            with self.assertRaises(ValueError):
                decode_database(self.database, opcode)

    def test_every_legal_destination_narrows_the_raw_immediate(self) -> None:
        state = LoadNonDregImmediateState.reset()
        legal_codes = [
            code for code, metadata in register_map().items()
            if code >> 4 != 0 and metadata["register"] != "SSTAT"
        ]
        for code in legal_codes:
            for data in (0, 1, 0x1F, 0xFF, 0x1FFF, 0x2000, 0x3FFF):
                result = apply_load_non_dreg_immediate_cycle(
                    state,
                    execute=True,
                    opcode=_opcode(code, data),
                )
                self.assertTrue(result.boundary_valid)
                self.assertFalse(result.pm_data_access)
                self.assertFalse(result.dm_access)
                observed, _ = read_internal_move_register(
                    result.state.registers,
                    code,
                )
                self.assertIsNot(observed, UNKNOWN)
                assert isinstance(observed, ExactWord)
                metadata = register_map()[code]
                width = metadata["storage_width"]
                stored = data & ((1 << width) - 1)
                if metadata["move_access"].endswith("sign_extended"):
                    sign = 1 << (width - 1)
                    if stored & sign:
                        stored |= 0xFFFF ^ ((1 << width) - 1)
                self.assertEqual(observed.value, stored)
                state = result.state

    def test_cntr_load_pushes_old_valid_value_only(self) -> None:
        first = apply_load_non_dreg_immediate_cycle(
            LoadNonDregImmediateState.reset(),
            execute=True,
            opcode=_opcode(0x35, 0x0123),
        )
        self.assertFalse(first.count_stack_push)
        second = apply_load_non_dreg_immediate_cycle(
            first.state,
            execute=True,
            opcode=_opcode(0x35, 0x2345),
        )
        self.assertTrue(second.count_stack_push)
        self.assertEqual(second.count_stack_push_value, 0x0123)
        self.assertEqual(second.state.registers.cntr, 0x2345)
        self.assertEqual(second.state.registers.stacks.count_entries, (0x0123,))

    def test_invalid_conflict_reset_and_setup_preserve_contract(self) -> None:
        state = apply_load_non_dreg_immediate_cycle(
            LoadNonDregImmediateState.reset(),
            setup=InternalMoveSetup(0x10, 0x1234),
        ).state
        invalid = apply_load_non_dreg_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(0x00, 0x2222),
        )
        self.assertTrue(invalid.invalid_subencoding)
        self.assertEqual(invalid.state, state)
        wrong_class = apply_load_non_dreg_immediate_cycle(
            state,
            execute=True,
            opcode=0,
        )
        self.assertTrue(wrong_class.invalid_opcode)
        self.assertEqual(wrong_class.state, state)
        conflict = apply_load_non_dreg_immediate_cycle(
            state,
            execute=True,
            opcode=_opcode(0x10, 0x3333),
            setup=InternalMoveSetup(0x11, 0x4444),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertEqual(conflict.state, state)
        reset = apply_load_non_dreg_immediate_cycle(state, reset=True)
        self.assertEqual(reset.state, LoadNonDregImmediateState.reset())

    def test_corrupt_semantics_fail_validation(self) -> None:
        corrupt = copy.deepcopy(self.database)
        corrupt["instruction"]["legal_action_count"] += 1
        with self.assertRaises(LoadNonDregImmediateValidationError):
            validate_database(corrupt)

        isa_path = ROOT / "docs/generated/adsp2100_isa.yaml"
        isa = json.loads(isa_path.read_text(encoding="utf-8"))
        type_7 = isa["encoding_classes"][6]
        self.assertEqual(type_7["original_type"], 7)
        self.assertEqual(type_7["status"], "COMPLETE_BOUNDED_STATE")
        self.assertEqual(type_7["confidence"], "VERIFIED_PRIMARY")


if __name__ == "__main__":
    unittest.main()
