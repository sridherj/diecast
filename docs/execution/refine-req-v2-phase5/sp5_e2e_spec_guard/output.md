# sp5 E2E Proof (SC-006) + Spec Lockstep + FR-007 Guard — Output

**Status:** ✅ Complete · 11 sp5 tests green (4 e2e + 7 FR-007 guard) · 273-test requirements/round-trip band green · 0 regressions · spec lints clean (exit 0) · 868 tests collect

Phase 5 is **done and provable without real downstream emitters.** A simulated downstream change
traces the entire receiving chain green, the binary SC-006 gate asserts the negatives, the
round-trip behavior is locked into a new canonical spec, and the FR-007 byte-identity guard now
proves the write-back agent is the *only* mutator.

## What was built

### 1. SC-006 end-to-end proof — `cast-server/tests/test_roundtrip_e2e.py` (created, 4 tests)

Drives the **simulated** emitter through the whole chain via the **same-door HTTP route** for intake
and the **sole-writer service path** for the file apply — deterministic (pure `verbatim_locate`, no
live subagent), so it stays in the **default suite** as the binary SC-006 gate (not a slow `eval_`).

- **`test_addition_traces_the_whole_chain_green`** — emit `requirements_writeback` → same-door intake
  (`201`, server-derived `author_type=agent`) → surgical apply → version bump (v1→v2) → change
  summary (`added==1`) + provenance badge (`FR-099 · planning · plan.collab.md`) → byte-identical
  splice on disk → relay drain → round-trip descriptor surfaces the change **exactly once**.
- **`test_modification_is_gated_at_intake_file_untouched`** — the negative: a modification of existing
  content intakes `proposed` (gated), queues **no** outbox FYI, and leaves the file byte-identical.
- **`test_conflicted_modification_is_refused_file_untouched`** — the load-bearing negative (US7): an
  apply over a region a human changed since `base_version` is **refused** (`conflicted`), the file is
  byte-identical, the 3-way surface is offered (no auto-merge), and a `conflicted` audit row is left.
- **`test_crash_between_commit_and_relay_loses_nothing_duplicates_nothing`** — injects one crash
  mid-drain; recovery re-delivers nothing flipped and loses nothing pending (at-least-once); the
  change has **two** outbox rows (intake FYI + apply FYI) yet `recent_writebacks` dedupes on
  `change_request_id` → surfaced exactly once (**0 lost / 0 duplicate**).

### 2. Simulated downstream emitter — `cast-server/tests/fixtures/synthetic_child.py` (created)

A pure, deterministic payload factory standing in for the hard-deferred real emitters. `writeback_artifact`
builds one `requirements_writeback` `output.json` artifact **validated against the real
`RequirementsWriteback` model** (same-door at the schema level); `emit_output` wraps a contract-v2
`AgentOutput` envelope; `extract_writebacks` pulls the proposals back out. Writes no file, drives no
subagent, carries only the columns an emitter legitimately controls (`author`/`author_type` are
server-derived at intake). Not collected as a test (fixture path, no `test_` prefix).

### 3. New canonical spec — `docs/specs/cast-requirements-roundtrip.collab.md` (created)

Authored directly in `/cast-update-spec` create-mode shape (the interactive approval gate cannot run
headless — Phase 3a sp5b precedent; recorded `auto-persisted: non-interactive run`). `bin/cast-spec-checker`
**exits 0**. Covers: the change-request lifecycle (`proposed→applied|conflicted|rejected|superseded`),
the same-door API, the graduated-trust `WRITEBACK_GATE_POLICY`, conflict semantics (`detect_conflict`:
`clean|conflicted|orphaned`, integer `base_version`), the sole-writer carve-out, and the extended
notification surface. **References — does not duplicate** — `cast-requirements-render.collab.md` (the
`block_diff`/`create_next`/`{convergence, open_comment_count}` surfaces) and
`cast-delegation-contract.collab.md` (the file-apply subagent carve-out), each by heading. The four
owner decisions are stated **verbatim** in a `## Decisions` section. Registered in
`docs/specs/_registry.md`.

### 4. FR-007 guard extension — `cast-server/tests/test_fr007_readonly_guard.py` (extended, +2 tests)

A third enforcement leg (the sole-mutator leg), documented in the module docstring:

- **`test_writeback_is_the_sole_mutator_and_surgical`** — applies one accepted addition (fresh unique
  `FR-901`) to a copy of the frozen spec-compliant fixture; removing the inserted line reproduces the
  original **byte-for-byte**; then render + version snapshot + re-parse leave the post-write source
  byte-identical (the writer is the *only* mutator); `bin/cast-spec-checker` stays green on the
  spliced source (SC-004 lock). The frozen fixture on disk is untouched.
- **`test_writer_has_no_whole_file_overwrite_path`** — the structural negative: tokenizes the apply
  module and asserts `write_text` / `save_artifact` never appear as **executable NAME tokens**
  (only as forbidding prose), while `_commit_spliced` / `read_text` do — so the no-overwrite ban is
  enforced by a test, not just convention.

### 5. Final reconciliation pass (Step 5.4)

Verified the landed names are adopted everywhere — `block_diff`/`summarize`, `create_next`,
`cast-comment-reanchor`, and the `{convergence, open_comment_count}` surface. No drift from
`_shared_context.md`'s Naming Contract.

## Verification

- `uv run pytest tests/test_roundtrip_e2e.py tests/test_fr007_readonly_guard.py` → **11 passed**.
- `uv run pytest tests/ -k "requirement or change_request or outbox or conflict or version or comment or schema_migration or writeback or roundtrip or notification or fr007"` → **273 passed**, 0 regressions.
- `python3 bin/cast-spec-checker docs/specs/cast-requirements-roundtrip.collab.md` → **exit 0**.
- `grep -n "cast-requirements-roundtrip" docs/specs/_registry.md` → registry row present.
- `uv run pytest --collect-only` → **868 tests collected** (6 new), no import errors; `synthetic_child.py` not collected as a test.

## Success criteria (all met)

- [x] SC-006 e2e passes: full chain green for an addition; **0** ungated modifications; **0** lost/dup notifications after an injected crash.
- [x] `cast-requirements-roundtrip.collab.md` created, lints clean (exit 0), registered in `_registry.md`.
- [x] New spec **references** the render + delegation specs by heading; no duplication.
- [x] FR-007 guard extended: writer is the only mutator; byte-identity proven; no whole-file overwrite path (structural test).
- [x] Name reconciliation pass complete; landed names adopted everywhere.

## Notes / hand-offs

- **Default-suite SC-006:** the e2e is deterministic (no live subagent), so it runs in CI as the
  binary gate rather than as an excluded `eval_` test. The live-subagent orchestration
  (`cast-requirements-writeback` / `cast-comment-reanchor`) is unit-proven in sp4; SC-006 proves the
  mechanism closes the loop.
- **Two outbox rows per auto-applied addition** (sp2 intake FYI + sp4 apply FYI) is intentional; the
  read surface dedupes on `change_request_id`, which the crash-injection test asserts directly.
- **Deferred (out of scope, fenced in the spec):** real planner/executor emitters, co-editing/CRDT,
  auto-textual merge, PROV-O/JSON-LD export.
