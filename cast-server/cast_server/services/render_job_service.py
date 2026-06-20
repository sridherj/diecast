"""Background maker render-job pipeline (refine-requirements-v3 Phase 3c).

`GET /goals/{slug}/render` is now served, on the happy path, by a **two-agent maker pipeline**
run as a **background job**: `cast-requirements-what` emits a machine-checkable WHAT doc and
`cast-requirements-how` turns it into a self-contained bespoke HTML page. This module owns that
job — the single-flight registry, the per-job daemon thread, the in-flight semaphore, the lazy
reaper, the named pipeline stages, and the two terminal degradation branches. The deterministic
`requirements_render_service.render_requirements()` substrate is demoted to the **fallback branch**,
served **only on a literal no-output failure**.

Both agents are tool-free `claude -p` subprocesses (the `eval_render_checker.py` / `agent_service`
`/context` invocation pattern), NOT the tmux HTTP dispatcher (a page view must never pop a visible
terminal). `--tools ""` makes "the maker never writes the canonical `.collab.md`" **structural**,
not behavioural (FR-007).

The named stage seam (4a-2 inserted `run_checker → decide_quality` between `gate_html` and
`publish`; 5a inserted the gap machinery between `gate_what` and the loop's FINAL `run_how`) is:

    run_what → gate_what
      → [5a, once per job] run_how(probe) → ask_what → run_gapfill → validate_evidence
                                          → emit_change_requests(gaps-state.json + gap CRs via the v2 gate)
      → run_how → gate_html → run_checker → decide_quality → publish
        └──────── the HOW quality rework loop (against a FIXED WHAT doc + gap state) ────────┘

The gap stages run ONCE per job (the gap set is a property of the source, not a rendering attempt);
the probe `run_how` does NOT debit `QUALITY_MAX_ATTEMPTS` (C6) and `ask_what` does NOT debit
`QUALITY_MAX_WHAT_REWORKS` (A2) — they are pre-loop gap machinery, on counters of their own.

`cast-requirements-render-checker` (ONE agent grading comprehension AND visual quality in a single
pass) scores every extractable attempt; `decide_quality` drives the rework loop and lands the
terminal state. The loop is rationed ONLY by a HIGH anti-infinite-loop ceiling (`QUALITY_*` knobs) —
NEVER by cost, latency, or model tier (owner decision, binding). The Phase-3 in-flight semaphore
stays the only resource guard. The structural gate (`gate_html`, widened by 4b-1's comment-survival
merge) owns fidelity to the source; the LLM checker owns the reader's experience — it judges only
the rendered artifact + family label (zero-click view first), never the canonical source or the
WHAT doc, so the cold-reader property is guaranteed by construction (it is tool-free).

Terminal states (the **OWNER OVERRIDE**, decisions-so-far.md lines 104/107, 2026-06-12 — supersedes
the source plan's RATIFIED structural-fallback fork):

- **Clean publish.** An attempt that passes BOTH structural gates AND the checker → `published`,
  no flag, `served-by: maker`.
- **Flagged best-attempt** (any non-clean terminal where ≥1 attempt was extracted). Serve the best
  attempt **flagged** (`human_review=1` + a `review_reason`), the artifact stamped with the flag.
  Best-attempt ranking is **PREFER VALID, THEN SCORE**: a structurally-valid attempt always
  outranks a broken one regardless of score (`served-by: maker`, `review_reason` ∈
  {`non_convergent`, `checker_unavailable`, `structural_degradation`}); only when **zero** valid
  attempts exist is a structurally-broken attempt served (`served-by: structural_violation`,
  `review_reason='structural_violation'`). The deterministic page is **NEVER** served when any
  attempt exists — surfacing the degraded render beats silently swapping it (surface, don't suppress).
- **Literal no-output → deterministic fallback.** Crash, timeout, or nothing extractable across ALL
  attempts → the v2 deterministic page, `status=fallback`. This is the ONLY fallback trigger and is
  never LLM-gated. (The source plan's "zero structurally-valid attempts → deterministic" row is
  DELETED by the override.)

Readiness is **never** derived from `render_jobs` — the published artifact's embedded `source-hash`
is the single source of truth. The table is the observability / status / failure-reason surface and
the seam where 4a records its richer human-review flag.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path

import yaml

import cast_server.config as config
from cast_server.config import GOALS_DIR
from cast_server.db.connection import get_connection
# Shared render core (exploration-pipeline-nxm sub-phase 4, Decision 2A): the runner seam, the
# sentinel contract, the concurrency mechanism, and the quality-loop skeleton live in render_common
# now (ONE copy, shared with the exploration render-job). Imported under the names this module's
# existing callers + tests expect (`extract_render`, `AgentRunner`, `JobState`, `_acquire_slot`, …).
from cast_server.render_common.agent_runner import (
    AgentRunError,
    AgentRunner,
    ProductionAgentRunner,
    _clean_child_env,
    _load_agent_md,
)
from cast_server.render_common.job_runtime import JobRegistry
from cast_server.render_common.job_runtime import age_seconds as _age_seconds
from cast_server.render_common.job_runtime import get_job_row, latest_job_row
from cast_server.render_common.job_runtime import insert_job as _insert_job
from cast_server.render_common.job_runtime import update_job as _update_job
from cast_server.render_common.job_runtime import utcnow as _utcnow
from cast_server.render_common.job_runtime import utcnow_iso as _utcnow_iso
from cast_server.render_common.quality_loop import AttemptRecord, FeedbackItem
from cast_server.render_common.quality_loop import best_attempt as _best_attempt
from cast_server.render_common.quality_loop import decide_quality as _decide_quality
from cast_server.render_common.quality_loop import run_quality_loop as _run_quality_loop
from cast_server.render_common.sentinel import _BEGIN_SENTINEL, _END_SENTINEL, extract_render
from cast_server.requirements_render import (
    ParsedRequirements,
    is_stub,
    parse_requirements,
    parse_requirements_file,
)
# HOW-update-mode 3a: the deterministic changed-set the UPDATE mode decision consumes. `block_diff`
# is the single deterministic diff engine (FR-024 extend-never-fork) — `diff_blocks` / `summarize`
# / `_key` are CONSUMED unchanged here, never edited or re-implemented.
from cast_server.requirements_render import block_diff
# HOW-update-mode 3b: the deterministic UPDATE splice (server keeps unchanged unit-container bytes
# verbatim + splices HOW changed-block fragments — 1a verdict FAIL → deterministic-splice).
from cast_server.requirements_render import block_splice
from cast_server.requirements_render.checker_verdict import (
    CHECKER_CONTRACT,
    GATED_TOKENS,
    CheckerVerdict,
    CheckerVerdictError,
    canonical_score,
    derive_pass,
    parse_verdict,
)
from cast_server.requirements_render.hashing import content_hash
from cast_server.requirements_render.maker_gate import (
    GateReport,
    _label_in,
    _norm_ref,
    check_comment_survival,
    check_gaps_state,
    check_html,
    check_update_fidelity,
    check_what_doc,
    container_text_index,
)
from cast_server.requirements_render.zero_click import extract_zero_click_view
from cast_server.services import (
    change_request_service,
    comment_service,
    requirement_version_service,
    requirements_render_service,
)
# Single-helper discipline (shared context Cross-Phase Hard Edges): the 5a evidence trust boundary
# REUSES the one `verbatim_locate` — it never adds a second locate. change_request_service is
# otherwise consumed unchanged (no intake/gate/apply edits): 5b calls only its public `create(...)`
# (the governed write path) + reads its `verbatim_locate` locator — never re-implements intake.
from cast_server.services.change_request_service import verbatim_locate

logger = logging.getLogger(__name__)

# The strict sentinel pair (`_BEGIN_SENTINEL` / `_END_SENTINEL`) + `extract_render` now live in
# `render_common.sentinel` (imported above) — the HOW contract is identical for both render-jobs.

_WHAT_AGENT = "cast-requirements-what"
_HOW_AGENT = "cast-requirements-how"
_CHECKER_AGENT = "cast-requirements-render-checker"
_GAPFILL_AGENT = "cast-requirements-gapfill"
# HOW-update-mode 3b: the publish-boundary re-anchor subagent (contract v3 — render-space hints).
# Dispatched ONCE after an UPDATE publish to relocate/resolve/orphan comments on CHANGED blocks
# (the expected survival misses), extending 4b's version-boundary dispatch to the render boundary.
_REANCHOR_AGENT = "cast-comment-reanchor"

# The HOW `GAPS-DETECTED` trailer lives OUTSIDE the render sentinels (after the first END), so
# `extract_render` is byte-untouched. The probe harvests it via `_parse_gaps_trailer`.
_GAPS_TRAILER_BEGIN = "<!-- GAPS-DETECTED"
# `cast-requirements-gapfill` emits one YAML list (one entry per gap) between these sentinels.
_GAPFILL_BEGIN = "<!-- BEGIN GAPFILL -->"
_GAPFILL_END = "<!-- END GAPFILL -->"
# The grounding corpus allowlist (5a): the goal's OWN upstream artifacts only — the wider repo is
# NEVER a requirements source. Resolved inside the goal's own tree (path-validated).
_CORPUS_FILES = ("requirements.human.md", "research_notes.human.md", "exploration/summary.md")
# Whitespace/smart-quote tolerance for the evidence locate (T2 parity) — folded into BOTH the
# corpus text and the quote before the SHARED `verbatim_locate` runs (no second locate).
_SMART_QUOTE_FOLD = {
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "–": "-", "—": "-", " ": " ",
}

_NO_OUTPUT_FEEDBACK = (
    "Your previous output did not contain a single well-formed render. Emit EXACTLY ONE "
    f"`{_BEGIN_SENTINEL}` … `{_END_SENTINEL}` block wrapping a complete self-contained HTML "
    "document, with no markdown fences or chatty preamble around it."
)


# `FeedbackItem` / `AttemptRecord` + the `AgentRunner` Protocol / `AgentRunError` /
# `ProductionAgentRunner` / `_clean_child_env` / `_load_agent_md` now live in render_common
# (imported above). Re-exported names keep `svc.FeedbackItem` / `svc.AgentRunError` resolving.


# ======================================================================================
# Job state
# ======================================================================================
@dataclass
class JobState:
    """One single-flight render job: its identity, inputs, the daemon thread, the in-flight slot,
    and the accumulating pipeline outputs. Registered under `(goal_slug, source_hash)`."""

    key: tuple[str, str]
    goal_slug: str
    source_hash: str
    parsed: ParsedRequirements
    goal_dir: Path
    goals_dir: Path | None
    db_path: Path | None
    runner: AgentRunner
    job_dir: Path
    family: str | None = None
    row_id: int | None = None
    thread: threading.Thread | None = None
    slot_held: bool = False
    attempts: int = 0
    what_doc: str | None = None
    what_report: GateReport | None = None
    how_raw: str | None = None
    html: str | None = None  # last EXTRACTABLE render
    html_report: GateReport | None = None
    notes: list[str] = field(default_factory=list)
    terminal: str | None = None
    # --- 4a-2 quality-loop state ---
    how_attempts: int = 0  # HOW iterations consumed (the QUALITY_MAX_ATTEMPTS ceiling counter)
    what_reworks: int = 0  # forced run_what re-runs (the QUALITY_MAX_WHAT_REWORKS budget)
    consecutive_structural: int = 0  # consecutive structural-gate failures (QUALITY_STRUCTURAL_STOP)
    missing_streak: int = 0  # consecutive verdicts naming the same gated missing[] token
    missing_streak_tokens: frozenset[str] = field(default_factory=frozenset)
    attempts_history: list[AttemptRecord] = field(default_factory=list)
    # --- 5a gap-machinery state (runs ONCE per job, before the 4a quality loop) ---
    gaps_trailer: list[dict] = field(default_factory=list)   # HOW-detected gaps (probe harvest)
    open_gaps: list[dict] = field(default_factory=list)      # WHAT doc's gaps[] after ask_what
    gapfill_answers: list[dict] = field(default_factory=list)  # parsed gapfill output (claims)
    gaps_state: list[dict] = field(default_factory=list)    # gaps-state.json resolution records
    open_gap_markers: list[dict] = field(default_factory=list)  # {question, status} for the render
    ask_rounds: int = 0  # GAPFILL_ASK_ROUNDS counter — INDEPENDENT of QUALITY_MAX_WHAT_REWORKS (A2)
    # --- HOW-update-mode 3a: the two-mode (CREATE/UPDATE) decision + recovered UPDATE inputs ---
    # `mode` is the DECIDED mode ('create' | 'update'); it is stamped on the row + drives the inert
    # UPDATE path. The path is flag-gated (config.RENDER_UPDATE_ENABLED) — production stays CREATE
    # even when mode == 'update' until Sub-phase 3b flips the gate.
    mode: str | None = None
    prior_html: str | None = None              # the recovered prior published render (UPDATE input)
    prior_parsed: ParsedRequirements | None = None  # the recovered prior SOURCE, parsed
    changed_refs: frozenset = frozenset()      # changed-block match-keys (block_diff._key space)
    # --- HOW-update-mode 3b: canonical-id dispositions for the splice + the survival reorient ---
    # These are CANONICAL refs (`_norm_ref` space — `FR-001`/`US1`/`SC-003`), distinct from the
    # `block_diff._key` `changed_refs` above; the splice + the render-space survival gate key on them.
    update_modified_refs: frozenset[str] = frozenset()
    update_added_refs: frozenset[str] = frozenset()
    update_removed_refs: frozenset[str] = frozenset()
    update_unchanged_refs: frozenset[str] = frozenset()  # current labeled units NOT changed
    splice_missing_refs: tuple[str, ...] = ()  # changed refs HOW emitted no fragment for (this attempt)
    last_survival: dict | None = None          # latest check_comment_survival report (publish boundary)


# ======================================================================================
# Module-level concurrency state (single-flight registry + in-flight semaphore + reaper)
# ======================================================================================
# The mechanism lives in render_common.job_runtime.JobRegistry now (shared with the exploration
# render-job). This module owns ONE instance and re-exports its members under the existing module
# names so callers + the (unchanged) tests keep resolving `_registry`, `_acquire_slot`, etc.
_runtime = JobRegistry(config.RENDER_MAX_INFLIGHT)
_registry = _runtime.registry
_registry_lock = _runtime.registry_lock
_acquire_slot = _runtime.acquire_slot
_release_slot = _runtime.release_slot
slots_held = _runtime.slots_held


def _reset_state(*, max_inflight: int | None = None) -> None:
    """Test hook: clear the registry + held-slot set and rebuild the semaphore. NOT for prod use."""
    _runtime.reset(max_inflight=max_inflight or config.RENDER_MAX_INFLIGHT)


# Row I/O (`_insert_job` / `_update_job` / `get_job_row` / `latest_job_row`) + the time helpers
# (`_utcnow` / `_utcnow_iso` / `_age_seconds`) are imported from render_common.job_runtime above.


def list_flagged_renders(db_path=None, limit: int = 100) -> list[dict]:
    """Read-only list of render jobs flagged for human review (Phase 5d's honest
    degraded-page surface). One dict per ``render_jobs`` row with ``human_review=1``,
    carrying the existing flag columns (``review_reason``, ``published_score``,
    ``published_attempt``) plus ``goal_slug``/``source_hash`` so the caller can link to
    the render. NO new write path, NO new column — this reads the 4a recording-only flag
    columns the executor already stamps ("surface, don't suppress"). The render link is
    ``/goals/{goal_slug}/render`` (the page regenerates from canonical on view).
    """
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, goal_slug, source_hash, status, review_reason, "
            "published_score, published_attempt, finished_at "
            "FROM render_jobs WHERE human_review = 1 "
            "ORDER BY finished_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


# `latest_job_row` is imported from render_common.job_runtime above (re-exported for 3d's status
# endpoint + callers).


def _heartbeat(state: JobState, stage: str) -> None:
    """Stamp `heartbeat_at` (+ the running attempt count) at a stage boundary (revision a). The
    heartbeat is the reaper's staleness detector — the reaper ceiling is derived from the
    configured stage-timeout list, so a job that stops advancing is eventually declared orphaned."""
    if state.row_id is not None:
        _update_job(state.row_id, state.db_path, heartbeat_at=_utcnow_iso(), attempts=state.attempts)


def _note(state: JobState, msg: str) -> None:
    """Record a non-fatal pipeline note (folded into a fallback/flag reason — zero silent drops)."""
    state.notes.append(msg)
    logger.info("render job %s: %s", state.key, msg)


def _write_artifact(state: JobState, name: str, content: str) -> None:
    """Persist a job working artifact under build/render-jobs/{slug}/{hash12}/ (best-effort). NEVER
    under goals/{slug}/ — the FR-026 folder invariant stays intact."""
    try:
        state.job_dir.mkdir(parents=True, exist_ok=True)
        (state.job_dir / name).write_text(content, encoding="utf-8")
    except OSError as exc:
        logger.warning("render job %s: could not write artifact %s: %s", state.key, name, exc)


def _report_json(report: GateReport) -> str:
    return json.dumps({"passed": report.passed, "violations": list(report.violations)}, indent=2)


# `extract_render` + the sentinel pair are imported from render_common.sentinel above (the HOW
# output contract is identical for both render-jobs).


# ======================================================================================
# Prompt builders — the runner inlines all agent inputs (Step 3c.1)
# ======================================================================================
def _block_inventory(parsed: ParsedRequirements) -> str:
    lines = [
        f"- {b.ref} [{b.kind.value}] {b.heading or ''}".rstrip()
        for b in parsed.blocks if b.ref
    ]
    return "\n".join(lines) or "(no canonical refs)"


def _render_feedback(
    prompt: str, feedback: list[FeedbackItem] | None, score_history: str | None = None
) -> str:
    """Append provenance-separated feedback to a prompt (CQ1).

    Structural and quality items ride the same list but render under distinct headings so the agent
    can tell a hard requirement from a taste nudge. The optional `score_history` one-liner lets the
    agent see that regression is visible (4a2.3)."""
    if not feedback and not score_history:
        return prompt
    structural = [i.text for i in (feedback or []) if i.provenance == "structural"]
    quality = [i.text for i in (feedback or []) if i.provenance == "quality"]
    parts = [prompt]
    if structural:
        parts.append(
            "Structural fixes (required) — your previous attempt FAILED these non-negotiable "
            "structural checks; fix EVERY one and re-emit the COMPLETE output:"
        )
        parts.extend(f"- {t}" for t in structural)
    if quality:
        parts.append(
            "Quality improvements (guidance) — the reviewer asked for these to raise comprehension "
            "and visual quality; treat them as guidance, not hard requirements:"
        )
        parts.extend(f"- {t}" for t in quality)
    if score_history:
        parts.append(score_history)
    return "\n".join(parts) + "\n"


def _build_what_prompt(state: JobState) -> str:
    parsed = state.parsed
    family = f"work_family: {state.family}\n" if state.family else ""
    return (
        f"Produce the WHAT doc (contract cast-requirements-what/v1) for this goal.\n"
        f"goal_slug: {state.goal_slug}\n"
        f"source_hash: {state.source_hash}\n"
        f"{family}"
        f"\nCanonical block inventory — every ref MUST map into exactly one section:\n"
        f"{_block_inventory(parsed)}\n"
        f"\n----- BEGIN SOURCE refined_requirements.collab.md -----\n"
        f"{parsed.source_text}\n"
        f"----- END SOURCE -----\n"
    )


def _build_how_update_section(state: JobState) -> str:
    """The INERT UPDATE sub-contract appended to the HOW prompt in UPDATE mode (Step 3a.5).

    Shaped by the **Sub-phase 1a verdict: FAIL → deterministic-splice** (read at exec time from
    `spikes/update-fidelity/verdict.md`). The verdict proved the production HOW agent paraphrases
    unchanged narrative cells ~10% of the time even under a literal copy-exact instruction, so the
    UPDATE mechanism does NOT ask HOW to re-emit the whole page and hold unchanged containers
    byte-identical (the PASS branch's gate-enforced-LLM-copy). Instead the SERVER keeps the prior
    render's unchanged unit-container bytes verbatim and splices in HOW-rendered **changed-block
    fragments** — byte-identity of untouched prose is guaranteed by construction. This sub-contract
    therefore asks HOW only for the reliable thing the spike confirmed it does well (15/15
    add/modify rendered, 15/15 removed dropped): render the CHANGED blocks as standalone fragments.

    Appended only when `_is_update_active(state)` (an UPDATE was decided). Sub-phase 3b finalized the
    **fragment-delimiter protocol** the server splices on — kept byte-aligned with `block_splice.
    parse_fragments` and the two-mode section of `cast-requirements-how.md`: HOW emits, between the
    render sentinels, ONE ``<!-- RR-FRAGMENT ref="<ID>" -->`` … ``<!-- /RR-FRAGMENT -->`` block per
    CHANGED (added/modified) ref — the standalone unit-container fragment for that ref. Nothing else
    (no full page, no unchanged units, no fragment for a removal)."""
    # Human-readable changed-set (added / modified / removed), recomputed from the recovered prior
    # source via the shared diff engine (pure; consumed unchanged).
    if state.prior_parsed is not None:
        summary = block_diff.summarize(block_diff.diff_blocks(state.prior_parsed, state.parsed))
    else:  # defensive — UPDATE is only decided with a recovered prior_parsed
        summary = {"counts": {}, "items": []}
    fragment_refs = sorted(state.update_modified_refs | state.update_added_refs)
    return (
        "\n----- BEGIN UPDATE MODE (deterministic-splice — 1a verdict: FAIL) -----\n"
        "This is an UPDATE of an existing published render, NOT a fresh page. The SERVER already "
        "holds every UNCHANGED unit container's bytes from the prior render and keeps them verbatim — "
        "you MUST NOT reproduce, re-word, or re-emit any unchanged content, and you MUST NOT emit a "
        "full page. Render ONLY the changed units below, each as a standalone unit-container fragment "
        "matching the prior render's structure + style, wrapped in the EXACT delimiters:\n"
        '  <!-- RR-FRAGMENT ref="FR-001" -->\n'
        "  <li><strong>FR-001</strong> …the new unit-container fragment…</li>\n"
        "  <!-- /RR-FRAGMENT -->\n"
        "Emit exactly one RR-FRAGMENT block per ref in this list (added → a new fragment; modified → "
        "the replacement fragment): \n"
        f"  {fragment_refs}\n"
        "Removed blocks: emit NOTHING (the server drops them). Carry each fragment's own anchor label "
        "verbatim exactly once; never invent or rename an id. The fragments may appear in any order — "
        "the server splices each into the prior page by its ref.\n"
        "\n----- BEGIN CHANGED-SET (the ONLY blocks to render) -----\n"
        f"{json.dumps(summary, indent=2)}\n"
        "----- END CHANGED-SET -----\n"
        "\n----- BEGIN PRIOR RENDER (style + structure reference — DO NOT re-emit unchanged parts) -----\n"
        f"{state.prior_html}\n"
        "----- END PRIOR RENDER -----\n"
        "----- END UPDATE MODE -----\n"
    )


def _build_how_prompt(state: JobState) -> str:
    family = f"work_family: {state.family}\n" if state.family else ""
    # 5a: inline the OPEN gaps (question + resolved status) so the final, gap-aware render carries
    # one `.rr-gap` marker per open gap. Absent on the gap-probe (markers not resolved yet) and on a
    # gapless render. The page renders the QUESTION + a status note — NEVER an answer (FR-016).
    gaps_section = ""
    if state.open_gap_markers:
        gaps_section = (
            "\n----- BEGIN OPEN GAPS (render exactly ONE .rr-gap marker per entry: its question + a "
            "short status note; NEVER render an answer or proposed body) -----\n"
            f"{json.dumps(state.open_gap_markers, indent=2)}\n"
            "----- END OPEN GAPS -----\n"
        )
    # HOW-update-mode 3a: in UPDATE mode the fragment sub-contract is appended (INERT — only when
    # `_is_update_active`, i.e. an UPDATE was decided AND the flag-gate is open; off in production
    # until 3b). CREATE mode (the production path) is byte-unchanged.
    update_section = _build_how_update_section(state) if _is_update_active(state) else ""
    return (
        f"Produce the self-contained HTML render between the {_BEGIN_SENTINEL} / "
        f"{_END_SENTINEL} sentinels, per your contract.\n"
        f"goal_slug: {state.goal_slug}\n"
        f"source_hash: {state.source_hash}\n"
        f"{family}"
        f"\n----- BEGIN WHAT DOC -----\n"
        f"{state.what_doc}\n"
        f"----- END WHAT DOC -----\n"
        f"\n----- BEGIN SOURCE refined_requirements.collab.md -----\n"
        f"{state.parsed.source_text}\n"
        f"----- END SOURCE -----\n"
        f"{gaps_section}"
        f"{update_section}"
    )


def _build_checker_prompt(state: JobState, html: str) -> str:
    """The checker sees ONLY the rendered artifact + the family label — never the canonical source
    or the WHAT doc (the cold-reader property, guaranteed by construction; the agent is also
    `--tools ""` so it physically cannot fetch them). The zero-click view goes first: it is the
    surface a non-clicking reader actually sees, computed deterministically by `extract_zero_click_view`."""
    zero_click = extract_zero_click_view(html)
    family = f"work_family: {state.family}\n" if state.family else ""
    return (
        f"Grade this rendered requirements page. Emit ONE bare JSON verdict (contract "
        f"{CHECKER_CONTRACT}) — no prose, no code fences.\n"
        f"{family}"
        f"\n----- BEGIN ZERO-CLICK VIEW (what a non-clicking reader sees) -----\n"
        f"{zero_click}\n"
        f"----- END ZERO-CLICK VIEW -----\n"
        f"\n----- BEGIN FULL RENDERED HTML -----\n"
        f"{html}\n"
        f"----- END FULL RENDERED HTML -----\n"
    )


# ======================================================================================
# HOW-update-mode 3a: two-mode (CREATE / UPDATE) decision + prior-render recovery
# ======================================================================================
# The whole block below is PLUMBING — built, tested, and INERT. `decide_mode` is pure and
# unit-tested at every threshold boundary; the recovery + `_prepare_mode` glue runs at job start and
# stamps the DECIDED mode for observability, but `config.RENDER_UPDATE_ENABLED` gates whether the
# UPDATE behaviour (WHAT reuse, fragment HOW sub-contract, gap-emit skip) actually fires. Until
# Sub-phase 3b flips that default, production renders 100% CREATE regardless of the decided mode.

def decide_mode(
    *,
    prior_html: str | None,
    prior_served_by: str | None,
    prior_human_review: bool,
    prior_source: str | None,
    changed_fraction: float,
    prior_render_bytes: int,
    workflow_family_changed: bool,
    max_changed_fraction: float | None = None,
    max_prior_bytes: int | None = None,
) -> tuple[str, str | None]:
    """Decide CREATE vs UPDATE for a render job. PURE — no I/O, fully unit-testable.

    Returns ``(mode, note)`` where ``mode`` ∈ ``{'create', 'update'}`` and ``note`` is the
    degrade-to-CREATE reason (``None`` only on a clean UPDATE). UPDATE iff **all** preconditions hold;
    EVERY failure degrades to CREATE with a non-empty note — never a job error, since CREATE is always
    a safe answer (shared-context Owner Principle: every UPDATE precondition failure degrades to CREATE
    with a job ``_note``).

    Preconditions (each maps to one degrade reason):
      * a prior render exists AND it was a CLEAN maker publish (``served-by: maker``, NOT human-review)
        — never UPDATE *from* a flagged/fallback render (it would propagate the flaw; a fresh CREATE is
        exactly the recovery for a flagged prior);
      * the prior source is recoverable (so the changed-set is real, not guessed);
      * the goal's ``workflow_family`` is unchanged (a family flip is a different page shape);
      * ``changed_fraction <= RENDER_UPDATE_MAX_CHANGED_FRACTION`` (a massive edit re-renders fresh);
      * ``prior_render_bytes <= RENDER_UPDATE_MAX_PRIOR_BYTES`` (plan-review Decision #6 — a prior page
        near the context budget can silently truncate, dropping tail unchanged containers).
    """
    max_changed_fraction = (
        config.RENDER_UPDATE_MAX_CHANGED_FRACTION
        if max_changed_fraction is None else max_changed_fraction
    )
    max_prior_bytes = (
        config.RENDER_UPDATE_MAX_PRIOR_BYTES if max_prior_bytes is None else max_prior_bytes
    )
    if not prior_html:
        return "create", "no recoverable prior render — first render of this goal/source"
    if prior_served_by != "maker":
        return "create", f"prior render is not a clean maker publish (served-by={prior_served_by!r})"
    if prior_human_review:
        return "create", "prior render was flagged for human review — never UPDATE from a flagged prior"
    if not prior_source:
        return "create", "prior source not recoverable — cannot compute a trustworthy changed-set"
    if workflow_family_changed:
        return "create", "workflow_family changed since the prior render"
    if changed_fraction > max_changed_fraction:
        return "create", (
            f"changed_fraction {changed_fraction:.3f} exceeds "
            f"RENDER_UPDATE_MAX_CHANGED_FRACTION {max_changed_fraction} — massive edit, re-render fresh"
        )
    if prior_render_bytes > max_prior_bytes:
        return "create", (
            f"prior_render_bytes {prior_render_bytes} exceeds "
            f"RENDER_UPDATE_MAX_PRIOR_BYTES {max_prior_bytes} — too large to inline safely"
        )
    return "update", None


def _front_matter_family(parsed: ParsedRequirements | None) -> str | None:
    """The declared ``classification.family`` from a parsed doc's front matter, or None. Used only to
    detect a workflow_family flip between the prior and current source (a CREATE trigger)."""
    if parsed is None:
        return None
    classification = parsed.front_matter.get("classification") if parsed.front_matter else None
    if isinstance(classification, dict):
        return classification.get("family")
    return None


def _compute_changed_set(
    prior: ParsedRequirements, current: ParsedRequirements
) -> tuple[float, frozenset, dict]:
    """The deterministic changed-set from ``prior`` to ``current`` via the shared ``block_diff``
    engine (consumed unchanged — FR-024). Returns ``(changed_fraction, changed_refs, summary)``:

      * ``changed_fraction = (added + removed + modified) / max(old_blocks, new_blocks)`` — the
        massive-change measure the mode decision thresholds against;
      * ``changed_refs`` — the set of changed-block match-keys (``block_diff._key`` space — the SAME
        keying 3b's splice uses to find unchanged-container seams); added/modified.new/removed blocks;
      * ``summary`` — ``summarize(diff)`` (the JSON-able changed-set for the job-dir artifact + the
        UPDATE prompt's human-readable fragment list).
    """
    diff = block_diff.diff_blocks(prior, current)
    summary = block_diff.summarize(diff)
    counts = summary["counts"]
    changed = counts["added"] + counts["removed"] + counts["modified"]
    denom = max(len(prior.blocks), len(current.blocks), 1)
    changed_fraction = changed / denom
    keys: set = set()
    keys.update(block_diff._key(b) for b in diff.added)
    keys.update(block_diff._key(mb.new) for mb in diff.modified)
    keys.update(block_diff._key(b) for b in diff.removed)
    return changed_fraction, frozenset(keys), summary


def _recover_prior_source(state: JobState, prior_hash: str | None) -> str | None:
    """Recover the prior render's SOURCE text. Primary: the prior job dir's persisted ``source.md``
    (``build/render-jobs/{slug}/{prior_hash12}/source.md``). Fallback: a ``requirement_versions``
    snapshot whose ``content_hash`` matches ``prior_hash``. Nothing found → None (→ CREATE).

    The job dir is non-CI runtime state — wiping it only costs UPDATE capability for the next render
    (the fallback, then CREATE), never publish (shared-context job-dir lifecycle invariant)."""
    if not prior_hash:
        return None
    job_source = Path(config.RENDER_JOBS_DIR) / state.goal_slug / prior_hash[:12] / "source.md"
    try:
        if job_source.exists():
            return job_source.read_text(encoding="utf-8")
    except OSError as exc:
        _note(state, f"prior source.md unreadable ({exc}) — trying requirement_versions fallback")
    # Fallback: a content-hash-matching requirement_versions snapshot (the prior canonical content).
    conn = get_connection(state.db_path)
    try:
        row = conn.execute(
            "SELECT content FROM requirement_versions WHERE goal_slug = ? AND content_hash = ? "
            "ORDER BY version DESC LIMIT 1",
            (state.goal_slug, prior_hash),
        ).fetchone()
    finally:
        conn.close()
    return row["content"] if row else None


# The leading AUTO-GENERATED envelope `publish_maker_html` prepends — stripped from the recovered
# prior render so the UPDATE splice templates on the MAKER BODY, not the published artifact (else
# `publish_maker_html` would prepend a SECOND envelope, doubling it on every UPDATE).
_ENVELOPE_PREFIXES = (
    requirements_render_service._AUTO_GENERATED_HEADER,
    requirements_render_service._SOURCE_HASH_PREFIX,
    requirements_render_service._SERVED_BY_PREFIX,
    requirements_render_service._HUMAN_REVIEW_PREFIX,
    requirements_render_service._REVIEW_REASON_PREFIX,
)


def _strip_render_envelope(html: str) -> str:
    """Drop the leading AUTO-GENERATED/source-hash/served-by/human-review/review-reason comment lines
    `publish_maker_html` prepends, returning the maker body. Stops at the first non-envelope line (the
    maker body is a full `<!doctype html>` doc), so a body comment is never mistaken for an envelope."""
    lines = html.splitlines(keepends=True)
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith(_ENVELOPE_PREFIXES):
        i += 1
    return "".join(lines[i:])


def _recover_prior_render(state: JobState) -> dict | None:
    """Recover the prior published render + its embedded stamps from ``goals/{slug}/
    refined_requirements.html`` (it IS the prior render until publish overwrites it). Returns a dict
    ``{html, served_by, human_review, source_hash, source, parsed}`` or None when no prior render
    exists / is unreadable. Stamp extraction REUSES the single-implementation ``_embedded_*`` readers
    in ``requirements_render_service`` (never a second parser); ``html`` is the ENVELOPE-STRIPPED
    maker body (the UPDATE splice template — see ``_strip_render_envelope``)."""
    html_path = state.goal_dir / "refined_requirements.html"
    if not html_path.exists():
        return None
    try:
        raw = html_path.read_text(encoding="utf-8")
    except OSError as exc:
        _note(state, f"prior render unreadable ({exc}) — CREATE")
        return None
    source_hash = requirements_render_service._embedded_source_hash(raw)
    prior_source = _recover_prior_source(state, source_hash)
    prior_parsed = parse_requirements(prior_source) if prior_source else None
    return {
        "html": _strip_render_envelope(raw),  # the maker body (splice template — no envelope)
        "served_by": requirements_render_service._embedded_served_by(raw),
        "human_review": requirements_render_service._embedded_human_review(raw),
        "source_hash": source_hash,
        "source": prior_source,
        "parsed": prior_parsed,
    }


def _prepare_mode(state: JobState) -> None:
    """Job-start plumbing: persist the recovery input ``source.md``, decide CREATE vs UPDATE, and
    stamp the decided ``mode`` (+ the changed-set) for observability.

    Runs at the TOP of the job thread (NOT under the single-flight registry lock — recovery does file
    + DB I/O). INERT by construction: it records the decision and assembles UPDATE inputs, but the
    pipeline only ACTS on ``mode='update'`` when ``config.RENDER_UPDATE_ENABLED`` is set (Sub-phase 3b
    flips that default). Every degrade-to-CREATE is a note, never an error."""
    # Persist the parsed source text for THIS job — the recovery input a FUTURE render reads to
    # reconstruct the changed-set (Step 3a.2). Best-effort; a write failure only costs the next
    # render's UPDATE capability (it degrades to CREATE), never this publish.
    _write_artifact(state, "source.md", state.parsed.source_text)

    prior = _recover_prior_render(state)
    if prior is None:
        mode, note = "create", "no recoverable prior render — first render of this goal/source"
    else:
        changed_fraction, changed_refs, summary = _compute_changed_set(
            prior["parsed"], state.parsed
        ) if prior["parsed"] is not None else (1.0, frozenset(), {"counts": {}, "items": []})
        family_changed = _front_matter_family(prior["parsed"]) != _front_matter_family(state.parsed)
        mode, note = decide_mode(
            prior_html=prior["html"],
            prior_served_by=prior["served_by"],
            prior_human_review=prior["human_review"],
            prior_source=prior["source"],
            changed_fraction=changed_fraction,
            prior_render_bytes=len(prior["html"].encode("utf-8")),
            workflow_family_changed=family_changed,
        )
        if mode == "update":
            # 3b: derive the CANONICAL-id dispositions the splice + the render-space survival gate
            # key on (distinct from the `block_diff._key`-space `changed_refs`). A change to a
            # REF-LESS block (Intent prose, a Constraints bullet — no anchor label in the render)
            # cannot be keyed by ref, so the splice cannot faithfully re-render it → degrade to
            # CREATE (owner principle: every UPDATE precondition failure degrades to CREATE, noted,
            # never errored — CREATE re-renders the whole page fresh and handles ref-less edits).
            diff = block_diff.diff_blocks(prior["parsed"], state.parsed)
            refless = (
                any(b.ref is None for b in diff.added)
                or any(b.ref is None for b in diff.removed)
                or any(mb.new.ref is None for mb in diff.modified)
            )
            n_changed = len(diff.added) + len(diff.modified) + len(diff.removed)
            if refless:
                mode, note = "create", (
                    "a ref-less block (no anchor label) changed — the splice cannot key it; "
                    "re-rendering fresh"
                )
            elif n_changed == 0:
                # The source hash changed but `block_diff` localizes NO block change — the edit is
                # something the block engine can't pin to a ref (front matter, inter-block prose the
                # parser attaches ambiguously, a resolved gap's answer). A zero-changed-set UPDATE
                # would splice the prior render byte-for-byte and silently ignore the edit (e.g. a
                # stale `.rr-gap` marker surviving a resolved gap), so re-render fresh.
                mode, note = "create", (
                    "source changed but no block-level change is localizable — re-rendering fresh"
                )
            else:
                state.prior_html = prior["html"]
                state.prior_parsed = prior["parsed"]
                state.changed_refs = changed_refs
                state.update_modified_refs = frozenset(
                    _norm_ref(mb.new.ref) for mb in diff.modified if mb.new.ref
                )
                state.update_added_refs = frozenset(
                    _norm_ref(b.ref) for b in diff.added if b.ref
                )
                state.update_removed_refs = frozenset(
                    _norm_ref(b.ref) for b in diff.removed if b.ref
                )
                current_refs = frozenset(
                    _norm_ref(b.ref) for b in state.parsed.blocks if b.ref
                )
                state.update_unchanged_refs = (
                    current_refs - state.update_modified_refs - state.update_added_refs
                )
                _write_artifact(state, "changed-set.json", json.dumps(summary, indent=2))

    state.mode = mode
    if note is not None:
        _note(state, f"render mode=CREATE: {note}")
    else:
        _note(
            state,
            f"render mode=UPDATE decided (modified={sorted(state.update_modified_refs)}, "
            f"added={sorted(state.update_added_refs)}, removed={sorted(state.update_removed_refs)})",
        )
    if state.row_id is not None:
        _update_job(state.row_id, state.db_path, mode=mode)


def _is_update_active(state: JobState) -> bool:
    """Whether the UPDATE BEHAVIOUR fires this job — simply: an UPDATE was decided.

    **Sub-phase 3b wired the mode decision LIVE: the 3a flag-gate is gone.** When `decide_mode`
    (refined by `_prepare_mode`'s ref-less-change degrade) lands ``mode='update'``, the deterministic
    splice runs for real — the server keeps unchanged unit-container bytes verbatim and splices HOW's
    changed-block fragments (1a verdict FAIL → deterministic-splice). ``config.RENDER_UPDATE_ENABLED``
    is retired as a behaviour gate (kept only as a harmless legacy constant)."""
    return state.mode == "update"


# ======================================================================================
# Named pipeline stages (the 4a/5 insertion seam)
# ======================================================================================
def run_what(state: JobState, feedback: list[FeedbackItem] | None = None) -> None:
    """Run `cast-requirements-what` once → `state.what_doc`. A crash/empty attempt leaves any prior
    doc intact (so a failed retry never discards a usable attempt-1 doc)."""
    _heartbeat(state, "run_what")
    state.attempts += 1
    n = state.attempts
    prompt = _render_feedback(_build_what_prompt(state), feedback)
    try:
        raw = state.runner.run_agent(_WHAT_AGENT, prompt, timeout_s=_stage_timeout("run_what"))
    except AgentRunError as exc:
        _note(state, f"{_WHAT_AGENT} attempt {n} failed: {exc}")
        return
    _write_artifact(state, f"what-attempt-{n}.md", raw or "")
    if raw and raw.strip():
        state.what_doc = raw
    else:
        _note(state, f"{_WHAT_AGENT} attempt {n} produced empty output")


def gate_what(state: JobState) -> None:
    """Gate the WHAT doc with `check_what_doc` → `state.what_report` (None when no doc exists).

    HOW-update-mode 3a: on a PASSING gate, persist the gated WHAT doc at the stable
    `_what_doc_job_ref(state)` path (`render-jobs/{slug}/{hash12}/what-doc.md`) — making the path the
    gap emitter already references real, and giving a future UPDATE render a recoverable WHAT doc to
    reuse (Step 3a.2). Best-effort; never blocks the gate."""
    _heartbeat(state, "gate_what")
    if state.what_doc is None:
        state.what_report = None
        return
    state.what_report = check_what_doc(state.what_doc, state.parsed)
    _write_artifact(state, "gate_what.json", _report_json(state.what_report))
    if state.what_report.passed:
        _write_artifact(state, "what-doc.md", state.what_doc)


def run_how(
    state: JobState,
    feedback: list[FeedbackItem] | None = None,
    score_history: str | None = None,
) -> str | None:
    """Run `cast-requirements-how` once → return THIS call's extractable render (or None on a
    crash / no-sentinel attempt), also updating `state.html` to the latest extractable render.
    Skipped (returns None) when no WHAT doc exists. The return lets the loop tell a no-extract
    attempt (a per-attempt no-output) apart from a stale-but-present `state.html`."""
    _heartbeat(state, "run_how")
    if state.what_doc is None:
        _note(state, f"{_HOW_AGENT} skipped — no WHAT doc to render")
        return None
    state.attempts += 1
    state.how_attempts += 1
    n = state.how_attempts
    prompt = _render_feedback(_build_how_prompt(state), feedback, score_history)
    try:
        raw = state.runner.run_agent(_HOW_AGENT, prompt, timeout_s=_stage_timeout("run_how"))
    except AgentRunError as exc:
        _note(state, f"{_HOW_AGENT} attempt {n} failed: {exc}")
        return None
    state.how_raw = raw
    extracted = extract_render(raw)
    # UPDATE mode (3b deterministic splice): the extracted bytes are HOW's CHANGED-block FRAGMENTS,
    # not a full page. The server assembles the published page by keeping the prior render's
    # unchanged unit-container bytes verbatim and splicing the fragments in. `extract_render` returning
    # None is still a literal no-output (no sentinels) — only that triggers the deterministic fallback.
    if extracted is not None and _is_update_active(state):
        extracted = _assemble_update_html(state, extracted, n)
    else:
        state.splice_missing_refs = ()
    _write_artifact(state, f"attempt-{n}.html", extracted if extracted is not None else (raw or ""))
    if extracted is not None:
        state.html = extracted
        return extracted
    _note(state, f"{_HOW_AGENT} attempt {n}: no extractable render (sentinel failure)")
    return None


def _assemble_update_html(state: JobState, fragment_output: str, n: int) -> str:
    """Splice HOW's UPDATE-mode fragment output into the prior render (3b deterministic-splice).

    Persists the raw fragment output for the post-mortem, runs `block_splice.splice_update`, and
    records any changed ref HOW emitted no fragment for (`splice_missing_refs`) so `gate_html`
    surfaces it as a structural violation (→ the standard retry → best-attempt + flag path; never a
    silent stale-prior publish). Returns the assembled page (prior bytes for unchanged units)."""
    _write_artifact(state, f"attempt-{n}.fragments.html", fragment_output)
    fragments = block_splice.parse_fragments(fragment_output)
    result = block_splice.splice_update(
        state.prior_html, fragments,
        modified_refs=state.update_modified_refs,
        added_refs=state.update_added_refs,
        removed_refs=state.update_removed_refs,
    )
    state.splice_missing_refs = result.missing_refs
    if result.missing_refs:
        _note(
            state,
            f"UPDATE splice attempt {n}: HOW emitted no fragment for "
            f"{sorted(set(result.missing_refs))} — flagged structural",
        )
    return result.html


def gate_html(state: JobState) -> None:
    """Gate the best-attempt HTML with `check_html`, then widen the report with the comment-
    survival check (Phase 4b-1) → `state.html_report` (None when no HTML).

    DECISION #10 OVERRIDE: an **in-block** survival miss is a real verbatim-carriage failure, so
    it merges into the EXISTING `html_report.violations` structural channel — the maker gets its
    one structural retry (`_execute_pipeline`) and, on exhaustion, the already-shipped `publish()`
    serves the best attempt + `structural_violation` flag. There is NO new blocking branch here.
    **Cross-boundary** misses are recorded in `survival.json` (and surface read-time via the
    `.comment-unplaced` tray badge) but never flip `passed` and never merge into the report.

    Open comments are fetched **at this stage entry, re-read on every `gate_html` entry** (Decision
    #9) — one indexed SELECT, so a structural retry / 4a re-entry sees the current comment set.
    """
    _heartbeat(state, "gate_html")
    if state.html is None:
        state.html_report = None
        return
    # 5a: the structural gate also asserts gap-marker correspondence against the OPEN gaps the gap
    # pipeline resolved for this job (empty on a gapless render → only "no stray .rr-gap" bites).
    report = check_html(
        state.html, state.parsed,
        open_gap_questions=[m["question"] for m in state.open_gap_markers],
    )

    # Fetch the goal's OPEN comments at stage entry (re-read per attempt) and run the pure gate.
    # 3b: pass each comment's render-space anchor (`block_ref` + `anchor_space`) + the UPDATE
    # changed-ref set so the survival gate scores render-space comments correctly — an unchanged-block
    # miss is structural; a changed-block miss is EXPECTED (routed to the publish-boundary re-anchor).
    comments = comment_service.list_comments(
        state.goal_slug, state="open", db_path=state.db_path, goals_dir=state.goals_dir
    )
    changed_refs = state.update_modified_refs | state.update_removed_refs
    survival = check_comment_survival(
        state.html, state.parsed,
        [{"id": c["id"], "quoted_text": c["quoted_text"],
          "block_ref": c.get("block_ref"), "anchor_space": c.get("anchor_space")} for c in comments],
        changed_refs=changed_refs,
    )
    _write_artifact(state, "survival.json", json.dumps(survival, indent=2))
    state.last_survival = survival

    # 3b: UPDATE-splice fidelity — every UNCHANGED unit container kept byte-identical to the prior
    # render. Byte-identity is a CONSTRUCTION guarantee (the server kept the prior bytes), so this
    # only ever fires on a splice bug — a structural violation that takes the standard retry. A
    # changed ref HOW emitted no fragment for is likewise structural (else a stale-prior unit would
    # publish silently).
    structural_extra: list[str] = list(survival["violations"])
    if _is_update_active(state):
        fidelity = check_update_fidelity(state.html, state.prior_html, state.update_unchanged_refs)
        structural_extra.extend(fidelity.violations)
        structural_extra.extend(
            f"UPDATE: changed unit {ref} has no rendered fragment (the splice kept stale prior bytes "
            "or dropped it) — re-emit its RR-FRAGMENT." for ref in state.splice_missing_refs
        )

    # Merge structural survival/fidelity violations into the SAME structural channel (frozen report ⇒
    # build a new one, never mutate). Cross-boundary / expected-miss-only misses leave the list empty,
    # so `passed` is untouched — they surface via the badge / publish-boundary re-anchor instead.
    if structural_extra:
        report = GateReport(
            passed=False,
            violations=report.violations + tuple(structural_extra),
        )

    state.html_report = report
    _write_artifact(state, "gate_html.json", _report_json(state.html_report))


def run_checker(state: JobState, html: str) -> tuple[CheckerVerdict | None, bool]:
    """Run `cast-requirements-render-checker` over one extractable attempt → `(verdict, unscored)`.

    The checker is scoreable for EVERY extractable attempt — even a structurally-broken one (the
    OVERRIDE: broken ≠ short-circuit; `decide_quality` is the single terminal decision point). ONE
    retry on a subprocess error or a malformed verdict; a second failure marks the attempt
    `unscored` (recorded, never silent) and returns `(None, True)`. The parsed verdict (plus the
    code-side `derive_pass` / `canonical_score`) is written to `attempt-N.verdict.json` so the
    non-convergence post-mortem is replayable from disk."""
    _heartbeat(state, "run_checker")
    n = state.how_attempts
    prompt = _build_checker_prompt(state, html)
    last_raw = ""
    for attempt in range(2):  # the one retry
        try:
            last_raw = state.runner.run_agent(
                _CHECKER_AGENT, prompt, timeout_s=_stage_timeout("run_checker")
            )
            verdict = parse_verdict(last_raw)
        except (AgentRunError, CheckerVerdictError) as exc:
            _note(state, f"{_CHECKER_AGENT} attempt {n} try {attempt + 1} failed: {exc}")
            continue
        _write_artifact(state, f"attempt-{n}.verdict.json", _verdict_json(verdict))
        return verdict, False
    # Second failure → unscored (recorded with the raw output for the post-mortem).
    _write_artifact(
        state, f"attempt-{n}.verdict.json",
        json.dumps({"unscored": True, "raw": last_raw[:4000]}, indent=2),
    )
    return None, True


def _verdict_json(verdict: CheckerVerdict) -> str:
    """Serialize a parsed verdict + the code-side derived gate/score (replayable post-mortem)."""
    return json.dumps(
        {
            "contract": verdict.contract,
            "can_state_what": verdict.can_state_what,
            "missing": list(verdict.missing),
            "issues": [
                {"dimension": i.dimension, "criterion": i.criterion, "severity": i.severity,
                 "description": i.description, "evidence": i.evidence}
                for i in verdict.issues
            ],
            "rework_feedback": list(verdict.rework_feedback),
            "agent_score": verdict.score,            # advisory only
            "canonical_score": canonical_score(verdict),   # the value ranking uses
            "derive_pass": derive_pass(verdict),
        },
        indent=2,
    )


# ======================================================================================
# Gap machinery (Phase 5a) — the upstream-ask loop, run ONCE per job before the 4a loop
# ======================================================================================
# The full ordering inserted between `gate_what` and the FINAL `run_how`:
#   run_how PROBE (harvest trailer, NO QUALITY debit — C6) → ask_what (bounded re-run, OWN counter —
#   A2) → run_gapfill (grounded-or-refuse) → validate_evidence (the server-side trust boundary) →
#   emit_change_requests (5b: reconcile validated gaps through the v2 gate + resolve gaps-state.json).
# The gap set is a property of the SOURCE, not a rendering attempt — so it is computed once, before
# the quality loop reworks HOW attempts against a FIXED WHAT doc + gap state (FR-015 "before
# finalizing"). "Never fabricates" is enforced at `validate_evidence`, not promised by the agent.


def _what_front_matter(what_doc: str | None) -> dict | None:
    """Parse the leading `---`-fenced YAML front matter of a WHAT doc (local, read-only). Not one of
    the load-bearing single-helpers (locate/stripper/walker) — just a front-matter split so the
    service can read the gated doc's `gaps[]`. The doc already passed `check_what_doc`."""
    if not what_doc:
        return None
    lines = what_doc.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            try:
                fm = yaml.safe_load("\n".join(lines[1:i]))
            except yaml.YAMLError:
                return None
            return fm if isinstance(fm, dict) else None
    return None


def _extract_what_gaps(what_doc: str | None) -> list[dict]:
    """The open gap set declared by a gated WHAT doc's `gaps[]` front matter, normalized to
    `{gap_id, section_title, block_refs, question, why_it_matters}`. Empty when the doc declares
    none (the clean-render common case)."""
    fm = _what_front_matter(what_doc) or {}
    gaps = fm.get("gaps")
    out: list[dict] = []
    if isinstance(gaps, list):
        for g in gaps:
            if isinstance(g, dict) and g.get("gap_id") and g.get("question"):
                out.append({
                    "gap_id": str(g["gap_id"]),
                    "section_title": str(g.get("section_title") or ""),
                    "block_refs": [str(r) for r in (g.get("block_refs") or [])],
                    "question": str(g["question"]),
                    "why_it_matters": str(g.get("why_it_matters") or ""),
                })
    return out


def _parse_gaps_trailer(raw: str | None) -> list[dict]:
    """Parse the optional HOW `<!-- GAPS-DETECTED … -->` trailer (the "HOW asks WHAT" channel). It
    lives OUTSIDE the render sentinels (after the first `<!-- END RENDER -->`), so `extract_render`
    is byte-untouched. Returns `{section_title, question, why_it_matters}` entries (no ids — the WHAT
    re-run assigns them). Empty on a clean render / parse miss."""
    if not raw:
        return []
    end = raw.find(_END_SENTINEL)
    search_from = (end + len(_END_SENTINEL)) if end != -1 else 0
    start = raw.find(_GAPS_TRAILER_BEGIN, search_from)
    if start == -1:
        return []
    inner_start = start + len(_GAPS_TRAILER_BEGIN)
    close = raw.find("-->", inner_start)
    if close == -1:
        return []
    try:
        data = yaml.safe_load(raw[inner_start:close])
    except yaml.YAMLError:
        return []
    if not isinstance(data, list):
        return []
    return [
        {"section_title": str(e.get("section_title") or ""),
         "question": str(e.get("question")),
         "why_it_matters": str(e.get("why_it_matters") or "")}
        for e in data if isinstance(e, dict) and e.get("question")
    ]


def run_how_probe(state: JobState) -> None:
    """The pre-loop trailer-harvest `run_how` (Plan Review C6). Runs the HOW agent ONCE to surface
    any `<!-- GAPS-DETECTED -->` trailer the HOW layer emits. It does NOT debit
    `QUALITY_MAX_ATTEMPTS` — it never touches `how_attempts` (it is gap machinery, not a quality
    attempt). Its render is discarded (the gap-aware render is the loop's job); only the trailer is
    kept. A probe crash is non-fatal — no trailer harvested, the pipeline proceeds."""
    _heartbeat(state, "run_how")
    if state.what_doc is None:
        return
    try:
        raw = state.runner.run_agent(
            _HOW_AGENT, _build_how_prompt(state), timeout_s=_stage_timeout("run_how")
        )
    except AgentRunError as exc:
        _note(state, f"{_HOW_AGENT} gap-probe failed (no trailer harvested): {exc}")
        return
    _write_artifact(state, "gap-probe.how.txt", raw or "")
    state.gaps_trailer = _parse_gaps_trailer(raw)
    if state.gaps_trailer:
        _note(state, f"gap-probe harvested {len(state.gaps_trailer)} HOW-detected gap question(s)")


def ask_what(state: JobState) -> None:
    """The bounded HOW-asks-WHAT re-run (Plan Review A2). When the probe harvested a non-empty
    trailer AND the `GAPFILL_ASK_ROUNDS` budget allows, re-run `run_what` ONCE with the HOW
    questions appended, then re-gate. The re-run either dissolves a question (the first pass
    under-served source the re-run now maps) or confirms it into `gaps[]`. It uses its OWN counter
    (`ask_rounds`) — it NEVER debits `QUALITY_MAX_WHAT_REWORKS`. A re-gen that fails its gate is
    discarded and the prior WHAT retained (the CQ2 discipline). Always recomputes `open_gaps` from
    the current WHAT doc (so first-pass WHAT-declared gaps count even with no trailer)."""
    _heartbeat(state, "ask_what")
    if state.gaps_trailer and state.ask_rounds < config.GAPFILL_ASK_ROUNDS:
        state.ask_rounds += 1
        prior_doc, prior_report = state.what_doc, state.what_report
        questions = "\n".join(
            f"- {g['question']}"
            + (f"  (section: {g['section_title']})" if g["section_title"] else "")
            for g in state.gaps_trailer
        )
        feedback = [FeedbackItem(
            "The HOW layer asked these questions about details the source may be missing. For EACH: "
            "either map it to source content your first pass under-served, or DECLARE it in `gaps[]` "
            "(you only NAME the gap — never answer it; the answer is grounded-or-refused downstream):"
            f"\n{questions}",
            "quality",
        )]
        run_what(state, feedback=feedback)
        gate_what(state)
        if state.what_report is None or not state.what_report.passed:
            state.what_doc, state.what_report = prior_doc, prior_report
            _note(state, "ask_what re-gen failed gate_what — retained prior WHAT (A2/CQ2)")
    state.open_gaps = _extract_what_gaps(state.what_doc)


def _within_goal_tree(state: JobState, path: Path) -> bool:
    """True iff `path` resolves to a file inside the goal's own artifact tree (path-validated —
    the corpus allowlist is the goal's OWN upstream artifacts, never the wider repo)."""
    try:
        base = state.goal_dir.resolve()
        rp = path.resolve()
    except OSError:
        return False
    return rp == base or base in rp.parents


def _resolve_corpus(state: JobState) -> dict[str, str]:
    """Resolve the grounding-corpus allowlist inside the goal's own tree (FR-015 / decisions-so-far:
    the goal's OWN upstream artifacts only — `requirements.human.md`, `research_notes.human.md`,
    `exploration/summary.md` if present). Returns `{relname: text}`. The wider repo is NEVER a
    requirements source. "Upstream cannot supply" = these files don't contain it."""
    corpus: dict[str, str] = {}
    for name in _CORPUS_FILES:
        p = state.goal_dir / name
        if not _within_goal_tree(state, p) or not p.is_file():
            continue
        try:
            corpus[name] = p.read_text(encoding="utf-8")
        except OSError:
            continue
    return corpus


def _build_gapfill_prompt(state: JobState, corpus: dict[str, str]) -> str:
    gaps_yaml = "\n".join(
        f"- gap_id: {g['gap_id']}\n"
        f"  question: {json.dumps(g['question'])}\n"
        f"  section_hint: {json.dumps(g['section_title'])}"
        for g in state.open_gaps
    )
    if corpus:
        corpus_text = "\n\n".join(
            f"----- BEGIN CORPUS FILE {name} -----\n{text}\n----- END CORPUS FILE {name} -----"
            for name, text in corpus.items()
        )
    else:
        corpus_text = "(no upstream corpus files present — you can only REFUSE every gap.)"
    return (
        "Answer each open comprehension gap GROUNDED-OR-REFUSE from the grounding corpus below. "
        "Supply ONLY what the corpus LITERALLY supports, with a verbatim evidence quote; when in "
        "doubt, REFUSE (refusal is a correct answer).\n"
        f"goal_slug: {state.goal_slug}\n"
        f"\n----- BEGIN OPEN GAPS -----\n{gaps_yaml}\n----- END OPEN GAPS -----\n"
        f"\n----- BEGIN CANONICAL SOURCE -----\n{state.parsed.source_text}\n"
        "----- END CANONICAL SOURCE -----\n"
        f"\n----- BEGIN GROUNDING CORPUS (the ONLY admissible evidence) -----\n{corpus_text}\n"
        "----- END GROUNDING CORPUS -----\n"
        f"\nEmit ONE YAML list between {_GAPFILL_BEGIN} and {_GAPFILL_END}, one entry per gap, per "
        "your contract.\n"
    )


def _parse_gapfill(raw: str | None) -> list[dict] | None:
    """Extract the gapfill YAML list between the gapfill sentinels. None on a crash/garbage/no-
    sentinel output (→ every open gap resolves `unfilled-ask-failed`)."""
    if not raw:
        return None
    begin = raw.find(_GAPFILL_BEGIN)
    if begin == -1:
        return None
    end = raw.find(_GAPFILL_END, begin + len(_GAPFILL_BEGIN))
    if end == -1:
        return None
    try:
        data = yaml.safe_load(raw[begin + len(_GAPFILL_BEGIN):end])
    except yaml.YAMLError:
        return None
    if not isinstance(data, list):
        return None
    return [e for e in data if isinstance(e, dict) and e.get("gap_id")]


def run_gapfill(state: JobState) -> None:
    """Run `cast-requirements-gapfill` ONCE over ALL open gaps (once per job). Crash / timeout /
    unparseable output → `gapfill_answers` stays empty → every open gap resolves
    `unfilled-ask-failed` (the pipeline proceeds to a MARKED render; never blocks, never fabricates).
    This stage only COLLECTS the agent's claims — the trust boundary (`validate_evidence`) is a
    separate server-side stage."""
    _heartbeat(state, "run_gapfill")
    state.gapfill_answers = []
    if not state.open_gaps:
        return
    corpus = _resolve_corpus(state)
    try:
        raw = state.runner.run_agent(
            _GAPFILL_AGENT, _build_gapfill_prompt(state, corpus),
            timeout_s=_stage_timeout("run_gapfill"),
        )
    except AgentRunError as exc:
        _note(state, f"{_GAPFILL_AGENT} failed: {exc} — every open gap unfilled-ask-failed")
        return
    _write_artifact(state, "gapfill.txt", raw or "")
    answers = _parse_gapfill(raw)
    if answers is None:
        _note(state, f"{_GAPFILL_AGENT} produced unparseable output — open gaps unfilled-ask-failed")
        return
    state.gapfill_answers = answers


def _fold_for_locate(text: str) -> str:
    """Whitespace/smart-quote tolerance for the evidence locate (T2 parity): fold smart quotes/
    dashes to ASCII and collapse every whitespace run to a single space. Applied to BOTH the corpus
    text and the quote BEFORE the SHARED `verbatim_locate` runs — so tolerance is a pre-normalization
    of the inputs, NOT a second locate implementation (single-helper discipline preserved)."""
    for src, dst in _SMART_QUOTE_FOLD.items():
        text = text.replace(src, dst)
    return " ".join(text.split())


def _evidence_locates(content: str, quote: str) -> bool:
    """Does `quote` verbatim-locate in `content`? The located decision is ALWAYS made by the shared
    `verbatim_locate` (never a raw `str.find()`): an exact pass first, then a whitespace/smart-quote-
    tolerant pass over folded inputs. A substantively different quote still fails both (T2)."""
    if not quote:
        return False
    if verbatim_locate(content, quote) is not None:
        return True
    return verbatim_locate(_fold_for_locate(content), _fold_for_locate(quote)) is not None


def validate_evidence(state: JobState) -> None:
    """The trust boundary (deterministic, server-side). For each `supplied` gapfill answer, assert
    `evidence.file` is in the corpus allowlist AND `evidence.quote` verbatim-locates in that file via
    the SHARED `verbatim_locate`. A failure DEMOTES the answer (record `evidence-validation-failed`
    on the job row — zero silent failures): an ungrounded answer can NEVER reach the CR door. Each
    answer is annotated in-place with `_validated: bool`."""
    _heartbeat(state, "validate_evidence")
    corpus = _resolve_corpus(state)
    for ans in state.gapfill_answers:
        if not ans.get("supplied"):
            ans["_validated"] = False
            continue
        ev = ans.get("evidence") or {}
        ev_file, ev_quote = ev.get("file"), ev.get("quote")
        ok = (
            isinstance(ev_file, str) and ev_file in corpus
            and isinstance(ev_quote, str) and _evidence_locates(corpus[ev_file], ev_quote)
        )
        ans["_validated"] = bool(ok)
        if not ok:
            _note(
                state,
                f"evidence-validation-failed for {ans.get('gap_id')}: quote not grounded in "
                f"{ev_file!r}",
            )


# --------------------------------------------------------------------------------------
# 5b: reconciliation through the v2 gate — the FIRST real downstream emitter the roundtrip
# spec hard-deferred. The gate / policy lanes / conflict predicate / writeback / outbox / relay
# are all consumed BYTE-UNCHANGED; this stage is a *proposer* (`change_request_service.create`)
# and a *resolver of marker status* — never a new writer of canonical (FR-016 structural).
# --------------------------------------------------------------------------------------

# FIXED `.rr-gap` page status vocabulary (shared-context table) — 1:1 with the gaps-state.json
# status enum. The SERVICE owns the fixed strings (deterministic), not the LLM: the marker carries
# the gap's `question` + EXACTLY one of these. `cr-applied` has NO marker (the detail is now
# canonical and un-marks by regeneration). The `proposed_body` NEVER appears here (FR-016).
_MARKER_STATUS_TEXT = {
    "cr-proposed": "a detail is missing here — proposed upstream, awaiting review",
    "unfilled-cannot-supply": "missing — upstream could not supply it",
    "unfilled-declined": "missing — a proposed detail was declined",
    "unfilled-ask-failed": "missing from the requirements",
}

# A live fingerprint match in any of these statuses suppresses a re-propose (no CR spam). Only
# `superseded` frees re-proposal; a `rejected` match means "asked and answered" → unfilled-declined.
_LIVE_GAP_CR_STATUSES = ("applied", "conflicted", "proposed", "rejected")


def _normalize_gap_question(question: str) -> str:
    """NAMED question normalizer for the dedupe fingerprint (Plan Review CQ1): casefold → collapse
    every whitespace run → strip trailing punctuation. Folds the cosmetic re-wording the WHAT agent
    introduces across re-renders (case, spacing, a trailing '?') so the fingerprint stays stable;
    the structural key (block_refs + section) carries the real weight."""
    folded = " ".join((question or "").casefold().split())
    return folded.rstrip(".?!,;:- ")


def _gap_fingerprint(gap: dict) -> str:
    """Stable 12-hex structural fingerprint of an open gap (shared-context Dedupe schema). Keyed on
    the STRUCTURAL identity `sorted(block_refs) + " " + section_title` (primary — survives LLM
    re-wording) with the normalized `question` as a secondary component. Embedded as the CR's
    `origin_artifact_path` `#gap=<fp12>` fragment (no schema column; the gate stays unchanged)."""
    structural = " ".join(sorted(gap.get("block_refs") or [])) + " " + (gap.get("section_title") or "")
    key = structural + "\x1f" + _normalize_gap_question(gap.get("question") or "")
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def _existing_gap_cr(goal_slug: str, fp12: str, db_path) -> tuple[str, int] | None:
    """The most-relevant LIVE change-request carrying this gap fingerprint, as `(status, cr_id)`, or
    None when re-proposal is free. Filters by `goal_slug` FIRST (`idx_change_requests_goal_status`),
    THEN substring-matches the `#gap={fp12}` fragment in `origin_artifact_path` — O(CRs-per-goal),
    never a global scan (Plan Review P1). Only `proposed`/`applied`/`conflicted`/`rejected` are live;
    a sole `superseded` match returns None (re-propose allowed)."""
    fragment = f"#gap={fp12}"
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT id, status, origin_artifact_path FROM change_requests WHERE goal_slug = ?",
            (goal_slug,),
        ).fetchall()
    finally:
        conn.close()
    live: dict[str, int] = {}
    for r in rows:
        if fragment in (r["origin_artifact_path"] or "") and r["status"] in _LIVE_GAP_CR_STATUSES:
            live.setdefault(r["status"], r["id"])
    for status in _LIVE_GAP_CR_STATUSES:           # precedence: applied > conflicted > proposed > rejected
        if status in live:
            return status, live[status]
    return None


def _what_doc_job_ref(state: JobState) -> str:
    """The provenance anchor for a gap CR — the WHAT doc (job artifact) that DECLARED the gap. A
    stable, job-scoped relative path under `build/render-jobs/`; the `#gap=<fp12>` fragment is then
    appended by the emitter (the dedupe pre-check substring-matches that fragment)."""
    return f"render-jobs/{state.goal_slug}/{state.source_hash[:12]}/what-doc.md"


def _reconcile_gap(state: JobState, gap: dict, ans: dict) -> tuple[str, int | None]:
    """Reconcile ONE supplied+evidence-validated gap through the v2 gate. Dedupe first (a live
    fingerprint match suppresses a re-propose); otherwise `change_request_service.create(...)` with
    the FIXED provenance columns. Returns `(gaps_state_status, cr_id)`.

    The gate is consumed UNCHANGED: `status` is derived exactly as the route does, via
    `gate_status(kind, target_quote, policy)` — under the goal's GATE-ALL default this is always
    `"proposed"` (no FYI), so the gap lands `cr-proposed` and awaits the human gate. The mechanism
    still supports a fast-track policy (→ `applied` → `cr-applied`) so a policy change elsewhere
    keeps working."""
    fp12 = _gap_fingerprint(gap)

    # --- Dedupe (Step 5b.3): never spam the human with a re-ask of a live gap ------------------
    existing = _existing_gap_cr(state.goal_slug, fp12, state.db_path)
    if existing is not None:
        ex_status, ex_id = existing
        if ex_status == "rejected":
            _note(state, f"{gap['gap_id']}: a prior gap CR was rejected — unfilled-declined (asked and answered)")
            return "unfilled-declined", ex_id
        if ex_status == "applied":
            return "cr-applied", ex_id           # the detail is canonical — no marker
        return "cr-proposed", ex_id              # proposed / conflicted — already in flight

    # --- Propose (Step 5b.2): the FIRST real downstream emitter -------------------------------
    pc = ans.get("proposed_change") or {}
    proposed_body = (pc.get("proposed_body") or ans.get("answer") or "").strip()
    if not proposed_body:                        # nothing to propose — never create an empty CR
        _note(state, f"{gap['gap_id']}: supplied answer carried no proposed body — unfilled-cannot-supply")
        return "unfilled-cannot-supply", None
    section_hint = pc.get("section_hint") or gap.get("section_title") or None
    current = requirement_version_service.get_current(state.goal_slug, db_path=state.db_path)
    base_version = int(current["version"]) if current else 0   # READ AT EMIT TIME (conflict guard)
    try:
        cr = change_request_service.create(
            state.goal_slug,
            kind="addition",                     # LOCKED (a gap is MISSING content, never a rewrite)
            proposed_body=proposed_body,
            base_version=base_version,
            target_quote=None,                   # a pure addition touches no existing region
            section_hint=section_hint,
            author="cast-requirements-gapfill",
            author_type="agent",                 # HARD-CODED at the emitter — no spoof surface
            origin_phase="render-gapfill",
            origin_activity_id=str(state.row_id) if state.row_id is not None else None,
            origin_artifact_path=f"{_what_doc_job_ref(state)}#gap={fp12}",
            status=change_request_service.gate_status("addition", None, config.WRITEBACK_GATE_POLICY),
            db_path=state.db_path,
        )
    except Exception as exc:                     # noqa: BLE001 — a CR-store failure never blocks the render
        _note(state, f"{gap['gap_id']}: gap CR creation failed ({exc}) — unfilled-ask-failed; "
                     "next regen retries (dedupe finds no row)")
        return "unfilled-ask-failed", None
    # `applied` is only reachable under a fast-track policy (not this goal's GATE-ALL default).
    return ("cr-applied" if cr["status"] == "applied" else "cr-proposed"), cr["id"]


def emit_change_requests(state: JobState) -> None:
    """**5b emitter** — reconcile each supplied+validated gap through the v2 change-request gate and
    resolve the per-job `gaps-state.json` record + the page's `.rr-gap` markers. Per open gap, the
    single closed-enum status is:

    - no answer for the gap (gapfill crashed / unparseable)  → `unfilled-ask-failed`
    - the agent refused (`supplied: false`)                  → `unfilled-cannot-supply`
    - supplied but evidence failed server-side validation    → `unfilled-cannot-supply`
    - supplied AND evidence validated → reconcile through the gate (`_reconcile_gap`): a deduped
      `change_request_service.create` → `cr-proposed` (the GATE-ALL lane; `cr_id` recorded), a live
      fingerprint match → its standing resolution (`cr-applied` / `cr-proposed` / `unfilled-declined`).

    The record is gated by `check_gaps_state` (closed enum) before it is written. Markers carry the
    gap's `question` + EXACTLY one FIXED status string (`_MARKER_STATUS_TEXT`); the `proposed_body`
    NEVER reaches the page (FR-016 structural). The service annotates state BESIDE the agents' docs;
    it never mutates them and never writes canonical (the v2 writeback agent is the SOLE writer)."""
    _heartbeat(state, "emit_change_requests")
    answers = {a["gap_id"]: a for a in state.gapfill_answers}
    gaps_state: list[dict] = []
    markers: list[dict] = []
    for g in state.open_gaps:
        gid = g["gap_id"]
        ans = answers.get(gid)
        cr_id: int | None = None
        if ans is None:
            status = "unfilled-ask-failed"
        elif not ans.get("supplied"):
            status = "unfilled-cannot-supply"
        elif not ans.get("_validated"):
            status = "unfilled-cannot-supply"    # evidence-demoted
        else:
            status, cr_id = _reconcile_gap(state, g, ans)
        entry: dict = {"gap_id": gid, "status": status}
        if cr_id is not None:
            entry["cr_id"] = cr_id
        gaps_state.append(entry)
        if status != "cr-applied":               # cr-applied has no marker (the detail is canonical)
            markers.append({"question": g["question"], "status": _MARKER_STATUS_TEXT[status]})

    report = check_gaps_state({"gaps": gaps_state})
    if not report.passed:  # defensive: an out-of-enum status is a construction bug, not user data
        _note(state, "gaps-state failed check_gaps_state: " + "; ".join(report.violations))
    state.gaps_state = gaps_state
    state.open_gap_markers = markers
    _write_artifact(state, "gaps-state.json", json.dumps({"gaps": gaps_state}, indent=2))


# Job-row reason markers a CLEAN publish must still surface (zero silent failures) — the gap
# degradations that don't otherwise reach the row error because the render itself published clean.
_GAP_ROW_MARKERS = ("evidence-validation-failed", "unfilled-ask-failed")


def _gap_row_reason(state: JobState) -> str | None:
    """The gap-degradation notes (evidence-demotion / ask-failure) to stamp on the terminal row even
    on a clean publish. None when no gap degraded (so a gapless / fully-grounded job keeps a clean
    `error IS NULL` row)."""
    hits = [n for n in state.notes if any(m in n for m in _GAP_ROW_MARKERS)]
    return "; ".join(hits) or None


def _prior_job_artifact(state: JobState, name: str) -> str | None:
    """Read a named artifact from the PRIOR render's job dir (keyed by the recovered prior source's
    content-hash). None when no prior parsed source / the file is absent / unreadable. The prior
    source-hash IS `state.prior_parsed.content_hash` (the recovered prior source, re-hashed)."""
    if state.prior_parsed is None:
        return None
    prior_dir = Path(config.RENDER_JOBS_DIR) / state.goal_slug / state.prior_parsed.content_hash[:12]
    path = prior_dir / name
    try:
        return path.read_text(encoding="utf-8") if path.exists() else None
    except OSError as exc:
        _note(state, f"UPDATE: prior {name} unreadable ({exc})")
        return None


def _patch_what_source_hash(doc: str, new_hash: str) -> str:
    """Deterministically retarget a reused WHAT doc's `source_hash:` front-matter line to the current
    source hash — the ONE field a content-preserving edit always invalidates (`check_what_doc` asserts
    `source_hash == parsed.content_hash`). The section plan / ref mapping is left UNTOUCHED: if the
    diff actually added/removed refs the stale mapping no longer covers, `check_what_doc` still rejects
    it and the job degrades to CREATE. Line-based (no regex), first match only."""
    out: list[str] = []
    patched = False
    for line in doc.splitlines(keepends=True):
        if not patched and line.lstrip().startswith("source_hash:"):
            indent = line[: len(line) - len(line.lstrip())]
            nl = "\n" if line.endswith("\n") else ""
            out.append(f"{indent}source_hash: {new_hash}{nl}")
            patched = True
        else:
            out.append(line)
    return "".join(out)


def _reuse_prior_what(state: JobState) -> bool:
    """UPDATE-mode WHAT reuse (Step 3a.6): adopt the prior job's gated `what-doc.md` instead of
    re-running `cast-requirements-what` — a small edit must not reshuffle the section plan. The reused
    doc's `source_hash:` is deterministically retargeted to the current hash (the only field a
    content-preserving edit invalidates), then re-gated against the CURRENT parsed source: a clean gate
    → reuse (return True); otherwise (the diff added/removed refs the stale plan no longer maps
    cleanly) DEGRADE THE WHOLE JOB TO CREATE — flip `state.mode`, re-stamp the row, discard the stale
    doc — rather than render against a stale structure (return False; the caller runs the CREATE WHAT
    path).

    The richer id-map patch the plan sketches (added ref → its neighbors' section) is deferred to a
    refinement: `check_what_doc` is the correctness backstop — a stale plan that still maps every
    current ref reuses cleanly, one that doesn't degrades to CREATE."""
    doc = _prior_job_artifact(state, "what-doc.md")
    if doc and doc.strip():
        state.what_doc = _patch_what_source_hash(doc, state.source_hash)
        gate_what(state)
        if state.what_report is not None and state.what_report.passed:
            _note(state, "UPDATE: reused prior gated WHAT doc (no run_what)")
            return True
        _note(state, "UPDATE: prior WHAT doc failed gate against current source — degrading to CREATE")
    else:
        _note(state, "UPDATE: prior WHAT doc not recoverable — degrading to CREATE")
    # Degrade: the job is no longer an UPDATE. Reset WHAT + UPDATE state so the CREATE path runs
    # fresh (and `_is_update_active` is False, so run_how renders a full page, not fragments).
    state.mode = "create"
    state.what_doc = None
    state.what_report = None
    state.prior_html = None
    state.changed_refs = frozenset()
    state.update_modified_refs = frozenset()
    state.update_added_refs = frozenset()
    state.update_removed_refs = frozenset()
    state.update_unchanged_refs = frozenset()
    if state.row_id is not None:
        _update_job(state.row_id, state.db_path, mode="create")
    return False


def _reuse_prior_gaps(state: JobState) -> None:
    """UPDATE-mode gap reuse (Step 3a.6 / plan-review Decision #2 — LOAD-BEARING, not an optimization).
    Reuse the prior job's `gaps-state.json` unchanged and **SKIP `emit_change_requests` entirely**.

    Why the skip is load-bearing: the gap-CR dedupe fingerprint rides `origin_artifact_path =
    _what_doc_job_ref(state)`, keyed by the CURRENT `source_hash[:12]`. An UPDATE runs under a NEW
    source hash, so re-emitting would write a gap CR against a new provenance path the dedupe
    pre-check can't match → a DUPLICATE gap CR. Any diff that would actually CHANGE the gap set has
    already flipped the job to CREATE (WHAT reuse fell back), so reuse-without-re-emit keeps gap CRs
    idempotent. The prior render's `.rr-gap` markers ride along in the unchanged containers the splice
    preserves (3b owns marker carry-forward), so the fragment render emits no gap section here."""
    raw = _prior_job_artifact(state, "gaps-state.json")
    gaps_state: list[dict] = []
    if raw:
        try:
            gaps_state = json.loads(raw).get("gaps", [])
        except json.JSONDecodeError as exc:
            _note(state, f"UPDATE: prior gaps-state.json unparseable ({exc}) — proceeding gapless")
    state.gaps_state = gaps_state
    state.open_gap_markers = []  # carried by the splice from unchanged containers (3b); none re-rendered
    _note(state, "UPDATE: reused prior gaps-state.json, skipped emit_change_requests (Decision #2)")


def _run_gap_pipeline(state: JobState) -> None:
    """The Phase-5a gap machinery — runs ONCE per job, BETWEEN `gate_what` and the 4a quality loop.
    Ordering: probe `run_how` (harvest trailer, no QUALITY debit) → `ask_what` (bounded re-run) →
    `run_gapfill` (grounded-or-refuse) → `validate_evidence` (trust boundary) →
    `emit_change_requests` (5b: reconcile validated gaps through the v2 gate, resolve gaps-state.json
    + the `.rr-gap` markers). A gapless job costs one probe `run_how`, then the four no-op gap
    stages (no gaps → no gapfill, no CRs). Canonical is NEVER written here — the gate owns that."""
    run_how_probe(state)
    ask_what(state)
    run_gapfill(state)
    validate_evidence(state)
    emit_change_requests(state)


# --------------------------------------------------------------------------------------
# Rework mechanics (Step 4a2.3 — provenance-tagged feedback under separate headings)
# --------------------------------------------------------------------------------------
def _rework_feedback(state: JobState, verdict: CheckerVerdict | None) -> list[FeedbackItem]:
    """Build the provenance-tagged rework feedback (CQ1): deterministic structural violations
    (hard) + the checker's `rework_feedback` (quality nudges), on the SAME transport but tagged so
    the prompt renders them under separate headings."""
    items: list[FeedbackItem] = []
    if state.html_report is not None and not state.html_report.passed:
        items += [FeedbackItem(v, "structural") for v in state.html_report.violations]
    if state.what_report is not None and not state.what_report.passed:
        items += [FeedbackItem(v, "structural") for v in state.what_report.violations]
    if verdict is not None:
        items += [FeedbackItem(f, "quality") for f in verdict.rework_feedback]
    return items


def _score_history(state: JobState) -> str:
    """A one-line score history so the agent sees that regression is visible (4a2.3)."""
    scored = [r for r in state.attempts_history if r.canonical_score is not None]
    if not scored:
        return f"attempt {state.how_attempts + 1} of up to {config.QUALITY_MAX_ATTEMPTS}; no scored attempt yet."
    best = max(scored, key=lambda r: r.canonical_score)
    return (
        f"attempt {state.how_attempts + 1} of up to {config.QUALITY_MAX_ATTEMPTS}; "
        f"best so far {best.canonical_score:.2f} at attempt {best.attempt_no}."
    )


# --------------------------------------------------------------------------------------
# WHAT-escalation (Step 4a2.4 / CQ2) — intent-level comprehension miss → re-run run_what
# --------------------------------------------------------------------------------------
def _gated_tokens_in(verdict: CheckerVerdict | None) -> frozenset[str]:
    """The gated WHAT tokens (`job`/`outcome`/`scope`) named in a verdict's `missing[]`."""
    if verdict is None:
        return frozenset()
    found = set()
    for entry in verdict.missing:
        low = str(entry).lower()
        found.update(tok for tok in GATED_TOKENS if tok in low)
    return frozenset(found)


def _maybe_escalate_what(state: JobState, verdict: CheckerVerdict | None) -> None:
    """If 3 CONSECUTIVE verdicts name the SAME gated `missing[]` token, the comprehension failure is
    intent-level (not representation-level) → re-run `run_what` once with accumulated feedback, then
    `gate_what`, then resume HOW reworks. Bounded by `QUALITY_MAX_WHAT_REWORKS`.

    [CQ2] if the forced WHAT re-gen FAILS its own `gate_what`, the prior known-good WHAT is RETAINED
    (the failed re-gen discarded, NOT the good WHAT); the budget is STILL decremented; HOW reworks
    resume against the retained WHAT; NO deterministic fallback fires (a present attempt history
    already exists)."""
    tokens = _gated_tokens_in(verdict)
    common = (state.missing_streak_tokens & tokens) if state.missing_streak_tokens else tokens
    if tokens and common:
        state.missing_streak += 1
        state.missing_streak_tokens = common
    else:
        state.missing_streak = 1 if tokens else 0
        state.missing_streak_tokens = tokens

    if state.missing_streak < 3:
        return
    if state.what_reworks >= config.QUALITY_MAX_WHAT_REWORKS:
        return

    prior_doc, prior_report = state.what_doc, state.what_report
    state.what_reworks += 1  # budget decremented even if the re-gen fails its gate (CQ2)
    feedback = [FeedbackItem(
        "The render keeps failing to communicate the "
        f"{', '.join(sorted(state.missing_streak_tokens))} — this is an intent-level gap, not a "
        "layout problem. Revise the WHAT doc so each of these is unmistakable.",
        "quality",
    )]
    run_what(state, feedback=feedback)
    gate_what(state)
    if state.what_report is None or not state.what_report.passed:
        # CQ2: the re-gen failed its own gate → retain the prior known-good WHAT.
        state.what_doc, state.what_report = prior_doc, prior_report
        _note(state, "WHAT re-gen failed gate_what — retained prior WHAT (CQ2)")
    state.missing_streak = 0
    state.missing_streak_tokens = frozenset()


# --------------------------------------------------------------------------------------
# The quality loop + the terminal decision (Step 4a2.2 — the policy table, OVERRIDE baked in)
# --------------------------------------------------------------------------------------
# The loop MECHANISM (rework iteration, ranking, the policy table, the OVERRIDE) lives in
# render_common.quality_loop now (shared with the exploration render-job). This module supplies the
# requirements-specific stage bodies + terminal hooks via `_RequirementsLoopOps`, an adapter the
# generic loop drives over `JobState`. Behavior is byte-identical: the clean-publish path still
# records `_gap_row_reason`, the flagged path `_terminal_error`, and both run `_post_publish_reanchor`
# after a successful `_compare_and_publish`; the `_maybe_escalate_what` hook fires unchanged.
class _RequirementsLoopOps:
    """Bind the generic quality loop to one requirements `JobState`."""

    def __init__(self, state: JobState) -> None:
        self.state = state

    # --- ceiling knobs (read dynamically so tests can monkeypatch config) ---
    @property
    def max_attempts(self) -> int:
        return config.QUALITY_MAX_ATTEMPTS

    @property
    def structural_stop(self) -> int:
        return config.QUALITY_STRUCTURAL_STOP

    # --- stage callables ---
    def run_how(self, feedback, score_history) -> str | None:
        return run_how(self.state, feedback, score_history)

    def gate_html(self) -> None:
        gate_html(self.state)

    def run_checker(self, html: str):
        return run_checker(self.state, html)

    # --- reads off the latest gate results ---
    def structurally_valid(self) -> bool:
        return self.state.html_report is not None and self.state.html_report.passed

    def what_ok(self) -> bool:
        return self.state.what_report is not None and self.state.what_report.passed

    # --- verdict math ---
    def derive_pass(self, verdict) -> bool:
        return derive_pass(verdict)

    def canonical_score(self, verdict) -> float:
        return canonical_score(verdict)

    def gate_report(self):
        return self.state.html_report

    # --- counters (proxy onto JobState so the loop's mutations land on the real state) ---
    @property
    def how_attempts(self) -> int:
        return self.state.how_attempts

    @property
    def consecutive_structural(self) -> int:
        return self.state.consecutive_structural

    @consecutive_structural.setter
    def consecutive_structural(self, value: int) -> None:
        self.state.consecutive_structural = value

    @property
    def attempts_history(self) -> list[AttemptRecord]:
        return self.state.attempts_history

    # --- feedback builders ---
    def no_output_feedback(self) -> FeedbackItem:
        return FeedbackItem(_NO_OUTPUT_FEEDBACK, "structural")

    def rework_feedback(self, verdict) -> list[FeedbackItem]:
        return _rework_feedback(self.state, verdict)

    def score_history(self) -> str:
        return _score_history(self.state)

    # --- escalation hook (intent-level comprehension miss → re-run run_what) ---
    def maybe_escalate(self, verdict) -> None:
        _maybe_escalate_what(self.state, verdict)

    # --- terminal hooks ---
    def heartbeat(self, stage: str) -> None:
        _heartbeat(self.state, stage)

    def publish_clean(self, record: AttemptRecord) -> None:
        state = self.state
        if _compare_and_publish(state, record.html, served_by="maker",
                                human_review=False, review_reason=None):
            # 5a: even on a CLEAN publish, a gap that could not be filled (evidence-demoted or
            # ask-failed) is recorded on the row — zero silent failures. The page already marks the
            # gap honestly; the row carries the machine-readable reason.
            _finalize(state, "published", error=_gap_row_reason(state),
                      published_attempt=record.attempt_no, published_score=record.canonical_score)
            _post_publish_reanchor(state)  # 3b: ONE re-anchor for UPDATE expected misses

    def publish_flagged(self, record: AttemptRecord, *, served_by: str, reason: str) -> None:
        state = self.state
        if _compare_and_publish(state, record.html, served_by=served_by,
                                human_review=True, review_reason=reason):
            _finalize(state, "published", error=_terminal_error(state, record),
                      human_review=1, review_reason=reason,
                      published_attempt=record.attempt_no, published_score=record.canonical_score)
            _post_publish_reanchor(state)

    def publish_fallback(self, reason: str) -> None:
        _publish_fallback(self.state, reason)


def _quality_loop(state: JobState) -> None:
    """Drive the HOW rework loop (generic skeleton, requirements-bound ops). See
    render_common.quality_loop.run_quality_loop for the mechanism."""
    _run_quality_loop(_RequirementsLoopOps(state))


def decide_quality(state: JobState) -> None:
    """The terminal decision (the policy table, OVERRIDE baked in). PREFER VALID, THEN SCORE.
    Generic policy in render_common.quality_loop.decide_quality, bound to this JobState's ops."""
    _decide_quality(_RequirementsLoopOps(state))


def _terminal_error(state: JobState, chosen: AttemptRecord) -> str | None:
    """The reason recorded on a flagged terminal row — the served attempt's failing gate violations
    and any checker `error` issue descriptions (zero silent failures)."""
    parts: list[str] = []
    if chosen.gate_report is not None and not chosen.gate_report.passed:
        parts.extend(chosen.gate_report.violations)
    if not chosen.what_ok and state.what_report is not None and not state.what_report.passed:
        parts.extend(state.what_report.violations)
    if chosen.verdict is not None:
        parts.extend(i.description for i in chosen.verdict.error_issues)
    if not parts:
        parts = list(state.notes)
    return "; ".join(parts) if parts else None


def _compare_and_publish(
    state: JobState, html: str, *, served_by: str, human_review: bool, review_reason: str | None
) -> bool:
    """Compare-and-publish the chosen attempt through the shared publish seam. Re-reads the source
    hash: if it disappeared → `failed`; if it moved → `superseded` (writes nothing). Otherwise
    publishes (stamping the human-review flag) and returns True for the caller to finalize."""
    current = requirements_render_service.current_source_hash(
        state.goal_slug, goals_dir=state.goals_dir, db_path=state.db_path
    )
    if current is None:
        _finalize(state, "failed", error="source .collab.md disappeared during render")
        return False
    if current != state.source_hash:
        _finalize(state, "superseded", error=None)
        return False
    requirements_render_service.publish_maker_html(
        state.goal_slug, html, source_hash=state.source_hash, served_by=served_by,
        human_review=human_review, review_reason=review_reason,
        goals_dir=state.goals_dir, db_path=state.db_path,
    )
    return True


# ======================================================================================
# Publish-boundary re-anchor dispatch (refine-req-v3 sp3b, Step 3b.3)
# ======================================================================================
# After an UPDATE publish, the survival report's EXPECTED misses are render-space comments on
# CHANGED (modified/removed) blocks — the block was re-rendered or dropped, so the quote no longer
# places. ONE `cast-comment-reanchor` v3 dispatch (render-space hints) relocates / resolves /
# orphans them, extending 4b's version-boundary dispatch pattern to the render boundary. It runs
# AFTER `_finalize` (the row is already terminal → never reaped) so a slow/failed re-anchor never
# affects the publish; a crash or garbage verdict leaves the comments open + badged (the read-time
# `.comment-unplaced` tray surface is the honest fallback — never a retry loop).

def _container_text_for_ref(idx, ref: str | None) -> str | None:
    """The descendant text of the unit container labelled `ref` on a render index, or None. A
    render-space re-anchor hint (`prior_render_text` / `candidate_render_text`)."""
    if ref is None:
        return None
    for unit in idx.units():
        if _label_in(ref, unit.text):
            return unit.text
    return None


def _build_reanchor_prompt(state: JobState, targets: list[dict], prior_idx, cand_idx) -> str:
    """The contract-v3 (render-space) re-anchor user message: the displaced comments + both source
    versions + each comment's prior/candidate render container text. Verdicts-only (no `change_set`
    → `narration: null`); the gate already owns change emission (UPDATE skips it, Decision #2)."""
    comments_payload = []
    for c in targets:
        ref = c.get("block_ref")
        comments_payload.append({
            "id": c["id"],
            "quoted_text": c.get("quoted_text") or "",
            "section_hint": c.get("section_hint"),
            "body": c.get("body") or "",
            "block_ref": ref,
            "prior_render_text": _container_text_for_ref(prior_idx, ref),
            "candidate_render_text": _container_text_for_ref(cand_idx, ref),
        })
    old_source = state.prior_parsed.source_text if state.prior_parsed is not None else ""
    return (
        "Re-anchor these displaced render-space comments against the freshly published render "
        "(contract v3). Emit ONE bare JSON object — `narration: null` and a `verdicts` array, one "
        "verdict per input comment, per your contract. A `relocated` `new_quoted_text` MUST be a "
        "verbatim substring of the candidate render text for that comment.\n"
        f"goal_slug: {state.goal_slug}\n"
        f"\n----- BEGIN COMMENTS -----\n{json.dumps(comments_payload, indent=2)}\n"
        "----- END COMMENTS -----\n"
        f"\n----- BEGIN old_content (prior source) -----\n{old_source}\n"
        "----- END old_content -----\n"
        f"\n----- BEGIN new_content (current source) -----\n{state.parsed.source_text}\n"
        "----- END new_content -----\n"
    )


def _parse_reanchor_verdicts(raw: str | None) -> list[dict] | None:
    """Parse the re-anchor agent's bare-JSON object → its `verdicts` list. None on crash / non-JSON /
    wrong shape (→ comments stay open + badged, never a guess). Tolerant of a stray code fence."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        nl = text.find("\n")
        if nl != -1:
            text = text[nl + 1:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        obj = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None
    verdicts = obj.get("verdicts") if isinstance(obj, dict) else None
    return verdicts if isinstance(verdicts, list) else None


def _apply_reanchor_verdicts(state: JobState, verdicts: list[dict], placeable_ids: set[int]) -> None:
    """Apply each verdict through the SAME-door comment service (verdict safety unchanged). A
    `relocated` whose `new_quoted_text` does NOT place on the served render is DOWNGRADED to orphan
    (the 422 verbatim backstop, applied here at the service boundary) — a bad guess never silently
    mis-places a comment. `resolved` → resolve; `orphaned` (or any unknown verdict) → orphan."""
    served_text = container_text_index(state.html).document_text
    actor = _REANCHOR_AGENT
    for v in verdicts:
        cid = v.get("comment_id")
        if not isinstance(cid, int) or cid not in placeable_ids:
            continue
        verdict = v.get("verdict")
        try:
            if verdict == "relocated":
                quote = v.get("new_quoted_text") or ""
                if quote and quote in served_text:
                    comment_service.relocate_comment(
                        cid, quote, v.get("new_section_hint"), actor, db_path=state.db_path
                    )
                else:  # backstop: a non-present quote → orphan, never a silent mis-place
                    comment_service.orphan_comment(cid, actor, db_path=state.db_path)
            elif verdict == "resolved":
                comment_service.resolve_comment(cid, actor, db_path=state.db_path)
            else:  # "orphaned" or any unknown verdict → orphan (surfaced in the tray)
                comment_service.orphan_comment(cid, actor, db_path=state.db_path)
        except Exception as exc:  # noqa: BLE001 — one bad verdict never aborts the batch
            _note(state, f"reanchor verdict for comment {cid} could not be applied ({exc})")


def _post_publish_reanchor(state: JobState) -> None:
    """ONE `cast-comment-reanchor` v3 dispatch for the UPDATE's EXPECTED survival misses. No-op
    unless this was an UPDATE with expected misses. Crash / garbage verdict → comments stay open +
    badged (no retry loop). Runs post-`_finalize` so it never affects the (already terminal) row."""
    if not _is_update_active(state):
        return
    survival = state.last_survival or {}
    expected_ids = [c for c in survival.get("expected_misses", []) if isinstance(c, int)]
    if not expected_ids:
        return
    open_comments = comment_service.list_comments(
        state.goal_slug, state="open", db_path=state.db_path, goals_dir=state.goals_dir
    )
    by_id = {c["id"]: c for c in open_comments}
    targets = [by_id[cid] for cid in expected_ids if cid in by_id]
    if not targets:
        return
    _note(state, f"publish-boundary reanchor: dispatching for {len(targets)} expected-miss comment(s)")
    prior_idx = container_text_index(state.prior_html)
    cand_idx = container_text_index(state.html)
    prompt = _build_reanchor_prompt(state, targets, prior_idx, cand_idx)
    try:
        raw = state.runner.run_agent(
            _REANCHOR_AGENT, prompt, timeout_s=_stage_timeout("run_checker")
        )
    except AgentRunError as exc:
        _note(state, f"reanchor dispatch failed ({exc}) — {len(targets)} comment(s) stay open + badged")
        return
    _write_artifact(state, "reanchor.json", raw or "")
    verdicts = _parse_reanchor_verdicts(raw)
    if verdicts is None:
        _note(state, "reanchor produced no parseable verdicts — comments stay open + badged")
        return
    _apply_reanchor_verdicts(state, verdicts, {c["id"] for c in targets})


def _publish_fallback(state: JobState, reason: str) -> None:
    """Literal no-output → the v2 deterministic page (`status=fallback`). Honors compare-and-publish
    first (a source moved mid-job → `superseded`, not a stale fallback)."""
    current = requirements_render_service.current_source_hash(
        state.goal_slug, goals_dir=state.goals_dir, db_path=state.db_path
    )
    if current is None:
        _finalize(state, "failed", error="source .collab.md disappeared during render")
        return
    if current != state.source_hash:
        _finalize(state, "superseded", error=None)
        return
    requirements_render_service.rerender_requirements_html(
        state.goal_slug, goals_dir=state.goals_dir, db_path=state.db_path
    )
    _finalize(state, "fallback", error="; ".join(state.notes) or reason)


def _finalize(
    state: JobState, status: str, *, error: str | None,
    human_review: int = 0, review_reason: str | None = None,
    published_attempt: int | None = None, published_score: float | None = None,
) -> None:
    """Record a terminal render_jobs row — every terminal state is a row with a reason (zero silent
    failures). The four flag columns are the queryable/observability copy (Phase-5 sweep,
    post-mortem); the served-artifact envelope stamp is the status-poll read path (A2)."""
    state.terminal = status
    now = _utcnow_iso()
    _update_job(state.row_id, state.db_path, status=status, error=error,
                attempts=state.attempts, finished_at=now, heartbeat_at=now,
                human_review=human_review, review_reason=review_reason,
                published_attempt=published_attempt, published_score=published_score)


def _stage_timeout(stage: str) -> int:
    """The configured per-stage subprocess timeout (seconds). Reads config dynamically so tests can
    monkeypatch the stage list."""
    for name, secs in config.RENDER_STAGE_TIMEOUTS:
        if name == stage:
            return secs
    return 60


# ======================================================================================
# Pipeline driver + the per-job thread
# ======================================================================================
def _execute_pipeline(state: JobState) -> None:
    """Drive the full gated pipeline:
    `run_what → gate_what → run_how → gate_html → run_checker → decide_quality → publish`.

    WHAT runs once with one structural retry (Phase 3, unchanged — a WHAT-gate failure is rare and
    not what the quality loop reworks). If WHAT never produces a doc, that is a literal no-output →
    deterministic fallback (HOW is never run). Otherwise the HOW quality loop owns everything from
    `run_how` to the terminal decision.

    HOW-update-mode 3a: the job FIRST decides CREATE vs UPDATE (`_prepare_mode` — persists source.md,
    recovers the prior render, stamps the decided `mode`). When the UPDATE BEHAVIOUR is active
    (`_is_update_active` — decided UPDATE AND the flag-gate open; OFF in production until 3b) the WHAT
    doc is REUSED (no run_what) and the gap stage reuses prior state + SKIPS emit_change_requests
    (Decision #2). A WHAT-reuse miss degrades the whole job back to CREATE. While the flag-gate is
    closed this branch is never taken — production is 100% CREATE even on a decided UPDATE."""
    _prepare_mode(state)

    if _is_update_active(state):
        # UPDATE behaviour (INERT until 3b flips the flag-gate). Reuse the prior WHAT doc; on a clean
        # re-gate, reuse gap state + skip emit, then the quality loop renders changed-block fragments.
        if _reuse_prior_what(state):
            _reuse_prior_gaps(state)
            _quality_loop(state)
            return
        # WHAT reuse failed → the job degraded to CREATE inside _reuse_prior_what; fall through.

    # WHAT: run_what → gate_what (one structural retry on a gate violation).
    run_what(state)
    gate_what(state)
    if state.what_doc is not None and state.what_report is not None and not state.what_report.passed:
        run_what(state, feedback=[FeedbackItem(v, "structural") for v in state.what_report.violations])
        gate_what(state)

    if state.what_doc is None:
        # Literal no-output: the WHAT agent never produced a doc → HOW has no input to render.
        _publish_fallback(state, "; ".join(state.notes) or "WHAT agent produced no doc")
        return

    # 5a/5b: the gap machinery runs ONCE per job here — between gate_what and the quality loop. It
    # harvests/declares gaps, fills them grounded-or-refuse, validates evidence server-side, emits
    # validated gaps as change-requests through the v2 gate (5b), and writes gaps-state.json + the
    # `.rr-gap` markers. The quality loop then reworks HOW attempts against the FIXED WHAT doc + the
    # resolved gap state.
    _run_gap_pipeline(state)

    _quality_loop(state)


def _run_job_thread(state: JobState) -> None:
    """Acquire an in-flight slot (blocking — generating state shown meanwhile), run the pipeline,
    always release the slot + drop from the registry."""
    try:
        _acquire_slot(state)
        _execute_pipeline(state)
    except Exception as exc:  # noqa: BLE001 — never let a job thread die silently
        logger.exception("render job %s crashed: %s", state.key, exc)
        try:
            requirements_render_service.rerender_requirements_html(
                state.goal_slug, goals_dir=state.goals_dir, db_path=state.db_path
            )
            _finalize(state, "fallback", error=f"pipeline crash: {exc}")
        except Exception as inner:  # noqa: BLE001
            _finalize(state, "failed", error=f"pipeline crash + fallback failed: {inner}")
    finally:
        _release_slot(state)
        with _registry_lock:
            if _registry.get(state.key) is state:
                _registry.pop(state.key, None)


# ======================================================================================
# Lazy reaper (Step 3c.8 — ceiling from the configured stage-timeout list)
# ======================================================================================
def reaper_ceiling_seconds() -> int:
    """A generous (≥2×) multiple of the sum of registered stage timeouts PLUS a one-stage
    structural-retry allowance. Reads `config.RENDER_STAGE_TIMEOUTS`, so 4a/5 extend it by
    registering stages — zero formula edits."""
    stages = config.RENDER_STAGE_TIMEOUTS
    base = sum(secs for _, secs in stages)
    retry = max((secs for _, secs in stages), default=0)  # the one structural retry of a stage
    return config.RENDER_REAPER_CEILING_MULTIPLE * (base + retry)


def reap_stale_jobs(db_path=None) -> list[int]:
    """Mark every orphaned `running` render_jobs row `failed` and release any slot it leaked.

    An orphan is a `running` row whose `heartbeat_at` is older than the derived ceiling AND has no
    live thread (after a server restart the in-memory registry is empty, so the ceiling is the real
    guard). A job blocked on an in-flight slot has a *live* thread and is never reaped. The reaper
    MUST release the in-flight slot of a reaped orphan (revision a) — else a crashed-thread orphan
    leaks a slot permanently. Returns the reaped row ids. The mechanism lives in
    render_common.job_runtime; this binds the requirements ceiling (from the configured stage list)."""
    return _runtime.reap_stale_jobs(ceiling=reaper_ceiling_seconds(), db_path=db_path)


# ======================================================================================
# Entry point — the orchestrator (maker primary / deterministic fallback)
# ======================================================================================
def _lookup_family(goal_slug: str, db_path) -> str | None:
    try:
        from cast_server.services import goal_service
        goal = goal_service.get_goal(goal_slug, db_path=db_path)
        return goal.get("workflow_family") if goal else None
    except Exception:  # noqa: BLE001 — family is best-effort prompt context, never fatal
        return None


def _start_job(
    goal_slug: str, source_hash: str, parsed: ParsedRequirements, goal_dir: Path,
    goals_dir: Path | None, db_path, runner: AgentRunner | None,
) -> JobState:
    """Insert the row, build the job dir + state, register, and start the daemon thread. MUST be
    called holding `_registry_lock` (keeps single-flight atomic)."""
    job_dir = Path(config.RENDER_JOBS_DIR) / goal_slug / source_hash[:12]
    runner = runner or ProductionAgentRunner(job_dir)
    row_id = _insert_job(goal_slug, source_hash, db_path)
    state = JobState(
        key=(goal_slug, source_hash), goal_slug=goal_slug, source_hash=source_hash,
        parsed=parsed, goal_dir=goal_dir, goals_dir=goals_dir, db_path=db_path,
        runner=runner, job_dir=job_dir, family=_lookup_family(goal_slug, db_path), row_id=row_id,
    )
    thread = threading.Thread(
        target=_run_job_thread, args=(state,),
        name=f"render-job-{goal_slug}-{source_hash[:12]}", daemon=True,
    )
    state.thread = thread
    _registry[state.key] = state
    thread.start()
    return state


def request_render(
    goal_slug: str, *, runner: AgentRunner | None = None,
    goals_dir: Path | None = None, db_path=None, wait: bool = False,
) -> dict:
    """The maker-primary render orchestrator (Step 3c — the seam 3d's route + status call into).

    Resolves the source, short-circuits stubs to the deterministic prompt-to-begin render, then
    starts (or joins onto) the single-flight background job for `(goal_slug, source_hash)`. Every
    entry first runs the lazy reaper. With `wait=False` (the production page path) it returns the
    `generating` state immediately; with `wait=True` (tests / synchronous callers) it joins the job
    thread and returns the terminal status.

    Returns a small status dict: `state` (missing | stub | generating | <terminal-status>),
    `goal_slug`, and — for a started/joined job — `source_hash`, `job_id`, `status`, `started`.
    """
    reap_stale_jobs(db_path=db_path)
    goals_dir = goals_dir or GOALS_DIR
    goal_dir = requirements_render_service._resolve_goal_dir(goal_slug, goals_dir, db_path)
    source_path = goal_dir / "refined_requirements.collab.md"
    if not source_path.exists():
        return {"state": "missing", "goal_slug": goal_slug}

    parsed = parse_requirements_file(source_path)
    # Stub short-circuit BEFORE any job logic: the maker is never invoked for a stub (US1 S2).
    if is_stub(parsed):
        requirements_render_service.rerender_requirements_html(
            goal_slug, goals_dir=goals_dir, db_path=db_path
        )
        return {"state": "stub", "goal_slug": goal_slug, "served_by": "deterministic"}

    source_hash = content_hash(parsed.source_text)
    key = (goal_slug, source_hash)
    with _registry_lock:
        existing = _registry.get(key)
        if existing is not None and existing.thread is not None and existing.thread.is_alive():
            job, started = existing, False
        else:
            job = _start_job(goal_slug, source_hash, parsed, goal_dir, goals_dir, db_path, runner)
            started = True

    if wait and job.thread is not None:
        job.thread.join()

    row = get_job_row(job.row_id, db_path) if job.row_id is not None else None
    status = row["status"] if row else None
    return {
        "state": status if wait else "generating",
        "goal_slug": goal_slug,
        "source_hash": source_hash,
        "job_id": job.row_id,
        "status": status,
        "started": started,
    }
