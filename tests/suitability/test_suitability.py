"""Suitability-matrix acceptance criteria (docs/06_SUITABILITY_SPEC.md §5)."""

from __future__ import annotations

from analog_compass import config
from analog_compass.pipeline.bundle import get_bundle
from analog_compass.suitability import site_suitability


def _proxy_must_tests() -> set[str]:
    chars = config.characteristics()
    out = set()
    for tid, t in config.tests().items():
        for r in t["requirements"]:
            if r.get("role") == "must" and chars.get(r["characteristic"], {}).get("tier") == "C":
                out.add(tid)
    return out


def test_ac_s1_entry_for_every_test_with_reasons() -> None:
    obs = get_bundle().curated_observation("atacama")
    r = site_suitability(obs, "mars_mid_latitude", n_draws=128)
    assert len(r["tests"]) == len(config.tests())
    for e in r["tests"]:
        if e["verdict"] != "pass":
            assert e["reasons"], f"{e['test_id']} non-pass without a reason"


def test_ac_s4_proxy_must_never_passes() -> None:
    obs = get_bundle().curated_observation("devon_island")
    r = site_suitability(obs, "mars_mid_latitude", n_draws=128)
    proxy_tests = _proxy_must_tests()
    for e in r["tests"]:
        if e["test_id"] in proxy_tests:
            assert e["verdict"] != "pass", f"{e['test_id']} passed on proxy evidence"
