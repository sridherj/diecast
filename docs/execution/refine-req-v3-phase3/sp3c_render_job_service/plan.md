# Sub-phase 3c: The Render Service Runs the Maker as a Background Job

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase3/_shared_context.md` before starting.

## Objective

Create `cast_server/services/render_job_service.py` to execute the
`run_what → gate_what → run_how → gate_html → publish` pipeline as a background job (single-flight per
`(goal_slug, source_hash)`), invoking both agents as tool-free `claude -p` subprocesses.
`requirements_render_service` gains the orchestrator seam: the maker pipeline is the **primary
branch**, `rerender_requirements_html`/`render_requirements()` is demoted to the **fallback branch**
served **only on a literal no-output failure**. The canonical `.collab.md` is structurally unwritable
by the maker (`--tools ""`). This sub-phase carries the two heaviest reconciliation edits: the
**structural-violation OWNER OVERRIDE** and **revision (a)** (reaper-from-stage-list + semaphore
release + `heartbeat_at`).

## Dependencies

- **Requires completed:** 3a (the two agents + contracts) and 3b (`maker_gate.py`, incl.
  `container_text_index`).
- **Assumed codebase state:** `requirements_render_service.rerender_requirements_html` (atomic write +
  AUTO-GENERATED header + `source-hash` cache), `render_requirements()`, `is_stub`/`STUB_WORD_THRESHOLD`,
  `agent_service.py` env-hygiene precedent, `config.py`, `schema.sql`, `db/connection.py` all exist.

## Scope

**In scope:**
- `render_job_service.py`: `AgentRunner` seam, the named pipeline stages, single-flight registry,
  per-job daemon thread, the in-flight semaphore, the lazy reaper, the fallback branch, publish +
  compare-and-publish, the stub short-circuit.
- The orchestrator seam in `requirements_render_service` (maker primary / deterministic fallback).
- `render_jobs` CREATE TABLE in `schema.sql` (**including `heartbeat_at`**).
- `config.py`: `RENDER_JOBS_DIR`, the **stage-timeout list**, the reaper-ceiling multiple, the
  in-flight cap.
- `cast-server/tests/test_render_job_service.py` + the `test_fr007_readonly_guard.py` maker sweep.

**Out of scope (do NOT do these):**
- Do NOT change the route or build the generating-state UI / status endpoint (3d).
- Do NOT add the checker / quality loop / the four 4a flag columns (`human_review`, `review_reason`,
  `published_attempt`, `published_score`) — 4a-2 owns those.
- Do NOT edit the spec (3e).
- Do NOT modify the deterministic writer's behavior — only demote its role.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/render_job_service.py` | Create | Does not exist |
| `cast-server/cast_server/services/requirements_render_service.py` | Modify | Has v2 deterministic writer + cache |
| `cast-server/cast_server/db/schema.sql` | Modify | No `render_jobs` table |
| `cast-server/cast_server/config.py` | Modify | No render-job constants |
| `cast-server/tests/test_render_job_service.py` | Create | Does not exist |
| `cast-server/tests/test_fr007_readonly_guard.py` | Modify | Exists; gains a maker-path sweep |
| `cast-server/tests/test_schema_migration.py` | Modify (if pattern requires) | Covers schema.sql changes |

## Detailed Steps

### Step 3c.1: `AgentRunner` seam

A tiny protocol `run_agent(agent_name, user_msg, *, timeout_s) -> str`. Production impl loads
`agents/<name>/<name>.md` + `config.yaml` and runs:

```
["claude", "-p", user_msg, "--append-system-prompt", agent_md, "--model", config.model, "--tools", ""]
```

(the `eval_render_checker.py` pattern). The runner **inlines all agent inputs** into `user_msg`
(source text, block inventory, classification, recipe vocabulary; toolkit + archetypes for HOW).
Tests inject fakes.

**Subprocess hygiene (plan-review A1 — pin to the `agent_service.py` production precedent):**
`env -u CLAUDECODE` + an explicit job-dir cwd + `_clean_child_env`-style hygiene. This is net-new
request-path subprocess code; a `claude -p` that inherits a parent session's `CLAUDECODE`/cwd can hang
or recurse. Do **not** under-specify env isolation.

### Step 3c.2: Pipeline stages as named functions (the 4a seam)

`run_what → gate_what (check_what_doc) → run_how → gate_html (check_html) → publish`.

On a `gate_what`/`gate_html` violation: **ONE structural retry** of the failing stage with
`GateReport.violations` appended to the prompt; a second violation → the **structural-exhaustion
branch** (see Step 3c.4 — this is the OVERRIDE path, NOT deterministic fallback).

4a will insert `run_checker → decide_quality` between `gate_html` and `publish`; the stage seam is
designed so 4a adds a stage, not a rewrite.

### Step 3c.3: Strict sentinel extraction → no-output classification (plan-review CQ2)

Extract content from the **first** `<!-- BEGIN RENDER -->` to the **first following**
`<!-- END RENDER -->`. The following all count as **no-output**:
- missing / mis-ordered / duplicate sentinels;
- a markdown-fenced (```` ```html ````) or chatty wrapper around the sentinels;
- unparseable WHAT front matter.

Anything **after** the first `END RENDER` (e.g. the reserved Phase-5 `GAPS-DETECTED` trailer) is
outside the window and **byte-ignored** — write no handling for it.

### Step 3c.4: Two terminal degradation branches (the OVERRIDE) — READ CAREFULLY

This is the **structural-violation OWNER OVERRIDE** (2026-06-12, supersedes the source plan's
Decisions-Made-Autonomously #4 and the older "structural exhaustion → deterministic fallback" text).
Encode **two distinct branches**:

**Branch 1 — literal no-output → deterministic fallback.** Crash, timeout, empty/unparseable output,
or sentinel-extraction failure (Step 3c.3) → call `rerender_requirements_html` (the v2 deterministic
path) and record `status=fallback` + the reason on the job row. This is FR-006's literal
"true no-output" branch.

**Branch 2 — structural-gate exhaustion → BEST ATTEMPT + flag (NOT the deterministic page).** When the
HOW agent **did** produce extractable HTML but it fails `gate_html` after the one structural retry,
serve the **best attempt** (in Phase 3, with no scoring, "best attempt" = the last extractable HTML
produced) and **flag it**:
- `status = flagged` (new terminal value);
- `error` = the `GateReport.violations` joined (the `structural_violation` reason, human/LLM-readable);
- **stamp the served artifact**: the AUTO-GENERATED header comment gains `served-by: structural_violation`
  beside `source-hash` (3d derives a reader-visible "needs review" badge from this stamp);
- publish the best-attempt HTML through the **same** atomic-write + header + cache envelope as a normal
  publish (it IS a published artifact, just flagged).

**Rationale (record it in the code/docstring):** serving the deterministic page here would *erase the
evidence* of a degraded render; the owner principle is **surface, don't suppress**. "Never SILENTLY
drop" still binds — the loss is surfaced via the `flagged` status + the `served-by` stamp + (in 3d)
the badge. The four richer 4a flag columns layer on top of this minimal signal later; Phase 3 does
**not** create them.

A clean maker render that passes `gate_html` publishes with `status=published` and (optionally)
`served-by: maker`.

### Step 3c.5: Publish + compare-and-publish

Wrap the chosen HTML (clean maker, flagged best-attempt, or deterministic fallback) in the same
`AUTO-GENERATED` header + `source-hash: <h>` (+ `served-by: <maker|structural_violation|fallback>`)
and `_atomic_write` it to `goals/{slug}/refined_requirements.html` — the v2 cache mechanism reused
byte-for-byte (FR-005/SC-005). **Compare-and-publish:** re-read the source hash at publish time; if it
moved, mark the job `superseded` and write nothing (the next view starts a fresh job).

### Step 3c.6: Single-flight + threading model + in-flight semaphore

- Module-level registry `dict[(slug, hash), Job]` guarded by a `threading.Lock`.
- One daemon `threading.Thread` per job running `subprocess.run(..., timeout=...)` synchronously
  (page routes are sync `def` in the threadpool — threads avoid event-loop interplay; the asyncio
  dispatcher/relay in `app.py` stays untouched).
- **Global in-flight ceiling (plan-review P1):** a bounded semaphore (config-driven, small default
  e.g. 3) over distinct `(slug, hash)` jobs caps concurrent maker subprocesses. Past the ceiling a new
  view serves the generating state and the job waits for a slot. This is a **resource-safety guard**
  (analogous to the owner-sanctioned anti-infinite-loop ceiling), **NOT** a cost/latency constraint
  (cost and model tier remain explicitly unconstrained).

### Step 3c.7: `render_jobs` table — INITIAL CREATE TABLE (revision a)

Add to `schema.sql`:

```
render_jobs(
  id, goal_slug, source_hash,
  status,        -- running | published | fallback | superseded | failed | flagged
  attempts, error,
  started_at, finished_at,
  heartbeat_at   -- revision a: in the INITIAL create table, NOT a later migration
)
```

- The per-job thread **writes `heartbeat_at` at EVERY stage boundary** (`run_what`, `gate_what`,
  `run_how`, `gate_html`, `publish`). Heartbeat = the staleness detector.
- **4a-2's migration later adds ONLY the four flag columns** — do NOT create
  `human_review`/`review_reason`/`published_attempt`/`published_score` here.
- Readiness is **never** derived from this table — the artifact's embedded `source-hash` is the single
  source of truth (3d).

### Step 3c.8: Lazy reaper (revision a — ceiling from the configured stage-timeout list)

- The reaper ceiling is a **function of the configured stage-timeout list** in `config.py` — NOT a
  magic constant and NOT a hardcoded `what_timeout + how_timeout` formula. Compute it as a generous
  multiple (≥2×) of the **sum of registered stage timeouts** (including the one structural retry).
  Because the ceiling reads the stage list, **4a/5 extend it by registering their stages — zero
  formula edits.**
- After a server restart the in-memory registry is empty, so the **ceiling is the real guard**: a
  `render_jobs` row `running` past the ceiling with a stale `heartbeat_at` and no live thread is marked
  `failed` by the next `resolve_render`/status call, and a fresh job starts.
- **The reaper MUST release the in-flight semaphore slot of a reaped orphan** (revision a) — otherwise
  a crashed-thread orphan permanently leaks a slot.

### Step 3c.9: Job artifact retention + stub short-circuit

- Each job writes `what.md`, `attempt-N.html`, and gate reports under
  `build/render-jobs/{slug}/{hash12}/` (new `RENDER_JOBS_DIR` in `config.py`; `build/` is a non-goal,
  non-CI-collected area) — **never** inside `goals/{slug}/` (FR-026 invariant intact).
- **Stub short-circuit:** resolve stub/missing sources BEFORE any job logic — `is_stub(parsed)` → the
  deterministic prompt-to-begin render exactly as today (US1 Scenario 2 unchanged); the maker is never
  invoked for a stub.

### Step 3c.10: `config.py` additions

`RENDER_JOBS_DIR`; the **stage-timeout list** (registers `run_what`/`run_how` worst-case timeouts read
from each agent's `config.yaml`, plus fast gate/publish stages); `RENDER_REAPER_CEILING_MULTIPLE`
(≥2); `RENDER_MAX_INFLIGHT` (small default, e.g. 3). Disjoint from 4a's `QUALITY_*` and 5's
`GAPFILL_*` keys.

## Verification

### Automated Tests (permanent)
`pytest cast-server/tests/test_render_job_service.py` green, with an **injected fake runner**
(no LLM in default CI):
- happy path → publishes (`status=published`);
- **gate-violation → one feedback retry → second violation → BEST ATTEMPT published + `status=flagged`
  + `served-by: structural_violation` stamp + reason recorded** (the OVERRIDE path — assert it does
  NOT serve the deterministic page);
- subprocess crash / timeout / empty-output / sentinel-extraction failure → **deterministic fallback**
  published + `status=fallback` + reason (the literal no-output branch);
- **T2 (plan-review — deterministic, not sleep-timed):** the fake runner blocks on an injected latch
  the test releases; two concurrent requests for the same `(slug, hash)` start exactly one job; a
  source edited mid-job → compare-and-publish discards (`status=superseded`), no stale publish — both
  asserted on a controlled interleaving;
- **T3 reaper (plan-review):** write a stale `running` row (old `heartbeat_at`, no live thread) past
  the derived ceiling directly; the next `resolve_render`/status call marks it `failed`, **releases its
  semaphore slot**, and a fresh job starts.

Plus:
- `test_fr007_readonly_guard.py` maker sweep: a full fake-runner pipeline run (incl. the `flagged` and
  `fallback` branches) leaves the canonical `.collab.md` **byte-identical**.
- Existing `test_render_route_and_service.py` (service half) stays green — the deterministic writer's
  behavior is unchanged, only its role demoted.
- `test_schema_migration.py` covers the `render_jobs` CREATE TABLE (incl. `heartbeat_at`).

### Validation Scripts (temporary)
- A one-off fake-runner driver printing the job row + served-artifact header for each branch
  (published / flagged / fallback / superseded / failed). Discardable.

### Manual Checks
- Grep `render_job_service.py` for `env -u CLAUDECODE` / clean-env usage. Confirm `--tools ""` on the
  production runner. Confirm the reaper releases the semaphore on reap. Confirm no
  `human_review`/`review_reason`/`published_attempt`/`published_score` columns were created.

### Success Criteria
- [ ] Maker is the primary branch; deterministic renderer demoted to fallback (role-only change).
- [ ] **OVERRIDE encoded:** structural-gate exhaustion → `status=flagged` best-attempt + `served-by:
      structural_violation` stamp; deterministic fallback fires **only** on literal no-output.
- [ ] `render_jobs` CREATE TABLE includes `heartbeat_at`; thread writes it at every stage boundary.
- [ ] Reaper ceiling derives from the configured stage-timeout list AND the reaper releases the
      semaphore slot of a reaped orphan.
- [ ] In-flight semaphore caps concurrent maker subprocesses (resource-safety, not a cost cap).
- [ ] `--tools ""` + `env -u CLAUDECODE` + clean cwd; canonical `.collab.md` never written
      (readonly-guard sweep green).
- [ ] T2 (latch-deterministic) + T3 (reaper) + all branch tests green; FR-026 invariant intact
      (artifacts under `build/`).
- [ ] No 4a flag columns created.

## Execution Notes

- **The OVERRIDE is the single most important deviation from the source plan.** The source plan
  (Decisions-Made-Autonomously #4 + Key Risks) still says "structural exhaustion → deterministic
  fallback"; that is **superseded** by the owner override recorded in
  `decisions-so-far.md` (lines 104, 107) and confirmed for this split. Implement Branch 2 (flagged
  best-attempt), not the old fallback-on-structural-exhaustion.
- "Best attempt" in Phase 3 = the last extractable HTML (no scoring yet). 4a introduces scoring and the
  "best-scoring valid attempt" refinement; do not anticipate it.
- Zero silent failures: every terminal state (`published`, `flagged`, `fallback`, `superseded`,
  `failed`) is a recorded row with a reason.
- **Spec consistency:** US2/FR-003 (synchronous regen) and the FR-006 fallback wording change here —
  flag for **3e's** `/cast-update-spec`; do not edit the spec in 3c.
