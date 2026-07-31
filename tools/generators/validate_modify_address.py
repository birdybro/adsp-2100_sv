#!/usr/bin/env python3
"""Validate source-backed original ADSP-2100 Type 21 semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_modify_address.yaml"

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
from tools.generators.validate_isa_fields import (  # noqa: E402
    load_database as load_field_database,
    validate_database as validate_field_database,
)


class ModifyAddressValidationError(ValueError):
    """Raised when Type 21 semantics disagree with verified records."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModifyAddressValidationError(
            f"cannot load {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise ModifyAddressValidationError(
            "modify-address database root must be an object"
        )
    return data


def _parse_hex24(value: object, name: str) -> int:
    if not isinstance(value, str):
        raise ModifyAddressValidationError(
            f"{name} must be a hexadecimal string"
        )
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise ModifyAddressValidationError(
            f"{name} is not hexadecimal"
        ) from exc
    if not 0 <= parsed <= 0xFFFFFF:
        raise ModifyAddressValidationError(f"{name} exceeds 24 bits")
    return parsed


def _pattern_mask_value(pattern: object) -> tuple[int, int]:
    if (
        not isinstance(pattern, str)
        or len(pattern) != 24
        or set(pattern) - {"0", "1", "x"}
    ):
        raise ModifyAddressValidationError(
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


def decode_selection(
    data: dict[str, Any],
    opcode: int,
) -> dict[str, int] | None:
    """Decode Type 21 register numbers, failing closed on other words."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    instruction = data["instruction"]
    mask = int(instruction["opcode_mask"], 16)
    value = int(instruction["opcode_value"], 16)
    if opcode & mask != value:
        return None
    dag = (opcode >> 4) & 0x1
    i_local = (opcode >> 2) & 0x3
    m_local = opcode & 0x3
    return {
        "dag": dag,
        "i_local": i_local,
        "m_local": m_local,
        "i_address": (dag << 2) | i_local,
        "m_address": (dag << 2) | m_local,
        "l_address": (dag << 2) | i_local,
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
        "isa_field_database",
        "instruction",
        "fields",
        "register_selection",
        "execution_semantics",
        "assembly",
        "parallel_actions",
        "source_citations",
        "unresolved_issues",
    }
    if set(data) != expected_top_keys:
        raise ModifyAddressValidationError(
            f"database requires exactly {sorted(expected_top_keys)}"
        )
    if data["schema_version"] != 1:
        raise ModifyAddressValidationError("unsupported schema_version")
    if data["device"] != "ADSP-2100" or data["program_word_width"] != 24:
        raise ModifyAddressValidationError(
            "database must target 24-bit original ADSP-2100"
        )
    if data["status"] != "COMPLETE_FOR_ORIGINAL_TYPE_21_ACTION_DECODE":
        raise ModifyAddressValidationError(
            "database must state bounded Type 21 completeness"
        )
    if data["confidence"] != "CORROBORATED":
        raise ModifyAddressValidationError(
            "full action semantics must remain CORROBORATED"
        )
    expected_links = {
        "isa_database": "docs/generated/adsp2100_isa.yaml",
        "instruction_format_database":
            "docs/generated/adsp2100_instruction_formats.yaml",
        "isa_field_database": "docs/generated/adsp2100_isa_fields.yaml",
    }
    for key, expected in expected_links.items():
        if data[key] != expected:
            raise ModifyAddressValidationError(f"incorrect {key} link")

    isa = load_isa_database()
    formats = load_format_database()
    fields = load_field_database()
    validate_isa_database(isa)
    validate_format_database(formats)
    validate_field_database(fields)

    instruction = data["instruction"]
    required_instruction_keys = {
        "original_type",
        "name",
        "opcode_mask",
        "opcode_value",
        "encoding_pattern",
        "field_defined_encoding_count",
        "dag_count",
        "index_choices_per_dag",
        "modify_choices_per_dag",
        "condition",
        "base_instruction_cycles",
        "memory_spaces_accessed",
        "pm_data_transfer",
        "dm_transfer",
        "status_generated",
        "source_value_rule",
        "address_output_rule",
        "wait_state_sensitivity",
    }
    if set(instruction) != required_instruction_keys:
        raise ModifyAddressValidationError(
            "instruction record fields are incomplete"
        )
    if instruction["original_type"] != 21:
        raise ModifyAddressValidationError(
            "modify semantics must describe original Type 21"
        )
    mask = _parse_hex24(instruction["opcode_mask"], "opcode_mask")
    value = _parse_hex24(instruction["opcode_value"], "opcode_value")
    if (mask, value) != _pattern_mask_value(
        instruction["encoding_pattern"]
    ):
        raise ModifyAddressValidationError(
            "encoding pattern and mask/value disagree"
        )
    type_21 = isa["encoding_classes"][20]
    if (
        type_21["original_type"] != 21
        or mask != int(type_21["opcode_mask"], 16)
        or value != int(type_21["opcode_value"], 16)
    ):
        raise ModifyAddressValidationError(
            "semantic mask/value disagree with ISA Type 21"
        )
    expected_counts = {
        "field_defined_encoding_count": 32,
        "dag_count": 2,
        "index_choices_per_dag": 4,
        "modify_choices_per_dag": 4,
        "base_instruction_cycles": 1,
    }
    for key, expected in expected_counts.items():
        if instruction[key] != expected:
            raise ModifyAddressValidationError(
                f"{key} must equal {expected}"
            )
    if (
        instruction["pm_data_transfer"] != "NONE"
        or instruction["dm_transfer"] != "NONE"
        or instruction["status_generated"] != "NONE"
    ):
        raise ModifyAddressValidationError(
            "Type 21 must not claim memory-data or status effects"
        )

    expected_fields = [
        {"id": "G", "msb": 4, "lsb": 4, "role": "DAG_SELECTOR"},
        {
            "id": "I",
            "msb": 3,
            "lsb": 2,
            "role": "INDEX_SELECTOR_WITH_G",
        },
        {
            "id": "M",
            "msb": 1,
            "lsb": 0,
            "role": "MODIFY_SELECTOR_WITH_G",
        },
    ]
    if data["fields"] != expected_fields:
        raise ModifyAddressValidationError(
            "Type 21 G/I/M fields are incorrect"
        )
    format_fields = extract_fields(formats, 21, value | 0x1F)
    if format_fields != {"G": 1, "I": 3, "M": 3}:
        raise ModifyAddressValidationError(
            "semantic field positions disagree with format database"
        )

    field_tables = {
        table["id"]: table for table in fields["tables"]
    }
    if field_tables["G"]["values"] != [
        {"code": 0, "bits": "0", "name": "DAG1", "notes": ""},
        {"code": 1, "bits": "1", "name": "DAG2", "notes": ""},
    ]:
        raise ModifyAddressValidationError("G field table is incorrect")

    seen: set[tuple[int, int]] = set()
    for payload in range(32):
        opcode = value | payload
        classes = classify_opcode(isa, opcode)
        if [record["original_type"] for record in classes] != [21]:
            raise ModifyAddressValidationError(
                f"0x{opcode:06x} does not classify uniquely as Type 21"
            )
        selection = decode_selection(data, opcode)
        assert selection is not None
        expected_dag = (payload >> 4) & 1
        if selection != {
            "dag": expected_dag,
            "i_local": (payload >> 2) & 3,
            "m_local": payload & 3,
            "i_address": (expected_dag << 2) | ((payload >> 2) & 3),
            "m_address": (expected_dag << 2) | (payload & 3),
            "l_address": (expected_dag << 2) | ((payload >> 2) & 3),
        }:
            raise ModifyAddressValidationError(
                f"incorrect register selection for 0x{opcode:06x}"
            )
        if selection["i_address"] // 4 != selection["m_address"] // 4:
            raise ModifyAddressValidationError(
                "field-defined selection crosses DAGs"
            )
        seen.add((selection["i_address"], selection["m_address"]))
    if len(seen) != 32:
        raise ModifyAddressValidationError(
            "Type 21 does not enumerate 32 distinct I/M pairs"
        )
    for opcode in (value - 1, value + 0x20, 0, 0xFFFFFF):
        if decode_selection(data, opcode) is not None:
            raise ModifyAddressValidationError(
                f"non-Type-21 opcode 0x{opcode:06x} decoded as MODIFY"
            )

    selection_map = data["register_selection"]
    for dag in range(2):
        record = selection_map[f"G_{dag}"]
        base = dag * 4
        if record != {
            "dag": f"DAG{dag + 1}",
            "index_registers": [
                f"I{index}" for index in range(base, base + 4)
            ],
            "modify_registers": [
                f"M{index}" for index in range(base, base + 4)
            ],
            "length_registers_following_I": [
                f"L{index}" for index in range(base, base + 4)
            ],
        }:
            raise ModifyAddressValidationError(
                f"G={dag} register map is incorrect"
            )
    if data["assembly"] != {
        "syntax": "MODIFY (Ix, My);",
        "same_dag_required": True,
        "canonical_spacing": "MODIFY (Ix, My);",
    }:
        raise ModifyAddressValidationError(
            "MODIFY assembly contract is incorrect"
        )
    citations = data["source_citations"]
    if (
        not isinstance(citations, list)
        or len(citations) < 4
        or not any(
            citation.get("reference_id") == "ADI-UM-1989"
            and citation.get("authority") == "ORIGINAL_DEVICE_PRIMARY"
            and "A-4" in citation.get("location", "")
            for citation in citations
        )
    ):
        raise ModifyAddressValidationError(
            "exact original Type 21 citation is required"
        )
    if not any(
        citation.get("authority") == "LATER_DEVICE_CORROBORATION_ONLY"
        for citation in citations
    ):
        raise ModifyAddressValidationError(
            "later modulus wording must remain applicability-labeled"
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
    except ModifyAddressValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(
        "PASS 32 original Type 21 encodings, same-DAG selections, "
        "no memory-data/status effects"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
