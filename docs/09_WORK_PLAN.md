# 09 — Work Plan & Status

## 1. Where the previous session left off

The prior working session (my colleague's assistant) completed the **design/specification phase** and produced a **context pack** plus a **kickoff prompt** for a coding agent. Concretely finished there:

- Design docs (`AGENTS.md`, `02_ARCHITECTURE`, `03_ENGINE_SPEC`, `05_DATA_SPEC`, `09_WORK_PLAN`, `10_PM_PROCESS`, `13_CHALLENGE_ALIGNMENT`, `QUESTIONS`), the **validated `api/openapi.yaml`**, `config/*`, checker scripts, and the golden worked example.
- A **synthetic data generator** (+ reference inspector, source registry, cited facts), later shrunk from 56 MB by smoothing noisy coarse layers.
- Late design additions driven by the user: the **Offline Candidate Screen** (discovery), the **test→site suitability matrix**, **threshold_min/max** match functions, and new domain layers (lithology, caves/lava tubes, remoteness, vegetation, dust, wind, permafrost, illumination).

**The exact stopping point:** mid-edit, *patching `03_ENGINE_SPEC.md` to add the suitability-matrix section and the threshold rules*, when the session paused ("free usage returns at 6:20 AM"). **No implementation ticket was ever executed** — the kickoff prompt for `T-001` had just been written.

> **Net state inherited:** design ≈ 95% complete; **code 0%**. The context-pack *files* were attachments not transferred into this repo, so this session **reconstructs** the specs from the transcript (this vault) and then **implements**.

## 2. Continuation strategy

We resume by (a) finishing the design that was mid-edit — the suitability matrix ([[06_SUITABILITY_SPEC]]), the discovery engine ([[04_DISCOVERY_SPEC]]), and the knowledge base ([[07_KNOWLEDGE_BASE]]) are now fully specified — and (b) executing the implementation tickets, which the previous session never started.

## 3. Ticket board

Legend: ✅ done this session · 🔨 in progress · ⬜ planned · 🔒 blocked on real data (13 Nov).

| Ticket | Title | Status |
|--------|-------|--------|
| T-000 | Comprehension report | ✅ (this vault + readout) |
| **T-001** | **Repo scaffold** (uv, Makefile, pre-commit, CI, package layout, smoke test) | 🔨 |
| T-010 | Engine types + match functions (§5) + unit tests | ⬜ |
| T-011 | Gates + Monte Carlo (per-draw gating, triangular draw, seed) | ⬜ |
| T-012 | Verdict + honest-limit templates + golden recompute test | ⬜ |
| T-020 | FastAPI app + contract tests (`/compare`, `/sites`, `/targets`) | ⬜ |
| T-021 | GeoJSON map export | ⬜ |
| T-030 | Synthetic bundle generator + descriptors + source registry | ⬜ |
| T-031 | Pipeline: bundle loader + window aggregation + QA rules | ⬜ |
| T-040 | Discovery: Offline Candidate Screen + provenance + AC-D tests | ⬜ |
| T-041 | Suitability matrix + AC-S tests | ⬜ |
| T-042 | Knowledge base loaders (targets/tests/facts) + cross-ref checks | ⬜ |
| T-043 | AI agent: tools + runtime + guardrails + eval battery | ⬜ |
| T-044 | Real-data inspector (shape defined by reference inspector) | 🔒 |
| T-050 | Frontend: map + compare + suitability + chat | ⬜ |
| T-051 | Deploy (Vercel: Next.js + Python Fluid Compute) + env wiring | ⬜ |
| T-060 | Data day: swap `data_mode=real`, qa-real, golden recompute | 🔒 |

## 4. Build order this session

Pragmatic dependency order (not strict ticket numbers): **T-001 → engine (T-010/011/012) → synthetic+pipeline (T-030/031) → discovery+suitability+KB (T-040/041/042) → API (T-020/021) → agent (T-043) → frontend (T-050) → deploy (T-051)**. Engine-first because everything else (API, discovery, suitability, agent) calls it.

## 5. Definition of done (per ticket)

Every acceptance criterion maps to a test that can actually fail; code follows the spec text (spot-recompute two numbers); nothing invented; contract unchanged; `make ci` green; honest report. See [[10_PM_PROCESS]].

See next: [[10_PM_PROCESS]].
