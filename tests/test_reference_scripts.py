from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.fetch_references import fetch_one


def reference_for(local_filename: str, sha256: str | None) -> dict[str, object]:
    return {
        "id": "TEST-PDF",
        "source_url": "https://invalid.example.invalid/manual.pdf",
        "local_filename": local_filename,
        "sha256": sha256,
        "download": {
            "enabled": True,
            "expected_content_types": ["application/pdf"],
            "max_bytes": 1024,
        },
    }


class ReferenceScriptTests(unittest.TestCase):
    def test_existing_valid_payload_is_idempotent_without_network(self) -> None:
        payload = b"%PDF-1.4\n% deterministic test payload\n"
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary)
            destination = cache / "test/manual.pdf"
            destination.parent.mkdir()
            destination.write_bytes(payload)
            status, detail = fetch_one(
                reference_for("test/manual.pdf", digest), cache, refresh=False
            )
        self.assertEqual(status, "PRESENT")
        self.assertEqual(detail, digest)

    def test_existing_digest_mismatch_fails_without_replacement(self) -> None:
        payload = b"%PDF-1.4\n% wrong payload\n"
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary)
            destination = cache / "test/manual.pdf"
            destination.parent.mkdir()
            destination.write_bytes(payload)
            status, detail = fetch_one(
                reference_for("test/manual.pdf", "0" * 64), cache, refresh=False
            )
            self.assertEqual(destination.read_bytes(), payload)
        self.assertEqual(status, "FAIL")
        self.assertIn("SHA-256 mismatch", detail)


if __name__ == "__main__":
    unittest.main()
