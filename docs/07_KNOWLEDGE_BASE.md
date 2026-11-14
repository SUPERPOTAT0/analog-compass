# 07 — Knowledge Base (targets & operations)

> Your request: a **dedicated knowledge base** of the atmospheric/environmental factors on each target, plus the **characteristics and requirements of every operation/test**, so the system can decide which tests fit a newly found site — and so the **AI agent** can reason, discuss and communicate about this domain accurately and scientifically.

The KB is the **domain brain**. It is declarative, cited, and tiered by verification — it never asserts a fact the system cannot back. It feeds three consumers: the engine/suitability (requirements), the discovery screen (requirement profiles), and the AI agent (grounding facts + citations).

## 1. Structure

```
config/
  targets.yaml      # target environments: Moon, Mars (+ sub-regions), per-characteristic + narrative facts
  tests.yaml        # operations/tests: requirements + rationale (see [[06_SUITABILITY_SPEC]])
kb/
  targets.py        # loads + validates target facts, exposes to engine & agent
  tests.py          # loads + validates test facts
data/kb/
  target_facts.md   # cited narrative facts, graded by verification depth
```

## 2. Target environment facts

Each target carries **(a) the per-characteristic machine values** the engine uses and **(b) a set of cited narrative facts** the agent can quote, each graded by how thoroughly it was verified.

```yaml
# config/targets.yaml (excerpt)
- target_id: mars_mid_latitude
  body: mars
  label: "Mars — mid-latitude mantled terrain"
  characteristics:
    temperature:   {kind: envelope, envelope: [-120, 20], tier: B, source_id: mars_climate}
    slope:         {kind: distribution, quantiles_ref: mars_slope_q, tier: B, source_id: mola}
    dust_aerosol_load: {kind: scalar, value: 0.4, unit: opacity, tier: C, source_id: mars_dust,
                        note: "opacity vs Earth AOD 550nm — conversion required"}
    permafrost_index:  {kind: requirement, note: "ground ice plausible; proxy only"}
  facts:
    - id: mars_obliquity
      text: "Mars' axial obliquity is ~25.2°, close to Earth's, driving strong seasons."
      grade: verified
      source_id: mars_obliquity_ref
    - id: mars_dust_storms
      text: "Global dust storms can raise atmospheric opacity for weeks."
      grade: verified
      source_id: mars_dust_ref
- target_id: moon_polar
  body: moon
  label: "Moon — polar, permanently shadowed vicinity"
  characteristics:
    sunlit_fraction:  {kind: distribution, quantiles_ref: moon_pole_illum, tier: B, source_id: lola_illum}
    sun_elevation_max:{kind: scalar, value: 1.54, unit: deg, tier: A, source_id: moon_obliquity}
    temperature:      {kind: envelope, envelope: [-240, -50], tier: B, source_id: diviner}
  facts:
    - id: moon_obliquity
      text: "The Moon's obliquity to the ecliptic is ~1.54°, so polar crater floors stay in permanent shadow."
      grade: verified
      source_id: moon_obliquity_ref
```

**Grades:** `verified` (checked against a cited primary source), `cited` (from a named source, not independently rechecked), `asserted` (plausible, unverified — agent must hedge), `unknown` (missing). The agent's confidence language is driven by these grades ([[08_AI_AGENT]]).

## 3. Operation / test facts

Each test in `config/tests.yaml` ([[06_SUITABILITY_SPEC]]) carries a `rationale` (why each requirement matters physically) and `domains`. The KB exposes, per test: what it validates, which characteristics gate it, which are merely scored, and the honest caveat (e.g. *"permafrost here is a proxy for icy regolith; a pass is provisional"*). This is what lets the agent answer *"why would site X suit a cryo-drill trial?"* with physical reasoning, not vibes.

## 4. Narrative facts file (`data/kb/target_facts.md`)

Facts written in our own words, each with a `grade` and `source_id`, so the agent can cite without reproducing copyrighted text. Example rows:

| id | fact (our words) | grade | source |
|---|---|---|---|
| moon_obliquity | The Moon's ~1.54° obliquity keeps some polar crater floors permanently shadowed. | verified | lunar-fact-ref |
| mars_obliquity | Mars' ~25.2° obliquity is Earth-like, so it has pronounced seasons. | verified | mars-fact-ref |
| lava_tube_basalt | Lava tubes form in basaltic terrain; basalt presence is necessary but not sufficient. | cited | volcanology-ref |
| permafrost_proxy | Earth permafrost is a *terrestrial* ground-ice proxy for icy regolith, not a measurement of it. | asserted | internal |

## 5. Guarantees

- The KB **never** feeds a value into a Must gate above its evidence floor (a tier-C proxy stays provisional).
- Every agent-quotable fact has a `grade` and `source_id`; ungraded facts are not exposed.
- The KB is validated by `scripts/check_config_crossrefs.py`: every `source_id` resolves, every characteristic referenced by a test/target exists in `config/characteristics.yaml`, every domain in `config/domains.yaml`.

See next: [[08_AI_AGENT]].
