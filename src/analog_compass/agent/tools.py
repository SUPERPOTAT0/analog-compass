"""Read-only tools the agent calls. Every tool is backed by the deterministic engine,
discovery, suitability or KB — so the agent cannot invent a characteristic value.

`dispatch` returns a compact JSON string; tool outputs are the ONLY external facts the
agent may use in its answer (docs/08_AI_AGENT.md §1/§3).
"""

from __future__ import annotations

import json
from typing import Any

from analog_compass import kb, service

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "list_targets",
        "description": "List available Moon/Mars target environments (ids, bodies, labels).",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "list_tests",
        "description": "List test/operation templates (ids, labels, rationale, domains).",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "list_sites",
        "description": "List curated candidate Earth sites (ids, labels, coordinates).",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "compare_sites",
        "description": "Rank curated sites for a target x test. Returns verdicts, scores, gate "
                       "pass-rates and honest-limit notes with a reproducible run_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string"},
                "test_id": {"type": "string"},
                "site_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["target_id", "test_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "site_suitability",
        "description": "For one curated site, which tests it can support (pass/borderline/"
                       "excluded) and the limiting characteristic for each.",
        "input_schema": {
            "type": "object",
            "properties": {
                "site_id": {"type": "string"},
                "target_id": {"type": "string"},
            },
            "required": ["site_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "discover",
        "description": "Discover NEW candidate windows anywhere on Earth for a target x test "
                       "via the Offline Candidate Screen. Returns new candidates with provenance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_id": {"type": "string"},
                "test_id": {"type": "string"},
                "k": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["target_id", "test_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "target_facts",
        "description": "Cited environmental facts about a target, each with a verification grade.",
        "input_schema": {
            "type": "object",
            "properties": {"target_id": {"type": "string"}},
            "required": ["target_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "characteristic_info",
        "description": "What a characteristic measures, its unit, data source, evidence tier, "
                       "and what (if anything) it is a proxy for.",
        "input_schema": {
            "type": "object",
            "properties": {"characteristic_id": {"type": "string"}},
            "required": ["characteristic_id"],
            "additionalProperties": False,
        },
    },
]


def _trim_result(result: dict[str, Any]) -> dict[str, Any]:
    sites = []
    for s in result["sites"]:
        sites.append({
            "site_id": s["site_id"],
            "label": s["label"],
            "candidate_kind": s["candidate_kind"],
            "verdict": s["verdict"],
            "p_gate": s["p_gate"],
            "score": s["score"],
            "coverage": s["coverage"],
            "honest_limits": s["honest_limits"],
            "key_characteristics": [
                {"characteristic": c["characteristic"], "status": c["status"],
                 "tier": c["tier"], "match": c["match"], "gate_pass_rate": c["gate_pass_rate"],
                 "source_id": c["source_id"]}
                for c in s["characteristics"] if c["status"] != "setup"
            ],
            "provenance": s.get("provenance"),
        })
    return {"run_id": result["run_id"], "data_version": result["data_version"],
            "data_mode": result["data_mode"], "target_id": result["target_id"],
            "test_id": result["test_id"], "sites": sites}


def dispatch(name: str, tool_input: dict[str, Any]) -> str:
    from analog_compass.api import serialize

    if name == "list_targets":
        return json.dumps(kb.list_targets())
    if name == "list_tests":
        return json.dumps(kb.list_tests())
    if name == "list_sites":
        return json.dumps(kb.list_sites())
    if name == "compare_sites":
        res = service.run_compare(tool_input["target_id"], tool_input["test_id"],
                                  tool_input.get("site_ids"))
        return json.dumps(_trim_result(serialize.result_to_dict(res)))
    if name == "site_suitability":
        return json.dumps(service.run_suitability(tool_input["site_id"],
                                                  tool_input.get("target_id")))
    if name == "discover":
        res = service.run_discover(tool_input["target_id"], tool_input["test_id"],
                                   k=int(tool_input.get("k", 8)))
        return json.dumps(_trim_result(serialize.result_to_dict(res)))
    if name == "target_facts":
        return json.dumps(kb.target_facts(tool_input["target_id"]))
    if name == "characteristic_info":
        return json.dumps(kb.characteristic_info(tool_input["characteristic_id"]))
    raise KeyError(f"unknown tool {name!r}")
