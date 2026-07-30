#!/usr/bin/env python3
"""Safely fetch public reference files into the gitignored local cache."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import date
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
    references_by_id,
    sha256_file,
    write_manifest,
)

USER_AGENT = "adsp-2100_sv-reference-fetcher/0.1 (+clean-room research)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", type=Path, default=default_manifest_path(), help="manifest path"
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=project_root() / "reference_cache",
        help="gitignored destination directory",
    )
    parser.add_argument("--id", action="append", dest="ids", help="fetch only this ID")
    parser.add_argument(
        "--update-manifest",
        action="store_true",
        help="record retrieval date and a previously absent SHA-256",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="redownload even if a valid local file exists",
    )
    return parser.parse_args()


def fetch_one(
    reference: dict[str, object],
    cache_dir: Path,
    refresh: bool,
) -> tuple[str, str | None]:
    reference_id = str(reference["id"])
    destination = cache_path(reference, cache_dir)
    if destination is None:
        return "SKIP", "no local filename"
    destination.parent.mkdir(parents=True, exist_ok=True)

    expected_digest = reference["sha256"]
    expected_types = list(reference["download"]["expected_content_types"])  # type: ignore[index]
    if destination.exists() and not refresh:
        digest = sha256_file(destination)
        if expected_digest is not None and digest != expected_digest:
            return "FAIL", f"local SHA-256 mismatch: {digest}"
        guessed_type = (
            "application/pdf"
            if destination.suffix.lower() == ".pdf"
            else expected_types[0]
        )
        valid, reason = content_looks_valid(destination, guessed_type, expected_types)
        if not valid:
            return "FAIL", f"invalid existing file: {reason}"
        return "PRESENT", digest

    request = urllib.request.Request(
        str(reference["source_url"]),
        headers={"User-Agent": USER_AGENT, "Accept": ", ".join(expected_types)},
    )
    max_bytes = int(reference["download"]["max_bytes"])  # type: ignore[index]
    temporary_path: Path | None = None
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            status = getattr(response, "status", None)
            if status != 200:
                return "FAIL", f"HTTP status {status}"
            content_type = response.headers.get_content_type().lower()
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > max_bytes:
                return "FAIL", f"content length {content_length} exceeds {max_bytes}"

            with tempfile.NamedTemporaryFile(
                prefix=f".{destination.name}.",
                suffix=".part",
                dir=destination.parent,
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        return "FAIL", f"download exceeded {max_bytes} bytes"
                    temporary.write(chunk)

        assert temporary_path is not None
        valid, reason = content_looks_valid(
            temporary_path, content_type, expected_types
        )
        if not valid:
            return "FAIL", reason
        digest = sha256_file(temporary_path)
        if expected_digest is not None and digest != expected_digest:
            return "FAIL", f"downloaded SHA-256 mismatch: {digest}"
        os.replace(temporary_path, destination)
        temporary_path = None
        return "FETCHED", digest
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return "FAIL", str(exc)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    try:
        manifest = load_manifest(args.manifest)
    except ManifestError as exc:
        print(f"FAIL manifest: {exc}", file=sys.stderr)
        return 2

    known = references_by_id(manifest)
    if args.ids:
        unknown = sorted(set(args.ids) - known.keys())
        if unknown:
            print(f"FAIL unknown reference IDs: {', '.join(unknown)}", file=sys.stderr)
            return 2
        selected = [known[reference_id] for reference_id in args.ids]
    else:
        selected = [
            reference
            for reference in manifest["references"]
            if reference["download"]["enabled"]
        ]

    failures = 0
    changed = False
    for reference in selected:
        if not reference["download"]["enabled"]:
            print(f"SKIP {reference['id']}: download disabled")
            continue
        status, detail = fetch_one(reference, args.cache, args.refresh)
        if status == "FAIL":
            failures += 1
            print(f"FAIL {reference['id']}: {detail}", file=sys.stderr)
            continue
        print(f"{status} {reference['id']}: {detail}")
        if args.update_manifest and detail is not None:
            if reference["sha256"] is None:
                reference["sha256"] = detail
                changed = True
            if reference["retrieval_date"] is None:
                reference["retrieval_date"] = date.today().isoformat()
                changed = True
            if reference["acquisition_status"] != "acquired":
                reference["acquisition_status"] = "acquired"
                changed = True

    if changed:
        manifest["updated"] = date.today().isoformat()
        try:
            write_manifest(manifest, args.manifest)
        except ManifestError as exc:
            print(f"FAIL refusing invalid manifest update: {exc}", file=sys.stderr)
            return 2
        print(f"UPDATED {args.manifest}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
