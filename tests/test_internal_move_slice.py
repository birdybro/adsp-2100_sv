from __future__ import annotations

import unittest

from sim.reference_models.adsp2100_model import (
    ExactWord,
    InternalMoveSetup,
    InternalMoveSliceState,
    UNKNOWN,
    apply_internal_move_cycle,
    read_internal_move_register,
    register_code_by_name,
)


READABLE = register_code_by_name(writable=False)
WRITABLE = register_code_by_name(writable=True)


def _opcode(destination: str, source: str) -> int:
    destination_code = WRITABLE[destination]
    source_code = READABLE[source]
    return (
        0x0D0000
        | ((destination_code >> 4) << 10)
        | ((source_code >> 4) << 8)
        | ((destination_code & 0xF) << 4)
        | (source_code & 0xF)
    )


def _setup(
    state: InternalMoveSliceState,
    register: str,
    value: int,
) -> InternalMoveSliceState:
    result = apply_internal_move_cycle(
        state,
        setup=InternalMoveSetup(WRITABLE[register], value),
    )
    if result.bank_selection_unknown:
        raise AssertionError("test setup unexpectedly lost bank selection")
    return result.state


def _expected_destination_read(register: str, value: int) -> int:
    if register in ("SE", "MR2"):
        narrow = value & 0xFF
        return narrow | (0xFF00 if narrow & 0x80 else 0)
    if (
        (len(register) == 2 and register[0] in ("I", "L") and register[1].isdigit())
        or register == "CNTR"
    ):
        return value & 0x3FFF
    if len(register) == 2 and register[0] == "M" and register[1].isdigit():
        narrow = value & 0x3FFF
        return narrow | (0xC000 if narrow & 0x2000 else 0)
    widths = {
        "ASTAT": 8,
        "MSTAT": 4,
        "IMASK": 4,
        "ICNTL": 5,
        "PX": 8,
    }
    if register in widths:
        return value & ((1 << widths[register]) - 1)
    if register == "SB":
        narrow = value & 0x1F
        return narrow | (0xFFE0 if narrow & 0x10 else 0)
    return value & 0xFFFF


def _fully_initialized_state(*, alternate_selected: bool = False) -> InternalMoveSliceState:
    state = InternalMoveSliceState.reset()
    for code, name in sorted((code, name) for name, code in WRITABLE.items() if code >> 4):
        if name == "MSTAT":
            continue
        state = _setup(state, name, (code * 0x421 + 0x1357) & 0xFFFF)

    for name, code in sorted(WRITABLE.items(), key=lambda item: item[1]):
        if code >> 4 == 0:
            state = _setup(state, name, (code * 0x811 + 0x2468) & 0xFFFF)
    state = _setup(state, "SB", 0x0007)

    state = _setup(state, "MSTAT", 1)
    for name, code in sorted(WRITABLE.items(), key=lambda item: item[1]):
        if code >> 4 == 0:
            state = _setup(state, name, (code * 0x911 + 0xA468) & 0xFFFF)
    state = _setup(state, "SB", 0x0017)
    state = _setup(state, "MSTAT", int(alternate_selected))
    return state


class InternalMoveSliceTests(unittest.TestCase):
    def test_reset_preserves_documented_unknowns(self) -> None:
        state = InternalMoveSliceState.reset()
        self.assertEqual(state.mstat, 0)
        self.assertEqual(state.imask, 0)
        self.assertIsNone(state.astat)
        self.assertIsNone(state.icntl)
        self.assertIsNone(state.cntr)
        self.assertIsNone(state.px)
        self.assertEqual(state.sstat, 0x55)
        value, provisional = read_internal_move_register(state, READABLE["AX0"])
        self.assertIs(value, UNKNOWN)
        self.assertFalse(provisional)

    def test_unknown_source_invalidates_destination_without_fabrication(self) -> None:
        state = _setup(InternalMoveSliceState.reset(), "AR", 0x1234)
        result = apply_internal_move_cycle(
            state,
            execute=True,
            opcode=_opcode("AR", "AX0"),
        )
        self.assertTrue(result.boundary_valid)
        self.assertFalse(result.source_valid)
        value, _ = read_internal_move_register(result.state, READABLE["AR"])
        self.assertIs(value, UNKNOWN)

    def test_status_reads_use_labeled_oq016_zero_extension(self) -> None:
        state = InternalMoveSliceState.reset()
        for register, value in (
            ("ASTAT", 0xA5),
            ("MSTAT", 0xB),
            ("IMASK", 0xD),
            ("ICNTL", 0x15),
        ):
            state = _setup(state, register, value)
            read, provisional = read_internal_move_register(
                state,
                READABLE[register],
            )
            self.assertEqual(read, ExactWord(16, value))
            self.assertTrue(provisional)
        sstat, provisional = read_internal_move_register(state, READABLE["SSTAT"])
        self.assertEqual(sstat, ExactWord(16, 0x55))
        self.assertTrue(provisional)

    def test_cycle_start_bank_selection_and_mr1_side_effect(self) -> None:
        state = InternalMoveSliceState.reset()
        state = _setup(state, "AX0", 0x8001)
        state = _setup(state, "MSTAT", 1)
        state = _setup(state, "AX0", 0x1234)
        state = _setup(state, "MSTAT", 0)
        result = apply_internal_move_cycle(
            state,
            execute=True,
            opcode=_opcode("MSTAT", "AX0"),
        )
        self.assertEqual(result.source_data, 0x8001)
        self.assertEqual(result.state.mstat, 1)
        result = apply_internal_move_cycle(
            result.state,
            execute=True,
            opcode=_opcode("MR1", "AX0"),
        )
        self.assertEqual(result.source_data, 0x1234)
        mr2, _ = read_internal_move_register(result.state, READABLE["MR2"])
        self.assertEqual(mr2, ExactWord(16, 0x0000))
        state = _setup(result.state, "AX0", 0x9234)
        result = apply_internal_move_cycle(
            state,
            execute=True,
            opcode=_opcode("MR1", "AX0"),
        )
        mr2, _ = read_internal_move_register(result.state, READABLE["MR2"])
        self.assertEqual(mr2, ExactWord(16, 0xFFFF))

    def test_cntr_load_pushes_old_count_and_updates_sstat(self) -> None:
        state = InternalMoveSliceState.reset()
        state = _setup(state, "AX0", 0x0001)
        for value in range(6):
            state = _setup(state, "AX0", 0x1200 + value)
            result = apply_internal_move_cycle(
                state,
                execute=True,
                opcode=_opcode("CNTR", "AX0"),
            )
            state = result.state
        self.assertEqual(state.cntr, 0x1205)
        self.assertEqual(state.stacks.count_entries, (0x1200, 0x1201, 0x1202, 0x1203))
        self.assertTrue(state.stacks.count_overflow)
        self.assertEqual(state.sstat & 0x0C, 0x08)

    def test_every_legal_move_executes_from_known_state(self) -> None:
        count = 0
        for alternate_selected in (False, True):
            base = _fully_initialized_state(alternate_selected=alternate_selected)
            for destination, destination_code in WRITABLE.items():
                for source, source_code in READABLE.items():
                    before, provisional = read_internal_move_register(base, source_code)
                    self.assertIsInstance(before, ExactWord)
                    assert isinstance(before, ExactWord)
                    result = apply_internal_move_cycle(
                        base,
                        execute=True,
                        opcode=_opcode(destination, source),
                    )
                    self.assertTrue(result.boundary_valid)
                    self.assertTrue(result.source_valid)
                    self.assertEqual(result.source_data, before.value)
                    self.assertEqual(
                        result.source_extension_provisional,
                        provisional,
                    )
                    after, _ = read_internal_move_register(
                        result.state,
                        destination_code,
                    )
                    self.assertEqual(
                        after,
                        ExactWord(
                            16,
                            _expected_destination_read(
                                destination,
                                before.value,
                            ),
                        ),
                        f"{destination} = {source}, bank={int(alternate_selected)}",
                    )
                    count += 1
        self.assertEqual(count, 4512)

    def test_invalid_and_conflicting_requests_preserve_state(self) -> None:
        state = _fully_initialized_state()
        for opcode in (0x000000, 0x0D04C0, 0x0D0C20):
            result = apply_internal_move_cycle(
                state,
                execute=True,
                opcode=opcode,
            )
            self.assertEqual(result.state, state)
            self.assertFalse(result.boundary_valid)
        result = apply_internal_move_cycle(
            state,
            execute=True,
            opcode=_opcode("AR", "AX0"),
            setup=InternalMoveSetup(WRITABLE["AX0"], 0x1111),
        )
        self.assertTrue(result.integration_conflict)
        self.assertEqual(result.state, state)


if __name__ == "__main__":
    unittest.main()
