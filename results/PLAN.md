# PLAN.md — results/
## Benchmark Results
STATUS:stable|FILES:14|SIZE:900K

### Files
```
summary.json                    2.9K  all results at a glance
claude_opus_judge_222q.json     403K  full 222q results (Opus judge, all tiers)
mistral_judge_222q.json         431K  full 222q results (Mistral-Small judge)

Model Baselines (raw, no grounding):
  gpt52_raw.json                790B  GPT-5.2: 26.1%
  gemini_25_pro_raw.json        791B  Gemini 2.5 Pro: 42.3%
  mistral_7b_raw.json           802B  Mistral 7B: 22.5%
  bielik_11b_raw.json           18K   Bielik 11B: 21.6%
  claude_sonnet_raw.json        924B  Claude Sonnet: 45.0%

Triad Engine Results:
  gpt52_triad.json              879B  GPT-5.2: 100.0%
  gemini_25_pro_triad.json      877B  Gemini 2.5 Pro: 95.0%
  mistral_7b_triad.json         959B  Mistral 7B: 99.5%
  bielik_11b_triad_v6.json      18K   Bielik 11B: 88.7%
  claude_sonnet_triad.json      922B  Claude Sonnet: 100.0% (Gemini judge)

Other:
  cascade_coding_benchmark.json 6.5K  Windsurf/Cascade coding domain (40%→100%)
```

### Result Schema (per-model)
```json
{
  "model": str,
  "mode": "Triad Engine"|"Raw baseline",
  "judge": str,
  "completed": int,
  "passed": int,
  "accuracy_pct": float,
  "categories": {str: {"passed": int, "total": int}},
  "details": [{
    "index": int, "category": str, "question": str,
    "ground_truth": str, "answer": str,
    "verdict": "PASS"|"FAIL"|"ERROR", "passed": bool
  }]
}
```

### Key Findings
```
Triad never degrades: 0 regressions (no question where raw correct but triad fails)
Best: GPT-5.2 + Triad = 100% (222/222)
Worst: Bielik 11B + Triad = 88.7% (COMPLEX_SCENARIOS hardest at 58.3%)
Biggest gap: Character Identity — Raw 0% → Triad 96.1% (+96.1pp)
```
