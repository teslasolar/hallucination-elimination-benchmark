# PLAN.md — Root
## Hallucination Elimination Benchmark + KONOMI Standard
STATUS:refactored|TAGS:36/36|UDTS:52|CROSSWALKS:10×48|LAYERS:0-9|PROVIDERS:5|QUESTIONS:222

### Architecture
```
INPUT→ data/{questions,cultural_guide,characters}.json
ENGINE→ konomi/triad/{engine,judge,lifecycle,providers/*}
ANALYSIS→ konomi/triad/{winding,adversarial,analyze,chain}
STANDARDS→ konomi/standards/{base_udts,isa_*,opc_ua,mqtt,modbus,kpi}
CROSSWALK→ konomi/crosswalks/engine.py
TOOLS→ konomi/tools/{entropy}
OUTPUT→ results/*.json + docs/konomi/*.json
CONTROL→ README.md (executable, 36 tags) + konomi/readme_exec.py
API→ konomi/api/server.py (--demo --port 8095)
PAGES→ docs/{index.html,konomi/index.html}
```

### Directories
```
PAPER/          1 file   202K  research PDF
chaining/       8 files  380K  compositional chains + results
cultural_guide/ 1 file   4K   domain guide schema template
data/           2 files  60K  questions.json + guide sample
docs/          58 files  1.4M GitHub Pages (dashboard+konomi+benchmark mirror)
evaluation/     1 file   1K   deprecated → konomi/triad/
figures/        2 files  13K  SVG diagrams
konomi/        30 files  80K  KONOMI Standard + Triad Engine (52 UDTs, 10 crosswalks)
questions/      1 file   22K  222 question generator
results/       14 files  900K model results (6 models, raw+triad)
runners/        1 file   2K   deprecated → konomi/triad/run.py
tools/          1 file   1K   deprecated → konomi/tools/
```

### Refactor Map (completed — legacy files removed)
```
REMOVED                            → ACTIVE (konomi/)
runners/run_*.py (×5, 82K)        → triad/providers/*.py + triad/run.py
evaluation/run_benchmark.py (25K)  → triad/{winding,adversarial,lifecycle}.py
evaluation/analyze_results.py (12K)→ triad/analyze.py
chaining/run_chain_benchmark.py    → triad/chain.py
tools/entropy_gap_detector.py (21K)→ tools/__init__.py
```

### CLI Entry Points
```
python -m konomi.triad.run       # unified benchmark runner
python -m konomi.triad.analyze   # offline result analysis
python -m konomi.triad.chain     # compositional chaining
python -m konomi.tools.entropy   # domain guide quality
python -m konomi.api.server      # HTTP API
python -m konomi.api.generate_pages  # static JSON for Pages
python -m konomi.readme_exec     # executable README (36 tags)
```

### Test Surface (README tags)
```
@path  ×11  repo structure verification
@test  ×16  import/load/crosswalk/tags/inheritance/demo/codegen/pages/
             triad/providers/lifecycle/winding/adversarial/analyzer/entropy/chain
@udt   ×4   Equipment/Phase/Alarm/OEE
@run   ×2   clear_cache/regen_pages
@validate×2  ISA-95 Equipment, ISA-18.2 Alarm
@crosswalk×1 ISA-95→ISA-88 WorkCenter→ProcessCell
TOTAL: 36/36 PASSING
```

### Next Steps
- [ ] Add GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY as GitHub repo secrets
- [ ] Run full 222q benchmark through unified runner (CI runs single-category on push to main)
