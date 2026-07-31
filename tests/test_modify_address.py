from __future__ import annotations

import copy
import json
from pathlib import Path
import random
import unittest

from sim.reference_models.adsp2100_model import (
    MODIFY_ADDRESS_VALUE,
    DAGRegisterKind,
    DAGRegisterSetup,
    DAGRegisterState,
    apply_modify_address_cycle,
    decode_modify_address,
)
from tools.generators.validate_modify_address import (
    ModifyAddressValidationError,
    decode_selection,
    load_database,
    validate_database,
)


ROOT = Path(__file__).resolve().parents[1]


class ModifyAddressSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.database = load_database()
        cls.fixture = json.loads(
            (
                ROOT / "tests/vectors/modify_address_fixtures.json"
            ).read_text(encoding="utf-8")
        )

    def test_machine_readable_semantics_validate(self) -> None:
        validate_database(self.database)
        self.assertIn("ADI-UM-1989", self.fixture["source"])

    def test_independent_hand_fixtures_match_decode(self) -> None:
        for case in self.fixture["hand_checked_cases"]:
            opcode = int(case["opcode"], 16)
            selection = decode_modify_address(opcode)
            generated = decode_selection(self.database, opcode)
            self.assertIsNotNone(selection)
            self.assertIsNotNone(generated)
            assert selection is not None and generated is not None
            self.assertEqual(selection.dag, case["dag"])
            self.assertEqual(selection.i_address, case["i_address"])
            self.assertEqual(selection.m_address, case["m_address"])
            self.assertEqual(generated["i_address"], case["i_address"])
            self.assertEqual(generated["m_address"], case["m_address"])

    def test_all_32_encodings_select_same_dag_pairs(self) -> None:
        seen: set[tuple[int, int]] = set()
        for payload in range(32):
            selection = decode_modify_address(
                MODIFY_ADDRESS_VALUE | payload
            )
            self.assertIsNotNone(selection)
            assert selection is not None
            self.assertEqual(selection.dag, payload >> 4)
            self.assertEqual(selection.i_local, (payload >> 2) & 3)
            self.assertEqual(selection.m_local, payload & 3)
            self.assertEqual(
                selection.i_address // 4,
                selection.m_address // 4,
            )
            seen.add((selection.i_address, selection.m_address))
        self.assertEqual(len(seen), 32)

    def test_non_type_21_and_width_errors_fail_closed(self) -> None:
        for opcode in (0, 0x08FFFF, 0x090020, 0x0A0000, 0xFFFFFF):
            self.assertIsNone(decode_modify_address(opcode))
            self.assertIsNone(decode_selection(self.database, opcode))
        for opcode in (-1, 0x1000000):
            with self.assertRaises(ValueError):
                decode_modify_address(opcode)
            with self.assertRaises(ValueError):
                decode_selection(self.database, opcode)

    def test_reset_setup_linear_modify_and_selected_i_only(self) -> None:
        state = DAGRegisterState(
            i=tuple(range(8)),
            m=tuple(range(8)),
            l=tuple(range(8)),
        )
        state = apply_modify_address_cycle(state, reset=True).state
        self.assertEqual(state, DAGRegisterState())

        for kind, address, value in (
            (DAGRegisterKind.I, 1, 0x0100),
            (DAGRegisterKind.M, 1, 3),
            (DAGRegisterKind.L, 1, 0),
        ):
            state = apply_modify_address_cycle(
                state,
                setup=DAGRegisterSetup(kind, address, value),
            ).state
        before = state
        result = apply_modify_address_cycle(
            state,
            execute=True,
            opcode=0x090005,
        )
        self.assertTrue(result.boundary_valid)
        self.assertTrue(result.operands_valid)
        self.assertTrue(result.configuration_valid)
        self.assertTrue(result.writeback_valid)
        self.assertEqual(result.old_i, 0x0100)
        self.assertEqual(result.next_i, 0x0103)
        self.assertEqual(result.state.i[1], 0x0103)
        self.assertEqual(result.state.i[:1] + result.state.i[2:],
                         before.i[:1] + before.i[2:])
        self.assertEqual(result.state.m, before.m)
        self.assertEqual(result.state.l, before.l)
        self.assertFalse(result.pm_data_access)
        self.assertFalse(result.dm_access)

    def test_negative_and_original_circular_modification(self) -> None:
        state = DAGRegisterState(
            i=(7, None, None, None, 0, None, None, None),
            m=(1, None, None, None, 0x3FFF, None, None, None),
            l=(8, None, None, None, 0, None, None, None),
        )
        circular = apply_modify_address_cycle(
            state,
            execute=True,
            opcode=0x090000,
        )
        self.assertTrue(circular.configuration_valid)
        self.assertEqual(circular.next_i, 0)
        self.assertEqual(circular.state.i[0], 0)

        negative = apply_modify_address_cycle(
            circular.state,
            execute=True,
            opcode=0x090010,
        )
        self.assertTrue(negative.writeback_valid)
        self.assertEqual(negative.old_i, 0)
        self.assertEqual(negative.next_i, 0x3FFF)
        self.assertEqual(negative.state.i[4], 0x3FFF)

    def test_unknown_or_unsupported_configuration_invalidates_result(self) -> None:
        unknown_source = DAGRegisterState(
            i=(5,) + (None,) * 7,
            l=(0,) + (None,) * 7,
        )
        unknown = apply_modify_address_cycle(
            unknown_source,
            execute=True,
            opcode=0x090000,
        )
        self.assertTrue(unknown.boundary_valid)
        self.assertFalse(unknown.operands_valid)
        self.assertIsNone(unknown.state.i[0])

        invalid_configuration = DAGRegisterState(
            i=(8,) + (None,) * 7,
            m=(1,) + (None,) * 7,
            l=(8,) + (None,) * 7,
        )
        invalid = apply_modify_address_cycle(
            invalid_configuration,
            execute=True,
            opcode=0x090000,
        )
        self.assertTrue(invalid.operands_valid)
        self.assertFalse(invalid.configuration_valid)
        self.assertFalse(invalid.writeback_valid)
        self.assertIsNone(invalid.state.i[0])

    def test_invalid_opcode_and_setup_collision_preserve_state(self) -> None:
        state = DAGRegisterState(
            i=tuple(range(8)),
            m=tuple(range(8)),
            l=(0,) * 8,
        )
        invalid = apply_modify_address_cycle(
            state,
            execute=True,
            opcode=0x0A0000,
        )
        self.assertTrue(invalid.invalid_opcode)
        self.assertEqual(invalid.state, state)

        conflict = apply_modify_address_cycle(
            state,
            execute=True,
            opcode=0x090000,
            setup=DAGRegisterSetup(DAGRegisterKind.I, 0, 0x1234),
        )
        self.assertTrue(conflict.integration_conflict)
        self.assertFalse(conflict.boundary_valid)
        self.assertEqual(conflict.state, state)

    def test_deterministic_random_state_invariants(self) -> None:
        rng = random.Random(0x210021)
        state = DAGRegisterState()
        for cycle in range(20_000):
            choice = rng.randrange(12)
            if cycle == 0 or choice == 0:
                result = apply_modify_address_cycle(state, reset=True)
            elif choice < 7:
                result = apply_modify_address_cycle(
                    state,
                    setup=DAGRegisterSetup(
                        DAGRegisterKind(rng.randrange(3)),
                        rng.randrange(8),
                        rng.randrange(0x4000),
                    ),
                )
            elif choice < 11:
                result = apply_modify_address_cycle(
                    state,
                    execute=True,
                    opcode=MODIFY_ADDRESS_VALUE | rng.randrange(32),
                )
            else:
                result = apply_modify_address_cycle(
                    state,
                    execute=True,
                    opcode=0x0A0000 | rng.randrange(32),
                )
            for bank in (result.state.i, result.state.m, result.state.l):
                self.assertEqual(len(bank), 8)
                for value in bank:
                    self.assertTrue(value is None or 0 <= value < 0x4000)
            state = result.state

    def test_corrupt_semantics_fail_validation(self) -> None:
        wrong_mask = copy.deepcopy(self.database)
        wrong_mask["instruction"]["opcode_mask"] = "0xfffff0"
        with self.assertRaises(ModifyAddressValidationError):
            validate_database(wrong_mask)

        memory_access = copy.deepcopy(self.database)
        memory_access["instruction"]["dm_transfer"] = "READ"
        with self.assertRaises(ModifyAddressValidationError):
            validate_database(memory_access)

        wrong_field = copy.deepcopy(self.database)
        wrong_field["fields"][1]["lsb"] = 1
        with self.assertRaises(ModifyAddressValidationError):
            validate_database(wrong_field)


if __name__ == "__main__":
    unittest.main()
