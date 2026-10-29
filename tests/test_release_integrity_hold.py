"""Regression checks for the 2026-10-30 release-integrity hold.

These tests must never call Drive, Sheets, Buffer or Gumroad.
"""
import io
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

from scripts import asset_pipeline as pipeline
from src import autopilot as a


class ReleaseIntegrityHoldTests(unittest.TestCase):
    def test_manifest_does_not_touch_google_or_historical_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "manifest.json").write_text('{"campaign":"untrusted","stale_q_ids":["Q-01"]}')
            with patch.object(pipeline, "_build_credentials", side_effect=AssertionError("credentials touched")), \
                 patch.object(pipeline, "_get_sheet", side_effect=AssertionError("Sheets touched")), \
                 patch.object(pipeline, "_mark_stale", side_effect=AssertionError("history changed")):
                output = io.StringIO()
                with redirect_stdout(output):
                    pipeline.run_campaign(folder)
            self.assertIn("PIPELINE_RELEASE_GATE_BLOCKED", output.getvalue())

    def test_synthetic_google_links_never_pass_release_gate(self):
        for kind, url in (
            ("file", "https://drive.google.com/file/d/local-Q70_KGS022_MarketPayout/view"),
            ("document", "https://docs.google.com/document/d/local-KGS024_QA_Report/edit"),
        ):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "Synthetic local-"):
                a.google_file_id(url, kind)

    def test_real_looking_id_still_requires_actual_provider_readback(self):
        # Parsing is not a substitute for independent Drive/Docs readback.
        file_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz12345"
        self.assertEqual(a.google_file_id(f"https://drive.google.com/file/d/{file_id}/view"), file_id)

    def test_historical_stale_manifest_cannot_rewrite_status(self):
        ws = MagicMock()
        output = io.StringIO()
        with redirect_stdout(output):
            pipeline._mark_stale(ws, ["Q-01", "Q-02"])
        ws.assert_not_called()
        self.assertIn("PIPELINE_STALE_BLOCKED", output.getvalue())

    def test_failed_drive_upload_does_not_forge_local_url(self):
        drive = MagicMock()
        drive.files.return_value.create.side_effect = PermissionError("403")
        http = MagicMock()
        http.MediaFileUpload.return_value = object()
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "example.png"
            file.write_bytes(b"test")
            with self.assertRaisesRegex(RuntimeError, "PIPELINE_BLOCKED"):
                pipeline._upload_file(drive, http, file, "unwritable-parent")


if __name__ == "__main__":
    unittest.main()
