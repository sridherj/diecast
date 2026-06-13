# Refine Requirements — Better Rendering (v3): Phase 5 — Gap-Filling, Cross-Family Hardening & Sign-Off

## Overview

This plan details **Phase 5 only** — the last phase — of the v3 high-level plan: the
presenter fills genuine comprehension gaps by **asking upstream, never fabricating**
(FR-015/US7), reconciles obtained detail back to the canonical source **through the
existing v2 change-request gate unchanged** (FR-016), proves all nine `WorkFamily`
values render visibly distinct, clean, comprehensible pages (SC-002), runs the full
SC-001…SC-008 sweep with captured results, and lands the final `/cast-update-spec`
reconciliation pass. Phase 3 reserved the `gaps[]` seam in the WHAT-doc front matter
explicitly for this phase; Phase 5 activates it.

Two load-bearing insights ground the design:

1. **The FR-016 invariant is made structural, not behavioral.** The maker never consumes
   a gap answer directly — the answer's *only* destination is a change-request through the
   v2 same-door intake. The page renders a gap **marker** (question + status), and the gap
   un-marks only when the approved detail lands in canonical, bumps the version, changes
   the source hash, and the next view regenerates from canonical. The v2 cache mechanism
   does all the work; no special "un-mark" path exists to get wrong.
2. **Phase 5's gap-fill emitter is the first REAL downstream emitter** the roundtrip spec
   (`cast-requirements-roundtrip.collab.md`) hard-deferred ("v2 proves the receiving path
   with the simulated `synthetic_child.py`; wiring real planner/executor emitters is a
   later goal"). The intake/gate/apply contracts are consumed byte-unchanged; only the
   spec's Out-of-Scope fence is touched (see 5d).

Planning only — this document specifies Phase 5; it does not implement it. It assumes
Phases 3, 4a, and 4b are executed and green (their plans exist; execution had not started
at planning time). Where Phase 5 depends on a prior-phase interface, the dependency is on
the *planned contract* in `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
— if execution renamed something, Phase 5 inherits the executed name.

## Operating Mode

**HOLD SCOPE** — `refined_requirements.collab.md` front matter pins `scope_mode: hold`
and the delegation context repeats it ("Honor scope_mode: hold"). Owner decisions are
binding and not re-opened: gap-fill writes go ONLY through the existing v2 change-request
gate (no new writer, no lighter path); the maker never fabricates requirement content;
the nine-family enum is LOCKED (`taxonomy_version: 1` — no additions); the deferred human
timed-read evaluation from v2 stays out of scope. No review UI, no PROV export, no
real-emitter generalization beyond the one render-gap-fill emitter this phase requires.

## Position in Overall Plan

```
Phase 1 (spikes) ───────┐
                        ├──► Phase 3 (maker pipeline) ──┬──► Phase 4a (quality loop) ──┐
Phase 2 (commenting) ───┘                               └──► Phase 4b (survival) ──────┴──► Phase 5 (THIS PLAN)
```

Phase 5 is the terminal integrator: it consumes Phase 3's `gaps[]` seam + pipeline
stages, Phase 4a's quality loop + `human_review` flag, Phase 4b's survival gate +
narration surface, and the v2 roundtrip gate — and signs the goal off. Nothing depends
on Phase 5; Phase 5 depends on everything.

## Depends On (from prior plans / seed decisions)

From the binding seed (`refine-requirements-better-rendering-v3-decisions-so-far.md`):

- **Gap-fill write-back door:** detail the maker obtains upstream reconciles through the
  EXISTING v2 change-request gate unchanged (propose → notify → human gate, never
  auto-sync); no new writer into the canonical source; the page marks the gap until
  approval. Adopted as the spine of 5a/5b.
- **Quality loop / fallback policy / canonical-source rules** — adopted as-is; Phase 5
  adds stages at documented seams, it rewrites nothing.

From Phase 3 (planned):

- **The reserved `gaps[]` seam:** WHAT-doc YAML front matter already carries `gaps: []`
  ("schema field defined now, always empty in Phase 3, no behavior attached"). 5a defines
  the entry schema and attaches behavior — the seam working as designed.
- **Pipeline stage seam:** `run_what → gate_what → run_how → gate_html → publish` as
  named functions in `render_job_service.py`; 4a inserted `run_checker → decide_quality`
  between `gate_html` and `publish`. 5a inserts its gap stages between `gate_what` and
  the final `run_how` (detail below) — again a stage addition, not a rewrite.
- **`maker_gate.py`** pure-gate discipline (prompt-ready violation strings, fixtures per
  violation); **strict sentinel extraction** (first `BEGIN RENDER` → first `END RENDER`;
  5a's HOW gap trailer deliberately lives *outside* the sentinels so extraction is
  untouched); `AgentRunner` seam (tool-free `claude -p`, `env -u CLAUDECODE`, config-read
  model with the `[USER-DEFERRED]` tier comment); `build/render-jobs/` artifact dir;
  `render_jobs` table; stub short-circuit (stubs never invoke the maker — and therefore
  never invoke gap machinery).

From Phase 4a (planned):

- The quality loop wraps the structural gate; **structural violations stay on the
  no-output branch only while zero structurally-valid attempts exist**; `human_review` +
  `review_reason` + `published_attempt` + `published_score` + `heartbeat_at` columns on
  `render_jobs`; the served-artifact envelope stamps the flag. **4a's hand-off names
  Phase 5's consumption:** "Phase 5's nine-family sweep should run each family render
  through the full loop and read `human_review` as its per-family quality signal" — 5c
  does exactly that.
- Checker input = rendered artifact + family label ONLY (cold reader). 5b adds one
  checker-prompt line (gap amnesty — see Suggested Revisions).

From Phase 4b (planned):

- Survival check is part of the structural gate inside `gate_html`, evaluated before
  `run_checker` — gap markers must not break it (5b verification covers this); the
  narration POST exists as a surface round-trip summaries *may* reuse (Phase 5 takes the
  option: NOT adopted — see Decisions Made Autonomously #9); `cast-comment-reanchor`
  contract v2 is consumed untouched.

From v2 roundtrip (landed, consumed unchanged — the naming contract adopted verbatim):

- `POST /api/goals/{slug}/change-requests` same-door intake; ONE
  `change_request_service.create` write path; `gate_status(kind, target_quote, policy)`
  trust lanes under the single global `WRITEBACK_GATE_POLICY` (v2 default
  `gate-except-additions`: pure additions fast-track `applied` + one outbox FYI;
  modifications/annotations intake `proposed` and await the human gate); `change_requests`
  columns `kind ('addition'|'modification'|'annotation')`, `base_version` (integer
  `requirement_versions.version`), `origin_phase` / `origin_activity_id` /
  `origin_artifact_path`, `author` / `author_type`; `detect_conflict` purity;
  `cast-requirements-writeback` as the sole surgical file-writer; transactional outbox +
  relay. **None of this changes.**

From Phase 2 (landed surfaces consumed): `_theme.css.j2` (the `.rr-gap` marker class
lands beside `.comment-affordance` / `.render-refreshing` — same convention),
`strip_inline_markdown` (carriage gate dependency, unchanged).

---

## Sub-phase 5a: The Gap Contract & the Upstream Ask Loop

**Outcome:** The dormant `gaps[]` seam is live end-to-end on the agent side: the WHAT
agent detects and declares comprehension gaps in a machine-checkable schema; the HOW
agent can report gaps it finds through a structured trailer channel ("HOW asks WHAT");
a net-new tool-free `cast-requirements-gapfill` agent answers open gaps
**grounded-or-refuse** from the goal's own upstream artifacts; `render_job_service`
runs the bounded ask loop as named pipeline stages; and `maker_gate.py` proves every
piece deterministically. No change-request is emitted yet (5b) — 5a ends with a
validated `gaps-state.json` per job.

**Dependencies:** Phases 3 + 4a executed (pipeline stages + quality loop exist). None
within Phase 5.
**Estimated effort:** 2 sessions.

**Verification:**
- `pytest cast-server/tests/test_maker_gate.py` extended and green: gaps-schema pass +
  violation fixtures (duplicate `gap_id`, unknown `block_ref`, empty question, answer
  text smuggled into the WHAT doc, `.rr-gap` marker present with no matching gap, open
  gap with no marker, **and a two-open-gap fixture (Plan Review T3): exactly two `.rr-gap`
  containers each matching its own `question` — a render that merges two gaps into one
  marker, or swaps their questions, fails `check_html`**).
- `pytest cast-server/tests/test_render_job_service.py` extended (fake runners, latch
  pattern carried from 3c): WHAT-declared gaps flow to `gaps-state.json`; HOW trailer
  gaps trigger exactly ONE WHAT re-run (`GAPFILL_ASK_ROUNDS=1` honored); gapfill agent
  crash/timeout/garbage output → every open gap recorded `unfilled-ask-failed` on the
  job row, pipeline proceeds to a marked render (never blocks, never fabricates);
  fabricated evidence (quote that does not `verbatim_locate` in the cited file) → demoted
  to `cannot-supply` with the demotion reason recorded.
- **Evidence verbatim-locate parity (Plan Review T2):** an `evidence.quote` differing from
  the corpus only by whitespace/smart-quote MUST validate (via the shared `verbatim_locate`
  helper); a substantively-different quote MUST demote to `cannot-supply` with the reason
  recorded — pinning the trust-boundary locate semantics against silent future drift.
- Both new/changed agent dirs pass `/cast-agent-compliance`.
- A hand-run `claude -p` smoke of `cast-requirements-gapfill` over this goal's corpus
  (one answerable gap, one unanswerable) produces a parseable grounded-or-refuse doc —
  recorded as a smoke-run note, not CI.

Key activities:

- **Define the `gaps[]` entry schema** (activating Phase 3's reserved field) in the WHAT
  contract: each entry `{gap_id: "GAP-NN" (sequential per doc), section_title,
  block_refs: [...], question, why_it_matters}`. Hard rules, gate-enforced: `gap_id`s
  unique and sequential; every `block_refs` member is a parsed `Block.ref`; `question`
  non-empty; the WHAT doc NEVER contains a proposed answer (the WHAT layer only sees the
  source — it can name what's missing, it cannot supply it). Extend the
  `cast-requirements-what` prompt: detect gaps at the "would materially help the reader"
  bar (US7 language verbatim), with a hard cap `GAPFILL_MAX_GAPS` (config, default 5) —
  a page is communication, not an audit; trivia-hunting is explicitly instructed against.
- **Add the HOW gap-report trailer** to the `cast-requirements-how` contract: an optional
  `<!-- GAPS-DETECTED\n<yaml>\n-->` block placed AFTER the `<!-- END RENDER -->` sentinel
  (outside the strict extraction window, so 3c's sentinel rules are byte-untouched).
  Entries: `{section_title, question, why_it_matters}` — no ids (the WHAT re-run assigns
  them). This is the "HOW asks WHAT" channel of FR-015: the HOW layer never invents the
  WHAT, so when it needs a missing detail it *asks* rather than improvises.
- **Pipeline stages** (named functions, inserted at the Phase 3 seam):
  1. `run_what → gate_what` (existing).
  2. `run_how` first attempt (existing) — additionally harvest the trailer.
  3. `ask_what` (NEW, bounded): if the trailer is non-empty AND the round budget allows
     (`GAPFILL_ASK_ROUNDS`, config, default 1), re-run WHAT once with the HOW questions
     appended; the WHAT re-run either maps a question to source content the first pass
     under-served (the gap dissolves — the answer was in the source all along) or
     confirms it into `gaps[]`. Re-gate (`gate_what`). `GAPFILL_ASK_ROUNDS` is an
     INDEPENDENT counter from 4a's in-loop `QUALITY_MAX_WHAT_REWORKS=2` (Plan Review A2):
     this pre-loop gap-ask re-run never debits the in-loop WHAT-escalation budget, so a
     gap-bearing render keeps its full quality-loop reworks.
  4. `run_gapfill` (NEW): if open gaps exist, run `cast-requirements-gapfill` once per
     job over ALL open gaps.
  5. `validate_evidence` (NEW, deterministic, service-side): see below.
  6. `emit_change_requests` (NEW — specified in 5b; 5a lands it as a stage stub that
     only writes `gaps-state.json`).
  7. `run_how` final (with `gaps-state.json` inlined) → `gate_html` (now including gap-
     marker correspondence + 4b survival) → 4a quality loop → `publish` (all existing).
  The quality loop reworks HOW attempts against a **fixed** WHAT doc + gap state — gap
  machinery runs once per job, before the loop, satisfying FR-015's "before finalizing".
- **Author `agents/cast-requirements-gapfill/`** (net-new, the FR-010 "helpers as
  needed" slot; subagent carve-out config exactly like WHAT/HOW: `dispatch_mode:
  subagent`, `interactive: false`, `allowed_delegations: []`, `timeout_minutes: 15`,
  `model:` placeholder + `# [USER-DEFERRED] tier knob` comment). Input (inlined by the
  runner — tool-free): the open gap list, the canonical source, and the **grounding
  corpus**: the goal's own upstream artifacts only — `requirements.human.md`,
  `research_notes.human.md`, `exploration/` summary if present (an explicit allowlist
  the runner resolves; never the wider repo). Output: one YAML doc between sentinels,
  per gap: `{gap_id, supplied: true|false, answer, evidence: {file, quote},
  proposed_change: {kind: "addition" (LOCKED — Plan Review A1), section_hint,
  proposed_body}}` or `{gap_id, supplied: false, reason}`. A gap is *missing* content,
  never a rewrite of existing content, so `kind` is gate-pinned to `addition` (no
  `target_quote`): the v2 writeback places it via `section_hint` and `gate_status`
  fast-tracks it under the default policy, whereas a `modification`-kind gap (no
  `target_quote` to locate) would refuse `orphaned` at apply. Hard prompt rule: **supply
  only what the corpus literally supports, with a verbatim evidence quote; when in doubt,
  refuse** — refusal is a correct answer, the page will say so honestly.
- **`validate_evidence` (the trust boundary, deterministic):** for each `supplied` gap,
  the service asserts `evidence.file` is in the corpus allowlist AND `evidence.quote`
  verbatim-locates in that file by **reusing the existing `verbatim_locate` helper** (NOT
  a raw `str.find()`; Plan Review CQ2) — one locate implementation shared with the v2
  writeback backstop, so trivial whitespace/smart-quote differences don't falsely demote a
  grounded answer. Failure → demote to `cannot-supply`, record `evidence-validation-failed`
  on the job row (zero silent failures). This makes "never fabricates" **enforced, not
  promised**: an ungrounded answer cannot reach the change-request door.
- **`maker_gate.py` extensions** (pure, fixture-tested): `check_what_doc` gains the
  gaps-schema rules above; `check_html` gains **gap-marker correspondence** — every open
  gap in the WHAT doc has exactly one `.rr-gap` container in the HTML whose text contains
  that gap's `question` verbatim, and no `.rr-gap` exists without a matching gap (a gap
  is never silently dropped; a marker is never invented). Markers are class-based — zero
  `id=`, zero `data-block-anchor`, per the preserved DOM contract.
- **`gaps-state.json`** (job artifact, `build/render-jobs/{slug}/{hash12}/`): the
  service-owned resolution record `{gap_id, status: "cr-proposed"|"cr-applied"|
  "unfilled-cannot-supply"|"unfilled-declined"|"unfilled-ask-failed", cr_id?}` — the
  agents' docs stay agent-written; the service annotates state beside them, never
  mutates them. This `status` enum is THE single closed gap vocabulary (Plan Review A3):
  5b's fixed marker strings and the job-row reason codes (`evidence-validation-failed`,
  `unfilled-ask-failed`, …) map 1:1 to it via the explicit table in 5b, and `maker_gate`
  rejects any out-of-enum status — three drifting vocabularies collapse to one.
- → Delegate: `/cast-agent-compliance` over `cast-requirements-gapfill` + the two
  modified agent dirs — review output for carve-out and config-shape violations.
- → Delegate: consult `/cast-agent-design-guide` (I/O contract section) while authoring
  the gapfill contract block.

**Design review:**
- **Architecture ✓** — gap machinery is stage additions at the documented Phase 3 seam;
  the gapfill agent follows the established tool-free carve-out; the service owns all
  I/O and validation, agents stay pure text-to-text.
- **Error & rescue (zero silent failures):** every degradation is recorded and honest —
  ask-round exhausted, gapfill crash, evidence demotion all land on the job row AND in
  `gaps-state.json`, and the page still ships with explicit markers; the gap path can
  never block a render or fabricate content.
- **Security:** the grounding corpus is an explicit allowlist resolved by the runner
  inside the goal's own artifact tree (path-validated, the existing traversal rule);
  the gapfill agent is `--tools ""` — it cannot read beyond what the runner inlines and
  cannot write anything; evidence validation is server-side, not agent-side.
- **Naming ✓** — `cast-requirements-gapfill` parallels `-what`/`-how`; `GAPFILL_*`
  config knobs parallel 4a's `QUALITY_*`; `GAP-NN` ids parallel the canonical id style
  without colliding with it (gate rejects `GAP-NN` appearing as a canonical ref).
- **Spec consistency ⚠️** — gaps schema, trailer channel, ask bounds, and the
  grounded-or-refuse contract are new spec'd behavior under
  `cast-requirements-render.collab.md` → recorded in 5d's single `/cast-update-spec`
  pass (clause texts fixed here, the 3e discipline).

## Sub-phase 5b: Reconciliation Through the Gate & Honest Page Markers

**Outcome:** Supplied gap answers become normal change-requests through the v2 same-door
gate (deduped, provenance-stamped, policy-laned by the UNCHANGED global
`WRITEBACK_GATE_POLICY`); the page renders an honest `.rr-gap` marker per open gap —
question + status, NEVER the proposed answer text — and un-marks naturally when the
approved detail lands in canonical and the next view regenerates. The gap-injection test
(SC-007's realization) is green.

**Dependencies:** 5a.
**Estimated effort:** 1–1.5 sessions.

**Verification:**
- `pytest cast-server/tests/test_gap_reconciliation.py` (new, fake runners + real
  service + real DB): a supplied gap produces exactly one `change_requests` row with
  `kind = "addition"` (Plan Review A1), `base_version` = current
  `requirement_versions.version`, `author="cast-requirements-gapfill"`,
  `author_type="agent"`, `origin_phase="render-gapfill"`, `origin_activity_id` = job id,
  and the gap fingerprint in `origin_artifact_path`; intake status matches
  `gate_status` under the live policy (fast-track `applied` + one outbox FYI for the
  pure addition under the default; `proposed`, no FYI, under `gate-all`).
- **Dedupe tests:** re-render same source → zero new CRs; CR `rejected` → re-render →
  zero new CRs AND marker reads "declined"; CR `superseded` → re-propose allowed.
- **Convergence test (auto-apply lane):** a fast-track-applied addition bumps the
  version and changes the source hash → the in-flight job is `superseded`
  (compare-and-publish) → the fresh job's WHAT run no longer detects the gap → the
  rendered page has no marker and no new CR. Asserts the loop terminates (no
  propose-regen-propose cycle).
- **Gated-lane convergence test (Plan Review T1):** emit a gated gap CR (policy
  `gate-all`, or any non-fast-tracked lane), approve it in-test via
  `change_request_service` apply, re-render with fake runners → assert the marker is gone,
  the detail renders as normal canonical content, and NO new CR is created. The auto-apply
  lane has its convergence test above; this gives the human-gated FR-016 lane the same
  deterministic regression instead of resting only on the manual e2e.
- `test_fr007_readonly_guard.py` extended: a full gap-fill pipeline run (fake runners)
  leaves the canonical `.collab.md` byte-identical — the ONLY mutation path remains the
  v2 writeback agent on CR approval.
- **Gap-injection test (SC-007):** start from a corpus fixture, delete a key detail
  (e.g. the data source of a metric), run the pipeline → assert (a) a gap was declared,
  (b) either a CR exists (grounded answer found in the fixture's `requirements.human.md`)
  or the render carries an explicit `.rr-gap` marker — and in NO branch does an unmarked,
  silently-incomplete render publish. Run both arms: answerable (detail present in raw
  upstream) and unanswerable (detail nowhere).
- Survival + carriage regression: `gate_html` green on a marked render (markers sit
  between block containers; anchorable text untouched).

Key activities:

- **`emit_change_requests` stage (filling 5a's stub):** for each `supplied` +
  evidence-validated gap, call **`change_request_service.create` directly** — the single
  governed write path the route itself runs (Decisions Made Autonomously #4) — with the
  column values listed in Verification (`kind="addition"`, `target_quote=None`,
  `section_hint` from the proposal). Status from `gate_status(kind, target_quote, policy)`
  exactly as the route derives it; the gate, policy flag, conflict predicate, writeback
  agent, outbox, and relay are all **consumed byte-unchanged**.
- **Dedupe before propose (no CR spam):** fingerprint = first 12 hex of `sha256(...)` over
  a STRUCTURAL key — `sorted(block_refs) + " " + section_title` as the primary
  component, with the question folded through a NAMED deterministic normalizer
  (`_normalize_gap_question`: casefold → collapse whitespace → strip trailing punctuation)
  as a secondary component (Plan Review CQ1). Keying on block_refs/section keeps the
  fingerprint stable when the WHAT agent re-words the question prose between renders — an
  unstable question-only hash is exactly the CR-spam this guards against. Embedded as
  `origin_artifact_path = "{what_doc_job_path}#gap={fp12}"`. Before creating, query
  `change_requests` for the goal — filter by `goal_slug` FIRST (the existing
  `idx_change_requests_goal_status` index) then substring-match the fragment: an
  O(CRs-per-goal) scan, not an indexed fragment lookup, accepted under HOLD (no new
  column; Plan Review P1) and bounded by per-goal CR volume. Skip when ANY row with the
  same fingerprint exists in `proposed` / `applied` / `conflicted` / `rejected` — only
  `superseded` frees re-proposal. A `rejected` match maps the gap to `unfilled-declined`
  ("asked and answered — do not re-ask the human").
- **Marker rendering (`.rr-gap`):** the HOW agent renders one themed callout per open
  gap inside its section — the `question`, a status line from a FIXED vocabulary
  ("a detail is missing here — proposed upstream, awaiting review" /
  "missing — upstream could not supply it" / "missing — a proposed detail was declined"
  / "missing from the requirements"), and nothing else. Each status string maps 1:1 to
  the `gaps-state.json` status enum (Plan Review A3). **The `proposed_body` never appears
  on the page** — it lives solely on the CR review surface (FR-016: the page never shows
  content that exists nowhere else; the CR DB is not "the page"). CSS in `_theme.css.j2`
  beside `.render-refreshing`; visually distinct (this is the honest-gap affordance SC-007
  demands), class-based only.
- **Un-mark is the existing machinery, verified not built:** approval → writeback
  surgical apply → version bump → source-hash change → stale render → next view
  regenerates → WHAT (reading the now-complete source) declares no gap. The convergence
  test in Verification pins it for the auto-apply lane; the gated-lane convergence test
  (Plan Review T1) pins the human-gated lane in CI, and a manual e2e walks the same lane
  in a browser (propose → marker visible → approve in the CR surface → re-view → marker
  gone, detail rendered as normal canonical content).
- **Checker gap-amnesty (4a coordination, one line):** add to the
  `cast-requirements-render-checker` prompt: "an explicitly-marked gap (`.rr-gap`) is
  honest communication, not a comprehension failure — judge the page given the gap, do
  not fail it for having one." Without this the quality loop would rework forever
  against a gap only a human can close. (See Suggested Revisions.)
- **Notification surface check:** a fast-track-applied gap CR rides the existing outbox
  → relay → `recent_writebacks` descriptor with its provenance badge sourced from
  `origin_*` ("from render-gapfill, by cast-requirements-gapfill") — assert the badge
  renders from existing code paths with zero new notification code.

**Design review:**
- **Spec consistency ⚠️ (the headline check):** gap-fill rides
  `cast-requirements-roundtrip.collab.md` FR-001/FR-002/FR-005/FR-013 *as a consumer*.
  One genuine touch: the spec's Out of Scope says real downstream emitters are deferred —
  this sub-phase ships the first one → conditional minimal spec delta in 5d. The intake
  handler, gate function, policy values, and writeback path are NOT modified — verified
  by leaving every roundtrip test untouched and green.
- **Architecture ✓** — no new writer, no lighter path: the only canonical-file mutation
  remains the v2 writeback agent behind the gate; the emitter is a *proposer*. The page
  ↔ canonical loop is closed by the existing cache/version machinery, not new state.
- **Error & rescue:** CR creation failure (DB error) → gap recorded
  `unfilled-ask-failed`, marker still renders, job row records the error — the render
  never blocks on the proposal store; next regen retries (dedupe finds no row, so the
  retry is natural).
- **Security:** `author_type` is hard-coded `"agent"` at the emitter (no spoof surface);
  `proposed_body` is exactly the evidence-validated answer; `base_version` read at
  emit time so the v2 conflict predicate guards a canonical that moved between ask and
  approval.
- **Naming ✓** — `.rr-gap` follows the `.rr-*` family; `origin_phase="render-gapfill"`
  follows the spec's `origin_phase` examples; status vocabulary in `gaps-state.json` is
  closed and gate-checked.

## Sub-phase 5c: Nine-Family Corpus & Golden Renders (parallel with 5a/5b)

**Outcome:** A representative, **authored-not-fiction** requirements document exists for
every one of the nine LOCKED `WorkFamily` values; each renders end-to-end through the
full pipeline (WHAT → gates → HOW → 4a quality loop); the nine pages are deterministically
distinct (pairwise different section-heading sets, no US/FR/SC slot headings, no padded
empty blocks) and per-family quality is read from the `human_review` flag (4a's hand-off);
any family that renders broken or padded is fixed at the WHAT-prompt / recipe-vocabulary
level. SC-002's evidence is *provisionally* captured here and finalized in 5d.

**Dependencies:** Phases 3 + 4a executed. Independent of 5a/5b (gap machinery dormant →
`gaps[]` empty → Phase 3/4a behavior), so 5c runs in parallel.
**Estimated effort:** 1.5 sessions.

**Verification:**
- `eval_family_sweep.py` (eval harness, `eval_` prefix — real pipeline, NOT default CI,
  extending the 3e/4a eval pattern) runs all nine corpus docs and asserts: pipeline
  terminal state ∈ {published, published+human_review} (never fallback, never failed);
  pairwise section-heading sets differ; no heading equals a US/FR/SC slot name; no empty
  section shells (US2 Scenario 2); `check_html` green per family; per-family checker
  verdict + score recorded.
- Corpus docs each pass `bin/cast-spec-checker`-adjacent shape checks: valid
  classification front matter (`family` pinned, `confirmed_by: "manual"`,
  `taxonomy_version: 1`), non-stub content.
- Golden renders + verdicts copied to
  `docs/goal/refine-requirements-better-rendering-v3/signoff/golden/{family}.html` (+ a
  one-page index) — the SC-002 evidence trail.
- Human-eyeball browser pass recorded as a carry-forward item (autonomous runs cannot
  drive a browser; static verdicts never block — per the standing project note).

Key activities:

- **Corpus strategy (authored, not fiction — every doc derived from REAL work):**
  - `new_initiative` — this goal's own `refined_requirements.collab.md` (real).
  - `bug_fix` — the Phase 1a authored doc built from the real `goal_card.py`
    markdown-leak defect (exists in `spikes/1a/`).
  - `data_analysis` — the Phase 1a stretch doc if authored; else author from a real
    investigation (e.g. the dispatcher slot-saturation analysis).
  - `refactor_migration` — author from the real per-goal `.cast` namespacing change
    (commit `b2e9661`).
  - `testing_qa` — author from the real UI-test sweep / runner-dispatch hardening work.
  - `pilot_poc` — author from a real spike (the Phase 1 maker spike itself is a
    legitimate PoC subject).
  - `random_idea` — author from a real captured idea (one-paragraph source is fine —
    this family IS the structural floor; its render should be honest about thinness,
    not padded).
  - `personal_non_eng` — author from a real personal/non-engineering task of the owner's.
  - `generic` — a deliberately family-ambiguous doc (exercises the model-selected
    unmatched-fallback path).
  Each gets pinned classification front matter so the sweep never depends on classifier
  agreement (classifier behavior is `cast-goal-classification.collab.md` scope, consumed
  not tested here).
- **Location:** `cast-server/tests/fixtures/family_corpus/{family}/refined_requirements.collab.md`
  — importable by the 5b gap-injection test and the eval harness; goal-dir copies only
  for the rendered evidence (keeps `goals/{slug}/` runtime dirs and the FR-026 invariant
  untouched).
- **Run the sweep; fix the broken-or-padded.** The fix loop operates ONLY at the
  vocabulary/prompt level: per-family guidance in the `cast-requirements-what` prompt
  and `FAMILY_RECIPES` recipe wording in `families.py` (starting vocabulary — tuning its
  *wording* is in scope; the nine-value enum is LOCKED, the 6-block recipe model shape is
  not redesigned). Record a before/after note per fixed family. Padding fixes flow
  through US2 Scenario 2 (omit, never pad).
- **Read `human_review` as the per-family quality signal** (the 4a hand-off): a family
  that converges only with a flag is a finding — fix its vocabulary, or carry the flag
  into 5d's sign-off as an honest open item; never suppress the flag.

**Design review:**
- **Architecture ✓** — the sweep exercises production code paths via the established
  eval-harness pattern; no test-only render path is built.
- **Spec consistency ✓** — nine-family verification realizes the render spec's SC-002
  as narrowed by 3e/4a (LLM-judged happy path, deterministic fallback substrate
  untouched); the LOCKED enum is consumed from `cast-goal-classification.collab.md`,
  not modified.
- **Code quality:** corpus docs are fixtures with provenance headers (one comment line:
  what real work each was authored from) so a future reader knows they are
  representative, not synthetic noise.
- **Error & rescue:** a family whose render goes to deterministic fallback in the sweep
  is a hard finding (the happy path must work for every family) — the eval asserts it,
  never papers over it.

## Sub-phase 5d: Full SC Sweep, Final Spec Reconciliation & Sign-Off

**Outcome:** SC-001…SC-008 are swept against the integrated system with results captured
in a sign-off artifact; the accumulated cross-phase coordination notes are verified
landed (drift sweep); `cast-requirements-render.collab.md` records the shipped v3
behavior including gap-fill; `cast-requirements-roundtrip.collab.md` gets its one
conditional minimal delta (first real emitter) or a recorded no-change rationale; the
goal is signed off with every flag and carry-forward stated, none suppressed.

**Dependencies:** 5a + 5b + 5c.
**Estimated effort:** 1 session.

**Verification:**
- `docs/goal/refine-requirements-better-rendering-v3/signoff/sc-sweep.md` exists with a
  per-SC row: procedure run, result, evidence link, residual flags.
- `bin/cast-spec-checker` green on both updated specs; `docs/specs/_registry.md` rows
  bumped.
- Full test suite green (`pytest cast-server/tests/`), eval harness results recorded.
- The sign-off lists every `human_review`-flagged family render and every human-eyeball
  carry-forward as explicit open items.

Key activities:

- **The SC sweep — each criterion against the integrated system:**
  - **SC-001** (cold reader): the 4a checker verdicts from the 5c sweep, per family —
    the checker stands in for the human reader (its verdict shape is a strict superset
    of v2 SC-001 by 4a design).
  - **SC-002** (nine distinct families): RE-RUN `eval_family_sweep.py` after 5a/5b land
    (gap machinery live) so the final evidence reflects the shipped pipeline — the
    harness exists, the re-run is cheap; refresh `signoff/golden/`.
  - **SC-003** (comment survival): re-run 4b's SC-003 eval sweep on a regenerate with
    open comments through the integrated pipeline.
  - **SC-004** (no-output crash → deterministic): re-run 3c's fault-injection (fake
    runner crash) + one live kill of a real job.
  - **SC-005** (cache hit): repeat-view observation — second view serves the cached
    file, `render_jobs` shows no new row.
  - **SC-006** (discoverable commenting): Phase 2's affordance — static verdict +
    human-eyeball carry-forward (unprompted-usability is a human check by nature).
  - **SC-007** (gap injection): the 5b gap-injection test, both arms, plus one live
    end-to-end run against a corpus doc with a deleted detail.
  - **SC-008** (non-convergence → best-attempt + flag): re-run 4a's force-never-pass
    eval; assert best-scoring valid attempt served, `human_review` recorded,
    deterministic page NOT served.
- **Integration drift sweep** (the reconciliation duties prior phases deferred to "the
  merge" — verify landed, fix residue):
  - 4a→3 corrections: reaper ceiling derived from the full configured stage list
    (quality-loop-sized); reaper releases the in-flight semaphore slot of a reaped
    orphan; `heartbeat_at` written at stage boundaries — **now extended for the 5a gap
    stages** (the ceiling formula must include `gapfill_timeout` + the ask-round WHAT
    re-run; heartbeats at each new stage boundary). The gap-ask WHAT re-run
    (`GAPFILL_ASK_ROUNDS`) is a SEPARATE counter from the in-loop
    `QUALITY_MAX_WHAT_REWORKS` (Plan Review A2) — the merge must not collapse them into
    one budget.
  - 4b seam pin: survival evaluated inside `gate_html` before `run_checker`; a
    survival-failing attempt is never a "structurally-valid attempt" for the
    best-scoring-valid serve — confirm the merged loop honors it with gap markers
    present.
  - 3b walker helper shared with 4b (no copied container-text walker); single
    `strip_inline_markdown` (no second stripper anywhere, including the new gap code);
    single `verbatim_locate` (the 5a evidence check reuses it, no second locate — Plan
    Review CQ2).
  - 5b checker gap-amnesty line present in the checker prompt.
- → Delegate: `/cast-update-spec` on `cast-requirements-render.collab.md` (review the
  diff before approval, per the skill's gate) with these deltas:
  1. **Gap-fill contract (FR-015/FR-016 realized):** the activated `gaps[]` schema; the
     HOW trailer ask-channel + the bounded ask loop (`GAPFILL_ASK_ROUNDS`,
     `GAPFILL_MAX_GAPS`); the `cast-requirements-gapfill` agent (tool-free subagent
     carve-out, grounded-or-refuse, corpus allowlist, server-side verbatim evidence
     validation via the shared `verbatim_locate`); gap CRs gate-pinned to `kind="addition"`;
     the `.rr-gap` marker contract (question + fixed status vocabulary, NEVER the proposed
     answer) and the page-renders-only-canonical-content invariant with its
     un-mark-via-regeneration mechanism; gap CRs as normal change-requests (provenance
     values recorded).
  2. **Nine-family verification record:** SC-002's evidence procedure (corpus +
     `eval_family_sweep.py` + `human_review` signal) recorded as the standing
     verification for the happy path.
  3. New surfaces appended to `linked_files`: the gapfill agent dir, the gap additions
     in `maker_gate.py` / `render_job_service.py`, `gaps-state.json` shape,
     `test_gap_reconciliation.py`, the corpus fixtures dir.
- → Delegate: `/cast-update-spec` on `cast-requirements-roundtrip.collab.md` —
  **conditional minimal delta:** narrow the Out-of-Scope "real downstream emitters"
  fence to record the first real emitter (render gap-fill; emitter-side only —
  intake/gate/apply contracts unchanged), add the emitter to `linked_files`. If the
  diff review concludes even this is over-reach, record the explicit no-change rationale
  in `sc-sweep.md` instead — either way the decision is written down, not silent.
- **Write the sign-off** (`signoff/sc-sweep.md` + a closing note in the goal dir):
  what's green, what's flagged (`human_review` renders, human-eyeball carry-forwards),
  what stays deferred (**[USER-DEFERRED]** model tier; the human-review queue UI from
  4a's open questions; the v2 timed-read evaluation) — the "put in front of a customer
  without apologizing" bar, with the apologies that DO remain stated explicitly.

**Design review:**
- **Spec consistency ✓ (this IS the spec work)** — all 5a/5b flags resolve in one render-
  spec pass; the roundtrip touch is minimal and conditional; clause texts were fixed by
  this plan up front (the 3e discipline: the spec records behavior, never retro-discovers
  it).
- **Tests ✓** — the sweep re-runs existing verification machinery; nothing is asserted
  by hand that a harness already proves; eval results are committed evidence, not
  ephemeral terminal output.
- **Process:** sign-off lists every residual flag explicitly — a flagged render or a
  carried-forward eyeball check is an honest open item, never silently dropped at the
  finish line.

---

## Build Order

```
Sub-phase 5a (gap contract + ask loop) ──► Sub-phase 5b (gate reconciliation + markers) ──► Sub-phase 5d (SC sweep + spec + sign-off)
Sub-phase 5c (nine-family corpus + golden renders) ────────────────────────────────────────────┘
   (parallel with 5a/5b)
```

**Critical path:** 5a → 5b → 5d (≈ 4–4.5 sessions). 5c (1.5 sessions) runs fully in
parallel, so wall-clock stays within the high-level 3–5 session estimate; total effort
is 5.5–6 sessions if executed serially.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 5a | gaps schema / trailer / gapfill agent are new spec'd behavior | Clause texts fixed in this plan; single `/cast-update-spec` in 5d |
| 5a | Ungrounded gap answers could reach canonical | Server-side `validate_evidence` (shared `verbatim_locate` in allowlisted corpus) before any CR; demotion recorded |
| 5a | `GAP-NN` could collide with canonical ref space | Gate rejects `GAP-` tokens as canonical refs; markers are class-based, no DOM ids |
| 5b | Roundtrip spec's "real emitters deferred" fence is touched by the first real emitter | Conditional minimal `/cast-update-spec` delta in 5d (or recorded no-change rationale) |
| 5b | CR spam across regenerations / after human rejection | Structural fingerprint dedupe (block_refs+section primary) over `proposed`/`applied`/`conflicted`/`rejected`; only `superseded` re-proposes |
| 5b | Auto-applied addition could loop (propose → regen → re-propose) | Convergence test: post-apply WHAT run detects no gap; compare-and-publish supersedes the in-flight job |
| 5b | Quality loop could rework forever against an honest gap | Checker gap-amnesty prompt line (4a coordination) |
| 5b | Gap markers could break carriage/survival gates | Markers sit outside anchorable block text; `gate_html` regression test with markers present |
| 5c | Corpus fiction would make SC-002 evidence hollow | Authored-not-fiction rule: every doc derived from named real work, provenance header per fixture |
| 5d | 4a/4b coordination notes could silently not have landed | Explicit integration drift sweep with named items; gap stages added to the reaper-ceiling formula |
| 5d | Spec version bumps + registry rows | Included in both `/cast-update-spec` activities |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| WHAT over-detects gaps (trivia-hunting) and floods the CR surface | Med | "Materially help the reader" bar verbatim in the prompt; `GAPFILL_MAX_GAPS` cap; fingerprint dedupe; checker amnesty removes any incentive to gap-hunt for score |
| Gapfill agent supplies plausible-but-ungrounded answers | High | Grounded-or-refuse contract + server-side verbatim evidence validation (shared `verbatim_locate`) — an unverifiable answer is structurally demoted to cannot-supply and never reaches the gate |
| Fast-track auto-apply (default policy) lands agent-drafted text in canonical without a human click | Med | It is the spec'd v2 graduated-trust behavior, notified via outbox FYI, surgical, conflict-guarded, and fully audited; the taste call is surfaced (Open Questions) with the sanctioned global knob (`gate-all`) — never a silent per-origin fork |
| A family can't clear the quality bar even after vocabulary fixes | Med | `human_review` flag is the honest terminal state — carried into sign-off as an open item, never suppressed; fix loop is bounded to prompt/recipe wording under HOLD scope |
| Gap machinery + quality loop interplay creates unbounded agent runs | Med | All gap stages run once per job before the loop (`GAPFILL_ASK_ROUNDS=1`, one gapfill run); the 4a ceiling + the extended reaper formula bound the whole job |
| Prior-phase execution diverged from planned interfaces (this plan was written before 3/4a/4b ran) | Med | Depends-On names contracts, not line numbers; 5d's drift sweep verifies the coordination notes; deviations inherit executed names per the decisions-so-far discipline |
| Dedupe pre-check is an unindexed `origin_artifact_path` fragment scan | Low | Filter by `goal_slug` first (indexed via `idx_change_requests_goal_status`), then substring-match the fingerprint — O(CRs-per-goal), bounded; no new column under HOLD (Plan Review P1) |
| No browser in autonomous runs for the nine-family visual review | Low | Static verdicts (checker + deterministic distinctness assertions) + human-eyeball carry-forward recorded — never blocks (standing project note) |

## Open Questions

- **Owner taste check (non-blocking, default = keep current):** under the v2 default
  `WRITEBACK_GATE_POLICY="gate-except-additions"`, a *pure-addition* gap answer
  fast-tracks to `applied` (with FYI notification) — agent-drafted, evidence-grounded
  text reaches canonical without a human click. The gate is consumed unchanged (binding
  decision), and the FR-016 page invariant holds either way. If the owner wants every
  gap answer human-gated, the sanctioned knob is the **global** `gate-all` config value
  (affects all writebacks; a per-origin policy would change the gate, which HOLD scope
  forbids). Default this plan assumes: keep `gate-except-additions`.
- **Carried forward, unchanged:** **[USER-DEFERRED]** maker/checker/gapfill model tier
  (config-file knob, placeholder values); the human-review queue UI (4a open question —
  flags are recorded and queryable; a review surface is a future-goal owner call).

## Decisions Made Autonomously (per the autonomous-run instruction)

1. **Gap answers flow under the EXISTING global gate policy, unchanged.** The binding
   decision says the v2 change-request gate is consumed unchanged; the roundtrip spec's
   owner decision #3 explicitly rejected per-element policies. So gap CRs take whatever
   lane `gate_status` gives them — fast-track-applied additions included. The FR-016
   invariant is unaffected because the page only ever renders canonical content. The
   residual taste call (global `gate-all`) is surfaced above, not silently decided.
2. **The "refine agent" ask target is realized as net-new `cast-requirements-gapfill`**
   (FR-010's "plus helpers as needed"), not an extension of the interactive
   `cast-refine-requirements`: the interactive agent's AskUserQuestion protocol is a bad
   headless citizen, and the carve-out precedent (classifier, reanchor, WHAT/HOW) is the
   established shape for tool-free `claude -p` helpers. The gapfill agent IS the refine
   layer's knowledge applied headless: it answers only from the refine pipeline's own
   upstream artifacts.
3. **Grounding corpus = the goal's own upstream artifacts only** (`requirements.human.md`,
   `research_notes.human.md`, `exploration/`), resolved by the runner as an explicit
   allowlist. The wider repo is not a requirements source; "upstream cannot supply"
   (US7 Scenario 2) means *these files don't contain it*, which is exactly the honest
   answer the marker should report.
4. **CR emission calls `change_request_service.create` directly** rather than
   HTTP-self-POSTing the same-door route. Grounds: `create` IS the single governed write
   path (roundtrip FR-002 — the route is the identity-stamping door for *external*
   actors); the emitter stamps exactly what the route's agent lane would
   (`author_type="agent"`, self-declared author, origin columns); a server HTTP call to
   itself adds a port/config/test liability for zero governance gain. If review prefers
   the literal one-door reading, the swap is a one-function change.
5. **The page never renders a gap answer — only the question + a fixed status
   vocabulary.** The `proposed_body` lives solely on the CR surface until approved into
   canonical. This makes FR-016 structural: there is no code path by which un-approved
   text reaches a reader as requirement content.
6. **HOW-asks-WHAT is a bounded structured round-trip** (trailer outside the sentinels →
   one WHAT re-run with questions appended), not free-form agent-to-agent chat: it keeps
   the WHAT doc the single source of section/gap truth, keeps strict sentinel extraction
   untouched, and bounds agent invocations per job.
7. **Dedupe fingerprint rides `origin_artifact_path`** as a `#gap=<fp12>` fragment —
   the schema gains no column (gate unchanged), the fragment is parseable, and the
   column still carries the real artifact path. Alternative (a JSON payload in the first
   event row) was rejected as harder to query.
8. **Corpus fixtures live in `cast-server/tests/fixtures/family_corpus/`** (importable
   by tests + eval), with rendered evidence copied to the goal's `signoff/` dir; SC-002's
   final evidence is regenerated in 5d after gap machinery lands, so the sign-off
   reflects the shipped pipeline, not a pre-integration snapshot.
9. **4b's narration surface is NOT adopted for gap-fill round-trip summaries.** 4b left
   it as an option; the existing `recent_writebacks` provenance descriptor already
   surfaces gap CRs with zero new code, and narration is per-version-boundary, not
   per-CR. Recorded so the option is closed deliberately, not forgotten.
10. **Gap stages run once per job, before the 4a quality loop** — the loop reworks HOW
    attempts against fixed gap state. Re-asking upstream per quality attempt would
    multiply agent runs for no comprehension gain (the gap set is a property of the
    source, not of a rendering attempt) and honors FR-015's "before finalizing".

## Suggested Revisions to Prior Sub-Phases

- **Phase 4a (additive, one line):** the `cast-requirements-render-checker` prompt gains
  the gap-amnesty clause ("an explicitly-marked `.rr-gap` is honest communication, not a
  comprehension failure"). Without it the quality loop and the gap contract fight each
  other — the loop would burn attempts trying to rework a gap only a human can close.
  No 4a decision is overturned; checker input stays artifact + family.
- **Phase 3/4a (formula extension, already in their spirit):** the reaper ceiling
  formula and the `heartbeat_at` stage boundaries must include the three new gap stages
  (`ask_what` re-run, `run_gapfill`, `validate_evidence`/`emit_change_requests`) — the
  4a revision derived the ceiling "from the configured stage list", so this is that
  formula doing its job, flagged so the merge includes the new stages. The
  `GAPFILL_ASK_ROUNDS` counter stays independent of the in-loop `QUALITY_MAX_WHAT_REWORKS`
  (Plan Review A2).
- **Phase 3 (contract addition at a designed seam):** the HOW agent contract gains the
  optional `GAPS-DETECTED` trailer *outside* the sentinels; strict extraction and the
  no-output classification are byte-untouched. The WHAT contract's reserved `gaps[]`
  field gains its entry schema — the seam Phase 3 explicitly reserved for this phase.
- None that change a prior decision.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` (v3 after 3e/4a-3/4b-4) | Maker contract + WHAT-doc schema (gains `gaps[]` activation); pipeline stages (gains gap stages); DOM contract (preserved — `.rr-gap` is class-based, zero `id=`); FR-028 progressive enhancement (markers are static content); SC-001/SC-002 verification (sweep procedures recorded) | 1 family of additions — all resolved by the single `/cast-update-spec` pass in 5d (gap-fill contract, marker vocabulary, nine-family verification record) |
| `cast-requirements-roundtrip.collab.md` (Draft v1) | FR-001/FR-002 (same-door, one write path); FR-005 (`gate_status` + global policy); FR-006 (status lifecycle — dedupe reads it); FR-013 (provenance badge from `origin_*`); US2/US3/US5 (graduated trust, conflict, notification — all consumed) | 1 minor — Out of Scope defers "real downstream emitters"; 5b ships the first one → conditional minimal delta in 5d (intake/gate/apply contracts unchanged); `cast-goal-classification.collab.md` is consumed via `families.py` only (LOCKED enum, not loaded as a third spec) |

## Plan Review Decisions (cast-plan-review, BIG CHANGE scope — autonomous)

Reviewed under HOLD scope; every fork auto-decided against the binding owner decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`. **None of the
findings re-open an owner-resolved decision** (gap-fill reconciles through the v2
change-request gate unchanged; the maker never fabricates; the nine-family enum is LOCKED;
`scope_mode: hold`). All sharpen the emitter contract, the dedupe/evidence trust boundary,
status-vocabulary coherence, and test determinism *within* the existing Phase-5 design.
Phase 3/4a/4b internals stayed out of scope (consumed as interfaces); planning-only — no
implementation was reviewed. Findings grounded against the live
`cast-server/cast_server/services/change_request_service.py` (`gate_status` keys the
addition fast-track on `target_quote is None`; `apply` locates modifications via
`verbatim_locate`/`detect_conflict`; `create` signature; `idx_change_requests_goal_status`).
Per the B2 single-Write contract this appendix and the inline body sharpenings above were
committed in one write. Mirrors the depth and appendix format of the Phase 3 review.

Summary: 9 issues found / 9 resolved / 0 deferred (Architecture 3, Code Quality 2, Tests 3,
Performance 1).

- **2026-06-12T09:40:00Z — A1 — Architecture: is a gap answer's `kind` constrained so the v2 writeback can actually apply it?** — Decision: Sharpen — gate-pin `proposed_change.kind` to `addition` (no `target_quote`); a gap is *missing* content, never a rewrite. Rationale: a `modification`-kind gap CR carries no `target_quote`, so `change_request_service.apply`'s `locate`/`detect_conflict` would refuse it `orphaned`, and `gate_status` fast-tracks only `target_quote is None` additions; the plan's "typically addition" hedge left a non-appliable modification path open. The gate is consumed unchanged — this constrains the emitter, not the door. (Body patched: 5a gapfill output schema, 5b emit_change_requests + Verification.)
- **2026-06-12T09:40:00Z — A2 — Architecture: does the `ask_what` WHAT re-run share 4a's `QUALITY_MAX_WHAT_REWORKS` budget?** — Decision: Sharpen — declare the counters independent: `GAPFILL_ASK_ROUNDS` (one pre-loop WHAT re-run for gap detection) is separate from 4a's in-loop `QUALITY_MAX_WHAT_REWORKS=2`. Rationale: gap stages run once before the loop; a job that spent its gap-ask WHAT re-run must keep its full in-loop WHAT-escalation budget, else gap-bearing renders are silently throttled at the quality bar. (Body patched: 5a pipeline stage 3, 5d drift sweep, Suggested Revisions.)
- **2026-06-12T09:40:00Z — A3 — Architecture: is there one closed status vocabulary across gaps-state, page markers, and job-row reasons?** — Decision: Sharpen — the `gaps-state.json` status enum is THE single closed vocabulary; 5b's fixed marker strings and the job-row reason codes map 1:1 to it via an explicit table, gate-checked (`maker_gate` rejects any out-of-enum status). Rationale: three parallel vocabularies (gaps-state statuses, marker text, reasons like `evidence-validation-failed`) drift silently; one enum + one mapping keeps "zero silent failures" honest. (Body patched: 5a gaps-state bullet, 5b marker rendering.)
- **2026-06-12T09:40:00Z — CQ1 — Code Quality: is the dedupe fingerprint stable across LLM re-wording of the gap question?** — Decision: Sharpen — key the fingerprint on `sorted(block_refs) + section_title` as primary, folding the question through a NAMED deterministic normalizer (`_normalize_gap_question`: casefold → collapse whitespace → strip trailing punctuation) only as a secondary component. Rationale: the WHAT agent re-emits question prose every render; an LLM rewording silently changes a question-derived hash → the exact CR-spam the plan flags as a risk; block_refs/section are structural and stable. (Body patched: 5b dedupe bullet.)
- **2026-06-12T09:40:00Z — CQ2 — Code Quality: does evidence validation reuse the writeback's locate or a separate `find()`?** — Decision: Sharpen — `validate_evidence` reuses the existing `verbatim_locate` helper over the corpus, not a raw `str.find()`. Rationale: one locate implementation (DRY) shared with the v2 backstop, and it avoids false `cannot-supply` demotions when an evidence quote differs from the corpus only by whitespace/smart-quote — the "never fabricates" trust boundary becomes a deliberate, single shared semantic. (Body patched: 5a validate_evidence bullet, 5d drift sweep, Design Review Flags / Key Risks.)
- **2026-06-12T09:40:00Z — T1 — Tests: is the human-gated un-mark lane covered automatically or only by manual e2e?** — Decision: Sharpen — add an automated gated-lane convergence test: emit a gated gap CR (under `gate-all`, or any non-fast-tracked lane), apply it in-test via `change_request_service`, re-render with fake runners, assert the marker is gone and no new CR. Rationale: today only the auto-apply lane has a deterministic convergence test; the human-gated lane (the FR-016 headline) rested on a manual e2e that autonomous runs cannot execute — both lanes need automated regression. (Body patched: 5b Verification + un-mark activity.)
- **2026-06-12T09:40:00Z — T2 — Tests: is the evidence verbatim-locate boundary pinned by a parity test?** — Decision: Sharpen — add a test pair: an evidence quote differing from the corpus only by whitespace MUST validate (post-CQ2 `verbatim_locate` reuse); a substantively-different quote MUST demote to `cannot-supply` with the reason recorded. Rationale: the boundary's locate semantics are load-bearing for "never fabricates"; without a pinning test a future locate change silently widens or narrows the trust boundary. (Body patched: 5a Verification.)
- **2026-06-12T09:40:00Z — T3 — Tests: is gap-marker correspondence proven for the multi-gap case?** — Decision: Sharpen — add a two-open-gap fixture asserting exactly two `.rr-gap` containers each matching its own `question`; a render that merges two gaps into one marker, or swaps their questions, fails `check_html`. Rationale: the plan states correspondence for the single-gap case; the silent-merge / swapped-question failure modes (a gap effectively dropped) need an explicit multi-gap negative test. (Body patched: 5a Verification, maker_gate extensions.)
- **2026-06-12T09:40:00Z — P1 — Performance: is the dedupe pre-check an indexed lookup or a scan?** — Decision: Accept + document — the fingerprint lives in the `origin_artifact_path` fragment (no index; HOLD forbids a new column); the pre-check narrows by `goal_slug` via `idx_change_requests_goal_status` then substring-matches, an O(CRs-per-goal) scan. Acceptable at expected per-goal CR volume; recorded as a known bound so a future scale problem is anticipated, and the query MUST filter by goal first (never a global table scan). Rationale: indexing the fragment would need a schema change HOLD scope forbids; per-goal narrowing keeps the scan bounded. (Body patched: 5b dedupe bullet, Key Risks.)
