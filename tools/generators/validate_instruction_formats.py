#!/usr/bin/env python3
"""Validate original ADSP-2100 Appendix A instruction field placement."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = (
    ROOT / "docs/generated/adsp2100_instruction_formats.yaml"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.generators.validate_condition_codes import (  # noqa: E402
    load_database as load_condition_database,
    validate_database as validate_condition_database,
)
from tools.generators.validate_isa import (  # noqa: E402
    load_database as load_isa_database,
    validate_database as validate_isa_database,
)
from tools.generators.validate_isa_fields import (  # noqa: E402
    load_database as load_field_database,
    validate_database as validate_field_database,
)
from tools.generators.validate_register_codes import (  # noqa: E402
    load_and_validate as load_register_database,
)


class InstructionFormatValidationError(ValueError):
    """Raised when a format record disagrees with the original class masks."""


def load_database(path: Path = DEFAULT_DATABASE) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstructionFormatValidationError(
            f"cannot load {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise InstructionFormatValidationError(
            "instruction-format database root must be an object"
        )
    return data


def _code_table_widths() -> dict[str, int]:
    field_database = load_field_database()
    condition_database = load_condition_database()
    register_database = load_register_database()
    validate_field_database(field_database)
    validate_condition_database(condition_database)

    widths = {
        f"ISA_FIELDS:{table['id']}": table["width"]
        for table in field_database["tables"]
    }
    widths["CONDITION_CODES"] = condition_database["field_width"]
    for name, width in register_database["field_widths"].items():
        widths[f"REGISTER_CODES:{name}"] = width
    return widths


def _field_mask(field: dict[str, Any]) -> int:
    width = field["msb"] - field["lsb"] + 1
    return ((1 << width) - 1) << field["lsb"]


def extract_fields(
    data: dict[str, Any],
    original_type: int,
    opcode: int,
) -> dict[str, int]:
    """Extract the named format fields from one already-classified opcode."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    record = next(
        (
            item
            for item in data["formats"]
            if item["original_type"] == original_type
        ),
        None,
    )
    if record is None:
        raise ValueError(f"unknown original instruction type {original_type}")
    return {
        field["id"]: (opcode & _field_mask(field)) >> field["lsb"]
        for field in record["fields"]
    }


def validate_database(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise InstructionFormatValidationError(
            "unsupported instruction-format schema_version"
        )
    if data.get("device") != "ADSP-2100":
        raise InstructionFormatValidationError(
            "instruction formats must target the exact ADSP-2100"
        )
    if data.get("program_word_width") != 24:
        raise InstructionFormatValidationError(
            "program_word_width must be 24"
        )
    if data.get("status") != "COMPLETE_FOR_APPENDIX_A_BIT_PLACEMENT":
        raise InstructionFormatValidationError(
            "format database must state its bounded completeness"
        )
    if data.get("isa_database") != "docs/generated/adsp2100_isa.yaml":
        raise InstructionFormatValidationError(
            "format database must link the source ISA database"
        )
    citations = data.get("source_citations")
    if (
        not isinstance(citations, list)
        or not citations
        or not all(isinstance(item, str) and item for item in citations)
    ):
        raise InstructionFormatValidationError(
            "format database requires primary source citations"
        )
    if data.get("confidence") != "VERIFIED_PRIMARY":
        raise InstructionFormatValidationError(
            "completed bit placement must retain VERIFIED_PRIMARY confidence"
        )

    isa_database = load_isa_database()
    validate_isa_database(isa_database)
    classes = {
        item["original_type"]: item
        for item in isa_database["encoding_classes"]
    }
    formats = data.get("formats")
    if (
        not isinstance(formats, list)
        or [item.get("original_type") for item in formats]
        != list(range(1, 31))
    ):
        raise InstructionFormatValidationError(
            "formats must enumerate original Types 1 through 30"
        )

    table_widths = _code_table_widths()
    field_name_pattern = re.compile(r"^[A-Z][A-Z0-9_]*$")
    format_keys = {"original_type", "fields", "notes"}
    field_keys = {"id", "msb", "lsb", "code_table", "role"}
    for record in formats:
        original_type = record["original_type"]
        where = f"type {original_type}"
        if set(record) != format_keys:
            raise InstructionFormatValidationError(
                f"{where} requires exactly {sorted(format_keys)}"
            )
        if not isinstance(record["notes"], str):
            raise InstructionFormatValidationError(
                f"{where}.notes must be a string"
            )
        fields = record["fields"]
        if not isinstance(fields, list):
            raise InstructionFormatValidationError(
                f"{where}.fields must be a list"
            )

        occupied_mask = 0
        seen_ids: set[str] = set()
        prior_msb = 24
        for index, field in enumerate(fields):
            field_where = f"{where}.fields[{index}]"
            if not isinstance(field, dict) or set(field) != field_keys:
                raise InstructionFormatValidationError(
                    f"{field_where} requires exactly {sorted(field_keys)}"
                )
            field_id = field["id"]
            if (
                not isinstance(field_id, str)
                or field_name_pattern.fullmatch(field_id) is None
                or field_id in seen_ids
            ):
                raise InstructionFormatValidationError(
                    f"{field_where}.id is invalid or duplicated"
                )
            seen_ids.add(field_id)
            msb = field["msb"]
            lsb = field["lsb"]
            if (
                not isinstance(msb, int)
                or not isinstance(lsb, int)
                or not 0 <= lsb <= msb < 24
            ):
                raise InstructionFormatValidationError(
                    f"{field_where} has an invalid inclusive bit range"
                )
            if msb >= prior_msb:
                raise InstructionFormatValidationError(
                    f"{where} fields must be ordered from high to low bits"
                )
            prior_msb = msb
            mask = _field_mask(field)
            if occupied_mask & mask:
                raise InstructionFormatValidationError(
                    f"{where} fields overlap at mask 0x{mask:06x}"
                )
            occupied_mask |= mask

            role = field["role"]
            if not isinstance(role, str) or not role:
                raise InstructionFormatValidationError(
                    f"{field_where}.role must be nonempty"
                )
            code_table = field["code_table"]
            if code_table is not None:
                if code_table not in table_widths:
                    raise InstructionFormatValidationError(
                        f"{field_where} references unknown {code_table!r}"
                    )
                width = msb - lsb + 1
                if table_widths[code_table] != width:
                    raise InstructionFormatValidationError(
                        f"{field_where} width {width} disagrees with "
                        f"{code_table} width {table_widths[code_table]}"
                    )

        class_mask = int(classes[original_type]["opcode_mask"], 16)
        expected_variable_mask = (~class_mask) & 0xFFFFFF
        if occupied_mask != expected_variable_mask:
            raise InstructionFormatValidationError(
                f"{where} fields cover 0x{occupied_mask:06x}, not class "
                f"variable mask 0x{expected_variable_mask:06x}"
            )

    stack_format = formats[25]
    if [
        (field["id"], field["msb"], field["lsb"])
        for field in stack_format["fields"]
    ] != [
        ("PP", 4, 4),
        ("LP", 3, 3),
        ("CP", 2, 2),
        ("SPP", 1, 0),
    ]:
        raise InstructionFormatValidationError(
            "Type 26 must preserve the primary PP/LP/CP/SPP field layout"
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
    except InstructionFormatValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    field_count = sum(len(item["fields"]) for item in data["formats"])
    variable_bits = sum(
        field["msb"] - field["lsb"] + 1
        for item in data["formats"]
        for field in item["fields"]
    )
    print(
        "PASS 30 original Appendix A formats, "
        f"{field_count} named fields, and {variable_bits} variable bit "
        "positions exactly partition their source-backed class masks"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
