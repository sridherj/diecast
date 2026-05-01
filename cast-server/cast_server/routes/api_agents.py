"""Agent API endpoints — DB-backed agent run tracking."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, ValidationError

from cast_server import config as _config
from cast_server.deps import templates
from cast_server.models.agent_config import load_agent_config
from cast_server.models.delegation import DelegationContext
from cast_server.services import (
    agent_service,
    subagent_invocation_service,
    user_invocation_service,
)
from cast_server.services.agent_service import (
    MalformedOutputError,
    MissingExternalProjectDirError,
    load_canonical_file,
)
from cast_server.services.error_memory_service import resolve_memory


class InvokeRequest(BaseModel):
    goal_slug: str | None = None
    context: str = ""
    task_id: int | None = None


class ContinueRunRequest(BaseModel):
    message: str


class UserInvocationOpenRequest(BaseModel):
    agent_name: str
    prompt: str
    session_id: str | None = None


class UserInvocationCompleteRequest(BaseModel):
    session_id: str | None = None


class SubagentInvocationOpenRequest(BaseModel):
    agent_type: str
    session_id: str
    claude_agent_id: str
    transcript_path: str | None = None
    prompt: str | None = None


class SubagentInvocationCompleteRequest(BaseModel):
    claude_agent_id: str


class SubagentInvocationSkillRequest(BaseModel):
    session_id: str
    skill: str
    invoked_at: str | None = None


router = APIRouter(prefix="/api/agents", tags=["agents"])


def _enrich_interactive(run: dict) -> None:
    """Add is_interactive flag from agent config."""
    if run.get("agent_name"):
        cfg = load_agent_config(run["agent_name"])
        run["is_interactive"] = cfg.interactive
    else:
        run["is_interactive"] = False


@router.get("/goals/{slug}/recommendations")
async def get_recommendations(request: Request, slug: str):
    """Get recommended agents for a goal, derived from task-level recommended_agent."""
    agents = agent_service.get_recommended_agents(slug)
    recent_runs = agent_service.get_runs_for_goal(slug)
    return templates.TemplateResponse(
        request,
        "fragments/agent_panel.html",
        {"agents": agents, "runs": recent_runs, "goal_slug": slug},
    )


@router.post("/{name}/trigger")
async def trigger_agent(request: Request, name: str):
    """Enqueue an agent run. Accepts optional task_id and scheduled_at."""
    data = await request.json()
    goal_slug = data.get("goal_slug", "")
    context = data.get("context", "")
    task_id = data.get("task_id")
    scheduled_at = data.get("scheduled_at")  # ISO UTC timestamp or None
    parent_run_id = data.get("parent_run_id")

    delegation_context_raw = data.get("delegation_context")
    if delegation_context_raw:
        delegation_context_raw.setdefault("goal_slug", goal_slug)
        delegation_context_raw.setdefault("parent_run_id", parent_run_id or "")
        # Default output_dir to <GOALS_DIR>/<slug> when caller omits it.
        # Mirrors the goal_slug / parent_run_id setdefault pattern above; keeps
        # all defaulting in one place and avoids post-construction mutation.
        output_block = delegation_context_raw.setdefault("output", {})
        output_block.setdefault("output_dir", str(_config.GOALS_DIR / goal_slug))

        try:
            delegation_context = DelegationContext(**delegation_context_raw)
        except ValidationError as e:
            return JSONResponse(
                status_code=422,
                content={
                    "error_code": "invalid_delegation_context",
                    "detail": "delegation_context failed validation",
                    "errors": e.errors(include_url=False),
                    "hint": (
                        "See docs/specs/cast-delegation-contract.collab.md and "
                        "skills/claude-code/cast-child-delegation/SKILL.md for the "
                        "expected shape."
                    ),
                },
            )
    else:
        delegation_context = None

    input_params = {"goal_slug": goal_slug, "context": context}
    if task_id:
        input_params["task_id"] = task_id

    try:
        run_id = await agent_service.trigger_agent(
            agent_name=name,
            goal_slug=goal_slug,
            context=context,
            task_id=task_id,
            input_params=input_params,
            scheduled_at=scheduled_at,
            parent_run_id=parent_run_id,
            delegation_context=delegation_context,
        )
    except MissingExternalProjectDirError as e:
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "missing_external_project_dir",
                "goal_slug": e.goal_slug,
                "configured_path": e.configured_path,
                "detail": str(e),
                "hint": (
                    "Set external_project_dir on the goal before dispatching. "
                    "PATCH /api/goals/{slug}/config (form field external_project_dir=<absolute path>)."
                ),
            },
        )
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    return {"run_id": run_id, "status": "scheduled" if scheduled_at else "pending"}


@router.post("/user-invocations")
async def open_user_invocation(req: UserInvocationOpenRequest):
    """Open a user-invocation row for a Claude Code slash-command prompt.

    Server is agnostic to the ``/cast-`` prefix (Decision #13) — any non-empty
    ``agent_name`` is accepted; the hook handler is responsible for filtering.
    """
    run_id = user_invocation_service.register(
        agent_name=req.agent_name,
        prompt=req.prompt,
        session_id=req.session_id,
    )
    return {"run_id": run_id}


@router.post("/user-invocations/complete")
async def complete_user_invocation(req: UserInvocationCompleteRequest):
    """Close every still-running user-invocation row in this session.

    A missing or empty ``session_id`` is **not** an error — the contract
    returns ``{"closed": 0}`` so the Stop hook can fire unconditionally.
    """
    closed = user_invocation_service.complete(req.session_id)
    return {"closed": closed}


@router.post("/subagent-invocations")
async def open_subagent_invocation(req: SubagentInvocationOpenRequest):
    """Open a subagent-invocation row for a Task()-dispatched cast-* subagent.

    Returns ``{"run_id": null}`` (200) when ``agent_type`` is not a cast-*
    name — hook scripts must exit 0 (FR-010). The handler authoritatively
    enforces the cast-* scope filter via ``AGENT_TYPE_PATTERN``.
    """
    run_id = subagent_invocation_service.register(
        agent_type=req.agent_type,
        session_id=req.session_id,
        claude_agent_id=req.claude_agent_id,
        transcript_path=req.transcript_path,
        prompt=req.prompt,
    )
    return {"run_id": run_id}


@router.post("/subagent-invocations/complete")
async def complete_subagent_invocation(req: SubagentInvocationCompleteRequest):
    """Close the running subagent row whose ``claude_agent_id`` matches.

    Returns ``{"closed": 0 | 1}`` (200) — never 4xx, even on miss, so a
    SubagentStop hook never has reason to retry.
    """
    closed = subagent_invocation_service.complete(req.claude_agent_id)
    return {"closed": closed}


@router.post("/subagent-invocations/skill")
async def record_subagent_skill(req: SubagentInvocationSkillRequest):
    """Append a skill invocation to the most-recent running cast-* row.

    Wire field ``skill`` is singular (matches ``tool_input.skill`` from the
    empirical ``PreToolUse(Skill)`` payload). Returns
    ``{"appended": 0 | 1}`` (200) — 0 when no candidate row exists.
    """
    appended = subagent_invocation_service.record_skill(
        session_id=req.session_id,
        skill_name=req.skill,
        invoked_at=req.invoked_at,
    )
    return {"appended": appended}


@router.get("/jobs/{run_id}")
async def get_run_status(run_id: str, include: str | None = None):
    """Get agent run status by ID — file-canonical read-through.

    Precedence (Phase 3b sp5; references docs/specs/cast-delegation-contract.collab.md):
      * File present + parseable → file fields win (DB fills gaps); ``source: "file"``.
      * File missing → DB-only state; ``source: "db"``.
      * File malformed → 502 + ``source: "file_invalid"`` and parse error in ``error``.
      * Unknown run_id (no DB row) → 404. Server-dispatched-only carve-out per
        Q#17/A3 lock — no filesystem fallback resolver in v1.

    File is read on every request; no caching. The canonical-file rule
    supersedes any future caching layer.

    ``?include=children`` augments the response with a ``children`` array
    holding the descendant tree (depth-capped, rollups attached) shaped by
    ``get_run_with_rollups``.
    """
    db_row = agent_service.get_agent_run(run_id)
    if db_row is None:
        raise HTTPException(status_code=404, detail=f"Unknown run_id: {run_id}")

    goal_slug = db_row.get("goal_slug") or ""
    goal_dir = Path(_config.GOALS_DIR) / goal_slug if goal_slug else Path(_config.GOALS_DIR)

    try:
        file_data = load_canonical_file(goal_dir, run_id)
    except MalformedOutputError as e:
        return JSONResponse(
            status_code=502,
            content={
                "run_id": run_id,
                "source": "file_invalid",
                "error": str(e),
                "db_state": db_row,
            },
        )

    if file_data is None:
        merged = {**db_row, "source": "db"}
    else:
        # Field-by-field merge: file wins where present; DB fills gaps
        # (created_at, parent_run_id, worktree_path, etc.).
        merged = {**db_row, **file_data, "source": "file"}

    if include == "children":
        tree = agent_service.get_run_with_rollups(run_id)
        merged["children"] = (tree or {}).get("children", []) or []

    return merged


@router.post("/jobs/{run_id}/recheck")
async def recheck_run(request: Request, run_id: str):
    """Recheck a failed agent run — recover if agent finished after timeout.

    Returns the re-rendered task_item fragment for goal-page callers, or the
    threaded `.run-group` fragment (run_node macro) for /runs-page callers,
    matching the macro's `hx-target="closest .run-group"`.
    """
    from cast_server.services.task_service import get_task

    updated = agent_service.recheck_failed_run(run_id)
    if not updated:
        return Response(status_code=422, content="Agent has not finished yet")

    task_id = updated.get("task_id")
    if task_id:
        task = get_task(task_id)
        if task:
            task["active_run"] = agent_service.get_active_run_for_task(task_id)
            runs = agent_service.get_runs_for_task(task_id)
            task["last_run"] = next(
                (r for r in runs if r["status"] in ("completed", "failed", "partial")), None
            )
            return templates.TemplateResponse(request, "fragments/task_item.html", {
                "task": task,
            })

    run = agent_service.get_run_with_rollups(run_id) or updated
    _enrich_interactive(run)
    return templates.TemplateResponse(request, "fragments/run_group.html", {
        "run": run,
    })


@router.post("/runs/backfill-context")
async def backfill_context_usage():
    """One-time backfill: populate context_usage from JSONL for all runs missing it."""
    updated = agent_service.backfill_context_usage()
    return {"updated": updated}


@router.get("/runs")
async def list_runs(request: Request, status: str = "all", page: int = 1):
    """List runs as a tree: top-level entries with full descendant trees attached.

    Content negotiation: HTMX requests (carry the ``HX-Request`` header) get the
    threaded HTML fragment for partial swaps; plain API consumers get the
    raw JSON tree dict so they can introspect descendant counts, rollups, etc.
    """
    status_filter = None if status in ("all", "") else status
    result = agent_service.get_runs_tree(status_filter=status_filter, page=page, per_page=25)
    for run in result["runs"]:
        _enrich_interactive(run)
    if request.headers.get("hx-request", "").lower() != "true":
        return JSONResponse(result)
    escalated = agent_service.get_escalated_agents()
    return templates.TemplateResponse(request, "fragments/runs_list.html", {
        "runs": result["runs"],
        "escalated_agents": escalated,
        "pagination": result,
        "active_filter": status_filter or "all",
    })


@router.get("/runs/{run_id}/status_cells")
async def get_run_status_cells(request: Request, run_id: str):
    """HTMX fragment: line-2 status cells for a single run.

    Polled every 3s by running rows on the threaded /runs page. Renders the
    inner `.run-status-cells` span so expand state on the outer `.run-node`
    survives the swap. Recomputes rollups (descendant counts, status_rollup,
    total_cost_usd, ctx_class) since they can change between polls.
    """
    run = agent_service.get_run_with_rollups(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return templates.TemplateResponse(request, "fragments/run_status_cells.html", {
        "run": run,
    })


@router.post("/{name}/invoke")
async def invoke_agent(name: str, body: InvokeRequest):
    """Invoke an agent from CLI — creates run, assembles prompt, returns both."""
    try:
        result = await agent_service.invoke_agent(
            agent_name=name,
            goal_slug=body.goal_slug,
            context=body.context,
            task_id=body.task_id,
        )
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    return result


@router.post("/runs/{run_id}/continue")
async def continue_run(run_id: str, body: ContinueRunRequest):
    """Send a follow-up message to an existing agent's tmux session."""
    try:
        await agent_service.continue_agent_run(run_id, body.message)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    return {"status": "continued", "run_id": run_id}


@router.post("/runs/{run_id}/complete")
async def complete_run(run_id: str):
    """Finalize a CLI-registered agent run. Auto-closes tmux container after 30s."""
    run = agent_service.get_agent_run(run_id)
    if not run:
        return JSONResponse(status_code=404, content={"detail": "Run not found"})

    agent_service.update_agent_run(run_id, status="completed")

    # Schedule tmux session cleanup (30s delay to allow inspection)
    import asyncio
    async def _cleanup():
        await asyncio.sleep(30)
        try:
            tmux = agent_service._get_tmux()
            session_name = f"agent-{run_id}"
            if tmux.session_exists(session_name):
                tmux.kill_session(session_name)
        except Exception:
            pass  # Best-effort cleanup
    asyncio.create_task(_cleanup())

    return {"status": "completed", "run_id": run_id}


@router.post("/runs/{run_id}/cancel")
async def cancel_run_endpoint(request: Request, run_id: str):
    """Cancel an active agent run. Returns the threaded `.run-group` fragment
    (run_node macro) for HTMX callers — matches the macro's
    `hx-target="closest .run-group"` swap target.
    """
    try:
        result = agent_service.cancel_run(run_id)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    if request.headers.get("HX-Request"):
        run = agent_service.get_run_with_rollups(run_id)
        if run:
            _enrich_interactive(run)
            return templates.TemplateResponse(request, "fragments/run_group.html", {"run": run})
    return result


@router.delete("/runs/{run_id}")
async def delete_run_endpoint(request: Request, run_id: str):
    """Delete a terminal agent run from the database."""
    try:
        agent_service.delete_run(run_id)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    if request.headers.get("HX-Request"):
        return Response(content="", media_type="text/html")
    return {"status": "deleted"}


@router.post("/runs/{run_id}/fail")
async def fail_run_endpoint(run_id: str):
    """Manually mark a run as failed."""
    try:
        result = agent_service.fail_run(run_id)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    return result


@router.post("/error-memories/{memory_id}/resolve")
async def resolve_error_memory(memory_id: int, request: Request):
    """Mark an error memory as resolved with optional resolution text."""
    body = await request.json()
    resolution = body.get("resolution", "")
    resolve_memory(memory_id, resolution)
    return {"status": "resolved"}
