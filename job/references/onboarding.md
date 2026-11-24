# Onboarding & Workspace Setup

Use this guide during first-time setup or whenever the user updates their resume, preferences, or reusable answers.

## 1. Initialize Workspace Structure

Create a private workspace directory (kept outside git, e.g. `workspace/`):

```bash
python job/scripts/init_workspace.py <workspace_dir>
```

This creates:
- `profile.md` — Structured facts extracted from the user's CV/resume.
- `answers.md` — Reusable form answers, authorization wording, salary rule, EEO defaults, and saved custom Q&A.
- `rules.json` — Deterministic lint/build/dedupe rules (author name, file prefix, confirmed/unconfirmed software, forbidden claims, employer order, employer aliases, style checks).
- `credentials.md` — Portal accounts the agent creates or reuses (username + password per employer).
- `preferences.md` — How the user likes the agent to work, saved from their corrections (only after a yes).
- `cover-letter-spec.json` — Starter spec for `scripts/coverletter/build.py`.
- `docs/`, `evidence/`, `output/pdf/`, and an empty `applications.jsonl`.

`init_workspace.py` never overwrites existing files unless `--force` is passed.

## 2. Preflight Document Checklist

Confirm required files before running applications, and ask whether optional items apply:

### Required
- **Resume / CV PDF** saved in `<workspace_dir>/docs/` (keep filename clean, e.g. `First_Last_Resume.pdf`).
- **Core profile facts** (`profile.md`): full name, email, phone, city/state/ZIP, LinkedIn URL, education (school, degree, dates, exact GPA and scale), work history in preferred CV order, and confirmed skills/software.
- **Core answers** (`answers.md`): work authorization & sponsorship wording, earliest start date / availability, salary expectation rule, target roles, target locations / relocation stance, companies to prefer or avoid, and EEO preference (disclose or decline).
- **Configured `rules.json`**: update `author_name`, `file_prefix`, `confirmed_software`, `unconfirmed_software`, `forbidden_claims`, `employer_order`, and `employer_aliases`.

### Optional (Ask If Applicable)
- Certifications or professional licenses (with exact exam/registration status and dates).
- Unofficial or official academic transcripts (PDF in `docs/`).
- Existing cover-letter template or writing samples.
- Professional references (only include when explicitly requested by a portal).
- Portfolio, GitHub, publications, or work sample PDFs/URLs.

## 3. CV-to-`profile.md` Extraction Rule

1. On initial onboarding (or whenever the user supplies a new CV PDF), extract all facts accurately into `<workspace_dir>/profile.md`.
2. Preserve the user's exact **CV employment order**, exact job titles, dates, metrics, degree titles, and GPA scale.
3. During subsequent job runs, **read `profile.md` instead of re-parsing the CV PDF** to save tokens and keep facts consistent.
4. Reopen the raw CV PDF only when:
   - Uploading the PDF file to an ATS, or
   - Refreshing `profile.md` after the user provides a newer resume version.

## 4. Configuring `rules.json`

Update `<workspace_dir>/rules.json` so automated checks catch mistakes before submission:
- `author_name`: exact name used in cover-letter header, signature, and PDF metadata.
- `file_prefix`: filename prefix for generated cover letters (e.g., `First_Last_Cover_Letter`).
- `confirmed_software`: tools the candidate genuinely uses.
- `unconfirmed_software`: common tools in the candidate's industry that the candidate has **not** confirmed (triggers a lint error if accidentally claimed).
- `forbidden_claims`: list of `{"label": "...", "pattern": "..."}` regex rules catching untrue claims (e.g., claiming an active state license when only an exam was passed, or claiming citizenship when on a visa).
- `employer_order`: ordered list of employers matching the user's CV order so cover letters narrate roles consistently.
- `employer_aliases`: array of alias lists (e.g., `[["Acme Engineering", "Acme Corp", "Acme"]]`) so `ledger.py check` catches duplicates across brand variants.

## 5. Confirming the Search Plan

Before the first job search, `render.py next` returns `confirm_search` with a card listing target roles, places / work mode, and companies to prefer or avoid (from `answers.md`). Fill what you can from the resume first, so the user only confirms or corrects.
- User says it looks good: write today's date (`YYYY-MM-DD`) into `Search Plan Confirmed On`.
- User changes something: update those `answers.md` fields, then show the card again.
- User says "change my search" later: clear the date and repeat.
