# sp4 Sole File Writer — `cast-requirements-writeback` agent — Output

**Status:** ✅ Complete · 8 new apply tests green · 261-test requirements/change-request band green · 0 regressions

## What was built

The **one and only** code path that mutates a goal's canonical `refined_requirements.collab.md`.
It mirrors `cast-update-spec`'s "sole write path" posture and is the explicit
`cast-delegation-contract` carve-out: the server owns the proposal DB (sp2 intake / sp3a conflict
/ sp3b notify), and this path owns the file apply. The silent-drift bug US7 exists to kill is now
**structurally impossible** — there is no whole-file overwrite path; every apply is a verified
surgical splice.

### 1. Apply path — `cast-server/cast_server/services/change_request_service.py` (extended)

The byte-faithful, fully-unit-tested apply machinery (sp2 created the intake half; sp4 adds the
apply half on the same module):

- **`apply_change_request(cr_id, *, goal_dir, locate=verbatim_locate, allowed_root, actor,
  target_quote_override, section_hint_override, db_path)`** — the pipeline:
  **path-scope → conflict gate (sp3a `detect_conflict`) → surgical splice → byte-identity verify
  → atomic write → `create_next()` version bump → change summary (provenance badge) → `applied`
  event + `notifications_outbox` row in ONE `BEGIN IMMEDIATE` txn.**
  Returns `{status, applied_version, convergence, displaced_comment_ids, change_summary,
  provenance_badge, file}`.
- **`verbatim_locate(content, target_quote, section_hint)`** — the production quote→region
  locator: the **enclosing line(s)** of the verbatim quote (sp3a's "region = enclosing line"
  discipline so a reworded region reads `conflicted`, not a false `clean`), or `None` →
  `orphaned`. Pure; the same injected-`Locator` shape `detect_conflict` consumes.
- **Surgical splice helpers** — `_apply_addition` (insert under the named `section_hint`, else
  file tail) / `_insert_in_section` / `_apply_modification` (replace exactly the located region).
  Pure character splices: every original byte survives in order.
- **`_verify_surgical`** — the load-bearing guard. An addition may remove **nothing** (common
  prefix+suffix must reconstruct the original); a modification's bytes before/after the region
  must survive verbatim. If it ever fails, we raise **before** writing — never a drifted file.
- **`_commit_spliced`** — the single carve-out write: tmp file + `os.replace` (atomic, crash-safe).
  Deliberately **not** `Path.write_text` / `save_artifact` (the whole-file-overwrite tokens the
  US7 guard greps for) — the bytes written are the verified splice of the file we just read.
- **`_provenance_badge`** — `+FR-099 — added by planning · agent cast-high-level-planner · derived
  from plan.collab.md`, built from the change-request's own `origin_*`/`author` columns + the lead
  change item (data, never an author code-branch — FR-013).
- **`WritebackRefused`** — the three non-apply outcomes (`conflicted` / `orphaned` / `out-of-tree`),
  each leaving the file byte-identical. Conflict/orphan leave a `change_request_events` audit row
  (never a silent no-op); conflict flips status to `conflicted` and carries the 3-way
  `ConflictSurface`. **No auto-merge.**
- **`apply_for_goal(...)`** + a **CLI** (`python -m cast_server.services.change_request_service
  apply <goal_slug> <cr_id> [--actor|--target-quote|--section-hint]`) — the production entry the
  agent shells out to. It resolves the routed-goal `folder_path` (render-service precedent), wires
  `verbatim_locate`, scopes the writer to the goal dir, and prints one JSON line (`applied` /
  `refused`, exit 0/1).

### 2. Agent — `agents/cast-requirements-writeback/` (created)

`config.yaml`: `model: sonnet, dispatch_mode: subagent, interactive: false, context_mode:
lightweight, allowed_delegations: [cast-comment-reanchor]`. The subagent precedent
(cast-comment-reanchor / cast-requirements-checker) — outside `cast-delegation-contract`, returns
ONE bare-JSON verdict, no `.output.json`.

`cast-requirements-writeback.md`: the orchestrator. It invokes the apply CLI (never hand-edits the
file — the byte-faithful logic lives in tested Python), and branches on the verdict:
- **clean** → applied; report version + provenance badge + change summary.
- **conflicted** → surface the 3-way choice, file untouched, stop (no merge).
- **orphaned** → dispatch **`cast-comment-reanchor`** (the only relocator) to get a verbatim
  relocated quote, retry the CLI **once** with `--target-quote`; orphan stays surfaced otherwise.
- **out-of-tree** → hard refusal, never widen scope.

### 3. Tests — `cast-server/tests/test_writeback_apply.py` (created, 8 tests)

Addition applies under `section_hint` with every other byte identical (removing the one inserted
row reproduces the original) + version bump + provenance badge + `applied` event + outbox row;
clean modification is surgical (prefix/suffix byte-identical, real `verbatim_locate`); `conflicted`
→ refused + surfaced + file untouched + audit row + status flip; `orphaned` → refused + untouched +
audit row; path-scope out-of-tree → refused, no file, no apply/conflict event, no crash; render
(`rerender_requirements_html`) leaves the `.collab.md` byte-identical (the writer is the only
mutator); `apply_for_goal` resolves `folder_path` end-to-end.

## Verification

- `uv run pytest tests/test_writeback_apply.py` → **8 passed**.
- `uv run pytest tests/ -k "requirement or change_request or outbox or conflict or version or comment or schema_migration or writeback"` → **261 passed**, 0 regressions.
- `python -c "import cast_server.app"` → clean; full suite **862 tests collected**, no import errors.
- `grep -rn "write_text\|save_artifact" agents/cast-requirements-writeback/ …/change_request_service.py` → only prose/comments **forbidding** the overwrite path; **no actual call**.
- `bin/generate-skills` → re-run; `cast-requirements-writeback` SKILL.md materialized (61 agents).

## Success criteria (all met)

- [x] Addition applies surgically; all non-target bytes identical.
- [x] `conflicted` / `orphaned` → refused + surfaced, file untouched (audit row left).
- [x] Provenance appended; version bumped via `create_next()`; change summary carries the badge.
- [x] `applied` event + outbox row written in one apply txn.
- [x] Writer is path-scoped to the goal's `.collab.md`; out-of-tree target refused, never crashes.
- [x] No whole-file overwrite anywhere; the server (sp2 intake / any route) writes no file.
- [x] `cast-comment-reanchor` is the only quote→region relocator (displaced-target path).
- [x] `bin/generate-skills` re-run.

## Notes / hand-offs to sp5 (E2E + spec + guard)

- **Spec carve-out to restate:** the new `cast-requirements-roundtrip.collab.md` must document the
  sole-writer carve-out — server owns the proposal DB, `cast-requirements-writeback` (via the apply
  CLI) owns the file apply. No conflict with `cast-delegation-contract`; restate, don't fork.
- **FR-007 guard extension:** `test_writeback_apply.py::test_render_never_mutates_collab_md`
  asserts render never mutates; sp5's `test_fr007_readonly_guard.py` should add the
  post-writeback byte-identity guard (the apply is the *only* sanctioned mutation).
- **Outbox dedupe:** for an auto-applied addition, sp2 intake already queued one outbox row and the
  apply txn queues a second (richer) one. sp3b dedupes on `change_request_id` at read time → the
  human/agent sees the change once. Intentional, not a bug.
- **Synthetic-child E2E (SC-006):** sp5 drives `synthetic_child.py` → intake → accept → this
  agent's apply, asserting the round-trip closes with provenance + notification + byte-faithful file.
