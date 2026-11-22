# Habashi-kit

**Habashi-kit** is a modular collection of ready-to-use, domain-agnostic AI agent skills built for progressive disclosure, deterministic local tooling, and zero hardcoded personal data.

## Available Skills

| Skill | Path | Description |
| --- | --- | --- |
| **Habashi-kit/job** (`habashi-kit-job`) | `job/` | End-to-end job-search and job-application skill with startup preflight checks, browser/tool readiness detection, Q&A memory updates, duplicate-safe JSONL logging, tailored 1-page PDF cover-letter generation, and ATS playbooks. |

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
   - Fill out `workspace/profile.md`, `workspace/answers.md`, and `workspace/rules.json`.
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

## Repository Map

```text
Habashi-kit/
├── AGENTS.md                       # Contributor & agent guidelines
├── README.md                       # Project overview and quickstart
├── logo.svg                        # Project icon
├── t3.json                         # T3 project metadata
├── .gitignore                      # Excludes workspace/, caches, node_modules/
├── LICENSE                         # MIT
└── job/                            # Habashi-kit/job skill
    ├── SKILL.md                    # Lean entry point & routing table
    ├── references/                 # On-demand playbooks & guardrails
    │   ├── onboarding.md
    │   ├── browser-and-tools.md
    │   ├── ats-playbooks.md
    │   ├── form-and-truthfulness.md
    │   ├── logging-and-parallel.md
    │   └── rendering.md            # Rendered cards (HTML) or plain-text fallback
    ├── templates/                  # Clean starter files for user workspaces
    │   ├── profile.md
    │   ├── answers.md
    │   ├── rules.json
    │   ├── credentials.md
    │   └── cover-letter-spec.json
    ├── scripts/                    # Deterministic CLI & browser helpers
    │   ├── init_workspace.py
    │   ├── ledger/ledger.py
    │   ├── render/render.py        # preflight | tools | ledger | card -> HTML or text
    │   ├── render/toolcheck.py     # BrowserOS Neo + Codex computer-use checks
    │   ├── coverletter/
    │   │   ├── lint.py
    │   │   └── build.py
    │   └── neo/
    │       ├── package.json
    │       ├── emit.mjs
    │       ├── jobs.mjs
    │       └── lib/ (core.js, icims.js, paylocity.js, aaim.js, yello.js)
    └── tests/                      # Automated pytest suite
```

## Verification

```bash
python -m pytest -q job/tests
node job/scripts/neo/emit.mjs --list
```

## License

MIT. See [LICENSE](LICENSE).
