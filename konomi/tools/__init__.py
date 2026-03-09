"""Entropy gap detector — find sparse sections in domain guides.

Adapted from Thomas P. Frumkin's LookingGlass commit 9fa2488
("nodes reverse-engineered from entropy gaps").

Usage:
    python -m konomi.tools.entropy --guide data/cultural_guide.json
    python -m konomi.tools.entropy --guide data/cultural_guide.json --threshold 0.5
"""
import json, sys, statistics
from pathlib import Path
from collections import defaultdict

CATEGORY_SECTION_MAP = {
    "ANACHRONISM_DETECTION": ["anachronisms_to_avoid", "timeline", "not_yet_built",
                               "not_yet_happened", "technology_notes"],
    "CHARACTER_IDENTITY":    ["notable_people", "characters", "roman_names",
                               "social_structure", "occupations"],
    "CULTURAL_VALUES":       ["customs", "values", "religion", "philosophy",
                               "daily_life", "family", "gender", "ethics"],
    "DOMAIN_SPECIFIC":       ["prices_and_costs", "medicine", "law", "education",
                               "agriculture", "military", "economy", "food"],
    "COMPLEX_SCENARIOS":     ["politics", "legal", "military", "trade",
                               "social_structure", "provinces", "administration"],
}


def extract_leaves(obj, depth=0):
    """Recursively extract all leaf string values."""
    leaves = []
    if isinstance(obj, str):
        leaves.append(obj)
    elif isinstance(obj, list):
        for item in obj:
            leaves.extend(extract_leaves(item, depth + 1))
    elif isinstance(obj, dict):
        for v in obj.values():
            leaves.extend(extract_leaves(v, depth + 1))
    return leaves


def compute_section_entropy(section_data, word_threshold=200,
                            leaf_threshold=20, sparse_threshold=0.65) -> dict:
    """Score a section by its leaf count, depth, word density, and uniqueness."""
    leaves = extract_leaves(section_data)
    word_count = sum(len(l.split()) for l in leaves)
    leaf_count = len(leaves)

    if leaf_count == 0:
        return {"entropy": 1.0, "leaves": 0, "words": 0,
                "unique": 0, "diversity": 0, "sparse": True}

    unique_leaves = len(set(leaves))
    diversity = unique_leaves / leaf_count

    # Normalize: more leaves + more words = lower entropy (denser)
    density = min(1.0, word_count / word_threshold)
    cardinality = min(1.0, leaf_count / leaf_threshold)
    # Penalize homogeneous lists (low diversity)
    entropy = 1.0 - (density * 0.5 + cardinality * 0.3 + diversity * 0.2)

    return {"entropy": round(entropy, 3), "leaves": leaf_count,
            "words": word_count, "unique": unique_leaves,
            "diversity": round(diversity, 3),
            "sparse": entropy > sparse_threshold}


def analyze_guide(guide: dict, threshold: float = 0.65,
                  category_map: dict = None) -> dict:
    """Analyze all sections of a domain guide for entropy gaps."""
    results = {}
    for key, value in guide.items():
        if key.startswith("_"):
            continue
        score = compute_section_entropy(value, sparse_threshold=threshold)
        score["key"] = key
        score["flagged"] = score["entropy"] > threshold
        if value is None or value == [] or value == {}:
            score["flagged"] = True
            score["reason"] = "empty_section"
        elif score["sparse"]:
            score["reason"] = "sparse_content"
        elif score.get("diversity", 1) < 0.3 and score["leaves"] > 5:
            score["flagged"] = True
            score["reason"] = "homogeneous_list"
        results[key] = score
    return results


def check_coverage(guide: dict, questions: list[dict]) -> dict:
    """Check which categories have thin guide coverage."""
    coverage = {}
    for cat, section_keys in CATEGORY_SECTION_MAP.items():
        q_count = sum(1 for q in questions if q.get("category") == cat)
        found_sections = sum(1 for k in section_keys
                            if any(k in gk for gk in guide.keys()))
        total_sections = len(section_keys)
        coverage[cat] = {
            "questions": q_count,
            "guide_sections_found": found_sections,
            "guide_sections_expected": total_sections,
            "coverage_pct": round(found_sections / total_sections * 100, 1) if total_sections else 0,
        }
    return coverage


def print_report(entropy_results: dict, coverage: dict = None, threshold: float = 0.65):
    """Print formatted entropy gap report."""
    print(f"\n{'='*60}")
    print(f"ENTROPY GAP ANALYSIS (threshold={threshold})")
    print(f"{'='*60}")

    flagged = [v for v in entropy_results.values() if v.get("flagged")]
    ok = [v for v in entropy_results.values() if not v.get("flagged")]

    print(f"\n  {len(flagged)} sparse sections, {len(ok)} dense sections\n")
    print(f"  {'Section':<30} {'Entropy':>8} {'Leaves':>7} {'Words':>7} {'Status':>8}")
    print(f"  {'-'*65}")
    for k, v in sorted(entropy_results.items(), key=lambda x: -x[1]["entropy"]):
        status = "SPARSE" if v["flagged"] else "ok"
        print(f"  {k:<30} {v['entropy']:>8.3f} {v['leaves']:>7} {v['words']:>7} {status:>8}")

    if coverage:
        print(f"\n  Question Coverage:")
        for cat, v in coverage.items():
            bar = "█" * (v["coverage_pct"] // 10)
            print(f"  {cat:<28} {v['questions']:>3}q  {v['guide_sections_found']}/{v['guide_sections_expected']} sections  {bar}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Entropy gap detector")
    parser.add_argument("--guide", default="data/cultural_guide.json")
    parser.add_argument("--questions", default="data/questions.json")
    parser.add_argument("--threshold", type=float, default=0.65)
    args = parser.parse_args()

    guide_path = Path(args.guide)
    if not guide_path.exists():
        print(f"Guide not found: {guide_path}")
        sys.exit(1)

    guide = json.loads(guide_path.read_text())
    entropy = analyze_guide(guide, args.threshold)

    coverage = None
    q_path = Path(args.questions)
    if q_path.exists():
        questions = json.loads(q_path.read_text()).get("questions", [])
        coverage = check_coverage(guide, questions)

    print_report(entropy, coverage, args.threshold)


if __name__ == "__main__":
    main()
