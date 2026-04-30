"""Task Suggestion API endpoints — HTMX fragment responses."""

import logging

from fastapi import APIRouter, Request, Query

from cast_server.deps import templates
from cast_server.config import GOALS_DIR, DB_PATH
from fastapi.responses import HTMLResponse, Response
from cast_server.services.task_suggestion_service import (
    approve_suggestion, decline_suggestion, get_pending_suggestions,
    approve_suggestion_group, decline_suggestion_group, approve_parent_only,
)
from cast_server.services.agent_service import trigger_agent, get_latest_agent_run
from cast_server.utils.responses import toast_header

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/goals/{slug}/task-suggestions", tags=["task-suggestions"])


@router.post("/{suggestion_id}/approve")
async def approve(request: Request, slug: str, suggestion_id: int):
    """Approve a task suggestion — transitions status to pending, returns task_item fragment."""
    task = approve_suggestion(suggestion_id, goals_dir=GOALS_DIR, db_path=DB_PATH)
    response = templates.TemplateResponse(request, "fragments/task_item.html", {
        "task": task,
    })
    response.headers["HX-Trigger"] = toast_header("Task approved")
    return response


@router.post("/{suggestion_id}/decline")
async def decline(request: Request, slug: str, suggestion_id: int):
    """Decline a task suggestion — removes the suggestion card."""
    decline_suggestion(suggestion_id, db_path=DB_PATH)
    response = Response(content="", media_type="text/html")
    response.headers["HX-Trigger"] = toast_header("Suggestion declined")
    return response


@router.post("/{suggestion_id}/approve-group")
async def approve_group(request: Request, slug: str, suggestion_id: int):
    """Approve a parent suggestion and all its children — transitions to pending.
    Redirects to goal page since tasks live in a different DOM section than suggestions."""
    tasks = approve_suggestion_group(suggestion_id, goals_dir=GOALS_DIR, db_path=DB_PATH)
    parent_phase = tasks[0].get("phase", "execution") if tasks else "execution"
    return HTMLResponse(
        content="",
        headers={
            "HX-Redirect": f"/goals/{slug}#{parent_phase}",
            "HX-Trigger": toast_header(f"{len(tasks)} tasks approved"),
        },
    )


@router.post("/{suggestion_id}/approve-parent-only")
async def approve_parent(request: Request, slug: str, suggestion_id: int):
    """Approve only the parent suggestion — orphans children as standalone suggestions.
    Redirects to goal page to show new task + remaining orphaned suggestion cards."""
    task = approve_parent_only(suggestion_id, goals_dir=GOALS_DIR, db_path=DB_PATH)
    phase = task.get("phase", "execution")
    return HTMLResponse(
        content="",
        headers={
            "HX-Redirect": f"/goals/{slug}#{phase}",
            "HX-Trigger": toast_header("Parent approved, subtasks available as individual suggestions"),
        },
    )


@router.post("/{suggestion_id}/decline-group")
async def decline_group_endpoint(request: Request, slug: str, suggestion_id: int):
    """Decline a parent suggestion and all its children."""
    decline_suggestion_group(suggestion_id, db_path=DB_PATH)
    response = Response(content="", media_type="text/html")
    response.headers["HX-Trigger"] = toast_header("Suggestion group declined")
    return response


@router.post("/generate")
async def generate(request: Request, slug: str, phase: str = Query(default=None)):
    """Trigger task suggestion generation via agent_service.

    Returns suggest_status.html fragment showing running state with polling.
    """
    form = await request.form()
    user_context = form.get("user_context", "").strip() or ""
    run_id = await trigger_agent(
        agent_name="cast-task-suggester",
        goal_slug=slug,
        context=user_context,
    )
    job = {"status": "running", "run_id": run_id}
    response = templates.TemplateResponse(request, "fragments/suggest_status.html", {
        "job": job,
        "slug": slug,
        "phase": phase,
        "suggestions": [],
    })
    return response


@router.get("/status")
async def status(request: Request, slug: str, phase: str = Query(default=None)):
    """Get current suggester job status as HTML fragment.

    Reads from agent_runs table instead of in-memory state.
    Returns spinner while running, suggestion cards when done, error on failure.
    Polling stops automatically when status is completed or error (no hx-trigger).
    """
    run = get_latest_agent_run(slug, agent_name="cast-task-suggester", db_path=DB_PATH)
    suggestions = []

    if not run:
        return templates.TemplateResponse(request, "fragments/suggest_status.html", {
            "job": {"status": "idle"},
            "slug": slug,
            "phase": phase,
            "suggestions": suggestions,
        })

    # Map agent_runs statuses to template-expected statuses
    run_status = run["status"]

    if run_status in ("pending", "running"):
        job = {"status": "running", "run_id": run["id"]}
        return templates.TemplateResponse(request, "fragments/suggest_status.html", {
            "job": job,
            "slug": slug,
            "phase": phase,
            "suggestions": suggestions,
        })

    if run_status == "completed":
        suggestions = get_pending_suggestions(slug, phase=None, db_path=DB_PATH)
        job = {"status": "completed", "run_id": run["id"], "suggestions_count": len(suggestions)}
        response = templates.TemplateResponse(request, "fragments/suggest_status.html", {
            "job": job,
            "slug": slug,
            "phase": phase,
            "suggestions": suggestions,
        })
        response.headers["HX-Trigger"] = toast_header(f"{len(suggestions)} task suggestions ready")
        return response

    # failed / stuck — treat as error
    job = {"status": "error", "error": run.get("error_message") or "Suggestion generation failed"}
    response = templates.TemplateResponse(request, "fragments/suggest_status.html", {
        "job": job,
        "slug": slug,
        "phase": phase,
        "suggestions": suggestions,
    })
    response.headers["HX-Trigger"] = toast_header(
        job["error"], "error"
    )
    return response


@router.get("")
async def list_suggestions(request: Request, slug: str, phase: str = Query(default=None)):
    """Get pending task suggestions for a goal, optionally filtered by phase."""
    suggestions = get_pending_suggestions(slug, phase=phase, db_path=DB_PATH)
    return templates.TemplateResponse(request, "fragments/task_suggestion_cards.html", {
        "suggestions": suggestions,
    })
