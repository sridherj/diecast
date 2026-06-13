"""Same-door requirements comment API (Phase 4, WP-A) — prefix ``/api/goals/{goal_slug}/requirements``.

The FR-013 forcing function: a human composer's ``hx-post`` and an agent's ``curl`` hit the
IDENTICAL endpoint and run the SAME ``comment_service`` call. ``author_kind`` is the only
distinction; the request header (``HX-Request``) selects only the *response shape* — an HTML
fragment for HTMX, JSON otherwise. There is never a second write path.

Validation lives here (Pydantic request models: required/non-empty/≤10 KB) so the service
stays a thin DB layer. ``GET /versions`` ships list-only this sub-phase; ``POST``/``GET /{n}``
and ``/changes`` land in sp3/sp4a.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from cast_server.config import GOALS_DIR
from cast_server.deps import templates
from cast_server.requirements_render import parse_requirements
from cast_server.requirements_render.block_diff import diff_blocks, summarize
from cast_server.services import (
    comment_service,
    goal_service,
    notification_service,
    requirement_version_service,
    requirements_render_service,
)
from cast_server.services.comment_service import CommentNotFound, CommentStateError

router = APIRouter(prefix="/api/goals/{goal_slug}/requirements", tags=["requirements"])

_MAX_FIELD_BYTES = 10 * 1024  # 10 KB cap on quoted_text / body (WP-A design-review guard)


def _check_size(value: str, field: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field} must be non-empty")
    if len(value.encode("utf-8")) > _MAX_FIELD_BYTES:
        raise ValueError(f"{field} exceeds {_MAX_FIELD_BYTES} bytes")
    return value


class CreateCommentRequest(BaseModel):
    quoted_text: str
    body: str
    section_hint: str | None = None
    author: str = "human"
    author_kind: str = "human"

    @field_validator("quoted_text")
    @classmethod
    def _v_quoted(cls, v: str) -> str:
        return _check_size(v, "quoted_text")

    @field_validator("body")
    @classmethod
    def _v_body(cls, v: str) -> str:
        return _check_size(v, "body")


class ActorRequest(BaseModel):
    actor: str | None = None


class RelocateRequest(BaseModel):
    new_quoted_text: str
    new_section_hint: str | None = None
    actor: str | None = None

    @field_validator("new_quoted_text")
    @classmethod
    def _v_quoted(cls, v: str) -> str:
        return _check_size(v, "new_quoted_text")


class NarrationItemNote(BaseModel):
    change: str
    heading_or_ref: str
    note: str


class NarrationRequest(BaseModel):
    """Same-door narration body. ``created_by`` (the dispatching parent's actor id) rides the
    body — nothing about the caller is privileged. ``actor`` is accepted as an alias so the
    surface reads consistently with the resolve/relocate transition POSTs."""

    base: int
    overview: str
    item_notes: list[NarrationItemNote] = []
    created_by: str | None = None
    actor: str | None = None


def _require_goal(goal_slug: str):
    """Slug-validate first (the Phase 3a path-traversal rule); ``None`` → caller returns 404."""
    return goal_service.get_goal(goal_slug)


def _not_found() -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Goal not found"})


def _is_hx(request: Request) -> bool:
    return request.headers.get("hx-request", "").lower() == "true"


def _current_text(goal_slug: str) -> str:
    """Current goal-file text for the relocate substring backstop (``""`` if absent)."""
    return comment_service._resolve_current_text(goal_slug, None, None)


def _relocate_compare_text(goal_slug: str, comment: dict) -> str:
    """The verbatim-substring backstop text for a relocate, chosen per the comment's anchor space
    (refine-req-v3 sp2). A ``'render'``-space comment validates against the SERVED render's
    container text (degrading to the source check when no render is on disk); a ``'source'``-space
    comment keeps the canonical source check. ``block_ref`` is never read from the request — it
    stays server-resolved (trust boundary)."""
    if comment.get("anchor_space") == "render":
        return comment_service._resolve_render_compare_text(goal_slug, None, None)
    return comment_service._resolve_current_text(goal_slug, None, None)


# --------------------------------------------------------------------------- #
# Comments                                                                     #
# --------------------------------------------------------------------------- #

@router.get("/comments")
async def list_comments(request: Request, goal_slug: str, state: str | None = None):
    """List comments — JSON rows (open ones carry ``displaced``) | HTML tray fragment."""
    if _require_goal(goal_slug) is None:
        return _not_found()
    comments = comment_service.list_comments(goal_slug, state=state)
    if _is_hx(request):
        return templates.TemplateResponse(
            request, "fragments/requirements_comments/tray.html",
            {"goal_slug": goal_slug, "comments": comments},
        )
    return JSONResponse(content={"comments": comments})


@router.post("/comments")
async def create_comment(request: Request, goal_slug: str):
    """THE canonical dual-assertion handler (FR-013).

    ONE ``comment_service.create_comment`` call runs regardless of header; only the response
    shape differs (HTML thread-item fragment for HTMX, JSON 201 otherwise).
    """
    if _require_goal(goal_slug) is None:
        return _not_found()
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else dict(await request.form())
    try:
        payload = CreateCommentRequest(**body)
    except Exception as e:  # noqa: BLE001 — pydantic ValidationError → 422
        return JSONResponse(status_code=422, content={"detail": str(e)})

    row = comment_service.create_comment(
        goal_slug,
        quoted_text=payload.quoted_text,
        section_hint=payload.section_hint,
        body=payload.body,
        author=payload.author,
        author_kind=payload.author_kind,
    )
    if _is_hx(request):
        return templates.TemplateResponse(
            request, "fragments/requirements_comments/thread_item.html",
            {"goal_slug": goal_slug, "comment": row},
        )
    return JSONResponse(status_code=201, content=row)


def _transition_response(request: Request, goal_slug: str, row: dict):
    if _is_hx(request):
        return templates.TemplateResponse(
            request, "fragments/requirements_comments/thread_item.html",
            {"goal_slug": goal_slug, "comment": row},
        )
    return JSONResponse(content=row)


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(request: Request, goal_slug: str, comment_id: int):
    if _require_goal(goal_slug) is None:
        return _not_found()
    actor = (await _read_actor(request)).actor
    try:
        row = comment_service.resolve_comment(comment_id, actor)
    except CommentNotFound:
        return JSONResponse(status_code=404, content={"detail": "Comment not found"})
    except CommentStateError as e:
        return JSONResponse(status_code=409, content={"detail": str(e)})
    return _transition_response(request, goal_slug, row)


@router.post("/comments/{comment_id}/reopen")
async def reopen_comment(request: Request, goal_slug: str, comment_id: int):
    if _require_goal(goal_slug) is None:
        return _not_found()
    actor = (await _read_actor(request)).actor
    try:
        row = comment_service.reopen_comment(comment_id, actor)
    except CommentNotFound:
        return JSONResponse(status_code=404, content={"detail": "Comment not found"})
    except CommentStateError as e:
        return JSONResponse(status_code=409, content={"detail": str(e)})
    return _transition_response(request, goal_slug, row)


@router.post("/comments/{comment_id}/orphan")
async def orphan_comment(request: Request, goal_slug: str, comment_id: int):
    if _require_goal(goal_slug) is None:
        return _not_found()
    actor = (await _read_actor(request)).actor
    try:
        row = comment_service.orphan_comment(comment_id, actor)
    except CommentNotFound:
        return JSONResponse(status_code=404, content={"detail": "Comment not found"})
    return _transition_response(request, goal_slug, row)


@router.post("/comments/{comment_id}/relocate")
async def relocate_comment(request: Request, goal_slug: str, comment_id: int):
    """Re-anchor a comment. ``new_quoted_text`` MUST be a verbatim substring of the current
    file, else 422 (the deterministic backstop on subagent output; sp4b relies on it)."""
    if _require_goal(goal_slug) is None:
        return _not_found()
    raw = await _read_body(request)
    try:
        payload = RelocateRequest(**raw)
    except Exception as e:  # noqa: BLE001
        return JSONResponse(status_code=422, content={"detail": str(e)})

    # Load the comment first so the backstop validates against the RIGHT text space (render for a
    # render-anchored comment, source for a legacy one). A 404 here is the same as relocate's.
    try:
        existing = comment_service.get_comment(comment_id)
    except CommentNotFound:
        return JSONResponse(status_code=404, content={"detail": "Comment not found"})

    if payload.new_quoted_text not in _relocate_compare_text(goal_slug, existing):
        return JSONResponse(
            status_code=422,
            content={"detail": "new_quoted_text is not a verbatim substring of the current render",
                     "offending_quote": payload.new_quoted_text},
        )
    try:
        row = comment_service.relocate_comment(
            comment_id, payload.new_quoted_text, payload.new_section_hint, payload.actor,
        )
    except CommentNotFound:
        return JSONResponse(status_code=404, content={"detail": "Comment not found"})
    return _transition_response(request, goal_slug, row)


# --------------------------------------------------------------------------- #
# Versions (list only this sub-phase)                                          #
# --------------------------------------------------------------------------- #

@router.get("/versions")
async def list_versions(request: Request, goal_slug: str):
    """JSON version list + the structured ``needs_attention`` surface.

    ``convergence = "unconverged" if open_comment_count > 0 else "converged"`` (the one
    convergence rule, derived never stored). Phase 5 sp3b **extends** this same surface (owner
    decision #4 — never a parallel notifier) with ``recent_writebacks``: the round-trip /
    provenance descriptor sourced from *delivered* outbox rows, so the Goal-Card badge can render
    *what changed + from where* without a second fetch. The landed
    ``{versions, convergence, open_comment_count}`` keys are unchanged.
    """
    if _require_goal(goal_slug) is None:
        return _not_found()
    versions = requirement_version_service.list_versions(goal_slug)
    open_count = comment_service.open_comment_count(goal_slug)
    return JSONResponse(content={
        "versions": versions,
        "convergence": "unconverged" if open_count > 0 else "converged",
        "open_comment_count": open_count,
        "recent_writebacks": notification_service.recent_writebacks(goal_slug),
    })


@router.post("/versions")
async def create_version(request: Request, goal_slug: str):
    """Snapshot the next version from the goal's CURRENT ``refined_requirements.collab.md``.

    JSON-only (an agent/loop surface — no HTMX negotiation). The server READS the goal file;
    it never writes the artifact (delegation contract intact, FR-011). Missing file → 409
    ("nothing to snapshot"). Returns the ``create_next`` contract dict (version, convergence,
    open_comments, displaced_comment_ids) — the seam sp4b dispatches ``cast-comment-reanchor``
    over.
    """
    if _require_goal(goal_slug) is None:
        return _not_found()
    goal_dir = requirements_render_service._resolve_goal_dir(goal_slug, GOALS_DIR, None)
    source = goal_dir / "refined_requirements.collab.md"
    if not source.exists():
        return JSONResponse(
            status_code=409,
            content={"detail": "nothing to snapshot: refined_requirements.collab.md is absent"},
        )
    content = source.read_text(encoding="utf-8")
    actor = (await _read_actor(request)).actor or "human"
    result = requirement_version_service.create_next(goal_slug, content, created_by=actor)
    return JSONResponse(content=result)


def _resolve_diff_range(goal_slug: str, base: int | None, head: int | None):
    """Default ``head = current version``, ``base = head − 1`` (sp4a Step 4a.2).

    Returns ``(base, head)`` resolved against the goal's version list.
    """
    versions = requirement_version_service.list_versions(goal_slug)
    current = requirement_version_service.get_current(goal_slug)
    current_version = (
        current["version"] if current else (versions[-1]["version"] if versions else 0)
    )
    if head is None:
        head = current_version
    if base is None:
        base = head - 1
    return base, head


@router.get("/changes")
async def changes(request: Request, goal_slug: str, base: int | None = None, head: int | None = None):
    """The deterministic change set between two versions (FR-017's same-door surface).

    Negotiated: ``summarize(diff_blocks(old, new))`` JSON (header-less) | the "What changed"
    panel fragment (``HX-Request``). Agents read the change set EXACTLY as the panel renders
    it — one door, two shapes. The structural diff is the source of truth (decision #8); this
    endpoint never invents entries, it only reports ``summarize()``.

    Defaults: ``head = current``, ``base = head − 1``. Slug → 404; ``base >= head`` → 422;
    an unknown version → 404; an unparseable archived snapshot → 422 (never a 500).
    """
    if _require_goal(goal_slug) is None:
        return _not_found()
    base, head = _resolve_diff_range(goal_slug, base, head)
    if base >= head:
        return JSONResponse(
            status_code=422,
            content={"detail": "base must be older than head", "base": base, "head": head},
        )
    base_row = requirement_version_service.get_version(goal_slug, base)
    head_row = requirement_version_service.get_version(goal_slug, head)
    if base_row is None or head_row is None:
        return JSONResponse(status_code=404, content={"detail": "Version not found"})
    try:
        old = parse_requirements(base_row["content"])
        new = parse_requirements(head_row["content"])
    except Exception:  # noqa: BLE001 — a pre-parser snapshot cannot be diffed; never 500
        return JSONResponse(
            status_code=422,
            content={"detail": "cannot diff: one snapshot predates the structured parser"},
        )
    summary = summarize(diff_blocks(old, new))
    # FR-024 re-scope: `counts`/`items` stay byte-for-byte `summarize()`; `narration` is a SIBLING
    # key (None when no narration was posted — the deterministic panel is the floor).
    narration = requirement_version_service.get_narration(goal_slug, base, head)
    if _is_hx(request):
        return templates.TemplateResponse(
            request, "fragments/requirements_comments/changes_panel.html",
            {"goal_slug": goal_slug, "base": base, "head": head,
             "summary": summary, "narration": narration},
        )
    return JSONResponse(content={**summary, "narration": narration})


@router.post("/versions/{head}/narration")
async def post_narration(request: Request, goal_slug: str, head: int):
    """Store the same-door narration for the ``(base, head)`` diff (Phase 4b-3).

    JSON-only (agents are the writers; humans read). Slug-validated first (FR-014) → 404. The
    server recomputes the deterministic diff and rejects any note referencing a change absent
    from it → **422 with the offending keys** (all-or-nothing — no silent note-dropping). An
    unknown base/head version → 404; a size-cap violation → 422. ``created_by`` is taken from the
    request body (``created_by`` or its ``actor`` alias) and stamped on the row.
    """
    if _require_goal(goal_slug) is None:
        return _not_found()
    raw = await _read_body(request)
    try:
        payload = NarrationRequest(**raw)
    except Exception as e:  # noqa: BLE001 — pydantic ValidationError → 422
        return JSONResponse(status_code=422, content={"detail": str(e)})

    created_by = payload.created_by or payload.actor
    try:
        narration = requirement_version_service.save_narration(
            goal_slug, payload.base, head, payload.overview,
            [n.model_dump() for n in payload.item_notes], created_by,
        )
    except requirement_version_service.NarrationVersionNotFound:
        return JSONResponse(status_code=404, content={"detail": "Version not found"})
    except requirement_version_service.NarrationValidationError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": str(e), "offending_keys": e.offending_keys},
        )
    return JSONResponse(content=narration)


@router.get("/versions/{version}")
async def get_version(request: Request, goal_slug: str, version: int):
    """An archived (or current) version row WITH its comments at as-of resolution state (US5 S3).

    The as-of state is reconstructed by replaying each comment's append-only ``comment_events``
    trail up to this version's supersession instant — a query over the trail, never a stored
    feature. Unknown slug → 404; unknown version → 404.
    """
    if _require_goal(goal_slug) is None:
        return _not_found()
    payload = requirement_version_service.get_version_with_comments(goal_slug, version)
    if payload is None:
        return JSONResponse(status_code=404, content={"detail": "Version not found"})
    return JSONResponse(content=payload)


# --------------------------------------------------------------------------- #
# Body helpers — accept JSON or form (the same-door composer posts form data)  #
# --------------------------------------------------------------------------- #

async def _read_body(request: Request) -> dict:
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            return await request.json()
        except Exception:  # noqa: BLE001 — empty/invalid JSON body
            return {}
    return dict(await request.form())


async def _read_actor(request: Request) -> ActorRequest:
    try:
        return ActorRequest(**(await _read_body(request)))
    except Exception:  # noqa: BLE001
        return ActorRequest()
