"""Engine orchestration: compare sites against a target x test. Pure & deterministic.

`compare(request)` derives a seed and run_id from the canonical request (no clock),
runs the Monte Carlo per site with per-draw gating, and returns verdicts + evidence
+ honest-limit notes. See docs/03_ENGINE_SPEC.md.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from analog_compass.engine import text
from analog_compass.engine.montecarlo import CharEval, evaluate_char
from analog_compass.engine.types import (
    CharResult,
    CompareResult,
    EngineRequest,
    Requirement,
    SiteObservation,
    SiteResult,
    Verdict,
)
from analog_compass.engine.verdict import decide


def _round_arr(a: np.ndarray | None) -> list[float] | None:
    if a is None:
        return None
    return [round(float(x), 6) for x in a.tolist()]


def _canonical(request: EngineRequest) -> str:
    """Stable JSON of the parts of the request that determine the result."""
    p = request.params
    obj = {
        "target_id": request.target_id,
        "test_id": request.test_id,
        "data_version": request.data_version,
        "data_mode": request.data_mode,
        "engine_version": p.engine_version,
        "params": {
            "n_draws": p.n_draws,
            "pass_gate": p.pass_gate,
            "pass_score": p.pass_score,
            "exclude_gate": p.exclude_gate,
            "scale_warning_band_add": p.scale_warning_band_add,
        },
        "requirements": [
            {
                "characteristic": r.characteristic,
                "role": r.role,
                "kind": r.kind,
                "weight": r.weight,
                "tau": r.tau,
                "gate": [r.gate_stat, r.gate_min, r.gate_max],
                "req": [r.req_value, r.req_tau],
                "evidence_floor": r.evidence_floor,
            }
            for r in sorted(request.requirements, key=lambda x: x.characteristic)
        ],
        "target": {
            k: {
                "kind": v.kind,
                "tier": v.tier,
                "missing": v.missing,
                "scalar": v.scalar,
                "quantiles": _round_arr(v.quantiles),
                "envelope": list(v.envelope) if v.envelope else None,
                "ordinal_index": v.ordinal_index,
            }
            for k, v in sorted(request.target.items())
        },
        "sites": [
            {
                "site_id": s.site_id,
                "candidate_kind": s.candidate_kind,
                "chars": {
                    k: {
                        "kind": c.kind,
                        "tier": c.tier,
                        "missing": c.missing,
                        "band": round(c.band, 6),
                        "scale_warning": c.scale_warning,
                        "scalar": c.scalar,
                        "quantiles": _round_arr(c.quantiles),
                        "envelope": list(c.envelope) if c.envelope else None,
                        "ordinal_index": c.ordinal_index,
                    }
                    for k, c in sorted(s.chars.items())
                },
            }
            for s in sorted(request.sites, key=lambda x: x.site_id)
        ],
    }
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _digest(payload: str, salt: str, n: int) -> bytes:
    return hashlib.blake2b((payload + "|" + salt).encode("utf-8"), digest_size=n).digest()


def derive_seed(request: EngineRequest) -> int:
    payload = _canonical(request)
    return int.from_bytes(_digest(payload, request.params.seed_salt, 8), "big")


def derive_run_id(request: EngineRequest) -> str:
    payload = _canonical(request) + "|" + request.params.engine_version
    return _digest(payload, request.params.seed_salt, 16).hex()


def _tau_for(req: Requirement, request: EngineRequest) -> float:
    if req.kind in ("threshold_min", "threshold_max"):
        # req_tau validated present for threshold kinds
        return float(req.req_tau or 1.0)
    if req.tau is not None:
        return req.tau
    return request.params.default_tau.get(req.kind, 1.0)


def _score_one_site(
    site: SiteObservation,
    request: EngineRequest,
    base_seed: int,
) -> SiteResult:
    params = request.params
    n = params.n_draws
    # Independent, deterministic RNG per site.
    site_seed = int.from_bytes(
        hashlib.blake2b(f"{base_seed}:{site.site_id}".encode(), digest_size=8).digest(), "big"
    )
    rng = np.random.default_rng(site_seed)

    evals: dict[str, CharEval] = {}
    for req in sorted(request.requirements, key=lambda x: x.characteristic):
        tc = request.target.get(req.characteristic)
        obs = site.chars.get(req.characteristic)
        tau = _tau_for(req, request)
        evals[req.characteristic] = evaluate_char(
            req, tc, obs, tau, n, rng, params.scale_warning_band_add
        )

    reqs_by_char = {r.characteristic: r for r in request.requirements}

    # --- terminal conditions from Must characteristics ---------------------
    must_chars = [c for c, r in reqs_by_char.items() if r.role == "must"]
    has_must = len(must_chars) > 0
    target_missing_must = [c for c in must_chars if evals[c].status == "target_missing"]
    site_missing_must = [c for c in must_chars if evals[c].status == "missing"]

    total_weight = sum(r.weight for r in request.requirements if r.role != "setup")
    proxy_must_chars = [c for c in must_chars if evals[c].is_proxy_must]

    if target_missing_must:
        return _terminal_site(
            site, "blocked", reqs_by_char, evals, total_weight,
            [text.note("target_missing_must", characteristic=c) for c in target_missing_must],
        )
    if site_missing_must:
        return _terminal_site(
            site, "excluded", reqs_by_char, evals, total_weight,
            [text.note("site_missing_must", characteristic=c) for c in site_missing_must],
        )

    # --- aggregate scored + must contributions over draws ------------------
    included_weight = 0.0
    draw_score = np.zeros(n)
    dropped: list[str] = []
    gate_stack: list[np.ndarray] = []
    gate_rates: dict[str, float] = {}

    for char, req in reqs_by_char.items():
        if req.role == "setup":
            continue
        ev = evals[char]
        if ev.status in ("missing", "target_missing") or ev.match_draws is None:
            dropped.append(char)
            continue
        included_weight += req.weight
        draw_score += req.weight * ev.match_draws
        if req.role == "must" and ev.gate_pass_draws is not None:
            gate_stack.append(ev.gate_pass_draws)
            gate_rates[char] = float(np.mean(ev.gate_pass_draws))

    if included_weight > 0:
        draw_score = draw_score / included_weight

    if gate_stack:
        all_gates = np.logical_and.reduce(gate_stack)
        p_gate = float(np.mean(all_gates))
    else:
        all_gates = np.ones(n, dtype=bool)
        p_gate = 1.0

    passing = draw_score[all_gates]
    if passing.size > 0:
        score = float(np.mean(passing))
        band = (float(np.percentile(passing, 10)), float(np.percentile(passing, 90)))
    else:
        score = 0.0
        band = (0.0, 0.0)

    verdict = decide(p_gate, score, has_must, bool(proxy_must_chars), params)
    coverage = float(included_weight / total_weight) if total_weight > 0 else 0.0

    # --- honest-limit notes -------------------------------------------------
    notes: list[str] = []
    if verdict == "excluded":
        notes.append(text.note("excluded_gate"))
    if verdict == "borderline" and has_must and gate_rates:
        limiting = min(gate_rates, key=lambda k: gate_rates[k])
        notes.append(
            text.note("straddles_gate", characteristic=limiting,
                      p_gate_pct=round(gate_rates[limiting] * 100))
        )
    for c in proxy_must_chars:
        notes.append(text.note("proxy_must", characteristic=c))
    if dropped:
        notes.append(
            text.note("coverage_reduced", coverage_pct=round(coverage * 100), n=len(dropped))
        )

    char_results = _char_results(reqs_by_char, evals, gate_rates, included_weight)
    return SiteResult(
        site_id=site.site_id,
        label=site.label,
        candidate_kind=site.candidate_kind,
        verdict=verdict,
        p_gate=round(p_gate, 6),
        score=round(score, 6),
        score_band=(round(band[0], 6), round(band[1], 6)),
        coverage=round(coverage, 6),
        characteristics=char_results,
        honest_limits=tuple(notes),
        lat=site.lat,
        lon=site.lon,
        provenance=site.provenance,
    )


def _char_results(
    reqs_by_char: dict[str, Requirement],
    evals: dict[str, CharEval],
    gate_rates: dict[str, float],
    included_weight: float,
) -> tuple[CharResult, ...]:
    out: list[CharResult] = []
    for char, req in sorted(reqs_by_char.items()):
        ev = evals[char]
        if req.role == "setup":
            out.append(CharResult(char, req.role, "setup", ev.tier, ev.source_id))
            continue
        if ev.match_draws is None:
            out.append(CharResult(char, req.role, "missing", ev.tier, ev.source_id))
            continue
        mean_match = float(np.mean(ev.match_draws))
        contribution = (
            round(req.weight * mean_match / included_weight, 6) if included_weight > 0 else None
        )
        out.append(
            CharResult(
                characteristic=char,
                role=req.role,
                status="proxy" if ev.is_proxy_must else "ok",
                tier=ev.tier,
                source_id=ev.source_id,
                match=round(mean_match, 6),
                contribution=contribution,
                gate_pass_rate=round(gate_rates[char], 6) if char in gate_rates else None,
                value_display=ev.value_display,
            )
        )
    return tuple(out)


def _terminal_site(
    site: SiteObservation,
    verdict: Verdict,
    reqs_by_char: dict[str, Requirement],
    evals: dict[str, CharEval],
    total_weight: float,
    notes: list[str],
) -> SiteResult:
    return SiteResult(
        site_id=site.site_id,
        label=site.label,
        candidate_kind=site.candidate_kind,
        verdict=verdict,
        p_gate=0.0,
        score=0.0,
        score_band=(0.0, 0.0),
        coverage=0.0,
        characteristics=_char_results(reqs_by_char, evals, {}, 0.0),
        honest_limits=tuple(notes),
        lat=site.lat,
        lon=site.lon,
        provenance=site.provenance,
    )


def compare(request: EngineRequest) -> CompareResult:
    """Score every site in the request. Deterministic given the request + data_version."""
    seed = derive_seed(request)
    run_id = derive_run_id(request)
    sites = tuple(
        _score_one_site(s, request, seed)
        for s in sorted(request.sites, key=lambda x: x.site_id)
    )
    # Rank: pass > borderline > blocked > excluded, then by score desc.
    order = {"pass": 0, "borderline": 1, "blocked": 2, "excluded": 3}
    sites = tuple(sorted(sites, key=lambda r: (order[r.verdict], -r.score)))
    return CompareResult(
        run_id=run_id,
        seed=seed,
        data_version=request.data_version,
        data_mode=request.data_mode,
        engine_version=request.params.engine_version,
        target_id=request.target_id,
        test_id=request.test_id,
        sites=sites,
    )
