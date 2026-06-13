# Review Summary: Refine Requirements v2 — Phase 1

Self-conducted SMALL-CHANGE review (max ~1 issue per section per sub-phase). A full 5-child
`/cast-plan-review` fan-out was intentionally NOT run: this split executes under an **autonomous,
no-user-questions** delegation, and an interactive review agent would stall at its question gates. The
source plan was already through `cast-plan-review` (run_20260611_160312_654fa9, BIG CHANGE, 5/5 resolved);
this pass checks only that the *split* preserves that resolved contract.

## Open Questions

**None blocking.** Mirrors the source plan ("Open Questions: None blocking"). The two planning-level
decisions (importlib grammar bridge; `unrecognized_sections` over a 9th block kind) were settled before
the split. All plan-review Decisions #1–#5 are carried into the relevant sub-phase files verbatim.

## Cross-Cutting Findings (surfaced during the split — already baked into the files)

1. **Path drift in the source plan (resolved in `_shared_context.md`).** The plan names
   `tests/test_migrations.py` and `tests/test_us7_spec_kit_shape.py`; neither exists under those names. The
   real migration test is `cast-server/tests/test_schema_migration.py` (sp2b targets it), and the
   subprocess-checker precedent file does not exist (sp4 establishes the pattern from scratch, with a
   `parents[N]` depth verification step). All plan test paths were rewritten with the real
   `cast-server/tests/` prefix. **This is the one thing a human should glance at** — confirm the executor
   should extend `test_schema_migration.py` rather than create a new file (the sub-phase says so).
2. **Two `schema.sql` files.** Canonical = `cast-server/cast_server/db/schema.sql`; legacy =
   root `db/schema.sql`. sp2b edits the canonical only; retiring the root copy is flagged as a separate
   housekeeping commit, out of scope.
3. **`parents[3]` / `parents[2]` index fragility.** sp2a's grammar bridge and sp4's checker subprocess both
   compute the repo root by walking up from `__file__`. Both sub-phases include an explicit
   "print-and-verify the resolved path once" step rather than trusting the index blindly.

## Review Notes by Sub-Phase

### sp1 — Design note
- Docs-only; no automated test possible. Success is a content checklist + canonical filename. No issue.
- Architecture: correctly records the *rejected* options (ULID/DB-canonical keystone, deterministic
  anchors) so the note is usable as a "do not re-inherit" reference, not just a "what we did" note. ✓

### sp2a — Parser package
- Tests (deferred to sp4): the split keeps all parser tests in sp4 so sp2a ∥ sp2b stay on disjoint files.
  Trade-off accepted — sp2a includes a temporary `python -c` smoke to catch gross mapping errors before
  handoff. ✓
- Code Quality: `Block.ref` wording pinned to plan-review Decision #2 ("in-memory only…"). ✓
- One watch-item (already noted in the file): front-matter parsing should reuse any existing cast-server
  `.collab.md` header handling before hand-rolling — flagged in Execution Notes, not blocking.

### sp2b — Thin DB spine
- Architecture: the two-source lockstep (`schema.sql` ↔ `_run_migrations()`) is the main risk; the file
  calls it out and the migration test guards the migration path. ✓
- Tests: extends the real `test_schema_migration.py` with both fresh-DB and pre-existing-DB existence
  assertions + index assertions. ✓

### sp3 — Version service
- Architecture: explicitly models on `goal_service.py`/`task_service.py`, NOT `orchestration_service.py`
  (Decision #1). ✓
- Performance/Txn: implements the accepted single-user limitation and records `BEGIN IMMEDIATE` as a
  fix-forward comment only (Decision #5) — does not over-build locking. ✓
- One watch-item (noted in the file): FK-on-`goals(slug)` may require seeding a `goals` row in tests;
  flagged forward to sp4's seeding step.

### sp4 — FR-007 guard + tests
- Tests: includes both plan-review positive tests — Decision #3 (unknown-H2 capture) and Decision #4
  (multi-line bullet grouping). ✓
- Guard: byte-identity (sha256 before==after) + `cast-spec-checker` exit-0 subprocess + grammar-bridge
  smoke test (fails loudly if the checker moves). ✓
- Delegation: `/cast-pytest-best-practices` over the three new files, with an explicit instruction to
  reject any "simplification" that loosens a pinned assertion. ✓
