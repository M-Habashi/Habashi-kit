# Writing Style, Transition Rules, Citations, Fresh Eyes & HTML Diff

Single source of truth for prose craft, sentence/paragraph transitions, claim precision, citations, Fresh Eyes cold reads, and HTML track-changes formatting in `Habashi-kit/writing`.

---

## 1. Planning, Transitions & Paragraph Craft

A paragraph is an argument, not a list of facts. Every sentence takes what the reader already holds and advances the paragraph's question.

### Structure & transitions (applies to every draft and checked strictly in pipeline mode)
1. **Reader question & proposition chain.** Read the heading, preceding/following paragraphs, equations, and figures. Identify the one question the paragraph answers and outline the factual propositions in the order the reader needs them (state what each step explains—never vague labels like "motivation" or "details"). Name the logical relation between every consecutive proposition: *because*, *therefore*, *so (that)*, *but / however*, *which means*, *for example*, *then* (sequence), or *to do this* (purpose). *"Also"*, *"in addition"*, *"another"*, and parallel lists (*"X shows A. Y shows B."*) are not relations—reorder, merge, or drop unrelated points.
2. **Given before new & strict antecedents.** Open each sentence with established information from the previous sentence and end with the new contribution (Gopen & Swan). Words such as *"this"*, *"these"*, *"the same"*, and *"the first"* require an explicit prior antecedent—repeating a noun alone is not a link.
3. **Entry & exit handoffs.** Open from the preceding text (unless starting an independent section such as Conclusions) and close by stating why the reader needs what immediately follows. Never jump ahead to a later section or close by restating a shared setting. When opening a section followed by a setup subsection, close with a brief ordered roadmap grounded in the paragraph's last point rather than an invented causal *"so"*.
4. **One relation per sentence & length.** Keep main subject and meaningful verb early (first-seven-words diagnostic), unpack strings of 3+ stacked nouns, and target ~15–20 words (**≤ 25 words ceiling** in pipeline mode). Split sentences carrying two relations at the second relation; never pad or over-compress unrelated ideas into packed sentences.
5. **Swap & bare-`"and"` test.** If two adjacent sentences can trade places without loss of logic, merge them with an explicit relation or rewrite one to depend on the other. Apply the same test to clauses joined by a bare *"and"*.
6. **True causes only.** For every *"so"*, *"therefore"*, *"because"*, and *"thus"*, verify the stated cause is the real physical or logical cause. A design choice relates to an expected effect by purpose (*"to test"*, *"to counter"*), not as its cause.
7. **Promise only what follows.** Any claim about a later test or section must match what that section actually delivers. State expected outcomes as expected, never as findings.

### Voice, wording & equations
- **Impersonal academic voice:** Avoid first-person *"we/our"* and instructional imperatives (*"Let x be"*, *"Define"*) unless the target venue requires otherwise. Keep physical/computational components active when they perform the action. Preserve grammatical *"where"* continuations after equations instead of changing them mechanically to *"Here"*.
- **Punctuation & word bans:** No colons (`:`) in prose sentences, no semicolons (`;`), no `"whose"`, no `"ideally"`, no suspended hyphens (write full terms like *"autospectra and cross spectra"*), and no vague praise (*"accurate"*, *"effective"*, *"useful"*) in place of a mechanism or metric.
- **Tone & register:** Positive tone for this work (omit limiting `"only"` on own method unless technically required); measured, factual tone for gaps in prior work; neutral technical verbs (*"degrades"*, *"compromises"*) instead of dramatic ones (*"sacrifices"*, *"destroys"*, *"abandons"*, *"kills"*).
- **Consistent scientific names & minimal churn:** Define the full term once, then reuse one clear short name (never invent synonyms for variety or drop to vague *"the method"*). Preserve clear, approved wording rather than rephrasing for variety.
- **Protect equations & definitions:** When simplifying prose, keep display equations intact (do not merge/reformat) and never drop symbol definitions. State at a high level what an equation combines or compares before showing it, and explain the purpose of a choice where it appears.

---

## 2. Precision of Claims, Experiments, Figures & Comments

- **Hedge precisely:** Keep measured or verified results definite; hedge only untested or conditional claims (*"can"*, *"may"*). Distinguish *"uncertain"* (partially known/estimated) from *"unknown"* (no information). Name the actual observed signal behind a decision rather than vague *"available data"*. Avoid repeating the same modal frame across neighboring sentences. Frame future directions openly (*"Future work can …"*, not *"Future work will …"*).
- **Experiments & results:** Open each results subsection with what is applied and expected before reporting outcomes. Give section introductions a brief substantive overview of each major part/test and its purpose. Omit internal file/code names, unjustified minor settings, and appendix references in the main body unless the venue requires them. Keep units consistent and precision appropriate to the argument.
- **Figures:** Describe every figure in text **before** it appears; never start a section or subsection with a figure. Introduce the subject first, then cite the figure, and state what it **plots** (signals, line styles, subplots, observations, reasons for differences). Use *"subplot"* rather than *"panel"*, boxed per-subplot legends (one line per entry), and full colors paired with distinct line styles for grayscale legibility.
- **Author comments & edits:** Treat highlight bounds as approximate—apply the author's intent across the full paragraph in connected prose (never paste chat notes literally). Proofread direct author edits for grammar and spelling while keeping their words and meaning.

---

## 3. Original-Source Citations & Evidence Ledger

1. **Read the actual original source before citing.** Inspect the paper, PDF, or book chapter (overview plus relevant method/results body). Trace general claims to the **oldest original source**, not recent reviews. Never verify a mechanism, assumption, result, or limitation from a search snippet, abstract, or third-party summary. If unavailable, flag as unverified and withhold or narrow the claim.
2. **Format & attribution.** Default to numbered-by-first-appearance (`Author [n]` in text, `[n]` parenthetically, `"et al."` for 3+ authors) unless the target journal specifies otherwise. Credit authors by name with a verified verb matching the source (*"introduced by"*, *"proposed by"*, *"presented by"*, *"derived by"*, *"showed that"*, *"found that"*)—never possessive (*"the method of Author [n]"*) and never guess a verb or claim priority without verification.
3. **Connect to local use.** State both what the source established and how this paper uses it (either *our work first* or *their work first*), mapping unfamiliar source jargon into the manuscript's own terms so a reader needs no external paper to follow the step. Order related citations by lineage rather than artificial contrasts, and use *"They"* after a named citation in the same paragraph instead of repeating `"Author et al. [n]"`.
4. **Source ledger (`sources.md`).** Maintain a local per-paper ledger recording author, title, year, DOI/URL, version read, sections actually read, short exact quote with page/section, supported claim, local role, and scope limits.

---

## 4. Fresh Eyes (Cold Read)

When the author asks for **"Fresh Eyes"** on a passage:

1. Spawn a fresh subagent (user-chosen model/effort) with **no file access and no searches**, supplying only the passage and its equations as part of a technical paper.
2. Ask for numbered questions it needs answered, grouped under: (a) high-level purpose, (b) what is combined or compared, (c) why each reference value/choice exists, (d) what problem it solves and what fails without it, (e) how the mechanism works, and (f) vague words. **No rewrite.**
3. Drop questions already answered earlier in the manuscript; present the rest with plain answers and a tracked-changes draft.
4. Offer a second Fresh Eyes pass on the agreed draft to verify the questions are gone.

---

## 5. HTML Track-Changes Presentation

Show every changed paragraph **in full** inside a self-contained HTML page (preview with `html_preview`, publish with `html_render` when available; inline fallback otherwise):
- Inherit host theme colors (never hardcode `background` or fixed dark `color` on `html`/`body`).
- Serif `.paper` typography; deletions in red `#901500` strikethrough (`<del>`); insertions in blue `#007CA8` underline (`<ins>`).
- Double-click toggles `.clean`, hiding only `<del>` while keeping `<ins>` blue.
- Flank each changed paragraph with its unchanged preceding and following paragraphs as greyed `<p class="context">`.
- Avoid stacked delete+insert on the same unchanged word (e.g., `the <del>test </del>implementation<ins> procedure</ins>`).

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Revision draft</title>
<style>
  :root { --ins: #007ca8; --del: #901500; --paper-ink: var(--foreground); }
  @media (prefers-color-scheme: dark) {
    :root { --ins: #5cc3e6; --del: #ef7b6a; }
  }
  html, body { margin: 0; color: var(--foreground); }
  body { padding: 8px 12px 24px; }
  .paper {
    font-family: "STIX Two Text", Cambria, "Times New Roman", serif;
    font-size: 10.5pt; line-height: 1.48; max-width: 44em; color: var(--paper-ink);
  }
  .paper p { margin: 0 0 7pt; text-align: justify; hyphens: auto; cursor: pointer; }
  .paper p.context { color: var(--muted-foreground); opacity: 0.72; cursor: default; }
  .paper h2 { font-size: 12pt; font-weight: 700; margin: 14pt 0 6pt; color: var(--foreground); }
  .paper .meta {
    font: 9pt/1.4 var(--font-sans, system-ui, sans-serif);
    color: var(--muted-foreground); margin-bottom: 12px; text-align: left; cursor: default;
  }
  .paper ins { color: var(--ins); text-decoration: underline; text-decoration-thickness: 1px; }
  .paper del { color: var(--del); text-decoration: line-through; }
  .paper .clean del { display: none; }
  button {
    font: 13px var(--font-sans, system-ui, sans-serif); margin-bottom: 10px; padding: 5px 10px;
    color: var(--foreground); background: var(--secondary, #eee);
    border: 1px solid var(--border, #ccc); border-radius: var(--radius, 6px); cursor: pointer;
  }
</style>
</head>
<body>
<button type="button" onclick="document.querySelectorAll('.paper p[data-toggle]').forEach(p=>p.classList.toggle('clean'))">Toggle all: tracked / clean</button>
<div class="paper">
<p class="meta">Section X revision — double-click a paragraph to toggle tracked / clean.</p>
<p class="context">Preceding unchanged paragraph…</p>
<p data-toggle>Full revised paragraph with <del>removed</del><ins>added</ins> wording…</p>
<p class="context">Following unchanged paragraph…</p>
</div>
<script>
document.querySelectorAll('.paper p[data-toggle]').forEach(p => p.addEventListener('dblclick', () => {
  p.classList.toggle('clean');
  window.getSelection().removeAllRanges();
}));
</script>
</body>
</html>
```
