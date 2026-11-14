"""Serialise engine dataclasses to the shapes in api/openapi.yaml."""

from __future__ import annotations

from typing import Any

from analog_compass.engine.types import CharResult, CompareResult, SiteResult


def char_to_dict(c: CharResult) -> dict[str, Any]:
    return {
        "characteristic": c.characteristic,
        "role": c.role,
        "status": c.status,
        "match": c.match,
        "tier": c.tier,
        "source_id": c.source_id,
        "contribution": c.contribution,
        "gate_pass_rate": c.gate_pass_rate,
        "value_display": c.value_display,
    }


def site_to_dict(s: SiteResult) -> dict[str, Any]:
    return {
        "site_id": s.site_id,
        "label": s.label,
        "lat": s.lat,
        "lon": s.lon,
        "candidate_kind": s.candidate_kind,
        "verdict": s.verdict,
        "p_gate": s.p_gate,
        "score": s.score,
        "score_band": list(s.score_band),
        "coverage": s.coverage,
        "characteristics": [char_to_dict(c) for c in s.characteristics],
        "honest_limits": list(s.honest_limits),
        "provenance": s.provenance,
    }


def result_to_dict(r: CompareResult) -> dict[str, Any]:
    return {
        "run_id": r.run_id,
        "seed": r.seed,
        "data_version": r.data_version,
        "data_mode": r.data_mode,
        "engine_version": r.engine_version,
        "target_id": r.target_id,
        "test_id": r.test_id,
        "sites": [site_to_dict(s) for s in r.sites],
    }
