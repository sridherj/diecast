"""The exploration WHAT→HOW→checker render-job (exploration-pipeline-nxm sub-phase 4).

A PARALLEL, lean clone of the requirements `render_job_service` maker pipeline, exploration-shaped.
Consumes 3a's N×M markdown substrate under `goals/{slug}/exploration/` (one playbook per step +
per-(step,hat) research notes + a summary) and produces ONE polished, self-contained
`exploration.html` laying out each step's opinionated POV with the DISTINCT hat takes beneath it
(never blended — FR-017 criterion 3), landed atomically with an AUTO-GENERATED + source-digest +
served-by envelope (inherits the 2b viewer + 3b commenting for free).

Reuses the REAL shared core (`render_common`): runner seam, sentinel contract, quality-loop +
`decide_quality`, verdict base, atomic write, `content_hash`. Supplies ONLY exploration specifics:
`ExplorationJobState`, the corpus loader, the source-digest, the three prompt builders + three stage
functions, an exploration verdict, the deterministic fallback, the publish helper, the entrypoint.
NO `ParsedRequirements`, NO UPDATE mode, NO gap machinery.

Terminal states mirror requirements (OWNER OVERRIDE): clean publish / flagged best-attempt (surface,
don't suppress) / deterministic fallback ONLY on literal no-output. A DEGRADED step (missing/
placeholder playbook OR zero hat notes) is marked, never dropped — the WHAT doc carries the degraded
status, the HOW page renders an explicit marker, and the checker's criterion-1 judges against the
APPLICABLE hat set so a degraded step cannot false-pass.
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cast_server.config as config
from cast_server.config import GOALS_DIR
from cast_server.render_common.agent_runner import AgentRunError, AgentRunner, ProductionAgentRunner
from cast_server.render_common.atomic import _atomic_write
from cast_server.render_common.job_runtime import (
    build_envelope,
    finalize_job,
    heartbeat,
    stage_timeout,
    write_artifact,
)
from cast_server.render_common.job_runtime import get_job_row  # noqa: F401 — re-exported for callers
from cast_server.render_common.job_runtime import insert_job as _insert_job
from cast_server.render_common.quality_loop import (
    AttemptRecord,
    FeedbackItem,
    LoopOpsBase,
    run_checker_with_retry,
)
from cast_server.render_common.quality_loop import decide_quality as _decide_quality
from cast_server.render_common.quality_loop import run_quality_loop as _run_quality_loop
from cast_server.render_common.sentinel import _BEGIN_SENTINEL, _END_SENTINEL, extract_render
from cast_server.render_common.verdict import CheckerVerdictError
from cast_server.exploration_render import prompts as _prompts
from cast_server.exploration_render.corpus import load_exploration_corpus
from cast_server.exploration_render.verdict import (
    ExplorationVerdict,
    canonical_score,
    derive_pass,
    parse_exploration_verdict,
)

logger = logging.getLogger(__name__)

_WHAT_AGENT = "cast-exploration-what"
_HOW_AGENT = "cast-exploration-how"
_CHECKER_AGENT = "cast-exploration-render-checker"

_AUTO_GENERATED_HEADER = (
    "<!-- AUTO-GENERATED: Read-only render of the exploration md substrate. Do not edit. -->"
)
_SOURCE_DIGEST_PREFIX = "<!-- source-digest: "
_SOURCE_DIGEST_SUFFIX = " -->"

_NO_OUTPUT_FEEDBACK = (
    "Your previous output did not contain a single well-formed render. Emit EXACTLY ONE "
    f"`{_BEGIN_SENTINEL}` … `{_END_SENTINEL}` block wrapping a complete self-contained HTML "
    "document, with no markdown fences or chatty preamble around it."
)


# Job state
@dataclass
class ExplorationJobState:
    """One exploration render job: identity, the loaded md corpus per step, the hat matrix, the daemon/runtime handles, and the accumulating quality-loop outputs."""

    goal_slug: str
    source_digest: str
    steps: list[dict]          # [{nn, slug, name, playbook_text, hat_notes:[...], summary_text, degraded}]
    hat_matrix: dict[str, list[str]]   # step-slug -> applicable hat_ids
    summary_text: str
    goal_dir: Path
    goals_dir: Path | None
    db_path: Path | None
    runner: AgentRunner
    job_dir: Path
    row_id: int | None = None
    # pipeline outputs
    attempts: int = 0
    what_doc: str | None = None
    what_ok_flag: bool = False
    how_raw: str | None = None
    html: str | None = None
    html_ok_flag: bool = False
    html_violations: tuple[str, ...] = ()
    notes: list[str] = field(default_factory=list)
    terminal: str | None = None
    # quality-loop counters
    how_attempts: int = 0
    consecutive_structural: int = 0
    attempts_history: list[AttemptRecord] = field(default_factory=list)


# Prompt builders live in exploration_render.prompts (forked, with provenance); aliased here so the
# call sites + the test surface (`_build_*_prompt`) resolve.
_build_what_prompt = _prompts.build_what_prompt
_build_how_prompt = _prompts.build_how_prompt
_build_checker_prompt = _prompts.build_checker_prompt


# ===== Named pipeline stages (thin wrappers over the shared job_runtime helpers) =====
def _heartbeat(state: ExplorationJobState, stage: str) -> None:
    heartbeat(state.row_id, state.db_path, state.attempts)


def _note(state: ExplorationJobState, msg: str) -> None:
    state.notes.append(msg)
    logger.info("exploration render %s: %s", state.goal_slug, msg)


def _write_artifact(state: ExplorationJobState, name: str, content: str) -> None:
    write_artifact(state.job_dir, name, content)


def _stage_timeout(stage: str) -> int:
    return stage_timeout(stage, config.RENDER_STAGE_TIMEOUTS)


def run_what(state: ExplorationJobState, feedback: list[FeedbackItem] | None = None) -> None:
    """Run `cast-exploration-what` once → `state.what_doc`. A crash/empty leaves any prior doc."""
    _heartbeat(state, "run_what")
    state.attempts += 1
    n = state.attempts
    try:
        raw = state.runner.run_agent(_WHAT_AGENT, _build_what_prompt(state, feedback),
                                     timeout_s=_stage_timeout("run_what"))
    except AgentRunError as exc:
        _note(state, f"{_WHAT_AGENT} attempt {n} failed: {exc}")
        return
    _write_artifact(state, f"what-attempt-{n}.md", raw or "")
    if raw and raw.strip():
        state.what_doc = raw
    else:
        _note(state, f"{_WHAT_AGENT} attempt {n} produced empty output")


def gate_what(state: ExplorationJobState) -> None:
    """Structural gate on the WHAT doc: it parses (JSON/YAML-ish front matter present) AND carries the exploration contract shape — every step named, each present cell mapped under its step's hat list with a status, distinct (not blended)."""
    _heartbeat(state, "gate_what")
    if state.what_doc is None:
        state.what_ok_flag = False
        return
    ok, violations = _check_what_doc(state)
    state.what_ok_flag = ok
    _write_artifact(state, "gate_what.json", json.dumps({"passed": ok, "violations": violations}, indent=2))


def _check_what_doc(state: ExplorationJobState) -> tuple[bool, list[str]]:
    """Structural shape check (no LLM)."""
    doc = state.what_doc or ""
    low = doc.lower()
    violations: list[str] = []
    for s in state.steps:
        if s["slug"] not in doc and s["name"].lower() not in low:
            violations.append(f"step {s['slug']} not named in the WHAT doc")
        if s["degraded"] and "degrad" not in low and "dropped" not in low:
            violations.append(f"degraded step {s['slug']} carries no degraded/dropped status")
        for h in s["hat_notes"]:
            if h["status"] == "present" and h["hat_id"] not in doc:
                violations.append(f"surviving hat {h['hat_id']} of step {s['slug']} not mapped")
    return (not violations), violations


def run_how(state: ExplorationJobState, feedback: list[FeedbackItem] | None = None,
            score_history: str | None = None) -> str | None:
    """Run `cast-exploration-how` once → the extractable render (or None on crash/no-sentinel)."""
    _heartbeat(state, "run_how")
    if state.what_doc is None:
        _note(state, f"{_HOW_AGENT} skipped — no WHAT doc to render")
        return None
    state.attempts += 1
    state.how_attempts += 1
    n = state.how_attempts
    try:
        raw = state.runner.run_agent(_HOW_AGENT, _build_how_prompt(state, feedback, score_history),
                                     timeout_s=_stage_timeout("run_how"))
    except AgentRunError as exc:
        _note(state, f"{_HOW_AGENT} attempt {n} failed: {exc}")
        return None
    state.how_raw = raw
    extracted = extract_render(raw)
    _write_artifact(state, f"attempt-{n}.html", extracted if extracted is not None else (raw or ""))
    if extracted is not None:
        state.html = extracted
        return extracted
    _note(state, f"{_HOW_AGENT} attempt {n}: no extractable render (sentinel failure)")
    return None


def gate_html(state: ExplorationJobState) -> None:
    """Structural gate: sentinels already extracted; assert self-contained (`<head>`/`<style>`) and one-unit-one-container for selectable hat takes (US7 — at least one container per present hat)."""
    _heartbeat(state, "gate_html")
    if state.html is None:
        state.html_ok_flag = False
        state.html_violations = ()
        return
    html = state.html
    low = html.lower()
    violations: list[str] = []
    if "<head" not in low or "<style" not in low:
        violations.append("page is not self-contained (missing <head>/<style>)")
    # One-unit-one-container: each present hat take must appear in some container element so a
    # selection yields a clean quoted_text (3b commenting). Heuristic: the hat_id label appears.
    for s in state.steps:
        for h in s["hat_notes"]:
            if h["status"] == "present" and h["hat_id"] not in html:
                violations.append(
                    f"present hat {h['hat_id']} (step {s['slug']}) has no selectable container")
    state.html_ok_flag = not violations
    state.html_violations = tuple(violations)
    _write_artifact(state, "gate_html.json",
                    json.dumps({"passed": state.html_ok_flag, "violations": violations}, indent=2))


def run_checker(state: ExplorationJobState, html: str) -> tuple[ExplorationVerdict | None, bool]:
    """Run `cast-exploration-render-checker` over one attempt → `(verdict, unscored)` (ONE retry)."""
    _heartbeat(state, "run_checker")
    n = state.how_attempts
    verdict, unscored, last_raw = run_checker_with_retry(
        state.runner, _CHECKER_AGENT, _build_checker_prompt(state, html),
        timeout_s=_stage_timeout("run_checker"), parse=parse_exploration_verdict,
        run_error=AgentRunError, parse_error=CheckerVerdictError,
        on_note=lambda m: _note(state, m))
    if verdict is not None:
        _write_artifact(state, f"attempt-{n}.verdict.json", json.dumps({
            "contract": verdict.contract, "missing": list(verdict.missing),
            "hat_coverage_ok": verdict.hat_coverage_ok, "pov_legible": verdict.pov_legible,
            "distinctness_ok": verdict.distinctness_ok, "visual_ok": verdict.visual_ok,
            "canonical_score": canonical_score(verdict), "derive_pass": derive_pass(verdict),
        }, indent=2))
        return verdict, False
    _write_artifact(state, f"attempt-{n}.verdict.json",
                    json.dumps({"unscored": True, "raw": last_raw[:4000]}, indent=2))
    return None, True


def _rework_feedback(state: ExplorationJobState, verdict: ExplorationVerdict | None) -> list[FeedbackItem]:
    items: list[FeedbackItem] = []
    items += [FeedbackItem(v, "structural") for v in state.html_violations]
    if verdict is not None:
        items += [FeedbackItem(f, "quality") for f in verdict.rework_feedback]
    return items


def _score_history(state: ExplorationJobState) -> str:
    scored = [r for r in state.attempts_history if r.canonical_score is not None]
    if not scored:
        return f"attempt {state.how_attempts + 1} of up to {config.QUALITY_MAX_ATTEMPTS}; no scored attempt yet."
    best = max(scored, key=lambda r: r.canonical_score)
    return (f"attempt {state.how_attempts + 1} of up to {config.QUALITY_MAX_ATTEMPTS}; "
            f"best so far {best.canonical_score:.2f} at attempt {best.attempt_no}.")


# Publish + fallback + finalize (reuse render_common._atomic_write)
def publish_exploration_html(slug: str, html: str, *, source_digest: str, served_by: str,
                             human_review: bool = False, review_reason: str | None = None,
                             goals_dir: Path | None = None, db_path: Path | None = None) -> Path:
    """Write the AUTO-GENERATED + source-digest + served-by (+ human-review/review-reason) envelope atomically to `goals/{slug}/exploration/exploration.html`."""
    goals_dir = goals_dir or GOALS_DIR
    target = goals_dir / slug / "exploration" / "exploration.html"
    lines = build_envelope(
        _AUTO_GENERATED_HEADER,
        digest_line=f"{_SOURCE_DIGEST_PREFIX}{source_digest}{_SOURCE_DIGEST_SUFFIX}",
        served_by=served_by, human_review=human_review, review_reason=review_reason,
    )
    _atomic_write(target, "\n".join(lines) + f"\n{html}")
    return target


def render_exploration_fallback(state: ExplorationJobState) -> str:
    """A trivial deterministic md-concatenation-to-HTML, served ONLY on literal no-output (parity with the requirements deterministic fallback)."""
    import html as _h
    parts = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>",
             "<title>Exploration</title><style>body{font-family:system-ui;max-width:60rem;"
             "margin:2rem auto;padding:0 1rem}section{margin:2rem 0}.rr-hat{border-left:3px solid "
             "#ccc;padding-left:.75rem;margin:.5rem 0}.rr-dropped{color:#a00}</style></head><body>",
             "<main class='rr-document'><h1>Exploration</h1>"]
    for s in state.steps:
        parts.append(f"<section class='rr-step'><h2>{_h.escape(s['name'])}</h2>")
        if s["degraded"]:
            parts.append("<p class='rr-dropped'>This step is degraded "
                         "(placeholder playbook or no hat notes) — attempted, dropped.</p>")
        parts.append(f"<pre>{_h.escape(s['playbook_text'][:2000])}</pre>")
        for hnote in s["hat_notes"]:
            cls = "rr-hat rr-dropped" if hnote["status"] != "present" else "rr-hat"
            label = f"{hnote['hat_id']} ({hnote['status']})"
            body = _h.escape(hnote["text"][:1000]) or "attempted, dropped"
            parts.append(f"<div class='{cls}'><strong>{_h.escape(label)}</strong><p>{body}</p></div>")
        parts.append("</section>")
    parts.append("</main></body></html>")
    return "".join(parts)


def _finalize(state: ExplorationJobState, status: str, *, error: str | None,
              human_review: int = 0, review_reason: str | None = None,
              published_attempt: int | None = None, published_score: float | None = None) -> None:
    state.terminal = status
    finalize_job(state.row_id, state.db_path, status, error=error, attempts=state.attempts,
                 human_review=human_review, review_reason=review_reason,
                 published_attempt=published_attempt, published_score=published_score)


def _current_digest(state: ExplorationJobState) -> str | None:
    """Re-read the md set's digest right now (compare-and-publish guard). None if the tree vanished."""
    expl = state.goal_dir / "exploration"
    if not expl.is_dir():
        return None
    _, _, _, digest = load_exploration_corpus(state.goal_dir)
    return digest


def _compare_and_publish(state: ExplorationJobState, html: str, *, served_by: str,
                         human_review: bool, review_reason: str | None) -> bool:
    """Re-read the digest: gone → `failed`; moved → `superseded` (writes nothing). Else publish."""
    current = _current_digest(state)
    if current is None:
        _finalize(state, "failed", error="exploration md tree disappeared during render")
        return False
    if current != state.source_digest:
        _finalize(state, "superseded", error=None)
        return False
    publish_exploration_html(state.goal_slug, html, source_digest=state.source_digest,
                             served_by=served_by, human_review=human_review,
                             review_reason=review_reason, goals_dir=state.goals_dir,
                             db_path=state.db_path)
    return True


def _publish_fallback(state: ExplorationJobState, reason: str) -> None:
    current = _current_digest(state)
    if current is None:
        _finalize(state, "failed", error="exploration md tree disappeared during render")
        return
    if current != state.source_digest:
        _finalize(state, "superseded", error=None)
        return
    publish_exploration_html(state.goal_slug, render_exploration_fallback(state),
                             source_digest=state.source_digest, served_by="deterministic",
                             goals_dir=state.goals_dir, db_path=state.db_path)
    _finalize(state, "fallback", error="; ".join(state.notes) or reason)


def _terminal_error(state: ExplorationJobState, chosen: AttemptRecord) -> str | None:
    parts: list[str] = list(state.html_violations) if not chosen.structurally_valid else []
    if chosen.verdict is not None:
        parts.extend(i.description for i in chosen.verdict.error_issues)
        parts.extend(f"criterion failed: {tok}" for tok in chosen.verdict.missing)
    if not parts:
        parts = list(state.notes)
    return "; ".join(parts) if parts else None


# Quality-loop ops adapter (binds the generic loop to ExplorationJobState)
class _ExplorationLoopOps(LoopOpsBase):
    def run_how(self, feedback, score_history) -> str | None:
        return run_how(self.state, feedback, score_history)

    def gate_html(self) -> None:
        gate_html(self.state)

    def run_checker(self, html: str):
        return run_checker(self.state, html)

    def structurally_valid(self) -> bool:
        return self.state.html_ok_flag

    def what_ok(self) -> bool:
        return self.state.what_ok_flag

    def derive_pass(self, verdict) -> bool:
        return derive_pass(verdict)

    def canonical_score(self, verdict) -> float:
        return canonical_score(verdict)

    def gate_report(self) -> Any:
        return {"passed": self.state.html_ok_flag, "violations": list(self.state.html_violations)}

    def no_output_feedback(self) -> FeedbackItem:
        return FeedbackItem(_NO_OUTPUT_FEEDBACK, "structural")

    def rework_feedback(self, verdict) -> list[FeedbackItem]:
        return _rework_feedback(self.state, verdict)

    def score_history(self) -> str:
        return _score_history(self.state)

    def maybe_escalate(self, verdict) -> None:
        return None  # exploration has no WHAT-escalation (no gap/intent re-run machinery)

    def heartbeat(self, stage: str) -> None:
        _heartbeat(self.state, stage)

    # Publish/finalize through the LoopOpsBase skeletons (publish_clean/publish_flagged inherited).
    def compare_and_publish(self, html, *, served_by, human_review, review_reason) -> bool:
        return _compare_and_publish(self.state, html, served_by=served_by,
                                    human_review=human_review, review_reason=review_reason)

    def finalize_published(self, record, *, human_review, review_reason, error) -> None:
        _finalize(self.state, "published", error=error, human_review=human_review,
                  review_reason=review_reason, published_attempt=record.attempt_no,
                  published_score=record.canonical_score)

    def flagged_error(self, record) -> str | None:
        return _terminal_error(self.state, record)

    def publish_fallback(self, reason: str) -> None:
        _publish_fallback(self.state, reason)


def decide_quality(state: ExplorationJobState) -> None:
    """Terminal decision (generic policy bound to ExplorationJobState)."""
    _decide_quality(_ExplorationLoopOps(state))


# Pipeline driver + entrypoint
def _execute_pipeline(state: ExplorationJobState) -> None:
    """`run_what → gate_what → run_how → gate_html → run_checker → decide_quality → publish`."""
    run_what(state)
    gate_what(state)
    if state.what_doc is not None and not state.what_ok_flag:
        run_what(state, feedback=[FeedbackItem(
            "The WHAT doc failed its structural gate — name every step, carry each surviving hat's "
            "hat_id distinctly, and mark every degraded step's dropped status.", "structural")])
        gate_what(state)
    if state.what_doc is None:
        _publish_fallback(state, "; ".join(state.notes) or "WHAT agent produced no doc")
        return
    _run_quality_loop(_ExplorationLoopOps(state))


def request_exploration_render(goal_slug: str, *, runner: AgentRunner | None = None,
                               goals_dir: Path | None = None, db_path=None,
                               wait: bool = False) -> dict:
    """Entrypoint (default A — callable by the 3a Workflow final stage as a background job)."""
    goals_dir = goals_dir or GOALS_DIR
    goal_dir = goals_dir / goal_slug
    expl = goal_dir / "exploration"
    if not expl.is_dir():
        return {"state": "missing", "goal_slug": goal_slug}

    steps, hat_matrix, summary_text, digest = load_exploration_corpus(goal_dir)
    if not steps:
        return {"state": "missing", "goal_slug": goal_slug, "reason": "no exploration steps found"}

    job_dir = Path(config.RENDER_JOBS_DIR) / goal_slug / ("exploration-" + digest[:12])
    runner = runner or ProductionAgentRunner(job_dir)
    row_id = _insert_job(goal_slug, digest, db_path)
    state = ExplorationJobState(
        goal_slug=goal_slug, source_digest=digest, steps=steps, hat_matrix=hat_matrix,
        summary_text=summary_text, goal_dir=goal_dir, goals_dir=goals_dir, db_path=db_path,
        runner=runner, job_dir=job_dir, row_id=row_id,
    )

    def _run() -> None:
        try:
            _execute_pipeline(state)
        except Exception as exc:  # noqa: BLE001 — never let the job thread die silently
            logger.exception("exploration render %s crashed: %s", goal_slug, exc)
            try:
                publish_exploration_html(goal_slug, render_exploration_fallback(state),
                                         source_digest=digest, served_by="deterministic",
                                         goals_dir=goals_dir, db_path=db_path)
                _finalize(state, "fallback", error=f"pipeline crash: {exc}")
            except Exception as inner:  # noqa: BLE001
                _finalize(state, "failed", error=f"pipeline crash + fallback failed: {inner}")

    if wait:
        _run()
    else:
        threading.Thread(target=_run, name=f"exploration-render-{goal_slug}", daemon=True).start()

    row = get_job_row(row_id, db_path) if row_id is not None else None
    status = row["status"] if row else None
    return {
        "state": status if wait else "generating", "goal_slug": goal_slug,
        "source_digest": digest, "job_id": row_id, "status": status,
    }
