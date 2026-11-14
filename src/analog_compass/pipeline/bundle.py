"""Bundle loader. A bundle = manifest + window records (+ descriptors).

The synthetic bundle mirrors the real schema exactly, so swapping in real data is a
config flip, not a rewrite (docs/05_DATA_SPEC.md §7). `data_mode=real` forbids any
window sourced from the synthetic generator (QA Q-19).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from analog_compass.engine.types import CharObservation, SiteObservation
from analog_compass.settings import get_settings


def _char_obs(spec: dict[str, Any]) -> CharObservation:
    q = spec.get("quantiles")
    env = spec.get("envelope")
    return CharObservation(
        kind=spec["kind"],
        tier=spec.get("tier", "B"),
        missing=bool(spec.get("missing", False)),
        source_id=spec.get("source_id", ""),
        band=float(spec.get("band", 0.0)),
        scale_warning=bool(spec.get("scale_warning", False)),
        scalar=(None if spec.get("scalar") is None else float(spec["scalar"])),
        quantiles=(np.asarray(q, dtype=float) if q is not None else None),
        envelope=(tuple(env) if env is not None else None),
        ordinal_index=spec.get("ordinal_index"),
    )


@dataclass
class Window:
    grid_id: str
    lat: float
    lon: float
    bbox: list[float]
    curated_site_id: str | None
    chars: dict[str, dict[str, Any]]

    def observation(self, *, candidate_kind: str = "new",
                    provenance: dict | None = None) -> SiteObservation:
        return SiteObservation(
            site_id=self.curated_site_id or self.grid_id,
            label=self.curated_site_id or self.grid_id,
            candidate_kind=candidate_kind,  # type: ignore[arg-type]
            lat=self.lat,
            lon=self.lon,
            chars={k: _char_obs(v) for k, v in self.chars.items()},
            provenance=provenance,
        )


class Bundle:
    def __init__(self, manifest: dict[str, Any], windows: list[Window]):
        self.manifest = manifest
        self.windows = windows
        self._by_site = {w.curated_site_id: w for w in windows if w.curated_site_id}

    @property
    def data_mode(self) -> str:
        return self.manifest.get("data_mode", "synthetic")

    @property
    def data_version(self) -> str:
        return self.manifest.get("data_version", "unknown")

    def curated_observations(self) -> list[SiteObservation]:
        from analog_compass import config

        pool = config.pool()
        out = []
        for site_id, site in pool.items():
            w = self._by_site.get(site_id)
            if w is None:
                continue
            obs = w.observation(candidate_kind="curated", provenance={"origin": "curated"})
            # carry the human label from the pool config
            out.append(
                SiteObservation(
                    site_id=obs.site_id, label=site.get("label", obs.label),
                    candidate_kind="curated", lat=obs.lat, lon=obs.lon,
                    chars=obs.chars, provenance=obs.provenance,
                )
            )
        return out

    def curated_observation(self, site_id: str) -> SiteObservation:
        from analog_compass import config

        w = self._by_site.get(site_id)
        if w is None:
            raise KeyError(f"no window for curated site {site_id!r}")
        label = config.pool().get(site_id, {}).get("label", site_id)
        obs = w.observation(candidate_kind="curated", provenance={"origin": "curated"})
        return SiteObservation(
            site_id=site_id, label=label, candidate_kind="curated",
            lat=obs.lat, lon=obs.lon, chars=obs.chars, provenance=obs.provenance,
        )

    def discovery_windows(self) -> list[Window]:
        """Windows eligible for discovery (not curated pool cells)."""
        return [w for w in self.windows if w.curated_site_id is None]

    def window_by_id(self, site_id: str | None = None,
                     grid_id: str | None = None) -> Window:
        if site_id and site_id in self._by_site:
            return self._by_site[site_id]
        for w in self.windows:
            if (grid_id and w.grid_id == grid_id) or (site_id and w.grid_id == site_id):
                return w
        raise KeyError(f"no window for site_id={site_id!r} grid_id={grid_id!r}")


def load_bundle(bundle_dir: Path | str | None = None) -> Bundle:
    settings = get_settings()
    d = Path(bundle_dir) if bundle_dir is not None else settings.bundle_dir
    manifest = json.loads((d / "bundle.json").read_text(encoding="utf-8"))
    records = json.loads((d / manifest["windows_file"]).read_text(encoding="utf-8"))

    if settings.data_mode == "real" and manifest.get("data_mode") == "synthetic":
        raise RuntimeError("Q-19: data_mode=real but bundle is synthetic — refusing to run.")

    windows = [
        Window(
            grid_id=r["grid_id"],
            lat=float(r["lat"]),
            lon=float(r["lon"]),
            bbox=r["bbox"],
            curated_site_id=r.get("curated_site_id"),
            chars=r["chars"],
        )
        for r in records
    ]
    return Bundle(manifest, windows)


@lru_cache(maxsize=4)
def _cached(dir_str: str) -> Bundle:
    return load_bundle(Path(dir_str))


def get_bundle() -> Bundle:
    return _cached(str(get_settings().bundle_dir))
