"""Same-door change-request intake — ``POST /api/goals/{slug}/change-requests`` (Phase 5, sp2).

ONE door for proposing a requirement change. A human "suggest edit" (browser HTMX) and an
agent write-back (``curl`` JSON) hit the **identical** handler and run the SAME
``change_request_service.create`` call. ``author_type`` is the only difference, and it is
**data**, not a code branch (FR-013) — there is no second internal write path the agent lacks.

Two things the route owns that the service does not:

* **Anti-spoof identity.** The browser/human lane's ``author``/``author_type`` is **server-
  derived** — a browser client can never stamp ``author_type="human"`` with a forged ``author``.
  An agent legitimately self-declares its own name + ``author_type="agent"`` (it honestly owns
  its ``output.json``). The request *context* — not the posted body — picks the lane: an HTMX
  request (``HX-Request`` header) is the human lane; a plain JSON request is the agent lane.
* **Content negotiation.** ``HX-Request`` → an HTML fragment (the UI); otherwise JSON (agents).
  Same data, one handler — the ``api_agents.list_runs`` precedent.

Validation (slug exists; emitter-shape via the shared ``RequirementsWriteback`` model; a
``proposed_body`` size cap) lives here so the service stays a thin DB layer. The graduated-trust
lane (``applied`` vs gated ``proposed``) is ``change_request_service.gate_status`` under the
single global ``WRITEBACK_GATE_POLICY`` flag. The ``conflicted`` lane is sp3a's verdict, fed in
later via ``create(status=...)`` — intake only *records* it.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from cast_server.config import WRITEBACK_HUMAN_AUTHOR
from cast_server.deps import templates
from cast_server.models.requirements_writeback import RequirementsWriteback
from cast_server.services import change_request_service, goal_service, notification_service

router = APIRouter(prefix="/api/goals/{goal_slug}", tags=["change-requests"])

_MAX_BODY_BYTES = 64 * 1024  # cap on proposed_body (oversized → 422)


def _is_hx(request: Request) -> bool:
    return request.headers.get("hx-request", "").lower() == "true"


async def _read_body(request: Request) -> dict:
    """Parse the request body — JSON (agents) or form-encoded (browser HTMX)."""
    if request.headers.get("content-type", "").startswith("application/json"):
        return await request.json()
    return dict(await request.form())


def _resolve_identity(request: Request, posted_author: str | None) -> tuple[str, str]:
    """Pick the (author, author_type) authoritatively — the anti-spoof seam.

    * **Human lane** (HTMX/browser, ``HX-Request`` set): the server STAMPS its own derived
      identity; the posted ``author``/``author_type`` are ignored entirely. A browser can
      never forge a human author or impersonate another user.
    * **Agent lane** (plain JSON): ``author_type`` is forced to ``"agent"`` and ``author`` is
      the agent's self-declared name (which it honestly owns). The author_type can therefore
      only ever read ``"human"`` from the trusted browser context.
    """
    if _is_hx(request):
        return WRITEBACK_HUMAN_AUTHOR, "human"
    return (posted_author or "").strip(), "agent"


@router.post("/change-requests")
async def create_change_request(request: Request, goal_slug: str):
    """Intake a proposed requirement change — the FR-013 dual-assertion door.

    ONE ``change_request_service.create`` call runs regardless of caller. Routes by blast
    radius into ``applied`` (auto-applied addition + queued FYI outbox row) | ``proposed``
    (gated modification/annotation). No file is touched here (sp4 applies); no conflict is
    computed here (sp3a). Response shape negotiates on ``HX-Request``: HTML fragment | JSON 201.
    """
    if goal_service.get_goal(goal_slug) is None:
        return JSONResponse(status_code=404, content={"detail": "Goal not found"})

    raw = await _read_body(request)

    # Size cap first — reject an oversized body before model construction.
    pb = raw.get("proposed_body")
    if isinstance(pb, str) and len(pb.encode("utf-8")) > _MAX_BODY_BYTES:
        return JSONResponse(
            status_code=422,
            content={"detail": f"proposed_body exceeds {_MAX_BODY_BYTES} bytes"},
        )

    # Emitter-shape validation via the SAME model an emitter validates against (same-door at
    # the schema level): kind enum, required int base_version, non-empty proposed_body, and
    # the kind↔target_quote cross-field rule. A failure is a 422 (malformed body).
    try:
        payload = RequirementsWriteback(**raw)
    except Exception as e:  # noqa: BLE001 — pydantic ValidationError → 422
        return JSONResponse(status_code=422, content={"detail": str(e)})

    author, author_type = _resolve_identity(request, raw.get("author"))
    if not author:
        # Agent lane with no self-declared name — nothing to attribute the proposal to.
        return JSONResponse(
            status_code=422,
            content={"detail": "author is required (agent must self-declare its name)"},
        )

    status = change_request_service.gate_status(payload.kind, payload.target_quote)
    row = change_request_service.create(
        goal_slug,
        kind=payload.kind,
        proposed_body=payload.proposed_body,
        base_version=payload.base_version,
        target_quote=payload.target_quote,
        section_hint=payload.section_hint,
        author=author,
        author_type=author_type,
        origin_phase=payload.origin_phase,
        origin_activity_id=payload.origin_activity_id,
        origin_artifact_path=payload.origin_artifact_path,
        status=status,
    )

    if _is_hx(request):
        return templates.TemplateResponse(
            request, "fragments/change_requests/intake_result.html",
            {"goal_slug": goal_slug, "change_request": row},
        )
    return JSONResponse(status_code=201, content=row)


# --------------------------------------------------------------------------- #
# /inbox — the LDN-aligned agent companion to the human Goal-Card badge         #
# --------------------------------------------------------------------------- #

@router.get("/inbox")
async def get_inbox(request: Request, goal_slug: str):
    """List round-trip write-back notifications — the **same** descriptor the badge consumes.

    A watching agent reads the identical resource a human sees: ``notifications`` carries the
    round-trip / provenance items from :func:`notification_service.recent_writebacks` — the same
    shape surfaced under ``recent_writebacks`` on ``GET .../requirements/versions`` (one surface,
    not two). W3C-LDN-aligned JSON.
    """
    if goal_service.get_goal(goal_slug) is None:
        return JSONResponse(status_code=404, content={"detail": "Goal not found"})
    return JSONResponse(content={
        "notifications": notification_service.recent_writebacks(goal_slug),
    })


@router.post("/inbox")
async def post_inbox(request: Request, goal_slug: str):
    """LDN notification sink (additive, minimal in v2).

    The authoritative round-trip alerts originate from the transactional outbox (the sp2 apply
    txn + sp3b relay), so this endpoint does not create canonical state; it acknowledges an
    inbound LDN notification so the surface is LDN-shaped for watching agents. 202 Accepted.
    """
    if goal_service.get_goal(goal_slug) is None:
        return JSONResponse(status_code=404, content={"detail": "Goal not found"})
    return JSONResponse(status_code=202, content={"status": "accepted"})
