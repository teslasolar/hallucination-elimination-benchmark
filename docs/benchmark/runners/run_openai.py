#!/usr/bin/env python3
"""
Hallucination Elimination Benchmark — OpenAI Runner
=====================================================
Runs the 222-question Rome 110 CE benchmark against any OpenAI model.
Works with gpt-4o, gpt-4o-mini, gpt-3.5-turbo, or any chat-completion model.

Usage:
    python run_openai.py --model gpt-4o-mini
    python run_openai.py --model gpt-4o --triad
    python run_openai.py --model gpt-3.5-turbo --no-resume

Requirements:
    - OPENAI_API_KEY env var set
    - GEMINI_API_KEY env var set (for Gemini 2.0 Flash judge)
    - pip install openai requests

Judge: Gemini 2.0 Flash (free tier, 1500 RPM)
"""

import json
import time
import os
import sys
import argparse
import requests
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
RESULTS_DIR = SCRIPT_DIR.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

QUESTIONS_FILE = DATA_DIR / "questions.json"
CULTURAL_GUIDE_FILE = DATA_DIR / "cultural_guide.json"
CHARACTERS_FILE = DATA_DIR / "characters.json"

# ── Config ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)


# ── Load data ─────────────────────────────────────────────────────────────────
def load_data():
    with open(QUESTIONS_FILE) as f:
        q_data = json.load(f)
    questions = q_data["questions"]

    with open(CULTURAL_GUIDE_FILE) as f:
        cultural_guide = json.load(f)

    with open(CHARACTERS_FILE) as f:
        char_data = json.load(f)
    char_map = {c["id"]: c for c in char_data["characters"]}

    return questions, cultural_guide, char_map


# ── Build system prompts ──────────────────────────────────────────────────────
def build_triad_system(cultural_guide, char_map, char_id=None):
    ctx = cultural_guide
    locs = [{"name": l["name"], "desc": l["description"]} for l in ctx["key_locations"][:6]]
    not_built = ", ".join(ctx["anachronisms_to_avoid"]["not_yet_built"])
    not_happened = ", ".join(ctx["anachronisms_to_avoid"]["not_yet_happened"])
    already_dead = ", ".join(ctx["anachronisms_to_avoid"]["already_dead"][:5])
    no_tech = ", ".join(ctx["anachronisms_to_avoid"]["technology_notes"])

    if char_id and char_id in char_map:
        c = char_map[char_id]
        char_section = (
            f"You are {c['name']}, age {c['age']}, {c['role']} in Rome 110 CE.\n"
            f"Backstory: {c['backstory']}\n"
            f"Personality: {', '.join(c['personality_traits'])}\n"
            f"Expertise: {', '.join(c['expertise'])}\n"
            f"Speaking style: {c.get('speaking_style', 'natural')}\n"
        )
        char_name = c["name"]
        char_role = c["role"]
    else:
        char_section = "You are a knowledgeable resident of Rome in 110 CE.\n"
        char_name = "a Roman citizen"
        char_role = "resident of Rome"

    body = f"""{char_section}
Emperor: {ctx['time_period_context']['emperor']} | Pop: {ctx['time_period_context']['population']} | Currency: {ctx['time_period_context']['currency']}
Timeline: {json.dumps(ctx['timeline_recent_events'], indent=0)[:600]}

ANACHRONISMS — DO NOT EXIST in 110 CE:
Not built: {not_built}
Not happened: {not_happened}
Dead: {already_dead}
No tech: {no_tech}
If asked about something not yet existing, say you don't know what they mean.

Locations: {json.dumps(locs, indent=0)[:600]}
Social: {json.dumps(ctx['social_structure'], indent=0)[:600]}
Economy: {json.dumps(ctx['economy_and_trade'], indent=0)[:500]}
Prices: {json.dumps(ctx.get('prices_and_costs', {}), indent=0)[:300]}
Daily life: {json.dumps(ctx['daily_life'], indent=0)[:400]}
Religion: {json.dumps(ctx['roman_religion']['major_gods'], indent=0)[:300]}
Entertainment: {json.dumps(ctx['entertainment'], indent=0)[:400]}
Engineering: {json.dumps(ctx['engineering_and_architecture'], indent=0)[:300]}
Medicine: {json.dumps(ctx['medicine_and_health'], indent=0)[:300]}
Customs: {json.dumps(ctx['customs'], indent=0)[:300]}

=== FINAL REMINDER — READ THIS LAST ===
You are {char_name}, {char_role}. The year is 110 CE. Emperor Trajan rules Rome.
- If asked about anything NOT YET EXISTING: say "I don't know what you mean by that."
- Stay in character at all times.
- Answer in 2-3 sentences maximum.
- NEVER mention anything from after 110 CE."""
    return body


def build_raw_system(char_map, char_id=None):
    if char_id and char_id in char_map:
        c = char_map[char_id]
        return (
            f"You are {c['name']}, a Roman citizen in 110 CE. "
            f"Answer questions as this character. "
            f"Keep answers to 2-3 sentences."
        )
    return "You are a Roman citizen in 110 CE. Answer questions in character. Keep answers to 2-3 sentences."


def wrap_question(question, category, char_id=None, char_map=None):
    if category == "ANACHRONISM_DETECTION":
        return (
            "Before answering, check: does this thing exist in 110 CE?\n"
            "If not, say you have never heard of it.\n\n" + question
        )
    elif category == "CHARACTER_IDENTITY" and char_id and char_map and char_id in char_map:
        c = char_map[char_id]
        return f"[You are {c['name']}, {c['role']}]\n{question}"
    elif category == "COMPLEX_SCENARIOS":
        return "Think through this using Roman law, custom, and social norms of 110 CE:\n\n" + question
    return question


# ── OpenAI call ───────────────────────────────────────────────────────────────
def call_openai(client, model, system_prompt, user_question, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question},
                ],
                max_tokens=500,
                temperature=0.0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "rate_limit" in err.lower() and attempt < retries - 1:
                wait = 2 ** attempt * 5
                print(f"  Rate limited, waiting {wait}s...", flush=True)
                time.sleep(wait)
            elif attempt == retries - 1:
                return f"ERROR: {e}"
            else:
                time.sleep(2 ** attempt)
    return "ERROR: max retries exceeded"


# ── Gemini judge ──────────────────────────────────────────────────────────────
JUDGE_PROMPT = """You are evaluating an AI playing a Roman character in 110 CE.

Category: {category}
Ground truth / expected behavior: {ground_truth}
Model's answer: {answer}

Did the model's answer PASS (correctly handle this culturally/historically) or FAIL?

Respond with exactly one word: PASS or FAIL"""


def call_gemini(prompt, retries=6):
    for attempt in range(retries):
        try:
            resp = requests.post(
                GEMINI_URL,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 50, "temperature": 0.0},
                },
                timeout=30,
            )
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"  Gemini rate-limited, waiting {wait}s...", flush=True)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            if not parts:
                return "JUDGE_FAILED"
            text = parts[0].get("text", "").strip().upper()
            return "PASS" if "PASS" in text else ("FAIL" if "FAIL" in text else "JUDGE_FAILED")
        except Exception:
            if attempt == retries - 1:
                return "JUDGE_FAILED"
            time.sleep(2 ** attempt)
    return "JUDGE_FAILED"


def gemini_judge(category, ground_truth, answer):
    if not answer or answer.startswith("ERROR:"):
        return "JUDGE_FAILED"
    prompt = JUDGE_PROMPT.format(
        category=category, ground_truth=ground_truth, answer=answer[:2000]
    )
    return call_gemini(prompt)


# ── Results ───────────────────────────────────────────────────────────────────
def make_results_filename(model, use_triad):
    safe = model.replace(":", "_").replace("/", "_").replace("-", "_")
    suffix = "_triad" if use_triad else "_raw"
    return RESULTS_DIR / f"benchmark_{safe}{suffix}.json"


def load_results(filepath, model, use_triad):
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {
        "model": model,
        "mode": "Triad Engine" if use_triad else "Raw baseline",
        "judge": GEMINI_MODEL,
        "benchmark_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": [],
    }


def save_results(data, filepath):
    details = data["details"]
    passed = sum(1 for d in details if d["verdict"] == "PASS")
    total = len(details)
    cats = {}
    for d in details:
        cat = d["category"]
        if cat not in cats:
            cats[cat] = {"passed": 0, "total": 0}
        cats[cat]["total"] += 1
        if d["verdict"] == "PASS":
            cats[cat]["passed"] += 1
    data.update(
        {
            "completed": total,
            "passed": passed,
            "failed": sum(1 for d in details if d["verdict"] == "FAIL"),
            "errors": sum(1 for d in details if d["verdict"] == "ERROR"),
            "judge_failed": sum(1 for d in details if d["verdict"] == "JUDGE_FAILED"),
            "accuracy_pct": round(passed / total * 100, 1) if total > 0 else 0,
            "categories": cats,
        }
    )
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Run hallucination benchmark via OpenAI API")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model (default: gpt-4o-mini)")
    parser.add_argument("--triad", action="store_true", help="Use Triad Engine context injection")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh")
    args = parser.parse_args()

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("Get a free key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    client = OpenAI(api_key=OPENAI_API_KEY)
    questions, cultural_guide, char_map = load_data()
    results_file = make_results_filename(args.model, args.triad)
    data = load_results(results_file, args.model, args.triad)

    done_indices = {
        d["index"]
        for d in data["details"]
        if d.get("verdict") in ("PASS", "FAIL") and len(d.get("answer", "")) > 10
    } if not args.no_resume else set()

    if done_indices:
        print(f"Resuming: {len(done_indices)}/{len(questions)} already done")

    print("=" * 70)
    print(f"Hallucination Elimination Benchmark")
    print(f"  Model: {args.model}")
    print(f"  Mode: {'Triad Engine (cultural context)' if args.triad else 'Raw baseline'}")
    print(f"  Judge: {GEMINI_MODEL}")
    print("=" * 70)

    for q in questions:
        idx = q["index"]
        if idx in done_indices:
            continue

        num = idx + 1
        category = q["category"]
        question = q["question"]
        ground_truth = q["ground_truth"]
        char_id = q.get("character")

        print(f"[{num}/{len(questions)}] {category}: {question[:60]}...", flush=True)

        if args.triad:
            system = build_triad_system(cultural_guide, char_map, char_id)
            user_msg = wrap_question(question, category, char_id, char_map)
        else:
            system = build_raw_system(char_map, char_id)
            user_msg = question

        answer = call_openai(client, args.model, system, user_msg)

        if answer.startswith("ERROR:"):
            verdict = "ERROR"
            print(f"  ERROR: {answer}", flush=True)
        else:
            verdict = gemini_judge(category, ground_truth, answer)
            print(f"  {verdict}", flush=True)

        data["details"].append(
            {
                "index": idx,
                "question_num": num,
                "category": category,
                "question": question,
                "ground_truth": ground_truth,
                "answer": answer,
                "verdict": verdict,
                "passed": verdict == "PASS",
            }
        )
        save_results(data, results_file)

    print()
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Overall: {data['passed']}/{data['completed']} ({data['accuracy_pct']}%)")
    print()
    print(f"{'Category':<25} {'Score':>8}  {'Pass/Total':>12}")
    print("-" * 50)
    for cat, stats in sorted(data["categories"].items()):
        pct = round(stats["passed"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        print(f"  {cat:<23} {pct:>7.1f}%  {stats['passed']}/{stats['total']}")
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
