# Pipeline, Reference-Paper Council & Section Blueprints

Multi-agent execution workflows, reference-paper comparison categories, and section blueprints for `Habashi-kit/writing`. All prose, transition, and citation rules live in `references/style-and-citations.md`—follow them throughout without duplicating them here. Prompt the user for model(s) and effort per `SKILL.md` before launching subagents.

---

## 1. Connected-Paragraph Pipeline

Use when requested (or set as project default); skip on **"no pipeline"**.

### 4 stages
1. **Manager brief (main agent).** Write one clean brief containing: the reader question, verbatim preceding and following paragraphs, verified facts/numbers, what later sections actually show, known limits, and any protected wording. Never dictate individual sentences.
2. **Drafter (fresh subagent).** Reads the brief, `style-and-citations.md`, and any local `preferences.md`. Applies all transition and craft rules in `style-and-citations.md` §1–§3 and outputs:
   - a clean draft file (passed alone to the Checker), and
   - a worksheet with its reader question, proposition chain, **link table** (every adjacent pair including entry and exit: relation + exact linking words), and claim-vs-brief check.
3. **Independent Checker (separate fresh subagent, blind to the Drafter's worksheet).** Reads only the clean draft, brief, and guides:
   - Rebuilds the link table from scratch (entry, every adjacent pair, exit).
   - Audits strictly against `style-and-citations.md` §1–§2 (false causes, missing antecedents, swappable sentences or bare `"and"`, overpromised claims, >25-word sentences, banned punctuation/words).
   - Quotes every failing phrase with the reader's difficulty, applies the **smallest** edits needed while keeping passing sentences verbatim, and rebuilds the link table to confirm 100% pass.
4. **Manager fact-check (main agent).** Verifies the Checker's revision against primary code/data/figures before presenting HTML track changes (or running the Council).

*(Outside full pipeline mode, still run one contextual reviewer subagent on the draft with its neighbors and relevant equations before presenting.)*

---

## 2. Reference-Paper Council

Convene on key sections (Introduction/Literature, Conclusions, or any target section) once `reference_papers/` holds at least **3** clean `.md` files.

### Setup & independence
- Launch **two independent subagents in parallel** using the user-chosen model(s) and effort (two distinct models/providers preferred when available).
- Neither member sees the other's report, the Drafter's worksheet, or the Checker's notes.

### Procedure & 5 comparison categories
1. Each member reads the **matching section of every reference paper** in `reference_papers/` first—grading against what those papers actually do, not memory.
2. Each member grades these **5 categories** separately, returning a verdict (`matches`, `partly matches`, or `does not match`), a score (`1–5`), and the compared reference-paper passages (paper ID + section):
   1. **Meaning & content:** Covers the same core elements as the reference papers (e.g., motivation/history/gap/contributions for Intro; verified outcomes, tradeoffs, scope, and significance for Conclusions).
   2. **Citations, evidence & scope balance:** Matches reference-paper norms—oldest original sources and placement for Intro/Lit; number density, citation norms, and scope/future-work balance for Results/Conclusions.
   3. **Length & format:** Word count, sentence count, paragraph count, and prose vs. bullets compared to the reference papers' range and median.
   4. **Flow of ideas:** Sequence of rhetorical moves compared to the reference papers.
   5. **Transitions & sentence craft:** Sentence-pair and paragraph-boundary linkage compared to the reference papers.
3. Each member quotes departing sentences and proposes the **smallest fix** (no full rewrite).
4. **Manager reconciliation:** Verify disputed facts against manuscript/data, reconcile supported findings, verify length/rule checks, and present **both** council ratings side by side with the reconciled HTML track-changes draft.

---

## 3. Optional Independent Review

Offer after presenting a draft (when the Council has not already reviewed it) and run only if accepted.

1. Spawn one fresh subagent (user-chosen model/effort, no drafting history) with a blind package: original + proposed passage, heading, verbatim neighbors, equations, figures/captions, primary data/source paths, author constraints, and guides (**no** writer rationale or scores).
2. Audit comprehension in context, technical accuracy, original-source verification (`style-and-citations.md` §3), and prose flow (`§1–§2`).
3. Return a verdict (`ready`, `needs revision`, or `cannot fully verify`) separating required fixes from optional preferences, quoting affected wording with smallest fixes.
4. Resolve supported fixes and run at most **one** fresh re-check if required edits materially change the passage.

---

## 4. Section Blueprints

### Abstract (9–12 sentences, 8 moves)
1. **Context** (2–3 sentences: why the broader problem matters, its limit, how this paradigm addresses it).
2. **Problem** (specific threat grounded in prior findings).
3. **Gap** (what remains unverified or unaddressed).
4. **Aim** (all main contributions stated up front).
5. **Method** (1–2 plain sentences, no unexplained internal terms).
6. **Validation** (what was tested and whether physical, numerical/virtual, or analytical).
7. **Results** (core quantitative findings with meaning; every announced evaluation reports its result).
8. **Significance** (what the completed result enables).

### Introduction & Literature Review (4 stages)
1. **Study contract & outline:** Extract only verified study facts; if key facts are missing, return a provisional outline and exact missing facts rather than inventing gaps or results.
2. **Original-source research:** Define comparison axes (assessed quantity, system boundary, mechanism, inputs/models, intervention, evaluation evidence), read originals (`style-and-citations.md` §3), and log a claim-source matrix in `sources.md`.
3. **Funnel draft:**
   - **Opening funnel:** Broad importance → key limitation → how this approach addresses it → specific technical threat by paragraph 2–4.
   - **Role-grouped literature:** Group prior studies by argument role (not paper-by-paper). Credit achievements under actual conditions, end each paragraph with a measured limitation tied to this paper's problem, and open the next paragraph by addressing it.
   - **Explicit gap → mirrored contributions:** Close the literature review with 1–2 sentences combining the verified gap axes, immediately mirror them in 2–3 clear contributions naming the validation type, and close with scope plus an ordered paper roadmap (including Conclusions). Leave method internals, calibration settings, and results out of the introduction.
4. **Audit:** Check every claim against the study contract and `sources.md` before presenting.

### Conclusions
- **Open directly with this study's contributions** (never a section-external demonstrative like *"This agreement"*).
- **Keep uncited by default** (refer to prior findings in plain terms unless your reference papers cite in Conclusions).
- **Report core verified outcomes and tradeoffs concisely**, leaving secondary run details in Results.
- **Put demonstrated significance before scope limits and open future work** (*"Finally, … Future work can …"*).
