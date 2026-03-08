#!/usr/bin/env python3
"""
Entropy Gap Detector for Cultural Domain Guides
================================================
Concept adapted from Thomas P. Frumkin's LookingGlass commit 9fa2488
("nodes reverse-engineered from entropy gaps"), applied to JSON knowledge guides.

Analyzes a cultural_guide.json for sparse zones, cross-reference breaks,
and question coverage imbalances. Optionally fills gaps using Mistral 7B
(Ollama, production model) or Claude API.

Usage:
    python3 entropy_gap_detector.py
    python3 entropy_gap_detector.py --fill
    python3 entropy_gap_detector.py --fill --model claude
    python3 entropy_gap_detector.py --threshold 0.5
    python3 entropy_gap_detector.py --guide path/to/custom_guide.json
"""

import json
import argparse
import subprocess
import statistics
import os
import sys
from pathlib import Path

# ── Defaults ─────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent
DATA_DIR     = SCRIPT_DIR.parent / "data"
GUIDE_PATH   = DATA_DIR / "cultural_guide.json"
QUESTIONS_PATH = DATA_DIR / "questions.json"

DEFAULT_THRESHOLD = 0.65   # entropy score above which a section is flagged
DEFAULT_MODEL     = "mistral"

# Map benchmark question categories → guide section keywords
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

# ── Leaf extraction ───────────────────────────────────────────────────────────

def extract_leaves(obj, depth=0):
    """Recursively extract all leaf string values from a JSON object."""
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


def section_stats(value):
    """Compute cardinality and depth stats for one top-level section."""
    leaves = extract_leaves(value)
    cardinality = len(leaves)
    if cardinality == 0:
        return {"cardinality": 0, "avg_len": 0, "total_chars": 0}
    avg_len    = statistics.mean(len(s) for s in leaves)
    total_chars = sum(len(s) for s in leaves)
    return {"cardinality": cardinality, "avg_len": avg_len, "total_chars": total_chars}


# ── Entropy scoring ───────────────────────────────────────────────────────────

def compute_entropy_scores(guide):
    """Score every top-level section. Higher = more sparse = bigger gap."""
    profiles = {}
    for key, value in guide.items():
        profiles[key] = section_stats(value)

    cards = [p["cardinality"] for p in profiles.values()]
    depths = [p["avg_len"]     for p in profiles.values()]

    max_card  = max(cards)  or 1
    max_depth = max(depths) or 1

    scored = {}
    for key, p in profiles.items():
        norm_card  = p["cardinality"] / max_card
        norm_depth = p["avg_len"]     / max_depth
        entropy    = 1.0 - (norm_card * 0.5 + norm_depth * 0.5)
        scored[key] = {**p, "entropy": round(entropy, 3)}

    return scored


# ── Cross-reference checks ────────────────────────────────────────────────────

def check_cross_references(guide):
    """Return list of cross-reference inconsistency strings."""
    issues = []

    # 1. already_dead list vs notable_people sections
    already_dead_raw = []
    if "anachronisms_to_avoid" in guide:
        already_dead_raw = guide["anachronisms_to_avoid"].get("already_dead", [])

    notable_names = set()
    for key, val in guide.items():
        if "notable_people" in key and isinstance(val, dict):
            for section_val in val.values():
                if isinstance(section_val, list):
                    for person in section_val:
                        if isinstance(person, dict) and "name" in person:
                            notable_names.add(person["name"].lower())
                        elif isinstance(person, str):
                            notable_names.add(person.lower())
                elif isinstance(section_val, dict):
                    if "name" in section_val:
                        notable_names.add(section_val["name"].lower())

    for entry in already_dead_raw:
        name = entry.split("(")[0].strip().lower() if isinstance(entry, str) else ""
        if name and not any(name in n or n in name for n in notable_names):
            issues.append(f"already_dead entry not found in notable_people: '{entry}'")

    # 2. gossip mentions vs notable_people
    gossip_entries = []
    if "gossip_and_rumors" in guide:
        for arr in guide["gossip_and_rumors"].values():
            if isinstance(arr, list):
                gossip_entries.extend(arr)

    # Extract capitalized names from gossip (rough heuristic)
    import re
    for gossip in gossip_entries:
        if not isinstance(gossip, str):
            continue
        names_in_gossip = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b', gossip)
        roman_indicators = {"Rome", "Roman", "Emperor", "Senator", "Legion",
                            "Forum", "Caesar", "Trajan", "Via", "The", "His",
                            "Her", "They", "She", "He", "It", "This", "That"}
        for name in names_in_gossip:
            if name not in roman_indicators and len(name) > 3:
                if not any(name.lower() in n or n in name.lower()
                           for n in notable_names):
                    issues.append(
                        f"Name in gossip_and_rumors not in notable_people: '{name}'"
                    )
                    break  # one per gossip entry is enough

    return issues


# ── Question coverage check ───────────────────────────────────────────────────

def check_question_coverage(guide, questions):
    """Return coverage gaps: categories with many questions but thin guide sections."""
    # Count questions per category
    cat_counts = {}
    for q in questions:
        cat = q.get("category", "UNKNOWN")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    total_questions = sum(cat_counts.values()) or 1

    gaps = []
    for category, keywords in CATEGORY_SECTION_MAP.items():
        q_count = cat_counts.get(category, 0)
        q_ratio = q_count / total_questions

        # Find matching guide sections
        matched_total_chars = 0
        matched_sections = []
        for key in guide:
            if any(kw in key.lower() for kw in keywords):
                leaves = extract_leaves(guide[key])
                matched_total_chars += sum(len(s) for s in leaves)
                matched_sections.append(key)

        guide_total = sum(
            sum(len(s) for s in extract_leaves(v)) for v in guide.values()
        ) or 1
        guide_ratio = matched_total_chars / guide_total

        # Gap if question ratio is 2x+ the guide coverage ratio
        if q_ratio > 0 and guide_ratio < q_ratio / 2:
            gaps.append({
                "category":  category,
                "questions":  q_count,
                "q_ratio":   round(q_ratio, 3),
                "guide_ratio": round(guide_ratio, 3),
                "thin_sections": matched_sections or ["(no matching sections found)"],
            })

    return gaps


# ── Draft prompt generation ───────────────────────────────────────────────────

def make_fill_prompt(key, stats, guide_value):
    """Generate a specific enrichment prompt for a sparse section."""
    sample_leaves = extract_leaves(guide_value)[:3]
    sample_text   = "; ".join(sample_leaves[:2]) if sample_leaves else "(empty)"

    return (
        f"You are an expert on Ancient Rome in 110 CE under Emperor Trajan. "
        f"The knowledge guide section '{key}' is sparse (only {stats['cardinality']} "
        f"entries, avg {stats['avg_len']:.0f} chars each). "
        f"Current content sample: {sample_text[:200]}. "
        f"Add 8-12 new, historically accurate entries for '{key}' in 110 CE Rome. "
        f"Be specific: include names, prices in denarii/sestertii where relevant, "
        f"dates, locations, and concrete details. "
        f"Format as a JSON array of strings. Output ONLY valid JSON, no explanation."
    )


# ── Filling via Ollama / Claude ───────────────────────────────────────────────

def fill_with_ollama(prompt, model="mistral"):
    """Call ollama CLI and return response text."""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None


def fill_with_claude(prompt):
    """Call Claude API and return response text."""
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            env_file = Path(__file__).parent.parent.parent / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("ANTHROPIC_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"')
        if not api_key:
            print("  ERROR: ANTHROPIC_API_KEY not found in environment or .env")
            return None
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except ImportError:
        print("  ERROR: anthropic package not installed. Run: pip install anthropic")
        return None


def fill_with_gemini(prompt):
    """Call Gemini Flash API and return response text."""
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            env_file = Path(__file__).parent.parent.parent / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("GEMINI_API_KEY=") or line.startswith("GOOGLE_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"')
        if not api_key:
            print("  ERROR: GEMINI_API_KEY not found in environment or .env")
            return None
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except ImportError:
        print("  ERROR: google-generativeai not installed. Run: pip install google-generativeai")
        return None
    except Exception as e:
        print(f"  ERROR: Gemini call failed: {e}")
        return None


def parse_json_response(text):
    """Try to extract a JSON array from model response."""
    import re
    # Find first [...] block
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ── Main report ───────────────────────────────────────────────────────────────

def run(args):
    guide_path     = Path(args.guide)
    questions_path = Path(args.questions)

    if not guide_path.exists():
        print(f"ERROR: Guide not found: {guide_path}")
        sys.exit(1)

    with open(guide_path) as f:
        guide = json.load(f)

    questions = []
    if questions_path.exists():
        with open(questions_path) as f:
            raw = json.load(f)
        # questions.json wraps the list under a "questions" key
        if isinstance(raw, dict) and "questions" in raw:
            questions = raw["questions"]
        elif isinstance(raw, list):
            questions = raw

    print(f"\n{'='*60}")
    print(f"ENTROPY GAP REPORT — {guide_path.name}")
    print(f"{'='*60}")
    print(f"Sections: {len(guide)}  |  Threshold: {args.threshold}")

    # ── 1. Entropy scores ─────────────────────────────────────────────────────
    scores = compute_entropy_scores(guide)
    flagged = {k: v for k, v in scores.items() if v["entropy"] >= args.threshold}
    flagged_sorted = sorted(flagged.items(), key=lambda x: -x[1]["entropy"])

    print(f"\nSPARSE SECTIONS (entropy >= {args.threshold}):")
    if not flagged_sorted:
        print("  None — guide coverage looks balanced.")
    else:
        for key, stats in flagged_sorted:
            severity = "HIGH" if stats["entropy"] >= 0.80 else "MED"
            print(f"  [{severity}]  {key:<35} "
                  f"score={stats['entropy']:.3f}  "
                  f"entries={stats['cardinality']}  "
                  f"avg_len={stats['avg_len']:.0f} chars")

    # ── 2. Cross-reference issues ─────────────────────────────────────────────
    xref_issues = check_cross_references(guide)
    print(f"\nCONSISTENCY GAPS ({len(xref_issues)} found):")
    if not xref_issues:
        print("  None — cross-references look consistent.")
    else:
        for issue in xref_issues[:10]:   # cap at 10
            print(f"  - {issue}")
        if len(xref_issues) > 10:
            print(f"  ... and {len(xref_issues) - 10} more")

    # ── 3. Question coverage balance ──────────────────────────────────────────
    if questions:
        coverage_gaps = check_question_coverage(guide, questions)
        print(f"\nQUESTION COVERAGE GAPS:")
        if not coverage_gaps:
            print("  None — guide coverage matches question distribution.")
        else:
            for gap in coverage_gaps:
                thin = ", ".join(gap["thin_sections"][:3])
                print(f"  {gap['category']}: {gap['questions']} questions "
                      f"(q_ratio={gap['q_ratio']:.1%}) but guide coverage only "
                      f"{gap['guide_ratio']:.1%}  →  thin: {thin}")
    else:
        print(f"\nQUESTION COVERAGE: (questions.json not found, skipping)")

    # ── 4. Draft prompts ──────────────────────────────────────────────────────
    # Only generate prompts for sections also flagged by question coverage gaps
    question_gap_sections = set()
    if questions:
        for gap in check_question_coverage(guide, questions):
            question_gap_sections.update(gap["thin_sections"])

    # Prioritise: sections that are both sparse AND under-covered by questions
    if question_gap_sections:
        high_gaps = [(k, v) for k, v in flagged_sorted
                     if v["entropy"] >= 0.75 and k in question_gap_sections]
        # Fall back to top-10 by entropy if no overlap found
        if not high_gaps:
            high_gaps = [(k, v) for k, v in flagged_sorted if v["entropy"] >= 0.90][:10]
    else:
        high_gaps = [(k, v) for k, v in flagged_sorted if v["entropy"] >= 0.90][:10]

    if high_gaps:
        print(f"\nDRAFT FILL PROMPTS (top {len(high_gaps)} HIGH gaps):")
        prompts = {}
        for i, (key, stats) in enumerate(high_gaps, 1):
            prompt = make_fill_prompt(key, stats, guide[key])
            prompts[key] = prompt
            print(f"\n  [{i}] Section: {key}")
            print(f"       {prompt[:120]}...")

        # ── 5. Fill mode ──────────────────────────────────────────────────────
        if args.fill:
            print(f"\n{'='*60}")
            print(f"FILLING GAPS with model: {args.model}")
            print(f"{'='*60}")

            guide_modified = False
            for key, prompt in prompts.items():
                print(f"\n  Filling: {key} ...", end="", flush=True)

                if args.model == "claude":
                    response = fill_with_claude(prompt)
                elif args.model == "gemini":
                    response = fill_with_gemini(prompt)
                else:
                    response = fill_with_ollama(prompt, model=args.model)

                if not response:
                    print(f" FAILED (model did not respond)")
                    continue

                new_entries = parse_json_response(response)
                if not new_entries:
                    print(f" FAILED (could not parse JSON from response)")
                    print(f"    Raw response: {response[:200]}")
                    continue

                # Merge into guide
                existing = guide.get(key, {})
                if isinstance(existing, dict):
                    existing.setdefault("_enriched", []).extend(new_entries)
                    guide[key] = existing
                elif isinstance(existing, list):
                    guide[key] = existing + new_entries
                else:
                    guide[key] = new_entries

                print(f" OK (+{len(new_entries)} entries)")
                guide_modified = True

            if guide_modified:
                with open(guide_path, "w") as f:
                    json.dump(guide, f, indent=2, ensure_ascii=False)
                print(f"\nGuide updated: {guide_path}")
                print("Re-run without --fill to confirm entropy scores improved.")
            else:
                print("\nNo sections were successfully filled.")
    else:
        print("\nNo HIGH gaps found — no draft prompts generated.")
        if flagged_sorted:
            print("(MED gaps exist but are below auto-fill threshold of 0.75)")

    print(f"\n{'='*60}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detect entropy gaps in a cultural domain guide JSON."
    )
    parser.add_argument(
        "--guide", default=str(GUIDE_PATH),
        help=f"Path to cultural guide JSON (default: {GUIDE_PATH})"
    )
    parser.add_argument(
        "--questions", default=str(QUESTIONS_PATH),
        help=f"Path to questions JSON (default: {QUESTIONS_PATH})"
    )
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help=f"Entropy threshold for flagging sparse sections (default: {DEFAULT_THRESHOLD})"
    )
    parser.add_argument(
        "--fill", action="store_true",
        help="Auto-fill HIGH gaps using the specified model"
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        choices=["mistral", "claude", "gemini", "llama3", "gemma"],
        help=f"Model to use for filling (default: {DEFAULT_MODEL}). "
             "gemini uses Gemini 2.0 Flash API. claude uses Anthropic API. Others use Ollama."
    )
    args = parser.parse_args()
    run(args)
