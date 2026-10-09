import importlib.util
import json
import pathlib
import unittest
from unittest.mock import patch
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("autopilot", ROOT / "src/autopilot.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
sample = json.loads((ROOT / "sample_queue.json").read_text())


class PreflightTests(unittest.TestCase):
    def test_new_gumroad_004_is_ready(self):
        ready_new = dict(sample["gumroad"], **{"Product ID": "KGS-004", "Unique Slug": "new-budget-reflection-kit"})
        g = a.validate_gumroad(ready_new)
        self.assertEqual(g["slug"], "new-budget-reflection-kit")
        self.assertEqual(g["price"], "5")
        self.assertEqual(g["pdf"], "1rHxf3w8vAhHvE9pkJnucnBBxeiU9qEKc")

    def test_gumroad_create_uses_explicit_draft_flag_and_edit_url(self):
        """Regression: current Gumroad CLI publishes by default without --draft."""
        calls = []
        def fake_cli(args):
            calls.append(args)
            if args[:2] == ["products", "list"]:
                return {"products": []}
            if args[:2] == ["products", "create"]:
                return {"product": {"id": "newdraft123"}}
            if args[:2] == ["products", "view"]:
                return {"product": {"id": "newdraft123", "published": False,
                        "name": "My New Product", "files": [{"id": "pdf"}],
                        "covers": [{"id": "cover"}]}}
            raise AssertionError(f"Unexpected CLI command: {args}")
        class FakeStore:
            def get_bytes(self, file_id, mime_type):
                return b"stub"
            def get_doc_text(self, doc_id):
                return "BEGIN_GUMROAD_DESCRIPTION\n" + "A printable workbook. " * 20 + "\nEND_GUMROAD_DESCRIPTION"
        config = {"pdf": "pdf-id", "cover": "cover-id", "listing_doc": "listing-id",
                  "title": "My New Product", "slug": "new-product", "price": "5"}
        with patch.object(a, "gumroad_cli", side_effect=fake_cli), \
             patch.object(a, "validate_pdf", return_value=8), \
             patch.object(a, "validate_image", return_value=(1000,1500)):
            product_id, url = a.gumroad_create_draft(FakeStore(), config)
        self.assertEqual(product_id, "newdraft123")
        self.assertEqual(url, "https://gumroad.com/products/newdraft123/edit")
        create = next(cmd for cmd in calls if cmd[:2] == ["products", "create"])
        self.assertIn("--draft", create)
        self.assertIn("--all", next(cmd for cmd in calls if cmd[:2] == ["products", "list"]))

    def test_existing_gumroad_products_never_reuploaded(self):
        for protected in ("KGS-001", "KGS-002", "KGS-003"):
            g = dict(sample["gumroad"], **{"Product ID": protected})
            with self.subTest(protected=protected), self.assertRaises(ValueError):
                a.validate_gumroad(g)
        g = dict(sample["gumroad"], **{"Product ID": "KGS-004", "Unique Slug": "ultimate-budget-planner"})
        with self.assertRaises(ValueError):
            a.validate_gumroad(g)

    def test_protected_test_slug_is_rejected(self):
        g = dict(sample["gumroad"], **{"Product ID": "KGS-004", "Unique Slug": "kindgrid-autopilot-upload-test-20261009"})
        with self.assertRaises(ValueError):
            a.validate_gumroad(g)

    def test_bad_drive_links_rejected(self):
        g = dict(sample["gumroad"], **{"Product ID": "KGS-004", "Unique Slug": "new-budget-worksheet", "PDF Drive Link": "https://example.com/file.pdf"})
        with self.assertRaises(ValueError):
            a.validate_gumroad(g)

    def test_pin_2026_oct_12_correct_utc(self):
        self.assertEqual(a.pin_due_at(sample["pinterest"][0]).isoformat(),
                         "2026-10-12T12:14:00+00:00")

    def test_dst_mismatch_blocks_pin(self):
        pin = dict(sample["pinterest"][0], **{"US Scheduled Time": "08:14 EST / 17:44 IST"})
        with self.assertRaisesRegex(ValueError, "EDT/EST"):
            a.pin_due_at(pin)

    def test_pinterest_destination_is_restricted(self):
        for url in ["http://kindgridstudio.gumroad.com/l/test", "https://evil.example/l/test",
                    "https://kindgridstudio.gumroad.com", "https://kindgridstudio.gumroad.com/l/test?redirect=evil"]:
            with self.assertRaises(ValueError):
                a.validate_destination(url)

    def test_pin_accepts_only_ready_verified_within_window(self):
        now = datetime(2026, 10, 10, tzinfo=timezone.utc)
        pin = a.validate_pin(sample["pinterest"][0], now, 72)
        self.assertEqual(pin["id"], "Q-01")
        not_qa = dict(sample["pinterest"][0], **{"QA Verified (YES/NO)": "PENDING_EXTRACT"})
        with self.assertRaises(ValueError):
            a.validate_pin(not_qa, now, 72)
        already_scheduled = dict(sample["pinterest"][0], **{"Batch ID": "post_123"})
        with self.assertRaises(ValueError):
            a.validate_pin(already_scheduled, now, 72)

    def test_pin_outside_lookahead_is_not_eligible_yet(self):
        now = datetime(2026, 10, 9, 0, 0, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, "outside rolling queue"):
            a.validate_pin(sample["pinterest"][0], now, 72)

    def test_explicit_listing_markers(self):
        text = "BEGIN_GUMROAD_SUMMARY\nShort summary\nEND_GUMROAD_SUMMARY\nBEGIN_GUMROAD_DESCRIPTION\n" + ("An original, useful paragraph. " * 14) + "\nEND_GUMROAD_DESCRIPTION"
        summary, description = a.get_listing_copy(text)
        self.assertEqual(summary, "Short summary")
        self.assertIn("original", description)

    def test_unsupported_refund_claim_requires_gemini_review(self):
        text = "BEGIN_GUMROAD_DESCRIPTION\n" + ("A printable planner. " * 18) + " All sales of digital downloads are final.\nEND_GUMROAD_DESCRIPTION"
        with self.assertRaisesRegex(ValueError, "all sales final"):
            a.get_listing_copy(text)


    def test_existing_uncertain_pin_blocks_all_future_scheduled_pins(self):
        class FakeStore:
            def get_rows(self, sheet_name):
                if sheet_name == "Gumroad Upload Queue":
                    return []
                return [
                    {"Queue ID": "Q-77", "Status": "LINK_REVIEW"},
                    {"Queue ID": "Q-78", "Status": "READY",
                     "QA Verified (YES/NO)": "YES"},
                ]
        env = {"GOOGLE_SERVICE_ACCOUNT_JSON_B64": "test-placeholder",
               "LIVE_MODE": "true", "PIN_AUTOSCHEDULE": "true",
               "GUMROAD_CREATE_DRAFTS": "false",
               "GUMROAD_AUTOPUBLISH": "false",
               "DISPATCH_DRY_RUN": "false"}
        with patch.dict(a.os.environ, env), \
             patch.object(a, "GoogleStore", return_value=FakeStore()), \
             patch.object(a, "monitor_existing_pins", return_value=[]), \
             patch.object(a, "process_pins") as process_pins:
            self.assertEqual(a.main(), 0)
            process_pins.assert_not_called()

    def test_buffer_success_without_id_never_marked_scheduled(self):
        record = sample["pinterest"][0]
        class FakeStore:
            def __init__(self):
                self.updates = []
            def patch(self, sheet_name, row, fields):
                self.updates.append(fields)
            def get_bytes(self, file_id, media_type):
                return b"test-image"
        class FakeBuffer:
            def boards(self):
                return {record["Target Board"]: "board123"}
            def scheduled(self):
                return 0
            def create(self, pin, image_url, board_id):
                return {"metadata": {"url": pin["destination"]}}
        store = FakeStore()
        with patch.dict(a.os.environ, {"LIVE_MODE": "true", "PIN_AUTOSCHEDULE": "true"}), \
             patch.object(a, "BufferClient", return_value=FakeBuffer()), \
             patch.object(a, "validate_image", return_value=(1000, 1500)), \
             patch.object(a, "cloudinary_upload", return_value="https://res.cloudinary.com/sample/image"):
            messages = a.process_pins(store, [record], datetime(2026, 10, 10, tzinfo=timezone.utc))
        self.assertTrue(any("LINK_REVIEW" in m for m in messages))
        self.assertEqual(store.updates[-1]["Status"], "LINK_REVIEW")
        self.assertFalse(any(u["Status"] == "SCHEDULED_BUFFER" for u in store.updates))

    def test_scheduled_workflow_forbids_gumroad_publication_and_manual_live(self):
        workflow = (ROOT / ".github/workflows/publisher.yml").read_text()
        self.assertIn("GUMROAD_AUTOPUBLISH: 'false'", workflow)
        self.assertIn("github.event_name == 'schedule'", workflow)
        self.assertIn("AUTOPILOT_PAUSED", workflow)
        self.assertIn("AUTOPILOT_LIVE_ENABLED == 'true'", workflow)
        self.assertIn("needs_cli == 'true'", workflow)


if __name__ == "__main__":
    unittest.main()
