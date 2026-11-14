Claude
/
The review found real issues, so I fixed them before giving you the prompt. The updated analog-compass-context-pack and analog-compass-openapi files carry the fixes. After the fixes, the API contract and all config files validate, and both checker scripts fail correctly when I feed them broken input.

The challenge confirms the core idea. A test-led, evidence-based comparison with honest limits matches what the brief asks for. It does not ask for one place that looks like the Moon or Mars, and it expects us to say where an analog breaks down.

The main gap was discovery. The brief wants a systematic search for new analogs, anywhere on Earth, and says not to just rediscover known sites. Our design had a hand-picked pool with no reproducible way to find new candidates.

Fix: I added an offline candidate screen. It nominates new windows, and the engine then judges them like any other site.
Provenance: each new candidate now carries where it came from (new API field and a QA rule).
Labelling: a site is called “new candidate” only if it was nominated. Otherwise it’s called “curated candidate”.
Priority: the screen is not on the cut list. Cutting it means we cannot claim to discover new analogs.
Other issues I found and fixed:

Scored characteristics with missing target data now downgrade automatically, instead of making every site show a missing value.
The rule for when a site pair is offered now has a defined baseline.
The triangular-draw formula and the ordering rules are now specified exactly.
Target definitions were missing and are now seeded.
I added a GeoJSON map export, since the brief asks for a map.
I mapped the brief to the design in docs/13_CHALLENGE_ALIGNMENT.md.
Gaps the brief lists that we do not cover (stated plainly in that file):

dust and wind
biology and habitability
subsurface
Earth processes
We must not claim them in the pitch.

Still unverified: I haven’t seen the Resources tab, so please paste its text and links into this chat. The official data is also unread until the 13th.

Here is the first prompt for your coding agent. It is also saved as docs/KICKOFF_PROMPT.md.

ROLE
You are the coding agent for the Analog Compass Core: a stateless Python API, scoring engine and data pipeline that helps a field-campaign lead choose Earth test sites for a Moon or Mars target. A project manager reviews every ticket you finish. A frontend and backend developer depends on your API contract, and real data arrives on 13 November. Accuracy and honesty matter more than speed.

STEP 1. READ (do not skim)
Open AGENTS.md and read it completely. Then read, completely and in the order AGENTS.md lists them, every document it names. Also read api/openapi.yaml, every file in config/ and scripts/, and tests/fixtures/golden_worked_example.json. Treat docs/design/* as background only. If anything in docs/design/ conflicts with the rest, the rest wins.

STEP 2. COMPREHENSION REPORT
Create reports/T-000-comprehension.md and print it in your reply. It must contain:
A. Your understanding of the project in ten bullets, in your own words.
B. Answers to these ten checks, one to three sentences each, in your own words, from the documents:
   1. What is the verdict when a Must characteristic's interval straddles its gate, and why is Site C of the golden example "borderline" and not "excluded"?
   2. Why are gates evaluated inside every simulation draw, and what goes wrong if they are evaluated only once?
   3. What happens when the target lacks data for a Must characteristic, and what happens when it lacks data for a Scored one?
   4. Which setup controls are never scored, what status does the API give them, and why do they still appear in the API?
   5. What does data_mode = real forbid, and what does a partial real bundle look like?
   6. What may you never invent, and what do you do instead?
   7. Which changes are allowed on data day, and which are escalations?
   8. What may the known-analog flag be used for, and what is it never used for?
   9. What can proxy evidence do and not do for a Must gate?
   10. How are run_id and seed derived, and why does a response body carry no timestamp?
C. Problems found: a numbered list of contradictions (document, section, the exact conflict), unclear or missing specifications, anything you believe is technically or scientifically wrong (with evidence), and risks. If you find none, write "None found" and list what you checked.
D. Your plan for T-001: files you will create, tests you will write, and how you will prove it done.

STEP 3. DECIDE
If part C lists any blocking problem, or any answer in part B shows you are unsure, STOP after printing the report. Write no code. Wait for me.
If there is no blocking problem, continue to Step 4 without asking.

STEP 4. DO TICKET T-001 ONLY
Follow the T-001 section of docs/09_WORK_PLAN.md and AGENTS.md sections 4 to 7. Specifics:
- Create the repository layout from docs/02_ARCHITECTURE.md section 3. Python 3.12 or newer, pinned in .python-version. uv with a committed uv.lock. Dependency groups: runtime, dev, pipeline. Put openapi-spec-validator, jsonschema, referencing, pyyaml, pytest, ruff, mypy in dev.
- Makefile with every target in AGENTS.md section 5:
  - make spec-check runs scripts/spec_check.py.
  - make config-check runs scripts/check_config_crossrefs.py. Include it in make ci.
  - make test-contract prints "skipped until T-020" and exits 0 until the app exists.
  - Targets for later tickets (data-inspect, bundle-synthetic, bundle-real, qa-real, licence-check, spotcheck, smoke-real, freeze, deploy, rollback) print "not implemented yet (ticket T-xxx)" with the right ticket and exit 1. They are not part of make ci.
  - make ci runs lint, type, spec-check, config-check, test and test-contract. It must pass.
- One trivial smoke test so pytest collects at least one test.
- make doctor prints tool versions and checks that required tools and environment variable names exist, without printing any secret.
- pre-commit with ruff and a secret scan. A CI workflow that runs make ci on every pull request.
- Do NOT implement any engine, API, model or pipeline code. Do NOT change any document, config file or the OpenAPI contract, except to fix a validation error that you must report.
- Branch: ticket/T-001-scaffold. Small commits.
- Write reports/T-001.md using the template in docs/10_PM_PROCESS.md section 3. Attach the full output of make ci.

STEP 5. STOP
Do not start T-002. Reply with: a short summary, the full make ci output, the path of the report, and any open question you added to docs/QUESTIONS.md.

RULES THAT NEVER BEND
1. Never invent science, data, citations, dataset names, resolutions, licences or coordinates. Mark unknowns as missing or null and ask.
2. Missing data is never zero and never a match. No silent fallbacks. No bare except.
3. api/openapi.yaml is the contract. Do not change it inside a feature ticket.
4. Tests first. Never loosen a tolerance or weaken a test to make it pass. If a test can only pass by changing a spec, a contract or a parameter, stop and ask.
5. The engine is pure: no I/O, no clock, no randomness without an explicit seed.
6. User-visible text only comes from the templates in docs/03_ENGINE_SPEC.md section 16. Never use the banned words in AGENTS.md.
7. Never commit secrets or restricted data. Read credentials from environment variables.
8. Do only the current ticket. No refactors outside it. No new dependency without a one-line reason and a licence check in the report.
9. If documents conflict or are unclear, stop and write the question in docs/QUESTIONS.md.
10. Report honestly. Never claim a test passed that you did not run.
How I review. Send me reports/T-000-comprehension.md, then reports/T-001.md with the full make ci output. A repository zip (no virtual environment, data or secrets) lets me run the checks in my own sandbox.

For each ticket I check:

that each acceptance criterion maps to a test that can actually fail;
that the code follows the spec text, spot-recomputing two numbers by hand;
that nothing was invented;
that the contract is unchanged;
that the report is honest.
I answer with Accepted, Accepted with notes, or Returned with numbered defects, and no later ticket starts until T-001 is accepted.

The agent’s comprehension report is the earliest warning sign. If it answers the ten checks wrongly, or finds no problems at all, send it to me before it writes any code.

Which coding agent will you run this in? Its setup and permissions differ slightly between tools.

Analog compass context pack
ZIP
Analog compass openapi
YAML
Could we also use the core characteristics of each test to help discover new sites? For example, these characteristics could help us determine which tests a particular site might be suitable for. This would allow us not only to discover new locations, but also to identify which tests we can actually conduct at each location.
This is one of the main objectives of the challenge. Therefore, we need to make sure we cover all the domains mentioned in the challenge details.
I also want you to think deeply and carefully about the design of the Offline Candidate Screen algorithm. We need a well-thought-out, precise, and technically sound approach.
Additionally, we must define clear Acceptance Criteria for the Discovery Engine to prove that it genuinely discovers new candidates rather than simply re-ranking sites that already exist in our curated pool.

Two big ideas here, and both are right. Discovery should run through the tests themselves, so every site gets a “which tests can I support here” profile. And covering all the challenge’s domains is part of the brief. I’ll be careful on one point: I can design all of it now, but I must not claim data that I haven’t verified. So I’ll research candidate datasets for the domains we marked unavailable before designing anything.

Continue, but I want to add that we could build a dedicated knowledge base covering all the atmospheric and environmental factors present on each of the targets.
We also need to take into consideration all the characteristics and requirements of every operation or test conducted on the targets. This will allow us to determine which tests can actually be performed at a newly discovered location and which ones that location is suitable for. It will also help the AI bot I’m developing to properly understand this entire area, so it can analyze, discuss, and communicate about it accurately and scientifically.
So please take all of this into account very carefully.
Regarding the data, it will be released on the 13th. I want you to create a synthetic dataset that closely replicates the exact structure, format, schema, and characteristics of the dataset expected on the 13th, based precisely on the details I’ve already provided. The goal is to make the synthetic data as close as possible to the real dataset, so that when the actual data is released, the system and engine will already be familiar with its structure and ready to work with it immediately.

Vegetation cover (MOD44B, 250 m, no use restrictions) is confirmed for the biology domain. Now the remaining domains: lithology, caves and lava tubes, and remoteness for operations.

GLiM lithology (16 classes, CC BY 3.0) and the Mars Global Cave Candidate Catalog (public domain, from USGS) are both confirmed. Now remoteness for operations, and land-surface temperature.

Continue

Continue

Continue

Continue

It builds, but at 56 MB the sample is too large to ship. I’ll see where the bytes go before deciding how to shrink it.

The white noise I added to a few coarse layers is what makes them incompressible. Smoothing that noise keeps the layers realistic but small.

Continue

All ten drop tests pass. Now a reference inspector, which both defines the report shape the agent’s real inspector (T-044) must produce and independently proves every file in the drop is readable.

Continue

Continue

Now the source registry and target plans need to cover the new layers, and the cross-check script must validate the domain map too.

Continue

Now the cited facts, written in my own words and graded by how thoroughly I verified each one.

Continue

Continue

Continue

Continue

Continue

Next, the large documentation files and engine spec additions.

Listing the remaining files to write, then packaging.

Patching the engine spec’s threshold rules and adding a suitability matrix section.

Bringing the engine spec into line with the new design
Continue

bash

cd /home/claude/pack && python3 - <<'EOF'
import re
def patch(path, pairs):
    t=open(path,encoding='utf8').read()
    for old,new in pairs:
        assert t.count(old)==1, f"{path}: not found/ambiguous: {old[:70]!r} (count={t.count(old)})"
        t=t.replace(old,new)
    open(path,'w',encoding='utf8').write(t); print("patched", path)

# sources: lighting id
patch('config/sources.yaml',[("used_for: [lighting_geometry]","used_for: [sunlit_fraction]")])
# openapi example ids
patch('api/openapi.yaml',[("characteristic_ids: [lighting_geometry]}","characteristic_ids: [sunlit_fraction]}"),
                          ("{characteristic_id: lighting_geometry, label: Lighting,","{characteristic_id: sunlit_fraction, label: Sunlit fraction,")])
# data spec: replace the lighting row with two rows and add the new domain layers
t=open('docs/05_DATA_SPEC.md',encoding='utf8').read()
i=t.index("| `lighting_geometry` |"); j=t.index("\n",i)
new_rows = ("| `sunlit_fraction` | distribution, fraction, per month | Moon: LOLA polar illumination maps (PGDA product 69: 240 m per pixel, averaged over the 18.6-year cycle; value semantics to confirm in the product documentation) | Computed from the Earth DEM, solar position and a horizon mask per month. Atmosphere ignored | Evidence class `derived`, tier B. Document the solar-position source and test it against independently found, cited reference values | Verified for the lunar maps |\n"
            "| `sun_elevation_max` | scalar, deg, per month | Moon: analytic from the lunar obliquity of 1.54 degrees (verified), plus local slope effects | Analytic from latitude and the date window | Tier B. Both sides computed by the same function | Verified for the obliquity |\n"
            "| `permafrost_index` | scalar, index 0 to 1 | Requirement threshold (ground ice in shadowed regions is a candidate resource; no verified direct data) | Global Permafrost Zonation Index, 30 arc-seconds, excludes Antarctica (verified); Northern Hemisphere 1 km TTOP map as a secondary source (verified) | Window median. Evidence class `proxy` (tier C): a proxy for ground ice, so a pass is provisional at best. The `.hdr` carries no CRS: the descriptor sets one with a justification | Verified products, proxy meaning |\n"
            "| `basaltic_volcanic_fraction` | scalar, fraction | Requirement threshold | GLiM lithology (16 first-level classes; 0.5 degree grid on PANGAEA and a vector original) (verified): fraction of window area in the basic volcanic class | Evidence class `proxy` (tier C): terrain where lava tubes can form, not evidence that they exist | Verified product, proxy meaning |\n"
            "| `cave_evidence` | ordinal | Mars: USGS Mars Global Cave Candidate Catalog (verified to exist). Moon: lunar pit catalogue not verified | Curated from literature in `config/pool.yaml` with citations | Scale is a placeholder (OPEN-12) | Curated |\n"
            "| `dust_aerosol_load` | scalar, optical depth | Requirement threshold. Earth aerosol optical depth (550 nm) and Mars dust opacity use different wavelengths: a documented conversion is needed | MERRA-2 aerosol diagnostics, 0.5 by 0.625 degrees, monthly (verified product family; variable names to confirm) | Window mean of a model-derived field: tier B, coarse | Partly verified |\n"
            "| `wind_speed_mean` | scalar, m/s | Requirement threshold | MERRA-2 single-level wind (product and variable names to confirm) | Tier B, coarse | Unverified product name |\n"
            "| `vegetation_cover` | scalar, percent | Requirement threshold (a life-limited environment) | MODIS Vegetation Continuous Fields, yearly 250 m (verified); real files are HDF (adapter gap: convert with GDAL) | Window median. A proxy for life-limited conditions, not a habitability measurement (tier C) | Verified product |\n"
            "| `remoteness_time` | scalar, minutes | Requirement threshold (isolation) | Global travel-time-to-cities map, 1 km, 85 N to 60 S, year 2015 (verified) | Window median. Outside 85 N to 60 S the value is `missing` with `outside_coverage` | Verified product |")
t=t[:i]+new_rows+t[j:]
open('docs/05_DATA_SPEC.md','w',encoding='utf8').write(t); print("data spec rows replaced")
# data spec: resampling rule + QA Q-16/Q-17 + synthetic drop pointer
patch('docs/05_DATA_SPEC.md',[
 ("4. **Same algorithm on every body.** Slope, roughness and the rest are derived by one function regardless of body, on the same 30 m analysis grid.",
  "4. **Same algorithm on every body.** Slope, roughness and the rest are derived by one function regardless of body, on the same 30 m analysis grid. **Resampling to the grid uses one method for every DEM: GDAL area averaging.** In the synthetic drop, the choice of method moved slope p50 by several percent (ratios of 0.82 to 0.90 of the latent value across nearest, bilinear, cubic and average), which is large next to the match tolerances. The method is recorded in `method_id`."),
 ("| Q-15 |","| Q-16 | Resampling sensitivity: for every DEM layer, slope p50 under two resampling methods is compared and the ratio reported. A ratio outside 0.85 to 1.15 goes to a human | Warning |\n| Q-17 | Every `crs_override` in a descriptor carries a written justification (for example the ESRI float grid with no CRS) and is listed in the QA report | Blocking |\n| Q-15 |"),
])
EOF
python3 - <<'EOF'
# ---------------- engine spec ----------------
import re
p='/home/claude/pack/docs/03_ENGINE_SPEC.md'; t=open(p,encoding='utf8').read()
old="**Band.** `b = max(band_site, band_target)`."
assert t.count(old)==1
new = ("| threshold_min (requirement) | `m = 1` if `x_s >= r`, else `max(0, 1 - (r - x_s) / tau)` | The test sets a **requirement** `r` (for example isolation at least a stated travel time), not a measured target value. `r` comes from the template rule's `requirement.value`; `tau` is the rule's fixed tolerance. A null `r` or `tau` means the characteristic has no usable requirement, which counts as missing target data (section 4) |\n"
       "| threshold_max (requirement) | `m = 1` if `x_s <= r`, else `max(0, 1 - (x_s - r) / tau)` | Same, for a ceiling (for example vegetation cover at most a stated percent) |\n\n"+old)
t=t.replace(old,new)
# put the table rows into the table: the two rows must be inside the table; find end of table before '**Band.**' -> we inserted rows after a blank line; fix by moving them directly after the envelope row
t=t.replace("| envelope (temperature) |","| envelope (temperature) |",1)
open(p,'w',encoding='utf8').write(t)
EOF
sed -n '/^## 5. Match functions/,/^\*\*Band/p' /home/claude/pack/docs/03_ENGINE_SPEC.md | head -30
Output

patched config/sources.yaml
patched api/openapi.yaml
data spec rows replaced
patched docs/05_DATA_SPEC.md
## 5. Match functions

`tau` is the characteristic's tolerance. `Q_T`, `Q_s` are 101-value quantile arrays (levels 0 to 100 percent).

| Kind | Formula | Notes |
|---|---|---|
| distribution | `d = mean over k=0..100 of abs(Q_T[k] - Q_s[k])`, `m = max(0, 1 - d / tau)` | `d` is the 1-D Wasserstein-1 distance. Same unit on both sides or fail the build |
| scalar | `m = max(0, 1 - abs(x_T - x_s) / tau)` | |
| ordinal | `m = max(0, 1 - abs(idx_T - idx_s) / tau)` | `tau` in classes. `idx` is the position in `scale` |
| set | `m = size(T intersect S) / size(T)` | If `T` is empty the characteristic is `ignore` |
| envelope (temperature) | `lo = Q_s[1]`, `hi = Q_s[99]`, `[r0, r1] = envelope`, `m = max(0, min(hi, r1) - max(lo, r0)) / (r1 - r0)` | Fraction of the required range that the site's 1st to 99th percentile range covers. `tau` unused |

| threshold_min (requirement) | `m = 1` if `x_s >= r`, else `max(0, 1 - (r - x_s) / tau)` | The test sets a **requirement** `r` (for example isolation at least a stated travel time), not a measured target value. `r` comes from the template rule's `requirement.value`; `tau` is the rule's fixed tolerance. A null `r` or `tau` means the characteristic has no usable requirement, which counts as missing target data (section 4) |
| threshold_max (requirement) | `m = 1` if `x_s <= r`, else `max(0, 1 - (x_s - r) / tau)` | Same, for a ceiling (for example vegetation cover at most a stated percent) |

**Band.** `b = max(band_site, band_target)`. If `scale_warning` is true, `b = b + params.scale_warning_band_add`.
Paused: Your free usage returns at 6:20 AM. Continue then.


You are out of free messages until 6:20 AM


Claude is AI and can make mistakes. Please double-check responses.
