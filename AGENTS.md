# AGENTS.md — how to work in this repository

This file governs any automated or human contributor. Read it before writing code. The full design lives in `docs/` (start at `docs/00_INDEX.md`).

## 1. What this project is

**Analog Compass**: a stateless Python API + a pure scoring engine + a data pipeline + a discovery engine + a grounded AI agent, that help a field-campaign lead choose Earth test sites for a Moon/Mars target. Accuracy and honesty matter more than speed.

## 2. Rules that never bend

1. Never invent science, data, citations, dataset names, resolutions, licences or coordinates. Mark unknowns as `missing`/`null` and ask in `docs/QUESTIONS.md`.
2. Missing data is never zero and never a match. No silent fallbacks. No bare `except`.
3. `api/openapi.yaml` is the contract. Do not change it inside a feature ticket (only to fix a validation error you must report).
4. Tests first. Never loosen a tolerance or weaken a test to make it pass. If a test can only pass by changing a spec/contract/parameter — stop and ask.
5. The engine is pure: no I/O, no clock, no randomness without an explicit seed.
6. User-visible text only comes from the templates in `docs/03_ENGINE_SPEC.md` §10. Never use the banned words listed there.
7. Never commit secrets or restricted data. Read credentials from environment variables.
8. Do only the current ticket. No refactors outside it. No new dependency without a one-line reason + a licence check in the report.
9. If documents conflict or are unclear, stop and write the question in `docs/QUESTIONS.md`.
10. Report honestly. Never claim a test passed that you did not run.

## 3. Layout

See `docs/02_ARCHITECTURE.md` §3. Engine under `src/analog_compass/engine/` must stay pure (enforced by `tests/engine/test_purity.py`).

## 4–7. Build, test, review

- Dev setup: `uv sync --all-extras --group dev`.
- Everything runs through the `Makefile` (see §5 there and `make help`).
- `make ci` must pass before review: lint, type, spec-check, config-check, test, contract.
- Ticket lifecycle, report template and acceptance rules: `docs/10_PM_PROCESS.md`.

## 5. Make targets

| Target | Does |
|--------|------|
| `make doctor` | print tool versions; check required tools + env var NAMES exist (no secrets) |
| `make spec-check` | validate `api/openapi.yaml` + internal refs |
| `make config-check` | validate `config/*` cross-refs against docs + contract |
| `make test` | pytest |
| `make test-contract` | contract tests (prints "skipped until T-020" until the app exists) |
| `make ci` | lint + type + spec-check + config-check + test + test-contract |
| `make synthetic` | build the synthetic bundle |
| `make data-inspect` | run the reference inspector on a bundle |
| `make serve` | run the API locally |

Later-ticket targets (`bundle-real`, `qa-real`, `licence-check`, `spotcheck`, `smoke-real`, `freeze`, `deploy`, `rollback`) print "not implemented yet (ticket T-xxx)" and exit 1 until implemented. They are not part of `make ci`.
