#!/usr/bin/env python3
"""Reference inspector: independently prove a bundle is readable and summarise it.

Defines the report shape the real-data inspector (ticket T-044) must reproduce.
"""

from __future__ import annotations

import sys
from collections import Counter

import _bootstrap  # noqa: F401
from analog_compass.pipeline.bundle import load_bundle


def main(argv: list[str]) -> int:
    bundle_dir = argv[1] if len(argv) > 1 else None
    b = load_bundle(bundle_dir)
    print(f"bundle: data_mode={b.data_mode} data_version={b.data_version} "
          f"windows={len(b.windows)}")
    curated = sum(1 for w in b.windows if w.curated_site_id)
    print(f"  curated windows: {curated}; discovery windows: {len(b.windows) - curated}")

    layer_counts: Counter[str] = Counter()
    missing_counts: Counter[str] = Counter()
    for w in b.windows:
        for cid, spec in w.chars.items():
            layer_counts[cid] += 1
            if spec.get("missing"):
                missing_counts[cid] += 1
    print("  layers (present / missing):")
    for cid in sorted(layer_counts):
        print(f"    {cid:<28} {layer_counts[cid]:>4} / {missing_counts.get(cid, 0)}")
    print("inspector: OK (every window readable).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
