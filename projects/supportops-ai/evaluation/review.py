"""Create a source-grounded review worksheet; never assigns automatic truth labels."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from evaluation.run import ROOT

VERDICTS = {"pending", "supported", "unsupported", "incomplete", "abstained"}


def worksheet(report, source_hash):
    if report["mode"] != "ollama":
        raise ValueError("Only real-inference reports can be reviewed")
    rows = []
    for case in report["results"]:
        if case["repeat"] != 1:
            continue
        rows.append({"id": case["id"], "question": case["question"], "category": case["category"],
                     "expected_documents": case["expected_documents"],
                     "reference_texts": {name: (ROOT / "data/policies" / name).read_text() for name in case["expected_documents"]},
                     "response": case["response"], "verdict": "pending", "rationale": ""})
    return {"protocol": "fidelity-review-v1", "source_report_sha256": source_hash,
            "reviewer_type": "unassigned", "scope": "First repetition, all cases; no random sampling; human validation pending.", "cases": rows}


def summarize(review):
    if review["reviewer_type"] not in {"unassigned", "ai_assisted", "human"}:
        raise ValueError("Unknown reviewer type")
    counts = Counter()
    for row in review["cases"]:
        verdict = row["verdict"]
        if verdict not in VERDICTS:
            raise ValueError("Unknown verdict")
        if verdict != "pending" and (not row["rationale"].strip() or review["reviewer_type"] == "unassigned"):
            raise ValueError("Annotations require a rationale and an identified reviewer type")
        counts[verdict] += 1
    return {"reviewer_type": review["reviewer_type"], "cases": len(review["cases"]), "verdict_counts": dict(counts),
            "independent_human_validation": review["reviewer_type"] == "human"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summarize", type=Path)
    args = parser.parse_args()
    if args.summarize:
        print(json.dumps(summarize(json.loads(args.summarize.read_text())), ensure_ascii=False, indent=2))
        return
    if not args.report or not args.output or args.output.exists():
        parser.error("Supply --report and an unused --output path")
    raw = args.report.read_bytes()
    report = json.loads(raw)
    # Refuse to pair a historical response with silently modified reference policies.
    for name, digest in report["sha256"].items():
        if name.startswith("data/policies/") and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("Reference corpus differs from the evaluated corpus")
    result = worksheet(report, hashlib.sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
