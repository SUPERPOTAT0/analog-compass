"""Golden worked example: per-draw gating produces pass / excluded / borderline,
and runs are byte-deterministic. Mirrors tests/fixtures/golden_worked_example.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from analog_compass.engine import compare
from analog_compass.engine.types import (
    CharObservation,
    EngineParams,
    EngineRequest,
    Requirement,
    SiteObservation,
    TargetChar,
    quantiles_from_control_points,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "golden_worked_example.json"

TARGET_SLOPE = quantiles_from_control_points({0.01: -2.0, 0.5: 8.0, 0.99: 18.0})


def _slope_obs(med: float, band: float) -> CharObservation:
    q = quantiles_from_control_points({0.01: med - 10, 0.5: med, 0.99: med + 10})
    return CharObservation(kind="distribution", tier="B", band=band, quantiles=q,
                           source_id="dem_srtm")


def _request(n_draws: int = 2000) -> EngineRequest:
    req = Requirement(characteristic="slope", role="must", kind="distribution",
                      weight=1.0, tau=5.0, gate_stat="p50", gate_max=15.0)
    sites = (
        SiteObservation("A_pass", "A", chars={"slope": _slope_obs(8.0, 0.0)}),
        SiteObservation("B_excluded", "B", chars={"slope": _slope_obs(25.0, 0.0)}),
        SiteObservation("C_borderline", "C", chars={"slope": _slope_obs(15.0, 4.0)}),
    )
    return EngineRequest(
        target_id="t", test_id="golden_slope_gate",
        target={"slope": TargetChar(kind="distribution", tier="B", quantiles=TARGET_SLOPE)},
        requirements=(req,), sites=sites, params=EngineParams(n_draws=n_draws),
        data_version="golden-1",
    )


def _by_id(result):
    return {s.site_id: s for s in result.sites}


def test_golden_verdicts() -> None:
    res = _by_id(compare(_request()))

    # Hand-check 1: A is identical to the target slope -> match 1.0, gate always passes.
    a = res["A_pass"]
    a_slope = next(c for c in a.characteristics if c.characteristic == "slope")
    assert a.verdict == "pass"
    assert abs(a_slope.match - 1.0) < 1e-9
    assert abs(a.score - 1.0) < 1e-9
    assert a.p_gate == 1.0

    # B's p50 sits above the gate in every draw -> excluded.
    assert res["B_excluded"].verdict == "excluded"
    assert res["B_excluded"].p_gate == 0.0

    # Hand-check 2: C's p50 straddles the gate symmetrically -> ~50% pass -> borderline.
    c = res["C_borderline"]
    assert c.verdict == "borderline"
    assert 0.4 < c.p_gate < 0.6
    assert any("Borderline" in n for n in c.honest_limits)


def test_determinism_byte_identical() -> None:
    r1 = compare(_request())
    r2 = compare(_request())
    assert r1.run_id == r2.run_id
    assert r1.seed == r2.seed
    assert [(s.site_id, s.score, s.p_gate) for s in r1.sites] == \
           [(s.site_id, s.score, s.p_gate) for s in r2.sites]


def test_fixture_expectations_align() -> None:
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    res = _by_id(compare(_request()))
    assert res["A_pass"].verdict == fx["expected"]["A_pass"]["verdict"]
    assert res["B_excluded"].verdict == fx["expected"]["B_excluded"]["verdict"]
    assert res["C_borderline"].verdict == fx["expected"]["C_borderline"]["verdict"]
    lo, hi = fx["expected"]["C_borderline"]["p_gate_range"]
    assert lo <= res["C_borderline"].p_gate <= hi
