# Refine Requirements — Better Rendering (v3): Phase 4b — Comments & Versions Survive the Maker

> ## ✅ RESOLVED — OWNER OVERRIDE (2026-06-12): structural-violation policy is FINAL
> **This supersedes any "survival-failing attempt → structural-violation branch → deterministic
> fallback / not servable" wording later in this document** (including "Decisions #10" and the
> survival-is-structural branch passages).
>
> **Rule (binding):** a survival-failing attempt is **no longer disqualified from serving.**
> The maker's best attempt is served + flagged; **in-block comment-placement misses surface at
> read time as the `.comment-unplaced` tray badge** rather than blocking or forcing the
> deterministic page. The deterministic page is reserved for *literal* no-output only.
> "Never silently drop" still binds — the lost mark is **surfaced** (badge), not hidden.
> Principle: **surface, don't suppress.** Unchanged by the override: `cast-comment-reanchor` is
> extended in place (contract v2, never replaced); the survival check imports Phase 3's shared
> `container_text_index` helper (no copy); `block_diff`/`diff_render` are untouched. Canonical
> record: `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`
> (§ Post-reconciliation owner decisions).

## Overview

This plan details **Phase 4b only** of the v3 high-level plan: regenerating a render through
the maker leaves every open comment anchored with **zero new orphans** (SC-003); the
structural version diff stays **deterministic** (id-based set-arithmetic on the logical
backbone, exactly the v2 `block_diff` engine); and an LLM is used only to **narrate** the
deterministic change set and to **re-anchor or resolve** comments whose target text genuinely
moved or was reworded — never inventing a change absent from the source (FR-011, US3).

The shaping insight, carried from Phase 1's sharpened risk: **the comment and version layer
is entirely source-side.** Comments anchor to a verbatim quote validated against the canonical
`refined_requirements.collab.md`; versions snapshot the source; `block_diff` diffs parsed
*source* versions; displacement is a source-side string-find. A maker regenerate (same source,
new HTML) therefore *cannot* orphan a comment at the DB layer — the genuine exposure is
**silent `<mark>`-placement loss on a paraphrased maker DOM** (the JS `highlight()` returns
`false` and the comment quietly loses its visible mark). Phase 4b's job is consequently three
surgical additions, not a re-architecture: (1) a **comment-survival gate** over the *real*
open comments at maker-publish time, riding maker_gate's verbatim-carriage guarantee; (2) the
**diff-and-comment-resolution agent** — `cast-comment-reanchor` extended in place to a
backward-compatible contract v2 that adds diff narration and block-level re-anchoring context;
(3) a **same-door narration surface** (stored once per version cut, structurally validated
against the deterministic change set, rendered only by attachment to deterministic items so
the UI *cannot* show an invented change).

Planning only — this document specifies Phase 4b; it does not implement it. It assumes
Phase 1's 1b gate passed (quote-anchored backbone holds) and Phase 3 is built (maker pipeline,
`maker_gate.py`, `render_job_service`, WHAT-doc id-mapping, verbatim-carriage clause).

## Operating Mode

**HOLD SCOPE** — `refined_requirements.collab.md` front matter pins `scope_mode: hold` and the
delegation context repeats it ("Honor scope_mode: hold"). Owner decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md` are binding and not
re-opened. The quality checker, rework loop, human-review flag and `render_jobs` flag columns
(4a) and gap-fill asks (Phase 5) are **out of scope** — 4b consumes `render_jobs` read-only if
at all, and touches `render_job_service` only at the `gate_html` seam Phase 3 reserved.

## Position in Overall Plan

```
Phase 1 (1b: backbone validated) ──┐
                                   ├──► Phase 3 (maker pipeline) ──┬──► Phase 4a (checker/loop)
Phase 2 (commenting + fixes) ──────┘                               └──► Phase 4b (THIS PLAN)
                                                                              └──► Phase 5
```

Phase 4b runs **parallel with 4a** once Phase 3 exists. Both phases touch
`render_job_service`; the contention is managed by seam discipline (see Design Review Flags):
4a *inserts stages* between `gate_html` and `publish`; 4b *widens the `gate_html` report*
with the survival check. Phase 5 consumes nothing from 4b beyond the spec'd narration
surface and the survival gate staying green.

## Depends On (from prior plans / seed decisions)

From the binding seed (`refine-requirements-better-rendering-v3-decisions-so-far.md`):

- **Anchor backbone:** canonical ids (`US-NN`/`FR-NNN`/`SC-NNN`) are a LOGICAL backbone only;
  the served DOM keeps v2 quote/verbatim-substring anchoring — **no** `id=` /
  `data-block-anchor` anywhere (the FR-025 transient-id exception stays scoped to the diff
  view). Only the diff agent becomes id-aware.
- **Orphan-over-guess stands** (render-spec US13/decision #9); a comment is never silently
  dropped. **Trust boundary:** the LLM may narrate and re-anchor; a diff must never invent a
  change absent from the source.
- **Canonical source** stays `refined_requirements.collab.md`; the maker never writes it.

From Phase 1 (1b, gates assumed green):

- **Mark-placement harness semantics:** Python re-implementation of
  `requirements_comments.js` placement — per block container, concatenate descendant
  text-node content (stdlib `HTMLParser`) and `find(quoted_text)`; a hit counts only inside
  the intended container; whitespace byte-faithful to the JS walker; the
  deliberately-split-across-inline-elements quote stays a self-test. 4b productionizes this
  over *real* comments.
- **Sharpened risk (the design driver):** DB orphaning cannot come from render variation
  (anchor validation is source-side); the real exposure is silent `<mark>`-placement loss on
  a paraphrased maker DOM.

From Phase 3 (parallel-built; consumed as specified there):

- **`maker_gate.py`** — pure `check_what_doc` / `check_html` with the **verbatim-carriage
  clause**: each unit's anchorable text (source body through Phase 2's
  `strip_inline_markdown`) appears verbatim and contiguous within one semantic container.
  This is the guarantee 4b's survival gate rides: any quote *within* one block's anchorable
  text is placeable by construction. **3b is also expected to expose its `HTMLParser`
  container-text walker as a shared module-private helper** (the carriage check's per-container
  text concatenator); 4b-1's survival check imports that one walker rather than re-deriving
  the 1b semantics — see 4b-1 Dependencies and Suggested Revisions #1.
- **`render_job_service`** pipeline stages `run_what → gate_what → run_how → gate_html →
  publish`, with `GateReport.violations` as the prompt-ready feedback channel, one bounded
  structural retry, then deterministic fallback (structurally-unusable = no-output branch).
  Job artifacts under `build/render-jobs/{slug}/{hash12}/` (`RENDER_JOBS_DIR`).
- **WHAT-doc YAML id-mapping** — the total `sections[].block_refs` map over `Block.ref`; this
  is "the logical id backbone the diff agent reads." Note the id space is the same in-memory
  `Block.ref` vocabulary (`US1`/`FR-007`/`SC-001`) `block_diff._key` already keys on — the
  diff *engine* needs no change.

From Phase 4a (parallel; surfaces 4b must NOT touch): the checker agent, the quality loop,
`decide_quality`, and the `render_jobs` flag columns (`human_review`, `review_reason`,
`published_attempt`, `published_score`, `heartbeat_at`) are all 4a property. **One seam
4b-1 must respect (not own):** a survival violation makes an attempt *structurally invalid*,
so it is NOT a "structurally-valid attempt" in 4a's "once any valid attempt exists, serve the
best-scoring valid one" rule (4a's ratified fork). Survival is part of the structural gate
that must pass *before* the quality checker scores an attempt — recorded for the reconciliation
hand-off in 4b-4, not implemented here.

From v2 (consumed verbatim; the naming contract of render-spec v2):

- `comment_service` (state machine; `relocate` 422 verbatim-substring backstop;
  displacement derived read-time), `requirement_version_service.create_next`
  (`displaced_comment_ids` string-find — the dispatch seam), `block_diff.diff_blocks` /
  `summarize` (partition invariant; "an LLM may narrate these rows but SHALL never add
  entries"), `diff_render` (transient-id exception, FR-025), `requirements_comments.js`
  (tree-walk + `indexOf` mark placement; displaced ⇒ tray-only),
  `agents/cast-comment-reanchor/` (bare-JSON subagent carve-out, FR-027; dispatched by
  `cast-refine-requirements` step 3 of its Phase-4 loop, and by the writeback flow after a
  deterministic `orphaned` verdict in `change_request_service`).

---

## Sub-phase 4b-1: The Survival Gate — Real Comments Provably Place on Every Published Maker Render

**Outcome:** No maker render is published whose DOM would silently lose the `<mark>` of an
open comment that *should* place (its quote lies within one block's anchorable text); the
rare legitimately-unplaceable comment (quote spans block boundaries, inline-markdown seams,
or render decoration) is **visibly surfaced** in the tray — never silently markless. SC-003's
"zero new orphans" becomes machine-checked at publish time, not hoped for.

**Dependencies:** Phase 3 (3b `maker_gate.py` + 3c `render_job_service`). Parallel with 4b-2.
**Hard prerequisite (no-copy rule):** the survival check shares 3b's `HTMLParser` container-text
walker. If 3b has not yet exposed that walker as a shared module-private helper (the parallel
build order makes this real, not hypothetical), 4b-1 **blocks on it or lifts it to a shared
pure helper — it never copies the walk.** A duplicated walker is exactly the drift that would
silently break "any in-block quote is placeable by construction": carriage and survival must
walk the DOM with byte-identical semantics or the guarantee is a fiction. (Mirrors Phase 3's
CQ1 resolution for `strip_inline_markdown`.)
**Estimated effort:** 1–1.5 sessions.

**Verification:**
- `pytest cast-server/tests/test_comment_survival.py` green: at least one fixture per class —
  in-block quote placeable (pass), in-block quote missing from HTML (violation), quote
  spanning two blocks (cross-boundary: recorded, NOT a violation), quote spanning an
  inline-markdown seam (cross-boundary), quote of maker-added decoration text (cross-boundary),
  and the 1b split-across-inline-elements self-test replayed.
- **Legacy-cutover fixture (proves Key-Risk row 1, not just asserts it):** a comment whose
  quote was selected on the *v2 deterministic DOM* (carries render decoration / rendered
  inline-markdown that is absent from any stripped block body) replays through
  `check_comment_survival` and classifies **cross-boundary → surfaced, never a violation**.
  Without this fixture the "legacy comments read as cross-boundary, not failures" mitigation is
  an unverified claim guarding the cutover.
- The Phase 1b fixture pair (v2 fixture + heavier-edit variant) replays through
  `check_comment_survival` with the same placement results the spike recorded.
- The live deterministic fallback render (`render_requirements()` output) passes the survival
  check for in-block quotes — the same trust-pinning move as Phase 3's T1 (the fallback is
  published ungated; this test proves the substrate never regresses below the gate).
- `render_job_service` test (fake runner): a fixture HTML that drops one block's carried text
  → job takes the structural-violation branch with a survival violation string; after retry
  exhaustion → deterministic fallback, never a publish that loses the mark.
  > **⛔ SUPERSEDED by the OWNER OVERRIDE banner at the top of this doc (2026-06-12).** After
  > retry exhaustion the best attempt is **served + flagged** (deterministic fallback only on
  > literal no-output); a survival-failing render IS publishable and its in-block misses surface
  > as `.comment-unplaced` badges — the loss is surfaced, not avoided by blocking the serve.
- **Survival-is-structural branch test (pins the 4a seam):** a fake-runner attempt that passes
  carriage but fails survival is routed to the structural-violation branch and is NOT recorded
  as a "structurally-valid attempt" eligible for 4a's best-scoring-valid serve. This is a
  4b-1-side assertion of the seam 4a consumes (see Phase 4a Depends-On note); it keeps a
  mark-losing render from ever being served as a "valid" attempt.
  > **⛔ Override note (2026-06-12):** under the owner override a survival-failing attempt is
  > still *servable* (best attempt + flag + `.comment-unplaced` badge). What this test pins is
  > narrower: a survival-failing attempt is not treated as a *clean* "structurally-valid" pass —
  > it is served flagged, with its misses surfaced, never served silently as if clean.
- **Mid-job comment-inclusion test (fake-runner latch, deterministic):** a comment created
  *after* job start but *before* the `gate_html` stage entry is included in the survival check
  — proving the survival fetch reads at the gate stage, not at job start (see the `gate_html`
  activity below). The latch the test releases makes the interleaving controlled, not a sleep
  window (same determinism bar as Phase 3 T2).
- JS/tray check (e2e screen, browser-capable CI per cast-ui-testing): an open, non-displaced
  comment whose quote is absent from the served DOM shows the `.comment-unplaced` badge in
  the tray instead of nothing.

Key activities:

- **Pure `check_comment_survival(html: str, parsed, comments) -> SurvivalReport` in
  `maker_gate.py`** (co-located so it shares the carriage check's `HTMLParser` container-text
  walker — the shared module-private helper named in Dependencies, never a duplicate).
  `comments` is a plain sequence of `{id, quoted_text}` (the gate stays I/O-free; the service
  fetches). **Single-walk discipline:** the candidate HTML is walked **once** into a
  per-container text map, and the per-block stripped anchorable text
  (`strip_inline_markdown(block.body)`) is precomputed **once per pass**; both the carriage
  check and the survival classification read those two maps, so the cost is O(blocks + comments)
  — not O(comments × blocks) strip calls or a second DOM walk. Per comment, classify:
  - **in-block** — `quoted_text` is a substring of some block's anchorable text
    (`strip_inline_markdown(block.body)`). Given the verbatim-carriage clause this MUST place
    in the HTML; assert it with the 1b semantics (concatenated descendant text per container,
    `find()`, hit valid only in that block's container). A miss ⇒ **violation** (it *is* a
    carriage failure, witnessed by real data).
  - **cross-boundary** — the quote is not within any single block's anchorable text (spans
    blocks, spans a markdown-strip seam, or quotes render decoration). Best-effort
    whole-document find; **recorded either way, never a violation** — these can fail even on
    the deterministic substrate (the v2-inherited limitation Phase 3 logged as 4b input), so
    blocking the maker on them would be a bar the fallback itself cannot meet.
  - `SurvivalReport` = frozen `{passed: bool, violations: [str], unplaced: [comment_id],
    placed: [comment_id]}`; violation strings are prompt-ready (e.g. `"comment 12's anchor
    'the maker never writes…' missing from FR-008's container"`) for the 3c feedback channel.
- **Widen the `gate_html` stage in `render_job_service`:** fetch the goal's open comments
  **at `gate_html` stage entry** (`comment_service.list_comments(state="open")` — read-only,
  the comment path stays instant and independent), **re-reading per attempt** so the check
  reflects comments created or resolved during a long background job (the 4a loop can re-enter
  `gate_html` many times / minutes apart; a once-at-job-start fetch would check a stale comment
  set — see Decisions #9). The fetch is one indexed SELECT per `gate_html` entry. After
  `check_html` passes, run `check_comment_survival`; merge its `violations` into the same
  GateReport channel (same one-bounded-retry → deterministic-fallback policy as 3c — see
  Decisions #4). Write the full `SurvivalReport` to the job's artifact dir
  (`build/render-jobs/{slug}/{hash12}/survival.json`) — observability without touching
  `render_jobs` columns (4a owns those).
- **Surface unplaceable comments read-time in the tray:** in `requirements_comments.js`
  `placeMarks`, collect open non-displaced comments whose `highlight()` returned `false`;
  toggle a `.comment-unplaced` badge ("not visible on this render") on their tray
  `#comment-{id}` item. Derived per render pass, nothing stored — the same lazy philosophy as
  `displaced`. Badge CSS in `_theme.css.j2` beside Phase 2's `.comment-affordance` additions.
- **Anchor-pickability at creation (tiny, defensive):** when the composer posts a comment
  whose `quoted_text` is not a substring of the canonical source (e.g. the reader selected
  maker decoration text), the existing read-path already stamps it `displaced` and routes it
  to the tray — verify this with a test, and have the composer's success handler simply rely
  on the existing tray refresh. No new creation-time validation (HOLD: the lazy + surfaced
  tray model already gives the honest behavior).

**Design review:**
- **Architecture ✓** — the gate stays pure (service fetches, gate computes); mirrors 3b's
  no-I/O discipline; the walker is shared, not duplicated; a single DOM walk feeds both
  carriage and survival.
- **Error & rescue:** the in-block/cross-boundary split is the load-bearing call — in-block
  misses block publish (silent mark loss is the exact silent-data-loss class the v2 rule
  reserves deterministic machinery for); cross-boundary misses surface visibly instead of
  blocking on a bar the deterministic fallback can't meet either. Zero silent failures both
  ways.
- **Spec consistency ⚠️** — the survival gate and the `.comment-unplaced` tray badge are new
  user-facing behavior under `cast-requirements-render.collab.md` (US12 tray grouping,
  SC-009 selector list) → recorded for 4b-4's single `/cast-update-spec` pass.
- **Performance:** survival adds **one shared** pure pass over the candidate HTML per attempt
  (reusing the carriage walk, not a second walk); the comment fetch is one indexed SELECT per
  `gate_html` entry. Nothing on the view or comment paths.
- **Coordination ⚠️ (4a parallel):** this sub-phase edits `render_job_service` at `gate_html`
  only; 4a inserts `run_checker`/`decide_quality` *after* `gate_html`. Different seams — and
  the survival violation is part of the **structural** gate that precedes scoring: a
  survival-failing attempt is not a "structurally-valid attempt" for 4a's best-scoring-valid
  serve rule (Decisions #10). Flagged for the reconciliation pass.

## Sub-phase 4b-2: The Diff Agent — `cast-comment-reanchor` Contract v2 Narrates and Re-anchors with Block Context

**Outcome:** One agent — `cast-comment-reanchor`, extended in place (see Decisions #1) — is
the v3 "diff-and-comment-resolution agent": given the deterministic change set and the
displaced comments with their block context, it returns (a) re-anchor/resolve verdicts that
reason about meaning block-wise, and (b) a narration of the diff keyed exactly to the
deterministic items. Existing verdicts-only call sites keep working byte-unchanged.

**Dependencies:** None within 4b (parallel with 4b-1). Phase 3's WHAT-doc id-mapping exists.
**Estimated effort:** 1 session.

**Verification:**
- `tests/eval_reanchor.py` (the existing eval gate, `eval_` prefix — not default CI) extended
  and green: legacy verdicts-only fixture unchanged; a narration fixture where every
  `item_note` keys to a real summarize() item; an adversarial fixture proving the agent does
  NOT emit a note for a change absent from the provided set; a moved+reworded block fixture
  re-anchored (not orphaned) using the block-context hint; a markdown-seam fixture where the
  returned `new_quoted_text` avoids inline-markdown markers.
- `/cast-agent-compliance` over `agents/cast-comment-reanchor/` passes (config shape,
  carve-out conventions intact).
- A dry-run dispatch (Agent tool, subagent mode) over this goal's v2 fixture pair returns one
  bare JSON object parsing against the v2 schema.

Key activities:

- **Extend `agents/cast-comment-reanchor/cast-comment-reanchor.md` to contract v2 —
  backward-compatible superset:**
  - *Inputs (all additions optional):* `change_set` — the `summarize()` dict (counts + items)
    for the version pair; per displaced comment, `block_ref` (the `Block.ref` whose old body
    contained the quote, derived deterministically by the parent from the parsed old version)
    and that ref's diff disposition (`modified`/`removed`/`unchanged`). Legacy calls that pass
    only `{comments, old_content, new_content}` get legacy behavior: verdicts only.
  - *Outputs:* `{"narration": {...} | null, "verdicts": [...]}`. `narration` is emitted only
    when `change_set` was provided: `{overview: "1–3 sentences", item_notes: [{change,
    heading_or_ref, note}]}` where every `(change, heading_or_ref)` pair MUST equal an entry
    in the provided `change_set.items` — never merged, never added, never reworded keys.
    `verdicts` keep the v1 fields and gain one new verdict value (next bullet).
  - *Third verdict `resolved`* (the US3-S2 "re-anchor **or resolve**" half): when the new
    version *demonstrably addressed* the comment's ask (the change the quote sat on is
    exactly what the comment requested), the agent may return `resolved` with honest
    confidence and reasoning. Safety asymmetry, recorded in the prompt: a wrong `resolved` is
    **recoverable** (the tray shows it collapsed; `reopen` is one click; the event trail keeps
    everything) unlike a wrong relocate — but the bias order stays
    `relocated > resolved > never-guess`: prefer `relocated` when the content survives, use
    `resolved` only on a demonstrable fix, and `orphaned` whenever unsure.
  - *Anchor-pickability rule:* `new_quoted_text` must remain a verbatim substring of
    `new_content` (unchanged backstop), and SHOULD avoid spans containing inline-markdown
    markers (`**`, `` ` ``) so the anchor is both source-verbatim *and* placeable on the
    stripped-carriage maker DOM (closes the v2-inherited seam from the 4b-1 cross-boundary
    class at its origin).
  - *Trust boundary, stated as a hard rule:* the narration describes ONLY entries of
    `change_set.items`; if the agent believes the set is wrong, it says so in `overview`
    wording ("the structural diff shows…") — it never adds an item. The deterministic set is
    the source of truth; the agent decorates it.
- **Update `config.yaml` minimally:** `timeout_minutes: 15` (narration adds output volume);
  everything else unchanged (`dispatch_mode: subagent`, `model: sonnet` with a
  `# [USER-DEFERRED] tier knob` comment added — the deferred owner decision stays a config
  edit).
- **Update the dispatch site in `cast-refine-requirements` (Phase-4 loop, step 3):** pass the
  `change_set` (from `GET …/requirements/changes?base=N-1&head=N` JSON) and per-comment block
  context; on return, apply verdicts exactly as today (`relocated` → relocate, 422 downgrades
  to orphan; `orphaned` → orphan; new: `resolved` → `POST …/resolve` with
  `actor=cast-comment-reanchor`). **The `resolved` application respects the v2 comment state
  machine** (`comment_service`): if the comment is no longer `open` at apply time — a human
  resolved or reopened it between dispatch and verdict — the resolve POST is a clean no-op /
  rejection, never a forced overwrite (symmetric to relocate's 422 downgrade; the state
  machine, not the agent verdict, owns the final transition; see Decisions #11). Then POST the
  narration (4b-3 endpoint). A failed / timed-out / unparseable dispatch stays a **no-op** (no
  verdicts applied, no narration — the tray and the deterministic panel carry the load; next
  cycle retries).
- **Leave the writeback site untouched:** `change_request_service` / the writeback agent's
  reanchor use is verdicts-only and remains valid under v2 by construction (optional inputs).
  Adopting narration there is a Phase 5/reconciliation choice, not a 4b obligation.
- → Delegate: `/cast-agent-compliance` over the modified agent dir — review output for
  carve-out and config-shape violations.
- → Delegate: consult `/cast-agent-design-guide` (I/O contract section) while extending — the
  v2 contract block goes in the agent `.md` exactly as the v1 block is today.

**Design review:**
- **Architecture ✓** — extend-in-place honors the owner's "extends or replaces" fork with the
  lowest blast radius (Decisions #1); the verdict safety machinery (orphan-over-guess, 422
  backstop, no-op on garbage) carries over untouched rather than being re-implemented.
- **Naming ⚠️ (accepted):** the directory name `cast-comment-reanchor` now under-describes
  (it also narrates). Accepted trade-off vs. churning FR-027, the refine-loop prompt, the
  writeback references, and the eval gate; the agent `.md` title becomes "Diecast Comment
  Re-anchor & Diff Narrator" so discovery reads true. Revisit only if a Phase-5 surface makes
  the name actively misleading.
- **Error & rescue:** every new failure mode terminates honestly — narration key mismatch is
  rejected server-side (4b-3) and the parent retries once then proceeds without narration;
  a `resolved` misfire is reversible via `reopen` with the full event trail, and a stale-state
  `resolved` is absorbed by the state machine rather than clobbering a human action.
- **Spec consistency ⚠️** — FR-027's schema and US13's verdict enumeration change (superset)
  → 4b-4's `/cast-update-spec`.

## Sub-phase 4b-3: Narration Lands Same-Door — Stored Once, Validated Structurally, Rendered by Attachment Only

**Outcome:** A version cut can carry one stored narration per `(base, head)` pair, posted
through the same-door API by whichever agent cut the version; the server **structurally
rejects** any narration that references a change absent from the deterministic set; the
changes panel and the tracked-changes view render narration only by attaching notes to
deterministic items — so the UI cannot display an invented change even if the DB were
hand-edited. No narration ⇒ the deterministic panel serves exactly as today.

**Dependencies:** 4b-2 (the narration schema it stores is the agent's output shape).
**Estimated effort:** 1 session.

**Verification:**
- `pytest cast-server/tests/test_diff_narration.py` green: save/get round-trip; upsert on
  re-post; **422 on any `item_note` whose `(change, heading_or_ref)` does not match the
  recomputed `summarize()` items for that pair** (all-or-nothing — no silent note-dropping);
  422 on size-cap violations; 404 unknown version/slug; the `GET …/changes` JSON `counts`/
  `items` stay byte-identical to `summarize()` with narration present and absent.
- Fragment tests: `changes_panel.html` renders the overview labeled as agent narration plus
  per-item notes only on items that exist; a narration row with no matching item (forced via
  test seam) renders nothing for that note.
- `test_fr007_readonly_guard.py` sweep stays green (narration is DB-only; no goal-folder
  writes).
- Existing `test_block_diff.py` / `test_diff_render.py` untouched and green — the
  deterministic engine and view did not change.

Key activities:

- **Schema:** new table `version_diff_narrations` in `schema.sql` (+ the migration-test
  pattern): `id`, `goal_slug`, `base_version`, `head_version`, `overview`, `item_notes`
  (JSON), `created_by`, `created_at`, `UNIQUE(goal_slug, base_version, head_version)`.
  Re-post upserts (a retried loop cycle replaces, never duplicates). `created_by` records the
  **dispatching parent's actor id** (e.g. `cast-refine-requirements`), matching the `actor`
  the verdicts were applied under, so the narration's provenance reads true in the tray label
  and the event trail (see Decisions #2).
- **Service functions in `requirement_version_service`** (house pattern: flat functions,
  injectable `db_path`): `save_narration(goal_slug, base, head, overview, item_notes,
  created_by)` — loads both version rows (404 semantics if absent), recomputes
  `summarize(diff_blocks(old, new))` server-side, and validates **every** `item_note` keys to
  a deterministic item; any mismatch raises (route → 422) listing the offending keys
  (prompt-ready for the parent's single retry). `get_narration(goal_slug, base, head)`.
  Size caps mirror FR-017 (overview ≤ 2 KB, each note ≤ 2 KB, ≤ 1 note per item).
- **Route:** `POST /api/goals/{goal_slug}/requirements/versions/{head}/narration` with
  `{base, overview, item_notes}` in `api_requirements.py` — slug validated via
  `goal_service.get_goal` first (FR-014 rule), JSON-only (agents are the writers; humans
  read). Same-door: nothing about the caller is privileged.
- **Read surface:** `GET …/requirements/changes?base=N&head=M` gains a sibling
  `narration: {...} | null` key — `counts`/`items` remain byte-for-byte `summarize()` (the
  FR-024 guarantee re-scoped to those keys, recorded in 4b-4). The
  `changes_panel.html` fragment renders: deterministic counts line (unchanged) → overview
  paragraph visibly labeled as agent narration (`.diff-narration`, autoescaped — narration is
  LLM text and MUST flow through the escaped template, never `innerHTML`) → per-item notes
  attached by `(change, heading_or_ref)` lookup against the deterministic items.
  `render_diff` (the tracked-changes view) gains the same optional narration strip in its
  "What changed" panel, passed in by the route when a stored pair matches; the view itself
  stays deterministic and is byte-identical when no narration exists.
- **Nothing dispatches LLMs on the version path:** the server stores and validates; the
  *parent agent* that cut the version narrates and posts (4b-2). A human-initiated version
  cut simply has no narration — the deterministic panel is the floor (consistent with v2's
  "re-anchoring runs only at the next agent touchpoint, never on a human save").

**Design review:**
- **Architecture ✓** — validation recomputes the diff rather than trusting the poster;
  attachment-only rendering makes "never shows a change not in the source" structural at
  three layers (prompt rule → 422 gate → lookup-only render).
- **Security ⚠️ → handled:** narration is LLM-authored text entering HTML — autoescaped
  fragment rendering only; size caps; JSON-only endpoint behind slug validation.
- **Naming ✓** — `version_diff_narrations`, `.diff-narration` follow the existing
  `requirement_versions` / `.diff-*` conventions.
- **Error & rescue:** all-or-nothing 422 (never silently drop a note) + parent single-retry +
  honest degradation to the deterministic panel. A missing narration is a normal state, not
  an error.
- **Spec consistency ⚠️** — FR-024's "byte-for-byte" wording and FR-023's version-route
  enumeration change → 4b-4.

## Sub-phase 4b-4: The Spec Records the Survival Contract, and SC-003 Proves It End-to-End

**Outcome:** `cast-requirements-render.collab.md` records the 4b contract — quote-anchoring
preserved under a varying render, the logical id backbone the diff agent reads, the
LLM-resolution trust boundary, the survival gate, and the contract-v2 carve-out — and the
SC-003 sweep passes against the real pipeline: with open comments present, a maker regenerate
leaves every comment anchored with zero new orphans; a moved/reworded block is re-anchored by
the LLM, not dropped; the diff never shows a change absent from the source.

**Dependencies:** 4b-1 + 4b-2 + 4b-3.
**Estimated effort:** 0.5–1 session.

**Verification (the phase gate, from the high-level plan):**
- **Same-source regenerate (render-only):** with N open comments placed, force a maker
  re-render (cache-busted attempt against the same source) → zero DB changes of any kind
  (no new version, no displacement, no orphans), survival gate green, all in-block marks
  place on the new DOM. The deterministic check: comment rows byte-identical before/after.
- **Source-edit regenerate (the full loop):** edit the source so one commented block is
  reworded+moved, one is deleted, one untouched → version cut → `displaced_comment_ids`
  contains exactly the reworded and deleted ones → agent dispatch → reworded comment
  `relocated` (422-backstop not triggered), deleted-block comment `orphaned` (surfaced in
  tray), untouched comment never displaced → **zero new orphans beyond the genuinely-deleted
  block** (the 1b gate, now end-to-end) → new maker render publishes with survival green and
  the relocated mark placed.
- **Trust-boundary check:** the posted narration for that version pair contains only notes
  keyed to the deterministic items (assert server-accepted = recomputed set); the rendered
  panel shows no change entry beyond `summarize()`'s items.
- `bin/cast-spec-checker` green on the updated spec; `docs/specs/_registry.md` row bumped.
- Human-eyeball browser pass over the tray badge + narration panel recorded as a
  carry-forward item (autonomous runs cannot drive a browser; static verdicts never block).

Key activities:

- → Delegate: `/cast-update-spec` on `cast-requirements-render.collab.md` with these deltas
  (review the diff before approval, per the skill's gate):
  1. **Anchoring under a varying render:** the comment/version layer keeps
     quote/verbatim-substring anchoring with the DOM contract unchanged (zero `id=`, zero
     `data-block-anchor`; FR-025's transient-id exception stays diff-view-only); `<mark>`
     placement is re-derived per render, and the **comment-survival gate** (in-block
     placeability over real open comments, riding the verbatim-carriage clause) is part of
     structural maker gating. Cross-boundary quotes are a recorded limitation surfaced by the
     `.comment-unplaced` tray badge (US12 tray grouping + SC-009 selector list extended).
  2. **The logical id backbone the diff agent reads:** the WHAT-doc id-mapping and the parsed
     `Block.ref` space are the same id vocabulary; `block_diff` set-arithmetic stays
     deterministic, source-side, and unchanged (FR-024 engine untouched).
  3. **The LLM-resolution trust boundary:** the LLM narrates the deterministic change set and
     re-anchors/resolves moved-or-reworded comments only; narration is structurally validated
     (every note keys to a `summarize()` item, else 422) and rendered by attachment only —
     a diff can never show a change absent from the source. FR-024's byte-for-byte guarantee
     re-scoped to the `counts`/`items` keys with `narration` as a sibling; FR-023 gains the
     narration POST.
  4. **FR-027/US13 superset:** `cast-comment-reanchor` contract v2 — optional `change_set` +
     block-context inputs, `narration` output, the `resolved` verdict with its
     recoverability rationale and the `relocated > resolved > orphaned-when-unsure` bias, the
     anchor-pickability rule; still the bare-JSON subagent carve-out (recorded, not drift).
  5. New surfaces appended to `linked_files`: `version_diff_narrations` migration,
     the survival additions in `maker_gate.py`, the narration fragment/CSS touches.
- **Run the SC-003 sweep** (the three verification blocks above) via the eval harness (real
  pipeline, `eval_` prefix — not default CI) and record results + the human-eyeball
  carry-forward in the goal's artifacts.
- **Hand-off note for Phase 5 / reconciliation** (one short section in the goal dir): the
  narration POST is the surface Phase 5's round-trip summaries may reuse; the writeback
  dispatch site remains verdicts-only and may adopt `change_set` context at reconciliation;
  4a/4b both touched `render_job_service` — list the exact seams for the merge, **including
  the explicit ordering contract: the survival check is part of the structural gate inside
  `gate_html`, so a survival-failing attempt is structurally invalid and is not eligible as a
  "structurally-valid attempt" for 4a's best-scoring-valid serve rule** (Decisions #10). The
  merge must keep survival evaluated before `run_checker` scores an attempt.

**Design review:**
- **Spec consistency ✓ (this IS the spec work)** — all flags from 4b-1/2/3 resolve in one
  `/cast-update-spec` pass; the DOM contract is asserted unchanged.
- **Process ✓** — clause texts were fixed by this plan up front; the spec records behavior,
  it does not retro-discover it. Same discipline as 3e.

---

## Build Order

```
Sub-phase 4b-1 (survival gate + tray surfacing) ──┐
                                                  ├──► Sub-phase 4b-4 (spec + SC-003 e2e gate)
Sub-phase 4b-2 (diff agent contract v2) ──► 4b-3 (narration store/API/render) ──┘
```

**Critical path:** 4b-2 → 4b-3 → 4b-4 (4b-1 runs parallel to 4b-2/4b-3). Total **3.5–4.5
sessions**, matching the high-level 3–4 estimate.

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 4b-1 | 4a and 4b both edit `render_job_service` in parallel | Seam discipline: 4b widens `gate_html`'s report only; 4a inserts stages after `gate_html`; listed in the 4b-4 hand-off for reconciliation |
| 4b-1 | A survival-failing attempt must not count as 4a's "structurally-valid attempt" | Survival is part of the structural gate inside `gate_html`, evaluated before `run_checker`; explicit ordering contract recorded in the 4b-4 hand-off (Decisions #10) |
| 4b-1 | Shared `HTMLParser` walker could be copied across the parallel build (carriage vs. survival) | Hard no-copy prerequisite: 4b-1 imports 3b's shared walker or lifts it to a shared helper; never duplicates (Decisions #12) |
| 4b-1 | Survival results must not touch `render_jobs` columns (4a property) | Report written to the job's `build/render-jobs/...` artifact dir instead |
| 4b-1 | Cross-boundary quotes can fail even on the deterministic substrate (v2-inherited) | Never a violation; surfaced via `.comment-unplaced` tray badge; recorded limitation in spec; legacy-cutover fixture proves the classification |
| 4b-1 | New tray badge + selector is spec'd UX | US12/SC-009 deltas in 4b-4's `/cast-update-spec` |
| 4b-2 | FR-027/US13 schema is spec'd; verdicts gain `resolved` | Contract-v2 superset recorded in 4b-4; eval gate extended first |
| 4b-2 | Agent dir name under-describes after extension | Accepted (Decisions #1); `.md` title updated; revisit only if Phase 5 makes it misleading |
| 4b-2 | `resolved` could clobber a concurrently human-changed comment state | Application respects the v2 state machine — no-op/reject if not `open` (Decisions #11) |
| 4b-3 | FR-024 "byte-for-byte" wording conflicts with adding `narration` to `/changes` JSON | Re-scope the guarantee to `counts`/`items` keys; `narration` sibling; 4b-4 delta #3 |
| 4b-3 | LLM text rendered into HTML | Autoescaped fragments only; size caps; JSON-only endpoint behind slug validation |
| 4b-3 | Silent note-dropping would hide narration drift | All-or-nothing 422 listing offending keys; parent retries once then proceeds narration-less |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Legacy comments (quotes selected on the v2 deterministic DOM) don't match stripped-body carriage at cutover and read as failures | Med | They classify as cross-boundary (not within any stripped block body) → surfaced via tray badge, never blocking publish; the genuinely in-block majority is guaranteed by carriage; a legacy-cutover eval fixture pins the classification |
| 4a/4b concurrent edits to `render_job_service` collide | Med | Disjoint seams (widen `gate_html` vs. insert after it); explicit ordering + hand-off note for the reconciliation pass (survival is structural, precedes scoring) |
| A survival-failing attempt is mistakenly served as 4a's best-scoring "valid" attempt, losing a mark | Med | Survival violation makes an attempt structurally invalid (no-output branch); 4b-1 branch test pins it; recorded as the ordering contract in the 4b-4 hand-off |
| Comment set goes stale during a long background render and the survival gate checks the wrong comments | Low | Open comments fetched at `gate_html` stage entry (re-read per attempt), not once at job start; mid-job-inclusion latch test proves it |
| Narration key drift (`FR-7` vs `FR-007`) empties the narration via 422 loops | Low | Exact-key rule in the prompt + an eval fixture pinning it; 422 lists offending keys verbatim for the single retry; degradation floor is the deterministic panel |
| The `resolved` verdict auto-resolves feedback a human wanted to see | Low | Reversible by design (reopen + full event trail + collapsed-but-visible in tray); prompt bias `relocated > resolved > orphaned-when-unsure`; state-machine guard absorbs stale-state applies; eval fixture for an over-eager resolve |
| Survival gate makes maker publishes fail persistently on one stubborn comment | Low | Only in-block misses block — and those are real carriage violations the retry feedback names precisely; exhaustion degrades to the deterministic fallback (which provably places in-block quotes), so the reader never loses the mark either way |
| Prompt growth (narration + verdicts) degrades verdict quality | Low | Eval gate covers both jobs in one dispatch; narration is only requested when a change set is passed, so verdict-only dispatches keep the v1 prompt surface |

## Open Questions

- None blocking. The single goal-level open item remains the **[USER-DEFERRED]** model-tier
  knob — honored here by keeping `model:` in `cast-comment-reanchor/config.yaml` a one-line
  config edit (now annotated with the tuning-knob comment).

## Decisions Made Autonomously (per the autonomous-run instruction)

1. **Extend `cast-comment-reanchor` in place (contract v2), not replace it.** The owner
   decision sanctioned either ("extends or replaces"). Grounds: the verdict safety machinery
   — orphan-over-guess, the 422 verbatim backstop, no-op-on-garbage — is the load-bearing
   protection against silent data loss, and it carries over untouched; both jobs (narrate +
   resolve) fire at the same version boundary over the same context, so one dispatch serves
   both; existing call sites (refine loop, writeback) stay valid byte-unchanged because every
   new input is optional. Cost accepted: the directory name under-describes (flagged, title
   updated). A new `cast-requirements-diff` agent would churn FR-027, two dispatch sites, and
   the eval gate for naming purity alone.
2. **Narration is posted same-door by the parent agent that cut the version; the server never
   dispatches an LLM on the version path.** Matches v2's rule that re-anchoring runs at agent
   touchpoints, never on a human save; keeps `POST /versions` instant; a human-initiated cut
   simply has no narration and the deterministic panel is the floor. `created_by` records the
   dispatching parent's actor id so provenance reads true in the tray and event trail.
3. **Narration validation is all-or-nothing 422 with the offending keys listed.** Silently
   dropping non-matching notes would be a silent failure; rejecting whole gives the parent
   one precise retry and keeps "accepted ⇒ fully grounded in the deterministic set" as an
   invariant. Stored per `(goal_slug, base, head)` with upsert-on-repost (loop retries
   replace, never duplicate).
4. **In-block survival misses are structural violations (no-output branch on exhaustion);
   cross-boundary misses never block.** An in-block miss *is* a verbatim-carriage failure
   witnessed by real data — exactly Phase 3's structurally-unusable class, so it inherits
   3c's retry-then-deterministic-fallback policy (Decisions Made Autonomously #4 there);
   cross-boundary quotes can fail on the deterministic substrate too, so gating the maker on
   them would demand more than the fallback delivers — they get visible tray surfacing
   instead.
5. **Unplaceable-comment surfacing is read-time and JS-side (`.comment-unplaced` badge),
   nothing stored.** Same derived-property philosophy as `displaced`; the server-side
   `SurvivalReport` in the job artifacts covers observability without new DB state or 4a's
   columns.
6. **The `resolved` verdict is included (not deferred) under HOLD.** US3 Scenario 2 and
   FR-011 say "re-anchor **or resolve**" — cutting it would be silent scope reduction. Its
   safety profile differs from relocate in the right direction: a wrong resolve is fully
   recoverable (reopen + event trail + still visible collapsed in tray), so
   orphan-over-guess extends naturally to `relocated > resolved > orphaned-when-unsure`.
7. **`/changes` JSON shape: `narration` as a sibling key; the byte-for-byte guarantee
   re-scoped to `counts`/`items`.** Keeps every existing consumer of the deterministic
   payload byte-stable while making narration's optionality explicit, and avoids a second
   endpoint for what is one negotiated resource.
8. **`block_diff` and `diff_render` are not modified.** The "logical id backbone" the diff
   agent reads is the same `Block.ref` space `_key()` already keys on; the engine already is
   id-based set-arithmetic over source versions, and the maker never enters that path. 4b
   adds consumers beside the engine, never forks it (the FR-024 "extend, never fork" rule).
9. **The survival gate fetches open comments at `gate_html` stage entry, re-read per attempt,
   not once at job start.** A maker render is a background job that — under 4a's loop — can
   re-enter `gate_html` many times across minutes; a once-at-job-start fetch would gate a
   stale comment set (missing a comment created during the job, or checking one a human just
   resolved). The fetch is one indexed SELECT per stage entry, so honesty costs nothing on the
   view or comment paths. (Added inline to the plan-review pass; see appendix A1.)
10. **A survival violation makes an attempt *structurally invalid*; survival is evaluated
    inside the structural gate, before 4a's `run_checker` scores the attempt.** This pins the
    seam 4a consumes: 4a's ratified fork serves the best-scoring *structurally-valid* attempt
    once any exists — a mark-losing (survival-failing) attempt must never qualify as "valid,"
    or the reader silently loses a mark on a "best" render. 4b owns only its side of the seam
    (the branch routing + a pinning test); the ordering contract is recorded in the 4b-4
    hand-off for the reconciliation merge, not implemented into 4a internals. (Appendix A2.)
11. **`resolved` application respects the v2 comment state machine.** If a human resolved or
    reopened the comment between dispatch and verdict apply, the resolve POST is a clean
    no-op/rejection — the state machine owns the final transition, symmetric to relocate's 422
    downgrade. Closes a concurrency gap without re-opening the orphan-over-guess decision.
    (Appendix CQ2.)
12. **No-copy rule on the shared `HTMLParser` walker.** Carriage and survival MUST walk the
    DOM with byte-identical semantics — a duplicated walker is exactly the drift that would
    silently void "any in-block quote is placeable by construction." 4b-1 imports 3b's shared
    helper or lifts it to a shared pure module; it never copies the walk. Mirrors Phase 3's
    CQ1 resolution for `strip_inline_markdown`. (Appendix CQ1.)

## Suggested Revisions to Prior Sub-Phases

- **None that change a decision.** Two coordination notes for the reconciliation pass:
  (1) Phase 3's 3b should expose its container-text walker as a module-private helper inside
  `maker_gate.py` so 4b-1's survival check shares it rather than duplicating the 1b
  semantics — an extraction, not a behavior change, and now a **hard no-copy prerequisite**
  on 4b-1 (Decisions #12). (2) Phase 4a's loop design should treat the widened `gate_html`
  report (carriage + survival violations in one channel) as the structural gate it wraps, with
  a survival-failing attempt counted as structurally invalid (not a "valid attempt" for the
  best-scoring-valid serve) — already implied by its "structural violations stay on the
  no-output branch" ratification, restated here (Decisions #10) so the merge is mechanical.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` (Draft v2) | US7/FR-012/FR-013 (DOM contract — preserved verbatim); US9/FR-018/FR-019 (state machine + relocate backstop — consumed); US10/FR-021–FR-023 (versions/`create_next` — consumed; FR-023 gains the narration POST); US11/FR-024/FR-025 (diff engine "extend, never fork"; byte-for-byte JSON — **re-scoped**; transient-id exception — preserved); US12 (tray grouping — gains `.comment-unplaced`); US13/FR-027 (re-anchor carve-out — **contract v2 superset**); SC-009 (selector list — extended) | 4 — all resolved by the single `/cast-update-spec` pass in 4b-4 (survival gate + tray badge, FR-024 re-scope + narration surface, FR-027/US13 contract v2, FR-023 narration route) |
| `cast-requirements-roundtrip.collab.md` (Draft v1) | Writeback reanchor dispatch + `target_quote_override` flow | None — consumed, not modified; the verdicts-only call site stays valid under contract v2 by construction |

## Plan Review Decisions (cast-plan-review, BIG CHANGE scope — autonomous)

Reviewed under HOLD scope; every fork auto-decided against the binding owner decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`. **None of the
findings re-open an owner-resolved decision** (logical id backbone / quote-anchored DOM with
no `id=`, orphan-over-guess, background-job render model, fallback only on true no-output
failure, v2 hash cache reused unchanged). All sharpen comment-set freshness, the 4a structural
seam, walker-sharing, concurrency safety, and test determinism *within* the existing Phase-4b
design. Phase 4a internals (quality checker, rework loop, `render_jobs` flag columns) and
Phase 5 gap-fill stayed out of scope — this plan only consumes their seams; planning-only, no
implementation was reviewed. Per the B2 single-Write contract this appendix and the inline body
sharpenings above were committed in one write. Mirrors the depth and appendix format of the
Phase 3 review.

Summary: 8 issues found / 8 resolved / 0 deferred (Architecture 2, Code Quality 2, Tests 3,
Performance 1).

- **2026-06-12T09:15:00Z — A1 — Architecture: does the survival gate read a fresh comment set, or one that can go stale during a long background render?** — Decision: Sharpen — fetch open comments at the `gate_html` stage entry, re-read per attempt, not once at job start. Rationale: the render is a background job that under 4a's loop re-enters `gate_html` many times across minutes; a once-at-job-start fetch would gate a stale set (miss a comment created mid-job, or still check one a human just resolved). The fetch is one indexed SELECT per stage entry — honesty is free on the view/comment paths. Does not re-open the background-job render model; it makes the gate read the model honestly. (Body patched: 4b-1 `gate_html` activity + Performance bullet; Decisions #9; Key Risks; mid-job-inclusion test added.)
- **2026-06-12T09:15:00Z — A2 — Architecture: is a survival-failing attempt prevented from being served as 4a's best-scoring "valid" attempt?** — Decision: Sharpen — make the survival violation part of the **structural** gate inside `gate_html`, evaluated before `run_checker`, so a survival-failing attempt is structurally invalid and never qualifies as a "structurally-valid attempt" for 4a's best-scoring-valid serve. Rationale: 4a's ratified fork serves the best-scoring valid attempt once any exists; if a mark-losing render counted as "valid," the reader would silently lose a mark on the "best" render — the exact silent-data-loss class the survival gate exists to prevent. 4b owns only its side (branch routing + a pinning test); the ordering contract goes to the 4b-4 reconciliation hand-off, not into 4a internals (which stay out of scope). (Body patched: Phase 4a Depends-On note; 4b-1 Coordination + branch test; 4b-4 hand-off; Decisions #10; Design Review Flags + Key Risks rows.)
- **2026-06-12T09:15:00Z — CQ1 — Code Quality: is the shared `HTMLParser` container-text walker safe from duplication across the 3b/4b-1 parallel build?** — Decision: Sharpen — add a hard no-copy prerequisite on 4b-1: import 3b's shared walker or lift it to a shared pure helper; never copy the walk. Rationale: carriage and survival must walk the DOM with byte-identical semantics or "any in-block quote is placeable by construction" silently becomes a fiction; a copied walker is precisely the drift the plan's own Suggested-Revisions note warns about, and the parallel build order makes the missing-helper case real — mirrors Phase 3's CQ1 resolution for `strip_inline_markdown`. (Body patched: 4b-1 Dependencies hard-prerequisite; Phase 3 Depends-On note; Suggested Revisions #1 strengthened; Decisions #12; Design Review Flags row.)
- **2026-06-12T09:15:00Z — CQ2 — Code Quality: can a `resolved` verdict clobber a comment a human concurrently resolved or reopened?** — Decision: Sharpen — `resolved` application respects the v2 `comment_service` state machine: if the comment is no longer `open` at apply time, the resolve POST is a clean no-op/rejection, never a forced overwrite. Rationale: the dispatch→apply window is real (the agent runs async); the state machine, not the stale agent verdict, must own the final transition — symmetric to relocate's existing 422 downgrade. Closes a concurrency gap without touching orphan-over-guess. (Body patched: 4b-2 dispatch-site bullet; Decisions #11; Error & rescue bullet; Design Review Flags + Key Risks rows.)
- **2026-06-12T09:15:00Z — T1 — Tests: is the A1 fetch-timing fix proven, not just asserted?** — Decision: Sharpen — add a deterministic fake-runner-latch test: a comment created after job start but before `gate_html` entry appears in the survival check. Rationale: the staleness window is a thread-timing property; a latch the test releases makes the interleaving controlled rather than a flaky sleep window (Phase 3 T2's determinism bar). Pins A1 against regression. (Body patched: 4b-1 Verification.)
- **2026-06-12T09:15:00Z — T2 — Tests: is the legacy-comment cutover mitigation tested or only claimed?** — Decision: Sharpen — add a fixture replaying a real v2-DOM-selected quote (carrying render decoration / rendered inline-markdown) and assert it classifies cross-boundary → surfaced, never a violation. Rationale: Key-Risk row 1 is load-bearing — it's how the plan avoids blocking publish on every pre-existing comment at cutover; a risk-table claim guarding a cutover must be a gate, not an assertion. (Body patched: 4b-1 Verification; Key Risks row updated.)
- **2026-06-12T09:15:00Z — T3 — Tests: is the A2 structural-branch behavior pinned by a test on 4b's side of the seam?** — Decision: Sharpen — add a `render_job_service` test: an attempt that passes carriage but fails survival routes to the structural-violation branch and is not recorded as a structurally-valid attempt. Rationale: A2 is a cross-phase seam; 4b can and should assert its own side so the merge with 4a starts from a green pin rather than a prose contract. (Body patched: 4b-1 Verification.)
- **2026-06-12T09:15:00Z — P1 — Performance: does the survival check walk the DOM and strip block bodies redundantly?** — Decision: Sharpen — one shared DOM walk feeds both carriage and survival (the shared walker from CQ1), and the per-block stripped anchorable text is precomputed once per pass; classification is O(blocks + comments), not O(comments × blocks) strip calls or a second walk. Rationale: the naive shape recomputes `strip_inline_markdown(block.body)` per comment×block and walks the candidate HTML twice; a single walk + precompute keeps survival a genuinely cheap per-attempt pass, matching the "nothing on the view/comment paths" claim. (Body patched: 4b-1 `check_comment_survival` activity + Performance bullet.)
