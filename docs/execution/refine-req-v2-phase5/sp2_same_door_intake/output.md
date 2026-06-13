# sp2 Same-Door Intake — Execution Output

**Status:** completed
**Run:** run_20260612_052201_6893f7 (cast-subphase-runner)
**Date:** 2026-06-12

## What was built

The single intake door for proposing a requirement change —
`POST /api/goals/{slug}/change-requests` — plus the atomic service write and the
graduated-trust router behind it. One handler serves both a human "suggest edit"
(browser/HTMX) and an agent write-back (JSON `curl`); `author_type` is the only
difference and it is **data, not a code branch** (FR-013). **No file is touched**
(sp4 applies) and **no conflict verdict is computed** (sp3a) — intake records the
verdict it is handed.

### 1. Config flag (`cast-server/cast_server/config.py`)

- `WRITEBACK_GATE_POLICY` — the single global graduated-trust flag (owner decision
  #3), placed beside `WORKFLOW_REGISTRY` / `STARTER_TASKS` / `PHASES`. Default
  `"gate-except-additions"`; env-overridable via `CAST_WRITEBACK_GATE_POLICY`.
  Forward-compat values `"gate-all"` / `"gate-none"` are handled, not yet exercised.
- `WRITEBACK_HUMAN_AUTHOR` — the **server-derived** human identity for the anti-spoof
  human lane (`CAST_HUMAN_AUTHOR` → OS login → `"human"` literal, never raises).

### 2. Service (`cast-server/cast_server/services/change_request_service.py` — created)

House DB pattern (flat functions, injectable `db_path`, `get_connection`), modeled on
`comment_service` / `requirement_version_service`.

- `gate_status(kind, target_quote, policy)` — the graduated-trust router: branches by
  **blast radius**, not author. Pure addition → `applied`; modification/annotation →
  `proposed` (under the v2 default). The `conflicted` lane is sp3a's verdict, fed in
  via `create(status=...)`.
- `create(...)` — the atomic intake write. One `BEGIN IMMEDIATE` transaction wraps the
  `change_requests` insert, the `change_request_events('proposed')` append, and (only on
  the `applied` lane) the `notifications_outbox('pending')` FYI row. A mid-write crash
  leaves **nothing** orphaned (all-or-nothing; `conn.close()` on exception rolls back).
- `get` / `list_events` / `list_outbox` read helpers.

### 3. Route (`cast-server/cast_server/routes/change_requests.py` — created)

`APIRouter(prefix="/api/goals/{goal_slug}", tags=["change-requests"])`, registered in
`app.py` — the dedicated-module placement (owner decision #1, goals namespace), parallel
to `api_requirements.py`.

- **One handler** (`POST /change-requests`), `HX-Request` content negotiation: HTML
  fragment for the UI, JSON 201 for agents (the `api_agents.list_runs` precedent).
- **Anti-spoof identity** (`_resolve_identity`): the request *context* — not the posted
  body — picks the lane. HTMX/browser → server STAMPS `author_type="human"` +
  `WRITEBACK_HUMAN_AUTHOR` (posted author/author_type ignored). Plain JSON → agent lane,
  `author_type="agent"` forced, `author` = the agent's self-declared name. `author_type`
  can therefore only ever read `"human"` from the trusted browser context.
- **Validation**: slug exists (404); emitter shape via the **shared** `RequirementsWriteback`
  model (kind enum, required int `base_version`, non-empty `proposed_body`, the
  kind↔target_quote cross-field rule) → 422; `proposed_body` size cap (64 KB) → 422;
  agent lane with no name → 422.

### 4. HTML fragment (`templates/fragments/change_requests/intake_result.html` — created)

The negotiated HTML half — same data as the JSON response, Jinja-autoescaped, structure +
class names + data attributes only (visual CSS deferred).

### 5. Tests (`cast-server/tests/test_change_request_intake.py` — created, 14 tests)

Hermetic FastAPI app + `TestClient`, DB isolation per the `test_api_goals_route.py`
pattern (`isolated_db` + `connection.DB_PATH` patch). Covers: addition → `applied` +
queued outbox; modification/annotation → `proposed`, no outbox; 404/422 validation edges
(missing base_version, empty body, cross-field rule, oversized body, agent-without-name);
**same-door parity** (human-shaped vs agent-shaped persist identical columns except
author/author_type); **anti-spoof** (browser cannot forge a human author; agent lane
cannot claim `author_type="human"`); **transactionality** (event-insert failure leaves
no orphaned request/event/outbox rows).

## Verification

- `uv run pytest cast-server/tests/test_change_request_intake.py cast-server/tests/test_change_request_model.py cast-server/tests/test_schema_migration.py` → **42 passed**.
- Regression sweep (`test_api_goals_route` / `test_comment_service` / `test_families` / `test_api_agents`) → **137 passed**.
- Full suite collection → **824 tests collected**, no import errors.
- `import cast_server.app` OK; route registered at `/api/goals/{goal_slug}/change-requests`.
- `grep -rn "change-requests" cast-server/cast_server/routes/` → exactly **one** POST handler.

## Success criteria (all met)

- [x] Exactly one intake handler; no second internal write path (FR-013).
- [x] Addition → `applied` + outbox queued; modification → `proposed`, gated; malformed → 422.
- [x] Human/agent bodies identical except `author`/`author_type` (data, not a branch).
- [x] Human `author`/`author_type` derived server-side; client cannot spoof.
- [x] Row + event (+ outbox on auto-apply) written in **one** `BEGIN IMMEDIATE` txn; crash leaves nothing.
- [x] `WRITEBACK_GATE_POLICY` flag controls the gate lane; default `"gate-except-additions"`.
- [x] No file written by this sub-phase.

## Deviations from plan (intentional, low-risk)

- **`proposed_body` cap = 64 KB** (vs `api_requirements`'s 10 KB for `quoted_text`/`body`):
  a proposed_body can be a whole requirement block, so a more generous cap. Still rejects
  oversized → 422.
- **Emitter validation reuses `RequirementsWriteback`** rather than a bespoke route model —
  ties intake validation to the exact model an emitter validates against (same-door at the
  schema level). Extra `author`/`author_type` keys are ignored by the model (pydantic default).

## Notes for downstream sub-phases

- **sp3a** (conflict predicate): `gate_status` deliberately does NOT decide `conflicted`.
  Wire `detect_conflict` (keyed off `base_version` + `content_hash()` over the located
  region) in the route and pass `create(status="conflicted")` when it diverges — intake
  already records that status value and queues no outbox for it.
- **sp3b** (notification outbox relay): the `applied` lane already queues a denormalized
  `notifications_outbox('pending')` payload (`change_request_service._notification_payload`).
  sp3b builds the relay loop that delivers it onto the `{convergence, open_comment_count}`
  surface.
- **sp4** (sole file writer): keeps the same-door + anti-spoof + policy semantics stable so
  sp5 can document them in the new `cast-requirements-roundtrip` spec faithfully.
- The human "gate" here is the `proposed` status (no auto-apply), mirroring `cast-update-spec`'s
  gate posture; the actual `AskUserQuestion` accept UX is sp4's apply-time concern, not intake's.
