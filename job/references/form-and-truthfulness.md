# Form Accuracy, Truthfulness & Cover-Letter Standards

## 1. Core Truthfulness Guardrails

- **Never fabricate or embellish facts**: do not invent licenses, certifications, software proficiency, employers, dates, citizenship, or unrestricted work authorization.
- **Never convert GPA across scales** unless the user explicitly provides an official converted value in `profile.md` (e.g., do not convert a 10-point or 100-point GPA to a 4.0 scale on your own; treat incompatible required GPA scales as a blocker or ask the user).
- **Never assume HR will fix a wrong checkbox**: if a required dropdown or radio question has no truthful option that fits the candidate, stop and ask the user (or mark `blocked`) rather than picking an inaccurate proxy.

## 2. Wording-Sensitive Exceptions Table

Read question wording carefully — small phrasing differences flip the truthful answer:

| Topic | Wording Pattern A | Wording Pattern B | Rule |
| --- | --- | --- | --- |
| **Exam vs License** | *"Have you passed the [FE/Bar/CPA/etc.] exam?"* | *"Do you hold an active [state] registration/license?"* | Never answer **Yes** to active registration/licensure based solely on passing a qualifying exam. Check `profile.md` for exact credential status. |
| **Sponsorship & Work Auth** | *"Will you now or in the future require sponsorship for employment visa status?"* | *"Are you authorized to work in [Country] (including F-1 CPT/OPT/STEM OPT)?"* | Follow the exact wording rules in `answers.md`. Distinguish current work authorization (e.g., OPT/CPT/EAD) from future visa sponsorship (e.g., H-1B), and never claim unrestricted permanent work authorization unless confirmed. |
| **Degree Status** | *"Expected graduation date / degree in progress"* | *"Have you already completed / conferred a [Degree]?"* | Never mark an in-progress degree as already conferred when the prompt explicitly requires a completed degree at time of application. |

## 3. Learnable-Software Rule

- Missing a specific tool or software listed in a job description **never automatically disqualifies** an otherwise strong role match.
- Claim **only** tools listed under `confirmed_software` in `rules.json` / `profile.md`. Never claim tools in `unconfirmed_software`.
- In cover letters and open-text responses, emphasize confirmed adjacent tools and fast ramp-up positively — **without volunteering negative gaps** (do not write *"Although I have not used Tool X..."*).

## 4. Employment Order

- Preserve the user's **preferred CV employment order** (`employer_order` in `rules.json` and `profile.md`) in forms and cover letters, unless an ATS portal forces automatic chronological sorting by date.

## 5. Cover-Letter Structure & Writing Hygiene

### 6-Part Narrative Structure
1. **Role fit & opening**: State the exact role, employer, and immediate value fit clearly.
2. **Concrete work experience (in CV order)**: Highlight measurable work outcomes matching the role, ordered consistently with `employer_order`.
3. **Academic / project evidence**: Connect relevant thesis, coursework, lab, or portfolio project outcomes.
4. **Direct skill & tool match**: Map confirmed tools/methods directly to the job posting's core deliverables.
5. **Unique value-add**: Explain why this specific team/company's domain or projects align with the candidate.
6. **Concise closing**: Reiterate availability, enthusiasm, and call to action cleanly.

### Writing Hygiene (Enforced by `scripts/coverletter/lint.py` & `build.py`)
- **No em dashes (`—`)** or double-hyphen em-dash substitutes (`--`).
- **No 3+ item comma-separated lists** (e.g., avoid `"A, B, and C"` runs that read like keyword stuffing; group cleanly into tight phrases or pairs).
- **Strictly 1 page**: verify page count = 1 via PyMuPDF and inspect the rendered QA PNG for balanced margins and zero overflow/clipping.
- Never overwrite an existing generated PDF without explicit `--overwrite`.

## 6. Official Email-Route Applications

Use email submission **only** when the official employer job posting explicitly instructs applicants to email their application:
1. Verify the official recipient email address, required subject line format, and required attachments directly from the employer posting.
2. Attach the resume PDF (and tailored cover letter / requested docs) and confirm every attachment is present before sending.
3. After sending, verify the message appears in the user's **Sent** folder with the exact recipient, subject, and attached filenames before recording `verified` in the ledger and saving evidence.
