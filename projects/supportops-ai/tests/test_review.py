import unittest
from evaluation.review import summarize, worksheet


class ReviewTests(unittest.TestCase):
    def test_pending_is_not_a_success(self):
        result = summarize({"reviewer_type": "unassigned", "cases": [{"verdict": "pending", "rationale": ""}]})
        self.assertEqual(result["verdict_counts"], {"pending": 1})
        self.assertFalse(result["independent_human_validation"])

    def test_annotation_requires_rationale(self):
        with self.assertRaises(ValueError):
            summarize({"reviewer_type": "ai_assisted", "cases": [{"verdict": "supported", "rationale": ""}]})

    def test_ai_review_is_not_human_validation(self):
        result = summarize({"reviewer_type": "ai_assisted", "cases": [{"verdict": "unsupported", "rationale": "Contradicts source"}]})
        self.assertFalse(result["independent_human_validation"])

    def test_demo_not_accepted_as_inference(self):
        with self.assertRaises(ValueError):
            worksheet({"mode": "demo"}, "hash")
