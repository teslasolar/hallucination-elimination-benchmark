"""Unified benchmark runner — replaces all 5 individual runner scripts.

Usage:
    python -m konomi.triad.run --provider anthropic --model claude-haiku-4-5-20251001 --triad
    python -m konomi.triad.run --provider openai --model gpt-4o-mini --triad
    python -m konomi.triad.run --provider gemini --model gemini-2.5-pro --triad
    python -m konomi.triad.run --provider ollama --model mistral:instruct --triad
    python -m konomi.triad.run --provider perplexity --model sonar --triad

    # List available providers
    python -m konomi.triad.run --list-providers

    # Filter categories, no resume
    python -m konomi.triad.run --provider ollama --model mistral:instruct --triad \\
        --categories DOMAIN_SPECIFIC,COMPLEX_SCENARIOS --no-resume
"""
import sys
import argparse

from konomi.triad.engine import TriadEngine
from konomi.triad.judge import GeminiJudge
from konomi.triad.lifecycle import BenchmarkRun
from konomi.triad.providers import get_provider, list_providers


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
    args = parser.parse_args()

    if args.list_providers:
        print("Available providers:", ", ".join(list_providers()))
        sys.exit(0)

    # Build components
    call_model = get_provider(args.provider, args.model,
                              temperature=args.temperature)
    engine = TriadEngine.from_files()
    judge = GeminiJudge()

    # Create and run batch
    batch = BenchmarkRun(
        model=args.model,
        provider=args.provider,
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
