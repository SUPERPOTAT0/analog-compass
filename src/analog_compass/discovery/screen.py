"""Offline Candidate Screen (docs/04_DISCOVERY_SPEC.md).

Nominates NEW windows (not curated-pool cells) that match a target x test requirement
profile, judges them with the SAME engine as curated sites, excludes pool-overlaps so
the `new candidate` label is trustworthy, de-dups spatially, and attaches provenance.
Deterministic: seeded from the bundle + target + test + screen params.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

from analog_compass import builder, config
from analog_compass.discovery.provenance import cluster_id, haversine_km
from analog_compass.engine import compare
from analog_compass.engine.types import CompareResult, SiteObservation, SiteResult
from analog_compass.pipeline.bundle import Bundle

SCREEN_VERSION = "1.0.0"
MIN_SEPARATION_KM = 60.0


def _in_bbox(lat: float, lon: float, bbox: list[float] | None) -> bool:
    if bbox is None:
        return True
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def _must_characteristics(test_id: str, constraints: list[dict] | None = None) -> list[str]:
    merged = builder.merge_requirements(test_id, constraints)
    return [r.characteristic for r in merged if r.role == "must"]


def _screen_seed(bundle: Bundle, target_id: str, test_id: str, k: int) -> int:
    payload = f"{bundle.data_version}|{target_id}|{test_id}|{SCREEN_VERSION}|{k}"
    return int.from_bytes(hashlib.blake2b(payload.encode(), digest_size=8).digest(), "big")


def discover(
    bundle: Bundle,
    target_id: str,
    test_id: str,
    *,
    region_bbox: list[float] | None = None,
    k: int = 10,
    include_curated: bool = False,
    n_draws: int | None = None,
    constraints: list[dict] | None = None,
) -> CompareResult:
    """Return up to `k` discovered candidates (plus curated, if requested)."""
    pool = config.pool()
    pool_coords = [(s["lat"], s["lon"]) for s in pool.values()]
    must_chars = _must_characteristics(test_id, constraints)

    # Stage 0-1: search space + cheap exclusion (missing a Must -> cannot pass).
    windows = [
        w for w in bundle.discovery_windows()
        if _in_bbox(w.lat, w.lon, region_bbox)
        and not any(w.chars.get(c, {}).get("missing") for c in must_chars)
    ]

    # Stage 3: pool-overlap exclusion (novelty by construction).
    nominees: list[tuple] = []  # (window, min_sep_km)
    for w in windows:
        sep = min((haversine_km(w.lat, w.lon, la, lo) for la, lo in pool_coords), default=1e9)
        if sep < MIN_SEPARATION_KM:
            continue  # a rediscovery of a known site, not a new candidate
        nominees.append((w, sep))

    # Stage 4: full engine evaluation (same engine as curated).
    observations: list[SiteObservation] = []
    meta: dict[str, tuple] = {}
    for w, sep in nominees:
        prov = {
            "origin": "screen",
            "screen_version": SCREEN_VERSION,
            "nominated_from": must_chars,
            "window": {"grid_id": w.grid_id, "bbox": w.bbox},
            "novelty": {"pool_overlap": False,
                        "min_separation_km": round(sep, 1),
                        "cluster_id": cluster_id(w.lat, w.lon)},
            "seed": _screen_seed(bundle, target_id, test_id, k),
        }
        obs = w.observation(candidate_kind="new", provenance=prov)
        observations.append(obs)
        meta[obs.site_id] = (w, sep)

    if include_curated:
        observations.extend(bundle.curated_observations())

    req = builder.build_request(target_id, test_id, observations, n_draws=n_draws,
                                constraints=constraints)
    result = compare(req)
    if not observations:
        return result

    # Keep only promising verdicts; de-dup by cluster keeping the best per cluster.
    keep_order = {"pass": 0, "borderline": 1}
    best_per_cluster: dict[int, SiteResult] = {}
    passthrough: list[SiteResult] = []
    for sr in result.sites:
        if sr.candidate_kind == "curated":
            passthrough.append(sr)
            continue
        if sr.verdict not in keep_order:
            continue
        w, _sep = meta[sr.site_id]
        cid = cluster_id(w.lat, w.lon)
        cur = best_per_cluster.get(cid)
        if cur is None or (keep_order[sr.verdict], -sr.score) < (keep_order[cur.verdict], -cur.score):
            best_per_cluster[cid] = sr

    new_candidates = sorted(
        best_per_cluster.values(),
        key=lambda s: (keep_order[s.verdict], -s.score),
    )[:k]

    # Give discovered candidates a readable label.
    new_candidates = [
        replace(s, label=f"Candidate {s.site_id} ({s.lat:.1f}, {s.lon:.1f})")
        for s in new_candidates
    ]
    return replace(result, sites=tuple(passthrough + new_candidates))
