#!/usr/bin/env python3
"""Validate api/openapi.yaml against the OpenAPI schema (and resolve internal refs)."""

from __future__ import annotations

from pathlib import Path

import yaml
from openapi_spec_validator import validate

import _bootstrap  # noqa: F401

SPEC = Path(__file__).resolve().parents[1] / "api" / "openapi.yaml"


def main() -> int:
    with SPEC.open(encoding="utf-8") as fh:
        spec = yaml.safe_load(fh)
    try:
        validate(spec)
    except Exception as exc:  # noqa: BLE001 - report and fail
        print(f"FAIL: openapi.yaml invalid:\n{exc}")
        return 1
    n_paths = len(spec.get("paths", {}))
    n_schemas = len(spec.get("components", {}).get("schemas", {}))
    print(f"OK: openapi.yaml valid — {n_paths} paths, {n_schemas} schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
