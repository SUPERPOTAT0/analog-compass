# QUESTIONS — open items

Anything unclear or unverified is logged here instead of guessed. Ids are referenced from specs/configs.

## Resolved by the uploaded challenge reference (Earth_Analog_Finder_Challenge_Reference.md)

- **Q-RES-1** — ✅ The official brief + data sources are now in hand. Confirmed: search
  globally/systematically for NEW analogs (not rediscover famous ones); characterise across
  geology/terrain/thermal/illumination/water-ice/dust-wind/biology/caves-subsurface/ops;
  explain where the analogy breaks down; name Earth's fundamental limits; present as a
  map/visualization/tool. Our design already matches this (see [[13_CHALLENGE_ALIGNMENT]]).

## Still open / to confirm against the provided portals

- **Q-DATA-1** — The provided data are open **portals** (Earthdata, Worldview, PDS, LRO
  Diviner/LOLA, Copernicus/Sentinel, RADARSAT, JAXA), not one structured drop. "Real" mode
  means ingesting specific products from these via the pipeline adapters, then
  `make data-inspect` → `qa-real` → golden recompute. More resources may be added before the
  hackathon. *Owner: pipeline adapters per portal.*

## To confirm on data day (allowed, non-escalating)

- **OPEN-07** — MERRA‑2 exact product + **variable names** for `dust_aerosol_load` and `wind_speed_mean`.
- **OPEN-08** — LOLA polar-illumination **value semantics** (PGDA product 69): what the stored fraction means per pixel.
- **OPEN-09** — Earth AOD (550 nm) → Mars dust-opacity **conversion**: find/cite a documented relation or keep `dust` as scored-only with a caveat.
- **OPEN-10** — Moon **pit/cave catalogue** source (Mars catalogue verified; lunar not). If none verified, `cave_evidence` for Moon stays curated-with-caveat.
- **OPEN-12** — `cave_evidence` **ordinal scale** definition (currently a placeholder); needs a cited basis before it gates anything.
- **OPEN-13** — Confirm `temperature` climatology source for each target and the LST product for Earth.

## Escalations (must stop + ask before changing)

Any change to `api/openapi.yaml`, the engine math, a tolerance, or a characteristic's role/kind is an escalation — not a data-day edit. ([[05_DATA_SPEC]] §7, [[10_PM_PROCESS]] rule 4.)

## Resolved

- **R-01** — Discovery vs re-ranking: resolved by the Offline Candidate Screen + novelty exclusion + provenance ([[04_DISCOVERY_SPEC]]).
- **R-02** — Test↔site duality: resolved by the suitability matrix ([[06_SUITABILITY_SPEC]]).
- **R-03** — Missing-target-data making every site show a missing value: resolved by dropping the characteristic from the weighted denominator for all sites ([[03_ENGINE_SPEC]] §4).
