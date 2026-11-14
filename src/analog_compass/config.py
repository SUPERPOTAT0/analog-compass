"""Load and lightly validate the declarative config in config/*.yaml.

This is the only place YAML is read for domain config. Loaders cache per path.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

import yaml

from analog_compass.settings import get_settings


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"expected a mapping at top of {path}")
    return data


@cache
def _cfg(name: str) -> dict[str, Any]:
    return _load_yaml(get_settings().config_dir / name)


def params() -> dict[str, Any]:
    return _cfg("params.yaml")


def characteristics() -> dict[str, dict[str, Any]]:
    return {c["id"]: c for c in _cfg("characteristics.yaml")["characteristics"]}


def sources() -> dict[str, dict[str, Any]]:
    return {s["id"]: s for s in _cfg("sources.yaml")["sources"]}


def domains() -> list[dict[str, Any]]:
    return _cfg("domains.yaml")["domains"]


def targets() -> dict[str, dict[str, Any]]:
    return {t["target_id"]: t for t in _cfg("targets.yaml")["targets"]}


def tests() -> dict[str, dict[str, Any]]:
    return {t["test_id"]: t for t in _cfg("tests.yaml")["tests"]}


def pool() -> dict[str, dict[str, Any]]:
    return {s["site_id"]: s for s in _cfg("pool.yaml")["pool"]}


def clear_cache() -> None:
    _cfg.cache_clear()
