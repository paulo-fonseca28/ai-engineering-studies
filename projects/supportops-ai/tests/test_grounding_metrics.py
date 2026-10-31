import unittest
from evaluation.run import summarize
from supportops.grounding import QUOTE_PREFIX


class GroundingMetricTests(unittest.TestCase):
    def row(self, text, expected_recall=1):
        return {"category": "answerable", "recall_at_1": 1, "recall_at_3": 1,
                "citation_document_recall": expected_recall, "response": {"answer": text,
                "answer_kind": "policy_quote", "inference_status": "completed", "duration_ms": 1,
                "needs_review": True, "usage": None, "citations": ["a"],
                "sources": [{"id": "a", "text": "Política completa."}]}}

    def test_literal_integrity_does_not_imply_correct_document(self):
        result = summarize([self.row(QUOTE_PREFIX + "Política completa.", 0)], "grounded")["grounded"]
        self.assertEqual(result["literal_quote_integrity_rate"], 1)
        self.assertEqual(result["correct_document_quote_rate_answerable"], 0)

    def test_modified_quote_not_counted_as_literal(self):
        result = summarize([self.row("Já realizei reembolso")], "grounded")["grounded"]
        self.assertEqual(result["literal_quote_integrity_rate"], 0)
