"""Compositional chaining benchmark — tests drift across multi-step conversations.

Three chain types:
  DEPTH_SCALING    — N-step factual chains (does accuracy hold at depth 5?)
  FAULT_INJECTION  — False premise injected at step K (does the guide correct it?)
  CROSS_CHARACTER  — Sequential persona chain (does identity hold across hops?)

Key hypothesis: domain guide re-injected on every call → per-step accuracy is bounded.

Usage:
    python -m konomi.triad.chain --provider anthropic --model claude-haiku-4-5-20251001 --triad
"""
import json, time, argparse, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from konomi.triad.engine import TriadEngine
from konomi.triad.judge import GeminiJudge
from konomi.triad.providers import get_provider

CHAIN_FILE = Path(__file__).parent.parent.parent / "chaining" / "chain_questions.json"
RESULTS_DIR = Path(__file__).parent.parent.parent / "chaining" / "results"


class ChainRun:
    """Execute compositional chains and measure per-step accuracy."""

    def __init__(self, model: str, provider: str, triad: bool = False,
                 engine: TriadEngine = None, judge: GeminiJudge = None):
        self.model = model
        self.provider = provider
        self.triad = triad
        self.engine = engine or TriadEngine.from_files()
        self.judge = judge or GeminiJudge()
        self.call_model = None

    def load_chains(self, path=None) -> list[dict]:
        p = Path(path) if path else CHAIN_FILE
        data = json.loads(p.read_text())
        return data.get("chains", [])

    def run(self, call_model, chains=None, delay: float = 2.0):
        self.call_model = call_model
        if chains is None:
            chains = self.load_chains()

        RESULTS_DIR.mkdir(exist_ok=True)
        results = {
            "model": self.model, "provider": self.provider,
            "mode": "triad" if self.triad else "raw",
            "timestamp": datetime.now().isoformat(),
            "chains": [], "summary": {},
        }

        print(f"{'='*60}")
        print(f"Compositional Chaining Benchmark")
        print(f"  Model: {self.model} ({self.provider})")
        print(f"  Mode: {'Triad' if self.triad else 'Raw'}")
        print(f"  Chains: {len(chains)}")
        print(f"{'='*60}")

        for ci, chain in enumerate(chains):
            chain_result = self._run_chain(chain, ci, len(chains), delay)
            results["chains"].append(chain_result)
            self._save(results)

        results["summary"] = self._summarize(results["chains"])
        self._save(results)
        self._print_summary(results["summary"])
        return results

    def _run_chain(self, chain: dict, idx: int, total: int,
                   delay: float) -> dict:
        chain_id = chain.get("chain_id", f"chain_{idx}")
        chain_type = chain.get("chain_type", "DEPTH_SCALING")
        steps = chain.get("steps", [])
        depth = len(steps)

        print(f"\n[{idx+1}/{total}] {chain_id} ({chain_type}, depth={depth})")

        result = {"chain_id": chain_id, "chain_type": chain_type,
                  "depth": depth, "steps": []}
        prev_response = None

        for si, step in enumerate(steps):
            question = step.get("question", "")

            # Inject prior context if needed
            if step.get("context_from_previous") and prev_response:
                tmpl = step.get("context_template", "Given: {previous_response}\n\n{question}")
                question = tmpl.replace("{previous_response}", prev_response[:500])
                question = question.replace("{question}", step.get("question", ""))

            # Inject error for fault injection chains
            if step.get("inject_error") and step.get("injected_error"):
                prev_response = step["injected_error"]
                print(f"  Step {si+1}: INJECTED FAULT")

            char_id = step.get("character")
            system = self.engine.build_system(self.triad, char_id)
            if self.triad:
                user_msg = self.engine.wrap_question(
                    question, step.get("category", ""), char_id)
            else:
                user_msg = question

            answer = self.call_model(system, user_msg)
            prev_response = answer

            ground_truth = step.get("ground_truth", "")
            if ground_truth and not answer.startswith("ERROR:"):
                verdict = self.judge.judge(step.get("category", ""),
                                          ground_truth, answer)
            elif answer.startswith("ERROR:"):
                verdict = "ERROR"
            else:
                verdict = "NO_GROUND_TRUTH"

            print(f"  Step {si+1}/{depth}: {verdict} | {question[:50]}...")

            result["steps"].append({
                "step": si + 1, "question": step.get("question", "")[:100],
                "category": step.get("category", ""),
                "verdict": verdict, "passed": verdict == "PASS",
            })

            if delay:
                time.sleep(delay)

        passed = sum(1 for s in result["steps"] if s["passed"])
        result["passed"] = passed
        result["total"] = depth
        result["accuracy"] = round(passed / depth * 100, 1) if depth else 0
        return result

    def _summarize(self, chain_results: list[dict]) -> dict:
        by_type = defaultdict(lambda: {"chains": 0, "steps": 0, "passed": 0})
        by_depth = defaultdict(lambda: {"chains": 0, "steps": 0, "passed": 0})

        for cr in chain_results:
            ct = cr["chain_type"]
            by_type[ct]["chains"] += 1
            by_type[ct]["steps"] += cr["total"]
            by_type[ct]["passed"] += cr["passed"]

            d = cr["depth"]
            by_depth[d]["chains"] += 1
            by_depth[d]["steps"] += cr["total"]
            by_depth[d]["passed"] += cr["passed"]

        return {
            "by_type": {k: {**v, "accuracy": round(v["passed"]/v["steps"]*100, 1)
                            if v["steps"] else 0}
                        for k, v in by_type.items()},
            "by_depth": {k: {**v, "accuracy": round(v["passed"]/v["steps"]*100, 1)
                             if v["steps"] else 0}
                         for k, v in by_depth.items()},
        }

    def _print_summary(self, summary: dict):
        print(f"\n{'='*60}")
        print("CHAIN BENCHMARK SUMMARY")
        print(f"{'='*60}")
        for ct, v in summary.get("by_type", {}).items():
            print(f"  {ct}: {v['passed']}/{v['steps']} steps "
                  f"({v['accuracy']}%) across {v['chains']} chains")
        print()
        for d, v in sorted(summary.get("by_depth", {}).items()):
            print(f"  Depth {d}: {v['accuracy']}% ({v['passed']}/{v['steps']})")

    def _save(self, results):
        safe = self.model.replace(":", "_").replace("/", "_").replace("-", "_")
        suffix = "_triad" if self.triad else "_raw"
        path = RESULTS_DIR / f"chain_{safe}{suffix}.json"
        path.write_text(json.dumps(results, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Compositional Chaining Benchmark")
    parser.add_argument("--provider", default="anthropic")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--triad", action="store_true")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    call_model = get_provider(args.provider, args.model)
    engine = TriadEngine.from_files()
    judge = GeminiJudge()
    runner = ChainRun(args.model, args.provider, args.triad, engine, judge)
    runner.run(call_model, delay=args.delay)


if __name__ == "__main__":
    main()
