"""Page routes — full HTML page renders."""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from cast_server import config as _config
from cast_server.deps import templates
from cast_server.db.connection import get_connection
from cast_server.config import STATUS_TRANSITIONS, PHASES, PHASE_ARTIFACTS, SCRATCHPAD_PATH
from cast_server.services import goal_service, task_service
from cast_server.services.agent_service import get_all_agents, get_dashboard_summary, get_escalated_agents, get_runs_tree
from cast_server.services.task_suggestion_service import get_pending_suggestions

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def index():
    return RedirectResponse(url="/dashboard")


@router.get("/dashboard")
async def dashboard(request: Request, tab: str = "active"):
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

    # Select goals for the active tab
    if tab == "inactive":
        goals = inactive_goals
    elif tab == "completed":
        goals = completed_goals
    else:
        tab = "active"
        goals = active_goals

    # Sort: focused first, then by title
    goals.sort(key=lambda g: (not g["in_focus"], g["title"]))

    conn = get_connection()
    try:
        entries = [dict(r) for r in conn.execute(
            "SELECT * FROM scratchpad_entries ORDER BY entry_date DESC, id DESC LIMIT 5"
        ).fetchall()]

        suggestions = [dict(r) for r in conn.execute(
            "SELECT * FROM goal_suggestions WHERE status = 'pending' ORDER BY created_at DESC"
        ).fetchall()]
    finally:
        conn.close()

    return templates.TemplateResponse(request, "pages/dashboard.html", {
        "goals": goals,
        "tab_counts": tab_counts,
        "active_tab": tab,
        "entries": entries,
        "suggestions": suggestions,
        "active_page": "dashboard",
    })


@router.get("/goals/{slug}")
async def goal_detail(request: Request, slug: str):
    goal = goal_service.get_goal(slug)
    if not goal:
        return templates.TemplateResponse(request, "pages/goal_detail.html", {
            "goal": None,
            "active_page": "dashboard",
        })

    # Load ALL tasks upfront (cheap DB query)
    all_tasks = task_service.get_tasks_for_goal(slug)

    # Group tasks by phase for the Overview tab
    tasks_by_phase = {phase: [] for phase in PHASES}
    for task in all_tasks:
        p = task.get("phase") or "execution"
        if p in tasks_by_phase:
            tasks_by_phase[p].append(task)

    # Compute tab counts (total and completed)
    tab_counts = {phase: len(tasks) for phase, tasks in tasks_by_phase.items()}
    tab_completed = {phase: sum(1 for t in tasks if t.get("status") == "completed")
                     for phase, tasks in tasks_by_phase.items()}

    # Compute phase breadcrumb state
    current_phase = goal.get("phase") or "requirements"
    phase_states = {}
    for phase in PHASES:
        if phase == current_phase:
            phase_states[phase] = "current"
        elif PHASES.index(phase) < PHASES.index(current_phase):
            phase_states[phase] = "completed"
        else:
            phase_states[phase] = "future"

    # Detect which phases have artifacts (for tab indicators)
    folder = Path(goal["folder_path"])
    has_artifacts = {}
    for phase_name, patterns in PHASE_ARTIFACTS.items():
        for pat in patterns:
            if pat.endswith("/"):
                d = folder / pat.rstrip("/")
                if d.is_dir() and any(d.rglob("*.md")):
                    has_artifacts[phase_name] = True
                    break
            else:
                if (folder / pat).is_file():
                    has_artifacts[phase_name] = True
                    break

    # Status navigation info
    next_statuses = STATUS_TRANSITIONS.get(goal["status"], [])

    # Load pending task suggestions grouped by phase
    task_suggestions = get_pending_suggestions(slug)
    suggestions_by_phase = {}
    for s in task_suggestions:
        suggestions_by_phase.setdefault(s["phase"], []).append(s)

    return templates.TemplateResponse(request, "pages/goal_detail.html", {
        "goal": goal,
        "tasks": all_tasks,
        "tasks_by_phase": tasks_by_phase,
        "tab_counts": tab_counts,
        "tab_completed": tab_completed,
        "phase_states": phase_states,
        "has_artifacts": has_artifacts,
        "phases": PHASES,
        "next_statuses": next_statuses,
        "suggestions_by_phase": suggestions_by_phase,
        "agents": get_all_agents(),
        "active_page": "dashboard",
    })


@router.get("/scratchpad")
async def scratchpad(request: Request):
    conn = get_connection()
    try:
        entries = [dict(r) for r in conn.execute(
            "SELECT * FROM scratchpad_entries ORDER BY entry_date DESC, id DESC"
        ).fetchall()]
    finally:
        conn.close()

    grouped = {}
    for entry in entries:
        date = entry["entry_date"]
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(entry)

    return templates.TemplateResponse(request, "pages/scratchpad.html", {
        "grouped_entries": grouped,
        "scratchpad_path": str(SCRATCHPAD_PATH),
        "active_page": "scratchpad",
    })


@router.get("/runs")
async def runs_page(request: Request):
    page = int(request.query_params.get("page", 1))
    status_filter = request.query_params.get("status")
    result = get_runs_tree(status_filter=status_filter, page=page, per_page=25)
    runs = result["runs"]
    active_count = sum(1 for r in runs if r["status"] in ("running", "pending"))
    summary = get_dashboard_summary()
    escalated = get_escalated_agents()
    return templates.TemplateResponse(request, "pages/runs.html", {
        "runs": runs,
        "active_count": active_count,
        "active_filter": status_filter or "all",
        "active_page": "runs",
        "summary": summary,
        "escalated_agents": escalated,
        "pagination": result,
    })


@router.get("/agents")
async def agents_page(request: Request):
    agents = get_all_agents()
    agent_types = sorted(set(a.get("type", "") for a in agents if a.get("type")))
    return templates.TemplateResponse(request, "pages/agents.html", {
        "agents": agents,
        "agent_types": agent_types,
        "active_page": "agents",
    })


@router.get("/focus")
async def focus(request: Request):
    all_goals = goal_service.get_all_goals()
    focused_goals = [g for g in all_goals if g.get("in_focus")]
    focused_goals.sort(key=lambda g: (g.get("status", ""), g.get("title", "")))

    conn = get_connection()
    try:
        goal_slugs = [g["slug"] for g in focused_goals]
        all_tasks = []
        if goal_slugs:
            placeholders = ",".join("?" * len(goal_slugs))
            all_tasks = [dict(r) for r in conn.execute(
                f"SELECT * FROM tasks WHERE goal_slug IN ({placeholders}) AND status != 'completed' AND parent_id IS NULL ORDER BY sort_order",
                goal_slugs,
            ).fetchall()]
    finally:
        conn.close()

    # Group tasks by goal, then by phase within each goal
    tasks_by_goal = {}
    for task in all_tasks:
        tasks_by_goal.setdefault(task["goal_slug"], []).append(task)

    focus_data = []
    for goal in focused_goals:
        goal_tasks = tasks_by_goal.get(goal["slug"], [])
        tasks_by_phase = {phase: [] for phase in PHASES}
        for task in goal_tasks:
            p = task.get("phase") or "execution"
            if p in tasks_by_phase:
                tasks_by_phase[p].append(task)
        focus_data.append({
            "goal": goal,
            "tasks": goal_tasks,
            "tasks_by_phase": tasks_by_phase,
        })

    return templates.TemplateResponse(request, "pages/focus.html", {
        "focus_data": focus_data,
        "phases": PHASES,
        "active_page": "focus",
    })


@router.get("/preso/review/{goal_slug}")
def preso_review(goal_slug: str):
    path = Path(_config.GOALS_DIR) / goal_slug / "presentation" / "review.html"
    if not path.exists():
        return HTMLResponse(
            "<p>No presentation review available for this goal.</p>",
            status_code=404,
        )
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.get("/about")
async def about(request: Request):
    version_path = Path(__file__).resolve().parents[3] / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "dev"
    return templates.TemplateResponse(request, "pages/about.html", {
        "version": version,
        "active_page": "about",
    })
