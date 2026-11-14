# 06 — Suitability Matrix (test ↔ site)

> Your idea: use the **core characteristics of each test** both to *discover* sites and to *identify which tests a site can support*. This document specifies the **suitability matrix** — the test↔site dual of the compare engine.

## 1. The duality

- **Compare** answers: *given a target × test, how do sites rank?*
- **Suitability** answers: *given a site, which tests can it support, and why?*

Both use the **same** requirement templates (`config/tests.yaml`), the **same** match functions and the **same** gate logic ([[03_ENGINE_SPEC]]). Suitability is just the compare engine evaluated across **all tests** for a **fixed site**, then summarised into a per-test verdict with reasons.

## 2. Test requirement template (`config/tests.yaml`)

Each test/operation is declarative:
```yaml
- test_id: cryo_drill_trial
  label: Cryogenic / permafrost drilling trial
  domains: [subsurface_proxy, thermal, operations]
  rationale: "Validates a percussive/cryo drill in frozen ground analogous to icy regolith."
  requirements:
    - characteristic: permafrost_index
      role: must
      kind: threshold_min
      requirement: {value: 0.5, tau: 0.2}
      evidence_floor: C         # proxy allowed but caps verdict at borderline
    - characteristic: slope
      role: must
      kind: distribution_gate
      gate: {stat: p50, max: 15}   # degrees
      tau: 5
    - characteristic: remoteness_time
      role: scored
      kind: threshold_min
      requirement: {value: 120, tau: 120}   # minutes
      weight: 0.3
    - characteristic: temperature
      role: scored
      kind: envelope
      weight: 0.7
  setup:
    - characteristic: logistics_access
      note: "Road/airstrip access within a day is desirable but not scored."
```

The catalogue covers the operation types the brief implies (illustrative, extensible): `life_detection_assay`, `rover_traverse_autonomy`, `pneumatic_regolith_drill`, `cryo_drill_trial`, `lava_tube_exploration`, `eva_procedure_rehearsal`, `thermal_cycling_hardware`, `dust_mitigation_test`, `sample_caching_protocol`, `isru_regolith_processing`. Each lists its domains, rationale, and requirements. Every requirement cites why it matters in `rationale` so the AI agent and UI can explain it.

## 3. Suitability computation

For a fixed site `s`:

```
for each test t in tests.yaml:
    req = resolve(t, target)                      # some requirements reference the target
    result[t] = engine.evaluate(site=s, target=target, test=t)   # same engine
suitability(s) = {
    supported:  [t for t if result[t].verdict == pass],
    borderline: [t for t if result[t].verdict == borderline],
    unsupported:[t for t if result[t].verdict == excluded],
    reasons:    {t: result[t].honest_limits + driving characteristics}
}
```

Output per (site, test): `verdict`, the **driving characteristic(s)** (largest positive/negative contributions), the **limiting characteristic** (the one that caps it), and honest-limit notes — so the UI can say *"Supports cryo-drilling (permafrost gate met in 88% of draws); limited for life-detection (vegetation cover too high)."*

## 4. Why this matters for discovery

A newly discovered window is far more actionable as *"this window can support cryo-drill + rover-autonomy trials"* than as *"generic Mars-like terrain."* Discovery ([[04_DISCOVERY_SPEC]]) and suitability are the same requirement-space computation from opposite ends, so a nominee automatically arrives with its supported-test profile.

## 5. Acceptance criteria

- **AC-S1** — For every curated pool site, the suitability matrix returns a verdict for every test in `tests.yaml`, with a non-empty reason for each non-pass.
- **AC-S2** — A test whose Must requirement references a characteristic the site is `missing` yields `excluded`/`site_missing_must`, never a silent pass.
- **AC-S3** — Changing a single requirement tolerance changes only the affected test's verdict (isolation of templates).
- **AC-S4** — A proxy-only Must (e.g. `permafrost_index`) can never report `pass`, only `borderline` with `proxy_must` (tier-C rule).
- **AC-S5** — Suitability(site) for test `t` equals Compare(target, t) restricted to that site (duality is literally the same engine call).

See next: [[07_KNOWLEDGE_BASE]].
