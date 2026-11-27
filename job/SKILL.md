---
name: habashi-kit-job
description: Reusable, domain-agnostic job-search and job-application skill for non-technical job seekers. Use when the user says "start", "what's next", "next", "continue", or asks to find or apply for jobs. Startup app/document checks, Q&A memory, duplicate-safe logging, 1-page tailored cover letters, and ATS playbooks.
---

# Habashi-kit/job

A structured, progressive-disclosure workflow for discovering roles, filling ATS forms truthfully, generating tailored 1-page cover letters, and recording verified submissions. Keep this file as your runbook and load files from `references/` only when needed.

## The User Is Not Technical

Users are job seekers, not programmers. In everything you say to them:
- Use plain words. No commands, file names, code, or terms like MCP, CLI, JSON, or plugin.
- Do every technical step yourself: run scripts, edit `profile.md`/`answers.md`/`rules.json`, set up tools, open apps. Never ask the user to run a command or edit a file.
- Ask the user only for what only they can do: share documents, answer questions about themselves, install an app, sign in, open or reopen an app. Give one short step at a time.
- Fill as much as you can from their resume first, then ask only for what's still missing.

## Simple Commands

The user only needs to say a few words. Workspace: `workspace/` unless the user named another folder.

| User says | You do |
| --- | --- |
| **"start"** | Create the workspace if missing (`init_workspace.py`), run the Step 1 startup gate, then continue as for "what's next". |
| **"what's next"**, **"next"**, **"continue"** | `python job/scripts/render/render.py next --workspace <workspace_dir> --neo-agent <ok\|error:msg> --json` → show its card, then do its `action` right away: `fix_browser` (Step 1A), `share_resume` (ask for the PDF), `fill_from_resume` (fill profile/settings yourself, `references/onboarding.md`), `ask_answers` (plain questions → `answers.md`), `answer_waiting` / `finish_open` (resume those applications), `confirm_search` (show the plan card; on "looks good" write today's date into `Search Plan Confirmed On` in `answers.md`; on changes, update `answers.md` and show the plan again), `find_jobs` (search with that plan, show a short list to approve, then Step 2 for each approved job). |
| **"status"**, **"my applications"** | `render.py ledger --workspace <workspace_dir>` card. |
| **"change my search"** | Clear `Search Plan Confirmed On`, then do `confirm_search`. |

**End every reply with a recommendation**: one plain line saying what you recommend doing next and why, e.g. *"Next I recommend checking your search plan, so I only apply where you want. Reply "next" to go ahead."* Do this after every message, not only finished steps. If there are two sensible paths, recommend one and name the other in a few words.

## Reporting a Job

After each job ends **filled** (stopped before Submit), **blocked**, or **submitted**, report it in two parts:
1. **The card**: `render.py job --status filled|blocked|submitted --id "<listing ID>" --title "<job title>" --employer "<employer>" --location "<city, state>" --url "<posting>" --out <workspace_dir>/output/render/job.html`, shown as in Output Rendering. It is one numbered line: number, ID, status, company, position, date and time (`Nov, 26 - 23:58`). Several jobs: one `card` payload with one `job` block each; they stack into one numbered table.
   - **This template is fixed.** Always produce it with `render.py job` or `job` blocks. Never hand-write it or change its columns, order, colors or date format. Only the user can ask for a new design; then update `tests/golden/` with it.
2. **Points under it**: as few as possible (zero is fine), one short line each, only these kinds:
   - **Need from you**: information you can't continue without. Ask nothing else.
   - **Assumed**: choices you made that the profile, answers or the user's request didn't spell out.
   - **Heads-up**: anything that could change the user's mind: a requirement gap, pay, location, a red flag, a fix needed before submitting.

   Then the "Done by" line and your recommended next step. Never restate the card or list what went as expected.

When you hand a job to a helper, ask it to return these points; you render the card. A hand-off message never replaces this format.

## When the User Corrects You

Whenever the user corrects a fact, an answer, a choice you made, or how you work: fix it now, then ask once, in plain words, *"Should I remember this for next time?"*, naming the place in plain words ("your profile", "your standard answers"). Save only after a yes. Skip the question when the user says the change is just for this one job, or the same fact is already saved. You pick the file:

| The correction is about... | Save it in |
| --- | --- |
| Facts about them: contact details, education, jobs, dates, skills | `profile.md` ("your profile") |
| How to answer a form question, targets, places, companies, salary, authorization | `answers.md` ("your standard answers") |
| Cover-letter wording, tools they have or don't, claims never to make, employer names or order | `rules.json` ("your cover-letter settings") |
| How you should work: tone, how much to ask, which jobs to skip, habits | `preferences.md` ("your preferences") |
| A portal login | `credentials.md` + the browser's saved passwords (no need to ask) |
| How a website or the kit works for everyone, with no personal details | The matching `references/` file ("my notes on that website") |

If it fits two places, save it in the more specific one. If none fits, use `preferences.md`.

## Output Rendering (Default for Every Report)

Show structured output (checklists, blocker notices, gate checks, reviews, batch summaries, the ledger) as a **rendered card**, never as hand-formatted Markdown:
- **Inline HTML render tool available** (e.g. `html_render`): `python job/scripts/render/render.py <preflight|ledger|card payload.json> --out <workspace_dir>/output/render/<name>.html`, then render that path. Don't restate the card in prose.
- **No inline renderer**: add `--format text` and paste the plain-text output verbatim.
- Single questions and one-line updates stay plain text. Payload format and examples: `references/rendering.md`.

## Step 1: Startup Gate (Always Run First, Tools Before Documents)

Before opening job portals, drafting materials, or submitting anything:
1. Call Neo `tabs` with action `list` yourself. That's the only check the script can't do for you.
2. Run one command. It checks the apps first, then the documents. `--fix` first does every fix it can by itself (opens BrowserOS, starts the Cua Driver, sets up helper tools):
   ```bash
   python job/scripts/render/render.py preflight --workspace <workspace_dir> --fix --live --neo-agent <ok|error:message> --out <workspace_dir>/output/render/preflight.html
   ```
   If the workspace doesn't exist yet, run `python job/scripts/init_workspace.py <workspace_dir>` first.
3. The card has **one line per required tool**: the browser (BrowserOS Neo), the desktop helper (Cua Driver), and helper tools. A line shows text only when something is wrong, and that text is already a plain-language step for the user. If everything is ready, show the card and move on. Otherwise show it and ask for the first step only. Exit code `2` means a blocker (the browser isn't usable, or required documents are missing): resolve it before anything else. `render.py tools --fix` rechecks just the apps.

### 1A. Tools: Browser vs. OS Computer Use
1. **Browser = BrowserOS Neo, always.** Do all web work in Neo: pages, forms, uploads, tabs, and saved passwords. Don't switch to another browser.
   - If Neo can't be reached or a call errors, check and debug it (is BrowserOS running, does the MCP answer, retry).
   - Not installed: stop and ask the user to install BrowserOS Neo.
   - Installed but closed or broken: use the Cua Driver to open or fix it, then continue in Neo.
2. **Desktop helper = Cua Driver** ([github.com/trycua/cua](https://github.com/trycua/cua), open source, works with any agent). Required next to BrowserOS Neo. Use it for windows outside the web page: sign-in pop-ups (e.g. LinkedIn "Authorize"), native dialogs, opening or fixing BrowserOS. One window, one step, then back to Neo. Details: `references/browser-and-tools.md` §3.
   - Not installed: install it yourself with the official command from its GitHub README (Windows: `irm https://cua.ai/driver/install.ps1 | iex`), then `cua-driver doctor`.
   - Use it as an MCP server (`cua-driver mcp`) or from the shell (`cua-driver call <tool> '<json>'`).
   - If it can't be used, fall back to PowerShell (`references/browser-and-tools.md` §3). Ask the user only if that also fails.
3. **Who does the work**: whoever takes a task completes it end to end, including pop-ups and OS-level steps; never hand part of a task to another agent. A helper agent may take a whole task (one application, one job search) at reasoning effort high and standard speed unless the user asks otherwise. Report every finished task in one plain line, "Done by <model> (<effort>, <speed>)", adding "sent by <model>" if it was handed over, and record the same with `--done-by`/`--sent-by` in the ledger. Details: `references/browser-and-tools.md` §3.
4. **Helper tools**: Python `reportlab` + `pymupdf` for cover letters; Node.js packages for `scripts/neo/`. `--fix` installs them; only a missing Node.js needs the user.
5. **Renderer**: note whether an inline HTML render tool exists. This sets `html` or `text` mode for the whole session (see Output Rendering above).

### 1B. Documents & Profile
The preflight card inspects the workspace (`workspace/` by default) for you:
1. **Required**: Resume / CV PDF in `docs/`; `profile.md` (contact info, links, education with exact GPA/scales, work history in CV order, confirmed skills); `answers.md` (work authorization & sponsorship wording, start date, salary rule, target roles/locations); `rules.json` (author name, file prefix, software lists, forbidden claims, employer order, aliases).
2. **Preferences**: `preferences.md` holds how the user likes you to work. Read it at the start of every session and follow it.
3. **Optional (ask if applicable)**: certifications or licenses, transcripts, references or a cover-letter template, portfolio/GitHub/work samples.
4. If required items are missing, ask for the resume first, fill everything you can from it yourself, then ask plain questions for the rest. Extract CV facts once into `profile.md` (see `references/onboarding.md`). During normal runs, read `profile.md` instead of re-parsing the PDF; reopen the PDF only for uploads or profile updates.

## Step 2: Core Workflow (Single Job or Batch)

Follow this exact sequence for each target role:

### 1. Duplicate Check First
Before opening a form or drafting anything, check the workspace ledger:
```bash
python job/scripts/ledger/ledger.py check "<Employer>" --req "<ReqID>" --workspace <workspace_dir>
```
- Exit code `1` means a `submitted` or `verified` record already exists (including configured aliases or matching req ID) — skip to avoid duplicate applications.
- Exit code `0` means safe to proceed; reserve or log status as needed (see `references/logging-and-parallel.md`).

### 2. Early Blocker Check (Before Drafting a Cover Letter)
Read the full job description and knockout questions first. Check for hard blockers before spending tokens on a tailored cover letter:
- Citizenship, security clearance, or unrestricted work authorization the candidate does not hold.
- Mandatory active license/registration the candidate does not hold.
- Hard GPA scale or degree requirement that cannot be truthfully met.
- Note the **learnable-software rule**: missing a listed software tool never disqualifies an otherwise strong fit — never claim unconfirmed tools, and see `references/form-and-truthfulness.md`.
If a hard blocker exists, record `skipped` or `blocked` with reason and move on.

### 3. Complete Form Accurately & Q&A Memory Loop
If the portal needs an account, look in `<workspace_dir>/credentials.md` and the browser's saved passwords first. If none exists, you are allowed to create a new account. Save its username and password in **both** `credentials.md` and the password manager of the browser you are using (BrowserOS Neo: `credentials` action `add`), so future runs and the user's own manual sign-ins can reuse it. See `references/browser-and-tools.md` §6.

Fill every field strictly from `profile.md` and `answers.md`. Never fabricate licenses, dates, GPAs, employers, or skills, and never assume HR will fix a wrong checkbox.
- **When an unanswered question appears**:
  - Single-job mode: ask the user concisely and wait for their answer.
  - Bulk/batch mode: leave the tab intact (place in a `Needs your input` group if supported), record `blocked` with the exact question, and continue to the next job.
- **After the user answers a new question**, ask once:
  > *"Should I save this answer to your `answers.md` for future applications?"*
  Never silently edit `answers.md` without explicit user permission.

### 4. Tailored 1-Page Cover Letter (When Requested or Offered)
When the portal asks for or accepts a cover letter (and early blockers are cleared):
1. Author a role-specific JSON spec based on `templates/cover-letter-spec.json`.
2. Lint and build via:
   ```bash
   python job/scripts/coverletter/lint.py <spec.json> --rules <workspace_dir>/rules.json
   python job/scripts/coverletter/build.py <spec.json> --rules <workspace_dir>/rules.json --out-root <workspace_dir>/output
   ```
3. Inspect the rendered QA PNG to verify clean 1-page visual layout before uploading.

### 5. Non-Negotiable Submission Gates
Do not click final **Submit** until every applicable gate passes (render them as a checklist card, `references/rendering.md`):
- [ ] Resume / CV PDF is visibly attached in the portal UI (attach even when marked optional).
- [ ] LinkedIn URL (and portfolio/GitHub if configured) is entered whenever offered.
- [ ] Tailored cover letter is attached when requested or offered.
- [ ] All visible required fields, dropdowns, and review-page values are verified accurate.
- [ ] Pre-submit checkpoint (`submission_attempted`) is recorded in `applications.jsonl` immediately before clicking Submit.
- [ ] Post-submit confirmation receipt (confirmation page text, requisition number, or confirmation email) is visibly verified.

### 6. Post-Submission Logging, Review & Cleanup
1. Record `verified` with confirmation receipt/URL in the ledger and re-render `log.md`:
   ```bash
   python job/scripts/ledger/ledger.py record --employer "<Employer>" --role "<Role>" --status verified --req "<ReqID>" --url "<URL>" --receipt "<Receipt>" --done-by "<model (effort, speed)>" --sent-by "<model>" --workspace <workspace_dir>
   python job/scripts/ledger/ledger.py render --workspace <workspace_dir>
   ```
2. Save confirmation screenshot/text evidence under `<workspace_dir>/evidence/<employer-slug>/`.
3. Report it as in **Reporting a Job** above.
4. Safely close completed confirmation tabs one at a time after verifying live URL/title. **Never close unfinished, blocked, or unverified tabs.**

## On-Demand Reference Routing

Load only the reference file relevant to your current step:

| When You Need To... | Read This Reference |
| --- | --- |
| Run first-time setup, extract CV into `profile.md`, configure `answers.md` / `rules.json`, or confirm the search plan | `references/onboarding.md` |
| Debug or fix BrowserOS Neo, use OS computer use, decide who does the work, create or reuse portal accounts, handle iframe uploads, or manage tabs | `references/browser-and-tools.md` |
| Automate Workday, iCIMS, Paylocity, AAIM, Yello, Paycor, cookie banners, or run `scripts/neo/emit.mjs` & `jobs.mjs` | `references/ats-playbooks.md` |
| Render a checklist, blocker notice, gate check, review, batch summary, or ledger (HTML or plain-text fallback) | `references/rendering.md` |
| Apply truthfulness rules, wording exceptions, learnable-software framing, CV order, cover-letter structure, or email-route applications | `references/form-and-truthfulness.md` |
| Manage ledger states, checkpoints, crash/timeout reconciliation, or coordinate parallel subagents | `references/logging-and-parallel.md` |
