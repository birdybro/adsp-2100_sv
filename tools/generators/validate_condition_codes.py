#!/usr/bin/env python3
"""Validate the original ADSP-2100 IF and DO UNTIL condition-code tables."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_condition_codes.yaml"

EXPECTED_IF_MNEMONICS = (
    "EQ",
    "NE",
    "GT",
    "LE",
    "LT",
    "GE",
    "AV",
    "NOT AV",
    "AC",
    "NOT AC",
    "NEG",
    "POS",
    "MV",
    "NOT MV",
    "NOT CE",
    "TRUE",
)

EXPECTED_DO_MNEMONICS = (
    "NE",
    "EQ",
    "LE",
    "GT",
    "GE",
    "LT",
    "NOT AV",
    "AV",
    "NOT AC",
    "AC",
    "POS",
    "NEG",
    "NOT MV",
    "MV",
    "CE",
    "FOREVER",
)

EXPECTED_IF_PREDICATES = (
    "az",
    "not az",
    "not ((an xor av) or az)",
    "(an xor av) or az",
    "an xor av",
    "not (an xor av)",
    "av",
    "not av",
    "ac",
    "not ac",
    "as",
    "not as",
    "mv",
    "not mv",
    "not_counter_expired",
    "true",
)

EXPECTED_DO_PREDICATES = (
    "not az",
    "az",
    "(an xor av) or az",
    "not ((an xor av) or az)",
    "not (an xor av)",
    "an xor av",
    "not av",
    "av",
    "not ac",
    "ac",
    "not as",
    "as",
    "not mv",
    "mv",
    "counter_expired",
    "false",
)


class ConditionCodeValidationError(ValueError):
    """The machine-readable condition table is inconsistent."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConditionCodeValidationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConditionCodeValidationError("database root must be an object")
    return data


def _validate_table(
    table: object,
    expected_mnemonics: tuple[str, ...],
    expected_predicates: tuple[str, ...],
    *,
    require_if_relation: bool,
) -> None:
    if not isinstance(table, list) or len(table) != 16:
        raise ConditionCodeValidationError("condition table must contain 16 entries")
    if [entry.get("code") for entry in table] != list(range(16)):
        raise ConditionCodeValidationError("condition codes must be ordered 0 through 15")
    if tuple(entry.get("mnemonic") for entry in table) != expected_mnemonics:
        raise ConditionCodeValidationError("condition mnemonic ordering disagrees with Appendix A")
    if tuple(entry.get("predicate") for entry in table) != expected_predicates:
        raise ConditionCodeValidationError("condition predicates disagree with the primary tables")
    for code, entry in enumerate(table):
        required = {"code", "bits", "mnemonic", "predicate"}
        if require_if_relation:
            required.add("same_code_if_mnemonic")
        if not isinstance(entry, dict) or set(entry) != required:
            raise ConditionCodeValidationError(
                f"condition code {code} has incomplete or unexpected fields"
            )
        if entry["bits"] != f"{code:04b}":
            raise ConditionCodeValidationError(f"condition code {code} has wrong bit text")
        if not isinstance(entry["predicate"], str) or not entry["predicate"]:
            raise ConditionCodeValidationError(f"condition code {code} lacks a predicate")


def validate_database(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ConditionCodeValidationError("unsupported schema_version")
    if data.get("device") != "ADSP-2100" or data.get("field_width") != 4:
        raise ConditionCodeValidationError("database must describe the original 4-bit field")
    if data.get("status") != "COMPLETE_FOR_ORIGINAL_CONDITION_FIELD":
        raise ConditionCodeValidationError("condition-field completeness status is missing")
    citations = data.get("source_citations")
    if not isinstance(citations, list) or len(citations) < 3:
        raise ConditionCodeValidationError("condition codes require page-level primary citations")
    if data.get("confidence") != "VERIFIED_PRIMARY":
        raise ConditionCodeValidationError("condition table confidence must remain primary-backed")

    if_table = data.get("if_conditions")
    do_table = data.get("do_until_termination_conditions")
    _validate_table(
        if_table,
        EXPECTED_IF_MNEMONICS,
        EXPECTED_IF_PREDICATES,
        require_if_relation=False,
    )
    _validate_table(
        do_table,
        EXPECTED_DO_MNEMONICS,
        EXPECTED_DO_PREDICATES,
        require_if_relation=True,
    )

    for code, entry in enumerate(do_table):
        if entry["same_code_if_mnemonic"] != if_table[code]["mnemonic"]:
            raise ConditionCodeValidationError(
                f"DO condition {code} does not identify its same-code IF condition"
            )


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATABASE
    try:
        validate_database(load_database(path))
    except ConditionCodeValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS all 16 IF and 16 inverse-sense DO UNTIL condition codes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
