"""Ollama adapter: versioned prompt, bounded generation and strict output contract."""
import json
import os
from pathlib import Path
import urllib.request

PROMPT_PATH = Path(__file__).parent / "prompts" / "answer-v1.txt"
OPTIONS = {"temperature": 0, "seed": 42, "num_predict": 512, "num_ctx": 4096}


class InferenceError(ValueError):
    def __init__(self, code, usage=None):
        super().__init__(code)
        self.code = code
        self.usage = usage


def infer(question, sources):
    model = os.environ.get("OLLAMA_MODEL", "").strip()
    if not model:
        raise InferenceError("missing_model")
    allowed = {s["id"] for s in sources}
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"answer": {"type": "string"},
                             "citations": {"type": "array", "items": {"type": "string", "enum": sorted(allowed)}},
                             "needs_review": {"type": "boolean"}},
              "required": ["answer", "citations", "needs_review"]}
    payload = {"model": model, "stream": False, "think": False, "format": schema,
               "options": OPTIONS, "messages": [
                   {"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
                   {"role": "user", "content": json.dumps({"question": question, "sources": sources}, ensure_ascii=False)}]}
    request = urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat"),
                                     data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    if not isinstance(result, dict):
        raise InferenceError("invalid_provider_response")
    usage = {"model": model, "input_tokens": result.get("prompt_eval_count"), "output_tokens": result.get("eval_count"),
             "provider_duration_ns": result.get("total_duration"), "load_duration_ns": result.get("load_duration")}
    if result.get("done_reason") == "length":
        raise InferenceError("truncated_output", usage)
    try:
        output = json.loads(result["message"]["content"])
    except (ValueError, KeyError, TypeError):
        raise InferenceError("invalid_json", usage) from None
    if not isinstance(output, dict) or set(output) != {"answer", "citations", "needs_review"}:
        raise InferenceError("invalid_contract", usage)
    if not isinstance(output["answer"], str) or not 1 <= len(output["answer"].strip()) <= 8000:
        raise InferenceError("invalid_answer", usage)
    citations = output["citations"]
    if not isinstance(citations, list) or not all(isinstance(c, str) and c in allowed for c in citations):
        raise InferenceError("invalid_citations", usage)
    if len(citations) != len(set(citations)):
        raise InferenceError("duplicate_citations", usage)
    if type(output["needs_review"]) is not bool or (not output["needs_review"] and not citations):
        raise InferenceError("unsupported_answer", usage)
    return output, usage
