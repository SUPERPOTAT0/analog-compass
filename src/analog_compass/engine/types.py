"""Frozen types for the pure engine. No I/O, no clock, no unseeded RNG."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

Kind = Literal["distribution", "scalar", "ordinal", "envelope", "threshold_min", "threshold_max"]
Role = Literal["must", "scored", "setup"]
Tier = Literal["A", "B", "C"]
Verdict = Literal["pass", "borderline", "excluded", "blocked"]

N_LEVELS = 101  # quantile levels 0..100%


def quantiles_from_control_points(points: dict[float, float]) -> np.ndarray:
    """Build a 101-value quantile array (levels 0..1) from sparse control points.

    `points` maps a level in [0, 1] to a value. Linear interpolation between the
    given points; flat extrapolation outside the provided range. Pure.
    """
    levels = np.linspace(0.0, 1.0, N_LEVELS)
    xs = np.array(sorted(points.keys()), dtype=float)
    ys = np.array([points[k] for k in sorted(points.keys())], dtype=float)
    return np.interp(levels, xs, ys)


@dataclass(frozen=True)
class TargetChar:
    """A target's value for one characteristic (what a site is matched against)."""

    kind: Kind
    tier: Tier = "B"
    missing: bool = False
    scalar: float | None = None
    quantiles: np.ndarray | None = None  # length N_LEVELS, for distribution
    envelope: tuple[float, float] | None = None  # for envelope kind
    ordinal_index: int | None = None  # for ordinal kind


@dataclass(frozen=True)
class CharObservation:
    """A site's observed value for one characteristic."""

    kind: Kind
    tier: Tier = "B"
    missing: bool = False
    source_id: str = ""
    band: float = 0.0  # uncertainty half-width used by the Monte Carlo
    scale_warning: bool = False
    scalar: float | None = None
    quantiles: np.ndarray | None = None
    envelope: tuple[float, float] | None = None
    ordinal_index: int | None = None


@dataclass(frozen=True)
class Requirement:
    """A test's requirement on one characteristic."""

    characteristic: str
    role: Role
    kind: Kind
    weight: float = 0.0
    tau: float | None = None
    # gate for distribution/scalar/ordinal/envelope Must characteristics:
    gate_stat: Literal["p50", "value", "overlap"] | None = None
    gate_min: float | None = None
    gate_max: float | None = None
    # requirement for threshold_min/max kinds:
    req_value: float | None = None
    req_tau: float | None = None
    evidence_floor: Tier | None = None
    rationale: str = ""


@dataclass(frozen=True)
class EngineParams:
    n_draws: int = 512
    pass_gate: float = 0.80
    pass_score: float = 0.60
    exclude_gate: float = 0.20
    scale_warning_band_add: float = 0.10
    seed_salt: str = "analog-compass"
    engine_version: str = "0.1.0"
    default_tau: dict[str, float] = field(
        default_factory=lambda: {"distribution": 8.0, "scalar": 0.25, "ordinal": 1.0}
    )


@dataclass(frozen=True)
class SiteObservation:
    site_id: str
    label: str
    candidate_kind: Literal["curated", "new"] = "curated"
    lat: float | None = None
    lon: float | None = None
    chars: dict[str, CharObservation] = field(default_factory=dict)
    provenance: dict | None = None


@dataclass(frozen=True)
class EngineRequest:
    target_id: str
    test_id: str
    target: dict[str, TargetChar]
    requirements: tuple[Requirement, ...]
    sites: tuple[SiteObservation, ...]
    params: EngineParams
    data_version: str
    data_mode: Literal["synthetic", "real"] = "synthetic"


@dataclass(frozen=True)
class CharResult:
    characteristic: str
    role: Role
    status: Literal["ok", "missing", "setup", "proxy"]
    tier: Tier
    source_id: str = ""
    match: float | None = None
    contribution: float | None = None
    gate_pass_rate: float | None = None
    value_display: str | None = None  # raw observed value (median/scalar/ordinal) for UIs


@dataclass(frozen=True)
class SiteResult:
    site_id: str
    label: str
    candidate_kind: Literal["curated", "new"]
    verdict: Verdict
    p_gate: float
    score: float
    score_band: tuple[float, float]
    coverage: float
    characteristics: tuple[CharResult, ...]
    honest_limits: tuple[str, ...]
    lat: float | None = None
    lon: float | None = None
    provenance: dict | None = None


@dataclass(frozen=True)
class CompareResult:
    run_id: str
    seed: int
    data_version: str
    data_mode: str
    engine_version: str
    target_id: str
    test_id: str
    sites: tuple[SiteResult, ...]
