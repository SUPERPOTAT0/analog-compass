"""The engine must stay pure: no I/O, no clock, no unseeded randomness."""

from __future__ import annotations

from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2] / "src" / "analog_compass" / "engine"
FORBIDDEN = ["import os", "import time", "import datetime", "import random",
             "import requests", "open(", "time.time", "datetime.now", "np.random.seed"]


def test_engine_has_no_io_or_clock_or_unseeded_rng() -> None:
    offenders = []
    for path in ENGINE.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            if token in text:
                offenders.append(f"{path.name}: {token}")
    assert not offenders, f"engine purity violations: {offenders}"


def test_engine_uses_seeded_generator_only() -> None:
    mc = (ENGINE / "montecarlo.py").read_text(encoding="utf-8")
    # draws come from an explicitly-seeded Generator passed in, never a global.
    assert "default_rng" not in mc, "montecarlo must receive a seeded rng, not create one"
