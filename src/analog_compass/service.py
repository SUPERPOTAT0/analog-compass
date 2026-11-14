"""Application service layer: shared use-cases for the API and the AI agent.

Thin orchestration over builder + engine + discovery + suitability. Stateless.
"""

from __future__ import annotations

from typing import Any

from analog_compass import builder, config
from analog_compass.discovery import discover as _discover
from analog_compass.engine import compare
from analog_compass.engine.types import CompareResult, SiteObservation
from analog_compass.pipeline.bundle import get_bundle
from analog_compass.suitability import site_suitability


def curated_observations(site_ids: list[str] | None = None) -> list[SiteObservation]:
    obs = get_bundle().curated_observations()
    if site_ids:
        wanted = set(site_ids)
        obs = [o for o in obs if o.site_id in wanted]
    return obs


def run_compare(
    target_id: str, test_id: str, site_ids: list[str] | None = None,
    n_draws: int | None = None,
) -> CompareResult:
    obs = curated_observations(site_ids)
    req = builder.build_request(target_id, test_id, obs, n_draws=n_draws)
    return compare(req)


def run_discover(
    target_id: str, test_id: str, region_bbox: list[float] | None = None,
    k: int = 10, include_curated: bool = False, n_draws: int | None = None,
    constraints: list[dict[str, Any]] | None = None,
) -> CompareResult:
    return _discover(
        get_bundle(), target_id, test_id, region_bbox=region_bbox,
        k=k, include_curated=include_curated, n_draws=n_draws, constraints=constraints,
    )


def run_suitability(
    site_id: str, target_id: str | None = None, n_draws: int | None = None,
) -> dict[str, Any]:
    obs = get_bundle().curated_observation(site_id)
    tid = target_id or "mars_mid_latitude"
    return site_suitability(obs, tid, n_draws=n_draws)


def _format_value(spec: dict[str, Any], char_cfg: dict[str, Any]) -> str | None:
    if spec.get("missing"):
        return None
    if spec.get("scalar") is not None:
        return f"{round(float(spec['scalar']), 3)}"
    q = spec.get("quantiles")
    if q is not None:
        return f"{round(float(q[50]), 2)}"
    idx = spec.get("ordinal_index")
    if idx is not None:
        scale = char_cfg.get("scale")
        return scale[idx] if scale and idx < len(scale) else str(idx)
    return None


def site_profile(site_id: str | None = None, grid_id: str | None = None) -> dict[str, Any]:
    """Full data profile of one window: every characteristic's raw value + provenance.

    Part of the data feature — gives UIs the real measured values behind a candidate.
    """
    b = get_bundle()
    w = b.window_by_id(site_id=site_id, grid_id=grid_id)
    chars_cfg = config.characteristics()
    srcs = config.sources()
    doms = config.domains()
    dom_of: dict[str, str] = {}
    for d in doms:
        for cid in d.get("characteristics", []):
            dom_of[cid] = d["label"]

    out = []
    for cid, spec in w.chars.items():
        c = chars_cfg.get(cid, {})
        s = srcs.get(c.get("source_id", ""), {})
        out.append({
            "characteristic": cid,
            "value_display": _format_value(spec, c),
            "unit": c.get("unit"),
            "tier": c.get("tier", spec.get("tier", "B")),
            "domain": dom_of.get(cid),
            "proxy_for": c.get("proxy_for"),
            "source_id": c.get("source_id"),
            "source_name": s.get("name"),
            "missing": bool(spec.get("missing", False)),
        })
    return {"id": w.curated_site_id or w.grid_id, "lat": w.lat, "lon": w.lon,
            "characteristics": out}


def site_operations(
    site_id: str | None = None, grid_id: str | None = None,
    target_id: str | None = None, n_draws: int | None = None,
) -> dict[str, Any]:
    """Tests & Base Operations for one window: which engineering/science tests this
    environment can support, and why each matters for a Moon/Mars base.
    """
    b = get_bundle()
    w = b.window_by_id(site_id=site_id, grid_id=grid_id)
    obs = w.observation(candidate_kind="curated" if w.curated_site_id else "new")
    tid = target_id or "mars_mid_latitude"
    suit = site_suitability(obs, tid, n_draws=n_draws)
    tests_cfg = config.tests()
    order = {"pass": 0, "borderline": 1, "blocked": 2, "excluded": 3}
    ops = []
    for e in suit["tests"]:
        t = tests_cfg.get(e["test_id"], {})
        ops.append({
            "test_id": e["test_id"],
            "label": e["label"],
            "verdict": e["verdict"],
            "supported": e["verdict"] in ("pass", "borderline"),
            "actionable": t.get("actionable", t.get("rationale", "")),
            "base_relevance": t.get("base_relevance", ""),
            "domains": t.get("domains", []),
            "limiting_characteristic": e.get("limiting_characteristic"),
            "reasons": e.get("reasons", []),
        })
    ops.sort(key=lambda o: order[o["verdict"]])
    return {"id": w.curated_site_id or w.grid_id, "lat": w.lat, "lon": w.lon,
            "target_id": tid, "operations": ops}


def health() -> dict[str, Any]:
    from analog_compass.settings import get_settings

    s = get_settings()
    return {
        "status": "ok",
        "data_mode": s.data_mode,
        "data_version": s.data_version,
        "engine_version": str(config.params()["seed"]["engine_version"]),
        "agent_available": bool(s.anthropic_api_key),
    }
