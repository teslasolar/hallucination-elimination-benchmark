# PLAN.md — tools/
## Legacy Entropy Gap Detector
STATUS:legacy|FILES:1|SIZE:21K|REFACTORED→konomi/tools/

### Files
```
entropy_gap_detector.py  21K  489 lines
```

### Purpose
Detect sparse sections in cultural domain guides. Score by leaf count,
word density, cross-reference consistency. Optionally auto-fill gaps
using LLM (Ollama/Claude/Gemini).

### Refactored To
```
konomi/tools/__init__.py  5.4K  core functions (no LLM fill — pure analysis)
  extract_leaves()         recursive JSON leaf extraction
  compute_section_entropy() score by density+cardinality
  analyze_guide()          all sections → entropy scores
  check_coverage()         questions vs guide section mapping
  print_report()           formatted output

CLI: python -m konomi.tools.entropy --guide data/cultural_guide.json
```

### Not Refactored (removed)
```
fill_with_ollama()   — optional LLM gap-filling (use separately if needed)
fill_with_claude()   — optional LLM gap-filling
fill_with_gemini()   — optional LLM gap-filling
```

### Notes
- Legacy file kept for users who want the auto-fill feature
- Refactored version is analysis-only (pure, no API calls)
