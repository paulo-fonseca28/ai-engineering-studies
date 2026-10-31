"""Constrained policy selection. Only application-owned templates and approved quotes are rendered."""
import json
import os
from pathlib import Path
import urllib.request
from .llm import InferenceError

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data/grounding-v3.json"
PROMPT_PATH = Path(__file__).parent / "prompts/select-v1.txt"
OPTIONS = {"temperature": 0, "seed": 42, "num_predict": 128, "num_ctx": 4096}
QUOTE_PREFIX = "Política de demonstração — trecho literal:\n"
CLARIFICATION = "Pode detalhar o problema e o que deseja saber sobre o pedido? É necessária revisão humana."
ABSTENTION = "Não há evidência suficiente para responder a essa solicitação. É necessária revisão humana."


def load_config():
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(config["approved_documents"], dict) or not config["approved_documents"]:
            raise ValueError("Empty approval manifest")
        if type(config["threshold"]) not in (int, float) or not 0 <= config["threshold"] <= 1:
            raise ValueError("Invalid threshold")
        if not isinstance(config["embedding_digest"], str) or not config["embedding_digest"]:
            raise ValueError("Missing model digest")
        return config
    except (OSError, KeyError, ValueError, TypeError) as error:
        raise InferenceError("invalid_grounding_config") from error


def approved_chunks(chunks, config):
    allowed = config["approved_documents"]
    return [c for c in chunks if allowed.get(c["document"]) == c["version"]]


def gate(sources, retrieval_info, config):
    metadata = retrieval_info.get("embedding", {})
    if metadata.get("digest") != config["embedding_digest"] or metadata.get("model") != config["embedding_model"]:
        raise InferenceError("uncalibrated_embedding_model")
    return [source for source in sources if source["score"] >= config["threshold"]]


def render(selection, sources):
    if not isinstance(selection, dict) or set(selection) != {"decision", "source_id"}:
        raise InferenceError("invalid_selection_contract")
    decision, source_id = selection["decision"], selection["source_id"]
    if decision not in ("quote", "clarify", "abstain") or not isinstance(source_id, str):
        raise InferenceError("invalid_selection")
    if decision == "quote":
        selected = next((s for s in sources if s["id"] == source_id), None)
        if selected is None:
            raise InferenceError("unknown_selected_source")
        return {"answer": QUOTE_PREFIX + selected["text"], "citations": [source_id], "needs_review": True, "answer_kind": "policy_quote"}
    if source_id:
        raise InferenceError("unexpected_selected_source")
    return {"answer": CLARIFICATION if decision == "clarify" else ABSTENTION,
            "citations": [], "needs_review": True, "answer_kind": "clarification" if decision == "clarify" else "abstention"}


def select_policy(question, sources):
    model = os.environ.get("OLLAMA_MODEL", "").strip()
    if not model:
        raise InferenceError("missing_model")
    schema = {"type": "object", "additionalProperties": False,
              "properties": {"decision": {"type": "string", "enum": ["quote", "clarify", "abstain"]},
                             "source_id": {"type": "string", "enum": [""] + [s["id"] for s in sources]}},
              "required": ["decision", "source_id"]}
    payload = {"model": model, "stream": False, "think": False, "format": schema, "options": OPTIONS,
               "messages": [{"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
                            {"role": "user", "content": json.dumps({"question": question, "sources": sources}, ensure_ascii=False)}]}
    request = urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat"),
                                     data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    if not isinstance(result, dict):
        raise InferenceError("invalid_provider_response")
    usage = {"model": model, "input_tokens": result.get("prompt_eval_count"), "output_tokens": result.get("eval_count"),
             "provider_duration_ns": result.get("total_duration"), "load_duration_ns": result.get("load_duration")}
    try:
        if result.get("done_reason") == "length":
            raise InferenceError("truncated_selection")
        selected = json.loads(result["message"]["content"])
        response = render(selected, sources)
    except InferenceError as error:
        error.usage = usage
        raise
    except (ValueError, KeyError, TypeError) as error:
        raise InferenceError("invalid_selection_json", usage) from error
    return response, usage
