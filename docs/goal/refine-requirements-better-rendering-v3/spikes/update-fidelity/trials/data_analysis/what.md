---
contract: cast-requirements-what/v1
goal_slug: spike-data_analysis
family: data_analysis
source_hash: 1b04657b506a97a3618033381d84bfb7ac8bcb8ff260ca4793b2eb6177293ae2
sections:
  - title: "What we're trying to find out"
    outcome: >-
      L1: The dispatcher quietly stops launching children not because the loop
      is dead, but because we don't yet know how many slots the database
      believes are occupied. L2: The reader must grasp that flat, healthy HTTP
      latency is itself a clue (a hung loop would stall HTTP too), and that the
      investigation deliberately reads the DB directly instead of trusting the
      status API, because the two disagree and the size of that disagreement is
      the whole question.
    block_refs: []
  - title: "What the data shows"
    outcome: >-
      L1: The slots are full of zombies, not workers — the launch predicate is
      slot-bounded (COUNT(status='running') < MAX_CONCURRENT_AGENTS, default 7),
      so once 7 abandoned interactive sessions hold the slots forever, the loop
      launches nothing and logs nothing because nothing failed. L2: The
      supporting evidence — the API under-reports (1 running on paper vs 7 in
      the DB), the reaper never fires on idle panes, restart resumes the zombies
      via recover_stale_runs, and the saturation signature (flat ~16ms latency,
      zero Launched lines, free slots on paper) — is what makes the diagnosis
      trustworthy.
    block_refs: []
  - title: "Still unanswered"
    outcome: >-
      L1: The analysis stops at the diagnosis and does not prescribe the fix —
      the open question is whether the monitor should auto-reap interactive
      sessions idle past a threshold, or whether operator-driven cancellation is
      the safer default given the risk of killing an actively-working pane. L2:
      The reader should leave understanding this is a deliberate fork left open,
      not an oversight.
    block_refs: []
unmapped_refs: []
gaps: []
---

## What we're trying to find out

**L1 takeaway:** Frame the investigation as a question about *occupancy*, not liveness — "how many slots does the database think are occupied, and by what?" — not "is the loop dead?" The reader must walk away knowing the dispatcher's silence is the thing being explained, and that silence plus health is the paradox to resolve.

**L2 supporting points:**
- The symptom is "alarming and quiet at once": children pile up `pending`, the dispatcher loop logs nothing, HTTP latency stays flat and healthy.
- Flat latency is itself diagnostic — a hung event loop would stall HTTP too, so health *rules out* the obvious "dead loop" theory.
- The analysis distrusts the `GET /api/agents/runs?status=running` view on purpose and reads the `agent_runs` table directly, because the two disagree and the magnitude of that disagreement is the finding.

**Source content carrying this:** the `## Intent` section, specifically the job statement and the paragraph contrasting the API view against the database read.

## What the data shows

**L1 takeaway:** The slots are saturated by zombies. The launch predicate only fires when `COUNT(status='running') < MAX_CONCURRENT_AGENTS` (default 7); abandoned interactive Claude sessions idling at a `new task?` / selection-menu prompt keep `status='running'` forever, so the count sits at 7, the loop launches nothing, and — because nothing actually failed — it logs nothing.

**L2 supporting points:**
- **The API under-reports:** a live capture showed the API returning 1 running while the database held 7; the only trustworthy figure is `SELECT COUNT(*) FROM agent_runs WHERE status='running'` against `~/.cast/diecast.db`.
- **The reaper never fires on idle panes:** the monitor's terminal-output contract has no idle-timeout branch, so a session parked at a menu is indistinguishable from one mid-task.
- **Restart re-saturates:** `recover_stale_runs` resumes the zombies as `running` on server restart.
- **The signature is conclusive:** flat ~16ms latency + zero `Launched` lines across several 10-second cycles + free slots on paper together mean saturation, not a stuck loop.

**Source content carrying this:** the five bullets of the `## Evidence` section.

## Still unanswered

**L1 takeaway:** The finding is a diagnosis, not a patch — the report deliberately leaves the remediation choice open rather than prescribing one.

**L2 supporting points:**
- The single open question: should the monitor auto-reap interactive sessions idle past a threshold, or is operator-driven cancellation the safer default?
- The tension named in the source is the risk of killing an actively-working pane, which is why the fork is left to a human.

**Source content carrying this:** the `## Open Questions` section's single `[OPEN]` item.
