"""Verdict decision (docs/03_ENGINE_SPEC.md §7). Pure."""

from __future__ import annotations

from analog_compass.engine.types import EngineParams, Verdict


def decide(
    p_gate: float,
    score: float,
    has_must: bool,
    proxy_must_present: bool,
    params: EngineParams,
) -> Verdict:
    """Map gate pass-rate + score to a verdict.

    - `pass` requires the Must set to hold in most draws AND a good score.
    - `excluded` when the Must set fails in almost every draw.
    - otherwise `borderline`.
    A proxy-only Must caps the best achievable verdict at `borderline`
    (a tier-C proxy can never, by itself, grant a hard pass; §3).
    """
    if has_must and p_gate <= params.exclude_gate:
        return "excluded"
    if has_must and p_gate >= params.pass_gate and score >= params.pass_score:
        return "borderline" if proxy_must_present else "pass"
    if not has_must and score >= params.pass_score:
        return "pass"
    return "borderline"
