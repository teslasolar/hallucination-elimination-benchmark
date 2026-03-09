# Hallucination Elimination Benchmark

**Cultural grounding eliminates LLM hallucination at inference time — no fine-tuning required.**

> **Full results and architecture →** [Domain Grounding Benchmark Paper (PDF)](PAPER/Domain_Grounding_Hallucination_Elimination_Benchmark.pdf)

![Benchmark Results](figures/benchmark_results.svg)

![Triad Engine Architecture](figures/triad_engine_architecture.svg)

This repository contains the full benchmark suite, question sets, results, evaluation code, and the **KONOMI Standard** — a self-defining industrial standards compression system where UDTs define UDTs and tags drive behavior.

> **This README is executable.** UDT tags embedded in HTML comments let you run, test, validate, and crosswalk directly from this file. See [Executable README](#executable-readme) below.

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
├── README.md                        ← YOU ARE HERE (executable)
├── LICENSE                          # MIT — evaluation code
├── CASCADE_CASE_STUDY.md            # Windsurf/Cascade coding domain validation
│
├── PAPER/
│   └── Domain_Grounding_...pdf      # Full research paper
│
├── data/
│   └── questions.json               # 222 benchmark questions with ground truth
│
├── runners/                         # Ready-to-run model scripts
│   ├── run_anthropic.py             # Claude (all versions)
│   ├── run_openai.py                # GPT-4o, GPT-5.2
│   ├── run_gemini.py                # Gemini 2.0/2.5/1.5
│   └── run_ollama.py                # Local models via Ollama
│
├── results/                         # JSON result files for all models
│   ├── summary.json
│   ├── claude_opus_judge_222q.json
│   ├── gpt52_triad.json
│   └── ...
│
├── evaluation/
│   ├── run_benchmark.py             # Benchmark runner
│   └── analyze_results.py           # Category breakdown + failure modes
│
├── konomi/                          # KONOMI Standard + Triad Engine
│   ├── core.py                      # Layer 0: Meta-UDT (UDTs define UDTs)
│   ├── readme_exec.py               # README executor — runs UDT tags
│   ├── standards/                   # Layers 1-9 (<520 tokens each)
│   │   ├── base_udts.py             # Layer 1: Identifier, Timestamp, Quality...
│   │   ├── isa_95.py                # Layer 2: Enterprise↔Control
│   │   ├── isa_88.py                # Layer 3: Batch Process Control
│   │   ├── isa_101.py               # Layer 4: HMI Design
│   │   ├── isa_18_2.py              # Layer 5: Alarm Management
│   │   ├── opc_ua.py                # Layer 6: OPC-UA
│   │   ├── mqtt_sparkplug.py        # Layer 7: MQTT/Sparkplug B
│   │   ├── modbus.py                # Layer 8: Modbus
│   │   └── kpi.py                   # Layer 9: KPIs (OEE, MTBF, MTTR)
│   ├── triad/                       # Refactored Triad Engine
│   │   ├── engine.py                # Prompt construction + question wrapping
│   │   ├── judge.py                 # Gemini judge (independent evaluator)
│   │   ├── lifecycle.py             # ISA-88 Batch state machine lifecycle
│   │   ├── run.py                   # Unified CLI (replaces 5 runner scripts)
│   │   └── providers/               # Thin API adapters
│   │       ├── anthropic.py         # Claude (all versions)
│   │       ├── openai.py            # GPT-4o, GPT-5.2
│   │       ├── gemini.py            # Gemini 2.0/2.5
│   │       ├── ollama.py            # Local models (Mistral, Bielik, etc.)
│   │       └── perplexity.py        # Sonar, Sonar-Pro
│   ├── crosswalks/
│   │   └── engine.py                # Inter-standard mapping engine
│   └── api/
│       ├── server.py                # HTTP API with --demo flag
│       └── generate_pages.py        # Static JSON generator for Pages
│
├── docs/
│   ├── index.html                   # Main benchmark dashboard
│   └── konomi/                      # KONOMI Standards dashboard (GitHub Pages)
│       ├── index.html               # Interactive standard browser
│       ├── standards.json           # Standard index
│       ├── udts.json                # All UDT definitions
│       ├── crosswalks.json          # Inter-standard mappings
│       └── isa_*.json, kpi.json...  # Per-standard data
│
└── cultural_guide_schema/
    └── example_guide.json           # Schema for building domain guides
```

---

## KONOMI Standard — Self-Defining Industrial Standards Compression v1.0

The KONOMI Standard is a **meta-standard** where Layer 0 defines how all other layers are structured. Every standard is expressed as UDTs (User-Defined Types) with tags that drive behavior — states, transitions, validation rules, color palettes, and crosswalks between standards.

### Layer Architecture

| Layer | Standard | UDTs | Scope |
|-------|----------|------|-------|
| 0 | **Meta** | STD, UDT, LEVEL, STATE_MACHINE, ENTITY, RULE, CROSSWALK | How standards define themselves |
| 1 | **Base** | Identifier, Timestamp, Quality, Value, Range, Quantity, Duration, Status | Primitives all standards share |
| 2 | **ISA-95** | PhysicalAsset, Equipment, Material, Personnel, ProcessSegment | Enterprise↔Control integration |
| 3 | **ISA-88** | ProcessCell, Unit, Phase, Recipe, Batch | Batch process control |
| 4 | **ISA-101** | HMI_Layer, ColorMeaning, Faceplate | HMI design standards |
| 5 | **ISA-18.2** | AlarmPriority, Alarm | Alarm management lifecycle |
| 6 | **OPC-UA** | OPC_Node, OPC_Variable, OPC_Method, OPC_Subscription | Industrial interoperability |
| 7 | **Sparkplug** | MQTT_Topic, SparkplugPayload | Lightweight pub/sub |
| 8 | **Modbus** | ModbusRegister, ModbusMap | Field device communication |
| 9 | **KPI** | OEE, MTBF, MTTR, CycleTime, Throughput, EnergyKPI | Operational metrics |

### Tags Drive Behavior

Every UDT carries a `tags` dictionary. Downstream systems read tags to determine states, transitions, validation rules, palettes — without hardcoding behavior:

```python
from konomi import KS, UDT

phase = UDT.get("Phase")
phase.tagged("states")       # ['IDLE','RUNNING','COMPLETE','HOLDING',...]
phase.tagged("transitions")  # [('IDLE','RUNNING','start'), ('RUNNING','COMPLETE','done'), ...]

alarm = UDT.get("Alarm")
alarm.tagged("types")        # ['HI','HIHI','LO','LOLO','DEV','ROG','DISC']
alarm.tagged("states")       # ['NORM','UNACK','ACKED','RTN_UNACK','SHELVED','OUT_OF_SERVICE']

color = UDT.get("ColorMeaning")
color.tagged("palette")      # [('Normal','Gray','#808080'), ('Running','Green','#00AA00'), ...]
```

### Crosswalks

Map entities between any two standards:

```python
from konomi import KS

# ISA-95 WorkCenter → ISA-88 ProcessCell
mapped = KS.crosswalk({"_udt": "WorkCenter", "name": "Cell1"}, "ISA-95", "ISA-88")
# → {'mapped': True, 'entity': {'_udt': 'ProcessCell', 'name': 'Cell1', '_crosswalk': {...}}}
```

| From | Entity | → | To | Entity | Mapping |
|------|--------|---|----|---------|---------|
| ISA-95 | WorkCenter | → | ISA-88 | ProcessCell | exact |
| ISA-95 | WorkUnit | → | ISA-88 | S88_Unit | exact |
| ISA-95 | ProcessSegment | → | ISA-88 | Operation | exact |
| ISA-95 | Equipment | → | OPC-UA | OPC_Node | exact |
| ISA-88 | RUNNING | → | PackML | EXECUTE | exact |
| OPC-UA | OPC_Variable | → | Sparkplug | Metric | exact |
| ISA-101 | ColorMeaning | → | ISA-18.2 | Priority | partial |

### API Server

```bash
# Start with demo flag (all validations pass)
python -m konomi.api.server --demo --port 8095

# Endpoints:
#   GET  /api/standards          — list all standards
#   GET  /api/standards/{id}     — expand a standard
#   GET  /api/udts               — list all UDTs
#   GET  /api/expand/{id}        — full expansion with hierarchy
#   GET  /api/crosswalks         — all inter-standard mappings
#   GET  /api/generate/{udt}     — generate Python class from UDT
#   POST /api/validate           — validate entity against standard
#   POST /api/crosswalk          — map entity between standards
#   GET  /api/health             — health check + demo flag status
```

### GitHub Pages Dashboard

Browse all standards, UDTs, state machines, and crosswalks interactively at:

**[docs/konomi/index.html](docs/konomi/index.html)** — append `?demo=1` for demo mode

---

## Executable README

This README contains embedded **UDT tags** in HTML comments. The `readme_exec.py` parser finds them and runs them — turning this file into a live repo control surface.

### Tag Types

| Tag | Purpose | Example |
|-----|---------|---------|
| `@run` | Execute shell command | CLI calls, builds |
| `@test` | Run and assert exit code 0 | Automated tests |
| `@path` | Verify file/directory exists | Structural checks |
| `@udt` | Load and inspect a UDT | Type verification |
| `@validate` | Validate entity against standard | Compliance check |
| `@crosswalk` | Map entity between standards | Inter-standard mapping |
| `@state` | Log state machine reference | Audit trail |

### How to Run

```bash
# Run all tags (dry-run first)
python -m konomi.readme_exec --dry-run

# Run all tags for real
python -m konomi.readme_exec

# Run only test tags
python -m konomi.readme_exec --tag test

# Run only path checks
python -m konomi.readme_exec --tag path

# Logs written to .konomi/exec.log
```

### Embedded Tags

The following tags are parsed and executed by `readme_exec.py`. On GitHub they render as invisible HTML comments. Locally they're your CI.

#### Path Checks — Verify repo structure

<!-- @path[questions] -->
```
data/questions.json
```

<!-- @path[results] -->
```
results/summary.json
```

<!-- @path[konomi_core] -->
```
konomi/core.py
```

<!-- @path[konomi_dashboard] -->
```
docs/konomi/index.html
```

<!-- @path[paper] -->
```
PAPER/Domain_Grounding_Hallucination_Elimination_Benchmark.pdf
```

#### Tests — Run and verify

<!-- @test[konomi_import] -->
```bash
python -c "from konomi import KS, UDT; print('OK:', len(UDT.all()), 'UDTs')"
```

<!-- @test[standards_load] -->
```bash
python -c "
from konomi.core import KS
from konomi.standards import base_udts, isa_95, isa_88, isa_101, isa_18_2, opc_ua, mqtt_sparkplug, modbus, kpi
base_udts.build_all()
for m in [isa_95, isa_88, isa_101, isa_18_2, opc_ua, mqtt_sparkplug, modbus, kpi]: m.build()
stds = KS.list_standards()
assert len(stds) == 8, f'Expected 8, got {len(stds)}'
print('OK:', stds)
"
```

<!-- @test[crosswalk_engine] -->
```bash
python -c "
from konomi.core import KS
from konomi.standards import base_udts, isa_95, isa_88
base_udts.build_all(); isa_95.build(); isa_88.build()
r = KS.crosswalk({'_udt': 'WorkCenter', 'name': 'C1'}, 'ISA-95', 'ISA-88')
assert r['mapped'], f'Crosswalk failed: {r}'
print('OK: WorkCenter → ProcessCell')
"
```

<!-- @test[udt_tags_drive_behavior] -->
```bash
python -c "
from konomi.core import UDT
from konomi.standards import base_udts, isa_88
base_udts.build_all(); isa_88.build()
phase = UDT.get('Phase')
states = phase.tagged('states')
trans = phase.tagged('transitions')
assert 'IDLE' in states and 'RUNNING' in states
assert ('IDLE', 'RUNNING', 'start') in trans
print('OK: Phase states:', len(states), '/ transitions:', len(trans))
"
```

<!-- @test[udt_inheritance] -->
```bash
python -c "
from konomi.core import UDT
from konomi.standards import base_udts, isa_95
base_udts.build_all(); isa_95.build()
equip = UDT.get('Equipment')
fields = equip.resolved_fields
names = [f['name'] for f in fields]
assert 'id' in names and 'state' in names and 'capability' in names
print('OK: Equipment has', len(fields), 'fields (inherited + own)')
"
```

<!-- @test[demo_mode] -->
```bash
python -c "
from konomi.core import KS, demo_mode
from konomi.standards import base_udts, isa_18_2
base_udts.build_all(); isa_18_2.build()
demo_mode(True)
r = KS.validate({'_udt': 'Alarm'}, 'ISA-18.2')
assert r['valid'], 'Demo mode should pass all validations'
print('OK: demo mode passes validation')
"
```

<!-- @test[code_generation] -->
```bash
python -c "
from konomi.core import KS
from konomi.standards import base_udts, isa_88
base_udts.build_all(); isa_88.build()
code = KS.generate('ISA-88.Batch')
assert 'class Batch' in code
assert 'self.recipe' in code
print('OK: generated Batch class')
print(code)
"
```

<!-- @test[pages_json] -->
```bash
python -c "
import json, os
base = 'docs/konomi'
for f in ['standards.json', 'udts.json', 'crosswalks.json']:
    path = os.path.join(base, f)
    assert os.path.exists(path), f'Missing: {path}'
    data = json.load(open(path))
    assert len(data) > 0, f'Empty: {path}'
print('OK: all GitHub Pages JSON files present and non-empty')
"
```

#### UDT Inspections

<!-- @udt[Equipment] -->
```
Equipment
```

<!-- @udt[Phase] -->
```
Phase
```

<!-- @udt[Alarm] -->
```
Alarm
```

<!-- @udt[OEE] -->
```
OEE
```

#### Triad Engine Tests

<!-- @test[triad_engine] -->
```bash
python -c "
from konomi.triad.engine import TriadEngine
engine = TriadEngine(cultural_guide=None, char_map={})
raw = engine.build_system(triad=False)
assert 'Roman citizen' in raw
w = engine.wrap_question('Hadrian Wall?', 'ANACHRONISM_DETECTION')
assert 'does this thing exist' in w
print('OK: TriadEngine prompts work')
"
```

<!-- @test[triad_providers] -->
```bash
python -c "
from konomi.triad.providers import list_providers
p = list_providers()
assert 'anthropic' in p and 'ollama' in p and 'gemini' in p
assert len(p) == 5
print('OK: 5 providers registered:', p)
"
```

<!-- @test[triad_lifecycle] -->
```bash
python -c "
from konomi.triad.lifecycle import BenchmarkRun, BATCH_STATES
assert BATCH_STATES == ['Created','Scheduled','Running','Complete','Held','Aborted']
from konomi.triad.engine import TriadEngine
batch = BenchmarkRun('test', 'test', engine=TriadEngine())
assert batch.state == 'Created'
batch._transition('Scheduled')
assert batch.state == 'Scheduled'
assert len(batch.events) == 1
print('OK: ISA-88 batch lifecycle works')
"
```

<!-- @path[triad_run] -->
```
konomi/triad/run.py
```

<!-- @path[triad_engine_file] -->
```
konomi/triad/engine.py
```

#### Repo Maintenance

<!-- @run[clear_cache] -->
```bash
rm -rf .konomi/ __pycache__ konomi/__pycache__ konomi/standards/__pycache__ konomi/api/__pycache__ konomi/crosswalks/__pycache__ && echo "Cache cleared"
```

<!-- @run[regen_pages] -->
```bash
python -m konomi.api.generate_pages
```

#### State Machine References

<!-- @state[udt=Phase] -->
<!-- @state[udt=Alarm] -->
<!-- @state[udt=Batch] -->

#### Validate — Entity compliance

<!-- @validate[std=ISA-95] -->
```json
{"_udt": "Equipment", "id": "EQ-001", "path": "Site1/Area2/Line3", "name": "Filler"}
```

<!-- @validate[std=ISA-18.2] -->
```json
{"_udt": "Alarm", "id": "ALM-101", "tag": "TT-101", "priority": 2, "type": "HI"}
```

#### Crosswalk — Map between standards

<!-- @crosswalk[from=ISA-95, to=ISA-88] -->
```json
{"_udt": "WorkCenter", "name": "PackagingCell"}
```

---

## Quick Start — Reproduce Any Result

### Unified Runner (recommended)

```bash
pip install requests anthropic openai

# Any provider, any model — one command
export GEMINI_API_KEY="your-key"   # free judge: aistudio.google.com/app/apikey

# Claude
export ANTHROPIC_API_KEY="your-key"
python -m konomi.triad.run --provider anthropic --model claude-haiku-4-5-20251001 --triad

# GPT
export OPENAI_API_KEY="your-key"
python -m konomi.triad.run --provider openai --model gpt-4o-mini --triad

# Gemini
python -m konomi.triad.run --provider gemini --model gemini-2.5-pro --triad

# Local Ollama (free)
ollama pull mistral:instruct
python -m konomi.triad.run --provider ollama --model mistral:instruct --triad

# Filter categories, list providers
python -m konomi.triad.run --provider ollama --model mistral:instruct --triad --categories DOMAIN_SPECIFIC
python -m konomi.triad.run --list-providers
```

### Legacy Runners (still work)

```bash
python runners/run_anthropic.py --model claude-haiku-4-5-20251001 --triad
python runners/run_openai.py --model gpt-4o-mini --triad
python runners/run_ollama.py --model mistral:instruct --triad
```

All runners save after every question and resume automatically if interrupted. Results go to `results/benchmark_{model}_{mode}.json`. The ISA-88 batch lifecycle tracks state transitions (Created → Scheduled → Running → Complete | Held | Aborted) in the result JSON.

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
- **Thomas Frumkin** ([Konomi Systems](https://github.com/thomasfrumkin)) — MacCubeFACE recursive spatial equations, LookingGlass CPU-only mathematics framework, Konomi Systems equations, KONOMI Standard
- **Simon Gant** — Retrocausal temporal reasoning components
- **Michal Wojtkow** — topoAGI topological analysis library (winding number classifier)

---

## License

Benchmark evaluation code: **MIT** — see [LICENSE](LICENSE)

The Rome domain guide and Triad Engine production system are not included. Contact for enterprise licensing or domain guide consulting.
