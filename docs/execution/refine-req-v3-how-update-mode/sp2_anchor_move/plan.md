# Sub-phase 2: Anchor Move — Comments Anchor to the Render Snapshot

> **Pre-requisite:** Read `docs/execution/refine-req-v3-how-update-mode/_shared_context.md` before
> starting — especially the Crux Decision, the `block_ref`-NULL-is-success rule (plan-review Decision
> #1), and the `block_ref`-is-server-resolved trust boundary.

## Objective

A comment's full lifecycle (create/validate, displacement, relocate backstop, re-anchor dispatch) runs
against the **published render's text** with a server-resolved `block_ref` bridge to canonical source
space. Every pre-existing comment migrates without loss (worst case: the existing `.comment-unplaced`
badge — never deletion or silent orphaning). **The verbatim-carriage gate is still in force at the end
of this sub-phase** — anchoring moves first; the carriage flip (Sub-phase 3b) only happens once comments
no longer depend on it.

## Dependencies

- **Requires completed:** Sub-phase 1b (its `MIGRATION_SIZING` table sizes the migration; its
  classified miss-handling is the creation path's blueprint).
- **Runs in parallel with Sub-phase 3a.** Disjoint files: this sub-phase touches `comment_service.py`,
  `comment_anchor.py`, `api_requirements.py`, `schema.sql`, `agents/cast-comment-reanchor/`,
  `test_schema_migration.py`; sp3a touches `render_job_service.py`, `config.py`, the HOW prompt's UPDATE
  section. **No shared files** — verify before starting.
- **Assumed codebase state:** `create_comment` (`comment_service.py:92`), `list_comments` (`:125`,
  derived `displaced`), `relocate_comment` (`:244`); `resolve_block_ref` (`comment_anchor.py:29`),
  `resolve_block_context` (`:52`); `requirement_comments` table (`schema.sql:131`); `comment_events`
  trail (`schema.sql:146`); the route-level 422 relocate backstop in `api_requirements.py`.

## Scope

**In scope:**
- Additive schema: `requirement_comments.block_ref TEXT NULL` + `anchor_space TEXT NOT NULL DEFAULT
  'source'`; migration test coverage.
- `create_comment` resolves `block_ref` **server-side** from the served render; new comments get
  `anchor_space='render'`.
- `list_comments` derived `displaced` re-targets the served render text for `'render'`-space comments
  (`'source'`-space comments keep the source check until migrated).
- Route-level 422 relocate backstop re-targets the served render text for `'render'`-space comments.
- `cast-comment-reanchor` **contract v3** (additive superset of v2): optional render-space inputs.
- One-time idempotent migration: flip placeable comments to `'render'` + backfill `block_ref`; leave
  the rest in `'source'` space, surfaced by the existing badge. Record disposition in `comment_events`.

**Out of scope (do NOT do these):**
- Do NOT flip the verbatim-carriage gate — that is Sub-phase 3b. The carriage clause stays in force
  here; this sub-phase only moves *where comments anchor*, so the flip is safe later.
- Do NOT edit the spec — flag deltas for the Sub-phase 5 `/cast-update-spec` pass.
- Do NOT touch `render_job_service.py` (sp3a/sp3b property), `block_diff.py` / `diff_render.py`, or the
  HOW/WHAT prompts.
- Do NOT change `requirements_comments.js` placement logic — it already places against the rendered DOM;
  **verify only** that nothing client-side assumes source-substring semantics.
- Do NOT accept `block_ref` from the client — keep it OUT of the POST body schema (trust boundary).
- Do NOT re-implement `container_text_index` or `strip_inline_markdown` — import both.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/db/schema.sql` | Modify | `requirement_comments` (:131) gains `block_ref` + `anchor_space` |
| `cast-server/tests/test_schema_migration.py` | Modify | Extend with the two new columns + back-compat default assertion |
| `cast-server/cast_server/services/comment_service.py` | Modify | `create_comment` resolves `block_ref` + sets `anchor_space='render'`; `list_comments` displacement re-targets render text per `anchor_space` |
| `cast-server/cast_server/requirements_render/comment_anchor.py` | Modify | Add a **render-space** resolver (place against served render text → enclosing labeled unit → canonical id); cross-boundary/ref-less → NULL |
| `cast-server/cast_server/routes/api_requirements.py` | Modify | 422 relocate backstop re-targets served render text for `'render'`-space comments; `block_ref` stays OUT of the POST body |
| `agents/cast-comment-reanchor/cast-comment-reanchor.md` + `config.yaml` | Modify | Contract v3 additive superset (optional render-space inputs); `sonnet` tier untouched |
| `cast-server/cast_server/services/comment_service.py` (migration fn) OR a dedicated migration module | Create/Modify | One-time idempotent render-space migration over existing open comments |
| `cast-server/tests/test_comment_anchor_render.py` (or extend existing) | Create | Render-space resolver + migration + displacement tests |

## Detailed Steps

### Step 2.1: Additive schema + migration test

Add to `requirement_comments` (`schema.sql:131`):

```sql
block_ref    TEXT NULL,                          -- canonical id of the enclosing labeled unit container
                                                  --   (server-resolved); NULL = cross-boundary OR ref-less render
anchor_space TEXT NOT NULL DEFAULT 'source',     -- 'source' | 'render'
```

Old rows keep `anchor_space='source'`, `block_ref=NULL`. Extend `test_schema_migration.py` to assert
both columns exist after migration and that a pre-existing row reads back `anchor_space='source'`.

### Step 2.2: Render-space resolver in `comment_anchor.py`

Add a render-space sibling to `resolve_block_ref` (do **not** rewrite the source-space one — it stays
for `'source'` comments). Given the **served render text** + a quote:
- `idx = container_text_index(render_html)` (import — no re-walk);
- place the quote; take the enclosing labeled unit container (`idx.unit_at` + the visible anchor label)
  → the canonical id = `block_ref`;
- **cross-boundary → NULL** (never guessed — the orphan-over-guess discipline carries over);
- **ref-less render (zero anchor labels) → NULL by construction** — this is the honest, expected state
  (plan-review Decision #1), NOT a placement miss.

### Step 2.3: Creation path resolves `block_ref` server-side

`create_comment` (`comment_service.py:92`, same-door, `author_kind` untouched — FR-013): read the
**served** artifact, run the Step 2.2 resolver, store `block_ref` + `anchor_space='render'`.

- **`block_ref=NULL` is stored and treated as success** when the render is ref-less (zero anchor
  labels) — the comment lives in render space and surfaces normally; it just has no source handle
  because the source has none either. Never retry or badge a ref-less NULL as broken.
- **Trust boundary:** `block_ref` is resolved server-side; it is NEVER read from the POST body. Keep
  the field out of the request schema. Record the served artifact's embedded `source-hash` in the
  `created` event payload for forensics (no new column).

### Step 2.4: Displacement re-target in `list_comments`

`list_comments`' derived `displaced` (`comment_service.py:125`):
- for `anchor_space='render'` comments → `quoted_text not in <served render text>` (extract via the
  shared `container_text_index` walker — **never a second tokenizer**);
- for `anchor_space='source'` comments → keep the existing source check (until migrated);
- **no render artifact on disk → fall back to the source check** (a missing file must never crash the
  read-time detector — existing discipline);
- a ref-less-render NULL `block_ref` is **never** treated as displaced/unplaced.

### Step 2.5: Relocate backstop re-target

The route-level 422 verbatim-substring relocate validation (`api_requirements.py`): for
`'render'`-space comments, validate the new quote against the **served render text**; `'source'`-space
comments keep the source check.

### Step 2.6: `cast-comment-reanchor` contract v3 (additive superset)

Extend `cast-comment-reanchor.md` (+ `config.yaml`) to a **v3** that adds OPTIONAL render-space inputs:
the comment's prior-render container text (by `block_ref`) and the candidate new-render container text.
- Verdict vocabulary (`relocated > resolved > orphaned`-when-unsure), safety machinery
  (orphan-over-guess, 422 backstop, no-op-on-garbage), and the `sonnet` tier carry **untouched**.
- Every new input optional → every existing call site (the v2 verdicts-only calls) stays byte-valid.
  Same precedent as v2-over-v1.

### Step 2.7: One-time idempotent migration

For each existing open comment (1b's exact procedure, productionized):
- attempt render-space placement + `block_ref` resolution against the served render;
- **places** → flip `anchor_space='render'`, backfill `block_ref` (NULL allowed for ref-less);
- **doesn't place** → leave `'source'`-space, surfaced by the existing `.comment-unplaced` tray badge;
- **never** resolve / orphan / delete — surface, don't suppress.
- Record per-comment disposition in `comment_events`. **Idempotent:** re-running flips nothing already
  in `'render'` space and re-resolves identically.

### Step 2.8: Verify the JS makes no source-substring assumption (no code change)

`requirements_comments.js` already places against the rendered DOM. **Verify only** (read + a static
assertion) that nothing client-side assumes source-substring semantics; do not change placement logic.

## Verification

### Automated Tests (permanent)
`pytest` green over:
- **Schema migration** (`test_schema_migration.py`): both columns present; old row default `'source'`.
- **Render-space resolver** (`test_comment_anchor_render.py`): in-block quote → correct `block_ref`;
  cross-boundary → NULL; **ref-less render (zero anchor labels) → NULL treated as success**.
- **Creation path:** a comment created against a maker render stores `anchor_space='render'` + the
  correct `block_ref`; `block_ref` is NOT accepted from the POST body (trust-boundary test — a body
  carrying a spoofed `block_ref` is ignored/rejected, the server resolves its own).
- **Displacement:** a `'render'`-space comment whose quote is absent from the served render reads
  `displaced=True`; a `'source'`-space comment still uses the source check; missing render file →
  source-check fallback, no crash; ref-less NULL never reads displaced.
- **Migration idempotency:** run migration twice over a fixture set → identical end state, no duplicate
  `comment_events`, nothing deleted/orphaned; a non-placing comment stays `'source'` + badged.
- **`eval_reanchor.py`** green against the v3 contract (legacy verdicts-only calls still valid; new
  optional render-space inputs accepted).

### Validation Scripts (temporary)
- A same-door `curl` create against a live maker render → confirm the response/DB row carries a correct
  server-resolved `block_ref` and `anchor_space='render'`; a second `curl` carrying a bogus `block_ref`
  in the body → confirm the server ignores it and resolves its own.

### Manual Checks
- `grep -n "container_text_index\|strip_inline_markdown" cast-server/cast_server/services/comment_service.py cast-server/cast_server/requirements_render/comment_anchor.py` —
  confirm both are imported, neither re-implemented.
- Confirm the verbatim-carriage gate (`maker_gate.check_html`) is **unchanged** by this sub-phase.
- Confirm `block_ref` is absent from the comment POST body schema in `api_requirements.py`.

### Static / carry-forward (no browser)
- The UI-minted-quote-highlights confirmation is a static verdict + human-eyeball carry-forward (the JS
  is unchanged; the rendered-DOM placement already works). Never blocks the autonomous run.

### Success Criteria
- [ ] `requirement_comments` has `block_ref` + `anchor_space`; old rows default `'source'`; migration
      test green.
- [ ] `create_comment` resolves `block_ref` server-side, sets `anchor_space='render'`; `block_ref`
      never from the client (trust-boundary test green).
- [ ] Ref-less-render `block_ref=NULL` is success everywhere (creation, displacement, migration) —
      never an unplaced miss.
- [ ] `list_comments` displacement re-targets render text per `anchor_space`; missing-file fallback safe.
- [ ] `cast-comment-reanchor` v3 is an additive superset; legacy call sites byte-valid; `sonnet` tier
      kept; `eval_reanchor.py` green.
- [ ] Migration is additive + idempotent; non-placing comments stay `'source'` + badged; nothing
      deleted/orphaned; disposition in `comment_events`.
- [ ] The verbatim-carriage gate is still in force (unchanged by this sub-phase).

## Execution Notes

- **Order matters: anchoring moves BEFORE the carriage flip.** This sub-phase deliberately leaves
  `maker_gate.check_html`'s verbatim-carriage class intact so the system is never simultaneously
  losing both the source anchor AND the verbatim guarantee. Sub-phase 3b flips carriage only after
  comments no longer depend on it.
- **The ref-less NULL trap (plan-review Decision #1):** a source with zero canonical ids has nothing to
  bridge to. Leaving this implicit invites an executor to "fix" a non-bug into a retry/badge loop.
  Treat ref-less NULL as success in creation, displacement, AND migration.
- **Trust boundary:** a spoofed `block_ref` would mis-route a future change-request. Server-resolved only.
- **Spec-linked files:** this sub-phase reverses `cast-requirements-render.collab.md` > US8 (same-door
  quote validation), US12 (derived displacement), US13/US19 (reanchor source-space inputs). **Do not
  patch the spec piecemeal** — flag every delta for the single Sub-phase 5 `/cast-update-spec` pass;
  until then the spec is knowingly ahead of the code.
