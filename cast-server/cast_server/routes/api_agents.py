"""Agent API endpoints — DB-backed agent run tracking."""

from fastapi import APIRouter, Request
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

from cast_server.deps import templates
from cast_server.models.agent_config import load_agent_config
from cast_server.models.delegation import DelegationContext
from cast_server.services import agent_service
from cast_server.services.error_memory_service import resolve_memory


class InvokeRequest(BaseModel):
    goal_slug: str | None = None
    context: str = ""
    task_id: int | None = None


class ContinueRunRequest(BaseModel):
    message: str

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
        delegation_context = DelegationContext(**delegation_context_raw)
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
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    return {"run_id": run_id, "status": "scheduled" if scheduled_at else "pending"}


@router.get("/jobs/{run_id}")
async def get_run_status(run_id: str):
    """Get agent run status by ID."""
    run = agent_service.get_agent_run(run_id)
    if not run:
        return Response(status_code=404, content="Run not found")
    return run


@router.post("/jobs/{run_id}/recheck")
async def recheck_run(request: Request, run_id: str):
    """Recheck a failed agent run — recover if agent finished after timeout.

    Returns the re-rendered task_item fragment so HTMX can swap it in-place.
    """
    from cast_server.services.task_service import get_task

    updated = agent_service.recheck_failed_run(run_id)
    if not updated:
        return Response(status_code=422, content="Agent has not finished yet")

    # Re-render the task item with updated run state
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

    # Fallback: render as run_row if accessed from runs page
    _enrich_interactive(updated)
    return templates.TemplateResponse(request, "fragments/run_row.html", {
        "run": updated,
    })


@router.post("/runs/backfill-context")
async def backfill_context_usage():
    """One-time backfill: populate context_usage from JSONL for all runs missing it."""
    updated = agent_service.backfill_context_usage()
    return {"updated": updated}


@router.get("/runs/{run_id}/children")
async def get_run_children(request: Request, run_id: str):
    """HTMX fragment: child runs for a parent run."""
    children = agent_service.get_children_runs(run_id)
    for child in children:
        _enrich_interactive(child)
    return templates.TemplateResponse(request, "fragments/run_children.html", {
        "children": children,
    })


@router.get("/runs")
async def list_runs(request: Request, status: str = "all", page: int = 1):
    """HTMX fragment: filtered list of all agent runs."""
    escalated = agent_service.get_escalated_agents()
    result = agent_service.get_all_runs(status_filter=status, top_level_only=True, page=page, per_page=25)
    for run in result["runs"]:
        _enrich_interactive(run)
    return templates.TemplateResponse(request, "fragments/runs_list.html", {
        "runs": result["runs"], "escalated_agents": escalated, "pagination": result,
    })


@router.get("/runs/{run_id}/row")
async def get_run_row(request: Request, run_id: str):
    """HTMX fragment: single run row for polling updates."""
    run = agent_service.get_agent_run(run_id)
    if not run:
        return Response(status_code=404, content="Run not found")
    # Inline enrichment: fetch goal_title and task_title
    from cast_server.db.connection import get_connection
    conn = get_connection()
    try:
        if run.get("goal_slug"):
            row = conn.execute("SELECT title FROM goals WHERE slug = ?", (run["goal_slug"],)).fetchone()
            run["goal_title"] = row["title"] if row else None
        if run.get("task_id"):
            row = conn.execute("SELECT title FROM tasks WHERE id = ?", (run["task_id"],)).fetchone()
            run["task_title"] = row["title"] if row else None
    finally:
        conn.close()
    _enrich_interactive(run)
    return templates.TemplateResponse(request, "fragments/run_row.html", {
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
    """Cancel an active agent run. Returns updated row HTML for HTMX."""
    try:
        result = agent_service.cancel_run(run_id)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})
    if request.headers.get("HX-Request"):
        run = agent_service.get_agent_run(run_id)
        if run:
            _enrich_interactive(run)
            return templates.TemplateResponse(request, "fragments/run_row.html", {"run": run})
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
