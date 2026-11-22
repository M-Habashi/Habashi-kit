"""Deterministic tool-readiness checks for Habashi-kit/job (browser + OS computer use).

Every check returns a checklist item: {"label", "status", "detail"}.
Browser problems are blocking ("missing"); OS computer-use problems are "warn" so the agent
notifies the user and continues (OS-level steps then go to the user).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

NEO_URL_DEFAULT = "http://127.0.0.1:9010/mcp"
CU_LIVE_PROMPT = (
    "Diagnostic test only, read-only. Using your Windows/macOS computer-use tool: call list_windows() "
    "and count the windows, then capture ONE window with a screenshot (get_window_state with "
    "include_screenshot true). Do not click, type, launch, activate, or close anything. "
    "Reply in one line: 'CU_OK <window count>' or 'CU_FAIL <exact error>'."
)


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)
    else:
        proc.kill()


def run_cmd(args: list[str], timeout: int = 30) -> tuple[int, str]:
    """Run a command with stdin closed and output in a temp file, so neither a CLI waiting
    for stdin nor a grandchild holding a pipe can hang the check. Kills the tree on timeout."""
    with tempfile.TemporaryFile() as out:
        try:
            proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT)
        except OSError as exc:
            return -1, str(exc)
        try:
            code = proc.wait(timeout=timeout)
            suffix = ""
        except subprocess.TimeoutExpired:
            kill_tree(proc)
            proc.wait(timeout=10)
            code, suffix = -1, f"\n[timed out after {timeout}s]"
        out.seek(0)
        return code, out.read().decode("utf-8", "replace").strip() + suffix


def process_paths() -> list[str]:
    """Executable paths (Windows) or command names (macOS/Linux) of running processes."""
    if os.name == "nt":
        code, out = run_cmd(["powershell", "-NoProfile", "-Command",
                             "Get-Process | ForEach-Object { $_.Path } | Where-Object { $_ }"])
    else:
        code, out = run_cmd(["ps", "-axo", "comm="])
    return [line.strip() for line in out.splitlines() if line.strip()] if code == 0 else []


def item(label: str, status: str, detail: str) -> dict[str, str]:
    return {"label": label, "status": status, "detail": detail}


# --------------------------------------------------------------------------- browser (Neo)

def browseros_install_paths() -> list[Path]:
    candidates = [Path("/Applications/BrowserOS.app"), Path("/opt/browseros")]
    if os.environ.get("LOCALAPPDATA"):
        local = Path(os.environ["LOCALAPPDATA"])
        candidates[:0] = [local / "BrowserOS" / "Application", local / "BrowserClaw" / "Application"]
    return [p for p in candidates if p.exists()]


def browseros_running(procs: list[str]) -> bool:
    for proc in procs:
        low = proc.replace("\\", "/").lower()
        is_app = ("/browseros/application/" in low or "/browserclaw/application/" in low
                  or "browseros.app/" in low or low.endswith("/browseros"))
        if is_app and "server" not in low.rsplit("/", 1)[-1]:
            return True
    return False


def mcp_answers(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    """Any HTTP response (even 4xx such as 406) means the MCP server is listening."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return True, f"HTTP {exc.code}"
    except (urllib.error.URLError, OSError) as exc:
        return False, str(getattr(exc, "reason", exc))


def browser_checks(procs: list[str], neo_url: str) -> list[dict[str, str]]:
    installs = browseros_install_paths()
    running = browseros_running(procs)
    up, why = mcp_answers(neo_url)
    if not installs and not running:
        installed = item("BrowserOS Neo installed", "missing", "Not found - ask the user to install BrowserOS Neo, then rerun")
    else:
        installed = item("BrowserOS Neo installed", "ok", str(installs[0]) if installs else "Running")
    if running:
        window = item("BrowserOS Neo running", "ok", "Browser window process found")
    elif installs:
        window = item("BrowserOS Neo running", "missing", "Installed but not running - open it with OS computer use")
    else:
        window = item("BrowserOS Neo running", "missing", "Install it first")
    mcp = item("Neo MCP server answering", "ok" if up else "missing",
               f"{neo_url} ({why})" if up else f"{neo_url} not reachable ({why}) - open or fix BrowserOS, then retry")
    return [installed, window, mcp]


# --------------------------------------------------------------------------- OS computer use (Codex)

APP_PATH_RE = re.compile(r"""([A-Za-z]:\\{1,2}[^'"\n;]*OpenAI\.Codex_[^'"\n;]*|/Applications/Codex\.app[^'"\n;]*)""")


def stale_app_paths(config_text: str) -> list[str]:
    """Paths in Codex config that point into a Codex app install folder that no longer exists."""
    missing = []
    for raw in sorted(set(APP_PATH_RE.findall(config_text))):
        path = raw.replace("\\\\", "\\").rstrip("\\ ")
        if not os.path.exists(path):
            missing.append(path)
    return missing


def codex_app_running(procs: list[str]) -> tuple[bool, bool]:
    """(app running, computer-use helper running). Ignores the browser extension host,
    which can stay alive after the app closes."""
    app = helper = False
    for proc in procs:
        low = proc.replace("\\", "/").lower()
        name = low.rsplit("/", 1)[-1]
        if "/openai.codex_" in low or "codex.app/" in low:
            if name.startswith("codex-computer-use"):
                helper = True
            elif not name.startswith("extension-host"):
                app = True
    return app, helper


def codex_live_test(codex: str, timeout: int = 240) -> tuple[str, str]:
    code, out = run_cmd([codex, "exec", "--skip-git-repo-check", CU_LIVE_PROMPT], timeout=timeout)
    lines = [l.strip() for l in out.splitlines() if l.strip().startswith(("CU_OK", "CU_FAIL"))]
    if lines and lines[-1].startswith("CU_OK"):
        return "ok", lines[-1]
    if lines:
        return "warn", lines[-1]
    return "warn", f"No result (exit {code}): {out[-160:]}"


def codex_checks(procs: list[str], live: bool = False) -> list[dict[str, str]]:
    codex = shutil.which("codex")
    if not codex:
        return [item("Codex CLI installed", "warn", "Not found - OS-level steps will be handed to the user")]
    items = []
    _, version = run_cmd([codex, "--version"])
    items.append(item("Codex CLI installed", "ok", version.splitlines()[0] if version else codex))

    code, login = run_cmd([codex, "login", "status"])
    signed_in = code == 0 and "logged in" in login.lower()
    items.append(item("Codex signed in", "ok" if signed_in else "warn",
                      login.splitlines()[0] if signed_in else "Run: codex login"))

    app, helper = codex_app_running(procs)
    items.append(item("Codex desktop app running", "ok" if app else "warn",
                      ("Computer-use helper is up" if helper else "App open; computer-use helper not started yet")
                      if app else "Open the Codex app - it hosts computer use; the CLI alone cannot do it"))

    config = codex_home() / "config.toml"
    text = config.read_text(encoding="utf-8", errors="replace") if config.is_file() else ""
    plugin = ("[mcp_servers.cua_repl]" in text
              or (codex_home() / "plugins" / "cache" / "openai-bundled" / "unified-computer-use").is_dir())
    stale = stale_app_paths(text)
    if not plugin:
        items.append(item("Computer-use plugin", "warn", "Not installed - enable Computer Use in the Codex app"))
    elif stale:
        items.append(item("Computer-use plugin", "warn",
                          f"{len(stale)} config path(s) point to a removed app version - open the Codex app to refresh them"))
    else:
        items.append(item("Computer-use plugin", "ok", "Installed; config paths match the installed app"))

    if live and signed_in and app and plugin and not stale:
        status, detail = codex_live_test(codex)
        items.append(item("Live window test (read-only)", status, detail))
    else:
        items.append(item("Live window test (read-only)", "pending",
                          "Runs with --live once the checks above pass" if not live else "Skipped - fix the items above first"))
    return items


def claude_note() -> dict[str, str]:
    return item("Claude computer use", "optional",
                "Only in sessions inside the Claude desktop app with Computer use on; Claude Code CLI has none")


def system_checks(neo_url: str = NEO_URL_DEFAULT, live: bool = False) -> tuple[list[dict], list[dict]]:
    procs = process_paths()
    return browser_checks(procs, neo_url), codex_checks(procs, live) + [claude_note()]


if __name__ == "__main__":  # quick manual check
    for block in system_checks(live="--live" in sys.argv):
        for entry in block:
            print(f"{entry['status']:8} {entry['label']} - {entry['detail']}")
