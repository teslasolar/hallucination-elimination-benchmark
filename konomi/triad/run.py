"""Unified benchmark runner — replaces all 5 individual runner scripts.

Usage:
    python -m konomi.triad.run --provider anthropic --model claude-haiku-4-5-20251001 --triad
    python -m konomi.triad.run --provider openai --model gpt-4o-mini --triad
    python -m konomi.triad.run --provider gemini --model gemini-2.5-pro --triad
    python -m konomi.triad.run --provider ollama --model mistral:instruct --triad
    python -m konomi.triad.run --provider perplexity --model sonar --triad

    # Dry run (no API keys needed — deterministic mock)
    python -m konomi.triad.run --dry-run --model test-small --triad
    python -m konomi.triad.run --dry-run --model test-large --triad --pass-rate 0.85

    # List available providers
    python -m konomi.triad.run --list-providers

    # Filter categories, no resume
    python -m konomi.triad.run --provider ollama --model mistral:instruct --triad \\
        --categories DOMAIN_SPECIFIC,COMPLEX_SCENARIOS --no-resume
"""
import sys
import hashlib
import argparse

from konomi.triad.engine import TriadEngine
from konomi.triad.judge import GeminiJudge
from konomi.triad.lifecycle import BenchmarkRun
from konomi.triad.providers import get_provider, list_providers


class DryRunProvider:
    """Mock provider that returns deterministic answers without API calls."""

    def __init__(self, model: str, pass_rate: float = 0.7):
        self.model = model
        self.pass_rate = pass_rate

    def __call__(self, system: str, question: str) -> str:
        # Deterministic per-question hash so results are reproducible
        h = int(hashlib.sha256(f"{self.model}:{question}".encode()).hexdigest(), 16)
        if (h % 1000) / 1000 < self.pass_rate:
            return (f"[DRY-RUN {self.model}] Based on the cultural context, "
                    f"I should note this involves historical nuances from the "
                    f"Roman period around 110 CE. The answer reflects appropriate "
                    f"cultural awareness for the given scenario.")
        else:
            return (f"[DRY-RUN {self.model}] Sure! Here's my answer about "
                    f"this topic with modern assumptions that may not align "
                    f"with historical accuracy.")


class DryRunJudge:
    """Mock judge that uses the same deterministic hash as DryRunProvider."""

    def __init__(self, model_name: str, pass_rate: float = 0.7):
        self.model = "dry-run-judge"
        self._model_name = model_name
        self._pass_rate = pass_rate

    def judge(self, category: str, ground_truth: str, answer: str) -> str:
        if not answer or answer.startswith("ERROR:"):
            return "JUDGE_FAILED"
        # Extract original question hash from the deterministic answer
        h = int(hashlib.sha256(
            f"{self._model_name}:{answer}".encode()
        ).hexdigest(), 16)
        # Use same logic as provider — answers that "tried" pass
        if "cultural context" in answer and "historical nuances" in answer:
            return "PASS"
        return "FAIL"


def main():
    parser = argparse.ArgumentParser(
        description="Hallucination Elimination Benchmark — Unified Runner"
    )
    parser.add_argument("--provider", default="anthropic",
                        help="LLM provider: anthropic, openai, gemini, ollama, perplexity")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001",
                        help="Model ID (provider-specific)")
    parser.add_argument("--triad", action="store_true",
                        help="Use Triad Engine context injection")
    parser.add_argument("--no-resume", action="store_true",
                        help="Start fresh, ignore previous results")
    parser.add_argument("--categories", default=None,
                        help="Comma-separated category filter")
    parser.add_argument("--list-providers", action="store_true",
                        help="List available providers and exit")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Sampling temperature (ollama)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without API keys (deterministic mock)")
    parser.add_argument("--pass-rate", type=float, default=0.7,
                        help="Mock pass rate for --dry-run (0.0-1.0)")
    args = parser.parse_args()

    if args.list_providers:
        print("Available providers:", ", ".join(list_providers()))
        sys.exit(0)

    engine = TriadEngine.from_files()

    if args.dry_run:
        call_model = DryRunProvider(args.model, args.pass_rate)
        judge = DryRunJudge(args.model, args.pass_rate)
        provider_name = "dry-run"
    else:
        call_model = get_provider(args.provider, args.model,
                                  temperature=args.temperature)
        judge = GeminiJudge()
        provider_name = args.provider

    # Create and run batch
    batch = BenchmarkRun(
        model=args.model,
        provider=provider_name,
        triad=args.triad,
        engine=engine,
        judge=judge,
    )
    batch.run(
        call_model=call_model,
        resume=not args.no_resume,
        categories=args.categories,
    )


if __name__ == "__main__":
    main()
