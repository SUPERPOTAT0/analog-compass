#!/usr/bin/env python3
"""Print tool versions and check required env var NAMES exist (never values)."""

from __future__ import annotations

import os
import platform

import _bootstrap  # noqa: F401

REQUIRED_ENV = ["DATA_MODE", "DATA_BUNDLE_URI", "DATA_VERSION"]
OPTIONAL_ENV = ["ANTHROPIC_API_KEY", "ANALOG_AGENT_MODEL", "ALLOWED_ORIGINS"]


def _ver(mod: str) -> str:
    try:
        m = __import__(mod)
        return getattr(m, "__version__", "?")
    except Exception as exc:  # noqa: BLE001 - diagnostic only
        return f"not importable ({exc})"


def main() -> int:
    print(f"python         {platform.python_version()}")
    for mod in ("numpy", "pydantic", "fastapi", "yaml"):
        print(f"{mod:<14} {_ver(mod)}")
    print("\nenv var names (presence only, values never printed):")
    ok = True
    for name in REQUIRED_ENV:
        present = name in os.environ
        print(f"  [{'x' if present else ' '}] {name} (required)")
    for name in OPTIONAL_ENV:
        present = name in os.environ
        print(f"  [{'x' if present else ' '}] {name} (optional)")
    print("\nnote: required vars have code defaults, so absence is not fatal in dev.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
