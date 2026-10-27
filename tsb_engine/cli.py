"""Command line: ``python -m tsb_engine lint animation.json [--json]``."""

from __future__ import annotations

import argparse
import json
import sys

from . import serialization
from .linter import format_report, lint


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tsb_engine")
    sub = parser.add_subparsers(dest="command", required=True)
    p_lint = sub.add_parser("lint", help="check an animation JSON against the craft rules")
    p_lint.add_argument("path")
    p_lint.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    anim = serialization.load(args.path)
    findings = lint(anim)
    if args.json:
        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        print(format_report(anim, findings))
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
