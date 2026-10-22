"""Regression tests for the unverified KindGrid auxiliary asset pipeline.

No network requests, publication, uploads, or Dashboard writes are permitted.
These tests protect the temporary fail-closed gate only, not end-to-end QA.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import asset_pipeline


class AssetPipelineFailClosedTests(unittest.TestCase):
    def assert_blocked_without_side_effects(self, manifest=None):
        with tempfile.TemporaryDirectory() as root:
            campaign = Path(root) / "kgs-test"
            campaign.mkdir()
            if manifest is not None:
                (campaign / "manifest.json").write_text(
                    json.dumps(manifest), encoding="utf-8"
                )
                (campaign / "paid.xlsx").write_bytes(b"not-a-real-workbook")
            original_files = {
                p.name: p.read_bytes() for p in campaign.iterdir() if p.is_file()
            }
            with (
                patch.object(asset_pipeline, "_build_credentials", side_effect=AssertionError("credentials requested")) as auth,
                patch.object(asset_pipeline, "_get_or_create_folder", side_effect=AssertionError("Drive folder requested")) as folder,
                patch.object(asset_pipeline, "_upload_file", side_effect=AssertionError("Drive upload requested")) as upload,
                patch.object(asset_pipeline, "_get_sheet", side_effect=AssertionError("Dashboard requested")) as sheet,
                patch.object(asset_pipeline, "_append_row", side_effect=AssertionError("Dashboard write requested")) as append,
                patch.object(asset_pipeline, "_mark_stale", side_effect=AssertionError("Existing queue mutation requested")) as stale,
            ):
                with self.assertRaisesRegex(RuntimeError, "PIPELINE_BLOCKED: independent KGS-QA-V2 verification"):
                    asset_pipeline.run(campaign)
                for mock in (auth, folder, upload, sheet, append, stale):
                    mock.assert_not_called()
            final_files = {
                p.name: p.read_bytes() for p in campaign.iterdir() if p.is_file()
            }
            self.assertEqual(original_files, final_files)
            self.assertFalse((campaign / "drive_links.json").exists())

    def test_blocks_even_without_manifest_before_any_network_access(self):
        self.assert_blocked_without_side_effects()

    def test_blocks_forged_pass_ready_and_stale_mutations(self):
        self.assert_blocked_without_side_effects({
            "campaign": "kgs-test", "pair_id": "PAIR-TEST",
            "products": {
                "paid": {"product_id": "KGS-TEST", "qa_outcome": "PASS", "upload_status": "PAIR_READY", "pdf_file": "paid.xlsx"},
                "free": {"product_id": "KGS-FREE", "price_usd": 0, "qa_outcome": "PASS"},
            },
            "pinterest_pins": [{"queue_id": "Q-TEST", "status": "READY", "image_file": "paid.xlsx"}],
            "stale_q_ids": ["Q-55", "Q-56"],
        })

    def test_blocks_empty_campaign_without_fabricating_qa(self):
        self.assert_blocked_without_side_effects({"campaign": "kgs-test", "products": {}, "pinterest_pins": []})


if __name__ == "__main__":
    unittest.main()
