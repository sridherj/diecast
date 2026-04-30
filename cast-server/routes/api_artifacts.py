"""API endpoints for inline artifact editing and artifact sidebar."""

from pathlib import Path

import markdown as md
from fastapi import APIRouter, Form, Request, Response

from taskos.config import GOALS_DIR
from taskos.deps import templates  # noqa: F401 — used by edit_artifact
from taskos.utils.responses import toast_header

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])

MD_EXTENSIONS = ["fenced_code", "tables", "toc", "codehilite"]
MD_EXTENSION_CONFIGS = {
    "codehilite": {"css_class": "highlight", "guess_lang": False},
}


def _validate_artifact_path_base(path: str, goal_slug: str | None = None) -> Path:
    """Core path validation — within GOALS_DIR or goal's external_project_dir."""
    original = Path(path)
    resolved = original.resolve()

    # Always allow within GOALS_DIR
    if resolved.is_relative_to(GOALS_DIR.resolve()):
        if not resolved.exists():
            raise ValueError("File not found")
        return resolved

    # Allow within external_project_dir if goal has one
    if goal_slug:
        from taskos.services import goal_service
        goal = goal_service.get_goal(goal_slug)
        ext_dir = goal.get("external_project_dir") if goal else None
        if ext_dir:
            ext_resolved = Path(ext_dir).expanduser().resolve()
            if resolved.is_relative_to(ext_resolved) and resolved.exists():
                return resolved

    raise ValueError("Path outside allowed directories")


def validate_artifact_path(path: str, goal_slug: str | None = None) -> Path:
    """Validate artifact path for EDITING. Must be .human.md or .collab.md."""
    resolved = _validate_artifact_path_base(path, goal_slug=goal_slug)
    if not (resolved.name.endswith(".human.md") or resolved.name.endswith(".collab.md")):
        raise ValueError("Only .human.md and .collab.md files are editable")
    return resolved


def validate_artifact_path_read(path: str, goal_slug: str | None = None) -> Path:
    """Validate artifact path for READING. Any .md file within allowed dirs."""
    resolved = _validate_artifact_path_base(path, goal_slug=goal_slug)
    if not resolved.name.endswith(".md"):
        raise ValueError("Only markdown files can be viewed")
    return resolved


@router.get("/edit")
async def edit_artifact(request: Request, path: str, goal_slug: str = "", phase: str = ""):
    """Return editor form with artifact content in a textarea."""
    try:
        resolved = validate_artifact_path(path, goal_slug=goal_slug)
    except ValueError as e:
        return Response(status_code=400, content=str(e))

    content = resolved.read_text()
    return templates.TemplateResponse(
        request,
        "fragments/artifact_editor.html",
        {
            "path": path,
            "content": content,
            "goal_slug": goal_slug,
            "phase": phase,
        },
    )


@router.put("/save")
async def save_artifact(
    path: str = Form(...),
    content: str = Form(...),
    goal_slug: str = Form(""),
    phase: str = Form(""),
):
    """Save edited artifact content back to file, then reload phase tab."""
    try:
        resolved = validate_artifact_path(path, goal_slug=goal_slug)
    except ValueError as e:
        return Response(status_code=400, content=str(e))

    resolved.write_text(content)

    # Return a placeholder that auto-loads the full phase tab via HTMX
    html = (
        f'<div class="phase-tab-content"'
        f' hx-get="/api/goals/{goal_slug}/tab/{phase}"'
        f' hx-trigger="load"'
        f' hx-swap="outerHTML">'
        f'<p class="loading-text">Saving...</p>'
        f'</div>'
    )
    response = Response(content=html, media_type="text/html")
    response.headers["HX-Trigger"] = toast_header("Artifact saved")
    return response


@router.get("/artifact-sidebar")
async def artifact_sidebar(request: Request, task_id: int, artifact_path: str):
    """Return rendered artifact sidebar fragment for a task's linked artifact."""
    from taskos.services.task_service import get_task

    task = get_task(task_id)
    if not task:
        return Response(status_code=404, content="Task not found")

    goal_slug = task["goal_slug"]

    # Resolve path relative to goal directory
    goal_dir = GOALS_DIR / goal_slug
    full_path_str = str((goal_dir / artifact_path).resolve())

    try:
        resolved = validate_artifact_path_read(full_path_str, goal_slug=goal_slug)
    except ValueError as e:
        return Response(status_code=400, content=str(e))

    # Read and render markdown
    content = resolved.read_text()
    html = md.markdown(content, extensions=MD_EXTENSIONS,
                       extension_configs=MD_EXTENSION_CONFIGS)

    # Determine authorship from filename
    name = resolved.name
    authorship = None
    if name.endswith(".human.md"):
        authorship = "human"
    elif name.endswith(".collab.md"):
        authorship = "collab"
    elif name.endswith(".ai.md"):
        authorship = "ai"

    # Use relative path for display (don't leak server filesystem paths)
    display_path = f"{goal_slug}/{artifact_path}"

    return templates.TemplateResponse(request, "fragments/artifact_sidebar.html", {
        "name": name,
        "path": display_path,
        "html": html,
        "authorship": authorship,
        "goal_slug": goal_slug,
        "phase": task.get("phase", ""),
    })
