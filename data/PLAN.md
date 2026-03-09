# PLAN.md — data/
## Benchmark Data
STATUS:stable|FILES:2|SIZE:60K

### Files
```
questions.json              59K  222 benchmark questions + ground truth
cultural_guide_sample.json  647B sample/stub guide (proprietary guide not included)
```

### questions.json Schema
```json
{
  "name": "Hallucination Elimination Benchmark — Ancient Rome 110 CE",
  "total_questions": 222,
  "categories": {
    "ANACHRONISM_DETECTION": 47,
    "CHARACTER_IDENTITY": 51,
    "COMPLEX_SCENARIOS": 36,
    "CULTURAL_VALUES": 43,
    "DOMAIN_SPECIFIC": 45
  },
  "questions": [{
    "index": int,
    "category": str,
    "question": str,
    "ground_truth": str,
    "character": str|null
  }]
}
```

### Dependencies
```
← questions/benchmark_questions.py (generates questions.json)
→ runners/run_*.py (load_data reads questions)
→ konomi/triad/engine.py (TriadEngine.load_questions)
→ konomi/tools/ (entropy coverage analysis)
```

### Missing (by design)
```
cultural_guide.json   PROPRIETARY — full Rome 110 CE domain guide
characters.json       PROPRIETARY — character definitions (Julia, Marcus, Gaius)
```
