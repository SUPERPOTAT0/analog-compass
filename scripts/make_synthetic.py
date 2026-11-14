#!/usr/bin/env python3
"""Generate the synthetic data bundle.

Mirrors the expected real-data schema (docs/05_DATA_SPEC.md §7): same layer ids,
kinds, units, tiers and source ids. Values come from smooth latent fields so the
bundle is realistic yet small and compressible. Stamped data_mode=synthetic; it can
never leak into a real run (QA Q-19). This generator MAY fabricate values — they are
synthetic by construction and clearly labelled.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import _bootstrap  # noqa: F401
from analog_compass import config

OUT = Path(__file__).resolve().parents[1] / "data" / "synthetic"
N_RANDOM = 420
SEED = 42

BANDS = {
    "slope": 1.5, "roughness": 1.0, "temperature": 3.0, "sunlit_fraction": 0.05,
    "sun_elevation_max": 3.0, "permafrost_index": 0.1, "basaltic_volcanic_fraction": 0.08,
    "dust_aerosol_load": 0.05, "wind_speed_mean": 1.0, "vegetation_cover": 2.0,
    "remoteness_time": 30.0,
}

# Synthetic overrides for curated pool sites, to make the demo scientifically legible.
POOL_OVERRIDES: dict[str, dict] = {
    "atacama":      {"vegetation_cover": 0.4, "remoteness_time": 650, "temp_mean": 18, "permafrost_index": 0.0, "basaltic_volcanic_fraction": 0.2},
    "rio_tinto":    {"vegetation_cover": 22, "remoteness_time": 120, "basaltic_volcanic_fraction": 0.35, "temp_mean": 17},
    "devon_island": {"permafrost_index": 0.85, "remoteness_time": 1800, "vegetation_cover": 1.0, "temp_mean": -16, "slope_med": 7},
    "holuhraun":    {"basaltic_volcanic_fraction": 0.85, "cave_idx": 2, "vegetation_cover": 2, "remoteness_time": 900, "temp_mean": 1, "slope_med": 6},
    "mauna_loa":    {"basaltic_volcanic_fraction": 0.8, "vegetation_cover": 5, "remoteness_time": 300, "temp_mean": 6, "slope_med": 9, "cave_idx": 2},
    "dry_valleys":  {"permafrost_index": 0.9, "vegetation_cover": 0.2, "remoteness_time": 2200, "temp_mean": -25, "slope_med": 8},
    "lava_beds":    {"basaltic_volcanic_fraction": 0.7, "cave_idx": 3, "vegetation_cover": 20, "remoteness_time": 180, "temp_mean": 9, "slope_med": 5},
    "danakil":      {"basaltic_volcanic_fraction": 0.6, "vegetation_cover": 1.0, "remoteness_time": 1200, "temp_mean": 35, "slope_med": 4},
}


def _f1(lat: float, lon: float, phase: float) -> float:
    la, lo = np.radians(lat), np.radians(lon)
    v = (
        np.sin(2 * la + phase) * np.cos(3 * lo - phase)
        + 0.5 * np.sin(5 * lo + 2 * phase)
        + 0.5 * np.cos(4 * la - phase)
    )
    return float((np.tanh(v) + 1) / 2)


def _quantiles(med: float, spread: float, lo_floor: float | None = None,
               hi_cap: float | None = None) -> list[float]:
    pts_x = np.array([0.0, 0.01, 0.25, 0.5, 0.75, 0.99, 1.0])
    pts_y = np.array([
        med - 2.2 * spread, med - 2.0 * spread, med - 0.7 * spread, med,
        med + 0.7 * spread, med + 2.0 * spread, med + 2.2 * spread,
    ])
    levels = np.linspace(0.0, 1.0, 101)
    q = np.interp(levels, pts_x, pts_y)
    if lo_floor is not None:
        q = np.maximum(q, lo_floor)
    if hi_cap is not None:
        q = np.minimum(q, hi_cap)
    return [round(float(x), 3) for x in q]


def _window_chars(lat: float, lon: float, site_id: str | None) -> dict:
    chars_cfg = config.characteristics()
    rug = _f1(lat, lon, 0.3)
    volc = _f1(lat, lon, 1.7) ** 2
    wet = _f1(lat, lon, 3.1)
    pop = _f1(lat, lon, 4.9)
    alat = abs(lat)

    ov = POOL_OVERRIDES.get(site_id or "", {})

    slope_med = ov.get("slope_med", 2 + 28 * rug)
    rough_med = 0.2 + 10 * rug
    temp_mean = ov.get("temp_mean", 30 - 0.6 * alat + 12 * (wet - 0.5))
    temp_spread = 8 + 10 * rug
    sunlit_med = float(np.clip(0.6 - 0.5 * max(0.0, (alat - 55) / 35), 0.05, 0.95))
    sun_elev = float(np.clip(90 - alat, 5, 89))
    permafrost = ov.get("permafrost_index",
                         float(np.clip((alat - 50) / 35 + 0.3 * rug * max(0, (alat - 40) / 50), 0, 1)))
    basalt = ov.get("basaltic_volcanic_fraction", float(np.clip(volc, 0, 1)))
    veg = ov.get("vegetation_cover", float(np.clip(90 * wet - 0.5 * alat, 0, 95)))
    remote = ov.get("remoteness_time", float(np.clip(2400 * (1 - pop), 2, 3000)))
    dust = float(np.clip(0.05 + 0.5 * (1 - wet), 0.02, 0.9))
    wind = float(np.clip(2 + 8 * (1 - wet), 0.5, 15))
    if "cave_idx" in ov:
        cave_idx = int(ov["cave_idx"])
    else:
        cave_idx = 2 if (basalt > 0.5 and rug > 0.5) else (1 if basalt > 0.4 else 0)

    def tier(cid: str) -> str:
        return chars_cfg[cid].get("tier", "B")

    def src(cid: str) -> str:
        return chars_cfg[cid].get("source_id", "")

    def dist(cid: str, med: float, spread: float, lo=None, hi=None) -> dict:
        return {"kind": "distribution", "tier": tier(cid), "source_id": src(cid),
                "band": BANDS[cid], "quantiles": _quantiles(med, spread, lo, hi)}

    def scal(cid: str, value: float) -> dict:
        return {"kind": "scalar", "tier": tier(cid), "source_id": src(cid),
                "band": BANDS[cid], "scalar": round(float(value), 4)}

    chars = {
        "slope": dist("slope", slope_med, max(0.5, 0.4 * slope_med), lo=0.0),
        "roughness": dist("roughness", rough_med, max(0.2, 0.4 * rough_med), lo=0.0),
        "temperature": dist("temperature", temp_mean, temp_spread),
        "sunlit_fraction": dist("sunlit_fraction", sunlit_med, 0.15, lo=0.0, hi=1.0),
        "sun_elevation_max": scal("sun_elevation_max", sun_elev),
        "permafrost_index": scal("permafrost_index", permafrost),
        "basaltic_volcanic_fraction": scal("basaltic_volcanic_fraction", basalt),
        "dust_aerosol_load": scal("dust_aerosol_load", dust),
        "wind_speed_mean": scal("wind_speed_mean", wind),
        "vegetation_cover": scal("vegetation_cover", veg),
        "remoteness_time": scal("remoteness_time", remote),
        "cave_evidence": {"kind": "ordinal", "tier": tier("cave_evidence"),
                          "source_id": src("cave_evidence"), "band": 0.0,
                          "ordinal_index": cave_idx},
        "logistics_access": {"kind": "setup", "tier": "B", "source_id": "curated",
                             "band": 0.0, "scalar": None},
    }
    # Travel-time coverage hole: outside 85N-60S -> missing (outside_coverage).
    if lat > 85 or lat < -60:
        chars["remoteness_time"] = {"kind": "scalar", "tier": tier("remoteness_time"),
                                    "source_id": src("remoteness_time"), "band": 0.0,
                                    "scalar": None, "missing": True}
    return chars


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    records = []

    # Curated pool windows at their real coordinates.
    for site_id, site in config.pool().items():
        lat, lon = float(site["lat"]), float(site["lon"])
        records.append({
            "grid_id": f"pool-{site_id}",
            "lat": lat, "lon": lon,
            "bbox": [lon - 0.125, lat - 0.125, lon + 0.125, lat + 0.125],
            "curated_site_id": site_id,
            "chars": _window_chars(lat, lon, site_id),
        })

    # Random discovery windows across the globe.
    lats = rng.uniform(-78, 82, N_RANDOM)
    lons = rng.uniform(-180, 180, N_RANDOM)
    for i in range(N_RANDOM):
        lat, lon = float(lats[i]), float(lons[i])
        records.append({
            "grid_id": f"w{i:04d}",
            "lat": round(lat, 4), "lon": round(lon, 4),
            "bbox": [round(lon - 0.125, 4), round(lat - 0.125, 4),
                     round(lon + 0.125, 4), round(lat + 0.125, 4)],
            "curated_site_id": None,
            "chars": _window_chars(lat, lon, None),
        })

    chars_cfg = config.characteristics()
    srcs = config.sources()
    layers = [
        {"layer_id": cid, "kind": c["kind"], "unit": c.get("unit"),
         "source_id": c.get("source_id"), "tier": c.get("tier", "B"),
         "licence": srcs.get(c.get("source_id", ""), {}).get("licence", "unknown")}
        for cid, c in chars_cfg.items()
    ]
    manifest = {
        "data_mode": "synthetic",
        "data_version": "synthetic-0.1.0",
        "screen_version": "1.0.0",
        "grid_spacing_deg": 0.25,
        "coverage_bbox": [-180, -78, 180, 85],
        "windows_file": "windows.json",
        "n_windows": len(records),
        "layers": layers,
    }
    (OUT / "windows.json").write_text(json.dumps(records), encoding="utf-8")
    (OUT / "bundle.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    size_kb = (OUT / "windows.json").stat().st_size / 1024
    print(f"wrote {len(records)} windows -> {OUT}/windows.json ({size_kb:.0f} KB)")
    print(f"manifest -> {OUT}/bundle.json  data_mode=synthetic data_version=synthetic-0.1.0")


if __name__ == "__main__":
    main()
