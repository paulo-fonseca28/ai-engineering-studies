import hashlib
import math
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path
from uuid import uuid4

from .llm import InferenceError, infer

DATA = Path(__file__).resolve().parents[1] / "data" / "policies"
STOPWORDS = set("a o as os um uma de da do das dos em no na e ou que para por com meu minha quero como qual posso".split())


def tokens(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return [t for t in re.findall(r"[a-z0-9]+", text) if t not in STOPWORDS]


def ingest(directory=DATA):
    chunks = []
    for path in sorted(directory.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        version = hashlib.sha256(raw.encode()).hexdigest()
        title = raw.splitlines()[0].lstrip("# ") if raw else path.stem
        for index, paragraph in enumerate(re.split(r"\n\s*\n", raw)):
            paragraph = re.sub(r"^#{1,6}\s+.*$", "", paragraph, flags=re.MULTILINE).strip()
            for offset in range(0, len(paragraph), 900):
                text = paragraph[offset:offset + 900].strip()
                if text:
                    chunks.append(dict(id=f"{path.stem}:{version[:12]}:{index}:{offset}",
                                       document=path.name, version=version, title=title, text=text))
    return chunks


def retrieve(question, chunks, k=3):
    query = set(tokens(question))
    counts = [Counter(tokens(c["text"])) for c in chunks]
    ranked = []
    for chunk, count in zip(chunks, counts):
        score = sum((1 + math.log(count[t])) * (1 + math.log((len(chunks) + 1) / (1 + sum(t in c for c in counts)))) for t in query if count[t]) / math.sqrt(max(1, sum(count.values())))
        if score > 0:
            ranked.append(dict(chunk, score=round(score, 6)))
    return sorted(ranked, key=lambda c: (-c["score"], c["id"]))[:k]


def answer(question, mode="demo", directory=DATA):
    if mode not in {"demo", "ollama"}:
        raise ValueError("Modo inválido")
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 4000:
        raise ValueError("Pergunta deve ter entre 1 e 4000 caracteres")
    started = time.perf_counter()
    chunks = ingest(directory)
    sources = retrieve(question, chunks)
    trace = [{"step": "retrieval", "strategy": "lexical", "chunks_indexed": len(chunks), "sources_found": len(sources)}]
    usage = None
    inference_status = "skipped_no_sources"
    result = {"answer": "Não há evidências suficientes. Encaminhe para revisão humana.", "citations": [], "needs_review": True}
    if sources and mode == "demo":
        inference_status = "demo"
        result = {"answer": "Demonstração: trechos recuperados, sem inferência de LLM.\n" + "\n".join(s["text"] for s in sources), "citations": [s["id"] for s in sources], "needs_review": True}
    elif sources:
        try:
            result, usage = infer(question, sources)
        except (ValueError, KeyError, TypeError, OSError) as error:
            inference_status = "failed"
            usage = error.usage if isinstance(error, InferenceError) else None
            result["answer"] = "Não foi possível validar a resposta do modelo. Encaminhe para revisão humana."
            trace.append({"step": "inference", "status": "failed", "error": error.code if isinstance(error, InferenceError) else "provider_error"})
        else:
            inference_status = "completed"
            trace.append({"step": "inference", "status": "completed"})
    return dict(result, inference_status=inference_status, sources=sources, mode=mode, simulated=mode == "demo", usage=usage, trace_id=str(uuid4()), trace=trace, duration_ms=round((time.perf_counter() - started) * 1000, 3))
