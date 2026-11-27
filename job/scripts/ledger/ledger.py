#!/usr/bin/env python3
"""Append-only JSONL application ledger with alias-aware duplicate checks and Markdown rendering."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_STATUSES = (
    "reserved",
    "submission_attempted",
    "submitted_reported",
    "submitted",
    "verified",
    "blocked",
    "outcome_unknown",
    "skipped",
)

BLOCKING_STATUSES = frozenset({"submitted", "submitted_reported", "verified"})

STATUS_ORDER = (
    "verified",
    "submitted_reported",
    "submitted",
    "submission_attempted",
    "reserved",
    "blocked",
    "outcome_unknown",
    "skipped",
)


def normalize_name(text: str) -> str:
    """Normalize an employer or role string for reliable matching."""
    cleaned = text.lower().replace("&", " and ")
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_req(req: str | None) -> str:
    """Normalize a requisition ID for case-insensitive matching."""
    if not req:
        return ""
    return re.sub(r"\s+", "", req.strip()).upper()


def load_alias_map(rules_path: Path | None) -> dict[str, str]:
    """Build normalized alias -> canonical normalized name map from rules.json."""
    if not rules_path or not rules_path.is_file():
        return {}
    data = json.loads(rules_path.read_text(encoding="utf-8"))
    alias_groups = data.get("employer_aliases", [])
    alias_map: dict[str, str] = {}
    for group in alias_groups:
        if not isinstance(group, list):
            continue
        normalized_items = [normalize_name(str(item)) for item in group if str(item).strip()]
        normalized_items = [item for item in normalized_items if item]
        if not normalized_items:
            continue
        canonical = normalized_items[0]
        for item in normalized_items:
            alias_map[item] = canonical
    return alias_map


def canonical_employer(name: str, alias_map: dict[str, str]) -> str:
    norm = normalize_name(name)
    return alias_map.get(norm, norm)


def resolve_paths(workspace: Path, rules: Path | None = None) -> tuple[Path, Path | None]:
    ledger_path = workspace / "applications.jsonl"
    rules_path = rules if rules is not None else (workspace / "rules.json")
    return ledger_path, rules_path if rules_path.is_file() else None


def read_records(ledger_path: Path) -> list[dict[str, Any]]:
    if not ledger_path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line_no, raw in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            records.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_no} of {ledger_path}: {exc}") from exc
    return records


def collapse_latest(records: list[dict[str, Any]], alias_map: dict[str, str]) -> list[dict[str, Any]]:
    """Collapse append-only events into the latest state per application entry."""
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str]] = []

    for rec in records:
        emp_key = canonical_employer(str(rec.get("employer", "")), alias_map)
        req_key = normalize_req(rec.get("req"))
        role_key = normalize_name(str(rec.get("role", "")))
        key = (emp_key, req_key, "" if req_key else role_key)

        if key not in grouped:
            grouped[key] = dict(rec)
            order.append(key)
        else:
            merged = dict(grouped[key])
            for field, value in rec.items():
                if value not in (None, ""):
                    merged[field] = value
            grouped[key] = merged

    return [grouped[k] for k in order]


def check_duplicates(
    employer: str,
    workspace: Path,
    req: str | None = None,
    rules: Path | None = None,
) -> dict[str, Any]:
    ledger_path, rules_path = resolve_paths(workspace, rules)
    alias_map = load_alias_map(rules_path)
    records = read_records(ledger_path)
    latest = collapse_latest(records, alias_map)

    target_emp = canonical_employer(employer, alias_map)
    target_req = normalize_req(req)

    matches: list[dict[str, Any]] = []
    blocking_matches: list[dict[str, Any]] = []

    for entry in latest:
        entry_emp = canonical_employer(str(entry.get("employer", "")), alias_map)
        entry_req = normalize_req(entry.get("req"))
        emp_match = bool(target_emp and entry_emp == target_emp)
        req_match = bool(target_req and entry_req and entry_req == target_req)
        if emp_match or req_match:
            match_info = dict(entry)
            match_info["matched_by"] = [
                reason
                for reason, flag in (("employer", emp_match), ("req", req_match))
                if flag
            ]
            matches.append(match_info)
            if str(entry.get("status", "")).lower() in BLOCKING_STATUSES:
                blocking_matches.append(match_info)

    return {
        "employer": employer,
        "canonical_employer": target_emp,
        "req": target_req,
        "duplicate": bool(blocking_matches),
        "blocking_matches": blocking_matches,
        "all_matches": matches,
    }


def record_entry(
    workspace: Path,
    employer: str,
    role: str,
    status: str,
    req: str = "",
    location: str = "",
    url: str = "",
    receipt: str = "",
    notes: str = "",
    sent_by: str = "",
    done_by: str = "",
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Expected one of: {', '.join(VALID_STATUSES)}")
    workspace.mkdir(parents=True, exist_ok=True)
    ledger_path = workspace / "applications.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "employer": employer.strip(),
        "role": role.strip(),
        "status": status,
        "req": req.strip(),
        "location": location.strip(),
        "url": url.strip(),
        "receipt": receipt.strip(),
        "notes": notes.strip(),
        "sent_by": sent_by.strip(),
        "done_by": done_by.strip(),
    }
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def agents(entry: dict[str, Any]) -> str:
    """'<model> (high, standard), sent by <model>', or whichever part is known."""
    done, sent = str(entry.get("done_by") or "").strip(), str(entry.get("sent_by") or "").strip()
    if done and sent and done != sent:
        return f"{done}, sent by {sent}"
    return done or sent


def _md_cell(value: Any) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    return text.replace("|", "\\|")


def render_markdown(workspace: Path, rules: Path | None = None, output: Path | None = None) -> Path:
    ledger_path, rules_path = resolve_paths(workspace, rules)
    alias_map = load_alias_map(rules_path)
    records = read_records(ledger_path)
    latest = collapse_latest(records, alias_map)

    by_status: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in latest:
        status = str(entry.get("status", "unknown")).lower()
        by_status[status].append(entry)

    verified_count = len(by_status.get("verified", []))
    total_tracked = len(latest)

    lines: list[str] = [
        "# Application Log",
        "",
        f"- **Verified Applications**: {verified_count}",
        f"- **Total Tracked Roles**: {total_tracked}",
    ]

    summary_parts = [
        f"`{status}`: {len(by_status[status])}"
        for status in STATUS_ORDER
        if by_status.get(status)
    ]
    if summary_parts:
        lines.append("- **By Status**: " + " | ".join(summary_parts))
    lines.append("")

    ordered_statuses = list(STATUS_ORDER) + [
        s for s in sorted(by_status) if s not in STATUS_ORDER
    ]
    rendered_any = False
    for status in ordered_statuses:
        entries = by_status.get(status, [])
        if not entries:
            continue
        rendered_any = True
        title = status.replace("_", " ").title()
        lines.extend(
            [
                f"## {title} ({len(entries)})",
                "",
                "| Employer | Role | Req ID | Location | Receipt | Updated (UTC) | Done by | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in entries:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(item.get("employer")),
                        _md_cell(item.get("role")),
                        _md_cell(item.get("req")),
                        _md_cell(item.get("location")),
                        _md_cell(item.get("receipt")),
                        _md_cell(item.get("timestamp")),
                        _md_cell(agents(item)),
                        _md_cell(item.get("notes")),
                    ]
                )
                + " |"
            )
        lines.append("")

    if not rendered_any:
        lines.append("_No applications recorded yet._")
        lines.append("")

    out_path = output if output is not None else (workspace / "log.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the Habashi-kit/job application ledger.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Check whether an employer or requisition is already submitted/verified.")
    p_check.add_argument("employer", help="Employer name to check.")
    p_check.add_argument("--req", default="", help="Optional requisition ID.")
    p_check.add_argument("--workspace", type=Path, default=Path("workspace"), help="Workspace directory.")
    p_check.add_argument("--rules", type=Path, default=None, help="Optional path to rules.json.")
    p_check.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output.")

    p_record = sub.add_parser("record", help="Append an application status event to applications.jsonl.")
    p_record.add_argument("--employer", required=True, help="Employer name.")
    p_record.add_argument("--role", required=True, help="Role title.")
    p_record.add_argument("--status", required=True, choices=VALID_STATUSES, help="Ledger status.")
    p_record.add_argument("--req", default="", help="Requisition ID.")
    p_record.add_argument("--location", default="", help="Job location.")
    p_record.add_argument("--url", default="", help="Job posting or portal URL.")
    p_record.add_argument("--receipt", default="", help="Confirmation code or receipt summary.")
    p_record.add_argument("--notes", default="", help="Additional context or blocker details.")
    p_record.add_argument("--sent-by", default="", help="Model that handed the job over, if any.")
    p_record.add_argument("--done-by", default="", help="Model that did the job, with effort and speed, e.g. '<model> (high, standard)'.")
    p_record.add_argument("--workspace", type=Path, default=Path("workspace"), help="Workspace directory.")

    p_render = sub.add_parser("render", help="Render applications.jsonl into a clean Markdown log.md.")
    p_render.add_argument("--workspace", type=Path, default=Path("workspace"), help="Workspace directory.")
    p_render.add_argument("--rules", type=Path, default=None, help="Optional path to rules.json.")
    p_render.add_argument("--output", type=Path, default=None, help="Optional output path (defaults to <workspace>/log.md).")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "check":
        result = check_duplicates(
            employer=args.employer,
            workspace=args.workspace,
            req=args.req or None,
            rules=args.rules,
        )
        if args.as_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result["duplicate"]:
                first = result["blocking_matches"][0]
                print(
                    f"DUPLICATE: {first.get('employer')} — {first.get('role')} "
                    f"(status={first.get('status')}, req={first.get('req') or 'n/a'})"
                )
            else:
                print(f"OK: No submitted/verified duplicate for '{args.employer}'.")
        return 1 if result["duplicate"] else 0

    if args.command == "record":
        entry = record_entry(
            workspace=args.workspace,
            employer=args.employer,
            role=args.role,
            status=args.status,
            req=args.req,
            location=args.location,
            url=args.url,
            receipt=args.receipt,
            notes=args.notes,
            sent_by=args.sent_by,
            done_by=args.done_by,
        )
        print(f"Recorded {entry['status']} for {entry['employer']} — {entry['role']}")
        return 0

    if args.command == "render":
        out_path = render_markdown(workspace=args.workspace, rules=args.rules, output=args.output)
        print(f"Rendered {out_path}")
        return 0

    return 2


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
