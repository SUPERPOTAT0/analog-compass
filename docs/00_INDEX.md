# Analog Compass — Documentation Vault

> **Analog Compass** helps a field-campaign lead find the Earth sites that are the best **test analogues** for a Moon or Mars target — in a *test-led, evidence-based* way, with *honest limits*, and with the ability to **discover new sites anywhere on Earth** (not just rediscover the famous ones).

This is an [Obsidian](https://obsidian.md)-compatible vault. Links use `[[wikilink]]` syntax. Open the folder as a vault, or read the files directly.

## How to read this vault

Read in order. Each document is self-contained but builds on the previous.

| # | Document | What it covers |
|---|----------|----------------|
| 00 | **[[00_INDEX]]** | This page |
| 01 | [[01_OVERVIEW]] | Problem, challenge brief, product vision, the "test-led" idea, glossary |
| 02 | [[02_ARCHITECTURE]] | System architecture, components, data flow, repo layout, tech stack |
| 03 | [[03_ENGINE_SPEC]] | The deterministic scoring engine: match functions, gates, Monte Carlo, verdicts |
| 04 | [[04_DISCOVERY_SPEC]] | The Offline Candidate Screen — how new analogues are discovered |
| 05 | [[05_DATA_SPEC]] | Data layers, characteristics, sources, synthetic data, data pipeline, QA |
| 06 | [[06_SUITABILITY_SPEC]] | Test → site suitability matrix: which tests a site can support, and why |
| 07 | [[07_KNOWLEDGE_BASE]] | Target environment KB (Moon/Mars) + test/operation requirements catalogue |
| 08 | [[08_AI_AGENT]] | The Geologist-Analysis AI agent: grounded tool-calling, prompts, guardrails |
| 09 | [[09_WORK_PLAN]] | Ticketed work plan, **where my colleague left off**, and the continuation |
| 10 | [[10_PM_PROCESS]] | Ticket lifecycle, report template, acceptance rules |
| 11 | [[11_DEPLOYMENT]] | Infrastructure, environments, CI/CD, scaling, security |
| 12 | [[12_FRONTEND]] | Frontend architecture: map, comparison, suitability, chat |
| 13 | [[13_CHALLENGE_ALIGNMENT]] | Brief → design mapping, and what we honestly do **not** cover |
| — | [[QUESTIONS]] | Open questions awaiting the real data / resources tab |

## Status at a glance

- **Design / specification:** ~95% complete (inherited from the prior session, reconstructed and finished here).
- **Implementation:** building now — see [[09_WORK_PLAN]] for live ticket status.
- **Real data:** not yet integrated. The system runs on a **synthetic bundle** that mirrors the expected schema; swapping in the real bundle is a config flip (`data_mode=real`). See [[05_DATA_SPEC]].

## The three rules that shape everything

1. **Never invent science or data.** Unknowns are `missing`/`null` and are asked about — never zero, never a silent match. (See [[03_ENGINE_SPEC]] §missing-data and [[08_AI_AGENT]] grounding.)
2. **The engine is pure and deterministic.** No I/O, no clock, no unseeded randomness. Same inputs → same `run_id` → same bytes out.
3. **Honest limits.** Every verdict states where the analogue breaks down. Domains we do not cover are named plainly in [[13_CHALLENGE_ALIGNMENT]].
