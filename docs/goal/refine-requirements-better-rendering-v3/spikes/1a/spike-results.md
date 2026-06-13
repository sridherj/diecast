# Spike 1a — Maker Quality Ceiling: Results

> **Sub-phase:** sp1a (`refine-req-v3-phase1`) · **Gate fed:** G1 (with sp1b) ·
> **Run:** `run_20260612_102118_059586` (cast-subphase-runner) · **Date:** 2026-06-12
> **Operating mode:** HOLD SCOPE — this spike *validates*, it does **not** re-decide. The
> binding maker-vs-hybrid call is made by the owner at **G1**; everything below is a
> **recommended** disposition plus evidence.

## TL;DR

| Family | BEATS DETERMINISTIC | Strength of evidence |
|---|---|---|
| `bug_fix` | **YES** | **Strong / structural.** The deterministic baseline silently **drops 5 of 7 canonical ids** (the entire fix scope + most acceptance checks); the maker surfaces all 7 in family-appropriate "The fix" / "How we'll know it's fixed" sections. Not a taste call — a measured comprehension gap. |
| `new_initiative` | **YES (qualified)** | **Moderate / structural + visual.** Id coverage is at parity (the `new_initiative` recipe already realizes US/FR/SC). The win is hierarchy and scannability: the maker keeps the entire WHAT **open** (0 `<details>`) in &lt;½ the bytes, where the baseline collapses the WHAT-depth behind **13 `<details>`**. The ceiling-level visual win needs the human-eyeball carry-forward to confirm. |

**Recommended gate disposition: PROCEED to Phase 3.** The quality bar ("a maker render clearly
beats the v2 deterministic page for ≥2 families, carries every canonical id verbatim on the
correct block, stays a self-contained single file") **is reachable by hand** for both families
in the corpus. One **anomaly** (the v2 SC-001 checker is necessary-but-not-sufficient — it
passes the baseline too) is recorded below as **Phase-4a input**, not acted on here.

## Hand-effort honesty (this is a *ceiling* proof)

A human crafted these two maker pages. The gate wording is deliberately **"reachable by
hand"** — the artifacts establish that the bar *exists and can be cleared*, not that the
eventual Phase-3 agent will clear it unaided. Phase 3 re-proves it **agent-generated**, reusing
`spike_id_audit.py` (below) as its acceptance pattern. Only one real classified doc exists in
the repo (`new_initiative`); the `bug_fix` doc was **authored from the real v2 dogfooding
defect** (the `goal_card.py` / `renderer.py` raw-markdown leak), not synthesized fiction.
Family breadth across all nine families is re-validated in Phase 5 (SC-002) — out of scope here.

## Corpus

| Family | Source doc | Maker HTML | Deterministic baseline |
|---|---|---|---|
| `new_initiative` | `refined_requirements.collab.md` (this goal's own classified doc) | `new_initiative-maker.html` (21.7 KB) | `new_initiative-baseline.html` (48.9 KB) |
| `bug_fix` | `fixtures/goal-card-markdown-leak.collab.md` (authored from the real defect) | `bug_fix-maker.html` (11.6 KB) | `bug_fix-baseline.html` (26.6 KB) |

`data_analysis` (the stretch third family) was **not** attempted — descoped to keep the run
within budget; ≥2 families is the gate bar and is met. Recorded as a non-blocking carry-forward.

Each maker page follows the cast-preso-how **8-step discipline by hand** (see
`briefs/<family>-brief.md`), adapted from a reveal.js slide to a **scrolling document page**.
**Conscious non-delegation, recorded in both briefs:** `/cast-preso-how` is **not** invoked
(it generates reveal.js slides and the net-new requirements maker agents are Phase-3-owned) —
only its discipline is followed.

---

## Audit 1–4 results (raw output: `spike_id_audit.out.txt`)

`spike_id_audit.py` runs four audits per family. **All four pass for both families.** The
source id-set is taken **structurally from the parser** (the authoritative assigned-id set),
never from a prose regex, so a cross-reference like "(this is SC-001)" never inflates it.

### Audit 1 — id-token set equality

| Family | Source ids | Visible-in-maker ids | Missing | Invented | Verdict |
|---|---|---|---|---|---|
| `new_initiative` | 31 (US1–7, FR-001…016, SC-001…008) | 31 | none | none | **PASS** |
| `bug_fix` | 7 (FR-001…004, SC-001…003) | 7 | none | none | **PASS** |

### Audit 2 — FR-003 per-block correspondence (the load-bearing one)

Set-equality alone would pass a label sitting on the **wrong** block. The faithful test:
each id's *anchoring label* (`<span class="anchor">`, visible text — **never** an `id=`
attribute) is **unique**, and the maker block carrying it overlaps **that id's** source text
**more than any other id's** (nearest-source argmax over the same kind-prefix). This is robust
to the maker legitimately *distilling* a user story for communication — it requires verbatim
carriage of the **id**, not of the WHAT.

- `new_initiative`: 31/31 anchor labels, each unique, **every block matches its own id best** → **PASS**
- `bug_fix`: 7/7 anchor labels, each unique, **every block matches its own id best** → **PASS**

(For the seven `new_initiative` user-story cards the maker distilled the prose; own-overlap is
lower in absolute terms but is still the argmax against all other US sources — i.e. correctly
placed. FR/SC rows are carried near-verbatim, overlap ratios 0.8–1.0.)

### Audit 3 — self-containment

Both maker files: **no** `<link>`, **no** external `src`/`href` beyond the two FR-028-sanctioned
references (`/static/htmx.min.js`, `/static/requirements_comments.js`), CSS fully inline, no CDN
fonts (system-stack fallbacks only). → **PASS** both. *(So sp1b can reuse these files: each
carries the sanctioned script tags + `data-goal-slug` on `<body>`.)*

### Audit 4 — zero-`id` / `data-block-anchor` (attribute-based)

Checked as **attributes** via the parse tree (not a naive substring grep): the maker may, and
does, quote the words "no `data-block-anchor`" as escaped **requirement text** (it is FR-003 /
SC-002 source content) — that is content, not an attribute. Elements with an `id` attribute: 0.
Elements with a `data-block-anchor` attribute: 0. Start-tag `id=` grep: 0. → **PASS** both.
The raw substring `data-block-anchor` count (1 in `new_initiative`, 3 in `bug_fix`) is entirely
prose/comment mentions of the contract — surfaced in the audit output for transparency.

---

## The gate judgement (Step 1a.6)

### `cast-requirements-checker` verdicts (delegation — subagent, bare JSON)

Run over the `extract_zero_click_view` of **both** the maker and the deterministic baseline,
per family (4 runs). The checker is the **v2 SC-001 cold-reader** (binary WHAT-restate gate).

| Page | `can_state_what` | `missing` | `score` | Restated outcome (abridged) |
|---|---|---|---|---|
| `new_initiative` — **maker** | ✅ true | [] | 1.0 | "A bespoke, per-family LLM render that **beats the plain page on comprehension**, with WHAT/HOW/checker/diff agents." |
| `new_initiative` — baseline | ✅ true | [] | 1.0 | "A first-time reader can state the job… within sixty seconds…" *(restated a meta-**criterion**, SC-001 text, as the outcome — see anomaly)* |
| `bug_fix` — **maker** | ✅ true | [] | 1.0 | "Zero literal markdown characters appear on the Goal Card after the fix…" |
| `bug_fix` — baseline | ✅ true | [] | 1.0 | "A Goal Card whose source contains inline markdown renders all formatting correctly…" |

### ⚠️ Anomaly recorded as **Phase-4a input** (not tuned here)

**The v2 SC-001 checker passes the baseline too — it cannot, by itself, decide "beats
deterministic."** This is expected and is exactly why v3 replaces it (decision: *a single new
comprehension-plus-visual checker*; FR-004/FR-009). The checker measures one thing — *can an
unfamiliar reader restate the WHAT from the zero-click surface* — and both pages clear that low
bar. It does **not** score visual quality, scannability, or family-appropriateness, and it does
**not** notice that the `bug_fix` baseline **silently dropped the entire fix scope** (it can
still restate the job/outcome from the Goal Card + Intent + Evidence prose alone). Two concrete
signals for the Phase-4a checker to fix:

1. **No "beats" axis.** The gate is pass/pass; a richer checker must grade comprehension/visual
   quality and family-fit, not only WHAT-restate.
2. **Blind to dropped depth.** It rated the `bug_fix` baseline 1.0 despite 5/7 canonical ids
   (the fix + acceptance checks) being absent from the page — because they are absent from the
   *zero-click* surface it reads, it never knows they should be there. A v3 checker needs the
   source-vs-render id-coverage signal (Audit 1/2) folded in.

Per the plan: **do not tune `cast-requirements-checker` now** — it is replaced in Phase 4a.

### Structured rubric self-assessment (maker vs baseline)

Scored 0–10 by hand from the HTML structure + zero-click extracts. **Visual-quality rows are
structural estimates pending the human-eyeball carry-forward** (no browser in an autonomous run).

| Dimension | `new_initiative` maker / baseline | `bug_fix` maker / baseline | Why |
|---|---|---|---|
| **Hierarchy** (L1 job dominates, depth secondary) | **9 / 6** | **9 / 6** | Maker: single-stat / one-statement Goal Card, job at L1, scope compare open. Baseline: WHAT-depth collapsed behind 13 / 4 `<details>` — the reader must click to reach it. |
| **Scannability** (find a requirement by id fast) | **9 / 5** | **9 / 3** | Maker: every id an open, accent anchor label on an open block. Baseline `new_initiative`: FR/SC tables behind a closed `<details>`. Baseline `bug_fix`: **FR/SC not rendered at all**. |
| **Family-appropriateness** (US2) | **9 / 6** | **9 / 4** | Maker `new_initiative`: "The bet / Key decisions / What a reader walks away with" + compare-contrast decisions. Maker `bug_fix`: red-dialed "What broke / The evidence (before→after diff) / The fix" — reads like a bug. Baseline applies one generic recipe shell. |
| **Visual quality** *(carry-forward estimate)* | **8 / 5** | **8 / 5** | Maker reuses the toolkit tokens (cream/navy/raspberry, IBM Plex Mono + DM Sans, 40px grid) with a connective accent spine; in &lt;½ the bytes. Confirm at the ceiling level with the human pass. |

### Decisive structural evidence (independent of taste)

- **`bug_fix` id coverage:** source defines **7** canonical ids; the deterministic baseline
  renders **2** id tokens — and both are incidental (one prose mention `(this is SC-001)`, one
  `FR-012` inside a CSS comment in the inlined theme). The bug_fix recipe is `PROBLEM → EVIDENCE
  → OPEN`, so it **realizes no FR/SC tables at all**: a reader of the plain bug_fix page
  **cannot see what the fix is or how it will be verified.** The maker carries all 7, audited.
  This is the single clearest "maker beats deterministic" result in the corpus and it is a real
  property of the shipped recipe, not a contrivance.
- **Open vs hidden WHAT:** maker `<details>` count = **0** (both); baseline = **13**
  (`new_initiative`) / **4** (`bug_fix`). The maker keeps the whole WHAT on the zero-click
  surface; the baseline hides depth behind disclosure.
- **Compactness:** maker is **&lt; half** the baseline byte size in both families while showing
  *more* of the WHAT open.

---

## BEATS DETERMINISTIC — per family (Step 1a.7)

### `bug_fix`: **YES**
Strong, structural. The deterministic page drops the fix scope and most acceptance criteria
(5/7 ids invisible); the maker surfaces all of them in a family-shaped layout with a before→after
evidence diff. All four audits pass. Checker passes the maker (and, anomalously, the baseline).

### `new_initiative`: **YES (qualified)**
Id coverage is at parity (the recipe realizes US/FR/SC), so this win is hierarchy +
scannability + family-fit rather than dropped content: the maker keeps the entire WHAT open and
scannable in &lt;½ the bytes where the baseline collapses it behind 13 disclosures. All four
audits pass. The ceiling-level visual claim is pending the human-eyeball carry-forward.

---

## Recommended disposition → **G1**

**Recommend Phase 3 PROCEEDS with the maker direction.** Both corpus families clear the
"reachable by hand" bar with all four audits green; the maker-vs-hybrid fork does **not** need
to be surfaced for re-decision. The binding decision is the owner's at G1. *(This sub-phase does
not silently re-scope; HOLD SCOPE is intact.)*

## Carry-forward items (recorded, not acted on)

1. **Human-eyeball browser pass (visual/taste gate).** No browser in this autonomous run. A
   human must open all four files side-by-side and confirm the visual-quality rubric estimates
   at the *ceiling* level. Static verdicts above; this does **not** block the spike.
2. **Phase-4a checker anomaly.** The v2 SC-001 checker is necessary-but-not-sufficient (passes
   the baseline; no "beats" axis; blind to dropped depth). Fold source-vs-render id-coverage and
   a comprehension/visual-quality axis into the Phase-4a replacement. **Do not tune the v2
   checker.**
3. **Spec carry-forward gap (already flagged, not acted on here):** the verbatim-carriage clause
   for `cast-requirements-render.collab.md` is a Phase-3 `/cast-update-spec` item.
4. **Stretch family un-run:** `data_analysis` was descoped from this run; ≥2-family bar met.
   Nine-family breadth is Phase 5 / SC-002.

## Artifacts produced (all under `docs/goal/refine-requirements-better-rendering-v3/spikes/1a/`)

- `fixtures/goal-card-markdown-leak.collab.md` — authored `bug_fix` source doc
- `new_initiative-maker.html`, `bug_fix-maker.html` — hand-crafted maker renders
- `new_initiative-baseline.html`, `bug_fix-baseline.html` — `render_requirements()` pure-call output
- `*-maker.zeroclick.txt`, `*-baseline.zeroclick.txt` — `extract_zero_click_view` extracts (checker input)
- `briefs/new_initiative-brief.md`, `briefs/bug_fix-brief.md` — the 8-step discipline by hand (+ recorded non-delegation)
- `spike_id_audit.py` + `spike_id_audit.out.txt` — the four-audit script (Phase-3 reuses it) and its captured run
- `spike-results.md` — this file
