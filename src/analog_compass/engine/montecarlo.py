"""Monte Carlo draws + per-draw gate evaluation (docs/03_ENGINE_SPEC.md §6).

Gates are evaluated *inside every draw* so that a value whose uncertainty interval
straddles a gate is reflected as "passes some of the time" (the basis of the
`borderline` verdict). Pure given an explicitly-seeded Generator.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from analog_compass.engine import match as M
from analog_compass.engine.types import CharObservation, Requirement, TargetChar, Tier


@dataclass
class CharEval:
    """Result of evaluating one characteristic across all draws for one site."""

    status: str  # ok | missing | setup | proxy | target_missing
    role: str
    tier: Tier
    source_id: str
    match_draws: np.ndarray | None = None  # (n_draws,)
    gate_pass_draws: np.ndarray | None = None  # (n_draws,) bool, Must only
    is_proxy_must: bool = False
    value_display: str | None = None  # raw observed value for UIs


def _value_display(obs: CharObservation) -> str | None:
    """Human-readable raw value of an observation (median for distributions)."""
    if obs.missing:
        return None
    if obs.scalar is not None:
        return f"{round(obs.scalar, 3)}"
    if obs.quantiles is not None:
        return f"{round(float(obs.quantiles[50]), 2)}"
    if obs.ordinal_index is not None:
        return str(obs.ordinal_index)
    if obs.envelope is not None:
        return f"{obs.envelope[0]}—{obs.envelope[1]}"
    return None


def _draw_offsets(rng: np.random.Generator, band: float, n: int) -> np.ndarray:
    if band <= 0:
        return np.zeros(n)
    return rng.triangular(-band, 0.0, band, size=n)


def _draw_scalar(rng: np.random.Generator, nominal: float, band: float, n: int) -> np.ndarray:
    if band <= 0:
        return np.full(n, nominal, dtype=float)
    return rng.triangular(nominal - band, nominal, nominal + band, size=n)


def _effective_band(obs: CharObservation, scale_warning_band_add: float) -> float:
    b = obs.band
    if obs.scale_warning:
        b += scale_warning_band_add
    return b


def _gate_pass(values: np.ndarray, req: Requirement) -> np.ndarray:
    ok = np.ones(values.shape, dtype=bool)
    if req.gate_min is not None:
        ok &= values >= req.gate_min
    if req.gate_max is not None:
        ok &= values <= req.gate_max
    return ok


def evaluate_char(
    req: Requirement,
    target: TargetChar | None,
    obs: CharObservation | None,
    tau: float,
    n_draws: int,
    rng: np.random.Generator,
    scale_warning_band_add: float,
) -> CharEval:
    """Evaluate one characteristic across draws. See module docstring."""
    if req.role == "setup":
        return CharEval(status="setup", role=req.role, tier=(obs.tier if obs else "B"),
                        source_id=(obs.source_id if obs else ""))

    # Missing site observation.
    if obs is None or obs.missing:
        return CharEval(status="missing", role=req.role,
                        tier=(obs.tier if obs else "B"),
                        source_id=(obs.source_id if obs else ""))

    is_threshold = req.kind in ("threshold_min", "threshold_max")

    # Non-threshold kinds need a target value; missing target -> cannot evaluate.
    if not is_threshold and (target is None or target.missing):
        return CharEval(status="target_missing", role=req.role, tier=obs.tier,
                        source_id=obs.source_id)

    band = _effective_band(obs, scale_warning_band_add)
    proxy_must = req.role == "must" and obs.tier == "C"

    match_draws: np.ndarray
    gate_pass: np.ndarray | None = None

    if req.kind == "distribution":
        assert target is not None and target.quantiles is not None and obs.quantiles is not None
        residual = target.quantiles - obs.quantiles
        offsets = _draw_offsets(rng, band, n_draws)
        match_draws = M.match_distribution_offsets(residual, offsets, tau)
        if req.role == "must" and req.gate_stat == "p50":
            drawn_p50 = obs.quantiles[50] + offsets
            gate_pass = _gate_pass(drawn_p50, req)

    elif req.kind == "scalar":
        assert target is not None and target.scalar is not None and obs.scalar is not None
        draws = _draw_scalar(rng, obs.scalar, band, n_draws)
        match_draws = np.asarray(M.match_scalar(target.scalar, draws, tau), dtype=float)
        if req.role == "must" and req.gate_stat == "value":
            gate_pass = _gate_pass(draws, req)

    elif req.kind == "ordinal":
        assert target is not None and target.ordinal_index is not None and obs.ordinal_index is not None
        m = M.match_ordinal(target.ordinal_index, obs.ordinal_index, tau)
        match_draws = np.full(n_draws, m, dtype=float)

    elif req.kind == "envelope":
        assert target is not None and target.envelope is not None and obs.quantiles is not None
        offsets = _draw_offsets(rng, band, n_draws)
        lo = obs.quantiles[1] + offsets
        hi = obs.quantiles[99] + offsets
        r0, r1 = target.envelope
        match_draws = np.asarray(M.match_envelope(lo, hi, r0, r1), dtype=float)
        if req.role == "must" and req.gate_stat == "overlap":
            gate_pass = _gate_pass(match_draws, req)

    elif req.kind in ("threshold_min", "threshold_max"):
        assert req.req_value is not None and req.req_tau is not None
        # Use the scalar value, or the distribution median for distribution characteristics.
        nominal = obs.scalar
        if nominal is None and obs.quantiles is not None:
            nominal = float(obs.quantiles[50])
        assert nominal is not None
        draws = _draw_scalar(rng, nominal, band, n_draws)
        if req.kind == "threshold_min":
            match_draws = np.asarray(M.match_threshold_min(draws, req.req_value, req.req_tau), dtype=float)
            gate_src = draws >= req.req_value
        else:
            match_draws = np.asarray(M.match_threshold_max(draws, req.req_value, req.req_tau), dtype=float)
            gate_src = draws <= req.req_value
        if req.role == "must":
            gate_pass = gate_src

    else:  # pragma: no cover - guarded by config validation
        raise ValueError(f"unknown kind {req.kind!r}")

    return CharEval(
        status="proxy" if proxy_must else "ok",
        role=req.role,
        tier=obs.tier,
        source_id=obs.source_id,
        match_draws=match_draws,
        gate_pass_draws=gate_pass,
        is_proxy_must=proxy_must,
        value_display=_value_display(obs),
    )
