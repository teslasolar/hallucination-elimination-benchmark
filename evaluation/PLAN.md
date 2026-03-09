# PLAN.md — evaluation/
## Deprecated — Use konomi/triad/
STATUS:removed|REFACTORED→konomi/triad/

### Migration
```
python -m konomi.triad.run         # was: run_benchmark.py (Tier 1)
python -m konomi.triad.analyze     # was: analyze_results.py
python -m konomi.triad.winding     # was: run_benchmark.py (Tier 2)
python -m konomi.triad.adversarial # was: run_benchmark.py (Tier 4)
```
