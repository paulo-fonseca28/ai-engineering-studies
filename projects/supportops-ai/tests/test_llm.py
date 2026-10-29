import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from supportops.core import answer, ingest
from supportops.llm import InferenceError, infer


class InferenceTests(unittest.TestCase):
    def provider(self, output, **extra):
        return io.BytesIO(json.dumps({"message": {"content": json.dumps(output)}, **extra}).encode())

    @patch.dict("os.environ", {"OLLAMA_MODEL": "test-model"})
    def test_rejects_wrong_boolean_and_extra_fields(self):
        for output in [
            {"answer": "Resposta", "citations": ["a"], "needs_review": "false"},
            {"answer": "Resposta", "citations": ["a"], "needs_review": False, "action": "refund"},
            {"answer": "Resposta", "citations": ["a", "a"], "needs_review": False},
            {"answer": "Resposta", "citations": [], "needs_review": False},
        ]:
            with patch("urllib.request.urlopen", return_value=self.provider(output)):
                with self.assertRaises(InferenceError):
                    infer("pergunta", [{"id": "a"}])

    @patch.dict("os.environ", {"OLLAMA_MODEL": "test-model"})
    def test_truncated_response_keeps_token_usage(self):
        output = {"answer": "Parcial", "citations": ["a"], "needs_review": True}
        with patch("urllib.request.urlopen", return_value=self.provider(output, done_reason="length", eval_count=512)):
            result = answer("reembolso", mode="ollama")
        self.assertEqual(result["inference_status"], "failed")
        self.assertEqual(result["usage"]["output_tokens"], 512)
        self.assertEqual(result["trace"][-1]["error"], "truncated_output")

    @patch.dict("os.environ", {"OLLAMA_MODEL": "test-model"})
    def test_non_object_provider_response_fails_closed(self):
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b"[]")):
            result = answer("reembolso", mode="ollama")
        self.assertTrue(result["needs_review"])
        self.assertEqual(result["inference_status"], "failed")

    def test_no_sources_never_calls_provider(self):
        with patch("supportops.core.infer") as mock:
            result = answer("astronomia galáxia", mode="ollama")
        mock.assert_not_called()
        self.assertEqual(result["inference_status"], "skipped_no_sources")

    def test_ingest_preserves_body_without_blank_line(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "policy.md").write_text("# Política\nReembolso exige revisão.")
            self.assertEqual(ingest(Path(directory))[0]["text"], "Reembolso exige revisão.")
