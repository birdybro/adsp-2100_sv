"""Exact-width foundation for an independent original ADSP-2100 model.

The integrated instruction boundary currently covers linear-flow NOP, the
source-closed Type 6/7 immediate-load classes, Type 9 conditional compute,
Type 8 ALU/MAC-plus-move packets, Type 14 shifter-plus-move packets, Type 15
immediate shifts, Type 16 conditional shifts, original Type 18 mode control,
all 32 Type 21 MODIFY selections, all 32 Type 26 manual stack controls, Type
23 DIVQ, the source-closed Type 24 DIVS forms, exact Type 25 MR saturation,
all 507,904 source-closed Type 10 direct transfers, and legal Type 17 internal
moves from known sources.
Unsupported behavior fails closed instead of becoming an accidental no-op.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import json
import random
from typing import Final

from tools.generators.validate_isa import classify_opcode, load_database


PROGRAM_WORD_WIDTH: Final = 24
DATA_WORD_WIDTH: Final = 16
ADDRESS_WIDTH: Final = 14
MR_WIDTH: Final = 40


class UnsupportedOpcode(RuntimeError):
    """The instruction is not yet source-verified and implemented."""


class ReservedOpcode(UnsupportedOpcode):
    """The original manual marks the instruction word as reserved."""


class UnsupportedFeature(RuntimeError):
    """The requested architectural context is outside the verified slice."""


@dataclass(frozen=True)
class _UnknownValue:
    label: str = "UNKNOWN"

    def __str__(self) -> str:
        return self.label


UNKNOWN: Final = _UnknownValue()
KnownOrUnknown = "ExactWord | _UnknownValue"


@dataclass(frozen=True, order=True)
class ExactWord:
    """An unsigned bit vector that rejects, rather than masks, invalid input."""

    width: int
    value: int

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("width must be positive")
        if not 0 <= self.value < (1 << self.width):
            raise ValueError(f"value {self.value} does not fit unsigned {self.width} bits")

    @property
    def signed(self) -> int:
        return sign_extend(self.value, self.width)

    def incremented(self, amount: int = 1) -> "ExactWord":
        return ExactWord(self.width, mask_to_width(self.value + amount, self.width))

    def hex(self) -> str:
        digits = (self.width + 3) // 4
        return f"0x{self.value:0{digits}x}"


def mask_to_width(value: int, width: int) -> int:
    """Explicitly apply hardware truncation at a named width boundary."""

    if width <= 0:
        raise ValueError("width must be positive")
    return value & ((1 << width) - 1)


def sign_extend(value: int, width: int) -> int:
    """Interpret an unsigned *width*-bit pattern as two's-complement."""

    word = ExactWord(width, value)
    sign = 1 << (width - 1)
    return (word.value ^ sign) - sign


def _unknown_words(count: int) -> tuple[_UnknownValue, ...]:
    return (UNKNOWN,) * count


@dataclass(frozen=True)
class ComputationalBank:
    """Original computational data registers, with authentic reset unknowns."""

    ax: tuple[KnownOrUnknown, KnownOrUnknown] = field(default_factory=lambda: _unknown_words(2))
    ay: tuple[KnownOrUnknown, KnownOrUnknown] = field(default_factory=lambda: _unknown_words(2))
    ar: KnownOrUnknown = UNKNOWN
    af: KnownOrUnknown = UNKNOWN
    mx: tuple[KnownOrUnknown, KnownOrUnknown] = field(default_factory=lambda: _unknown_words(2))
    my: tuple[KnownOrUnknown, KnownOrUnknown] = field(default_factory=lambda: _unknown_words(2))
    mf: KnownOrUnknown = UNKNOWN
    # Segment order follows the architectural names MR0, MR1, MR2. Keeping
    # each segment independent preserves partially initialized states.
    mr: tuple[KnownOrUnknown, KnownOrUnknown, KnownOrUnknown] = field(
        default_factory=lambda: _unknown_words(3)
    )
    si: KnownOrUnknown = UNKNOWN
    se: KnownOrUnknown = UNKNOWN
    sb: KnownOrUnknown = UNKNOWN
    # Segment order follows the architectural names SR0, SR1.
    sr: tuple[KnownOrUnknown, KnownOrUnknown] = field(
        default_factory=lambda: _unknown_words(2)
    )

    @classmethod
    def randomized(cls, rng: random.Random) -> "ComputationalBank":
        w16 = lambda: ExactWord(DATA_WORD_WIDTH, rng.randrange(1 << DATA_WORD_WIDTH))
        return cls(
            ax=(w16(), w16()),
            ay=(w16(), w16()),
            ar=w16(),
            af=w16(),
            mx=(w16(), w16()),
            my=(w16(), w16()),
            mf=w16(),
            mr=(
                w16(),
                w16(),
                ExactWord(8, rng.randrange(1 << 8)),
            ),
            si=w16(),
            se=ExactWord(8, rng.randrange(1 << 8)),
            sb=ExactWord(5, rng.randrange(1 << 5)),
            sr=(w16(), w16()),
        )


@dataclass(frozen=True)
class DAGRegisters:
    i: tuple[KnownOrUnknown, ...] = field(default_factory=lambda: _unknown_words(8))
    m: tuple[KnownOrUnknown, ...] = field(default_factory=lambda: _unknown_words(8))
    l: tuple[KnownOrUnknown, ...] = field(default_factory=lambda: _unknown_words(8))

    @classmethod
    def randomized(cls, rng: random.Random) -> "DAGRegisters":
        words = lambda: tuple(ExactWord(ADDRESS_WIDTH, rng.randrange(1 << ADDRESS_WIDTH)) for _ in range(8))
        return cls(i=words(), m=words(), l=words())


@dataclass(frozen=True)
class ArchitecturalState:
    """Architectural state visible at a verified instruction boundary."""

    pc: ExactWord = field(default_factory=lambda: ExactWord(ADDRESS_WIDTH, 4))
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    dag: DAGRegisters = field(default_factory=DAGRegisters)
    px: KnownOrUnknown = UNKNOWN
    astat: KnownOrUnknown = UNKNOWN
    sstat: ExactWord = field(default_factory=lambda: ExactWord(8, 0x55))
    mstat: ExactWord = field(default_factory=lambda: ExactWord(4, 0))
    imask: ExactWord = field(default_factory=lambda: ExactWord(4, 0))
    icntl: KnownOrUnknown = UNKNOWN
    cntr: KnownOrUnknown = UNKNOWN
    pc_stack: tuple[ExactWord, ...] = ()
    loop_stack: tuple[tuple[ExactWord, ExactWord], ...] = ()
    count_stack: tuple[ExactWord, ...] = ()
    status_stack: tuple[
        tuple[KnownOrUnknown, ExactWord, ExactWord], ...
    ] = ()
    total_instruction_cycles: int = 0

    @classmethod
    def reset(cls) -> "ArchitecturalState":
        """State after documented reset release, preserving undefined fields."""

        return cls()

    @classmethod
    def randomized(cls, seed: int) -> "ArchitecturalState":
        """Produce deterministic known state for future replayable tests."""

        rng = random.Random(seed)
        return cls(
            pc=ExactWord(ADDRESS_WIDTH, rng.randrange(1 << ADDRESS_WIDTH)),
            primary=ComputationalBank.randomized(rng),
            alternate=ComputationalBank.randomized(rng),
            dag=DAGRegisters.randomized(rng),
            px=ExactWord(8, rng.randrange(1 << 8)),
            astat=ExactWord(8, rng.randrange(1 << 8)),
            sstat=ExactWord(8, rng.randrange(1 << 8)),
            mstat=ExactWord(4, rng.randrange(1 << 4)),
            imask=ExactWord(4, rng.randrange(1 << 4)),
            icntl=ExactWord(5, rng.randrange(1 << 5)),
            cntr=ExactWord(ADDRESS_WIDTH, rng.randrange(1 << ADDRESS_WIDTH)),
        )


class MemorySpace(str, Enum):
    PROGRAM = "PM"
    DATA = "DM"


class TransactionKind(str, Enum):
    INSTRUCTION_FETCH = "INSTRUCTION_FETCH"
    DATA_READ = "DATA_READ"
    DATA_WRITE = "DATA_WRITE"


@dataclass(frozen=True)
class MemoryTransaction:
    space: MemorySpace
    kind: TransactionKind
    address: ExactWord
    width: int
    data: ExactWord | None
    wait_instruction_cycles: int = 0


@dataclass(frozen=True)
class TraceFrame:
    retirement_index: int
    pc_before: ExactWord
    pc_after: ExactWord
    opcode: ExactWord
    instruction_cycles: int
    transactions: tuple[MemoryTransaction, ...]

    def to_json(self) -> str:
        transaction_data = [
            {
                "space": transaction.space.value,
                "kind": transaction.kind.value,
                "address": transaction.address.hex(),
                "width": transaction.width,
                "data": None if transaction.data is None else transaction.data.hex(),
                "wait_instruction_cycles": transaction.wait_instruction_cycles,
            }
            for transaction in self.transactions
        ]
        return json.dumps(
            {
                "retirement_index": self.retirement_index,
                "pc_before": self.pc_before.hex(),
                "pc_after": self.pc_after.hex(),
                "opcode": self.opcode.hex(),
                "instruction_cycles": self.instruction_cycles,
                "transactions": transaction_data,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass
class ADSP2100Model:
    """Fail-closed partial model, structurally independent from future RTL."""

    state: ArchitecturalState = field(default_factory=ArchitecturalState.reset)
    trace: list[TraceFrame] = field(default_factory=list)
    program_memory: dict[int, ExactWord] = field(default_factory=dict)
    data_memory: dict[int, ExactWord] = field(default_factory=dict)

    def reset(self) -> None:
        self.state = ArchitecturalState.reset()
        self.trace.clear()

    def load_program(self, words: list[int] | tuple[int, ...], *, origin: int = 4) -> None:
        if not 0 <= origin < (1 << ADDRESS_WIDTH):
            raise ValueError("program origin must fit 14 bits")
        if origin + len(words) > (1 << ADDRESS_WIDTH):
            raise ValueError("program image exceeds 14-bit instruction address space")
        for offset, word in enumerate(words):
            self.program_memory[origin + offset] = ExactWord(PROGRAM_WORD_WIDTH, word)

    def load_data(self, words: list[int] | tuple[int, ...], *, origin: int = 0) -> None:
        if not 0 <= origin < (1 << ADDRESS_WIDTH):
            raise ValueError("data origin must fit 14 bits")
        if origin + len(words) > (1 << ADDRESS_WIDTH):
            raise ValueError("data image exceeds 14-bit data address space")
        for offset, word in enumerate(words):
            self.data_memory[origin + offset] = ExactWord(DATA_WORD_WIDTH, word)

    def step_program(self, *, fetch_wait_instruction_cycles: int = 0) -> TraceFrame:
        address = self.state.pc.value
        try:
            instruction = self.program_memory[address]
        except KeyError as exc:
            raise UnsupportedFeature(
                f"no 24-bit program word loaded at 0x{address:04x}"
            ) from exc
        return self.step(
            instruction.value,
            fetch_wait_instruction_cycles=fetch_wait_instruction_cycles,
        )

    def step(self, opcode: int, *, fetch_wait_instruction_cycles: int = 0) -> TraceFrame:
        """Retire one verified instruction.

        The original program-memory interface has no acknowledge input: in the
        verified linear baseline, the current instruction executes while the
        next instruction word is fetched in the same processor cycle.  Loop
        terminal handling remains fail-closed until integrated sequencing owns
        it.
        """

        instruction = ExactWord(PROGRAM_WORD_WIDTH, opcode)
        if fetch_wait_instruction_cycles < 0:
            raise ValueError("fetch wait cycles cannot be negative")
        if fetch_wait_instruction_cycles:
            raise UnsupportedFeature(
                "the original ADSP-2100 PM fetch has no wait-state extension"
            )
        if self.state.loop_stack:
            raise UnsupportedFeature("loop-terminal handling is not implemented")

        next_state = self.state
        pc_after = self.state.pc.incremented()
        if instruction.value == 0:
            pass
        elif instruction.value & 0xFFFFE0 == 0x040000:
            next_state = _apply_type26_stack_control(
                self.state,
                instruction.value,
            )
        elif instruction.value & 0xF80000 == 0x180000:
            next_state, pc_after = _apply_type10_direct_jump(
                self.state,
                instruction.value,
            )
        elif instruction.value & 0xF00000 == 0x400000:
            from .load_dreg_immediate import decode_load_dreg_immediate
            from .registers import DREGWrite, apply_dreg_cycle

            action = decode_load_dreg_immediate(instruction.value)
            assert action is not None
            registers = apply_dreg_cycle(
                self.state.primary,
                self.state.alternate,
                alternate_selected=bool(self.state.mstat.value & 1),
                writes=(DREGWrite(action.destination, action.data),),
            )
            next_state = replace(
                self.state,
                primary=registers.primary,
                alternate=registers.alternate,
            )
        elif instruction.value & 0xF00000 == 0x300000:
            from .load_non_dreg_immediate import decode_load_non_dreg_immediate

            action = decode_load_non_dreg_immediate(instruction.value)
            assert action is not None
            if not action.legal:
                raise ReservedOpcode(
                    f"opcode {instruction.hex()} has reserved Type 7 destination: "
                    f"{action.invalid_reason}"
                )
            assert action.register is not None
            next_state = _apply_type7_immediate(self.state, action.register, action.data)
        elif instruction.value & 0xFFF00F == 0x0C0000:
            from .mode_control import apply_mode_control, decode_mode_control

            action = decode_mode_control(instruction.value)
            assert action is not None
            next_state = replace(
                self.state,
                mstat=apply_mode_control(self.state.mstat, action),
            )
        elif instruction.value & 0xFFFFE0 == 0x090000:
            next_state = _apply_type21_modify(self.state, instruction.value)
        elif instruction.value & 0xFFF000 == 0x0D0000:
            from .internal_move import decode_internal_move

            action = decode_internal_move(instruction.value)
            assert action is not None
            if not action.legal:
                raise ReservedOpcode(
                    f"opcode {instruction.hex()} has reserved Type 17 selectors: "
                    f"{action.invalid_reason}"
                )
            assert action.source_register is not None
            assert action.destination_register is not None
            source = _read_type17_source(self.state, action.source_register)
            if source is UNKNOWN:
                raise UnsupportedFeature(
                    "integrated Type 17 execution requires a known source; "
                    "the bounded state model retains unknown propagation"
                )
            assert isinstance(source, ExactWord)
            next_state = _apply_type17_destination(
                self.state,
                action.destination_register,
                source,
            )
        elif instruction.value & 0xF80000 == 0x280000:
            from .compute_move import (
                ComputeMoveState,
                apply_compute_move_cycle,
                decode_compute_move,
            )
            from .status import ASTATState, StatusRegisters

            action = decode_compute_move(instruction.value)
            if action is None:
                raise ReservedOpcode(
                    f"opcode {instruction.hex()} has unsupported Type 8 fields"
                )
            computed = apply_compute_move_cycle(
                ComputeMoveState(
                    primary=self.state.primary,
                    alternate=self.state.alternate,
                    status=StatusRegisters(
                        astat=(
                            ASTATState()
                            if self.state.astat is UNKNOWN
                            else ASTATState.from_word(self.state.astat)
                        ),
                        mstat=self.state.mstat,
                        icntl=self.state.icntl,
                        imask=self.state.imask,
                    ),
                ),
                execute=True,
                opcode=instruction.value,
            )
            next_astat = (
                computed.state.status.astat.to_word()
                if computed.state.status.astat.is_fully_known
                else UNKNOWN
            )
            next_state = replace(
                self.state,
                primary=computed.state.primary,
                alternate=computed.state.alternate,
                astat=next_astat,
                mstat=computed.state.status.mstat,
                icntl=computed.state.status.icntl,
                imask=computed.state.status.imask,
            )
        elif instruction.value & 0xF800F0 == 0x200000:
            from .conditional_compute import (
                ConditionalComputeState,
                apply_conditional_compute_cycle,
            )
            from .status import ASTATState, StatusRegisters

            status = StatusRegisters(
                astat=(
                    ASTATState()
                    if self.state.astat is UNKNOWN
                    else ASTATState.from_word(self.state.astat)
                ),
                mstat=self.state.mstat,
                icntl=self.state.icntl,
                imask=self.state.imask,
            )
            compute_state = ConditionalComputeState(
                primary=self.state.primary,
                alternate=self.state.alternate,
                status=status,
            )
            computed = apply_conditional_compute_cycle(
                compute_state,
                execute=True,
                opcode=instruction.value,
                not_counter_expired=(
                    isinstance(self.state.cntr, ExactWord)
                    and self.state.cntr.value != 1
                ),
            )
            next_astat = (
                computed.state.status.astat.to_word()
                if computed.state.status.astat.is_fully_known
                else UNKNOWN
            )
            next_state = replace(
                self.state,
                primary=computed.state.primary,
                alternate=computed.state.alternate,
                astat=next_astat,
                mstat=computed.state.status.mstat,
                icntl=computed.state.status.icntl,
                imask=computed.state.status.imask,
            )
        elif instruction.value & 0xFFE0FF == 0x060000:
            from .divide_sign import (
                DivideSignInputs,
                DivideSignState,
                apply_divide_sign_cycle,
                decode_divide_sign,
            )
            from .status import ASTATState, StatusRegisters

            action = decode_divide_sign(instruction.value)
            assert action is not None
            if not action.supported:
                raise ReservedOpcode(
                    f"opcode {instruction.hex()} has unsupported Type 24 YOP"
                )
            sign = apply_divide_sign_cycle(
                DivideSignState(
                    primary=self.state.primary,
                    alternate=self.state.alternate,
                    status=StatusRegisters(
                        astat=(
                            ASTATState()
                            if self.state.astat is UNKNOWN
                            else ASTATState.from_word(self.state.astat)
                        ),
                        mstat=self.state.mstat,
                        icntl=self.state.icntl,
                        imask=self.state.imask,
                    ),
                ),
                DivideSignInputs(execute=True, opcode=instruction.value),
            )
            next_astat = (
                sign.state.status.astat.to_word()
                if sign.state.status.astat.is_fully_known
                else UNKNOWN
            )
            next_state = replace(
                self.state,
                primary=sign.state.primary,
                alternate=sign.state.alternate,
                astat=next_astat,
                mstat=sign.state.status.mstat,
                icntl=sign.state.status.icntl,
                imask=sign.state.status.imask,
            )
        elif instruction.value & 0xFFF8FF == 0x071000:
            from .divide_quotient import (
                DivideQuotientInputs,
                DivideQuotientState,
                apply_divide_quotient_cycle,
            )
            from .status import ASTATState, StatusRegisters

            quotient = apply_divide_quotient_cycle(
                DivideQuotientState(
                    primary=self.state.primary,
                    alternate=self.state.alternate,
                    status=StatusRegisters(
                        astat=(
                            ASTATState()
                            if self.state.astat is UNKNOWN
                            else ASTATState.from_word(self.state.astat)
                        ),
                        mstat=self.state.mstat,
                        icntl=self.state.icntl,
                        imask=self.state.imask,
                    ),
                ),
                DivideQuotientInputs(
                    execute=True,
                    opcode=instruction.value,
                ),
            )
            next_astat = (
                quotient.state.status.astat.to_word()
                if quotient.state.status.astat.is_fully_known
                else UNKNOWN
            )
            next_state = replace(
                self.state,
                primary=quotient.state.primary,
                alternate=quotient.state.alternate,
                astat=next_astat,
                mstat=quotient.state.status.mstat,
                icntl=quotient.state.status.icntl,
                imask=quotient.state.status.imask,
            )
        elif instruction.value == 0x050000:
            from .mr_saturation_slice import (
                MRSaturationSliceInputs,
                MRSaturationSliceState,
                apply_mr_saturation_slice_cycle,
            )
            from .status import ASTATState, StatusRegisters

            saturated = apply_mr_saturation_slice_cycle(
                MRSaturationSliceState(
                    status=StatusRegisters(
                        astat=(
                            ASTATState()
                            if self.state.astat is UNKNOWN
                            else ASTATState.from_word(self.state.astat)
                        ),
                        mstat=self.state.mstat,
                        icntl=self.state.icntl,
                        imask=self.state.imask,
                    ),
                    primary=self.state.primary,
                    alternate=self.state.alternate,
                ),
                MRSaturationSliceInputs(
                    execute=True,
                    opcode=instruction.value,
                ),
            )
            next_astat = (
                saturated.state.status.astat.to_word()
                if saturated.state.status.astat.is_fully_known
                else UNKNOWN
            )
            next_state = replace(
                self.state,
                primary=saturated.state.primary,
                alternate=saturated.state.alternate,
                astat=next_astat,
                mstat=saturated.state.status.mstat,
                icntl=saturated.state.status.icntl,
                imask=saturated.state.status.imask,
            )
        elif instruction.value & 0xFF0000 == 0x100000:
            from .shift_move import (
                ShiftMoveState,
                apply_shift_move_cycle,
                decode_shift_move,
            )
            from .status import ASTATState, StatusRegisters

            action = decode_shift_move(instruction.value)
            if action is None:
                raise ReservedOpcode(
                    f"opcode {instruction.hex()} has an unsupported Type 14 "
                    "shifter-plus-move subencoding"
                )
            shifted = apply_shift_move_cycle(
                ShiftMoveState(
                    primary=self.state.primary,
                    alternate=self.state.alternate,
                    status=StatusRegisters(
                        astat=(
                            ASTATState()
                            if self.state.astat is UNKNOWN
                            else ASTATState.from_word(self.state.astat)
                        ),
                        mstat=self.state.mstat,
                        icntl=self.state.icntl,
                        imask=self.state.imask,
                    ),
                ),
                execute=True,
                opcode=instruction.value,
            )
            next_astat = (
                shifted.state.status.astat.to_word()
                if shifted.state.status.astat.is_fully_known
                else UNKNOWN
            )
            next_state = replace(
                self.state,
                primary=shifted.state.primary,
                alternate=shifted.state.alternate,
                astat=next_astat,
                mstat=shifted.state.status.mstat,
                icntl=shifted.state.status.icntl,
                imask=shifted.state.status.imask,
            )
        elif instruction.value & 0xFF8000 == 0x0F0000:
            from .immediate_shift import (
                ImmediateShiftState,
                apply_immediate_shift_cycle,
                decode_immediate_shift,
            )

            action = decode_immediate_shift(instruction.value)
            if action is None:
                raise ReservedOpcode(
                    f"opcode {instruction.hex()} has an unsupported Type 15 "
                    "shifter subencoding"
                )
            shifted = apply_immediate_shift_cycle(
                ImmediateShiftState(
                    primary=self.state.primary,
                    alternate=self.state.alternate,
                    mstat=self.state.mstat,
                ),
                execute=True,
                opcode=instruction.value,
            )
            next_state = replace(
                self.state,
                primary=shifted.state.primary,
                alternate=shifted.state.alternate,
                mstat=shifted.state.mstat,
            )
        elif instruction.value & 0xFF80F0 == 0x0E0000:
            from .conditional_shift import (
                ConditionalShiftState,
                apply_conditional_shift_cycle,
                decode_conditional_shift,
            )
            from .status import ASTATState, StatusRegisters

            action = decode_conditional_shift(instruction.value)
            if action is None:
                raise ReservedOpcode(
                    f"opcode {instruction.hex()} has an unsupported Type 16 "
                    "shifter source subencoding"
                )
            shifted = apply_conditional_shift_cycle(
                ConditionalShiftState(
                    primary=self.state.primary,
                    alternate=self.state.alternate,
                    status=StatusRegisters(
                        astat=(
                            ASTATState()
                            if self.state.astat is UNKNOWN
                            else ASTATState.from_word(self.state.astat)
                        ),
                        mstat=self.state.mstat,
                        icntl=self.state.icntl,
                        imask=self.state.imask,
                    ),
                ),
                execute=True,
                opcode=instruction.value,
                not_counter_expired=(
                    isinstance(self.state.cntr, ExactWord)
                    and self.state.cntr.value != 1
                ),
            )
            next_astat = (
                shifted.state.status.astat.to_word()
                if shifted.state.status.astat.is_fully_known
                else UNKNOWN
            )
            next_state = replace(
                self.state,
                primary=shifted.state.primary,
                alternate=shifted.state.alternate,
                astat=next_astat,
                mstat=shifted.state.status.mstat,
                icntl=shifted.state.status.icntl,
                imask=shifted.state.status.imask,
            )
        else:
            database = load_database()
            classes = classify_opcode(database, instruction.value)
            if not classes or classes[0]["name"] == "reserved":
                raise ReservedOpcode(
                    f"opcode {instruction.hex()} is reserved on the original ADSP-2100"
                )
            raise UnsupportedOpcode(
                f"opcode {instruction.hex()} is source-classified as "
                f"type {classes[0]['original_type']} but not semantically implemented"
            )

        pc_before = self.state.pc
        instruction_cycles = 1
        transaction = MemoryTransaction(
            space=MemorySpace.PROGRAM,
            kind=TransactionKind.INSTRUCTION_FETCH,
            address=pc_after,
            width=PROGRAM_WORD_WIDTH,
            data=self.program_memory.get(pc_after.value),
        )
        frame = TraceFrame(
            retirement_index=len(self.trace),
            pc_before=pc_before,
            pc_after=pc_after,
            opcode=instruction,
            instruction_cycles=instruction_cycles,
            transactions=(transaction,),
        )
        self.state = replace(
            next_state,
            pc=pc_after,
            total_instruction_cycles=self.state.total_instruction_cycles + instruction_cycles,
        )
        self.trace.append(frame)
        return frame


def _replace_word(
    values: tuple[KnownOrUnknown, ...],
    index: int,
    value: ExactWord,
) -> tuple[KnownOrUnknown, ...]:
    updated = list(values)
    updated[index] = value
    return tuple(updated)


def _apply_type10_direct_jump(
    state: ArchitecturalState,
    opcode: int,
) -> tuple[ArchitecturalState, ExactWord]:
    """Apply one source-closed direct transfer and select its fetch address."""

    from .counter import CounterState
    from .direct_jump import decode_direct_jump
    from .flow_condition import evaluate_flow_condition
    from .status import ASTATState

    action = decode_direct_jump(opcode)
    assert action is not None
    if not action.supported:
        raise UnsupportedFeature(
            "Type 10 CALL NOT CE remains unresolved under OQ-012"
        )

    astat = (
        ASTATState()
        if state.astat is UNKNOWN
        else ASTATState.from_word(state.astat)
    )
    condition = evaluate_flow_condition(
        action.condition,
        astat,
        CounterState(
            None if state.cntr is UNKNOWN else state.cntr.value
        ),
    )
    if condition is UNKNOWN:
        raise UnsupportedFeature(
            "Type 10 execution requires known condition inputs"
        )

    taken = bool(condition)
    sequential_pc = state.pc.incremented()
    pc_after = ExactWord(14, action.address) if taken else sequential_pc
    pc_stack = state.pc_stack
    count_stack = state.count_stack
    cntr = state.cntr
    sstat = state.sstat.value & 0xAA

    if taken and action.call:
        if len(pc_stack) < 16:
            pc_stack += (sequential_pc,)
        else:
            sstat |= 1 << 1

    if not action.call and action.condition == 0xE:
        assert isinstance(state.cntr, ExactWord)
        if state.cntr.value == 1:
            if count_stack:
                cntr = count_stack[-1]
                count_stack = count_stack[:-1]
            else:
                cntr = UNKNOWN
        else:
            cntr = ExactWord(14, (state.cntr.value - 1) & 0x3FFF)

    if not pc_stack:
        sstat |= 1 << 0
    if not count_stack:
        sstat |= 1 << 2
    if not state.status_stack:
        sstat |= 1 << 4
    if not state.loop_stack:
        sstat |= 1 << 6

    return (
        replace(
            state,
            pc=pc_after,
            cntr=cntr,
            pc_stack=pc_stack,
            count_stack=count_stack,
            sstat=ExactWord(8, sstat),
        ),
        pc_after,
    )


def _apply_type21_modify(
    state: ArchitecturalState,
    opcode: int,
) -> ArchitecturalState:
    """Commit one Type 21 action through the independent DAG model."""

    from .modify_address import (
        DAGRegisterState,
        apply_modify_address_cycle,
    )

    def bounded(values: tuple[KnownOrUnknown, ...]) -> tuple[int | None, ...]:
        return tuple(
            value.value if isinstance(value, ExactWord) else None
            for value in values
        )

    result = apply_modify_address_cycle(
        DAGRegisterState(
            i=bounded(state.dag.i),
            m=bounded(state.dag.m),
            l=bounded(state.dag.l),
        ),
        execute=True,
        opcode=opcode,
    )

    def architectural(
        values: tuple[int | None, ...],
    ) -> tuple[KnownOrUnknown, ...]:
        return tuple(
            UNKNOWN if value is None else ExactWord(ADDRESS_WIDTH, value)
            for value in values
        )

    return replace(
        state,
        dag=DAGRegisters(
            i=architectural(result.state.i),
            m=architectural(result.state.m),
            l=architectural(result.state.l),
        ),
    )


def _apply_type26_stack_control(
    state: ArchitecturalState,
    opcode: int,
) -> ArchitecturalState:
    """Apply one source-closed manual stack-control action bundle."""

    from .stack_control import (
        StackControlStatusOperation,
        decode_stack_control,
    )

    action = decode_stack_control(opcode)
    assert action is not None

    pc_stack = state.pc_stack
    loop_stack = state.loop_stack
    count_stack = state.count_stack
    status_stack = state.status_stack
    astat = state.astat
    mstat = state.mstat
    imask = state.imask
    cntr = state.cntr
    sstat = state.sstat.value & 0xAA

    if action.status_operation is StackControlStatusOperation.PUSH:
        if len(status_stack) < 4:
            status_stack += ((state.astat, state.mstat, state.imask),)
        else:
            sstat |= 1 << 5
    elif action.status_operation is StackControlStatusOperation.POP:
        if status_stack:
            astat, mstat, imask = status_stack[-1]
            status_stack = status_stack[:-1]

    if action.count_pop and count_stack:
        cntr = count_stack[-1]
        count_stack = count_stack[:-1]
    if action.pc_pop and pc_stack:
        pc_stack = pc_stack[:-1]
    if action.loop_pop and loop_stack:
        loop_stack = loop_stack[:-1]

    if not pc_stack:
        sstat |= 1 << 0
    if not count_stack:
        sstat |= 1 << 2
    if not status_stack:
        sstat |= 1 << 4
    if not loop_stack:
        sstat |= 1 << 6

    return replace(
        state,
        astat=astat,
        mstat=mstat,
        imask=imask,
        cntr=cntr,
        pc_stack=pc_stack,
        loop_stack=loop_stack,
        count_stack=count_stack,
        status_stack=status_stack,
        sstat=ExactWord(8, sstat),
    )


def _apply_type7_immediate(
    state: ArchitecturalState,
    register: str,
    data: ExactWord,
) -> ArchitecturalState:
    """Apply one already-validated Type 7 destination write.

    The action is kept local to the integrated model rather than converting to
    the bounded RTL-slice state.  This preserves the model/RTL structural
    independence while sharing the source-derived decode classification.
    """

    if data.width != 14:
        raise ValueError("Type 7 immediate must be exactly 14 bits")
    if register[0] in ("I", "M", "L") and register[1:].isdigit():
        index = int(register[1:])
        if not 0 <= index < 8:
            raise AssertionError("validated DAG destination outside I/M/L0..7")
        value = ExactWord(14, data.value)
        if register[0] == "I":
            dag = replace(state.dag, i=_replace_word(state.dag.i, index, value))
        elif register[0] == "M":
            dag = replace(state.dag, m=_replace_word(state.dag.m, index, value))
        else:
            dag = replace(state.dag, l=_replace_word(state.dag.l, index, value))
        return replace(state, dag=dag)
    if register == "ASTAT":
        return replace(state, astat=ExactWord(8, data.value & 0xFF))
    if register == "MSTAT":
        return replace(state, mstat=ExactWord(4, data.value & 0xF))
    if register == "IMASK":
        return replace(state, imask=ExactWord(4, data.value & 0xF))
    if register == "ICNTL":
        return replace(state, icntl=ExactWord(5, data.value & 0x1F))
    if register == "CNTR":
        count_stack = state.count_stack
        sstat = state.sstat.value
        if isinstance(state.cntr, ExactWord):
            if len(count_stack) < 4:
                count_stack += (state.cntr,)
                sstat &= ~(1 << 2)
            else:
                sstat |= 1 << 3
        return replace(
            state,
            cntr=ExactWord(14, data.value),
            count_stack=count_stack,
            sstat=ExactWord(8, sstat),
        )
    if register == "SB":
        bank = state.alternate if state.mstat.value & 1 else state.primary
        bank = replace(bank, sb=ExactWord(5, data.value & 0x1F))
        return replace(
            state,
            alternate=bank if state.mstat.value & 1 else state.alternate,
            primary=state.primary if state.mstat.value & 1 else bank,
        )
    if register == "PX":
        return replace(state, px=ExactWord(8, data.value & 0xFF))
    raise AssertionError(f"validated Type 7 destination {register} was not handled")


def _read_type17_source(
    state: ArchitecturalState,
    register: str,
) -> KnownOrUnknown:
    """Read one Type 17 source without reusing the bounded slice model."""

    from .registers import DREG, read_dreg

    if register in DREG.__members__:
        bank = state.alternate if state.mstat.value & 1 else state.primary
        return read_dreg(bank, DREG[register])
    if len(register) == 2 and register[0] in "IML" and register[1].isdigit():
        index = int(register[1])
        value = getattr(state.dag, register[0].lower())[index]
        if value is UNKNOWN:
            return UNKNOWN
        assert isinstance(value, ExactWord)
        if register[0] == "M" and value.value & 0x2000:
            return ExactWord(16, value.value | 0xC000)
        return ExactWord(16, value.value)
    if register == "ASTAT":
        return UNKNOWN if state.astat is UNKNOWN else ExactWord(16, state.astat.value)
    if register == "MSTAT":
        return ExactWord(16, state.mstat.value)
    if register == "SSTAT":
        return ExactWord(16, state.sstat.value)
    if register == "IMASK":
        return ExactWord(16, state.imask.value)
    if register == "ICNTL":
        return UNKNOWN if state.icntl is UNKNOWN else ExactWord(16, state.icntl.value)
    if register == "CNTR":
        return UNKNOWN if state.cntr is UNKNOWN else ExactWord(16, state.cntr.value)
    if register == "SB":
        bank = state.alternate if state.mstat.value & 1 else state.primary
        if bank.sb is UNKNOWN:
            return UNKNOWN
        assert isinstance(bank.sb, ExactWord)
        value = bank.sb.value | (0xFFE0 if bank.sb.value & 0x10 else 0)
        return ExactWord(16, value)
    if register == "PX":
        return UNKNOWN if state.px is UNKNOWN else ExactWord(16, state.px.value)
    raise AssertionError(f"validated Type 17 source {register} was not handled")


def _apply_type17_destination(
    state: ArchitecturalState,
    register: str,
    data: ExactWord,
) -> ArchitecturalState:
    """Commit one known Type 17 value through independent shared state."""

    from .registers import DREG, DREGWrite, apply_dreg_cycle

    if data.width != 16:
        raise ValueError("Type 17 internal move data must be exactly 16 bits")
    if register in DREG.__members__:
        registers = apply_dreg_cycle(
            state.primary,
            state.alternate,
            alternate_selected=bool(state.mstat.value & 1),
            writes=(DREGWrite(DREG[register], data),),
        )
        return replace(
            state,
            primary=registers.primary,
            alternate=registers.alternate,
        )
    return _apply_type7_immediate(
        state,
        register,
        ExactWord(14, data.value & 0x3FFF),
    )
