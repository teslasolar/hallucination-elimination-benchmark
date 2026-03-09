# PLAN.md — konomi/
## KONOMI Standard + Triad Engine
STATUS:active|FILES:30|SIZE:70K|TESTS:36/36

### Module Map
```
__init__.py         251B  re-exports KS, UDT, Standard, demo_mode
core.py             6.7K  LAYER 0: Meta-UDT (UDTs define UDTs)
readme_exec.py      7.2K  executable README parser (@path/@test/@run/@udt/@validate/@crosswalk/@state)

standards/                LAYERS 1-9 (all <520 tokens)
  __init__.py        63B
  base_udts.py      2.1K  L1: Identifier,Timestamp,Quality,Value,Range,Quantity,Duration,Status
  isa_95.py         3.3K  L2: PhysicalAsset,Equipment,Material,Personnel,ProcessSegment
  isa_88.py         2.8K  L3: ProcessCell,Unit,Phase,Recipe,Batch (state machines)
  isa_101.py        2.1K  L4: HMI_Layer,ColorMeaning,Faceplate
  isa_18_2.py       2.4K  L5: AlarmPriority,Alarm (lifecycle states)
  opc_ua.py         2.1K  L6: OPC_Node,OPC_Variable,OPC_Method,OPC_Subscription
  mqtt_sparkplug.py 1.5K  L7: MQTT_Topic,SparkplugPayload
  modbus.py         1.8K  L8: ModbusRegister,ModbusMap
  kpi.py            1.8K  L9: OEE,MTBF,MTTR,CycleTime,Throughput,EnergyKPI

crosswalks/
  __init__.py        51B
  engine.py         2.4K  ISA-95↔88, 95↔OPC-UA, 88↔PackML, 101↔18.2, OPC↔Sparkplug

api/
  __init__.py        48B
  server.py         4.3K  HTTP REST API (GET/POST, --demo flag, CORS)
  generate_pages.py 1.4K  static JSON for GitHub Pages

tools/
  __init__.py       5.4K  entropy gap detector (extract_leaves, analyze_guide, check_coverage)
  entropy.py         191B  re-exports

triad/                    TRIAD ENGINE (refactored from 5 runners)
  __init__.py       270B  re-exports TriadEngine, GeminiJudge, BenchmarkRun
  engine.py         5.6K  prompt construction + question wrapping
  judge.py          2.6K  Gemini independent evaluator (6 retries, rate limit handling)
  lifecycle.py      7.7K  ISA-88 Batch state machine (Created→Running→Complete|Held|Aborted)
  run.py            2.7K  unified CLI: --provider X --model Y --triad
  winding.py        2.8K  topological paradox classifier (F1=0.939, N=64)
  adversarial.py    3.5K  20 false-premise adversarial queries
  analyze.py        4.1K  offline result analysis (categories, failures, winding)
  chain.py          7.6K  compositional chaining benchmark

  providers/               thin API adapters (20-35 lines each)
    __init__.py     170B  re-exports get_provider, list_providers
    registry.py     988B  decorator-based provider registration
    anthropic.py    1.1K  Claude (all versions)
    openai.py       1.2K  GPT-4o, GPT-5.2
    gemini.py       1.4K  Gemini 2.0/2.5
    ollama.py       935B  local models via Ollama
    perplexity.py   1.5K  Sonar, Sonar-Pro
```

### Core Concepts
```
UDT           User-Defined Type — atom of KONOMI. Fields + tags + constraints + inheritance.
Standard      Collection of UDTs + hierarchy + states + rules + crosswalks.
KS            Entry point: parse/expand/validate/crosswalk/generate.
Tags          Dict on each UDT — states, transitions, priorities, palettes.
              Downstream reads tags to determine behavior (no hardcoding).
Crosswalk     Maps entities between standards (ISA-95 WorkCenter → ISA-88 ProcessCell).
Demo mode     KONOMI_DEMO=1 → all validations pass (for testing/exploration).
BenchmarkRun  ISA-88 Batch lifecycle: Created→Scheduled→Running→Complete|Held|Aborted.
```

### CLI Entry Points
```
python -m konomi.triad.run --provider anthropic --model claude-haiku-4-5-20251001 --triad
python -m konomi.triad.run --list-providers
python -m konomi.triad.analyze results/claude_opus_judge_222q.json
python -m konomi.triad.chain --provider ollama --model mistral:instruct --triad
python -m konomi.tools.entropy --guide data/cultural_guide.json --threshold 0.5
python -m konomi.api.server --demo --port 8095
python -m konomi.api.generate_pages
python -m konomi.readme_exec [--dry-run] [--tag TAG]
```

### API Endpoints
```
GET  /api/standards          list all 8 standards
GET  /api/standards/{id}     expand one standard
GET  /api/udts               list all 36 UDTs
GET  /api/expand/{id}        full expansion with hierarchy
GET  /api/crosswalks         all inter-standard mappings
GET  /api/generate/{udt}     generate Python class from UDT
POST /api/validate           validate entity against standard
POST /api/crosswalk          map entity between standards
GET  /api/health             health + demo flag
```

### Test Tags (36/36 passing)
```
@path  ×11  questions,results,konomi_core,konomi_dashboard,paper,
            triad_run,triad_engine_file,winding_file,adversarial_file,
            analyze_file,entropy_file
@test  ×16  konomi_import,standards_load,crosswalk_engine,udt_tags_drive_behavior,
            udt_inheritance,demo_mode,code_generation,pages_json,
            triad_engine,triad_providers,triad_lifecycle,
            winding_classifier,adversarial_queries,analyzer,entropy_detector,chain_module
@udt   ×4   Equipment,Phase,Alarm,OEE
@run   ×2   clear_cache,regen_pages
@validate×2  ISA-95/Equipment, ISA-18.2/Alarm
@crosswalk×1 ISA-95→ISA-88/WorkCenter→ProcessCell
@state ×3   Phase,Alarm,Batch
```
