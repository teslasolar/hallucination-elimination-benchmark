"""Result analysis — offline deep analysis of benchmark results.
No API calls required. Generates failure taxonomies, winding distributions, LaTeX tables.

Usage:
    python -m konomi.triad.analyze results/claude_opus_judge_222q.json
    python -m konomi.triad.analyze results/gpt52_triad.json
"""
import json, sys, statistics
from collections import defaultdict
from konomi.triad.winding import compute_winding, THRESHOLD


def analyze(results: dict) -> dict:
    """Analyze benchmark results. Accepts either tier1 format or single-model format."""
    # Handle both formats
    if "tier1" in results:
        details = results["tier1"]["details"]
        raw_key, triad_key = "raw_pass", "grounded_pass"
    elif "details" in results:
        details = results["details"]
        raw_key, triad_key = "passed", "passed"
    else:
        return {"error": "Unrecognized result format"}

    n = len(details)
    if n == 0:
        return {"error": "No details found"}

    # Category breakdown
    cats = defaultdict(lambda: {"total": 0, "passed": 0})
    for d in details:
        cat = d["category"]
        cats[cat]["total"] += 1
        if d.get("verdict") == "PASS" or d.get(triad_key):
            cats[cat]["passed"] += 1

    passed = sum(c["passed"] for c in cats.values())

    # Failure taxonomy
    failures = defaultdict(list)
    for d in details:
        is_fail = d.get("verdict") == "FAIL" or not d.get(triad_key, True)
        if is_fail:
            cat = d["category"]
            failures[cat].append(d.get("question", "")[:80])

    # Response lengths
    answers = [d.get("answer", "") or d.get("grounded_answer", "") or "" for d in details]
    lengths = [len(a) for a in answers if a]

    # Winding numbers
    winding_data = {}
    for d in details:
        q = d.get("question", "")
        w, _ = compute_winding(q)
        cat = d["category"]
        if cat not in winding_data:
            winding_data[cat] = []
        winding_data[cat].append(w)

    return {
        "total": n,
        "passed": passed,
        "failed": n - passed,
        "accuracy_pct": round(passed / n * 100, 1),
        "categories": {k: {"total": v["total"], "passed": v["passed"],
                           "pct": round(v["passed"] / v["total"] * 100, 1)}
                       for k, v in cats.items()},
        "failures": {k: {"count": len(v), "samples": v[:3]} for k, v in failures.items()},
        "response_lengths": {
            "mean": round(statistics.mean(lengths)) if lengths else 0,
            "median": round(statistics.median(lengths)) if lengths else 0,
        },
        "winding": {k: {"mean": round(float(statistics.mean(v)), 3),
                         "max": round(float(max(v)), 3)}
                    for k, v in winding_data.items()},
    }


def print_report(analysis: dict):
    """Print formatted analysis report."""
    print(f"\n{'='*70}")
    print(f"BENCHMARK ANALYSIS")
    print(f"{'='*70}")
    print(f"Total: {analysis['total']} | Passed: {analysis['passed']} | "
          f"Accuracy: {analysis['accuracy_pct']}%\n")

    print(f"{'Category':<28} {'n':>4} {'Pass':>6} {'Pct':>8}")
    print("-" * 50)
    for cat, v in sorted(analysis["categories"].items()):
        print(f"  {cat:<26} {v['total']:>4} {v['passed']:>6} {v['pct']:>7.1f}%")

    if analysis["failures"]:
        print(f"\nFailure Taxonomy:")
        for cat, v in sorted(analysis["failures"].items(), key=lambda x: -x[1]["count"]):
            print(f"  {cat}: {v['count']} failures")
            for s in v["samples"]:
                print(f"    - {s}")

    print(f"\nResponse Lengths: mean={analysis['response_lengths']['mean']}, "
          f"median={analysis['response_lengths']['median']}")

    print(f"\nWinding Numbers:")
    for cat, v in sorted(analysis["winding"].items()):
        print(f"  {cat:<28} mean={v['mean']:.3f}  max={v['max']:.3f}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m konomi.triad.analyze <results.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    report = analyze(data)
    print_report(report)


if __name__ == "__main__":
    main()
