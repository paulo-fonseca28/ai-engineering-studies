"""Compare retrieval strategies on development data only, without generation."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time
from evaluation.run import ROOT, fingerprint, load_cases, mean, percentile95, recall
from supportops.core import ingest
from supportops.retrieval import search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1 or args.output.exists() or args.output.with_suffix(".md").exists():
        parser.error("Positive repeats and unused output filenames required")
    cases = load_cases(ROOT / "evaluation/dev.jsonl")
    chunks = ingest()
    rows = []
    for repeat in range(1, args.repeats + 1):
        for case in cases:
            # Rotate execution order; first dense call still includes model/index initialization.
            strategies = ["lexical", "semantic", "hybrid"]
            offset = (repeat - 1) % 3
            for strategy in strategies[offset:] + strategies[:offset]:
                started = time.perf_counter()
                sources, metadata = search(case["question"], chunks, strategy)
                elapsed = (time.perf_counter() - started) * 1000
                rows.append(dict(case, repeat=repeat, strategy=strategy, sources=sources, metadata=metadata,
                                 duration_ms=elapsed, recall_at_1=recall(case["expected_documents"], [s["document"] for s in sources[:1]]),
                                 recall_at_3=recall(case["expected_documents"], [s["document"] for s in sources])))
            print(f"{repeat}/{args.repeats} {case['id']}", flush=True)
    summary = {}
    for strategy in ("lexical", "semantic", "hybrid"):
        selected = [r for r in rows if r["strategy"] == strategy]
        answerable = [r for r in selected if r["category"] == "answerable"]
        unknown = [r for r in selected if r["category"] == "unanswerable"]
        latencies = [r["duration_ms"] for r in selected]
        summary[strategy] = {"recall_at_1": mean([r["recall_at_1"] for r in answerable]),
                             "recall_at_3": mean([r["recall_at_3"] for r in answerable]),
                             "unanswerable_retrieval_rate": mean([bool(r["sources"]) for r in unknown]),
                             "latency_ms_median": statistics.median(latencies), "latency_ms_p95": percentile95(latencies),
                             "latency_ms_max": max(latencies)}
    report = {"protocol": "retrieval-comparison-v2", "created_at": datetime.now(timezone.utc).isoformat(),
              "split": "dev", "cases": len(cases), "repeats": args.repeats,
              "environment": {"python": platform.python_version(), "os": platform.system()},
              "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "sha256": fingerprint(), "summary": summary, "results": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = ["# Retrieval comparison — development", "", "| Strategy | Recall@1 | Recall@3 | Retrieval on unanswerable | Median ms | p95 ms |", "| --- | --- | --- | --- | --- | --- |"]
    for name, s in summary.items():
        lines.append(f"| {name} | {s['recall_at_1']:.3f} | {s['recall_at_3']:.3f} | {s['unanswerable_retrieval_rate']:.3f} | {s['latency_ms_median']:.2f} | {s['latency_ms_p95']:.2f} |")
    lines += ["", "Dense retrieval has no rejection threshold: it always returns top-k when the corpus is nonempty. This is not evidence sufficiency. First dense query includes initialization; document vectors are reused in memory. Query vectors are computed per search. No generation or semantic correctness is measured here."]
    args.output.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
