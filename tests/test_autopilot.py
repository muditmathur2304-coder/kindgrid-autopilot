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

# Test fixtures simulate the NEW audit gate; historical source records still
# require Gemini's separate retrospective review and must not be auto-approved.
QA_SAMPLE = {
    "QA Version": a.QA_VERSION,
    "QA Report Drive Link": "https://docs.google.com/document/d/1b3dhZzzXs8YzXfsH96T1IkA_3GoaovhvoYULh8eRqZE/edit",
    "QA Audited UTC": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "QA Outcome": "PASS",
}
sample["gumroad"].update(QA_SAMPLE)
for record in sample["pinterest"]:
    record.update(QA_SAMPLE)



class PreflightTests(unittest.TestCase):
    def test_new_gumroad_004_is_ready(self):
        ready_new = dict(sample["gumroad"], **{"Product ID": "KGS-006", "Unique Slug": "new-budget-reflection-kit"})
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
        g = dict(sample["gumroad"], **{"Product ID": "KGS-006", "Unique Slug": "ultimate-budget-planner"})
        with self.assertRaises(ValueError):
            a.validate_gumroad(g)

    def test_protected_test_slug_is_rejected(self):
        g = dict(sample["gumroad"], **{"Product ID": "KGS-006", "Unique Slug": "kindgrid-autopilot-upload-test-20261009"})
        with self.assertRaises(ValueError):
            a.validate_gumroad(g)

    def test_bad_drive_links_rejected(self):
        g = dict(sample["gumroad"], **{"Product ID": "KGS-006", "Unique Slug": "new-budget-worksheet", "PDF Drive Link": "https://example.com/file.pdf"})
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
        # The older sample fixture predates required US-day Time Window.
        # Make it valid here to test missing Buffer ID rather than slot rejection.
        record = dict(sample["pinterest"][0], **{"Time Window": "Morning"})
        class FakeStore:
            def __init__(self):
                self.updates = []
            def get_rows(self, sheet_name):
                return []
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
             patch.object(a, "cloudinary_upload", return_value="https://res.cloudinary.com/sample/image"), \
             patch.object(a, "verify_qa_report", return_value=None), \
             patch.object(a, "verify_public_product_url", return_value=None):
            messages = a.process_pins(store, [record], datetime(2026, 10, 10, tzinfo=timezone.utc))
        self.assertTrue(any("LINK_REVIEW" in m for m in messages))
        self.assertEqual(store.updates[-1]["Status"], "LINK_REVIEW")
        self.assertFalse(any(u["Status"] == "SCHEDULED_BUFFER" for u in store.updates))

    def test_missing_qa_v2_blocks_ready_uploads(self):
        for dataset in ("gumroad", "pinterest"):
            base = sample["gumroad"] if dataset == "gumroad" else sample["pinterest"][0]
            item = dict(base, **{"QA Version": ""})
            with self.subTest(item=dataset), self.assertRaisesRegex(ValueError, "KGS-QA-V2"):
                if dataset == "gumroad":
                    a.validate_gumroad(item)
                else:
                    a.validate_pin(item, datetime(2026, 10, 10, tzinfo=timezone.utc), 72)

    def test_expired_qa_requires_reaudit(self):
        from datetime import timedelta
        old_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        item = dict(sample["gumroad"], **{
            "Product ID": "KGS-006", "Unique Slug": "new-budget-printable",
            "QA Audited UTC": old_time
        })
        with self.assertRaisesRegex(ValueError, "outdated"):
            a.validate_gumroad(item)

    def test_unverified_report_cannot_be_accepted(self):
        class FakeStore:
            def get_doc_text(self, doc):
                return "ITEM ID: KGS-006\nQA VERSION: KGS-QA-V2\nRESULT: PASS\n"
        row = dict(sample["gumroad"], **{
            "Product ID": "KGS-006", "Unique Slug": "budget-journal-v2",
        })
        with self.assertRaisesRegex(ValueError, "substantive"):
            a.verify_qa_report(FakeStore(), row, "KGS-006")

    def test_existing_gumroad_draft_not_autopublished(self):
        class FakeStore:
            def get_rows(self, sheet_name):
                if sheet_name == "Gumroad Upload Queue":
                    return [{"Product ID": "KGS-003", "Upload Status": "DRAFT_VERIFIED",
                             "QA Verified (YES/NO)": "YES"}]
                return []
        with patch.dict(a.os.environ, {
                "GOOGLE_SERVICE_ACCOUNT_JSON_B64": "placeholder",
                "LIVE_MODE": "true", "PIN_AUTOSCHEDULE": "false",
                "GUMROAD_AUTOPUBLISH": "true", "DISPATCH_DRY_RUN": "false"}), \
             patch.object(a, "GoogleStore", return_value=FakeStore()), \
             patch.object(a, "gumroad_cli") as gumroad:
            self.assertEqual(a.main(), 0)
            gumroad.assert_not_called()

    def test_qa_approved_new_product_auto_publishes(self):
        class FakeStore:
            def __init__(self):
                self.updates = []
            def patch(self, sheet_name, row, values):
                self.updates.append(values)
        row = dict(sample["gumroad"], **{
            "Product ID": "KGS-006", "Unique Slug": "unique-original-budget-planner",
            "Upload Status": "READY",
        })
        store = FakeStore()
        def cli(command):
            if command[:2] == ["products", "publish"]:
                return {"success": True}
            if command[:2] == ["products", "view"]:
                return {"product": {"published": True}}
            raise AssertionError("Unexpected Gumroad CLI call")
        with patch.dict(a.os.environ, {"LIVE_MODE": "true",
                 "GUMROAD_CREATE_DRAFTS": "true", "GUMROAD_AUTOPUBLISH": "true"}), \
             patch.object(a, "verify_qa_report", return_value=None), \
             patch.object(a, "gumroad_create_draft", return_value=("new-id", "https://gumroad.com/products/new-id/edit")), \
             patch.object(a, "gumroad_cli", side_effect=cli), \
             patch.object(a, "verify_public_product_url", return_value=None):
            outcome = a.process_gumroad(store, row)
        self.assertIn("auto-published", outcome)
        self.assertEqual(store.updates[-1]["Upload Status"], "PUBLISHED")
        self.assertEqual(store.updates[-1]["Gumroad Live URL"],
                         "https://kindgridstudio.gumroad.com/l/unique-original-budget-planner")

    def test_existing_kgs003_requires_exact_release_ready_and_qa(self):
        row = dict(sample["gumroad"], **{
            "Product ID": "KGS-003",
            "Unique Slug": "debt-payoff-accelerator",
            "Upload Status": "DRAFT_VERIFIED"})
        with self.assertRaisesRegex(ValueError, "Not ready"):
            a.validate_gumroad(row, existing_release=True)
        row["Upload Status"] = "RELEASE_READY"
        config = a.validate_gumroad(row, existing_release=True)
        self.assertEqual(config["product_id"], "KGS-003")
        row["Product ID"] = "KGS-005"
        with self.assertRaisesRegex(ValueError, "KGS-003"):
            a.validate_gumroad(row, existing_release=True)

    def test_pin_daily_cap_blocks_duplicate_slots(self):
        record = dict(sample["pinterest"][0], **{
            "Queue ID": "Q-88", "Status": "READY",
            "Scheduled Date": "2026-10-12",
            "Time Window": "Morning"})
        class FakeStore:
            def __init__(self):
                self.updates = []
            def get_rows(self, sheet_name):
                return [{"Queue ID": "Q-01", "Status": "SCHEDULED_BUFFER",
                         "Scheduled Date": "2026-10-12", "Time Window": "Morning"}]
            def patch(self, sheet_name, row, values):
                self.updates.append(values)
        store = FakeStore()
        with patch.dict(a.os.environ, {"LIVE_MODE": "true", "PIN_AUTOSCHEDULE": "true"}), \
             patch.object(a, "verify_qa_report", return_value=None), \
             patch.object(a, "BufferClient") as client:
            messages = a.process_pins(store, [record], datetime(2026, 10, 10, tzinfo=timezone.utc))
        self.assertTrue(any("time window already" in x for x in messages))
        client.assert_not_called()

    def test_revoked_qa_document_never_passes_even_with_pass_labels(self):
        class ReissuedButRevoked:
            def get_doc_text(self, document_id):
                headings = ["ITEM ID: Q-03", "QA VERSION: KGS-QA-V2",
                            "RESULT: PASS", "EVIDENCE: image opened and arithmetic checked"]
                headings.extend(check + ': PASS' for check in a.QA_FIELDS)
                headings.append("RESULT: FAIL")
                headings.append("QA RELEASE CERTIFICATION: REVOKED")
                return "\n".join(headings) + (" Further original inspection evidence." * 12)
        row = dict(sample["pinterest"][0], **{"Queue ID": "Q-03"})
        with self.assertRaisesRegex(ValueError, "revoked"):
            a.verify_qa_report(ReissuedButRevoked(), row, "Q-03")

    def test_existing_gumroad_draft_cannot_publish_without_safe_file_replacement(self):
        with self.assertRaisesRegex(ValueError, "historical draft release blocked"):
            a.finalize_existing_draft(object(), {"Upload Status": "RELEASE_READY"})

    def test_qa_document_pass_is_item_specific(self):
        class VerifiedReport:
            def get_doc_text(self, document_id):
                fields = [
                    "ITEM ID: KGS-006", "QA VERSION: KGS-QA-V2",
                    "RESULT: PASS", "ASSET_OPEN: PASS", "VISUAL: PASS",
                    "CONTENT: PASS", "COPY: PASS", "LINKS: PASS",
                    "LICENSE: PASS", "FACTS: PASS", "PRODUCT_MATCH: PASS",
                    "EVIDENCE: Independently checked each printable page in full "
                    "and checked the item against its final listing and media. "
                    "Each destination was opened from a public browser, all sums "
                    "were recalculated, and digital product licence claims were "
                    "checked against the actual template deliverables. " * 3,
                ]
                return "\n".join(fields)
        row = dict(sample["gumroad"], **{"Product ID": "KGS-006",
                                             "Unique Slug": "new-debt-planner-v2"})
        a.verify_qa_report(VerifiedReport(), row, "KGS-006")
        with self.assertRaisesRegex(ValueError, "item ID"):
            a.verify_qa_report(VerifiedReport(), row, "KGS-009")

    def test_false_automated_calculation_claim_is_rejected(self):
        description = "Thoughtfully designed, printable worksheet for budgeting. " * 10
        description += " Includes automated rollover compounding."
        text = ("BEGIN_GUMROAD_DESCRIPTION\n" + description
                + "\nEND_GUMROAD_DESCRIPTION")
        with self.assertRaisesRegex(ValueError, "automated calculation"):
            a.get_listing_copy(text)

    def test_uncertain_public_verification_after_upload_is_review_not_retry(self):
        class FakeStore:
            def __init__(self):
                self.events = []
            def patch(self, sheet_name, row, values):
                self.events.append(values)
        row = dict(sample["gumroad"], **{
            "Product ID": "KGS-006", "Unique Slug": "new-spending-reset-v2",
            "Upload Status": "READY"})
        store = FakeStore()
        def cli(args):
            if args[:2] == ["products", "publish"]:
                return {}
            if args[:2] == ["products", "view"]:
                return {"product": {"published": True}}
            raise AssertionError("Unexpected Gumroad command")
        with patch.dict(a.os.environ, {"LIVE_MODE": "true",
                 "GUMROAD_CREATE_DRAFTS": "true", "GUMROAD_AUTOPUBLISH": "true"}), \
             patch.object(a, "verify_qa_report", return_value=None), \
             patch.object(a, "gumroad_create_draft", return_value=("new-id", "https://gumroad.com/products/new-id/edit")), \
             patch.object(a, "gumroad_cli", side_effect=cli), \
             patch.object(a, "verify_public_product_url", side_effect=ValueError("HTTP 403")):
            result = a.process_gumroad(store, row)
        self.assertIn("REVIEW", result)
        self.assertEqual(store.events[-1]["Upload Status"], "REVIEW")

    def test_scheduled_workflow_forbids_gumroad_publication_and_manual_live(self):
        workflow = (ROOT / ".github/workflows/publisher.yml").read_text()
        self.assertIn("GUMROAD_AUTOPUBLISH:", workflow)
        self.assertIn("GUMROAD_CREATE_DRAFTS:", workflow)
        self.assertIn("github.event_name == 'schedule'", workflow)
        self.assertIn("AUTOPILOT_PAUSED", workflow)
        self.assertIn("AUTOPILOT_LIVE_ENABLED == 'true'", workflow)
        self.assertIn("needs_cli == 'true'", workflow)


if __name__ == "__main__":
    unittest.main()
