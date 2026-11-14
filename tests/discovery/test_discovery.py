"""Discovery acceptance criteria (docs/04_DISCOVERY_SPEC.md §5)."""

from __future__ import annotations

from analog_compass import config
from analog_compass.discovery import discover
from analog_compass.discovery.screen import MIN_SEPARATION_KM
from analog_compass.pipeline.bundle import get_bundle

TARGET = "mars_mid_latitude"
TEST = "rover_traverse_autonomy"


def _new(res):
    return [s for s in res.sites if s.candidate_kind == "new"]


def test_ac_d3_finds_unknown_candidates() -> None:
    res = discover(get_bundle(), TARGET, TEST, k=8, n_draws=128)
    new = _new(res)
    assert new, "screen returned no new candidates"
    assert all(s.verdict in ("pass", "borderline") for s in new)


def test_ac_d1_novelty_by_construction() -> None:
    res = discover(get_bundle(), TARGET, TEST, k=10, n_draws=128)
    pool_ids = set(config.pool())
    for s in _new(res):
        assert s.site_id not in pool_ids
        assert s.provenance["origin"] == "screen"
        assert s.provenance["novelty"]["pool_overlap"] is False
        assert s.provenance["novelty"]["min_separation_km"] >= MIN_SEPARATION_KM


def test_ac_d4_provenance_complete() -> None:
    res = discover(get_bundle(), TARGET, TEST, k=5, n_draws=128)
    for s in _new(res):
        p = s.provenance
        assert set(["origin", "screen_version", "nominated_from", "window", "novelty", "seed"]).issubset(p)


def test_ac_d5_determinism() -> None:
    a = discover(get_bundle(), TARGET, TEST, k=8, n_draws=128)
    b = discover(get_bundle(), TARGET, TEST, k=8, n_draws=128)
    assert a.run_id == b.run_id
    assert [s.site_id for s in a.sites] == [s.site_id for s in b.sites]


def test_ac_d7_no_fabrication_of_missing_must() -> None:
    # life_detection requires remoteness_time (Must); windows missing it must never be
    # promoted as passing new candidates.
    res = discover(get_bundle(), TARGET, "life_detection_assay", k=10, n_draws=128)
    for s in _new(res):
        rt = next((c for c in s.characteristics if c.characteristic == "remoteness_time"), None)
        assert rt is None or rt.status != "missing"
