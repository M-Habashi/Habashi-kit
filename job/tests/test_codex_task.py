from __future__ import annotations

import json
import sys
from pathlib import Path

JOB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(JOB_ROOT / "scripts" / "agents"))
sys.path.insert(0, str(JOB_ROOT / "scripts" / "ledger"))

import codex_task  # noqa: E402
import ledger  # noqa: E402

CATALOG = [
    {"slug": "gpt-6.2-astra", "visibility": "list"},
    {"slug": "gpt-6.1-sol", "visibility": "list"},
    {"slug": "gpt-6.10-sol", "visibility": "hide"},
    {"slug": "gpt-6.2-sol", "visibility": "list", "display_name": "GPT-6.2-Sol"},
    {"slug": "gpt-5.6-sol", "visibility": "list"},
    {"slug": "gpt-6-sol", "visibility": "list"},
]


def test_picks_newest_listed_sol_by_version_not_order() -> None:
    assert codex_task.pick_latest_sol(CATALOG)["slug"] == "gpt-6.2-sol"
    assert codex_task.pick_latest_sol(list(reversed(CATALOG)))["slug"] == "gpt-6.2-sol"
    assert codex_task.pick_latest_sol([{"slug": "gpt-6.2-astra"}]) is None
    assert codex_task.version("gpt-6.10-sol") > codex_task.version("gpt-6.2-sol")


def test_command_defaults_to_high_effort_and_standard_speed() -> None:
    cmd = codex_task.build_command("codex", "gpt-6.2-sol")
    assert cmd[:2] == ["codex", "exec"] and cmd[cmd.index("-m") + 1] == "gpt-6.2-sol"
    assert 'model_reasoning_effort="high"' in cmd and 'service_tier="default"' in cmd
    assert cmd[-1] == "-"  # multi-line prompt goes on stdin
    assert 'service_tier="priority"' in codex_task.build_command("codex", "m", fast=True)


def test_ledger_records_who_did_the_job(tmp_path: Path) -> None:
    ledger.record_entry(tmp_path, "Northstar", "Analyst", "verified",
                        done_by="GPT-6.2-Sol (high, standard)", sent_by="Claude Opus 5.5")
    entry = json.loads((tmp_path / "applications.jsonl").read_text(encoding="utf-8"))
    assert ledger.agents(entry) == "GPT-6.2-Sol (high, standard), sent by Claude Opus 5.5"
    assert ledger.agents({"done_by": "Claude Opus 5.5", "sent_by": "Claude Opus 5.5"}) == "Claude Opus 5.5"
    log = ledger.render_markdown(workspace=tmp_path, rules=None, output=None).read_text(encoding="utf-8")
    assert "Done by" in log and "sent by Claude Opus 5.5" in log
