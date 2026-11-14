# 03 — Engine Specification

The engine is a **pure, deterministic** function. No I/O, no clock, no randomness without an explicit seed. Given the same request and data version it returns the same bytes. All user-visible phrasing comes from the templates in §10 — the engine never free-writes prose.

## 1. Inputs (frozen)

An `EngineRequest` carries:

- `target`: the resolved target, per-characteristic (`TargetCharacteristic`: `kind`, value(s), `role`, `tier`, or `missing`).
- `test`: the resolved test/operation template — which characteristics are **Must** vs **Scored**, their `weight`, `tau` (tolerance), and any `requirement` (for threshold kinds).
- `sites`: a list of `SiteObservation`s, each per-characteristic (`kind`, sampled values / quantiles / scalar, `tier`, `missing` flag, `source_id`).
- `params`: `n_draws`, `seed_material`, tolerances defaults, `scale_warning_band_add`, verdict thresholds.
- `data_version`: string pinned to the bundle.

All inputs are frozen dataclasses. The engine mutates nothing.

## 2. Characteristic roles

| Role | Scored? | Gated? | Appears in API? |
|------|---------|--------|-----------------|
| **Must** | contributes **and** gated | yes | yes |
| **Scored** | contributes | no | yes |
| **Setup** | never | never | **yes** — context the planner needs, with status `setup`, but it does not move the score |

Setup controls (e.g. logistics flags, access notes) appear so the planner sees the full picture, but they are explicitly not part of the number. Scoring them would smuggle un-vetted judgement into the result.

## 3. Evidence tiers

Each value has a tier: **A** (`measured`/directly observed), **B** (`derived` by a documented function), **C** (`proxy`). Rule: **a `proxy` (tier C) value can never, by itself, satisfy a Must gate** — at best it yields a *provisional* pass that is downgraded and flagged. This is a hard guardrail against dressing up weak evidence as a hard match.

## 4. Missing-data policy

Missing is **never zero** and **never a match**. Specifically:

- **Target lacks a Must characteristic** → that characteristic's requirement is unusable; the **site cannot be gated** on it → the site is `blocked` for this test with reason `target_missing_must`. (We refuse to pass a hard requirement we cannot define.)
- **Target lacks a Scored characteristic** → that characteristic is **dropped from the weighted sum for every site** and its weight removed from the denominator (so one missing target value does not make every site show a missing component). The result notes the reduced coverage.
- **Site lacks a characteristic** → that characteristic's match is `missing` for that site; a Must → that site is `excluded` (reason `site_missing_must`); a Scored → dropped from that site's weighted sum (weight removed from its denominator) and flagged, lowering coverage/confidence.

No silent fallbacks. No bare `except`. Any ambiguity stops and is written to [[QUESTIONS]].

## 5. Match functions

`tau` is the characteristic's tolerance. `Q_T`, `Q_s` are 101-value quantile arrays (levels 0…100%). Returns a match `m ∈ [0, 1]`.

| Kind | Formula | Notes |
|---|---|---|
| **distribution** | `d = mean_{k=0..100} |Q_T[k] − Q_s[k]|`, `m = max(0, 1 − d/tau)` | `d` is the 1‑D Wasserstein‑1 distance. Same unit both sides or the build fails. |
| **scalar** | `m = max(0, 1 − |x_T − x_s| / tau)` | |
| **ordinal** | `m = max(0, 1 − |idx_T − idx_s| / tau)` | `tau` in classes; `idx` is the position in `scale`. |
| **set** | `m = |T ∩ S| / |T|` | If `T` is empty the characteristic is `ignore`. |
| **envelope** (temperature) | `lo = Q_s[1]`, `hi = Q_s[99]`, `[r0,r1]=envelope`, `m = max(0, min(hi,r1) − max(lo,r0)) / (r1 − r0)` | Fraction of the required range the site's 1st–99th pct range covers. `tau` unused. |
| **threshold_min** (requirement) | `m = 1` if `x_s ≥ r`, else `max(0, 1 − (r − x_s)/tau)` | The **test** sets a requirement `r` (e.g. isolation ≥ a travel time), not a measured target. `r` from the template rule's `requirement.value`; `tau` the rule's fixed tolerance. Null `r`/`tau` ⇒ treated as missing target data (§4). |
| **threshold_max** (requirement) | `m = 1` if `x_s ≤ r`, else `max(0, 1 − (x_s − r)/tau)` | Ceiling, e.g. vegetation cover ≤ a stated percent. |

**Band.** `b = max(band_site, band_target)`. If `scale_warning` is true, `b = b + params.scale_warning_band_add`. The band is the per-characteristic uncertainty half-width used by the Monte Carlo (§6).

## 6. Monte Carlo and gates

For `n_draws` draws (default in `config/params.yaml`):

1. **Draw** a perturbed value for each characteristic within its band `b` using a **triangular distribution** centred on the nominal value, lower/upper limits `nominal ∓ b`, mode = nominal. (Triangular is bounded and needs no extra scale parameter — honest about "we know it's within ±b, most likely the nominal".) Distribution-kind characteristics are perturbed by shifting the quantile array by the drawn offset.
2. **Evaluate gates inside this draw.** Each Must characteristic has a gate (a `threshold`/interval). A draw **passes** the gate iff the drawn value satisfies it. Gates are evaluated **per draw** — never once on the nominal — so that a value whose uncertainty interval *straddles* the gate is correctly reflected as "passes some of the time."
3. **Score the draw**: weighted mean of Scored matches (missing dropped from the denominator per §4). Gate failures mark the draw as failing the Must set.

**Why gates inside every draw:** evaluating a gate once on the nominal throws away uncertainty. A site whose slope is `gate ± noise` would be reported as a clean pass or clean fail, when the truth is "borderline — passes p% of the time." Per-draw gating is what makes the `borderline` verdict meaningful.

## 7. Verdict

Let `p_gate` = fraction of draws that pass **all** Must gates. Let `score` = mean weighted Scored match over draws that passed the gates (with confidence band from the draw spread).

- `p_gate ≥ params.pass_gate` **and** `score ≥ params.pass_score` → **`pass`**
- `p_gate ≤ params.exclude_gate` → **`excluded`** (reason: the Must set fails almost always)
- otherwise → **`borderline`**

**Worked example — Site C is `borderline`, not `excluded`:** Site C's Must characteristic (say slope) has a nominal value whose uncertainty interval **straddles the gate**. Across draws it passes the gate in, e.g., ~55% of them — above `exclude_gate` but below `pass_gate`. So the Must set neither clearly holds nor clearly fails ⇒ **borderline**. If instead the whole interval sat on the failing side (`p_gate ≤ exclude_gate`), it would be `excluded`. This is the canonical check in `tests/fixtures/golden_worked_example.json`.

Any Must that is a **proxy (tier C)** can at best yield a **provisional pass** which caps the verdict at `borderline` and attaches the honest-limit note `proxy_must` (§3).

## 8. Determinism — `run_id` and `seed`

- `seed = int.from_bytes(blake2b(canonical_json(request) + data_version)[:8])`. Canonicalisation sorts keys and normalises floats, so logically-equal requests produce the same seed.
- `run_id = hex(blake2b(canonical_json(request) + data_version + engine_version)[:16])`.
- The RNG is seeded per run (`numpy.random.default_rng(seed)`). **No wall-clock, no entropy source.** The response body carries **no timestamp** — a timestamp would break byte-equality of identical runs and is metadata, not result. (Timestamps, if needed, live in transport headers/logs, not the body.)

## 9. Outputs

Per site: `verdict`, `p_gate`, `score` + band, per-characteristic `{kind, match, status (ok|missing|setup|proxy), tier, source_id, contribution}`, a list of **honest-limit notes**, and `candidate_kind` (`curated` | `new`). Plus run metadata: `run_id`, `seed`, `data_version`, `data_mode`, `engine_version`, coverage (fraction of intended weight actually used).

## 10. User-visible text templates

All phrasing the user sees is assembled from a fixed template table (keyed note ids → sentences with slots), e.g.:

- `proxy_must` → "Passes only on proxy evidence for {characteristic}; treat as provisional."
- `site_missing_must` → "Excluded: no data for required {characteristic}."
- `straddles_gate` → "Borderline: {characteristic} meets the gate in {p_gate_pct}% of draws."
- `coverage_reduced` → "Scored on {coverage_pct}% of the intended characteristics; {n} dropped for missing data."
- `outside_coverage` → "{characteristic} is outside the layer's coverage here; reported as missing."

**Banned words** (never emitted by engine or agent): hype/absolutes that overstate evidence — e.g. *perfect*, *identical to Mars*, *exactly like the Moon*, *guaranteed*, *proven* (unless citing a measured tier-A fact). The agent inherits this list ([[08_AI_AGENT]]).

## 11. Purity contract (enforced by tests)

- No module under `engine/` imports `os`, `time`, `datetime`, `random`, `requests`, or `open`.
- Every public engine function is referentially transparent given its inputs.
- The golden test recomputes two numbers by hand and asserts byte-equal output across two runs.

See next: [[04_DISCOVERY_SPEC]].
