import unittest
from evaluation.run import ROOT, load_cases, percentile95, recall, summarize


class EvaluationTests(unittest.TestCase):
    def test_recall_uses_all_relevant_documents(self):
        self.assertEqual(recall(["a", "b"], ["a", "a", "c"]), .5)
        self.assertIsNone(recall([], ["a"]))

    def test_nearest_rank_p95(self):
        self.assertEqual(percentile95(list(range(1, 21))), 19)
        self.assertIsNone(percentile95([]))

    def test_splits_have_unique_ids_and_questions(self):
        dev = load_cases(ROOT / "evaluation/dev.jsonl")
        test = load_cases(ROOT / "evaluation/test.jsonl")
        self.assertFalse({c["id"] for c in dev} & {c["id"] for c in test})
        self.assertFalse({c["question"] for c in dev} & {c["question"] for c in test})
        for cases in (dev, test):
            self.assertEqual({c["category"] for c in cases}, {"answerable", "ambiguous", "unanswerable", "adversarial"})

    def row(self, status, category="answerable"):
        return {"category": category, "recall_at_1": 1, "recall_at_3": 1,
                "citation_document_recall": 0, "response": {"inference_status": status,
                "duration_ms": 10, "sources": [], "needs_review": True, "usage": None}}

    def test_failures_stay_in_inference_denominator(self):
        summary = summarize([self.row("completed"), self.row("failed"), self.row("skipped_no_sources")], "ollama")
        self.assertEqual(summary["llm"]["attempted"], 2)
        self.assertEqual(summary["llm"]["contract_acceptance_rate"], .5)
        self.assertEqual(summary["llm"]["input_tokens_missing_calls"], 2)

    def test_demo_does_not_produce_llm_metrics(self):
        self.assertIsNone(summarize([self.row("demo")], "demo")["llm"])
