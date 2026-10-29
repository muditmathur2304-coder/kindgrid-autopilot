"""Unit tests: KGS-024 / KGS-025 campaign assets and preflight compliance."""
import json
import unittest
from pathlib import Path
from PIL import Image
from src import autopilot as a
from src import paired_release as pair


class KGS024CampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign_dir = Path("assets/kgs-024")
        cls.manifest = json.loads((cls.campaign_dir / "manifest.json").read_text(encoding="utf-8"))

    def test_xlsx_decision_tool_integrity(self):
        blob = (self.campaign_dir / "CraftMargin_Studio_Pricing_System.xlsx").read_bytes()
        pair.validate_tool_xlsx(blob, "KG-PAIR-024-025")

    def test_paid_pdf_page_count_and_geometry(self):
        blob = (self.campaign_dir / "KGS024_CraftMargin_Field_Guide.pdf").read_bytes()
        pages = a.validate_pdf(blob)
        self.assertEqual(pages, 10)

    def test_free_pdf_page_count_and_geometry(self):
        blob = (self.campaign_dir / "KGS025_Booth_Breakeven_Starter.pdf").read_bytes()
        pages = a.validate_pdf(blob)
        self.assertEqual(pages, 5)

    def test_visual_ratio_for_all_pins_and_covers(self):
        images = [
            "KGS024_Cover.png", "KGS025_Cover.png",
            "KGS024_Gallery_1.png", "KGS024_Gallery_2.png", "KGS025_Gallery_1.png",
            "Q70_KGS022_MarketPayout.png", "Q71_KGS023_OneDayCheck.png",
            "Q72_KGS024_CraftMargin.png", "Q73_KGS025_BoothCheck.png"
        ]
        for name in images:
            blob = (self.campaign_dir / name).read_bytes()
            a.validate_image(blob)

    def test_contact_sheet_dimensions(self):
        cs = Image.open(self.campaign_dir / "KGS024_Contact_Sheet.png")
        self.assertGreaterEqual(cs.width, 850)
        self.assertGreaterEqual(cs.height, 500)

    def test_listing_copy_content_and_reciprocal_link(self):
        copy_p = (self.campaign_dir / "KGS024_Listing_Copy.txt").read_text(encoding="utf-8")
        sum_p, desc_p = a.get_listing_copy(copy_p)
        self.assertGreaterEqual(len(sum_p), 60)
        self.assertGreaterEqual(len(desc_p), 650)

        copy_f = (self.campaign_dir / "KGS025_Listing_Copy.txt").read_text(encoding="utf-8")
        sum_f, desc_f = a.get_listing_copy(copy_f)
        self.assertGreaterEqual(len(sum_f), 60)
        self.assertGreaterEqual(len(desc_f), 400)
        self.assertIn("https://kindgridstudio.gumroad.com/l/craftmargin-handmade-pricing-studio", desc_f)

    def test_demand_evidence_criteria(self):
        evidence = (self.campaign_dir / "KGS_PAIR_024_025_Demand_Evidence.txt").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(evidence.strip()), 750)
        for r in ("BUYER PROBLEM", "COMPETITOR", "DIFFERENTIATION", "EVIDENCE", "LIMITATION"):
            self.assertIn(r, evidence.upper())
        self.assertGreaterEqual(evidence.lower().count("https://"), 2)

    def test_qa_reports_and_local_store_resolution(self):
        class MockStore(a.GoogleStore):
            def __init__(self):
                pass
        store = MockStore()
        pdf_bytes = store.get_bytes("local-kgs024-craftmargin-field-guide", "application/pdf")
        self.assertGreaterEqual(len(pdf_bytes), 1000)

        doc_text = store.get_doc_text("local-kgs024-listing-copy")
        self.assertIn("BEGIN_GUMROAD_SUMMARY", doc_text)

        row_paid = {
            "QA Version": "KGS-QA-V2", "QA Outcome": "PASS",
            "QA Report Drive Link": "https://docs.google.com/document/d/local-kgs024-qa-report/edit",
            "QA Audited UTC": "2026-10-29T12:00:00Z"
        }
        a.verify_qa_report(store, row_paid, "KGS-024")

        row_free = {
            "QA Version": "KGS-QA-V2", "QA Outcome": "PASS",
            "QA Report Drive Link": "https://docs.google.com/document/d/local-kgs025-qa-report/edit",
            "QA Audited UTC": "2026-10-29T12:00:00Z"
        }
        a.verify_qa_report(store, row_free, "KGS-025")


if __name__ == "__main__":
    unittest.main()
