# PLAN.md — runners/
## Legacy Per-Provider Runners
STATUS:legacy|FILES:6|SIZE:82K|REFACTORED→konomi/triad/

### Files
```
run_anthropic.py   15K  375 lines  Claude (all versions)
run_openai.py      15K  373 lines  GPT-4o, GPT-5.2
run_gemini.py      16K  388 lines  Gemini 2.0/2.5/1.5
run_ollama.py      16K  397 lines  Local models via Ollama
run_perplexity.py  17K  397 lines  Sonar, Sonar-Pro
README.md          2.5K 79 lines   quick reference
```

### Shared Code (duplicated across all 5)
```
load_data()                    → konomi/triad/engine.py:TriadEngine.from_files()
build_triad_system()           → konomi/triad/engine.py:TriadEngine._build_triad()
build_raw_system()             → konomi/triad/engine.py:TriadEngine._build_raw()
wrap_question()                → konomi/triad/engine.py:TriadEngine.wrap_question()
JUDGE_PROMPT + gemini_judge()  → konomi/triad/judge.py:GeminiJudge
save_results() + load_results()→ konomi/triad/lifecycle.py:BenchmarkRun._save()
main() loop                    → konomi/triad/lifecycle.py:BenchmarkRun.run()
```

### Only Unique Code Per Runner
```
call_anthropic()   25 lines  → konomi/triad/providers/anthropic.py
call_openai()      25 lines  → konomi/triad/providers/openai.py
call_gemini()      30 lines  → konomi/triad/providers/gemini.py
call_ollama()      15 lines  → konomi/triad/providers/ollama.py
call_perplexity()  25 lines  → konomi/triad/providers/perplexity.py
```

### Recommended
```
# Instead of:
python runners/run_anthropic.py --model claude-haiku-4-5-20251001 --triad

# Use:
python -m konomi.triad.run --provider anthropic --model claude-haiku-4-5-20251001 --triad
```

### Notes
- Legacy runners still work, not removed for backward compat
- Consider removing once unified runner proven in production
