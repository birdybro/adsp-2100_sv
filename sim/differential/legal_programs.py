"""Deterministic source-closed programs for bounded differential replay.

This generator intentionally emits only straight-line instruction classes whose
complete emitted field space is implemented by the independent model.  It does
not infer unresolved control-flow, memory-data, interrupt, or cache behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import random
from typing import Callable, Final

from sim.differential.model_trace_adapter import adapt_model_trace_frame
from sim.reference_models.adsp2100_model import (
    ADSP2100Model,
    ArchitecturalState,
    ExactWord,
)
from tools.trace.adsp2100_trace import DifferentialTraceFrame


LEGAL_PROGRAM_SCHEMA_VERSION: Final = 1
_MAX_SEED: Final = (1 << 64) - 1
_STATE_SEED_XOR: Final = 0xAD5_2100_5EED


def _nop(_rng: random.Random) -> int:
    return 0x000000


def _type6(rng: random.Random) -> int:
    # Every DATA[19:4]/DREG[3:0] combination is an original Type 6 word.
    return 0x400000 | rng.randrange(1 << 20)


_TYPE7_REGISTER_CODES: Final = (
    *range(0x10, 0x1C),
    *range(0x20, 0x2C),
    0x30,
    0x31,
    0x33,
    0x34,
    0x35,
    0x36,
    0x37,
)


def _type7(rng: random.Random) -> int:
    # The 31 codes are every writable original non-data register; SSTAT and
    # the blank Appendix A table cells are deliberately absent.
    code = _TYPE7_REGISTER_CODES[rng.randrange(len(_TYPE7_REGISTER_CODES))]
    return (
        0x300000
        | ((code >> 4) << 18)
        | (rng.randrange(1 << 14) << 4)
        | (code & 0xF)
    )


def _type9(rng: random.Random) -> int:
    # Every Z/AMF/YOP/XOP/COND tuple, including documented AMF-zero aliases,
    # is source closed; bits 7:4 remain the fixed zero format field.
    return (
        0x200000
        | (rng.randrange(1 << 1) << 18)
        | (rng.randrange(1 << 5) << 13)
        | (rng.randrange(1 << 2) << 11)
        | (rng.randrange(1 << 3) << 8)
        | rng.randrange(1 << 4)
    )


_SHIFTER_XOPS: Final = (0, 2, 3, 4, 5, 6, 7)


def _type15(rng: random.Random) -> int:
    # Type 15 is source closed for SF 0-7 and the seven original X operands.
    return (
        0x0F0000
        | (rng.randrange(8) << 11)
        | (_SHIFTER_XOPS[rng.randrange(len(_SHIFTER_XOPS))] << 8)
        | rng.randrange(1 << 8)
    )


def _type16(rng: random.Random) -> int:
    # All SF and COND values are closed for the seven original X operands.
    return (
        0x0E0000
        | (rng.randrange(1 << 4) << 11)
        | (_SHIFTER_XOPS[rng.randrange(len(_SHIFTER_XOPS))] << 8)
        | rng.randrange(1 << 4)
    )


def _type17_dreg(rng: random.Random) -> int:
    # Restrict both selectors to RGP=00. This exercises all DREG moves without
    # depending on OQ-016 narrow status/control source extension.
    return 0x0D0000 | (rng.randrange(1 << 4) << 4) | rng.randrange(1 << 4)


def _type18(rng: random.Random) -> int:
    # Four independent two-bit MCC fields occupy bits 11:4.
    return 0x0C0000 | (rng.randrange(1 << 8) << 4)


def _type21(rng: random.Random) -> int:
    # All G/I/M selections in bits 4:0 are source closed.
    return 0x090000 | rng.randrange(1 << 5)


def _type23(rng: random.Random) -> int:
    # All eight ALU-X divisor selections are source closed.
    return 0x071000 | (rng.randrange(1 << 3) << 8)


def _type24(rng: random.Random) -> int:
    # Only AY1 and AF are source-closed upper-dividend selections.
    yop = (1, 2)[rng.randrange(2)]
    return 0x060000 | (yop << 11) | (rng.randrange(1 << 3) << 8)


def _type25(_rng: random.Random) -> int:
    return 0x050000


def _type26_no_effect(_rng: random.Random) -> int:
    # The all-zero Type 26 action fields are a documented no-effect alias.
    return 0x040000


_FACTORIES: Final[tuple[tuple[str, Callable[[random.Random], int]], ...]] = (
    ("NOP", _nop),
    ("TYPE_06", _type6),
    ("TYPE_07", _type7),
    ("TYPE_09", _type9),
    ("TYPE_15", _type15),
    ("TYPE_16", _type16),
    ("TYPE_17_DREG", _type17_dreg),
    ("TYPE_18", _type18),
    ("TYPE_21", _type21),
    ("TYPE_23", _type23),
    ("TYPE_24", _type24),
    ("TYPE_25", _type25),
    ("TYPE_26_NO_EFFECT", _type26_no_effect),
)
_FACTORY_BY_NAME: Final = dict(_FACTORIES)


def _word_matches_class(word: int, class_name: str) -> bool:
    if class_name == "NOP":
        return word == 0x000000
    if class_name == "TYPE_06":
        return word & 0xF00000 == 0x400000
    if class_name == "TYPE_07":
        code = (((word >> 18) & 0x3) << 4) | (word & 0xF)
        return word & 0xF00000 == 0x300000 and code in _TYPE7_REGISTER_CODES
    if class_name == "TYPE_09":
        return word & 0xF800F0 == 0x200000
    if class_name == "TYPE_15":
        return (
            word & 0xFF8000 == 0x0F0000
            and ((word >> 11) & 0xF) < 8
            and ((word >> 8) & 0x7) in _SHIFTER_XOPS
        )
    if class_name == "TYPE_16":
        return (
            word & 0xFF80F0 == 0x0E0000
            and ((word >> 8) & 0x7) in _SHIFTER_XOPS
        )
    if class_name == "TYPE_17_DREG":
        return word & 0xFFFF00 == 0x0D0000
    if class_name == "TYPE_18":
        return word & 0xFFF00F == 0x0C0000
    if class_name == "TYPE_21":
        return word & 0xFFFFE0 == 0x090000
    if class_name == "TYPE_23":
        return word & 0xFFF8FF == 0x071000
    if class_name == "TYPE_24":
        return (
            word & 0xFFE0FF == 0x060000
            and ((word >> 11) & 0x3) in (1, 2)
        )
    if class_name == "TYPE_25":
        return word == 0x050000
    if class_name == "TYPE_26_NO_EFFECT":
        return word == 0x040000
    return False


@dataclass(frozen=True)
class LegalProgram:
    """Replayable bounded program plus independently generated class labels."""

    seed: int
    origin: int
    words: tuple[int, ...]
    classes: tuple[str, ...]
    schema_version: int = LEGAL_PROGRAM_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != LEGAL_PROGRAM_SCHEMA_VERSION
        ):
            raise ValueError("unsupported legal-program schema version")
        if (
            not isinstance(self.seed, int)
            or isinstance(self.seed, bool)
            or not 0 <= self.seed <= _MAX_SEED
        ):
            raise ValueError("seed must be an unsigned 64-bit integer")
        if (
            not isinstance(self.origin, int)
            or isinstance(self.origin, bool)
            or not 0 <= self.origin < (1 << 14)
        ):
            raise ValueError("origin must fit 14 bits")
        if len(self.words) != len(self.classes):
            raise ValueError("words and classes must have equal lengths")
        if self.origin + len(self.words) > (1 << 14):
            raise ValueError("program exceeds the 14-bit PM address space")
        for index, (word, class_name) in enumerate(zip(self.words, self.classes)):
            if (
                not isinstance(word, int)
                or isinstance(word, bool)
                or not 0 <= word < (1 << 24)
            ):
                raise ValueError(f"word {index} must fit 24 bits")
            if not isinstance(class_name, str) or class_name not in _FACTORY_BY_NAME:
                raise ValueError(f"word {index} has an unsupported class label")
            if not _word_matches_class(word, class_name):
                raise ValueError(f"word {index} does not match {class_name}")

    def initial_state(self) -> ArchitecturalState:
        """Return deterministic known state with an empty sequencer context."""

        state = ArchitecturalState.randomized(self.seed ^ _STATE_SEED_XOR)
        return replace(
            state,
            pc=ExactWord(14, self.origin),
            sstat=ExactWord(8, 0x55),
            mstat_valid_mask=0xF,
            pc_stack=(),
            loop_stack=(),
            count_stack=(),
            status_stack=(),
            total_instruction_cycles=0,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "seed": f"0x{self.seed:016x}",
            "origin": f"0x{self.origin:04x}",
            "instructions": [
                {"class": class_name, "opcode": f"0x{word:06x}"}
                for word, class_name in zip(self.words, self.classes)
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: object) -> "LegalProgram":
        if not isinstance(value, dict):
            raise ValueError("legal program must be an object")
        expected = {"schema_version", "seed", "origin", "instructions"}
        if set(value) != expected:
            raise ValueError("legal-program object keys differ from the schema")
        if (
            not isinstance(value["schema_version"], int)
            or isinstance(value["schema_version"], bool)
            or value["schema_version"] != LEGAL_PROGRAM_SCHEMA_VERSION
        ):
            raise ValueError("unsupported legal-program schema version")

        def parse_hex(item: object, digits: int, name: str) -> int:
            if not isinstance(item, str) or len(item) != digits + 2:
                raise ValueError(f"{name} is not canonically padded hexadecimal")
            if not item.startswith("0x") or item.lower() != item:
                raise ValueError(f"{name} is not canonical hexadecimal")
            try:
                return int(item[2:], 16)
            except ValueError as exc:
                raise ValueError(f"{name} is not hexadecimal") from exc

        instructions = value["instructions"]
        if not isinstance(instructions, list):
            raise ValueError("instructions must be an array")
        words: list[int] = []
        classes: list[str] = []
        for index, instruction in enumerate(instructions):
            if not isinstance(instruction, dict) or set(instruction) != {
                "class",
                "opcode",
            }:
                raise ValueError(f"instruction {index} keys differ from the schema")
            class_name = instruction["class"]
            if not isinstance(class_name, str):
                raise ValueError(f"instruction {index} class must be a string")
            words.append(parse_hex(instruction["opcode"], 6, "opcode"))
            classes.append(class_name)
        return cls(
            seed=parse_hex(value["seed"], 16, "seed"),
            origin=parse_hex(value["origin"], 4, "origin"),
            words=tuple(words),
            classes=tuple(classes),
        )

    @classmethod
    def from_json(cls, value: str) -> "LegalProgram":
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("legal program is not valid JSON") from exc
        return cls.from_dict(decoded)


def generate_legal_program(
    seed: int,
    length: int,
    *,
    origin: int = 4,
) -> LegalProgram:
    """Generate a deterministic straight-line program from the bounded subset."""

    if (
        not isinstance(seed, int)
        or isinstance(seed, bool)
        or not 0 <= seed <= _MAX_SEED
    ):
        raise ValueError("seed must be an unsigned 64-bit integer")
    if not isinstance(length, int) or isinstance(length, bool) or length < 0:
        raise ValueError("length must be nonnegative")
    if (
        not isinstance(origin, int)
        or isinstance(origin, bool)
        or not 0 <= origin < (1 << 14)
    ):
        raise ValueError("origin must fit 14 bits")
    if origin + length > (1 << 14):
        raise ValueError("program exceeds the 14-bit PM address space")

    rng = random.Random(seed)
    prefix = [name for name, _factory in _FACTORIES]
    rng.shuffle(prefix)
    classes = tuple(
        prefix[index]
        if index < len(prefix)
        else _FACTORIES[rng.randrange(len(_FACTORIES))][0]
        for index in range(length)
    )
    words = tuple(_FACTORY_BY_NAME[class_name](rng) for class_name in classes)
    return LegalProgram(seed=seed, origin=origin, words=words, classes=classes)


def run_model_program(
    program: LegalProgram,
    *,
    producer: str = "independent-model",
) -> tuple[DifferentialTraceFrame, ...]:
    """Execute a bounded program and return common post-retirement frames."""

    model = ADSP2100Model(state=program.initial_state())
    model.load_program(program.words, origin=program.origin)
    frames: list[DifferentialTraceFrame] = []
    for _word in program.words:
        frame = model.step_program()
        frames.append(
            adapt_model_trace_frame(frame, model.state, producer=producer)
        )
    return tuple(frames)
