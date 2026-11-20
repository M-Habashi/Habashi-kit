# Logging, Checkpoints & Parallel Coordination

## 1. Workspace Storage Layout

Keep all user runtime data inside `<workspace_dir>/` (never committed to git):

```text
<workspace_dir>/
├── profile.md                 # Extracted CV facts (read during runs)
├── answers.md                 # Reusable form Q&A (edit only with user approval)
├── rules.json                 # Lint, build, and alias rules
├── portals.md                 # Per-employer ATS portal notes
├── applications.jsonl         # Append-only source-of-truth ledger
├── log.md                     # Auto-rendered summary from applications.jsonl
├── docs/                      # Resume PDF + optional transcripts/licenses/samples
├── output/                    # Generated cover-letter PDFs & QA PNGs
└── evidence/<employer-slug>/  # Confirmation screenshots, receipt text, Sent proofs
```

## 2. Q&A Memory Update Approval Rule

When you encounter a question not covered by `answers.md`:
1. Ask the user for the answer (or park as `blocked` in batch mode).
2. After the user responds, prompt **once**:
   > *"Should I save this answer to your `answers.md` for future applications?"*
3. Update `answers.md` **only if the user explicitly says yes**. Never silently mutate `answers.md`.

## 3. Ledger States & Pre-Submit Checkpoint

`scripts/ledger/ledger.py` uses an append-only JSONL log (`applications.jsonl`) and renders `log.md`. Valid statuses:

| Status | Meaning | Counts as Verified? |
| --- | --- | --- |
| `reserved` | Claimed before opening/filling to prevent duplicate work | No |
| `submission_attempted` | **Required checkpoint recorded immediately before clicking final Submit** | No |
| `submitted_reported` | Worker reported submit click, awaiting independent receipt check | No |
| `verified` | Visible confirmation page, receipt ID, or Sent-mail proof verified | **Yes** |
| `blocked` | Needs user input, CAPTCHA, or unresolved login/blocker | No |
| `outcome_unknown` | Timeout/crash occurred around submit; must reconcile before retry | No |
| `skipped` | Duplicate or hard eligibility blocker identified early | No |

### Mandatory Final-Action Checkpoint
Right before clicking the final **Submit** button (or sending an official email application), record:
```bash
python job/scripts/ledger/ledger.py record --employer "<Employer>" --role "<Role>" --status submission_attempted --req "<ReqID>" --url "<URL>" --workspace <workspace_dir>
```
Only after seeing the visible confirmation receipt (or verified Sent message with attachments), record `verified` with `--receipt "<receipt text>"` and run `ledger.py render`.

## 4. Timeout & Crash Reconciliation

If a browser tab, tool call, or agent crashes or times out during or right after clicking Submit:
1. Record `outcome_unknown` immediately.
2. **Never blindly re-submit.** First verify whether the application went through by checking:
   - The employer portal's "My Applications" / candidate dashboard, and
   - The user's email inbox (confirmation email) or Sent folder (email-route applications).
3. Update the ledger to `verified` (if confirmed) or resume cleanly (if confirmed not submitted).

## 5. Parallel Multi-Agent Coordination

When running multiple workers in parallel on a batch of jobs:
1. **Single coordinator authority**: One coordinator owns `applications.jsonl` reservations, final submit clearance (`allowed: true`), and official verified counts.
2. **Reserve before work**: Workers never start an employer/req until the coordinator confirms `ledger.py check` exits `0` and records `reserved`.
3. **Final clearance gate**: Before clicking final Submit, a worker confirms with the coordinator that no duplicate was submitted concurrently (`allowed: true`), records `submission_attempted`, submits, and returns receipt evidence.
4. **Honest counting**: Only `verified` submissions count toward batch totals. Drafts, open tabs, CAPTCHA-blocked applications, recruiter outreach, and `outcome_unknown` records add **zero** to the verified count.
