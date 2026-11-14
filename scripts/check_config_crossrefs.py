#!/usr/bin/env python3
"""Validate cross-references across config/*.yaml, docs domains and the contract.

Fails (exit 1) on any dangling reference so a broken config never reaches the engine.
"""

from __future__ import annotations

import _bootstrap  # noqa: F401
from analog_compass import config

VALID_KINDS = {"distribution", "scalar", "ordinal", "envelope", "threshold_min",
               "threshold_max", "setup"}


def main() -> int:
    errors: list[str] = []
    chars = config.characteristics()
    srcs = config.sources()
    char_ids = set(chars)

    # characteristics -> sources
    for cid, c in chars.items():
        sid = c.get("source_id")
        if sid and sid not in srcs:
            errors.append(f"characteristic {cid}: unknown source_id {sid!r}")
        if c["kind"] not in VALID_KINDS:
            errors.append(f"characteristic {cid}: invalid kind {c['kind']!r}")

    # sources.used_for -> characteristics
    for sid, s in srcs.items():
        for cid in s.get("used_for", []):
            if cid not in char_ids:
                errors.append(f"source {sid}: used_for unknown characteristic {cid!r}")

    # domains -> characteristics
    for d in config.domains():
        for cid in d.get("characteristics", []):
            if cid not in char_ids:
                errors.append(f"domain {d['id']}: unknown characteristic {cid!r}")

    # targets -> characteristics
    for tid, t in config.targets().items():
        for cid in t["characteristics"]:
            if cid not in char_ids:
                errors.append(f"target {tid}: unknown characteristic {cid!r}")
        for fact in t.get("facts", []):
            if fact.get("source_id") and fact["source_id"] not in srcs:
                errors.append(f"target {tid} fact {fact.get('id')}: unknown source_id")

    # tests -> characteristics + kind sanity
    for tid, t in config.tests().items():
        wsum = 0.0
        for r in t["requirements"]:
            cid = r["characteristic"]
            if cid not in char_ids:
                errors.append(f"test {tid}: unknown characteristic {cid!r}")
            if r["role"] != "setup" and r.get("kind") not in VALID_KINDS:
                errors.append(f"test {tid}/{cid}: invalid kind {r.get('kind')!r}")
            # proxy Must must declare evidence_floor C (tier-C guardrail)
            if (r.get("role") == "must" and chars.get(cid, {}).get("tier") == "C"
                    and r.get("evidence_floor") != "C"):
                errors.append(f"test {tid}/{cid}: proxy Must must set evidence_floor: C")
            wsum += float(r.get("weight", 0.0))
        if abs(wsum - 1.0) > 0.001 and wsum > 0:
            errors.append(f"test {tid}: requirement weights sum to {wsum:.3f}, expected ~1.0")

    # pool -> domains referenced by noted_for
    domain_ids = {d["id"] for d in config.domains()}
    for sid, s in config.pool().items():
        for dom in s.get("noted_for", []):
            if dom not in domain_ids:
                errors.append(f"pool {sid}: noted_for unknown domain {dom!r}")

    if errors:
        print("config-check FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK: config cross-references valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
