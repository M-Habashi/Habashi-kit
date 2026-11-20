#!/usr/bin/env python3
"""Initialize a private Habashi-kit/job user workspace from clean templates."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
REQUIRED_SUBDIRS = ("docs", "evidence", "output/pdf")


def init_workspace(target_dir: Path, force: bool = False) -> dict[str, list[str]]:
    """Copy starter templates and create workspace folders without clobbering existing files."""
    if not TEMPLATES_DIR.is_dir():
        raise FileNotFoundError(f"Templates directory not found: {TEMPLATES_DIR}")

    target_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[str] = []

    for rel_dir in REQUIRED_SUBDIRS:
        dir_path = target_dir / rel_dir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(f"{rel_dir}/")

    for src in sorted(TEMPLATES_DIR.iterdir()):
        if not src.is_file():
            continue
        dst = target_dir / src.name
        if dst.exists() and not force:
            skipped.append(src.name)
            continue
        shutil.copyfile(src, dst)
        created.append(src.name)

    ledger_path = target_dir / "applications.jsonl"
    if ledger_path.exists() and not force:
        skipped.append("applications.jsonl")
    else:
        ledger_path.write_text("", encoding="utf-8")
        created.append("applications.jsonl")

    return {"created": created, "skipped": skipped}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize a private Habashi-kit/job workspace from clean templates."
    )
    parser.add_argument("target_dir", type=Path, help="Target workspace directory to create/populate.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing template files and reset applications.jsonl.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = init_workspace(args.target_dir, force=args.force)
    print(f"Workspace initialized at: {args.target_dir.resolve()}")
    if result["created"]:
        print("Created / updated: " + ", ".join(result["created"]))
    if result["skipped"]:
        print("Preserved existing: " + ", ".join(result["skipped"]))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
