"""Diecast FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cast_server.config import STATIC_DIR
from cast_server.db.connection import init_db
from cast_server.services.agent_service import recover_stale_runs, start_dispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB, start dispatcher."""
    logger.info("Starting Diecast — initializing DB...")
    init_db()
    logger.info("DB initialized")
    try:
        recovered = recover_stale_runs()
        if recovered:
            logger.info("Recovered %d stale agent run(s)", len(recovered))
    except Exception:
        logger.exception("Agent run recovery failed")

    dispatcher_task = asyncio.create_task(start_dispatcher())
    logger.info("Dispatcher background task created")

    yield

    dispatcher_task.cancel()
    try:
        await dispatcher_task
    except asyncio.CancelledError:
        logger.info("Dispatcher stopped")


app = FastAPI(title="Diecast", lifespan=lifespan)


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

from cast_server.routes.pages import router as pages_router
from cast_server.routes.api_goals import router as api_goals_router
from cast_server.routes.api_tasks import router as api_tasks_router
from cast_server.routes.api_agents import router as api_agents_router
from cast_server.routes.api_scratchpad import router as api_scratchpad_router
from cast_server.routes.api_sync import router as api_sync_router
from cast_server.routes.api_task_suggestions import router as api_task_suggestions_router
from cast_server.routes.api_artifacts import router as api_artifacts_router
app.include_router(pages_router)
app.include_router(api_goals_router)
app.include_router(api_tasks_router)
app.include_router(api_scratchpad_router)
app.include_router(api_agents_router)
app.include_router(api_sync_router)
app.include_router(api_task_suggestions_router)
app.include_router(api_artifacts_router)
