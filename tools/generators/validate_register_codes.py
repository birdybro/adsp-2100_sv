#!/usr/bin/env python3
"""Validate original ADSP-2100 RGP/REG general-MOVE code metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = ROOT / "docs/generated/adsp2100_register_codes.yaml"


class RegisterCodeError(ValueError):
    pass


def load_and_validate(path: Path = DEFAULT_DATABASE) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegisterCodeError(f"cannot load {path}: {exc}") from exc
    if data.get("schema_version") != 1 or data.get("device") != "ADSP-2100":
        raise RegisterCodeError("wrong schema or device")
    if data.get("field_widths") != {"RGP": 2, "REG": 4}:
        raise RegisterCodeError("RGP/REG widths must be 2/4")
    groups = data.get("groups")
    if not isinstance(groups, dict) or set(groups) != {"00", "01", "10", "11"}:
        raise RegisterCodeError("exactly four binary RGP groups are required")
    register_names: set[str] = set()
    for group_code, group in groups.items():
        if not isinstance(group, dict):
            raise RegisterCodeError(f"RGP {group_code} must be an object")
        codes = group.get("codes")
        reserved = group.get("reserved_codes")
        if not isinstance(codes, dict) or not isinstance(reserved, list):
            raise RegisterCodeError(f"RGP {group_code} needs codes and reserved_codes")
        numeric_codes = {int(code) for code in codes}
        reserved_codes = set(reserved)
        if numeric_codes & reserved_codes:
            raise RegisterCodeError(f"RGP {group_code} code is both register and reserved")
        if numeric_codes | reserved_codes != set(range(16)):
            raise RegisterCodeError(f"RGP {group_code} does not account for all REG codes")
        for code, metadata in codes.items():
            if not isinstance(metadata, dict):
                raise RegisterCodeError(f"RGP {group_code} REG {code} metadata invalid")
            register = metadata.get("register")
            width = metadata.get("storage_width")
            access = metadata.get("move_access")
            if not isinstance(register, str) or register in register_names:
                raise RegisterCodeError(f"duplicate/invalid register {register!r}")
            register_names.add(register)
            if not isinstance(width, int) or not 1 <= width <= 16:
                raise RegisterCodeError(f"{register} has invalid storage width")
            if not isinstance(access, str) or not access:
                raise RegisterCodeError(f"{register} has invalid access")
    if data.get("not_general_move_encoded") != ["AF", "MF", "PC"]:
        raise RegisterCodeError("AF, MF, and PC exclusion must remain explicit")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", nargs="?", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    try:
        data = load_and_validate(args.database)
    except RegisterCodeError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    count = sum(len(group["codes"]) for group in data["groups"].values())
    print(f"PASS {count} register codes and 3 explicit non-encoded registers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
