"""Build a pure EngineRequest from declarative config + site observations.

Keeps all config parsing out of the engine (which must stay pure). Raises on
unknown ids rather than inventing defaults (AGENTS.md rule 1/2).
"""

from __future__ import annotations

from typing import Any

from analog_compass import config
from analog_compass.engine.types import (
    EngineParams,
    EngineRequest,
    Requirement,
    Role,
    SiteObservation,
    TargetChar,
    quantiles_from_control_points,
)
from analog_compass.settings import get_settings


def engine_params(n_draws: int | None = None) -> EngineParams:
    p = config.params()
    s = get_settings()
    return EngineParams(
        n_draws=int(n_draws or s.engine_n_draws or p["monte_carlo"]["n_draws"]),
        pass_gate=float(p["verdict"]["pass_gate"]),
        pass_score=float(p["verdict"]["pass_score"]),
        exclude_gate=float(p["verdict"]["exclude_gate"]),
        scale_warning_band_add=float(p["bands"]["scale_warning_band_add"]),
        seed_salt=s.engine_seed_salt or p["seed"]["salt"],
        engine_version=str(p["seed"]["engine_version"]),
        default_tau={k: float(v) for k, v in p["default_tau"].items()},
    )


def _target_char(spec: dict[str, Any], char_id: str) -> TargetChar:
    kind = spec["kind"]
    tier = spec.get("tier", "B")
    if kind == "distribution":
        pts = {float(k): float(v) for k, v in spec["quantiles"].items()}
        return TargetChar(kind=kind, tier=tier, quantiles=quantiles_from_control_points(pts))
    if kind == "scalar":
        return TargetChar(kind=kind, tier=tier, scalar=float(spec["value"]))
    if kind == "envelope":
        lo, hi = spec["envelope"]
        return TargetChar(kind=kind, tier=tier, envelope=(float(lo), float(hi)))
    if kind == "ordinal":
        scale = config.characteristics()[char_id].get("scale", [])
        return TargetChar(kind=kind, tier=tier, ordinal_index=scale.index(spec["value"]))
    raise ValueError(f"unsupported target kind {kind!r} for {char_id!r}")


def build_target(target_id: str) -> dict[str, TargetChar]:
    t = config.targets().get(target_id)
    if t is None:
        raise KeyError(f"unknown target_id {target_id!r}")
    return {cid: _target_char(spec, cid) for cid, spec in t["characteristics"].items()}


def build_requirements(test_id: str) -> tuple[Requirement, ...]:
    t = config.tests().get(test_id)
    if t is None:
        raise KeyError(f"unknown test_id {test_id!r}")
    out: list[Requirement] = []
    for r in t["requirements"]:
        gate = r.get("gate", {})
        req = r.get("requirement", {})
        out.append(
            Requirement(
                characteristic=r["characteristic"],
                role=r["role"],
                kind=r.get("kind", "setup"),
                weight=float(r.get("weight", 0.0)),
                tau=(float(r["tau"]) if "tau" in r else None),
                gate_stat=gate.get("stat"),
                gate_min=(float(gate["min"]) if "min" in gate else None),
                gate_max=(float(gate["max"]) if "max" in gate else None),
                req_value=(float(req["value"]) if "value" in req else None),
                req_tau=(float(req["tau"]) if "tau" in req else None),
                evidence_floor=r.get("evidence_floor"),
                rationale=r.get("rationale", ""),
            )
        )
    return tuple(out)


def requirements_from_constraints(constraints: list[dict[str, Any]]) -> list[Requirement]:
    """Turn scientist-supplied filters into engine Requirements (strict matching).

    A constraint is {characteristic, op: "min"|"max", value, required?: bool, weight?}.
    Distribution characteristics (slope/temperature/sunlit) become a gate on the median
    plus a match against the planetary target; scalar characteristics become a
    threshold_min/max. `required: true` makes it a Must gate, so windows that fail it are
    excluded — never returned as a loose/random result.
    """
    chars = config.characteristics()
    out: list[Requirement] = []
    for c in constraints:
        cid = c["characteristic"]
        if cid not in chars:
            raise KeyError(f"unknown characteristic in constraint: {cid!r}")
        op = c["op"]
        val = float(c["value"])
        required = bool(c.get("required", True))
        weight = float(c.get("weight") or 0.25)
        role: Role = "must" if required else "scored"
        # Every constraint is a threshold on the site's value (median for distributions),
        # so a scientist filter is a strict, target-independent gate.
        tau = max(abs(val) * 0.5, 0.2)
        out.append(Requirement(
            characteristic=cid, role=role,
            kind="threshold_min" if op == "min" else "threshold_max",
            weight=weight, req_value=val, req_tau=tau,
            evidence_floor=chars[cid].get("tier"),
            rationale="scientist filter",
        ))
    return out


def merge_requirements(
    test_id: str, constraints: list[dict[str, Any]] | None,
) -> tuple[Requirement, ...]:
    """Test-template requirements, with scientist constraints overriding per characteristic."""
    base = list(build_requirements(test_id))
    if not constraints:
        return tuple(base)
    extra = requirements_from_constraints(constraints)
    overridden = {r.characteristic for r in extra}
    kept = [r for r in base if r.characteristic not in overridden]
    return tuple(kept + extra)


def build_request(
    target_id: str,
    test_id: str,
    sites: list[SiteObservation],
    *,
    n_draws: int | None = None,
    constraints: list[dict[str, Any]] | None = None,
) -> EngineRequest:
    s = get_settings()
    return EngineRequest(
        target_id=target_id,
        test_id=test_id,
        target=build_target(target_id),
        requirements=merge_requirements(test_id, constraints),
        sites=tuple(sites),
        params=engine_params(n_draws),
        data_version=s.data_version,
        data_mode=s.data_mode,  # type: ignore[arg-type]
    )
