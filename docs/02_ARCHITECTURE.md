# 02 — System Architecture

## 1. Design principles

1. **Pure, deterministic core.** The scoring engine is a pure function: no I/O, no clock, no unseeded randomness. This makes runs reproducible and testable, and lets the AI agent call it as a trustworthy tool. See [[03_ENGINE_SPEC]].
2. **Contract-first.** `api/openapi.yaml` is the single source of truth for the HTTP surface. Code conforms to it; it does not change inside a feature ticket.
3. **Provenance everywhere.** Every value carries a source id and an evidence tier. Every candidate carries where it came from. Nothing is invented.
4. **Stateless services.** The API holds no session state; everything needed to reproduce a run is in the request + the pinned data bundle.
5. **Synthetic-first, real-ready.** The system is developed against a synthetic bundle that mirrors the real schema exactly, so real data is a config flip, not a rewrite.
6. **Separation of concerns.** Engine (math) ⟂ pipeline (data) ⟂ discovery (search) ⟂ KB (domain facts) ⟂ API (transport) ⟂ agent (NL) ⟂ frontend (UX).

## 2. Component map

```
                         ┌──────────────────────────────────────────────┐
                         │                  FRONTEND                      │
                         │  Next.js (App Router) · MapLibre · shadcn/ui   │
                         │  Compare · Discover · Suitability · Ask (chat) │
                         └───────────────┬──────────────────────────────┘
                                         │ HTTPS (JSON + SSE stream)
                         ┌───────────────▼──────────────────────────────┐
                         │                 API (FastAPI)                  │
                         │  stateless · implements api/openapi.yaml       │
                         │  /compare /discover /suitability /sites        │
                         │  /targets /map.geojson /agent/chat (SSE)       │
                         └───┬───────────┬───────────┬───────────┬───────┘
                             │           │           │           │
            ┌────────────────▼─┐  ┌──────▼──────┐ ┌──▼─────────┐ ┌▼───────────────┐
            │   ENGINE (pure)  │  │  DISCOVERY  │ │ SUITABILITY│ │   AI AGENT     │
            │ match · gates ·  │  │ Offline     │ │ test×site  │ │ Claude +       │
            │ Monte Carlo ·    │  │ Candidate   │ │ matrix     │ │ tool-calling   │
            │ verdicts         │  │ Screen      │ │            │ │ (calls engine) │
            └───────▲──────────┘  └──────▲──────┘ └────▲───────┘ └──────▲─────────┘
                    │                    │             │                │
            ┌───────┴────────────────────┴─────────────┴────────────────┴─────────┐
            │                        PIPELINE + KB (data layer)                     │
            │  bundle loader · descriptors · window aggregation · QA gates          │
            │  Target KB (Moon/Mars) · Test/Operation requirements catalogue        │
            └───────────────────────────────▲──────────────────────────────────────┘
                                             │
                          ┌──────────────────┴───────────────────┐
                          │   DATA BUNDLE  (synthetic | real)      │
                          │  rasters + descriptors + source reg.   │
                          └────────────────────────────────────────┘
```

## 3. Repository layout

```
analog-compass/
├── AGENTS.md                      # how coding agents must behave (rules that never bend)
├── README.md
├── pyproject.toml                 # uv-managed; groups: runtime, dev, pipeline, agent
├── uv.lock
├── .python-version                # 3.12
├── Makefile                       # spec-check, config-check, test, ci, data-*, deploy…
├── .pre-commit-config.yaml        # ruff + secret scan
├── .github/workflows/ci.yml       # runs `make ci` on every PR
├── api/
│   └── openapi.yaml               # THE contract
├── config/                        # declarative, cross-checked by scripts/
│   ├── params.yaml                # engine params (draws, seed policy, tolerances…)
│   ├── characteristics.yaml       # characteristic registry (kind, unit, role, tier)
│   ├── targets.yaml               # Moon/Mars target definitions (seeded)
│   ├── tests.yaml                 # test/operation requirement templates
│   ├── domains.yaml               # challenge domains ↔ characteristics map
│   ├── sources.yaml               # data source registry (licence, resolution, used_for)
│   └── pool.yaml                  # curated candidate sites (with citations)
├── src/analog_compass/
│   ├── engine/                    # PURE: no I/O, no clock, no unseeded RNG
│   │   ├── match.py               # match functions (§5 of ENGINE_SPEC)
│   │   ├── gates.py               # gate evaluation
│   │   ├── montecarlo.py          # draws, seed derivation
│   │   ├── verdict.py             # pass/borderline/excluded
│   │   ├── score.py               # orchestration (compare one site vs target×test)
│   │   └── types.py               # frozen dataclasses / pydantic models
│   ├── pipeline/
│   │   ├── bundle.py              # load + validate a bundle (synthetic|real)
│   │   ├── descriptors.py         # per-layer descriptor schema
│   │   ├── aggregate.py           # window → quantiles/scalars (pure given arrays)
│   │   ├── inspect.py             # reference inspector (report shape)
│   │   └── qa.py                  # Q-rules (blocking/warning)
│   ├── discovery/
│   │   ├── screen.py              # Offline Candidate Screen
│   │   ├── nominate.py            # window nomination strategies
│   │   └── provenance.py          # candidate provenance records
│   ├── suitability/
│   │   └── matrix.py              # test×site suitability
│   ├── kb/
│   │   ├── targets.py             # target environment facts loader
│   │   └── tests.py               # test/operation requirement facts loader
│   ├── api/
│   │   ├── app.py                 # FastAPI app factory
│   │   ├── routes_*.py            # endpoint handlers
│   │   ├── schemas.py             # request/response models (match openapi.yaml)
│   │   └── geojson.py             # map export
│   ├── agent/
│   │   ├── tools.py               # engine/discovery/KB exposed as Claude tools
│   │   ├── prompts.py             # system prompt + guardrails
│   │   └── runtime.py             # agent loop (tool-use), streaming
│   └── settings.py                # env-driven config (no secrets in code)
├── scripts/
│   ├── spec_check.py              # validates openapi.yaml + internal refs
│   ├── check_config_crossrefs.py  # config ↔ docs ↔ contract cross-validation
│   ├── make_synthetic.py          # builds the synthetic bundle
│   └── inspect_bundle.py          # CLI around pipeline.inspect
├── data/
│   └── synthetic/                 # generated; small, smoothed, shippable
├── tests/
│   ├── fixtures/golden_worked_example.json
│   ├── engine/ …                  # unit + golden recompute
│   ├── pipeline/ …
│   ├── discovery/ …
│   └── contract/ …                # schemathesis-style contract tests
├── frontend/                      # Next.js app (see [[12_FRONTEND]])
└── docs/                          # this vault
```

## 4. End-to-end data flow

**Compare request** (`POST /compare`):

1. API validates the request against the contract and resolves `target_id`, `test_id`, and the candidate set (curated and/or discovered).
2. Pipeline loads the pinned **bundle**, aggregates each candidate's **window** into quantile arrays / scalars (with evidence tiers and `missing` flags). No fabrication: missing stays missing.
3. API builds a pure **engine request** (frozen inputs) and derives `run_id` + `seed` from `hash(request_canonical + data_version)` — **no clock**.
4. **Engine** runs: for each Monte Carlo draw it samples each characteristic within uncertainty, evaluates **gates inside the draw**, computes weighted matches, aggregates to a verdict with confidence bands.
5. API serialises the result to the contract shape: per-site verdict, per-characteristic evidence, honest-limits notes, and a GeoJSON map. The body carries **no timestamp** (determinism).

**Discover request** (`POST /discover`): the Offline Candidate Screen ([[04_DISCOVERY_SPEC]]) nominates new windows from global rasters, attaches provenance, then each nominee flows through the same steps 2–5 and is labelled `new candidate`.

**Ask** (`POST /agent/chat`, SSE): the agent plans, calls the engine/discovery/KB **tools**, and composes an answer strictly from their returns. See [[08_AI_AGENT]].

## 5. Technology stack & rationale

| Layer | Choice | Why |
|-------|--------|-----|
| Core language | **Python 3.12** | Scientific ecosystem; matches the inherited spec. |
| Packaging | **uv** + locked `uv.lock` | Fast, reproducible, dependency groups (runtime/dev/pipeline/agent). |
| Engine math | **NumPy** only (pure) | Determinism, speed, no heavy deps in the core. |
| API | **FastAPI** + Pydantic v2 | Contract-first, async, OpenAPI-native, SSE streaming. |
| Geospatial (pipeline) | **rasterio / pyproj / shapely** (pipeline group) | Real-data adapters; isolated from the pure engine. |
| AI agent | **Anthropic SDK** (Claude) with tool-use | Grounded tool-calling; see [[08_AI_AGENT]] and the `claude-api` reference. |
| Frontend | **Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + MapLibre GL** | Map-first UX, streaming chat, Vercel-native. |
| Deploy | **Vercel** (Next.js + Python Fluid Compute) | One platform, native Python functions, preview deploys. See [[11_DEPLOYMENT]]. |
| CI | **GitHub Actions** → `make ci` | Lint, type, spec-check, config-check, tests, contract tests. |

## 6. Non-functional requirements

- **Reproducibility:** identical request + data version ⇒ identical bytes (golden tests enforce it).
- **Performance:** a compare over ~50 candidates × default draws returns < ~1 s on a warm function; discovery over a region is batched/cached.
- **Scalability:** engine is embarrassingly parallel across candidates and draws; discovery tiled across windows; stateless API scales horizontally on Fluid Compute.
- **Security:** secrets only from env; no restricted data committed; least-privilege keys; agent cannot exfiltrate or act outside its read-only tools. See [[11_DEPLOYMENT]].
- **Maintainability:** strict typing (mypy), lint (ruff), small modules, contract + golden tests guarding behaviour.
- **Observability:** structured logs, per-run `run_id` correlation, QA reports persisted per bundle.

See next: [[03_ENGINE_SPEC]].
