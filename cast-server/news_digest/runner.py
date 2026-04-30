"""News digest runner — tmux-based terminal lifecycle management."""

import asyncio
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from taskos.config import SECOND_BRAIN_ROOT, DIGESTS_DIR
from taskos.infra.tmux_manager import TmuxSessionManager, TmuxError

logger = logging.getLogger(__name__)

# In-memory job state (singleton — only one digest generation at a time)
_job: dict | None = None


async def run_digest_generator() -> dict:
    """Launch digest generation in a tmux session.

    Returns job dict with id, status.
    If already running, returns existing job (concurrent generation blocked).
    """
    global _job
    if _job and _job.get("status") == "running":
        return _job

    job_id = str(uuid4())[:8]
    done_file = DIGESTS_DIR / f".digest-{job_id}.done"
    exitcode_file = DIGESTS_DIR / f".digest-{job_id}.exitcode"

    prompt = (
        "Use the taskos-generate-news-digest agent. "
        "Generate a news digest for today."
    )
    prompt_file = DIGESTS_DIR / f".digest-prompt-{job_id}.txt"
    prompt_file.write_text(prompt)

    session_name = f"digest-{job_id}"
    cmd = "claude --dangerously-skip-permissions --model sonnet"

    try:
        tmux = TmuxSessionManager()
        tmux.create_session(session_name, cmd, str(SECOND_BRAIN_ROOT))

        if not tmux.wait_for_ready(session_name, timeout_seconds=30):
            tmux.kill_session(session_name)
            _job = {
                "id": job_id,
                "status": "error",
                "error": "Claude did not become ready within 30s",
            }
            return _job

        # Deliver prompt via file (prompt may be large with context)
        delivery = f"Read the file {prompt_file} and follow its instructions exactly."
        tmux.send_keys(session_name, delivery)
        time.sleep(0.3)
        tmux.send_enter(session_name)

    except TmuxError as e:
        _job = {
            "id": job_id,
            "status": "error",
            "error": f"tmux session creation failed: {e}",
        }
        return _job

    _job = {
        "id": job_id,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "done_file": str(done_file),
        "exitcode_file": str(exitcode_file),
        "prompt_file": str(prompt_file),
        "session_name": session_name,
        "error": None,
    }

    asyncio.create_task(_poll_completion())
    return _job


async def _poll_completion():
    """Poll for .done file and update job status."""
    global _job
    if not _job:
        return

    done_file = Path(_job["done_file"])
    exitcode_file = Path(_job["exitcode_file"])
    prompt_file = Path(_job["prompt_file"])
    session_name = _job.get("session_name")

    while not done_file.exists():
        await asyncio.sleep(2)

    try:
        exitcode = int(exitcode_file.read_text().strip()) if exitcode_file.exists() else 1

        if exitcode != 0:
            _job["status"] = "error"
            _job["error"] = f"Agent exited with code {exitcode}"
        else:
            _job["status"] = "completed"
    except Exception as e:
        logger.exception("Digest generation status check failed")
        _job["status"] = "error"
        _job["error"] = str(e)
    finally:
        for f in [done_file, exitcode_file, prompt_file]:
            Path(f).unlink(missing_ok=True)
        # Clean up tmux session
        if session_name:
            try:
                tmux = TmuxSessionManager()
                tmux.kill_session(session_name)
            except TmuxError:
                pass

    logger.info("Digest job %s finished: %s", _job["id"], _job["status"])


def get_digest_status() -> dict | None:
    """Get current digest generation job status."""
    return _job
