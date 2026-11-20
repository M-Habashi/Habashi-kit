#!/usr/bin/env python3
"""Build a 1-page cover-letter PDF and QA PNG preview from a JSON spec + rules.json."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import fitz  # PyMuPDF
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lint import lint_spec, load_json, load_rules  # noqa: E402

TEMPLATE_SPEC = SCRIPT_DIR.parent.parent / "templates" / "cover-letter-spec.json"

CALIBRI_CANDIDATES = (
    (Path("C:/Windows/Fonts/calibri.ttf"), Path("C:/Windows/Fonts/calibrib.ttf")),
    (Path("/Library/Fonts/Calibri.ttf"), Path("/Library/Fonts/Calibri Bold.ttf")),
    (Path("/usr/share/fonts/truetype/msttcorefonts/Calibri.ttf"), Path("/usr/share/fonts/truetype/msttcorefonts/Calibrib.ttf")),
)


def register_fonts() -> tuple[str, str]:
    """Use Calibri when installed on the host OS, otherwise fall back gracefully to Helvetica."""
    for regular_path, bold_path in CALIBRI_CANDIDATES:
        if regular_path.is_file() and bold_path.is_file():
            try:
                if "Calibri" not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont("Calibri", str(regular_path)))
                if "Calibri-Bold" not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont("Calibri-Bold", str(bold_path)))
                return "Calibri", "Calibri-Bold"
            except Exception:
                break
    return "Helvetica", "Helvetica-Bold"


def sanitize_slug(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", text.strip())
    return cleaned.strip("_") or "Cover_Letter"


def resolve_output_paths(spec: dict[str, Any], rules: dict[str, Any], out_root: Path) -> tuple[Path, Path]:
    prefix = sanitize_slug(str(rules.get("file_prefix", "") or "Cover_Letter"))
    slug_source = (
        str(spec.get("output_slug", "")).strip()
        or f"{spec.get('employer', '')}_{spec.get('role', '')}".strip("_")
    )
    slug = sanitize_slug(slug_source)
    stem = f"{prefix}_{slug}"
    pdf_path = out_root / "pdf" / f"{stem}.pdf"
    png_path = out_root / "qa" / f"{stem}.png"
    return pdf_path, png_path


def render_pdf(spec: dict[str, Any], rules: dict[str, Any], pdf_path: Path) -> str:
    """Render the cover letter to pdf_path and return the regular font name used."""
    font_regular, font_bold = register_fonts()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    header = spec.get("header", {})
    author_name = str(header.get("name") or rules.get("author_name") or "").strip()
    contact_line = str(header.get("contact_line", "")).strip()
    recipient = spec.get("recipient", {})

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=f"{author_name} - {spec.get('employer', '')} Cover Letter".strip(" -"),
        author=author_name,
    )

    name_style = ParagraphStyle(
        "HeaderName",
        fontName=font_bold,
        fontSize=15,
        leading=18,
        textColor=HexColor("#0f172a"),
        spaceAfter=2,
    )
    contact_style = ParagraphStyle(
        "HeaderContact",
        fontName=font_regular,
        fontSize=9.5,
        leading=12.5,
        textColor=HexColor("#475569"),
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "Meta",
        fontName=font_regular,
        fontSize=10.5,
        leading=14,
        textColor=HexColor("#1e293b"),
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName=font_regular,
        fontSize=10.5,
        leading=14.5,
        textColor=HexColor("#0f172a"),
        spaceAfter=9,
    )
    sig_style = ParagraphStyle(
        "Signature",
        fontName=font_bold,
        fontSize=10.5,
        leading=14,
        textColor=HexColor("#0f172a"),
    )

    story: list[Any] = []
    if author_name:
        story.append(Paragraph(escape(author_name), name_style))
    if contact_line:
        story.append(Paragraph(escape(contact_line), contact_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#cbd5e1"), spaceAfter=12))

    date_str = str(spec.get("date", "")).strip()
    if date_str:
        story.append(Paragraph(escape(date_str), meta_style))
        story.append(Spacer(1, 6))

    for key in ("name", "company", "location"):
        val = str(recipient.get(key, "")).strip()
        if val:
            story.append(Paragraph(escape(val), meta_style))

    role = str(spec.get("role", "")).strip()
    req_id = str(spec.get("req_id", "")).strip()
    if role:
        subject = f"Re: {role}" + (f" ({req_id})" if req_id else "")
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>{escape(subject)}</b>", meta_style))

    story.append(Spacer(1, 10))

    salutation = str(spec.get("salutation", "Dear Hiring Team,")).strip()
    story.append(Paragraph(escape(salutation), body_style))

    for para in spec.get("paragraphs", []):
        text = str(para).strip()
        if text:
            story.append(Paragraph(escape(text), body_style))

    closing = str(spec.get("closing", "Sincerely,")).strip()
    signature = str(spec.get("signature") or author_name).strip()
    story.append(Spacer(1, 4))
    story.append(Paragraph(escape(closing), body_style))
    if signature:
        story.append(Paragraph(escape(signature), sig_style))

    doc.build(story)
    return font_regular


def verify_and_render_qa(pdf_path: Path, png_path: Path, max_pages: int) -> int:
    """Enforce max_pages via PyMuPDF and render page 1 to a QA PNG."""
    with fitz.open(str(pdf_path)) as doc:
        page_count = doc.page_count
        if page_count > max_pages:
            raise ValueError(
                f"Generated PDF has {page_count} pages, exceeding max_pages={max_pages}."
            )
        png_path.parent.mkdir(parents=True, exist_ok=True)
        pix = doc[0].get_pixmap(dpi=150)
        pix.save(str(png_path))
    return page_count


def init_spec_file(dest: Path, overwrite: bool = False) -> Path:
    if dest.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing spec without --overwrite: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if TEMPLATE_SPEC.is_file():
        shutil.copyfile(TEMPLATE_SPEC, dest)
    else:
        starter = {
            "employer": "Example Company",
            "role": "Example Role",
            "date": "2026-01-15",
            "output_slug": "Example_Company_Example_Role",
            "header": {"name": "Your Name", "contact_line": "City, State | email@example.com"},
            "recipient": {"name": "Hiring Team", "company": "Example Company", "location": "City, State"},
            "salutation": "Dear Hiring Team,",
            "paragraphs": ["Replace with tailored cover-letter paragraphs."],
            "closing": "Sincerely,",
            "signature": "Your Name",
        }
        dest.write_text(json.dumps(starter, indent=2) + "\n", encoding="utf-8")
    return dest


def build_cover_letter(
    spec_path: Path,
    rules_path: Path | None,
    out_root: Path,
    overwrite: bool = False,
    skip_lint: bool = False,
) -> dict[str, Any]:
    spec = load_json(spec_path)
    rules = load_rules(rules_path)

    if not skip_lint:
        errors = lint_spec(spec, rules)
        if errors:
            raise ValueError("Lint failed:\n" + "\n".join(f"- {e}" for e in errors))

    pdf_path, png_path = resolve_output_paths(spec, rules, out_root)
    if pdf_path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing PDF without --overwrite: {pdf_path}")

    font_used = render_pdf(spec, rules, pdf_path)
    max_pages = int(rules.get("style", {}).get("max_pages", 1))
    try:
        page_count = verify_and_render_qa(pdf_path, png_path, max_pages=max_pages)
    except Exception:
        if pdf_path.exists():
            pdf_path.unlink()
        raise

    return {
        "pdf": str(pdf_path),
        "qa_png": str(png_path),
        "pages": page_count,
        "font": font_used,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a 1-page cover-letter PDF and QA PNG.")
    parser.add_argument("spec", nargs="?", type=Path, help="Path to cover-letter JSON spec.")
    parser.add_argument("--init", type=Path, default=None, help="Create a starter cover-letter JSON spec at this path.")
    parser.add_argument("--rules", type=Path, default=None, help="Path to rules.json.")
    parser.add_argument("--out-root", type=Path, default=Path("output"), help="Output root directory (creates pdf/ and qa/).")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing PDF or spec files.")
    parser.add_argument("--skip-lint", action="store_true", help="Skip lint checks before building.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.init is not None:
            created = init_spec_file(args.init, overwrite=args.overwrite)
            print(f"Created starter spec: {created}")
            return 0
        if args.spec is None:
            print("ERROR: Provide a spec path or use --init <path>.", file=sys.stderr)
            return 2
        result = build_cover_letter(
            spec_path=args.spec,
            rules_path=args.rules,
            out_root=args.out_root,
            overwrite=args.overwrite,
            skip_lint=args.skip_lint,
        )
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
