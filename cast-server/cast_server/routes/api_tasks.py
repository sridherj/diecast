"""Task API endpoints — HTMX fragment responses."""

import logging
from datetime import datetime, timezone, timedelta

from pydantic import ValidationError
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response

from cast_server.deps import templates
from cast_server.services.task_service import (
    get_tasks_for_goal, get_task, create_task, update_task,
    update_task_status, complete_task,
)
from cast_server.services import agent_service, goal_service
from cast_server.models.agent_config import load_agent_config
from cast_server.models.task import TaskCreate
from cast_server.config import GOALS_DIR, OFF_PEAK_HOUR
from cast_server.utils.responses import toast_header

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["tasks"])


def _enrich_task_for_render(task: dict) -> None:
    """Add computed fields needed by task_item.html template."""
    if task.get("recommended_agent"):
        agent_cfg = load_agent_config(task["recommended_agent"])
        task["is_interactive"] = agent_cfg.interactive
    else:
        task["is_interactive"] = False


def _compute_next_off_peak() -> str:
    """Compute the next occurrence of OFF_PEAK_HOUR as an ISO UTC timestamp.

    Uses local time for the hour comparison (it's about SJ's schedule),
    but returns UTC ISO for storage in scheduled_at.
    """
    now_local = datetime.now()
    if now_local.hour < OFF_PEAK_HOUR:
        # Today at OFF_PEAK_HOUR
        target_local = now_local.replace(hour=OFF_PEAK_HOUR, minute=0, second=0, microsecond=0)
    else:
        # Tomorrow at OFF_PEAK_HOUR
        tomorrow = now_local + timedelta(days=1)
        target_local = tomorrow.replace(hour=OFF_PEAK_HOUR, minute=0, second=0, microsecond=0)

    # Convert to UTC for storage
    target_utc = target_local.astimezone(timezone.utc)
    return target_utc.isoformat()


@router.get("/goals/{slug}/tasks")
async def list_tasks(request: Request, slug: str):
    """Get task list fragment for a goal."""
    tasks = get_tasks_for_goal(slug)
    return templates.TemplateResponse(request, "fragments/task_list.html", {
        "tasks": tasks, "goal_slug": slug,
    })


@router.post("/goals/{slug}/tasks")
async def add_task(request: Request, slug: str):
    """Create a new task. Supports both JSON (agents) and Form (HTMX UI) input."""
    content_type = request.headers.get("content-type", "")
    is_json = "application/json" in content_type

    if is_json:
        body = await request.json()
        try:
            task_data = TaskCreate(**body)
        except ValidationError as e:
            errors = [{"msg": str(err["ctx"]["error"]) if "ctx" in err and "error" in err["ctx"] else err["msg"],
                        "field": err["loc"][-1] if err.get("loc") else "unknown"}
                       for err in e.errors()]
            return JSONResponse(status_code=422, content={"detail": errors})
        title = task_data.title
        phase = task_data.phase or "execution"
        parent_id_val = task_data.parent_id

        task = create_task(
            goal_slug=slug,
            title=title,
            phase=phase,
            outcome=task_data.outcome,
            action=task_data.action,
            task_type=task_data.task_type,
            estimated_time=task_data.estimated_time,
            energy=task_data.energy,
            assigned_to=task_data.assigned_to,
            tip=task_data.tip,
            recommended_agent=task_data.recommended_agent,
            parent_id=parent_id_val,
            task_artifacts=task_data.task_artifacts,
            rationale=task_data.rationale,
            is_spike=task_data.is_spike,
            status=task_data.status,
        )
        logger.info("Task created (JSON): '%s' for goal '%s' (status: %s)", title, slug, task_data.status)
        return JSONResponse(task)

    # Form path (HTMX UI) — preserve existing behavior
    form = await request.form()
    title = form.get("title", "")
    phase = form.get("phase", "execution")
    outcome = form.get("outcome", "")
    action = form.get("action", "")
    task_type = form.get("task_type", "")
    estimated_time = form.get("estimated_time", "")
    energy = form.get("energy", "")
    assigned_to = form.get("assigned_to", "")
    tip = form.get("tip", "")
    recommended_agent = form.get("recommended_agent", "")
    parent_id = form.get("parent_id", "")
    task_artifacts = form.get("task_artifacts", "")

    if not title:
        raise HTTPException(400, "title is required")

    artifacts_list = [p.strip() for p in task_artifacts.split(",") if p.strip()] if task_artifacts else None

    task = create_task(
        goal_slug=slug,
        title=title,
        phase=phase,
        outcome=outcome or None,
        action=action or None,
        task_type=task_type or None,
        estimated_time=estimated_time or None,
        energy=energy or None,
        assigned_to=assigned_to or None,
        tip=tip or None,
        recommended_agent=recommended_agent or None,
        parent_id=int(parent_id) if parent_id else None,
        task_artifacts=artifacts_list,
    )
    logger.info("Task created: '%s' for goal '%s' (phase: %s)", title, slug, phase)

    # If this is a subtask, return the new subtask_item fragment (appended to .subtask-list)
    # plus an OOB-swapped parent for progress badge update
    if parent_id:
        parent_task = get_task(int(parent_id))
        # Render the new subtask as a subtask_item
        primary_html = templates.get_template("fragments/subtask_item.html").render(
            request=request, sub=task,
        )
        oob_html = ""
        if parent_task:
            if parent_task.get("recommended_agent"):
                parent_task["active_run"] = agent_service.get_active_run_for_task(int(parent_id))
                runs = agent_service.get_runs_for_task(int(parent_id))
                parent_task["last_run"] = next(
                    (r for r in runs if r["status"] in ("completed", "failed", "partial")), None
                )
            _enrich_task_for_render(parent_task)
            oob_html = templates.get_template("fragments/task_item.html").render(
                request=request, task=parent_task, oob=True,
            )
        return HTMLResponse(
            content=primary_html + oob_html,
            headers={"HX-Trigger": toast_header("Subtask added")},
        )

    return HTMLResponse(
        content="",
        headers={
            "HX-Redirect": f"/goals/{slug}#{phase}",
            "HX-Trigger": toast_header("Task created"),
        },
    )


@router.put("/tasks/{task_id}/status")
async def change_status(
    request: Request,
    task_id: int,
    status: str = Form(...),
):
    """Update task status. Returns task_item fragment.
    If task is a subtask, also returns OOB-swapped parent fragment."""
    task = update_task_status(task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info("Task %d status changed to '%s'", task_id, status)

    # Attach agent run context
    if task.get("recommended_agent"):
        task["active_run"] = agent_service.get_active_run_for_task(task_id)
        runs = agent_service.get_runs_for_task(task_id)
        task["last_run"] = next(
            (r for r in runs if r["status"] in ("completed", "failed", "partial")), None
        )

    # If this is a subtask, return subtask_item + OOB parent
    parent_task = task.get("parent_task")
    if parent_task:
        if parent_task.get("recommended_agent"):
            parent_task["active_run"] = agent_service.get_active_run_for_task(parent_task["id"])
            runs = agent_service.get_runs_for_task(parent_task["id"])
            parent_task["last_run"] = next(
                (r for r in runs if r["status"] in ("completed", "failed", "partial")), None
            )
        # Render subtask fragment (primary response)
        primary_html = templates.get_template("fragments/subtask_item.html").render(
            request=request, sub=task,
        )
        # Render parent with OOB flag for live progress badge update
        _enrich_task_for_render(parent_task)
        oob_html = templates.get_template("fragments/task_item.html").render(
            request=request, task=parent_task, oob=True,
        )
        return HTMLResponse(
            content=primary_html + oob_html,
            headers={"HX-Trigger": toast_header(f"Task status: {status}")},
        )

    _enrich_task_for_render(task)
    response = templates.TemplateResponse(request, "fragments/task_item.html", {
        "task": task,
    })
    response.headers["HX-Trigger"] = toast_header(f"Task status: {status}")
    return response


@router.put("/tasks/{task_id}/complete")
async def mark_complete(
    request: Request,
    task_id: int,
    actual_time: str = Form(""),
    moved_toward_goal: str = Form(""),
    notes: str = Form(""),
):
    """Mark task as completed with metadata. Returns task_item fragment."""
    task = complete_task(
        task_id,
        actual_time=actual_time or None,
        moved_toward_goal=moved_toward_goal or None,
        notes=notes or None,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info("Task %d completed", task_id)
    if task.get("recommended_agent"):
        task["active_run"] = agent_service.get_active_run_for_task(task_id)
        runs = agent_service.get_runs_for_task(task_id)
        task["last_run"] = next(
            (r for r in runs if r["status"] in ("completed", "failed", "partial")), None
        )

    # If this is a subtask, return subtask_item + OOB parent
    parent_task = task.get("parent_task")
    if parent_task:
        if parent_task.get("recommended_agent"):
            parent_task["active_run"] = agent_service.get_active_run_for_task(parent_task["id"])
            runs = agent_service.get_runs_for_task(parent_task["id"])
            parent_task["last_run"] = next(
                (r for r in runs if r["status"] in ("completed", "failed", "partial")), None
            )
        primary_html = templates.get_template("fragments/subtask_item.html").render(
            request=request, sub=task,
        )
        _enrich_task_for_render(parent_task)
        oob_html = templates.get_template("fragments/task_item.html").render(
            request=request, task=parent_task, oob=True,
        )
        return HTMLResponse(
            content=primary_html + oob_html,
            headers={"HX-Trigger": toast_header("Task completed!")},
        )

    _enrich_task_for_render(task)
    response = templates.TemplateResponse(request, "fragments/task_item.html", {
        "task": task,
    })
    response.headers["HX-Trigger"] = toast_header("Task completed!")
    return response


@router.get("/tasks/{task_id}")
async def get_task_item(request: Request, task_id: int):
    """Return read-only task_item fragment (used by cancel edit and HTMX polling)."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Attach agent run context for run button states
    if task.get("recommended_agent"):
        task["active_run"] = agent_service.get_active_run_for_task(task_id)
        runs = agent_service.get_runs_for_task(task_id)
        task["last_run"] = next(
            (r for r in runs if r["status"] in ("completed", "failed", "partial")), None
        )
    _enrich_task_for_render(task)
    return templates.TemplateResponse(request, "fragments/task_item.html", {
        "task": task,
    })


@router.get("/tasks/{task_id}/edit")
async def edit_task_form(request: Request, task_id: int):
    """Return inline edit form fragment for a task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return templates.TemplateResponse(request, "fragments/task_edit.html", {
        "task": task, "agents": agent_service.get_all_agents(),
    })


@router.put("/tasks/{task_id}")
async def update_task_fields(
    request: Request,
    task_id: int,
    title: str = Form(...),
    outcome: str = Form(""),
    action: str = Form(""),
    task_type: str = Form(""),
    estimated_time: str = Form(""),
    energy: str = Form(""),
    assigned_to: str = Form(""),
    phase: str = Form(""),
    tip: str = Form(""),
    recommended_agent: str = Form(""),
    task_artifacts: str = Form(""),
):
    """Update task fields. Returns task_item fragment."""
    # Parse comma-separated artifacts
    artifacts_list = [p.strip() for p in task_artifacts.split(",") if p.strip()] if task_artifacts else None

    task = update_task(
        task_id,
        title=title,
        outcome=outcome,
        action=action,
        task_type=task_type,
        estimated_time=estimated_time,
        energy=energy,
        assigned_to=assigned_to,
        phase=phase,
        tip=tip,
        recommended_agent=recommended_agent,
        task_artifacts=artifacts_list,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logger.info("Task %d updated: '%s'", task_id, title)
    if task.get("recommended_agent"):
        task["active_run"] = agent_service.get_active_run_for_task(task_id)
        runs = agent_service.get_runs_for_task(task_id)
        task["last_run"] = next(
            (r for r in runs if r["status"] in ("completed", "failed", "partial")), None
        )
    _enrich_task_for_render(task)
    response = templates.TemplateResponse(request, "fragments/task_item.html", {
        "task": task,
    })
    response.headers["HX-Trigger"] = toast_header(f"Task '{title}' updated")
    return response


@router.post("/tasks/{task_id}/run-agent")
async def run_agent_for_task(request: Request, task_id: int, schedule: str = ""):
    """Trigger the recommended agent for a task.

    Query params:
      schedule=off-peak  →  schedule for next OFF_PEAK_HOUR instead of immediate run
    """
    # 1. Look up task
    task = get_task(task_id)
    if not task:
        return Response(status_code=404, content="Task not found")

    # 2. Validate recommended_agent is set
    if not task.get("recommended_agent"):
        return Response(status_code=400, content="Task has no recommended agent")

    # 3. Check for active run (concurrent guard)
    active_run = agent_service.get_active_run_for_task(task_id)
    if active_run:
        task["active_run"] = active_run
        _enrich_task_for_render(task)
        return templates.TemplateResponse(
            request,
            "fragments/task_item.html",
            {"task": task},
            status_code=409,
        )

    # 4. Look up goal context
    goal = goal_service.get_goal(task["goal_slug"])
    if not goal:
        return Response(status_code=404, content="Goal not found")

    # 5. Build input_params
    goal_dir = GOALS_DIR / task["goal_slug"]
    input_params = {
        "goal_slug": task["goal_slug"],
        "goal_title": goal["title"],
        "goal_phase": goal.get("phase", ""),
        "goal_dir": str(goal_dir),
        "task_id": task_id,
        "task_title": task["title"],
        "task_outcome": task.get("outcome", ""),
        "context": "",
    }

    # 6. Compute scheduled_at if off-peak requested
    scheduled_at = None
    if schedule == "off-peak":
        scheduled_at = _compute_next_off_peak()

    # 7. Enqueue agent run
    run_id = await agent_service.trigger_agent(
        agent_name=task["recommended_agent"],
        goal_slug=task["goal_slug"],
        task_id=task_id,
        input_params=input_params,
        scheduled_at=scheduled_at,
    )

    # 8. Set task status to in_progress (after successful enqueue)
    update_task_status(task_id, "in_progress")

    # 9. Return re-rendered task_item.html with new state
    updated_task = get_task(task_id) or task
    updated_task["active_run"] = agent_service.get_agent_run(run_id)
    _enrich_task_for_render(updated_task)
    return templates.TemplateResponse(
        request,
        "fragments/task_item.html",
        {"task": updated_task},
    )
