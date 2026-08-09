"""Versioned implementation-neutral retirement trace records.

The schema deliberately represents known bits with an explicit mask.  This
lets the authentic model preserve reset-unknown and partially known state
without assigning a binary value that the original-device sources do not
establish.  Producer identity is provenance, not a compared architectural
field.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Mapping, Sequence


TRACE_SCHEMA_VERSION = 1
TRACE_DEVICE = "original ADSP-2100"
TRACE_SPACES = frozenset(("PM", "DM"))
TRACE_TRANSACTION_KINDS = frozenset(
    ("INSTRUCTION_FETCH", "DATA_READ", "DATA_WRITE")
)
TRACE_MISSING = "<MISSING>"


def _hex_for_width(value: int, width: int) -> str:
    return f"0x{value:0{(width + 3) // 4}x}"


def _require_exact_keys(
    value: Mapping[str, object], expected: frozenset[str], context: str
) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"{context} keys differ: missing={missing}, extra={extra}"
        )


@dataclass(frozen=True, order=True)
class TraceWord:
    """One exact-width word with bitwise validity.

    Unknown bits must carry zero in ``value``.  Requiring that canonical form
    makes independently produced JSON byte-stable and prevents irrelevant
    hidden values from creating a false differential mismatch.
    """

    width: int
    value: int
    known_mask: int

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("trace word width must be positive")
        limit = 1 << self.width
        if not 0 <= self.value < limit:
            raise ValueError("trace word value does not fit its width")
        if not 0 <= self.known_mask < limit:
            raise ValueError("trace word known mask does not fit its width")
        if self.value & ~self.known_mask:
            raise ValueError("unknown trace-word bits must have zero value")

    @classmethod
    def known(cls, width: int, value: int) -> "TraceWord":
        return cls(width=width, value=value, known_mask=(1 << width) - 1)

    @classmethod
    def unknown(cls, width: int) -> "TraceWord":
        return cls(width=width, value=0, known_mask=0)

    def to_dict(self) -> dict[str, object]:
        return {
            "width": self.width,
            "value": _hex_for_width(self.value, self.width),
            "known_mask": _hex_for_width(self.known_mask, self.width),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "TraceWord":
        _require_exact_keys(
            value, frozenset(("width", "value", "known_mask")), "trace word"
        )
        width = value["width"]
        encoded_value = value["value"]
        encoded_mask = value["known_mask"]
        if not isinstance(width, int) or isinstance(width, bool):
            raise ValueError("trace word width must be an integer")
        if not isinstance(encoded_value, str) or not encoded_value.startswith("0x"):
            raise ValueError("trace word value must be a hexadecimal string")
        if not isinstance(encoded_mask, str) or not encoded_mask.startswith("0x"):
            raise ValueError("trace word known mask must be a hexadecimal string")
        try:
            numeric_value = int(encoded_value, 16)
            numeric_mask = int(encoded_mask, 16)
        except ValueError as exc:
            raise ValueError("trace word contains invalid hexadecimal data") from exc
        word = cls(width=width, value=numeric_value, known_mask=numeric_mask)
        if encoded_value != _hex_for_width(word.value, word.width):
            raise ValueError("trace word value is not canonically padded")
        if encoded_mask != _hex_for_width(word.known_mask, word.width):
            raise ValueError("trace word known mask is not canonically padded")
        return word


@dataclass(frozen=True)
class TraceTransaction:
    space: str
    kind: str
    address: TraceWord
    width: int
    data: TraceWord | None
    wait_instruction_cycles: int = 0

    def __post_init__(self) -> None:
        if self.space not in TRACE_SPACES:
            raise ValueError(f"unsupported trace memory space {self.space!r}")
        if self.kind not in TRACE_TRANSACTION_KINDS:
            raise ValueError(f"unsupported trace transaction kind {self.kind!r}")
        if self.address.width != 14:
            raise ValueError("trace transaction address must be 14 bits")
        expected_width = 24 if self.space == "PM" else 16
        if self.width != expected_width:
            raise ValueError(
                f"{self.space} trace transaction width must be {expected_width}"
            )
        if self.kind == "INSTRUCTION_FETCH" and self.space != "PM":
            raise ValueError("instruction fetch must use program memory")
        if self.kind == "DATA_WRITE" and self.data is None:
            raise ValueError("data write must carry a data word")
        if self.data is not None and self.data.width != self.width:
            raise ValueError("trace transaction data width differs from its bus width")
        if self.wait_instruction_cycles < 0:
            raise ValueError("trace transaction wait count cannot be negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "space": self.space,
            "kind": self.kind,
            "address": self.address.to_dict(),
            "width": self.width,
            "data": None if self.data is None else self.data.to_dict(),
            "wait_instruction_cycles": self.wait_instruction_cycles,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "TraceTransaction":
        _require_exact_keys(
            value,
            frozenset(
                (
                    "space",
                    "kind",
                    "address",
                    "width",
                    "data",
                    "wait_instruction_cycles",
                )
            ),
            "trace transaction",
        )
        space = value["space"]
        kind = value["kind"]
        address = value["address"]
        width = value["width"]
        data = value["data"]
        wait_cycles = value["wait_instruction_cycles"]
        if not isinstance(space, str) or not isinstance(kind, str):
            raise ValueError("trace transaction space and kind must be strings")
        if not isinstance(address, Mapping):
            raise ValueError("trace transaction address must be an object")
        if not isinstance(width, int) or isinstance(width, bool):
            raise ValueError("trace transaction width must be an integer")
        if not isinstance(wait_cycles, int) or isinstance(wait_cycles, bool):
            raise ValueError("trace transaction wait count must be an integer")
        if data is not None and not isinstance(data, Mapping):
            raise ValueError("trace transaction data must be null or an object")
        return cls(
            space=space,
            kind=kind,
            address=TraceWord.from_dict(address),
            width=width,
            data=None if data is None else TraceWord.from_dict(data),
            wait_instruction_cycles=wait_cycles,
        )


@dataclass(frozen=True)
class DifferentialTraceFrame:
    """One implementation-neutral post-retirement observation."""

    producer: str
    retirement_index: int
    pc_before: TraceWord
    pc_after: TraceWord
    opcode: TraceWord
    instruction_cycles: int
    state: tuple[tuple[str, TraceWord], ...]
    transactions: tuple[TraceTransaction, ...]
    events: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.producer:
            raise ValueError("trace producer must not be empty")
        if self.retirement_index < 0:
            raise ValueError("retirement index cannot be negative")
        if self.pc_before.width != 14 or self.pc_after.width != 14:
            raise ValueError("trace PCs must be 14 bits")
        if self.opcode.width != 24:
            raise ValueError("trace opcode must be 24 bits")
        if self.instruction_cycles <= 0:
            raise ValueError("instruction cycle count must be positive")
        paths = tuple(path for path, _ in self.state)
        if paths != tuple(sorted(paths)) or len(paths) != len(set(paths)):
            raise ValueError("trace state paths must be unique and sorted")
        if any(not path or path.startswith(".") or path.endswith(".") for path in paths):
            raise ValueError("trace state paths must be nonempty dotted names")
        if self.events != tuple(sorted(set(self.events))):
            raise ValueError("trace events must be unique and sorted")

    @classmethod
    def create(
        cls,
        *,
        producer: str,
        retirement_index: int,
        pc_before: TraceWord,
        pc_after: TraceWord,
        opcode: TraceWord,
        instruction_cycles: int,
        state: Mapping[str, TraceWord],
        transactions: Sequence[TraceTransaction],
        events: Iterable[str] = (),
    ) -> "DifferentialTraceFrame":
        return cls(
            producer=producer,
            retirement_index=retirement_index,
            pc_before=pc_before,
            pc_after=pc_after,
            opcode=opcode,
            instruction_cycles=instruction_cycles,
            state=tuple(sorted(state.items())),
            transactions=tuple(transactions),
            events=tuple(sorted(set(events))),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": TRACE_SCHEMA_VERSION,
            "device": TRACE_DEVICE,
            "producer": self.producer,
            "retirement_index": self.retirement_index,
            "pc_before": self.pc_before.to_dict(),
            "pc_after": self.pc_after.to_dict(),
            "opcode": self.opcode.to_dict(),
            "instruction_cycles": self.instruction_cycles,
            "state": {path: value.to_dict() for path, value in self.state},
            "transactions": [transaction.to_dict() for transaction in self.transactions],
            "events": list(self.events),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":")
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "DifferentialTraceFrame":
        _require_exact_keys(
            value,
            frozenset(
                (
                    "schema_version",
                    "device",
                    "producer",
                    "retirement_index",
                    "pc_before",
                    "pc_after",
                    "opcode",
                    "instruction_cycles",
                    "state",
                    "transactions",
                    "events",
                )
            ),
            "trace frame",
        )
        if value["schema_version"] != TRACE_SCHEMA_VERSION:
            raise ValueError("unsupported trace schema version")
        if value["device"] != TRACE_DEVICE:
            raise ValueError("trace does not target the original ADSP-2100")
        producer = value["producer"]
        retirement_index = value["retirement_index"]
        instruction_cycles = value["instruction_cycles"]
        pc_before = value["pc_before"]
        pc_after = value["pc_after"]
        opcode = value["opcode"]
        state = value["state"]
        transactions = value["transactions"]
        events = value["events"]
        if not isinstance(producer, str):
            raise ValueError("trace producer must be a string")
        if not isinstance(retirement_index, int) or isinstance(retirement_index, bool):
            raise ValueError("retirement index must be an integer")
        if not isinstance(instruction_cycles, int) or isinstance(instruction_cycles, bool):
            raise ValueError("instruction cycle count must be an integer")
        if not all(isinstance(word, Mapping) for word in (pc_before, pc_after, opcode)):
            raise ValueError("trace PC and opcode fields must be objects")
        if not isinstance(state, Mapping):
            raise ValueError("trace state must be an object")
        if not isinstance(transactions, list):
            raise ValueError("trace transactions must be an array")
        if not isinstance(events, list) or not all(isinstance(event, str) for event in events):
            raise ValueError("trace events must be an array of strings")
        if not all(isinstance(item, Mapping) for item in transactions):
            raise ValueError("each trace transaction must be an object")
        state_words: dict[str, TraceWord] = {}
        for path, word in state.items():
            if not isinstance(path, str) or not isinstance(word, Mapping):
                raise ValueError("trace state maps string paths to word objects")
            state_words[path] = TraceWord.from_dict(word)
        return cls.create(
            producer=producer,
            retirement_index=retirement_index,
            pc_before=TraceWord.from_dict(pc_before),
            pc_after=TraceWord.from_dict(pc_after),
            opcode=TraceWord.from_dict(opcode),
            instruction_cycles=instruction_cycles,
            state=state_words,
            transactions=tuple(
                TraceTransaction.from_dict(item) for item in transactions
            ),
            events=events,
        )

    @classmethod
    def from_json(cls, encoded: str) -> "DifferentialTraceFrame":
        try:
            value = json.loads(encoded)
        except json.JSONDecodeError as exc:
            raise ValueError("invalid trace JSON") from exc
        if not isinstance(value, Mapping):
            raise ValueError("trace frame JSON must contain an object")
        return cls.from_dict(value)


@dataclass(frozen=True)
class TraceMismatch:
    path: str
    left: object
    right: object


def compare_trace_frames(
    left: DifferentialTraceFrame,
    right: DifferentialTraceFrame,
    *,
    requested_state: Iterable[str] | None = None,
) -> tuple[TraceMismatch, ...]:
    """Compare architectural content while ignoring producer provenance."""

    mismatches: list[TraceMismatch] = []

    def compare(path: str, left_value: object, right_value: object) -> None:
        if left_value != right_value:
            mismatches.append(TraceMismatch(path, left_value, right_value))

    compare("retirement_index", left.retirement_index, right.retirement_index)
    compare("pc_before", left.pc_before, right.pc_before)
    compare("pc_after", left.pc_after, right.pc_after)
    compare("opcode", left.opcode, right.opcode)
    compare("instruction_cycles", left.instruction_cycles, right.instruction_cycles)
    compare("events", left.events, right.events)

    left_state = dict(left.state)
    right_state = dict(right.state)
    if requested_state is None:
        paths = sorted(set(left_state) | set(right_state))
    else:
        paths = sorted(set(requested_state))
    for path in paths:
        compare(
            f"state.{path}",
            left_state.get(path, TRACE_MISSING),
            right_state.get(path, TRACE_MISSING),
        )

    compare("transactions.length", len(left.transactions), len(right.transactions))
    for index, (left_transaction, right_transaction) in enumerate(
        zip(left.transactions, right.transactions)
    ):
        for field_name in (
            "space",
            "kind",
            "address",
            "width",
            "data",
            "wait_instruction_cycles",
        ):
            compare(
                f"transactions[{index}].{field_name}",
                getattr(left_transaction, field_name),
                getattr(right_transaction, field_name),
            )
    return tuple(mismatches)


def compare_trace_streams(
    left: Sequence[DifferentialTraceFrame],
    right: Sequence[DifferentialTraceFrame],
    *,
    requested_state: Iterable[str] | None = None,
) -> tuple[TraceMismatch, ...]:
    mismatches: list[TraceMismatch] = []
    if len(left) != len(right):
        mismatches.append(TraceMismatch("frames.length", len(left), len(right)))
    for index, (left_frame, right_frame) in enumerate(zip(left, right)):
        mismatches.extend(
            TraceMismatch(f"frames[{index}].{item.path}", item.left, item.right)
            for item in compare_trace_frames(
                left_frame, right_frame, requested_state=requested_state
            )
        )
    return tuple(mismatches)


def trace_stream_to_ndjson(frames: Iterable[DifferentialTraceFrame]) -> str:
    encoded = [frame.to_json() for frame in frames]
    return "" if not encoded else "\n".join(encoded) + "\n"


def trace_stream_from_ndjson(encoded: str) -> tuple[DifferentialTraceFrame, ...]:
    frames: list[DifferentialTraceFrame] = []
    for line_number, line in enumerate(encoded.splitlines(), start=1):
        if not line:
            raise ValueError(f"blank trace line at {line_number}")
        try:
            frames.append(DifferentialTraceFrame.from_json(line))
        except ValueError as exc:
            raise ValueError(f"invalid trace line {line_number}: {exc}") from exc
    return tuple(frames)
