#!/usr/bin/env python3
"""Remove expired report directories from a GitHub Pages source tree."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("docs"))
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: Report root does not exist: {root}", file=sys.stderr)
        return 2

    removed = 0
    for metadata_path in sorted(root.rglob("report.json")):
        report_directory = metadata_path.parent.resolve()
        if report_directory == root or not is_within(report_directory, root):
            print(f"ERROR: Refusing unsafe report path: {report_directory}", file=sys.stderr)
            return 2
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            expiry = date.fromisoformat(str(metadata["expires_at"]))
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
            print(f"ERROR: Invalid metadata in {metadata_path}: {error}", file=sys.stderr)
            return 2
        if expiry > args.today:
            continue
        if args.dry_run:
            print(f"Would remove expired report: {report_directory}")
        else:
            shutil.rmtree(report_directory)
            print(f"Removed expired report: {report_directory}")
        removed += 1

    print(f"Expired report directories matched: {removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
