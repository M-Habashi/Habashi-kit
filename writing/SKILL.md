---
name: habashi-kit-writing
description: Reusable, domain-agnostic academic and technical manuscript writing skill. Use when drafting, revising, auditing, or fixing review comments on research papers, abstracts, introductions, literature reviews, methods, results, or conclusions. Includes a reference-paper startup gate (>=3 reference papers converted from PDF to Markdown), a connected-paragraph drafting/checking pipeline, a dual-reviewer Reference-Paper Council, original-source citation verification, Fresh Eyes cold reads, and HTML track-changes draft review.
---

# Habashi-kit/writing

Domain-agnostic workflow for drafting, revising, and auditing academic and technical manuscripts against reference papers from your target field and journal. Keep this file as your runbook; load files from `references/` only when needed.

## Step 1: Startup Gate (Reference Papers First)

Before drafting, revising, or running the council:

1. **Locate reference papers.** Check `writing/reference_papers/` by default, or a paper-specific `reference_papers/` folder named by the user.
2. **Require at least 3 reference papers.** If fewer than 3 published papers (`.pdf` or `.md`) exist there, stop and ask the user to add at least **3** representative papers from their target journal or subfield before proceeding.
3. **Default PDF-to-Markdown prompt.** If any `.pdf` lacks a matching clean `.md` file, prompt the user by default to convert the PDFs into reading-order `.md` files (column-aware extraction, e.g., PyMuPDF `fitz` block sorting, avoids scrambled two-column text). Once converted and at least 3 readable `.md` files exist, confirm ready to go.
4. **Load per-paper notes (if present).** Read any local `preferences.md`, `sources.md`, or paper-context notes in the manuscript workspace.

## Modes & Reference Routing

| Task / Trigger | Action & Reference to Load |
| --- | --- |
| **Draft or revise prose** (default) | Gather neighbors, equations, figures, and verified facts; follow `references/style-and-citations.md` (§1–§3); run a contextual reviewer subagent on the draft in context; present HTML track changes (§5). |
| **Review comments or author edits** | Interpret intent across each full paragraph, proofread direct author edits while preserving meaning (`references/style-and-citations.md` §2), and present HTML track changes (§5). |
| **"Fresh Eyes"** | Run the zero-context cold-read protocol in `references/style-and-citations.md` §4. |
| **Use the pipeline** (or project default) | Run the 4-stage connected-paragraph pipeline in `references/pipeline-and-council.md` §1. Skip when the user says **"no pipeline"**. End every reply that used it with: *"Used the connected-paragraph pipeline. To skip it, say 'no pipeline' in your prompt next time."* |
| **Run the council** | Run the dual-reviewer Reference-Paper Council in `references/pipeline-and-council.md` §2 against all `.md` files in `reference_papers/` and report both ratings side by side. |
| **Independent review** | Offer or run the blind single-agent audit in `references/pipeline-and-council.md` §3. |
| **Draft Abstract / Intro & Lit / Conclusions** | Combine `references/pipeline-and-council.md` §4 with `references/style-and-citations.md`. |
| **Audit the manuscript** | Check the full manuscript for cross-section contradictions (numbers, units, symbols, figures/tables, roadmap links, overclaims, diagram/equation mismatches) and report findings before editing. |
| **Set up the review website** | Copy `writing/review-template/` into the user's paper folder; edit `.agent/build_manuscript.py`, run `python .agent/build_manuscript.py "note"` to publish a new version, check edits/comments with `python .agent/review_status.py`, and serve via `python .agent/review_server.py` (or `.agent/share_review.ps1` for a public link). |

## Core Gates

1. **Model & effort selection:** Never hardcode or silently choose subagent models. Before delegating any subagent role (Drafter, Checker, Council reviewer, literature researcher, or independent reviewer), prompt the user for the **model(s) and reasoning effort** unless already specified in the prompt or `preferences.md`. If a chosen model is unavailable, say so and ask—never silently substitute another.
2. **Author approval before manuscript edits:** Never modify manuscript source files until the author explicitly confirms the draft (except unambiguous single-item deletions or undo requests). Present every proposed prose change as full-paragraph HTML track changes with greyed before/after context (`references/style-and-citations.md` §5)—never Markdown diffs or comment tables.
3. **Plain-English locations in chat:** Name manuscript locations by section, paragraph, figure, or equation, never by raw source line links as sentence subjects.
4. **Grounding & privacy:** Verify every number, claim, and equation against primary data/code/figures (never invent details for flow). Keep local reference PDFs/MDs, `preferences.md`, and `sources.md` out of git unless the user commits them to a private paper repo.
5. **Learn author preferences:** When the author corrects style, wording, or workflow, infer why (ask briefly if unclear; flag contradictions before acting), apply the fix, and log the generalized rule in the paper's `preferences.md` with **Why** and a short `before → after` example.
