#!/usr/bin/env python3
"""Validate source-backed original ADSP-2100 Type 3 action semantics."""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_direct_dm.yaml"
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


class DirectDMValidationError(ValueError):
    """Raised when Type 3 records disagree with primary-backed metadata."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DirectDMValidationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise DirectDMValidationError("direct-DM database root must be an object")
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


def decode_direct_dm(data: dict[str, Any], opcode: int) -> dict[str, Any] | None:
    """Decode raw Type 3 fields against the generated register metadata."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    instruction = data["instruction"]
    mask = int(instruction["opcode_mask"], 16)
    value = int(instruction["opcode_value"], 16)
    if opcode & mask != value:
        return None

    write = bool((opcode >> 20) & 1)
    group = (opcode >> 18) & 3
    index = opcode & 0xF
    code = (group << 4) | index
    metadata = register_map().get(code)
    invalid_reason: str | None = None
    if metadata is None:
        invalid_reason = (
            "RESERVED_SOURCE_SELECTOR"
            if write else "RESERVED_DESTINATION_SELECTOR"
        )
    elif not write and metadata["register"] == "SSTAT":
        invalid_reason = "READ_ONLY_SSTAT_DESTINATION"
    return {
        "write": write,
        "address": (opcode >> 4) & 0x3FFF,
        "register_group": group,
        "register_index": index,
        "register_code": code,
        "register": metadata["register"] if metadata is not None else None,
        "legal": invalid_reason is None,
        "invalid_reason": invalid_reason,
    }


def _pattern_mask_value(pattern: object) -> tuple[int, int]:
    if (
        not isinstance(pattern, str)
        or len(pattern) != 24
        or set(pattern) - {"0", "1", "x"}
    ):
        raise DirectDMValidationError(
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
        "schema_version", "device", "program_word_width", "data_word_width",
        "data_address_width", "status", "confidence", "isa_database",
        "instruction_format_database", "register_code_database", "instruction",
        "fields", "direction", "legality", "execution_semantics",
        "implementation_boundary", "assembly", "parallel_actions",
        "source_citations", "unresolved_issues",
    }
    if set(data) != expected_keys:
        raise DirectDMValidationError(
            f"database requires exactly {sorted(expected_keys)}"
        )
    if (
        data["schema_version"] != 1
        or data["device"] != "ADSP-2100"
        or data["program_word_width"] != 24
        or data["data_word_width"] != 16
        or data["data_address_width"] != 14
    ):
        raise DirectDMValidationError("database widths/device are not original ADSP-2100")
    if (
        data["status"] != "COMPLETE_FOR_ORIGINAL_TYPE_3_ACTION_DECODE"
        or data["confidence"] != "VERIFIED_PRIMARY"
    ):
        raise DirectDMValidationError("Type 3 action boundary must retain primary confidence")

    isa = load_isa_database()
    formats = load_format_database()
    validate_isa_database(isa)
    validate_format_database(formats)
    instruction = data["instruction"]
    mask = int(instruction["opcode_mask"], 16)
    value = int(instruction["opcode_value"], 16)
    if (mask, value) != _pattern_mask_value(instruction["encoding_pattern"]):
        raise DirectDMValidationError("encoding pattern and mask/value disagree")
    type_3 = isa["encoding_classes"][2]
    if (
        type_3["original_type"] != 3
        or mask != int(type_3["opcode_mask"], 16)
        or value != int(type_3["opcode_value"], 16)
    ):
        raise DirectDMValidationError("semantic mask/value disagree with ISA Type 3")

    expected_fields = [
        {"id": "D", "msb": 20, "lsb": 20, "role": "DM_DIRECTION"},
        {"id": "RGP", "msb": 19, "lsb": 18, "role": "GENERAL_REGISTER_GROUP"},
        {"id": "ADDR", "msb": 17, "lsb": 4, "role": "DIRECT_DM_ADDRESS"},
        {"id": "REG", "msb": 3, "lsb": 0, "role": "GENERAL_REGISTER_INDEX"},
    ]
    if data["fields"] != expected_fields:
        raise DirectDMValidationError("Type 3 fields are incorrect")
    if extract_fields(formats, 3, 0x9FFFFF) != {
        "D": 1, "RGP": 3, "ADDR": 0x3FFF, "REG": 0xF,
    }:
        raise DirectDMValidationError("semantic fields disagree with format database")

    registers = register_map()
    writable = {
        code: metadata for code, metadata in registers.items()
        if metadata["register"] != "SSTAT"
    }
    if len(registers) != 48 or len(writable) != 47:
        raise DirectDMValidationError("original REG direction sets changed")

    address_count = 1 << 14
    legal_read_count = len(writable) * address_count
    legal_write_count = len(registers) * address_count
    legal_count = legal_read_count + legal_write_count
    type_count = 1 << 21
    invalid_count = type_count - legal_count
    expected_counts = {
        "field_defined_encoding_count": type_count,
        "legal_action_count": legal_count,
        "legal_read_count": legal_read_count,
        "legal_write_count": legal_write_count,
        "illegal_or_reserved_subencoding_count": invalid_count,
        "source_register_count": len(registers),
        "destination_register_count": len(writable),
    }
    for key, expected in expected_counts.items():
        if instruction[key] != expected:
            raise DirectDMValidationError(f"{key} must equal {expected}")
    if (
        type_count != 2_097_152
        or legal_read_count != 770_048
        or legal_write_count != 786_432
        or invalid_count != 540_672
    ):
        raise DirectDMValidationError("Type 3 selector accounting changed unexpectedly")
    if (
        instruction["base_instruction_cycles"] != 1
        or instruction["pm_data_transfer"] != "NONE"
        or instruction["dm_transfer"] != "READ_OR_WRITE"
        or instruction["dag_used"] != "NONE"
        or instruction["status_generated"] != "NONE"
        or not instruction["wait_state_sensitive"]
    ):
        raise DirectDMValidationError("Type 3 transfer/timing effects are incorrect")
    if data["implementation_boundary"] != {
        "action_decode": "COMPLETE",
        "state_execution": "PENDING",
        "native_dm_attachment": "PENDING",
        "provisional_dependency": (
            "OQ-016 applies only to DM writes sourced by narrow status/control "
            "registers."
        ),
    }:
        raise DirectDMValidationError("implementation boundary must remain explicit")

    # Every selector direction is enumerated independently of the address field.
    legal_read_selectors = 0
    legal_write_selectors = 0
    invalid_selectors = 0
    for write in range(2):
        for code in range(64):
            opcode = value | (write << 20) | ((code >> 4) << 18) | (code & 0xF)
            decoded = decode_direct_dm(data, opcode)
            assert decoded is not None
            if decoded["legal"]:
                if write:
                    legal_write_selectors += 1
                else:
                    legal_read_selectors += 1
            else:
                invalid_selectors += 1
    if (legal_read_selectors, legal_write_selectors, invalid_selectors) != (47, 48, 33):
        raise DirectDMValidationError("Type 3 direction/selector partition is wrong")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", nargs="?", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    try:
        data = load_database(args.database)
        validate_database(data)
    except (DirectDMValidationError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    instruction = data["instruction"]
    print(
        "PASS original Type 3 action decode: "
        f"{instruction['legal_read_count']} reads, "
        f"{instruction['legal_write_count']} writes, "
        f"{instruction['illegal_or_reserved_subencoding_count']} unsupported words"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
