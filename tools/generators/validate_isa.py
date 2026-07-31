#!/usr/bin/env python3
"""Validate the hand-audited seed of the ADSP-2100 ISA database."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_isa.yaml"


class ISAValidationError(ValueError):
    """Raised when the machine-readable ISA database is inconsistent."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ISAValidationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ISAValidationError("database root must be an object")
    return data


def _parse_hex24(value: object, field: str) -> int:
    if not isinstance(value, str):
        raise ISAValidationError(f"{field} must be a hexadecimal string")
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise ISAValidationError(f"{field} is not hexadecimal: {value!r}") from exc
    if not 0 <= parsed <= 0xFFFFFF:
        raise ISAValidationError(f"{field} exceeds 24 bits: {value!r}")
    return parsed


def _pattern_mask_value(pattern: object, field: str) -> tuple[int, int]:
    if not isinstance(pattern, str) or len(pattern) != 24 or set(pattern) - {"0", "1", "x"}:
        raise ISAValidationError(f"{field} must be exactly 24 binary/x bits")
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


def classify_opcode(data: dict[str, Any], opcode: int) -> list[dict[str, Any]]:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return [
        encoding_class
        for encoding_class in data["encoding_classes"]
        if opcode & int(encoding_class["opcode_mask"], 16)
        == int(encoding_class["opcode_value"], 16)
    ]


def decode_classification(data: dict[str, Any], opcode: int) -> str:
    matches = classify_opcode(data, opcode)
    if matches:
        return f"TYPE_{matches[0]['original_type']:02d}"
    return str(data["unshown_encoding_policy"]["classification"])


def validate_database(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ISAValidationError("unsupported schema_version")
    if data.get("device") != "ADSP-2100":
        raise ISAValidationError("database must target the exact ADSP-2100")
    if data.get("program_word_width") != 24:
        raise ISAValidationError("program_word_width must be 24")
    if data.get("completeness_claim") is not False:
        raise ISAValidationError("partial seed must not claim completeness")
    if data.get("field_code_databases") != [
        "docs/generated/adsp2100_isa_fields.yaml",
        "docs/generated/adsp2100_condition_codes.yaml",
        "docs/generated/adsp2100_register_codes.yaml",
    ]:
        raise ISAValidationError("ISA field-code database links are incomplete")
    if (
        data.get("instruction_format_database")
        != "docs/generated/adsp2100_instruction_formats.yaml"
    ):
        raise ISAValidationError(
            "ISA instruction-format database link is incomplete"
        )
    if data.get("semantic_databases") != [
        "docs/generated/adsp2100_stack_control.yaml",
        "docs/generated/adsp2100_mr_saturation.yaml",
        "docs/generated/adsp2100_mode_control.yaml",
        "docs/generated/adsp2100_modify_address.yaml",
    ]:
        raise ISAValidationError(
            "ISA semantic database links are incomplete"
        )
    if data.get("integration_databases") != [
        "docs/generated/adsp2100_stack_control_slice.yaml",
        "docs/generated/adsp2100_mr_saturation_slice.yaml",
        "docs/generated/adsp2100_mode_control_slice.yaml",
        "docs/generated/adsp2100_modify_address_slice.yaml",
    ]:
        raise ISAValidationError(
            "ISA integration database links are incomplete"
        )
    unshown_policy = data.get("unshown_encoding_policy")
    if not isinstance(unshown_policy, dict):
        raise ISAValidationError("unshown_encoding_policy must be an object")
    if set(unshown_policy) != {
        "classification",
        "architectural_behavior",
        "implementation_rule",
        "source_citation",
        "confidence",
    }:
        raise ISAValidationError("unshown_encoding_policy has incomplete fields")
    if unshown_policy["classification"] != "RESERVED_UNSHOWN":
        raise ISAValidationError("unshown opcodes must remain explicitly reserved")
    if unshown_policy["architectural_behavior"] != "UNDOCUMENTED":
        raise ISAValidationError("unshown reserved behavior must not be invented")
    if not unshown_policy["source_citation"]:
        raise ISAValidationError("unshown encoding policy requires a primary citation")

    required = data.get("required_instruction_fields")
    instructions = data.get("instructions")
    classes = data.get("encoding_classes")
    if not isinstance(required, list) or not all(isinstance(x, str) for x in required):
        raise ISAValidationError("required_instruction_fields must be strings")
    if not isinstance(instructions, list) or not instructions:
        raise ISAValidationError("at least one hand-verified instruction is required")
    if not isinstance(classes, list) or [x.get("original_type") for x in classes] != list(range(1, 31)):
        raise ISAValidationError("encoding_classes must enumerate original types 1 through 30")

    class_required = {
        "original_type",
        "name",
        "encoding_pattern",
        "opcode_mask",
        "opcode_value",
        "status",
        "confidence",
        "source_citation",
    }
    for encoding_class in classes:
        class_id = f"type {encoding_class.get('original_type', '<unknown>')}"
        missing = class_required - set(encoding_class)
        if missing:
            raise ISAValidationError(f"{class_id} missing fields: {sorted(missing)}")
        pattern_mask, pattern_value = _pattern_mask_value(
            encoding_class["encoding_pattern"], f"{class_id}.encoding_pattern"
        )
        mask = _parse_hex24(encoding_class["opcode_mask"], f"{class_id}.opcode_mask")
        value = _parse_hex24(encoding_class["opcode_value"], f"{class_id}.opcode_value")
        if (mask, value) != (pattern_mask, pattern_value):
            raise ISAValidationError(
                f"{class_id} pattern implies mask/value "
                f"0x{pattern_mask:06x}/0x{pattern_value:06x}, not "
                f"0x{mask:06x}/0x{value:06x}"
            )
        if encoding_class["confidence"] not in {
            "VERIFIED_PRIMARY",
            "VERIFIED_HARDWARE",
            "CORROBORATED",
            "INFERRED",
            "PROVISIONAL",
            "UNKNOWN",
        }:
            raise ISAValidationError(f"{class_id} has invalid confidence")
        if not isinstance(encoding_class["source_citation"], str) or not encoding_class["source_citation"]:
            raise ISAValidationError(f"{class_id} requires a source citation")

    for left_index, left in enumerate(classes):
        left_mask = int(left["opcode_mask"], 16)
        left_value = int(left["opcode_value"], 16)
        for right in classes[left_index + 1 :]:
            right_mask = int(right["opcode_mask"], 16)
            right_value = int(right["opcode_value"], 16)
            common_mask = left_mask & right_mask
            if ((left_value ^ right_value) & common_mask) == 0:
                raise ISAValidationError(
                    "encoding-class overlap: "
                    f"type {left['original_type']} and type {right['original_type']}"
                )
    shown_encoding_count = sum(
        1 << (24 - int(encoding_class["opcode_mask"], 16).bit_count())
        for encoding_class in classes
    )
    if not 0 < shown_encoding_count < (1 << 24):
        raise ISAValidationError("shown encoding coverage must leave documented unshown codes")

    seen_ids: set[str] = set()
    exact_values: dict[int, str] = {}
    for instruction in instructions:
        if not isinstance(instruction, dict):
            raise ISAValidationError("instruction entries must be objects")
        missing = set(required) - set(instruction)
        if missing:
            raise ISAValidationError(
                f"{instruction.get('id', '<unknown>')} missing fields: {sorted(missing)}"
            )
        instruction_id = instruction["id"]
        if not isinstance(instruction_id, str) or instruction_id in seen_ids:
            raise ISAValidationError(f"duplicate or invalid instruction id: {instruction_id!r}")
        seen_ids.add(instruction_id)

        mask = _parse_hex24(instruction["opcode_mask"], f"{instruction_id}.opcode_mask")
        value = _parse_hex24(instruction["opcode_value"], f"{instruction_id}.opcode_value")
        if value & ~mask:
            raise ISAValidationError(f"{instruction_id} value sets bits outside its mask")
        pattern_mask, pattern_value = _pattern_mask_value(
            instruction["encoding_pattern"], f"{instruction_id}.encoding_pattern"
        )
        if (mask, value) != (pattern_mask, pattern_value):
            raise ISAValidationError(
                f"{instruction_id} pattern and opcode mask/value disagree"
            )
        if mask == 0xFFFFFF:
            if value in exact_values:
                raise ISAValidationError(
                    f"exact opcode collision: {instruction_id} and {exact_values[value]}"
                )
            exact_values[value] = instruction_id
        if instruction["confidence"] not in {
            "VERIFIED_PRIMARY",
            "VERIFIED_HARDWARE",
            "CORROBORATED",
            "INFERRED",
            "PROVISIONAL",
            "UNKNOWN",
        }:
            raise ISAValidationError(f"{instruction_id} has invalid confidence")
        citations = instruction["source_citations"]
        if not isinstance(citations, list) or not citations:
            raise ISAValidationError(f"{instruction_id} requires at least one source citation")
        matching_classes = classify_opcode(data, value)
        if len(matching_classes) != 1:
            raise ISAValidationError(
                f"{instruction_id} exact value matches {len(matching_classes)} encoding classes"
            )

    nop = next((item for item in instructions if item["id"] == "NOP-000000"), None)
    if nop is None or _parse_hex24(nop["opcode_value"], "NOP opcode") != 0:
        raise ISAValidationError("hand-verified all-zero NOP fixture is missing")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", nargs="?", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    try:
        data = load_database(args.database)
        validate_database(data)
    except ISAValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    shown_encoding_count = sum(
        1 << (24 - int(encoding_class["opcode_mask"], 16).bit_count())
        for encoding_class in data["encoding_classes"]
    )
    print(
        "PASS "
        f"{len(data['instructions'])} verified instruction fixture(s), "
        f"{len(data['encoding_classes'])} non-overlapping source-backed class records; "
        f"{shown_encoding_count} shown and {(1 << 24) - shown_encoding_count} "
        "explicitly reserved-unshown encodings; database semantically partial"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
