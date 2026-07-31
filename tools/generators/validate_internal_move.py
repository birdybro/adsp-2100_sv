#!/usr/bin/env python3
"""Validate source-backed original ADSP-2100 Type 17 action decode."""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_internal_move.yaml"
REGISTER_DATABASE = ROOT / "docs/generated/adsp2100_register_codes.yaml"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.generators.validate_instruction_formats import (  # noqa: E402
    extract_fields,
    load_database as load_format_database,
    validate_database as validate_format_database,
)
from tools.generators.validate_isa import (  # noqa: E402
    load_database as load_isa_database,
    validate_database as validate_isa_database,
)
from tools.generators.validate_register_codes import (  # noqa: E402
    load_and_validate as load_register_database,
)


class InternalMoveValidationError(ValueError):
    """Raised when Type 17 records disagree with primary-backed metadata."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InternalMoveValidationError(
            f"cannot load {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise InternalMoveValidationError(
            "internal-move database root must be an object"
        )
    return data


@lru_cache(maxsize=1)
def register_map() -> dict[int, dict[str, Any]]:
    """Load the primary-backed combined RGP/REG selector map."""

    data = load_register_database(REGISTER_DATABASE)
    result: dict[int, dict[str, Any]] = {}
    for group_text, group in data["groups"].items():
        group_code = int(group_text, 2)
        for index_text, metadata in group["codes"].items():
            code = (group_code << 4) | int(index_text)
            result[code] = metadata
    return result


def decode_internal_move(
    data: dict[str, Any],
    opcode: int,
) -> dict[str, Any] | None:
    """Decode raw Type 17 selectors and legal register action."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    instruction = data["instruction"]
    mask = int(instruction["opcode_mask"], 16)
    value = int(instruction["opcode_value"], 16)
    if opcode & mask != value:
        return None

    destination_group = (opcode >> 10) & 0x3
    source_group = (opcode >> 8) & 0x3
    destination_index = (opcode >> 4) & 0xF
    source_index = opcode & 0xF
    destination_code = (destination_group << 4) | destination_index
    source_code = (source_group << 4) | source_index
    registers = register_map()
    destination = registers.get(destination_code)
    source = registers.get(source_code)

    invalid_reason: str | None = None
    if source is None:
        invalid_reason = "RESERVED_SOURCE_SELECTOR"
    elif destination is None:
        invalid_reason = "RESERVED_DESTINATION_SELECTOR"
    elif destination["register"] == "SSTAT":
        invalid_reason = "READ_ONLY_SSTAT_DESTINATION"

    return {
        "destination_group": destination_group,
        "source_group": source_group,
        "destination_index": destination_index,
        "source_index": source_index,
        "destination_code": destination_code,
        "source_code": source_code,
        "destination_register":
            destination["register"] if destination is not None else None,
        "source_register":
            source["register"] if source is not None else None,
        "legal": invalid_reason is None,
        "invalid_reason": invalid_reason,
    }


def _pattern_mask_value(pattern: object) -> tuple[int, int]:
    if (
        not isinstance(pattern, str)
        or len(pattern) != 24
        or set(pattern) - {"0", "1", "x"}
    ):
        raise InternalMoveValidationError(
            "encoding_pattern must contain exactly 24 binary/x bits"
        )
    mask = 0
    value = 0
    for character in pattern:
        mask <<= 1
        value <<= 1
        if character != "x":
            mask |= 1
            value |= character == "1"
    return mask, value


def validate_database(data: dict[str, Any]) -> None:
    expected_keys = {
        "schema_version",
        "device",
        "program_word_width",
        "status",
        "confidence",
        "isa_database",
        "instruction_format_database",
        "register_code_database",
        "instruction",
        "fields",
        "legality",
        "execution_semantics",
        "bounded_state_execution",
        "architectural_side_effects_requiring_composition",
        "assembly",
        "parallel_actions",
        "source_citations",
        "unresolved_issues",
    }
    if set(data) != expected_keys:
        raise InternalMoveValidationError(
            f"database requires exactly {sorted(expected_keys)}"
        )
    if (
        data["schema_version"] != 1
        or data["device"] != "ADSP-2100"
        or data["program_word_width"] != 24
    ):
        raise InternalMoveValidationError(
            "database must target the 24-bit original ADSP-2100"
        )
    if data["status"] != "COMPLETE_FOR_ORIGINAL_TYPE_17_ACTION_DECODE":
        raise InternalMoveValidationError(
            "database must state bounded action-decode completeness"
        )
    if data["confidence"] != "VERIFIED_PRIMARY":
        raise InternalMoveValidationError(
            "Type 17 action decode must retain primary confidence"
        )

    bounded = data["bounded_state_execution"]
    if set(bounded) != {
        "status",
        "confidence",
        "connected_state",
        "ordering",
        "fail_closed",
        "provisional_observable",
    }:
        raise InternalMoveValidationError(
            "bounded state metadata has an unexpected shape"
        )
    if (
        bounded["status"] != "IMPLEMENTED_WITH_PROVISIONAL_OQ_016"
        or bounded["confidence"]
        != "CORROBORATED_EXCEPT_NARROW_STATUS_EXTENSION"
        or "COMPOSED_SSTAT" not in bounded["connected_state"]
        or "source_extension_provisional"
        not in bounded["provisional_observable"]
    ):
        raise InternalMoveValidationError(
            "bounded state metadata must preserve the OQ-016 boundary"
        )

    isa = load_isa_database()
    formats = load_format_database()
    validate_isa_database(isa)
    validate_format_database(formats)

    instruction = data["instruction"]
    mask = int(instruction["opcode_mask"], 16)
    value = int(instruction["opcode_value"], 16)
    if (mask, value) != _pattern_mask_value(
        instruction["encoding_pattern"]
    ):
        raise InternalMoveValidationError(
            "encoding pattern and mask/value disagree"
        )
    type_17 = isa["encoding_classes"][16]
    if (
        type_17["original_type"] != 17
        or mask != int(type_17["opcode_mask"], 16)
        or value != int(type_17["opcode_value"], 16)
    ):
        raise InternalMoveValidationError(
            "semantic mask/value disagree with ISA Type 17"
        )

    expected_fields = [
        {
            "id": "DEST_RGP",
            "msb": 11,
            "lsb": 10,
            "role": "DESTINATION_REGISTER_GROUP",
        },
        {
            "id": "SOURCE_RGP",
            "msb": 9,
            "lsb": 8,
            "role": "SOURCE_REGISTER_GROUP",
        },
        {
            "id": "DEST_REG",
            "msb": 7,
            "lsb": 4,
            "role": "DESTINATION_REGISTER_INDEX",
        },
        {
            "id": "SOURCE_REG",
            "msb": 3,
            "lsb": 0,
            "role": "SOURCE_REGISTER_INDEX",
        },
    ]
    if data["fields"] != expected_fields:
        raise InternalMoveValidationError(
            "Type 17 selector fields are incorrect"
        )
    extracted = extract_fields(formats, 17, value | 0xFFF)
    if extracted != {
        "DEST_RGP": 3,
        "SOURCE_RGP": 3,
        "DEST_REG": 15,
        "SOURCE_REG": 15,
    }:
        raise InternalMoveValidationError(
            "semantic fields disagree with format database"
        )

    registers = register_map()
    if len(registers) != 48:
        raise InternalMoveValidationError(
            "original REG table must contain 48 source registers"
        )
    writable = {
        code: metadata
        for code, metadata in registers.items()
        if metadata["register"] != "SSTAT"
    }
    if len(writable) != 47:
        raise InternalMoveValidationError(
            "SSTAT exclusion must leave 47 destinations"
        )

    type_count = 0
    legal_count = 0
    illegal_count = 0
    for payload in range(0x1000):
        decoded = decode_internal_move(data, value | payload)
        if decoded is None:
            raise InternalMoveValidationError(
                "field-defined Type 17 word did not decode"
            )
        type_count += 1
        if decoded["legal"]:
            legal_count += 1
            if (
                decoded["source_code"] not in registers
                or decoded["destination_code"] not in writable
            ):
                raise InternalMoveValidationError(
                    "legal action uses an inaccessible register"
                )
        else:
            illegal_count += 1

    expected_counts = {
        "field_defined_encoding_count": type_count,
        "legal_action_count": legal_count,
        "illegal_or_reserved_subencoding_count": illegal_count,
        "source_register_count": len(registers),
        "destination_register_count": len(writable),
    }
    for key, expected in expected_counts.items():
        if instruction[key] != expected:
            raise InternalMoveValidationError(
                f"{key} must equal {expected}"
            )
    if (
        legal_count != 2256
        or illegal_count != 1840
        or type_count != 4096
    ):
        raise InternalMoveValidationError(
            "Type 17 selector accounting changed unexpectedly"
        )
    if (
        instruction["pm_data_transfer"] != "NONE"
        or instruction["dm_transfer"] != "NONE"
        or instruction["status_generated"] != "NONE"
        or instruction["base_instruction_cycles"] != 1
    ):
        raise InternalMoveValidationError(
            "Type 17 transfer/timing effects are incorrect"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", nargs="?", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    try:
        data = load_database(args.database)
        validate_database(data)
    except (InternalMoveValidationError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    instruction = data["instruction"]
    print(
        "PASS original Type 17 action decode: "
        f"{instruction['legal_action_count']} legal moves, "
        f"{instruction['illegal_or_reserved_subencoding_count']} "
        "reserved/read-only-destination words"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
