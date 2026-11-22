# Rendering Skill Output

Every structured report this skill produces is **rendered by default** when the host can show HTML inline, and falls back to **plain text** when it cannot. `scripts/render/render.py` does all formatting deterministically, so the agent only supplies data.

## 1. Detect the Renderer Once per Session

Check your available tools at preflight (Step 1B) and remember the result:

| Host capability | Mode | How to show a report |
| --- | --- | --- |
| Inline HTML render tool (e.g. T3 Code `html_render`, or any tool that displays an HTML file/string inside the chat) | `html` | `render.py ... --out <workspace>/output/render/<name>.html`, then pass that absolute path to the render tool with a short title |
| No inline renderer (plain terminal, API, chat without HTML display) | `text` | `render.py ... --format text`, then paste the output verbatim (inside a plain ``` fence when the host renders Markdown, so the columns stay aligned) |

- Page publishers (artifacts, canvases, docs connectors) are **not** inline renderers. Use them only when the user asks for a shareable report.
- If the render tool errors, retry once, then fall back to `text` for the rest of the session.
- After rendering, **do not restate the card in prose**. Your reply should only add what the card does not say: the next action or a question.
- In batch mode, overwrite the same file names for each job, for example `submit-gates.html`, so `output/render/` stays small.

## 2. What Gets Rendered

| Moment | Command / payload |
| --- | --- |
| Step 1 startup gate (tools, then documents) | `render.py preflight --workspace <ws> --fix --live --neo-agent ok` (exit `2` = blocker → resolve first). Apps only: `render.py tools --fix --live --neo-agent ok`. One line per app; text appears only when the user must do something, written in plain words |
| Early blocker / skip notice | `card` with a `kv` block (requirement vs. profile) and an info `note`; see `examples/blocker.json` |
| Pre-submit gate check (Step 2.5) | `card` with one `checklist`; see `examples/submit-gates.json` |
| Post-submit review (Step 2.6) | `card` with receipt `kv`, uploaded-files `list`, Q&A `table`, blank-fields `list`; see `examples/submission-review.json` |
| Batch summary / needs-your-input list | `card` with a `table` (a `Status` column becomes pills); see `examples/batch-summary.json` |
| Application history | `render.py ledger --workspace <ws>` |

Plain text stays plain in every mode: a single question, the "save to `answers.md`?" prompt, one-line progress updates. Rendering a single sentence adds nothing.

## 3. Payload Format (`card`)

```json
{
  "title": "Ready to submit?",
  "subtitle": "Employer - Role (REQ-ID)",
  "badge": "optional pill text", "tone": "success | warning | danger | info | muted",
  "blocks": [
    {"type": "checklist", "heading": "optional", "items": [{"label": "...", "status": "ok", "detail": "optional"}]},
    {"type": "kv", "rows": [["Key", "Value"]]},
    {"type": "table", "columns": ["Employer", "Status"], "rows": [["...", "verified"]]},
    {"type": "list", "items": ["..."]},
    {"type": "note", "tone": "warning", "text": "..."}
  ]
}
```

- Checklist statuses: `ok`, `missing`, `blocked`, `warn`, `pending`, `optional`, `skipped`. All ledger statuses (`verified`, `submitted`, `submission_attempted`, `outcome_unknown`, ...) also map to colored pills.
- Without `badge`, the header pill is computed from the checklist items: `N missing`, `N to check`, or `Ready`.
- Write the payload to a temp file (or pipe it with `card -`). `--json` on `preflight`/`ledger` prints the payload so you can add blocks before rendering it with `card`.
- All values are HTML-escaped. Put only real data in payloads; never put personal data in the repo's `examples/`.

## 4. Styling Contract

The HTML uses the host's theme variables (`--foreground`, `--muted-foreground`, `--card`, `--border`, `--success`, `--destructive`, `--warning`, `--info`, `--radius`, `--font-sans`) when they exist. Without them it falls back to its own light and dark palettes (AA contrast), chosen by `prefers-color-scheme` or a host `data-theme="dark"|"light"` / `.dark` / `.light` on the root, and it declares `color-scheme: light dark` so a standalone file opened in a browser gets a matching page background. It sets no page background or outer frame, and the layout works at phone width (tables scroll horizontally). Don't hand-write HTML for these reports; extend `render.py` when a new block type is needed.
