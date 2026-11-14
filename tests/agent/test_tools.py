"""Agent tools are backed by the engine/KB and run fully offline (no network)."""

from __future__ import annotations

import json

from analog_compass.agent import tools


def test_tool_specs_wellformed() -> None:
    names = {t["name"] for t in tools.TOOL_SPECS}
    assert {"compare_sites", "discover", "site_suitability", "characteristic_info"}.issubset(names)
    for spec in tools.TOOL_SPECS:
        assert spec["input_schema"]["type"] == "object"


def test_compare_tool_returns_grounded_result() -> None:
    out = json.loads(tools.dispatch("compare_sites", {
        "target_id": "mars_mid_latitude", "test_id": "rover_traverse_autonomy"}))
    assert out["run_id"] and out["sites"]
    assert out["data_mode"] in {"synthetic", "real"}


def test_characteristic_info_exposes_tier() -> None:
    ci = json.loads(tools.dispatch("characteristic_info", {"characteristic_id": "permafrost_index"}))
    assert ci["tier"] == "C"
    assert ci["proxy_for"]


def test_unknown_tool_raises() -> None:
    import pytest

    with pytest.raises(KeyError):
        tools.dispatch("nonexistent_tool", {})
