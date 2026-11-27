from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

JOB_ROOT = Path(__file__).resolve().parent.parent
LEDGER_SCRIPT = JOB_ROOT / "scripts" / "ledger" / "ledger.py"


def run_ledger(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LEDGER_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def write_rules(ws: Path) -> Path:
    rules_path = ws / "rules.json"
    rules = {
        "employer_aliases": [
            ["Northstar Engineering LLC", "Northstar Engineering", "Northstar"],
            ["Apex Labs Inc.", "Apex Labs"],
        ]
    }
    rules_path.write_text(json.dumps(rules, indent=2), encoding="utf-8")
    return rules_path


def test_check_returns_zero_when_clean_or_non_submitted(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    write_rules(ws)

    # Empty workspace -> exit 0
    res = run_ledger("check", "Northstar", "--workspace", str(ws))
    assert res.returncode == 0

    # Non-blocking states -> exit 0
    for status in ("reserved", "submission_attempted", "blocked", "outcome_unknown", "skipped"):
        rec = run_ledger(
            "record",
            "--employer",
            "Northstar Engineering",
            "--role",
            "Design Engineer",
            "--status",
            status,
            "--req",
            "REQ-100",
            "--workspace",
            str(ws),
        )
        assert rec.returncode == 0, rec.stderr

        chk = run_ledger("check", "Northstar", "--workspace", str(ws), "--json")
        assert chk.returncode == 0
        payload = json.loads(chk.stdout)
        assert payload["duplicate"] is False
        assert len(payload["all_matches"]) == 1


def test_check_returns_one_on_verified_alias_and_req_match(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    write_rules(ws)

    rec = run_ledger(
        "record",
        "--employer",
        "Northstar Engineering LLC",
        "--role",
        "Systems Analyst",
        "--status",
        "verified",
        "--req",
        "REQ-778",
        "--location",
        "Remote",
        "--receipt",
        "CONF-778",
        "--workspace",
        str(ws),
    )
    assert rec.returncode == 0

    # Alias match -> exit 1
    chk_alias = run_ledger("check", "Northstar", "--workspace", str(ws), "--json")
    assert chk_alias.returncode == 1
    alias_data = json.loads(chk_alias.stdout)
    assert alias_data["duplicate"] is True
    assert "employer" in alias_data["blocking_matches"][0]["matched_by"]

    # Req ID match even with different name -> exit 1
    chk_req = run_ledger("check", "Unrelated Brand", "--req", "req-778", "--workspace", str(ws), "--json")
    assert chk_req.returncode == 1
    req_data = json.loads(chk_req.stdout)
    assert req_data["duplicate"] is True
    assert "req" in req_data["blocking_matches"][0]["matched_by"]

    # Unrelated employer + req -> exit 0
    chk_other = run_ledger("check", "Apex Labs", "--req", "REQ-999", "--workspace", str(ws))
    assert chk_other.returncode == 0


def test_render_collapses_events_and_groups_by_status(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    write_rules(ws)

    # Lifecycle of one application: reserved -> submission_attempted -> verified
    assert run_ledger(
        "record", "--employer", "Apex Labs", "--role", "Data Engineer",
        "--status", "reserved", "--req", "R-1", "--location", "Austin, TX",
        "--workspace", str(ws),
    ).returncode == 0
    assert run_ledger(
        "record", "--employer", "Apex Labs Inc.", "--role", "Data Engineer",
        "--status", "submission_attempted", "--req", "R-1",
        "--workspace", str(ws),
    ).returncode == 0
    assert run_ledger(
        "record", "--employer", "Apex Labs", "--role", "Data Engineer",
        "--status", "verified", "--req", "R-1", "--receipt", "APP-2026-01",
        "--workspace", str(ws),
    ).returncode == 0

    # Second blocked application
    assert run_ledger(
        "record", "--employer", "Harbor Works", "--role", "Project Coordinator",
        "--status", "blocked", "--req", "R-2", "--notes", "Waiting on salary range",
        "--workspace", str(ws),
    ).returncode == 0

    ren = run_ledger("render", "--workspace", str(ws))
    assert ren.returncode == 0

    log_md = (ws / "log.md").read_text(encoding="utf-8")
    assert "- **Verified Applications**: 1" in log_md
    assert "- **Total Tracked Roles**: 2" in log_md
    assert "## Verified (1)" in log_md
    assert "## Blocked (1)" in log_md
    assert "APP-2026-01" in log_md
    assert "Austin, TX" in log_md
    assert "Waiting on salary range" in log_md


def test_ledger_records_who_did_the_job(tmp_path: Path) -> None:
    sys.path.insert(0, str(LEDGER_SCRIPT.parent))
    import ledger  # noqa: E402

    ledger.record_entry(tmp_path, "Northstar", "Analyst", "verified",
                        done_by="Model A (high, standard)", sent_by="Model B")
    entry = json.loads((tmp_path / "applications.jsonl").read_text(encoding="utf-8"))
    assert ledger.agents(entry) == "Model A (high, standard), sent by Model B"
    assert ledger.agents({"done_by": "Model B", "sent_by": "Model B"}) == "Model B"
    log = ledger.render_markdown(workspace=tmp_path, rules=None, output=None).read_text(encoding="utf-8")
    assert "Done by" in log and "sent by Model B" in log
