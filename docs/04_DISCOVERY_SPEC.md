# 04 — Discovery Specification (Offline Candidate Screen)

> The brief's hardest requirement: **systematically search for new analogues anywhere on Earth** — and prove you are *discovering*, not re-ranking a hand-picked pool. This document specifies the **Offline Candidate Screen** and the acceptance criteria that prove genuine discovery.

## 1. What "discovery" means here

Discovery nominates **windows** (fixed-footprint tiles on the analysis grid) from **global rasters**, with full provenance, that are *not* in the curated pool. Each nominee is then judged by the **same engine** as any curated site ([[03_ENGINE_SPEC]]). A nominee that survives is labelled a **`new candidate`**; a surviving pool site is a **`curated candidate`**. The label is decided **solely by whether the window was nominated by the screen**, never by how good it looks.

## 2. Why screen *through the tests*

A target alone ("Mars polar") admits a huge, vague search. A **test** ("cryo-drill trial") imposes concrete requirements (permafrost present, slope below X, remoteness above Y). So the screen searches for windows that satisfy a **target × test** requirement profile. This is the same duality as the suitability matrix ([[06_SUITABILITY_SPEC]]): discovery and "which tests can this site support" are the same computation seen from opposite ends.

## 3. Algorithm — the Offline Candidate Screen

The screen is **offline** (runs over a pinned bundle, no live calls) and **deterministic** (seeded). It is a multi-stage funnel designed to be cheap first, precise last.

### Stage 0 — Define the search space
- Analysis grid of fixed-size windows (e.g. ~0.25° tiles) over the bundle's spatial coverage. Windows with no valid data (`outside_coverage`) are dropped up front.
- The target × test profile selects which characteristic rasters matter and their gates/requirements.

### Stage 1 — Cheap prefilter (hard gates on coarse layers)
- For each required Must characteristic that has a global raster, compute a fast window statistic (e.g. median) and apply the gate with a **generous margin** (gate ± band) so we never drop a true borderline early. Windows failing a hard requirement here are eliminated. This stage cuts the grid from millions of windows to thousands cheaply.

### Stage 2 — Requirement-space scoring (coarse rank)
- For surviving windows, compute a **requirement-space distance**: a weighted combination of per-characteristic match to the target × test profile, using the same match functions as the engine but on coarse window statistics. Keep the top-`K` per region plus anything within a margin of the gate (so borderliners survive).
- **Novelty de-duplication:** cluster windows spatially and by characteristic signature; keep the representative of each cluster. This stops the screen from returning 500 adjacent tiles of the same desert.

### Stage 3 — Pool-overlap exclusion (prove novelty)
- Any nominee window whose footprint overlaps (or sits within a `min_separation`) of a curated pool site is **re-labelled** as a rediscovery of that pool site, **not** a new candidate. This is the mechanism that makes the `new candidate` label trustworthy.

### Stage 4 — Promote to full evaluation
- The remaining nominees get full window aggregation (quantile arrays, evidence tiers, `missing` flags) and are passed to the **engine** exactly like curated sites. Verdicts, honest limits and provenance are produced identically.

### Stage 5 — Provenance record
Each nominee carries a `provenance` object (new API field + QA rule):
```yaml
provenance:
  origin: screen            # vs "curated"
  screen_version: "1.0.0"
  nominated_from: [slope_raster, permafrost_index, remoteness_time]
  window: {grid_id, bbox}
  stage_scores: {prefilter: …, requirement_distance: …}
  novelty: {pool_overlap: false, min_separation_km: 42.0, cluster_id: 17}
  seed: <int>
```

## 4. Determinism & reproducibility

The screen is seeded from `hash(bundle_version + target_id + test_id + screen_params)`. Same inputs ⇒ same nominees in the same order. No clock, no network. This is what lets a judge re-run discovery and get identical candidates.

## 5. Acceptance criteria — *proving* genuine discovery

These are testable gates in CI (`tests/discovery/`). The Discovery Engine is only "accepted" when all pass:

- **AC-D1 — Novelty by construction.** For a run with a known curated pool, **every** returned `new candidate` has `provenance.origin == screen` and `novelty.pool_overlap == false`. A test injects a pool site's exact window into the grid and asserts it is returned as `curated`/rediscovery, **never** as `new candidate`.
- **AC-D2 — Not a re-rank.** Remove the curated pool entirely; the screen must still return candidates (it does not depend on the pool existing). Conversely, with only the pool and no raster coverage, the screen returns **zero** new candidates (it cannot invent them).
- **AC-D3 — Found-unknown test.** Plant a synthetic window in the bundle that satisfies a target × test profile and is **absent** from the pool. Assert the screen nominates it and the engine passes/borderlines it. This proves the screen can surface a genuinely unknown site.
- **AC-D4 — Provenance completeness.** Every nominee has a complete `provenance` record; a QA rule fails the run if any field is missing.
- **AC-D5 — Determinism.** Two runs with identical inputs return byte-identical nominee lists.
- **AC-D6 — De-dup works.** A region of near-identical tiles yields a bounded number of cluster representatives, not the whole region.
- **AC-D7 — No fabrication.** A window with `missing` on a required Must is never promoted as a pass; it is excluded or reported missing (never zero-filled).

## 6. Honest limits of discovery

- Resolution floor: windows are only as trustworthy as the coarsest required raster; low-resolution proxies cap a nominee at `borderline` (tier-C rule, [[03_ENGINE_SPEC]] §3).
- Coverage holes: outside a layer's coverage (e.g. travel-time map's 85°N–60°S), required characteristics are `missing`, not guessed.
- The screen finds **where the measured characteristics match a test's requirements**; it does not certify ground truth. Nominees are *leads for fieldwork*, stated as such.

See next: [[05_DATA_SPEC]].
