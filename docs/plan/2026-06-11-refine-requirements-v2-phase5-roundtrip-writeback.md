# Refine Requirements v2: Phase 5 — Living Source of Truth: Round-Trip Write-Back

> Detailed execution plan (authored 2026-06-12 by `cast-detailed-plan`; filed under the
> `2026-06-11-refine-requirements-v2-phase*` series for sibling consistency). Covers **only**
> Phase 5 of `goals/refine-requirements-v2/plan.collab.md` and adopts all prior canon from
> `docs/plan/refine-requirements-v2-decisions-so-far.md`. The standalone high-level section is
> `goals/refine-requirements-v2/fanout/phase5_section.md`; the synthesized design is
> `exploration/playbooks/07-living-source-of-truth-roundtrip.ai.md` (impact 9/10).

## Overview

Phase 5 closes the loop: a downstream phase (exploration / planning / execution) that surfaces a
requirement-affecting change gets that change **written back into the canonical requirements file**
— with provenance (which phase/agent, derived from what), a user notification (what changed + from
where), inclusion in the version change summary, and **conflict surfacing instead of silent
overwrite**. v2 builds the *receiving* mechanism and proves it with a **simulated** downstream
emitter; wiring real planner/executor emitters is a later goal (US6/Constraints).

The headline insight from exploration: **this is an *assembly* of primitives Phases 1 and 4 already
produce, not a greenfield subsystem.** Write-back is modeled as **"propose + notify + gate, never
auto-sync"** — a downstream phase does not edit a requirement; it `POST`s a first-class
`change_request` carrying *where it came from* (`origin_*`) and *what version it assumed*
(`base_version`) to a DB the **server owns**, and a single **`cast-requirements-writeback` agent**
(the sole file-writer, mirroring `cast-update-spec`) applies accepted changes surgically to the
`.collab.md`. The load-bearing correctness claim: **silent two-way sync of a source-of-truth
document is *worse* than drift — it is untraceable overwrite of human intent** (US7 Scenario 4).
Truth must be *governed*, not eventually-consistent.

**Reconciliation with what landed (critical).** The Step-7 playbook was written assuming a
DB-canonical store with stable per-element surrogates (`spec_elements.surrogate`). The **landed**
Phase 1 design is the opposite — **files-canonical + thin spine, no per-element IDs**. This plan
therefore targets changes by **`quoted_text` + `section_hint`** (the same shape as
`requirement_comments`), resolved at apply-time by Phase 4's **`cast-comment-reanchor`** subagent,
with conflict detection via Phase 1's **`content_hash()`** over the located region at the base
version vs HEAD. Wherever the playbook says `surrogate`, read `quoted_text + section_hint`.

## Operating Mode

**HOLD SCOPE** — with an explicit, quoted deferral fence. The requirements bulletproof the
*receiving* path ("conflicting changes shall be **surfaced**, not silently overwritten" — FR-020;
SC-006 demands a full end-to-end trace) while ruthlessly fencing off everything beyond it: "v2
builds the *receiving* mechanism and proves it with a *simulated* downstream emitter (real
planner/executor emitters are a later goal)"; "**No CRDT/OT** (co-editing is out of scope)";
PROV-O/JSON-LD export "deferred". So: maximum rigor on intake → conflict → apply → notify; hard
deferral of emitters, co-editing, and provenance serialization ceremony. No silent drift between
those two postures.

## Depends On (from prior phases)

| Prior deliverable | Where (landed/planned) | How Phase 5 consumes it |
|---|---|---|
| `requirement_versions` (`goal_slug, version, content, content_hash, status current/archived`, `UNIQUE(goal_slug, version)`) | Phase 1 schema (landed) | `base_version` references a row's `version`; new versions appended on apply |
| `requirement_comments` (`quoted_text, section_hint, body, state, author, author_kind`, **no anchor column**) | Phase 1 schema (landed) | Shape template for `change_requests.target_quote/section_hint`; `author_kind` is the only human/agent distinction (FR-013) |
| `comment_events` append-only trail | Phase 1 schema (landed) | Shape template for `change_request_events` |
| `content_hash(text)` | Phase 1 `requirements_render/hashing.py` (landed) | Conflict predicate; never reimplemented |
| `requirement_version_service.create_snapshot / get_current / get_version / list_versions` | Phase 1 `services/requirement_version_service.py` (landed) | `create_next()` (Phase 4) wraps it; the writer bumps the version through it |
| `ParsedRequirements` / `Block{kind, level, body, heading, ref(in-memory), line_start, line_end}` | Phase 1 `requirements_render/blocks.py` (landed) | Diff input; quote→region location works over `Block` spans |
| Service DB pattern: flat functions, `db_path: Path \| None = None` + `get_connection(db_path)` | Phase 1 canon (landed) | `change_request_service.py` inherits this exact shape |
| `block_diff` deterministic change-summary engine (`{added, removed, modified}` set arithmetic) | Phase 4 plan (planned) `[PENDING Phase 4]` | Change summary reused **verbatim** + one provenance-badge column |
| `comment_service` + `create_next()` (comment-aware version gate) | Phase 4 plan (planned) `[PENDING Phase 4]` | Version bump on apply; "open items mark unconverged" precedent |
| `cast-comment-reanchor` subagent (quote → region, orphaning always surfaced) | Phase 4 plan (planned) `[PENDING Phase 4]` | The **only** locator the writer/conflict predicate use — Phase 5 builds no new anchoring |
| Same-door HTTP pattern (`HX-Request` content negotiation; one POST for human + agent) | Phase 4 plan + `routes/api_agents.py:list_runs` precedent | `POST /api/goals/{slug}/change-requests` mirrors it |
| `needs_attention` / `human_action_needed` rail + HTMX badge (`_finalize_run`) | landed (cast-server) + Phase 4 structured-payload extension `[PENDING Phase 4]` | Phase 5 extends the **same** surface — no second notification system |
| `output.json` contract-v2 (`artifacts[]`, "parents ignore unknown fields") | landed; `docs/specs/cast-output-json-contract.collab.md` | `requirements_writeback` rides as an additive artifact type |
| `tests/fixtures/synthetic_child.py` | landed (exists) | Emits the simulated downstream write-back for SC-006 |
| `orchestration_service.update_manifest_status()` surgical edit-by-key | landed (`services/orchestration_service.py`) | The **template** for surgical in-place file edit (NOT `api_artifacts.save_artifact`) |

**Sequencing note.** Phase 5 has a **hard dependency on Phase 4** (diff engine, `create_next`,
`cast-comment-reanchor`, structured `needs_attention`). Phase 4's detailed plan is complete but
**not yet executed**. Phase 5 execution is gated on Phase 4 landing. Where this plan binds a
specific Phase 4 interface, it is marked `[PENDING Phase 4]`; if names drift on landing, **adopt the
landed names — do not fork the vocabulary** (decisions-so-far standing rule).

---

## Sub-phase 1: Proposal Spine — change-request schema, event trail, outbox + payload model

**Outcome:** Four tables (`change_requests`, `change_request_events`, `notifications_outbox`) exist
on a fresh DB **and** migrate onto a pre-Phase-5 DB; a downstream agent can emit a validated
`requirements_writeback` artifact in its `output.json` and it round-trips through the pydantic model
without breaking any existing parent. Nothing applies anything yet — this is the substrate.

**Dependencies:** None within Phase 5 (consumes only landed Phase 1 schema). Build first.

**Estimated effort:** 0.5 session

**Verification:**
- `uv run pytest cast-server/tests/test_schema_migration.py` green — extend it with existence
  assertions for the three new tables + their FKs/indexes (mirror Phase 1 sp2b's pattern).
- A new `test_change_request_model.py`: `RequirementsWriteback` validates a good payload, rejects a
  bad `kind`/missing `base_version`; an `AgentOutput.artifacts[]` carrying type
  `requirements_writeback` parses and the unknown type is ignored by an old parser fixture.

Key activities:
- Add the three tables to the **canonical** `cast-server/cast_server/db/schema.sql` **and** mirror
  byte-identical `CREATE TABLE IF NOT EXISTS` in `_run_migrations()` in `db/connection.py` (Phase 1
  canon: edit both; the root `db/schema.sql` is legacy — do **not** touch it). Columns per the
  playbook Step 1 SQL, **with the thin-spine substitution**: replace
  `target_surrogate REFERENCES spec_elements(surrogate)` with `target_quote TEXT` + `section_hint
  TEXT` (NULL `target_quote` ⇒ pure addition, no target). `base_version INTEGER` references the
  `requirement_versions.version` the change assumed. Provenance as denormalized W3C-PROV columns
  (`origin_phase`, `origin_activity_id`, `origin_artifact_path`, `author`, `author_type`).
- `change_request_events` = append-only audit (generalize `comment_events`):
  `proposed|accepted|rejected|conflicted|applied|superseded`.
- `notifications_outbox`: `change_request_id`, JSON `payload`, `status pending|delivered`, timestamps.
- Define `RequirementsWriteback` (pydantic v2) in `cast_server/schemas/` and register
  `requirements_writeback` as an `artifacts[].type` value. Keep it additive — the contract already
  says parents MUST ignore unknown fields.
- → Delegate: `/cast-pytest-best-practices` over the migration + model tests. Review for the
  legacy-DB migration path (ALTER/CREATE idempotency) coverage.

**Design review:**
- ⚠️ **Thin-spine reconciliation (must-do):** the playbook's `spec_elements(surrogate)` FK does not
  exist. `target_quote + section_hint` is the landed locator shape. Flag in the schema comment block
  so a future reader doesn't "restore" a surrogate FK.
- Naming: `change_requests` / `change_request_events` follow the `requirement_versions` /
  `comment_events` house plural + `_events` convention ✓.
- Architecture: tables-absent-from-schema also mirrored in `_run_migrations()` per Phase 1 — pin
  this with the existence test so the canonical/migration pair can't drift.
- Security: `author_type` is a CHECK-constrained enum (`human|agent`); it is **data**, never a code
  branch (FR-013) — but see sp2 for spoof-prevention on the write path.

## Sub-phase 2: Same-Door Intake — POST change-requests + graduated-trust router

**Outcome:** A single `POST /api/goals/{slug}/change-requests` accepts an identical body from a human
"suggest edit" and an agent write-back (`author_type` is the only difference, and it is data); the
handler writes a `change_request` + a `change_request_events('proposed')` row + (on auto-apply path)
the outbox row **in one transaction**, and routes by blast radius into
`applied | proposed | conflicted`. No file is touched yet (sp4 does the apply).

**Dependencies:** Sub-phase 1.

**Estimated effort:** 1 session

**Verification:**
- `test_change_request_intake.py`: a pure-addition POST → status `applied` (fast-track, FYI queued);
  a modification of existing content → status `proposed` (gated); a malformed/oversized body → 422;
  the human-shaped and agent-shaped bodies hit the identical handler and differ only by `author_type`.
- Transactionality: simulate a failure after the `change_request` insert and assert **no** orphaned
  `change_request_events` / outbox row (all-or-nothing).

Key activities:
- One handler in `cast_server/routes/` (a new `routes/change_requests.py` or extend the goals router,
  matching the landed `POST /api/goals/{slug}/route` placement from Phase 3b). `HX-Request` content
  negotiation per `routes/api_agents.py:list_runs` precedent: HTML fragment for the UI, JSON for
  agents — same data.
- `change_request_service.py` (flat functions, `db_path` injectable, house DB pattern): `create(...)`
  writes the row + event (+ outbox when auto-applied) atomically.
- **Graduated-trust router** branches by *blast radius, not author*: pure addition (`target_quote`
  NULL) → fast-track `applied` + FYI; modification/annotation of existing content → `proposed` +
  `AskUserQuestion` gate (the same gate `cast-update-spec` uses); divergence from `base_version` →
  `conflicted` (sp3a decides this; intake just records the verdict). Policy lives in **config**
  (recommend a single `WRITEBACK_GATE_POLICY="gate-except-additions"` flag for v2) so it can loosen
  later without a code change.
- → Delegate: `/cast-update-spec` is the model for the human gate UX; do not reinvent the
  AskUserQuestion flow.

**Design review:**
- ⚠️ **FR-013 forcing function:** the UI must have **no privileged write path the agent lacks**.
  Verify there is exactly one intake handler; a second "internal" write path silently violates FR-013.
- Security: `author_type` and `author` for **human** submissions must be derived from the request
  context, **not** trusted from the client body (an agent legitimately self-declares `agent`; a
  browser client must not be able to spoof `human`/another author). Add request-origin validation;
  validate `slug` exists; cap `proposed_body` length.
- Error & rescue: the three-way write (row+event+outbox) is a multi-statement txn — wrap in a single
  `BEGIN IMMEDIATE` (Phase 1 version-service precedent) so a mid-write crash leaves nothing.

## Sub-phase 3a: Conflict Predicate — three-way content-hash check against base version

**Outcome:** A pure, total `detect_conflict(...)` returns `clean | conflicted | orphaned` by
comparing the target region's `content_hash` at `base_version` vs HEAD — located by quote, never by a
stable ID; a region a human touched since `base_version` returns `conflicted` (→ surface, never
overwrite); a quote that no longer locates returns `orphaned` (→ surface). Zero silent overwrites by
construction.

**Dependencies:** Sub-phase 1. (Consumes Phase 1 `content_hash` + `[PENDING Phase 4]`
`cast-comment-reanchor`.) **Parallel with sub-phase 3b** (disjoint files).

**Estimated effort:** 1 session

**Verification:**
- `test_conflict_predicate.py` over the frozen fixture
  (`tests/fixtures/refine_requirements_v2/refined_requirements.collab.md`) + checked-in edited
  variants: unchanged-since-base → `clean`; human edited the region since base → `conflicted`;
  quote deleted since base → `orphaned`. Pure function: no DB, no LLM, no I/O in the predicate itself
  (the quote→region resolution is injected).
- Property: `detect_conflict` never returns `clean` when the HEAD region hash ≠ base region hash.

Key activities:
- `conflict.py` in `requirements_render` (or `change_request_service`): `region_hash(version,
  target_quote, section_hint)` resolves the quote→region within that version's stored
  `requirement_versions.content` (reusing the `cast-comment-reanchor` locator skill `[PENDING Phase
  4]` — do **not** build a second locator), then `content_hash(region)`. `detect_conflict` =
  `clean` iff `region_hash(base) == region_hash(HEAD)`, else `conflicted`; unlocatable ⇒ `orphaned`.
- Conflict resolution **surface** (rendered, not auto-merged): a 3-way choice — *accept-incoming /
  keep-current / merge-with-free-edit* (Jama "suspect until cleared" semantics). **No
  auto-textual-merge in v2** (element granularity keeps conflicts small). Every transition →
  `change_request_events`.

**Design review:**
- ⚠️ **Thin-spine fragility:** with no stable IDs, conflict detection *is* quote-location. Reuse the
  exact `cast-comment-reanchor` subagent and its orphan-surfacing — an orphan must surface, never
  silently no-op. Flag binding as `[PENDING Phase 4]`.
- Architecture: keep the predicate pure/total (mirrors Phase 3b's `resolve` discipline) so it is
  unit-testable without a DB or model.

## Sub-phase 3b: Notification Outbox + Unified `needs_attention` Surface

**Outcome:** The change and its alert commit in the **same transaction** (no dual-write drift); a
polling relay drains `notifications_outbox WHERE status='pending'` at-least-once and marks
`delivered`; the alert reaches the user through the **existing** `needs_attention` rail carrying a
**structured** payload ("requirements updated from planning: +FR-021"), plus a minimal
W3C-LDN-aligned `GET/POST /api/goals/{slug}/inbox` JSON endpoint so watching agents consume the same
resource. One surface, shared with Phase 4 comments — not two.

**Dependencies:** Sub-phase 1. (Extends `[PENDING Phase 4]` structured `needs_attention`.) **Parallel
with sub-phase 3a.**

**Estimated effort:** 1 session

**Verification:**
- `test_outbox_relay.py`: insert a change+outbox in one txn; run the relay → `delivered`; inject a
  **crash between commit and relay** and re-run → the alert still delivers (at-least-once) with **0
  lost and 0 duplicate** after UI dedupe on `change_request_id` (the SC-006 crash assertion, unit-level).
- `/inbox` returns the same payload shape the HTMX badge consumes.

Key activities:
- FastAPI lifespan-managed background task (the dispatcher/monitor-loop precedent) polls + delivers +
  marks delivered. CDC/Debezium is over-engineering at SQLite scale — polling is the right weight.
- Extend `_finalize_run`'s `needs_attention`/`human_action_needed` with a **structured** descriptor
  (today it carries a bare boolean + prose) so the badge can render *what changed + from where*
  (FR-019 in one shape). **Reuse** the rail — do not stand up a parallel notifier.
- `GET/POST /api/goals/{slug}/inbox` (LDN-aligned), JSON; the agent companion to the human badge.

**Design review:**
- ⚠️ **Unification (must-do):** Phase 4 owns the "unified notification surface (resolved at plan
  review)". If Phase 4 lands the structured `needs_attention` payload, **extend** it; if Phase 4
  ships only the boolean, this sub-phase absorbs the structuring. Mark `[PENDING Phase 4]` and confirm
  ownership (Open Question 2).
- Error & rescue: outbox is the dual-write fix — assert the same-txn insert in code review; UI dedupe
  key is `change_request_id`.

## Sub-phase 4: The Sole File Writer — `cast-requirements-writeback` agent (surgical apply)

**Outcome:** A single subagent applies an accepted/auto-applied `change_request` to the canonical
`.collab.md` as a **targeted addition/annotation that leaves the rest of the file byte-identical**,
appends provenance, bumps the version via `create_next()`, and emits the change summary with a
provenance badge. The server **never** writes the file; this agent is the only mutator. The
silent-drift bug US7 exists to kill is structurally impossible (no whole-file overwrite path).

**Dependencies:** Sub-phase 2 (an `accepted`/`applied` change to act on), Sub-phase 3a (conflict
verdict gates the apply), Sub-phase 3b (notification on apply). Critical path. **Heaviest sub-phase.**

**Estimated effort:** 1.5 sessions

**Verification:**
- `test_writeback_apply.py`: an accepted addition → the FR appears at the file tail, every other byte
  identical (diff shows exactly the added region); a `conflicted` change → **refused**, surfaced, file
  untouched; provenance row + `applied` event + version bump + change-summary delta with the
  provenance badge all present.
- FR-007 guard (extended in sp5): the writer is the *only* code path that may mutate the `.collab.md`;
  `rerender`/render code still never mutates it.

Key activities:
- New `agents/cast-requirements-writeback/` — subagent shape cloned from the Phase 2/3a/4 precedent
  (`model: sonnet, dispatch_mode: subagent, interactive: false, context_mode: lightweight`); mirrors
  `cast-update-spec`'s "sole write path" posture. Run `bin/generate-skills` after authoring.
- Apply logic: resolve `target_quote` → region via `cast-comment-reanchor` `[PENDING Phase 4]`; run
  `detect_conflict` (sp3a); if `clean`/addition → apply surgically. **Lift
  `orchestration_service.update_manifest_status()` as the exact surgical-edit-by-key template** — it
  already rewrites one keyed region and leaves the rest of a markdown doc untouched. **Never** build
  on `api_artifacts.save_artifact`'s `write_text` whole-file overwrite (the code-G4 silent-drift bug).
- Append provenance; bump version via `create_next()` `[PENDING Phase 4]`; emit the change summary by
  reusing Phase 4's `block_diff` `[PENDING Phase 4]` + one provenance-badge column (`+FR-021 — added
  by planning · agent cast-high-level-planner · derived from plan.collab.md`); write the outbox row
  in the apply txn (hand to sp3b relay).

**Design review:**
- ⚠️ **Spec consistency — delegation contract:** `cast-delegation-contract.collab.md` says the server
  never writes artifact files; this agent is the carve-out (server owns the proposal DB, the agent
  owns the file). No conflict, but sp5 must restate this in the new spec.
- ⚠️ **Security (path scope):** the writeback agent must be path-scoped to the goal's
  `refined_requirements.collab.md` — refuse any target outside the goal dir (out-of-tree edit refused,
  never crash). Mirror the subphase-runner's path-traversal posture.
- Architecture: one writer = one place for provenance + conflict + version bump. Do not let sp2's
  intake or any route write the file.

## Sub-phase 5: End-to-End Proof (SC-006) + Spec Lockstep + FR-007 Guard

**Outcome:** A simulated downstream change traces the **entire** chain green, the binary SC-006 gate
passes, the round-trip behavior is documented in a new canonical spec, and the FR-007 byte-identity
guard is extended to prove the writer is the only mutator. Phase 5 is done and provable without real
downstream emitters.

**Dependencies:** Sub-phase 4.

**Estimated effort:** 1 session

**Verification:**
- `test_roundtrip_e2e.py` (SC-006): `synthetic_child.py` emits a valid `requirements_writeback` →
  `change_request` row → conflict verdict → surgical file apply → version bump → change summary with
  provenance badge → outbox row → notification surfaced. Assert **0** modifications to existing
  content applied without a passed gate or surfaced conflict; **0** lost/duplicate notifications after
  an injected crash between commit and relay. Mark slow/eval-style if it drives a live subagent
  (mirror `eval_*` exclusion convention).
- `bin/cast-spec-checker` exit 0 on the new spec; FR-007 guard suite green.

Key activities:
- → Delegate: `/cast-update-spec` (create mode) for **`docs/specs/cast-requirements-roundtrip.collab.md`**
  — the change-request lifecycle, same-door API, graduated-trust policy, conflict semantics, the
  sole-writer carve-out, the notification surface; register it in `docs/specs/_registry.md`. (Authored
  in create-mode shape if the interactive approval gate can't run headless — Phase 3a sp5b precedent.)
- Extend `cast-server/tests/test_fr007_readonly_guard.py` with a post-write-back byte-identity test:
  the writer changes exactly the target region; no other path mutates the `.collab.md`.
- → Delegate: `/cast-pytest-best-practices` over the e2e + guard suites. Review for the crash-injection
  assertion quality (0 lost / 0 dup).
- Final reconciliation pass: if Phase 4 landed with drifted names for `block_diff` / `create_next` /
  `cast-comment-reanchor` / `needs_attention`, adopt the landed names across sp3a/sp3b/sp4.

**Design review:**
- ⚠️ **Spec lockstep:** the new spec is the contract Phase-5-and-later cite; it must reference (not
  duplicate) `cast-requirements-render.collab.md` (the change summary + conflict surface ride that
  page) and `cast-delegation-contract.collab.md` (the sole-writer carve-out).
- Security: SC-006 must assert the negative — **no** existing content mutated without a passed
  gate/surfaced conflict — not just the happy path.

---

## Build Order

```
sp1 Proposal Spine ──► sp2 Same-Door Intake ──┬──────────────► sp4 Sole File Writer ──► sp5 E2E + Spec + Guard
                                              │                      ▲   ▲
              sp3a Conflict Predicate ────────┼──────────────────────┘   │
              (parallel)                      │                          │
              sp3b Notification Outbox ───────┴──────────────────────────┘
              (parallel, disjoint files)
```

**Critical path:** sp1 → sp2 → sp4 → sp5. sp3a and sp3b run in parallel after sp1 and both feed sp4
(conflict verdict + notification). Total ≈ 3–4 sessions (matches the high-level estimate).

**Hard external gate:** all of Phase 5 is blocked on **Phase 4 landing** (diff engine, `create_next`,
`cast-comment-reanchor`, structured `needs_attention`). Do not begin sp4 until those interfaces exist;
sp1/sp2/sp3a/sp3b can be built against Phase 1 primitives + stubs, but their `[PENDING Phase 4]`
bindings must be reconciled before sp4.

## Design Review Flags

| Sub-phase | Flag | Action |
|---|---|---|
| sp1 | Playbook's `spec_elements(surrogate)` FK doesn't exist (thin spine) | Use `target_quote + section_hint`; note in schema comment |
| sp1 | Canonical `schema.sql` ↔ `_run_migrations()` can drift | Pin with table-existence migration test (Phase 1 sp2b pattern) |
| sp2 | FR-013: a 2nd internal write path silently violates same-door | Assert exactly one intake handler in review |
| sp2 | `author_type`/`author` spoofable from client body | Derive human identity from request context, not client JSON |
| sp3a | No stable IDs → conflict detection is quote-location | Reuse `cast-comment-reanchor`; orphan must surface `[PENDING Phase 4]` |
| sp3b | Two notification surfaces would violate "unified" decision | Extend `needs_attention`; confirm Phase 4 ownership (OQ2) |
| sp4 | Server-writes-file would violate delegation contract | Agent is sole writer; restate carve-out in sp5 spec |
| sp4 | Whole-file overwrite reintroduces US7 silent-drift bug | Lift `update_manifest_status` template; never `save_artifact` |
| sp4 | Writeback path outside goal dir = traversal risk | Path-scope the writer to the goal's `.collab.md` |
| sp5 | Spec must not duplicate render/delegation specs | Reference by heading; new spec lints clean |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Phase 4 not yet executed** — Phase 5 binds 4 of its interfaces | High | Execution gated on Phase 4 landing; `[PENDING Phase 4]` markers; adopt landed names on drift (standing rule). sp1/2/3 buildable against Phase 1 + stubs |
| Thin-spine quote-location fragility for conflict detection | High | Reuse exact `cast-comment-reanchor` + orphan-surfacing; element granularity keeps conflicts small; **never silent** |
| Surgical apply corrupts unrelated bytes (the bug US7 kills) | High | Lift `update_manifest_status` template; FR-007 byte-identity guard (sp5); ban `save_artifact` overwrite |
| Outbox crash window (dual-write) | Med | Same-txn change+outbox insert; at-least-once relay; UI dedupe on `change_request_id`; sp5 injects the crash |
| Gate fatigue vs. data-loss lane | Med | Gate-everything-except-pure-additions, config-driven (loosen later without code change) |

## Open Questions

**Resolved via `/cast-interactive-questions` (owner, 2026-06-12) — none blocking for execution:**

1. **Endpoint namespace → `/api/goals/{slug}/change-requests`.** Matches the landed `goals`
   slug namespace (Phase 3a `GET /goals/{slug}/render`, Phase 3b `POST /api/goals/{slug}/route`);
   the playbook's `/api/specs/...` is dropped. Applies to sp2 + the new spec.
3. **Graduated-trust granularity → global `WRITEBACK_GATE_POLICY` config flag.** Per-element
   (Jama-style) config is deferred as forward-compat, not a v2 need; the flag can be loosened
   later without a code change.
4. **`base_version` reference shape → integer `requirement_versions.version`.** Matches the
   landed `UNIQUE(goal_slug, version)`; no synthetic version id. Applies to sp1 schema +
   conflict detection.

**Resolved from Phase 4 landed code (orchestrator, 2026-06-12):**

2. **Notification surface → Phase 4 shipped a STRUCTURED surface; Phase 5 EXTENDS it (sp3b does
   NOT structure-from-boolean).** Phase 4 landed `comment_service.open_comment_count(goal_slug)
   -> int` and `GET /goals/{slug}/versions` returning `{versions, convergence, open_comment_count}`
   (`convergence = "unconverged" if open_comment_count > 0 else "converged"`), plus the Goal-Card
   comment-count slot filled client-side. sp3b adds the round-trip/provenance notification onto
   this existing surface — it does not build the structuring from scratch. (The integer
   `agent_runs.needs_attention` flag is a separate agent-run signal, unrelated to this surface.)

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|---|---|---|
| `cast-delegation-contract.collab.md` | Server-never-writes-artifacts; subagent carve-out | None — server writes DB rows only; `cast-requirements-writeback` is the file-apply carve-out (restated in the new spec) |
| `cast-output-json-contract.collab.md` | Contract-v2 `artifacts[]`; "parents ignore unknown fields" | None — `requirements_writeback` is an additive artifact type |
| `cast-requirements-render.collab.md` (Phase 3a/4) | Route semantics, DOM contract, change-summary surface | n/a — Phase 5's change summary + conflict surface ride this page; the new roundtrip spec references it |
| *(create)* `cast-requirements-roundtrip.collab.md` | New — change-request lifecycle, same-door API, conflict + gate, sole-writer, notification | Created in sp5 via `/cast-update-spec`; registered in `_registry.md` |
