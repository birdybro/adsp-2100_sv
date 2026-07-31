#!/usr/bin/env python3
"""Validate source-backed original ADSP-2100 Type 26 action semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_stack_control.yaml"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.generators.validate_instruction_formats import (  # noqa: E402
    extract_fields,
    load_database as load_format_database,
    validate_database as validate_format_database,
)
from tools.generators.validate_isa import (  # noqa: E402
    classify_opcode,
    load_database as load_isa_database,
    validate_database as validate_isa_database,
)


class StackControlValidationError(ValueError):
    """Raised when Type 26 semantics disagree with verified source records."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StackControlValidationError(
            f"cannot load {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise StackControlValidationError(
            "stack-control database root must be an object"
        )
    return data


def _parse_hex24(value: object, field: str) -> int:
    if not isinstance(value, str):
        raise StackControlValidationError(
            f"{field} must be a hexadecimal string"
        )
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise StackControlValidationError(
            f"{field} is not hexadecimal"
        ) from exc
    if not 0 <= parsed <= 0xFFFFFF:
        raise StackControlValidationError(f"{field} exceeds 24 bits")
    return parsed


def _pattern_mask_value(pattern: object) -> tuple[int, int]:
    if (
        not isinstance(pattern, str)
        or len(pattern) != 24
        or set(pattern) - {"0", "1", "x"}
    ):
        raise StackControlValidationError(
            "encoding_pattern must be exactly 24 binary/x bits"
        )
    mask = 0
    value = 0
    for character in pattern:
        mask <<= 1
        value <<= 1
        if character != "x":
            mask |= 1
            if character == "1":
                value |= 1
    return mask, value


def decode_actions(data: dict[str, Any], opcode: int) -> dict[str, Any] | None:
    """Decode only the Type 26 action fields, failing closed otherwise."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    instruction = data["instruction"]
    mask = int(instruction["opcode_mask"], 16)
    value = int(instruction["opcode_value"], 16)
    if opcode & mask != value:
        return None
    spp = opcode & 0x3
    return {
        "status_operation": (
            "NO_CHANGE_ZERO",
            "NO_CHANGE_ONE",
            "PUSH",
            "POP",
        )[spp],
        "count_pop": bool(opcode & 0x4),
        "loop_pop": bool(opcode & 0x8),
        "pc_pop": bool(opcode & 0x10),
        "has_effect": bool((opcode & 0x1E) != 0),
    }


def validate_database(data: dict[str, Any]) -> None:
    expected_top_keys = {
        "schema_version",
        "device",
        "program_word_width",
        "status",
        "confidence",
        "isa_database",
        "instruction_format_database",
        "instruction",
        "fields",
        "assembly",
        "parallel_actions",
        "source_citations",
        "unresolved_issues",
    }
    if set(data) != expected_top_keys:
        raise StackControlValidationError(
            f"database requires exactly {sorted(expected_top_keys)}"
        )
    if data["schema_version"] != 1:
        raise StackControlValidationError("unsupported schema_version")
    if data["device"] != "ADSP-2100" or data["program_word_width"] != 24:
        raise StackControlValidationError(
            "database must target 24-bit original ADSP-2100"
        )
    if data["status"] != "COMPLETE_FOR_TYPE_26_ACTION_DECODE":
        raise StackControlValidationError(
            "database must state its bounded completeness"
        )
    if data["confidence"] != "VERIFIED_PRIMARY":
        raise StackControlValidationError(
            "action decode must retain VERIFIED_PRIMARY confidence"
        )
    if data["isa_database"] != "docs/generated/adsp2100_isa.yaml":
        raise StackControlValidationError("incorrect ISA database link")
    if (
        data["instruction_format_database"]
        != "docs/generated/adsp2100_instruction_formats.yaml"
    ):
        raise StackControlValidationError(
            "incorrect instruction-format database link"
        )

    isa = load_isa_database()
    formats = load_format_database()
    validate_isa_database(isa)
    validate_format_database(formats)

    instruction = data["instruction"]
    required_instruction_keys = {
        "original_type",
        "name",
        "opcode_mask",
        "opcode_value",
        "encoding_pattern",
        "field_defined_encoding_count",
        "condition",
        "base_instruction_cycles",
        "memory_spaces_accessed",
        "pm_data_transfer",
        "dm_transfer",
        "wait_state_sensitivity",
        "combination_rule",
        "source_value_rule",
        "underflow_rule",
        "overflow_rule",
    }
    if set(instruction) != required_instruction_keys:
        raise StackControlValidationError(
            "instruction record fields are incomplete"
        )
    if instruction["original_type"] != 26:
        raise StackControlValidationError(
            "stack-control semantics must describe original Type 26"
        )
    mask = _parse_hex24(instruction["opcode_mask"], "opcode_mask")
    value = _parse_hex24(instruction["opcode_value"], "opcode_value")
    if (mask, value) != _pattern_mask_value(
        instruction["encoding_pattern"]
    ):
        raise StackControlValidationError(
            "encoding pattern and mask/value disagree"
        )
    type_26 = isa["encoding_classes"][25]
    if (
        mask != int(type_26["opcode_mask"], 16)
        or value != int(type_26["opcode_value"], 16)
    ):
        raise StackControlValidationError(
            "semantic mask/value disagree with ISA Type 26"
        )
    if instruction["field_defined_encoding_count"] != 32:
        raise StackControlValidationError(
            "Type 26 must retain all 32 field-defined encodings"
        )
    if instruction["base_instruction_cycles"] != 1:
        raise StackControlValidationError(
            "original stack control must remain one instruction cycle"
        )
    if instruction["underflow_rule"] != "OPEN_QUESTION_OQ_013":
        raise StackControlValidationError(
            "empty-pop behavior must remain explicitly unresolved"
        )

    fields = data["fields"]
    expected_fields = [
        ("PP", 4, 4, {"0": "NO_CHANGE", "1": "POP_PC_STACK"}),
        ("LP", 3, 3, {"0": "NO_CHANGE", "1": "POP_LOOP_STACK"}),
        (
            "CP",
            2,
            2,
            {"0": "NO_CHANGE", "1": "POP_COUNT_STACK_TO_CNTR"},
        ),
        (
            "SPP",
            1,
            0,
            {
                "0": "NO_CHANGE_ZERO",
                "1": "NO_CHANGE_ONE",
                "2": "PUSH_STATUS_STACK",
                "3": "POP_STATUS_STACK_TO_ASTAT_MSTAT_IMASK",
            },
        ),
    ]
    if not isinstance(fields, list) or len(fields) != len(expected_fields):
        raise StackControlValidationError(
            "fields must enumerate PP, LP, CP, and SPP"
        )
    for field, expected in zip(fields, expected_fields, strict=True):
        field_id, msb, lsb, actions = expected
        if field != {
            "id": field_id,
            "msb": msb,
            "lsb": lsb,
            "actions": actions,
        }:
            raise StackControlValidationError(
                f"{field_id} action table or bit position is incorrect"
            )

    format_fields = extract_fields(formats, 26, value | 0x1F)
    if format_fields != {"PP": 1, "LP": 1, "CP": 1, "SPP": 3}:
        raise StackControlValidationError(
            "semantic field locations disagree with format database"
        )

    seen_behaviors: set[tuple[object, ...]] = set()
    for payload in range(32):
        opcode = value | payload
        if [record["original_type"] for record in classify_opcode(isa, opcode)] != [26]:
            raise StackControlValidationError(
                f"0x{opcode:06x} does not classify uniquely as Type 26"
            )
        actions = decode_actions(data, opcode)
        assert actions is not None
        normalized_status = (
            "NO_CHANGE"
            if actions["status_operation"].startswith("NO_CHANGE")
            else actions["status_operation"]
        )
        seen_behaviors.add(
            (
                normalized_status,
                actions["count_pop"],
                actions["loop_pop"],
                actions["pc_pop"],
            )
        )
    if len(seen_behaviors) != 24:
        raise StackControlValidationError(
            "SPP no-change alias should produce 24 distinct action bundles"
        )
    for opcode in (value - 1, value + 32, 0, 0xFFFFFF):
        if decode_actions(data, opcode) is not None:
            raise StackControlValidationError(
                f"non-Type-26 opcode 0x{opcode:06x} decoded as stack control"
            )

    citations = data["source_citations"]
    if (
        not isinstance(citations, list)
        or len(citations) < 2
        or not any(
            item.get("reference_id") == "ADI-UM-1989"
            and item.get("authority") == "ORIGINAL_DEVICE_PRIMARY"
            for item in citations
        )
    ):
        raise StackControlValidationError(
            "original-device primary citations are required"
        )
    if not isinstance(data["unresolved_issues"], list) or not any(
        "OQ-013" in issue for issue in data["unresolved_issues"]
    ):
        raise StackControlValidationError(
            "OQ-013 must remain visible in unresolved issues"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "database",
        nargs="?",
        type=Path,
        default=DEFAULT_DATABASE,
    )
    args = parser.parse_args()
    try:
        data = load_database(args.database)
        validate_database(data)
    except StackControlValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(
        "PASS 32 original Type 26 encodings, 24 distinct action bundles, "
        "one-cycle action decode; empty-pop effects remain OQ-013"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
