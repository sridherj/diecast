# `cast-server` Agent Runs API

> Phase 3b sp5 — HTTP read-through over the file-canonical run state.
>
> **Contract source of truth:** `docs/specs/cast-delegation-contract.collab.md`
> (Phase 3a sp1) defines what the canonical
> `.agent-run_<RUN_ID>.output.json` file means and what it must contain. This
> document covers HTTP-specific concerns only — route shape, response merge
> rules, status codes. When the contract and this doc disagree, the contract
> wins.
>
> **Caching disclaimer:** The canonical file is read on every request; there
> is no caching. The canonical-file rule supersedes any future caching layer
> — caches must be invalidated by file mtime or skipped entirely.

## Overview

`cast-server` persists a row to its SQLite DB whenever it dispatches an agent
run. The dispatched child writes its final state to a per-run file:

```
<goal_dir>/.agent-run_<RUN_ID>.output.json
```

That file is the **canonical** state of the run. The DB row carries
information the file does not (e.g. `created_at`, `parent_run_id`,
`worktree_path`) and serves as a fallback while the run is in flight or if
the child never wrote a file.

`GET /api/agents/jobs/{run_id}` is read-through: it merges the file (when
present) over the DB row and reports which source supplied the bulk of the
fields via a `source` discriminator.

## Routes

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/agents/{name}/trigger` | Dispatch an agent run. Returns `{run_id, status}`. |
| `GET`  | `/api/agents/jobs/{run_id}` | Read run state (file-canonical, see precedence below). |
| `POST` | `/api/agents/jobs/{run_id}/recheck` | Re-evaluate a failed run; recover if the agent finished after timeout. |
| `POST` | `/api/agents/runs/{run_id}/continue` | Send a follow-up message to an idle agent's tmux session. |
| `POST` | `/api/agents/runs/{run_id}/cancel` | Cancel an active run. |
| `POST` | `/api/agents/runs/{run_id}/complete` | Finalize a CLI-registered run; cleans up tmux. |
| `POST` | `/api/agents/runs/{run_id}/fail` | Manually mark a run as failed. |
| `DELETE` | `/api/agents/runs/{run_id}` | Delete a terminal run. |
| `GET`  | `/api/agents/runs` | List runs (filter via `?status=`, paginated). |
| `GET`  | `/api/agents/jobs/{run_id}?include=children` | JSON: run state + descendant tree (rollups attached). Replaces the removed `GET /api/agents/runs/{run_id}/children` fragment endpoint. |
| `POST` | `/api/agents/{name}/invoke` | CLI invoke — creates run, returns prompt for tmux launch. |
| `POST` | `/api/agents/error-memories/{memory_id}/resolve` | Mark an error memory resolved. |

### `?include=children` on `GET /api/agents/jobs/{run_id}`

Optional query parameter that augments the merged run JSON with a `children`
array. Each entry is a descendant run shaped by `get_run_with_rollups` —
depth-capped, with rollup fields (`descendant_count`, `failed_descendant_count`,
`rework_count`, `status_rollup`, `total_cost_usd`, `ctx_class`,
`wall_duration_seconds`) computed; nested children appear under their
respective entries' `children` arrays.

**Removed in this release:** `GET /api/agents/runs/{run_id}/children` (HTML
fragment) and `GET /api/agents/runs/{run_id}/row` (HTML fragment). The threaded
`/runs` page no longer renders per-row HTML for those callers; live updates
flow through `GET /api/agents/runs/{run_id}/status_cells` and the descendant
tree is exposed as JSON via `?include=children`.

## Precedence rule for `GET /api/agents/jobs/{run_id}`

Given a `run_id`, the server resolves the response in this order:

1. **DB row missing → 404.** The HTTP API serves only runs that
   `cast-server` itself dispatched. See *Server-dispatched-only carve-out*
   below.
2. **DB row present, file missing →** return DB row, set `"source": "db"`.
3. **DB row present, file present and parseable →** merge field-by-field with
   the file taking precedence; set `"source": "file"`. The DB fills any keys
   the file omits (`created_at`, `parent_run_id`, `worktree_path`,
   `agent_name`, etc.).
4. **DB row present, file exists but is malformed JSON →** return HTTP 502
   with body:
   ```json
   {
     "run_id": "<id>",
     "source": "file_invalid",
     "error": "Malformed output file at <path>: <parser message>",
     "db_state": { ... DB row ... }
   }
   ```
   Distinguishing malformed from missing matters: a missing file means the
   child has not (yet) written, but a malformed file means the child wrote
   something the contract does not permit and a human needs to look. The
   server does not silently fall back to DB state in this case.

### Server-dispatched-only carve-out (Q#17 / A3 lock, 2026-04-30)

Phase 3a B5 added a "cast-server-stopped" path: if the user runs an agent
locally while `cast-server` is not up, the file-canonical contract still
produces a valid `.agent-run_<RUN_ID>.output.json` on disk, but no DB row
ever exists. In **v1**, those runs are intentionally not queryable via the
HTTP API — `GET /api/agents/jobs/<id>` returns 404 even when the file is on
disk. The API does not scan the goals directory looking for orphan files.

If user demand surfaces, a v1.1 filesystem-fallback resolver may be added.
Until then, the rule is: HTTP knows about the runs `cast-server` dispatched;
file-only runs live as files. CLI tooling (`cast goal show-run <id>`) and
direct file inspection remain the way to consume cast-server-stopped runs.

## Field-merge semantics

The file generally carries the run's **outcome**: `status`, `summary`,
`artifacts`, `errors`, `next_steps`, `human_action_*`, `completed_at`. The
DB carries the run's **provenance**: `id`, `agent_name`, `goal_slug`,
`task_id`, `created_at`, `started_at`, `parent_run_id`, `worktree_path`,
`session_id`, `cost_usd`, etc.

Merge rule, applied per top-level key:

* If the file dict has the key (even if value is `null` or empty), the
  file's value wins.
* Otherwise the DB row's value is preserved.

The merged dict gets one extra synthetic key, `"source"`, set to `"file"`,
`"db"`, or `"file_invalid"`.

## Cross-references

* `docs/specs/cast-delegation-contract.collab.md` — what the file contains
  and how children write it.
* `docs/specs/cast-output-json-contract.collab.md` — the JSON schema for
  `.agent-run_<RUN_ID>.output.json` (`contract_version: "2"` as of Phase 3a).
* `cast-server/services/agent_service.py` — `load_canonical_file` helper.
* `cast-server/routes/api_agents.py` — route handler.
* `cast-server/tests/test_runs_api.py` — branch coverage for the precedence
  rule.
