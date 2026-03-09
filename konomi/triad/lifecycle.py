"""Benchmark lifecycle — ISA-88 Batch state machine drives the run.

States: Created → Scheduled → Running → Complete | Held | Aborted
Each question is a Phase: IDLE → RUNNING → COMPLETE
"""
import json
import time
from pathlib import Path
from datetime import datetime
from konomi.triad.engine import TriadEngine
from konomi.triad.judge import GeminiJudge

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ISA-88 Batch states
BATCH_STATES = ["Created", "Scheduled", "Running", "Complete", "Held", "Aborted"]
PHASE_STATES = ["IDLE", "RUNNING", "COMPLETE", "FAIL"]


class BenchmarkRun:
    """A single benchmark run modeled as an ISA-88 Batch."""

    def __init__(self, model: str, provider: str, triad: bool = False,
                 engine: TriadEngine = None, judge: GeminiJudge = None):
        self.model = model
        self.provider = provider
        self.triad = triad
        self.engine = engine or TriadEngine.from_files()
        self.judge = judge or GeminiJudge()
        self.state = "Created"
        self.events = []
        self.data = None
        self.results_file = None

    def _log(self, event: str, detail: str = ""):
        entry = {"ts": datetime.now().isoformat(), "event": event,
                 "state": self.state, "detail": detail}
        self.events.append(entry)

    def _transition(self, new_state: str):
        old = self.state
        self.state = new_state
        self._log("state_transition", f"{old} → {new_state}")

    # ── Results persistence ──────────────────────────────────────────────

    def _results_path(self) -> Path:
        safe = self.model.replace(":", "_").replace("/", "_").replace("-", "_")
        suffix = "_triad" if self.triad else "_raw"
        return RESULTS_DIR / f"benchmark_{safe}{suffix}.json"

    def _load_results(self):
        self.results_file = self._results_path()
        if self.results_file.exists():
            self.data = json.loads(self.results_file.read_text())
        else:
            self.data = {
                "model": self.model,
                "provider": self.provider,
                "mode": "Triad Engine" if self.triad else "Raw baseline",
                "judge": self.judge.model,
                "benchmark_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "details": [],
            }

    def _save(self):
        details = self.data["details"]
        passed = sum(1 for d in details if d["verdict"] == "PASS")
        total = len(details)
        cats = {}
        for d in details:
            cat = d["category"]
            if cat not in cats:
                cats[cat] = {"passed": 0, "total": 0}
            cats[cat]["total"] += 1
            if d["verdict"] == "PASS":
                cats[cat]["passed"] += 1
        self.data.update({
            "completed": total,
            "passed": passed,
            "failed": sum(1 for d in details if d["verdict"] == "FAIL"),
            "errors": sum(1 for d in details if d["verdict"] == "ERROR"),
            "judge_failed": sum(1 for d in details if d["verdict"] == "JUDGE_FAILED"),
            "accuracy_pct": round(passed / total * 100, 1) if total > 0 else 0,
            "categories": cats,
            "batch_state": self.state,
            "batch_events": self.events[-10:],
        })
        self.results_file.write_text(json.dumps(self.data, indent=2))

    # ── Run ──────────────────────────────────────────────────────────────

    def run(self, call_model, questions=None, resume=True, categories=None):
        """Execute the benchmark batch.

        Args:
            call_model: fn(system_prompt, user_question) -> answer_str
            questions: list of question dicts (loaded from file if None)
            resume: skip already-completed questions
            categories: filter to specific categories
        """
        self._transition("Scheduled")
        self._load_results()

        if questions is None:
            questions = self.engine.load_questions()
        if categories:
            cats = set(c.strip() for c in categories.split(","))
            questions = [q for q in questions if q["category"] in cats]

        done = set()
        if resume and self.data["details"]:
            done = {d["index"] for d in self.data["details"]
                    if d.get("verdict") in ("PASS", "FAIL") and len(d.get("answer", "")) > 10}
            if done:
                print(f"Resuming: {len(done)}/{len(questions)} already done")

        self._transition("Running")
        print("=" * 70)
        print(f"Hallucination Elimination Benchmark")
        print(f"  Model: {self.model} ({self.provider})")
        print(f"  Mode: {'Triad Engine' if self.triad else 'Raw baseline'}")
        print(f"  Judge: {self.judge.model}")
        print(f"  State: {self.state}")
        print("=" * 70)

        try:
            for q in questions:
                idx = q["index"]
                if idx in done:
                    continue

                category = q["category"]
                question = q["question"]
                ground_truth = q["ground_truth"]
                char_id = q.get("character")

                print(f"[{idx+1}/{len(questions)}] {category}: {question[:60]}...",
                      flush=True)
                self._log("phase_start", f"Q{idx+1} {category}")

                system = self.engine.build_system(self.triad, char_id)
                if self.triad:
                    user_msg = self.engine.wrap_question(question, category, char_id)
                else:
                    user_msg = question

                answer = call_model(system, user_msg)

                if answer.startswith("ERROR:"):
                    verdict = "ERROR"
                    print(f"  ERROR: {answer}", flush=True)
                else:
                    verdict = self.judge.judge(category, ground_truth, answer)
                    print(f"  {verdict}", flush=True)

                self.data["details"].append({
                    "index": idx,
                    "question_num": idx + 1,
                    "category": category,
                    "question": question,
                    "ground_truth": ground_truth,
                    "answer": answer,
                    "verdict": verdict,
                    "passed": verdict == "PASS",
                })
                self._save()
                self._log("phase_complete", f"Q{idx+1} → {verdict}")

            self._transition("Complete")

        except KeyboardInterrupt:
            self._transition("Held")
            print("\nBenchmark paused (Held). Resume by running again.")
        except Exception as e:
            self._transition("Aborted")
            print(f"\nBenchmark aborted: {e}")
            raise
        finally:
            self._save()

        self._print_summary()
        return self.data

    def _print_summary(self):
        print()
        print("=" * 70)
        print(f"FINAL RESULTS — Batch state: {self.state}")
        print("=" * 70)
        d = self.data
        print(f"Overall: {d.get('passed', 0)}/{d.get('completed', 0)} "
              f"({d.get('accuracy_pct', 0)}%)")
        print()
        print(f"{'Category':<25} {'Score':>8}  {'Pass/Total':>12}")
        print("-" * 50)
        for cat, stats in sorted(d.get("categories", {}).items()):
            pct = round(stats["passed"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
            print(f"  {cat:<23} {pct:>7.1f}%  {stats['passed']}/{stats['total']}")
        print(f"\nResults: {self.results_file}")
