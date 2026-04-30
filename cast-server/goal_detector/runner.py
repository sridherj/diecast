"""GoalDetector runner — subprocess lifecycle management."""

import asyncio
import json
import logging
from datetime import datetime, timezone

from taskos.config import GOALS_DIR, SECOND_BRAIN_ROOT
from taskos.goal_detector.detector import (
    build_detector_prompt,
    ensure_intent_suggestions,
    parse_detector_output,
)
from taskos.services.suggestion_service import create_suggestions

logger = logging.getLogger(__name__)

# In-memory job state
_detector_job: dict | None = None


async def run_detector() -> dict:
    """Run the GoalDetector as a Claude Code subprocess.

    Returns job status dict.
    """
    global _detector_job

    if _detector_job and _detector_job["status"] == "running":
        return _detector_job

    _detector_job = {
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_count": 0,
        "error": None,
    }

    try:
        prompt, intent_lines = build_detector_prompt()

        proc = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt,
            "--output-format", "json",
            cwd=str(SECOND_BRAIN_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            _detector_job["status"] = "failed"
            _detector_job["error"] = stderr.decode()[:500]
            logger.error("GoalDetector failed: %s", _detector_job["error"])
            return _detector_job

        # Parse output
        stdout_text = stdout.decode()

        # If output-format is json, Claude wraps result
        try:
            wrapper = json.loads(stdout_text)
            if isinstance(wrapper, dict) and "result" in wrapper:
                stdout_text = wrapper["result"]
        except (json.JSONDecodeError, TypeError):
            pass

        suggestions = parse_detector_output(stdout_text)

        # Post-process: ensure regex-matched intents appear in suggestions
        if intent_lines:
            from taskos.services.goal_service import get_all_goals
            existing_slugs = [g["slug"] for g in get_all_goals()]
            suggestions = ensure_intent_suggestions(
                intent_lines, suggestions, existing_slugs,
            )

        if suggestions:
            create_suggestions(suggestions)

        _detector_job["status"] = "done"
        _detector_job["suggestions_count"] = len(suggestions)
        logger.info("GoalDetector found %d suggestions", len(suggestions))

    except Exception as e:
        _detector_job["status"] = "failed"
        _detector_job["error"] = str(e)
        logger.exception("GoalDetector crashed")

    return _detector_job


def get_detector_status() -> dict | None:
    """Get current detector job status."""
    return _detector_job
