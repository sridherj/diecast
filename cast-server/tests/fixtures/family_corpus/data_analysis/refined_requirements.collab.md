---
status: refined
scope_mode: hold
confidence:
  intent: high
  behavior: medium
  constraints: medium
  out_of_scope: medium
open_unknowns: 2
questions_asked: 0
classification:
  family: "data_analysis"
  confidence: 0.88
  alt_family: "bug_fix"
  reasoning: "The work is an investigation: read the dispatcher's run-state data to explain why pending children stop launching with no errors. The deliverable is a measured finding and a diagnosis, not a code change — the fix is a separate follow-up."
  uncertainty_factors:
    - "Shades toward bug_fix because a defect motivates it, but the requested output is an analysis of the run-state data, not the patch."
  modifiers:
    irreversible: false
    unknown_cause: false
  confirmed_by: "manual"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

<!-- CORPUS-PROVENANCE: family=data_analysis — authored from the real dispatcher slot-saturation investigation (zombie running-runs hold all MAX_CONCURRENT_AGENTS slots; API status view under-reports). -->

# Why does the dispatcher silently stop launching children?

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** cast-server/cast_server/services/agent_service.py

## Intent

**Job statement:** Explain, from the run-state data, why the cast-server dispatcher enqueues children as `pending` but never launches them — with no errors in the log — and quantify the gap between what the status API reports and what the database actually holds.

The symptom is alarming and quiet at once: children pile up `pending`, the dispatcher loop logs nothing, and HTTP latency stays flat and healthy. A hung event loop would stall HTTP too, so the flat latency is itself a clue. The analysis reads the `agent_runs` table directly rather than trusting the `GET /api/agents/runs?status=running` view, because the two disagree — and the size of that disagreement is the whole finding. The question is not "is the loop dead?" but "how many slots does the database think are occupied, and by what?"

## Evidence

- **The launch predicate is slot-bounded.** `_dispatcher_loop` only launches when `COUNT(status='running') < MAX_CONCURRENT_AGENTS` (default 7, `CAST_MAX_CONCURRENT_AGENTS`). When the count is already 7, the loop launches nothing and logs nothing — there is no error because nothing failed.
- **The occupants are zombies, not workers.** Abandoned interactive Claude sessions idling at a `new task?` / selection-menu prompt keep `status='running'` forever: the monitor sees a live tmux session and no terminal-output contract, so it never marks them terminal. On server restart, `recover_stale_runs` resumes them as `running`, re-saturating the slots.
- **The status API under-reports.** A live capture showed the API returning 2 running while the database held 7. Counting straight from the DB —  `SELECT COUNT(*) FROM agent_runs WHERE status='running'` at `~/.cast/diecast.db` — is the only trustworthy figure.
- **The signature is diagnostic.** Flat ~16ms HTTP latency, zero `Launched` log lines across several 10-second dispatcher cycles, and free slots on paper together mean saturation, not a stuck loop.

## Open Questions

- **[OPEN]** Should the monitor reap interactive sessions idle past a threshold automatically, or is operator-driven cancellation the safer default given the risk of killing an actively-working pane?
- **[DEFERRED]** Whether the status API's `running` filter should be reconciled to the raw DB count, or whether the divergence is intentional and only the documentation needs to warn against trusting it.
