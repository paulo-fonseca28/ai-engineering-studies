"""Local dense retrieval and reciprocal-rank fusion; lexical baseline stays in core."""
from functools import lru_cache
import json
import math
import os
from urllib.parse import urlsplit, urlunsplit
import urllib.request

EMBEDDING_MODEL = "qwen3-embedding:0.6b"
QUERY_INSTRUCTION = "Instruct: Given a support question, retrieve the policy passages that answer it.\nQuery: "
RRF_K = 60


class RetrievalError(ValueError):
    pass


def endpoint(path):
    url = urlsplit(os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat"))
    return urlunsplit((url.scheme, url.netloc, path, "", ""))


def model_metadata():
    model = os.environ.get("OLLAMA_EMBEDDING_MODEL", EMBEDDING_MODEL)
    with urllib.request.urlopen(endpoint("/api/tags"), timeout=10) as response:
        tags = json.load(response)
    entry = next((m for m in tags["models"] if m["name"] == model), None)
    if entry is None:
        raise RetrievalError("embedding_model_missing")
    return {"model": model, "digest": entry["digest"], "details": entry.get("details")}


def normalize(vector):
    if not isinstance(vector, list) or not vector or any(type(v) not in (int, float) or not math.isfinite(v) for v in vector):
        raise RetrievalError("invalid_vector")
    norm = math.sqrt(sum(v * v for v in vector))
    if not math.isfinite(norm) or norm == 0:
        raise RetrievalError("zero_or_invalid_norm")
    return tuple(v / norm for v in vector)


def embed(texts, model, url):
    request = urllib.request.Request(url, data=json.dumps({"model": model, "input": list(texts), "truncate": False}).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    vectors = result.get("embeddings") if isinstance(result, dict) else None
    if not isinstance(vectors, list) or len(vectors) != len(texts):
        raise RetrievalError("invalid_embedding_count")
    vectors = tuple(normalize(vector) for vector in vectors)
    if len({len(v) for v in vectors}) > 1:
        raise RetrievalError("inconsistent_dimensions")
    return vectors


@lru_cache(maxsize=8)
def document_vectors(texts, model, digest, url):
    # Digest is part of the cache identity even though the endpoint accepts a model tag.
    return embed(texts, model, url)


def dense(question, chunks, metadata):
    texts = tuple(chunk["title"] + "\n" + chunk["text"] for chunk in chunks)
    url = endpoint("/api/embed")
    vectors = document_vectors(texts, metadata["model"], metadata["digest"], url)
    query = embed((QUERY_INSTRUCTION + question,), metadata["model"], url)[0]
    if any(len(vector) != len(query) for vector in vectors):
        raise RetrievalError("query_dimension_mismatch")
    scores = [dict(chunk, score=sum(a * b for a, b in zip(query, vector))) for chunk, vector in zip(chunks, vectors)]
    return sorted(scores, key=lambda c: (-c["score"], c["id"]))


def fuse(lexical, semantic, k=3):
    scores, chunks = {}, {}
    for ranking in (lexical, semantic):
        seen = set()
        for rank, chunk in enumerate(ranking, 1):
            key = chunk["id"]
            if key in seen:
                continue
            seen.add(key)
            chunks[key] = chunk
            scores[key] = scores.get(key, 0) + 1 / (RRF_K + rank)
    return [dict(chunks[key], score=scores[key]) for key in sorted(scores, key=lambda key: (-scores[key], key))[:k]]


def search(question, chunks, strategy="lexical", k=3):
    from .core import retrieve
    if strategy not in {"lexical", "semantic", "hybrid"}:
        raise ValueError("Unknown retrieval strategy")
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    if not chunks:
        return [], {"strategy": strategy}
    if strategy == "lexical":
        return retrieve(question, chunks, k), {"strategy": strategy}
    try:
        metadata = model_metadata()
        ranked = dense(question, chunks, metadata)
        if strategy == "hybrid":
            ranked = fuse(retrieve(question, chunks, len(chunks)), ranked, k)
        return ranked[:k], {"strategy": strategy, "embedding": metadata, "rrf_k": RRF_K if strategy == "hybrid" else None}
    except RetrievalError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RetrievalError("embedding_provider_error") from error
