---
feature: cast-requirements-roundtrip
module: cast-server
linked_files:
  - cast-server/cast_server/routes/change_requests.py
  - cast-server/cast_server/services/change_request_service.py
  - cast-server/cast_server/services/notification_service.py
  - cast-server/cast_server/requirements_render/conflict.py
  - cast-server/cast_server/models/requirements_writeback.py
  - cast-server/cast_server/config.py
  - cast-server/cast_server/db/schema.sql
  - agents/cast-requirements-writeback/cast-requirements-writeback.md
  - agents/cast-requirements-writeback/config.yaml
  - cast-server/tests/test_change_request_intake.py
  - cast-server/tests/test_writeback_apply.py
  - cast-server/tests/test_roundtrip_e2e.py
  - cast-server/tests/test_fr007_readonly_guard.py
  - cast-server/tests/fixtures/synthetic_child.py
  - docs/plan/2026-06-11-refine-requirements-v2-phase5-roundtrip-writeback.md
  # v2 (Phase 5d) — the first REAL downstream emitter (render gap-fill); intake/gate/apply unchanged
  - cast-server/cast_server/services/render_job_service.py
  - cast-server/tests/test_gap_reconciliation.py
last_verified: "2026-06-12"
---

# Cast Requirements Round-Trip Write-Back — Spec

> **Spec maturity:** draft
> **Version:** 2
> **Updated:** 2026-06-12 — v2 (Phase 5d): the **first real downstream emitter** lands. Render
> gap-fill (`render_job_service.emit_change_requests`) proposes a genuinely-missing detail as a
> `kind="addition"` change-request through this contract's intake — **emitter-side only**: the
> same-door intake, the graduated-trust gate, the conflict predicate, the sole-writer apply, the
> outbox + relay are all consumed **byte-unchanged** (every roundtrip test stays green). The
> "real emitters deferred" Out-of-Scope fence is narrowed to record this one emitter.
> **Status:** Draft
> **Provenance:** auto-persisted — non-interactive run (Phase 5 sp5/sp5d; `/cast-update-spec`
> create/update-mode shape authored directly under standing session approval because the interactive
> approval gate cannot run headless, mirroring the Phase 3a sp5b precedent). `bin/cast-spec-checker`
> exits 0 on this file.

## Intent

Refine Requirements v2 closes the loop: a downstream phase (exploration / planning / execution) that
surfaces a requirement-affecting change must get that change **written back into the canonical
requirements file** — with provenance (which phase/agent, derived from what), a user notification
(what changed + from where), inclusion in the version change summary, and **conflict surfacing
instead of silent overwrite**.

The load-bearing correctness claim (the goal's US7 Scenario 4): **silent two-way sync of a
source-of-truth document is *worse* than drift — it is untraceable overwrite of human intent.** Truth
must be *governed*, not eventually-consistent. The model is therefore **"propose + notify + gate,
never auto-sync."** A downstream phase does not edit a requirement; it `POST`s a first-class
`change_request` carrying *where it came from* (`origin_*`) and *what version it assumed*
(`base_version`) to a DB the **server owns**. A single **`cast-requirements-writeback`** agent — the
sole file-writer, mirroring `cast-update-spec` — applies accepted changes **surgically** to the
`.collab.md`. v2 builds the *receiving* mechanism and proves it with a **simulated** downstream
emitter (`tests/fixtures/synthetic_child.py`); wiring real planner/executor emitters is hard-deferred
to a later goal. **No CRDT/OT** (co-editing is out of scope); PROV-O/JSON-LD export is deferred.

This spec is the **contract Phase-5-and-later goals cite.** It **references** two adjacent specs and
does not duplicate them:

- **`cast-requirements-render.collab.md`** owns the change-summary engine (`block_diff` /
  `summarize`), the `requirement_version_service.create_next` version gate, the
  `{convergence, open_comment_count}` structured surface, and the `cast-comment-reanchor` bare-JSON
  re-anchor carve-out. The round-trip change summary, provenance badge, and notification **ride that
  page's surfaces** — see its **Functional Requirements** and **Success Criteria**. This spec records
  only how a write-back *produces* a new version and *extends* that notification surface.
- **`cast-delegation-contract.collab.md`** owns the server-never-writes-artifacts rule and the
  subagent carve-out. `cast-requirements-writeback` is the explicit **file-apply carve-out**: the
  server owns the proposal DB; the agent owns the file. See its **subagent carve-out** heading — this
  spec restates the boundary, it does not fork it.

Symbol, route, and status-value names below are the **naming contract** — later goals adopt them
verbatim.

## User Stories

### US1 — Same-door change-request intake (human and agent through one endpoint) (Priority: P1)

**As a** downstream phase or a human reviewer, **I want to** propose a requirement change through a
single endpoint, **so that** there is exactly one governed write path and no privileged door the
other party lacks.

**Independent test:** A plain-JSON `POST /api/goals/{slug}/change-requests` (agent lane) and an
`HX-Request` form POST (human lane) hit the identical handler and persist identical `change_requests`
columns except the server-derived `author` / `author_type`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN an agent POSTs a valid write-back proposal as JSON, THE SYSTEM SHALL record one
  `change_requests` row whose `author_type` is `agent` and whose `author` is the agent's self-declared
  name, and return `201` with the row.
- **Scenario 2:** WHEN a browser POSTs the same proposal with an `HX-Request` header, IF the body
  claims `author_type="human"` with a forged `author`, THE SYSTEM SHALL ignore the posted identity
  and stamp its own server-derived human identity instead.
- **Scenario 3:** WHEN the slug does not exist, THE SYSTEM SHALL return `404` and persist nothing.

### US2 — Graduated-trust gate by blast radius, not by author (Priority: P1)

**As a** maintainer of a source-of-truth document, **I want to** auto-apply only the lowest-blast
changes and gate everything that touches existing content, **so that** convenience never costs
governance.

**Independent test:** With `WRITEBACK_GATE_POLICY="gate-except-additions"`, a pure addition intakes
`applied` and a modification of existing content intakes `proposed`, decided by blast radius and
identically for a human and an agent.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a pure addition (no `target_quote`) is intaken under the default policy, THE
  SYSTEM SHALL set status `applied` and queue one `pending` notification.
- **Scenario 2:** WHEN a modification or annotation of existing content is intaken, THE SYSTEM SHALL
  set status `proposed` (gated) and queue NO notification.
- **Scenario 3:** WHEN the policy is `gate-all`, THE SYSTEM SHALL set every proposal `proposed`
  regardless of blast radius; WHEN it is `gate-none`, THE SYSTEM SHALL set every proposal `applied`.

### US3 — Conflict surfaced, never silently overwritten (Priority: P1)

**As a** reviewer whose intent is canonical, **I want** a change that assumed an older version of a
region I have since edited to be surfaced, not applied, **so that** my edit is never untraceably
overwritten.

**Independent test:** A modification whose `target_quote` region changed on disk since its
`base_version` yields verdict `conflicted`, the file is left byte-identical, and a 3-way resolution
surface is offered with no auto-merge.

**Acceptance scenarios:**

- **Scenario 1:** WHEN the located target region's content hash at `base_version` differs from HEAD,
  THE SYSTEM SHALL return `conflicted`, leave the file untouched, and append a `conflicted` audit row.
- **Scenario 2:** WHEN the target quote no longer locates in HEAD, THE SYSTEM SHALL return `orphaned`,
  leave the file untouched, and surface the orphan rather than silently no-op.
- **Scenario 3:** WHEN a verdict is `conflicted`, THE SYSTEM SHALL offer exactly the choices
  `accept-incoming`, `keep-current`, `merge-with-free-edit` and compute no textual merge itself.

### US4 — The write-back agent is the sole, surgical file-writer (Priority: P1)

**As a** holder of a byte-faithful canonical file, **I want** exactly one code path to ever mutate it,
applying only the target region, **so that** the silent-drift bug cannot recur by construction.

**Independent test:** Applying an accepted addition changes only the inserted line (every other byte
identical); no render / rerender / parse / snapshot path mutates the file; the apply module contains
no executable whole-file overwrite call.

**Acceptance scenarios:**

- **Scenario 1:** WHEN an accepted change is applied, THE SYSTEM SHALL splice only the located region,
  verify every non-target byte is unchanged before writing, and commit atomically (temp file +
  `os.replace`).
- **Scenario 2:** WHEN any other surface runs (HTML render, version snapshot, re-parse), THE SYSTEM
  SHALL leave the `.collab.md` byte-identical.
- **Scenario 3:** WHEN the resolved goal directory escapes the allowed root, THE SYSTEM SHALL refuse
  `out-of-tree`, write no file, and not crash.

### US5 — Round-trip notification with provenance, on the existing surface (Priority: P1)

**As a** human or a watching agent, **I want** to be told what changed and from where on the surface I
already read, exactly once, **so that** a write-back is observable without standing up a parallel
notifier.

**Independent test:** An applied change queues a transactional-outbox row in the same transaction as
the change; the relay drains it at-least-once; the round-trip descriptor surfaces the change exactly
once (deduped on `change_request_id`) on the extended `{convergence, open_comment_count}` surface.

**Acceptance scenarios:**

- **Scenario 1:** WHEN a change is applied, THE SYSTEM SHALL write its notification row in the SAME
  transaction as the apply, so no change commits without its alert and no alert without its change.
- **Scenario 2:** WHEN the relay drains the outbox after a crash mid-drain, THE SYSTEM SHALL deliver
  every pending row at-least-once and re-deliver nothing already delivered.
- **Scenario 3:** WHEN one change has more than one outbox row (an intake FYI and an apply FYI), THE
  SYSTEM SHALL surface it exactly once on the read descriptor.

### US6 — The whole round-trip closes the loop with zero silent drift (Priority: P1)

**As a** product owner relying on the requirements file as the living source of truth, **I want** an
end-to-end proof that a simulated downstream change traces the whole chain green while never mutating
existing content ungated, **so that** the governance guarantee is verified, not asserted.

**Independent test:** `tests/test_roundtrip_e2e.py` traces emit → intake → conflict → surgical apply →
version bump → change summary + provenance → outbox → notification, and asserts 0 ungated
modifications and 0 lost / 0 duplicate notifications after an injected crash. (Realizes the goal's
SC-006.)

**Acceptance scenarios:**

- **Scenario 1:** WHEN a simulated downstream addition runs the full chain, THE SYSTEM SHALL produce a
  bumped version, a change summary carrying a provenance badge, and one surfaced notification.
- **Scenario 2:** WHEN any existing content would change, THE SYSTEM SHALL apply it only after a passed
  gate or surface a conflict — never silently — so the count of ungated modifications is zero.
- **Scenario 3:** WHEN a crash is injected between the outbox commit and the relay, THE SYSTEM SHALL
  lose no notification and duplicate none at the read surface.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The same-door intake endpoint is `POST /api/goals/{goal_slug}/change-requests` (goals namespace), validating the slug first (unknown → `404`); response negotiates on `HX-Request` (HTML fragment for the browser, JSON `201` for agents) | Owner decision #1 — see Decisions |
| FR-002 | There is exactly ONE intake handler running ONE `change_request_service.create` call for both lanes; the human/agent distinction is the `author_type` column (`human` \| `agent`), data, never a code branch | Realizes the goal's same-door requirement; no second internal write path |
| FR-003 | Identity is server-authoritative: the human lane (`HX-Request`) stamps a server-derived identity and ignores the posted `author`/`author_type`; the agent lane forces `author_type="agent"` and uses the agent's self-declared `author`; a missing agent name → `422` | Anti-spoof seam in the route, not the service |
| FR-004 | A proposal references the version it assumed as an integer `base_version` equal to a `requirement_versions.version` (no synthetic version id) | Owner decision #2 — see Decisions |
| FR-005 | The trust lane is decided by `change_request_service.gate_status(kind, target_quote, policy)` under a single global `WRITEBACK_GATE_POLICY` flag (not per-element): the v2 default `gate-except-additions` applies additions and gates everything that modifies existing content; `gate-all` / `gate-none` are the other values | Owner decision #3 — see Decisions |
| FR-006 | A change-request moves through the status set `proposed` → `applied` \| `conflicted` \| `rejected` \| `superseded`; every transition appends exactly one append-only `change_request_events` row; a refusal is never a silent no-op | Lifecycle + audit trail |
| FR-007 | The conflict predicate `detect_conflict(base_content, head_content, target_quote, section_hint, *, locate)` is pure and total, returning `clean` \| `conflicted` \| `orphaned` by comparing the `content_hash` of the located region at base vs HEAD; a pure addition (no `target_quote`) is always `clean` | The region is found by quote, never a stable id (thin spine) |
| FR-008 | A `conflicted` verdict offers exactly the 3-way `ConflictSurface` choices `accept-incoming` \| `keep-current` \| `merge-with-free-edit`; v2 computes no auto-textual-merge; the change is held until a human picks one | Jama "suspect until cleared" semantics |
| FR-009 | The `cast-requirements-writeback` subagent (via the apply CLI) is the SOLE file-writer; it splices only the located region and verifies every non-target byte is unchanged before committing — the explicit `cast-delegation-contract` file-apply carve-out (server owns the proposal DB; agent owns the file) | References — does not duplicate — the delegation contract's subagent carve-out |
| FR-010 | There is no whole-file overwrite path: the apply module never executes `Path.write_text` / `save_artifact`; the only write is an atomic temp-file + `os.replace` of the verified in-memory splice | Structural guard against the US7 silent-drift bug |
| FR-011 | The apply writes its `applied` event and a `notifications_outbox` row in the SAME transaction as the file-apply status flip (transactional outbox); a lifespan relay drains `pending` rows to `delivered` at-least-once, surviving a mid-drain crash with nothing lost and nothing re-delivered | Fixes the dual-write trap |
| FR-012 | The round-trip notification EXTENDS the existing structured `{convergence, open_comment_count}` surface plus the Goal-Card slot with a round-trip / provenance descriptor; `recent_writebacks` is sourced from `delivered` outbox rows and dedupes on `change_request_id` so a change surfaces exactly once; it is NOT structured-from-boolean | Owner decision #4 — see Decisions; rides `cast-requirements-render.collab.md` |
| FR-013 | The change summary is the deterministic `summarize(diff_blocks(...))` set from `cast-requirements-render.collab.md` (imported, never forked), plus a one-line provenance badge — *what changed + from where* — built from the change-request's own `origin_*` / `author` columns | Provenance is data, never an author code branch |
| FR-014 | The apply path is scoped to the goal's directory; a resolved `goal_dir` that escapes the allowed root (default `GOALS_DIR`), or a missing requirements file, is refused (`out-of-tree` \| `orphaned`) with no file write and no crash | Path-scope security |
| FR-015 | A downstream emitter proposes via the additive `RequirementsWriteback` `output.json` artifact (`type == "requirements_writeback"`); a parent that does not understand the type ignores it for free (contract-v2 "parents ignore unknown fields") | The simulated emitter (`synthetic_child.py`) validates against this same model |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | Human and agent reach the proposal store through one door: a JSON (agent) and an `HX-Request` (human) intake produce the same `change_requests` row modulo id / `author` / `author_type`, and a browser cannot forge a human identity | `tests/test_change_request_intake.py` same-door + anti-spoof tests |
| SC-002 | Zero ungated modifications: existing content is never mutated without a passed gate or a surfaced conflict — a modification intakes `proposed` (file untouched, no FYI) and a conflicted apply is refused with the file byte-identical | `tests/test_roundtrip_e2e.py` negative assertions + `tests/test_writeback_apply.py` |
| SC-003 | Zero lost / zero duplicate notifications across an injected crash between the outbox commit and the relay; a change with two outbox rows surfaces exactly once | `tests/test_roundtrip_e2e.py` crash-injection test |
| SC-004 | The write-back agent is the only mutator and the apply is surgical: only the target region changes, no other path mutates the `.collab.md`, the apply module has no executable whole-file overwrite, and `bin/cast-spec-checker` stays green on the spliced source | `tests/test_fr007_readonly_guard.py` sole-mutator + no-overwrite tests |
| SC-005 | The full happy-path chain is green for a pure addition: intake → surgical apply → version bump → change summary with a provenance badge → outbox → de-duplicated notification | `tests/test_roundtrip_e2e.py` whole-chain test |
| SC-006 | The conflict predicate is pure and total and surfaces (never overwrites): every input maps to exactly one of `clean` / `conflicted` / `orphaned`, and a diverged region is held with a 3-way surface | `tests/test_conflict_predicate.py` + `tests/test_writeback_apply.py` conflicted/orphaned refusal tests |

## Decisions

These four owner-resolved decisions are binding and stated verbatim (folded from the Phase 5 plan's
Open Questions; not re-litigated here):

1. **Endpoint namespace → `POST /api/goals/{slug}/change-requests`** (goals namespace, **NOT**
   `/api/specs/...`). Matches landed `POST /api/goals/{slug}/route` (Phase 3b).
2. **`base_version` reference shape → integer `requirement_versions.version`** (matches landed
   `UNIQUE(goal_slug, version)`; no synthetic version id).
3. **Graduated-trust gate → a single global `WRITEBACK_GATE_POLICY` config flag** (NOT per-element).
   Recommended v2 value: `"gate-except-additions"`. Can loosen later without a code change.
4. **Notification → EXTEND the existing structured `{convergence, open_comment_count}` surface +
   Goal-Card slot.** sp3b adds round-trip/provenance notifications onto it; it does **NOT**
   structure-from-boolean.

## Out of Scope

- **Real downstream emitters — narrowed (v2, Phase 5d).** v1 proved the receiving path with the
  simulated `synthetic_child.py`. Phase 5d wires the **first real emitter**: render gap-fill
  (`render_job_service.emit_change_requests`) proposes a missing detail as a `kind="addition"` CR
  (`author_type="agent"`, `origin_phase="render-gapfill"`) through this contract's `create(...)` — the
  governed write path consumed **byte-unchanged** (no intake/gate/apply/outbox/relay edit; verified by
  every roundtrip test staying green). Wiring the **remaining** real planner/executor emitters is still
  a later goal — this fence records the one realized emitter, not a general-emitter generalization.
- **Co-editing / CRDT / OT.** Truth is governed (propose + gate), not eventually-consistent.
- **Auto-textual merge.** A `conflicted` verdict surfaces a 3-way human choice; the system computes no
  merge text.
- **PROV-O / JSON-LD provenance serialization.** The denormalized `origin_*` columns + the
  one-line badge are the v2 provenance surface; formal export is deferred.

## Open Questions

- None blocking. The endpoint namespace, `base_version` shape, gate policy, and notification surface
  are the four owner-resolved decisions above; the conflict semantics, sole-writer carve-out, and
  outbox relay are landed and tested. The deferred items are recorded under Out of Scope as
  intentional fences, not unresolved questions.
