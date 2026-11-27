"""Compact tool-readiness checks for Habashi-kit/job, written for non-technical users.

One checklist line per required tool: the browser (BrowserOS Neo) and the desktop helper
(Cua Driver, https://github.com/trycua/cua) that handles windows outside the browser, such as
sign-in pop-ups and native dialogs. A line carries text only when something is wrong, and that
text is one plain-language step for the user.

With fix=True the agent-side fixes run first (open BrowserOS, start the Cua Driver daemon), so only
steps that truly need the user remain. Browser problems block applications ("missing").
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any
from pathlib import Path

NEO_URL_DEFAULT = "http://127.0.0.1:9010/mcp"
BROWSER = "Browser (BrowserOS)"
CUA = "Desktop helper (Cua Driver): pop-ups and other windows"
CUA_REPO = "https://github.com/trycua/cua"
CUA_TEXT = {
    "missing": "The desktop helper (Cua Driver) isn't installed. Say \"install it\" and I'll set it up.",
    "stopped": "The desktop helper (Cua Driver) isn't running. Please restart your computer, then tell me.",
    "live": "The desktop helper (Cua Driver) couldn't see your windows. Please restart your computer, then tell me.",
}


def item(label: str, status: str, detail: str) -> dict[str, str]:
    return {"label": label, "status": status, "detail": detail}


# --------------------------------------------------------------------------- process helpers

def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, check=False)
    else:
        proc.kill()


def run_cmd(args: list[str], timeout: int = 30, stdin_text: str | None = None) -> tuple[int, str]:
    """Run a command with stdin closed (or fed from `stdin_text` via a temp file) and output in a
    temp file, so neither a CLI waiting for stdin nor a grandchild holding a pipe can hang the
    check. Kills the tree on timeout."""
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as inp:
        stdin: Any = subprocess.DEVNULL
        if stdin_text is not None:
            inp.write(stdin_text.encode("utf-8"))
            inp.seek(0)
            stdin = inp
        try:
            proc = subprocess.Popen(args, stdin=stdin, stdout=out, stderr=subprocess.STDOUT)
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


def launch(args: list[str]) -> bool:
    """Start an app without waiting for it."""
    try:
        flags = 0
        if os.name == "nt":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=flags)
        return True
    except OSError:
        return False


def wait_until(predicate, seconds: int) -> bool:
    for _ in range(seconds):
        if predicate():
            return True
        time.sleep(1)
    return bool(predicate())


def process_paths() -> list[str]:
    """Executable paths (Windows) or command names (macOS/Linux) of running processes."""
    if os.name == "nt":
        code, out = run_cmd(["powershell", "-NoProfile", "-Command",
                             "Get-Process | ForEach-Object { $_.Path } | Where-Object { $_ }"])
    else:
        code, out = run_cmd(["ps", "-axo", "comm="])
    return [line.strip() for line in out.splitlines() if line.strip()] if code == 0 else []


# --------------------------------------------------------------------------- browser (BrowserOS Neo)

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


def browseros_command(installs: list[Path]) -> list[str] | None:
    for base in installs:
        if base.suffix == ".app":
            return ["open", "-a", str(base)]
        exe = base / "chrome.exe"
        if exe.is_file():
            return [str(exe)]
    return None


def mcp_answers(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    """Any HTTP response (even 4xx such as 406) means the MCP server is listening."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        return True, f"HTTP {exc.code}"
    except (urllib.error.URLError, OSError) as exc:
        return False, str(getattr(exc, "reason", exc))


def neo_item(procs: list[str], neo_url: str, agent: str | None = None, fix: bool = False) -> dict[str, str]:
    """One line: installed + open + responding (+ this agent can reach it)."""
    installs, running = browseros_install_paths(), browseros_running(procs)
    if not installs and not running:
        return item(BROWSER, "missing", "BrowserOS isn't installed. Please install BrowserOS, then tell me.")
    if not running and fix:
        command = browseros_command(installs)
        if command and launch(command):
            running = wait_until(lambda: mcp_answers(neo_url, 2)[0], 30)
    if not running:
        return item(BROWSER, "missing", "BrowserOS is closed. Please open BrowserOS, then tell me.")
    if not mcp_answers(neo_url)[0]:
        return item(BROWSER, "missing", "BrowserOS is open but not responding. Please close and reopen it.")
    if agent and agent.lower().startswith("error"):
        return item(BROWSER, "missing", "I can't connect to BrowserOS. Please close and reopen it, then tell me.")
    return item(BROWSER, "ok", "")


# --------------------------------------------------------------------------- desktop helper (Cua Driver)

def cua_path() -> str | None:
    """The cua-driver executable: on PATH, or in its default install folder."""
    found = shutil.which("cua-driver")
    if found:
        return found
    candidates = [Path.home() / ".local" / "bin" / "cua-driver", Path("/usr/local/bin/cua-driver")]
    if os.environ.get("LOCALAPPDATA"):
        candidates.insert(0, Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Cua" / "cua-driver" / "bin" / "cua-driver.exe")
    return next((str(p) for p in candidates if p.is_file()), None)


def cua_running(exe: str) -> bool:
    code, out = run_cmd([exe, "status"], timeout=15)
    return code == 0 and "daemon is running" in out.lower()


def cua_live_test(exe: str) -> bool:
    """Read-only: list on-screen windows."""
    code, out = run_cmd([exe, "call", "list_windows", '{"on_screen_only":true}'], timeout=30)
    return code == 0 and '"window_id"' in out


def cua_item(live: bool = False, fix: bool = False) -> dict[str, str]:
    """One line: installed + daemon running (+ can list windows)."""
    exe = cua_path()
    if not exe:
        return item(CUA, "missing", CUA_TEXT["missing"])
    if fix and not cua_running(exe):
        launch([exe, "serve"])
        wait_until(lambda: cua_running(exe), 20)
    if not cua_running(exe):
        return item(CUA, "missing", CUA_TEXT["stopped"])
    if live and not cua_live_test(exe):
        return item(CUA, "missing", CUA_TEXT["live"])
    return item(CUA, "ok", "")


def system_items(neo_url: str = NEO_URL_DEFAULT, live: bool = False, neo_agent: str | None = None,
                 fix: bool = False) -> list[dict[str, str]]:
    procs = process_paths()
    return [neo_item(procs, neo_url, neo_agent, fix), cua_item(live, fix)]


if __name__ == "__main__":  # quick manual check
    for entry in system_items(live="--live" in sys.argv, fix="--fix" in sys.argv):
        print(f"{entry['status']:8} {entry['label']}  {entry['detail']}")
