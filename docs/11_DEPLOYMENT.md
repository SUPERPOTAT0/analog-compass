# 11 — Deployment, Infrastructure & Security

## 1. Topology

```
 Browser ──HTTPS──▶ Vercel Edge/CDN
                      │
          ┌───────────┴────────────┐
          ▼                        ▼
  Next.js frontend           Python API (FastAPI)
  (App Router, SSR/ISR)      Vercel Fluid Compute (Python 3.12)
          │                        │
          │                        ├─ engine (pure, in-process)
          │                        ├─ pipeline + bundle (read-only volume / object store)
          │                        ├─ discovery + suitability
          │                        └─ agent ─▶ Claude (via Anthropic SDK / Vercel AI Gateway)
          └───────── SSE stream (agent chat) ────────┘
```

Both deploy on **Vercel**: Next.js natively; the FastAPI app as Python **Fluid Compute** functions (full Node-free Python runtime, 300 s default timeout, instance reuse → low cold starts). Alternative: containerise the API (Dockerfile provided) for any OCI host — the API is a plain ASGI app with no Vercel lock-in.

## 2. Environments

| Env | Branch | Data mode | Notes |
|-----|--------|-----------|-------|
| Preview | every PR | `synthetic` | Vercel preview URL per PR; safe, no secrets beyond a scoped agent key. |
| Staging | `main` | `synthetic` | Full system on synthetic bundle; eval battery runs here. |
| Production | release tag | `real` once 13 Nov data is in and QA passes | `data_mode=real`, Q-19 enforced. |

## 3. Configuration & secrets

- All config via env (`src/analog_compass/settings.py`, Pydantic settings). **No secrets in code or git.**
- `ANTHROPIC_API_KEY` (agent) — scoped, rotatable. Optionally front with **Vercel AI Gateway** for observability, spend caps, and model fallback.
- `DATA_BUNDLE_URI`, `DATA_MODE`, `DATA_VERSION` pin the dataset.
- `vercel env pull` for local parity; `.env.example` lists every variable name (never values).

## 4. CI/CD

- **GitHub Actions** runs `make ci` (lint, type, spec-check, config-check, unit, contract) on every PR. Merge blocked on green.
- Vercel builds preview deploys per PR; production promotion is manual/tagged.
- `make freeze` stamps `data_version`/`engine_version`; `make deploy` / `make rollback` wrap the platform CLI (placeholders until T-051).

## 5. Scaling & performance

- **Engine** is embarrassingly parallel across candidates and Monte Carlo draws (vectorised in NumPy); a compare over ~50 candidates returns sub-second warm.
- **Discovery** tiles the grid; Stages 0–1 are cheap filters that shed millions of windows before the expensive stages; results cached per `(bundle, target, test)` via the runtime cache.
- **Stateless API** scales horizontally; Fluid Compute reuses instances to amortise bundle load.
- Large rasters live in object storage (read-only), memory-mapped; never bundled into the function.

## 6. Security posture

- Least privilege: the API is read-only over data; the agent's tools are read-only; no tool can write, deploy, or make arbitrary network calls.
- No restricted/licensed raw data in git; only descriptors + source registry. Licence check (`make licence-check`) gates any dataset.
- Input validation at the contract boundary (Pydantic); strict CORS; rate limiting / Vercel Firewall + BotID on public endpoints.
- Determinism aids audit: any result can be re-derived from `run_id` + request + `data_version`.
- Secret scanning in pre-commit and CI.

## 7. Observability

- Structured JSON logs keyed by `run_id`; agent tool-calls traced.
- QA reports persisted per bundle; discovery provenance persisted per run.
- Web analytics + runtime error capture on the frontend/API (platform-native).

See next: [[12_FRONTEND]].
