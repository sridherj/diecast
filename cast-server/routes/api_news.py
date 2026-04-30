"""News Digest API endpoints — HTMX fragment responses."""

import logging

from fastapi import APIRouter, Request

from taskos.deps import templates
from taskos.news_digest.runner import run_digest_generator, get_digest_status
from taskos.utils.responses import toast_header

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["news"])


@router.post("/generate")
async def generate_digest(request: Request):
    """Trigger digest generation. Returns news_status.html fragment with polling."""
    job = await run_digest_generator()
    return templates.TemplateResponse(request, "fragments/news_status.html", {
        "job": job,
    })


@router.get("/status")
async def digest_status(request: Request):
    """Poll digest generation status. Returns news_status.html fragment.

    Polling stops automatically when status is completed or error (no hx-trigger).
    """
    job = get_digest_status()

    if job and job["status"] == "completed":
        response = templates.TemplateResponse(request, "fragments/news_status.html", {
            "job": job,
        })
        response.headers["HX-Trigger"] = toast_header("News digest generated")
        return response

    if job and job["status"] == "error":
        response = templates.TemplateResponse(request, "fragments/news_status.html", {
            "job": job,
        })
        response.headers["HX-Trigger"] = toast_header(
            job.get("error", "Digest generation failed"), "error"
        )
        return response

    return templates.TemplateResponse(request, "fragments/news_status.html", {
        "job": job or {"status": "idle"},
    })
