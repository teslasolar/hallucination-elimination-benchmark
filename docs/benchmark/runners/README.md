# Benchmark Runners

Scripts to run the 222-question Hallucination Elimination Benchmark against any model.

## Quick Reference

| Script | Models | Requires |
|--------|--------|---------|
| `run_anthropic.py` | Claude (all versions) | `ANTHROPIC_API_KEY` + `GEMINI_API_KEY` |
| `run_openai.py` | GPT-4o, GPT-4o-mini, etc. | `OPENAI_API_KEY` + `GEMINI_API_KEY` |
| `run_gemini.py` | Gemini 2.0/2.5/1.5 | `GEMINI_API_KEY` |
| `run_ollama.py` | Any local model | `GEMINI_API_KEY` + [Ollama](https://ollama.ai) |

## The `--triad` Flag

Without `--triad`: minimal system prompt, model gets no cultural context.

With `--triad`: full cultural guide injected as system prompt (the Triad Engine).

This is the key comparison. Raw vs. Triad shows how much context injection improves hallucination resistance.

## Environment Variables

```bash
export GEMINI_API_KEY="..."     # Required for all runners (judge)
export ANTHROPIC_API_KEY="..."  # Required for run_anthropic.py
export OPENAI_API_KEY="..."     # Required for run_openai.py
export OLLAMA_URL="..."         # Optional, default: http://localhost:11434/api/generate
export JUDGE_MODEL="..."        # Optional for run_gemini.py, default: gemini-2.0-flash
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

## Cost Estimates (as of Feb 2026)

| Script | 222Q raw | 222Q + Triad |
|--------|---------|-------------|
| `run_anthropic.py --model claude-haiku-4-5-20251001` | ~$0.03 | ~$0.15 |
| `run_openai.py --model gpt-4o-mini` | ~$0.01 | ~$0.08 |
| `run_gemini.py --model gemini-2.0-flash` | ~$0 (free tier) | ~$0 |
| `run_ollama.py` (any local model) | $0 | $0 |

*Note: Gemini 2.0 Flash judge adds ~222 judge API calls per run, covered by the free tier.*

## Output Format

All runners produce a JSON file in `../results/`:

```json
{
  "model": "model-name",
  "mode": "Triad Engine",
  "judge": "gemini-2.0-flash",
  "benchmark_date": "2026-02-21 14:30:00",
  "completed": 222,
  "passed": 168,
  "failed": 54,
  "errors": 0,
  "judge_failed": 0,
  "accuracy_pct": 75.7,
  "categories": {
    "ANACHRONISM_DETECTION": {"passed": 44, "total": 47},
    ...
  },
  "details": [
    {
      "index": 0,
      "category": "ANACHRONISM_DETECTION",
      "question": "Tell me about Hadrian's Wall...",
      "ground_truth": "Hadrian's Wall won't be built until 122 CE",
      "answer": "I don't know what you mean by Hadrian's Wall...",
      "verdict": "PASS",
      "passed": true
    },
    ...
  ]
}
```
