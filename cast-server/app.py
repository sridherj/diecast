"""Task OS FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from taskos.config import STATIC_DIR
from taskos.db.connection import init_db
from taskos.services.agent_service import recover_stale_runs, start_dispatcher
from taskos.sync.engine import full_sync, incremental_sync

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run full sync on startup, start dispatcher."""
    logger.info("Starting Task OS — initializing DB...")
    init_db()
    logger.info("DB initialized")
    logger.info("Running full sync...")
    try:
        summary = full_sync()
        logger.info("Sync complete: %s", summary)
    except Exception:
        logger.exception("Initial sync failed — starting with empty DB")
    try:
        recovered = recover_stale_runs()
        if recovered:
            logger.info("Recovered %d stale agent run(s)", len(recovered))
    except Exception:
        logger.exception("Agent run recovery failed")

    # Start dispatcher background task
    dispatcher_task = asyncio.create_task(start_dispatcher())
    logger.info("Dispatcher background task created")

    yield

    # Cancel dispatcher on shutdown
    dispatcher_task.cancel()
    try:
        await dispatcher_task
    except asyncio.CancelledError:
        logger.info("Dispatcher stopped")


app = FastAPI(title="Task OS", lifespan=lifespan)


@app.middleware("http")
async def sync_middleware(request: Request, call_next):
    """Run incremental sync on each request (debounced to 30s)."""
    # Skip sync for static files
    if not request.url.path.startswith("/static"):
        try:
            incremental_sync()
        except Exception:
            logger.exception("Incremental sync failed")
    response = await call_next(request)
    return response


# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register routers
from taskos.routes.pages import router as pages_router
from taskos.routes.api_goals import router as api_goals_router
from taskos.routes.api_tasks import router as api_tasks_router
from taskos.routes.api_agents import router as api_agents_router
from taskos.routes.api_scratchpad import router as api_scratchpad_router
from taskos.routes.api_sync import router as api_sync_router
from taskos.routes.api_task_suggestions import router as api_task_suggestions_router
from taskos.routes.api_artifacts import router as api_artifacts_router
from taskos.routes.api_news import router as api_news_router
app.include_router(pages_router)
app.include_router(api_goals_router)
app.include_router(api_tasks_router)
app.include_router(api_scratchpad_router)
app.include_router(api_agents_router)
app.include_router(api_sync_router)
app.include_router(api_task_suggestions_router)
app.include_router(api_artifacts_router)
app.include_router(api_news_router)
