"""Which tests can a given site support, and why.

The suitability matrix is the compare engine evaluated across ALL tests for a fixed
site (docs/06_SUITABILITY_SPEC.md §3) — the same engine, so AC-S5 (duality) holds by
construction.
"""

from __future__ import annotations

from typing import Any

from analog_compass import builder, config
from analog_compass.engine import compare
from analog_compass.engine.types import SiteObservation, SiteResult

DEFAULT_TARGET = "mars_mid_latitude"


def _driving_and_limiting(sr: SiteResult) -> tuple[str | None, str | None]:
    scored = [c for c in sr.characteristics if c.status in ("ok", "proxy") and c.contribution is not None]
    driving = max(scored, key=lambda c: c.contribution or 0.0).characteristic if scored else None
    # limiting: the Must with the lowest gate pass-rate, else the lowest-match scored char.
    musts = [c for c in sr.characteristics if c.role == "must" and c.gate_pass_rate is not None]
    if musts:
        limiting = min(musts, key=lambda c: c.gate_pass_rate or 0.0).characteristic
    elif scored:
        limiting = min(scored, key=lambda c: c.match or 0.0).characteristic
    else:
        limiting = None
    return driving, limiting


def site_suitability(
    site_obs: SiteObservation,
    target_id: str = DEFAULT_TARGET,
    *,
    n_draws: int | None = None,
) -> dict[str, Any]:
    tests = config.tests()
    entries = []
    for test_id, t in tests.items():
        req = builder.build_request(target_id, test_id, [site_obs], n_draws=n_draws)
        res = compare(req)
        sr = res.sites[0]
        driving, limiting = _driving_and_limiting(sr)
        reasons = list(sr.honest_limits)
        if not reasons and sr.verdict == "pass":
            reasons.append(f"Meets all requirements (gate {round(sr.p_gate * 100)}% of draws).")
        entries.append({
            "test_id": test_id,
            "label": t["label"],
            "verdict": sr.verdict,
            "driving_characteristic": driving,
            "limiting_characteristic": limiting,
            "reasons": reasons,
        })
    order = {"pass": 0, "borderline": 1, "blocked": 2, "excluded": 3}
    entries.sort(key=lambda e: order[e["verdict"]])
    return {"site_id": site_obs.site_id, "target_id": target_id, "tests": entries}
