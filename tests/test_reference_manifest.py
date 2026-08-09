from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.reference.manifest import content_looks_valid, load_manifest


class ReferenceManifestTests(unittest.TestCase):
    def test_manifest_is_valid_and_ids_are_unique(self) -> None:
        manifest = load_manifest()
        ids = [reference["id"] for reference in manifest["references"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 15)

    def test_acquired_material_with_unclear_rights_is_not_committable(self) -> None:
        manifest = load_manifest()
        for reference in manifest["references"]:
            if reference["redistribution_status"] != "permitted":
                self.assertFalse(reference["may_commit"], reference["id"])

    def test_every_acquired_reference_is_hash_pinned(self) -> None:
        manifest = load_manifest()
        acquired = [
            reference
            for reference in manifest["references"]
            if reference["acquisition_status"] == "acquired"
        ]
        self.assertGreaterEqual(len(acquired), 10)
        for reference in acquired:
            self.assertRegex(reference["sha256"], r"^[0-9a-f]{64}$")
            self.assertIsNotNone(reference["retrieval_date"])

    def test_joint_original_device_datasheet_is_hash_pinned(self) -> None:
        manifest = load_manifest()
        references = {
            reference["id"]: reference
            for reference in manifest["references"]
        }
        joint = references["ADI-DATABOOK-1989"]
        self.assertEqual(joint["acquisition_status"], "acquired")
        self.assertEqual(joint["authority_level"], "primary_original_device")
        self.assertEqual(
            joint["family_member_applicability"][:2],
            ["ADSP-2100", "ADSP-2100A"],
        )
        self.assertRegex(joint["sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(
            any(
                "printed p. 2-19" in citation
                for citation in joint["cited_pages_or_sections"]
            )
        )

    def test_html_error_page_is_rejected_as_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "error.pdf"
            path.write_text("<!doctype html><title>not a manual</title>", encoding="utf-8")
            valid, reason = content_looks_valid(
                path, "application/pdf", ["application/pdf"]
            )
        self.assertFalse(valid)
        self.assertIn("PDF signature", reason)

    def test_realistic_pdf_prefix_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manual.pdf"
            path.write_bytes(b"%PDF-1.4\n% test fixture\n")
            valid, reason = content_looks_valid(
                path, "application/pdf", ["application/pdf"]
            )
        self.assertTrue(valid, reason)


if __name__ == "__main__":
    unittest.main()
