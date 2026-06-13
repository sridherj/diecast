# Shared Context: refine-req-v2-phase5 (Living Source of Truth — Round-Trip Write-Back)

> Read this file at the start of **every** sub-phase session. It is the DRY reference for the
> whole Phase 5 execution. Sub-phase plans (`spN_*/plan.md`) reference it instead of repeating it.

## Source Documents

- **Plan (this phase):** `docs/plan/2026-06-11-refine-requirements-v2-phase5-roundtrip-writeback.md`
- **Cross-phase canon (binding):** `docs/plan/refine-requirements-v2-decisions-so-far.md`
- **Synthesized design:** `goals/refine-requirements-v2/exploration/playbooks/07-living-source-of-truth-roundtrip.ai.md` (impact 9/10)
- **Goal:** `goals/refine-requirements-v2/plan.collab.md` (Phase 5 section)

## Project Background (the "why")

Phase 5 closes the loop. A downstream phase (exploration / planning / execution) that surfaces a
requirement-affecting change must get that change **written back into the canonical requirements
file** — with provenance (which phase/agent, derived from what), a user notification (what changed +
from where), inclusion in the version change summary, and **conflict surfacing instead of silent
overwrite**.

The load-bearing correctness claim (US7 Scenario 4): **silent two-way sync of a source-of-truth
document is *worse* than drift — it is untraceable overwrite of human intent.** Truth must be
*governed*, not eventually-consistent. The model is therefore **"propose + notify + gate, never
auto-sync"**: a downstream phase does not edit a requirement; it `POST`s a first-class
`change_request` carrying *where it came from* (`origin_*`) and *what version it assumed*
(`base_version`) to a DB the **server owns**. A single **`cast-requirements-writeback` agent** — the
sole file-writer, mirroring `cast-update-spec` — applies accepted changes **surgically** to the
`.collab.md`.

v2 builds the *receiving* mechanism and proves it with a **simulated** downstream emitter
(`tests/fixtures/synthetic_child.py`). Wiring real planner/executor emitters is a **later goal** —
hard-deferred here. **No CRDT/OT** (co-editing out of scope). PROV-O/JSON-LD export deferred.

## Operating Mode: HOLD SCOPE (with a quoted deferral fence)

Maximum rigor on the *receiving* path — intake → conflict → apply → notify. Hard deferral of:
real emitters, co-editing, provenance serialization ceremony. No silent drift between the two
postures. If you find yourself building an emitter, a merge engine, or a JSON-LD exporter, **stop —
it is out of scope for v2.**

## Critical Reconciliation: Phase 4 has LANDED (verified 2026-06-12)

The Phase 5 plan was authored with `[PENDING Phase 4]` markers because it bound interfaces that were
planned-but-not-executed. **Those interfaces have since landed.** This execution plan uses the
**verified landed names** below. If you ever find a name has drifted from what is listed here,
**adopt the landed name — do not fork the vocabulary** (decisions-so-far standing rule).

### Thin-spine reality (NOT the playbook's DB-canonical assumption)

The Step-7 playbook assumed a DB-canonical store with per-element surrogate IDs
(`spec_elements.surrogate`). **That does not exist.** The landed design is **files-canonical + thin
spine, no per-element IDs.** Wherever the playbook says `surrogate`, read **`quoted_text +
section_hint`** (the same locator shape as `requirement_comments`), resolved at apply-time by the
`cast-comment-reanchor` subagent, with conflict detection via `content_hash()` over the located
region at the base version vs HEAD.

## Key File Paths (landed — read to ground your work)

| Path | Role |
|------|------|
| `cast-server/cast_server/db/schema.sql` | **CANONICAL** schema. Add Phase 5 tables here. (Root `db/schema.sql` is legacy/diverged — **never touch it**.) |
| `cast-server/cast_server/db/connection.py` | `_run_migrations()` — mirror every new `CREATE TABLE IF NOT EXISTS` here byte-identically; `get_connection(db_path)` |
| `cast-server/cast_server/requirements_render/hashing.py` | `content_hash(text: str) -> str` (sha256 hex). The conflict predicate. Never reimplement. |
| `cast-server/cast_server/requirements_render/parser.py` | `parse_requirements(text)`, `parse_requirements_file(path)` → `ParsedRequirements` (read-only) |
| `cast-server/cast_server/requirements_render/blocks.py` | `ParsedRequirements`, `Block{kind, level, body, heading, ref, line_start, line_end}`, `BlockKind` |
| `cast-server/cast_server/requirements_render/block_diff.py` | `diff_blocks(old, new) -> BlockDiff`; `summarize(diff) -> dict`; `BlockDiff`, `ModifiedBlock` dataclasses |
| `cast-server/cast_server/services/requirement_version_service.py` | `create_next(...)`, `create_snapshot(...)`, `get_current`, `get_version`, `list_versions` |
| `cast-server/cast_server/services/comment_service.py` | `create_comment`, `list_comments`, `open_comment_count`, `resolve/reopen/relocate/orphan_comment` |
| `cast-server/cast_server/services/orchestration_service.py` | `update_manifest_status()` — the **surgical edit-by-key template** sp4 lifts |
| `cast-server/cast_server/routes/api_requirements.py` | Landed comment/version API, prefix `/api/goals/{goal_slug}/requirements`; `GET /versions` (the structured surface sp3b extends) |
| `cast-server/cast_server/routes/api_goals.py` | `POST /{slug}/route` (Phase 3b) — the goals-namespace route placement precedent |
| `cast-server/cast_server/routes/api_agents.py` | `list_runs` — `HX-Request` content-negotiation precedent (HTML for UI, JSON for agents) |
| `agents/cast-comment-reanchor/` | The quote→region locator subagent (bare-JSON verdict, no output.json). The **only** locator Phase 5 uses. |
| `agents/cast-update-spec/` | The "sole write path" + human-gate posture sp2/sp4 mirror |
| `cast-server/cast_server/config.py` | `WORKFLOW_REGISTRY`, `STARTER_TASKS`, `PHASES` — sp2 adds `WRITEBACK_GATE_POLICY` beside them |
| `cast-server/tests/fixtures/synthetic_child.py` | Emits the simulated downstream write-back for SC-006 (sp5) |
| `cast-server/tests/test_schema_migration.py` | Extend with Phase 5 table-existence assertions (sp1) |
| `cast-server/tests/test_fr007_readonly_guard.py` | Extend with the post-writeback byte-identity guard (sp5) |

## Landed Interface Signatures (use these exact names)

```python
# requirements_render/hashing.py
content_hash(text: str) -> str                       # sha256 hex of UTF-8

# requirements_render/block_diff.py
diff_blocks(old: ParsedRequirements, new: ParsedRequirements) -> BlockDiff
summarize(diff: BlockDiff) -> dict                    # {added:[...], removed:[...], modified:[...]}
# BlockDiff(frozen): .added, .removed, .modified ;  ModifiedBlock(frozen)

# services/requirement_version_service.py
create_next(goal_slug: str, content: str, created_by: str | None = None,
            *, db_path: Path | None = None) -> dict
#   -> {version: dict, convergence: "converged"|"unconverged",
#       open_comments: list[dict], displaced_comment_ids: list[int]}
get_current(goal_slug, *, db_path=None) -> dict | None
get_version(goal_slug, version: int, *, db_path=None) -> dict | None
list_versions(goal_slug, *, db_path=None) -> list[dict]

# services/comment_service.py
open_comment_count(goal_slug: str, *, db_path: Path | None = None) -> int
create_comment(goal_slug, quoted_text, section_hint, body, ...) -> dict
relocate_comment(comment_id, new_quoted_text, new_section_hint, actor, *, db_path=None) -> dict
```

### `cast-comment-reanchor` subagent contract (the only locator)

`agents/cast-comment-reanchor/` — `dispatch_mode: subagent`, `interactive: false`. The parent feeds
it the displaced/target quotes + both document versions; it returns **one bare JSON verdict list** as
its final assistant message (per item: `relocated` with the new quote, or `orphaned`). It writes
**no `.output.json` envelope and no files** — it is deliberately outside `cast-delegation-contract`.
The server's verbatim-substring backstop on `POST .../relocate` (422 on a non-present quote) means a
bad guess can never silently mis-place anything. **Phase 5 builds no new anchoring** — it reuses this.

## The structured notification surface sp3b EXTENDS (do not rebuild)

Phase 4 landed a **structured** surface — sp3b adds onto it, does **not** structure-from-boolean:

```
GET /api/goals/{goal_slug}/requirements/versions
  -> {versions: [...], convergence: "converged"|"unconverged", open_comment_count: int}
# convergence = "unconverged" if open_comment_count > 0 else "converged"  (derived, never stored)
```

The Goal-Card comment-count slot is filled client-side from this. sp3b adds round-trip / provenance
notifications **onto this existing surface**. (The integer `agent_runs.needs_attention` flag is a
*separate* agent-run signal — unrelated to this requirements surface. Do not conflate them.)

## Data Schemas & Contracts (Phase 5 new tables — sp1 builds these)

Add to **canonical** `cast-server/cast_server/db/schema.sql` AND mirror byte-identically in
`_run_migrations()` (`db/connection.py`). The schema header already reserves space:
"and change_request* tables (Phase 5)".

```sql
CREATE TABLE IF NOT EXISTS change_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_slug TEXT NOT NULL,
    -- THIN-SPINE LOCATOR (NOT a surrogate FK — that table does not exist; do not "restore" it):
    target_quote TEXT,                       -- NULL ⇒ pure addition, no target region
    section_hint TEXT,                       -- nearest heading hint, mirrors requirement_comments
    base_version INTEGER,                    -- the requirement_versions.version the change assumed
    proposed_body TEXT NOT NULL,             -- the addition/modification text
    kind TEXT NOT NULL,                      -- 'addition' | 'modification' | 'annotation'
    status TEXT NOT NULL DEFAULT 'proposed', -- 'proposed'|'applied'|'conflicted'|'rejected'|'superseded'
    -- W3C-PROV denormalized provenance columns:
    origin_phase TEXT,                       -- e.g. 'planning'
    origin_activity_id TEXT,                 -- run_id of the emitting agent
    origin_artifact_path TEXT,               -- e.g. 'plan.collab.md'
    author TEXT NOT NULL,                    -- agent name or human identity (server-derived for humans)
    author_type TEXT NOT NULL CHECK (author_type IN ('human','agent')),  -- DATA, never a code branch (FR-013)
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (goal_slug) REFERENCES goals(slug) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS change_request_events (   -- append-only audit (generalizes comment_events)
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_request_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,                -- 'proposed'|'accepted'|'rejected'|'conflicted'|'applied'|'superseded'
    actor TEXT,
    payload TEXT,                            -- JSON
    created_at TEXT NOT NULL,
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications_outbox (    -- transactional outbox (dual-write fix)
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_request_id INTEGER NOT NULL,
    payload TEXT NOT NULL,                   -- JSON: what changed + from where
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'delivered'
    created_at TEXT NOT NULL,
    delivered_at TEXT,
    FOREIGN KEY (change_request_id) REFERENCES change_requests(id) ON DELETE CASCADE
);
```

> The plan prose says "Four tables" in one place and lists three — the **three** above are correct
> (`change_requests`, `change_request_events`, `notifications_outbox`). The pydantic
> `RequirementsWriteback` payload model is the fourth *artifact*, not a table.

## Pre-Existing Decisions (binding — adopt verbatim)

These four owner-resolved decisions are already folded into the plan's Open Questions. **Do not
re-litigate.**

1. **Endpoint namespace → `POST /api/goals/{slug}/change-requests`** (goals namespace, **NOT**
   `/api/specs/...`). Matches landed `POST /api/goals/{slug}/route` (Phase 3b). Applies to sp2 + the
   new spec.
2. **`base_version` reference shape → integer `requirement_versions.version`** (matches landed
   `UNIQUE(goal_slug, version)`; no synthetic version id). Applies to sp1 schema + sp3a conflict.
3. **Graduated-trust gate → a single global `WRITEBACK_GATE_POLICY` config flag** (NOT per-element).
   Recommended v2 value: `"gate-except-additions"`. Can loosen later without a code change.
4. **Notification → EXTEND the existing structured `{convergence, open_comment_count}` surface +
   Goal-Card slot.** sp3b adds round-trip/provenance notifications onto it; it does **NOT**
   structure-from-boolean.

Other standing canon (from decisions-so-far):
- **Service DB pattern (canon for all service code):** flat functions, `db_path: Path | None = None`
  injectable + `get_connection(db_path)`. Modeled on `goal_service.py`/`task_service.py`, **NOT**
  `orchestration_service.py` (which is file/manifest-based; sp4 borrows only its surgical-edit
  *structure*, not its persistence).
- **FR-013:** `author_type`/`author_kind` is the **only** human/agent distinction, and it is data —
  never a code branch. The UI must have **no privileged write path the agent lacks** (one intake
  handler).
- **FR-007:** the `.collab.md` is byte-faithful; render/`rerender` code **never** mutates it. After
  Phase 5, the `cast-requirements-writeback` agent is the **sole** mutator (the carve-out).

## Relevant Specs

Sub-phases that touch spec-linked files must read the spec and preserve its SAV behaviors:

- **`docs/specs/cast-delegation-contract.collab.md`** — server-never-writes-artifacts; subagent
  carve-out. Phase 5's `cast-requirements-writeback` is the explicit file-apply carve-out (server
  owns the proposal DB; the agent owns the file). Restated in the new sp5 spec — **no conflict**.
- **`docs/specs/cast-output-json-contract.collab.md`** — contract-v2 `artifacts[]`; "parents ignore
  unknown fields". `requirements_writeback` is an **additive** artifact type. No conflict.
- **`docs/specs/cast-requirements-render.collab.md`** (v2, Phase 3a/4) — route semantics, DOM
  contract, change-summary surface, `block_diff`, `create_next`, convergence rule,
  `cast-comment-reanchor` carve-out. Phase 5's change summary + conflict surface **ride this page**;
  the new roundtrip spec **references** it (does not duplicate).
- **`docs/specs/cast-requirements-roundtrip.collab.md`** *(create in sp5)* — change-request
  lifecycle, same-door API, graduated-trust policy, conflict semantics, sole-writer carve-out,
  notification surface. Register in `docs/specs/_registry.md`.

## Sub-Phase Dependency Summary

| Sub-phase | Type | Depends On | Blocks | Can Parallel With |
|---|---|---|---|---|
| sp1 Proposal Spine | Sub-phase | None (Phase 1 + landed Phase 4) | sp2, sp3a, sp3b | — |
| sp2 Same-Door Intake | Sub-phase | sp1 | sp4 | sp3a, sp3b |
| sp3a Conflict Predicate | Sub-phase | sp1 | sp4 | sp2, sp3b |
| sp3b Notification Outbox | Sub-phase | sp1 | sp4 | sp2, sp3a |
| sp4 Sole File Writer | Sub-phase | sp2, sp3a, sp3b | sp5 | — |
| sp5 E2E + Spec + Guard | Sub-phase | sp4 | — | — |

No decision gates — all Open Questions in the plan are owner-resolved.

## Test & Tooling Conventions

- Run tests with `uv run pytest` from repo root (or `cd cast-server && uv run pytest`).
- Migration tests mirror Phase 1 sp2b's table-existence assertion pattern (`test_schema_migration.py`).
- Slow / live-subagent tests use the `eval_*` filename convention so they are excluded from the
  default suite (mirror Phase 4's e2e exclusion).
- After authoring/editing any agent under `agents/`, run `bin/generate-skills`.
- Spec lint: `bin/cast-spec-checker <spec>` must exit 0.
