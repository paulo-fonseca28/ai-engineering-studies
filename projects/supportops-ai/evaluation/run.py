"""Reproducible baseline evaluation. Run from the project directory."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
from urllib.parse import urlsplit, urlunsplit
import urllib.request

from supportops.core import DATA, answer
from supportops.llm import OPTIONS

ROOT = Path(__file__).resolve().parents[1]


def load_cases(path):
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not cases:
        raise ValueError("Empty dataset")
    ids, questions = set(), set()
    documents = {p.name for p in DATA.glob("*.md")}
    for case in cases:
        if case["id"] in ids or case["question"].strip().casefold() in questions:
            raise ValueError("Duplicate case")
        ids.add(case["id"])
        questions.add(case["question"].strip().casefold())
        if case["category"] not in {"answerable", "ambiguous", "unanswerable", "adversarial"}:
            raise ValueError("Unknown category")
        expected = case["expected_documents"]
        if not isinstance(expected, list) or not set(expected) <= documents or len(expected) != len(set(expected)):
            raise ValueError("Unknown or duplicated reference document")
        if case["category"] == "answerable" and not expected:
            raise ValueError("Answerable case without reference")
    return cases


def recall(expected, retrieved):
    return len(set(expected) & set(retrieved)) / len(set(expected)) if expected else None


def mean(values):
    values = [value for value in values if value is not None]
    return statistics.mean(values) if values else None


def percentile95(values):
    return sorted(values)[math.ceil(.95 * len(values)) - 1] if values else None


def provider_metadata():
    url = urlsplit(os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat"))
    base = urlunsplit((url.scheme, url.netloc, "", "", ""))
    def get(path):
        with urllib.request.urlopen(base + path, timeout=10) as response:
            return json.load(response)
    model = os.environ.get("OLLAMA_MODEL", "").strip()
    tags = get("/api/tags")
    entry = next((item for item in tags["models"] if model in (item["name"], item.get("model"))), None)
    if not entry:
        raise ValueError("OLLAMA_MODEL must name an installed model exactly")
    return {"version": get("/api/version")["version"], "model": model, "digest": entry["digest"],
            "details": entry.get("details"), "options": OPTIONS, "think": False}


def fingerprint():
    paths = list((ROOT / "supportops").rglob("*.py")) + list((ROOT / "supportops/prompts").glob("*.txt"))
    paths += list(DATA.glob("*.md")) + list((ROOT / "evaluation").glob("*.jsonl"))
    paths += list((ROOT / "evaluation").glob("*.py")) + [ROOT / "requirements.txt"]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def summarize(rows, mode):
    answerable = [r for r in rows if r["category"] == "answerable"]
    unknown = [r for r in rows if r["category"] == "unanswerable"]
    required = [r for r in rows if r["category"] != "answerable"]
    attempted = [r for r in rows if r["response"]["inference_status"] in {"completed", "failed"}]
    latencies = [r["response"]["duration_ms"] for r in rows]
    summary = {"executions": len(rows), "recall_at_1": mean([r["recall_at_1"] for r in answerable]),
               "recall_at_3": mean([r["recall_at_3"] for r in answerable]),
               "unanswerable_retrieval_rate": mean([bool(r["response"]["sources"]) for r in unknown]),
               "latency_ms_median": statistics.median(latencies) if latencies else None,
               "latency_ms_p95": percentile95(latencies), "llm": None}
    if mode == "ollama":
        summary["llm"] = {"attempted": len(attempted),
                          "completed": sum(r["response"]["inference_status"] == "completed" for r in attempted),
                          "contract_acceptance_rate": mean([r["response"]["inference_status"] == "completed" for r in attempted]),
                          "required_review_rate": mean([r["response"]["needs_review"] for r in required]),
                          "citation_document_recall": mean([r["citation_document_recall"] for r in answerable]),
                          "semantic_correctness": None, "task_success": None, "cost_usd": None}
        for key in ("input_tokens", "output_tokens"):
            values = [(r["response"].get("usage") or {}).get(key) for r in attempted]
            summary["llm"][key + "_observed"] = sum(v for v in values if isinstance(v, int))
            summary["llm"][key + "_missing_calls"] = sum(v is None for v in values)
    return summary


def markdown(report):
    s = report["summary"]
    lines = [f"# Evaluation {report['split']} / {report['mode']} / {report.get('strategy', 'lexical')}", "", f"Executado em {report['created_at']}. Casos: {report['cases']}; repetições: {report['repeats']}.", "",
             "| Métrica | Valor |", "| --- | --- |"]
    for key, value in s.items():
        if key != "llm":
            lines.append(f"| {key} | {value} |")
    if s["llm"]:
        for key, value in s["llm"].items():
            lines.append(f"| llm.{key} | {value} |")
    lines += ["", "Valores nulos não foram medidos. Citações por ID não comprovam fidelidade semântica. Demonstração não mede qualidade de LLM.", "",
              "## Falhas de recuperação (primeira repetição)", ""]
    failures = [r for r in report["results"] if r["repeat"] == 1 and r["category"] == "answerable" and r["recall_at_3"] < 1]
    lines += [f"- {r['id']}: {r['question']} (Recall@3={r['recall_at_3']})" for r in failures] or ["Nenhuma neste conjunto pequeno."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--strategy", choices=["lexical", "semantic", "hybrid"], default="lexical")
    parser.add_argument("--mode", choices=["demo", "ollama"], default="demo")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    if args.output.exists() or args.output.with_suffix(".md").exists():
        parser.error("Choose a new report filename; existing experiments are immutable")
    datasets = {split: load_cases(ROOT / "evaluation" / f"{split}.jsonl") for split in ("dev", "test")}
    if {c["question"].strip().casefold() for c in datasets["dev"]} & {c["question"].strip().casefold() for c in datasets["test"]}:
        raise ValueError("Overlapping questions across splits")
    provider = provider_metadata() if args.mode == "ollama" else None
    cases = datasets[args.split]
    rows = []
    for repeat in range(1, args.repeats + 1):
        for case in cases:
            result = answer(case["question"], mode=args.mode, strategy=args.strategy)
            ranked = result["sources"]
            cited_docs = [s["document"] for s in result["sources"] if s["id"] in result["citations"]]
            rows.append(dict(case, repeat=repeat, response=result,
                             recall_at_1=recall(case["expected_documents"], [s["document"] for s in ranked[:1]]),
                             recall_at_3=recall(case["expected_documents"], [s["document"] for s in ranked[:3]]),
                             citation_document_recall=recall(case["expected_documents"], cited_docs)))
            print(f"{repeat}/{args.repeats} {case['id']} {result['inference_status']}", flush=True)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    report = {"protocol": "retrieval-v2", "strategy": args.strategy, "created_at": datetime.now(timezone.utc).isoformat(),
              "split": args.split, "mode": args.mode, "cases": len(cases), "repeats": args.repeats,
              "environment": {"python": platform.python_version(), "os": platform.system(), "kernel": platform.release(), "architecture": platform.machine()},
              "git_revision": revision.stdout.strip(), "working_tree_dirty": bool(dirty.stdout.strip()),
              "sha256": fingerprint(), "provider": provider, "summary": summarize(rows, args.mode), "results": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if any(row["response"]["inference_status"] == "skipped_retrieval_error" for row in rows):
        raise SystemExit("Retrieval failure; report saved and experiment invalid")
    if args.mode == "ollama" and not report["summary"]["llm"]["completed"]:
        raise SystemExit("No successful inference; report saved with failures")


if __name__ == "__main__":
    main()
