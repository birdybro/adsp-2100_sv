#!/usr/bin/env python3
"""Validate source-backed original ADSP-2100 Type 7 semantics."""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_load_non_dreg_immediate.yaml"
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


class LoadNonDregImmediateValidationError(ValueError):
    """Raised when Type 7 records disagree with primary-backed metadata."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LoadNonDregImmediateValidationError(
            f"cannot load {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise LoadNonDregImmediateValidationError(
            "Type 7 database root must be an object"
        )
    return data


@lru_cache(maxsize=1)
def register_map() -> dict[int, dict[str, Any]]:
    data = load_register_database(REGISTER_DATABASE)
    result: dict[int, dict[str, Any]] = {}
    for group_text, group in data["groups"].items():
        group_code = int(group_text, 2)
        for index_text, metadata in group["codes"].items():
            result[(group_code << 4) | int(index_text)] = metadata
    return result


def decode_load_non_dreg_immediate(
    data: dict[str, Any], opcode: int,
) -> dict[str, Any] | None:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    instruction = data["instruction"]
    if opcode & int(instruction["opcode_mask"], 16) != int(
        instruction["opcode_value"], 16
    ):
        return None
    group = (opcode >> 18) & 3
    index = opcode & 0xF
    code = (group << 4) | index
    metadata = register_map().get(code)
    invalid_reason: str | None = None
    if group == 0:
        invalid_reason = "DATA_REGISTER_DESTINATION"
    elif metadata is None:
        invalid_reason = "RESERVED_DESTINATION_SELECTOR"
    elif metadata["register"] == "SSTAT":
        invalid_reason = "READ_ONLY_SSTAT_DESTINATION"
    return {
        "register_group": group,
        "register_index": index,
        "register_code": code,
        "register": metadata["register"] if metadata is not None else None,
        "data": (opcode >> 4) & 0x3FFF,
        "legal": invalid_reason is None,
        "invalid_reason": invalid_reason,
    }


def _pattern_mask_value(pattern: object) -> tuple[int, int]:
    if (
        not isinstance(pattern, str)
        or len(pattern) != 24
        or set(pattern) - {"0", "1", "x"}
    ):
        raise LoadNonDregImmediateValidationError(
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
        "schema_version", "device", "program_word_width", "immediate_width",
        "status", "confidence", "isa_database", "instruction_format_database",
        "register_code_database", "instruction", "fields", "legality",
        "execution_semantics", "implementation_boundary", "assembly",
        "parallel_actions", "source_citations", "unresolved_issues",
    }
    if set(data) != expected_keys:
        raise LoadNonDregImmediateValidationError(
            f"database requires exactly {sorted(expected_keys)}"
        )
    if (
        data["schema_version"] != 1
        or data["device"] != "ADSP-2100"
        or data["program_word_width"] != 24
        or data["immediate_width"] != 14
        or data["status"] != "COMPLETE_FOR_ORIGINAL_TYPE_7_BOUNDED_STATE"
        or data["confidence"] != "VERIFIED_PRIMARY"
    ):
        raise LoadNonDregImmediateValidationError(
            "Type 7 device, widths, status, or confidence are incorrect"
        )

    isa = load_isa_database()
    formats = load_format_database()
    validate_isa_database(isa)
    validate_format_database(formats)
    instruction = data["instruction"]
    mask = int(instruction["opcode_mask"], 16)
    value = int(instruction["opcode_value"], 16)
    if (mask, value) != _pattern_mask_value(instruction["encoding_pattern"]):
        raise LoadNonDregImmediateValidationError(
            "encoding pattern and mask/value disagree"
        )
    type_7 = isa["encoding_classes"][6]
    if (
        type_7["original_type"] != 7
        or type_7["name"] != "non-data-register immediate"
        or type_7["status"] != "COMPLETE_BOUNDED_STATE"
        or type_7["confidence"] != "VERIFIED_PRIMARY"
        or mask != int(type_7["opcode_mask"], 16)
        or value != int(type_7["opcode_value"], 16)
    ):
        raise LoadNonDregImmediateValidationError(
            "semantic identity/status/mask/value disagree with ISA Type 7"
        )
    expected_fields = [
        {"id": "RGP", "msb": 19, "lsb": 18, "role": "NON_DATA_REGISTER_GROUP"},
        {"id": "DATA", "msb": 17, "lsb": 4, "role": "RAW_14_BIT_IMMEDIATE"},
        {"id": "REG", "msb": 3, "lsb": 0, "role": "NON_DATA_REGISTER_INDEX"},
    ]
    if data["fields"] != expected_fields:
        raise LoadNonDregImmediateValidationError("Type 7 fields are incorrect")
    if extract_fields(formats, 7, 0x3FFFFF) != {
        "RGP": 3, "DATA": 0x3FFF, "REG": 0xF,
    }:
        raise LoadNonDregImmediateValidationError(
            "semantic fields disagree with format database"
        )

    registers = register_map()
    legal_codes = {
        code for code, metadata in registers.items()
        if code >> 4 != 0 and metadata["register"] != "SSTAT"
    }
    if len(registers) != 48 or len(legal_codes) != 31:
        raise LoadNonDregImmediateValidationError(
            "original non-data destination set changed"
        )
    immediate_count = 1 << 14
    legal_count = len(legal_codes) * immediate_count
    class_count = 1 << 20
    invalid_count = class_count - legal_count
    expected_counts = {
        "field_defined_encoding_count": class_count,
        "legal_action_count": legal_count,
        "illegal_or_reserved_subencoding_count": invalid_count,
        "destination_register_count": len(legal_codes),
    }
    for key, expected in expected_counts.items():
        if instruction[key] != expected:
            raise LoadNonDregImmediateValidationError(
                f"{key} must equal {expected}"
            )
    if (class_count, legal_count, invalid_count) != (
        1_048_576, 507_904, 540_672
    ):
        raise LoadNonDregImmediateValidationError(
            "Type 7 selector accounting changed unexpectedly"
        )
    if (
        instruction["base_instruction_cycles"] != 1
        or instruction["pm_data_transfer"] != "NONE"
        or instruction["dm_transfer"] != "NONE"
        or instruction["status_generated"] != "NONE"
    ):
        raise LoadNonDregImmediateValidationError(
            "Type 7 transaction/timing fields are incorrect"
        )
    if data["implementation_boundary"] != {
        "action_decode": "COMPLETE",
        "state_execution": "COMPLETE_BOUNDED",
        "native_bus_attachment": "NOT_APPLICABLE_NO_DATA_TRANSFER",
        "whole_core_fetch_interrupt_attachment": "NOT_IMPLEMENTED",
    }:
        raise LoadNonDregImmediateValidationError(
            "implementation boundary must remain explicit"
        )
    legal_selectors = 0
    invalid_selectors = 0
    for code in range(64):
        opcode = value | ((code >> 4) << 18) | (code & 0xF)
        decoded = decode_load_non_dreg_immediate(data, opcode)
        assert decoded is not None
        if decoded["legal"]:
            legal_selectors += 1
        else:
            invalid_selectors += 1
    if (legal_selectors, invalid_selectors) != (31, 33):
        raise LoadNonDregImmediateValidationError(
            "Type 7 destination partition is wrong"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", nargs="?", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    try:
        data = load_database(args.database)
        validate_database(data)
    except (LoadNonDregImmediateValidationError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    instruction = data["instruction"]
    print(
        "PASS original Type 7 bounded-state contract: "
        f"{instruction['legal_action_count']} legal, "
        f"{instruction['illegal_or_reserved_subencoding_count']} unsupported words"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
