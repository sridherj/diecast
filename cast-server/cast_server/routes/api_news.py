# removed in Diecast scope-prune; see docs/scope-prune.md
"""News digest API — stubbed; see docs/scope-prune.md."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/news", tags=["news"])

_REMOVED_MSG = "removed in Diecast scope-prune; see docs/scope-prune.md"


@router.post("/generate")
async def generate_digest(*args, **kwargs):
    raise NotImplementedError(_REMOVED_MSG)


@router.get("/status")
async def digest_status(*args, **kwargs):
    raise NotImplementedError(_REMOVED_MSG)
