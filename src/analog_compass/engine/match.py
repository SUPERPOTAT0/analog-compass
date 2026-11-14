"""Match functions (docs/03_ENGINE_SPEC.md §5). Pure; NumPy-vectorised over draws.

Each returns a match m in [0, 1]. Functions accept scalars or NumPy arrays so the
same code serves a single nominal computation and a batch of Monte Carlo draws.
"""

from __future__ import annotations

import numpy as np


def _clip01(x: np.ndarray | float) -> np.ndarray | float:
    return np.clip(x, 0.0, 1.0)


def wasserstein1(q_target: np.ndarray, q_site: np.ndarray) -> float:
    """1-D Wasserstein-1 distance between two equal-length quantile arrays."""
    if q_target.shape != q_site.shape:
        raise ValueError("quantile arrays must have the same shape")
    return float(np.mean(np.abs(q_target - q_site)))


def match_distribution(q_target: np.ndarray, q_site: np.ndarray, tau: float) -> float:
    d = wasserstein1(q_target, q_site)
    return float(_clip01(1.0 - d / tau))


def match_distribution_offsets(
    residual: np.ndarray, offsets: np.ndarray, tau: float
) -> np.ndarray:
    """Vectorised distribution match for Monte Carlo.

    `residual[k] = q_target[k] - q_site_nominal[k]`. Each draw shifts the site
    distribution by a scalar `offset`, so the drawn distance is
    `d = mean_k |residual[k] - offset|`. Returns one match per offset.
    """
    # (n_draws, n_levels) broadcast then mean over levels.
    d = np.mean(np.abs(residual[None, :] - offsets[:, None]), axis=1)
    return np.clip(1.0 - d / tau, 0.0, 1.0)


def match_scalar(x_target: np.ndarray | float, x_site: np.ndarray | float, tau: float) -> np.ndarray | float:
    return _clip01(1.0 - np.abs(np.asarray(x_target) - np.asarray(x_site)) / tau)


def match_ordinal(idx_target: int, idx_site: int, tau: float) -> float:
    return float(_clip01(1.0 - abs(idx_target - idx_site) / tau))


def match_envelope(
    lo: np.ndarray | float, hi: np.ndarray | float, r0: float, r1: float
) -> np.ndarray | float:
    """Fraction of the required range [r0, r1] covered by the site range [lo, hi]."""
    if r1 <= r0:
        raise ValueError("envelope requires r1 > r0")
    lo = np.asarray(lo, dtype=float)
    hi = np.asarray(hi, dtype=float)
    overlap = np.minimum(hi, r1) - np.maximum(lo, r0)
    return _clip01(np.maximum(0.0, overlap) / (r1 - r0))


def match_threshold_min(
    x_site: np.ndarray | float, r: float, tau: float
) -> np.ndarray | float:
    x = np.asarray(x_site, dtype=float)
    return np.where(x >= r, 1.0, _clip01(1.0 - (r - x) / tau))


def match_threshold_max(
    x_site: np.ndarray | float, r: float, tau: float
) -> np.ndarray | float:
    x = np.asarray(x_site, dtype=float)
    return np.where(x <= r, 1.0, _clip01(1.0 - (x - r) / tau))
