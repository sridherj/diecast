"""Task OS configuration — paths, constants, status/phase definitions."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Directory paths
TASKOS_ROOT = Path(__file__).resolve().parent.parent.parent  # taskos/

# Load .env.local for local dev (tests load .env.test first, which takes priority)
_env_file = TASKOS_ROOT / ".env.local"
if _env_file.is_file():
    load_dotenv(_env_file)

_db_path_env = os.environ.get("TASKOS_DB_PATH")
DB_PATH = Path(_db_path_env) if _db_path_env else TASKOS_ROOT / "data" / "taskos.db"

_goals_dir_env = os.environ.get("TASKOS_GOALS_DIR")
GOALS_DIR = Path(_goals_dir_env) if _goals_dir_env else TASKOS_ROOT / "goals"

SCRATCHPAD_PATH = TASKOS_ROOT / "scratchpad.md"
SECOND_BRAIN_ROOT = TASKOS_ROOT.parent  # second-brain/
REGISTRY_PATH = SECOND_BRAIN_ROOT / "agents" / "REGISTRY.md"
DIGESTS_DIR = SECOND_BRAIN_ROOT / "docs" / "digests"

# Template and static paths
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

# Goal statuses (lifecycle — "is this worth doing?")
STATUSES = ["idea", "accepted", "inactive", "completed", "declined"]
TERMINAL_STATUSES = {"completed", "declined"}
STATUS_TRANSITIONS = {
    "idea": ["accepted", "declined"],
    "accepted": ["inactive", "completed"],
    "inactive": ["accepted"],
}

# Work phases (for accepted goals — "where am I in the work?")
PHASES = ["requirements", "exploration", "plan", "execution"]
PHASE_ARTIFACTS = {
    "requirements": ["requirements.human.md", "refined_requirements.collab.md"],
    "exploration": ["exploration/"],
    "plan": ["plan.collab.md"],
    "execution": [],
}

# Authorship tracking for goal artifacts
AUTHORSHIP_TYPES = {
    "human": {"label": "Human"},
    "ai": {"label": "AI"},
    "collab": {"label": "Collab"},
}

ARTIFACT_DEFAULTS = {
    "requirements": "human",
    "plan": "collab",
    "research": "ai",
    "playbooks": "ai",
    "summary": "ai",
    "research_notes": "human",
    "refined_requirements": "collab",
}

STARTER_TASKS = [
    {"title": "Finish brainstorming/initial requirements", "phase": "requirements",
     "tip": "Dump everything, messy is fine", "recommended_agent": None,
     "artifact": "requirements.human.md"},
    {"title": "Refine requirements writeup", "phase": "requirements",
     "tip": "AI-assisted refinement of your initial requirements",
     "recommended_agent": "taskos-refine-requirements",
     "artifact": "refined_requirements.collab.md"},
    {"title": "Run starter exploration", "phase": "exploration",
     "tip": "Deep 7-angle research on the goal", "recommended_agent": "taskos-explore"},
    {"title": "Go through starter research output", "phase": "exploration",
     "tip": "Leverage research, form your POV", "recommended_agent": None},
    {"title": "Add research notes", "phase": "exploration",
     "tip": "Dump notes from starter research + own research", "recommended_agent": None,
     "artifact": "exploration/research_notes.human.md"},
    {"title": "Finalize high level phasing plan", "phase": "plan",
     "tip": "City map — directionally right, progressively detailed", "recommended_agent": "taskos-high-level-planner"},
    {"title": "Create detailed execution plan", "phase": "plan",
     "tip": "Spec-aware planning with inline design review",
     "recommended_agent": "taskos-detailed-plan"},
]

# Dispatcher concurrency
MAX_CONCURRENT_AGENTS = int(os.environ.get("TASKOS_MAX_CONCURRENT_AGENTS", "7"))

# Agent lifecycle timeouts (all in seconds, overridable via env)
AGENT_MONITOR_INTERVAL = int(os.environ.get("TASKOS_MONITOR_INTERVAL", "5"))
AGENT_READY_TIMEOUT = int(os.environ.get("TASKOS_READY_TIMEOUT", "30"))
AGENT_IDLE_WARNING = int(os.environ.get("TASKOS_IDLE_WARNING", "600"))      # 10 min → needs_attention
AGENT_IDLE_STUCK = int(os.environ.get("TASKOS_IDLE_STUCK", "1800"))         # 30 min → stuck
AGENT_SESSION_CLEANUP_DELAY = int(os.environ.get("TASKOS_SESSION_CLEANUP_DELAY", "30"))
AGENT_SENDKEY_DELAY = float(os.environ.get("TASKOS_SENDKEY_DELAY", "5"))  # pause between paste + enter (>1s to let paste mode expire)

# Off-peak scheduling (hour in local time, 0 = midnight)
OFF_PEAK_HOUR = 0

# Origins
ORIGINS = {"manual", "goal-detector"}

# Task types
TASK_TYPES = {"Decision", "Research", "Execution", "Exploration", "Coding", "Learning"}

# Energy levels
ENERGY_LEVELS = {"High", "Medium", "Low"}

# Assignees
ASSIGNEES = {"SJ", "Claude", "SJ + Claude"}
