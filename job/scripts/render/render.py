#!/usr/bin/env python3
"""Render Habashi-kit/job reports as themed HTML cards or plain text.

Subcommands:
  card <payload.json | ->   Render any report payload (checklist, kv, table, list, note blocks).
  preflight --workspace W   Inspect a workspace and render the Step 1 preflight checklist.
  ledger --workspace W      Render the application ledger (latest state per role).

Exit codes: 0 = rendered (preflight: all required items ready), 2 = preflight found missing
required items, 1 = usage or input error.
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

JOB_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = JOB_ROOT / "scripts" / "ledger" / "ledger.py"
NEO_DIR = JOB_ROOT / "scripts" / "neo"

# status -> (tone, text-mode label)
STATUS = {
    "ok": ("success", "OK"),
    "missing": ("danger", "MISSING"),
    "blocked": ("danger", "BLOCKED"),
    "warn": ("warning", "CHECK"),
    "pending": ("info", "PENDING"),
    "optional": ("muted", "OPTIONAL"),
    "skipped": ("muted", "SKIPPED"),
    # ledger statuses
    "verified": ("success", "VERIFIED"),
    "submitted": ("success", "SUBMITTED"),
    "submitted_reported": ("success", "REPORTED"),
    "submission_attempted": ("info", "ATTEMPTED"),
    "reserved": ("info", "RESERVED"),
    "outcome_unknown": ("warning", "UNKNOWN"),
}
TONES = {
    "success": "var(--success, #16a34a)",
    "danger": "var(--destructive, #dc2626)",
    "warning": "var(--warning, #d97706)",
    "info": "var(--info, #2563eb)",
    "muted": "var(--muted-foreground, #6b7280)",
}
ICONS = {
    "success": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "danger": '<path d="M7 7l10 10M17 7L7 17"/>',
    "warning": '<path d="M12 6v7"/><path d="M12 17.5h.01"/>',
    "info": '<path d="M12 7v5l3 2"/>',
    "muted": '<path d="M7 12h10"/>',
}
BLOCK_TYPES = {"checklist", "kv", "table", "list", "note"}

CSS = """
.hk{font-family:var(--font-sans,system-ui,-apple-system,"Segoe UI",sans-serif);color:var(--foreground,inherit);display:flex;flex-direction:column;gap:14px;font-size:14px;line-height:1.45}
.hk *{box-sizing:border-box}
.hd{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px}
.hd h1{font-size:16px;font-weight:600;margin:0}
.sub{color:var(--muted-foreground,#6b7280);font-size:13px;margin-top:-8px}
.pill{display:inline-flex;align-items:center;font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px;white-space:nowrap;color:var(--t);background:color-mix(in srgb,var(--t) 14%,transparent)}
.sec h2{font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--muted-foreground,#6b7280);margin:0 0 6px}
.box{background:var(--card,transparent);border:1px solid var(--border,rgba(127,127,127,.28));border-radius:var(--radius,10px);padding:6px 16px}
.row{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-top:1px solid var(--border,rgba(127,127,127,.2))}
.row:first-child{border-top:0}
.ic{flex:none;width:20px;height:20px;border-radius:50%;display:grid;place-items:center;color:var(--t);background:color-mix(in srgb,var(--t) 15%,transparent);margin-top:1px}
.ic svg{width:13px;height:13px}
.tx{flex:1;min-width:0}
.lb{font-weight:500;overflow-wrap:anywhere}
.dt{color:var(--muted-foreground,#6b7280);font-size:13px;overflow-wrap:anywhere}
.kv{display:grid;grid-template-columns:minmax(90px,max-content) 1fr;gap:6px 16px;padding:10px 0;margin:0}
.kv dt{color:var(--muted-foreground,#6b7280)}
.kv dd{margin:0;overflow-wrap:anywhere}
.tw{overflow-x:auto;padding:4px 0}
table{border-collapse:collapse;width:100%;font-size:13px}
th{text-align:left;font-weight:600;color:var(--muted-foreground,#6b7280);padding:6px 10px 6px 0;white-space:nowrap}
td{padding:7px 10px 7px 0;border-top:1px solid var(--border,rgba(127,127,127,.2));vertical-align:top}
ul.ls{margin:0;padding:10px 0 10px 18px;display:flex;flex-direction:column;gap:4px}
.note{border-left:3px solid var(--t);background:color-mix(in srgb,var(--t) 10%,transparent);border-radius:var(--radius,10px);padding:10px 14px}
"""


# --------------------------------------------------------------------------- payload helpers

def tone_of(status: str) -> str:
    return STATUS.get(str(status).lower(), ("muted", ""))[0]


def label_of(status: str) -> str:
    key = str(status).lower()
    return STATUS.get(key, ("muted", key.upper() or "-"))[1]


def validate(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or not str(payload.get("title", "")).strip():
        raise ValueError("Payload must be a JSON object with a non-empty 'title'.")
    blocks = payload.get("blocks", [])
    if not isinstance(blocks, list):
        raise ValueError("'blocks' must be a list.")
    for i, block in enumerate(blocks):
        if not isinstance(block, dict) or block.get("type") not in BLOCK_TYPES:
            raise ValueError(f"Block {i} needs a 'type' in {sorted(BLOCK_TYPES)}.")
    return payload


def summary_badge(payload: dict[str, Any]) -> tuple[str, str] | None:
    """Return (text, tone) for the header pill; explicit 'badge'/'tone' win."""
    if payload.get("badge"):
        return str(payload["badge"]), str(payload.get("tone", "info"))
    statuses = [
        str(item.get("status", "")).lower()
        for block in payload.get("blocks", [])
        if block.get("type") == "checklist"
        for item in block.get("items", [])
    ]
    if not statuses:
        return None
    bad = sum(s in ("missing", "blocked") for s in statuses)
    warn = sum(s == "warn" for s in statuses)
    if bad:
        return f"{bad} missing" if all(s != "blocked" for s in statuses) else f"{bad} blocking", "danger"
    if warn:
        return f"{warn} to check", "warning"
    return "Ready", "success"


# --------------------------------------------------------------------------- HTML

def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def pill(text: str, tone: str) -> str:
    return f'<span class="pill" style="--t:{TONES.get(tone, TONES["muted"])}">{esc(text)}</span>'


def render_block_html(block: dict[str, Any]) -> str:
    kind = block["type"]
    heading = f'<h2>{esc(block["heading"])}</h2>' if block.get("heading") else ""
    if kind == "note":
        tone = block.get("tone", "info")
        return f'<div class="sec">{heading}<div class="note" style="--t:{TONES.get(tone, TONES["info"])}">{esc(block.get("text", ""))}</div></div>'
    if kind == "checklist":
        rows = []
        for item in block.get("items", []):
            tone = tone_of(item.get("status", ""))
            color = TONES[tone]
            detail = f'<div class="dt">{esc(item["detail"])}</div>' if item.get("detail") else ""
            rows.append(
                f'<div class="row"><span class="ic" style="--t:{color}"><svg viewBox="0 0 24 24" fill="none" '
                f'stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{ICONS[tone]}</svg></span>'
                f'<div class="tx"><div class="lb">{esc(item.get("label", ""))}</div>{detail}</div>'
                f'{pill(label_of(item.get("status", "")).title(), tone)}</div>'
            )
        body = "".join(rows) or '<div class="row"><div class="dt">Nothing to show.</div></div>'
    elif kind == "kv":
        pairs = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in block.get("rows", []))
        body = f'<dl class="kv">{pairs}</dl>'
    elif kind == "table":
        cols = [str(c) for c in block.get("columns", [])]
        status_idx = {i for i, c in enumerate(cols) if c.strip().lower() == "status"}
        head = "".join(f"<th>{esc(c)}</th>" for c in cols)
        rows = []
        for row in block.get("rows", []):
            cells = []
            for i, cell in enumerate(row):
                if i in status_idx and str(cell).lower() in STATUS:
                    cells.append(f"<td>{pill(label_of(cell).title(), tone_of(cell))}</td>")
                else:
                    cells.append(f"<td>{esc(cell)}</td>")
            rows.append("<tr>" + "".join(cells) + "</tr>")
        if not rows:
            rows.append(f'<tr><td colspan="{max(len(cols), 1)}" class="dt">Nothing recorded yet.</td></tr>')
        body = f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    else:  # list
        items = "".join(f"<li>{esc(x)}</li>" for x in block.get("items", []))
        body = f'<ul class="ls">{items}</ul>'
    return f'<div class="sec">{heading}<div class="box">{body}</div></div>'


def render_html(payload: dict[str, Any]) -> str:
    payload = validate(payload)
    badge = summary_badge(payload)
    header = f'<div class="hd"><h1>{esc(payload["title"])}</h1>{pill(*badge) if badge else ""}</div>'
    sub = f'<div class="sub">{esc(payload["subtitle"])}</div>' if payload.get("subtitle") else ""
    blocks = "".join(render_block_html(b) for b in payload.get("blocks", []))
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(payload['title'])}</title><style>{CSS}</style></head>"
        f'<body><div class="hk">{header}{sub}{blocks}</div></body></html>'
    )


# --------------------------------------------------------------------------- plain text

def render_text(payload: dict[str, Any]) -> str:
    payload = validate(payload)
    badge = summary_badge(payload)
    lines = [payload["title"] + (f"  [{badge[0]}]" if badge else "")]
    if payload.get("subtitle"):
        lines.append(str(payload["subtitle"]))
    for block in payload.get("blocks", []):
        lines.append("")
        if block.get("heading"):
            lines.append(str(block["heading"]))
        kind = block["type"]
        if kind == "checklist":
            width = max((len(label_of(i.get("status", ""))) for i in block.get("items", [])), default=2)
            for item in block.get("items", []):
                line = f"  {label_of(item.get('status', '')).ljust(width)}  {item.get('label', '')}"
                if item.get("detail"):
                    line += f" - {item['detail']}"
                lines.append(line)
        elif kind == "kv":
            rows = block.get("rows", [])
            width = max((len(str(k)) for k, _ in rows), default=0)
            lines.extend(f"  {str(k).ljust(width)}  {v}" for k, v in rows)
        elif kind == "table":
            cols = [str(c) for c in block.get("columns", [])]
            rows = [[str(c) for c in r] for r in block.get("rows", [])]
            if not rows:
                lines.append("  Nothing recorded yet.")
                continue
            widths = [max(len(cols[i]), *(len(r[i]) for r in rows if i < len(r))) for i in range(len(cols))]
            lines.append("  " + "  ".join(c.ljust(w) for c, w in zip(cols, widths)).rstrip())
            for r in rows:
                lines.append("  " + "  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip())
        elif kind == "list":
            lines.extend(f"  - {x}" for x in block.get("items", []))
        else:  # note
            lines.append(f"  NOTE: {block.get('text', '')}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- preflight

PLACEHOLDER = re.compile(r"<[^<>\n]{2,}>")
PROFILE_REQUIRED = ("Full Name", "Email", "Phone", "Location", "LinkedIn")
ANSWERS_REQUIRED = (
    "Authorized to Work in Target Country Today?",
    "Will You Now or in the Future Require Visa Sponsorship?",
    "Earliest Available Start Date",
    "Salary Expectation Rule",
    "Target Roles",
    "Target Locations / Work Mode",
)
RULES_DEFAULTS = {"author_name": "Your Name", "file_prefix": "Your_Name_Cover_Letter"}


def field_value(text: str, label: str) -> str | None:
    match = re.search(rf"^\s*-\s*\*\*{re.escape(label)}\*\*\s*:\s*(.*)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def unfilled(text: str, labels: tuple[str, ...]) -> list[str]:
    out = []
    for label in labels:
        value = field_value(text, label)
        if value is None or not value.strip("` ") or PLACEHOLDER.search(value):
            out.append(label)
    return out


def check_md(path: Path, labels: tuple[str, ...], name: str, purpose: str) -> dict[str, str]:
    if not path.is_file():
        return {"label": name, "status": "missing", "detail": "File not found - run init_workspace.py"}
    text = path.read_text(encoding="utf-8")
    missing = unfilled(text, labels)
    if missing:
        return {"label": name, "status": "missing", "detail": "Unfilled: " + ", ".join(missing)}
    left = len(PLACEHOLDER.findall(text))
    if left:
        return {"label": name, "status": "warn", "detail": f"{purpose} filled; {left} other placeholder(s) left"}
    return {"label": name, "status": "ok", "detail": purpose + " filled"}


def check_rules(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {"label": "rules.json", "status": "missing", "detail": "File not found - run init_workspace.py"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"label": "rules.json", "status": "missing", "detail": f"Invalid JSON: {exc.msg} (line {exc.lineno})"}
    stale = [k for k, default in RULES_DEFAULTS.items() if str(data.get(k, default)).strip() in ("", default)]
    if "Current or Primary Employer" in data.get("employer_order", []):
        stale.append("employer_order")
    if stale:
        return {"label": "rules.json", "status": "missing", "detail": "Still template values: " + ", ".join(stale)}
    return {"label": "rules.json", "status": "ok", "detail": "Author, file prefix and employer order set"}


def module_ok(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def parse_tool(spec: str) -> dict[str, str]:
    """NAME=STATUS[:DETAIL] -> checklist item."""
    name, sep, rest = spec.partition("=")
    status, _, detail = rest.partition(":")
    status = status.strip().lower()
    if not sep or not name.strip() or status not in STATUS:
        raise ValueError(f"--tool expects NAME=STATUS[:DETAIL] with STATUS in {sorted(STATUS)}; got {spec!r}")
    return {"label": name.strip(), "status": status, "detail": detail.strip()}


def preflight_payload(workspace: Path, tools: list[str] | None = None) -> dict[str, Any]:
    docs = workspace / "docs"
    pdfs = sorted(p.name for p in docs.glob("*.pdf")) if docs.is_dir() else []
    profile_text = (workspace / "profile.md").read_text(encoding="utf-8") if (workspace / "profile.md").is_file() else ""
    portfolio = field_value(profile_text, "Portfolio / GitHub / Website") or ""

    required = [
        {"label": "Resume / CV PDF", "status": "ok" if pdfs else "missing",
         "detail": ", ".join(f"docs/{p}" for p in pdfs) if pdfs else "Add your resume PDF to docs/"},
        check_md(workspace / "profile.md", PROFILE_REQUIRED, "profile.md", "Contact header"),
        check_md(workspace / "answers.md", ANSWERS_REQUIRED, "answers.md", "Authorization, availability, salary and targets"),
        check_rules(workspace / "rules.json"),
    ]
    optional = [
        {"label": "Certifications / licenses", "status": "optional", "detail": "Ask if applicable to the field"},
        {"label": "Academic transcripts", "status": "optional", "detail": "Ask if applicable"},
        {"label": "Cover-letter template or references", "status": "optional", "detail": "Ask if applicable"},
        {"label": "Portfolio / GitHub / work samples",
         "status": "ok" if portfolio and not PLACEHOLDER.search(portfolio) else "optional",
         "detail": portfolio.strip("`") if portfolio and not PLACEHOLDER.search(portfolio) else "Ask if applicable"},
    ]

    neo_ready = (NEO_DIR / "node_modules" / "jsdom").is_dir()
    tool_items = [parse_tool(t) for t in (tools or [])]
    tool_items += [
        {"label": "Python reportlab + pymupdf", "status": "ok" if module_ok("reportlab") and module_ok("fitz") else "warn",
         "detail": "Cover-letter PDF + QA PNG" if module_ok("reportlab") and module_ok("fitz")
         else "pip install reportlab pymupdf (needed for cover letters)"},
        {"label": "Node.js + neo dependencies", "status": "ok" if shutil.which("node") and neo_ready else "warn",
         "detail": "emit.mjs / jobs.mjs ready" if shutil.which("node") and neo_ready
         else ("pnpm --dir job/scripts/neo install" if shutil.which("node") else "Install Node.js")},
    ]

    blocks: list[dict[str, Any]] = [
        {"type": "checklist", "heading": "Required", "items": required},
        {"type": "checklist", "heading": "Optional - ask if applicable", "items": optional},
        {"type": "checklist", "heading": "Tools & browser", "items": tool_items},
    ]
    if any(i["status"] == "missing" for i in required):
        blocks.append({"type": "note", "tone": "danger",
                       "text": "Applications are paused until the required items above are provided."})
    return {"title": "Preflight check", "subtitle": f"Workspace: {workspace.as_posix()}", "blocks": blocks}


# --------------------------------------------------------------------------- ledger

def load_ledger_module():
    spec = importlib.util.spec_from_file_location("hk_ledger", LEDGER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("hk_ledger", module)
    spec.loader.exec_module(module)
    return module


def ledger_payload(workspace: Path, rules: Path | None = None) -> dict[str, Any]:
    lg = load_ledger_module()
    ledger_path, rules_path = lg.resolve_paths(workspace, rules)
    latest = lg.collapse_latest(lg.read_records(ledger_path), lg.load_alias_map(rules_path))
    rank = {s: i for i, s in enumerate(lg.STATUS_ORDER)}
    latest.sort(key=lambda e: (rank.get(str(e.get("status", "")).lower(), 99), str(e.get("timestamp", ""))))
    counts: dict[str, int] = {}
    for entry in latest:
        status = str(entry.get("status", "unknown")).lower()
        counts[status] = counts.get(status, 0) + 1
    kv = [["Tracked roles", str(len(latest))]] + [
        [s.replace("_", " ").capitalize(), str(counts[s])] for s in lg.STATUS_ORDER if counts.get(s)
    ]
    rows = [
        [e.get("employer", ""), e.get("role", ""), e.get("req", "") or "-", str(e.get("status", "")).lower(),
         str(e.get("timestamp", ""))[:10], e.get("receipt") or e.get("notes") or ""]
        for e in latest
    ]
    verified = counts.get("verified", 0)
    return {
        "title": "Application log",
        "badge": f"{verified} verified",
        "tone": "success" if verified else "muted",
        "blocks": [
            {"type": "kv", "heading": "Summary", "rows": kv},
            {"type": "table", "heading": "Applications",
             "columns": ["Employer", "Role", "Req", "Status", "Updated", "Receipt / notes"], "rows": rows},
        ],
    }


# --------------------------------------------------------------------------- CLI

def emit(payload: dict[str, Any], fmt: str, out: Path | None) -> None:
    content = render_html(payload) if fmt == "html" else render_text(payload)
    if out is None:
        sys.stdout.write(content)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(out.resolve())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Habashi-kit/job reports as HTML cards or plain text.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--format", choices=("html", "text"), default="html", help="Output format (default html).")
    common.add_argument("--out", type=Path, default=None, help="Write to this file and print its absolute path.")
    common.add_argument("--json", action="store_true", dest="as_json", help="Print the payload JSON instead of rendering.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_card = sub.add_parser("card", parents=[common], help="Render a payload JSON file ('-' for stdin).")
    p_card.add_argument("payload", help="Path to payload JSON, or '-' for stdin.")

    p_pre = sub.add_parser("preflight", parents=[common], help="Inspect a workspace and render the preflight checklist.")
    p_pre.add_argument("--workspace", type=Path, default=Path("workspace"))
    p_pre.add_argument("--tool", action="append", default=[], metavar="NAME=STATUS[:DETAIL]",
                       help="Agent-detected tool readiness, e.g. 'BrowserOS Neo=ok:Connected'. Repeatable.")

    p_led = sub.add_parser("ledger", parents=[common], help="Render the application ledger.")
    p_led.add_argument("--workspace", type=Path, default=Path("workspace"))
    p_led.add_argument("--rules", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "card":
            raw = sys.stdin.read() if args.payload == "-" else Path(args.payload).read_text(encoding="utf-8")
            payload = validate(json.loads(raw))
        elif args.command == "preflight":
            payload = preflight_payload(args.workspace, args.tool)
        else:
            payload = ledger_payload(args.workspace, args.rules)
        if args.as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            emit(payload, args.format, args.out)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.command == "preflight":
        required = payload["blocks"][0]["items"]
        return 2 if any(i["status"] == "missing" for i in required) else 0
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
