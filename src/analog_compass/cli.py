"""Minimal CLI: quick compare / discover / suitability from the terminal."""

from __future__ import annotations

import argparse
import json

from analog_compass import service
from analog_compass.api import serialize


def main() -> int:
    parser = argparse.ArgumentParser(prog="analog-compass")
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compare", help="rank curated sites for a target x test")
    c.add_argument("target_id")
    c.add_argument("test_id")

    d = sub.add_parser("discover", help="discover new candidate windows")
    d.add_argument("target_id")
    d.add_argument("test_id")
    d.add_argument("-k", type=int, default=8)

    s = sub.add_parser("suitability", help="which tests a site supports")
    s.add_argument("site_id")
    s.add_argument("--target", default=None)

    args = parser.parse_args()
    if args.cmd == "compare":
        out = serialize.result_to_dict(service.run_compare(args.target_id, args.test_id))
    elif args.cmd == "discover":
        out = serialize.result_to_dict(
            service.run_discover(args.target_id, args.test_id, k=args.k)
        )
    else:
        out = service.run_suitability(args.site_id, args.target)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
