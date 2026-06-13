# Sub-phase 2: Same-Door Intake — POST change-requests + graduated-trust router

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase5/_shared_context.md` before starting.

## Objective

Open **one** door for proposing a requirement change. A single
`POST /api/goals/{slug}/change-requests` accepts an identical body from a human "suggest edit" and an
agent write-back — `author_type` is the only difference, and it is **data**, not a code branch
(FR-013). The handler writes a `change_request` row + a `change_request_events('proposed')` row
(+ the outbox row on the auto-apply path) **in one transaction**, and routes by **blast radius** into
`applied | proposed | conflicted`. **No file is touched** (sp4 applies).

## Dependencies

- **Requires completed:** sp1 (tables + `change_request` shape exist).
- **Assumed codebase state:** `change_requests`/`change_request_events`/`notifications_outbox` tables present; `RequirementsWriteback` model available.

## Scope

**In scope:**
- One intake handler under `cast_server/routes/` with `HX-Request` content negotiation.
- `change_request_service.py` (flat functions, house DB pattern) with an atomic `create(...)`.
- The graduated-trust router branching by blast radius, driven by a new `WRITEBACK_GATE_POLICY` config flag.
- Server-derived human identity (anti-spoof); slug validation; body-size cap.

**Out of scope (do NOT do these):**
- Do **not** compute the real conflict verdict here (that is sp3a's `detect_conflict`); intake only
  *records* the verdict it is handed / the `conflicted` status when sp3a is wired. For v2 sp2, the
  `conflicted` lane is a recorded status value, not a computation.
- Do **not** write the `.collab.md` (sp4). Do **not** build the relay loop (sp3b).
- Do **not** add a second "internal" write path — exactly one intake handler.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/routes/change_requests.py` | Create | Does not exist (alternatively extend `api_goals.py` — see Step 2.1) |
| `cast-server/cast_server/app.py` | Modify | Registers routers; add the new one if a new module |
| `cast-server/cast_server/services/change_request_service.py` | Create | Does not exist |
| `cast-server/cast_server/config.py` | Modify | Has `WORKFLOW_REGISTRY`/`STARTER_TASKS`/`PHASES`; add `WRITEBACK_GATE_POLICY` |
| `cast-server/tests/test_change_request_intake.py` | Create | Does not exist |

## Detailed Steps

### Step 2.1: Route placement (goals namespace — owner decision #1)

The endpoint is `POST /api/goals/{slug}/change-requests` (goals namespace, **not** `/api/specs/...`).
Two valid placements; pick to match the landed house style:
- **New `routes/change_requests.py`** with `APIRouter(prefix="/api/goals/{goal_slug}", tags=["change-requests"])` and `@router.post("/change-requests")`, registered in `app.py`. **Recommended** (keeps the file writer + intake cohesive, parallels `api_requirements.py`'s dedicated module).
- Or extend `api_goals.py` (which already hosts `POST /{slug}/route`).

`HX-Request` content negotiation per the `routes/api_agents.py:list_runs` precedent: return an HTML
fragment when `HX-Request` is set (the UI), JSON otherwise (agents) — **same data, one handler.**

### Step 2.2: `change_request_service.create(...)` — atomic write

`cast-server/cast_server/services/change_request_service.py`, flat functions, `db_path: Path | None
= None` injectable, `get_connection(db_path)` (house pattern). The write is multi-statement → wrap in
a single `BEGIN IMMEDIATE` (Phase 1 version-service precedent) so a mid-write crash leaves **nothing**
orphaned:

```python
def create(goal_slug: str, *, kind: str, proposed_body: str, base_version: int,
           target_quote: str | None, section_hint: str | None,
           author: str, author_type: str, origin_phase: str | None = None,
           origin_activity_id: str | None = None, origin_artifact_path: str | None = None,
           status: str = "proposed", db_path: Path | None = None) -> dict:
    conn = get_connection(db_path)
    with conn:                                    # single txn; BEGIN IMMEDIATE
        cur = conn.execute("BEGIN IMMEDIATE")
        cr_id = conn.execute("INSERT INTO change_requests (...) VALUES (...)", ...).lastrowid
        conn.execute("INSERT INTO change_request_events (change_request_id, event_type, actor, created_at) "
                     "VALUES (?, 'proposed', ?, ?)", (cr_id, author, now))
        if status == "applied":                   # auto-apply (pure addition) → queue notification
            conn.execute("INSERT INTO notifications_outbox (change_request_id, payload, status, created_at) "
                         "VALUES (?, ?, 'pending', ?)", (cr_id, json.dumps(payload), now))
        return _get(conn, cr_id)
```

Add `_append_event(...)` and `_get(...)` helpers mirroring `comment_service`'s shape.

### Step 2.3: Graduated-trust router (branch by blast radius, NOT author)

Decide `status` from blast radius, gated by the config policy:
- **Pure addition** (`target_quote` is NULL / `kind == "addition"`) → fast-track `applied` + FYI
  outbox row queued.
- **Modification / annotation of existing content** → `proposed` (gated). The human gate uses the
  same `AskUserQuestion` flow `cast-update-spec` uses — **do not reinvent it**.
- **Divergence from `base_version`** → `conflicted`. sp3a *computes* this; sp2 just records the
  verdict it is given (intake-records-the-verdict).

Policy lives in **config** (owner decision #3):

```python
# config.py, beside WORKFLOW_REGISTRY / STARTER_TASKS / PHASES
WRITEBACK_GATE_POLICY = "gate-except-additions"   # v2 default. Loosen later without a code change.
#   "gate-except-additions" → additions auto-apply; modifications/annotations gated.
#   (forward-compat values, e.g. "gate-all" / "gate-none", may be added later)
```

→ **Delegate:** `/cast-update-spec` is the **model** for the human gate UX (the `AskUserQuestion`
flow). Read how it gates before applying; do not invent a parallel confirmation UX. (You are not
running update-spec here — you are mirroring its gate posture.)

### Step 2.4: Anti-spoof + validation (security)

- **Human identity is server-derived, never trusted from the client body.** An agent legitimately
  self-declares `author_type="agent"` (it controls its own `output.json`); a **browser** client must
  not be able to set `author_type="human"` with an arbitrary `author`, nor impersonate another user.
  Derive `author`/`author_type` for the human path from the request context (session/origin), not the
  posted JSON. Add request-origin validation.
- Validate `slug` exists (404 if not).
- Cap `proposed_body` length (reject oversized → 422).

## Verification

### Automated Tests (permanent)
`cast-server/tests/test_change_request_intake.py`:
- A pure-addition POST (`target_quote=None`) → status `applied` (fast-track) and a `pending` outbox
  row is queued.
- A modification of existing content → status `proposed` (gated), **no** outbox row yet.
- A malformed / oversized body → 422.
- **Same-door parity:** a human-shaped body and an agent-shaped body hit the **identical** handler
  and differ only by `author_type` (assert one handler, identical persisted columns except
  `author_type`/`author`).
- **Anti-spoof:** a browser-context request claiming `author_type="human"` with a forged `author`
  gets the server-derived identity, not the posted one.
- **Transactionality:** simulate a failure after the `change_request` insert (monkeypatch the event
  insert to raise) → assert **no** orphaned `change_request_events` / `notifications_outbox` row
  (all-or-nothing).

### Validation Scripts (temporary)
- `curl -s -X POST localhost:8005/api/goals/<slug>/change-requests -H 'Content-Type: application/json' -d '{"kind":"addition","proposed_body":"FR-099 ...","base_version":1}'` → JSON with `status:"applied"`.
- Same with `-H 'HX-Request: true'` → an HTML fragment (negotiation works).

### Manual Checks
- `grep -rn "change-requests" cast-server/cast_server/routes/` → exactly **one** POST handler.

### Success Criteria
- [ ] Exactly one intake handler; no second internal write path (FR-013).
- [ ] Addition → `applied` + outbox queued; modification → `proposed`, gated; malformed → 422.
- [ ] Human/agent bodies identical except `author_type` (data, not a branch).
- [ ] Human `author`/`author_type` derived server-side; client cannot spoof.
- [ ] Row + event (+ outbox on auto-apply) written in **one** `BEGIN IMMEDIATE` txn; crash leaves nothing.
- [ ] `WRITEBACK_GATE_POLICY` flag controls the gate lane; default `"gate-except-additions"`.
- [ ] No file written by this sub-phase.

## Execution Notes
- The `conflicted` lane is *recorded* here; the predicate that decides it is sp3a. Keep intake's
  branching a thin dispatch over (blast-radius, policy, supplied-verdict) so sp4 can call
  `detect_conflict` and feed the verdict in.
- **Spec-linked files:** the intake route is part of the new `cast-requirements-roundtrip` contract
  authored in sp5 — keep the same-door + anti-spoof + policy semantics stable so sp5 documents them
  faithfully. No existing spec's SAV behavior changes here.
