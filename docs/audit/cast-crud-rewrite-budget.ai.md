# cast-crud Rewrite Budget (Phase 5.1)

> Generated 2026-04-30 by `cast-create-execution-plan` consuming Phase 2 spike output.
> Drives Phase 5 sub-phases sp2/sp3a/sp3b/sp3c.
> Source spike: `docs/audit/linkedout-coupling-spike.ai.md` (15 rows, schema-valid).

## Per-agent rewrite budget

| agent_name | score | estimated_sessions | linkedout_isms | worked_example_role |
|---|---|---|---|---|
| cast-crud-orchestrator | green | 0.5 | (none) | dispatch root for the Widget maker chain — invokes schema → entity → repository → service → controller → (custom-controller) in MVCS order |
| cast-schema-creation | yellow | 0.5 | reference_code/src/common/schemas/* anchors (host-local reference paths; not LinkedOut-specific — relocate under diecast `references/`) | author Widget DDL: `id INT PK, name TEXT, sku TEXT UNIQUE, price_cents INT, created_at TIMESTAMP` |
| cast-entity-creation | green | 0.25 | (none) | Widget Pydantic model (mirrors DDL fields) |
| cast-repository | green | 0.25 | (none) | Widget repository CRUD methods (`create`, `get`, `list`, `update`, `delete`) with transaction context |
| cast-service | green | 0.25 | (none) | Widget service layer — returns Widget schema (not entity), wraps repository transactions |
| cast-controller | green | 0.25 | (none) | Widget HTTP routes (`POST /widgets`, `GET /widgets/{id}`, etc.) |
| cast-custom-controller | green | 0.25 | (none) | Widget status-transition example (e.g., archive/unarchive endpoint) — included in v1 (Q#23: green) |
| cast-crud-compliance-checker | green | 0.25 | (none) | validates Widget maker output against MVCS layer rules (service returns schema, repository owns transactions, controller bypasses nothing) |
| cast-repository-test | green | 0.25 | (none) | Widget repository test fixtures (in-memory + transactional) |
| cast-service-test | green | 0.25 | (none) | Widget service-layer mocked-repository tests |
| cast-controller-test | green | 0.25 | (none) | Widget HTTP route tests with mocked service |
| cast-integration-test-creator | yellow | 0.5 | `tests/integration/project_mgmt/label/test_label_controller.py` and `from project_mgmt.enums import TaskStatus` host-codebase anchors — parameterize to host project, not LinkedOut-specific | Widget end-to-end integration test (DB → repository → service → controller → HTTP) |
| cast-integration-test-orchestrator | red | 1.5 | upstream-private installation/demo slash commands, sandbox container name, host-private fixture paths (`linkedin-connections-subset.csv`, `gmail-contacts-subset.csv`), upstream-specific `goal_slug`, hard-coded host-private `output_dir`, upstream `TmuxHarness` literal, host-private `/tmp/.../decisions.jsonl`, host-private `.env.local` reference, "LinkedIn profiles for Apify enrichment" prose, $0.10 budget tied to LinkedOut profile cost | drives the Widget end-to-end test harness — major rewrite to a generic diecast harness (reuses Widget DDL + seed for the demo run) |
| cast-seed-db-creator | green | 0.25 | (none) | seeds 3 Widget rows (idempotent re-run check required per sp3c) |
| cast-seed-test-db-creator | green | 0.25 | (none) | seeds Widget test fixtures parameterized on the entity shape |

Row count: 15 (matches spike). The spike ships 15 rows; this budget table mirrors that count.

## Decisions

### cast-custom-controller v1 inclusion

- **Spike score:** green
- **v1 decision:** include
- **If deferred:** N/A (not deferred; included in v1 maker chain)
- **Rationale:** Per Q#23, green/yellow → include; red → defer to v1.1. Spike scored `green` (no LinkedOut-isms; uses `project_mgmt/task` status-transition example only). Including in v1 maker chain at MVCS position 6.

### Worked-example shape

- **Locked:** Widget table (per Q#9, maintainer-approved 2026-04-30).
- **Shape:** `Widget { id: int, name: str, sku: str, price_cents: int, created_at: datetime }`
- **Rationale:** Single entity is the smallest shape that exercises every layer of the maker chain (schema → entity → repository → service → controller). User+Profile pair would add a relational layer that proves nothing the single-entity case doesn't already prove and risks dragging joins/foreign-keys into the worked example. User+Profile relationship example deferred to v1.1 if the need surfaces.
- **Consumed by:** cast-schema-creation (DDL), cast-entity-creation (Pydantic model), cast-repository (CRUD methods), cast-service (business logic), cast-controller (HTTP routes), cast-custom-controller (status-transition route), cast-repository-test (fixtures), cast-service-test (mocks), cast-controller-test (HTTP tests), cast-integration-test-creator (E2E test), cast-integration-test-orchestrator (E2E harness driver), cast-seed-db-creator (3 seed rows), cast-seed-test-db-creator (test fixtures), cast-crud-compliance-checker (MVCS-rule validation against the Widget maker output).
- **Generality dry-run shape (sp2 verification g):** `Note { id: int, title: str, body: str }` (per Q#27, maintainer-approved 2026-04-30) — orthogonal to Widget, no relationships, used to catch shape-baked-into-prompt regressions before sp3b.

## Coherent-unit feasibility (US15 gate)

- **Total estimated_sessions:** 5.75 (must be ≤ 6.0) ✓
- **Red-scored agent count:** 1 — `cast-integration-test-orchestrator` (must be ≤ 2) ✓
- **Go/no-go:** **GO**

Breakdown (prose, to avoid double-count in pipe-delimited float scan):

- green: 12 agents, 3.25 sessions total.
- yellow: 2 agents, 1.0 session total.
- red: 1 agent, 1.5 sessions.
- All: 15 agents, 5.75 sessions.

The single red (`cast-integration-test-orchestrator`) consumes 26% of the total Phase 5 budget. sp3b should plan a generic diecast end-to-end harness as the replacement target rather than a line-by-line rewrite of the LinkedOut driver — the goal is harness portability, not LinkedOut feature parity.

The two yellow agents are host-local reference-codebase anchors, not LinkedOut entity coupling. sp2 and sp3b may downgrade these to green if a `references/` bundle ships alongside the cast-crud worked example (per spike note in linkedout-coupling-spike.ai.md).

## Forward references (for downstream sub-phases)

- **sp2** consumes the per-agent budget rows + Widget shape lock. Maker chain harvest order follows MVCS layering (schema → entity → repository → service → controller → custom-controller).
- **sp3a** consumes the `cast-crud-compliance-checker` budget row + Widget shape (for MVCS-rule violation fixtures).
- **sp3b** consumes the test maker rows + the red `cast-integration-test-orchestrator` budget allocation (1.5 sessions).
- **sp3c** consumes the seed-db-creator rows + Widget shape for idempotent seed scripts.
- **sp4** consumes the worked-example shape + budget total for the `docs/maker-checker.md` walkthrough.
