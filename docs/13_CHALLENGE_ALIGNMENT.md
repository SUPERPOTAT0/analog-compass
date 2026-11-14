# 13 — Challenge Alignment

Maps the brief to the design, and states plainly what we do **not** cover. The pitch must not claim the uncovered domains.

## 1. Brief → design

| Brief expectation | How Analog Compass meets it | Where |
|---|---|---|
| Find Earth analogues for a Moon/Mars target | Compare engine ranks candidate sites per target | [[03_ENGINE_SPEC]] |
| **Test-led**, evidence-based | Tests impose requirements/gates; every value carries source + tier | [[06_SUITABILITY_SPEC]], [[05_DATA_SPEC]] |
| **Honest limits** — where an analogue breaks down | Per-site honest-limit notes; `borderline`; proxy caps; domains-not-covered | [[03_ENGINE_SPEC]] §7/§10 |
| **Discover new analogues anywhere on Earth** (not re-rank known) | Offline Candidate Screen over global rasters, provenance, novelty exclusion | [[04_DISCOVERY_SPEC]] |
| Determine which tests a site can support | Suitability matrix (test↔site duality) | [[06_SUITABILITY_SPEC]] |
| Produce a **map** | GeoJSON export + MapLibre frontend | [[12_FRONTEND]] |
| Cover the challenge domains | Terrain, thermal, illumination, lithology, caves, remoteness, biology(proxy), dust/wind | [[05_DATA_SPEC]] §3 |
| Reproducible / trustworthy | Deterministic engine, `run_id`/`seed`, no timestamp, golden tests | [[03_ENGINE_SPEC]] §8/§11 |
| Natural-language analysis | Grounded AI geologist agent | [[08_AI_AGENT]] |

## 2. Domains we cover (and how strongly)

- **Terrain/morphology** — `slope`, `roughness` (DEM-derived, tier B): strong.
- **Thermal** — `temperature` envelope, `sun_elevation_max`: good.
- **Illumination** — `sunlit_fraction` (Moon polar), `sun_elevation_max`: good for polar.
- **Lithology** — `basaltic_volcanic_fraction` (GLiM, **proxy**): indicative.
- **Caves/lava tubes** — `cave_evidence` (curated + Mars catalogue) + basalt proxy: partial.
- **Remoteness/operations** — `remoteness_time` (travel-time, tier B): good within coverage.
- **Biology/habitability** — `vegetation_cover` (**proxy** for life-limited conditions): *indicative only, not a habitability measurement.*
- **Dust & wind** — `dust_aerosol_load`, `wind_speed_mean` (MERRA‑2, coarse model): partial.

## 3. Domains we do **NOT** cover — stated plainly

- **Subsurface** (beyond a permafrost/ground-ice *proxy*) — no borehole/geophysics layer.
- **Earth processes** (active tectonics/erosion dynamics as such) — not modelled.
- **Dust & wind** only partially (coarse, model-derived; Earth AOD ≠ Mars opacity without a documented conversion).
- **Biology/habitability** only via a vegetation **proxy** — we make no habitability claim.

These are listed so the demo and agent decline them rather than bluff. The AI agent refuses out-of-scope domains ([[08_AI_AGENT]] §7).

## 4. Fundamental Earth limits (the brief asks us to name these)

The official brief is explicit: *"Earth cannot reproduce important lunar and Martian conditions such as reduced gravity, the lunar vacuum, the thin Martian atmosphere, or their radiation environments. Recognizing these differences is part of good scientific analysis."* Analog Compass treats these as **non-analogous by construction** — we never score them and never imply a site reproduces them:

- **Reduced gravity** (Moon ~1/6 g, Mars ~3/8 g) — no Earth surface site is an analog; flagged as a standing limit.
- **Vacuum (Moon) / thin CO₂ atmosphere (Mars)** — Earth's atmosphere differs fundamentally; our `dust`/`wind` layers are *process* analogs only, not pressure analogs.
- **Radiation environment** — no surface-radiation layer; stated as uncovered.
- **Regolith/vacuum weathering, electrostatic dust** — not reproduced.

The AI agent surfaces these limits when a user over-claims a match ([[08_AI_AGENT]] §5), and the UI shows them as standing caveats. This turns a weakness into exactly the "good scientific analysis" the brief rewards.

## 5. Challenge-provided data → our layers

The brief provides open **portals**, not one dataset. Mapping:

| Provided portal / product | Agency | Used for |
|---|---|---|
| NASA Earthdata Search / Worldview | NASA | discovery of Earth layers (vegetation, thermal, aerosols) |
| NASA PDS | NASA | Moon/Mars reference data |
| LRO **Diviner** | NASA | **lunar surface temperature** (`temperature` Moon target) |
| LRO **LOLA** | NASA | lunar topography + **polar illumination** (`sunlit_fraction`) |
| ESA Copernicus / **Sentinel** | ESA | SAR/optical — future lithology/terrain/aeolian layers |
| CSA **RADARSAT** / RCM SAR | CSA | roughness / surface / ice — future layers |
| JAXA G-Portal | JAXA | precipitation/snow/vegetation — future layers |

Earth-side products we derive (GLiM lithology, MODIS VCF, permafrost PZI, MERRA‑2, travel-time) are open datasets obtained via these portals and other open sources, as the brief permits ("data obtained locally"). See `config/sources.yaml`.

## 6. Unverified items gating the final claim

See [[QUESTIONS]] — the Resources tab may add more resources before the hackathon, and several Earth-side product details (MERRA‑2 variable names, exact DEM/LST products) and Moon-side semantics are "to confirm" against the portals above.
