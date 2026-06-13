# Execution Manifest: refine-req-v2-phase5 (Living Source of Truth — Round-Trip Write-Back)

> Source plan: `docs/plan/2026-06-11-refine-requirements-v2-phase5-roundtrip-writeback.md`
> Cross-phase canon: `docs/plan/refine-requirements-v2-decisions-so-far.md`
> **Hard external gate:** Phase 5 binds Phase 4 interfaces. **Phase 4 has LANDED** (verified
> 2026-06-12) — `create_next`, `block_diff`, `cast-comment-reanchor`, and the structured
> `{convergence, open_comment_count}` surface all exist with the names in `_shared_context.md`. No
> `[PENDING]` blockers remain.

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:
1. Start a new Claude session.
2. Tell Claude: *"Read `docs/execution/refine-req-v2-phase5/_shared_context.md` then execute
   `docs/execution/refine-req-v2-phase5/spN_name/plan.md`."*
3. After completion, update the Status column below.

## Sub-Phase Overview

| # | Sub-phase | Directory | Depends On | Status | Notes |
|---|-----------|-----------|-----------|--------|-------|
| 1 | Proposal Spine — schema, events, outbox + payload model | `sp1_proposal_spine/` | — | Done | Build first; Phase 1 + landed Phase 4 only |
| 2 | Same-Door Intake — POST change-requests + graduated-trust router | `sp2_same_door_intake/` | 1 | Done | One handler, anti-spoof, `WRITEBACK_GATE_POLICY` |
| 3a | Conflict Predicate — three-way content-hash check | `sp3a_conflict_predicate/` | 1 | Done | Parallel with 3b (disjoint files) |
| 3b | Notification Outbox + unified `needs_attention` surface | `sp3b_notification_outbox/` | 1 | Done | Parallel with 3a (disjoint files) |
| 4 | Sole File Writer — `cast-requirements-writeback` agent | `sp4_sole_file_writer/` | 2, 3a, 3b | Done | Critical path; heaviest; surgical apply only |
| 5 | E2E Proof (SC-006) + Spec Lockstep + FR-007 Guard | `sp5_e2e_spec_guard/` | 4 | Done | New roundtrip spec; negative assertions |

Status: Not Started → In Progress → Done → Verified → Skipped

No decision gates — all Open Questions in the source plan are owner-resolved (the 4 decisions in
`_shared_context.md` → "Pre-Existing Decisions").

## Dependency Graph

```
sp1 Proposal Spine ──► sp2 Same-Door Intake ──┬──────────────► sp4 Sole File Writer ──► sp5 E2E + Spec + Guard
                                              │                      ▲   ▲
              sp3a Conflict Predicate ────────┼──────────────────────┘   │
              (parallel)                      │                          │
              sp3b Notification Outbox ───────┴──────────────────────────┘
              (parallel, disjoint files)
```

**Critical path:** sp1 → sp2 → sp4 → sp5. sp3a and sp3b run in parallel after sp1 and both feed sp4
(conflict verdict + notification). Total ≈ 3–4 sessions.

### Parallel-safety verification (sp3a ∥ sp3b — must not touch the same files)

| sp3a writes | sp3b writes |
|---|---|
| `requirements_render/conflict.py` | `services/notification_service.py` |
| `tests/test_conflict_predicate.py` | `routes/api_requirements.py` (or `change_requests.py`) — payload extension + `/inbox` |
| `tests/fixtures/refine_requirements_v2/` (edited variants) | `app.py` (relay task registration) |
| | `tests/test_outbox_relay.py` |

Disjoint ✓. (sp2 also touches `app.py`/`change_requests.py`, but sp2 completes before the 3a∥3b
group runs in the critical-path ordering, so there is no concurrent write. If sp2 and sp3b are run
truly simultaneously, serialize the `app.py`/`change_requests.py` edits.)

## Execution Order

### Sequential Group 1
1. **sp1** Proposal Spine

### Sequential Group 2 (after Group 1)
2. **sp2** Same-Door Intake

### Parallel Group 3 (after Group 1 — may run alongside / after sp2; disjoint files)
- **sp3a** Conflict Predicate
- **sp3b** Notification Outbox

> sp3a and sp3b depend only on sp1, so they can start as soon as sp1 lands. They both feed sp4, which
> also needs sp2. Practically: run sp2, sp3a, sp3b after sp1 (sp3a/sp3b in parallel), then sp4.

### Sequential Group 4 (after sp2 + sp3a + sp3b)
4. **sp4** Sole File Writer

### Sequential Group 5 (after Group 4)
5. **sp5** E2E + Spec + Guard

## Reconciliation Status (landed-name verification, 2026-06-12)

| Bound interface | Plan marker | Landed name (verified) | Status |
|---|---|---|---|
| Version bump | `[PENDING Phase 4]` | `requirement_version_service.create_next(...) → {version, convergence, open_comments, displaced_comment_ids}` | ✅ landed |
| Change summary | `[PENDING Phase 4]` | `block_diff.diff_blocks(old,new)` + `summarize(diff)`; `BlockDiff`/`ModifiedBlock` | ✅ landed |
| Quote→region locator | `[PENDING Phase 4]` | `cast-comment-reanchor` subagent (bare-JSON verdict, no output.json) | ✅ landed |
| Structured notification surface | `[PENDING Phase 4]` | `GET /api/goals/{slug}/requirements/versions → {versions, convergence, open_comment_count}` | ✅ landed |
| Conflict hash | landed | `requirements_render/hashing.content_hash` | ✅ landed |
| `WRITEBACK_GATE_POLICY` | new (sp2) | does not exist yet — sp2 adds to `config.py` | ⬜ sp2 builds |

## Progress Log

_(Update after each sub-phase. Note any name drift discovered + the landed name adopted.)_

- 2026-06-12 — Execution plan authored by `cast-create-execution-plan`. All Phase 4 bindings verified
  landed; `[PENDING Phase 4]` markers resolved to concrete names in `_shared_context.md`.
