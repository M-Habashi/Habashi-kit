# ATS Playbooks & Neo Script Helpers

Use `job/scripts/neo/emit.mjs` to generate self-contained async snippets for BrowserOS Neo `run`, and `job/scripts/neo/jobs.mjs` to query public Workday and iCIMS boards directly without browser overhead.

## 1. CLI Quick Reference

### List and Emit Neo Helpers
```bash
node job/scripts/neo/emit.mjs --list
node job/scripts/neo/emit.mjs acceptCookies --page 0
node job/scripts/neo/emit.mjs icimsPickMany --page 2 --args '[[["field_name","query","Exact Option"]]]'
```

### Fast Public Job Board Discovery (`jobs.mjs`)
Requires `pnpm --dir job/scripts/neo install` (installs `jsdom`).
```bash
node job/scripts/neo/jobs.mjs workday <host.myworkdayjobs.com> <tenant> <site> "<query>" --filter "<regex>" --json
node job/scripts/neo/jobs.mjs icims <host.icims.com> "<query>" --filter "<regex>" --json
```

## 2. Cookie Banners

Always dismiss cookie banners early so they do not intercept clicks or cover submit buttons:
- Use `acceptCookies(p)` — prioritizes `#onetrust-accept-btn-handler` and visible accept/agree buttons while explicitly avoiding `reject`, `decline`, `necessary only`, `settings`, or `preferences`.

## 3. Platform-Specific Playbooks

### Workday (`*.myworkdayjobs.com`)
- Discover open postings rapidly with `jobs.mjs workday` before opening browser tabs.
- Reuse saved per-employer Workday credentials from `portals.md` (each company has an isolated tenant login).
- Autofill-from-resume often scrambles employment order or dates — always inspect every parsed Work Experience and Education block and fix discrepancies against `profile.md`.
- Wait for dynamic dropdown menus and multi-step "Save and Continue" validation banners to settle before clicking Next.

### iCIMS (`*.icims.com`)
- Most form controls live inside a same-origin iframe (`iframe[src*="icims.com"]` / `#icims_content_iframe`).
- Inspect visible fields first with `icimsDump(p)`.
- Set standard inputs, checkboxes, radios, and native `<select>` elements with `icimsSetNative(p, { fieldName: value })` (dispatches bubbling `input` and `change` events using the iframe's `defaultView.Event`).
- For searchable iCIMS dropdowns (`*_icimsDropdown`), use `icimsPick(p, name, query, exact)` or batch them with `icimsPickMany(p, triples)`:
  - Waits `1800ms` after typing the query for results to render and `800ms` after clicking the exact option, then verifies `selectedOptions[0]`.
  - `icimsPickMany` enforces a **24-second batch budget** (`24000ms`) and returns `{ done, remaining }` so long forms never hit Neo script timeouts — simply call again with `remaining`.

### Paylocity (`recruiting.paylocity.com`)
- Custom React Widgets comboboxes (`li[role=option].rw-list-option`) can silently revert if clicked too fast.
- Use `payPick(p, comboRef, exactText)` — clicks the combobox, clicks the visible option by exact text, waits `600ms`, and **verifies the updated value in an interactive snapshot**.
- On the final review screen, run `payReviewCheck(p, expectedLabelToValue)` to catch dropped answers before submitting.

### AAIM (`*.aaimtrack.com` / AAIM portals)
- Fill labeled textboxes with `aaimFill(p, { "Label": "Value" })` — uses `p.fill` (never raw value assignment) and requires an exact 1-to-1 label match.
- **Avoid clicking duplicate `Upload Files` buttons**: AAIM pages can contain multiple `Upload Files` buttons across forms. Use `aaimUpload(p, filePath)`, which targets `#default_resume` and scopes the click strictly to `form#upload_resume`, then waits until the filename appears next to a `button.delete[data-id]`.
- To replace a wrong attachment, use `aaimDeleteAttachment(p, matchText)` — handles native `confirm()` deletion dialogs via `p.dialogAccept()` and verifies the attachment ID disappears.

### Yello (`*.yello.co`)
- Yello uses `react-select` comboboxes that ignore direct `.value = ...` writes.
- Use `yelloPick(p, comboLabel, query, exact)` — locates the unique combobox by label, clears via `HTMLInputElement.prototype` native value setter + bubbling `input` event, inserts text, locates options via the focused input's `aria-controls` listbox, clicks the exact match, and verifies `[class*=singleValue]`.

### Paycor (`recruiting.paycor.com`)
- Inspect actual labels around file inputs before attaching: IDs like `#uploadResumeInput`, `#transcript`, and `#coverLetter` can be misleading or mismatched relative to visible sections.
- Verify every uploaded filename appears visibly under the intended document label before advancing.
