#!/usr/bin/env python3
"""Validate the original ADSP-2100 Appendix A abbreviation-code tables."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_isa_fields.yaml"

EXPECTED_TABLES = {
    "AMF": (5, 32),
    "CP": (1, 2),
    "D": (1, 2),
    "DD": (2, 4),
    "DREG": (4, 16),
    "G": (1, 2),
    "G_I": (3, 8),
    "LP": (1, 2),
    "G_M": (3, 8),
    "MCC": (2, 4),
    "PD": (2, 4),
    "PP": (1, 2),
    "S": (1, 2),
    "SF": (4, 16),
    "SPP": (2, 4),
    "T": (1, 2),
    "X": (3, 8),
    "Y": (2, 4),
    "Z": (1, 2),
}


class ISAFieldValidationError(ValueError):
    """The machine-readable ISA field table is inconsistent."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ISAFieldValidationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ISAFieldValidationError("database root must be an object")
    return data


def validate_database(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1 or data.get("device") != "ADSP-2100":
        raise ISAFieldValidationError("database must target schema 1 original ADSP-2100")
    if data.get("status") != "COMPLETE_FOR_APPENDIX_A_ABBREVIATION_TABLES_LISTED":
        raise ISAFieldValidationError("field-table completeness boundary is missing")
    citations = data.get("source_citations")
    if not isinstance(citations, list) or not citations:
        raise ISAFieldValidationError("field tables require a primary citation")
    if data.get("confidence") != "VERIFIED_PRIMARY":
        raise ISAFieldValidationError("field tables must retain primary-backed confidence")
    if data.get("external_tables") != {
        "COND_TERM": "docs/generated/adsp2100_condition_codes.yaml",
        "RGP_REG": "docs/generated/adsp2100_register_codes.yaml",
    }:
        raise ISAFieldValidationError("condition and register external-table links are incomplete")
    if data.get("mcc_targets") != [
        {"id": "SR", "name": "SECONDARY_REGISTER_BANK_MODE"},
        {"id": "BR", "name": "BIT_REVERSE_MODE"},
        {"id": "OL", "name": "ALU_OVERFLOW_LATCH_MODE"},
        {"id": "AS", "name": "AR_SATURATE_MODE"},
    ]:
        raise ISAFieldValidationError("original mode-control targets are incomplete")

    tables = data.get("tables")
    if not isinstance(tables, list):
        raise ISAFieldValidationError("tables must be a list")
    if [table.get("id") for table in tables] != list(EXPECTED_TABLES):
        raise ISAFieldValidationError("field tables are missing, duplicated, or out of review order")

    for table in tables:
        if set(table) != {"id", "description", "width", "notes", "values"}:
            raise ISAFieldValidationError(f"{table.get('id')} has incomplete table metadata")
        table_id = table["id"]
        width, count = EXPECTED_TABLES[table_id]
        if table["width"] != width:
            raise ISAFieldValidationError(f"{table_id} has wrong field width")
        values = table["values"]
        if not isinstance(values, list) or len(values) != count:
            raise ISAFieldValidationError(f"{table_id} must account for all {count} codes")
        if [entry.get("code") for entry in values] != list(range(count)):
            raise ISAFieldValidationError(f"{table_id} codes must be ordered and exhaustive")
        for code, entry in enumerate(values):
            if set(entry) != {"code", "bits", "name", "notes"}:
                raise ISAFieldValidationError(f"{table_id}[{code}] has incomplete fields")
            if entry["bits"] != f"{code:0{width}b}":
                raise ISAFieldValidationError(f"{table_id}[{code}] has wrong bit text")
            if not isinstance(entry["name"], str) or not entry["name"]:
                raise ISAFieldValidationError(f"{table_id}[{code}] lacks a semantic name")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATABASE
    try:
        validate_database(load_database(path))
    except ISAFieldValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS 19 exhaustive original Appendix A ISA field tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
