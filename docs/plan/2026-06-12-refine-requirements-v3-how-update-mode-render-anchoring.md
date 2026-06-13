# Refine Requirements Better Rendering V3: HOW Two-Mode + Render-Snapshot Anchoring (Post-Phase-5 Follow-Up)

## Overview

The Phase-5c nine-family sweep published all nine families but flagged three (`bug_fix`,
`pilot_poc`, `random_idea`) as HOW-layer carry-forwards. The owner's diagnosis: the HOW maker
treats CREATE and UPDATE identically — it regenerates the whole page from scratch on every source
edit, which is exactly when it paraphrases lead units and trips the verbatim-carriage gate. The
deeper reframe (decisions-so-far.md, "Post-Phase-5 follow-up"): **verbatim carriage was never the
goal — the most human-readable page is.** Verbatim was only a proxy that kept source-anchored
comments placeable. This plan removes the proxy properly: HOW gets a two-mode contract
(CREATE = fresh, readability-first, paraphrase freely; UPDATE = start from the prior render,
re-render only changed blocks, keep unchanged blocks byte-identical), and comment anchoring moves
from the canonical source to the **rendered-page snapshot** — UPDATE mode is precisely what keeps
render-anchored comments alive across edits. A massive-change threshold flips UPDATE back to CREATE.

This is a follow-up phase to the v3 goal (`docs/goal/refine-requirements-better-rendering-v3/`),
planned per the owner's "PLAN IT PROPERLY FIRST" decision (2026-06-12). **Execution starts after
Phase 5d sign-off** (the current SC-002 sweep record is the 5c provisional; 5d finalizes it).

## Operating Mode

**HOLD SCOPE** — the owner direction is an enumerated feature set: "the plan = {two-mode HOW} +
{relax leaf-text verbatim for readability} + {comment anchoring source→render snapshot} +
{massive-change threshold} + regression tests + re-run the 3 flagged families", explicitly framed
as "a small detailed plan". No extras, no cuts. The borderline item — whether the `pilot_poc`
(HOW invents ids) and `random_idea` (pads empty shells) fixes are in scope — is resolved IN by the
stated validation target: "re-run the 3 flagged families → clean" is unreachable without them
(`bug_fix` is the verbatim/UPDATE failure; the other two are distinct HOW defects). They get one
small dedicated sub-phase, not gold-plating.

## The Crux Decision (locked here): comments anchor to the render snapshot

**Decision: render-snapshot anchoring.** A comment's `quoted_text` is minted from, validated
against, displacement-checked against, and re-anchored within the **published render's container
text** (the same `container_text_index` text space `maker_gate` already walks) — no longer the
canonical `.collab.md`. A server-resolved **`block_ref` bridge** (the canonical id of the unit
container the quote landed in, resolved via the render's visible anchor labels) keeps every
comment traceable back to source space, so the comment→change-request→writeback flow keeps a
deterministic source handle even when the rendered text is a paraphrase.

What this reverses — flagged loudly, per the brief, because it is the load-bearing call:

- **The Phase-1b/Phase-3 "verbatim-carriage clause"** (spec `cast-requirements-render.collab.md` >
  US16 — Logical id backbone and verbatim carriage): blanket verbatim carriage is **superseded**.
  What survives of US16: anchor labels (canonical ids printed verbatim exactly once) and the
  one-unit-one-container DOM rule. What's removed: the copy-exact obligation on leaf requirement
  text in CREATE mode.
- **The v2 source-anchoring contract** (spec > US8/US12: quote validated against the source;
  `displaced = quoted_text not in current_text` where `current_text` is the `.collab.md`): both
  re-target the served render artifact.
- **4b's survival classification** (spec > US19: in-block = quote ⊆ source anchorable text):
  reorients to render space — in-block = the quote placed inside a labeled unit container on the
  render it was minted against; survival = it places in the same `block_ref`'s container on the
  next render. UPDATE-mode byte-identity makes survival structural for unchanged blocks; comments
  on modified/removed blocks route to re-anchoring instead of blocking.

Why this is safe to lock without a spike: the placement machinery is *already* render-side
(`requirements_comments.js` does `indexOf` over the rendered DOM; quotes are minted by selecting
rendered text). Only the *validation/displacement* reads point at the source today. The genuinely
unproven assumption is elsewhere — that UPDATE mode can actually hold unchanged blocks
byte-identical — and that is Sub-phase 1's spike, which gates the Sub-phase 3 design choice
(gate-enforced LLM copy vs. deterministic splice), **not** the anchoring decision itself.

## Depends On (from prior phases — consumed interfaces)

- `requirements_render/maker_gate.py` — `container_text_index` (the single DOM walker),
  `check_html`, `check_comment_survival`, `_anchorable_paragraphs`, `GateReport`.
- `requirements_render/block_diff.py` — `diff_blocks`/`summarize` (the deterministic changed-set;
  extend-never-fork, FR-024).
- `services/render_job_service.py` — `JobState`, the named stage seam
  (`run_what → gate_what → [gap stages] → run_how → gate_html → run_checker → decide_quality →
  publish`), `_build_how_prompt`, `_compare_and_publish`, the job dir
  `build/render-jobs/{slug}/{hash12}/`, `RENDER_STAGE_TIMEOUTS` (reaper formula reads it).
- `services/requirements_render_service.py` — `publish_maker_html` (served-by / human-review /
  source-hash envelope), `current_source_hash`, `RenderResolution`.
- `services/comment_service.py` — flat-fn comment CRUD + derived read-time `displaced`;
  `requirements_render/comment_anchor.py` — `resolve_block_ref` (source-space resolver).
- `agents/cast-comment-reanchor/` contract v2 (optional inputs, `relocated > resolved >
  orphaned`-when-unsure, 422 verbatim backstop) — extended additively to v3, never replaced.
- `cast-server/tests/eval_family_sweep.py`, `eval_sc003_survival.py`,
  `tests/fixtures/family_corpus/` — the validation harnesses.
- Owner principles binding on every fork here: **surface, don't suppress** (degraded output ships
  flagged + machine-readable, never a silent swap) and the structural override (deterministic
  fallback ONLY on literal no-output).

---

## Sub-phase 1: Evidence — UPDATE Byte-Fidelity & Render-Anchor Dry-Run (1a ∥ 1b)

**Outcome:** The one load-bearing unknown is answered with measurements: whether the HOW agent can
hold unchanged unit containers byte-identical when handed a prior render + a changed-block list
(1a), and the placement/bridge rate of real existing comments against published render text (1b).
1a's verdict selects the Sub-phase 3b UPDATE mechanism; 1b sizes the Sub-phase 2 migration.
**Dependencies:** None (Phase 5d sign-off is an execution-start gate, not a data dependency).
**Estimated effort:** 2 sessions (the two spikes run in parallel).
**Verification:** Evidence notes + raw trial artifacts at
`docs/goal/refine-requirements-better-rendering-v3/spikes/update-fidelity/` and `spikes/render-anchor/`,
each ending in an explicit PASS/FAIL verdict against the criteria below.

Key activities:

- **1a — UPDATE byte-fidelity spike.** Take the two clean published goldens (`new_initiative`,
  `data_analysis` from `signoff/golden/`) **plus one `bug_fix`-class doc** — the family whose
  lead-unit paraphrase is the entire reason this plan exists; an UPDATE-fidelity spike that never
  exercises the failing family measures the wrong thing (plan-review Issue #4). Use their corpus
  sources; author 2-3 small source edits each (one modified FR body, one added SC, one removed
  bullet). Prototype an UPDATE prompt
  (prior render + `block_diff` changed-set + "copy unchanged containers byte-exact" obligation)
  against the production `cast-requirements-how` agent via the `eval_*`/`agent_service` subprocess
  pattern. Measure per-trial: fraction of unchanged unit containers byte-identical (compare via
  `container_text_index` container text + raw HTML slice), correctness of changed-block re-renders,
  and whether removed blocks are dropped. **Success = ≥95% of unchanged containers byte-identical
  across ≥5 trials per doc** (≥3 was statistically too thin to resolve a 95% bar — at 3 trials a
  single miss reads as 67%, not signal; ≥5 per doc across the three docs gives the
  mechanism-selecting gate real resolution — plan-review Issue #4). PASS → Sub-phase 3b uses
  *gate-enforced LLM copy* (HOW emits the full
  page; a new deterministic gate verifies byte-identity, violations get the standard structural
  retry). FAIL → Sub-phase 3b uses *deterministic splice* (server keeps unchanged container bytes
  from the prior render and splices HOW-rendered changed-block fragments; byte-identity becomes
  guaranteed by construction, at the cost of a fragment-rendering HOW sub-contract). Record the
  verdict in the spike note — it is a decision gate, not advisory.
- **1b — render-anchor dry-run.** Re-validate every existing open comment (the v2 fixture pair
  `refined_requirements.collab.md` + `.v2-edit`, plus any live comments on the v3 goal) against the
  corresponding published render text: does the quote place (`container_text_index.find`)? Does it
  resolve to a single labeled unit container (`unit_at` + the anchor label → the `block_ref`
  bridge)? Measure placement rate and cross-boundary rate. **Success = every comment minted via
  the page UI places, and in-block quotes resolve a unique `block_ref`; misses are classifiable**
  (cross-boundary / decoration-spanning), not mysterious. This is a Python re-implementation
  dry-run (no browser — autonomous runs can't connect Chrome; per project convention the
  visual half is a static verdict + human-eyeball carry-forward).
- Both spikes are read-only against production code — no production edits in Sub-phase 1.

**Design review:**
- Naming: spike dirs use descriptive slugs (`update-fidelity/`, `render-anchor/`) following the
  Phase-1 `spikes/{1a,1b}/` precedent of keeping spike evidence away from render-class filenames
  and CI collection. ✓
- Error paths: 1a must record *what kind* of byte-divergence occurs (whitespace-only vs. reworded)
  — a whitespace-only failure mode argues for a normalization layer, not a splice; don't collapse
  the two.

## Sub-phase 2: Anchor Move — Comments Anchor to the Render Snapshot

**Outcome:** A comment's full lifecycle (create/validate, displacement, relocate backstop,
re-anchor dispatch) runs against the published render's text with a server-resolved `block_ref`
bridge to canonical source space; every pre-existing comment migrates without loss (worst case:
the existing `.comment-unplaced` badge, never deletion or silent orphaning). The verbatim-carriage
gate is **still in force** at the end of this sub-phase — anchoring moves first, the carriage flip
(Sub-phase 3b) only happens once comments no longer depend on it.
**Dependencies:** Sub-phase 1 (1b sizing). Runs in parallel with Sub-phase 3a.
**Estimated effort:** 3-4 sessions.
**Verification:** `pytest` over `comment_service`/`comment_anchor`/migration tests green;
`tests/test_schema_migration.py` extended and green; a manual same-door `curl` create against a
maker render resolves a correct `block_ref`; existing v2 comment fixtures still list/place;
`eval_reanchor.py` green against the v3 contract.

Key activities:

- **Schema (additive only):** `requirement_comments` gains `block_ref TEXT NULL` and
  `anchor_space TEXT NOT NULL DEFAULT 'source'` (`'source'` | `'render'`). Extend
  `db/schema.sql` + the migration test. Nothing existing is rewritten; old rows keep
  `anchor_space='source'`.
- **Creation path:** `create_comment` (same-door, `author_kind` untouched — FR-013) resolves
  `block_ref` server-side: read the *served* artifact, `container_text_index` it, place the quote,
  take the enclosing labeled unit container's canonical id; cross-boundary → `NULL` (never
  guessed — the `resolve_block_ref` orphan-over-guess discipline carries over). New comments get
  `anchor_space='render'`. **Ref-less renders (Sub-phase 4's `pilot_poc`/`random_idea` case — zero
  anchor labels by design) yield `block_ref=NULL` for EVERY comment by construction: there is no
  canonical id to bridge to. That NULL is the honest, expected state, not a placement miss to retry
  or badge as broken — the comment still lives in render space and surfaces normally; it just has no
  source handle because the source has none either** (plan-review Issue #1). Migration and the
  displacement detector must treat a ref-less-render NULL as success, never as an unplaced miss.
- **Displacement re-target:** `list_comments`' derived `displaced` checks
  `quoted_text not in <served render text>` for `anchor_space='render'` comments (extract the text
  via the shared walker — never a second tokenizer); `'source'`-space comments keep the existing
  source check until migrated. No render artifact on disk → fall back to the source check (a
  missing file must never crash the read-time detector — existing discipline).
- **Relocate backstop:** the route-level 422 verbatim-substring validation re-targets the served
  render text for `'render'`-space comments.
- **`cast-comment-reanchor` contract v3 (additive superset of v2, same precedent as v2-over-v1):**
  inputs gain optional render-space context — the comment's prior-render container text (by
  `block_ref`) and the candidate new-render container text. Verdict vocabulary, safety machinery
  (orphan-over-guess, 422 backstop, no-op-on-garbage), and the `sonnet` tier carry untouched; all
  new inputs optional so every existing call site stays byte-valid.
- **Migration (one-time, idempotent):** for each existing open comment, attempt render-space
  placement + `block_ref` resolution (1b's exact procedure, productionized): places → flip
  `anchor_space='render'`, backfill `block_ref`; doesn't place → leave `'source'`-space, surfaced
  by the existing `.comment-unplaced` tray badge. Migration never resolves, orphans, or deletes —
  surface, don't suppress. Record per-comment disposition in `comment_events`.
- `requirements_comments.js` needs no placement change (it already places against the rendered
  DOM); verify only that nothing client-side assumes source-substring semantics.

**Design review:**
- ⚠️ **Spec conflict (intentional, the point of the plan):** reverses
  `cast-requirements-render.collab.md` > US8 (same-door comment authoring quote validation),
  US12 (derived displacement), US13/US19 (reanchor + survival source-space inputs). The single
  `/cast-update-spec` pass in Sub-phase 5 records all of it; until then the spec is knowingly
  ahead of the code — do not patch the spec piecemeal.
- ⚠️ **Trust boundary:** `block_ref` is server-resolved from the served artifact, never accepted
  from the client — a spoofed `block_ref` would mis-route a future change-request. Keep the field
  out of the POST body schema.
- Architecture: reuses the single `container_text_index` walker and the single
  `strip_inline_markdown` stripper (the no-copy hard edge from Phases 3/4b). ✓
- Error paths: comment created against a *stale* render (served during `generating`) — the quote
  was minted on what the user actually saw; placement against the soon-published render is exactly
  the Sub-phase 3b survival gate's job. Record the served artifact's embedded `source-hash` in the
  `created` event payload for forensics (no new column).

## Sub-phase 3a: Two-Mode Plumbing — Mode Detection & Prior-Render Recovery

**Outcome:** `render_job_service` deterministically decides CREATE vs UPDATE at job start and
assembles every UPDATE input (prior render, prior parsed source, changed-block set, reused WHAT
doc) — while production behavior is still 100% CREATE (the UPDATE prompt path exists but is
flag-gated off until Sub-phase 3b flips it).
**Dependencies:** Sub-phase 1 (1a verdict shapes what gets passed to HOW). Runs in parallel with
Sub-phase 2.
**Estimated effort:** 2-3 sessions.
**Verification:** Unit tests over mode detection (threshold boundaries, missing prior source →
CREATE, flagged prior → CREATE, family change → CREATE); a wait=True job against an edited corpus
doc logs the correct mode + changed-set in the job dir; reaper ceiling unchanged-or-extended
correctly (`reaper_ceiling_seconds` reads the stage list — verify any new stage registers).

Key activities:

- **Persist the recovery inputs at job time:** write `source.md` (the parsed source text) into the
  job dir at job start, and persist the gated WHAT doc under the stable name `what-doc.md` at
  `gate_what` pass (the `_what_doc_job_ref` path already promises
  `render-jobs/{slug}/{hash12}/what-doc.md` — make it real). The *next* job recovers both by the
  prior render's embedded `source-hash` → `build/render-jobs/{slug}/{prior_hash12}/`.
- **Prior-render recovery at `_start_job`:** read the existing `goals/{slug}/refined_requirements.html`
  (it IS the prior render until publish overwrites it); extract its embedded `source-hash`,
  `served-by`, and `human-review` stamps; recover the prior source from the prior job dir (fall
  back: a `requirement_versions` snapshot whose content-hash matches; nothing found → CREATE).
- **Mode decision (pure function, unit-testable):** UPDATE iff a prior render exists AND it was a
  clean maker publish (`served-by: maker`, no human-review flag — never UPDATE *from* a flagged or
  fallback render: that would propagate the flaw; recovering from a flagged render is exactly what
  a fresh CREATE is for) AND the prior source is recoverable AND
  `changed_fraction ≤ RENDER_UPDATE_MAX_CHANGED_FRACTION` AND the goal's `workflow_family` is
  unchanged. `changed_fraction = (added + removed + modified) / max(old_blocks, new_blocks)` from
  `block_diff.diff_blocks` — the deterministic engine, consumed unchanged (FR-024 extend-never-fork).
- **Threshold knob:** `RENDER_UPDATE_MAX_CHANGED_FRACTION` in `config.py` (env-overridable like the
  `QUALITY_*` knobs). **Default 0.4** — a starting value, recorded as a tune-after-first-runs knob,
  not a researched constant.
- **Prior-render size ceiling (second UPDATE precondition):** `changed_fraction` bounds the *changed*
  work but NOT the *total bytes inlined*. UPDATE inlines the WHOLE prior render into the HOW prompt,
  and the worst case for byte-fidelity — a large page with a one-bullet edit — is exactly the UPDATE
  happy path AND the most context-stressed: a prior render near the context budget can silently
  truncate, dropping tail unchanged containers the maker was told to copy → a fidelity-gate flag on
  an edit that touched none of them. Add `RENDER_UPDATE_MAX_PRIOR_BYTES` (config, env-overridable);
  a prior render above it flips to CREATE (a fresh generation never needs the prior page in context).
  Same degrade-to-CREATE-with-a-`_note` discipline as every other precondition failure (plan-review
  Issue #6).
- **`JobState` additions:** `mode`, `prior_html`, `prior_parsed`, `changed_refs` (the changed-set
  keyed the same way `block_diff._key` keys blocks). `_build_how_prompt` gains the UPDATE section
  (prior render inlined + changed-block refs + the byte-copy/fragment obligations per 1a) — built
  and tested, **inert** until 3b.
- **WHAT reuse in UPDATE mode:** skip `run_what` and reuse the prior job's gated `what-doc.md`
  (the section plan must not reshuffle under a small edit — that's the whole point of UPDATE);
  if the diff adds/removes refs, patch the WHAT doc's id-mapping deterministically where trivial
  (added ref → the section its neighbors live in) and otherwise fall back to CREATE rather than
  re-running WHAT against a stale structure. Gap stages: a job in UPDATE mode reuses the prior
  job's `gaps-state.json` unchanged (the gap set is a property of the source; a small diff that
  touches a gap's grounding flips to CREATE via the WHAT-patch fallback above). **UPDATE mode
  therefore SKIPS the `emit_change_requests` gap-emission stage entirely — it re-emits nothing.**
  This is load-bearing, not an optimization: the gap-CR dedupe fingerprint rides
  `origin_artifact_path = _what_doc_job_ref(state)`, which is keyed by the *current* `source_hash[:12]`.
  An UPDATE job runs under a NEW source hash, so re-running emission would write the gap CR against a
  new provenance path the dedupe pre-check cannot match against the prior job's CRs → a DUPLICATE gap
  change-request. Reuse-without-re-emit is what keeps gap CRs idempotent across an UPDATE; any diff
  that would actually change the gap set has already flipped the job to CREATE by the rule above
  (plan-review Issue #2).

**Design review:**
- Naming: knob follows the `RENDER_*`/`QUALITY_*` config convention; mode values are the literal
  strings `create`/`update` stamped into the job row (`render_jobs` gains a nullable `mode` column,
  additive, for observability — same pattern as the 4a flag columns). ✓
- ⚠️ **Error & rescue:** every UPDATE precondition failure degrades to CREATE with a `_note` in
  the job notes (zero silent failures) — never a job error. CREATE is always a safe answer.
- ⚠️ **Job-dir lifecycle:** `build/render-jobs/` now carries recovery state across jobs. Document
  that wiping it only costs UPDATE capability for the next render (degrades to CREATE) — an
  acceptable, surfaced degradation. Never make publish depend on the job dir surviving.

## Sub-phase 3b: The Flip — Readability-First HOW + Re-Scoped Gates

**Outcome:** CREATE renders paraphrase leaf text freely for readability (the verbatim-carriage
blanket obligation is gone); UPDATE renders keep unchanged containers byte-identical (per the 1a
mechanism) and re-render only modified/added blocks, dropping removed ones; the structural gates
enforce the new contract; comments survive structurally on unchanged blocks and route to
render-space re-anchoring on modified ones. `bug_fix` re-renders clean.
**Dependencies:** Sub-phase 2 AND Sub-phase 3a (the carriage flip is only safe once comments no
longer anchor to source) AND the 1a decision gate.
**Estimated effort:** 3-4 sessions.
**Verification:** `pytest` over `maker_gate` (new + reoriented checks) green; a wait=True UPDATE
job over an edited `bug_fix` corpus doc publishes `served_by=maker` with unchanged containers
byte-identical and an open comment on an unchanged block placing; a CREATE job over the unedited
`bug_fix` doc publishes clean (no verbatim-carriage flag — the reproducible FR-001/SC-001
paraphrase is now *allowed*); `eval_sc003_survival.py` (extended in Sub-phase 5) green.

Key activities:

- **HOW prompt rewrite (`agents/cast-requirements-how/cast-requirements-how.md`):** a two-mode
  contract section replaces the VERBATIM-CARRIAGE constraint block. CREATE: optimize purely for
  the most human-readable delivery — paraphrase/distill freely; what remains hard: anchor labels
  verbatim-once (FR-003), one-unit-one-container, never invent facts/ids, omit-never-pad, the
  sentinel/DOM/self-containment contract unchanged. UPDATE: prior render + changed-block set
  inlined; unchanged containers byte-exact (or fragment-only rendering, per 1a); removed blocks
  dropped; added/modified blocks rendered in the prior page's established structure and style.
  Keep the prompt byte-aligned with the gate (the stated keep-them-byte-aligned discipline).
- **`maker_gate` re-scope:** (1) `check_html` drops the blanket verbatim-carriage violation class;
  anchor-label, DOM-contract, gap-marker, and id-parity checks stay. (2) New
  `check_update_fidelity(html, prior_html, changed_refs)` — pure: every unchanged block's container
  identical to the prior render's, or splice-verification if 1a chose splice. **Comparison
  granularity (gate-enforced-LLM-copy mode): compare NORMALIZED container TEXT via the shared
  `container_text_index` walker — the same text space displacement and survival already use — NOT
  raw bytes. A raw-byte equality gate on LLM output thrashes on insignificant serialization noise
  (a stray whitespace or attribute-order diff fails an edit that changed nothing). Raw-byte identity
  is the construction GUARANTEE of *splice* mode (server keeps the prior bytes verbatim), not a
  reasonable bar to hold LLM output to. The 1a whitespace-only-vs-reworded distinction feeds a
  normalization layer here, exactly as 1a's design-review note demands** (plan-review Issue #3).
  Violations are structural (standard retry → best-attempt + flag — the override
  machinery is reused, not re-derived). (3) `check_comment_survival` reorients: in-block =
  `anchor_space='render'` + `block_ref` resolved; survival = the quote places inside the
  same-labeled container on the candidate. On an *unchanged* block a miss is a real structural
  violation (UPDATE byte-identity makes it impossible on the happy path); on a *modified/removed*
  block a miss is **expected** — recorded, never a violation, routed to re-anchoring.
- **Publish-boundary re-anchor:** after a publish where the survival report lists expected misses,
  the service dispatches ONE `cast-comment-reanchor` v3 run (render-space inputs from Sub-phase 2)
  to relocate/resolve/orphan them — extending 4b's version-boundary dispatch pattern to the render
  boundary. Verdict safety unchanged; failures leave comments open + badged (the read-time
  `.comment-unplaced` surface is the honest fallback, exactly as today).
- **CREATE-mode meaning-fidelity guard (bounded):** with verbatim gone, nothing deterministic
  guards paraphrase *meaning*. Per the owner's surface-don't-suppress principle, do the cheap
  honest thing: the WHAT doc's total id-mapping + the HOW never-invent rules remain the contract;
  the 4a checker keeps grading comprehension cold-reader; and the spec records "paraphrase
  meaning-drift is LLM-guarded only" as a known limitation. A dedicated fidelity checker is OUT
  of scope (HOLD SCOPE) — see Open Questions.
- Wire the 3a mode decision live (remove the flag-gate); `RENDER_STAGE_TIMEOUTS` gains no new
  agent stage (re-anchor dispatch is post-publish, outside the job's stage list — verify the
  reaper formula is genuinely unaffected, else extend it as Phase 4a's revision-a precedent demands).

**Design review:**
- ⚠️ **Spec conflict (intentional):** supersedes `cast-requirements-render.collab.md` > US16
  (verbatim-carriage clause) and amends US19 (survival classification). Recorded in the Sub-phase 5
  spec pass; the HOW prompt's "CONTRACT SOURCE OF TRUTH" comment must be re-pointed at the v7 spec
  section in the same change.
- ⚠️ **Security/robustness:** UPDATE inlines the prior render (LLM-authored HTML) into an LLM
  prompt — prompt-injection-shaped text in a prior render could steer the maker. Mitigation:
  the prior render is the maker's *own* gated output (already trusted enough to serve), and the
  gates re-run on every attempt; note it, don't over-engineer it.
- ⚠️ **Error & rescue:** if the publish-boundary re-anchor dispatch fails (subprocess crash),
  comments stay open + badged — degraded but visible, never lost. No retry loop; the next render
  or version cut gets another chance.
- Architecture: gate-enforced-copy keeps "the maker emits ONE self-contained page between
  sentinels" intact; splice (if 1a forces it) bends that contract — if splice wins, add an
  explicit design note to the spec pass that the published artifact is server-assembled in
  UPDATE mode. Flagged so the executor doesn't paper over it.

## Sub-phase 4: HOW Hardening — Invented IDs & Empty Shells

**Outcome:** The two non-verbatim 5c findings are fixed at root cause: a ref-less source
(`pilot_poc` — 0 canonical refs in source, HOW invented `SC-001`/`SC-002`) renders with zero
anchor labels and zero invented ids; a thin source (`random_idea`) renders without empty
placeholder sections, and an empty-shell render can no longer score 1.00 past the gates.
**Dependencies:** Sub-phase 3b (the prompts being hardened are the ones 3b rewrites — don't edit
them twice in flight).
**Estimated effort:** 1-2 sessions.
**Verification:** Single-family eval runs (`eval_family_sweep.py --family pilot_poc` /
`--family random_idea`) publish `served_by=maker`, `human_review=0`, `check_html` green; a unit
test feeds an empty-shell fixture to `check_html` and gets a violation.

Key activities:

- **`pilot_poc` (invented ids):** the gate already catches invention (it's why the family served
  `structural_violation`) but the retry never converged. Root-cause fix: an explicit zero-ref
  contract in BOTH prompts — WHAT for a source with no canonical refs emits sections with empty
  `block_refs` (verify `check_what_doc` accepts a zero-ref source cleanly); HOW renders a ref-less
  doc with NO anchor labels at all. Sharpen the gate's violation message to name the invented ids
  (feedback specificity is what makes the structural retry converge).
- **`random_idea` (empty shells):** the contract already says omit-never-pad (US2 Scenario 2) but
  nothing deterministic enforces it and the checker scored the padded render 1.00. Add a
  deterministic `check_html` violation: a unit/section container whose heading has no
  non-decorative text content is an empty shell. Add one negative example to the HOW prompt's
  CREATE section. (Deterministic gate over checker-prompt tweak — the checker stays cold-reader
  and unmodified.)
- Re-run both family evals; record before/after in the job dirs.

**Design review:**
- Naming: violation strings follow the existing prompt-ready `check_html` style (they get fed
  straight back as structural feedback). ✓
- No spec conflict: both fixes *implement* already-spec'd behavior (FR-003 never-invented,
  US2 omit-never-pad) — the spec pass in Sub-phase 5 only needs the new empty-shell gate check
  recorded as enforcement detail.

## Sub-phase 5: Proof — Three Families Clean, Survival Regression, Spec v7

**Outcome:** The validation target is met and recorded: `bug_fix`, `pilot_poc`, `random_idea`
re-render clean (`served_by=maker`, `human_review=0`); the six previously-clean families don't
regress; comment survival holds under the new anchoring + UPDATE mode; one `/cast-update-spec`
pass lands every contract change as `cast-requirements-render.collab.md` v7; the goal's
decisions-so-far log gains this phase's outcome section.
**Dependencies:** Sub-phases 2, 3b, 4.
**Estimated effort:** 2-3 sessions.
**Verification:** `eval_family_sweep.py --aggregate --golden` → 9/9 published, 0 flagged (the
gate model's happy-path tier all-green this time); extended `eval_sc003_survival.py` green;
`bin/cast-spec-checker` green on the v7 spec; `_registry.md` bumped.

Key activities:

- **Three-family validation:** re-run the flagged families through the production pipeline; the
  acceptance bar is clean publishes, not flagged best-attempts. Then the full nine-family
  aggregate to prove no regression in the six clean families (paraphrase freedom must not
  *reduce* quality elsewhere). Regenerate goldens once, gated (the Phase-2 single-gated-golden-
  regeneration discipline).
- **Survival regression (extend `eval_sc003_survival.py`):** (a) same-source re-render → zero DB
  changes, all comments place; (b) small edit → UPDATE mode: comments on unchanged blocks place
  byte-identically (no reanchor dispatch needed); (c) comment on a modified block → relocated by
  the publish-boundary v3 dispatch or left open + badged — never silently dropped, never
  auto-resolved; (d) massive edit → CREATE mode: survivors place or surface badged; (e) the
  trust-boundary check carries forward; **(f) gap-CR idempotency under UPDATE — an UPDATE-mode
  re-render of a doc carrying an open gap emits ZERO new gap change-requests (the
  reuse-without-re-emit guarantee of Sub-phase 3a; guards the source-hash-keyed dedupe-fingerprint
  duplication risk — plan-review Issues #2/#5).**
- **→ Delegate: `/cast-update-spec`** — single pass, `cast-requirements-render.collab.md` v6 → v7:
  the HOW two-mode contract (CREATE/UPDATE + threshold knob + mode column); US16's
  verbatim-carriage clause superseded (anchor labels + one-unit-one-container survive); comment
  anchoring re-spec'd to the render snapshot (US8/US12 re-target, `block_ref`/`anchor_space`
  columns, server-resolved bridge, migration record); US19 survival reorientation +
  publish-boundary re-anchor; reanchor contract v3 (additive superset); the
  paraphrase-meaning-drift known-limitation note; the empty-shell gate check; registry bump.
  Review output for: every reversed clause explicitly marked superseded (not silently rewritten),
  and the v2→v3 reanchor compatibility statement.
- **Record the outcome** in `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
  (a new "Post-Phase-5 follow-up (executed)" section, same format as prior phase outcomes) and in
  the goal's signoff record (this phase supersedes 5d's "principal follow-up" carry-forward).

**Design review:**
- ⚠️ The nine-family sweep is expensive (9 full pipeline runs at opus tier). Owner has stated
  cost is explicitly not a constraint for this goal — run it, don't sample it.
- ⚠️ Spec pass must also touch `cast-requirements-roundtrip.collab.md` ONLY IF the
  comment→change-request bridge wording references source-anchored quotes — check, and if so it's
  a one-line cross-reference fix, not a second spec rewrite (the roundtrip contract itself —
  propose/notify/gate — is untouched by this plan).

---

## Build Order

```
Sub-phase 1 (1a ∥ 1b) ──┬──► Sub-phase 2  (anchor move) ──────┬──► Sub-phase 3b ──► Sub-phase 4 ──► Sub-phase 5
                        └──► Sub-phase 3a (two-mode plumbing) ┘      (the flip)      (hardening)      (proof + spec v7)
```

**Critical path:** Sub-phase 1 → Sub-phase 2 → Sub-phase 3b → Sub-phase 4 → Sub-phase 5.
Sub-phase 3a is off the critical path (parallel with 2) but must land before 3b.
**Execution-start gate:** Phase 5d sign-off (the 5c sweep record is provisional until then).

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 2 | Reverses spec US8/US12/US13/US19 (source-anchoring) — intentional | Single `/cast-update-spec` pass in Sub-phase 5; no piecemeal spec edits |
| 2 | `block_ref` must be server-resolved, never client-supplied | Keep out of POST body schema; trust-boundary test |
| 3a | Every UPDATE precondition failure must degrade to CREATE with a job note | Zero silent failures; CREATE is always safe |
| 3a | `build/render-jobs/` becomes cross-job recovery state | Document: wiping it degrades next render to CREATE, never breaks publish |
| 3b | Supersedes spec US16 (verbatim-carriage clause) — the load-bearing reversal | Spec v7 marks it superseded explicitly; HOW prompt contract pointer re-aimed |
| 3b | Paraphrase meaning-drift now LLM-guarded only | Recorded as known limitation in spec v7; revisit only on evidence |
| 3b | Splice (if 1a forces it) bends "maker emits one page" | Explicit spec design note if splice wins |
| 3b | Publish-boundary reanchor dispatch failure | Comments stay open + badged — degraded-but-visible, no retry loop |
| 5 | Roundtrip spec may need a one-line cross-reference fix | Check during the spec pass; do not rewrite the roundtrip contract |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| HOW cannot byte-copy unchanged containers reliably | High — UPDATE mode's core promise | Sub-phase 1a spike decides BEFORE build; deterministic splice is the designed fallback, not an improvisation |
| Paraphrased leaf text drifts in meaning with no deterministic guard | Med | WHAT id-mapping totality + HOW never-invent rules + 4a cold-reader checker; spec'd as known limitation; comments give humans the correction channel |
| Existing comments strand during migration | Med | Migration is additive + idempotent; misses keep working in source space and surface via the existing badge; nothing deleted/orphaned by migration |
| UPDATE from a degraded prior render propagates flaws | Med | Mode decision requires a clean maker prior (`served-by: maker`, unflagged); anything else → CREATE |
| Threshold mis-tuned (UPDATE on too-big diffs → incoherent pages; CREATE on tiny diffs → comment churn) | Low-Med | Single config knob, default 0.4, explicitly a tune-after-first-runs value; mode stamped on the job row for observability |
| Re-anchor dispatch volume grows (every paraphrasing publish can displace modified-block comments) | Low | One dispatch per publish (batch, 4b precedent), only for expected misses; unchanged blocks never dispatch under UPDATE |

## Open Questions

- **Meaning-fidelity guard:** should a future phase add a dedicated paraphrase-fidelity check
  (a second, source-seeing LLM pass over modified/created units only)? Deferred under HOLD SCOPE;
  the spec v7 known-limitation note is the honest placeholder. Revisit if post-ship comments show
  real meaning drift.
- **Version-boundary vs publish-boundary re-anchor convergence:** 4b dispatches at version cuts
  (source space), this plan adds publish-boundary dispatch (render space). Two dispatch points
  with one agent is fine short-term; should they merge into one render-space-only path once all
  comments are migrated? Decide after Sub-phase 5 evidence, not now.
- **Threshold default (0.4) and the changed-fraction formula** (denominator `max(old, new)` block
  count): starting values. The Sub-phase 3a executor has latitude to adjust the formula if the
  corpus argues for it; the knob name and the flip-to-CREATE semantics are fixed.
- **Prior-WHAT reuse edge:** how much WHAT-doc id-mapping patching is "trivial" before UPDATE
  should fall back to CREATE? Sub-phase 3a detail; default conservative (any ambiguity → CREATE).

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` (v6) | US8 — Same-door comment authoring; US12 — Derived displacement; US13 — Re-anchor subagent; US16 — Logical id backbone and verbatim carriage; US19 — Open comments survive the maker; US2 — omit-never-pad; FR-003; FR-024 | 4 intentional reversals/amendments (US8, US12/US13, US16, US19) — all land in the single Sub-phase 5 `/cast-update-spec` pass → v7 |
| `cast-requirements-roundtrip.collab.md` (v1) | Comment→change-request flow (consumed, not modified) | None expected; one-line cross-reference check in Sub-phase 5 |

## Resolved Decisions (this plan)

1. **Comment anchoring moves to the render snapshot**, with a server-resolved `block_ref` bridge
   back to canonical ids (owner-directed in decisions-so-far.md; design locked here; 1b sizes the
   migration, it does not re-open the decision).
2. **Scope includes all three flagged-family fixes** — forced by the validation target
   "re-run the 3 flagged families → clean".
3. **UPDATE only from clean maker priors**; every UPDATE precondition failure degrades to CREATE,
   noted, never errored.
4. **One spec pass** (Sub-phase 5, v6 → v7), never piecemeal edits while code and spec diverge
   mid-phase — the per-phase single-pass discipline from Phases 3/4a/4b/5.
5. **Verbatim-carriage's survivors:** anchor labels verbatim-once and one-unit-one-container stay
   hard; only the leaf-text copy-exact obligation is removed.

---

## Decisions

<!-- cast-plan-review (BIG CHANGE, delegated) — 2026-06-12. Single end-of-review commit (B2). The
     owner-directed reversals (US16 verbatim-carriage, US8/US12/US13 source-anchoring, US19 in-block
     survival) were reviewed for DESIGN QUALITY, not whether to reverse — all confirmed grounded in
     decisions-so-far.md and accurately scoped against the v6 spec. The six decisions below are
     executor-level design refinements applied inline above; none reverse owner direction or expand
     scope beyond the HOLD-SCOPE feature set. -->

- **2026-06-12T16:54:55Z — Architecture #1: ref-less renders (Sub-phase 4's `pilot_poc`/`random_idea`) carry zero anchor labels, so the `block_ref` bridge has nothing to resolve — is a NULL bridge a defect?** — Decision: No — `block_ref=NULL` is correct by construction and must be treated as success. A source with zero canonical ids has nothing to bridge *to*; the comment still lives in render space and surfaces normally. Added an explicit line to Sub-phase 2's creation path so migration/displacement never flag a ref-less-render NULL as an unplaced miss. Rationale: the block_ref bridge is only as strong as anchor-label coverage, and Sub-phase 4 deliberately produces label-free pages — leaving this implicit invites an executor to "fix" a non-bug into a retry/badge loop.
- **2026-06-12T16:54:55Z — Architecture #2: UPDATE runs under a new `source_hash`, but the gap-CR dedupe fingerprint rides `_what_doc_job_ref` keyed by `source_hash[:12]` — could an UPDATE job re-emit duplicate gap CRs?** — Decision: Yes, it could, and the plan under-specified it; make UPDATE SKIP the `emit_change_requests` stage entirely (reuse `gaps-state.json`, re-emit nothing). Added the explicit no-re-emit line + the keyed-fingerprint reasoning to Sub-phase 3a. Rationale: verified in `render_job_service.py:1129/1176` — the dedupe pre-check substring-matches `#gap=<fp12>` on a provenance path keyed by the current hash; an UPDATE's new hash defeats the match → duplicate CR. Any diff that actually changes the gap set already flips to CREATE, so reuse-without-re-emit is the idempotent path.
- **2026-06-12T16:54:55Z — Code Quality #3: should `check_update_fidelity` enforce RAW-byte container identity on gate-enforced-LLM-copy output?** — Decision: No — compare NORMALIZED container text via the shared `container_text_index` walker in LLM-copy mode; reserve raw-byte identity as the *splice*-mode construction guarantee. Patched Sub-phase 3b's maker_gate re-scope (2). Rationale: a raw-byte gate on LLM output thrashes on insignificant serialization noise (whitespace/attribute-order), flagging edits that changed nothing; the walker's text space is the same one displacement and survival already trust, keeping the no-second-tokenizer discipline. The 1a whitespace-vs-reworded distinction feeds the normalization layer, exactly as 1a's design note demands.
- **2026-06-12T16:54:55Z — Tests #4: the 1a spike selects the CREATE-vs-splice mechanism but tests only the two already-clean families at ≥3 trials — is that adequate evidence?** — Decision: No — add a `bug_fix`-class doc (the family the entire plan exists to fix) and raise to ≥5 trials/doc. Patched Sub-phase 1's 1a activity + success bar. Rationale: a mechanism-selecting decision gate that never exercises the failing condition measures the wrong thing; and ≥3 trials cannot resolve a 95% bar (one miss reads as 67%). Cost is explicitly not a constraint for this goal, so the wider spike is free.
- **2026-06-12T16:54:55Z — Tests #5: is the duplicate-gap-CR-under-UPDATE risk (Issue #2) covered by a regression?** — Decision: No — added survival-regression item (f): an UPDATE re-render of a doc with an open gap emits ZERO new gap CRs. Patched Sub-phase 5's `eval_sc003_survival.py` extension list. Rationale: Issue #2's fix is a behavioral guarantee (reuse-without-re-emit) that needs a test pinning it, or a future refactor silently reintroduces the duplication.
- **2026-06-12T16:54:55Z — Performance/robustness #6: the mode decision bounds `changed_fraction` but not total prior-render size — UPDATE inlines the whole prior page; is a huge-page + tiny-edit safe?** — Decision: No — add a `RENDER_UPDATE_MAX_PRIOR_BYTES` precondition; a prior render above it flips to CREATE. Patched Sub-phase 3a's threshold section. Rationale: the large-page/tiny-edit case is simultaneously the UPDATE happy path and the most context-stressed; silent context truncation drops tail unchanged containers the maker was told to copy → a fidelity flag on an edit that touched none of them. A fresh CREATE never needs the prior page in context, and the degrade-to-CREATE-with-a-note discipline already exists.
