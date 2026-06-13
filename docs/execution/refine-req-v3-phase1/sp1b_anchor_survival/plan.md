# Sub-phase 1b: The Quote-Anchored Backbone Survives a Varying Render

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase1/_shared_context.md` before starting.

## Objective

Demonstrate that the **existing, unmodified** v2 comment/version layer, attached to a
hand-crafted *varying* maker-style HTML, holds under the resolved logical-backbone +
quote-anchored-DOM approach: every open comment's mark places on the maker DOM; a
regenerate-with-moved-text produces **zero new orphans** (moved-but-surviving content
relocates; orphan verdicts only where content is genuinely gone); `block_diff` stays
deterministic on the id backbone; and the v2 "NO `id=`" DOM contract stays intact. If quote
anchoring proves insufficient under heavy rewording, surface the **revisit-trigger** to the
owner with the failing cases attached. **Validate, never re-decide** — no change to the
approach, the DOM contract, or any spec.

## Dependencies

- **Requires completed:** None (parallel with sp1a). May opportunistically reuse sp1a's
  hand-crafted HTML **if already available**, but must **not wait** on it — a minimal varying
  HTML pair suffices.
- **Assumed codebase state:** v2 services are intact and accept injectable `db_path=` —
  `comment_service` (`create_comment`/`relocate_comment`/`orphan_comment`/`open_comment_count`),
  `requirement_version_service.create_next`, `block_diff.diff_blocks`/`summarize`. The
  `cast-comment-reanchor` agent exists. The v2 fixture pair exists under
  `cast-server/tests/fixtures/refine_requirements_v2/`.

## Scope

**In scope:**
- A throwaway test bed: scratch SQLite via injectable `db_path`, a scratch goal + source doc.
- A source pair (original + moved/reworded/deleted edit), starting from the v2 fixture pair.
- Seeding ≥6 open comments spanning the survival/orphan/probe cases.
- A Python mark-placement harness that **byte-faithfully** mirrors `requirements_comments.js`
  (`concat.indexOf`, **scoped to the intended block container**).
- Running `create_next` to capture `displaced_comment_ids`; the `cast-comment-reanchor` chain;
  applying verdicts through same-door `relocate`/`orphan`.
- A `diff_blocks`/`summarize` determinism check on the source pair.
- Writing `spikes/1b/spike-results.md` with the measured numbers and a *recommended* gate
  disposition (the binding call is made at G1).

**Out of scope (do NOT do these):**
- Do **not** modify any v2 service, `requirements_comments.js`, the DOM contract, or any spec.
- Do **not** write to the live house DB or any real `goals/{slug}` folder — `db_path` injection
  + a scratch slug everywhere.
- Do **not** re-decide the anchor-backbone approach — only validate it or surface a
  revisit-trigger.
- Do **not** fabricate reanchor verdicts if the subagent dispatch fails (see Execution Notes).
- Do **not** touch Phase-2 files.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/goal/.../spikes/1b/<family>-maker-v1.html` (layout A) | Create | May reuse sp1a output if ready |
| `docs/goal/.../spikes/1b/<family>-maker-v2.html` (layout B, regenerated) | Create | Does not exist |
| `docs/goal/.../spikes/1b/source/original.collab.md` + `edited.collab.md` | Create | Seeded from v2 fixture pair, extended if needed |
| `docs/goal/.../spikes/1b/spike_mark_placement.py` (harness) | Create | Throwaway harness |
| `docs/goal/.../spikes/1b/spike_backbone.py` (test-bed driver) | Create | Throwaway driver |
| `docs/goal/.../spikes/1b/scratch.sqlite` | Create | Throwaway DB (gitignore or note as disposable) |
| `docs/goal/.../spikes/1b/spike-results.md` | Create | The gate-evidence artifact |

## Detailed Steps

### Step 1b.1: Build the test bed (isolated, never the live house DB)
- A throwaway SQLite DB via the services' injectable `db_path`, plus a scratch goal + source doc.
- **Source pair:** start from `cast-server/tests/fixtures/refine_requirements_v2/refined_requirements.collab.md`
  + `.v2-edit.collab.md`. If the edit doesn't move/reword enough text, author a heavier variant
  that (i) **moves** a commented block to a different section, (ii) **rewords** a commented
  sentence while preserving meaning, (iii) **deletes** one commented block outright (the
  legitimate-orphan control).

### Step 1b.2: Seed comments (≥6 open, via `comment_service.create_comment`, varied `author_kind`)
Span these cases:
- A comment on an US/FR/SC block that **will move**.
- One on text that **will be reworded**.
- One on text that **stays put** (must NOT displace).
- One on the block that **will be deleted** (the legitimate-orphan control).
- One with a **short/generic quote** (the hard reanchor + false-placement case).
- One anchored under a heading whose **maker-HTML section name differs** from the canonical
  heading (the `section_hint` robustness probe).

### Step 1b.3: Hand-craft maker-style HTML v1 (layout A)
For the original source (reuse sp1a output if available): family-communication section names,
varied layout, canonical ids as **visible text labels**, **zero `id=`**, FR-028 scripts +
`data-goal-slug`, and each requirement unit's anchorable text carried **verbatim and contiguous**
within one semantic container.

### Step 1b.4: Measure mark placement on v1 (`spike_mark_placement.py`)
- Replicate `requirements_comments.js` placement semantics in Python: per block container,
  concatenate descendant text-node content (stdlib `HTMLParser`) and run `find(quoted_text)` —
  exactly as the JS `concat.indexOf` would.
- **Gate:** 100% placement for comments whose source text is untouched.
- **A hit counts only when it lands within the comment's intended block container** — not merely
  `find()` ≥ 0 anywhere in the DOM. `concat.indexOf` returns the first match anywhere, so a
  generic/short quote could "place" on the wrong block and pass; scoping the assertion to the
  intended container turns the seeded short/generic-quote comment into a **real** test.
- **Harness fidelity:** keep it byte-faithful to the JS (`concat.indexOf`, **no whitespace
  normalization**). Include one **deliberately-split-across-inline-elements** quote as a harness
  self-test. Record a live-browser eyeball as a **carry-forward** item.

### Step 1b.5: Regenerate-with-moved-text
- Apply the edited source; hand-craft maker-style HTML **v2 with a deliberately different
  layout/section ordering** (this is the "varying" in varying render).
- Run `requirement_version_service.create_next` with the new content; capture
  `displaced_comment_ids`. **Assert it equals exactly the moved + reworded + deleted comment
  set** — the untouched comment must **NOT** displace.

### Step 1b.6: Run the reanchor chain
- → **Delegate:** `cast-comment-reanchor` (subagent-mode, bare-JSON verdicts) over
  `{displaced comments, old_content, new_content}` — **`new_content` is the new source
  markdown**, per the v2 contract (not the maker HTML).
  - **Review `cast-comment-reanchor` output for:** relocated verdicts whose `new_quoted_text`
    is **verbatim in the new source**; the deleted block's comment verdict = `orphaned`
    (correct — not a "new orphan", content is genuinely gone); **orphan-over-guess honored**
    on the generic-quote case.
- Apply verdicts through the **same-door** `relocate`/`orphan` service calls; confirm the
  **FR-019 verbatim backstop passes every relocate**. A relocate rejected by the 422 backstop
  downgrades to orphan and **counts AGAINST the gate**.

### Step 1b.7: Re-measure mark placement on v2
- With the relocated quotes, re-run the harness on the v2 maker DOM.
- **Gate = zero new orphans:** every comment whose content survives the edit ends `open` +
  mark-placeable on the v2 maker DOM; **only** the deleted-block comment is orphaned. 100%
  placement for relocated + untouched comments.

### Step 1b.8: Confirm the diff stays deterministic
- Run `diff_blocks(old_parsed, new_parsed)` + `summarize` over the **source pair**.
- Assert the partition invariant and that the moved block lands in `unchanged`/`modified` by its
  `(kind, ref)` id key — evidence the id backbone needs **no** new machinery (only the Phase-4b
  *narration* agent becomes id-aware). **The maker HTML plays no role here — record that
  explicitly.**

### Step 1b.9: Write the gate verdict
Write `spikes/1b/spike-results.md` recording, with numbers:
- Mark-placement rate on v1 and v2; displaced-comment count after the source edit; per-comment
  reanchor verdicts; orphan delta (must be **0 new orphans** for surviving content);
  `diff_blocks` partition-invariant result.
- The `section_hint`-mismatch probe's outcome **explicitly**: places via the verbatim quote
  despite the renamed maker section, **or** degrades to tray-only — recorded as a Phase-3 input.
  (A seeded comment with no recorded verdict is not a measured gate.)
- A **recommended** disposition: `BACKBONE HOLDS: confirmed` with the numbers, **or**
  `REVISIT-TRIGGER: quote anchoring insufficient under heavy rewording` with the failing cases.
  **The binding decision is made at G1 — no change to the approach/DOM contract/spec here.**

## Verification

### Automated Tests (permanent)
- **None.** Spike scripts are `spike_*.py` under `spikes/1b/` — pytest never collects them.

### Validation Scripts (temporary)
- `spike_mark_placement.py` — the byte-faithful JS-walker re-impl, with the split-quote
  self-test and intended-container scoping.
- `spike_backbone.py` — drives the test bed: seed → `create_next` → reanchor → apply → re-measure
  → `diff_blocks` check; prints every measured number captured in `spike-results.md`.

### Manual Checks
- Live-browser eyeball of v1/v2 placement (recorded as **carry-forward** if no browser).
- Confirm the throwaway DB path and scratch slug — assert in the harness that no live house DB
  or real goal folder is written.

### Success Criteria
- [ ] `spikes/1b/spike-results.md` records, with numbers: v1 + v2 mark-placement rates,
      displaced count, per-comment reanchor verdicts, orphan delta, `diff_blocks` partition result.
- [ ] The `section_hint`-mismatch probe outcome is recorded **explicitly** (places-via-quote vs
      degrades-to-tray).
- [ ] Committed evidence pair: maker HTML v1 (layout A) + v2 (layout B) + source pair
      (original + edited).
- [ ] Zero-`id` audit on **both** HTML files (no `id=`, no `data-block-anchor` — the golden
      `test_requirements_renderer.py` structural assertions replayed).
- [ ] Throwaway harness script(s) committed under `spikes/1b/` so the run is replayable.
- [ ] `displaced_comment_ids` equals exactly the moved + reworded + deleted set (untouched did
      NOT displace).
- [ ] Zero new orphans for surviving content; only the deleted-block comment is orphaned.
- [ ] A recommended gate disposition is written (`BACKBONE HOLDS` / `REVISIT-TRIGGER`) — not a
      binding re-decision.

## Execution Notes

- **Reanchor dispatch failure:** per FR-027 the failure is an explicit **no-op** (comments stay
  displaced in the tray). **Retry once, then record the dispatch failure** — never hand-fabricate
  verdicts.
- **422 backstop = gate failure signal:** a relocate rejected by the FR-019 verbatim backstop
  downgrades to orphan and counts **against** the gate — that is precisely the failure the spike
  exists to catch.
- **DB-level orphaning cannot be caused by render variation alone** — all anchor validation is
  source-side and the maker never writes the source. The genuine exposure 1b measures is silent
  `<mark>`-placement loss on a paraphrased maker DOM, plus the implied verbatim-carriage
  obligation. Keep the framing straight in `spike-results.md`.
- **Carry-forward (record, do NOT act):** the v3 maker contract needs an explicit "anchorable
  text carried verbatim in the DOM" clause — flag it for the Phase 3 `/cast-update-spec`
  activity. No spec edit in Phase 1.
- **Harness-fidelity risk (named):** a whitespace-normalization gap could pass the Python harness
  yet fail in a browser. Mitigation: byte-faithful `concat.indexOf`, the split-quote self-test,
  and the carried-forward live-browser check.
- **Spec-linked files:** this sub-phase modifies none. It consumes US7–US13 / FR-012–FR-028 of
  `cast-requirements-render.collab.md` read-only.
