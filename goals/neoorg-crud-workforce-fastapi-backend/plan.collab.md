# High-Level Phasing Plan: neoorg CRUD Workforce + FastAPI Backend

## Overview

Get neoorg **running** first, then make it **self-building**. Two discoveries reshape this plan
from its first draft: (1) composition dispatches **through the neoorg server over HTTP** — so the
server *is* the dispatcher the maker-checker contract names — and the system is **bootstrapped by
hand** before the Workforce exists; and (2) **most of the lower MVCS stack already exists** —
`Task` and `Run` (`AgentRun`) already have entity/repository/service/schema + Alembic migrations,
and the dispatch/proof machinery is already built in `contract/` (`delegation.dispatch_child`,
`check/proof.resolve_proof_of_check`, `check/gate`, `discovery/`). What is genuinely missing is the
**HTTP surface** (no FastAPI app anywhere) and the **`Goal` entity** (the one trio member with
nothing built).

So the path is short and linear: a **thin hand-built bootstrap** that mounts the existing services
behind FastAPI and exposes the existing dispatcher over HTTP → **author the Workforce** (with the
existing Task/Run layers as the craft oracle) → **prove it by building `Goal` end-to-end** (the
missing member) → **scale** to cockpit follow-on entities.

Inputs: the refined brief (`refined_requirements.collab.md`) and the neoorg specs (`maker-checker`,
`agent-contract`, `agent-packaging`, `tasks`, `spine`). The cockpit prototype (`app.html`) is the
eventual backend-breadth map; everything past the proving slice is forward work in Phase 4.

## Phase 1: Server Up & Dispatch Live (thin, hand-built)
**Outcome:** A neoorg FastAPI server boots from a launcher, serves full CRUD over the **existing**
`Task` and `Run` services on the PGLite spine (rows persist across restart), **and** exposes the
**existing** dispatch/proof machinery over an HTTP **agent-dispatch surface** — the dispatcher that
runs a builder agent, captures its envelope, and enforces proof of its declared checkers. "The
omnigent system is up." Built by hand (leveraging diecast's agents); the Workforce does not exist yet.
**Dependencies:** None.
**Estimated effort:** 2–4 sessions (much of the stack already exists)
**Verification:** start the server → `POST/GET/PUT/DELETE` on `/tasks` and `/runs` with `404`/`422`
semantics; a created row survives a restart; the dispatch endpoint runs the existing
`contract/dummy` canned agent and **refuses** an envelope whose declared checker has no proof;
`uv run leak-guard` + the existing `uv run pytest -m "not live"` stay green.

Key activities:
- Add `fastapi` + `uvicorn` to `pyproject.toml`; `uv sync`.
- App skeleton in `src/neoorg/server/` (FastAPI `app` + `__main__`) and a `bin/neoorg-server`
  launcher (stdlib, mirroring diecast's `bin/cast-server`); request-scoped DB sessions via the
  existing `DbSessionManager`.
- A neoorg-native **`CRUDRouterFactory`** that turns a `(service, schema)` pair into
  `POST/GET(one+list)/PUT/DELETE` with `404`/`422` — the foundation the future
  `mvcs-controller-builder` emits against.
- Mount **Task** (`spine/services/task_service`) and **Run** (`contract/services/agent_run_service`)
  controllers via the factory. (Decision/Item/Message are cheap add-ons if wanted; not required.)
- **Expose the dispatcher over HTTP:** an endpoint wrapping `contract/delegation.dispatch_child` +
  `contract/check/proof.resolve_proof_of_check` (+ the `discovery/` status seam) — the server
  enforces declared-checker proof and returns the proven outcome (or 422 on missing proof).
- Write the one-page **reconciliation note**: the neoorg server *is* the dispatcher the maker-checker
  contract names; the existing `check_delegation_allowed` / `dispatch_child` / `resolve_proof_of_check`
  are that dispatcher, now reachable over HTTP. (Largely records existing behavior.)

## Phase 2: The Workforce Exists — Builder/Checker Pairs, Born Conforming
**Outcome:** All seven Pairs are authored, installed in `~/.claude/agents/`, and `agent-checker`-
passed: `magicwand-crud-builder`/`-checker` + the per-layer
`magicwand-mvcs-{schema,entity,repository,service,controller}-builder`/`-checker` +
`magicwand-mvcs-test-builder`/`-checker`. `crud-builder` dispatches sub-builders through the Phase-1
HTTP dispatch surface. Each builder handles **create and update**, update-safe.
**Dependencies:** Phase 1 (the live dispatch surface + the existing Task/Run layers as the reference).
**Estimated effort:** 4–6 sessions (parallelizable per-Pair)
**Verification:** each Pair installs and resolves; each has an `agent-checker` pass envelope; a smoke
test composes a trivial entity through the server (server enforces sub-builder checker proof);
`crud-builder`'s charter declares its sub-builders + its whole-CRUD `crud-checker`.

Key activities:
- Author each per-layer builder via `magicwand-agent-creator`, **encoding the craft of the existing
  hand-written Task/Run layers** (`task_service.py`, `task_repository.py`, `task_schema.py`, …) as
  the reference; pair each with its `-checker`; verify with `magicwand-agent-checker`.
- Make each builder **create-or-update and update-safe** (surgical edits preserving custom code,
  alter-not-recreate migrations — sharpest at `mvcs-entity-builder`; checkers gate clobber +
  destructive migrations).
- Author `magicwand-crud-builder` to dispatch the chain via the server (HTTP), declaring its
  sub-builders and its own `crud-checker`; it never calls a sub-layer checker.
- Spec-consistency: update the `core-agents` roster + add `agents/` charters; promote
  `maker-checker`'s canonical `crud-builder`/`crud-checker` example to shipped (via `/cast-update-spec`).

## Phase 3: Proven by Building Goal — the Missing Trio Member, End-to-End
**Outcome:** `crud-builder` (dispatched through the server) builds the **`Goal`** entity end-to-end —
schema/entity/repository/service/controller + migration + tests — completing the trio, and its
craft **matches the existing hand-written Task/Run layers** used as the oracle. This is the decision
gate for the Workforce.
**Dependencies:** Phase 2 (the Workforce) + Phase 1 (the dispatch surface + the live server).
**Estimated effort:** 1–2 sessions + iteration buffer
**Verification:** `crud-builder` produces a full `Goal` stack; `POST/GET/PUT/DELETE /goals` works with
`404`/`422`; a created Goal survives restart; the new Alembic migration applies cleanly; `uv run
pytest` (incl. live PGLite) passes; the Goal layers' craft diffs acceptably against `task_service.py`
/ `task_repository.py`; the composability audit (SC-005) holds — the server enforced each
sub-builder's proof, no builder called another's checker, `crud-builder` proved its `crud-checker`;
`leak-guard` + MVCS-compliance pass.

Key activities:
- Settle the `Goal` shape (its fields vs. a top-level Task — decided: `Goal` is its own entity);
  draw on the cockpit prototype + `spine` for the goal-level fields (status, phase, workflow_family…).
- Run `crud-builder` over the `Goal` shape; let the server dispatch each sub-builder and enforce proof.
- Diff the Goal layers' craft against the existing Task/Run oracle.
- **Decision gate:** matches the oracle + passes the gates → proceed to Phase 4. Falls short →
  iterate the builder charters (back to Phase 2), re-verified by `agent-checker` — never hand-patch
  the output (that voids the proof).

## Phase 4: Scale — New Entities & the Update Path via the Workforce
**Outcome:** The Workforce builds the next cockpit follow-on entities (e.g. Milestone, then others
the Dashboard/session board needs) and exercises the **update** path (adding a field/filter/endpoint
to an existing entity), "new shape, same machine," with no new agent authoring.
**Dependencies:** Phase 3 (the proven Workforce).
**Estimated effort:** 1–2 sessions per entity
**Verification:** each new entity's CRUD surface is live, persists, and passes generated tests; an
update to an existing entity lands via the builders without clobbering custom code; producing each
required only the entity shape as new input.

Key activities:
- Pick the next entities from the cockpit prototype map (highest-leverage read first).
- Run `crud-builder` per entity through the server; wire each controller into the app router.
- Exercise the **update** path on a built entity to prove update-safety on real evolution.
- Close the goal's success criteria (SC-001…SC-005); log remaining cockpit entities as Future Work.

## Build Order

```
Phase 1 ───────────► Phase 2 ─────► Phase 3 ─────► Phase 4
(thin bootstrap:     (author the     (workforce      (workforce builds
 FastAPI + factory +  Workforce,      BUILDS Goal     new entities +
 controllers over     craft from      end-to-end vs   exercises the
 existing Task/Run +   existing        the Task/Run    update path)
 expose dispatch)      Task/Run craft) oracle)
```

**Critical path:** Phase 1 → Phase 2 → Phase 3 → Phase 4 (strictly linear — HTTP-dispatch makes the
live server a hard prerequisite for the composer).

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Wrapping the existing dispatch machinery over HTTP is subtler than it looks (envelope capture, proof enforcement, session lifecycle) | Med | The logic already exists + is tested (`delegation`, `check/proof`, `discovery`, `dummy/roundtrip`); Phase 1 wires, doesn't invent; reuse `contract/dummy` to test the endpoint |
| The Workforce can't match the Task/Run craft when building Goal | Med | Phase 3 is an explicit gate; iterate builder charters (Phase 2), never hand-patch the output |
| `Goal`-as-entity drifts from the locked unified-Task-primitive model | Med | Decided: Goal is its own entity; if Phase 3 surfaces overlap with Task, raise a spec reconciliation rather than silently diverging |
| Server is load-bearing for the Workforce — down server = no composed builds | Med | Accepted (dev server); per-layer builders can still run standalone for debugging; keep the launcher dead-simple |
| Update path clobbers custom code / emits destructive migration | Med | Update-safety is a charter requirement; the paired checker gates clobber + data-losing migrations |
| PGLite live-lane cold-start / flakiness slows verification | Low-Med | Use `bin/test-live` (`-n0`, serial sidecar) per the README; never run the live lane under `-n auto` |

## Open Questions

- **[RESOLVED 2026-06-25]** Composition dispatch = HTTP via the neoorg server (server is the dispatcher).
- **[RESOLVED 2026-06-25]** Bootstrap is **thin** — Task/Run MVCS + migrations + dispatch machinery
  already exist; Phase 1 adds the HTTP surface only.
- **[RESOLVED 2026-06-25]** Proving slice = the Workforce **builds `Goal` end-to-end** (Goal is its
  own entity), judged against the existing Task/Run craft oracle.
- **Dispatch surface: reuse vs re-expose.** Confirmed lean: wrap the existing `contract/` dispatch +
  proof functions behind HTTP rather than build new dispatch. Detailed in the Phase-1 plan.
- **Server transport/auth for v1:** assumed localhost-only, no auth (like diecast's dev cast-server);
  now load-bearing for the Workforce — confirm if that changes.
- **`Goal` field shape:** which goal-level fields (status/phase/workflow_family/in_focus…) — settled
  at the top of Phase 3 from the cockpit prototype + spine.
- **Phase 4 entity order:** which cockpit entity first (Milestone vs Decision-surface vs …) — pick by
  Dashboard/session-board value.

## Spec References

- **Governing:** `maker-checker.collab.md` (the server-as-dispatcher reading + the canonical
  `crud-builder`/`crud-checker` Pair this goal makes real), `tasks.collab.md` (the existing Task
  stack = the craft oracle; the unified-primitive model that `Goal`-as-entity must reconcile with).
  Also: `agent-contract`, `agent-packaging`, `agent-communication` §8, `spine.collab.md`, and the
  omnigent-adapter suite (the dispatch surface runs agent sessions).
- **Consistency flags (via `/cast-update-spec`):**
  - Phase 1's reconciliation note may make the server-as-dispatcher reading explicit in
    `agent-communication` §8 / `maker-checker`.
  - Phase 3's `Goal`-as-entity needs reconciling with the unified-Task-primitive decision in
    `tasks.collab.md` (does Goal join the spine as a sibling of Task, or reference a root Task?).
  - Phase 2 adds seven Workforce Pairs → update the `core-agents` roster + add `agents/` charters;
    promote `maker-checker`'s `crud-builder`/`crud-checker` example to shipped.
```
