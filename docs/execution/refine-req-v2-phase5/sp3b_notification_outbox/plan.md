# Sub-phase 3b: Notification Outbox + Unified `needs_attention` Surface

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase5/_shared_context.md` before starting.

## Objective

Deliver the alert **exactly once**, with **no dual-write drift**. The change and its alert commit in
the **same transaction** (the outbox row sp2 already writes on auto-apply); a polling relay drains
`notifications_outbox WHERE status='pending'` **at-least-once** and marks `delivered`; the alert
reaches the user through the **existing** structured surface — `{convergence, open_comment_count}`
from `GET /api/goals/{slug}/requirements/versions` (Phase 4, landed) — now carrying a **round-trip /
provenance** descriptor ("requirements updated from planning: +FR-021"), plus a minimal
W3C-LDN-aligned `GET/POST /api/goals/{slug}/inbox` JSON endpoint so watching agents consume the same
resource. **One surface, shared with Phase 4 — not two.**

## Dependencies

- **Requires completed:** sp1 (`notifications_outbox` table). sp2 writes the outbox row in its apply
  txn — sp3b only **drains and delivers** it.
- **Extends (landed):** the Phase 4 structured surface `{convergence, open_comment_count}` and its
  Goal-Card slot. sp3b adds round-trip notifications **onto** it (owner decision #4 — does **not**
  structure-from-boolean).
- **Parallel with sp3a** — disjoint files.

## Scope

**In scope:**
- A FastAPI lifespan-managed background relay that polls the outbox, delivers, marks `delivered`.
- Extending the structured `{convergence, open_comment_count}` descriptor with a round-trip /
  provenance field so the badge renders *what changed + from where* (FR-019).
- `GET/POST /api/goals/{slug}/inbox` (LDN-aligned JSON), the agent companion to the human badge.

**Out of scope (do NOT do these):**
- Do **not** stand up a parallel notifier — **extend** the existing surface (the unification decision).
- Do **not** structure-from-boolean — Phase 4 already shipped the structured surface; build onto it.
- No CDC/Debezium — polling is the right weight at SQLite scale.
- Do **not** touch sp3a's `conflict.py` or its tests.
- Do **not** write the `.collab.md` (sp4).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/notification_service.py` | Create | Does not exist (relay + outbox drain) |
| `cast-server/cast_server/app.py` | Modify | Has the lifespan + router registration; add the relay task + register `/inbox` |
| `cast-server/cast_server/routes/api_requirements.py` (or `change_requests.py`) | Modify | Extend the `{convergence, open_comment_count}` payload; add `/inbox` |
| `cast-server/tests/test_outbox_relay.py` | Create | Does not exist |

## Detailed Steps

### Step 3b.1: The relay (lifespan-managed background task)

Mirror the landed dispatcher/monitor-loop precedent (grep `app.py` for the existing lifespan
background task / `asyncio.create_task`). The relay:

```python
# notification_service.py — house DB pattern (flat fns, db_path injectable)
def drain_outbox(*, db_path: Path | None = None) -> list[dict]:
    """At-least-once: read pending rows, deliver, mark delivered. Idempotent on re-run."""
    conn = get_connection(db_path)
    pending = conn.execute("SELECT * FROM notifications_outbox WHERE status='pending' ORDER BY id").fetchall()
    delivered = []
    for row in pending:
        _deliver(row)                         # surface onto the structured needs_attention descriptor
        with conn:
            conn.execute("UPDATE notifications_outbox SET status='delivered', delivered_at=? WHERE id=?",
                         (now, row["id"]))
        delivered.append(dict(row))
    return delivered
```

Register it as a lifespan-managed periodic task in `app.py` (the same place the dispatcher loop is
started). **At-least-once** is the contract: a crash between commit and relay must still deliver on
re-run; the UI dedupes on `change_request_id`.

### Step 3b.2: Extend the structured surface (not a new one)

The landed `GET /api/goals/{goal_slug}/requirements/versions` returns
`{versions, convergence, open_comment_count}`. Add a round-trip / provenance descriptor so the
Goal-Card badge can render *what changed + from where* — e.g. an additional
`recent_writebacks: [{change_request_id, summary, origin_phase, origin_artifact_path, applied_at}]`
field (FR-019 in one shape), sourced from delivered outbox rows / applied change_requests. **Reuse
the existing rail** — do not add a parallel notification field or a second endpoint for the human badge.

> Confirm the exact descriptor field name with the Goal-Card client code
> (`templates/.../goal_detail.html` / the JS that fills the comment-count slot) so the badge consumes
> it without a second fetch.

### Step 3b.3: `/inbox` (LDN-aligned, agent companion)

`GET/POST /api/goals/{slug}/inbox` — JSON, returns the **same** payload shape the HTMX badge
consumes (so a watching agent reads the identical resource a human sees). `GET` lists; `POST` is the
LDN notification sink (additive; can be minimal in v2).

## Verification

### Automated Tests (permanent)
`cast-server/tests/test_outbox_relay.py`:
- Insert a change + outbox row in **one** txn (use sp2's `create` with the auto-apply path, or a
  direct fixture); run `drain_outbox` → the row is `delivered`.
- **Crash assertion (SC-006, unit-level):** inject a crash *between the commit and the relay* and
  re-run the relay → the alert still delivers (at-least-once) with **0 lost and 0 duplicate** after
  UI dedupe on `change_request_id`. (Simulate by committing the outbox row, then running the relay
  twice and asserting the descriptor surfaces the change once.)
- `/inbox` returns the same payload shape the HTMX badge consumes (assert structural parity with the
  `versions` endpoint's round-trip descriptor).
- The extended `versions` payload still returns the landed `{versions, convergence,
  open_comment_count}` keys unchanged (no regression) **plus** the new round-trip descriptor.

### Validation Scripts (temporary)
- `curl -s localhost:8005/api/goals/<slug>/requirements/versions | python -m json.tool` → shows the
  existing keys + the new round-trip descriptor.
- `curl -s localhost:8005/api/goals/<slug>/inbox` → same shape.

### Manual Checks
- `grep -rn "needs_attention\|notifications_outbox\|recent_writeback" cast-server/cast_server/` →
  confirm there is **one** notification surface extended, not a parallel one.

### Success Criteria
- [ ] Relay drains `pending` → `delivered`, at-least-once, idempotent on re-run.
- [ ] Crash between commit and relay still delivers; 0 lost / 0 duplicate after dedupe on `change_request_id`.
- [ ] The structured `{convergence, open_comment_count}` surface is **extended** (round-trip descriptor added), not duplicated.
- [ ] `/inbox` returns the same payload shape the badge consumes.
- [ ] No parallel notifier; no CDC; polling only.
- [ ] sp3a's files untouched.

## Execution Notes
- The outbox is the **dual-write fix**: the change + outbox insert share one txn (sp2 owns that
  write; sp3b owns the drain). Assert the same-txn insert in review; the UI dedupe key is
  `change_request_id`.
- Phase 4 owns the "unified notification surface" decision. Phase 4 **shipped the structured
  surface** (`{convergence, open_comment_count}` — confirmed landed), so sp3b **extends** it. There
  is no boolean-only fallback to absorb.
- **Spec-linked files:** the `versions` endpoint and Goal-Card slot are covered by
  `cast-requirements-render.collab.md` — read it; you are **additively** extending the payload, so
  existing SAV behaviors (the landed keys, the convergence rule) must remain intact. The round-trip
  notification semantics are documented in the new roundtrip spec (sp5).
