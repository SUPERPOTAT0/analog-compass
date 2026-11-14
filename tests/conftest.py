"""Shared fixtures. Ensures the synthetic bundle exists before data-dependent tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def _ensure_bundle() -> None:
    bundle = ROOT / "data" / "synthetic" / "windows.json"
    if not bundle.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_synthetic.py")],
                       check=True)
