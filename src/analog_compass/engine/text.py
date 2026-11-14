"""User-visible text templates (docs/03_ENGINE_SPEC.md §10).

The engine and agent emit prose ONLY by filling these templates. Never free-write
scientific claims, and never use a banned word.
"""

from __future__ import annotations

NOTE_TEMPLATES: dict[str, str] = {
    "proxy_must": "Passes only on proxy evidence for {characteristic}; treat as provisional.",
    "site_missing_must": "Excluded: no data for required {characteristic}.",
    "target_missing_must": "Blocked: the target has no value for required {characteristic}.",
    "straddles_gate": "Borderline: {characteristic} meets the gate in {p_gate_pct}% of draws.",
    "coverage_reduced": "Scored on {coverage_pct}% of the intended characteristics; {n} dropped for missing data.",
    "outside_coverage": "{characteristic} is outside the layer's coverage here; reported as missing.",
    "excluded_gate": "Excluded: the required characteristics fail in almost every draw.",
    "scored_dropped": "{characteristic} dropped (missing data); it did not count for or against this site.",
}

# Words that overstate evidence. Never emitted by the engine or the agent.
BANNED_WORDS: frozenset[str] = frozenset(
    {
        "perfect",
        "identical to mars",
        "identical to the moon",
        "exactly like mars",
        "exactly like the moon",
        "guaranteed",
        "flawless",
        "ideal match",
        "100% match",
    }
)


def note(note_id: str, **slots: object) -> str:
    """Render a template by id. Unknown ids raise (no silent free-text)."""
    template = NOTE_TEMPLATES[note_id]
    return template.format(**slots)


def contains_banned(text: str) -> list[str]:
    """Return any banned phrases found in `text` (case-insensitive)."""
    low = text.lower()
    return [w for w in BANNED_WORDS if w in low]
