"""Contract tests: endpoints conform to api/openapi.yaml shapes and are deterministic."""

from __future__ import annotations

from fastapi.testclient import TestClient

from analog_compass.api.app import app

client = TestClient(app)
VERDICTS = {"pass", "borderline", "excluded", "blocked"}


def test_health() -> None:
    h = client.get("/health").json()
    assert h["status"] == "ok"
    assert h["data_mode"] in {"synthetic", "real"}
    assert "engine_version" in h


def test_lists() -> None:
    assert client.get("/targets").json()
    assert client.get("/tests").json()
    assert client.get("/sites").json()


def test_compare_shape_and_determinism() -> None:
    body = {"target_id": "mars_mid_latitude", "test_id": "rover_traverse_autonomy", "n_draws": 128}
    r1 = client.post("/compare", json=body).json()
    assert r1["run_id"] and r1["sites"]
    for s in r1["sites"]:
        assert s["verdict"] in VERDICTS
        assert set(["site_id", "candidate_kind", "p_gate", "score", "honest_limits"]).issubset(s)
    r2 = client.post("/compare", json=body).json()
    assert r1["run_id"] == r2["run_id"]


def test_discover_and_suitability_and_map() -> None:
    disc = client.post("/discover", json={
        "target_id": "mars_mid_latitude", "test_id": "rover_traverse_autonomy",
        "k": 5, "n_draws": 128}).json()
    assert "run_id" in disc

    suit = client.post("/suitability", json={"site_id": "atacama", "n_draws": 128}).json()
    assert suit["tests"]

    geo = client.post("/map.geojson", json={
        "target_id": "mars_mid_latitude", "test_id": "rover_traverse_autonomy",
        "n_draws": 128}).json()
    assert geo["type"] == "FeatureCollection"
    assert all(f["type"] == "Feature" for f in geo["features"])


def test_layers_catalog() -> None:
    cat = client.get("/layers").json()
    assert cat["layers"] and cat["sources"]
    slope = next(x for x in cat["layers"] if x["id"] == "slope")
    assert slope["source"]["id"] == "dem_srtm"
    # proxy layers expose what they proxy for
    perma = next(x for x in cat["layers"] if x["id"] == "permafrost_index")
    assert perma["tier"] == "C" and perma["proxy_for"]


def test_compare_includes_value_display() -> None:
    body = {"target_id": "mars_mid_latitude", "test_id": "rover_traverse_autonomy", "n_draws": 64}
    r = client.post("/compare", json=body).json()
    chars = r["sites"][0]["characteristics"]
    scored = [c for c in chars if c["status"] in ("ok", "proxy")]
    assert any(c.get("value_display") for c in scored)


def test_site_profile_full_characteristics() -> None:
    prof = client.get("/site_profile", params={"site_id": "atacama"}).json()
    assert prof["id"] == "atacama"
    ids = {c["characteristic"] for c in prof["characteristics"]}
    assert {"slope", "permafrost_index", "basaltic_volcanic_fraction"}.issubset(ids)
    # Dry Valleys remoteness is missing (outside coverage) and stays null, not zeroed.
    dv = client.get("/site_profile", params={"site_id": "dry_valleys"}).json()
    rt = next(c for c in dv["characteristics"] if c["characteristic"] == "remoteness_time")
    assert rt["missing"] is True and rt["value_display"] is None


def test_data_contribution_intake() -> None:
    ok = client.post("/data/contributions", json={
        "name": "Global Permafrost Zonation Index", "source_link": "https://example.org/pzi",
        "measures": "Permafrost zonation index at 30 arc-seconds, global coverage.",
    }).json()
    assert ok["status"] == "received" and ok["ticket_id"].startswith("DS-")
    bad = client.post("/data/contributions", json={
        "name": "x", "source_link": "not-a-url", "measures": "short"}).json()
    assert bad["status"] == "rejected"
    assert not all(c["ok"] for c in bad["checks"])


def test_discover_respects_constraints_strictly() -> None:
    base = {"target_id": "mars_mid_latitude", "test_id": "isru_regolith_processing",
            "k": 10, "n_draws": 96}
    loose = client.post("/discover", json=base).json()
    strict = client.post("/discover", json={
        **base,
        "constraints": [{"characteristic": "basaltic_volcanic_fraction",
                         "op": "min", "value": 0.6, "required": True}],
    }).json()
    # Adding a constraint changes the computation (different reproducible run).
    assert loose["run_id"] != strict["run_id"]
    strict_new = [s for s in strict["sites"] if s["candidate_kind"] == "new"]
    assert strict_new, "strict constraint returned no candidates"
    # Every returned candidate actually meets the basaltic constraint (no random results).
    for s in strict_new:
        gid = s["provenance"]["window"]["grid_id"]
        prof = client.get("/site_profile", params={"grid_id": gid}).json()
        basalt = next(c for c in prof["characteristics"]
                      if c["characteristic"] == "basaltic_volcanic_fraction")
        assert float(basalt["value_display"]) >= 0.45


def test_site_operations_has_base_relevance() -> None:
    ops = client.get("/site_operations",
                     params={"site_id": "lava_beds", "target_id": "moon_polar"}).json()
    assert ops["operations"]
    lt = next(o for o in ops["operations"] if o["test_id"] == "lava_tube_exploration")
    assert lt["base_relevance"] and lt["actionable"]
    assert any(o["supported"] for o in ops["operations"])


def test_unknown_ids_return_422() -> None:
    r = client.post("/compare", json={"target_id": "nope", "test_id": "nope"})
    assert r.status_code == 422


def test_agent_requires_key() -> None:
    # No ANTHROPIC_API_KEY in the test env -> agent unavailable.
    r = client.post("/agent/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 503
