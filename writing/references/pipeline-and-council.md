# Connected-Paragraph Pipeline, Reference-Paper Council & Section Blueprints

Multi-agent drafting, transition-checking, reference-paper grading, and section-structure workflows for `Habashi-kit/writing`. Load this reference when running the pipeline, convening the council, conducting an optional independent review, or drafting an Abstract, Introduction/Literature Review, or Conclusions.

*(Before launching any subagent below, confirm the user's preferred model(s) and reasoning effort per `SKILL.md`.)*

---

## 1. Connected-Paragraph Pipeline

Run when requested explicitly (or configured as default for a project); skip whenever the user says **"no pipeline"**. End every reply that used it with:

> *Used the connected-paragraph pipeline. To skip it, say 'no pipeline' in your prompt next time.*

### Pipeline stages

1. **Manager brief.** The main agent writes one clean brief containing: the reader question, the verbatim preceding and following paragraphs, verified facts and numbers, what later sections actually show, known limits (what tests did *not* show), and any author-protected wording. **Never dictate the content of individual sentences.**
2. **Drafter (user-chosen model & effort).** Reads the brief, `style-and-citations.md`, and any per-paper `preferences.md`, then follows the 9-step protocol below. Outputs both a clean draft file and its full protocol worksheet (reader question, proposition chain, link table, claim check).
3. **Independent Checker (fresh subagent, user-chosen model & effort).** Must **not** see the drafter's worksheet or link table—only the clean draft, the brief, and the guides. Applies the checker steps below, lists every failure with quoted words, revises with the smallest possible edits, and re-verifies every pair.
4. **Manager review.** The main agent checks the revised draft against actual manuscript data/code/figures before presenting the HTML track-changes draft (or sending it to the Reference-Paper Council).

*(For routine edits outside the full pipeline, still run a single contextual reviewer subagent on the draft with its preceding/following paragraphs and relevant equations, fix supported findings, and verify facts before presenting.)*

### Drafter protocol & transition rules (9 steps)

A paragraph is an argument, not a list of facts. Every sentence must take something the reader already holds and do something with it.

1. **Reader question.** Write the one question this paragraph answers for a reader who just finished the preceding paragraph.
2. **Proposition chain.** List the propositions in the order the reader needs them. For each proposition after the first, name its logical relation to the one before: *because*, *therefore*, *so (that)*, *but / however*, *which means*, *for example*, *then* (sequence), or *to do this* (purpose). *"Also"*, *"in addition"*, *"another"*, and parallel lists (*"X shows A. Y shows B."*) are not relations—reorder, merge, or drop unrelated propositions.
3. **Given before new.** Open each sentence with what the previous sentence delivered (the consequence, concept, or a clear antecedent) and end with the new information. Words such as *"this"*, *"these"*, *"the same"*, and *"the first"* require an explicit prior antecedent.
4. **One relation per sentence.** Keep each sentence at **25 words or fewer**. If a sentence carries two relations, split at the second relation rather than packing both in.
5. **Entry and exit.** Sentence 1 picks up the last point of the preceding paragraph/section (unless opening an independent section such as Conclusions). The last sentence hands off directly to the immediately following paragraph by stating why the reader needs what comes next—never jump ahead to a later section or end on a generic shared setting. When opening a section followed by a setup subsection, close with a brief ordered roadmap grounded in the paragraph's last point rather than an invented causal *"so"*.
6. **Swap test.** If two adjacent sentences can trade places without loss of logic, they form a list—merge them with an explicit relation or rewrite one to depend on the other. Apply the same test to two clauses joined by a bare *"and"*.
7. **True causes only.** For every *"so"*, *"therefore"*, *"because"*, and *"thus"*, verify that the stated cause is the real physical or logical cause. A design choice relates to an expected effect by purpose (*"to test"*, *"to counter"*), not as its cause.
8. **Promise only what follows.** Every claim about a later test or section must match what the brief confirms that section delivers. State expected outcomes as expected, never as findings.
9. **Link table before returning.** For every adjacent pair—including entry (preceding text → sentence 1) and exit (last sentence → following text)—record the relation and the exact linking words. Also pair each claim about a later section with the brief's verified facts. Revise until every pair and claim passes.

### Independent Checker steps

1. Read only the clean draft, the manager brief, and the style/pipeline guides (never the drafter's notes).
2. Build a brand-new link table (entry, every adjacent pair, exit) and audit strictly for:
   - false causal words (Step 7)
   - `"this"`, `"these"`, `"the same"`, `"the first"`, or pronouns without a clear antecedent (Step 3)
   - swappable adjacent sentences or bare-`"and"` pairs (Step 6)
   - overpromised claims or expectations stated as findings (Step 8)
   - sentences over 25 words, colons, semicolons, `"whose"`, `"ideally"`, or other style violations
3. Quote every failing phrase and state the exact reader difficulty.
4. Revise with the **smallest** edits that fix every failure, preserving passing sentences verbatim.
5. Rebuild the link table on the revision and confirm 100% pass.

---

## 2. Reference-Paper Council

Convene the council on key sections (especially **Introduction / Literature Review** and **Conclusions**, or any section the author specifies) once `reference_papers/` holds at least **3** clean `.md` reference papers.

### Members & independence

Run two independent subagents in parallel using the **model(s) and effort chosen by the user** (prompt the user first if not already specified; using two distinct models/providers gives stronger cross-checking):
- **Member 1** and **Member 2** each work **alone**: neither sees the other's report, the drafter's notes, or the checker's notes.

### Required procedure & 5 comparison categories

1. **Read the matching section of every reference paper first.** Grade against what the reference papers actually do (structure, length, citations, number density, flow, transitions), not against a remembered impression.
2. **Grade these 5 categories separately**, returning for each: a verdict (`matches`, `partly matches`, or `does not match`), a score (`1–5`), and the specific reference-paper passages compared (paper ID and section):
   - **1. Meaning & content:** Does the draft cover the same substantive elements as the reference papers (e.g., field motivation/history/gap/contributions for Intro; verified outcomes, tradeoffs, scope, and significance for Conclusions)?
   - **2. Citations, evidence & scope balance:** For Intro/Lit: do citations follow reference-paper kind/placement with oldest original sources for general claims? For Conclusions/Results: do number density, citation norms (e.g., uncited conclusions), and scope/future-work balance match the reference papers?
   - **3. Length & format:** How do word count, sentence count, paragraph count, and prose vs. bullet format compare with the reference papers' range and median?
   - **4. Flow of ideas:** Does the sequence of rhetorical moves match the reference papers (e.g., funnel → gap → contribution in Intro; verified outcomes → demonstrated significance → limits/open future work in Conclusions)?
   - **5. Transitions & sentence craft:** Are sentence pairs and paragraph boundaries linked as cleanly as in the reference papers?
3. **Sentence-level fixes only.** Quote every departing sentence and propose the smallest fix. Do not rewrite the whole draft.
4. **Manager reconciliation.** Verify disputed factual points against the manuscript/data, apply the supported shared fixes, check word/sentence/rule constraints, and present **both** council ratings side by side with the reconciled HTML track-changes draft.

---

## 3. Optional Independent Review

After presenting a revised passage (when a council review has not already been run), you may offer: *"Would you like an independent review by a fresh subagent? If so, which model and effort would you like to use?"* Run only when accepted.

1. Spawn a fresh subagent using the user-selected model and effort (no inherited drafting history).
2. Supply a blind fixed package: original + proposed passage, section heading, verbatim neighbors, equations, figures/captions, verified data/implementation paths, author constraints, and guides—**never** writer rationale, self-reviews, or scores.
3. Require checks on: (a) comprehension in context, (b) technical accuracy and original-source citation verification, and (c) prose flow, repetition, and rules.
4. Require a structured verdict (`ready`, `needs revision`, or `cannot fully verify`) separating required fixes from optional preferences, quoting affected phrases with smallest corrections.
5. Resolve supported findings and run at most **one** fresh re-check if required edits materially change the passage.

---

## 4. Section Blueprints (Domain-Agnostic)

### Abstract (9–12 sentences, 8 moves)
1. **Context:** Why the broader testing/modeling problem matters, its core limitation, and how the study's approach addresses it (2–3 sentences).
2. **Problem:** The specific mechanism or threat, grounded in prior findings.
3. **Gap:** What remains unverified or unaddressed.
4. **Aim:** Every main contribution of this study, stated up front.
5. **Method:** 1–2 plain sentences with no unexplained internal terminology.
6. **Validation:** What was evaluated and whether it is physical, numerical/virtual, or analytical.
7. **Results:** Core quantitative findings with their physical/technical meaning stated (every announced evaluation must report its result).
8. **Significance:** What the completed result enables.

### Introduction & Literature Review (4-stage workflow)
1. **Study contract & provisional outline:** Extract only verified study facts (problem, reader question, method, available inputs, assumptions, evaluation type, intended contribution). If key study facts are missing, return a provisional outline and exact missing facts rather than inventing results or gaps.
2. **Original-source research & claim-source matrix:** Define comparison axes before searching (assessed quantity, system boundary, mechanism, required inputs/models, intervention, evaluation evidence). Read complete originals (never rely on abstracts/snippets for technical claims) and log each verified source in `sources.md` with exact version, section/page, and access status.
3. **Funnel draft:**
   - **Opening funnel:** Importance of the broader method → its key limitation → how this paradigm addresses it → narrow to the specific technical threat by paragraph 2–4.
   - **Role-grouped literature:** Group prior work by the role it plays in the argument (not a paper-by-paper catalogue). Credit what each group achieved under its conditions, then end the paragraph with a measured limitation tied to this paper's problem; open the next paragraph by answering that limitation.
   - **Explicit gap → mirrored contribution:** Close the literature review with 1–2 sentences combining the verified gap axes. Immediately mirror that gap in 2–3 clear contributions naming the validation type, followed by a brief scope statement and ordered paper roadmap (including the final Conclusions section). Leave method internals, calibration settings, and results out of the introduction.
4. **Structural & evidence audit:** Confirm every claim against the study contract and `sources.md`, check adjacent links and boundaries, and keep drafts/audits separate from the manuscript until approved.

### Conclusions
- **Open directly with this study's contributions** (never with a section-external demonstrative like *"This agreement"*).
- **Separate prior work from this study** in plain terms (uncited by default unless your reference papers cite in Conclusions).
- **Highlight verified mechanisms, outcomes, and tradeoffs** concisely—keep core quantitative takeaways and leave secondary run details in the Results section.
- **Place demonstrated significance before limits and future work** so the paper's impact does not read as conditional on future studies.
- **Close neutrally on scope and open future work** (*"Finally, … Future work can …"*).
