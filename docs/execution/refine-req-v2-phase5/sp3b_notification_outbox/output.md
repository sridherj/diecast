# sp3b — Notification Outbox + Unified `needs_attention` Surface — Output

**Status:** ✅ Complete · all tests green (24 sp-local, 232 in the requirements/change-request band)

## What was built

The **delivery** half of the transactional outbox. sp2 already writes the `notifications_outbox`
row in the *same transaction* as the auto-applied `change_request`; sp3b drains it at-least-once
and surfaces it on the **existing** structured `{convergence, open_comment_count}` rail — one
surface, not a parallel notifier (owner decision #4).

### Files created / modified

| File | Action | What |
|------|--------|------|
| `cast-server/cast_server/services/notification_service.py` | **Create** | `drain_outbox()` (at-least-once relay drain, idempotent), `recent_writebacks()` (round-trip descriptor, deduped on `change_request_id`), `run_relay()` (lifespan loop) |
| `cast-server/cast_server/app.py` | Modify | Register the relay as a lifespan-managed background task beside the dispatcher; cancel both on shutdown |
| `cast-server/cast_server/routes/api_requirements.py` | Modify | **Extend** `GET …/requirements/versions` with `recent_writebacks` (landed keys untouched) |
| `cast-server/cast_server/routes/change_requests.py` | Modify | `GET/POST /api/goals/{slug}/inbox` (LDN-aligned, same item shape the badge consumes) |
| `cast-server/tests/test_outbox_relay.py` | **Create** | 14 tests — drain, idempotency, SC-006 crash assertion, surface extension, `/inbox` parity |

## Design decisions

- **Delivery = a status flip, not a push.** The relay flips `pending → delivered`; the human
  Goal-Card badge and the agent `/inbox` both *read* the descriptor (`recent_writebacks`) from
  delivered rows. This makes the whole path naturally idempotent and gives the SC-006 guarantee
  for free.
- **Dedupe on `change_request_id` at read time.** Even with a duplicate outbox row pointing at
  the same change (the at-least-once re-queue case), the descriptor surfaces the change **once**
  — 0 lost / 0 duplicate.
- **One surface.** `recent_writebacks()` is the single source for both `…/versions` (`recent_writebacks`)
  and `/inbox` (`notifications`). `grep` confirms no parallel notifier.
- **Relay interval** lives as a module constant (`CAST_NOTIFICATION_RELAY_INTERVAL`, default 5s)
  in `notification_service.py` — sp3b's touch-set deliberately excludes `config.py`. Polling is
  the right weight at SQLite scale (no CDC/Debezium).

## Verification

- `uv run pytest cast-server/tests/test_outbox_relay.py cast-server/tests/test_change_request_intake.py` → **24 passed**.
- `uv run pytest -k "requirement or change_request or outbox or version or comment or schema_migration"` → **232 passed**, 0 regressions.
- `python -c "import cast_server.app"` → clean import; relay coroutine wired.
- `grep -rn "recent_writeback|notifications_outbox|drain_outbox"` → exactly one notification surface, extended (not duplicated).

### Success criteria (from plan)

- [x] Relay drains `pending` → `delivered`, at-least-once, idempotent on re-run.
- [x] Crash between commit and relay still delivers; 0 lost / 0 duplicate after dedupe on `change_request_id`.
- [x] The `{convergence, open_comment_count}` surface is **extended** (round-trip descriptor added), not duplicated.
- [x] `/inbox` returns the same payload shape the badge consumes.
- [x] No parallel notifier; no CDC; polling only.
- [x] sp3a's files untouched.

## Notes / hand-offs

- **Spec reconciliation (sp5):** render-spec FR-023 lists the `versions` payload as
  `{versions, convergence, open_comment_count}`. sp3b's `recent_writebacks` is the sanctioned
  additive extension (owner decision #4); the three landed keys + convergence rule are unchanged.
  The new `cast-requirements-roundtrip.collab.md` (sp5) documents the round-trip notification
  semantics and references the render spec — no edit to the render spec was made here.
- **Client wiring (optional, deferred):** the server descriptor is live; rendering a round-trip
  badge in `requirements_comments.js` (which today fills the convergence chip from `/comments`)
  is a thin additive enhancement and is not required for the sp3b contract.
- **sp4** (sole file writer) is unblocked on the notification axis: an applied change's outbox
  row is committed in sp2's txn and delivered by this relay.
