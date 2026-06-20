"""Diecast configuration — paths, constants, status/phase definitions."""

import getpass
import os
from pathlib import Path

from dotenv import load_dotenv

# Directory paths
CAST_ROOT = Path(__file__).resolve().parent.parent.parent  # cast/

# Load .env.local for local dev (tests load .env.test first, which takes priority)
_env_file = CAST_ROOT / ".env.local"
if _env_file.is_file():
    load_dotenv(_env_file)

DEFAULT_DB_PATH = Path.home() / ".cast" / "diecast.db"


def _resolve_db_path() -> Path:
    override = os.environ.get("CAST_DB")
    if override:
        path = Path(override).expanduser()
    else:
        path = DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


DB_PATH = _resolve_db_path()
DB_URL = os.environ.get("DIECAST_DB_URL") or f"sqlite:///{DB_PATH}"

_goals_dir_env = os.environ.get("CAST_GOALS_DIR")
GOALS_DIR = Path(_goals_dir_env) if _goals_dir_env else CAST_ROOT / "goals"

SCRATCHPAD_PATH = CAST_ROOT / "scratchpad.md"
DIECAST_ROOT = CAST_ROOT  # repo root, e.g. /data/workspace/diecast

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
    "requirements": ["requirements.human.md", "refined_requirements.collab.md",
                     "refined_requirements.html"],
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
     "recommended_agent": "cast-refine-requirements",
     "artifact": "refined_requirements.collab.md"},
    {"title": "Run starter exploration", "phase": "exploration",
     "tip": "Deep 7-angle research on the goal", "recommended_agent": "cast-explore-workflow"},
    {"title": "Go through starter research output", "phase": "exploration",
     "tip": "Leverage research, form your POV", "recommended_agent": None},
    {"title": "Add research notes", "phase": "exploration",
     "tip": "Dump notes from starter research + own research", "recommended_agent": None,
     "artifact": "exploration/research_notes.human.md"},
    {"title": "Finalize high level phasing plan", "phase": "plan",
     "tip": "City map — directionally right, progressively detailed", "recommended_agent": "cast-high-level-planner"},
    {"title": "Create detailed execution plan", "phase": "plan",
     "tip": "Spec-aware planning with inline design review",
     "recommended_agent": "cast-fanout-detailed-plan"},
]

# Workflow routing registry (Phase 3b). Keys are WorkFamily string values —
# one vocabulary, two homes; kept as strings so config.py stays the
# dependency-free bottom layer (no requirements_render import). A pin test
# asserts key-set equality with families.WorkFamily.
WORKFLOW_REGISTRY: dict[str, dict] = {
    "new_initiative":     {"status": "stub", "steps": ["PRD", "architecture", "phased plan", "execute"]},
    "pilot_poc":          {"status": "stub", "steps": ["one-screen WHAT", "spike", "demo", "learnings"]},
    "bug_fix":            {"status": "stub", "steps": ["logs", "RCA", "confirm", "fix/test"]},
    "data_analysis":      {"status": "stub", "steps": ["question", "sources", "analysis", "writeup"]},
    "random_idea":        {"status": "stub", "steps": ["capture", "incubate", "promote-or-archive"]},
    "testing_qa":         {"status": "stub", "steps": ["inventory", "coverage gaps", "test plan", "implement"]},
    "refactor_migration": {"status": "stub", "steps": ["map current", "target design", "migration steps", "verify parity"]},
    "personal_non_eng":   {"status": "stub", "steps": ["clarify outcome", "plan", "do", "reflect"]},
    "generic":            {"status": "stub", "steps": ["refine", "explore", "plan", "execute"]},
}
WORKFLOW_FAMILIES = frozenset(WORKFLOW_REGISTRY)   # the closed set, derived — cannot drift from the map

# Phase 5 round-trip write-back (refine-requirements-v2). Lives beside WORKFLOW_REGISTRY /
# STARTER_TASKS / PHASES as a peer config constant.
#
# Graduated-trust gate policy (owner decision #3). A SINGLE global flag — NOT per-element —
# so the trust level can loosen later without a code change. The intake router
# (`change_request_service.gate_status`) decides a proposal's status by blast radius under
# this policy:
#   "gate-except-additions" (v2 default) → pure additions auto-apply; modifications/
#                                          annotations are gated (land as 'proposed').
#   "gate-all"  → everything gated ('proposed');  "gate-none" → everything auto-applies.
# refine-requirements-v3 (owner decision, 2026-06-12): the goal's global writeback policy is
# GATE-ALL — every change-request (gap-fill additions included) awaits explicit human approval
# before touching canonical. Additions are NOT fast-tracked. The gate mechanism
# (`change_request_service.gate_status` / the policy lanes / the conflict predicate / the
# writeback agent / outbox / relay) is consumed UNCHANGED; ONLY this value changes. Global by
# design — a per-origin policy would change the gate, which the goal's HOLD scope forbids.
WRITEBACK_GATE_POLICY = os.environ.get("CAST_WRITEBACK_GATE_POLICY", "gate-all")


def _derive_human_author() -> str:
    """Server-derived human identity for the write-back intake's human lane (anti-spoof).

    A browser client can NEVER set ``author``/``author_type`` from the posted body — the
    server stamps THIS identity for every human-lane proposal. Agents self-declare their own
    name + ``author_type="agent"`` (they honestly own their ``output.json``). Overridable via
    ``CAST_HUMAN_AUTHOR``; falls back to the OS login name, then a literal so it never raises.
    """
    override = os.environ.get("CAST_HUMAN_AUTHOR")
    if override:
        return override
    try:
        return getpass.getuser()
    except Exception:
        return "human"


WRITEBACK_HUMAN_AUTHOR = _derive_human_author()

# Cast-server bind/connect defaults — single source of truth.
# CAST_HOST: client-side connect target (skills, agents, server-emitted callback URLs).
# CAST_BIND_HOST: server-side uvicorn bind. Env-var-only; intentionally NOT in config.yaml.
# CAST_PORT: shared by both sides.
DEFAULT_CAST_PORT = int(os.environ.get("CAST_PORT", "8005"))
DEFAULT_CAST_HOST = os.environ.get("CAST_HOST", "localhost")
DEFAULT_CAST_BIND_HOST = os.environ.get("CAST_BIND_HOST", "127.0.0.1")

# Dispatcher concurrency
MAX_CONCURRENT_AGENTS = int(os.environ.get("CAST_MAX_CONCURRENT_AGENTS", "7"))

# --- Background maker render-job pipeline (refine-requirements-v3 Phase 3c) ---
# The WHAT→HOW maker runs as a background job; its working artifacts (what.md, attempt-N.html,
# gate reports) live under build/render-jobs/{slug}/{hash12}/ — `build/` is a non-goal,
# non-CI-collected runtime area, NEVER inside goals/{slug}/ (keeps the FR-026 folder invariant
# intact). The published refined_requirements.html still lands in the goal dir as today.
RENDER_JOBS_DIR = Path(
    os.environ.get("CAST_RENDER_JOBS_DIR") or (CAST_ROOT / "build" / "render-jobs")
)

# Per-stage worst-case timeouts (seconds), in pipeline order. The reaper ceiling is a FUNCTION
# of THIS list (revision a) — never a magic constant and never a hardcoded
# what_timeout + how_timeout formula. 4a/5 extend the pipeline by registering their stages here
# (run_checker / gap stages), and the ceiling formula picks them up with zero edits.
# `run_what` / `run_how` mirror the agents' config.yaml `timeout_minutes` (15 / 30) so the
# in-memory subprocess timeout and the reaper ceiling cannot silently drift apart. (config.py is
# the dependency-free bottom layer — it must not import the agent-config loader, which imports
# config.py — so the mirror is documented here rather than read at import time.)
RENDER_STAGE_TIMEOUTS: list[tuple[str, int]] = [
    ("run_what", int(os.environ.get("CAST_RENDER_WHAT_TIMEOUT_S", str(15 * 60)))),
    ("gate_what", int(os.environ.get("CAST_RENDER_GATE_WHAT_TIMEOUT_S", "5"))),
    # 5a: the gap-fill upstream-ask stages. Registering them here is the WHOLE reaper edit for
    # Phase 5 (same revision-a discipline as run_checker) — the ceiling formula reads this list, so
    # adding the stages extends the ceiling with no formula change (5d drift sweep verifies this).
    # `ask_what` is the bounded HOW-asks-WHAT re-run (mirrors run_what's 15-min budget); `run_gapfill`
    # mirrors `cast-requirements-gapfill`'s config.yaml `timeout_minutes` (15) so the subprocess
    # timeout and the reaper ceiling cannot drift; `validate_evidence` / `emit_change_requests` are
    # deterministic service-side steps (seconds). These run ONCE per job, before the 4a quality loop.
    ("ask_what", int(os.environ.get("CAST_RENDER_ASK_WHAT_TIMEOUT_S", str(15 * 60)))),
    ("run_gapfill", int(os.environ.get("CAST_RENDER_GAPFILL_TIMEOUT_S", str(15 * 60)))),
    ("validate_evidence", int(os.environ.get("CAST_RENDER_VALIDATE_EVIDENCE_TIMEOUT_S", "5"))),
    ("emit_change_requests", int(os.environ.get("CAST_RENDER_EMIT_CR_TIMEOUT_S", "5"))),
    ("run_how", int(os.environ.get("CAST_RENDER_HOW_TIMEOUT_S", str(30 * 60)))),
    ("gate_html", int(os.environ.get("CAST_RENDER_GATE_HTML_TIMEOUT_S", "5"))),
    # 4a-2: the LLM quality checker stage. Registering it here is the WHOLE reaper edit (revision a)
    # — the ceiling formula reads this list, so adding the stage extends the ceiling with no formula
    # change. The timeout mirrors `cast-requirements-render-checker`'s config.yaml `timeout_minutes`
    # (15) so the in-memory subprocess timeout and the reaper ceiling cannot silently drift apart.
    ("run_checker", int(os.environ.get("CAST_RENDER_CHECKER_TIMEOUT_S", str(15 * 60)))),
    ("decide_quality", int(os.environ.get("CAST_RENDER_DECIDE_TIMEOUT_S", "5"))),
    ("publish", int(os.environ.get("CAST_RENDER_PUBLISH_TIMEOUT_S", "10"))),
]
# Generous (≥2×) multiple of the registered stage-timeout sum (plus a one-stage structural-retry
# allowance) that bounds how long a `running` render_jobs row may go without a heartbeat before
# the lazy reaper declares it orphaned. Reads the stage list above — see render_job_service.
RENDER_REAPER_CEILING_MULTIPLE = int(os.environ.get("CAST_RENDER_REAPER_MULTIPLE", "2"))
# Global in-flight ceiling: a bounded semaphore over distinct (slug, source_hash) jobs caps how
# many maker subprocess pipelines run at once. Past the ceiling a new view serves the generating
# state and the job waits for a slot. This is a RESOURCE-SAFETY guard (analogous to the
# anti-infinite-loop ceiling), NOT a cost/latency constraint — cost and model tier are explicitly
# unconstrained for the maker.
RENDER_MAX_INFLIGHT = int(os.environ.get("CAST_RENDER_MAX_INFLIGHT", "3"))

# --- Two-mode HOW: CREATE vs UPDATE plumbing (refine-requirements-v3 HOW-update-mode, Sub-phase 3a) ---
# A render job deterministically decides CREATE vs UPDATE at job start (`render_job_service.decide_mode`).
# UPDATE re-renders only the changed blocks against a recovered prior render; CREATE renders the page
# fresh. These two knobs are the UPDATE preconditions that bound when an UPDATE is even attempted — both
# env-overridable on the RENDER_* convention, both recorded as tune-after-first-runs knobs, NOT
# researched constants.
#   * RENDER_UPDATE_MAX_CHANGED_FRACTION — past this fraction of changed blocks the edit is "massive"
#     and UPDATE flips back to CREATE (re-rendering most of the page fresh is cleaner than splicing it).
#     0.4 is a STARTING value (Step 3a.1) — tune after the first real runs.
#   * RENDER_UPDATE_MAX_PRIOR_BYTES — bounds the TOTAL prior-render bytes inlined into the UPDATE
#     context (plan-review Decision #6). A prior page near the context budget can silently truncate,
#     dropping tail unchanged containers → a fidelity flag on an edit that touched none of them; a fresh
#     CREATE never needs the prior page in context. The default (~600 KB) sits comfortably under the
#     model context budget even with the WHAT doc + source + changed fragments alongside it — a tune knob.
RENDER_UPDATE_MAX_CHANGED_FRACTION = float(
    os.environ.get("CAST_RENDER_UPDATE_MAX_CHANGED_FRACTION", "0.4")
)
RENDER_UPDATE_MAX_PRIOR_BYTES = int(
    os.environ.get("CAST_RENDER_UPDATE_MAX_PRIOR_BYTES", str(600_000))
)
# The inert flag-gate (Sub-phase 3a). The whole two-mode path — mode decision, prior-render recovery,
# changed-set assembly, the `mode` row stamp — is BUILT and exercised here, but production stays 100%
# CREATE: even when `decide_mode` returns 'update', the pipeline renders via CREATE while this flag is
# off. Sub-phase 3b flips the default to wire UPDATE live. Detection + assembly still run + log so the
# inert path is observable (the changed-set + `mode=update` land in the job dir / render_jobs row).
RENDER_UPDATE_ENABLED = os.environ.get("CAST_RENDER_UPDATE_ENABLED", "").strip().lower() in {
    "1", "true", "yes", "on",
}

# --- Quality-driven rework loop (refine-requirements-v3 Phase 4a-2) ---
# On the happy path no maker render reaches a reader unless `cast-requirements-render-checker`
# (ONE agent grading comprehension AND visual quality) passes it. The checker drives a quality
# rework loop inside render_job_service, inserted between `gate_html` and `publish`. These knobs
# bound that loop. CRITICAL (owner decision, binding): the loop is rationed ONLY by the high
# anti-infinite-loop ceiling — NEVER by cost, latency, or model tier. The Phase-3 in-flight
# semaphore (RENDER_MAX_INFLIGHT) stays the only resource guard. Disjoint from the RENDER_* keys
# (Phase 3) and the GAPFILL_* keys (Phase 5).
#
# QUALITY_MAX_ATTEMPTS: deliberately HIGH — the anti-infinite-loop guard ONLY, not a cost cap.
# QUALITY_MAX_WHAT_REWORKS: forced `run_what` re-runs per job when a comprehension miss is shown to
#   be intent-level (the same gated `missing[]` token recurs), not representation-level.
# QUALITY_STRUCTURAL_STOP: consecutive structural-gate failures after which the loop stops early —
#   continuing to rework a structurally-degraded maker just burns the ceiling for nothing; serve the
#   best attempt + flag instead (preferring a structurally-valid attempt).
QUALITY_MAX_ATTEMPTS = int(os.environ.get("CAST_QUALITY_MAX_ATTEMPTS", "15"))
QUALITY_MAX_WHAT_REWORKS = int(os.environ.get("CAST_QUALITY_MAX_WHAT_REWORKS", "2"))
QUALITY_STRUCTURAL_STOP = int(os.environ.get("CAST_QUALITY_STRUCTURAL_STOP", "3"))

# --- Gap-fill upstream-ask loop (refine-requirements-v3 Phase 5a) ---
# Gap stages run ONCE per job, BEFORE the 4a quality loop (the gap set is a property of the source,
# not a rendering attempt). These counters are INDEPENDENT of the QUALITY_* loop knobs:
#   * GAPFILL_ASK_ROUNDS bounds the pre-loop HOW-asks-WHAT re-run; it does NOT debit
#     QUALITY_MAX_WHAT_REWORKS (Plan Review A2).
#   * The pre-loop trailer-harvest run_how does NOT debit QUALITY_MAX_ATTEMPTS (Plan Review C6).
# GAPFILL_MAX_GAPS caps WHAT-declared gaps per doc — a page is communication, not an audit.
GAPFILL_MAX_GAPS = int(os.environ.get("CAST_GAPFILL_MAX_GAPS", "5"))
GAPFILL_ASK_ROUNDS = int(os.environ.get("CAST_GAPFILL_ASK_ROUNDS", "1"))

# Agent lifecycle timeouts (all in seconds, overridable via env)
AGENT_MONITOR_INTERVAL = int(os.environ.get("CAST_MONITOR_INTERVAL", "5"))
AGENT_READY_TIMEOUT = int(os.environ.get("CAST_READY_TIMEOUT", "30"))
AGENT_IDLE_WARNING = int(os.environ.get("CAST_IDLE_WARNING", "600"))      # 10 min → needs_attention
AGENT_IDLE_STUCK = int(os.environ.get("CAST_IDLE_STUCK", "1800"))         # 30 min → stuck
AGENT_SESSION_CLEANUP_DELAY = int(os.environ.get("CAST_SESSION_CLEANUP_DELAY", "30"))
AGENT_SENDKEY_DELAY = float(os.environ.get("CAST_SENDKEY_DELAY", "5"))  # pause between paste + enter (>1s to let paste mode expire)

# Off-peak scheduling (hour in local time, 0 = midnight)
OFF_PEAK_HOUR = 0

# Origins
ORIGINS = {"manual", "goal-detector"}

# Task types
TASK_TYPES = {"Decision", "Research", "Execution", "Exploration", "Coding", "Learning"}

# Energy levels
ENERGY_LEVELS = {"High", "Medium", "Low"}

# Assignees
ASSIGNEES = {"User", "Claude", "User + Claude"}
