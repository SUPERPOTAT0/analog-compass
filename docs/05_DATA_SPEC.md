# 05 — Data Specification

> Real data is released on **13 November** and is unread until then. The system is built against a **synthetic bundle** that mirrors the expected schema exactly. Nothing here claims a dataset we have not verified; unverified items are marked and tracked in [[QUESTIONS]].

## 1. Principles

1. **One grid, one algorithm.** All derived characteristics (slope, roughness, …) come from one function on the same ~30 m analysis grid, regardless of body. **Resampling to the grid uses one method for every DEM: GDAL area averaging**, recorded in `method_id`. (In the synthetic drop, resampling method moved slope p50 by ratios of 0.82–0.90 of the latent value across nearest/bilinear/cubic/average — large next to match tolerances, so the method must be fixed and recorded.)
2. **Self-describing bundles.** A bundle is rasters + per-layer **descriptors** + a **source registry**. The pipeline validates every descriptor before use.
3. **Evidence tiers travel with values.** `measured` (A) / `derived` (B) / `proxy` (C). See [[03_ENGINE_SPEC]] §3.
4. **`data_mode`.** `synthetic` or `real`. **`real` forbids any synthetic fallback** — a missing real layer is `missing`, never backfilled from synthetic. A **partial real bundle** (some layers real, some absent) is allowed: present layers are used; absent ones are `missing` and reduce coverage.

## 2. Characteristic layers

Columns: id · kind · unit/shape · target source (Moon/Mars) · how the Earth value is derived · evidence/tier · verification status.

| Characteristic | Kind | Unit / shape | Target source | Earth derivation | Evidence / tier | Verified |
|---|---|---|---|---|---|---|
| `slope` | distribution | degrees, quantiles | DEM-derived both bodies | From Earth DEM on 30 m grid | derived, B | product-dependent |
| `roughness` | distribution | m, quantiles | DEM-derived | From Earth DEM | derived, B | product-dependent |
| `temperature` | envelope | °C range | Target climatology | Earth LST climatology, window range | derived, B | partly |
| `sunlit_fraction` | distribution | fraction, per month | Moon: LOLA polar illumination (PGDA product 69, 240 m, 18.6‑yr avg; semantics to confirm) | Computed from Earth DEM + solar position + horizon mask per month; atmosphere ignored | derived, B | lunar maps verified |
| `sun_elevation_max` | scalar | deg, per month | Moon: analytic from lunar obliquity 1.54° (verified) + local slope | Analytic from latitude + date window | derived, B | obliquity verified |
| `permafrost_index` | scalar | index 0–1 | Requirement threshold (ground ice in shadowed regions; no verified direct data) | Global Permafrost Zonation Index, 30″, excl. Antarctica (verified); NH 1 km TTOP as secondary (verified). Window median | **proxy, C** (proxy for ground ice; pass provisional). `.hdr` has no CRS → descriptor sets one with justification | products verified; proxy meaning |
| `basaltic_volcanic_fraction` | scalar | fraction | Requirement threshold | GLiM lithology (16 first-level classes; 0.5° PANGAEA grid + vector original; CC BY 3.0, verified): fraction of window in the basic-volcanic class | **proxy, C** (terrain where lava tubes *can* form, not that they exist) | product verified; proxy |
| `cave_evidence` | ordinal | scale (placeholder, OPEN-12) | Mars: USGS **Mars Global Cave Candidate Catalog** (public domain, verified to exist). Moon: pit catalogue **not** verified | Curated from literature in `pool.yaml` with citations | curated | Mars catalogue verified |
| `dust_aerosol_load` | scalar | optical depth | Requirement threshold (Earth AOD 550 nm vs Mars dust opacity differ in wavelength → documented conversion needed) | MERRA‑2 aerosol diagnostics, 0.5°×0.625°, monthly (product family verified; variable names to confirm). Window mean | derived (model), B, coarse | partly |
| `wind_speed_mean` | scalar | m/s | Requirement threshold | MERRA‑2 single-level wind (product/variable names to confirm). Window mean | derived (model), B, coarse | product name unverified |
| `vegetation_cover` | scalar | percent | Requirement threshold (life-limited environment) | MODIS Vegetation Continuous Fields **MOD44B**, yearly 250 m (verified; real files are HDF → GDAL adapter). Window median | **proxy, C** (proxy for life-limited conditions, not a habitability measurement) | product verified; no use restrictions |
| `remoteness_time` | scalar | minutes | Requirement threshold (isolation) | Global travel-time-to-cities, 1 km, 85°N–60°S, 2015 (verified). Window median; outside band → `missing`/`outside_coverage` | derived, B | product verified |

> **Confirmed, licence-clear datasets:** MOD44B vegetation (no use restrictions); GLiM lithology (CC BY 3.0); Mars Global Cave Candidate Catalog (public domain, USGS); LOLA polar illumination (PGDA 69); Global Permafrost Zonation Index (30″); travel-time-to-cities (1 km). MERRA‑2 variable names and several target-side semantics are **to confirm** on data day — see [[QUESTIONS]].

## 3. Challenge-domain coverage map (`config/domains.yaml`)

| Domain | Covered by | Status |
|---|---|---|
| Terrain / morphology | `slope`, `roughness` | covered |
| Thermal | `temperature`, `sun_elevation_max` | covered |
| Illumination | `sunlit_fraction`, `sun_elevation_max` | covered (Moon polar) |
| Lithology | `basaltic_volcanic_fraction` (proxy) | covered (proxy) |
| Caves / lava tubes | `cave_evidence`, `basaltic_volcanic_fraction` | partial (proxy + curated) |
| Remoteness / operations | `remoteness_time` | covered |
| Biology / habitability | `vegetation_cover` (proxy) | **proxy only — not a habitability claim** |
| Dust & wind | `dust_aerosol_load`, `wind_speed_mean` | partial (coarse, model) |
| Subsurface | — | **not covered** |
| Earth processes | — | **not covered** |

What we do **not** cover is stated plainly here and in [[13_CHALLENGE_ALIGNMENT]]; the pitch must not claim it.

## 4. Descriptors

Each layer ships a descriptor:
```yaml
layer_id: slope
kind: distribution
unit: degree
grid: analysis_30m
method_id: gdal_area_average
source_id: dem_srtm_v3            # → config/sources.yaml
evidence_class: derived           # measured | derived | proxy
tier: B
coverage_bbox: [-180, -56, 180, 60]
crs_override: null                # if set, carries a justification (QA Q-17)
nodata: -9999
value_semantics: "slope in degrees on 30 m grid"
```

## 5. Data pipeline

1. **Load** the bundle; validate every descriptor against the schema. Missing descriptor ⇒ blocking error (no guessing).
2. **Aggregate** each site/candidate window → quantile arrays (distribution kinds) or scalars (scalar/ordinal), with `missing` where `nodata`/outside coverage. Pure given the arrays (so it is unit-testable and feeds the pure engine).
3. **QA** gates run and produce a persisted QA report (see §6).
4. **Emit** `SiteObservation`s for the engine, each value carrying `tier`, `source_id`, `missing`.

The **reference inspector** (`pipeline/inspect.py`) defines the report shape that the real-data inspector (ticket T‑044) must reproduce and independently proves every file in a drop is readable.

## 6. QA rules (blocking / warning)

| Id | Rule | Severity |
|---|---|---|
| Q-15 | Every scored characteristic maps to a source in `config/sources.yaml` | Blocking |
| Q-16 | Resampling sensitivity: for every DEM layer, slope p50 under two resampling methods is compared; ratio outside 0.85–1.15 → human review | Warning |
| Q-17 | Every `crs_override` carries a written justification (e.g. the ESRI float grid with no CRS) and is listed in the QA report | Blocking |
| Q-18 | Every discovery nominee has a complete `provenance` record (AC-D4) | Blocking |
| Q-19 | `data_mode=real` ⇒ no layer sourced from the synthetic generator | Blocking |

## 7. Synthetic bundle

`scripts/make_synthetic.py` builds a small, shippable bundle that mirrors the real schema: same layer ids, kinds, units, descriptor fields, coverage boxes and nodata conventions. Coarse layers are generated from smooth latent fields (earlier white-noise made them incompressible at 56 MB; smoothing keeps them realistic and small). The synthetic bundle:

- lets the engine/pipeline/discovery run end-to-end today;
- powers the golden worked example and the discovery "found-unknown" test (AC-D3);
- is stamped `data_mode=synthetic` and can never leak into a `real` run (Q-19).

**Data day (13 Nov) plan:** point the loader at the real bundle, run `make data-inspect` → `qa-real` → golden recompute. Allowed changes on data day: source ids, resolutions, coverage boxes, variable-name confirmations. **Escalations** (stop + ask): any change to the contract, the engine math, a tolerance, or a characteristic's role/kind.

See next: [[06_SUITABILITY_SPEC]].
