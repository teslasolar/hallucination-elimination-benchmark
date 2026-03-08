#!/usr/bin/env python3
"""
Compositional Chaining Benchmark — Anthropic Runner
=====================================================
Tests whether Triad Engine drift is bounded when prior responses are passed
as context into subsequent calls.

Three chain types:
  DEPTH_SCALING    — N-step factual chains. Does accuracy hold at depth 5?
  FAULT_INJECTION  — False premise injected at step K. Does the guide correct it?
  CROSS_CHARACTER  — Sequential persona chain. Does identity hold across hops?

Key hypothesis: because the domain guide is re-injected on every call as the
system prompt, per-step accuracy should be bounded regardless of chain depth
or upstream corruption.

Usage:
    python run_chain_benchmark.py --model claude-haiku-4-5-20251001 --triad
    python run_chain_benchmark.py --model claude-sonnet-4-6 --triad
    python run_chain_benchmark.py --model claude-sonnet-4-6  # raw baseline

Requirements:
    - ANTHROPIC_API_KEY env var set
    - GEMINI_API_KEY env var set (for Gemini 2.0 Flash judge)
    - pip install anthropic requests
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
    import anthropic
except ImportError:
    anthropic = None  # Only required for Anthropic models

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
MAIN_DATA_DIR = SCRIPT_DIR.parent / "data"   # cultural_guide, characters (shared)
RESULTS_DIR = SCRIPT_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

CHAIN_QUESTIONS_FILE = SCRIPT_DIR / "chain_questions.json"
CULTURAL_GUIDE_FILE = MAIN_DATA_DIR / "cultural_guide.json"
CHARACTERS_FILE = MAIN_DATA_DIR / "characters.json"

# ── Load .env if keys not already in environment ───────────────────────────────
def _load_dotenv():
    for candidate in [
        SCRIPT_DIR.parent.parent / ".env",
        SCRIPT_DIR.parent.parent / "backend" / ".env",
    ]:
        if candidate.exists():
            with open(candidate) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
            break

_load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
JUDGE_GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


# ── Load data ─────────────────────────────────────────────────────────────────
def load_data():
    with open(CHAIN_QUESTIONS_FILE) as f:
        chain_data = json.load(f)

    with open(CULTURAL_GUIDE_FILE) as f:
        cultural_guide = json.load(f)

    with open(CHARACTERS_FILE) as f:
        char_data = json.load(f)
    char_map = {c["id"]: c for c in char_data["characters"]}

    return chain_data["chains"], cultural_guide, char_map


# ── System prompts (identical to run_anthropic.py — guide re-injected every call) ──
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


# ── Model calls (Anthropic or Gemini) ─────────────────────────────────────────
def call_anthropic(client, model, system_prompt, user_question, retries=3):
    for attempt in range(retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_question}],
            )
            return message.content[0].text.strip()
        except Exception as e:
            err = str(e)
            if ("overloaded" in err.lower() or "rate" in err.lower()) and attempt < retries - 1:
                wait = 2 ** attempt * 5
                print(f"  Rate limited, waiting {wait}s...", flush=True)
                time.sleep(wait)
            elif attempt == retries - 1:
                return f"ERROR: {e}"
            else:
                time.sleep(2 ** attempt)
    return "ERROR: max retries exceeded"


def call_gemini_model(model, system_prompt, user_question, retries=6):
    url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={GEMINI_API_KEY}"
    for attempt in range(retries):
        try:
            resp = requests.post(
                url,
                json={
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": user_question}]}],
                    "generationConfig": {"maxOutputTokens": 500, "temperature": 0.0},
                },
                timeout=60,
            )
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"  Rate limited, waiting {wait}s...", flush=True)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            if not parts:
                return "ERROR: empty response"
            return parts[0].get("text", "").strip()
        except Exception as e:
            if attempt == retries - 1:
                return f"ERROR: {e}"
            time.sleep(2 ** attempt)
    return "ERROR: max retries"


def call_model(provider, client, model, system_prompt, user_question):
    if provider == "gemini":
        return call_gemini_model(model, system_prompt, user_question)
    return call_anthropic(client, model, system_prompt, user_question)


# ── Gemini judge ───────────────────────────────────────────────────────────────
JUDGE_PROMPT = """You are evaluating an AI playing a Roman character in 110 CE.

Category: {category}
Ground truth / expected behavior: {ground_truth}
Model's answer: {answer}

Did the model's answer PASS (correctly handle this culturally/historically) or FAIL?

Respond with exactly one word: PASS or FAIL"""


def call_gemini_judge(prompt, retries=6):
    url = f"{GEMINI_BASE_URL}/{JUDGE_GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    for attempt in range(retries):
        try:
            resp = requests.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 50, "temperature": 0.0},
                },
                timeout=30,
            )
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"  Judge rate-limited, waiting {wait}s...", flush=True)
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
    return call_gemini_judge(prompt)


# ── Synthetic chain generator (for depth 50 / 100 / arbitrary) ───────────────
SEED_QUESTIONS = [
    ("DOMAIN_SPECIFIC",    "Who is the current emperor of Rome?",
     "Trajan (Marcus Ulpius Traianus), emperor since 98 CE, known for Dacian Wars and building programs."),
    ("DOMAIN_SPECIFIC",    "What coins does Rome use today, and what are they worth relative to each other?",
     "Aureus (gold) = 25 denarii; denarius (silver) = 4 sestertii; sestertius (bronze) = 4 asses."),
    ("DOMAIN_SPECIFIC",    "Where does most of Rome's grain come from?",
     "Primarily Egypt and North Africa (Carthage region) — grain provinces shipped via Ostia."),
    ("DOMAIN_SPECIFIC",    "What is the Praefectus Annonae?",
     "Equestrian-rank official who manages Rome's grain supply — imports, storage, and distribution to citizens."),
    ("CULTURAL_VALUES",    "What does dignitas mean to a Roman senator?",
     "Personal honor, political standing, and reputation — foundational to Roman identity, more important than wealth alone."),
    ("DOMAIN_SPECIFIC",    "What building projects is Trajan currently undertaking in Rome?",
     "Forum of Trajan and Trajan's Market under construction; Trajan's Column nearing completion (dedicated 113 CE)."),
    ("CULTURAL_VALUES",    "How does a Roman patron treat his clients?",
     "Morning salutatio (receiving clients), legal advocacy, financial support, political favors — a reciprocal bond of obligation."),
    ("DOMAIN_SPECIFIC",    "What goods arrive at Ostia from Alexandria?",
     "Egyptian grain (Rome's primary supply), papyrus, linen, glassware, luxury goods from India and Arabia routed through Alexandria."),
    ("CULTURAL_VALUES",    "What philosophical school is most fashionable among Roman elites in 110 CE?",
     "Stoicism — dominant among educated Romans. Epictetus teaches in Nicopolis; Pliny and Tacitus are active writers."),
    ("DOMAIN_SPECIFIC",    "How large is Rome's population?",
     "~1 million in the city, ~4-7 million in Italy, ~50-70 million across the empire. Largest city in the Western world."),
    ("DOMAIN_SPECIFIC",    "What is the Forum Romanum used for?",
     "Legal cases, business negotiations, political meetings, proclamations, religious ceremonies — the heart of Roman civic life."),
    ("CULTURAL_VALUES",    "What does it mean to be a Roman citizen in 110 CE?",
     "Legal rights, access to courts, grain dole eligibility, right of appeal to emperor. Status still varies greatly by class."),
    ("DOMAIN_SPECIFIC",    "What is the role of the Vestal Virgins?",
     "Six priestesses guarding the sacred flame of Vesta; 30-year service, enormous social prestige and legal privileges."),
    ("DOMAIN_SPECIFIC",    "What entertainment do Romans most enjoy?",
     "Circus Maximus chariot racing (250,000 capacity), Colosseum gladiatorial games, theater, public baths as social venues."),
    ("DOMAIN_SPECIFIC",    "What are the main writing materials used in Rome in 110 CE?",
     "Wax tablets (tabulae ceratae) with stylus for notes/correspondence; papyrus scrolls (volumen) for literature and records. No paper."),
    ("DOMAIN_SPECIFIC",    "How do Romans settle large commercial transactions?",
     "Metal coinage (aureus, denarius, sestertius) and letters of credit between trusted argentarii (bankers). No paper money."),
    ("CULTURAL_VALUES",    "What obligation do wealthy Romans have to public entertainment?",
     "Euergetism — wealthy patrons and magistrates are expected to fund games, public buildings, and feasts as civic duty."),
    ("DOMAIN_SPECIFIC",    "What are the main legionary deployments in 110 CE?",
     "Rhine (4 legions), Danube (8-9 legions), Syria/East (3-4), Egypt (2), Britannia (3), Dacia (newly pacified province)."),
    ("DOMAIN_SPECIFIC",    "What language do educated Romans write and speak?",
     "Latin for law, government, and literature; Greek widely used by educated Romans, especially for philosophy and science."),
    ("CULTURAL_VALUES",    "What is pietas to a Roman?",
     "Duty to gods, family, and state — not just personal piety but fulfillment of all obligations. Foundational Roman virtue alongside virtus and gravitas."),
]


def generate_synthetic_chain(depth):
    """
    Generate a synthetic DEPTH_SCALING chain of arbitrary length by cycling
    through SEED_QUESTIONS. Each step passes the prior model response as context.
    Used to test depth 50, 100, or more without hand-crafting every step.
    """
    steps = []
    for i in range(depth):
        cat, question, ground_truth = SEED_QUESTIONS[i % len(SEED_QUESTIONS)]
        step = {
            "step": i + 1,
            "category": cat,
            "question": question,
            "ground_truth": ground_truth,
            "character": None,
            "context_from_previous": i > 0,
        }
        if i > 0:
            step["context_template"] = (
                f"Prior exchange in this conversation: {{previous_response}}\n\n{question}"
            )
        steps.append(step)

    return {
        "chain_id": f"synthetic_depth_{depth}",
        "chain_type": "DEPTH_SCALING",
        "depth": depth,
        "description": f"Synthetic {depth}-hop scaling chain — auto-generated from seed questions to stress-test drift at maximum depth",
        "steps": steps,
    }


# ── Build user message for a step ─────────────────────────────────────────────
def build_user_message(step, previous_response, chain):
    """
    Resolve the user message for this step.

    - Step 1 (context_from_previous=False): use question directly
    - Subsequent steps: substitute {previous_response} into context_template
    - Fault injection steps: substitute {injected_error} instead of actual prior response
    """
    if not step.get("context_from_previous", False):
        return step["question"]

    template = step.get("context_template", "{previous_response}\n\n{question}")

    if step.get("inject_error", False):
        # Use the chain-level injected_error instead of real prior response
        injected = chain.get("injected_error", "")
        msg = template.replace("{injected_error}", injected)
        msg = msg.replace("{previous_response}", injected)
        msg = msg.replace("{question}", step["question"])
    else:
        msg = template.replace("{previous_response}", previous_response or "")
        msg = msg.replace("{question}", step["question"])

    return msg


# ── Run a single chain ─────────────────────────────────────────────────────────
def run_chain(chain, client, model, use_triad, cultural_guide, char_map, provider="anthropic"):
    chain_id = chain["chain_id"]
    chain_type = chain["chain_type"]
    steps = chain["steps"]

    print(f"\n{'─' * 60}")
    print(f"Chain: {chain_id} ({chain_type}) — {chain.get('description', '')}")
    print(f"{'─' * 60}")

    step_results = []
    previous_response = None

    for step in steps:
        step_num = step["step"]
        category = step["category"]
        ground_truth = step["ground_truth"]
        char_id = step.get("character")
        is_fault = step.get("inject_error", False)

        user_msg = build_user_message(step, previous_response, chain)

        label = f"  Step {step_num}/{len(steps)}"
        if is_fault:
            label += " [FAULT INJECTED]"
        print(f"{label}: {user_msg[:80].strip()}...", flush=True)

        if use_triad:
            system = build_triad_system(cultural_guide, char_map, char_id)
        else:
            system = build_raw_system(char_map, char_id)

        answer = call_model(provider, client, model, system, user_msg)

        if answer.startswith("ERROR:"):
            verdict = "ERROR"
        else:
            verdict = gemini_judge(category, ground_truth, answer)

        print(f"    → {verdict}", flush=True)

        step_results.append({
            "step": step_num,
            "category": category,
            "question": step["question"],
            "user_message_sent": user_msg,
            "ground_truth": ground_truth,
            "character": char_id,
            "fault_injected": is_fault,
            "answer": answer,
            "verdict": verdict,
            "passed": verdict == "PASS",
        })

        # Next step receives actual model response (not injected error)
        # On ERROR, preserve last good response so chain context doesn't blank out
        if not answer.startswith("ERROR:"):
            previous_response = answer

        time.sleep(6)  # 6s between steps keeps model+judge calls under 15 RPM free tier

    passed = sum(1 for s in step_results if s["passed"])
    total = len(step_results)
    pct = round(passed / total * 100, 1) if total > 0 else 0
    print(f"  Chain score: {passed}/{total} ({pct}%)")

    return {
        "chain_id": chain_id,
        "chain_type": chain_type,
        "description": chain.get("description", ""),
        "depth": len(steps),
        "steps": step_results,
        "passed": passed,
        "total": total,
        "accuracy_pct": pct,
    }


# ── Aggregate stats ────────────────────────────────────────────────────────────
def compute_summary(chain_results):
    by_type = {}
    depth_accuracy = {}  # step_number → [passed, total]

    for cr in chain_results:
        ct = cr["chain_type"]
        if ct not in by_type:
            by_type[ct] = {"passed": 0, "total": 0, "chains": 0}
        by_type[ct]["passed"] += cr["passed"]
        by_type[ct]["total"] += cr["total"]
        by_type[ct]["chains"] += 1

        for step in cr["steps"]:
            sn = step["step"]
            if sn not in depth_accuracy:
                depth_accuracy[sn] = {"passed": 0, "total": 0}
            depth_accuracy[sn]["total"] += 1
            if step["passed"]:
                depth_accuracy[sn]["passed"] += 1

    # Per-step accuracy (is there degradation as depth increases?)
    depth_stats = {}
    for sn, d in sorted(depth_accuracy.items()):
        pct = round(d["passed"] / d["total"] * 100, 1) if d["total"] > 0 else 0
        depth_stats[f"step_{sn}"] = {"passed": d["passed"], "total": d["total"], "accuracy_pct": pct}

    # Per-type accuracy
    type_stats = {}
    for ct, d in by_type.items():
        pct = round(d["passed"] / d["total"] * 100, 1) if d["total"] > 0 else 0
        type_stats[ct] = {"passed": d["passed"], "total": d["total"], "accuracy_pct": pct, "chains": d["chains"]}

    total_passed = sum(cr["passed"] for cr in chain_results)
    total_steps = sum(cr["total"] for cr in chain_results)
    overall_pct = round(total_passed / total_steps * 100, 1) if total_steps > 0 else 0

    return {
        "overall_accuracy_pct": overall_pct,
        "total_passed": total_passed,
        "total_steps": total_steps,
        "by_chain_type": type_stats,
        "by_step_depth": depth_stats,
    }


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Run compositional chaining benchmark")
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Model ID (Claude or Gemini)",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "gemini"],
        default=None,
        help="API provider (auto-detected from model name if not set)",
    )
    parser.add_argument("--triad", action="store_true", help="Use Triad Engine context injection")
    parser.add_argument(
        "--chain-type",
        choices=["DEPTH_SCALING", "FAULT_INJECTION", "CROSS_CHARACTER", "ALL"],
        default="ALL",
        help="Run only chains of this type (default: ALL)",
    )
    parser.add_argument(
        "--synthetic-depth",
        type=int,
        default=0,
        metavar="N",
        help="Add a synthetic N-hop depth scaling chain (e.g. --synthetic-depth 50). Runs alongside other chains.",
    )
    args = parser.parse_args()

    # Auto-detect provider from model name
    provider = args.provider
    if provider is None:
        provider = "gemini" if args.model.startswith("gemini") else "anthropic"

    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = None
    if provider == "anthropic":
        if not ANTHROPIC_API_KEY:
            print("ERROR: ANTHROPIC_API_KEY environment variable not set")
            sys.exit(1)
        if anthropic is None:
            print("ERROR: anthropic package not installed. Run: pip install anthropic")
            sys.exit(1)
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    chains, cultural_guide, char_map = load_data()

    if args.chain_type != "ALL":
        chains = [c for c in chains if c["chain_type"] == args.chain_type]

    if args.synthetic_depth > 0:
        chains.append(generate_synthetic_chain(args.synthetic_depth))

    mode = "Triad Engine" if args.triad else "Raw baseline"
    print("=" * 70)
    print("Compositional Chaining Benchmark")
    print(f"  Model:    {args.model}")
    print(f"  Provider: {provider}")
    print(f"  Mode:     {mode}")
    print(f"  Filter:   {args.chain_type}")
    print(f"  Chains:   {len(chains)}")
    print(f"  Judge:    {JUDGE_GEMINI_MODEL}")
    print("=" * 70)

    chain_results = []
    for chain in chains:
        result = run_chain(chain, client, args.model, args.triad, cultural_guide, char_map, provider)
        chain_results.append(result)

    summary = compute_summary(chain_results)

    # ── Save results ───────────────────────────────────────────────────────────
    safe_model = args.model.replace(":", "_").replace("/", "_").replace("-", "_")
    suffix = "_triad" if args.triad else "_raw"
    filter_tag = f"_{args.chain_type.lower()}" if args.chain_type != "ALL" else ""
    out_file = RESULTS_DIR / f"chain_benchmark_{safe_model}{suffix}{filter_tag}.json"

    output = {
        "benchmark": "Compositional Chaining Benchmark — Rome 110 CE",
        "model": args.model,
        "mode": mode,
        "judge": JUDGE_GEMINI_MODEL,
        "chain_type_filter": args.chain_type,
        "benchmark_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "chains": chain_results,
    }
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    # ── Print summary ──────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Overall: {summary['total_passed']}/{summary['total_steps']} ({summary['overall_accuracy_pct']}%)")

    print()
    print("By chain type:")
    print(f"  {'Type':<22} {'Score':>8}  {'Pass/Steps':>12}  {'Chains':>7}")
    print("  " + "-" * 54)
    for ct, s in summary["by_chain_type"].items():
        print(f"  {ct:<22} {s['accuracy_pct']:>7.1f}%  {s['passed']}/{s['total']:>8}  {s['chains']:>7}")

    print()
    print("By step depth (drift check — should be flat if guide holds):")
    print(f"  {'Step':<10} {'Accuracy':>10}  {'Pass/Total':>12}")
    print("  " + "-" * 36)
    for sn, s in summary["by_step_depth"].items():
        print(f"  {sn:<10} {s['accuracy_pct']:>9.1f}%  {s['passed']}/{s['total']}")

    print()
    print(f"Results saved to: {out_file}")

    # ── Fault injection summary ────────────────────────────────────────────────
    fault_chains = [cr for cr in chain_results if cr["chain_type"] == "FAULT_INJECTION"]
    if fault_chains:
        print()
        print("Fault injection — error suppression detail:")
        for fc in fault_chains:
            fault_steps = [s for s in fc["steps"] if s.get("fault_injected")]
            post_fault_steps = [
                s for s in fc["steps"]
                if not s.get("fault_injected") and s["step"] > min(
                    (s2["step"] for s2 in fault_steps), default=0
                )
            ]
            fault_pass = sum(1 for s in fault_steps if s["passed"])
            post_pass = sum(1 for s in post_fault_steps if s["passed"])
            print(f"  {fc['chain_id']}: fault step correction {fault_pass}/{len(fault_steps)} | "
                  f"post-fault steps {post_pass}/{len(post_fault_steps)}")


if __name__ == "__main__":
    main()
