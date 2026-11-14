#!/usr/bin/env python3
"""Run the contract test suite (tests/contract). App exists since T-020."""

from __future__ import annotations

from pathlib import Path

import pytest

import _bootstrap  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    return int(pytest.main([str(ROOT / "tests" / "contract"), "-q"]))


if __name__ == "__main__":
    raise SystemExit(main())
