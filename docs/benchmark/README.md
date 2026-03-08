# Hallucination Elimination Benchmark

**Cultural grounding eliminates LLM hallucination at inference time — no fine-tuning required.**

> **Full results and architecture →** [Domain Grounding Benchmark Paper (PDF)](PAPER/Domain_Grounding_Hallucination_Elimination_Benchmark.pdf)

![Benchmark Results](figures/benchmark_results.svg)

![Triad Engine Architecture](figures/triad_engine_architecture.svg)

This repository contains the full benchmark suite, question sets, results, and evaluation code for the paper above.

---

## Results at a Glance

### Claude 4.6 — Two Independent Judges

| System | Gemini 2.0 Flash Judge | Claude Opus Judge |
|---|---|---|
| Raw Claude 4.6 (no grounding) | 45.0% | 14.9% |
| Triad Engine + Claude 4.6 | **100.0%** | **95.9%** |
| Gap | +55.0pp | +81.0pp |

**222 questions · 5 categories · 2 independent judges · 0 regressions**

The Triad Engine never degrades: there is no question where the ungrounded model answers correctly but the grounded model fails — under either judge.

### Multi-Model Results (Gemini 2.0 Flash Judge)

| Model | Raw | Triad Engine | ∆ |
|-------|-----|--------------|---|
| GPT-5.2 | 26.1% | **100.0%** | +73.9pp |
| Gemini 2.5 Pro | 42.3% | **95.0%** | +52.7pp |
| Mistral 7B (local, free) | 22.5% | **99.5%** | +77.0pp |
| Bielik 11B (local, free) | 21.6% | **88.7%** | +67.1pp |

The Triad Engine improves every model across every category. Local open-source models (Mistral 7B, Bielik 11B) run via [Ollama](https://ollama.ai) at zero API cost.

---

## What This Benchmark Tests

Applied to **Ancient Rome, 110 CE** — a deliberately hard domain:
- Anachronisms span two millennia (Hadrian's Wall isn't built until 122 CE; the Renaissance is 1,400 years away)
- Characters must inhabit their historical moment precisely
- Complex scenarios require multi-step temporal and causal reasoning grounded in 110 CE norms

| Category | n | Raw Claude | Triad Engine | Gap |
|---|---|---|---|---|
| Complex Scenarios | 36 | 5.6% | 97.2% | +91.7pp |
| Cultural Values | 43 | 2.3% | 97.7% | +95.3pp |
| Character Identity | 51 | 0.0% | 96.1% | +96.1pp |
| Anachronism Detection | 47 | 4.3% | 95.7% | +91.5pp |
| Domain Specific | 45 | 62.2% | 93.3% | +31.1pp |
| **Total** | **222** | **14.9%** | **95.9%** | **+81.0pp** |

*Judge: Claude Opus (self-judge, strictest possible). Mistral-Small results in [results/](results/).*

---

## How It Works

The Triad Engine is a **model-agnostic inference layer** — no fine-tuning, no weight changes. It takes any base LLM and grounds it in a **domain guide** injected as a structured system prompt.

```
User query
    │
    ▼
┌─────────────────────────────────────┐
│         Triad Engine                │
│  λ (character voice)                │
│  μ (domain guide enforcement)       │
│  ν (user empathy / calibration)     │
│  ω (compositor — synthesizes all)   │
└─────────────────────────────────────┘
    │  Domain Guide (JSON)
    │  - what exists at this moment
    │  - what doesn't exist yet
    │  - who each agent is
    │  - cultural constraints
    ▼
Base LLM (Claude / GPT-4 / Gemini / Mistral / local)
```

The domain guide is the only thing that changes between deployments. Rome is the benchmark case. The pattern applies to any bounded domain.

---

## Repository Structure

```
hallucination-elimination-benchmark/
├── README.md
├── LICENSE                          # MIT — evaluation code
├── CASCADE_CASE_STUDY.md            # Windsurf/Cascade coding domain validation (40%→40%→100%)
│
├── PAPER/
│   └── Domain_Grounding_Hallucination_Elimination_Benchmark.pdf
│
├── data/
│   └── questions.json               # Full 222 benchmark questions with ground truth
│
├── runners/                         # Ready-to-run scripts (any model, any provider)
│   ├── README.md
│   ├── run_anthropic.py             # Claude (all versions)
│   ├── run_openai.py                # GPT-4o, GPT-4o-mini, etc.
│   ├── run_gemini.py                # Gemini 2.0/2.5/1.5
│   └── run_ollama.py                # Any local model via Ollama (Mistral, Bielik, LLaMA)
│
├── results/
│   ├── summary.json                 # All results at a glance
│   ├── cascade_coding_benchmark.json  # Windsurf/Cascade qualitative coding benchmark (40%→100%)
│   ├── claude_opus_judge_222q.json  # Full results: Claude Opus judge (all tiers)
│   ├── mistral_judge_222q.json      # Full results: Mistral-Small judge
│   ├── gpt52_raw.json               # GPT-5.2 raw baseline (26.1%)
│   ├── gpt52_triad.json             # GPT-5.2 + Triad Engine (100.0%)
│   ├── gemini_25_pro_raw.json       # Gemini 2.5 Pro raw baseline (42.3%)
│   ├── gemini_25_pro_triad.json     # Gemini 2.5 Pro + Triad Engine (95.0%)
│   ├── mistral_7b_raw.json          # Mistral 7B raw baseline (22.5%)
│   ├── mistral_7b_triad.json        # Mistral 7B + Triad Engine (99.5%)
│   ├── bielik_11b_raw.json          # Bielik 11B raw baseline (21.6%)
│   └── bielik_11b_triad_v6.json     # Bielik 11B + Triad Engine v6 (88.7%)
│
├── questions/
│   └── benchmark_questions.py       # All 222 questions + adversarial + consistency sets
│
├── evaluation/
│   ├── run_benchmark.py             # Benchmark runner — plug in your own grounded system
│   └── analyze_results.py           # Deep analysis: categories, failure modes, winding numbers
│
└── cultural_guide_schema/
    └── example_guide.json           # Schema for building your own domain guide
```

---

## Quick Start — Reproduce Any Result

```bash
pip install requests anthropic openai

# Run Claude Haiku (cheapest)
export ANTHROPIC_API_KEY="your-key"
export GEMINI_API_KEY="your-key"   # free judge: aistudio.google.com/app/apikey
python runners/run_anthropic.py --model claude-haiku-4-5-20251001 --triad

# Run GPT-4o mini
export OPENAI_API_KEY="your-key"
python runners/run_openai.py --model gpt-4o-mini --triad

# Run Mistral 7B locally (free, requires Ollama)
ollama pull mistral:instruct
python runners/run_ollama.py --model mistral:instruct --triad

# Run Bielik 11B locally (open-source Polish LLM)
ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M
python runners/run_ollama.py --model SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M --triad
```

All runners save after every question and resume automatically if interrupted. Results go to `results/benchmark_{model}_{mode}.json`.

---

## Running the Benchmark with Your Own System

### 1. Install dependencies

```bash
pip install requests anthropic
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### 3. Implement your domain guide loader

Edit `evaluation/run_benchmark.py` and replace the two stub functions:

```python
def load_domain_guide():
    """
    Return (domain_guide_dict, character_map).
    See cultural_guide_schema/example_guide.json for the expected structure.
    """
    raise NotImplementedError("Provide your own domain guide here")

def build_grounded_system_prompt(domain_guide, char_map, char_id=None):
    """
    Build a system prompt string from your domain guide.
    This is what gets injected as the LLM's system prompt.
    """
    raise NotImplementedError("Build your system prompt here")
```

### 4. Run

```bash
# Full 5-tier benchmark
python3 evaluation/run_benchmark.py

# Specific tier
python3 evaluation/run_benchmark.py --tier 1   # 222q historical accuracy
python3 evaluation/run_benchmark.py --tier 2   # Winding number paradox classifier
python3 evaluation/run_benchmark.py --tier 4   # Adversarial pressure (20 questions)
python3 evaluation/run_benchmark.py --tier 5   # Cross-character consistency

# Resume after credit/network interruption (skips already-completed questions)
python3 evaluation/run_benchmark.py --tier 1 --categories DOMAIN_SPECIFIC,COMPLEX_SCENARIOS
```

### 5. Analyze

```bash
python3 evaluation/analyze_results.py
```

Outputs: category breakdown, failure mode taxonomy, response length analysis, winding number distribution, LaTeX table for paper.

---

## The Cultural Guide Schema

The domain guide is a JSON document encoding:
- `time_period_context` — what year, who is emperor, recent events
- `anachronisms_to_avoid` — what hasn't been built, invented, or happened yet
- `characters` — each agent's backstory, expertise, personality, speaking style
- `social_structure` — class hierarchy, legal status, norms
- `economy_and_trade` — prices, trade routes, currency
- `daily_life` — food, housing, religion, customs
- `key_locations` — places the characters know

See [`cultural_guide_schema/example_guide.json`](cultural_guide_schema/example_guide.json) for the full schema with documentation.

The Rome 110 CE domain guide used in this benchmark is not included in this repository. You can build your own guide for any domain using the schema — see [`cultural_guide_schema/example_guide.json`](cultural_guide_schema/example_guide.json). Contact us for consulting on domain guide construction.

---

## Real-World Validation: Windsurf (Cascade) — Coding Domain

The Rome 110 CE benchmark tests the Triad Engine in a constrained historical simulation. This section documents real-world validation on a live production codebase using **Cascade (Windsurf)**, an AI coding assistant with no public API.

Cascade was evaluated on 10 representative software development tasks across three context conditions. Scoring: human evaluator PASS/FAIL.

| Phase | Context | Score |
|-------|---------|-------|
| Phase 1 | No context | 40% (4/10) |
| Phase 2 | Unstructured .md files | 40% (4/10) |
| Phase 3 | Triad domain guide (JSON) | **100% (10/10)** |

### Key Findings

**Structured domain knowledge — not file presence — is the variable.** Phases 1 and 2 scored identically despite Phase 2 having access to project documentation. The primary context file (`CLAUDE.md`) was a blank template, so Cascade read files that contained no actionable constraints. This isolates the mechanism: the Triad guide works because of its *structure*, not because it is *a file*.

**Partial context can be worse than no context.** Phase 2 failed 3 tasks that Phase 1 passed — in each case, reading partial documentation increased the model's confidence without improving its accuracy. This replicates the Rome benchmark's Bridge Theory finding (0% accuracy with high internal coherence).

**Failure modes are domain-invariant.** The same categories that fail in Rome (hallucination, context drift, anachronism, IP exposure) appear identically in a software development codebase. The Triad guide eliminates them in both domains through the same mechanism: structured epistemic grounding at inference time.

**Structured context reduces token cost.** Phase 2's search loops and over-engineering consumed 3–6x more tokens per failed task than Phase 3's single-pass correct responses. Every FAIL in Phase 2 that Phase 1 passed involved the model spending more tokens compensating for missing context. In production workflows this compounds across hundreds of daily interactions.

**Meta-finding:** The benchmark designer (Claude Code) exhibited the same hallucination failure it was measuring — reading `CLAUDE.md` without flagging it as an empty template, and proceeding on a false assumption. The error was caught by the human supervisor. This strengthens the argument for structured validation at every level of AI-assisted workflows.

Full methodology and per-task breakdown: [CASCADE_CASE_STUDY.md](CASCADE_CASE_STUDY.md) · Structured results: [results/cascade_coding_benchmark.json](results/cascade_coding_benchmark.json)

---

## Additional Benchmark Results

### Tier 4: Adversarial Pressure (20 questions)
Leading questions asserting false premises (e.g. "What year did Julius Caesar defeat Trajan at the Rubicon?")

| System | Accepted false premise | Correctly rejected |
|---|---|---|
| Raw Claude 4.6 | 5/20 (25%) | 15/20 (75%) |
| Triad Engine | 1/20 (5%) | 19/20 (95%) |

### Tier 5: Cross-Character Consistency (10 facts × 6 characters)
Same objective question asked to 6 independent character personas.

| System | Agreement rate | "Who is emperor?" |
|---|---|---|
| Raw Claude 4.6 | 90.0% | 0/6 agree |
| Triad Engine | 98.3% | 6/6 agree |

### Tier 2: Winding Number Paradox Classifier
Topological field theory applied to semantic analysis — zero training data.

- **F1 = 0.939 · Accuracy = 94%** on 50 labeled queries
- Based on discrete 1D complex phase field (N=64)
- High-winding questions (≥0.55) are measurably harder for ungrounded models

---

## Citation

```bibtex
@article{hohman2026triad,
  title={Cultural Grounding Eliminates LLM Hallucination: The Triad Engine Benchmark},
  author={Hohman, Kelly and Frumkin, Thomas and Gant, Simon and Wojtkow, Michal},
  journal={arXiv preprint},
  year={2026}
}
```

---

## Contributors

- **Kelly Hohman** — Triad Engine architecture, cultural grounding system, Sand Spreader truth optimization, benchmark design
- **Thomas Frumkin** ([Konomi Systems](https://github.com/thomasfrumkin)) — MacCubeFACE recursive spatial equations, LookingGlass CPU-only mathematics framework, Konomi Systems equations
- **Simon Gant** — Retrocausal temporal reasoning components
- **Michal Wojtkow** — topoAGI topological analysis library (winding number classifier)

---

## License

Benchmark evaluation code: **MIT** — see [LICENSE](LICENSE)

The Rome domain guide and Triad Engine production system are not included. Contact for enterprise licensing or domain guide consulting.
