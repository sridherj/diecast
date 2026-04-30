---
feature: cast-delegation-contract
module: cast-runtime
linked_files:
  - skills/claude-code/cast-child-delegation/SKILL.md
  - cast-server/
  - tests/test_b5_file_polling.py
  - tests/test_b5_atomic_write.py
  - tests/fixtures/synthetic_child.py
last_verified: "2026-04-30"
---

# Cast Parent-Child Delegation Contract — Spec

> One-line: file-based parent-child agent delegation contract — what every cast-* agent must obey when dispatching, polling, and consuming a child's output.

**Scope:** dispatch precondition (external_project_dir), output file naming, contract-v2 schema reference, terminal status set, polling backoff, idle timeout, heartbeat-by-mtime, atomic write, RUN_ID-scoped path validation, test hooks, edge cases, per-agent extension placeholder, cross-phase authorship, worked example.
**Version:** 2 | **Updated:** 2026-05-01 — Dispatch Precondition section added (server-side enforcement of usable `external_project_dir` at trigger time, structured 422 error contract). v1 (2026-04-30): Initial spec authored as part of Phase 3a sub-phase 1 (B5 file-based polling foundation); Open-Question Tags (US13) appended in sp4c; Typed `next_steps` Array (US14) appended in sp4d.
**Status:** Draft

---

## Intent

The Diecast runtime is a parent-child agent system. Every cast-* parent agent dispatches one or more children and consumes their terminal output. The output **file on disk** is canonical; cast-server is a read-through HTTP API that observes the same files and exposes them over the network — it never writes them.

This spec is the single source of truth for the file-based delegation contract. Anything that diverges from this spec is a bug. The runtime encoding lives at `skills/claude-code/cast-child-delegation/SKILL.md`; if the skill and this spec ever diverge, the spec is canonical.

## Behaviors

### Dispatch Precondition: external_project_dir

This is a first-class subsection because it gates every dispatch path. Without it, runs were enqueued against goals with no usable working directory and failed at launch with confusing terminal-readiness timeouts. The precondition surfaces the real problem ("this goal has no project directory") at the API boundary, not as a launcher symptom.

- **Server enforces at trigger time**: `POST /api/agents/{name}/trigger` calls `_validate_dispatch_preconditions(goal_slug)` before enqueueing. The goal MUST have a non-empty `external_project_dir` whose configured path resolves to a directory on disk. Same rule applies to scheduled runs (validated at enqueue, not at dispatch).
- **Both failure modes share one error code**: unset `external_project_dir` and set-but-path-missing both raise `MissingExternalProjectDirError` and map to `error_code: "missing_external_project_dir"`. The `configured_path` field on the response disambiguates ("never set" vs. "set to <path>").
- **Structured 422 response**: parents reading the route response can branch on `error_code` without parsing prose. Body shape:

  ```json
  {
    "error_code": "missing_external_project_dir",
    "goal_slug": "<slug>",
    "configured_path": null | "<path that doesn't exist>",
    "detail": "<human-readable message>",
    "hint": "Set external_project_dir on the goal before dispatching. PATCH /api/goals/{slug}/config (form field external_project_dir=<absolute path>)."
  }
  ```

- **Defense-in-depth at launch**: `_launch_agent` re-validates the same precondition. A run that bypasses the trigger contract (direct DB insert, scheduled enqueue under a stale config) raises `MissingExternalProjectDirError` and is marked `failed` with the error in `error_message`. The launcher MUST NOT silently fall back to a "default" working directory.
- **Client-side preflight (canonical)**: `cast-child-delegation` Section 0 GETs the goal config before dispatch and prompts the user via `AskUserQuestion` (cwd / type path / cancel) when `external_project_dir` is missing or stale. On user choice it `PATCH /api/goals/{slug}/config` and proceeds. The 422 path is the fallback; the preflight prompt is the happy path.

> Edge: `invoke_agent` (CLI `/invoke` route) is intentionally NOT subject to this precondition today — it serves ad-hoc, often goal-less, diagnostic invocations. Promoting `/invoke` to the same precondition is a separate concern.

### Overview & Boundary

- **File is canonical**: The child's terminal output is a JSON file at `<goal_dir>/.agent-run_<RUN_ID>.output.json`. Parent agents poll this file for terminal status. cast-server is a read-through HTTP API — it observes the file but never writes it.
- **HTTP API is best-effort, not authoritative**: When cast-server is reachable, parent agents MAY consult `GET /api/agents/jobs/<run_id>` for status. When unreachable (or `CAST_DISABLE_SERVER=1`), the file path alone is sufficient to drive parent state.

> Edge: parent must be able to terminate the polling loop on file evidence alone; HTTP confirmation is never required.

### Output File Naming

- **Path format**: `<goal_dir>/.agent-run_<RUN_ID>.output.json` (literal `agent-run_` prefix; literal `.output.json` suffix).
- **Forbidden renames**: future versions of this contract MUST NOT rename this file. Renaming would break the v1.x upgrade path for in-flight goal directories.

> Edge: `<goal_dir>` resolves to the goal directory the parent passed via `delegation_context.output.output_dir`. If unset, parent's own `goal_dir` is used.

### Contract v2 Schema

- **Schema is a separate spec**: see `docs/specs/cast-output-json-contract.collab.md` for field-by-field semantics, allowed values, and per-field examples. Do not duplicate the schema here.

### Terminal Status Set

- **Allowed terminal values**: `completed`, `partial`, `failed`. No other terminal values are recognized.
- **Non-terminal observed values**: `pending`, `running`, `idle` MAY appear in HTTP API responses but MUST NOT appear in the output JSON. If the parent reads any non-terminal value from the file, it MUST treat that file as malformed (`failed` with a parse error).

| Status | Meaning | Parent Action |
|--------|---------|---------------|
| `completed` | All requested work done | Read artifacts, verify, accept |
| `partial` | Some work done, not all | Read summary + errors, decide retry / fix / accept |
| `failed` | Could not accomplish task | Read errors[], decide retry / escalate |

### Polling Backoff Schedule

- **Default ladder (seconds)**: `1, 2, 5, 10, 30`. After the ladder exhausts, parent polls steady at 30s.
- **CI override**: parent reads `CAST_DELEGATION_BACKOFF_OVERRIDE` (CSV like `10ms,20ms,50ms`). When set, this REPLACES the default ladder entirely. Final value of the CSV is the steady-state interval.
- **30s ceiling is intentional**: fast-completing children may take up to ~18s extra to be detected (worst case). This is acceptable; sub-second polling would over-pressure cast-server when many parents poll concurrently.

### Idle Timeout & Heartbeat by mtime

This is a first-class subsection because long-running children (e.g., `cast-preso-orchestrator` with multi-slide loops) routinely exceed any naive single timeout. Without an mtime-based heartbeat, parents would either kill healthy long-running work or wait forever for crashed children.

- **Default idle timeout**: `300` seconds (5 minutes).
- **Heartbeat reset on mtime change**: parent stats the output file each poll; whenever `mtime` differs from the previously observed `mtime`, the idle countdown resets. Children signal liveness either by writing progressive partial JSON or by `os.utime`-touching the file.
- **Heartbeat cadence rule**: long-running children MUST touch the output file or write progressive partial JSON at least every `idle_timeout / 2` seconds. Default cadence is therefore at most ~150s between mtime updates.
- **CI override**: `CAST_DELEGATION_IDLE_TIMEOUT_SECONDS=<int>` shortens the timeout for tests.
- **Per-agent override**: parent MAY pass a custom timeout via `delegation_context.idle_timeout_seconds`. If both env-var and delegation-context overrides are set, delegation context wins.
- **Timeout result**: when the countdown elapses with no mtime change, parent returns a synthetic terminal-state result with `status="failed"`, `human_action_needed=True`, and an `errors[]` entry naming the path and elapsed seconds.

> Edge: a child that never writes the output file at all hits the same idle-timeout path; the synthetic failure response is identical.

### Atomic Write Contract

- **Tmp-and-rename**: child MUST write to `<goal_dir>/.agent-run_<RUN_ID>.output.json.tmp`, fsync, then `os.rename` to the final name. The rename is atomic on POSIX local filesystems.
- **Parent never reads `.tmp`**: parent's poll loop reads only the final path. Never glob `*.tmp`. This guarantees the parent never observes a partially-written JSON document.
- **Single-shot finalization**: the rename is one-way. Once the final file exists, it MUST NOT be overwritten in-place by the same child. (Re-runs land under a new RUN_ID.)

> Edge: a child that crashes mid-write leaves a `.tmp` file. Parent ignores it. Cleanup is a future concern (sp-cleanup) — orphan `.tmp` files are harmless.

### RUN_ID-Scoped Path Validation

- **Parent reads only its own RUN_ID file**: parent constructs the output path from the RUN_ID it received from dispatch and reads only that exact path. Glob-style reads are forbidden.
- **Cross-RUN_ID write protection**: a child MUST NOT write to a file whose RUN_ID does not match the one in its own delegation context. cast-server enforces this at write time when reachable; the spec mandates the same discipline file-side.

> Edge: residual file from a prior crashed run with a different RUN_ID is irrelevant — the new run targets a new path.

### Test Hooks (env-var contract)

These are first-class because B5's CI gate depends on env-var simulation; without these hooks, tests would either run for minutes per case or rely on real signal-killing the cast-server process.

- **`CAST_DELEGATION_IDLE_TIMEOUT_SECONDS`**: integer, overrides default 300s timeout. Tests use `4`–`30`.
- **`CAST_DELEGATION_BACKOFF_OVERRIDE`**: CSV ladder. Tests use `10ms,20ms,50ms` etc. Suffixes `ms` and `s` recognized; bare numbers default to seconds.
- **`CAST_DISABLE_SERVER`**: set to `1` to skip HTTP-API dispatch attempts entirely. Parent goes straight to the file-based dispatch + poll path. Used by per-PR CI; nightly CI uses real `pkill -f cast-server` instead (see `.github/workflows/nightly.yml`).

### Edge Cases

- **Residual file from prior crash**: a fresh dispatch with a new RUN_ID writes to a different path; the residual is irrelevant. Parent never reads files outside its own RUN_ID scope. Cleanup is out of scope here.
- **Parent crash mid-poll**: child output may complete and persist on disk while parent has died. The file is harmless — operators can inspect it manually. A future `cast-runs adopt` flow may reattach.
- **Malformed JSON from child**: parent treats this as `status=failed` with the JSON parse error captured in `errors[]`. No silent retry. Idle-timeout logic does not engage because the file does exist.
- **Non-terminal status in file**: parent treats as malformed (same handling as JSON parse error).
- **mtime racing rename**: on most filesystems `os.rename` updates mtime to "now"; parent observes the rename as a heartbeat tick. This is acceptable; the heartbeat is a best-effort liveness signal, not a strict ordering proof.

### Per-Agent Output Extensions

> **Placeholder subsection.** Empty stub at v1. Later sub-phases append per-agent additive fields here without restructuring this spec.

- *(future)* sp3d: cast-review-code emits `confidence: high|medium|low` per review issue; auto-apply rules: `high` → apply, `medium`/`low` → write to `<sub-phase>.followup.md`.
- *(landed)* sp4c: open-question tags `[EXTERNAL]` and `[USER-DEFERRED]` -- see "Open-Question Tags (US13)" below.
- *(landed)* sp4d: typed `next_steps` shape `{command, rationale, artifact_anchor}` -- see "Typed `next_steps` Array (US14)" below.

#### Open-Question Tags (US13)

When an artifact carries a trailing `Open Questions` section at terminal close-out, every item
in that section MUST be tagged with one of the following:

| Tag | Meaning | Reason field required |
|-----|---------|----------------------|
| `[EXTERNAL]` | Requires availability probe, third-party decision, or hardware in user's hand | Yes -- describe what external dependency blocks resolution |
| `[USER-DEFERRED]` | User explicitly chose to defer ("leave it open", "skip for now") | Yes -- quote or paraphrase the deferral |

Format: `- **[TAG]** <one-line item>. Reason: <one-line reason>.`

Untagged items in `Open Questions` violate the close-out discipline (US13). Consumers
(cast-server, downstream agents) treat untagged items as broken contract.

**Schema impact on `.agent-run_<RUN_ID>.output.json`:**

- `human_action_needed: true` SHOULD be set when the artifact has any `[EXTERNAL]` items.
- `human_action_items[]` SHOULD list each `[EXTERNAL]` item verbatim.
- `[USER-DEFERRED]` items are NOT lifted to `human_action_items[]` -- they're explicit deferrals.

**Resolution discipline:** before emitting any trailing `Open Questions` section, the agent
MUST first attempt to resolve each in-conversation ambiguity via `cast-interactive-questions`.
Only items that are genuinely unresolvable through interactive Q&A are eligible for the
`Open Questions` section, and those MUST carry a tag. The runtime enforcement of this
discipline lives in `skills/claude-code/cast-interactive-questions/SKILL.md`
("Close-out Discipline (US13)").

#### Typed `next_steps` Array (US14)

The `next_steps` field in `.agent-run_<RUN_ID>.output.json` is a typed array (was: string array).
Each element has shape:

| Field | Type | Required | Semantics |
|-------|------|----------|-----------|
| `command` | string | Yes | A `/cast-*` command or a shell command. NEVER auto-executed by cast-server UI. |
| `rationale` | string | Yes | One-line reason grounded in the artifact/state just produced. |
| `artifact_anchor` | string \| null | Yes | File path most relevant to the suggestion, or `null`. |

**Constraints:**
- 0–3 entries (1–3 is the encouraged shape; 0 allowed when there's truly no useful next step).
- No self-loops: the producing agent's own command MUST NOT appear in its `next_steps`.
- Validated against `tests/fixtures/next_steps.schema.json`.

**Render rule (per-agent `proactive` flag in `config.yaml`):**
- `proactive: true` (chain commands) → emit a `Suggested next:` block with all 1–3 entries
  at terminal close-out.
- `proactive: false` (terminal commands) → pick the single best entry and ask via
  `cast-interactive-questions`.

Resolution order: `proactive_overrides[<agent>] → per-agent default → proactive_global → false`.
Resolver helper: `agents/_shared/proactive.py:resolve_proactive()`.

**Parent-child suggestion:** when an agent dispatched any child run, include
`{"command": "/cast-runs --recent", "rationale": "Inspect dispatched runs", "artifact_anchor": null}`
as one of the 1–3 entries.

**Backwards compatibility:** legacy string-shape entries are bulk-migrated via
`bin/migrate-next-steps-shape.py`. After migration, every cast-* agent emits the typed shape.

**Security note (forwarded to Phase 3b):** `<shell command>` entries are LLM-generated.
The cast-server UI MUST NOT auto-execute them — render only, user clicks-to-confirm.

### Cross-Phase Authorship

- **Phase 3a authorship**: this spec, `cast-output-json-contract.collab.md`, `db/schema.sql` schema flips, and `taskos/src/taskos/models/task.py` enum changes.
- **Phase 3b consumption**: `cast-server` HTTP layer consumes the file via `task_service` only; never reads the JSON directly bypassing the service.
- **Cast-* agent reads**: cast-* agents reference this spec by path (and the output-json spec) instead of reverse-engineering schema details from prompt fragments.

### Worked Example: cast-detailed-plan → cast-plan-review auto-trigger

This is the chain `sp3c` automates. It is the canonical reference for parents that auto-trigger a single-step downstream review.

1. `cast-detailed-plan` finishes its plan synthesis and writes its own output JSON.
2. Before exit, `cast-detailed-plan` invokes `cast-child-delegation` to dispatch `cast-plan-review` with the plan path as input artifact and `parent_run_id` set to its own run.
3. Dispatch attempts HTTP first; falls back to file-only path if `CAST_DISABLE_SERVER=1` is set.
4. `cast-detailed-plan` polls `<goal_dir>/.agent-run_<child_run_id>.output.json` using the backoff ladder.
5. `cast-plan-review` writes its terminal output via tmp+rename.
6. `cast-detailed-plan` reads the terminal status; if `partial` or `failed`, it appends an `[EXTERNAL]`-tagged item to its own `human_action_items[]` (per US13) and re-emits its output. If `completed`, it links the child's review path in its own `next_steps[]` (per US14, once typed shape lands).

> Edge: if the child stays silent past idle timeout, parent records `human_action_needed=True` with the path of the orphaned output file so the operator can inspect manually.

## Decisions

### File is Canonical, HTTP API is Read-Through — 2026-04-30
**Chose:** file-based output as the authoritative signal; cast-server reads the same file when answering HTTP status calls.
**Over:** HTTP-only or DB-only authoritative signal.
**Because:** delegation must work even when cast-server is stopped, crashed, or being restarted (Phase 3b reload, OS reboot mid-run). Files survive cast-server lifecycles. Any model that requires cast-server to be running to confirm terminal state would couple every parent agent to server uptime.

### Heartbeat by mtime, not heartbeat field — 2026-04-30
**Chose:** liveness signaled by output-file mtime (touch or write).
**Over:** dedicated heartbeat field in the JSON or separate `<RUN_ID>.heartbeat` file.
**Because:** mtime is free (the kernel maintains it on every write), requires no schema additions, and naturally rides along with progressive partial writes that long-running children already do.

### B5 test density: 4 dedicated tests — 2026-04-30
**Chose:** happy / idle-timeout / heartbeat / atomic-write as separate tests.
**Over:** one combined polling test.
**Because:** each branch of the polling state machine has a different failure mode (race, leak, false negative, false positive). One combined test would obscure which branch broke.

### CI: env-var sim per-run, real kill nightly — 2026-04-30 (Q#21)
**Chose:** `CAST_DISABLE_SERVER=1` for per-PR CI; nightly CI runs `pkill -f cast-server` and re-runs the same suite.
**Over:** real-kill on every PR.
**Because:** real-kill is slow and flaky (race with Actions runner shutdown). Env-var simulation is fast and deterministic; nightly real-kill catches divergence between simulation and real-environment behavior at-cadence.

## Not Included

- Schema migrations to `task.py` or `db/schema.sql` (sp4b).
- `confidence` field addition to cast-review-code (sp3d).
- cast-server-side code (Phase 3b).
- Cleanup of orphan `.tmp` files (separate sub-phase, not yet planned).
- Migrating all ~30 cast-* agents to reference the output-JSON spec — sp1 covers 3 agents; the rest follow incrementally as agents are next touched.
