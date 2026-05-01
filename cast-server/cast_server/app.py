"""Diecast FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from cast_server.config import CAST_ROOT, DB_URL, DEFAULT_CAST_HOST, STATIC_DIR
from cast_server.db.connection import init_db
from cast_server.services.agent_service import recover_stale_runs, start_dispatcher

# Hosts treated as loopback for the unauthenticated-hook-endpoint warning.
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}

ALEMBIC_INI = CAST_ROOT / "cast-server" / "alembic.ini"

# bootstrap.log is owned by setup's `nohup ... >bootstrap.log 2>&1` redirect
# (captures uvicorn pre-logging stdout/stderr). This module owns server.log
# and rotates it; the two files do not share writers. — Decision #13
LOG_DIR = Path.home() / ".cache" / "diecast"
SERVER_LOG = LOG_DIR / "server.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)


_ROTATING_SENTINEL = "_cast_server_rotating"


def _attach_rotating_file_handler() -> None:
    """Attach a RotatingFileHandler for server.log to root + uvicorn loggers.

    Idempotent: safe to call from re-imports (test discovery, reload). Skips
    any logger that already has a sentinel-tagged handler, and avoids
    constructing a new RotatingFileHandler (which opens a file) when nothing
    needs attaching.
    """
    targets = ("", "uvicorn", "uvicorn.error", "uvicorn.access")
    needs_handler = [
        name for name in targets
        if not any(
            getattr(h, _ROTATING_SENTINEL, False)
            for h in logging.getLogger(name).handlers
        )
    ]
    if not needs_handler:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        SERVER_LOG,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    setattr(handler, _ROTATING_SENTINEL, True)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    ))

    for name in needs_handler:
        lg = logging.getLogger(name)
        lg.addHandler(handler)
        if not lg.level:
            lg.setLevel(logging.INFO)


_attach_rotating_file_handler()

logger = logging.getLogger(__name__)


def _ensure_db_at_head() -> None:
    """Skip-if-stamped Alembic check (Decision #15).

    Common case: alembic_version table holds the head revision → no-op
    after a single ``SELECT alembic_version``. Branches:

    1. DB file missing or empty → ``alembic upgrade head`` creates schema.
    2. Pre-Alembic DB (cast tables exist but no ``alembic_version``) →
       ``alembic stamp head`` claims the existing schema as baseline.
    3. ``alembic_version`` present at head → no-op.
    4. ``alembic_version`` present below head → ``alembic upgrade head``.

    Concurrency: two cast-server starts race only inside ``upgrade``;
    SQLite's write lock serialises them and the second sees ``current ==
    head`` once the first commits.
    """
    from alembic import command
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine, inspect

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", DB_URL)
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()

    engine = create_engine(DB_URL)
    try:
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            current = ctx.get_current_revision()
            inspector = inspect(conn)
            existing_tables = set(inspector.get_table_names())
    finally:
        engine.dispose()

    if current == head:
        return

    if current is None and existing_tables - {"alembic_version"}:
        # Pre-Alembic DB with cast schema already present — stamp it.
        command.stamp(cfg, "head")
        return

    command.upgrade(cfg, "head")


def _warn_if_non_loopback_host() -> None:
    """Warn when ``CAST_HOST`` is non-loopback — hook endpoints have no auth.

    The ``/api/agents/subagent-invocations/`` and
    ``/api/agents/user-invocations/`` POSTs are unauthenticated by design
    (Claude Code hooks fire-and-forget over loopback). Exposing cast-server
    on a public interface lets anyone forge agent_run rows.
    """
    host = (DEFAULT_CAST_HOST or "").strip().lower()
    if host and host not in _LOOPBACK_HOSTS:
        logger.warning(
            "CAST_HOST is bound to %r; hook endpoints under "
            "/api/agents/subagent-invocations/ and "
            "/api/agents/user-invocations/ are unauthenticated. "
            "Do not expose cast-server publicly.",
            host,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB, start dispatcher."""
    logger.info("Starting Diecast — initializing DB...")
    _warn_if_non_loopback_host()
    init_db()
    _ensure_db_at_head()
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
from cast_server.routes.api_health import router as api_health_router
from cast_server.routes.api_scratchpad import router as api_scratchpad_router
from cast_server.routes.api_task_suggestions import router as api_task_suggestions_router
from cast_server.routes.api_artifacts import router as api_artifacts_router
app.include_router(pages_router)
app.include_router(api_goals_router)
app.include_router(api_tasks_router)
app.include_router(api_scratchpad_router)
app.include_router(api_agents_router)
app.include_router(api_health_router)
app.include_router(api_task_suggestions_router)
app.include_router(api_artifacts_router)
