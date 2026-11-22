#!/usr/bin/env python3
"""Hand a browser or computer-use task to the newest Codex "Sol" model through the Codex CLI.

Use it when the agent can't delegate natively (for example, T3 Code isn't on the machine)
and isn't already that model. Defaults: reasoning effort high, standard speed.

  python job/scripts/agents/codex_task.py latest
  python job/scripts/agents/codex_task.py run "<task>" --sent-by "Claude Opus 5.5" [--workspace W]
      [--model M] [--effort high] [--fast] [--timeout 1800]

`run` prints JSON: {"ok", "model", "done_by", "sent_by", "effort", "speed", "result"}.
Exit codes: 0 done, 1 the task failed or timed out, 2 Codex or a Sol model isn't available.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "render"))
import toolcheck  # noqa: E402

SOL_RE = re.compile(r"^gpt-(\d+(?:\.\d+)*)-sol$")
EFFORTS = ("low", "medium", "high", "xhigh", "max", "ultra")
PREAMBLE = """You are doing one task for a job seeker, handed to you by {sent_by}.
- Do all web work in BrowserOS Neo (the browseros-neo tools). Don't use another browser.
- Use computer use only for windows outside the browser, one window at a time, and end it as soon as that part is done.
- Workspace: {workspace}. Read job/SKILL.md (Step 2) for the application rules when the task is an application.
- If you need an answer only the user can give, stop and list the exact questions.
- End with a short plain-language summary: what you did, the result, and any questions.

Task:
{task}"""


def catalog(codex: str) -> list[dict[str, Any]]:
    code, out = toolcheck.run_cmd([codex, "debug", "models"], timeout=60)
    if code != 0:
        return []
    try:
        return json.loads(out[out.index("{"):]).get("models", [])
    except (ValueError, AttributeError):
        return []


def version(slug: str) -> tuple[int, ...] | None:
    m = SOL_RE.match(slug)
    return tuple(int(p) for p in m.group(1).split(".")) if m else None


def pick_latest_sol(models: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Newest listed `gpt-<version>-sol` model, by version number (not catalog order)."""
    sols = [m for m in models if m.get("visibility", "list") == "list" and version(str(m.get("slug", "")))]
    return max(sols, key=lambda m: version(m["slug"]), default=None)


def display(model: dict[str, Any] | str) -> str:
    if isinstance(model, dict):
        return str(model.get("display_name") or model.get("slug"))
    return str(model)


def build_command(codex: str, model: str, effort: str = "high", fast: bool = False,
                  last_message: Path | None = None) -> list[str]:
    """The prompt goes on stdin (`-`): on Windows a multi-line argument is cut at the first line."""
    cmd = [codex, "exec", "--skip-git-repo-check", "-m", model,
           "-c", f'model_reasoning_effort="{effort}"',
           "-c", f'service_tier="{"priority" if fast else "default"}"']
    if last_message:
        cmd += ["-o", str(last_message)]
    return cmd + ["-"]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("latest", help="Print the newest Codex Sol model id.")
    p_run = sub.add_parser("run", help="Run one task on the newest Sol model.")
    p_run.add_argument("task")
    p_run.add_argument("--sent-by", required=True, help="The model handing the task over, e.g. 'Claude Opus 5.5'.")
    p_run.add_argument("--workspace", default="workspace")
    p_run.add_argument("--model", default=None, help="Override the model (default: newest Sol).")
    p_run.add_argument("--effort", choices=EFFORTS, default="high")
    p_run.add_argument("--fast", action="store_true", help="Fast speed (uses more of the plan). Only when the user asks.")
    p_run.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()

    codex = shutil.which("codex")
    if not codex:
        print(json.dumps({"ok": False, "error": "codex_missing"}))
        return 2
    models = catalog(codex)
    latest = pick_latest_sol(models)
    if args.command == "latest":
        if not latest:
            return 2
        print(latest["slug"])
        return 0

    chosen = next((m for m in models if m.get("slug") == args.model), args.model) if args.model else latest
    if not chosen:
        print(json.dumps({"ok": False, "error": "no_sol_model"}))
        return 2
    slug = chosen["slug"] if isinstance(chosen, dict) else chosen
    prompt = PREAMBLE.format(sent_by=args.sent_by, workspace=args.workspace, task=args.task)
    with tempfile.TemporaryDirectory() as tmp:
        last = Path(tmp) / "last.txt"
        code, out = toolcheck.run_cmd(build_command(codex, slug, args.effort, args.fast, last),
                                      timeout=args.timeout, stdin_text=prompt)
        result = last.read_text(encoding="utf-8").strip() if last.is_file() else out[-2000:]
    speed = "fast" if args.fast else "standard"
    print(json.dumps({
        "ok": code == 0, "model": slug, "effort": args.effort, "speed": speed,
        "done_by": f"{display(chosen)} ({args.effort}, {speed})", "sent_by": args.sent_by,
        "result": result,
    }, ensure_ascii=False, indent=2))
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
