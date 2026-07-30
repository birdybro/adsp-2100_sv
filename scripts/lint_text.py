#!/usr/bin/env python3
"""Small dependency-free source hygiene check used before richer linters."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".sv", ".svh", ".yaml", ".yml", ".json", ".tcl", ".sdc"}
EXCLUDED_PARTS = {".git", "build", "reference_cache", "__pycache__"}
EXCLUDED_RELATIVE_DIRS = {
    Path("synthesis/quartus/db"),
    Path("synthesis/quartus/incremental_db"),
}


def source_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if EXCLUDED_PARTS.intersection(relative.parts):
            continue
        if any(relative.is_relative_to(directory) for directory in EXCLUDED_RELATIVE_DIRS):
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    failures: list[str] = []
    for path in source_files():
        relative = path.relative_to(ROOT)
        content = path.read_bytes()
        if content and not content.endswith(b"\n"):
            failures.append(f"{relative}: missing final newline")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            failures.append(f"{relative}: not UTF-8: {exc}")
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if line != line.rstrip(" \t"):
                failures.append(f"{relative}:{number}: trailing whitespace")
            if "\r" in line:
                failures.append(f"{relative}:{number}: carriage return")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print(f"PASS text hygiene ({len(source_files())} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
