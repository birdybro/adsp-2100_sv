#!/usr/bin/env python3
"""Validate source-backed original ADSP-2100 Type 18 semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_mode_control.yaml"

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


class ModeControlValidationError(ValueError):
    """Raised when Type 18 semantics disagree with verified records."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModeControlValidationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ModeControlValidationError(
            "mode-control database root must be an object"
        )
    return data


def _parse_hex24(value: object, field: str) -> int:
    if not isinstance(value, str):
        raise ModeControlValidationError(
            f"{field} must be a hexadecimal string"
        )
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise ModeControlValidationError(
            f"{field} is not hexadecimal"
        ) from exc
    if not 0 <= parsed <= 0xFFFFFF:
        raise ModeControlValidationError(f"{field} exceeds 24 bits")
    return parsed


def _pattern_mask_value(pattern: object) -> tuple[int, int]:
    if (
        not isinstance(pattern, str)
        or len(pattern) != 24
        or set(pattern) - {"0", "1", "x"}
    ):
        raise ModeControlValidationError(
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
    """Decode raw Type 18 controls, failing closed on every other word."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    instruction = data["instruction"]
    mask = int(instruction["opcode_mask"], 16)
    value = int(instruction["opcode_value"], 16)
    if opcode & mask != value:
        return None
    names = data["control_codes"]
    fields = {
        "sr": (opcode >> 4) & 0x3,
        "br": (opcode >> 6) & 0x3,
        "ol": (opcode >> 8) & 0x3,
        "ar": (opcode >> 10) & 0x3,
    }
    return {
        **{name: names[str(code)] for name, code in fields.items()},
        "has_effect": any(code >= 2 for code in fields.values()),
        "has_no_change_one_alias": any(
            code == 1 for code in fields.values()
        ),
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
        "status_database",
        "instruction",
        "fields",
        "control_codes",
        "assembly",
        "parallel_actions",
        "source_citations",
        "unresolved_issues",
    }
    if set(data) != expected_top_keys:
        raise ModeControlValidationError(
            f"database requires exactly {sorted(expected_top_keys)}"
        )
    if data["schema_version"] != 1:
        raise ModeControlValidationError("unsupported schema_version")
    if data["device"] != "ADSP-2100" or data["program_word_width"] != 24:
        raise ModeControlValidationError(
            "database must target 24-bit original ADSP-2100"
        )
    if data["status"] != "COMPLETE_FOR_ORIGINAL_TYPE_18_ACTION_DECODE":
        raise ModeControlValidationError(
            "database must state its bounded completeness"
        )
    if data["confidence"] != "VERIFIED_PRIMARY":
        raise ModeControlValidationError(
            "action decode must retain VERIFIED_PRIMARY confidence"
        )
    if data["isa_database"] != "docs/generated/adsp2100_isa.yaml":
        raise ModeControlValidationError("incorrect ISA database link")
    if (
        data["instruction_format_database"]
        != "docs/generated/adsp2100_instruction_formats.yaml"
    ):
        raise ModeControlValidationError(
            "incorrect instruction-format database link"
        )
    if (
        data["status_database"]
        != "docs/generated/adsp2100_status_registers.yaml"
    ):
        raise ModeControlValidationError("incorrect status database link")

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
        "distinct_action_bundles",
        "actionless_alias_count",
        "condition",
        "base_instruction_cycles",
        "memory_spaces_accessed",
        "pm_data_transfer",
        "dm_transfer",
        "combination_rule",
        "source_value_rule",
        "later_device_exclusion",
        "wait_state_sensitivity",
    }
    if set(instruction) != required_instruction_keys:
        raise ModeControlValidationError(
            "instruction record fields are incomplete"
        )
    if instruction["original_type"] != 18:
        raise ModeControlValidationError(
            "mode-control semantics must describe original Type 18"
        )
    mask = _parse_hex24(instruction["opcode_mask"], "opcode_mask")
    value = _parse_hex24(instruction["opcode_value"], "opcode_value")
    if (mask, value) != _pattern_mask_value(
        instruction["encoding_pattern"]
    ):
        raise ModeControlValidationError(
            "encoding pattern and mask/value disagree"
        )
    type_18 = isa["encoding_classes"][17]
    if (
        mask != int(type_18["opcode_mask"], 16)
        or value != int(type_18["opcode_value"], 16)
    ):
        raise ModeControlValidationError(
            "semantic mask/value disagree with ISA Type 18"
        )
    expected_counts = {
        "field_defined_encoding_count": 256,
        "distinct_action_bundles": 81,
        "actionless_alias_count": 16,
        "base_instruction_cycles": 1,
    }
    for field, expected in expected_counts.items():
        if instruction[field] != expected:
            raise ModeControlValidationError(
                f"{field} must equal {expected}"
            )
    exclusion = instruction["later_device_exclusion"]
    if not all(name in exclusion for name in ("Timer", "GO", "multiplier")):
        raise ModeControlValidationError(
            "later-device Type 18 controls must remain explicitly excluded"
        )

    expected_fields = [
        ("AS_MCC", 3, 11, 10, "AR_SATURATE"),
        ("OL_MCC", 2, 9, 8, "OVERFLOW_LATCH"),
        ("BR_MCC", 1, 7, 6, "BIT_REVERSE"),
        ("SR_MCC", 0, 5, 4, "SECONDARY_REGISTER_BANK"),
    ]
    if not isinstance(data["fields"], list) or len(data["fields"]) != 4:
        raise ModeControlValidationError(
            "fields must enumerate original AS/OL/BR/SR controls"
        )
    for field, expected in zip(
        data["fields"], expected_fields, strict=True
    ):
        field_id, mstat_bit, msb, lsb, target = expected
        if field != {
            "id": field_id,
            "mstat_bit": mstat_bit,
            "msb": msb,
            "lsb": lsb,
            "target": target,
        }:
            raise ModeControlValidationError(
                f"{field_id} target or position is incorrect"
            )
    if data["control_codes"] != {
        "0": "NO_CHANGE_ZERO",
        "1": "NO_CHANGE_ONE",
        "2": "DEACTIVATE",
        "3": "ACTIVATE",
    }:
        raise ModeControlValidationError("MCC code meanings are incorrect")

    format_fields = extract_fields(formats, 18, value | 0xFF0)
    if format_fields != {
        "AS_MCC": 3,
        "OL_MCC": 3,
        "BR_MCC": 3,
        "SR_MCC": 3,
    }:
        raise ModeControlValidationError(
            "semantic field locations disagree with format database"
        )

    distinct_bundles: set[tuple[str, ...]] = set()
    actionless_count = 0
    for payload in range(256):
        opcode = value | (payload << 4)
        classes = classify_opcode(isa, opcode)
        if [record["original_type"] for record in classes] != [18]:
            raise ModeControlValidationError(
                f"0x{opcode:06x} does not classify uniquely as Type 18"
            )
        actions = decode_actions(data, opcode)
        assert actions is not None
        normalized = tuple(
            "NO_CHANGE" if actions[name].startswith("NO_CHANGE") else actions[name]
            for name in ("sr", "br", "ol", "ar")
        )
        distinct_bundles.add(normalized)
        if not actions["has_effect"]:
            actionless_count += 1
    if len(distinct_bundles) != 81 or actionless_count != 16:
        raise ModeControlValidationError(
            "Type 18 alias/action accounting is incorrect"
        )
    for opcode in (value - 1, value + 1, 0, 0xFFFFFF):
        if decode_actions(data, opcode) is not None:
            raise ModeControlValidationError(
                f"non-Type-18 opcode 0x{opcode:06x} decoded as mode control"
            )

    assembly = data["assembly"]
    if set(assembly) != {
        "clause_order",
        "target_to_field",
        "action_keywords",
        "omitted_field_encoding",
        "alias_policy",
    }:
        raise ModeControlValidationError(
            "assembly metadata fields are incomplete"
        )
    if assembly["clause_order"] != [
        "BIT_REV",
        "AV_LATCH",
        "AR_SAT",
        "SEC_REG",
    ]:
        raise ModeControlValidationError(
            "assembly clause order must follow original Table 6.9"
        )
    if assembly["target_to_field"] != {
        "BIT_REV": "BR_MCC",
        "AV_LATCH": "OL_MCC",
        "AR_SAT": "AS_MCC",
        "SEC_REG": "SR_MCC",
    }:
        raise ModeControlValidationError(
            "assembly targets do not map to original fields"
        )
    if assembly["action_keywords"] != {
        "DEACTIVATE": "DIS",
        "ACTIVATE": "ENA",
    }:
        raise ModeControlValidationError(
            "assembly action keywords are incorrect"
        )
    if assembly["omitted_field_encoding"] != 0:
        raise ModeControlValidationError(
            "assembler must deterministically use MCC=00 for omitted fields"
        )
    citations = data["source_citations"]
    if (
        not isinstance(citations, list)
        or len(citations) < 3
        or not any(
            item.get("reference_id") == "ADI-UM-1989"
            and item.get("authority") == "ORIGINAL_DEVICE_PRIMARY"
            for item in citations
        )
    ):
        raise ModeControlValidationError(
            "original-device primary citations are required"
        )
    if not any("OQ-015" in issue for issue in data["unresolved_issues"]):
        raise ModeControlValidationError(
            "OQ-015 must remain visible in unresolved issues"
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
    except ModeControlValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(
        "PASS 256 original Type 18 encodings, 81 distinct action bundles, "
        "16 actionless aliases, one-cycle mode control"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
