"""Scratchpad API endpoints — HTMX fragment responses."""

import logging

from fastapi import APIRouter, Request, Form

from taskos.deps import templates
from taskos.services.scratchpad_service import add_entry, get_recent_entries
from taskos.utils.responses import toast_header

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scratchpad", tags=["scratchpad"])


@router.get("")
async def list_entries(request: Request, limit: int = 20):
    """Get scratchpad entries."""
    entries = get_recent_entries(limit)
    return templates.TemplateResponse(request, "fragments/scratchpad_entry.html", {
        "entries": entries,
    })


@router.post("")
async def create_entry(request: Request, content: str = Form(...)):
    """Add a scratchpad entry. Returns entry fragment."""
    entry = add_entry(content)
    logger.info("Scratchpad entry added: '%s'", content[:50])
    response = templates.TemplateResponse(request, "fragments/scratchpad_entry.html", {
        "entry": entry,
    })
    response.headers["HX-Trigger"] = toast_header("Entry added")
    return response
