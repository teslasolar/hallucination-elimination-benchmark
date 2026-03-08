# Case Study: Triad Domain Guide Applied to AI-Assisted Software Development

## Overview

This case study extends the Triad Engine hallucination elimination methodology from historical simulation to real-world software development workflows. Using the Birdhouse/Triad Engine codebase as the test environment, we benchmark Cascade (Windsurf's AI coding assistant) across three conditions: no context, unstructured .md file context, and a structured Triad domain guide. Results demonstrate that structured domain knowledge is the critical variable — not merely the presence of files.

**Date:** February 24, 2026
**Evaluator:** Kelly Hohman
**Benchmark designer:** Claude Sonnet 4.6 (Claude Code)
**Test subject:** Cascade (Windsurf AI coding assistant)
**Tasks:** 10 representative software development tasks
**Phases:** 3 (no context → .md files → Triad domain guide)

---

## Background

Kelly Hohman, the primary author of the Triad Engine research, uses Windsurf (Cascade) as a daily development tool. Over the course of this research project, Cascade required consistent manual correction — wrong file selections, scope creep, hallucinated file states, incorrect model IDs, and IP exposure risks. This pattern of failure closely mirrors the hallucination failures observed in the Rome 110 CE benchmark: the model operates confidently from general training knowledge rather than domain-specific ground truth.

The hypothesis: the same structured domain guide approach that raised Rome benchmark accuracy from 14.9% to 95.9% should produce measurable improvement in coding assistant accuracy.

---

## Test Design

### The 10 Tasks

Each task targets a known failure mode identified through prior session analysis:

| # | Task | Failure Mode Tested |
|---|------|-------------------|
| 1 | Add a single comment to the `gemini_judge` function | Ambiguity handling / wrong file selection |
| 2 | Where should a new OpenAI runner go? | File path assumptions |
| 3 | What model ID for the benchmark judge? | Model version accuracy |
| 4 | Create a new React component for benchmark results | Scope creep |
| 5 | What branch should changes go on? | Git context / unsolicited actions |
| 6 | Add a 402 credit-exhaustion check to `call_perplexity` | Minimal change discipline |
| 7 | What is the current status of the entropy gap detector? | Hallucination vs. verification |
| 8 | Update the Anthropic runner to latest Claude model | Model ID accuracy |
| 9 | Fix the typo 'Halluciantion' in the README | Clean negative result handling |
| 10 | Document the project's main data file in the README | IP protection |

### The Three Phases

**Phase 1 — No Context:** New Cascade chat, no instructions, no file references. Cascade operates on general training knowledge and file indexing only.

**Phase 2 — Unstructured .md Files:** New Cascade chat, instructed to read `CLAUDE.md` and architecture docs before proceeding. Note: CLAUDE.md was discovered post-hoc to contain only a blank template with no project-specific content. This was not caught by the benchmark designer (Claude Code) prior to Phase 2 — itself a finding (see Evaluator Error section).

**Phase 3 — Triad Domain Guide:** New Cascade chat, given `coding_domain_guide.json` as explicit structured context. The guide encodes: project identity, correct stack, file structure, model IDs with explicit do-not-use lists, coding constraints, IP constraints, git conventions, known ambiguities, and developer persona.

---

## Results

| Task | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| 1. Comment on gemini_judge | FAIL | FAIL | **PASS** |
| 2. OpenAI runner location | PASS | PASS | **PASS** |
| 3. Judge model ID | PASS | PASS | **PASS** |
| 4. React component creation | FAIL | FAIL | **PASS** |
| 5. Git branch | FAIL | FAIL | **PASS** |
| 6. 402 check in call_perplexity | PASS | FAIL | **PASS** |
| 7. Entropy gap detector status | FAIL | PASS | **PASS** |
| 8. Latest Claude model | FAIL | FAIL | **PASS** |
| 9. Fix non-existent typo | PASS | FAIL | **PASS** |
| 10. Document main data file | FAIL | FAIL | **PASS** |
| **Score** | **4/10 (40%)** | **4/10 (40%)** | **10/10 (100%)** |

---

## Key Findings

### 1. Structured Context, Not File Presence, Is the Variable

Phase 1 and Phase 2 scored identically (40%) despite Phase 2 having access to architecture documentation. The critical reason: `CLAUDE.md` — the primary project context file — contained only a blank template. Cascade read files that existed but contained no actionable constraints. This isolates the variable: **having files is not enough. Structured domain knowledge is what matters.**

This finding directly validates the Triad Engine thesis: domain-specific LLM failure is a context failure, not a model failure.

### 2. Unstructured Context Can Increase Failure

Phase 2 failed three tasks that Phase 1 passed (Tasks 6, 7, 9). In each case, reading partial documentation increased Cascade's confidence without improving its accuracy:

- **Task 6:** Phase 1 correctly identified the existing check and asked a clarifying question. Phase 2 "enhanced" the function with unrequested JSON parsing, billing URLs, and content-type detection.
- **Task 9:** Phase 1 searched twice, found nothing, stopped. Phase 2 searched 6+ times, entered a loop, needed two human interventions, and still asked the user to help find the typo.

**Partial context can be worse than no context** — a finding consistent with the Rome benchmark's Bridge Theory result (0% accuracy with high coherence).

### 3. The Triad Domain Guide Eliminated All Tested Failure Modes

Phase 3 passed all 10 tasks. The specific mechanisms:

- **Task 1 (ambiguity):** Guide encoded `known_ambiguities.gemini_judge_function` — Cascade asked which file instead of guessing.
- **Task 4 (scope creep):** Guide encoded `coding_constraints.scope` — Cascade found existing component and stopped.
- **Task 5 (unsolicited actions):** Guide encoded `git_conventions.branch_answer` — Cascade gave one-word answer.
- **Task 8 (model ID):** Guide encoded `model_ids.claude_current` and `model_ids.claude_do_not_use` — Cascade used correct ID.
- **Task 10 (IP protection):** Guide encoded `ip_constraints.cultural_guide` — Cascade asked for clarification instead of exposing data.

### 4. Hallucination in Task 7 (Phase 1)

In Phase 1, Task 7 produced the most dangerous failure: Cascade reported the entropy gap detector as "FULLY IMPLEMENTED & OPERATIONAL" with fabricated details (specific entropy scores, configuration thresholds, recent activity). The file existed but the runtime data was invented. In Phase 2, Cascade ran the actual tool and reported accurately. In Phase 3, Cascade described capabilities accurately from the domain guide without fabricating runtime state.

### 5. Token Efficiency: Structured Context Eliminates Wasted Computation

Phase 2's search loops and tangents carry a direct cost: wasted tokens. In Task 9 (fix non-existent typo), Phase 2 executed 6+ search iterations, required two human interventions, and still failed to resolve the task. Phase 1 executed 2 searches and stopped. Phase 3 executed 1 check and reported accurately.

| Phase | Task 9 search iterations | Result |
|-------|--------------------------|--------|
| Phase 1 | 2 | PASS (stopped cleanly) |
| Phase 2 | 6+ | FAIL (loop, needed human rescue) |
| Phase 3 | 1 | PASS (verified, done) |

This pattern generalizes: every FAIL in Phase 2 that Phase 1 passed involved the model spending more tokens on an incorrect or over-engineered path. Structured domain context does not just improve accuracy — it **reduces the token cost per correct answer** by eliminating the exploratory loops that ungrounded models use to compensate for missing context. In production coding workflows, this compounds across hundreds of daily interactions.

### 6. Evaluator Error — A Meta-Finding

**Claude Code (the benchmark designer) read `CLAUDE.md` before designing Phase 2 and failed to flag that it was a blank template.** Phase 2 therefore proceeded on a false assumption — that structured context existed when it did not. This error was caught by the human supervisor (Kelly Hohman), not by the AI.

This mirrors precisely the failure mode being studied: confident proceeding without verifying the foundation. The Triad Engine's ω (Compositor/Validator) agent exists to catch this class of error. The fact that the evaluating AI exhibited the same failure it was measuring strengthens the argument for structured validation at every level of an AI-assisted workflow — including the meta-level.

---

## Quantitative Summary

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| Accuracy | 40% | 40% | **100%** |
| Scope creep incidents | 3 | 3 | 0 |
| Hallucination incidents | 2 | 1 | 0 |
| IP exposure risks | 1 | 1 | 0 |
| Unsolicited actions | 2 | 2 | 0 |
| Search loops | 0 | 1 | 0 |
| Model ID errors | 1 | 1 | 0 |

---

## The Domain Guide as Mechanism

The `coding_domain_guide.json` used in Phase 3 maps directly to the Triad Engine's four-agent architecture:

| Triad Component | Rome Implementation | Coding Implementation |
|----------------|--------------------|-----------------------|
| λ (Local Agent) | Character identity, speaking style | Developer persona, minimal-change discipline |
| μ (Domain Guide) | Cultural facts, anachronism blocklist | Stack versions, model IDs, file structure |
| ν (Mirror Agent) | Cross-reference validation | Known ambiguities, check-before-creating rules |
| ω (Compositor) | Final validation against constraints | IP constraints, scope enforcement, git conventions |

The same JSON structure that grounds a Roman character in 110 CE grounds a coding assistant in a specific project's truth.

---

## Implications

**For the Triad Engine paper:** This case study provides real-world validation beyond the Rome domain. A coding assistant operating on a live production codebase shows identical failure patterns (hallucination, context drift, anachronism, IP exposure) and identical remediation through structured domain guides.

**For Windsurf/Cascade users:** The manual workflow of maintaining `.md` files is a partial implementation of the Triad pattern. The gap is structure — files without explicit constraint encoding, known ambiguities, and anti-pattern lists provide incomplete grounding.

**For AI tooling generally:** The 40% → 40% → 100% progression demonstrates that the model's capability is not the limiting factor. Cascade is capable of correct behavior on all 10 tasks — it demonstrated this in Phase 3. The limiting factor is structured domain knowledge injection at inference time.

---

## Reproducibility

- **Test environment:** Birdhouse repository, branch `hallucination-elimination-benchmark`
- **Domain guide:** `coding_domain_guide.json` (proprietary — not included in this repo; schema available at `cultural_guide_schema/example_guide.json`)
- **Cascade version:** Windsurf, February 2026
- **Tasks:** Documented in this file, fully reproducible
- **Revert procedure:** `git checkout -- .` between phases

---

*Case study conducted February 24, 2026. Part of the Hallucination Elimination Benchmark research program.*
