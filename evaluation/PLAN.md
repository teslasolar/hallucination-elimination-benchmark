# PLAN.md — evaluation/
## Legacy Evaluation Framework
STATUS:legacy|FILES:2|SIZE:37K|REFACTORED→konomi/triad/

### Files
```
run_benchmark.py      25K  multi-tier framework (T1,T2,T4 — T5 stub)
analyze_results.py    12K  offline analysis (no API needed)
```

### run_benchmark.py
```
Tier 1: 222q Raw vs Grounded (Claude Opus judge)
  → STUB: load_domain_guide() + build_grounded_system_prompt()
  → Users must implement these for their domain
Tier 2: Winding number paradox classifier (no API)
  → REFACTORED to konomi/triad/winding.py
Tier 4: 20 adversarial false-premise questions
  → REFACTORED to konomi/triad/adversarial.py
Tier 5: Cross-character consistency (stub, not implemented)
```

### analyze_results.py
```
Reads: benchmark_claude_vs_triad_results.json
Outputs: category breakdown, failure taxonomy, winding distribution,
         response length analysis, arXiv LaTeX table
→ REFACTORED to konomi/triad/analyze.py
```

### Refactor Status
```
compute_winding()         → konomi/triad/winding.py
ADVERSARIAL_QUERIES       → konomi/triad/adversarial.py
category analysis         → konomi/triad/analyze.py
run_tier1() framework     → konomi/triad/lifecycle.py (BenchmarkRun)
call_claude/claude_judge  → konomi/triad/providers/ + judge.py
```

### Notes
- These files still work standalone for users who want the template
- Recommended: use `python -m konomi.triad.run` instead
