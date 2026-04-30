"""Sync API endpoint — manual trigger for re-sync."""

from fastapi import APIRouter

from cast_server.sync.engine import full_sync

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("")
async def trigger_sync():
    """Trigger a full sync. Useful after agents modify files."""
    summary = full_sync()
    return {"status": "ok", "summary": summary}
