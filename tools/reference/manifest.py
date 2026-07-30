"""Reference-manifest parsing and validation.

The manifest is written as JSON, which is a strict subset of YAML 1.2. Keeping
the parser in the Python standard library makes provenance checks usable before
third-party packages are installed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
CONFIDENCE_LEVELS = {
    "VERIFIED_PRIMARY",
    "VERIFIED_HARDWARE",
    "CORROBORATED",
    "INFERRED",
    "PROVISIONAL",
    "UNKNOWN",
}
AUTHORITY_LEVELS = {
    "primary_original_device",
    "primary_explicit_family",
    "primary_atari",
    "contemporary_toolchain",
    "physical_hardware",
    "original_engineer",
    "maintained_emulator",
    "prior_implementation",
    "secondary",
}
ACQUISITION_STATES = {"acquired", "identified", "unavailable", "superseded"}
REQUIRED_REFERENCE_FIELDS = {
    "id",
    "title",
    "author_or_organization",
    "publication_number",
    "publication_date",
    "revision",
    "source_url",
    "retrieval_date",
    "local_filename",
    "sha256",
    "document_type",
    "exact_device_applicability",
    "family_member_applicability",
    "redistribution_status",
    "license",
    "authority_level",
    "relevance",
    "cited_pages_or_sections",
    "may_commit",
    "acquisition_status",
    "confidence",
    "download",
    "notes",
}


class ManifestError(ValueError):
    """Raised when reference metadata violates the repository schema."""


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_manifest_path() -> Path:
    return project_root() / "docs" / "references" / "manifest.yaml"


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or default_manifest_path()
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(
            f"{manifest_path}:{exc.lineno}:{exc.colno}: invalid JSON-compatible YAML"
        ) from exc
    validate_manifest(data)
    return data


def write_manifest(data: dict[str, Any], path: Path | None = None) -> None:
    manifest_path = path or default_manifest_path()
    validate_manifest(data)
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    manifest_path.write_text(rendered, encoding="utf-8")


def validate_manifest(data: Any) -> None:
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a mapping")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError(
            f"schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}"
        )
    references = data.get("references")
    if not isinstance(references, list):
        raise ManifestError("references must be a list")

    seen_ids: set[str] = set()
    seen_local_names: set[str] = set()
    for index, reference in enumerate(references):
        where = f"references[{index}]"
        if not isinstance(reference, dict):
            raise ManifestError(f"{where} must be a mapping")
        missing = REQUIRED_REFERENCE_FIELDS - reference.keys()
        if missing:
            raise ManifestError(f"{where} missing fields: {', '.join(sorted(missing))}")

        reference_id = reference["id"]
        if not isinstance(reference_id, str) or not reference_id:
            raise ManifestError(f"{where}.id must be a nonempty string")
        if reference_id in seen_ids:
            raise ManifestError(f"duplicate reference id: {reference_id}")
        seen_ids.add(reference_id)

        if reference["authority_level"] not in AUTHORITY_LEVELS:
            raise ManifestError(
                f"{reference_id}: invalid authority_level "
                f"{reference['authority_level']!r}"
            )
        if reference["acquisition_status"] not in ACQUISITION_STATES:
            raise ManifestError(
                f"{reference_id}: invalid acquisition_status "
                f"{reference['acquisition_status']!r}"
            )
        if reference["confidence"] not in CONFIDENCE_LEVELS:
            raise ManifestError(
                f"{reference_id}: invalid confidence {reference['confidence']!r}"
            )
        if not isinstance(reference["may_commit"], bool):
            raise ManifestError(f"{reference_id}: may_commit must be boolean")
        if reference["may_commit"] and reference["redistribution_status"] != "permitted":
            raise ManifestError(
                f"{reference_id}: may_commit requires redistribution_status=permitted"
            )

        local_name = reference["local_filename"]
        if local_name is not None:
            if not isinstance(local_name, str) or not local_name:
                raise ManifestError(
                    f"{reference_id}: local_filename must be null or nonempty string"
                )
            local_path = Path(local_name)
            if local_path.is_absolute() or ".." in local_path.parts:
                raise ManifestError(f"{reference_id}: unsafe local_filename")
            if local_name in seen_local_names:
                raise ManifestError(f"duplicate local_filename: {local_name}")
            seen_local_names.add(local_name)

        digest = reference["sha256"]
        if digest is not None and (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ManifestError(f"{reference_id}: sha256 must be null or 64 lowercase hex")
        if reference["acquisition_status"] == "acquired":
            if local_name is None or digest is None or reference["retrieval_date"] is None:
                raise ManifestError(
                    f"{reference_id}: acquired entries need filename, hash, and date"
                )

        download = reference["download"]
        if not isinstance(download, dict):
            raise ManifestError(f"{reference_id}: download must be a mapping")
        if set(download) != {"enabled", "expected_content_types", "max_bytes"}:
            raise ManifestError(
                f"{reference_id}: download requires enabled, "
                "expected_content_types, and max_bytes"
            )
        if not isinstance(download["enabled"], bool):
            raise ManifestError(f"{reference_id}: download.enabled must be boolean")
        if download["enabled"] and local_name is None:
            raise ManifestError(
                f"{reference_id}: enabled download requires local_filename"
            )
        if (
            not isinstance(download["expected_content_types"], list)
            or not all(
                isinstance(item, str) and item
                for item in download["expected_content_types"]
            )
        ):
            raise ManifestError(
                f"{reference_id}: expected_content_types must be a string list"
            )
        if (
            not isinstance(download["max_bytes"], int)
            or download["max_bytes"] <= 0
        ):
            raise ManifestError(f"{reference_id}: max_bytes must be positive")


def references_by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in data["references"]}


def cache_path(reference: dict[str, Any], cache_dir: Path) -> Path | None:
    local_name = reference["local_filename"]
    return None if local_name is None else cache_dir / local_name


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_looks_valid(
    path: Path,
    content_type: str,
    expected_content_types: list[str],
) -> tuple[bool, str]:
    normalized_type = content_type.split(";", 1)[0].strip().lower()
    normalized_expected = {item.lower() for item in expected_content_types}
    if normalized_type not in normalized_expected:
        return (
            False,
            f"content type {normalized_type!r} not in {sorted(normalized_expected)!r}",
        )

    prefix = path.read_bytes()[:1024]
    stripped = prefix.lstrip().lower()
    if "application/pdf" in normalized_expected:
        if b"%pdf-" not in prefix[:1024].lower():
            return False, "PDF signature not found in first 1024 bytes"
        if stripped.startswith((b"<html", b"<!doctype html")):
            return False, "HTML error page detected where PDF was expected"
    return True, "ok"
