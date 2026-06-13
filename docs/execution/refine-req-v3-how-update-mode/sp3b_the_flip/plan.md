# Sub-phase 3b: The Flip — Readability-First HOW + Re-Scoped Gates

> **Pre-requisite:** Read `docs/execution/refine-req-v3-how-update-mode/_shared_context.md` — the Crux
> Decision, the `check_update_fidelity` NORMALIZED-text comparison rule (plan-review Decision #3), and
> the owner override (deterministic fallback ONLY on literal no-output). **Read the 1a verdict**
> (`spikes/update-fidelity/verdict.md`) — it decides gate-enforced-LLM-copy vs. deterministic-splice.

## Objective

CREATE renders **paraphrase leaf text freely** for readability (the verbatim-carriage blanket
obligation is gone); UPDATE renders keep unchanged containers byte-identical (per the 1a mechanism) and
re-render only modified/added blocks, dropping removed ones; the structural gates enforce the new
contract; comments survive structurally on unchanged blocks and route to render-space re-anchoring on
modified ones. **`bug_fix` re-renders clean.** This is the load-bearing reversal — flagged loudly.

## Dependencies

- **Requires completed (ALL THREE):**
  - **Sub-phase 2** — comments anchor to the render snapshot. The carriage flip is **only safe once
    comments no longer anchor to source** (Sub-phase 2's whole reason to go first).
  - **Sub-phase 3a** — the mode decision + recovery + the inert UPDATE prompt section. This sub-phase
    removes 3a's flag-gate and wires the mode decision live.
  - **The 1a verdict** — `MECHANISM: gate-enforced-llm-copy` vs `deterministic-splice` decides whether
    `check_update_fidelity` is a NORMALIZED-text gate over full-page LLM output, or a splice-construction
    guarantee. **If the verdict file is missing, stop** — do not guess.
- **Edits `agents/cast-requirements-how/cast-requirements-how.md` — Sub-phase 4 hardens the SAME prompt
  AFTER this sub-phase (sequential, never parallel).** Do not let any HOW-prompt edit run concurrently.
- **Assumed codebase state:** `maker_gate.check_html` (`:573`), `check_comment_survival` (`:849`),
  `container_text_index` (`:259`); `render_job_service` mode decision live-able (3a); `cast-comment-reanchor`
  v3 (sp2); `RENDER_STAGE_TIMEOUTS` reaper formula.

## Scope

**In scope:**
- HOW prompt rewrite: a two-mode contract section replaces the VERBATIM-CARRIAGE constraint block.
- `maker_gate` re-scope: drop the blanket verbatim-carriage violation class from `check_html`; add
  `check_update_fidelity`; reorient `check_comment_survival` to render space.
- Publish-boundary re-anchor: dispatch ONE `cast-comment-reanchor` v3 run for expected misses.
- Wire the 3a mode decision live (remove the flag-gate).
- A bounded CREATE-mode meaning-fidelity guard (the existing contract + spec known-limitation note —
  NO new fidelity checker).

**Out of scope (do NOT do these):**
- Do NOT add a dedicated paraphrase-meaning-fidelity checker (HOLD SCOPE — it is an Open Question; the
  spec records "paraphrase meaning-drift is LLM-guarded only" as a known limitation).
- Do NOT edit the spec — flag deltas for the Sub-phase 5 `/cast-update-spec` pass.
- Do NOT re-implement `container_text_index` — import it for the fidelity comparison.
- Do NOT harden the `pilot_poc`/`random_idea` invented-id / empty-shell defects here (Sub-phase 4 —
  don't edit the HOW prompt twice in flight).
- Do NOT change `block_diff` / the mode-decision contract (3a) / the comment schema (sp2).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-requirements-how/cast-requirements-how.md` | Modify | VERBATIM-CARRIAGE block replaced by the two-mode contract (CREATE readability-first / UPDATE byte-copy-or-fragment); CONTRACT SOURCE OF TRUTH pointer re-aimed at the v8 spec section (in the Sub-phase 5 spec change) |
| `cast-server/cast_server/requirements_render/maker_gate.py` | Modify | `check_html` (:573) drops the blanket verbatim-carriage class; add `check_update_fidelity(html, prior_html, changed_refs)`; reorient `check_comment_survival` (:849) to render space |
| `cast-server/cast_server/services/render_job_service.py` | Modify | Remove 3a's UPDATE flag-gate (wire mode live); add the post-publish `cast-comment-reanchor` v3 dispatch for expected survival misses |
| `cast-server/tests/test_maker_gate_update_fidelity.py` | Create | `check_update_fidelity` + re-scoped `check_html`/`check_comment_survival` unit tests |
| `cast-server/tests/test_render_update_publish.py` (or extend) | Create/Modify | wait=True UPDATE/CREATE publish integration over `bug_fix` |

## Detailed Steps

### Step 3b.1: HOW prompt rewrite — the two-mode contract

Replace the VERBATIM-CARRIAGE constraint block in `cast-requirements-how.md` with a two-mode section:
- **CREATE:** optimize purely for the **most human-readable delivery** — paraphrase/distill freely.
  What remains **hard**: anchor labels verbatim-once (FR-003), one-unit-one-container, never invent
  facts/ids, omit-never-pad, the sentinel/DOM/self-containment contract unchanged.
- **UPDATE:** prior render + changed-block set inlined; **unchanged containers byte-exact** (PASS /
  gate-enforced LLM copy) **OR fragment-only rendering** (FAIL / splice), **per the 1a verdict**;
  removed blocks dropped; added/modified blocks rendered in the prior page's established structure +
  style.
- **Keep the prompt byte-aligned with the gate** (the stated keep-them-byte-aligned discipline). The
  "CONTRACT SOURCE OF TRUTH" pointer is re-aimed at the v8 spec section **in the Sub-phase 5 spec
  change** (note it here; the actual re-point lands with the spec bump).

### Step 3b.2: `maker_gate` re-scope (three changes)

1. **`check_html` drops the blanket verbatim-carriage violation class.** Anchor-label, DOM-contract,
   gap-marker, and id-parity checks **stay**.
2. **New `check_update_fidelity(html, prior_html, changed_refs)` — pure:** every unchanged block's
   container identical to the prior render's.
   - **gate-enforced-LLM-copy mode (1a PASS):** compare **NORMALIZED container TEXT** via the shared
     `container_text_index` walker — the SAME text space displacement + survival use — **NOT raw bytes**
     (plan-review Decision #3). A raw-byte gate thrashes on serialization noise (whitespace /
     attribute-order) and would fail an edit that changed nothing. The 1a whitespace-vs-reworded split
     feeds this normalization layer.
   - **splice mode (1a FAIL):** raw-byte identity is the **construction guarantee** (the server keeps
     prior bytes verbatim) — `check_update_fidelity` verifies the splice rather than holding LLM output
     to a byte bar.
   - Violations are **structural** (standard retry → best-attempt + flag — reuse the override
     machinery, do not re-derive it).
3. **`check_comment_survival` reorients to render space:** in-block = `anchor_space='render'` +
   `block_ref` resolved; survival = the quote places inside the same-labeled container on the candidate.
   On an **unchanged** block a miss is a real structural violation (UPDATE byte-identity makes it
   impossible on the happy path); on a **modified/removed** block a miss is **expected** — recorded,
   never a violation, routed to re-anchoring.

### Step 3b.3: Publish-boundary re-anchor dispatch

After a publish where the survival report lists **expected misses**, the service dispatches **ONE**
`cast-comment-reanchor` v3 run (render-space inputs from Sub-phase 2) to relocate/resolve/orphan them —
extending 4b's version-boundary dispatch pattern to the render boundary. Verdict safety unchanged;
failures leave comments open + badged (the read-time `.comment-unplaced` surface is the honest fallback).

### Step 3b.4: Wire the mode decision live

Remove 3a's UPDATE flag-gate so `decide_mode` drives the real pipeline. `RENDER_STAGE_TIMEOUTS` gains
**no new agent stage** (re-anchor dispatch is post-publish, outside the job's stage list) — **verify the
reaper formula is genuinely unaffected**, else extend it as Phase 4a's revision-a precedent demands.

### Step 3b.5: CREATE-mode meaning-fidelity guard (bounded — NO new checker)

With verbatim gone, nothing deterministic guards paraphrase *meaning*. Do the cheap honest thing:
the WHAT doc's total id-mapping + the HOW never-invent rules remain the contract; the 4a checker keeps
grading comprehension cold-reader; the spec records "paraphrase meaning-drift is LLM-guarded only" as a
known limitation. **A dedicated fidelity checker is OUT of scope (HOLD SCOPE)** — comments are the human
correction channel.

## Verification

### Automated Tests (permanent)
`pytest` green over:
- **`check_update_fidelity` (pure):** unchanged container with whitespace-only diff → **PASS** (NORMALIZED
  comparison absorbs it, gate-enforced-copy mode); unchanged container reworded → **violation**;
  changed-block container → not compared (it's in `changed_refs`). If splice mode: a spliced page →
  raw-byte identity on unchanged containers verified.
- **`check_html` re-scope:** the reproducible `bug_fix` FR-001/SC-001 **paraphrase is now allowed** (no
  verbatim-carriage violation); anchor-label / DOM / gap-marker / id-parity checks still fire on their
  own violations.
- **`check_comment_survival` reorient:** unchanged-block miss → violation; modified/removed-block miss →
  expected, recorded, NOT a violation, routed to re-anchoring; in-block requires `anchor_space='render'`
  + resolved `block_ref`.
- **Integration (wait=True):**
  - An UPDATE job over an **edited `bug_fix` corpus doc** publishes `served_by=maker` with unchanged
    containers byte-identical AND an open comment on an unchanged block **places**.
  - A CREATE job over the **unedited `bug_fix` doc** publishes clean — **no verbatim-carriage flag**
    (the paraphrase is now allowed).
  - A modified-block comment → relocated by the publish-boundary v3 dispatch OR left open + badged —
    never silently dropped.
  - Publish-boundary dispatch **failure** (subprocess crash) → comments stay open + badged, no retry loop.
- **`eval_sc003_survival.py`** (extended in Sub-phase 5) green — run the relevant subset here as a smoke.

### Validation Scripts (temporary)
- A wait=True UPDATE over an edited `bug_fix` doc → diff the published HTML against the prior render;
  confirm only changed-block containers differ and an unchanged-block comment still places.

### Manual Checks
- `grep -n "container_text_index" cast-server/cast_server/requirements_render/maker_gate.py` → confirm
  `check_update_fidelity` reuses the shared walker (NORMALIZED text), no second walker, no raw-byte
  thrash in LLM-copy mode.
- Confirm the override machinery is **reused** (standard structural retry → best-attempt + flag), not a
  new blocking branch or a new deterministic-fallback path. Deterministic fallback still fires ONLY on
  literal no-output.
- Confirm `RENDER_STAGE_TIMEOUTS` / `reaper_ceiling_seconds` unaffected (or correctly extended).
- Confirm the HOW prompt is byte-aligned with the re-scoped gate.

### Static / carry-forward (no browser)
- The "unchanged-block comment still highlights on the served UPDATE render" visual confirmation is a
  static verdict + human-eyeball carry-forward. Never blocks the autonomous run.

### Success Criteria
- [ ] CREATE paraphrases leaf text freely — the `bug_fix` paraphrase no longer trips a verbatim-carriage
      flag; anchor-label / one-unit-one-container / never-invent / omit-never-pad still hard.
- [ ] `check_update_fidelity` compares **NORMALIZED text** (LLM-copy mode) / verifies the **splice**
      (splice mode), per the 1a verdict; violations reuse the structural-retry → best-attempt + flag path.
- [ ] `check_comment_survival` is render-space: unchanged-block miss = violation; modified/removed-block
      miss = expected, routed to re-anchoring.
- [ ] UPDATE keeps unchanged containers byte-identical + drops removed blocks; an unchanged-block comment
      survives structurally.
- [ ] ONE publish-boundary `cast-comment-reanchor` v3 dispatch for expected misses; failure → open +
      badged, no retry loop.
- [ ] Mode decision wired live (flag-gate removed); deterministic fallback fires ONLY on literal
      no-output; reaper formula unaffected.
- [ ] NO new meaning-fidelity checker (HOLD SCOPE); the known-limitation note is flagged for the spec pass.

## Execution Notes

- **This is the load-bearing reversal.** Read the override discipline: a survival/fidelity violation is
  **structural → standard retry → best-attempt + `structural_violation` flag**, never a silent swap for
  the deterministic page (that fires ONLY on literal no-output). Reuse the existing override machinery;
  do not re-derive or add a blocking branch.
- **The NORMALIZED-vs-raw-byte trap (plan-review Decision #3):** in gate-enforced-LLM-copy mode, a
  raw-byte gate on LLM output flags edits that changed nothing. Compare normalized container text via the
  shared walker. Raw-byte identity is **only** the splice-mode construction guarantee.
- **Architecture note for the spec pass:** gate-enforced-copy keeps "the maker emits ONE self-contained
  page between sentinels" intact; **splice (if 1a forced it) bends that contract** — the published
  artifact is server-assembled in UPDATE mode. If splice won, add an explicit design note for the
  Sub-phase 5 spec pass so the executor doesn't paper over it.
- **Security note:** UPDATE inlines the prior render (LLM-authored HTML) into an LLM prompt —
  prompt-injection-shaped text could steer the maker. Mitigation: the prior render is the maker's own
  gated output (already trusted enough to serve) and the gates re-run every attempt; note it, don't
  over-engineer it.
- **Spec-linked files:** supersedes `cast-requirements-render.collab.md` > US16 (verbatim-carriage) and
  amends US19 (survival classification). **Flag for the Sub-phase 5 `/cast-update-spec` pass — do not
  edit the spec here.** The HOW prompt's "CONTRACT SOURCE OF TRUTH" pointer is re-aimed at the v8 spec
  section in that same change.
