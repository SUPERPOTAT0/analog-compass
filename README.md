# Analog Compass 🧭🪐

**Find the Earth sites that are the best _test analogues_ for a Moon or Mars target — test-led, evidence-based, with honest limits — and discover new ones anywhere on Earth.**

Analog Compass helps a planetary field-campaign lead answer three questions:

- **Compare** — *For this target and this test, which sites rank best, and why?*
- **Discover** — *Where else on Earth (not just the famous sites) could this test be run?*
- **Ask** — a grounded **AI geologist** that explains, compares and recommends, backed by a deterministic engine so it never invents data.

> Full design & architecture: open **[`docs/`](docs/00_INDEX.md)** as an Obsidian vault.

## Why it's different

- **Deterministic core** — same request + data ⇒ same bytes (reproducible `run_id`, no clock). Judges can re-run and verify.
- **Discovery, not curation** — the Offline Candidate Screen nominates genuinely new windows with provenance; a QA rule proves they weren't just re-ranked from a hand-picked pool.
- **Test↔site duality** — the same model answers "best site for this test" *and* "which tests can this site support."
- **Honest limits by construction** — proxies stay provisional, missing data is never zeroed, and domains we don't cover are stated plainly.
- **A grounded AI agent** — physically cannot fabricate a characteristic value; it must call the engine and cite sources.

## Quick start

```bash
# 1. install (uv manages Python 3.12)
make setup

# 2. build the synthetic data bundle (mirrors the real schema; real data lands 13 Nov)
make synthetic

# 3. run the checks
make ci

# 4. run the API
make serve           # http://localhost:8000/docs

# 5. run the frontend (separate shell)
cd frontend && npm install && npm run dev   # http://localhost:3000
```

The AI agent (`/agent/chat`) needs `ANTHROPIC_API_KEY`; everything else runs without it. Copy `.env.example` → `.env`.

## Layout

```
api/openapi.yaml            # the contract
config/                     # declarative targets, tests, characteristics, sources, pool
src/analog_compass/
  engine/  pipeline/  discovery/  suitability/  kb/  api/  agent/
scripts/                    # checkers, synthetic generator, inspector
data/synthetic/             # generated bundle
frontend/                   # Next.js + MapLibre
docs/                       # Obsidian vault — architecture & specs
```

## Status

Design ~95% (inherited + completed); implementation in progress. Runs today on a **synthetic bundle**; swapping in the real dataset is a `data_mode=real` flip. See [`docs/09_WORK_PLAN.md`](docs/09_WORK_PLAN.md).

## License

MIT (code). Data layers retain their own licences — see `config/sources.yaml`.
