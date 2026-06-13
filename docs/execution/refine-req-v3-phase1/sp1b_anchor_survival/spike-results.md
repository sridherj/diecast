# Sub-phase 1b — Spike Results: The Quote-Anchored Backbone Survives a Varying Render

> **Sub-phase:** sp1b (anchor-survival) · **Phase:** refine-requirements-v3 Phase 1 (de-risking) ·
> **Operating mode:** HOLD SCOPE — this spike **validates** the anchor-backbone decision and may
> only surface a *revisit-trigger*; it never re-decides the approach, the DOM contract, or any spec.
> **Run:** `run_20260612_102118_3ac39b` (cast-subphase-runner) · **Reanchor delegation:**
> `cast-comment-reanchor` (subagent-mode, bare-JSON verdicts) — dispatched live, verdicts not fabricated.

## Recommended disposition

**`BACKBONE HOLDS: confirmed`.** The existing, **unmodified** v2 comment/version layer, attached to a
hand-crafted *varying* maker-style HTML pair, held under the resolved logical-backbone +
quote-anchored-DOM approach. On a regenerate-with-moved-text: **zero new orphans for surviving
content** (only the genuinely-deleted block orphaned), every surviving comment re-placed on the
varying v2 DOM, `block_diff` stayed deterministic on the `(kind, ref)` id backbone, and the v2
"NO `id=`" DOM contract held on both renders. One **carry-forward** (a verbatim-carriage maker clause)
and two **Phase-3 inputs** (generic-anchor hazard, `section_hint` robustness) are recorded below.
**The binding G1 decision is the human gate after both spikes — not made here.**

---

## Framing (kept straight, per the grounding insight)

All v2 anchor validation is **source-side**: comments anchor to the canonical `.collab.md`, the
displacement detector (`create_next → displaced_comment_ids`) is a pure substring find over the **new
source markdown**, and `cast-comment-reanchor` searches the **new source**, not the maker HTML (the
maker never writes the source — v3 FR-008). A varying maker render therefore **cannot orphan a comment
at the DB layer by itself**. The genuine exposure 1b instruments is **(1)** silent `<mark>`-placement
loss when the maker paraphrases requirement text, **(2)** the implied "anchorable text carried verbatim
and contiguous in the DOM" maker obligation, and **(3)** the full v2 reanchor chain firing on a real
source edit. This spike measures all three.

A direct consequence, measured below: a **pure/layout move does not displace** at the source backbone.
The plan's "moved" case is realized as a **maker-layout move** (FR-005's container relocated to a
different section in v2 with its source text byte-identical) — a *placement* concern, not a
*displacement* one. Displacement is driven only by source rewording/deletion. This sharpens, and does
not contradict, the plan.

## Test bed (isolated — never the live house DB)

| Artifact | Path |
|---|---|
| Source pair (original / edited) | `source/original.collab.md`, `source/edited.collab.md` |
| Maker render v1 (layout A — card stack) | `feature-maker-v1.html` |
| Maker render v2 (layout B — reordered, FR-005 moved to its own "Observability" section) | `feature-maker-v2.html` |
| Byte-faithful placement harness | `spike_mark_placement.py` |
| Test-bed driver (seed → `create_next` → reanchor → apply → re-measure → diff) | `spike_backbone.py` |
| DOM-contract audit (zero-`id` + FR-028) | `spike_audit.py` |
| Throwaway SQLite (gitignored, disposable) | `scratch.sqlite` |
| Reanchor I/O (dispatch payload + verdicts) | `reanchor_input.json`, `reanchor_verdicts.json` |
| Driver state + metrics | `state.json`, `metrics.json` |

**Isolation asserted in-harness** (`_assert_isolated`): scratch DB `…/spikes/1b/scratch.sqlite` ≠ live
house DB `/home/sridherj/.cast/diecast.db`; scratch slug `spike-1b-anchor-survival`; **no** real
`goals/spike-1b-anchor-survival/` folder was created. Confirmed post-run.

## Seeded comments (6 open, varied `author_kind`, one per plan case)

| id | case | author_kind | quoted_text (against original) | intended unit |
|----|------|-------------|--------------------------------|---------------|
| 1 | reword (will be reworded) | human | `delivered on time without manual effort` | US1 |
| 2 | delete (legitimate-orphan control) | agent | `retain the three most recent export artifacts per schedule` | FR-003 |
| 3 | stay (must NOT displace) | human | `lists runs newest-first with a status badge per run` | SC-003 |
| 4 | move (maker-layout move) | agent | `read-only history of the last fifty export runs` | FR-005 |
| 5 | generic (short/generic quote) | human | `the owner` | FR-004 |
| 6 | section (maker section renamed vs canonical heading) | agent | `accept a cron-style cadence expression and validate it before saving` | FR-001 |

---

## Measured numbers

### 1. Mark placement on v1 (maker layout A) — scoped to the intended container

Harness mirrors `requirements_comments.js` `highlight()` **byte-faithfully**: whole-`.rr-document`
text-node concatenation + `concat.indexOf(quote)` (Python `str.find`), **no whitespace normalization**.
A hit counts **only** when the first match lands inside the comment's intended requirement unit (units
identified by their canonical id rendered as **visible text**, never an `id=` attribute).

| id | case | found | landed unit | in intended | note |
|----|------|-------|-------------|-------------|------|
| 1 | reword | ✓ | US1 | ✅ | unique phrase |
| 2 | delete | ✓ | FR-003 | ✅ | |
| 3 | stay | ✓ | SC-003 | ✅ | |
| 4 | move | ✓ | FR-005 | ✅ | |
| 5 | generic | ✓ | **HERO** | ❌ **false placement** | `concat.indexOf("the owner")` matched the hero prose *before* FR-004 — the seeded hazard |
| 6 | section | ✓ | FR-001 | ✅ | placed via the verbatim quote **despite** the maker section being renamed "Functional Requirements" → "What the scheduler does" |

**v1 placement: 5/6 land in the intended container.** The 6th (generic) is the deliberate
**false-placement probe**: a short/generic quote `find()`s its *first* occurrence anywhere, which here is
an unrelated hero sentence — a naive `find() ≥ 0` check would have falsely "passed" it. Container-scoping
turns it into a real, failing measurement. **100% placement for every well-formed (uniquely-anchored)
comment whose source text is untouched.**

**Harness self-test (split-across-inline-elements):** the quote
`a recurring cadence for a report export` straddles `<strong>recurring</strong>` in US1; the byte-faithful
concat join places it correctly (offset 686, unit US1), and a re-spaced variant (`a␣␣recurring cadence`) is
correctly **rejected** — proving no whitespace normalization. (`spike_mark_placement.py` self-test: **OK**.)

### 2. Regenerate-with-moved-text → displacement (`create_next` on the edited source)

`requirement_version_service.create_next(slug, edited_source)` cut **v2**; convergence `unconverged`
(open comments present).

- **`displaced_comment_ids` = `[1, 2, 5]`** = `{reword, delete, generic}`.
- **Assertion `displaced == {reword, delete, generic}`: ✅ True.**
- **Assertion the untouched comments did NOT displace (`{stay, move, section}` disjoint from displaced):
  ✅ True.** Critically, the **maker-layout move (FR-005, id 4) did NOT displace** — its source text is
  byte-identical, so the backbone correctly leaves it alone. (Initial run also surfaced that the generic
  `the owner` quote can *coincidentally* re-match an unrelated added requirement — `FR-006`; the test bed
  was tightened so the generic case genuinely displaces. The coincidence itself is logged as a Phase-3
  input below.)

### 3. Reanchor chain (`cast-comment-reanchor`, subagent-mode) over the 3 displaced comments

`{displaced comments, old_content, new_content}` where **`new_content` is the new source markdown** (v2
contract), not the maker HTML. Live dispatch; verdicts:

| id | case | verdict | `new_quoted_text` | verbatim in new source? | confidence |
|----|------|---------|-------------------|--------------------------|------------|
| 1 | reword | **relocated** | `stakeholders receive the report on schedule without anyone lifting a finger` | ✅ | 0.92 |
| 2 | delete | **orphaned** | `null` | n/a (content genuinely gone) | 0.90 |
| 5 | generic | **relocated** | `the report owner` | ✅ | 0.78 |

- Verdicts applied through the **same-door** `relocate_comment` / `orphan_comment` service calls, each
  relocate first re-validated against the new source (the route's **FR-019 verbatim backstop**). **Backstop
  passed on every relocate** (`backstop_ok = True` for ids 1 and 5) — **zero** 422 downgrades, so **zero**
  gate-failure signals.
- **Deleted block (id 2) → `orphaned` is correct, not a "new orphan":** the retention requirement is
  genuinely absent from the new source.
- **Orphan-over-guess:** id 5's content clearly survived as the unique span `the report owner`, so the
  honest verdict was a **confident relocate**, not an orphan. The asymmetry is still **structurally
  enforced**: the FR-019 backstop means any non-verbatim relocate the agent might have guessed is rejected
  and downgraded to orphan (tray-only) — a wrong guess can never silently mis-attach. The clean orphan
  case (id 2) exercises the orphaned branch directly.

### 4. Re-measure mark placement on v2 (maker layout B) — with relocated quotes

Relocated comments now carry their **new** verbatim span; orphaned comments are tray-only (excluded). v2
uses a **deliberately different layout/section ordering** (Success Criteria before Capabilities; FR-005
pulled into its own "Observability" section).

| id | case | current quote | landed unit | in intended |
|----|------|---------------|-------------|-------------|
| 1 | reword | `stakeholders receive the report on schedule without anyone lifting a finger` | US1 | ✅ |
| 3 | stay | `lists runs newest-first with a status badge per run` | SC-003 | ✅ |
| 4 | move | `read-only history of the last fifty export runs` | FR-005 (now in "Observability") | ✅ |
| 5 | generic | `the report owner` | FR-004 | ✅ (unique anchor resolves the v1 false placement) |
| 6 | section | `accept a cron-style cadence expression and validate it before saving` | FR-001 (renamed section) | ✅ |

- **v2 placement rate (surviving comments): 5/5 = 100%.**
- **Orphaned ids = `[2]` = exactly the deleted-block comment.** `only_deleted_orphaned: True`.
- **Orphan delta for surviving content = 0 (zero new orphans).** Every comment whose content survives the
  edit ended `open` **and** mark-placeable on the varying v2 DOM; only the genuinely-deleted block orphaned.
- The **maker-layout move (id 4)** re-placed cleanly in FR-005's new "Observability" container — a moved
  *render* with unchanged *source* survives via the verbatim quote.

### 5. `diff_blocks` determinism + partition invariant (source pair only — maker HTML plays NO role)

`diff_blocks(parse(original), parse(edited))` run twice; `summarize()` byte-identical across runs.

- **Deterministic: ✅ True.**
- **Partition invariant — old side: ✅** every old block appears exactly once across `removed ∪ modified.old ∪ unchanged.old`.
- **Partition invariant — new side: ✅** every new block appears exactly once across `added ∪ modified.new ∪ unchanged.new`.
- **Counts:** `{added: 1, modified: 3, removed: 1, unchanged: 12}`.
  - `removed = [FR-003]` (the deleted block) · `added = [FR-006]` · `modified = [FR-004, SC-002, US1]` (the reworded rows).
  - The **maker-layout-moved FR-005 lands in `unchanged`** by its `(kind, ref)` key — **evidence the id
    backbone needs no new machinery**; only the Phase-4b *narration* agent becomes id-aware. **The maker
    HTML is not an input to this engine — recorded explicitly.**

### 6. DOM-contract audit (zero-`id`, FR-012/013 + FR-028) — both renders

`spike_audit.py` (replays the golden structural assertions), exit 0:

| file | `id=` attrs | `data-block-anchor` | scripts | non-sanctioned src | inline `<script>` | `http(s)://` | `data-goal-slug` | verdict |
|------|-------------|---------------------|---------|--------------------|-------------------|--------------|------------------|---------|
| v1 | 0 | 0 | `/static/htmx.min.js`, `/static/requirements_comments.js` | none | 0 | 0 (no CDN) | ×1 | **PASS** |
| v2 | 0 | 0 | `/static/htmx.min.js`, `/static/requirements_comments.js` | none | 0 | 0 (no CDN) | ×1 | **PASS** |

Each requirement unit is one contiguous semantic container under a real heading; the canonical id is a
**visible text label**, never an `id=`. FR-028 progressive enhancement honored (only the two sanctioned
script refs + `data-goal-slug`; CSS inline; no CDN fonts).

---

## Success-criteria checklist (from the sub-phase plan)

- [x] `spike-results.md` records, with numbers: v1 + v2 mark-placement rates (5/6 scoped on v1; 5/5 on v2),
      displaced count (3), per-comment reanchor verdicts, orphan delta (0 new), `diff_blocks` partition result (✅).
- [x] The `section_hint`-mismatch probe outcome recorded **explicitly**: **places via the verbatim quote**
      despite the renamed maker section (id 6, both v1 and v2) — it did **not** degrade to tray-only.
- [x] Committed evidence pair: maker HTML v1 (layout A) + v2 (layout B) + source pair (original + edited).
- [x] Zero-`id` audit on **both** HTML files (PASS; replayable via `spike_audit.py`).
- [x] Throwaway harness scripts committed under `spikes/1b/` (replayable: `build` → reanchor → `apply`).
- [x] `displaced_comment_ids` equals exactly the reworded + deleted + generic(reworded-anchor) set; the
      untouched (stay / move / section) did **NOT** displace.
- [x] Zero new orphans for surviving content; only the deleted-block comment orphaned.
- [x] A **recommended** disposition written (`BACKBONE HOLDS: confirmed`) — not a binding re-decision.

## `section_hint`-mismatch probe — explicit outcome

Comment id 6 was captured under canonical heading `Functional Requirements`, but the maker renders that
section as **"What the scheduler does"** (v1) and **"Capabilities"** (v2). Placement is driven by the
**verbatim quote** within the intended container, **independent of section name** — it placed correctly on
both renders. **Outcome: places-via-quote (did not degrade to tray-only).** Recorded as a Phase-3 input:
`section_hint` is a tray/disambiguation hint, not a placement key — robust to maker section renames.

## Carry-forward & Phase-3 inputs (recorded, NOT acted on — no spec edit in Phase 1)

1. **Verbatim-carriage maker clause (the named carry-forward).** Quote anchoring holds **iff** the maker
   carries each requirement unit's anchorable text **verbatim and contiguous** within one container. This
   spike satisfied it by construction; the v3 maker contract needs an explicit *"anchorable text carried
   verbatim in the DOM"* clause. Flag for the Phase-3 `/cast-update-spec` activity. **No spec edit here.**
2. **Generic-anchor hazard (Phase-3 input).** A short/generic quote (`the owner`) **false-placed** on the v1
   DOM (landed HERO) and **coincidentally re-matched** an unrelated added requirement at the source layer
   (`FR-006`) before the test bed was tightened. Mitigation belongs in Phase 3: the maker/composer should
   prefer **unique, sufficiently-specific** anchor spans; the comment composer may warn on quotes with
   multiple document matches.
3. **Harness-fidelity / live-browser carry-forward.** The Python harness is byte-faithful (`concat.indexOf`,
   no normalization, split-quote self-test passes), but a whitespace-normalization gap could still diverge
   from a real browser. **Autonomous run — no browser available**; a live-browser eyeball of v1/v2 `<mark>`
   placement is carried forward as a **human-eyeball** item (static verdict only; never blocks per the
   no-browser-for-visual-gates rule).

## Revisit-trigger status

**None raised.** Quote anchoring did **not** prove insufficient under rewording/deletion/move: every
surviving comment relocated to a verbatim span the FR-019 backstop accepted, the lone orphan was a genuine
deletion, and the id backbone diffed deterministically with the partition invariant intact. The
anchor-backbone decision is **validated**. (Binding confirmation is the human **G1** gate after sp1a + sp1b.)

## Replay

```
cd docs/goal/refine-requirements-better-rendering-v3/spikes/1b
python spike_backbone.py build      # fresh scratch DB, seed, measure v1, create_next → displaced
# dispatch cast-comment-reanchor (subagent) over reanchor_input.json → reanchor_verdicts.json
python spike_backbone.py apply      # FR-019 backstop + same-door apply, measure v2, diff_blocks
python spike_audit.py               # zero-id + FR-028 gate on both renders
python spike_mark_placement.py      # split-quote harness self-test
```
