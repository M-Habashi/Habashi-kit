# Writing Style, Citations, Fresh Eyes & HTML Track Changes

Domain-agnostic prose, evidence, citation, and presentation rules for `Habashi-kit/writing`. Load this reference whenever drafting, revising, auditing citations, running Fresh Eyes, or rendering tracked-changes drafts.

---

## 1. Planning & Paragraph Craft

1. **Plan what the reader must understand.** Read the preceding passage, heading, following passage, equations, and figures. Identify the one specific question the paragraph must answer and outline the factual propositions in the order the reader needs them. Vague labels ("motivation", "method", "details") are insufficient—state what each step actually explains.
2. **Open with the next necessary step.** Enter from the preceding text and advance directly to the method, assumption, comparison, or result the argument needs next. Reconnect with the established technical name when referring to the whole framework or component. Avoid reopening an established topic with generic goals.
3. **Check every sentence's contribution and placement before polishing length.** Confirm what each sentence adds, what prior information makes it intelligible, and how it advances the paragraph's question. Establish the main operation or comparison before adding examples or settings. Never invent a reason or procedural detail just to connect two sentences.
4. **Given before new (Gopen & Swan).** Open each sentence with established information from the previous sentence and place the new contribution at the end. Keep the main subject and meaningful verb early (first-seven-words diagnostic), unpack strings of three or more stacked nouns, and aim for ~15–20 words per sentence (≤ 25 words ceiling in pipeline mode) without padding or over-compressing distinct ideas into one packed sentence.
5. **Impersonal technical voice.** Use impersonal engineering/academic prose (avoid first-person "we"/"our" and instructional imperatives like "Let $x$ be" or "Define" unless the target venue requires otherwise). Keep physical or computational components active when they perform the action. Preserve grammatical `"where"` continuations defining symbols after equations instead of changing them mechanically to `"Here"`.
6. **Clean punctuation and word discipline.**
   - Avoid colons (`:`) in prose sentences (split into connected sentences or use a comma/conjunction).
   - Avoid semicolons (`;`), `"whose"`, `"ideally"`, and suspended hyphens (write complete terms such as *"autospectra and cross spectra"*).
   - Avoid vague praise (`"accurate"`, `"effective"`, `"useful"`, `"efficient"`) when a specific mechanism, comparison, or metric is needed.
   - Use concise, consistent scientific names (give the full term once, then reuse one clear short name rather than inventing synonyms for variety or dropping to vague `"the method"`).
   - Preserve wording that already works clearly; do not rephrase merely for variety.
7. **Positive tone for this work, measured tone for prior work.**
   - Leave out limiting words like `"only"` about the study's own method unless technically required.
   - When explaining a gap in prior work, state factually what earlier studies did and what remains unaddressed—never use an aggressive tone.
   - Use neutral technical verbs (`"degrades"`, `"compromises"`, `"limits"`) rather than dramatic ones (`"sacrifices"`, `"destroys"`, `"abandons"`, `"kills"`).
8. **Protect equations and symbol definitions.** When simplifying prose, keep display equations in their existing format (do not merge or reformat them) and never drop symbol definitions. State at a high level what an equation combines or compares before showing it, and explain the purpose of a choice at the moment it appears.

---

## 2. Precision of Claims, Experiments & Figures

### Claim precision
- **Hedge only what is untested or conditional.** Measured or proven results stay definite (`"the margin fell to 0.34"`). Untested cases or conditional generalizations take `"can"` or `"may"` (`"a stiffer specimen can tolerate a higher gain"`).
- **Distinguish uncertain from unknown.** Something partly known, identified, or estimated is *"uncertain"* (state its degree if needed); reserve *"unknown"* for complete absence of information.
- **Name the observation behind a decision.** Replace vague *"available data"* or *"available signals"* with the actual measured quantity.
- **Avoid repeating modal frames** across neighboring sentences (`"must ... must ..."`).
- **Frame future work openly.** Write *"Future work can …"* rather than *"Future work will …"* so future directions stay open without implying a commitment by the authors.

### Reporting experiments and results
- Open each results subsection with what is applied and expected before giving outcomes.
- Report what supports the paper's argument; omit internal code/file names, routine test justifications, and minor settings that add no explanatory value.
- Round dimensions and reported quantities to the precision the argument needs, and state units consistently.
- Give section introductions a brief substantive overview of each major part/test and its purpose rather than a bare list of subsection numbers.
- Never refer to internal appendices in the manuscript body unless the target venue explicitly uses appendices as part of the main argument.

### Figures
- Describe every figure in the text **before** it appears, never after. Never open a section or subsection with a figure.
- Introduce the subject first, then point to the figure (*"The reference structure is shown in Figure X"*, not *"Figure X shows the test"*).
- State what a figure **plots** (which line/style represents which signal, what each subplot shows, what is observed, and why cases differ). Use *"subplot"* rather than *"panel"*.
- Keep legends boxed inside each subplot (one entry per line, naming only that subplot's lines). Keep full colors while pairing distinct line styles so curves remain distinguishable in grayscale.

### Interpreting author comments and edits
- Treat comment highlights as approximate pointers; judge the affected wording from the author's intent across the **full paragraph**, and write connected prose rather than pasting chat notes literally.
- When porting direct author edits, proofread grammar and spelling while keeping their words and meaning.

---

## 3. Original-Source Citations & Evidence Ledger

1. **Read the actual original source before citing.** Open the paper, PDF, or book chapter. Check its overview (abstract, introduction, conclusion) and verify technical claims in the method/results body. Trace general claims to the **oldest original source** that established them rather than a recent review. Never certify a mechanism, assumption, result, or limitation from a search snippet, abstract, or third-party summary. If a source cannot be accessed, flag it as unverified and withhold or narrow the claim.
2. **Default citation format.** Number citations by first appearance (`Author [n]` when part of the sentence, `[n]` otherwise; `"et al."` for three or more authors), unless the target journal specifies another style.
3. **Credit authors by name with verified attribution verbs.** Place the reference number beside the author's name with a verb matching verified content (`"introduced by"`, `"proposed by"`, `"presented by"`, `"derived by"`, `"discussed in"`, `"recommended by"`, `"found that"`, `"showed that"`). Avoid possessive forms like *"the estimator of Author [n]"*. Do not guess an attribution verb or claim someone was "first" without verification.
4. **Connect the cited contribution to the local analysis.** State (a) what the source established or supplied and (b) how this work uses it—either **our work first** (*"Each window is weighted by the Hann window presented by Author [n]"*) or **their work first** (*"Author [n] showed that [verified finding]; therefore, [method] is used here to [purpose]"*). Map unfamiliar source terminology to the manuscript's own terms so a reader understands the step without opening the reference.
5. **Order by lineage, avoid redundant citations.** Link related prior works by what each built on rather than artificial contrasts. After a named citation in a paragraph, refer back with *"They"* instead of repeating `"Author et al. [n]"` in neighboring sentences.
6. **Conclusions without citations (default).** Keep the Conclusions section free of citations (refer to prior findings in plain terms, e.g., *"Previous numerical studies showed …"*) unless your benchmark papers regularly cite in Conclusions.
7. **Maintain a per-paper `sources.md` ledger.** For each verified source record: author, title, year, DOI/URL, version/PDF read, sections actually read, a short exact quote with page/section, the supported claim, its local role, and any scope limitations.

---

## 4. Fresh Eyes (Cold Read)

When the author asks for **"Fresh Eyes"** on a passage, test whether a technical reader with zero prior context can follow it:

1. Spawn a fresh subagent that reads **no files** and runs **no searches**. Supply only the target passage and any equations it introduces, framed as part of a technical paper in that field.
2. Ask it to list numbered questions it needs answered, grouped under: (a) what the passage does at a high level, (b) what it combines or compares with what, (c) why each reference value or choice is made, (d) what problem it solves and what fails without it, (e) how the mechanism achieves it, and (f) vague words. It proposes **no rewrite**.
3. Drop questions already answered by earlier manuscript text; present the remaining questions to the author with plain answers and a tracked-changes draft that resolves them.
4. After the author agrees on the draft, offer a second Fresh Eyes pass to confirm the questions are resolved.

---

## 5. Presenting Drafts: HTML Track Changes

Never present prose revisions as sentence fragments, Markdown Before/After blocks, bold-only diffs, or comment-mapping tables. Show **every changed paragraph in full** with `<del>` / `<ins>` markup, flanked by unchanged greyed `<p class="context">` neighbors, using the self-contained HTML skeleton below (preview with `html_preview`, then publish with `html_render` if available):

- **Never set a fixed `background` or fixed dark `color` on `html`/`body`** so light and dark themes both stay legible.
- **Avoid stacked delete+insert on the same unchanged word** (e.g., `the <del>test </del>implementation<ins> procedure</ins>`, not `<del>test implementation</del><ins>implementation procedure</ins>`).
- **One marked-up copy per paragraph:** the `.clean` toggle hides only `<del>` elements; `<ins>` stays blue so new text remains easy to scan.

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
