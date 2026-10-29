"""Regression: invalid synthetic QA evidence cannot crash the scheduled
publisher preflight or authorize a Gumroad release.

All tests are local and make no network, seller, Buffer or Sheets writes.
"""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts import check_pair_queue
from src import paired_release


def invalid_pair():
    common = {
        "Upload Status": "PAIR_READY",
        "Pair ID": "KG-PAIR-024-025",
        "QA Verified (YES/NO)": "YES",
        "QA Version": "KGS-QA-V2",
        "QA Outcome": "PASS",
        "QA Report Drive Link":
            "https://docs.google.com/document/d/local-KGS024_QA_Report/edit",
    }
    paid = dict(common, **{
        "Product ID": "KGS-024", "Pair Role": "PAID",
        "Paired Product ID": "KGS-025",
        "Price USD": "12.95", "Unique Slug": "new-paid-safe-slug",
    })
    free = dict(common, **{
        "Product ID": "KGS-025", "Pair Role": "FREE",
        "Paired Product ID": "KGS-024",
        "Price USD": "0.00", "Unique Slug": "new-free-safe-slug",
    })
    return [paid, free]


class InvalidPairPreflightTests(unittest.TestCase):
    def test_invalid_qa_preflight_exits_cleanly_and_requests_no_cli(self):
        store = MagicMock()
        store.get_rows.return_value = invalid_pair()
        with tempfile.TemporaryDirectory() as folder:
            output_file = Path(folder) / "github-output"
            with patch.dict(os.environ, {
                "LIVE_MODE": "true",
                "PAIRED_RELEASE_ENABLED": "true",
                "GITHUB_OUTPUT": str(output_file),
            }), patch.object(check_pair_queue.a, "GoogleStore", return_value=store):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    check_pair_queue.main()
            self.assertIn("PAIR_PREFLIGHT_BLOCKED", stdout.getvalue())
            self.assertIn("Synthetic local-*", stdout.getvalue())
            self.assertIn("needs_cli=false", stdout.getvalue())
            self.assertEqual(output_file.read_text(), "needs_cli=false\n")
        store.patch.assert_not_called()

    def test_invalid_qa_never_calls_seller_publisher(self):
        with patch.object(paired_release, "launch_pair_once") as publisher:
            result = paired_release.run_ready_pair_cycle(MagicMock(), invalid_pair())
        publisher.assert_not_called()
        self.assertEqual(len(result), 1)
        self.assertIn("PAIR_RELEASE_BLOCKED", result[0])
        self.assertIn("Synthetic local-*", result[0])


if __name__ == "__main__":
    unittest.main()
