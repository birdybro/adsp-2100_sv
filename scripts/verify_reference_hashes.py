#!/usr/bin/env python3
"""Verify acquired reference files against manifest SHA-256 values."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.reference.manifest import (
    ManifestError,
    cache_path,
    content_looks_valid,
    default_manifest_path,
    load_manifest,
    project_root,
    sha256_file,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=default_manifest_path())
    parser.add_argument(
        "--cache", type=Path, default=project_root() / "reference_cache"
    )
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
    except ManifestError as exc:
        print(f"FAIL manifest: {exc}", file=sys.stderr)
        return 2

    failures = 0
    verified = 0
    for reference in manifest["references"]:
        if reference["acquisition_status"] != "acquired":
            continue
        path = cache_path(reference, args.cache)
        if path is None or not path.is_file():
            failures += 1
            print(f"FAIL {reference['id']}: acquired file is missing", file=sys.stderr)
            continue
        digest = sha256_file(path)
        if digest != reference["sha256"]:
            failures += 1
            print(
                f"FAIL {reference['id']}: expected {reference['sha256']}, got {digest}",
                file=sys.stderr,
            )
            continue
        expected_types = reference["download"]["expected_content_types"]
        guessed_type = (
            "application/pdf"
            if path.suffix.lower() == ".pdf"
            else expected_types[0]
        )
        valid, reason = content_looks_valid(path, guessed_type, expected_types)
        if not valid:
            failures += 1
            print(f"FAIL {reference['id']}: {reason}", file=sys.stderr)
            continue
        verified += 1
        print(f"PASS {reference['id']}: {digest}")
    print(f"SUMMARY verified={verified} failed={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
