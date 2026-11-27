from __future__ import annotations

import socket
import sys
import time
from pathlib import Path

JOB_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(JOB_ROOT / "scripts" / "render"))

import toolcheck  # noqa: E402

def test_browseros_running_needs_browser_not_just_server() -> None:
    base = r"C:\Users\x\AppData\Local\BrowserClaw\Application"
    assert not toolcheck.browseros_running([base + r"\155.0\BrowserClawServer\bin\browseros-claw-server.exe"])
    assert toolcheck.browseros_running([base + r"\chrome.exe"])
    assert not toolcheck.browseros_running([r"C:\Program Files\Google\Chrome\Application\chrome.exe"])


def test_mcp_answers_false_on_closed_port() -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    ok, why = toolcheck.mcp_answers(f"http://127.0.0.1:{port}/mcp", timeout=1)
    assert not ok and why


def test_run_cmd_closes_stdin_and_times_out() -> None:
    code, out = toolcheck.run_cmd([sys.executable, "-c", "import sys; print(repr(sys.stdin.read()))"], timeout=20)
    assert code == 0 and "''" in out
    start = time.monotonic()
    code, out = toolcheck.run_cmd([sys.executable, "-c", "import time; time.sleep(30)"], timeout=2)
    assert code == -1 and "timed out" in out and time.monotonic() - start < 20


def test_neo_item_is_one_line_with_fix(monkeypatch) -> None:
    monkeypatch.setattr(toolcheck, "browseros_install_paths", lambda: [])
    entry = toolcheck.neo_item([], "http://127.0.0.1:9/mcp")
    assert entry["status"] == "missing" and "install BrowserOS" in entry["detail"]
    monkeypatch.setattr(toolcheck, "browseros_install_paths", lambda: [Path("x")])
    monkeypatch.setattr(toolcheck, "browseros_running", lambda procs: True)
    monkeypatch.setattr(toolcheck, "mcp_answers", lambda url, timeout=3.0: (True, "HTTP 406"))
    assert toolcheck.neo_item([], "u")["detail"] == ""
    assert "can't connect" in toolcheck.neo_item([], "u", "error: refused")["detail"]


def test_user_facing_text_has_no_jargon() -> None:
    jargon = ("mcp", "cli", "json", "config", "plugin path", "run:", "pnpm", "pip ")
    texts = list(toolcheck.CUA_TEXT.values())
    for text in texts:
        assert not any(word in text.lower() for word in jargon), text


def test_cua_item_reports_install_and_daemon(monkeypatch) -> None:
    monkeypatch.setattr(toolcheck, "cua_path", lambda: None)
    entry = toolcheck.cua_item()
    assert entry["status"] == "missing" and "isn't installed" in entry["detail"]
    monkeypatch.setattr(toolcheck, "cua_path", lambda: "cua-driver")
    monkeypatch.setattr(toolcheck, "run_cmd", lambda args, timeout=30: (0, "Cua Driver daemon is not running"))
    assert "isn't running" in toolcheck.cua_item()["detail"]
    monkeypatch.setattr(toolcheck, "run_cmd", lambda args, timeout=30: (0, "Cua Driver daemon is running"))
    assert toolcheck.cua_item() == {"label": toolcheck.CUA, "status": "ok", "detail": ""}
