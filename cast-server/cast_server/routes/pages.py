"""Page routes — full HTML page renders."""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from cast_server import config as _config
from cast_server.deps import templates
from cast_server.db.connection import get_connection
from cast_server.config import STATUS_TRANSITIONS, PHASES, PHASE_ARTIFACTS, SCRATCHPAD_PATH
from cast_server.services import (
    goal_service,
    task_service,
    requirements_render_service,
    render_job_service,
    requirement_version_service,
)
from cast_server.requirements_render import parse_requirements
from cast_server.requirements_render.block_diff import diff_blocks, summarize
from cast_server.requirements_render.blocks import ParsedRequirements
from cast_server.requirements_render.diff_render import render_diff
from cast_server.requirements_render.templating import get_environment
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


def _decorate_skills(run: dict) -> None:
    """Parse `skills_used` JSON in-place and compute `skills_aggregated`.

    Defensive on malformed JSON (`json.JSONDecodeError`) and non-string
    inputs (`TypeError`) — both fall back to an empty list so a single
    bad row never crashes the page. Aggregation groups by `name`,
    counting occurrences and tracking the earliest `invoked_at` as
    `first_invoked`. Recurses through the run's `children` so every
    node in the tree is decorated.
    """
    raw = run.get("skills_used")
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw or "[]")
        except (json.JSONDecodeError, TypeError):
            parsed = []
    elif isinstance(raw, list):
        parsed = raw
    else:
        parsed = []
    if not isinstance(parsed, list):
        parsed = []
    run["skills_used"] = parsed

    aggregated: dict[str, dict] = {}
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name:
            continue
        invoked_at = entry.get("invoked_at") or ""
        bucket = aggregated.get(name)
        if bucket is None:
            aggregated[name] = {"name": name, "first_invoked": invoked_at, "count": 1}
        else:
            bucket["count"] += 1
            if invoked_at and (not bucket["first_invoked"] or invoked_at < bucket["first_invoked"]):
                bucket["first_invoked"] = invoked_at
    run["skills_aggregated"] = list(aggregated.values())

    for child in run.get("children", []):
        _decorate_skills(child)


@router.get("/runs")
async def runs_page(request: Request):
    page = int(request.query_params.get("page", 1))
    status_filter = request.query_params.get("status")
    result = get_runs_tree(status_filter=status_filter, page=page, per_page=25)
    runs = result["runs"]
    for run in runs:
        _decorate_skills(run)
    active_count = sum(1 for r in runs if r["status"] in ("running", "pending"))
    summary = get_dashboard_summary()
    escalated = get_escalated_agents()
    # Phase 5d: read-only flagged-renders list — the honest degraded-page signal under the
    # structural-violation override ("surface, don't suppress"). Reads the 4a recording-only
    # render_jobs flag columns; no new write path, no new column.
    flagged_renders = render_job_service.list_flagged_renders()
    return templates.TemplateResponse(request, "pages/runs.html", {
        "runs": runs,
        "active_count": active_count,
        "active_filter": status_filter or "all",
        "active_page": "runs",
        "summary": summary,
        "escalated_agents": escalated,
        "pagination": result,
        "flagged_renders": flagged_renders,
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


_RENDER_500 = "<p>The requirements render could not be generated. Please try again.</p>"
_NO_REQUIREMENTS = "<p>No requirements yet — run requirements refinement to begin.</p>"


def _poll_script(goal_slug: str) -> str:
    """The ONE poll script (Step 3d.4), injected into BOTH generating flavors.

    Polls the status endpoint every ~4s. On ``ready`` it reloads (the route then serves the
    finished render — "swap-in" = reload-on-ready). On ``failed`` (no servable artifact) it STOPS
    polling and swaps in a terminal "reload to retry" affordance rather than polling forever. The
    slug is JSON-encoded into the URL so a hostile slug can never break out of the string literal.
    """
    status_url = json.dumps(f"/goals/{goal_slug}/render/status")
    return (
        "<script>\n"
        "(function () {\n"
        f"  var url = {status_url};\n"
        "  var POLL_MS = 4000;\n"
        "  function showFailed() {\n"
        "    var root = document.querySelector('[data-render-root]');\n"
        "    var msg = document.querySelector('[data-render-status]');\n"
        "    if (msg) { msg.textContent = 'Generation failed \\u2014 reload to retry.'; }\n"
        "    if (root) { root.setAttribute('data-render-state', 'failed'); }\n"
        "  }\n"
        "  function poll() {\n"
        "    fetch(url, { headers: { 'Accept': 'application/json' } })\n"
        "      .then(function (r) { return r.json(); })\n"
        "      .then(function (d) {\n"
        "        if (d && d.state === 'ready') { location.reload(); return; }\n"
        "        if (d && d.state === 'failed') { showFailed(); return; }\n"
        "        setTimeout(poll, POLL_MS);\n"
        "      })\n"
        "      .catch(function () { setTimeout(poll, POLL_MS); });\n"
        "  }\n"
        "  setTimeout(poll, POLL_MS);\n"
        "})();\n"
        "</script>"
    )


# Response-layer chrome (Step 3d.3 / 3d.4). Inline styles keep these self-contained so they render
# correctly injected into a *bespoke* maker page that does not share our CSS classes — the colours
# match the theme's semantic tokens (--color-warning / --color-danger / --color-on-accent). They are
# NEVER written to disk: injection happens on the response only, so the cached artifact stays
# byte-stable (asserted by the route tests + the manual grep check).
_BANNER_BASE_STYLE = (
    "position:fixed;left:0;right:0;bottom:0;z-index:50;padding:0.75rem 1rem;"
    "text-align:center;font-family:'IBM Plex Mono',monospace;font-size:0.9rem;"
    "color:#FFFFFF;box-shadow:0 -2px 8px rgba(26,26,40,0.18);"
)


def _refreshing_banner(goal_slug: str) -> str:
    """The stale-render regenerating banner + the shared poll script (response-layer injection)."""
    banner = (
        '<div data-render-root data-render-refreshing role="status" aria-live="polite" '
        f'style="{_BANNER_BASE_STYLE}background:#B5821A;">'
        '<span data-render-status>This page is regenerating — '
        "you're reading the previous version.</span>"
        "</div>"
    )
    return banner + _poll_script(goal_slug)


def _needs_review_badge() -> str:
    """The ``structural_violation`` "needs review" badge (response-layer; the OVERRIDE ripple).

    Derived from the served artifact's ``served-by: structural_violation`` stamp — a flagged
    best-attempt render IS servable (status ``ready``); the badge surfaces the degradation to the
    reader without suppressing the render (surface, don't suppress)."""
    return (
        '<div data-render-needs-review role="note" '
        f'style="{_BANNER_BASE_STYLE}background:#B22439;">'
        "Needs review — this render hit a structural issue and is shown as a best attempt."
        "</div>"
    )


def _inject_before_body_close(html: str, snippet: str) -> str:
    """Insert ``snippet`` immediately before the final ``</body>`` (or append if none exists)."""
    idx = html.rfind("</body>")
    if idx == -1:
        return html + snippet
    return html[:idx] + snippet + html[idx:]


def _generating_page(goal_slug: str) -> str:
    """Render the dedicated "no render yet" generating page (themed, poll script, noscript refresh)."""
    template = get_environment().get_template("generating.html.j2")
    return template.render(goal_slug=goal_slug, poll_script=_poll_script(goal_slug))


@router.get("/goals/{slug}/render")
def requirements_render(slug: str):
    """Serve the read-only HTML render of a goal's refined requirements — never blocking on the maker.

    Validates the slug against the goals DB first (unknown → 404, which also kills any
    path-traversal attempt), then dispatches over ``resolve_render``:

    * ``ready`` — serve the cached file untouched; a ``served-by: structural_violation`` artifact
      gets a reader-visible "needs review" badge injected on the response only (the OVERRIDE).
    * ``missing`` / ``stub`` — the legitimate prompt-to-begin / deterministic product states (200).
    * ``generating`` — kick off the idempotent background maker job and immediately serve a live
      generating state: the prior stale render with a regenerating banner when one exists, else a
      dedicated generating page. Either way the cached `.html` on disk is left byte-stable.

    A resolve/serve exception leaves any existing `.html` intact and returns a plain 500 (never a
    stack trace); a *job* failure never 500s the view.
    """
    if goal_service.get_goal(slug) is None:
        return HTMLResponse("<p>Goal not found.</p>", status_code=404)
    try:
        resolution = requirements_render_service.resolve_render(slug)
    except Exception:
        logger.exception("Failed to resolve requirements render for goal %s", slug)
        return HTMLResponse(_RENDER_500, status_code=500)

    if resolution.state == "missing":
        return HTMLResponse(_NO_REQUIREMENTS, status_code=200)

    if resolution.state == "stub":
        # Stub → today's deterministic prompt-to-begin render, instant. The maker is never invoked.
        try:
            path = requirements_render_service.rerender_requirements_html(slug)
        except Exception:
            logger.exception("Failed to render requirements for goal %s", slug)
            return HTMLResponse(_RENDER_500, status_code=500)
        if path is None:
            return HTMLResponse(_NO_REQUIREMENTS, status_code=200)
        return HTMLResponse(path.read_text(encoding="utf-8"))

    if resolution.state == "generating":
        # Idempotent single-flight start — never blocks the view; a start failure still serves a
        # generating state (the next view retries the start).
        try:
            render_job_service.request_render(slug)
        except Exception:
            logger.exception("Failed to start render job for goal %s", slug)
        if resolution.path is not None:
            stale = resolution.path.read_text(encoding="utf-8")
            return HTMLResponse(
                _inject_before_body_close(stale, _refreshing_banner(slug)), status_code=200
            )
        return HTMLResponse(_generating_page(slug), status_code=200)

    # ready — serve the fresh artifact; inject the needs-review badge for a flagged best-attempt.
    try:
        html = resolution.path.read_text(encoding="utf-8")
    except Exception:
        logger.exception("Failed to read requirements render for goal %s", slug)
        return HTMLResponse(_RENDER_500, status_code=500)
    if resolution.served_by == "structural_violation":
        html = _inject_before_body_close(html, _needs_review_badge())
    return HTMLResponse(html, status_code=200)


@router.get("/goals/{slug}/render/status")
def requirements_render_status(slug: str):
    """Poll target for the generating state → JSON ``{state, source_hash}`` (Step 3d.5).

    ``state`` ∈ ``ready`` | ``generating`` | ``failed``. Readiness is a **pure artifact-hash
    derivation** (embedded ``source-hash`` == current) — covering maker, flagged, AND fallback
    publishes; the ``served-by`` stamp drives the badge on the page read-path, never here.
    ``failed`` is returned ONLY when nothing servable exists for the current hash AND its latest
    job row is terminal-``failed`` (a first-generation crash the reaper marked). A stub is
    terminal-servable → ``ready`` (stops a stray poll). Unknown slug → 404 (the path-traversal rule).
    """
    if goal_service.get_goal(slug) is None:
        return JSONResponse({"error": "Goal not found."}, status_code=404)
    try:
        resolution = requirements_render_service.resolve_render(slug)
    except Exception:
        logger.exception("Failed to resolve render status for goal %s", slug)
        return JSONResponse({"state": "failed", "source_hash": None}, status_code=200)

    if resolution.state in ("ready", "stub"):
        # human_review (4a-2) is read from the SERVED artifact's envelope (resolve_render already
        # statted it for the freshness check) — NEVER from the latest render_jobs row, which would
        # silently clear the flag while a fresh regen for the same hash is `running` (A2/P1). A stub
        # is deterministic and never flagged → False.
        return JSONResponse({
            "state": "ready",
            "source_hash": resolution.source_hash,
            "human_review": resolution.human_review if resolution.state == "ready" else False,
        })
    if resolution.state == "missing":
        # No source to generate from — nothing servable will appear; stop the poll.
        return JSONResponse({"state": "failed", "source_hash": None})

    # generating: distinguish "still working" from "gave up with nothing to serve" via the job row.
    row = render_job_service.latest_job_row(slug, resolution.source_hash)
    if row is not None and row.get("status") == "failed":
        return JSONResponse({"state": "failed", "source_hash": resolution.source_hash})
    return JSONResponse({"state": "generating", "source_hash": resolution.source_hash})


def _safe_parse(content: str) -> Optional[ParsedRequirements]:
    """Parse a version snapshot, returning ``None`` on any failure.

    Archived snapshots may predate the structured parser (free-form text). A parse failure
    must NOT 500 the diff view — ``render_diff`` turns a ``None`` side into a "cannot diff
    this pair" card so the rest of the version history stays reachable (sp4a Step 4a.1).
    """
    try:
        return parse_requirements(content)
    except Exception:  # noqa: BLE001 — any parser failure degrades to the cannot-diff card
        logger.warning("Could not parse a version snapshot for diff rendering")
        return None


@router.get("/goals/{slug}/render/diff")
def requirements_render_diff(slug: str, base: Optional[int] = None, head: Optional[int] = None):
    """Serve the read-only tracked-changes view between two requirement versions.

    Derived, never persisted: rendered fresh each request and never written to the goal
    folder (FR-011 — only the canonical ``/render`` is a file artifact). The transient
    ``id="diff-{n}"`` anchors live only in this view, never in the canonical render.

    Defaults: ``head = current version``, ``base = head − 1``. Fewer than two versions → a
    plain "no prior version to compare" card (200, never an error). ``base >= head`` → 422.
    Unknown slug → 404 (the path-traversal rule). An unparseable archived snapshot degrades
    to a "cannot diff this pair" card, never a 500.
    """
    if goal_service.get_goal(slug) is None:
        return HTMLResponse("<p>Goal not found.</p>", status_code=404)

    versions = requirement_version_service.list_versions(slug)
    if len(versions) < 2:
        return HTMLResponse(
            "<main class='rr-document rr-diff'><section class='diff-changed-panel'>"
            "<h2 class='diff-changed-title'>No prior version to compare</h2>"
            "<p class='diff-changed-empty'>This goal has fewer than two requirement "
            "versions, so there is nothing to diff yet.</p></section></main>",
            status_code=200,
        )

    current = requirement_version_service.get_current(slug)
    current_version = current["version"] if current else versions[-1]["version"]
    if head is None:
        head = current_version
    if base is None:
        base = head - 1

    if base >= head:
        return HTMLResponse(
            "<p>Invalid version range: <code>base</code> must be older than "
            "<code>head</code>.</p>",
            status_code=422,
        )

    base_row = requirement_version_service.get_version(slug, base)
    head_row = requirement_version_service.get_version(slug, head)
    if base_row is None or head_row is None:
        return HTMLResponse("<p>Requested version not found.</p>", status_code=404)

    old_parsed = _safe_parse(base_row["content"])
    new_parsed = _safe_parse(head_row["content"])
    result = render_diff(old_parsed, new_parsed, base_version=base, head_version=head)
    html = _inject_diff_narration(slug, base, head, old_parsed, new_parsed, result.html)
    return HTMLResponse(html)


def _inject_diff_narration(
    slug: str,
    base: int,
    head: int,
    old_parsed: Optional[ParsedRequirements],
    new_parsed: Optional[ParsedRequirements],
    diff_html: str,
) -> str:
    """Splice the stored same-door narration into the tracked-changes "What changed" panel.

    `diff_render.py` is intentionally NOT modified (the deterministic view stays byte-identical);
    instead the route renders the SAME autoescaped `_diff_narration.html` partial the changes
    panel uses (lookup-only against the deterministic `summarize()` items) and inserts it before
    the panel's closing tag. When no narration is stored, the diff HTML is returned untouched —
    so the view is byte-identical to the no-narration render.
    """
    if old_parsed is None or new_parsed is None:
        return diff_html  # cannot-diff card has no deterministic items to attach to
    narration = requirement_version_service.get_narration(slug, base, head)
    if narration is None:
        return diff_html
    items = summarize(diff_blocks(old_parsed, new_parsed))["items"]
    strip = templates.get_template(
        "fragments/requirements_comments/_diff_narration.html"
    ).render(narration=narration, items=items)
    # The "What changed" panel is the first <section> in the diff document; insert before it
    # closes so the strip rides inside the panel, styled by the inlined `.diff-narration` CSS.
    return diff_html.replace("</section>", strip + "</section>", 1)


@router.get("/about")
async def about(request: Request):
    version_path = Path(__file__).resolve().parents[3] / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "dev"
    return templates.TemplateResponse(request, "pages/about.html", {
        "version": version,
        "active_page": "about",
    })
