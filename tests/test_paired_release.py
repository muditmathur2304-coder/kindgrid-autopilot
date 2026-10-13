"""Unit tests: strict free+paid pairing never authorizes standalone releases."""
import unittest
from datetime import datetime, timezone
from src import autopilot as a
from src import paired_release as pair


def rows():
    common = {
        "QA Verified (YES/NO)": "YES",
        "Upload Status": "PAIR_READY",
        "QA Version": a.QA_VERSION,
        "QA Outcome": "PASS",
        "QA Audited UTC": datetime.now(timezone.utc).isoformat(),
        "QA Report Drive Link": "https://docs.google.com/document/d/1AAaaaBBBbbbCCCccc1234567890abcd/edit",
        "Pair ID": "KG-PAIR-002",
    }
    paid = dict(common, **{
        "Product ID": "KGS-008", "Pair Role": "PAID", "Paired Product ID": "KGS-009",
        "Price USD": "9.00", "Unique Slug": "distinct-premium-kit"})
    free = dict(common, **{
        "Product ID": "KGS-009", "Pair Role": "FREE", "Paired Product ID": "KGS-008",
        "Price USD": "0.00", "Unique Slug": "distinct-free-guide"})
    return paid, free


class PairReleasePolicyTests(unittest.TestCase):
    def test_complete_reciprocal_pair_eligible(self):
        paid, free = rows()
        self.assertEqual(pair.select_ready_pairs([free,paid]), [(paid, free)])

    def test_an_orphan_paid_product_cannot_launch(self):
        paid, _ = rows()
        with self.assertRaisesRegex(ValueError, "exactly two"):
            pair.select_ready_pairs([paid])

    def test_unpaired_regular_ready_does_not_trigger_release(self):
        paid, free = rows()
        paid["Upload Status"] = "READY"
        free["Upload Status"] = "PREPARED"
        self.assertEqual(pair.select_ready_pairs([paid, free]), [])

    def test_an_unpaid_freebie_is_mandatory(self):
        paid, free = rows()
        free["Price USD"] = "2.00"
        with self.assertRaisesRegex(ValueError, "genuinely free"):
            pair.select_ready_pairs([paid, free])

    def test_wrong_partner_and_duplicate_role_fail(self):
        paid, free = rows()
        free["Paired Product ID"] = "KGS-010"
        with self.assertRaisesRegex(ValueError, "reciprocal"):
            pair.select_ready_pairs([paid, free])
        paid, free = rows()
        free["Pair Role"] = "PAID"
        with self.assertRaisesRegex(ValueError, "PAID and FREE"):
            pair.select_ready_pairs([paid, free])

    def test_existing_products_are_never_recreated(self):
        paid, free = rows()
        paid["Product ID"] = "KGS-006"
        free["Paired Product ID"] = "KGS-006"
        with self.assertRaisesRegex(ValueError, "historic product"):
            pair.select_ready_pairs([paid, free])

    def test_qa_failure_blocks_both_even_if_other_is_approved(self):
        paid, free = rows()
        free["QA Outcome"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "QA Outcome"):
            pair.select_ready_pairs([paid, free])

    def test_missing_pair_id_refused(self):
        paid, free = rows()
        free["Pair ID"] = ""
        with self.assertRaisesRegex(ValueError, "Pair ID"):
            pair.select_ready_pairs([paid, free])


    def test_seven_gumroad_listings_daily_count_new_york(self):
        """Confirmed listings are counted in NY business day, not server UTC."""
        day = datetime(2026, 10, 13, 18, 0, tzinfo=timezone.utc)
        records = [
            {"Upload Status": "PUBLISHED", "Last Updated UTC": "2026-10-13T04:14:52Z"},
            {"Upload Status": "PUBLISHED", "Last Updated UTC": "2026-10-13T05:13:27Z"},
            {"Upload Status": "PUBLISHED", "Last Updated UTC": "2026-10-13T20:00:00Z"},
            {"Upload Status": "PUBLISHED", "Last Updated UTC": "2026-10-14T02:59:59Z"},
            {"Upload Status": "REVIEW", "Last Updated UTC": "2026-10-13T15:00:00Z"},
            {"Upload Status": "PUBLISHED", "Last Updated UTC": "2026-10-12T04:10:00Z"},
        ]
        self.assertEqual(pair.published_today_count(records, now=day), 4)

    def test_daily_gumroad_cap_blocks_pair_without_any_upload(self):
        """Even with a valid PAID+FREE pair, 6 earlier listings block 2 more."""
        from unittest.mock import patch
        paid, free = rows()
        records = [paid, free] + [
            {"Upload Status": "PUBLISHED",
             "Last Updated UTC": datetime.now(timezone.utc).isoformat()}
            for _ in range(6)
        ]
        with patch.dict(pair.os.environ, {"GUMROAD_DAILY_LIMIT": "7"}), \
             patch.object(pair, "launch_pair_once") as publisher:
            msgs = pair.run_ready_pair_cycle(object(), records)
        self.assertTrue(any("PAIR_RELEASE_DAILY_CAP" in m for m in msgs))
        publisher.assert_not_called()


if __name__ == "__main__":
    unittest.main()
