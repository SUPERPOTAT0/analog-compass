# 01 — Overview

## The problem

Planetary scientists and mission planners test instruments, rovers, drills, EVA procedures and field protocols on **Earth analogue sites** before they fly to the Moon or Mars. A good analogue reproduces the *specific conditions that a specific test cares about* — not "a place that looks like Mars." The Atacama is a great analogue for a life-detection instrument (extreme aridity) but a poor one for a cryo-drill (no permafrost). The question is always **"analogue _for what test_?"**

Today this matching is done by expert intuition and a short list of famous sites (Atacama, Rio Tinto, Devon Island, Icelandic lava fields, Hawaii). That is slow, hard to defend, and it **misses unknown-but-excellent sites**.

## The challenge brief (as understood)

The brief asks for a system that:

1. Takes a **target** (a Moon or Mars condition/region) and finds the **best Earth analogue sites**.
2. Is **test-led and evidence-based** — comparisons are driven by what a test/operation needs, and every claim is backed by data with a stated confidence.
3. States **honest limits** — where each analogue *breaks down*, and which domains are *not* covered.
4. **Discovers new analogues anywhere on Earth** — a reproducible, systematic search, explicitly *not* just re-ranking a hand-picked pool.
5. Produces a **map** of candidates.

> This document reconstructs the brief from the working session; the authoritative brief text and the official datasets live behind a Resources tab that is still unread. Anything not yet verified against that source is flagged in [[QUESTIONS]].

## Product vision

**Analog Compass** is an intelligence platform with three faces over one deterministic core:

- **Compare** — "For *this target* and *this test*, how do candidate sites rank, and why?" Each site gets a verdict (`pass` / `borderline` / `excluded`), per-characteristic evidence, and an honest-limits note.
- **Discover** — "Find me *new* places on Earth that would work." The Offline Candidate Screen nominates windows from global rasters; the engine judges them exactly like curated sites, with full provenance.
- **Ask** — a **Geologist-Analysis AI agent** that answers natural-language questions ("Why is site X a better place to trial a cryo-drill than Y?") strictly from engine output and the knowledge base. See [[08_AI_AGENT]].

## The central idea: *test-led* analogue matching

A **target** is described per-characteristic (slope distribution, temperature envelope, illumination, lithology, …). A **test/operation** (e.g. *trial a pneumatic regolith drill*, *validate a life-detection assay*, *rover traverse autonomy*) imposes **requirements and gates** on a subset of those characteristics, with tolerances. A **site** is scored against the target **through the lens of the test**:

```
score( site | target, test ) =
    gates must all pass  (Must characteristics)
    weighted match on the Scored characteristics
    propagated through a Monte Carlo that respects measurement uncertainty
    → verdict + evidence + honest limits
```

Flipping this around gives the **suitability matrix** ([[06_SUITABILITY_SPEC]]): for a *given site*, *which tests* can it support? That is what turns discovery from "another Mars-looking desert" into "this newly found window can support cryo-drilling and rover-autonomy tests, but not life-detection."

## Why this is competitive

- **Determinism + provenance by construction** — reproducible runs, every number traceable to a source with an evidence tier. Judges can re-run and get the same bytes.
- **Discovery, not curation** — most entries show a pretty gallery of known sites; Analog Compass can nominate genuinely new windows and prove they were nominated (provenance field + QA rule).
- **Test↔site duality** — the same model answers "best site for this test" *and* "best tests for this site."
- **A grounded AI geologist** — the agent cannot invent facts; it is wired to the engine as tools, so it explains and compares with citations and confidence, and admits what it cannot know.
- **Honest limits as a feature** — stating where an analogue fails is exactly what the brief rewards, and what builds scientific trust.

## Glossary

| Term | Meaning |
|------|---------|
| **Target** | A Moon/Mars condition or region, described per-characteristic. Seeded in `config/targets.yaml`. |
| **Site** | An Earth location (a window/footprint) described per-characteristic. Curated (`pool.yaml`) or discovered. |
| **Candidate** | A site offered for a target. `curated candidate` (from the pool) or `new candidate` (nominated by discovery). |
| **Characteristic** | A measurable property (e.g. `slope`, `sunlit_fraction`, `basaltic_volcanic_fraction`). See [[05_DATA_SPEC]]. |
| **Test / Operation** | A field activity with requirements on characteristics (e.g. *cryo-drill trial*). See [[07_KNOWLEDGE_BASE]]. |
| **Must / Scored / Setup** | Characteristic roles: **Must** = hard gate; **Scored** = weighted contribution; **Setup** = context only, never scored. |
| **Gate** | A pass/fail threshold on a Must characteristic, evaluated **inside every Monte Carlo draw**. |
| **Verdict** | `pass`, `borderline`, or `excluded`. |
| **Evidence tier** | A–C confidence on a value. `derived`/`measured` (A/B) vs `proxy` (C). A proxy can never satisfy a Must gate alone. |
| **Window** | A fixed-size footprint on the analysis grid that discovery nominates and the engine scores. |
| **Bundle** | A self-describing set of data layers + descriptors the pipeline ingests. `synthetic` or `real`. |
| **data_mode** | `synthetic` or `real`. `real` forbids any synthetic fallback. |
| **run_id / seed** | Deterministic identifiers derived from the request + data version (no clock). |

See also: [[02_ARCHITECTURE]], [[13_CHALLENGE_ALIGNMENT]].
