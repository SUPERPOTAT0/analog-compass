# 10 — PM Process

## 1. Ticket lifecycle

`planned → in progress → in review → accepted | returned`. No later ticket starts until its blocker is **accepted**. One ticket at a time; no refactors outside the current ticket; no new dependency without a one-line reason + a licence check in the report.

## 2. Rules that never bend (from `AGENTS.md`)

1. Never invent science, data, citations, dataset names, resolutions, licences or coordinates. Unknown ⇒ `missing`/`null` + ask.
2. Missing data is never zero and never a match. No silent fallbacks. No bare `except`.
3. `api/openapi.yaml` is the contract. Not changed inside a feature ticket.
4. Tests first. Never loosen a tolerance or weaken a test to make it pass. If a test can only pass by changing a spec/contract/parameter — stop and ask.
5. The engine is pure: no I/O, no clock, no randomness without an explicit seed.
6. User-visible text only from the templates in [[03_ENGINE_SPEC]] §10. Never use the banned words.
7. Never commit secrets or restricted data. Credentials from env vars.
8. Do only the current ticket.
9. If documents conflict or are unclear — stop and write the question in [[QUESTIONS]].
10. Report honestly. Never claim a test passed that you did not run.

## 3. Report template (`reports/T-xxx.md`)

```markdown
# T-xxx — <title>
## Summary
<2–4 sentences: what changed and why>
## Acceptance criteria → tests
| AC | Test | Pass? |
## Spec conformance
<two numbers recomputed by hand vs the code>
## Nothing invented
<list of every value/source used and where it came from>
## Contract
<unchanged | validation fix reported>
## make ci output
<full paste>
## Open questions
<added to QUESTIONS.md? ids>
```

## 4. Review verdicts

`Accepted` · `Accepted with notes` · `Returned with numbered defects`. The comprehension report is the earliest warning sign: if the ten checks are answered wrongly, or *no* problems are found, it is reviewed before any code is written.

## 5. The ten comprehension checks (answered in the T-000 readout)

1. **Must interval straddles its gate** → verdict is `borderline` (passes the gate in some draws, not most); Site C is borderline not excluded because its gate pass-rate sits between `exclude_gate` and `pass_gate`. ([[03_ENGINE_SPEC]] §7)
2. **Gates inside every draw** so uncertainty is respected; evaluating once on the nominal collapses a borderline into a false clean pass/fail. (§6)
3. **Target missing a Must** → site `blocked` (`target_missing_must`); **target missing a Scored** → that characteristic dropped from the weighted sum for all sites, weight removed from denominator. (§4)
4. **Setup controls** are never scored, get status `setup`, and still appear because the planner needs the context. (§2)
5. **`data_mode=real`** forbids any synthetic fallback; a **partial real bundle** uses present layers and marks absent ones `missing`. ([[05_DATA_SPEC]] §1)
6. **Never invent** data/science/citations; instead mark `missing`/`null` and ask. (rule 1)
7. **Allowed on data day:** source ids, resolutions, coverage boxes, variable-name confirmations. **Escalations:** contract, engine math, tolerances, characteristic role/kind. ([[05_DATA_SPEC]] §7)
8. **Known-analog flag** may be used to label/annotate and to validate the system against expert expectations; it is **never** used to influence scoring or the `new candidate` label.
9. **Proxy evidence** can inform a Scored match and give a *provisional* signal, but **cannot by itself satisfy a Must gate** — at best a capped `borderline`. ([[03_ENGINE_SPEC]] §3)
10. **`run_id`/`seed`** derive from `hash(canonical_request + data_version[+engine_version])`; the body carries no timestamp so identical runs are byte-identical. (§8)

See next: [[11_DEPLOYMENT]].
