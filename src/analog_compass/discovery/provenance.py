"""Geo helpers + provenance records for discovery nominees."""

from __future__ import annotations

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def cluster_id(lat: float, lon: float, cell_deg: float = 10.0) -> int:
    """Snap to a coarse grid for spatial de-duplication (docs/04 Stage 2)."""
    row = int((lat + 90) // cell_deg)
    col = int((lon + 180) // cell_deg)
    return row * 1000 + col
