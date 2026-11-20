from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import fitz
import pytest

JOB_ROOT = Path(__file__).resolve().parent.parent
COVERLETTER_DIR = JOB_ROOT / "scripts" / "coverletter"
LINT_SCRIPT = COVERLETTER_DIR / "lint.py"
BUILD_SCRIPT = COVERLETTER_DIR / "build.py"

if str(COVERLETTER_DIR) not in sys.path:
    sys.path.insert(0, str(COVERLETTER_DIR))

import build as cl_build  # noqa: E402
import lint as cl_lint  # noqa: E402


def sample_rules() -> dict[str, Any]:
    return {
        "author_name": "Sample Candidate",
        "file_prefix": "Sample_Candidate_Cover_Letter",
        "confirmed_software": ["Python", "SQL"],
        "unconfirmed_software": ["MATLAB", "SolidWorks"],
        "forbidden_claims": [
            {"label": "Active license claim", "pattern": r"\blicensed\s+engineer\b"},
            {"label": "Citizenship claim", "pattern": r"\bU\.?S\.?\s+citizen\b"},
        ],
        "employer_order": ["Horizon Analytics", "Riverbend Systems"],
        "style": {
            "forbid_em_dash": True,
            "forbid_long_comma_lists": True,
            "max_pages": 1,
        },
        "employer_aliases": [],
    }


def sample_spec() -> dict[str, Any]:
    return {
        "employer": "Summit Tech",
        "role": "Operations Analyst",
        "req_id": "REQ-501",
        "date": "2026-03-01",
        "output_slug": "Summit_Tech_Operations_Analyst",
        "header": {
            "name": "Sample Candidate",
            "contact_line": "Denver, CO | candidate@example.com | +1-555-010-2020",
        },
        "recipient": {
            "name": "Hiring Team",
            "company": "Summit Tech",
            "location": "Denver, CO",
        },
        "salutation": "Dear Hiring Team,",
        "paragraphs": [
            "I am excited to apply for the Operations Analyst position at Summit Tech.",
            "At Horizon Analytics, I improved reporting accuracy across quarterly forecasting pipelines using Python and SQL.",
            "Earlier at Riverbend Systems, I coordinated process reviews and built clear dashboards for leadership.",
            "Thank you for your time and consideration. I look forward to discussing how I can contribute to Summit Tech.",
        ],
        "closing": "Sincerely,",
        "signature": "Sample Candidate",
    }


def test_lint_passes_valid_spec(tmp_path: Path) -> None:
    rules_path = tmp_path / "rules.json"
    spec_path = tmp_path / "spec.json"
    rules_path.write_text(json.dumps(sample_rules()), encoding="utf-8")
    spec_path.write_text(json.dumps(sample_spec()), encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(LINT_SCRIPT), str(spec_path), "--rules", str(rules_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr


def test_lint_catches_rule_violations() -> None:
    rules = sample_rules()
    spec = sample_spec()
    spec["header"]["name"] = "Wrong Name"
    spec["paragraphs"] = [
        "At Riverbend Systems I used MATLAB — and later at Horizon Analytics I became a licensed engineer.",
        "My work covered design, testing, and deployment across teams.",
    ]

    errors = cl_lint.lint_spec(spec, rules)
    joined = "\n".join(errors)
    assert "does not match rules.author_name" in joined
    assert "Unconfirmed software mentioned: 'MATLAB'" in joined
    assert "Forbidden claim triggered (Active license claim)" in joined
    assert "Employer order mismatch" in joined
    assert "Em dash" in joined
    assert "3+ item comma list" in joined


def test_build_init_and_overwrite_guard(tmp_path: Path) -> None:
    init_spec = tmp_path / "starter.json"
    res1 = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), "--init", str(init_spec)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res1.returncode == 0, res1.stderr
    assert init_spec.is_file()

    # Refuses overwrite without --overwrite
    res2 = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), "--init", str(init_spec)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res2.returncode != 0
    assert "Refusing to overwrite" in res2.stderr


def test_build_generates_one_page_pdf_qa_png_and_guards_overwrite(tmp_path: Path) -> None:
    rules_path = tmp_path / "rules.json"
    spec_path = tmp_path / "spec.json"
    out_root = tmp_path / "output"
    rules_path.write_text(json.dumps(sample_rules()), encoding="utf-8")
    spec_path.write_text(json.dumps(sample_spec()), encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            str(spec_path),
            "--rules",
            str(rules_path),
            "--out-root",
            str(out_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    pdf_path = Path(payload["pdf"])
    png_path = Path(payload["qa_png"])

    assert pdf_path.is_file()
    assert pdf_path.name == "Sample_Candidate_Cover_Letter_Summit_Tech_Operations_Analyst.pdf"
    assert png_path.is_file()
    assert payload["pages"] == 1

    with fitz.open(str(pdf_path)) as doc:
        assert doc.page_count == 1
        assert doc.metadata.get("author") == "Sample Candidate"

    # Second build without --overwrite fails
    res_dup = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            str(spec_path),
            "--rules",
            str(rules_path),
            "--out-root",
            str(out_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_dup.returncode != 0
    assert "Refusing to overwrite" in res_dup.stderr

    # Second build with --overwrite succeeds
    res_overwrite = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            str(spec_path),
            "--rules",
            str(rules_path),
            "--out-root",
            str(out_root),
            "--overwrite",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_overwrite.returncode == 0, res_overwrite.stderr


def test_build_enforces_one_page_limit(tmp_path: Path) -> None:
    rules_path = tmp_path / "rules.json"
    spec_path = tmp_path / "overflow.json"
    out_root = tmp_path / "output"
    rules_path.write_text(json.dumps(sample_rules()), encoding="utf-8")

    spec = sample_spec()
    long_para = " ".join(["This sentence verifies strict single-page PDF layout enforcement."] * 14)
    spec["paragraphs"] = [long_para for _ in range(10)]
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(BUILD_SCRIPT),
            str(spec_path),
            "--rules",
            str(rules_path),
            "--out-root",
            str(out_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode != 0
    assert "exceeding max_pages=1" in res.stderr


def test_register_fonts_falls_back_to_helvetica(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cl_build, "CALIBRI_CANDIDATES", ((Path("/nonexistent/calibri.ttf"), Path("/nonexistent/calibrib.ttf")),))
    assert cl_build.register_fonts() == ("Helvetica", "Helvetica-Bold")
