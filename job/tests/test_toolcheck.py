from __future__ import annotations

import socket
import sys
import time
from pathlib import Path

JOB_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(JOB_ROOT / "scripts" / "render"))

import toolcheck  # noqa: E402

APP_NEW = r"C:\Program Files\WindowsApps\OpenAI.Codex_26.2_x64__abc"
APP_OLD = r"C:\Program Files\WindowsApps\OpenAI.Codex_26.1_x64__abc"


def test_codex_app_detection_ignores_extension_host() -> None:
    only_host = [APP_OLD + r"\app\resources\plugins\chrome\extension-host\windows\x64\extension-host.exe"]
    assert toolcheck.codex_app_running(only_host) == (False, False)
    running = [APP_NEW + r"\app\ChatGPT.exe", APP_NEW + r"\app\resources\codex-computer-use-swift.exe"]
    assert toolcheck.codex_app_running(running) == (True, True)
    assert toolcheck.codex_app_running(["/Applications/Codex.app/Contents/MacOS/Codex"]) == (True, False)


def test_browseros_running_needs_browser_not_just_server() -> None:
    base = r"C:\Users\x\AppData\Local\BrowserClaw\Application"
    assert not toolcheck.browseros_running([base + r"\155.0\BrowserClawServer\bin\browseros-claw-server.exe"])
    assert toolcheck.browseros_running([base + r"\chrome.exe"])
    assert not toolcheck.browseros_running([r"C:\Program Files\Google\Chrome\Application\chrome.exe"])


def test_stale_app_paths_flags_missing_install(tmp_path: Path) -> None:
    present = tmp_path / "OpenAI.Codex_26.2_x64__abc" / "node.exe"
    present.parent.mkdir()
    present.write_text("")
    config = (
        f"command = '{present}'\n"
        "notify = [ \"C:\\Program Files\\WindowsApps\\OpenAI.Codex_26.1_x64__abc\\app\\cu.exe\" ]\n"
    )
    stale = toolcheck.stale_app_paths(config)
    assert len(stale) == 1 and "OpenAI.Codex_26.1" in stale[0]


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


def test_codex_checks_without_cli(monkeypatch) -> None:
    monkeypatch.setattr(toolcheck.shutil, "which", lambda name: None)
    items = toolcheck.codex_checks([])
    assert items[0]["status"] == "warn" and "handed to the user" in items[0]["detail"]
