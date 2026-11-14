"""Pure, deterministic scoring engine.

No module in this package may perform I/O, read the clock, or use unseeded
randomness. Enforced by tests/engine/test_purity.py. See docs/03_ENGINE_SPEC.md.
"""

from analog_compass.engine.score import compare
from analog_compass.engine.types import (
    CharObservation,
    EngineParams,
    EngineRequest,
    Requirement,
    SiteObservation,
    SiteResult,
    TargetChar,
)

__all__ = [
    "compare",
    "CharObservation",
    "EngineParams",
    "EngineRequest",
    "Requirement",
    "SiteObservation",
    "SiteResult",
    "TargetChar",
]
