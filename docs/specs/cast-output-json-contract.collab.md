---
feature: cast-output-json-contract
module: cast-runtime
linked_files:
  - skills/claude-code/cast-child-delegation/SKILL.md
  - docs/specs/cast-delegation-contract.collab.md
  - tests/fixtures/synthetic_child.py
  - agents/cast-review-code/cast-review-code.md
  - agents/cast-subphase-runner/cast-subphase-runner.md
last_verified: "2026-04-30"
---

# Cast Output JSON Contract — Spec

> One-line: contract-v2 schema for the terminal-output JSON file every cast-* agent writes at `<goal_dir>/.agent-run_<RUN_ID>.output.json`.

**Scope:** field-by-field schema, allowed status set, artifacts[] item shape, per-field examples, per-agent extension placeholder.
**Version:** 1 | **Updated:** 2026-04-30 — Initial spec authored as part of Phase 3a sub-phase 1 (B5 file-based polling foundation), per Q#22.
**Status:** Draft

---

## Intent

Every cast-* agent writes a single JSON file at terminal close-out. The parent agent reads this file to learn what happened. The contract version locks the shape so parents and children may evolve independently.

This spec defines the v2 shape. Cast-* agent prompts MUST reference this spec by path instead of inlining the schema; that way, schema changes (additive only at v2) propagate without combinatorial prompt edits.

The runtime delegation/poll/atomic-write semantics live in `docs/specs/cast-delegation-contract.collab.md` — read both specs together when working on parent or child mechanics.

## Behaviors

### Overview

- **Canonical path**: `<goal_dir>/.agent-run_<RUN_ID>.output.json`. See `cast-delegation-contract.collab.md` for path resolution and atomic-write rules.
- **One file per child run**: each dispatched child writes exactly one terminal output file. No append, no rotation.
- **Contract version**: this spec defines `contract_version: "2"`. v1 is legacy (pre-rebrand TaskOS); cast-* agents emit v2 only.

### Field-by-Field Schema

| Field | Type | Required | Semantics |
|-------|------|----------|-----------|
| `contract_version` | string | yes | Literal `"2"`. Parents reject non-`"2"` files as malformed. |
| `agent_name` | string | yes | The child agent that wrote this file (e.g., `"cast-detailed-plan"`). Must match the dispatched agent name. |
| `task_title` | string | yes | One-line title of the task. Empty string allowed when the dispatch had no specific task. |
| `status` | string | yes | One of `"completed"`, `"partial"`, `"failed"`. See "Status Allowed Values" below. |
| `summary` | string | yes | One-paragraph narrative of what the child accomplished. Reader-facing; do not include stack traces here. |
| `artifacts` | array | yes | List of artifact objects produced by the run. May be empty. See "Artifacts[] Item Schema". |
| `errors` | array | yes | List of error strings or structured error objects. Empty array on success. |
| `next_steps` | array | yes | Suggested follow-up actions for the operator or the parent agent. Strings at v1; typed shape lands in sp4d. |
| `human_action_needed` | boolean | yes | `true` when the run can't fully close without human input. |
| `human_action_items` | array | yes | List of strings describing what exactly a human must do. Empty when `human_action_needed=false`. |
| `started_at` | string (ISO-8601) | yes | When the child started. UTC, Z-suffixed. |
| `completed_at` | string (ISO-8601) | yes | When the child wrote this file. UTC, Z-suffixed. |

> Edge: extra unknown fields MAY appear (forwards-compatible additive evolution per "Per-Agent Output Extensions"). Parents MUST ignore unknown fields rather than rejecting the file.

### Status Allowed Values

| Status | Meaning |
|--------|---------|
| `completed` | All requested work done successfully. |
| `partial` | Some work done, but not everything (`summary` explains). |
| `failed` | Could not accomplish the task (`errors[]` explains). |

> Edge: any other value (e.g., `"running"`, `"idle"`, `"pending"`) appearing in the file is a malformed-output bug; parent treats the file as `failed` with a parse error.

### Artifacts[] Item Schema

Each entry is an object with the following shape:

| Field | Type | Required | Semantics |
|-------|------|----------|-----------|
| `path` | string | yes | Path relative to goal directory (the same `<goal_dir>` referenced in the canonical path). |
| `type` | string | yes | One of: `research`, `playbook`, `plan`, `code`, `data`. |
| `description` | string | yes | One sentence describing what's in the file. |

> Edge: artifacts MAY include directories (path is the directory). Type `data` covers structured outputs (JSON / YAML / SQLite); `code` covers source files; `plan` covers plan documents; `playbook` covers actionable how-to docs; `research` covers raw research notes.

### Per-Agent Output Extensions

> Additive per-agent fields land here without restructuring the rest of the spec. Parents
> ignore unknown fields per the forwards-compatibility rule.

#### cast-review-code

Each review-issue object emitted by cast-review-code carries an additional field:

| Field | Type | Allowed Values | Semantics |
|-------|------|----------------|-----------|
| `confidence` | string | `high \| medium \| low` | Tagging guidance: `high` for mechanical fixes (auto-applicable); `medium`/`low` for judgment-required issues (recorded to followup, not auto-applied). |

Consumers (notably cast-subphase-runner via B4) gate auto-apply on `confidence: high` AND
Edit-tool-applicable patches AND path under `goal_dir`/`docs/` tree. Anything else (file
creation, multi-line refactor, out-of-tree path, medium/low confidence) is recorded to
`<sub_phase_file>.followup.md` for human review and the runner continues without blocking.

Example review-issue object inside an `artifacts[].metadata.issues[]` array:

```json
{
  "file": "src/foo.py",
  "line": 12,
  "summary": "Trailing newline missing",
  "suggested_fix": "Append \\n to end of file",
  "confidence": "high"
}
```

#### Future extensions

- *(future)* sp4c: open-question tagging on `human_action_items[]` strings (`[EXTERNAL]`, `[USER-DEFERRED]` prefixes). Tag definitions also documented in `cast-delegation-contract.collab.md`.
- *(future)* sp4d: typed `next_steps` array — each entry becomes `{command, rationale, artifact_anchor}`. Cast-* agents that already populate `next_steps` as strings at v1 are forwards-compatible; the migration converts strings into typed objects.

### Per-Field Examples

A complete v2 example, emitted by `cast-web-researcher`:

```json
{
  "contract_version": "2",
  "agent_name": "cast-web-researcher",
  "task_title": "Research candidate frameworks for declarative agent runtimes",
  "status": "completed",
  "summary": "Researched 5 frameworks (LangGraph, CrewAI, Autogen, Letta, Mastra) across release history, license posture, and observability story. Verified all data current as of 2026-04-30.",
  "artifacts": [
    {
      "path": "exploration/frameworks_compared.md",
      "type": "research",
      "description": "5 frameworks side-by-side: release history, license, observability, runtime model"
    },
    {
      "path": "exploration/data/release_history.json",
      "type": "data",
      "description": "Per-framework release_history array with version + date for the last 24 months"
    }
  ],
  "errors": [],
  "next_steps": ["Pick the framework that satisfies declarative + open-license + Otel-native"],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "2026-04-30T10:30:00Z",
  "completed_at": "2026-04-30T11:15:00Z"
}
```

A `partial` example, emitted by `cast-batch-enrich` when only some companies were enriched before timeout:

```json
{
  "contract_version": "2",
  "agent_name": "cast-batch-enrich",
  "task_title": "Enrich 800 watching companies",
  "status": "partial",
  "summary": "Enriched 612 of 800 companies; remaining 188 timed out after the per-run budget. Re-dispatch with `--resume` to continue.",
  "artifacts": [
    {
      "path": "data/enrichment_run_<run_id>.jsonl",
      "type": "data",
      "description": "Per-company enrichment record (612 rows)"
    }
  ],
  "errors": [],
  "next_steps": ["Re-dispatch cast-batch-enrich with --resume"],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "2026-04-30T10:00:00Z",
  "completed_at": "2026-04-30T10:45:12Z"
}
```

A `failed` example with `human_action_needed`, emitted via parent's idle-timeout fallback:

```json
{
  "contract_version": "2",
  "agent_name": "cast-preso-orchestrator",
  "task_title": "Run Stage 3 for 8 slides",
  "status": "failed",
  "summary": "Child idle for 300s; output file mtime did not change.",
  "artifacts": [],
  "errors": ["child idle for 300s; check goal_dir/.agent-run_<run_id>.output.json"],
  "next_steps": ["Inspect tmux pane agent-<run_id>; recheck or cancel via cast-runs"],
  "human_action_needed": true,
  "human_action_items": ["Verify child status; either recheck or cancel the run"],
  "started_at": "2026-04-30T11:00:00Z",
  "completed_at": "2026-04-30T11:05:00Z"
}
```

## Decisions

### v2 baseline frozen at sp1 — 2026-04-30 (Q#22)
**Chose:** create a dedicated `cast-output-json-contract.collab.md` spec at sp1.
**Over:** continuing to inline the schema across cast-* agent prompts.
**Because:** the schema was duplicated in ~30 agents and drifting (one agent's `artifacts[]` had `name` instead of `path`). Centralizing the canonical text removes a class of merge conflicts and lets per-agent extensions land additively.

### Status set frozen at three values — 2026-04-30
**Chose:** `completed | partial | failed` only.
**Over:** richer states like `cancelled`, `escalated`, or `orphaned`.
**Because:** parents need a finite, total decision tree. Cancellation is observable via cast-server HTTP API; escalation is encoded as `human_action_needed=true` with `failed` status; orphan recovery is out of scope for v2.

### artifacts[].type closed enum — 2026-04-30
**Chose:** `research | playbook | plan | code | data` as the closed type set.
**Over:** free-form type strings.
**Because:** parents and viewers (e.g., a future TaskOS UI) want to render artifacts by type; an open enum makes that brittle. Additive new types require a spec bump.

### cast-review-code per-issue confidence is additive — 2026-04-30 (Q#20, sp3d)
**Chose:** add a `confidence: high|medium|low` field to each review-issue object.
**Over:** restructuring the review-output schema or carrying the gate decision on the parent side.
**Because:** the producer (cast-review-code) is the only party with enough context to know how mechanical a fix is; centralizing the tag at emit time means consumers (cast-subphase-runner B4) can gate auto-apply on a single field. The field is additive, so existing review tooling that doesn't read it stays compatible.

## Not Included

- v1 (pre-rebrand TaskOS) schema — deprecated. v1 fixtures may exist in TaskOS-era goal dirs but cast-* agents emit only v2.
- Open-question tagging on `human_action_items[]` — deferred to sp4c.
- Typed `next_steps` shape — deferred to sp4d.
- A JSON Schema document validating this contract — deferred (current verification is by spec text + per-agent fixture parsing).
