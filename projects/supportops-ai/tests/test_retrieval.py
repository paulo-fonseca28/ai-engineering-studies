import io
import json
import unittest
from unittest.mock import patch
from supportops.core import answer
from supportops.retrieval import RetrievalError, dense, document_vectors, embed, fuse, normalize, search


def chunk(key):
    return {"id": key, "title": key, "text": key, "document": key + ".md", "version": "v"}


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        document_vectors.cache_clear()

    def test_normalization(self):
        self.assertEqual(normalize([3, 4]), (.6, .8))
        for vector in [[], [0, 0], [float("nan")], [float("inf")], [True], ["1"]]:
            with self.assertRaises(RetrievalError):
                normalize(vector)

    def test_provider_batch_shape(self):
        for payload in [{"embeddings": []}, {"embeddings": [[1], [1, 2]]}, []]:
            with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())):
                with self.assertRaises(RetrievalError):
                    embed(["one", "two"], "model", "http://localhost/api/embed")

    def test_dense_cosine_ranking(self):
        with patch("supportops.retrieval.document_vectors", return_value=((1., 0.), (0., 1.))), patch("supportops.retrieval.embed", return_value=((0., 1.),)):
            result = dense("query", [chunk("a"), chunk("b")], {"model": "m", "digest": "v"})
        self.assertEqual([c["id"] for c in result], ["b", "a"])
        self.assertEqual(result[0]["score"], 1)

    def test_query_dimension_mismatch(self):
        with patch("supportops.retrieval.document_vectors", return_value=((1., 0.),)), patch("supportops.retrieval.embed", return_value=((1.,),)):
            with self.assertRaises(RetrievalError):
                dense("query", [chunk("a")], {"model": "m", "digest": "v"})

    def test_cache_invalidates_on_content_and_digest(self):
        with patch("supportops.retrieval.embed", return_value=((1.,),)) as mock:
            document_vectors(("a",), "m", "v1", "url")
            document_vectors(("a",), "m", "v1", "url")
            document_vectors(("b",), "m", "v1", "url")
            document_vectors(("b",), "m", "v2", "url")
        self.assertEqual(mock.call_count, 3)

    def test_rrf_uses_both_rankings(self):
        result = fuse([chunk("a"), chunk("b")], [chunk("b"), chunk("c")])
        self.assertEqual(result[0]["id"], "b")
        self.assertAlmostEqual(result[0]["score"], 1 / 62 + 1 / 61)
        self.assertEqual(len({c["id"] for c in result}), 3)

    def test_lexical_requires_no_embedding_service(self):
        with patch("supportops.retrieval.model_metadata") as mock:
            search("query", [chunk("a")], "lexical")
        mock.assert_not_called()

    def test_missing_provider_does_not_fallback(self):
        with patch("supportops.retrieval.model_metadata", side_effect=OSError("offline")), patch("supportops.core.infer") as infer:
            result = answer("reembolso", mode="ollama", strategy="semantic")
        self.assertEqual(result["inference_status"], "skipped_retrieval_error")
        self.assertEqual(result["sources"], [])
        self.assertTrue(result["needs_review"])
        infer.assert_not_called()

    def test_empty_index_requires_no_network(self):
        with patch("supportops.retrieval.model_metadata") as mock:
            self.assertEqual(search("q", [], "hybrid")[0], [])
        mock.assert_not_called()

    def test_invalid_strategy(self):
        with self.assertRaises(ValueError):
            search("q", [], "typo")
