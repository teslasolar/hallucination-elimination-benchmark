# Benchmark Runners (Deprecated)

> **These scripts have been removed.** Use the unified runner instead.

## Unified Runner

```bash
# Instead of: python runners/run_anthropic.py --model claude-haiku-4-5-20251001 --triad
python -m konomi.triad.run --provider anthropic --model claude-haiku-4-5-20251001 --triad

# Instead of: python runners/run_openai.py --model gpt-4o --triad
python -m konomi.triad.run --provider openai --model gpt-4o --triad

# Instead of: python runners/run_gemini.py --model gemini-2.0-flash --triad
python -m konomi.triad.run --provider gemini --model gemini-2.0-flash --triad

# Instead of: python runners/run_ollama.py --model mistral:instruct --triad
python -m konomi.triad.run --provider ollama --model mistral:instruct --triad

# List all providers:
python -m konomi.triad.run --list-providers
```

## Environment Variables

```bash
export GEMINI_API_KEY="..."     # Required for judge (all providers)
export ANTHROPIC_API_KEY="..."  # Required for --provider anthropic
export OPENAI_API_KEY="..."     # Required for --provider openai
```

## Why Removed

The 5 legacy per-provider scripts shared ~1,500 lines of duplicated code
(prompt construction, judge calls, result saving, main loop). The unified
runner in `konomi/triad/` eliminates this duplication:

- `konomi/triad/engine.py` — prompt construction
- `konomi/triad/judge.py` — Gemini judge
- `konomi/triad/lifecycle.py` — ISA-88 batch state machine
- `konomi/triad/providers/` — thin API adapters (20-35 lines each)
- `konomi/triad/run.py` — unified CLI
