# 12 — Frontend

## 1. Stack

**Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + MapLibre GL JS** (vector basemap, no proprietary key). Deployed on Vercel. The frontend is a thin, map-first client over the Python API; it holds no scoring logic (the engine is authoritative).

## 2. Views

1. **Compare** — pick a **target** and a **test**; see candidate sites ranked with `pass`/`borderline`/`excluded` chips, per-characteristic evidence bars (with tier + source), and an **"honest limits"** panel per site. Side-by-side comparison of two sites.
2. **Discover** — pick target × test, draw/choose a region, run the Offline Candidate Screen; new candidates drop onto the map with provenance popovers (where they came from, novelty, pool-overlap=false). Curated vs new are visually distinct.
3. **Suitability** — pick a site; a matrix of tests with supported/borderline/unsupported and the limiting characteristic for each.
4. **Ask** — the Geologist-Analysis **chat agent** (streamed), with inline citations (`source_id`, `run_id`) and clickable map/verdict references. Tool-calls are shown as "ran compare…", "ran discover…" so the user sees the evidence trail.

## 3. Map

- MapLibre GL with a free vector style; layers: curated sites, discovered candidates, target reference markers, and a verdict heat layer.
- The API's **GeoJSON export** (`/map.geojson`) feeds the map directly; features carry verdict, candidate_kind, provenance.
- Clicking a feature opens the evidence panel for that site.

## 4. Data flow

- Server Components fetch targets/tests/sites from the API at request time (ISR where static).
- Compare/discover are POSTs; results cached client-side by `run_id`.
- The chat uses SSE from `/agent/chat`; the UI renders streamed text + tool-activity badges.

## 5. UX principles

- **Evidence first:** never show a verdict without its drivers and limits.
- **Tiers visible:** proxy (tier C) values are visually marked so a user never mistakes a provisional pass for a hard one.
- **Reproducibility surfaced:** every result shows its `run_id` and `data_version`; "copy reproducible link" re-runs identically.
- **Honest limits are not fine print** — they sit next to the verdict.

## 6. Accessibility & performance

- Keyboard-navigable, labelled controls, sufficient contrast (WCAG AA).
- Code-split map; stream chat; prefetch target/test lists; image/font optimisation via the platform.

See also: [[11_DEPLOYMENT]], [[08_AI_AGENT]].
