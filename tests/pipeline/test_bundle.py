"""Bundle loader + observation construction."""

from __future__ import annotations

from analog_compass import config
from analog_compass.pipeline.bundle import get_bundle


def test_curated_observations_cover_pool() -> None:
    b = get_bundle()
    obs = {o.site_id for o in b.curated_observations()}
    assert set(config.pool()).issubset(obs)


def test_missing_is_preserved_not_zeroed() -> None:
    # Dry Valleys sits below 60S, outside the travel-time coverage -> remoteness missing.
    b = get_bundle()
    dv = b.curated_observation("dry_valleys")
    rt = dv.chars["remoteness_time"]
    assert rt.missing is True
    assert rt.scalar is None  # never backfilled with a number


def test_discovery_windows_exclude_curated_cells() -> None:
    b = get_bundle()
    assert all(w.curated_site_id is None for w in b.discovery_windows())
