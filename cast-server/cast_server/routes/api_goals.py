"""Goal API endpoints — HTMX fragment responses."""

import logging
from pathlib import Path

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, Response

from cast_server.deps import templates
from cast_server.services.goal_service import (
    create_goal, update_status as change_status, update_phase as set_phase, toggle_focus,
)
from cast_server.services import agent_service, goal_service, task_service
from cast_server.services.suggestion_service import approve_suggestion, decline_suggestion
from cast_server.utils.responses import toast_header

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/goals", tags=["goals"])


def _is_detail_page(request: Request, slug: str) -> bool:
    """Check if the HTMX request came from a goal detail page."""
    current_url = request.headers.get("HX-Current-URL", "")
    return f"/goals/{slug}" in current_url


def _is_dashboard(request: Request) -> bool:
    """Check if the HTMX request came from the dashboard."""
    current_url = request.headers.get("HX-Current-URL", "")
    return "/dashboard" in current_url


def _tab_count_oob() -> str:
    """Generate OOB swap HTML for dashboard tab count badges."""
    all_goals = goal_service.get_all_goals()
    active = sum(1 for g in all_goals if g["status"] in ("idea", "accepted"))
    inactive = sum(1 for g in all_goals if g["status"] == "inactive")
    completed = sum(1 for g in all_goals if g["status"] == "completed")
    return (
        f'<span class="dashboard-tab-count" id="tab-count-active" hx-swap-oob="true">{active}</span>'
        f'<span class="dashboard-tab-count" id="tab-count-inactive" hx-swap-oob="true">{inactive}</span>'
        f'<span class="dashboard-tab-count" id="tab-count-completed" hx-swap-oob="true">{completed}</span>'
    )


@router.get("/dashboard")
async def dashboard_goals(request: Request, tab: str = "active"):
    """Return filtered goal list fragment for dashboard tab switching."""
    all_goals = goal_service.get_all_goals()

    # Compute tab counts
    active_goals = [g for g in all_goals if g["status"] in ("idea", "accepted")]
    inactive_goals = [g for g in all_goals if g["status"] == "inactive"]
    completed_goals = [g for g in all_goals if g["status"] == "completed"]

    tab_counts = {
        "active": len(active_goals),
        "inactive": len(inactive_goals),
        "completed": len(completed_goals),
    }

    if tab == "inactive":
        goals = inactive_goals
    elif tab == "completed":
        goals = completed_goals
    else:
        tab = "active"
        goals = active_goals

    goals.sort(key=lambda g: (not g["in_focus"], g["title"]))

    response = templates.TemplateResponse(request, "fragments/dashboard_goal_list.html", {
        "goals": goals,
        "active_tab": tab,
    })
    # OOB swap tab counts — build combined body and return a new Response
    # to avoid Content-Length mismatch from mutating TemplateResponse.body
    oob_html = (
        f'<span class="dashboard-tab-count" id="tab-count-active" hx-swap-oob="true">{tab_counts["active"]}</span>'
        f'<span class="dashboard-tab-count" id="tab-count-inactive" hx-swap-oob="true">{tab_counts["inactive"]}</span>'
        f'<span class="dashboard-tab-count" id="tab-count-completed" hx-swap-oob="true">{tab_counts["completed"]}</span>'
    )
    combined = response.body + oob_html.encode()
    return Response(content=combined, media_type="text/html")


@router.post("")
async def create_goal_endpoint(
    request: Request,
    title: str = Form(...),
    tags: str = Form(""),
):
    """Create a new goal. Returns goal_card fragment."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    goal = create_goal(title=title, tags=tag_list)
    return templates.TemplateResponse(request, "fragments/goal_card.html", {
        "goal": goal,
    })


@router.put("/{slug}/status")
async def update_status(
    request: Request,
    slug: str,
    status: str = Form(...),
):
    """Change goal status. Returns updated goal_card fragment or redirects."""
    try:
        goal = change_status(slug, status)
    except ValueError as e:
        logger.warning("Status transition failed for %s: %s", slug, e)
        raise HTTPException(status_code=422, detail=str(e))

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    logger.info("Goal '%s' status changed to '%s'", slug, status)

    if _is_detail_page(request, slug):
        return Response(
            status_code=200,
            headers={
                "HX-Redirect": f"/goals/{slug}",
                "HX-Trigger": toast_header(f"Status updated to {status}"),
            },
        )

    if _is_dashboard(request):
        # On dashboard: remove the card (empty response) and update tab counts via OOB
        oob_html = _tab_count_oob()
        return Response(
            content=oob_html,
            media_type="text/html",
            headers={"HX-Trigger": toast_header(f"Status updated to {status}")},
        )

    response = templates.TemplateResponse(request, "fragments/goal_card.html", {
        "goal": goal,
    })
    response.headers["HX-Trigger"] = toast_header(f"Status updated to {status}")
    return response


@router.put("/{slug}/phase")
async def update_phase(
    request: Request,
    slug: str,
    phase: str = Form(...),
):
    """Change goal phase. Returns redirect to reload page."""
    try:
        goal = set_phase(slug, phase)
    except ValueError as e:
        logger.warning("Phase change failed for %s: %s", slug, e)
        raise HTTPException(status_code=422, detail=str(e))

    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    logger.info("Goal '%s' phase changed to '%s'", slug, phase)

    return Response(
        status_code=200,
        headers={
            "HX-Redirect": f"/goals/{slug}",
            "HX-Trigger": toast_header(f"Phase updated to {phase}"),
        },
    )


@router.put("/{slug}/focus")
async def update_focus(
    request: Request,
    slug: str,
    in_focus: str = Form(...),
):
    """Toggle focus. Returns updated goal_card fragment or redirects."""
    goal = toggle_focus(slug, in_focus == "true")
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    focus_msg = "Added to focus" if in_focus == "true" else "Removed from focus"
    logger.info("Goal '%s' focus toggled: %s", slug, focus_msg)

    if _is_detail_page(request, slug):
        return Response(
            status_code=200,
            headers={
                "HX-Redirect": f"/goals/{slug}",
                "HX-Trigger": toast_header(focus_msg),
            },
        )

    response = templates.TemplateResponse(request, "fragments/goal_card.html", {
        "goal": goal,
    })
    response.headers["HX-Trigger"] = toast_header(focus_msg)
    return response


@router.patch("/{slug}/config")
async def update_goal_config(
    request: Request,
    slug: str,
    gstack_dir: str = Form(None),
    external_project_dir: str = Form(None),
):
    """Update goal directory config fields.

    HTMX callers get the re-rendered dir-config fragment + a success toast.
    Non-HTMX callers get JSON.
    """
    goal = goal_service.get_goal(slug)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if external_project_dir is not None:
        external_project_dir = external_project_dir.strip() or None

    updated = goal_service.update_config(
        slug,
        gstack_dir=gstack_dir,
        external_project_dir=external_project_dir,
    )

    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            request,
            "fragments/goal_dir_config.html",
            {"goal": updated, "editing": False},
        )
        response.headers["HX-Trigger"] = toast_header("Project directory saved")
        return response
    return {"status": "ok", "goal": updated}


@router.get("/{slug}/config/edit")
async def get_goal_config_edit(request: Request, slug: str):
    """Return the dir-config fragment in edit (form) mode."""
    goal = goal_service.get_goal(slug)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return templates.TemplateResponse(
        request,
        "fragments/goal_dir_config.html",
        {"goal": goal, "editing": True},
    )


@router.get("/{slug}/config/view")
async def get_goal_config_view(request: Request, slug: str):
    """Return the dir-config fragment in view mode (cancel-edit)."""
    goal = goal_service.get_goal(slug)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return templates.TemplateResponse(
        request,
        "fragments/goal_dir_config.html",
        {"goal": goal, "editing": False},
    )


@router.get("/{slug}/tab/{phase}")
async def get_phase_tab(request: Request, slug: str, phase: str):
    """Return phase tab content fragment (tasks + rendered artifacts).
    Used by HTMX hx-trigger='click once' on phase tab buttons."""
    import markdown as md
    from cast_server.config import PHASES, PHASE_ARTIFACTS
    from cast_server.utils.file_utils import extract_authorship

    MD_EXTENSIONS = ["fenced_code", "tables", "toc", "codehilite"]
    MD_EXTENSION_CONFIGS = {
        "codehilite": {"css_class": "highlight", "guess_lang": False},
    }

    def render_md(text: str) -> str:
        try:
            return md.markdown(text, extensions=MD_EXTENSIONS,
                               extension_configs=MD_EXTENSION_CONFIGS)
        except Exception:
            return f"<pre>{text}</pre>"

    if phase not in PHASES:
        return HTMLResponse(content="Invalid phase", status_code=400)

    goal = goal_service.get_goal(slug)
    if not goal:
        return HTMLResponse(content="Goal not found", status_code=404)

    tasks = task_service.get_tasks_for_goal(slug, phase=phase)

    # Attach active_run and last_run to tasks that have recommended_agent
    task_ids = [t["id"] for t in tasks if t.get("recommended_agent")]
    if task_ids:
        active_runs = agent_service.get_active_runs_for_tasks(task_ids)

        from cast_server.db.connection import get_connection
        conn = get_connection()
        placeholders = ",".join("?" * len(task_ids))
        completed_rows = conn.execute(
            f"""SELECT * FROM agent_runs
                WHERE task_id IN ({placeholders})
                AND status IN ('completed', 'failed')
                ORDER BY completed_at DESC""",
            task_ids,
        ).fetchall()
        conn.close()
        last_runs = {}
        for row in completed_rows:
            d = agent_service._row_to_dict(row)
            if d["task_id"] not in last_runs:
                # Auto-recover timed-out runs whose agents finished late
                if d["status"] == "failed" and d.get("error_message", "").startswith("Timed out"):
                    recovered = agent_service.recheck_failed_run(d["id"])
                    if recovered:
                        d = recovered
                last_runs[d["task_id"]] = d

        for task in tasks:
            task["active_run"] = active_runs.get(task["id"])
            task["last_run"] = last_runs.get(task["id"])

    # Collect artifacts with rendered markdown content
    goal_dir = Path(goal["folder_path"])
    artifacts = []

    def _add_md_file(f: Path, section: str = ""):
        """Read a markdown file and append it as an artifact."""
        try:
            label = f.stem.replace("-", " ").replace("_", " ").title()
            if section:
                label = f"{section}: {label}"
            artifacts.append({
                "name": label,
                "path": str(f),
                "html": render_md(f.read_text()),
                "authorship": extract_authorship(f.name),
            })
        except OSError:
            pass

    for artifact_pattern in PHASE_ARTIFACTS.get(phase, []):
        if artifact_pattern.endswith("/"):
            dir_path = goal_dir / artifact_pattern.rstrip("/")
            if not dir_path.is_dir():
                continue
            # Top-level .md files (e.g. summary.md)
            for f in sorted(dir_path.glob("*.md")):
                _add_md_file(f)
            # Subdirectories (e.g. research/, playbooks/)
            for subdir in sorted(dir_path.iterdir()):
                if subdir.is_dir():
                    for f in sorted(subdir.glob("*.md")):
                        _add_md_file(f, section=subdir.name.capitalize())
        else:
            file_path = goal_dir / artifact_pattern
            if file_path.is_file():
                _add_md_file(file_path)

    from cast_server.services.task_suggestion_service import get_pending_suggestions
    phase_suggestions = get_pending_suggestions(slug, phase=phase)

    return templates.TemplateResponse(
        request,
        "fragments/phase_tab_content.html",
        {"goal": goal, "tasks": tasks,
         "phase": phase, "artifacts": artifacts,
         "phase_suggestions": phase_suggestions}
    )


@router.post("/suggestions/{suggestion_id}/approve")
async def approve(request: Request, suggestion_id: int):
    """Approve a goal suggestion — creates a goal at 'idea' status."""
    goal = approve_suggestion(suggestion_id)
    return templates.TemplateResponse(request, "fragments/goal_card.html", {
        "goal": goal,
    })


@router.post("/suggestions/{suggestion_id}/decline")
async def decline(request: Request, suggestion_id: int):
    """Decline a goal suggestion — removes the suggestion card."""
    decline_suggestion(suggestion_id)
    return Response(content="", media_type="text/html")


