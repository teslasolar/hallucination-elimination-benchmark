# PLAN.md — questions/
## Benchmark Question Generator
STATUS:stable|FILES:1|SIZE:22K

### Files
```
benchmark_questions.py  22K  generates 222 questions across 5 categories
```

### Function
```python
generate_questions(CHAR_MAP) → list[dict]
  Returns 222 dicts: {category, question, ground_truth, character?}
```

### Categories
```
ANACHRONISM_DETECTION  47q  things that don't exist in 110 CE
  Hadrian's Wall (122 CE), Pantheon dome (126 CE), printing press, etc.
CHARACTER_IDENTITY     51q  character-specific (3 chars × 17 attributes)
  Julia (patrician), Marcus (senator), Gaius (merchant)
CULTURAL_VALUES        43q  Roman social norms
  slavery, democracy, arranged marriage, gender roles, patron-client
DOMAIN_SPECIFIC        45q  historical facts
  bread prices (2 asses), emperor (Trajan), currency (denarius)
COMPLEX_SCENARIOS      36q  multi-step social/legal reasoning
  freedman→senator path, slave manumission, adult adoption
```

### Dependencies
```
→ data/questions.json (serialized output)
→ evaluation/run_benchmark.py (imports generate_questions)
→ konomi/triad/engine.py (loads questions.json)
```
