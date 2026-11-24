---
name: habashi-kit-writing
description: Reusable, domain-agnostic academic and technical manuscript writing skill. Use when drafting, revising, auditing, or fixing review comments on research papers, abstracts, introductions, literature reviews, methods, results, or conclusions. Includes a reference-paper startup gate (>=3 reference papers converted from PDF to Markdown), a connected-paragraph drafting/checking pipeline, a dual-reviewer Reference-Paper Council, original-source citation verification, Fresh Eyes cold reads, and HTML track-changes draft review.
---

# Habashi-kit/writing

A domain-agnostic, progressive-disclosure workflow for drafting, revising, and auditing academic and technical manuscripts against reference papers from your target field and journal. Keep this file as your runbook and load `references/` files only when needed.

## Step 1: Startup Gate (Reference Papers First)

Before drafting, revising, or running the council on any paper:

1. **Locate the reference-papers folder.** Check `writing/reference_papers/` by default, or use a paper-specific `reference_papers/` folder if the user named one in their manuscript workspace.
2. **Require at least 3 reference papers.** Count the published reference papers (`.pdf` or `.md`) in that folder.
   - If **fewer than 3** papers are present, stop and ask the user to add at least **3** representative reference papers from their target journal or subfield before proceeding. Explain that these reference papers anchor tone, length, citation placement, and structure.
3. **Default PDF-to-Markdown conversion prompt.** Check whether every `.pdf` in `reference_papers/` has a matching clean `.md` file alongside it (or in a `md/` subfolder).
   - If any PDF lacks a `.md` file, **prompt the user by default** to convert the reference-paper PDFs into clean reading-order `.md` files before starting (column-aware extraction, e.g., PyMuPDF `fitz` block sorting, avoids scrambled two-column text when drafting or running the council).
   - Once the user agrees, convert the PDFs into clean `.md` files (preserving section headings and reading order) and verify that at least 3 readable `.md` files exist.
4. **Load per-paper context (if present).** If the user's paper workspace has a `preferences.md`, `sources.md`, or paper-context notes, read them before drafting. Once at least 3 clean `.md` reference papers are ready, confirm that the workspace is ready to go.

## Modes & Commands

| User says / asks | You do |
| --- | --- |
| **Draft or revise a passage** (default) | Gather neighbors, equations, figures, and verified facts; follow `references/style-and-citations.md`; run a quick contextual reviewer subagent on the draft in context; present a full-paragraph HTML track-changes draft for author approval. |
| **Use the pipeline** (or project default) | Run the full 4-stage connected-paragraph pipeline in `references/pipeline-and-council.md` (Manager brief → Drafter → independent Checker → Manager fact-check). Skip when the user says **"no pipeline"**. End every reply that used it with: *"Used the connected-paragraph pipeline. To skip it, say 'no pipeline' in your prompt next time."* |
| **Run the council** | Run the independent dual-reviewer Reference-Paper Council in `references/pipeline-and-council.md` against all `.md` files in `reference_papers/`. Reconcile supported findings and report both ratings side by side. |
| **Draft Abstract / Intro & Literature / Conclusions** | Load the matching section blueprint in `references/pipeline-and-council.md` alongside `references/style-and-citations.md`. |
| **"Fresh Eyes"** | Run the zero-context cold-read subagent protocol in `references/style-and-citations.md` §4. |
| **Handle review comments or author edits** | Interpret intent across each full affected paragraph, draft connected prose, proofread any direct author edits for grammar/spelling while keeping their meaning, and present full-paragraph HTML track changes. |
| **Audit the manuscript** | Check the complete manuscript for cross-section contradictions (numbers, units, symbols, figure/table mismatches, missing roadmap links, overclaimed results, equation/diagram mismatches) and report concrete findings before editing. |

## Model & Effort Selection

Do **not** hardcode model names or silently choose models on the user's behalf:

- **Prompt the user before delegating:** Whenever a workflow uses subagents (pipeline Drafter & Checker, Council reviewers, literature researcher, or optional independent reviewer) and the user has not already specified models and effort in the prompt or `preferences.md`, ask the user which **model(s) and reasoning effort** they want for each role.
- **Role separation:**
  - **Main agent (Manager):** Gathers context and ground-truth data, writes briefs (never dictating individual sentences), fact-checks revisions against actual code/data/figures, reconciles checker and council feedback, and presents drafts to the author.
  - **Drafter & Independent Checker:** Run as separate fresh subagents using the user-selected model and effort; the Checker stays blind to the Drafter's notes and link table.
  - **Reference-Paper Council:** Runs two independent parallel reviewers using the user-selected model(s) and effort (typically two distinct models/providers if available), each blind to the other and to drafter/checker notes.
  - **Literature research & optional independent review:** Run with the user-selected model and effort.
- **Availability rule:** If a user-chosen model or provider is unavailable, say so clearly and ask the user how to proceed—never silently substitute another model.

## Author-Review Gate & Draft Presentation

1. **Never edit manuscript source files before explicit approval.** Draft the exact proposed wording in chat first and wait for confirmation, except when the author gives an unambiguous single-item deletion or asks to undo an earlier edit.
2. **Present full-paragraph HTML track changes.** Render every proposed prose revision as a self-contained HTML page (`html_preview` → `html_render` when available; clean inline fallback otherwise) using the skeleton in `references/style-and-citations.md` §5:
   - Manuscript serif typography, inheriting the host theme background (never hardcode a white or dark page background on `html`/`body`).
   - Deleted words in red `#901500` with strikethrough (`<del>`); inserted words in blue `#007CA8` with underline (`<ins>`).
   - Double-click toggle between tracked view and clean view (hiding deletions only while keeping insertions blue so new words stay visible).
   - Every changed paragraph shown in full, flanked by the unchanged preceding and following paragraphs as greyed context (`<p class="context">`).
   - Never substitute sentence fragments, Markdown Before/After blocks, bold-only diffs, or comment-mapping tables.
3. **Plain-English locations in chat.** Always name manuscript locations by section, paragraph, figure, or equation (e.g., *"the closing paragraph of Section 3.1"*), never by raw source line links as sentence subjects.

## Learning Author Preferences

Maintain a per-paper `preferences.md` (in the paper's working folder, outside git when using a shared skill repo). Whenever the author corrects wording, tone, structure, or workflow:

1. Infer the underlying preference and why (ask briefly if unclear; flag any contradiction with an earlier preference before acting).
2. Apply the fix, then record the preference concisely in `preferences.md` with **Why** and a short `before → after` example (merging into an existing point when closely related).

## Non-Negotiable Grounding Rules

- **Verify computational and experimental truth against primary sources** (code, data, tables, figures)—never invent a number, cause, or procedural detail to make prose flow.
- **Read original references before citing.** Never verify a mechanism, result, or limitation from a search snippet, abstract, or third-party summary.
- **Protect equations and symbol definitions.** When simplifying prose, keep display equations intact and never drop symbol definitions unless the author asks.
- **Zero personal or private data in git.** Keep reference-paper PDFs/MDs, `preferences.md`, and `sources.md` out of version control unless the user explicitly commits them to their own private manuscript repository.

## On-Demand Reference Routing

Load only the reference file needed for your current step:

| When You Need To... | Read This Reference |
| --- | --- |
| Apply prose craft and general transition rules, claim precision, hedging, figure/experiment reporting, original-source citation rules, Fresh Eyes, or copy the HTML track-changes skeleton | `references/style-and-citations.md` |
| Run the connected-paragraph pipeline (strict transition rules, link tables, Drafter & Checker), convene the Reference-Paper Council (5 comparison categories), run an optional independent review, or follow Abstract / Intro-Lit / Conclusions blueprints | `references/pipeline-and-council.md` |
