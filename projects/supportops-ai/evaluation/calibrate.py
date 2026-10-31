"""Choose a rejection threshold from development retrieval results only."""
import argparse
import hashlib
import json
from pathlib import Path

GRID = [0.0, 0.3, 0.4, 0.45, 0.47, 0.5, 0.55, 0.6, 0.7]


def calibrate(report):
    if report.get("split") != "dev":
        raise ValueError("Threshold selection is restricted to development")
    rows = [r for r in report["results"] if r["strategy"] == "semantic" and r["repeat"] == 1]
    positive = [r for r in rows if r["category"] == "answerable"]
    negative = [r for r in rows if r["category"] == "unanswerable"]
    if not positive or not negative:
        raise ValueError("Both answerable and unanswerable cases are required")
    candidates = []
    for threshold in GRID:
        candidates.append({"threshold": threshold,
            "answerable_retained": sum(bool(r["sources"]) and r["sources"][0]["score"] >= threshold for r in positive),
            "unanswerable_rejected": sum(not r["sources"] or r["sources"][0]["score"] < threshold for r in negative)})
    valid = [c for c in candidates if c["unanswerable_rejected"] == len(negative)]
    if not valid:
        raise ValueError("No candidate rejects all development unknowns")
    selected = min(valid, key=lambda c: (-c["answerable_retained"], c["threshold"]))
    return {"protocol": "threshold-v3", "selection_split": "dev", "selection_rule": "Reject all development unanswerable cases, maximize answerable retention, then lowest threshold",
            "answerable_cases": len(positive), "unanswerable_cases": len(negative), "candidates": candidates,
            "selected": selected, "embedding": rows[0]["metadata"]["embedding"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists")
    raw = args.report.read_bytes()
    result = calibrate(json.loads(raw))
    result["source_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["selected"]))


if __name__ == "__main__":
    main()
