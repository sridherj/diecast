# Shared Context: refine-req-v3-phase5 (Gap-Fill, Cross-Family Hardening & Sign-Off — FINAL)

> Read this file at session start before executing any sub-phase plan in this project.
> Phase 5 is the **terminal** phase of the v3 goal: it activates the dormant `gaps[]` seam,
> proves all nine work-families render, sweeps every success criterion, lands the final spec
> reconciliation, and signs the goal off. Nothing depends on Phase 5; Phase 5 depends on everything.

## Source Documents

- **Plan (authoritative for design):** `docs/plan/2026-06-12-refine-requirements-v3-phase5-gapfill-signoff.md`
- **Reconciliation report:** `docs/plan/2026-06-12-refine-requirements-v3-reconciliation.md`
- **Decisions-so-far (binding owner decisions — READ THIS):** `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
- **Prior-phase execution context (the seams Phase 5 consumes):**
  - `docs/execution/refine-req-v3-phase3/_shared_context.md` (maker pipeline, `maker_gate`, `render_job_service`, sentinels, `gaps[]` seam)
  - `docs/execution/refine-req-v3-phase4a/_shared_context.md` (quality loop, `human_review` flag columns, terminal policy)
  - `docs/execution/refine-req-v3-phase4b/_shared_context.md` (survival gate, `.comment-unplaced` badge, `container_text_index`, reanchor v2)

## Project Background

Phase 5 makes the presenter **fill genuine comprehension gaps by asking upstream, never
fabricating** (FR-015 / US7), and **reconciles obtained detail back to canonical through the
existing v2 change-request gate, unchanged** (FR-016). Two load-bearing insights ground the design:

1. **The FR-016 invariant is STRUCTURAL, not behavioral.** The maker never consumes a gap answer
   directly. The answer's *only* destination is a change-request through the v2 same-door intake.
   The page renders a gap **marker** (question + a fixed status string), and the gap un-marks only
   when the approved detail lands in canonical, bumps the version, changes the source hash, and the
   next view regenerates from canonical. The v2 cache/version machinery does all the work — there is
   **no special "un-mark" path** to get wrong, and **no code path** by which un-approved text reaches
   a reader as requirement content (`proposed_body` lives solely on the CR review surface).
2. **Phase 5's gap-fill emitter is the FIRST REAL downstream emitter** the roundtrip spec
   (`cast-requirements-roundtrip.collab.md`) hard-deferred. The intake / gate / apply contracts are
   consumed **byte-unchanged**; only the spec's Out-of-Scope fence is touched (5d, conditional).

Phase 5 is four sub-phases:
- **5a** — the gap contract + the bounded upstream-ask loop (net-new `cast-requirements-gapfill`
  agent, the `gaps[]` schema, the HOW `GAPS-DETECTED` trailer, the new pipeline stages, server-side
  `validate_evidence`, `maker_gate` extensions, `gaps-state.json`, the `GAPFILL_*` config knobs).
  Ends with a validated `gaps-state.json` per job — **no CR emitted yet.**
- **5b** — reconciliation through the v2 gate + honest `.rr-gap` page markers (the `emit_change_requests`
  stage, fingerprint dedupe, the marker contract, the checker gap-amnesty line, the gated-lane
  convergence test). **Applies the GATE-ALL policy flip.**
- **5c** — the nine-family corpus + golden renders (authored-not-fiction fixtures, the eval sweep,
  per-family quality read from `human_review`). **Runs parallel to 5a/5b.**
- **5d** — the full SC-001…SC-018 sweep, the integration drift sweep, the final `/cast-update-spec`
  passes, the **flagged-renders list**, and the sign-off.

Planning is done; this project **executes** the four sub-phases.

## Operating Mode

**HOLD SCOPE.** `refined_requirements.collab.md` front matter pins `scope_mode: hold`. Owner
decisions in `decisions-so-far.md` are binding and not re-opened: gap-fill writes go ONLY through
the existing v2 change-request gate (no new writer, no lighter path); the maker never fabricates
requirement content; the nine-family enum is **LOCKED** (`taxonomy_version: 1`, no additions); the
deferred human timed-read evaluation stays out of scope. No review UI beyond the minimal flagged-
renders list (5d), no PROV export, no real-emitter generalization beyond the one render-gap-fill
emitter this phase requires.

## ⚠️ Applied Owner-Resolved Edits (baked into the sub-phase plans — NOT open questions)

These are **decided**. The sub-phase plans below already encode them; do not re-open them at exec.

1. **GATE-ALL gap-CR policy (apply in 5b).** The goal's global `WRITEBACK_GATE_POLICY` switches to
   `"gate-all"`: every gap change-request (every `kind="addition"`) intakes `proposed` and **waits
   for explicit human approval** before touching canonical. Additions are **NOT** fast-tracked for
   this goal. **Mechanism (owner-confirmed):** flip the **config.py default** of
   `WRITEBACK_GATE_POLICY` to `"gate-all"` (env override `CAST_WRITEBACK_GATE_POLICY` preserved).
   The gate function, policy lanes, conflict predicate, writeback agent, outbox, and relay are all
   **consumed byte-unchanged** — *only the policy value changes*. This is **global** by design (the
   sanctioned knob; a per-origin policy would change the gate, which HOLD forbids). This **supersedes**
   the source plan's "Open Questions → default = keep `gate-except-additions`" taste call and
   Decision #1's fast-track framing — the owner resolved it to gate-all at reconciliation.
2. **Flagged-renders LIST in 5d (owner-resolved human-review surface).** Fold a **minimal** flagged-
   renders list (slug, reason, score, link) into Phase 5d's sign-off, on an **existing** screen
   (e.g. `/runs` or goals) — additive, read-only. 4a shipped **recording-only** (`render_jobs` flag
   columns + envelope stamp; SC-016 confirms "no list / review UI is built — that is Phase 5d"); 5d
   adds the list. Especially needed under the structural override, since flags are the only honest
   degraded-page signal ("surface, don't suppress").
3. **C5 — `GAPFILL_MAX_GAPS` knob (default 5) lands in `config.py` during 5a** alongside
   `GAPFILL_ASK_ROUNDS` (default 1). The config file already reserves a "GAPFILL_* keys (Phase 5)"
   slot beside the `QUALITY_*` block. 5d's drift sweep verifies both knobs landed and are read.
4. **C6 clarifier — the pre-loop probe `run_how` (trailer harvest) does NOT debit
   `QUALITY_MAX_ATTEMPTS`.** The first `run_how` exists to harvest the `GAPS-DETECTED` trailer before
   the quality loop starts; it is a gap-machinery step, not a quality attempt. This mirrors
   `GAPFILL_ASK_ROUNDS`'s independence from `QUALITY_MAX_WHAT_REWORKS` (Plan Review A2). Gap stages
   run **once per job, before** the 4a quality loop.
5. **Model tier = `opus` for `cast-requirements-gapfill`** (RESOLVED 2026-06-12 — opus confirmed as
   the starting tier for all four pipeline agents). The `[USER-DEFERRED]` knob converts to a
   tune-down review after the loop runs e2e. Placeholder already says opus.
6. **The full SC sweep is SC-001…SC-018**, not SC-001…SC-008. The source plan body says
   "SC-001…SC-008" because it was written before the spec grew to **v6** across Phases 3/4a/4b
   (SC-009 commenting e2e; SC-010–013 maker pipeline; SC-014–016 quality gate; SC-017–018 survival
   + narration). 5d sweeps all eighteen — running the gap/family-specific ones fresh and citing the
   existing phase-3/4a/4b evidence for the rest (each already has a named test/eval; see 5d).

## ⚠️ The Structural-Violation OWNER OVERRIDE (carried forward from Phase 3/4a/4b)

Best-attempt-plus-flag applies **even to structurally broken attempts**. The deterministic page is
served **ONLY** on a literal no-output failure (crash / timeout / nothing produced). A structurally
broken best attempt is served + `human_review`-flagged (`served-by: structural_violation`), and
every comment whose mark cannot place surfaces visibly (`.comment-unplaced` badge). "Never SILENTLY
drop" binds by **surfacing** the loss, not hiding it ("surface, don't suppress"). SC-013 / SC-015
already encode this; Phase 5 honors it (gap markers + flagged renders are the same family of honest
degraded-state signals). When resolving ANY new fork of this shape, prefer the visible-degraded
state with machine-readable context over the silent-safe swap.

## Codebase Conventions

- **Pure render package vs. service split.** `cast_server/requirements_render/` is pure (no I/O / DB
  / LLM) — `maker_gate.py` (the gap-schema + gap-marker-correspondence checks) lives here. All I/O /
  DB / subprocess work lives in `cast_server/services/` — `render_job_service.py` (the new gap
  pipeline stages + `validate_evidence`) and `change_request_service.py` (the emit target) live there.
- **Tool-free subagent carve-out (HARD).** `cast-requirements-gapfill` follows the established
  `cast-requirements-what` / `-how` shape EXACTLY: `dispatch_mode: subagent`, `interactive: false`,
  `allowed_delegations: []`, `timeout_minutes: 15`, `--tools ""` (cannot read beyond what the runner
  inlines, cannot write anything), `model: opus` + a `# [USER-DEFERRED] tier knob` comment. The
  agent is **pure text-to-text**; the SERVICE owns all I/O, corpus resolution, and evidence validation.
- **Single-implementation discipline (HARD — drift by construction otherwise).**
  - One `verbatim_locate` helper — the 5a `validate_evidence` check **reuses** it (NOT a raw
    `str.find()`; Plan Review CQ2), shared with the v2 writeback backstop.
  - One `strip_inline_markdown` (Phase 2, `goal_card.py`) — the gap code adds no second stripper.
  - One container-text walker `container_text_index` (3b, `maker_gate.py`) — gap-marker
    correspondence reuses it; never re-walk.
  - One change-request write path `change_request_service.create` — the emitter calls it directly
    (Decision #4 / autonomous), never re-implements intake.
- **Strict sentinel extraction is byte-untouched.** The HOW `GAPS-DETECTED` trailer lives **OUTSIDE**
  the `BEGIN RENDER` → `END RENDER` window (after `<!-- END RENDER -->`), so 3c's first-`BEGIN`→
  first-`END` extraction and the no-output classification are unchanged.
- **DOM contract preserved.** `.rr-gap` markers are **class-based only** — zero `id=`, zero
  `data-block-anchor`, per the preserved v2 DOM contract. They sit between block containers; anchorable
  block text is untouched (so carriage + survival gates stay green on a marked render).
- **Job artifacts under `build/render-jobs/{slug}/{hash12}/`** (`RENDER_JOBS_DIR`, never
  `goals/{slug}/`). `gaps-state.json` is a service-owned job artifact there.
- **`build/` is a non-goal, non-CI runtime area.** Eval harnesses use the `eval_` prefix (NOT
  collected by default `pytest cast-server/tests/test_*.py`).
- **Config knobs** live in `config.py` with `CAST_`-prefixed env overrides; the `GAPFILL_*` keys join
  the reserved slot beside `QUALITY_*` (line ~209).

## Key File Paths

| File | Role |
|------|------|
| `agents/cast-requirements-gapfill/` | **NET-NEW (5a).** Tool-free subagent: grounded-or-refuse gap answers from the corpus allowlist. `cast-requirements-gapfill.md` + `config.yaml`. |
| `agents/cast-requirements-what/` | **Modify (5a):** `gaps[]` entry schema + gap-detection prompt ("would materially help the reader" bar, `GAPFILL_MAX_GAPS` cap). |
| `agents/cast-requirements-how/` | **Modify (5a):** the optional `<!-- GAPS-DETECTED … -->` trailer AFTER `<!-- END RENDER -->`; the `.rr-gap` marker rendering (5b). |
| `agents/cast-requirements-render-checker/` | **Modify (5b):** one-line gap-amnesty clause. (Spec SC-014 already anticipates it — reconcile, don't duplicate.) |
| `cast-server/cast_server/requirements_render/maker_gate.py` | **Modify (5a):** `check_what_doc` gains gaps-schema rules; `check_html` gains gap-marker correspondence; rejects out-of-enum gap status + `GAP-NN` as a canonical ref. Pure, fixture-tested. |
| `cast-server/cast_server/services/render_job_service.py` | **Modify (5a/5b):** new stages `ask_what`, `run_gapfill`, `validate_evidence`, `emit_change_requests` between `gate_what` and the final `run_how`; reaper-ceiling + heartbeat extended for the new stages (5d drift sweep). |
| `cast-server/cast_server/services/change_request_service.py` | **Consumed unchanged (5b).** `create(...)` is the emit target; `gate_status(kind, target_quote, policy)` derives the lane under the (now gate-all) policy. |
| `cast-server/cast_server/config.py` | **Modify (5a/5b):** add `GAPFILL_MAX_GAPS=5`, `GAPFILL_ASK_ROUNDS=1` (5a); flip `WRITEBACK_GATE_POLICY` default → `"gate-all"` (5b). |
| `cast-server/cast_server/templates/.../_theme.css.j2` | **Modify (5b, append):** `.rr-gap` block beside `.render-refreshing` / `.comment-unplaced` — disjoint additive. |
| `cast-server/tests/fixtures/family_corpus/{family}/refined_requirements.collab.md` | **Create (5c):** nine authored-not-fiction corpus docs, pinned classification front matter. |
| `cast-server/tests/test_maker_gate.py` | **Modify (5a):** gaps-schema + gap-marker-correspondence fixtures (incl. the two-open-gap T3 case). |
| `cast-server/tests/test_render_job_service.py` | **Modify (5a):** gap-stage flow, ask-round bound, gapfill crash → `unfilled-ask-failed`, evidence demotion, verbatim-locate parity (T2). |
| `cast-server/tests/test_gap_reconciliation.py` | **Create (5b):** emit → dedupe → both convergence lanes (auto-apply mechanism + gated FR-016 lane T1) → SC-007 gap-injection. |
| `cast-server/tests/test_fr007_readonly_guard.py` | **Extend (5b):** a full gap-fill run leaves canonical byte-identical. |
| `cast-server/tests/eval_family_sweep.py` | **Create (5c):** `eval_`-prefixed nine-family real-pipeline sweep. |
| `docs/goal/refine-requirements-better-rendering-v3/signoff/` | **Create (5c/5d):** `golden/{family}.html` evidence + `sc-sweep.md` + the closing note. |
| `docs/specs/cast-requirements-render.collab.md` (v6) | **Update (5d):** gap contract, marker vocabulary, nine-family record, flagged-renders list, new `linked_files`. |
| `docs/specs/cast-requirements-roundtrip.collab.md` (Draft v1) | **Update (5d, conditional):** narrow the "real emitters deferred" fence to the one render-gapfill emitter, or record a no-change rationale. |

## Data Schemas & Contracts (fixed by the plan — copy verbatim, do not re-derive at exec)

### `gaps[]` WHAT-doc entry schema (5a — activating Phase 3's reserved field)

```yaml
gaps:
  - gap_id: GAP-01            # sequential per doc; gate rejects GAP-NN as a canonical ref token
    section_title: "Signal sources"
    block_refs: ["FR-008"]    # every member MUST be a parsed Block.ref
    question: "What is the data source for the conversion metric?"   # non-empty
    why_it_matters: "A reader can't trust the metric without its source."
    # NO proposed answer — the WHAT layer sees only the source; it names what's missing, never supplies it.
```

Gate-enforced (`maker_gate.check_what_doc`): `gap_id`s unique + sequential; every `block_refs` member
is a real `Block.ref`; `question` non-empty; the WHAT doc NEVER contains an answer. Detection bar =
US7's "would materially help the reader" (verbatim in the prompt); hard cap `GAPFILL_MAX_GAPS`
(default 5) — a page is communication, not an audit; trivia-hunting is instructed against.

### HOW `GAPS-DETECTED` trailer (5a — outside the sentinels)

```
<!-- END RENDER -->
<!-- GAPS-DETECTED
- section_title: "Signal sources"
  question: "What is the data source for the conversion metric?"
  why_it_matters: "..."
-->
```

No ids (the WHAT re-run assigns them). Placed AFTER `<!-- END RENDER -->` so strict extraction is
byte-untouched. This is the "HOW asks WHAT" channel of FR-015 — the HOW layer asks rather than improvises.

### `cast-requirements-gapfill` output (5a — one YAML doc between sentinels, per gap)

```yaml
# supplied:
- gap_id: GAP-01
  supplied: true
  answer: "The conversion metric is sourced from the Stripe webhook stream."
  evidence: { file: "requirements.human.md", quote: "<verbatim span from the corpus>" }
  proposed_change:
    kind: addition           # LOCKED — Plan Review A1 (a gap is MISSING content, never a rewrite)
    section_hint: "Signal sources"
    proposed_body: "..."     # NEVER reaches a reader pre-approval
# refused:
- gap_id: GAP-02
  supplied: false
  reason: "The corpus does not state the retention window."
```

Hard prompt rule: **supply only what the corpus literally supports, with a verbatim evidence quote;
when in doubt, REFUSE** — refusal is a correct answer; the page says so honestly. `kind` is
gate-pinned to `addition` (no `target_quote`): a `modification`-kind gap CR would refuse `orphaned`
at apply (no quote to locate), and `gate_status` only ever fast-tracks `target_quote is None`
additions (mechanism note — under GATE-ALL nothing fast-tracks anyway).

### Grounding corpus (5a — explicit allowlist, runner-resolved)

The goal's OWN upstream artifacts only — `requirements.human.md`, `research_notes.human.md`,
`exploration/` summary if present. The **wider repo is NEVER a requirements source**. The runner
resolves the allowlist inside the goal's own artifact tree (path-validated, existing traversal rule)
and inlines it. "Upstream cannot supply" (US7 Scenario 2) means *these files don't contain it* — the
honest answer the marker reports.

### `validate_evidence` (5a — the trust boundary, deterministic, service-side)

For each `supplied` gap: assert `evidence.file` ∈ corpus allowlist AND `evidence.quote`
**verbatim-locates** in that file via the shared `verbatim_locate` helper (whitespace/smart-quote
tolerant; NOT raw `find()`). Failure → demote to `cannot-supply`, record `evidence-validation-failed`
on the job row (zero silent failures). An ungrounded answer **cannot** reach the CR door.

### `gaps-state.json` (5a — service-owned job artifact, THE single closed status vocabulary)

```json
{ "gaps": [ { "gap_id": "GAP-01", "status": "cr-proposed", "cr_id": 42 } ] }
```

`status` ∈ **{`cr-proposed`, `cr-applied`, `unfilled-cannot-supply`, `unfilled-declined`,
`unfilled-ask-failed`}** — THE single closed gap vocabulary (Plan Review A3). 5b's fixed marker
strings and the job-row reason codes (`evidence-validation-failed`, `unfilled-ask-failed`, …) map
**1:1** to it via the explicit table in 5b's plan. `maker_gate` rejects any out-of-enum status. The
service annotates state beside the agents' docs — it never mutates them.

### Marker status vocabulary (5b — FIXED, 1:1 with `gaps-state.json`)

| `gaps-state.json` status | `.rr-gap` page status string |
|--------------------------|------------------------------|
| `cr-proposed` | "a detail is missing here — proposed upstream, awaiting review" |
| `cr-applied` | (no marker — the detail is now canonical; un-marked by regeneration) |
| `unfilled-cannot-supply` | "missing — upstream could not supply it" |
| `unfilled-declined` | "missing — a proposed detail was declined" |
| `unfilled-ask-failed` | "missing from the requirements" |

The `.rr-gap` callout renders the `question` + exactly ONE status string from this table. **The
`proposed_body` NEVER appears on the page** (FR-016 structural).

### Gap CR provenance (5b — the column values for `change_request_service.create`)

`kind="addition"`, `target_quote=None`, `section_hint` from the proposal, `base_version` = current
`requirement_versions.version` (read at emit time), `author="cast-requirements-gapfill"`,
`author_type="agent"` (hard-coded at the emitter — no spoof surface), `origin_phase="render-gapfill"`,
`origin_activity_id` = job id, `origin_artifact_path = "{what_doc_job_path}#gap={fp12}"`. Status from
`gate_status(kind, target_quote, policy)` — under GATE-ALL this is always `"proposed"`.

### Dedupe fingerprint (5b — structural, stable across LLM re-wording)

`fp12 = sha256(...)[:12]` over a **structural** key: `sorted(block_refs) + " " + section_title`
(primary) with the question folded through a NAMED normalizer `_normalize_gap_question`
(casefold → collapse whitespace → strip trailing punctuation) as a secondary component (Plan Review
CQ1 — keying on block_refs/section keeps the fingerprint stable when the WHAT agent re-words the
question). Embedded as the `origin_artifact_path` `#gap=<fp12>` fragment (no schema column; gate
unchanged). Before creating: filter `change_requests` by `goal_slug` FIRST
(`idx_change_requests_goal_status`), then substring-match the fragment — O(CRs-per-goal), accepted
under HOLD (Plan Review P1). Skip when ANY row with the fingerprint exists in
`proposed`/`applied`/`conflicted`/`rejected`; only `superseded` frees re-proposal. A `rejected`
match → `unfilled-declined` ("asked and answered — do not re-ask the human").

## Pre-Existing Decisions (binding — from decisions-so-far.md)

- **Gap-fill write-back door = the existing v2 change-request gate, unchanged.** No new writer, no
  lighter path. The page marks the gap until approval; un-mark is the v2 cache/version machinery.
- **The maker NEVER fabricates requirement content.** Grounded-or-refuse; server-side evidence
  validation makes "never fabricates" enforced, not promised.
- **`cast-requirements-gapfill` is NET-NEW** (FR-010's "helpers as needed"), NOT an extension of the
  interactive `cast-refine-requirements` (its AskUserQuestion protocol is a bad headless citizen).
- **Grounding corpus = the goal's own upstream artifacts only** (allowlist), never the wider repo.
- **CR emission calls `change_request_service.create` directly** (it IS the governed write path; the
  route is the identity door for *external* actors; a self-HTTP-POST adds liability for zero gain).
- **The page never renders a gap answer** — only the question + a fixed status string.
- **HOW-asks-WHAT is a bounded structured round-trip** (trailer → one WHAT re-run), not free-form chat.
- **Gap stages run once per job, before the 4a quality loop** (the gap set is a property of the
  source, not the attempt; honors FR-015's "before finalizing").
- **GATE-ALL** (post-reconciliation owner decision) — see Applied Edits #1.
- **Structural-violation OWNER OVERRIDE** — see the override section above.
- **`gate-all` is global**; a per-origin policy is forbidden (HOLD).
- **4b's narration surface is NOT adopted for gap-fill summaries** (Decision #9) — the existing
  `recent_writebacks` provenance descriptor surfaces gap CRs with zero new code.
- **Nine-family enum LOCKED** (`taxonomy_version: 1`); the 6-block recipe *wording* is tunable, the
  enum/shape is not.

## Relevant Specs

- **`cast-requirements-render.collab.md` (v6)** — `linked_files` overlap. Sub-phase **5d** runs the
  single `/cast-update-spec` pass: the gap-fill contract (FR-015/FR-016 realized), the `.rr-gap`
  marker vocabulary + page-renders-only-canonical invariant, the nine-family verification record
  (SC-002), the flagged-renders list (updates SC-016's "that is Phase 5d" pointer), and new
  `linked_files`. Sub-phases 5a/5b **flag** spec deltas (clause texts fixed in the source plan); they
  do NOT edit the spec — 5d records them. The DOM contract is preserved (`.rr-gap` is class-based).
  Note SC-014 already references gap amnesty and SC-016 already names "Phase 5d" — reconcile with
  these, do not duplicate.
- **`cast-requirements-roundtrip.collab.md` (Draft v1)** — gap-fill rides FR-001/FR-002/FR-005/FR-013
  **as a consumer**; the intake / gate / apply contracts are NOT modified (verified by leaving every
  roundtrip test untouched and green). One conditional minimal delta in **5d**: narrow the Out-of-Scope
  "real downstream emitters deferred" fence to record the first real emitter (emitter-side only), OR
  record an explicit no-change rationale in `sc-sweep.md`. `cast-goal-classification.collab.md` is
  consumed via `families.py` only (LOCKED enum, not loaded as a third spec).

## Cross-Phase Hard Edges (do not violate)

- **Sentinel extraction (3c) → 5a HOW trailer:** the `GAPS-DETECTED` block is OUTSIDE the
  `BEGIN RENDER`/`END RENDER` window. Never move it inside; never alter extraction.
- **`render_job_service` stage seam (3c/4a):** the gap stages insert between `gate_what` and the
  FINAL `run_how`; the 4a quality loop (`run_checker → decide_quality`) stays between `gate_html` and
  `publish` and runs AFTER all gap machinery. Gap stages run **once per job**, never per quality attempt.
- **`GAPFILL_ASK_ROUNDS` ⟂ `QUALITY_MAX_WHAT_REWORKS` (A2):** the pre-loop gap-ask WHAT re-run is a
  SEPARATE counter from the in-loop WHAT-escalation budget. The merge must not collapse them.
- **The probe `run_how` ⟂ `QUALITY_MAX_ATTEMPTS` (C6):** the first trailer-harvest `run_how` does not
  debit the quality-attempt ceiling.
- **Reaper ceiling + `heartbeat_at` (4a→3 correction) must include the new gap stages** — the ceiling
  formula derives from the configured stage list, so it must count `gapfill_timeout` + the ask-round
  WHAT re-run; heartbeats fire at each new stage boundary. 5d's drift sweep verifies this.
- **Single helpers:** `verbatim_locate` (5a evidence check reuses it — no second locate),
  `strip_inline_markdown` (no second stripper in gap code), `container_text_index` (marker
  correspondence reuses it — no second walker).
- **`change_request_service` consumed unchanged:** the emitter calls `create(...)`; it never edits
  intake / gate / apply / outbox / relay.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|-----------|------|-----------|--------|-------------------|
| 5a (gap contract + ask loop) | Sub-phase | Phases 3 + 4a (pipeline stages + quality loop) | 5b, 5d | 5c |
| 5b (gate reconciliation + markers) | Sub-phase | 5a | 5d | 5c |
| 5c (nine-family corpus + golden renders) | Sub-phase | Phases 3 + 4a (gap machinery dormant → `gaps[]` empty) | 5d | 5a, 5b |
| 5d (SC sweep + spec + sign-off) | Sub-phase | 5a, 5b, 5c | — (terminal) | — |

No `G`-prefixed orchestrator decision gates: the source plan defines none. 5d's two
`/cast-update-spec` passes are inline skill-approval gates (review the diff before approval) handled
**under STANDING SESSION APPROVAL** (the goal's standing additive-spec approval). The human-eyeball
browser passes (nine-family visual review, gap-marker e2e, SC-006) are non-blocking carry-forwards
(autonomous runs cannot drive a browser; static verdicts never block).
