#!/usr/bin/env python3
"""Rule-driven cover-letter specification linter."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Matches 3+ item Oxford or non-Oxford comma lists inside prose (e.g. "A, B, and C")
# while ignoring date commas ("January 15, 2026") and simple "City, State" pairs.
THREE_ITEM_COMMA_LIST_RE = re.compile(
    r"\b[A-Za-z0-9][A-Za-z0-9/+.#&'-]*(?:\s+[A-Za-z0-9/+.#&'-]+){0,3},"
    r"\s+[A-Za-z0-9][A-Za-z0-9/+.#&'-]*(?:\s+[A-Za-z0-9/+.#&'-]+){0,3},"
    r"\s+(?:and|or)\s+[A-Za-z0-9][A-Za-z0-9/+.#&'-]*(?:\s+[A-Za-z0-9/+.#&'-]+){0,3}\b",
    re.IGNORECASE,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_rules() -> dict[str, Any]:
    return {
        "author_name": "",
        "file_prefix": "Cover_Letter",
        "confirmed_software": [],
        "unconfirmed_software": [],
        "forbidden_claims": [],
        "employer_order": [],
        "style": {
            "forbid_em_dash": True,
            "forbid_long_comma_lists": True,
            "max_pages": 1,
        },
        "employer_aliases": [],
    }


def load_rules(rules_path: Path | None) -> dict[str, Any]:
    merged = default_rules()
    if rules_path and rules_path.is_file():
        user_rules = load_json(rules_path)
        for key, value in user_rules.items():
            if key == "style" and isinstance(value, dict):
                merged["style"].update(value)
            else:
                merged[key] = value
    return merged


def _whole_term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term.strip())
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def lint_spec(spec: dict[str, Any], rules: dict[str, Any]) -> list[str]:
    """Return a list of lint error messages for a cover-letter spec."""
    errors: list[str] = []

    paragraphs = spec.get("paragraphs", [])
    if not isinstance(paragraphs, list) or not [p for p in paragraphs if str(p).strip()]:
        errors.append("Spec must contain at least one non-empty paragraph.")
        return errors

    body_text = "\n\n".join(str(p).strip() for p in paragraphs if str(p).strip())
    salutation = str(spec.get("salutation", "")).strip()
    closing = str(spec.get("closing", "")).strip()
    signature = str(spec.get("signature", "")).strip()
    header_name = str(spec.get("header", {}).get("name", "")).strip()

    full_prose = "\n".join(part for part in (salutation, body_text, closing) if part)

    # 1. Author name consistency
    author_name = str(rules.get("author_name", "")).strip()
    if author_name and author_name.lower() != "your name":
        if header_name and header_name != author_name:
            errors.append(f"Header name '{header_name}' does not match rules.author_name '{author_name}'.")
        if signature and signature != author_name:
            errors.append(f"Signature '{signature}' does not match rules.author_name '{author_name}'.")

    # 2. Unconfirmed software mentions
    for tool in rules.get("unconfirmed_software", []):
        tool_str = str(tool).strip()
        if not tool_str:
            continue
        if _whole_term_pattern(tool_str).search(body_text):
            errors.append(f"Unconfirmed software mentioned: '{tool_str}'.")

    # 3. Forbidden claims
    for claim in rules.get("forbidden_claims", []):
        if not isinstance(claim, dict):
            continue
        pattern = str(claim.get("pattern", "")).strip()
        label = str(claim.get("label", pattern)).strip()
        if not pattern:
            continue
        if re.search(pattern, full_prose, re.IGNORECASE):
            errors.append(f"Forbidden claim triggered ({label}).")

    # 4. Employer order enforcement (preserve CV employment order)
    employer_order = [str(emp).strip() for emp in rules.get("employer_order", []) if str(emp).strip()]
    positions: list[tuple[int, str]] = []
    for emp in employer_order:
        match = _whole_term_pattern(emp).search(body_text)
        if match:
            positions.append((match.start(), emp))
    if len(positions) >= 2:
        expected_seq = [emp for _, emp in sorted(positions, key=lambda item: employer_order.index(item[1]))]
        actual_seq = [emp for _, emp in sorted(positions, key=lambda item: item[0])]
        if actual_seq != expected_seq:
            errors.append(
                f"Employer order mismatch: found {actual_seq}, expected CV order {expected_seq}."
            )

    # 5. Style checks
    style = rules.get("style", {})
    if style.get("forbid_em_dash", True):
        if "\u2014" in full_prose or "--" in full_prose:
            errors.append("Em dash ('—' or '--') is forbidden by style rules.")

    if style.get("forbid_long_comma_lists", True):
        for idx, para in enumerate(paragraphs, start=1):
            match = THREE_ITEM_COMMA_LIST_RE.search(str(para))
            if match:
                errors.append(
                    f"Paragraph {idx} contains a 3+ item comma list ('{match.group(0)}'), forbidden by style rules."
                )

    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint a cover-letter JSON spec against rules.json.")
    parser.add_argument("spec", type=Path, help="Path to cover-letter JSON spec.")
    parser.add_argument("--rules", type=Path, default=None, help="Path to rules.json.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    spec = load_json(args.spec)
    rules = load_rules(args.rules)
    errors = lint_spec(spec, rules)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print(f"OK: {args.spec} passed cover-letter lint.")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
