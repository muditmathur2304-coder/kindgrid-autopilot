"""Read-only QA Doc classification must fail closed on ambiguous evidence."""
import unittest

from scripts.staged_pair_preflight import classify_qa_doc_verdict


def doc(item="KGS-020", version="KGS-QA-V2", result="HOLD"):
    return f"ITEM ID: {item}\nQA VERSION: {version}\nRESULT: {result}\nEVIDENCE: Review pending.\n"


class StagedQaVerdictTests(unittest.TestCase):
    def test_explicit_hold(self):
        self.assertEqual(classify_qa_doc_verdict(doc(), "KGS-020"), "HOLD")

    def test_explicit_pass_only_with_identity(self):
        self.assertEqual(classify_qa_doc_verdict(doc(result="PASS"), "KGS-020"), "PASS")

    def test_wrong_item_is_not_approval(self):
        self.assertEqual(classify_qa_doc_verdict(doc(item="KGS-021", result="PASS"), "KGS-020"), "UNVERIFIED")

    def test_wrong_version_is_not_approval(self):
        self.assertEqual(classify_qa_doc_verdict(doc(version="KGS-QA-V1", result="PASS"), "KGS-020"), "UNVERIFIED")

    def test_conflicting_results_fail_closed(self):
        self.assertEqual(classify_qa_doc_verdict(doc(result="PASS") + "RESULT: HOLD\n", "KGS-020"), "UNVERIFIED")

    def test_body_mention_of_pass_is_not_result(self):
        text = "ITEM ID: KGS-020\nQA VERSION: KGS-QA-V2\nEVIDENCE: PASS if tests complete\n"
        self.assertEqual(classify_qa_doc_verdict(text, "KGS-020"), "UNVERIFIED")

    def test_result_not_on_its_own_line_fails_closed(self):
        self.assertEqual(classify_qa_doc_verdict(doc(result="PASS, but pending review"), "KGS-020"), "UNVERIFIED")

    def test_missing_qa_version_fails_closed(self):
        self.assertEqual(classify_qa_doc_verdict("ITEM ID: KGS-020\nRESULT: PASS\n", "KGS-020"), "UNVERIFIED")

    def test_markdown_bold_labels_supported(self):
        text = "**ITEM ID**: KGS-020\n**QA VERSION**: KGS-QA-V2\n**RESULT**: HOLD\n"
        self.assertEqual(classify_qa_doc_verdict(text, "KGS-020"), "HOLD")


if __name__ == "__main__":
    unittest.main()
