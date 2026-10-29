import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from supportops.core import answer, ingest, infer


class PipelineTests(unittest.TestCase):
    def test_demo_sources(self):
        result = answer("Qual a política de reembolso?")
        self.assertTrue(result["simulated"])
        self.assertTrue(result["needs_review"])
        self.assertIn("refund.md", [s["document"] for s in result["sources"]])
        self.assertTrue(set(result["citations"]) <= {s["id"] for s in result["sources"]})
        self.assertIsNone(result["usage"])

    def test_unknown_question(self):
        result = answer("astronomia galáxia")
        self.assertEqual(result["citations"], [])
        self.assertTrue(result["needs_review"])

    def test_empty_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(answer("reembolso", directory=Path(directory))["needs_review"])

    def test_version_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.md"
            path.write_text("# Política\n\nReembolso em análise.")
            before = ingest(Path(directory))
            path.write_text("# Política\n\nReembolso requer revisão.")
            self.assertNotEqual(before[0]["version"], ingest(Path(directory))[0]["version"])

    def test_provider_failure(self):
        with patch("supportops.core.infer", side_effect=OSError("offline")):
            result = answer("reembolso", mode="ollama")
        self.assertTrue(result["needs_review"])
        self.assertEqual(result["trace"][-1]["status"], "failed")

    def test_invalid_input(self):
        for question in ["", "   ", "x" * 4001]:
            with self.assertRaises(ValueError):
                answer(question)

    @patch.dict("os.environ", {"OLLAMA_MODEL": "test-model"})
    def test_fabricated_citation_rejected(self):
        payload = {"message": {"content": json.dumps({"answer": "Aprovado", "citations": ["inventada"], "needs_review": False})}}
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())):
            with self.assertRaises(ValueError):
                infer("reembolso", [{"id": "real"}])

    @patch.dict("os.environ", {"OLLAMA_MODEL": "test-model"})
    def test_valid_model_contract(self):
        payload = {"message": {"content": json.dumps({"answer": "Revisão necessária", "citations": ["real"], "needs_review": True})}, "eval_count": 10}
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())):
            result, usage = infer("reembolso", [{"id": "real"}])
        self.assertEqual(result["citations"], ["real"])
        self.assertEqual(usage["output_tokens"], 10)


if __name__ == "__main__":
    unittest.main()
