# PLAN.md — chaining/
## Compositional Chaining Benchmark
STATUS:legacy+refactored|FILES:8|SIZE:380K

### Purpose
Test drift across multi-step conversations. Key hypothesis:
domain guide re-injected every call → per-step accuracy bounded.

### Chain Types
```
DEPTH_SCALING    N-step factual chains (depth 2,3,5,50,100)
FAULT_INJECTION  False premise at step K → does guide correct?
CROSS_CHARACTER  Sequential persona chain → does identity hold?
```

### Files
```
chain_questions.json          44K  pre-defined chains (3 types)
run_chain_benchmark.py        28K  LEGACY runner (anthropic-only)
results/
  chain_*_raw.json            26K  raw baseline results
  chain_*_triad.json          27K  triad engine results
  chain_*_raw_depth.json      99K  depth scaling raw
  chain_*_triad_depth.json   104K  depth scaling triad
  chain_*_raw_fault.json      26K  fault injection raw
  chain_*_triad_fault.json    26K  fault injection triad
```

### Refactored To
```
konomi/triad/chain.py          ChainRun class
  Uses: konomi/triad/{engine,judge,providers}
  CLI: python -m konomi.triad.chain --provider X --model Y --triad
  Supports: all 5 providers (not just anthropic)
```

### chain_questions.json Schema
```json
{
  "chains": [{
    "chain_id": str,
    "chain_type": "DEPTH_SCALING|FAULT_INJECTION|CROSS_CHARACTER",
    "depth": int,
    "steps": [{
      "step": int,
      "category": str,
      "question": str,
      "ground_truth": str,
      "character": str|null,
      "context_from_previous": bool,
      "context_template": str|null,
      "inject_error": bool|null,
      "injected_error": str|null
    }]
  }]
}
```
