# Habashi-kit

**Habashi-kit** is a modular collection of ready-to-use, domain-agnostic AI agent skills built for progressive disclosure, deterministic local tooling, and zero hardcoded personal data.

## Available Skills

| Skill | Path | Description |
| --- | --- | --- |
| **Habashi-kit/job** (`habashi-kit-job`) | `job/` | End-to-end job-search and job-application skill with startup preflight checks, browser/tool readiness detection, Q&A memory updates, duplicate-safe JSONL logging, tailored 1-page PDF cover-letter generation, and ATS playbooks. |
| **Habashi-kit/writing** (`habashi-kit-writing`) | `writing/` | Domain-agnostic academic and technical manuscript writing skill with a benchmark-paper startup gate (`>=3` reference papers converted from PDF to Markdown), connected-paragraph drafting/checking pipeline, dual-model Benchmark Council (Opus + newest Sol), original-source citation rules, Fresh Eyes cold reads, and HTML track-changes draft review. |

## Quickstart (`Habashi-kit/job`)

0. **Get the kit**:
   ```bash
   git clone https://github.com/M-Habashi/Habashi-kit.git
   cd Habashi-kit
   ```
1. **Initialize a private user workspace** (kept outside git via `.gitignore`):
   ```bash
   python job/scripts/init_workspace.py workspace
   ```
2. **Add your documents & profile**:
   - Place your resume/CV PDF (and optional transcripts, licenses, or portfolio PDFs) in `workspace/docs/`.
   - Fill out `workspace/profile.md`, `workspace/answers.md`, and `workspace/rules.json`. `workspace/preferences.md` collects how you like the agent to work.
3. **Optional local tooling dependencies**:
   - **Cover-letter PDF + PNG QA builder** (Python): `reportlab` and `pymupdf` (`fitz`).
   - **ATS board discovery & Neo script helpers** (Node.js):
     ```bash
     pnpm --dir job/scripts/neo install
     node job/scripts/neo/emit.mjs --list
     ```
4. **Check readiness** (tools first, then documents; `--live` runs a read-only Codex computer-use test):
   ```bash
   python job/scripts/render/render.py preflight --workspace workspace --fix --live --format text
   ```
   Requirements: BrowserOS Neo for all browser work; for OS-level steps, Codex CLI **plus the Codex desktop app running** with its computer-use plugin.
5. **Point your AI agent at `job/SKILL.md`** and run your first job search or application. The skill uses BrowserOS Neo for all browser work and OS computer use (Codex Computer Use by default) only for tasks outside the browser.

## Quickstart (`Habashi-kit/writing`)

1. **Add at least 3 benchmark papers** from your target journal or subfield into `writing/reference_papers/` (gitignored so PDFs and extracted `.md` files stay local), or point the agent to your paper workspace's `reference_papers/` folder.
2. **Point your AI agent at `writing/SKILL.md`**. On startup, the skill verifies that at least 3 reference papers exist and prompts you to convert their PDFs into clean reading-order `.md` files.
3. **Draft, revise, or audit** any section—use `"pipeline"` for the Manager → Opus Drafter → independent Opus Checker workflow, `"council"` for dual-model grading (Opus + newest Sol) against your benchmark papers, or `"Fresh Eyes"` for a zero-context cold read.

## Repository Map

```text
Habashi-kit/
├── README.md                       # Project overview and quickstart
├── logo.svg                        # Project icon
├── t3.json                         # T3 project metadata
├── .gitignore                      # Excludes workspace/, writing/reference_papers/*, caches
├── LICENSE                         # MIT
├── job/                            # Habashi-kit/job skill
│   ├── SKILL.md                    # Lean entry point & routing table
│   ├── references/                 # On-demand playbooks & guardrails
│   │   ├── onboarding.md
│   │   ├── browser-and-tools.md
│   │   ├── ats-playbooks.md
│   │   ├── form-and-truthfulness.md
│   │   ├── logging-and-parallel.md
│   │   └── rendering.md            # Rendered cards (HTML) or plain-text fallback
│   ├── templates/                  # Clean starter files for user workspaces
│   │   ├── profile.md
│   │   ├── answers.md
│   │   ├── rules.json
│   │   ├── credentials.md
│   │   ├── preferences.md
│   │   └── cover-letter-spec.json
│   ├── scripts/                    # Deterministic CLI & browser helpers
│   │   ├── init_workspace.py
│   │   ├── ledger/ledger.py
│   │   ├── render/render.py        # preflight | tools | ledger | card -> HTML or text
│   │   ├── render/toolcheck.py     # BrowserOS Neo + Codex computer-use checks
│   │   ├── agents/codex_task.py    # Hand a task to the newest Codex Sol model (no T3 Code needed)
│   │   ├── coverletter/
│   │   │   ├── lint.py
│   │   │   └── build.py
│   │   └── neo/
│   │       ├── package.json
│   │       ├── emit.mjs
│   │       ├── jobs.mjs
│   │       └── lib/ (core.js, icims.js, paylocity.js, aaim.js, yello.js)
│   └── tests/                      # Automated pytest suite
└── writing/                        # Habashi-kit/writing skill
    ├── SKILL.md                    # Lean entry point, startup gate & routing table
    ├── references/                 # On-demand style, citation, pipeline & council guides
    │   ├── style-and-citations.md
    │   └── pipeline-and-council.md
    └── reference_papers/           # Local folder for >=3 benchmark paper PDFs/MDs (gitignored)
        └── .gitkeep
```

## Verification

```bash
python -m pytest -q job/tests
node job/scripts/neo/emit.mjs --list
```

## License

MIT. See [LICENSE](LICENSE).
