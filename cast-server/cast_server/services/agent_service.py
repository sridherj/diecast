"""Agent service — DB-backed agent run tracking, tmux-based execution, output parsing."""

import asyncio
import json
import logging
import os
import shlex
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cast_server.config import (
    GOALS_DIR, DIECAST_ROOT, MAX_CONCURRENT_AGENTS, OFF_PEAK_HOUR,
    AGENT_MONITOR_INTERVAL, AGENT_READY_TIMEOUT, AGENT_IDLE_WARNING,
    AGENT_IDLE_STUCK, AGENT_SESSION_CLEANUP_DELAY, AGENT_SENDKEY_DELAY,
    DEFAULT_CAST_HOST, DEFAULT_CAST_PORT,
)

# Server-emitted callback URLs use literal constants — server is telling the
# child where to call back; no env-var indirection needed (Decision #2).
SERVER_URL = f"http://{DEFAULT_CAST_HOST}:{DEFAULT_CAST_PORT}"
from cast_server.models.agent_config import load_agent_config
from cast_server.models.delegation import DelegationContext
from cast_server.db.connection import get_connection
from cast_server.models.agent_output import AgentOutput
from cast_server.infra.tmux_manager import TmuxSessionManager, TmuxError
from cast_server.infra.terminal import ResolutionError
from cast_server.infra.state_detection import detect_agent_state, AgentState
from cast_server.infra.rate_limit_parser import parse_rate_limit_reset
from cast_server.services import task_service
from cast_server.services.error_memory_service import extract_and_store_error, get_relevant_memories, should_auto_retry

logger = logging.getLogger(__name__)


# Delegation
MAX_DELEGATION_DEPTH = 3

# In-memory state for monitor loop (module-level singletons)
_tmux: TmuxSessionManager | None = None
_state_lock = asyncio.Lock()
_idle_since: dict[str, float] = {}      # run_id -> timestamp when idle started
_total_paused: dict[str, float] = {}    # run_id -> total paused seconds
_cooldown_until: dict[str, datetime] = {}  # run_id -> resume_at (rate limit)
_current_pause: dict[str, dict] = {}       # run_id -> pause entry being built
_session_id_resolved: set[str] = set()     # run_ids whose Claude session ID has been discovered


def _clean_child_env(*exclude: str) -> dict[str, str]:
    """Return os.environ minus the specified keys. Never mutates the global env."""
    skip = set(exclude)
    return {k: v for k, v in os.environ.items() if k not in skip}


def _get_tmux() -> TmuxSessionManager:
    """Lazy-init TmuxSessionManager singleton."""
    global _tmux
    if _tmux is None:
        _tmux = TmuxSessionManager()
    return _tmux

# Pricing per 1M tokens in USD
_MODEL_PRICING = {
    "opus": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
    "sonnet": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
    "haiku": {"input": 0.80, "output": 4.0, "cache_write": 1.0, "cache_read": 0.08},
}


def _discover_claude_session_id(started_after: str, run_id: str,
                                working_dir: str | None = None) -> str | None:
    """Find the real Claude CLI session ID from JSONL files.

    Scans the Claude projects directory for a session file created after
    `started_after` (ISO timestamp) that contains the run_id in its content
    (the prompt includes the run_id in the output.json filename).
    Returns the session ID (filename stem) or None.
    """
    raw_base = working_dir or str(DIECAST_ROOT)
    # Claude Code resolves symlinks when naming project dirs, so we must too
    try:
        base = str(Path(raw_base).resolve())
    except Exception:
        base = raw_base
    project_dir = base.replace("/", "-")
    jsonl_dir = Path.home() / ".claude" / "projects" / project_dir
    if not jsonl_dir.exists():
        return None

    try:
        cutoff = datetime.fromisoformat(started_after).timestamp()
    except (ValueError, TypeError):
        return None

    # Find JSONL files created after the agent launch
    candidates = []
    for f in jsonl_dir.glob("*.jsonl"):
        if f.stat().st_ctime >= cutoff - 5:  # 5s tolerance
            candidates.append((f.stat().st_ctime, f))

    if not candidates:
        return None

    # Use grep to find which file contains the run_id (fast, avoids reading full files)
    candidate_paths = [str(f) for _, f in candidates]
    try:
        result = subprocess.run(
            ["grep", "-l", f".agent-{run_id}"] + candidate_paths,
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            matched = result.stdout.strip().splitlines()[0]
            return Path(matched).stem
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def _resolve_jsonl_dir(working_dir: str | None) -> Path | None:
    """Resolve the Claude CLI JSONL directory for a given working directory."""
    if not working_dir:
        return None
    try:
        resolved = str(Path(working_dir).resolve())
    except Exception:
        resolved = working_dir
    project_slug = resolved.replace("/", "-")
    return Path.home() / ".claude" / "projects" / project_slug


def _resolve_jsonl_file(session_id: str, session_jsonl_dir: Path | None = None) -> Path | None:
    """Resolve the JSONL file path for a session, returning None if not found."""
    if not session_id:
        return None
    project_dir = str(DIECAST_ROOT).replace("/", "-")
    jsonl_dir = session_jsonl_dir or Path.home() / ".claude" / "projects" / project_dir
    jsonl_file = jsonl_dir / f"{session_id}.jsonl"
    return jsonl_file if jsonl_file.exists() else None


def _grep_usage_lines(jsonl_file: Path) -> str | None:
    """Grep a JSONL file for usage lines. Returns stdout or None."""
    try:
        result = subprocess.run(
            ["grep", '"usage"', str(jsonl_file)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0 or not result.stdout:
            return None
        return result.stdout
    except (OSError, subprocess.TimeoutExpired):
        return None


def _read_session_tokens(
    session_id: str, session_jsonl_dir: Path | None = None
) -> tuple[int | None, int | None, int | None, int | None]:
    """Read token counts from Claude CLI session JSONL log.

    Sums usage from all assistant messages in the session.
    Returns (input_tokens, cache_write_tokens, cache_read_tokens, output_tokens)
    or (None, None, None, None) if unavailable.
    """
    jsonl_file = _resolve_jsonl_file(session_id, session_jsonl_dir)
    if not jsonl_file:
        return None, None, None, None
    stdout = _grep_usage_lines(jsonl_file)
    if not stdout:
        return None, None, None, None
    try:
        total_in = 0
        total_cache_write = 0
        total_cache_read = 0
        total_out = 0
        found = False
        for line in stdout.splitlines():
            entry = json.loads(line)
            if entry.get("type") != "assistant":
                continue
            msg = entry.get("message")
            if not isinstance(msg, dict):
                continue
            usage = msg.get("usage")
            if not usage:
                continue
            found = True
            total_in += usage.get("input_tokens", 0)
            total_cache_write += usage.get("cache_creation_input_tokens", 0)
            total_cache_read += usage.get("cache_read_input_tokens", 0)
            total_out += usage.get("output_tokens", 0)
        return (total_in, total_cache_write, total_cache_read, total_out) if found else (None, None, None, None)
    except json.JSONDecodeError:
        return None, None, None, None


def _parse_token_str(s: str) -> int | None:
    """Convert '6.4k' or '2,300' or '1700' to int."""
    s = s.replace(",", "").strip()
    if s.endswith("k"):
        try:
            return int(float(s[:-1]) * 1000)
        except ValueError:
            return None
    try:
        return int(float(s))
    except ValueError:
        return None


# Mapping from /context output category names to our 4 buckets
_CONTEXT_CATEGORY_MAP = {
    "system prompt": "system",
    "system tools": "system",
    "mcp tools (deferred)": "system",
    "system tools (deferred)": "system",
    "memory files": "memory",
    "custom agents": "agents",
    "skills": "agents",
    "messages": "messages",
}


def _get_session_context_breakdown(
    session_id: str, working_dir: str | None = None
) -> dict | None:
    """Run `claude --resume {session_id} -p /context` and parse the breakdown.

    Returns {"system": N, "memory": N, "agents": N, "messages": N}
    or None if unavailable.
    """
    try:
        env = _clean_child_env("CLAUDE_SESSION_ID", "CLAUDECODE")
        cwd = working_dir or str(Path.home())
        result = subprocess.run(
            ["claude", "--resume", session_id, "-p", "/context"],
            capture_output=True, text=True, timeout=30,
            cwd=cwd, env=env,
        )
        if result.returncode != 0 or not result.stdout:
            return None
    except Exception:
        return None

    buckets: dict[str, int] = {}
    for line in result.stdout.splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        name = parts[0].strip()
        tok_str = parts[1].strip()
        if not name or not tok_str or set(tok_str) <= {"-", " "}:
            continue
        bucket = _CONTEXT_CATEGORY_MAP.get(name.lower())
        if bucket:
            tokens = _parse_token_str(tok_str)
            if tokens is not None:
                buckets[bucket] = buckets.get(bucket, 0) + tokens
    return buckets if buckets else None


def _read_context_usage(
    session_id: str, session_jsonl_dir: Path | None = None,
    working_dir: str | None = None,
) -> dict | None:
    """Read peak context window usage from Claude CLI session JSONL.

    Returns {"total": N, "limit": 200000} from the last assistant turn's
    input_tokens + cache_read, enriched with per-category breakdown
    (system/memory/agents/messages) when available via `claude --resume`.
    """
    jsonl_file = _resolve_jsonl_file(session_id, session_jsonl_dir)
    if not jsonl_file:
        return None
    stdout = _grep_usage_lines(jsonl_file)
    if not stdout:
        return None
    try:
        last_usage = None
        for line in stdout.splitlines():
            entry = json.loads(line)
            if entry.get("type") != "assistant":
                continue
            msg = entry.get("message")
            if not isinstance(msg, dict):
                continue
            usage = msg.get("usage")
            if usage:
                last_usage = usage
        if not last_usage:
            return None
        total = (last_usage.get("input_tokens", 0)
                 + last_usage.get("cache_read_input_tokens", 0))
        result = {"total": total, "limit": 200_000}

        breakdown = _get_session_context_breakdown(session_id, working_dir)
        if breakdown:
            result.update(breakdown)

        return result
    except json.JSONDecodeError:
        return None


def _estimate_cost(
    input_tokens: int | None,
    cache_write_tokens: int | None,
    cache_read_tokens: int | None,
    output_tokens: int | None,
    model: str | None = None,
) -> float | None:
    """Estimate USD cost from token counts and model name.

    Returns cost rounded to 4 decimal places, or None if tokens unavailable.
    """
    if input_tokens is None or output_tokens is None:
        return None
    # Determine pricing tier from model string
    pricing = _MODEL_PRICING["sonnet"]  # default
    if model:
        model_lower = model.lower()
        for key, rates in _MODEL_PRICING.items():
            if key in model_lower:
                pricing = rates
                break
    cost = (
        input_tokens * pricing["input"]
        + (cache_write_tokens or 0) * pricing["cache_write"]
        + (cache_read_tokens or 0) * pricing["cache_read"]
        + output_tokens * pricing["output"]
    ) / 1_000_000
    return round(cost, 4)


# ---------------------------------------------------------------------------
# Run ID generation
# ---------------------------------------------------------------------------

def _generate_run_id() -> str:
    """Generate a run ID: run_{timestamp}_{6-char-uuid}."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:6]
    return f"run_{ts}_{short_uuid}"


# ---------------------------------------------------------------------------
# DB-backed CRUD for agent_runs
# ---------------------------------------------------------------------------

def create_agent_run(agent_name: str, goal_slug: str, task_id: int | None,
                     input_params: dict | None, session_id: str | None = None,
                     scheduled_at: str | None = None, status: str = "pending",
                     parent_run_id: str | None = None,
                     claude_agent_id: str | None = None,
                     db_path=None) -> str:
    """Insert agent_run record, return run_id.

    ``claude_agent_id`` is the Claude Code per-subagent runtime id from
    ``SubagentStart.agent_id``. sp2 populates it for subagent-invocation rows;
    user-invocation and CLI-dispatched rows leave it NULL.
    """
    run_id = _generate_run_id()
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    conn.execute(
        """INSERT INTO agent_runs (id, agent_name, goal_slug, task_id, status,
           input_params, session_id, scheduled_at, parent_run_id,
           claude_agent_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, agent_name, goal_slug, task_id, status,
         json.dumps(input_params) if input_params else None, session_id,
         scheduled_at, parent_run_id, claude_agent_id, now),
    )
    conn.commit()
    conn.close()
    return run_id


def resolve_parent_for_subagent(
    session_id: str,
    db_path=None,
) -> str | None:
    """Return id of the most-recent running cast-* agent_run in ``session_id``, or None.

    The ``agent_name LIKE 'cast-%'`` filter is contract: a non-cast subagent
    (e.g. user-dispatched ``Explore``) MUST NOT become a parent of a later
    cast-* subagent. The ``status='running'`` filter prevents stale
    completed rows in the same session from being claimed as parents.
    Most-recent-by-``started_at`` wins so a nested cast-* subagent
    correctly picks the outer cast-* (not the user-invocation) as parent.
    """
    if not session_id:
        return None
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT id FROM agent_runs
             WHERE session_id = ?
               AND status = 'running'
               AND agent_name LIKE 'cast-%'
             ORDER BY started_at DESC
             LIMIT 1
            """,
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    return row["id"] if row else None


def resolve_run_by_claude_agent_id(
    claude_agent_id: str,
    db_path=None,
) -> str | None:
    """Return id of the agent_run whose ``claude_agent_id`` matches, or None.

    Used by the SubagentStop closure path. ``claude_agent_id`` is unique per
    subagent dispatch — single-row exact lookup. ORDER BY started_at DESC +
    LIMIT 1 is defensive: a duplicate should not happen, but if it does we
    close the most-recent.
    """
    if not claude_agent_id:
        return None
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            """
            SELECT id FROM agent_runs
             WHERE claude_agent_id = ?
             ORDER BY started_at DESC
             LIMIT 1
            """,
            (claude_agent_id,),
        ).fetchone()
    finally:
        conn.close()
    return row["id"] if row else None


def update_agent_run(run_id: str, db_path=None, **fields):
    """Update agent_run fields (status, output, completed_at, etc.)."""
    conn = get_connection(db_path)
    set_clauses = []
    values = []
    for key, value in fields.items():
        set_clauses.append(f"{key} = ?")
        if key in ("input_params", "output", "artifacts", "directories", "context_usage") and isinstance(value, (dict, list)):
            values.append(json.dumps(value))
        else:
            values.append(value)
    values.append(run_id)
    conn.execute(
        f"UPDATE agent_runs SET {', '.join(set_clauses)} WHERE id = ?",
        values,
    )
    conn.commit()
    conn.close()


def get_agent_run(run_id: str, db_path=None) -> dict | None:
    """Get single run by ID."""
    conn = get_connection(db_path)
    row = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_dict(row)


class MalformedOutputError(ValueError):
    """Raised when a canonical .agent-run_<id>.output.json file exists but cannot be parsed."""


class MissingExternalProjectDirError(ValueError):
    """Raised when a dispatch is attempted for a goal whose external_project_dir is unset
    or whose configured path does not exist on disk.

    Carries structured context so the route layer can surface a 422 with
    actionable fields (goal_slug, configured_path).
    """

    def __init__(self, goal_slug: str, configured_path: str | None) -> None:
        self.goal_slug = goal_slug
        self.configured_path = configured_path
        if configured_path:
            msg = (
                f"Goal '{goal_slug}' has external_project_dir set to '{configured_path}' "
                f"but that path does not exist on disk."
            )
        else:
            msg = (
                f"Goal '{goal_slug}' has no external_project_dir configured. "
                f"Set one before dispatching agents on this goal."
            )
        super().__init__(msg)


def _validate_dispatch_preconditions(goal_slug: str, db_path=None) -> None:
    """Refuse dispatch when the goal's external_project_dir is unusable.

    Raises ``MissingExternalProjectDirError`` if the goal lacks an
    ``external_project_dir`` or the configured path does not resolve to an
    existing directory. The dispatch contract treats both as the same
    user-facing problem; ``configured_path`` on the exception disambiguates.
    """
    from cast_server.services import goal_service
    goal_data = goal_service.get_goal(goal_slug, db_path=db_path)
    configured = goal_data.get("external_project_dir") if goal_data else None
    if not configured:
        raise MissingExternalProjectDirError(goal_slug, None)
    if not Path(configured).expanduser().is_dir():
        raise MissingExternalProjectDirError(goal_slug, configured)


def load_canonical_file(goal_dir: Path, run_id: str) -> dict | None:
    """Read the canonical agent-run output JSON from disk.

    Returns the parsed dict if the file exists and is valid JSON, ``None`` if
    the file does not exist, and raises :class:`MalformedOutputError` if it
    exists but cannot be parsed. The contract spec is at
    ``docs/specs/cast-delegation-contract.collab.md``; this helper only loads
    raw JSON and does not validate the schema.
    """
    path = Path(goal_dir) / f".agent-run_{run_id}.output.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise MalformedOutputError(f"Malformed output file at {path}: {e}") from e


def get_runs_for_goal(goal_slug: str, db_path=None) -> list[dict]:
    """Get all runs for a goal, ordered by created_at desc."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM agent_runs WHERE goal_slug = ? ORDER BY created_at DESC",
        (goal_slug,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_latest_agent_run(goal_slug: str, agent_name: str, db_path=None) -> dict | None:
    """Get the most recent run of a specific agent for a goal."""
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT * FROM agent_runs WHERE goal_slug = ? AND agent_name = ? ORDER BY id DESC LIMIT 1",
        (goal_slug, agent_name),
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def get_runs_for_task(task_id: int, db_path=None) -> list[dict]:
    """Get all runs for a specific task."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM agent_runs WHERE task_id = ? ORDER BY started_at DESC",
        (task_id,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_active_run_for_task(task_id: int, db_path=None) -> dict | None:
    """Get the currently active agent_run for a task (running, pending, or scheduled)."""
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT * FROM agent_runs WHERE task_id = ? AND status IN ('running', 'pending', 'scheduled') LIMIT 1",
        (task_id,),
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def get_active_runs_for_tasks(task_ids: list[int], db_path=None) -> dict[int, dict]:
    """Batch-load active runs for multiple tasks. Returns {task_id: run_dict}."""
    if not task_ids:
        return {}
    conn = get_connection(db_path)
    placeholders = ",".join("?" * len(task_ids))
    rows = conn.execute(
        f"SELECT * FROM agent_runs WHERE task_id IN ({placeholders}) AND status IN ('running', 'pending', 'scheduled')",
        task_ids,
    ).fetchall()
    conn.close()
    return {r["task_id"]: _row_to_dict(r) for r in rows}


def get_all_runs(
    status_filter: str | None = None,
    limit: int = 50,
    db_path=None,
    top_level_only: bool = False,
    exclude_test: bool | None = None,
    page: int = 1,
    per_page: int | None = None,
) -> dict:
    """Get agent runs with pagination, enriched with goal title and task title.

    Returns dict with keys: runs (list), total (int), page (int), per_page (int), pages (int).

    Args:
        exclude_test: If True, exclude runs where agent_name starts with 'test'.
            Defaults to True when CAST_ENV != 'test'.
        page: 1-based page number.
        per_page: Items per page. If None, uses `limit` for backward compat.
    """
    if exclude_test is None:
        exclude_test = os.environ.get("CAST_ENV") != "test"
    effective_per_page = per_page if per_page is not None else limit

    conn = get_connection(db_path)
    base_query = """
        FROM agent_runs ar
        LEFT JOIN goals g ON ar.goal_slug = g.slug
        LEFT JOIN tasks t ON ar.task_id = t.id
    """
    conditions = []
    params: list = []
    if status_filter and status_filter != "all":
        conditions.append("ar.status = ?")
        params.append(status_filter)
    if top_level_only:
        conditions.append("ar.parent_run_id IS NULL")
    if exclude_test:
        conditions.append("ar.agent_name NOT LIKE 'test%'")
    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    # Total count
    count_row = conn.execute(f"SELECT COUNT(*) as cnt {base_query}{where_clause}", params).fetchone()
    total = count_row["cnt"] if count_row else 0

    # Paginated fetch
    offset = (page - 1) * effective_per_page
    select_query = f"SELECT ar.*, g.title AS goal_title, t.title AS task_title {base_query}{where_clause} ORDER BY ar.created_at DESC LIMIT ? OFFSET ?"
    rows = conn.execute(select_query, [*params, effective_per_page, offset]).fetchall()
    conn.close()

    # Count children for each run
    result = [_row_to_dict(r) for r in rows]
    if top_level_only and result:
        run_ids = [r["id"] for r in result]
        conn = get_connection(db_path)
        placeholders = ",".join("?" * len(run_ids))
        child_counts = conn.execute(
            f"SELECT parent_run_id, COUNT(*) as cnt FROM agent_runs "
            f"WHERE parent_run_id IN ({placeholders}) GROUP BY parent_run_id",
            run_ids,
        ).fetchall()
        conn.close()
        count_map = {row["parent_run_id"]: row["cnt"] for row in child_counts}
        for r in result:
            r["child_count"] = count_map.get(r["id"], 0)

    pages = max(1, (total + effective_per_page - 1) // effective_per_page)
    return {"runs": result, "total": total, "page": page, "per_page": effective_per_page, "pages": pages}


# ---------------------------------------------------------------------------
# Threaded /runs page: get_runs_tree + helpers
# ---------------------------------------------------------------------------

# Severity ordering for status_rollup (Decision #4 in plan; locked).
# Higher = more severe. Unknown statuses default to lowest severity.
_STATUS_SEVERITY = {
    "completed": 0,
    "scheduled": 1,
    "pending": 2,
    "running": 3,
    "rate_limited": 4,
    "stuck": 5,
    "failed": 6,
}

# Depth cap for recursive CTE (Decision in plan; locked).
_TREE_DEPTH_CAP = 10


def _row_to_tree_dict(row) -> dict:
    """Tree-path row hydration: parses context_usage, artifacts, output.

    The detail panel inside the threaded /runs macro renders run.artifacts
    and run.output.summary, so leaving them as JSON strings makes Jinja
    iterate the string character-by-character. input_params/directories
    aren't read by the macro and stay deferred.
    """
    d = dict(row)
    for key in ("context_usage", "artifacts", "output"):
        val = d.get(key)
        if val and isinstance(val, str):
            try:
                d[key] = json.loads(val)
            except json.JSONDecodeError:
                pass
    return d


def _ctx_class(context_usage) -> str | None:
    """Bucket context usage into 'low' / 'mid' / 'high', or None when unknown."""
    if not isinstance(context_usage, dict):
        return None
    total = context_usage.get("total")
    limit = context_usage.get("limit")
    if total is None or limit is None or not limit:
        return None
    pct = (total / limit) * 100
    if pct < 40:
        return "low"
    if pct < 70:
        return "mid"
    return "high"


def _parse_iso(ts):
    """Parse an ISO timestamp string from SQLite, returning None on failure."""
    if not ts:
        return None
    try:
        # SQLite stores timestamps as text; some are naive, some have offsets.
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def _assemble_tree(rows: list[dict], l1_ids: list[str]) -> list[dict]:
    """Build parent→children tree from a flat row list.

    Returns the L1 roots (in the order of `l1_ids`) with `children` lists
    attached recursively. Each level is sorted by `created_at ASC`.
    """
    by_id: dict[str, dict] = {}
    for r in rows:
        r["children"] = []
        by_id[r["id"]] = r

    for r in rows:
        parent_id = r.get("parent_run_id")
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(r)

    # Sort children at every level by created_at ASC for determinism.
    for r in rows:
        r["children"].sort(key=lambda c: c.get("created_at") or "")

    return [by_id[lid] for lid in l1_ids if lid in by_id]


def _detect_rework(parent: dict) -> int:
    """Mark consecutive same-(agent_name, task_id) sibling reworks.

    Walks `parent["children"]` (already sorted ASC) and tracks how many
    times each (agent_name, task_id) key has been seen. The first sighting
    is the original; each subsequent sighting gets `is_rework=True` and
    `rework_index = N` (starts at 2 for the second instance).

    Returns the number of rework events at this level (= number of children
    flagged). Does NOT recurse — the caller drives recursion.
    """
    seen: dict[tuple, int] = {}
    rework_events = 0
    for child in parent["children"]:
        key = (child.get("agent_name"), child.get("task_id"))
        count = seen.get(key, 0) + 1
        seen[key] = count
        if count >= 2:
            child["is_rework"] = True
            child["rework_index"] = count
            rework_events += 1
        else:
            # First sighting: explicit defaults so downstream can trust shape.
            child.setdefault("is_rework", False)
            child.setdefault("rework_index", None)
    return rework_events


def _propagate_rework(roots: list[dict]) -> None:
    """Post-order DFS: rework_count = own rework events + sum of descendants'.

    An L1's `rework_count` reflects rework loops anywhere in its tree, so
    the rollup pill on the L1 row is meaningful without expansion.
    """
    def walk(node: dict) -> int:
        own = _detect_rework(node) if node["children"] else 0
        for child in node["children"]:
            child.setdefault("is_rework", False)
            child.setdefault("rework_index", None)
        sub = sum(walk(c) for c in node["children"])
        node["rework_count"] = own + sub
        return node["rework_count"]

    for root in roots:
        walk(root)


def _compute_rollups(roots: list[dict]) -> None:
    """Post-order DFS computing all per-node rollup fields in one walk.

    Sets on every node:
        descendant_count        (excludes self)
        failed_descendant_count (status in {failed, stuck})
        total_cost_usd          (self + descendants; None treated as 0.0)
        status_rollup           (max severity over self + descendants)
        ctx_class               (from own context_usage)
    Sets on L1 roots only:
        wall_duration_seconds   (completed_at - started_at; None otherwise)
    """
    def walk(node: dict, depth: int) -> tuple[int, int, float, int]:
        # Defaults so children of nodes with no kids still have the shape.
        node.setdefault("children", [])

        own_cost = node.get("cost_usd") or 0.0
        own_severity = _STATUS_SEVERITY.get(node.get("status"), 0)
        own_failed = 1 if node.get("status") in ("failed", "stuck") else 0

        sub_count = 0
        sub_failed = 0
        sub_cost = 0.0
        sub_max_sev = 0
        for child in node["children"]:
            c_count, c_failed, c_cost, c_sev = walk(child, depth + 1)
            sub_count += 1 + c_count
            sub_failed += c_failed
            sub_cost += c_cost
            if c_sev > sub_max_sev:
                sub_max_sev = c_sev

        node["descendant_count"] = sub_count
        node["failed_descendant_count"] = sub_failed
        node["total_cost_usd"] = round(own_cost + sub_cost, 6)

        max_sev = max(own_severity, sub_max_sev)
        # Reverse-lookup severity → status name. Stable: pick the canonical
        # name with the highest severity (only one per level in our table).
        node["status_rollup"] = _SEVERITY_TO_STATUS.get(max_sev, node.get("status") or "completed")

        node["ctx_class"] = _ctx_class(node.get("context_usage"))

        if depth == 0:
            started = _parse_iso(node.get("started_at"))
            completed = _parse_iso(node.get("completed_at"))
            if started and completed:
                node["wall_duration_seconds"] = int((completed - started).total_seconds())
            else:
                node["wall_duration_seconds"] = None

        # Return descendant accumulators for the parent's roll-up.
        return sub_count, sub_failed + own_failed, own_cost + sub_cost, max_sev

    for root in roots:
        walk(root, 0)


# Reverse map for status_rollup: severity -> status name.
_SEVERITY_TO_STATUS = {v: k for k, v in _STATUS_SEVERITY.items()}


def get_runs_tree(
    status_filter: str | None = None,
    page: int = 1,
    per_page: int = 25,
    exclude_test: bool | None = None,
    db_path=None,
) -> dict:
    """Return paginated L1 runs with full descendant trees attached.

    Pagination is bounded by L1 count (children never count toward the page
    limit). Trees are fetched via a depth-capped recursive CTE; trees deeper
    than 10 are silently truncated and a server-side warning is logged so
    runaway agent loops are visible in production.

    Each run dict includes:
        children: list[run]                # ordered by created_at ASC
        descendant_count: int              # total subtree size (excludes self)
        failed_descendant_count: int       # count where status in (failed, stuck)
        rework_count: int                  # propagated up to all ancestors
        status_rollup: str                 # max-severity status across self+descendants
        total_cost_usd: float              # sum of self + descendants
        wall_duration_seconds: int | None  # L1 only: completed_at - started_at
        ctx_class: str | None              # 'low' | 'mid' | 'high'
        is_rework: bool                    # set on children only
        rework_index: int | None           # 2,3,... for 2nd+ attempt

    Returns: {"runs": [...], "total": int, "page": int, "per_page": int, "pages": int}.

    The `status_filter` is rollup-aware (Decision #13): an L1 whose own
    status is `completed` but with a `failed` descendant matches
    `status_filter='failed'`. Filtering is post-rollup (in Python) for
    simplicity; per-page L1 cap bounds the cost.
    """
    if exclude_test is None:
        exclude_test = os.environ.get("CAST_ENV") != "test"

    conn = get_connection(db_path)
    try:
        # Step 1: Page L1 ids (no raw status pre-filter — rollup is the only
        # filter applied, post-assembly).
        l1_conditions = ["ar.parent_run_id IS NULL"]
        l1_params: list = []
        if exclude_test:
            l1_conditions.append("ar.agent_name NOT LIKE 'test%'")
        l1_where = " WHERE " + " AND ".join(l1_conditions)

        total_l1 = conn.execute(
            f"SELECT COUNT(*) AS cnt FROM agent_runs ar{l1_where}", l1_params
        ).fetchone()["cnt"]

        offset = (page - 1) * per_page
        l1_rows = conn.execute(
            f"SELECT ar.id FROM agent_runs ar{l1_where} "
            f"ORDER BY ar.created_at DESC LIMIT ? OFFSET ?",
            [*l1_params, per_page, offset],
        ).fetchall()
        l1_ids = [r["id"] for r in l1_rows]

        if not l1_ids:
            pages = max(1, (total_l1 + per_page - 1) // per_page) if total_l1 else 1
            return {"runs": [], "total": total_l1, "page": page,
                    "per_page": per_page, "pages": pages}

        # Step 2: Tree fetch via recursive CTE, depth-capped at 10.
        placeholders = ",".join("?" * len(l1_ids))
        tree_sql = f"""
            WITH RECURSIVE tree AS (
                SELECT ar.*, 0 AS depth
                FROM agent_runs ar
                WHERE ar.id IN ({placeholders})
                UNION ALL
                SELECT ar.*, tree.depth + 1
                FROM agent_runs ar
                JOIN tree ON ar.parent_run_id = tree.id
                WHERE tree.depth < ?
            )
            SELECT tree.*, g.title AS goal_title, t.title AS task_title
            FROM tree
            LEFT JOIN goals g ON tree.goal_slug = g.slug
            LEFT JOIN tasks t ON tree.task_id = t.id
        """
        rows = conn.execute(tree_sql, [*l1_ids, _TREE_DEPTH_CAP]).fetchall()

        # Detect truncation: any node at depth == cap whose row has children
        # in the DB indicates the tree was cut off.
        depth_cap_ids = [r["id"] for r in rows if r["depth"] >= _TREE_DEPTH_CAP]
        if depth_cap_ids:
            probe = conn.execute(
                f"SELECT DISTINCT parent_run_id FROM agent_runs "
                f"WHERE parent_run_id IN ({','.join('?' * len(depth_cap_ids))})",
                depth_cap_ids,
            ).fetchall()
            if probe:
                # Walk back up to find which L1 owns each truncated branch.
                truncated_l1s = set()
                # Build parent map for the fetched rows so we can walk up.
                parent_of = {r["id"]: r["parent_run_id"] for r in rows}
                for tid in (p["parent_run_id"] for p in probe):
                    cur = tid
                    while cur and parent_of.get(cur):
                        cur = parent_of[cur]
                    if cur:
                        truncated_l1s.add(cur)
                for l1 in truncated_l1s or {depth_cap_ids[0]}:
                    logger.warning(
                        "tree truncated at depth %d for L1 run_id=%s",
                        _TREE_DEPTH_CAP, l1,
                    )
    finally:
        conn.close()

    # Step 3: Trim per-row JSON parsing — only context_usage on the tree path.
    hydrated = [_row_to_tree_dict(r) for r in rows]

    # Step 4: Assemble tree.
    roots = _assemble_tree(hydrated, l1_ids)

    # Step 5: Compute rollups (single post-order walk).
    _compute_rollups(roots)

    # Step 6: Detect + propagate rework.
    _propagate_rework(roots)

    # Step 7: Rollup-aware status filter (Decision #13).
    if status_filter and status_filter != "all":
        roots = [r for r in roots if r.get("status_rollup") == status_filter]

    total = len(roots) if (status_filter and status_filter != "all") else total_l1
    pages = max(1, (total + per_page - 1) // per_page) if total else 1
    return {"runs": roots, "total": total, "page": page,
            "per_page": per_page, "pages": pages}


def get_run_with_rollups(run_id: str, db_path=None) -> dict | None:
    """Return a single run as an L1 root with descendants + rollups attached.

    Powers the `/api/agents/runs/{id}/status_cells` poll endpoint: rollup
    fields (descendant_count, failed_descendant_count, rework_count,
    status_rollup, total_cost_usd, ctx_class, wall_duration_seconds) can
    change between 3s polls, so the partial render must recompute them.
    Reuses the same recursive CTE + helpers as `get_runs_tree`, scoped to
    one root.
    """
    conn = get_connection(db_path)
    try:
        tree_sql = """
            WITH RECURSIVE tree AS (
                SELECT ar.*, 0 AS depth
                FROM agent_runs ar
                WHERE ar.id = ?
                UNION ALL
                SELECT ar.*, tree.depth + 1
                FROM agent_runs ar
                JOIN tree ON ar.parent_run_id = tree.id
                WHERE tree.depth < ?
            )
            SELECT tree.*, g.title AS goal_title, t.title AS task_title
            FROM tree
            LEFT JOIN goals g ON tree.goal_slug = g.slug
            LEFT JOIN tasks t ON tree.task_id = t.id
        """
        rows = conn.execute(tree_sql, (run_id, _TREE_DEPTH_CAP)).fetchall()
    finally:
        conn.close()

    if not rows:
        return None

    hydrated = [_row_to_tree_dict(r) for r in rows]
    roots = _assemble_tree(hydrated, [run_id])
    if not roots:
        return None
    _compute_rollups(roots)
    _propagate_rework(roots)
    return roots[0]


def get_dashboard_summary(db_path=None) -> dict:
    """Get summary stats for the runs dashboard: cost/tokens today, active counts."""
    conn = get_connection(db_path)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Cost today
    cost_today = conn.execute(
        "SELECT COALESCE(SUM(cost_usd), 0) FROM agent_runs "
        "WHERE date(completed_at) = ? AND cost_usd IS NOT NULL", (today,)
    ).fetchone()[0]

    # Tokens today
    tokens = conn.execute(
        "SELECT COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0), "
        "COALESCE(SUM(cache_read_tokens), 0) FROM agent_runs "
        "WHERE date(completed_at) = ?", (today,)
    ).fetchone()

    # Active counts
    counts = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM agent_runs "
        "WHERE status IN ('running', 'rate_limited', 'pending') "
        "GROUP BY status"
    ).fetchall()

    # Stuck detection: running in DB but no tmux session
    running_ids = conn.execute(
        "SELECT id FROM agent_runs WHERE status = 'running'"
    ).fetchall()
    conn.close()
    count_map = {row["status"]: row["cnt"] for row in counts}

    stuck = 0
    try:
        for row in running_ids:
            session = f"agent-{row['id']}"
            result = subprocess.run(
                ["tmux", "has-session", "-t", session],
                capture_output=True, timeout=2,
            )
            if result.returncode != 0:
                stuck += 1
    except Exception:
        pass  # tmux not available — skip stuck detection

    running = count_map.get("running", 0)
    return {
        "cost_today": round(cost_today, 2),
        "input_tokens": tokens[0],
        "output_tokens": tokens[1],
        "cache_read_tokens": tokens[2],
        "running": running,
        "rate_limited": count_map.get("rate_limited", 0),
        "pending": count_map.get("pending", 0),
        "max_slots": MAX_CONCURRENT_AGENTS,
        "slots_used": running,
        "slots_available": max(0, MAX_CONCURRENT_AGENTS - running),
        "stuck": stuck,
    }


def get_escalated_agents(db_path=None) -> set[str]:
    """Get agent names with escalated error memories (recurring failure patterns)."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT DISTINCT agent_name FROM agent_error_memories "
        "WHERE resolution_status = 'escalated'"
    ).fetchall()
    conn.close()
    return {row["agent_name"] for row in rows}


def cancel_run(run_id: str, db_path=None) -> dict | None:
    """Cancel an active agent run. Kills tmux session, marks as failed."""
    run = get_agent_run(run_id, db_path=db_path)
    if not run:
        raise ValueError(f"Run {run_id} not found")
    if run["status"] not in ("running", "pending", "scheduled"):
        raise ValueError("Can only cancel active runs")

    # Kill tmux session (best-effort)
    try:
        tmux = _get_tmux()
        if tmux.session_exists(f"agent-{run_id}"):
            tmux.kill_session(f"agent-{run_id}")
    except Exception:
        pass

    update_agent_run(
        run_id,
        status="failed",
        error_message="Cancelled by user",
        completed_at=datetime.now(timezone.utc).isoformat(),
        db_path=db_path,
    )

    # Clean up dot-files
    goal_dir = GOALS_DIR / run.get("goal_slug", "")
    for pattern in [f".agent-{run_id}.prompt", f".delegation-{run_id}.json"]:
        f = goal_dir / pattern
        if f.exists():
            f.unlink()

    # Clean up in-memory state
    _idle_since.pop(run_id, None)
    _total_paused.pop(run_id, None)
    _cooldown_until.pop(run_id, None)
    _current_pause.pop(run_id, None)
    return get_agent_run(run_id, db_path=db_path)


def delete_run(run_id: str, db_path=None) -> bool:
    """Delete an agent run from the database. Must be in terminal state."""
    run = get_agent_run(run_id, db_path=db_path)
    if not run:
        raise ValueError(f"Run {run_id} not found")
    if run["status"] in ("running", "pending", "scheduled"):
        raise ValueError("Cannot delete active runs. Cancel first.")

    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM agent_runs WHERE id = ?", (run_id,))
        conn.commit()
    finally:
        conn.close()
    return True


def fail_run(run_id: str, db_path=None) -> dict | None:
    """Manually mark a run as failed."""
    run = get_agent_run(run_id, db_path=db_path)
    if not run:
        raise ValueError(f"Run {run_id} not found")
    if run["status"] in ("completed", "failed"):
        raise ValueError("Run already in terminal state")

    update_agent_run(
        run_id,
        status="failed",
        error_message="Manually marked as failed",
        completed_at=datetime.now(timezone.utc).isoformat(),
        db_path=db_path,
    )

    # Clean up in-memory state
    _idle_since.pop(run_id, None)
    _total_paused.pop(run_id, None)
    _cooldown_until.pop(run_id, None)
    _current_pause.pop(run_id, None)

    return get_agent_run(run_id, db_path=db_path)


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a dict, parsing JSON fields."""
    d = dict(row)
    for json_field in ("input_params", "output", "artifacts", "directories", "context_usage"):
        if d.get(json_field) and isinstance(d[json_field], str):
            try:
                d[json_field] = json.loads(d[json_field])
            except json.JSONDecodeError:
                pass
    return d


# ---------------------------------------------------------------------------
# Context injection routing
# ---------------------------------------------------------------------------

def _inject_context(agent_name: str, goal_slug: str,
                    gstack_dir: str | None = None,
                    external_project_dir: str | None = None) -> str:
    """Build context section based on agent's context_mode and goal config."""
    config = load_agent_config(agent_name)
    goal_dir = GOALS_DIR / goal_slug
    context_parts = []

    if config.context_mode == "lightweight":
        context_map = goal_dir / ".context-map.md"
        if context_map.exists():
            context_parts.append(f"\n\nRead `{context_map}` for goal context overview.")
    else:
        # Full context mode: instruct agent to read all goal artifacts
        artifacts = []
        for suffix in [".human.md", ".collab.md", ".ai.md"]:
            artifacts.extend(goal_dir.glob(f"**/*{suffix}"))
        if artifacts:
            paths = "\n".join(f"- `{p}`" for p in sorted(artifacts))
            context_parts.append(f"\n\nRead these goal artifacts for full context:\n{paths}")

    # Add gstack context block
    if gstack_dir:
        expanded = Path(gstack_dir).expanduser()
        if expanded.exists():
            context_parts.append(
                f"\n## GStack Artifacts (reference-only context)\n"
                f"Directory: {expanded}\n"
                f"These are early-stage exploration/spec artifacts created outside Diecast.\n"
                f"See docs/reference/gstack-artifacts.md for what each file type means.\n"
                f"IMPORTANT: GStack artifacts are reference material, NOT the source of truth. "
                f"If a Diecast goal artifact or external project doc covers the same topic, "
                f"that version is authoritative. If you see conflicts, flag them for human "
                f"confirmation rather than assuming either is correct.\n"
                f"DO NOT write to this directory."
            )
        else:
            context_parts.append(
                f"\n## GStack Artifacts (WARNING: directory not found)\n"
                f"Configured path: {gstack_dir} (expanded: {expanded})\n"
                f"Directory does not exist. Skipping gstack context."
            )

    # Add external project context block
    if external_project_dir:
        expanded = Path(external_project_dir).expanduser()
        if expanded.exists():
            context_parts.append(
                f"\n## External Project Directory\n"
                f"You are running inside the project directory ({expanded}).\n"
                f"Goal artifacts (plans, research, playbooks) are in `.cast/`.\n"
                f"Code and execution artifacts go in the current working directory."
            )
        else:
            context_parts.append(
                f"\n## External Project Directory (WARNING: directory not found)\n"
                f"Configured path: {external_project_dir} (expanded: {expanded})\n"
                f"Directory does not exist. Running in diecast root instead."
            )

    return "\n".join(context_parts)


# ---------------------------------------------------------------------------
# Error memory injection
# ---------------------------------------------------------------------------

def _inject_error_memories(agent_name: str) -> str:
    """Build error memory context section for agent prompt."""
    memories = get_relevant_memories(agent_name)
    if not memories:
        return ""

    lines = ["\n\n## Known Error Patterns for This Agent\n"]
    lines.append("The following errors have occurred in past runs. Avoid repeating them:\n")
    for mem in memories:
        lines.append(
            f"- **{mem['category']}** ({mem['occurrences']}x, last: {mem['last_seen'][:10]}): "
            f"{mem['pattern']}"
        )
        if mem['resolution']:
            lines.append(f"  - Partial fix: {mem['resolution']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Delegation preamble helpers
# ---------------------------------------------------------------------------

def _universal_anti_inline(allowed_delegations: list[str]) -> str:
    """Always-on rule: never inline an agent's work yourself.

    Emitted when allowed_delegations is non-empty, regardless of per-target
    dispatch mix. Preserves the project's intentional anti-inlining invariant: the
    parent must dispatch, not paraphrase. Returns empty string when the
    parent has no delegations (nothing to inline).
    """
    if not allowed_delegations:
        return ""
    allowed_list = ", ".join(allowed_delegations)
    return (
        "\nCRITICAL: NEVER inline an agent's work yourself. When a task calls for "
        "one of your allowed_delegations, you MUST dispatch to that agent — do not "
        "attempt the work yourself, summarize what the agent would produce, or "
        "paraphrase its output.\n"
        f"Your allowed_delegations: [{allowed_list}]\n"
    )


def _http_dispatch_rules(http_targets: list[str]) -> str:
    """Rules for HTTP-dispatched delegation targets.

    Returns the 'never use Agent tool for these HTTP targets' block scoped
    to the listed names. Returns empty string when http_targets is empty.
    """
    if not http_targets:
        return ""
    targets = ", ".join(http_targets)
    return (
        f"\nHTTP-dispatched delegations: [{targets}]\n"
        "NEVER use the Agent tool for these targets. All child agent work for "
        "the listed agents MUST go through HTTP dispatch via the delegation "
        "skill. If HTTP dispatch fails (curl error, server down), STOP and ask "
        "the user — do NOT fall back to the Agent tool.\n"
    )


def _subagent_dispatch_rules(subagent_targets: list[str]) -> str:
    """Rules for subagent-dispatched delegation targets.

    Returns the subagent dispatch block covering Agent-tool dispatch, SendMessage
    continuation, pass-through verdict, and the lack of Diecast run tracking.
    Returns empty string when subagent_targets is empty.
    """
    if not subagent_targets:
        return ""
    targets = ", ".join(subagent_targets)
    return (
        f"\nSubagent-dispatched delegations: [{targets}]\n"
        "- Dispatch via the Agent tool with subagent_type=\"<name>\" for the "
        "targets above (Claude Code platform idiom; not Diecast HTTP).\n"
        "- To continue a running subagent, use SendMessage targeting its agentId — "
        "do NOT call Agent again for the same subagent.\n"
        "- Never summarize the subagent's output. Return its verdict/report "
        "structurally (pass-through).\n"
        "- These runs do NOT appear in Diecast /api/agents/runs — the parent "
        "Claude Code conversation log is authoritative.\n"
    )


def _quick_reference_curl(goal_dir: str) -> str:
    """HTTP-dispatch curl + poll reference. Emitted only when http_targets is non-empty.

    Retains the `{YOUR_RUN_ID}` / `{GOAL_SLUG}` placeholders for post-assembly
    substitution by the caller.
    """
    return f"""
Quick reference (full patterns in the skill):

  CHILD_RUN_ID=$(curl -s -X POST {SERVER_URL}/api/agents/{{agent}}/trigger \\
    -H "Content-Type: application/json" \\
    -d '{{
      "goal_slug": "{{GOAL_SLUG}}",
      "parent_run_id": "{{YOUR_RUN_ID}}",
      "delegation_context": {{
        "agent_name": "{{agent}}",
        "instructions": "What the child should do",
        "context": {{
          "goal_title": "...",
          "artifacts": ["relevant artifact paths"],
          "prior_output": "summary of your work so far"
        }},
        "output": {{
          "output_dir": "{{output_dir}}",
          "expected_artifacts": ["what you expect back"]
        }}
      }}
    }}' | jq -r '.run_id')

  GOAL_DIR="{goal_dir}"   # use this exact value — injected from your prompt preamble
  TIMEOUT=2700; ELAPSED=0
  while [ $ELAPSED -lt $TIMEOUT ]; do
    [ -f "$GOAL_DIR/.agent-$CHILD_RUN_ID.output.json" ] && break
    sleep 10; ELAPSED=$((ELAPSED + 10))
  done
  # On timeout, check: curl {SERVER_URL}/api/agents/jobs/$CHILD_RUN_ID | jq '.status'
"""


def _partition_delegations_by_mode(
    allowed_delegations: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Partition allowed_delegations by the per-target dispatch_mode on AgentConfig.

    Returns (http_targets, subagent_targets). Preserves order within each mode.
    Unknown / unreadable configs default to http (matching AgentConfig default).
    """
    http_targets: list[str] = []
    subagent_targets: list[str] = []
    if not allowed_delegations:
        return http_targets, subagent_targets
    for name in allowed_delegations:
        try:
            mode = load_agent_config(name).dispatch_mode
        except Exception:
            mode = "http"
        if mode == "subagent":
            subagent_targets.append(name)
        else:
            http_targets.append(name)
    return http_targets, subagent_targets


# ---------------------------------------------------------------------------
# Agent prompt builder
# ---------------------------------------------------------------------------

def _build_agent_prompt(agent_name: str, goal_title: str, task_title: str,
                        task_outcome: str, goal_dir: str, run_id: str,
                        start_time_iso: str, context: str = "",
                        output_dir: str = "",
                        context_map_exists: bool = False,
                        context_mode: str = "full",
                        interactive: bool = False,
                        goal_context: str = "",
                        goal_slug: str = "",
                        allowed_delegations: list[str] | None = None) -> str:
    """Build the structured agent prompt with output.json instructions."""
    context_line = f"\nAdditional context: {context}" if context else ""
    artifact_dir = output_dir or goal_dir

    context_map_block = ""
    if context_map_exists and context_mode == "lightweight":
        context_map_block = f"""
Context: Read {goal_dir}/.context-map.md for goal context overview.
"""
    elif context_map_exists:
        context_map_block = f"""
Context instructions for this goal directory ({goal_dir}):
- Always read .collab.md and .human.md files directly — these are authoritative.
- For .ai.md files: read {goal_dir}/.context-map.md first for a TOC overview.
  Only deep-read individual .ai.md files when you need specific details beyond the TOC.
- If no .context-map.md exists, fall back to reading .ai.md files directly.
"""

    interactive_block = ""
    if interactive:
        interactive_block = """
INTERACTIVE SESSION: A human is watching this terminal and will respond to your questions.
You MUST ask clarifying questions before proceeding when the agent calls for it (e.g., scope
clarification, approval gates, ambiguous requirements). Do NOT auto-resolve or guess — pause
and wait for the user's response. Type your question, then STOP and wait for input.

When you delegate to child agents: after reviewing their output (see delegation instructions
below), present your findings to the user — gaps found, issues spotted, open questions — and ask
whether to fix, re-delegate, or accept as-is. Do NOT silently absorb child output without
giving the user a chance to weigh in.
"""

    preamble = f"""Your run ID: {run_id}
Goal slug: {goal_slug}

Diecast API routes ({SERVER_URL}):
  POST /api/agents/{{name}}/trigger        — dispatch a child agent
  GET  /api/agents/jobs/{{run_id}}          — get run details/status
  POST /api/agents/jobs/{{run_id}}/recheck  — recheck a completed/failed run
  POST /api/agents/runs/{{run_id}}/continue — send message to idle agent
  POST /api/agents/runs/{{run_id}}/cancel   — cancel an active run
  POST /api/agents/runs/{{run_id}}/fail     — mark run as failed
  POST /api/agents/runs/{{run_id}}/complete — mark run as completed
  DELETE /api/agents/runs/{{run_id}}        — delete a terminal run
  GET  /api/agents/runs                     — list all runs
  GET  /api/agents/runs?status=running      — filter runs by status
  GET  /api/agents/jobs/{{run_id}}?include=children — descendant tree (rollups attached)
  POST /api/tasks/{{task_id}}/run-agent     — trigger agent for a task
  Health check: curl -s {SERVER_URL}/api/agents/runs?status=running | head -1
"""

    http_targets, subagent_targets = _partition_delegations_by_mode(allowed_delegations)

    delegation_policy_block = (
        _universal_anti_inline(allowed_delegations or [])
        + _http_dispatch_rules(http_targets)
        + _subagent_dispatch_rules(subagent_targets)
    )

    quick_reference_block = _quick_reference_curl(goal_dir) if http_targets else ""

    raw_prompt = f"""{preamble}Use the {agent_name} agent.

Goal: {goal_title}
Task: {task_title}
Expected outcome: {task_outcome}
Output directory: {artifact_dir}
{context_line}{context_map_block}{interactive_block}{goal_context}
Work in {artifact_dir}. Write all artifacts there.
{delegation_policy_block}
Agent composition: If your task would benefit from another agent's capabilities,
invoke the `/cast-child-delegation` skill BEFORE dispatching any child. It covers
dispatch, polling, status checks, continue vs. new trigger, and parent-child context.
{quick_reference_block}
IMPORTANT — when you are completely finished (as your very last action), write this exact JSON structure to {goal_dir}/.agent-{run_id}.output.json:

{{
    "contract_version": "2",
    "agent_name": "{agent_name}",
    "task_title": "{task_title}",
    "status": "completed | partial | failed",
    "summary": "One paragraph describing what you accomplished",
    "artifacts": [
        {{"path": "relative/to/goal/dir/file.md", "type": "research|playbook|plan|code|data", "description": "What this file contains"}}
    ],
    "errors": [],
    "next_steps": ["Suggested follow-up actions for the user"],
    "human_action_needed": false,
    "human_action_items": [],
    "started_at": "{start_time_iso}",
    "completed_at": "<fill in current ISO timestamp when you write this file>"
}}

Status values:
- "completed" = all requested work done successfully
- "partial" = some work done, but not everything (explain in summary)
- "failed" = could not accomplish the task (explain in errors)

Set human_action_needed to true when:
- You need human approval before changes take effect
- You found data issues that need manual correction
- You have open questions that block completion
- You completed the work but something needs human verification
Keep human_action_items specific and actionable (what exactly to do).

Artifact paths must be relative to {goal_dir}.""" + _inject_error_memories(agent_name)

    # Substitute concrete values in delegation template
    raw_prompt = raw_prompt.replace("{YOUR_RUN_ID}", run_id).replace("{GOAL_SLUG}", goal_slug)
    return raw_prompt


# ---------------------------------------------------------------------------
# Agent registry lookup
#
# The registry is read directly from `agents/<name>/<name>.md` frontmatter at
# request time. The legacy `agents` SQLite table is intentionally unused (the
# sync engine that populated it was deleted in Phase 3b sp13 — see
# cast-server/docs/scope-prune.md). The on-disk frontmatter contract is
# pinned in agents/README.md.
# ---------------------------------------------------------------------------

_AGENT_REGISTRY_CACHE: dict[Path, tuple[float, dict]] = {}


def _parse_frontmatter(md_path: Path) -> dict | None:
    """Extract the YAML frontmatter from a markdown file."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    import yaml
    try:
        data = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _load_agent_registry(agents_dir: Path | None = None) -> dict[str, dict]:
    """Scan agents/<name>/<name>.md and return {name: agent_dict}."""
    root = (agents_dir or (DIECAST_ROOT / "agents")).resolve()
    if not root.is_dir():
        return {}

    mtime = root.stat().st_mtime
    cached = _AGENT_REGISTRY_CACHE.get(root)
    if cached is not None and cached[0] == mtime:
        return cached[1]

    registry: dict[str, dict] = {}
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or not entry.name.startswith("cast-"):
            continue
        md_path = entry / f"{entry.name}.md"
        if not md_path.is_file():
            continue
        fm = _parse_frontmatter(md_path)
        if not fm:
            continue
        name = fm.get("name") or entry.name
        registry[name] = {
            "name": name,
            "description": (fm.get("description") or "").strip(),
            "model": fm.get("model", ""),
            "type": fm.get("type", ""),
            "tags": fm.get("tags") if isinstance(fm.get("tags"), list) else [],
            "triggers": fm.get("triggers") if isinstance(fm.get("triggers"), list) else [],
            "input": fm.get("input", ""),
            "output": fm.get("output", ""),
            "last_tested": fm.get("last_tested", ""),
            "source_root": str(root),
        }

    _AGENT_REGISTRY_CACHE[root] = (mtime, registry)
    return registry


def get_all_agents(db_path=None, agents_dir: Path | None = None) -> list[dict]:
    """Get all agents from disk, sorted by name, augmented with run_count."""
    registry = _load_agent_registry(agents_dir)
    test_dir = os.environ.get("CAST_TEST_AGENTS_DIR")
    if test_dir:
        test_registry = _load_agent_registry(Path(test_dir))
        merged: dict[str, dict] = dict(test_registry)
        for name, agent in registry.items():
            if name in merged:
                logger.warning(
                    "Test agent %r collides with production agent of the same name; "
                    "preferring production entry.",
                    name,
                )
            merged[name] = agent
        registry = merged
    conn = get_connection(db_path)
    try:
        counts = dict(
            conn.execute(
                "SELECT agent_name, COUNT(*) FROM agent_runs GROUP BY agent_name"
            ).fetchall()
        )
    finally:
        conn.close()

    result = []
    for name in sorted(registry):
        agent = dict(registry[name])
        agent["run_count"] = counts.get(name, 0)
        result.append(agent)
    return result


def get_recommended_agents(goal_slug: str, db_path=None) -> list[dict]:
    """Get recommended agents for a goal, derived from task-level recommended_agent fields."""
    registry = _load_agent_registry()
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT DISTINCT recommended_agent FROM tasks
               WHERE goal_slug = ? AND recommended_agent IS NOT NULL AND status != 'completed'""",
            (goal_slug,),
        ).fetchall()
        agents = []
        for row in rows:
            agent_name = row["recommended_agent"]
            agent_info = registry.get(agent_name)
            if agent_info:
                agents.append(dict(agent_info))
            else:
                agents.append({"name": agent_name, "description": f"Agent: {agent_name}"})
        return agents
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Artifact wiring helper
# ---------------------------------------------------------------------------

def _wire_artifacts_to_task(run_id: str, artifacts: list | None, db_path=None) -> None:
    """Wire agent output artifacts to the linked task's task_artifacts field."""
    try:
        run = get_agent_run(run_id, db_path=db_path)
        if not run or not run.get("task_id") or not artifacts:
            return
        artifact_paths = [
            a["path"] for a in artifacts
            if isinstance(a, dict) and a.get("path")
        ]
        if artifact_paths:
            task_service.update_task(
                run["task_id"],
                task_artifacts=artifact_paths,
                db_path=db_path,
            )
            logger.info("Wired %d artifacts to task %s from run %s",
                        len(artifact_paths), run["task_id"], run_id)
    except Exception:
        logger.exception("Failed to wire artifacts for run %s", run_id)


# ---------------------------------------------------------------------------
# Output parsing helper — shared by _run_agent and recheck_failed_run
# ---------------------------------------------------------------------------

def _finalize_run(run_id: str, goal_dir: Path, session_id: str | None = None,
                  agent_name: str = "", task_title: str = "",
                  started_at: str = "", model: str | None = None,
                  working_dir: str | None = None,
                  db_path=None) -> None:
    """Read agent output files, update DB, wire artifacts, clean up dot files.

    Consolidates output parsing logic used by both _run_agent and recheck_failed_run.
    """
    done_file = goal_dir / f".agent-{run_id}.done"
    exitcode_file = goal_dir / f".agent-{run_id}.exitcode"
    output_file = goal_dir / f".agent-{run_id}.output.json"
    now = datetime.now(timezone.utc).isoformat()

    # Read exit code
    exit_code = 0 if output_file.exists() else 1
    if exitcode_file.exists():
        try:
            exit_code = int(exitcode_file.read_text().strip())
        except (ValueError, OSError):
            exit_code = 1

    # Read and parse output.json
    output_data = None
    artifacts = None
    error_message = None
    status = "completed" if exit_code == 0 else "failed"

    if output_file.exists():
        try:
            raw = json.loads(output_file.read_text())
            parsed = AgentOutput(**raw)
            output_data = parsed.model_dump()
            artifacts = parsed.artifacts
            status = parsed.status
            if parsed.errors:
                error_message = "; ".join(parsed.errors)
        except (json.JSONDecodeError, Exception) as e:
            output_data = None
            error_message = f"Malformed output.json: {e}"
            status = "failed"
    else:
        synthetic = AgentOutput(
            agent_name=agent_name,
            task_title=task_title,
            status="failed",
            summary=f"Agent exited with code {exit_code}. No output.json was produced.",
            errors=[f"Process exit code: {exit_code}", "No output file written"],
            next_steps=["Check the terminal tab for error output", "Re-run the agent"],
            started_at=started_at,
            completed_at=now,
        )
        output_data = synthetic.model_dump()
        status = "failed"
        error_message = f"Agent exited with code {exit_code}. No output.json produced."

    # Attention flagging: explicit human_action_needed or partial status
    needs_attention = 0
    if output_data:
        if output_data.get("human_action_needed"):
            needs_attention = 1
    if status == "partial":
        needs_attention = 1

    # Read token usage and context usage from session JSONL
    context_usage = None
    if session_id:
        session_jsonl_dir = _resolve_jsonl_dir(working_dir)
        input_tokens, cache_write_tokens, cache_read_tokens, output_tokens = _read_session_tokens(
            session_id, session_jsonl_dir=session_jsonl_dir)
        # Peak context usage (fallback — SessionEnd handler may overwrite with breakdown)
        context_usage = _read_context_usage(session_id, session_jsonl_dir=session_jsonl_dir, working_dir=working_dir)
    else:
        input_tokens, cache_write_tokens, cache_read_tokens, output_tokens = None, None, None, None
    cost_usd = _estimate_cost(input_tokens, cache_write_tokens, cache_read_tokens, output_tokens, model)

    # resume_command — set from session_id so the run can be continued later
    resume_command = None
    if session_id:
        if working_dir:
            wd_quoted = shlex.quote(working_dir)
            resume_command = f"cd {wd_quoted} && env -u CLAUDECODE claude --resume {session_id} --dangerously-skip-permissions"
        else:
            resume_command = f"env -u CLAUDECODE claude --resume {session_id} --dangerously-skip-permissions"

    # Populate result_summary (first 300 chars of output summary)
    result_summary = None
    if output_data and isinstance(output_data, dict):
        summary = output_data.get("summary", "")
        result_summary = summary[:300] if summary else None

    # Update DB
    extra = {}
    if resume_command is not None:
        extra["resume_command"] = resume_command
    if context_usage is not None:
        extra["context_usage"] = context_usage

    update_agent_run(
        run_id,
        status=status,
        output=output_data,
        artifacts=artifacts,
        error_message=error_message,
        exit_code=exit_code,
        input_tokens=input_tokens,
        cache_write_tokens=cache_write_tokens,
        cache_read_tokens=cache_read_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        completed_at=now,
        needs_attention=needs_attention,
        result_summary=result_summary,
        **extra,
        db_path=db_path,
    )

    # Wire artifacts to task
    if status == "completed":
        _wire_artifacts_to_task(run_id, artifacts, db_path=db_path)

    # Clean up dot files (keep output_file — useful for parent polling)
    log_file = goal_dir / f".agent-{run_id}.log"
    for f in (done_file, exitcode_file):
        if f.exists():
            f.unlink()
    # Headless log: clean up on success, retain on failure for debugging
    if log_file.exists() and status == "completed":
        log_file.unlink()

    logger.info("Agent run %s finished: %s (tokens: %s/%s, cost: %s)",
                run_id, status, input_tokens, output_tokens, cost_usd)

    # Error memory extraction (only for failed/partial runs)
    if status in ("failed", "partial"):
        try:
            extract_and_store_error(
                agent_name=agent_name,
                run_id=run_id,
                output_json=output_data,
                error_message=error_message,
            )
        except Exception:
            logger.exception("Failed to store error memory for run %s", run_id)


# ---------------------------------------------------------------------------
# Agent execution — trigger + poll
# ---------------------------------------------------------------------------

def _get_delegation_depth(run_id: str, db_path=None) -> int:
    """Walk parent chain to compute delegation depth."""
    depth = 0
    current = run_id
    while current:
        run = get_agent_run(current, db_path=db_path)
        if not run or not run.get("parent_run_id"):
            break
        current = run["parent_run_id"]
        depth += 1
        if depth > MAX_DELEGATION_DEPTH + 1:
            break  # Safety: prevent infinite loop
    return depth


async def trigger_agent(agent_name: str, goal_slug: str, context: str = "",
                        task_id: int | None = None, input_params: dict | None = None,
                        scheduled_at: str | None = None,
                        parent_run_id: str | None = None,
                        delegation_context: DelegationContext | None = None,
                        db_path=None) -> str:
    """Enqueue an agent run, with optional delegation from a parent.

    Creates a DB record as 'pending' (or 'scheduled' if scheduled_at is in the future).
    The dispatcher launches it when a slot is available.
    """
    # Refuse dispatch if the goal has no usable external_project_dir.
    # Server is the single source of truth for this precondition;
    # see docs/specs/cast-delegation-contract.collab.md.
    _validate_dispatch_preconditions(goal_slug, db_path=db_path)

    # Validate delegation allowlist and depth
    if parent_run_id:
        parent_run = get_agent_run(parent_run_id, db_path=db_path)
        if not parent_run:
            raise ValueError(f"Parent run {parent_run_id} not found")
        parent_config = load_agent_config(parent_run["agent_name"])

        if agent_name not in parent_config.allowed_delegations:
            raise ValueError(
                f"Agent {parent_run['agent_name']} is not allowed to delegate to {agent_name}. "
                f"Allowed: {parent_config.allowed_delegations}"
            )

        depth = _get_delegation_depth(parent_run_id, db_path=db_path)
        if depth >= MAX_DELEGATION_DEPTH:
            raise ValueError(
                f"Max delegation depth ({MAX_DELEGATION_DEPTH}) exceeded. "
                f"Current depth: {depth}"
            )

    # Determine initial status
    status = "pending"
    if scheduled_at:
        try:
            sched_time = datetime.fromisoformat(scheduled_at)
            if sched_time > datetime.now(timezone.utc):
                status = "scheduled"
        except ValueError:
            pass  # Invalid timestamp → treat as immediate (pending)

    run_id = create_agent_run(
        agent_name, goal_slug, task_id, input_params,
        scheduled_at=scheduled_at, status=status,
        parent_run_id=parent_run_id,
        db_path=db_path,
    )

    # Write delegation context file
    if delegation_context:
        goal_dir = GOALS_DIR / goal_slug
        context_file = goal_dir / f".delegation-{run_id}.json"
        context_file.write_text(delegation_context.model_dump_json(indent=2))

    logger.info("Enqueued agent run %s: %s for %s/%s (status=%s, parent=%s)",
                run_id, agent_name, goal_slug, task_id, status, parent_run_id)
    return run_id


def _get_goal_title(goal_slug: str, db_path=None) -> str:
    """Get goal title from DB, falling back to slug."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT title FROM goals WHERE slug = ?", (goal_slug,)).fetchone()
    finally:
        conn.close()
    return row["title"] if row else goal_slug


async def invoke_agent(agent_name: str, goal_slug: str | None = None,
                       context: str = "", task_id: int | None = None,
                       db_path=None) -> dict:
    """Invoke an agent from CLI — creates run, assembles prompt, returns both.

    Replaces register_cli_agent(). Single entry point for CLI invocation.
    Returns {run_id, prompt, config}.
    """
    config = load_agent_config(agent_name)

    # Fallback to system-ops goal if no goal_slug
    effective_slug = goal_slug or "system-ops"

    # Validate goal exists — fall back to system-ops if not found
    goal_title = _get_goal_title(effective_slug, db_path=db_path)
    if goal_title == effective_slug:
        conn = get_connection(db_path)
        try:
            exists = conn.execute("SELECT 1 FROM goals WHERE slug = ?", (effective_slug,)).fetchone()
        finally:
            conn.close()
        if not exists:
            effective_slug = "system-ops"

    now = datetime.now(timezone.utc).isoformat()

    run_id = create_agent_run(
        agent_name=agent_name,
        goal_slug=effective_slug,
        task_id=task_id,
        input_params={"source": "cli", "context": context},
        status="running",
        db_path=db_path,
    )
    update_agent_run(run_id, started_at=now, db_path=db_path)

    # Conditional tmux session for delegating agents
    if config.allowed_delegations:
        tmux = _get_tmux()
        session_name = f"agent-{run_id}"
        tmux.create_session(session_name, "bash", str(DIECAST_ROOT))

    # Assemble prompt with concrete values
    goal_title = _get_goal_title(effective_slug, db_path=db_path)
    task_title = ""
    task_outcome = ""
    if task_id:
        task = task_service.get_task(task_id, db_path=db_path)
        if task:
            task_title = task.get("title", "")
            task_outcome = task.get("outcome", "")

    goal_dir = str(GOALS_DIR / effective_slug)

    # Resolve directory metadata for invoke path (Phase 3.1, Req 4.1)
    from cast_server.services import goal_service
    _invoke_goal_data = goal_service.get_goal(effective_slug, db_path=db_path)
    _invoke_ext_proj = _invoke_goal_data.get("external_project_dir") if _invoke_goal_data else None
    _invoke_working_dir = str(DIECAST_ROOT)
    _invoke_tracking_dir = goal_dir
    if _invoke_ext_proj:
        _ext_path = Path(_invoke_ext_proj).expanduser()
        if _ext_path.exists():
            _invoke_working_dir = str(_ext_path)
            _invoke_tracking_dir = str(_ext_path / ".cast")
    directories_json = json.dumps({
        "tracking_dir": _invoke_tracking_dir,
        "artifact_dir": _invoke_working_dir,
        "working_dir": _invoke_working_dir,
        "goal_dir": goal_dir,
        "external_project_dir": _invoke_ext_proj or None,
    })
    update_agent_run(run_id, directories=directories_json, working_dir=_invoke_working_dir, db_path=db_path)

    prompt = _build_agent_prompt(
        agent_name=agent_name,
        goal_title=goal_title,
        task_title=task_title or context,
        task_outcome=task_outcome or context,
        goal_dir=goal_dir,
        run_id=run_id,
        start_time_iso=now,
        context=context,
        context_mode=config.context_mode,
        interactive=config.interactive,
        goal_slug=effective_slug,
        allowed_delegations=config.allowed_delegations or None,
    )

    return {
        "run_id": run_id,
        "prompt": prompt,
        "config": {
            "model": config.model,
            "timeout_minutes": config.timeout_minutes,
        },
    }


async def continue_agent_run(run_id: str, message: str, db_path=None) -> None:
    """Send a follow-up message to an existing agent's tmux session.

    Use instead of trigger_agent when resuming a paused/completed session
    rather than starting fresh work.
    """
    run = get_agent_run(run_id, db_path=db_path)
    if not run:
        raise ValueError(f"Run {run_id} not found")

    # Verify tmux session still exists
    tmux = _get_tmux()
    session_name = f"agent-{run_id}"
    if not tmux.session_exists(session_name):
        raise ValueError(f"Session for {run_id} no longer exists -- use trigger_agent for a new run")

    # Deliver message via file (avoids Claude Code paste-preview mode for multiline text)
    goal_dir = GOALS_DIR / run["goal_slug"]
    prompt_file = goal_dir / f".agent-{run_id}.continue"
    prompt_file.write_text(message)
    tmux.send_keys(session_name, f"Read {prompt_file} and follow its instructions.")
    time.sleep(AGENT_SENDKEY_DELAY)
    tmux.send_enter(session_name)

    # Transition status back to running
    update_agent_run(run_id, status="running", db_path=db_path)



async def _launch_agent(run_id: str, db_path=None) -> None:
    """Launch an enqueued agent run in a tmux session.

    Called by the dispatcher when a slot opens. Creates a tmux session with Claude,
    waits for readiness, delivers the prompt, and marks run as 'running'.
    The monitor loop handles completion detection (no per-run polling).
    """
    run = get_agent_run(run_id, db_path=db_path)
    if not run:
        logger.error("_launch_agent: run %s not found", run_id)
        return
    if run["status"] not in ("pending",):
        logger.warning("_launch_agent: run %s has status %s, skipping", run_id, run["status"])
        return

    try:
        tmux = _get_tmux()
        agent_name = run["agent_name"]
        goal_slug = run["goal_slug"]
        task_id = run.get("task_id")
        input_params = run.get("input_params") or {}
        goal_dir = GOALS_DIR / goal_slug
        session_id = None  # Discovered by monitor loop from Claude CLI JSONL
        session_name = f"agent-{run_id}"

        # Resolve context fresh at launch time (important for scheduled runs)
        task_title = input_params.get("task_title", "")
        task_outcome = input_params.get("task_outcome", "")
        goal_title = input_params.get("goal_title", goal_slug)

        # Look up goal config for external directory fields
        from cast_server.services import goal_service
        goal_data = goal_service.get_goal(goal_slug, db_path=db_path)
        gstack_dir = goal_data.get("gstack_dir") if goal_data else None
        external_project_dir = goal_data.get("external_project_dir") if goal_data else None

        # Determine working directory and cast_goal_dir.
        # trigger_agent enforces external_project_dir as a dispatch precondition,
        # so reaching this branch with an unusable value means something bypassed
        # the API contract — fail loud rather than silently fall back.
        if not external_project_dir:
            raise MissingExternalProjectDirError(goal_slug, None)
        expanded_ext = Path(external_project_dir).expanduser()
        if not expanded_ext.is_dir():
            raise MissingExternalProjectDirError(goal_slug, external_project_dir)
        working_dir = str(expanded_ext)
        goal_service.ensure_cast_symlink(
            goal_slug, external_project_dir,
            folder_path=goal_data.get("folder_path") if goal_data else None,
        )
        cast_goal_dir = str(expanded_ext / ".cast")

        # Determine phase-aware output directory
        task = task_service.get_task(task_id, db_path=db_path) if task_id else None
        is_exploration = bool(task and task.get("phase") == "exploration")
        if is_exploration:
            output_dir = str(Path(cast_goal_dir) / "exploration")
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        else:
            output_dir = working_dir

        config = load_agent_config(agent_name)

        # Agent-config artifact_directory override (Req 4.3)
        # Exploration phase is exempt -- always routes to cast_goal_dir/exploration/
        if not is_exploration and config.artifact_directory == "external_project_dir":
            if external_project_dir:
                _ext_artifact_path = Path(external_project_dir).expanduser()
                if _ext_artifact_path.exists():
                    output_dir = str(_ext_artifact_path)
                else:
                    logger.warning(
                        "Agent %s has artifact_directory=external_project_dir but "
                        "path %s does not exist. Falling back to default routing.",
                        agent_name, external_project_dir,
                    )
            else:
                logger.warning(
                    "Agent %s has artifact_directory=external_project_dir but "
                    "goal %s has no external_project_dir configured. "
                    "Falling back to default routing.",
                    agent_name, goal_slug,
                )

        # Generate/update context map
        context_map_exists = False
        try:
            from cast_server.services.context_map import ensure_context_map
            context_map_path = ensure_context_map(goal_dir)
            context_map_exists = context_map_path is not None
        except Exception:
            logger.exception("Failed to generate context map for %s", goal_slug)

        # Inject goal directory context (gstack, external project)
        goal_context = _inject_context(
            agent_name, goal_slug,
            gstack_dir=gstack_dir,
            external_project_dir=external_project_dir,
        )

        started_at = datetime.now(timezone.utc).isoformat()
        prompt = _build_agent_prompt(
            agent_name=agent_name,
            goal_title=goal_title,
            task_title=task_title,
            task_outcome=task_outcome,
            goal_dir=cast_goal_dir,
            run_id=run_id,
            start_time_iso=started_at,
            context=input_params.get("context", ""),
            output_dir=output_dir,
            context_map_exists=context_map_exists,
            context_mode=config.context_mode,
            interactive=config.interactive,
            goal_context=goal_context,
            goal_slug=goal_slug,
            allowed_delegations=config.allowed_delegations or None,
        )

        # Build directory metadata JSON (Phase 3.1, Req 4.1)
        directories_json = json.dumps({
            "tracking_dir": cast_goal_dir,
            "artifact_dir": output_dir,
            "working_dir": working_dir,
            "goal_dir": str(goal_dir),
            "external_project_dir": external_project_dir or None,
        })

        # Capture git branch
        git_branch = None
        try:
            git_result = subprocess.run(
                ["git", "-C", working_dir, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=5
            )
            if git_result.returncode == 0:
                git_branch = git_result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Include delegation context file reference in prompt
        context_file = goal_dir / f".delegation-{run_id}.json"
        if context_file.exists():
            prompt = (
                f"Read the delegation context from `{context_file}` first, "
                f"then follow the instructions within.\n\n{prompt}"
            )

        # Build meaningful session display name (Phase 3.4, Req 2.2)
        if task_title:
            session_name_display = f"{agent_name} | {goal_title} | {task_title[:40]}"
        else:
            session_name_display = f"{agent_name} | {goal_title}"
        # Truncate to 80 chars for terminal title compatibility
        session_name_display = session_name_display[:80]

        model = config.model
        # Use --name flag to set human-readable session display name
        escaped_display = session_name_display.replace('"', '\\"')
        cmd = f'env -u CLAUDECODE claude --dangerously-skip-permissions --model {model} --name "{escaped_display}"'

        # Child agent: own tmux session + terminal tab
        parent_run_id = run.get("parent_run_id")
        if parent_run_id:
            tmux.create_session(session_name, cmd, working_dir)

            # Open terminal window early (matches top-level flow) so the SIGWINCH
            # from terminal attachment fires during startup, not after prompt delivery.
            child_title = f"[Child] {agent_name}"
            if task_title:
                child_title += f" | {task_title[:40]}"
            child_title = child_title[:80]
            try:
                tmux.open_terminal(session_name, title=child_title)
            except ResolutionError as exc:
                tmux.kill_session(session_name)
                logger.error(
                    "Child agent %s could not start — terminal resolution failed: %s",
                    run_id, exc,
                )
                raise TmuxError(
                    f"Child agent {run_id} could not start: {exc}"
                ) from exc

            if not tmux.wait_for_ready(session_name, timeout_seconds=AGENT_READY_TIMEOUT):
                tmux.kill_session(session_name)
                raise TmuxError(f"Child Claude did not become ready in session {session_name}")

            # Deliver prompt via file (avoids Claude Code paste-preview mode for multiline text)
            prompt_file = goal_dir / f".agent-{run_id}.prompt"
            prompt_file.write_text(prompt)
            tmux.send_keys(session_name, f"Read the file {prompt_file} and follow its instructions exactly.")
            time.sleep(AGENT_SENDKEY_DELAY)
            tmux.send_enter(session_name)

            update_agent_run(
                run_id,
                status="running",
                started_at=started_at,
                session_id=session_id,
                session_name=session_name_display,
                git_branch=git_branch,
                working_dir=working_dir,
                directories=directories_json,
                db_path=db_path,
            )
            _total_paused[run_id] = 0.0

            logger.info("Launched child agent %s: %s (session %s)", run_id, agent_name, session_name)
            return

        # Warn if both interactive and headless are set — interactive wins
        if config.interactive and config.headless:
            logger.warning(
                "Agent %s has both interactive and headless set — interactive overrides headless. "
                "Note: headless=True alone still requires a configured GUI terminal today; "
                "real headless dispatch is a separate follow-up.",
                agent_name,
            )

        # Normal (top-level) launch — tmux session creation
        tmux.create_session(session_name, cmd, working_dir)

        # Open visible terminal for all top-level agents (headless = non-interactive, not hidden)
        top_title = f"[Diecast] {agent_name} | goal: {goal_slug}"
        top_title = top_title[:80]
        try:
            tmux.open_terminal(session_name, title=top_title)
        except ResolutionError as exc:
            tmux.kill_session(session_name)
            logger.error(
                "Agent %s could not start — terminal resolution failed: %s",
                run_id, exc,
            )
            raise TmuxError(
                f"Agent {run_id} could not start: {exc}"
            ) from exc

        # Wait for Claude to be ready (input field visible)
        if not tmux.wait_for_ready(session_name, timeout_seconds=AGENT_READY_TIMEOUT):
            tmux.kill_session(session_name)
            raise TmuxError(f"Claude did not become ready within {AGENT_READY_TIMEOUT}s")

        # Deliver prompt via file (avoids Claude Code paste-preview mode for multiline text)
        prompt_file = goal_dir / f".agent-{run_id}.prompt"
        prompt_file.write_text(prompt)
        tmux.send_keys(session_name, f"Read the file {prompt_file} and follow its instructions exactly.")
        time.sleep(AGENT_SENDKEY_DELAY)
        tmux.send_enter(session_name)

        # Update run record
        update_agent_run(
            run_id,
            status="running",
            started_at=started_at,
            session_id=session_id,
            session_name=session_name_display,
            git_branch=git_branch,
            working_dir=working_dir,
            directories=directories_json,
            db_path=db_path,
        )
        _total_paused[run_id] = 0.0

        logger.info("Launched agent run %s: %s (tmux session: %s)", run_id, agent_name, session_name)

    except (TmuxError, Exception) as e:
        # Mark run as failed immediately — no retry
        logger.exception("Failed to launch agent run %s", run_id)
        update_agent_run(
            run_id,
            status="failed",
            error_message=f"Launch failed: {e}",
            completed_at=datetime.now(timezone.utc).isoformat(),
            db_path=db_path,
        )


# ---------------------------------------------------------------------------
# Monitor loop — centralized state checking for all running agents
# ---------------------------------------------------------------------------

async def _monitor_loop(db_path=None) -> None:
    """Every 5 seconds, check all running agents' tmux pane state."""
    logger.info("Monitor loop started")
    while True:
        try:
            async with _state_lock:
                await _check_all_agents(db_path=db_path)
        except Exception:
            logger.exception("Monitor loop error")
        await asyncio.sleep(AGENT_MONITOR_INTERVAL)



async def _check_all_agents(db_path=None) -> None:
    """Check state of all running/rate_limited agents."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT * FROM agent_runs WHERE status IN ('running', 'rate_limited')"
    ).fetchall()
    conn.close()
    running_runs = [_row_to_dict(r) for r in rows]

    if not running_runs:
        return

    tmux = _get_tmux()

    # Batch check pane commands (one subprocess call)
    pane_commands = tmux.list_all_pane_commands()

    for run in running_runs:
        run_id = run["id"]

        # All agents (parent or child) have their own tmux session
        session_name = f"agent-{run_id}"
        pane_cmd = pane_commands.get(session_name, "")

        # Only capture pane content for sessions running claude
        if pane_cmd == "claude" or not pane_cmd:
            pane_content = tmux.capture_pane(session_name, lines=15)
        else:
            pane_content = []

        state = detect_agent_state(pane_content, pane_cmd)

        # Discover real Claude session ID (once per run)
        if run_id not in _session_id_resolved and run.get("started_at"):
            real_session_id = _discover_claude_session_id(run["started_at"], run_id, working_dir=run.get("working_dir"))
            if real_session_id:
                wd = run.get("working_dir") or ""
                wd_quoted = shlex.quote(wd) if wd else ""
                resume_cmd = f"cd {wd_quoted} && env -u CLAUDECODE claude --resume {real_session_id} --dangerously-skip-permissions" if wd else f"env -u CLAUDECODE claude --resume {real_session_id} --dangerously-skip-permissions"
                update_agent_run(run_id, session_id=real_session_id, resume_command=resume_cmd, db_path=db_path)
                run["session_id"] = real_session_id
                _session_id_resolved.add(run_id)

        await _handle_state_transition(run, state, db_path=db_path)


async def _handle_state_transition(run: dict, state: AgentState, db_path=None) -> None:
    """Handle state changes for a running agent."""
    now = time.time()
    run_id = run["id"]

    if state == AgentState.WORKING:
        # Agent is active — clear idle timer
        _idle_since.pop(run_id, None)
        return

    if state in (AgentState.IDLE, AgentState.SHELL_RETURNED):
        # Check for .done file (dual completion signal)
        goal_dir = GOALS_DIR / run["goal_slug"]
        done_file = goal_dir / f".agent-{run_id}.done"
        output_file = goal_dir / f".agent-{run_id}.output.json"

        if done_file.exists() or output_file.exists():
            await _finalize_run_from_monitor(run, db_path=db_path)
            return

        if state == AgentState.SHELL_RETURNED:
            tmux = _get_tmux()
            session_name = f"agent-{run_id}"
            if not tmux.session_exists(session_name):
                update_agent_run(
                    run_id, status="failed",
                    error_message="Agent process exited without producing output",
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    db_path=db_path,
                )
                _idle_since.pop(run_id, None)
                _total_paused.pop(run_id, None)
                return

        # Interactive agents: skip idle-based stuck detection entirely.
        config = load_agent_config(run["agent_name"])
        if config.interactive:
            _idle_since.pop(run_id, None)  # Reset any accumulated idle time
            return

        # Idle timer tracking (non-interactive agents only)
        if run_id not in _idle_since:
            _idle_since[run_id] = now

        idle_duration = now - _idle_since[run_id]
        if idle_duration >= AGENT_IDLE_STUCK:
            update_agent_run(run_id, status="stuck", db_path=db_path)
            logger.warning("Agent %s (%s) stuck: %dm idle", run["agent_name"], run_id, idle_duration / 60)
        elif idle_duration >= AGENT_IDLE_WARNING:
            update_agent_run(run_id, needs_attention=1, db_path=db_path)
            logger.warning("Agent %s (%s) possibly stuck (%dm idle)", run["agent_name"], run_id, idle_duration / 60)

    elif state == AgentState.WAITING_INPUT:
        # [y/n] permission prompt — stuck even for interactive agents.
        # Interactive agents wait for user input in IDLE state (input field visible),
        # not via [y/n] prompts. A [y/n] prompt means a tool permission wasn't pre-authorized.
        update_agent_run(run_id, status="stuck", needs_attention=1, db_path=db_path)
        logger.warning("Agent %s (%s) waiting for input (y/n prompt)", run["agent_name"], run_id)

    elif state == AgentState.RATE_LIMITED:
        if run.get("status") != "rate_limited":
            # First detection — transition to rate_limited
            tmux = _get_tmux()
            session_name = f"agent-{run_id}"
            pane_content = tmux.capture_pane(session_name, lines=30)
            pane_text = "\n".join(pane_content)
            resume_at = parse_rate_limit_reset(pane_text)

            _cooldown_until[run_id] = resume_at
            update_agent_run(run_id, status="rate_limited", db_path=db_path)

            # Record pause start
            pause_entry = {
                "started_at": datetime.now(timezone.utc).isoformat(),
                "reset_time_parsed": resume_at.isoformat(),
            }
            _current_pause[run_id] = pause_entry

            logger.info(
                "Agent %s (%s) rate limited. Resume at %s",
                run["agent_name"], run_id, resume_at.strftime("%H:%M")
            )
        else:
            # Already rate_limited — check if cooldown expired
            resume_at = _cooldown_until.get(run_id)
            if resume_at and datetime.now() >= resume_at:
                # Resume: send Enter to tmux pane
                tmux = _get_tmux()
                session_name = f"agent-{run_id}"
                tmux.send_enter(session_name)
                update_agent_run(run_id, status="running", db_path=db_path)

                # Record pause end
                pause_entry = _current_pause.pop(run_id, {})
                pause_entry["ended_at"] = datetime.now(timezone.utc).isoformat()
                if "started_at" in pause_entry:
                    started = datetime.fromisoformat(pause_entry["started_at"])
                    ended = datetime.now(timezone.utc)
                    pause_entry["duration_seconds"] = int(
                        (ended - started).total_seconds()
                    )

                # Append to rate_limit_pauses JSON array
                existing = json.loads(run.get("rate_limit_pauses") or "[]")
                existing.append(pause_entry)
                update_agent_run(run_id, rate_limit_pauses=json.dumps(existing), db_path=db_path)

                # Update paused time for active_execution_seconds
                duration = pause_entry.get("duration_seconds", 0)
                _total_paused[run_id] = _total_paused.get(run_id, 0) + duration

                _cooldown_until.pop(run_id, None)
                logger.info("Agent %s (%s) resumed after rate limit", run["agent_name"], run_id)


async def _finalize_run_from_monitor(run: dict, db_path=None) -> None:
    """Finalize a run detected as complete by the monitor loop, including timing."""
    run_id = run["id"]
    goal_dir = GOALS_DIR / run["goal_slug"]

    config = load_agent_config(run["agent_name"])
    input_params = run.get("input_params") or {}
    task_title = input_params.get("task_title", "") if isinstance(input_params, dict) else ""

    _finalize_run(
        run_id, goal_dir,
        session_id=run.get("session_id"),
        agent_name=run["agent_name"],
        task_title=task_title,
        started_at=run.get("started_at") or "",
        model=config.model,
        working_dir=run.get("working_dir"),
        db_path=db_path,
    )

    # Calculate active execution time
    started_at = run.get("started_at")
    if started_at:
        try:
            started = datetime.fromisoformat(started_at)
            completed = datetime.now(timezone.utc)
            wall_seconds = (completed - started).total_seconds()
            paused_seconds = _total_paused.get(run_id, 0)
            active_seconds = max(0, int(wall_seconds - paused_seconds))
            update_agent_run(run_id, active_execution_seconds=active_seconds, db_path=db_path)
        except (ValueError, TypeError):
            pass

    # Cleanup prompt file if it exists
    prompt_file = goal_dir / f".agent-{run_id}.prompt"
    if prompt_file.exists():
        prompt_file.unlink()

    # Clean up delegation context file
    delegation_file = goal_dir / f".delegation-{run_id}.json"
    if delegation_file.exists():
        delegation_file.unlink()

    # Auto-close session 30s after completion (terminal tab/window closes when tmux session dies)
    session_name = f"agent-{run_id}"
    asyncio.create_task(_cleanup_parent_session(session_name))

    # Cleanup in-memory state
    _idle_since.pop(run_id, None)
    _total_paused.pop(run_id, None)
    _cooldown_until.pop(run_id, None)
    _current_pause.pop(run_id, None)



async def _cleanup_parent_session(session_name: str) -> None:
    """Auto-close parent tmux session after completion. Terminal window closes automatically."""
    await asyncio.sleep(AGENT_SESSION_CLEANUP_DELAY)
    try:
        tmux = _get_tmux()
        tmux.kill_session(session_name)
        logger.info("Auto-closed session %s", session_name)
    except (TmuxError, Exception):
        logger.debug("Session %s already closed", session_name)


# ---------------------------------------------------------------------------
# Recheck failed runs — recover from timeout when agent finished late
# ---------------------------------------------------------------------------

def recheck_failed_run(run_id: str, db_path=None) -> dict | None:
    """Re-examine a failed or stuck run's dot files on disk.

    Handles runs stuck in 'failed', 'running', or 'pending' status.
    If the agent finished after the polling timeout (or the polling task
    was interrupted), the .done and .output.json files will still be on disk.
    This function reads them, updates the DB record, cleans up, and returns
    the updated run dict.  Returns None if recovery isn't possible.
    """
    run = get_agent_run(run_id, db_path=db_path)
    if not run or run["status"] not in ("failed", "running", "pending"):
        return None

    goal_slug = run["goal_slug"]
    if not goal_slug and run.get("input_params"):
        try:
            params = json.loads(run["input_params"]) if isinstance(run["input_params"], str) else run["input_params"]
            goal_slug = params.get("goal_slug")
        except (json.JSONDecodeError, TypeError):
            pass
    if not goal_slug:
        return None

    goal_dir = GOALS_DIR / goal_slug
    done_file = goal_dir / f".agent-{run_id}.done"
    output_file = goal_dir / f".agent-{run_id}.output.json"

    if not output_file.exists() and not done_file.exists():
        return None  # Agent still hasn't finished

    model = load_agent_config(run["agent_name"]).model
    input_params = run.get("input_params") or {}
    task_title = input_params.get("task_title", "") if isinstance(input_params, dict) else ""
    _finalize_run(
        run_id, goal_dir,
        session_id=run.get("session_id"),
        agent_name=run["agent_name"],
        task_title=task_title,
        started_at=run.get("started_at") or "",
        model=model,
        working_dir=run.get("working_dir"),
        db_path=db_path,
    )

    logger.info("Rechecked run %s: recovered", run_id)
    return get_agent_run(run_id, db_path=db_path)


def _promote_scheduled_runs(db_path=None) -> int:
    """Promote scheduled runs whose scheduled_at has passed to pending.

    Returns the number of promoted runs.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection(db_path)
    cursor = conn.execute(
        "UPDATE agent_runs SET status = 'pending' WHERE status = 'scheduled' AND scheduled_at <= ?",
        (now,),
    )
    count = cursor.rowcount
    conn.commit()
    conn.close()
    if count:
        logger.info("Promoted %d scheduled run(s) to pending", count)
    return count


async def _dispatcher_loop(db_path=None) -> None:
    """Background loop: promote scheduled runs, launch pending runs up to concurrency limit.

    Runs every 10 seconds. Wrapped in try/except so one bad iteration doesn't kill the loop.
    """
    logger.info("Dispatcher started")
    while True:
        try:
            # Step 1: Promote scheduled → pending
            _promote_scheduled_runs(db_path=db_path)

            # Step 2: Count running, launch pending if under limit
            conn = get_connection(db_path)
            running_count = conn.execute(
                "SELECT COUNT(*) FROM agent_runs WHERE status = 'running'"
            ).fetchone()[0]

            if running_count < MAX_CONCURRENT_AGENTS:
                slots = MAX_CONCURRENT_AGENTS - running_count
                pending_runs = conn.execute(
                    "SELECT id FROM agent_runs WHERE status = 'pending' ORDER BY created_at ASC LIMIT ?",
                    (slots,),
                ).fetchall()
                conn.close()

                for row in pending_runs:
                    try:
                        # Check escalation before launching
                        run = get_agent_run(row["id"], db_path=db_path)
                        if run and not should_auto_retry(run["agent_name"]):
                            logger.warning(
                                "Skipping run %s: agent %s has escalated error patterns",
                                row["id"], run["agent_name"]
                            )
                            update_agent_run(
                                row["id"],
                                status="failed",
                                error_message="Auto-retry blocked: agent has escalated error patterns (3+ recurring failures). Resolve error memories first.",
                                completed_at=datetime.now(timezone.utc).isoformat(),
                                db_path=db_path,
                            )
                            continue
                        await _launch_agent(row["id"], db_path=db_path)
                    except Exception:
                        logger.exception("Dispatcher: failed to launch run %s", row["id"])
            else:
                conn.close()

        except Exception:
            logger.exception("Dispatcher loop iteration failed")

        await asyncio.sleep(10)


async def start_background_loops(db_path=None) -> None:
    """Start both dispatcher and monitor as independent async tasks."""
    asyncio.create_task(_dispatcher_loop(db_path=db_path))
    asyncio.create_task(_monitor_loop(db_path=db_path))


async def start_dispatcher(db_path=None) -> None:
    """Public entry point for background loops. Called from app.py lifespan."""
    await start_background_loops(db_path=db_path)


def recover_stale_runs(db_path=None) -> list[dict]:
    """Enhanced orphan recovery with tmux session check.

    Pass 1: Check tmux session existence for running/rate_limited runs.
            - Session alive → resume monitoring (monitor loop picks it up)
            - Session dead → attempt dot-file recovery, else force-fail
    Pass 2: Pending runs are left for the dispatcher. Scheduled runs untouched.
    """
    conn = get_connection(db_path)
    stale_rows = conn.execute(
        "SELECT * FROM agent_runs WHERE status IN ('running', 'rate_limited', 'pending')"
    ).fetchall()
    conn.close()

    recovered = []
    try:
        tmux = _get_tmux()
    except TmuxError:
        tmux = None
        logger.warning("tmux not available for orphan recovery — force-failing all running runs")

    for row in stale_rows:
        run = _row_to_dict(row)
        run_id = run["id"]

        if run["status"] == "pending":
            # Pending runs: attempt dot-file recovery only
            result = recheck_failed_run(run_id, db_path=db_path)
            if result:
                recovered.append(result)
                logger.info("Startup recovery: pending run %s → %s", run_id, result["status"])
            continue

        # Running/rate_limited runs: check tmux session
        session_name = f"agent-{run_id}"

        if tmux and tmux.session_exists(session_name):
            # Session alive → monitor loop will resume watching it
            logger.info("Resuming monitoring for %s (%s)", run["agent_name"], run_id)
            continue

        # Session dead — try dot-file recovery
        goal_dir = GOALS_DIR / run["goal_slug"]
        done_file = goal_dir / f".agent-{run_id}.done"
        output_file = goal_dir / f".agent-{run_id}.output.json"

        if done_file.exists() or output_file.exists():
            result = recheck_failed_run(run_id, db_path=db_path)
            if result:
                recovered.append(result)
                logger.info("Startup recovery: run %s → %s (dot-file)", run_id, result["status"])
                continue

        # Force-fail — no session, no dot files
        update_agent_run(
            run_id,
            status="failed",
            error_message="Orphaned by server restart — tmux session not found",
            completed_at=datetime.now(timezone.utc).isoformat(),
            db_path=db_path,
        )
        logger.info("Startup recovery: force-failed orphaned run %s", run_id)
        recovered.append(get_agent_run(run_id, db_path=db_path))

    if recovered:
        logger.info("Startup recovery: processed %d stale agent run(s)", len(recovered))
    return recovered


# ---------------------------------------------------------------------------
# Context usage backfill
# ---------------------------------------------------------------------------

def backfill_context_usage(db_path=None) -> int:
    """One-time backfill: read peak context from JSONL for all runs missing context_usage.

    Returns the number of runs updated.
    """
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT id, session_id, working_dir FROM agent_runs "
        "WHERE session_id IS NOT NULL AND context_usage IS NULL"
    ).fetchall()
    conn.close()

    updated = 0
    for i, row in enumerate(rows):
        session_jsonl_dir = _resolve_jsonl_dir(row["working_dir"])
        usage = _read_context_usage(row["session_id"], session_jsonl_dir, working_dir=row["working_dir"])
        if usage:
            update_agent_run(row["id"], context_usage=usage, db_path=db_path)
            updated += 1
        if (i + 1) % 50 == 0:
            logger.info("Context usage backfill progress: %d / %d", i + 1, len(rows))
    logger.info("Context usage backfill: updated %d / %d runs", updated, len(rows))
    return updated
