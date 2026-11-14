"""GeoJSON export for a compare/discover run (docs/05 §brief asks for a map)."""

from __future__ import annotations

from typing import Any

from analog_compass.engine.types import CompareResult


def to_feature_collection(result: CompareResult) -> dict[str, Any]:
    features = []
    for s in result.sites:
        if s.lat is None or s.lon is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s.lon, s.lat]},
            "properties": {
                "site_id": s.site_id,
                "label": s.label,
                "candidate_kind": s.candidate_kind,
                "verdict": s.verdict,
                "score": s.score,
                "p_gate": s.p_gate,
                "honest_limits": list(s.honest_limits),
                "provenance_origin": (s.provenance or {}).get("origin"),
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"run_id": result.run_id, "target_id": result.target_id,
                     "test_id": result.test_id, "data_version": result.data_version},
    }
