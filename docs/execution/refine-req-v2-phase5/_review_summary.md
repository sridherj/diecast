# Review Summary: refine-req-v2-phase5

> The source plan (`docs/plan/2026-06-11-refine-requirements-v2-phase5-roundtrip-writeback.md`) was
> authored by `cast-detailed-plan` with inline design review and a full "Design Review Flags" table.
> This summary consolidates those flags (carried into each sub-phase plan's **Execution Notes** /
> success criteria), adds the landed-code reconciliation done at split time, and lists the open
> questions (all owner-resolved — none block execution).

## Open Questions

**None blocking.** All four source-plan Open Questions are owner-resolved and folded into
`_shared_context.md` → "Pre-Existing Decisions":

1. Endpoint namespace → `POST /api/goals/{slug}/change-requests` (goals namespace). ✅
2. `base_version` → integer `requirement_versions.version`. ✅
3. Graduated-trust gate → single global `WRITEBACK_GATE_POLICY` config flag. ✅
4. Notification → **extend** the landed structured `{convergence, open_comment_count}` surface. ✅

The run was directed to proceed fully autonomously; no `AskUserQuestion` gates were hit.

## Landed-Code Reconciliation (done at split time)

Every `[PENDING Phase 4]` binding in the source plan was verified against landed code and resolved to
a concrete name (see `_manifest.md` → "Reconciliation Status"). Net effect: sub-phases reference real
signatures, not placeholders. One genuinely-new item: `WRITEBACK_GATE_POLICY` does not exist yet —
sp2 adds it to `config.py`.

## Review Notes by Sub-Phase

### sp1 — Proposal Spine
- ⚠️ **Thin-spine (must-do):** no `spec_elements(surrogate)` FK exists — use `target_quote +
  section_hint`; thin-spine comment block mandated in `schema.sql` so a future reader doesn't
  "restore" a surrogate FK. (In plan.)
- ⚠️ **Schema/migration drift:** canonical `schema.sql` ↔ `_run_migrations()` must stay byte-aligned
  — pinned by the table-existence migration test. (In plan.)
- Clarified: plan prose says "Four tables" but means **three** tables + the `RequirementsWriteback`
  *artifact* model. Documented in `_shared_context.md` and sp1 Execution Notes.

### sp2 — Same-Door Intake
- ⚠️ **FR-013 forcing function:** exactly one intake handler — a second internal write path silently
  violates same-door. Asserted in tests + a `grep` manual check.
- ⚠️ **Anti-spoof (security):** human `author`/`author_type` derived from request context, never the
  client body. Agent self-declares `agent`; browser cannot spoof `human`. (In plan + test.)
- Transactionality: row+event(+outbox) in one `BEGIN IMMEDIATE` txn. (In plan + test.)

### sp3a — Conflict Predicate
- ⚠️ **Thin-spine fragility:** no stable IDs → conflict detection *is* quote-location. Reuse the
  `cast-comment-reanchor` locator discipline; orphan must surface (never a silent no-op). (In plan.)
- Architecture: predicate kept pure/total (no DB/LLM/I/O; `locate` injected) — mirrors Phase 3b's
  `resolve` discipline. Pinned by a source/import manual check + a purity test.

### sp3b — Notification Outbox
- ⚠️ **Unification (must-do):** Phase 4 shipped the structured surface, so sp3b **extends**
  `{convergence, open_comment_count}` — it does **not** structure-from-boolean and does **not** stand
  up a parallel notifier. (Owner decision #4; in plan + a `grep` manual check.)
- Error & rescue: outbox is the dual-write fix — same-txn change+outbox insert (sp2 owns the write);
  UI dedupe key `change_request_id`. Crash assertion is unit-level here, e2e in sp5.

### sp4 — Sole File Writer
- ⚠️ **Delegation-contract carve-out:** the server never writes artifact files; this agent is the
  explicit carve-out (server owns the proposal DB, agent owns the file). Restated in the sp5 spec.
- ⚠️ **No whole-file overwrite:** lift `orchestration_service.update_manifest_status()` as the
  surgical-edit template; **never** `api_artifacts.save_artifact` `write_text` (the US7 silent-drift
  bug). Pinned by a `grep` check + the byte-identity test.
- ⚠️ **Path-scope (security):** writer scoped to the goal's `.collab.md`; out-of-tree target refused,
  never crashes. (In plan + test.)

### sp5 — E2E + Spec + Guard
- ⚠️ **SC-006 asserts the negative:** 0 ungated modifications, 0 lost/dup notifications after an
  injected crash — not just the happy path. (In plan.)
- ⚠️ **Spec lockstep:** new `cast-requirements-roundtrip.collab.md` **references** (not duplicates)
  the render + delegation specs; lints clean (`cast-spec-checker` exit 0); registered in `_registry.md`.
- Headless fallback: if `/cast-update-spec`'s interactive gate can't run headless, author in
  create-mode shape + record `auto-persisted: non-interactive run` (Phase 3a sp5b precedent).

## Recommended Follow-up (optional, per-sub-phase at execution time)

Each sub-phase plan calls out `/cast-pytest-best-practices` delegations on its test suites
(sp1, sp5) and `/cast-update-spec` as the gate-UX model (sp2) / spec author (sp5). Running
`/cast-plan-review` (SMALL CHANGE mode) on an individual sub-phase plan immediately before executing
it is encouraged but not required — the design-review flags above are already folded into each plan.
