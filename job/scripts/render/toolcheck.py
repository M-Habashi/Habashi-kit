"""Compact tool-readiness checks for Habashi-kit/job, written for non-technical users.

One checklist line per tool: the browser (BrowserOS Neo), the ChatGPT Codex app (preferred for
controlling apps and the browser), the Claude app (alternative). A line carries text only when
something is wrong, and that text is one plain-language step for the user.

With fix=True the agent-side fixes run first (open BrowserOS, open the Codex app, which also
refreshes its computer-use setup after an update, and link BrowserOS to Codex), so only steps
that truly need the user remain. Browser problems block applications ("missing"); app problems
are "warn".
"""

from __future__ import annotations

import os
import re
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
CHATGPT = "ChatGPT Codex app (preferred): controls apps and the browser"
CLAUDE = "Claude app (alternative): controls apps and the browser"
CU_LIVE_PROMPT = (
    "Diagnostic test only, read-only. Using your Windows/macOS computer-use tool: call list_windows() "
    "and count the windows, then capture ONE window with a screenshot (get_window_state with "
    "include_screenshot true). Do not click, type, launch, activate, or close anything. "
    "Reply in one line: 'CU_OK <window count>' or 'CU_FAIL <exact error>'."
)
CODEX_TEXT = {
    "missing": "The ChatGPT Codex app isn't installed. Install it, or use the Claude app instead.",
    "signin": "Please sign in to the ChatGPT Codex app with your ChatGPT account.",
    "app": "Please open the ChatGPT Codex app and leave it running.",
    "plugin": "Please turn on Computer Use in the ChatGPT Codex app settings.",
    "stale": "Please close and reopen the ChatGPT Codex app (it was just updated).",
    "neo": "I couldn't link BrowserOS to the ChatGPT Codex app. Please close and reopen both apps.",
    "live": "The ChatGPT Codex app couldn't control other apps. Please close and reopen it.",
}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


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


# --------------------------------------------------------------------------- ChatGPT Codex app

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
    which can stay alive after the app closes. On Windows the app process is named ChatGPT."""
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


def neo_registered(text: str, neo_url: str) -> bool:
    low = text.lower()
    return "browseros" in low or neo_url.lower() in low


def codex_state(codex: str, procs: list[str], neo_url: str) -> str:
    """First problem found as a CODEX_TEXT key, or '' when ready (before the live test)."""
    code, login = run_cmd([codex, "login", "status"])
    if code != 0 or "logged in" not in login.lower():
        return "signin"
    if not codex_app_running(procs)[0]:
        return "app"
    config = codex_home() / "config.toml"
    text = config.read_text(encoding="utf-8", errors="replace") if config.is_file() else ""
    if not ("[mcp_servers.cua_repl]" in text
            or (codex_home() / "plugins" / "cache" / "openai-bundled" / "unified-computer-use").is_dir()):
        return "plugin"
    if stale_app_paths(text):
        return "stale"
    if not neo_registered(text, neo_url):
        return "neo"
    return ""


def codex_live_test(codex: str, timeout: int = 240) -> tuple[str, str]:
    code, out = run_cmd([codex, "exec", "--skip-git-repo-check", CU_LIVE_PROMPT], timeout=timeout)
    lines = [l.strip() for l in out.splitlines() if l.strip().startswith(("CU_OK", "CU_FAIL"))]
    if lines and lines[-1].startswith("CU_OK"):
        return "ok", lines[-1]
    if lines:
        return "warn", lines[-1]
    return "warn", f"No result (exit {code}): {out[-160:]}"


def chatgpt_item(procs: list[str], live: bool = False, neo_url: str = NEO_URL_DEFAULT,
                 fix: bool = False) -> dict[str, str]:
    """Preferred: Codex (ChatGPT) computer use + BrowserOS automation, as one line."""
    codex = shutil.which("codex")
    if not codex:
        return item(CHATGPT, "warn", CODEX_TEXT["missing"])
    state = codex_state(codex, procs, neo_url)
    if fix and state in ("app", "stale"):
        # Opening the app starts computer use and rewrites stale paths after an update.
        launch([codex, "app"])
        wait_until(lambda: codex_state(codex, process_paths(), neo_url) not in ("app", "stale"), 45)
        state = codex_state(codex, process_paths(), neo_url)
    if fix and state == "neo":
        run_cmd([codex, "mcp", "add", "browseros-neo", "--url", neo_url])
        state = codex_state(codex, process_paths(), neo_url)
    if state:
        return item(CHATGPT, "warn", CODEX_TEXT[state])
    if live and codex_live_test(codex)[0] != "ok":
        return item(CHATGPT, "warn", CODEX_TEXT["live"])
    return item(CHATGPT, "ok", "")


# --------------------------------------------------------------------------- Claude app

def claude_app_running(procs: list[str]) -> bool:
    return any("/windowsapps/claude_" in p.replace("\\", "/").lower() or "claude.app/" in p.lower() for p in procs)


def claude_item(procs: list[str], agent_cu: str | None, neo_url: str = NEO_URL_DEFAULT) -> dict[str, str]:
    """Alternative: Claude has computer use only inside the Claude desktop app (not Claude Code CLI)."""
    claude_cfg = Path.home() / ".claude.json"
    text = claude_cfg.read_text(encoding="utf-8", errors="replace") if claude_cfg.is_file() else ""
    if agent_cu == "yes":
        linked = neo_registered(text, neo_url)
        return item(CLAUDE, "ok" if linked else "warn",
                    "" if linked else "I couldn't link BrowserOS to the Claude app. Please close and reopen both apps.")
    if not shutil.which("claude") and not claude_app_running(procs):
        return item(CLAUDE, "optional", "To use Claude instead: install the Claude app and turn on Computer use in its Settings.")
    return item(CLAUDE, "optional", "To use Claude instead: open this chat in the Claude app and turn on Computer use in its Settings.")


def system_items(neo_url: str = NEO_URL_DEFAULT, live: bool = False, neo_agent: str | None = None,
                 claude_cu: str | None = None, fix: bool = False) -> list[dict[str, str]]:
    procs = process_paths()
    neo = neo_item(procs, neo_url, neo_agent, fix)
    if fix:
        procs = process_paths()
    return [neo, chatgpt_item(procs, live, neo_url, fix), claude_item(procs, claude_cu, neo_url)]


if __name__ == "__main__":  # quick manual check
    for entry in system_items(live="--live" in sys.argv, fix="--fix" in sys.argv):
        print(f"{entry['status']:8} {entry['label']}  {entry['detail']}")
