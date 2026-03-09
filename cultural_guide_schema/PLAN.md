# PLAN.md — cultural_guide_schema/
## Domain Guide Schema Template
STATUS:stable|FILES:1|SIZE:4K

### Purpose
Template for building domain guides for ANY bounded domain.
Rome 110 CE is the benchmark case — schema works for medieval Europe,
Victorian England, 1920s New York, or software codebases.

### Schema Sections
```
time_period_context      year, emperor/leader, location, population, currency
anachronisms_to_avoid    not_yet_built, not_yet_happened, already_dead, technology_notes
timeline_recent_events   key events leading to the time period
key_locations            places characters know (name, description, significance)
social_structure         classes, legal statuses, hierarchies
economy_and_trade        currency, major trades, trade routes
prices_and_costs         specific prices in period currency
daily_life               food, housing, religion, typical day
characters               id, name, age, role, backstory, personality, expertise, speaking_style
roman_religion           major_gods (domain-specific section)
entertainment            domain-specific leisure/culture
engineering              domain-specific technology
medicine                 domain-specific health
customs                  domain-specific social norms
```

### Files
```
example_guide.json  4.1K  annotated template with _description fields
```

### Dependencies
```
→ runners/run_*.py (build_triad_system reads this schema)
→ konomi/triad/engine.py (TriadEngine._build_triad reads this schema)
→ konomi/tools/ (entropy gap detector validates against this schema)
```

### Notes
- Proprietary Rome guide NOT included in repo
- Schema is the interface contract between guide authors and engine
