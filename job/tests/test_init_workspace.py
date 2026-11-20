from __future__ import annotations

import subprocess
import sys
from pathlib import Path

JOB_ROOT = Path(__file__).resolve().parent.parent
INIT_SCRIPT = JOB_ROOT / "scripts" / "init_workspace.py"


def run_init(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INIT_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_init_workspace_creates_expected_structure(tmp_path: Path) -> None:
    target = tmp_path / "my_ws"
    res = run_init(str(target))
    assert res.returncode == 0, res.stderr

    for filename in (
        "profile.md",
        "answers.md",
        "rules.json",
        "portals.md",
        "cover-letter-spec.json",
        "applications.jsonl",
    ):
        assert (target / filename).is_file(), f"Missing {filename}"

    for subdir in ("docs", "evidence", "output/pdf"):
        assert (target / subdir).is_dir(), f"Missing {subdir}/"

    assert (target / "applications.jsonl").read_text(encoding="utf-8") == ""


def test_init_workspace_preserves_existing_without_force(tmp_path: Path) -> None:
    target = tmp_path / "my_ws"
    assert run_init(str(target)).returncode == 0

    custom_profile = "# Custom Profile\nCandidate: Test Candidate\n"
    (target / "profile.md").write_text(custom_profile, encoding="utf-8")
    (target / "applications.jsonl").write_text('{"employer":"Demo"}\n', encoding="utf-8")

    res = run_init(str(target))
    assert res.returncode == 0
    assert (target / "profile.md").read_text(encoding="utf-8") == custom_profile
    assert (target / "applications.jsonl").read_text(encoding="utf-8") == '{"employer":"Demo"}\n'


def test_init_workspace_overwrites_with_force(tmp_path: Path) -> None:
    target = tmp_path / "my_ws"
    assert run_init(str(target)).returncode == 0

    (target / "profile.md").write_text("temporary custom text", encoding="utf-8")
    res = run_init(str(target), "--force")
    assert res.returncode == 0
    assert (target / "profile.md").read_text(encoding="utf-8") != "temporary custom text"
    assert "# Candidate Profile" in (target / "profile.md").read_text(encoding="utf-8")
