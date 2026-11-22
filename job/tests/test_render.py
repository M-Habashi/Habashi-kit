from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

JOB_ROOT = Path(__file__).resolve().parent.parent
RENDER = JOB_ROOT / "scripts" / "render" / "render.py"
INIT = JOB_ROOT / "scripts" / "init_workspace.py"
LEDGER = JOB_ROOT / "scripts" / "ledger" / "ledger.py"
EXAMPLES = sorted((JOB_ROOT / "scripts" / "render" / "examples").glob("*.json"))


def run(script: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8", input=stdin, check=False,
    )


def fill_workspace(ws: Path) -> None:
    (ws / "docs" / "Sample_Resume.pdf").write_bytes(b"%PDF-1.4 sample")
    profile = (ws / "profile.md").read_text(encoding="utf-8")
    for label, value in {
        "Full Name": "Sample Candidate", "Email": "candidate@example.com", "Phone": "+1-555-010-2020",
        "Location": "Denver, CO", "LinkedIn": "https://www.linkedin.com/in/sample",
    }.items():
        profile = "\n".join(
            f"- **{label}**: `{value}`" if line.startswith(f"- **{label}**:") else line
            for line in profile.splitlines()
        )
    (ws / "profile.md").write_text(profile, encoding="utf-8")
    answers = (ws / "answers.md").read_text(encoding="utf-8")
    for label in (
        "Authorized to Work in Target Country Today?",
        "Will You Now or in the Future Require Visa Sponsorship?",
        "Earliest Available Start Date", "Salary Expectation Rule", "Target Roles",
        "Target Locations / Work Mode",
    ):
        answers = "\n".join(
            f"- **{label}**: `Filled`" if line.startswith(f"- **{label}**:") else line
            for line in answers.splitlines()
        )
    (ws / "answers.md").write_text(answers, encoding="utf-8")
    rules = json.loads((ws / "rules.json").read_text(encoding="utf-8"))
    rules.update(author_name="Sample Candidate", file_prefix="Sample_Candidate_Cover_Letter",
                 employer_order=["Example Employer"])
    (ws / "rules.json").write_text(json.dumps(rules), encoding="utf-8")


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_examples_render_in_both_formats(example: Path) -> None:
    html_res = run(RENDER, "card", str(example))
    assert html_res.returncode == 0, html_res.stderr
    assert html_res.stdout.startswith("<!doctype html>") and "var(--" in html_res.stdout
    text_res = run(RENDER, "card", str(example), "--format", "text")
    assert text_res.returncode == 0, text_res.stderr
    assert "<" not in text_res.stdout.split("\n", 1)[0]


def test_card_escapes_html_and_computes_badge() -> None:
    payload = {"title": "<script>x</script>", "blocks": [
        {"type": "checklist", "items": [{"label": "A & B", "status": "missing"}, {"label": "C", "status": "ok"}]}]}
    res = run(RENDER, "card", "-", stdin=json.dumps(payload))
    assert res.returncode == 0
    assert "<script>x" not in res.stdout and "&lt;script&gt;" in res.stdout
    assert "A &amp; B" in res.stdout and "1 missing" in res.stdout
    text = run(RENDER, "card", "-", "--format", "text", stdin=json.dumps(payload)).stdout
    assert "MISSING  A & B" in text and "[1 missing]" in text


def test_card_rejects_bad_payload() -> None:
    res = run(RENDER, "card", "-", stdin=json.dumps({"title": "x", "blocks": [{"type": "chart"}]}))
    assert res.returncode == 1 and "type" in res.stderr


def test_preflight_fresh_workspace_pauses(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    assert run(INIT, str(ws)).returncode == 0
    res = run(RENDER, "preflight", "--workspace", str(ws), "--format", "text", "--offline",
              "--tool", "BrowserOS Neo MCP=warn:Not connected")
    assert res.returncode == 2
    assert "MISSING   Your resume" in res.stdout
    assert "Still needed: full name" in res.stdout and "job history order" in res.stdout
    assert ".md" not in res.stdout and "json" not in res.stdout.lower()  # no file names for non-technical users
    assert "BrowserOS Neo MCP - Not connected" in res.stdout


def test_preflight_filled_workspace_passes_and_writes_file(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    run(INIT, str(ws))
    fill_workspace(ws)
    out = ws / "output" / "render" / "preflight.html"
    res = run(RENDER, "preflight", "--workspace", str(ws), "--offline", "--out", str(out))
    assert res.returncode == 0, res.stdout + res.stderr
    html = out.read_text(encoding="utf-8")
    assert "Your resume" in html and "pause applications" not in html


def test_preflight_rejects_bad_tool_flag(tmp_path: Path) -> None:
    res = run(RENDER, "preflight", "--workspace", str(tmp_path), "--offline", "--tool", "Neo=great")
    assert res.returncode == 1 and "NAME=STATUS" in res.stderr


def test_ledger_render(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    run(INIT, str(ws))
    run(LEDGER, "record", "--employer", "Northstar", "--role", "Analyst", "--status", "reserved",
        "--req", "R1", "--workspace", str(ws))
    run(LEDGER, "record", "--employer", "Northstar", "--role", "Analyst", "--status", "verified",
        "--req", "R1", "--receipt", "NS-1", "--workspace", str(ws))
    res = run(RENDER, "ledger", "--workspace", str(ws), "--format", "text")
    assert res.returncode == 0, res.stderr
    assert "[1 verified]" in res.stdout and "NS-1" in res.stdout and "reserved" not in res.stdout.lower().split("applications", 1)[1]
    payload = json.loads(run(RENDER, "ledger", "--workspace", str(ws), "--json").stdout)
    assert payload["blocks"][1]["rows"][0][3] == "verified"


def test_tools_offline_and_blocking_neo(tmp_path: Path) -> None:
    res = run(RENDER, "tools", "--offline", "--format", "text")
    assert res.returncode == 0 and "Browser (BrowserOS)" in res.stdout and "SKIPPED" in res.stdout
    tools_lines = [l for l in res.stdout.splitlines() if l.startswith("  ")]
    assert len(tools_lines) == 4  # one line per tool: Neo, ChatGPT/Codex, Claude, local scripts
    blocked = run(RENDER, "tools", "--offline", "--format", "text", "--neo-agent", "error:refused")
    assert blocked.returncode == 2 and "browser must work" in blocked.stdout and "MCP" not in blocked.stdout


def test_preflight_blocks_on_unusable_neo(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    run(INIT, str(ws))
    fill_workspace(ws)
    res = run(RENDER, "preflight", "--workspace", str(ws), "--offline", "--format", "text",
              "--neo-agent", "error:refused")
    assert res.returncode == 2 and "browser must work" in res.stdout
