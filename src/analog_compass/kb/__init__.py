"""Knowledge base: targets, tests and characteristic facts (docs/07_KNOWLEDGE_BASE.md).

Thin, validated accessors over config/*.yaml. The agent and API read the domain
through here so facts always carry a grade/source and nothing is free-invented.
"""

from __future__ import annotations

from typing import Any

from analog_compass import config


def list_targets() -> list[dict[str, Any]]:
    out = []
    for tid, t in config.targets().items():
        out.append({
            "target_id": tid,
            "body": t["body"],
            "label": t["label"],
            "characteristics": sorted(t["characteristics"].keys()),
            "facts": t.get("facts", []),
        })
    return out


def list_tests() -> list[dict[str, Any]]:
    out = []
    for tid, t in config.tests().items():
        out.append({
            "test_id": tid,
            "label": t["label"],
            "rationale": t.get("rationale", ""),
            "domains": t.get("domains", []),
            "requirements": t["requirements"],
        })
    return out


def list_sites() -> list[dict[str, Any]]:
    out = []
    for sid, s in config.pool().items():
        out.append({
            "site_id": sid,
            "label": s["label"],
            "lat": s["lat"],
            "lon": s["lon"],
            "known_analog": s.get("known_analog", False),
            "candidate_kind": "curated",
            "noted_for": s.get("noted_for", []),
        })
    return out


def target_facts(target_id: str) -> list[dict[str, Any]]:
    t = config.targets().get(target_id)
    if t is None:
        raise KeyError(f"unknown target_id {target_id!r}")
    return t.get("facts", [])


def characteristic_info(characteristic_id: str) -> dict[str, Any]:
    c = config.characteristics().get(characteristic_id)
    if c is None:
        raise KeyError(f"unknown characteristic {characteristic_id!r}")
    src = config.sources().get(c.get("source_id", ""), {})
    return {
        "id": c["id"],
        "kind": c["kind"],
        "unit": c.get("unit"),
        "tier": c.get("tier", "B"),
        "proxy_for": c.get("proxy_for"),
        "description": c.get("description", ""),
        "source": {"id": c.get("source_id"), "name": src.get("name"),
                   "licence": src.get("licence"), "verified": src.get("verified")},
    }


def domains() -> list[dict[str, Any]]:
    return config.domains()


def data_catalog() -> dict[str, Any]:
    """Data feature: the full catalog of characteristic layers + source registry.

    Surfaces the real provenance chain (which source feeds which characteristic, its
    licence, tier and domain) — nothing invented.
    """
    chars = config.characteristics()
    srcs = config.sources()
    doms = config.domains()
    dom_of: dict[str, str] = {}
    for d in doms:
        for cid in d.get("characteristics", []):
            dom_of[cid] = d["label"]

    layers = []
    for cid, c in chars.items():
        s = srcs.get(c.get("source_id", ""), {})
        layers.append({
            "id": cid,
            "kind": c["kind"],
            "unit": c.get("unit"),
            "tier": c.get("tier", "B"),
            "domain": dom_of.get(cid),
            "proxy_for": c.get("proxy_for"),
            "description": c.get("description", ""),
            "scale": c.get("scale"),
            "source": {
                "id": c.get("source_id"),
                "name": s.get("name"),
                "licence": s.get("licence"),
                "resolution": s.get("resolution"),
                "provided_by": s.get("provided_by"),
                "verified": s.get("verified"),
            },
        })

    # Source ledger: group each registry source with the characteristics it feeds.
    char_labels = {cid: cid.replace("_", " ") for cid in chars}
    ledger = []
    for sid, s in srcs.items():
        feeds = [char_labels[c] for c in s.get("used_for", []) if c in char_labels]
        ledger.append({
            "id": sid,
            "group": s.get("provided_by", s.get("licence", "open data")),
            "name": s.get("name", sid),
            "description": f"{s.get('resolution', '')} · {s.get('licence', '')}".strip(" ·"),
            "licence": s.get("licence"),
            "feeds": feeds,
            "verified": s.get("verified"),
        })

    from analog_compass.settings import get_settings
    st = get_settings()
    return {"data_mode": st.data_mode, "data_version": st.data_version,
            "layers": layers, "sources": ledger}


def review_contribution(payload: dict[str, Any]) -> dict[str, Any]:
    """Data-growth intake: validate a proposed dataset and return a review ticket.

    Stateless and honest — it never claims to store or ingest; it records the checks a
    human reviewer would run (traceable source, units, coverage) before indexing.
    """
    import hashlib

    name = (payload.get("name") or "").strip()
    link = (payload.get("source_link") or "").strip()
    measures = (payload.get("measures") or "").strip()
    checks = [
        {"name": "name_present", "ok": bool(name), "note": "A dataset name is required."},
        {"name": "source_link_valid",
         "ok": link.startswith("http://") or link.startswith("https://"),
         "note": "A stable http(s) source link is required for provenance."},
        {"name": "measures_described", "ok": len(measures) >= 10,
         "note": "Describe the measurement and its coverage."},
    ]
    ok = all(c["ok"] for c in checks)
    ticket = "DS-" + hashlib.blake2b(
        f"{name}|{link}".encode(), digest_size=4).hexdigest().upper()
    return {
        "ticket_id": ticket,
        "status": "received" if ok else "rejected",
        "message": (
            "Queued for human review of source, units, coverage and licence before indexing."
            if ok else "Some required fields are missing or invalid; see checks."
        ),
        "checks": checks,
    }
