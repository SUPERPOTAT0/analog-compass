"""Unit tests for the match functions (docs/03_ENGINE_SPEC.md §5)."""

from __future__ import annotations

import numpy as np

from analog_compass.engine import match as M


def test_scalar_exact_and_tolerance() -> None:
    assert M.match_scalar(10.0, 10.0, 2.0) == 1.0
    assert M.match_scalar(10.0, 11.0, 2.0) == 0.5
    assert M.match_scalar(10.0, 20.0, 2.0) == 0.0  # clipped at 0


def test_ordinal() -> None:
    assert M.match_ordinal(2, 2, 1.0) == 1.0
    assert M.match_ordinal(2, 3, 1.0) == 0.0
    assert M.match_ordinal(2, 3, 2.0) == 0.5


def test_envelope_overlap_fraction() -> None:
    # site range fully covers required range -> 1.0
    assert M.match_envelope(-100.0, 50.0, -50.0, 0.0) == 1.0
    # half overlap
    assert abs(M.match_envelope(-25.0, 100.0, -50.0, 0.0) - 0.5) < 1e-9
    # disjoint -> 0
    assert M.match_envelope(10.0, 20.0, -50.0, 0.0) == 0.0


def test_threshold_min_max() -> None:
    assert M.match_threshold_min(150.0, 120.0, 120.0) == 1.0
    assert M.match_threshold_min(60.0, 120.0, 120.0) == 0.5
    assert M.match_threshold_max(3.0, 5.0, 10.0) == 1.0
    assert M.match_threshold_max(10.0, 5.0, 10.0) == 0.5


def test_distribution_offsets_vectorised_matches_scalar_path() -> None:
    q_t = np.linspace(0, 10, 101)
    q_s = np.linspace(2, 12, 101)  # shifted by +2 everywhere
    residual = q_t - q_s  # == -2 everywhere
    offsets = np.array([0.0, -2.0, 2.0])
    out = M.match_distribution_offsets(residual, offsets, tau=4.0)
    # offset 0 -> d=2 -> m=0.5 ; offset -2 -> d=0 -> m=1 ; offset 2 -> d=4 -> m=0
    assert abs(out[0] - 0.5) < 1e-9
    assert abs(out[1] - 1.0) < 1e-9
    assert abs(out[2] - 0.0) < 1e-9
