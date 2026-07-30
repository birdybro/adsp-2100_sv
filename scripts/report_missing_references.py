#!/usr/bin/env python3
"""Report identified references that are unavailable from the local cache."""

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
    default_manifest_path,
    load_manifest,
    project_root,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=default_manifest_path())
    parser.add_argument(
        "--cache", type=Path, default=project_root() / "reference_cache"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return nonzero if any enabled or acquired reference is missing",
    )
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
    except ManifestError as exc:
        print(f"FAIL manifest: {exc}", file=sys.stderr)
        return 2

    missing_required = 0
    missing_identified = 0
    for reference in manifest["references"]:
        path = cache_path(reference, args.cache)
        present = path is not None and path.is_file()
        if present:
            continue
        if reference["download"]["enabled"] or reference["acquisition_status"] == "acquired":
            missing_required += 1
            category = "FETCHABLE"
        else:
            missing_identified += 1
            category = reference["acquisition_status"].upper()
        print(
            f"{category} {reference['id']}: {reference['title']} | "
            f"{reference['source_url']}"
        )
    print(
        f"SUMMARY fetchable_or_acquired_missing={missing_required} "
        f"identified_only={missing_identified}"
    )
    return 1 if args.strict and missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
