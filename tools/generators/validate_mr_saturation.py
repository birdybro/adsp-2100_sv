#!/usr/bin/env python3
"""Validate source-backed original ADSP-2100 Type 25 semantics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_mr_saturation.yaml"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.generators.validate_instruction_formats import (  # noqa: E402
    load_database as load_format_database,
    validate_database as validate_format_database,
)
from tools.generators.validate_isa import (  # noqa: E402
    load_database as load_isa_database,
    validate_database as validate_isa_database,
)


class MRSaturationValidationError(ValueError):
    """Raised when Type 25 semantics disagree with verified source records."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MRSaturationValidationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise MRSaturationValidationError("database root must be an object")
    return data


def validate_database(data: dict[str, Any]) -> None:
    expected_keys = {
        "schema_version",
        "device",
        "program_word_width",
        "status",
        "confidence",
        "isa_database",
        "instruction_format_database",
        "instruction",
        "result_table",
        "execution_semantics",
        "source_citations",
        "unresolved_issues",
    }
    if set(data) != expected_keys:
        raise MRSaturationValidationError(
            f"database requires exactly {sorted(expected_keys)}"
        )
    if (
        data["schema_version"] != 1
        or data["device"] != "ADSP-2100"
        or data["program_word_width"] != 24
    ):
        raise MRSaturationValidationError(
            "database must target the 24-bit original ADSP-2100"
        )
    if data["status"] != "COMPLETE_FOR_TYPE_25_ARCHITECTURAL_ACTION":
        raise MRSaturationValidationError("bounded completeness is missing")
    if data["confidence"] != "VERIFIED_PRIMARY":
        raise MRSaturationValidationError("Type 25 requires primary confidence")

    isa = load_isa_database()
    formats = load_format_database()
    validate_isa_database(isa)
    validate_format_database(formats)

    instruction = data["instruction"]
    if (
        instruction["original_type"] != 25
        or instruction["syntax"] != "IF MV SAT MR;"
        or instruction["opcode_mask"] != "0xffffff"
        or instruction["opcode_value"] != "0x050000"
        or instruction["encoding_pattern"]
        != "000001010000000000000000"
        or instruction["field_defined_encoding_count"] != 1
        or instruction["base_instruction_cycles"] != 1
        or instruction["status_flags_written"] != []
    ):
        raise MRSaturationValidationError(
            "Type 25 opcode, timing, or action metadata is incorrect"
        )

    type_25 = next(
        item for item in isa["encoding_classes"]
        if item["original_type"] == 25
    )
    if (
        instruction["opcode_mask"] != type_25["opcode_mask"]
        or instruction["opcode_value"] != type_25["opcode_value"]
        or instruction["encoding_pattern"] != type_25["encoding_pattern"]
    ):
        raise MRSaturationValidationError(
            "semantic opcode disagrees with ISA Type 25"
        )
    format_25 = next(
        item for item in formats["formats"]
        if item["original_type"] == 25
    )
    if format_25["fields"] != []:
        raise MRSaturationValidationError(
            "exact Type 25 encoding must not acquire variable fields"
        )

    expected_results = [
        {"mv": 0, "mr2_msb": "DONT_CARE", "result": "UNCHANGED"},
        {"mv": 1, "mr2_msb": 0, "result": "0x007fffffff"},
        {"mv": 1, "mr2_msb": 1, "result": "0xff80000000"},
    ]
    if data["result_table"] != expected_results:
        raise MRSaturationValidationError(
            "MR saturation result table is incorrect"
        )
    if (
        data["execution_semantics"]["source_reads"] != "CYCLE_START"
        or data["execution_semantics"]["state_commit"] != "CYCLE_END"
        or data["execution_semantics"]["astat_effect"] != "UNCHANGED"
    ):
        raise MRSaturationValidationError(
            "cycle boundary or status preservation is incorrect"
        )
    if not any(
        citation.get("authority") == "ORIGINAL_DEVICE_PRIMARY"
        for citation in data["source_citations"]
    ):
        raise MRSaturationValidationError("primary source citation is required")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", nargs="?", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    try:
        data = load_database(args.database)
        validate_database(data)
    except MRSaturationValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS original ADSP-2100 Type 25 MR-saturation semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
