"""The named-stage quality-loop skeleton + the terminal `decide_quality` policy table.

The GENERIC rework loop both render-jobs run: each iteration is `run_how → gate_html → run_checker`,
then the loop drives rework off the failing verdict's feedback, and `decide_quality` lands the
terminal state (clean publish / flagged best-attempt / deterministic no-output fallback). The loop
is PARAMETERIZED by a `QualityLoopOps` the render-job supplies — its stage callables, its
structural/what reads, its publish + fallback + finalize hooks, its feedback builders, and the
`QUALITY_*` ceiling knobs. The mechanism (ranking, the policy table, the OVERRIDE) is identical for
both; only the requirements/exploration-specific stage bodies differ.

The OWNER OVERRIDE baked into `decide_quality` (binding): PREFER VALID, THEN SCORE. A structurally-
valid attempt always outranks a broken one regardless of score; the deterministic page is served
ONLY on a literal no-output (zero attempts ever extracted), never to silently swap a degraded render
(surface, don't suppress). Generic over the gated-token vocabulary via the ops' `derive_pass`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class FeedbackItem:
    """One rework instruction with its provenance (CQ1). Structural items are hard, non-negotiable
    fixes (deterministic gate violations); quality items are the checker's subjective nudges. They
    ride the SAME transport but render under SEPARATE prompt headings so the HOW agent never treats
    a taste suggestion as a hard requirement or down-weights a structural correction."""

    text: str
    provenance: str  # "structural" | "quality"


@dataclass
class AttemptRecord:
    """One scored HOW attempt — the prefer-valid-then-score ranking input + the replayable
    post-mortem record. `structurally_valid` reads the structural gate; `canonical_score` is the
    code-side recompute (None when unscored)."""

    attempt_no: int
    html: str
    gate_report: Any
    what_ok: bool
    structurally_valid: bool
    verdict: Any
    unscored: bool
    canonical_score: float | None


def best_attempt(records: list[AttemptRecord]) -> AttemptRecord:
    """Best within a pool: scored over unscored, then highest canonical score, then latest."""
    return max(
        records,
        key=lambda r: (
            0 if r.unscored else 1,
            r.canonical_score if r.canonical_score is not None else -1.0,
            r.attempt_no,
        ),
    )


class QualityLoopOps(Protocol):
    """The render-job-supplied surface the generic loop drives. Requirements and exploration each
    implement this over their own JobState; the loop mechanism stays byte-identical."""

    # --- ceiling knobs (read dynamically so tests can monkeypatch config) ---
    @property
    def max_attempts(self) -> int: ...
    @property
    def structural_stop(self) -> int: ...

    # --- stage callables (one rework iteration) ---
    def run_how(self, feedback: list[FeedbackItem] | None,
                score_history: str | None) -> str | None: ...
    def gate_html(self) -> None: ...
    def run_checker(self, html: str) -> tuple[Any, bool]: ...

    # --- reads off the latest gate results ---
    def structurally_valid(self) -> bool: ...
    def what_ok(self) -> bool: ...

    # --- verdict math (binds the gated-token vocabulary) ---
    def derive_pass(self, verdict: Any) -> bool: ...
    def canonical_score(self, verdict: Any) -> float: ...
    def gate_report(self) -> Any: ...

    # --- loop bookkeeping / counters (the render-job owns the JobState) ---
    @property
    def how_attempts(self) -> int: ...
    @property
    def consecutive_structural(self) -> int: ...
    @consecutive_structural.setter
    def consecutive_structural(self, value: int) -> None: ...
    @property
    def attempts_history(self) -> list[AttemptRecord]: ...

    # --- feedback builders ---
    def no_output_feedback(self) -> FeedbackItem: ...
    def rework_feedback(self, verdict: Any) -> list[FeedbackItem]: ...
    def score_history(self) -> str: ...

    # --- escalation hook (requirements re-runs WHAT on an intent-level miss; exploration no-ops) ---
    def maybe_escalate(self, verdict: Any) -> None: ...

    # --- terminal hooks ---
    def heartbeat(self, stage: str) -> None: ...
    def publish_clean(self, record: AttemptRecord) -> None: ...
    def publish_flagged(self, record: AttemptRecord, *, served_by: str, reason: str) -> None: ...
    def publish_fallback(self, reason: str) -> None: ...


class LoopOpsBase:
    """Boilerplate base for a render-job's loop-ops adapter.

    Holds a `state` (the render-job's JobState) and implements the counter proxies + the ceiling
    knobs (read from `config.QUALITY_*` dynamically). A render-job subclasses this and implements
    ONLY the genuinely-different methods (the stage callables, the gate reads, the verdict math, the
    feedback builders, the escalation hook, the publish/fallback hooks). `state` must expose
    `how_attempts`, `consecutive_structural`, `attempts_history` (the loop mutates these in place).
    """

    def __init__(self, state: Any) -> None:
        self.state = state

    @property
    def max_attempts(self) -> int:
        import cast_server.config as config
        return config.QUALITY_MAX_ATTEMPTS

    @property
    def structural_stop(self) -> int:
        import cast_server.config as config
        return config.QUALITY_STRUCTURAL_STOP

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

    def no_output_feedback(self) -> FeedbackItem:
        # Render-jobs that want a custom no-output message override this.
        return FeedbackItem(
            "Your previous output did not contain a single well-formed render. Emit EXACTLY ONE "
            "`<!-- BEGIN RENDER -->` … `<!-- END RENDER -->` block wrapping a complete self-contained "
            "HTML document, with no markdown fences or chatty preamble around it.",
            "structural",
        )

    # --- terminal hooks: generic skeletons over render-job-supplied publish/finalize callbacks ---
    # A subclass implements `compare_and_publish(html, served_by, human_review, review_reason) ->
    # bool`, `finalize_published(record, *, human_review, review_reason)`, `publish_fallback(reason)`,
    # and may override `clean_error()` (the error string stamped on a clean row). The post-publish
    # hook (`after_publish`) is a no-op by default (requirements overrides it for the UPDATE reanchor).

    def clean_error(self) -> str | None:
        return None

    def after_publish(self) -> None:
        return None

    def compare_and_publish(self, html: str, *, served_by: str, human_review: bool,
                            review_reason: str | None) -> bool:  # pragma: no cover - overridden
        raise NotImplementedError

    def finalize_published(self, record: AttemptRecord, *, human_review: int,
                           review_reason: str | None, error: str | None) -> None:  # pragma: no cover
        raise NotImplementedError

    def publish_clean(self, record: AttemptRecord) -> None:
        if self.compare_and_publish(record.html, served_by="maker",
                                    human_review=False, review_reason=None):
            self.finalize_published(record, human_review=0, review_reason=None,
                                    error=self.clean_error())
            self.after_publish()

    def publish_flagged(self, record: AttemptRecord, *, served_by: str, reason: str) -> None:
        if self.compare_and_publish(record.html, served_by=served_by,
                                    human_review=True, review_reason=reason):
            self.finalize_published(record, human_review=1, review_reason=reason,
                                    error=self.flagged_error(record))
            self.after_publish()

    def flagged_error(self, record: AttemptRecord) -> str | None:  # pragma: no cover - overridden
        return None


def run_checker_with_retry(runner, agent_name: str, prompt: str, *, timeout_s: int,
                           parse, run_error, parse_error, on_note=None):
    """The shared checker dispatch: ONE retry on a subprocess error or a malformed verdict; a second
    failure returns `(None, True, last_raw)` (the attempt is unscored, recorded by the caller).
    `parse` turns raw stdout into a verdict; `run_error`/`parse_error` are the exception types to
    swallow-and-retry. Returns `(verdict, unscored, last_raw)`."""
    last_raw = ""
    for attempt in range(2):
        try:
            last_raw = runner.run_agent(agent_name, prompt, timeout_s=timeout_s)
            verdict = parse(last_raw)
        except (run_error, parse_error) as exc:
            if on_note is not None:
                on_note(f"{agent_name} try {attempt + 1} failed: {exc}")
            continue
        return verdict, False, last_raw
    return None, True, last_raw


def run_quality_loop(ops: QualityLoopOps) -> None:
    """Drive the HOW rework loop until a clean publish, the structural-stop, or the ceiling.

    Each iteration: `run_how → gate_html → run_checker`, then decide. A clean attempt (structurally
    valid AND `derive_pass`) publishes immediately; otherwise the failing verdict's feedback drives
    the next rework. A structural failure is just another rework, bounded by `structural_stop`
    consecutive failures (which would otherwise burn the ceiling on a degraded maker for nothing).
    """
    feedback: list[FeedbackItem] | None = None
    while ops.how_attempts < ops.max_attempts:
        score_history = ops.score_history() if feedback else None
        extracted = ops.run_how(feedback, score_history)
        ops.gate_html()

        if extracted is None:
            # A per-attempt no-output (crash / sentinel failure) is a structural failure with
            # nothing to score. Surface it as no-output feedback and rework.
            ops.consecutive_structural += 1
            if ops.consecutive_structural >= ops.structural_stop:
                break
            feedback = [ops.no_output_feedback()]
            continue

        verdict, unscored = ops.run_checker(extracted)
        structurally_valid = ops.structurally_valid()
        what_ok = ops.what_ok()
        score = None if unscored or verdict is None else ops.canonical_score(verdict)
        ops.attempts_history.append(AttemptRecord(
            attempt_no=ops.how_attempts, html=extracted, gate_report=ops.gate_report(),
            what_ok=what_ok, structurally_valid=structurally_valid,
            verdict=verdict, unscored=unscored, canonical_score=score,
        ))

        # Clean publish requires BOTH structural validity AND the checker.
        if what_ok and structurally_valid and verdict is not None and ops.derive_pass(verdict):
            ops.publish_clean(ops.attempts_history[-1])
            return

        # Not clean → track consecutive structural failures (a quality-only fail resets the streak).
        if structurally_valid and what_ok:
            ops.consecutive_structural = 0
        else:
            ops.consecutive_structural += 1

        ops.maybe_escalate(verdict)

        if ops.consecutive_structural >= ops.structural_stop:
            break
        feedback = ops.rework_feedback(verdict)

    decide_quality(ops)


def decide_quality(ops: QualityLoopOps) -> None:
    """The terminal decision (the policy table, OVERRIDE baked in). PREFER VALID, THEN SCORE.

    - No attempt ever extracted → **literal no-output** → deterministic fallback (the ONLY fallback
      trigger; never LLM-gated).
    - ≥1 structurally-VALID attempt → serve the best valid one (`served-by: maker`), flagged
      `human_review=1` with a `review_reason` (`structural_degradation` on the structural-stop,
      `checker_unavailable` if every valid attempt is unscored, else `non_convergent`).
    - Zero valid attempts but attempts WERE extracted → serve the best structurally-BROKEN attempt
      (`served-by: structural_violation`, `review_reason='structural_violation'`). A broken attempt
      can NEVER outrank a valid one on score alone."""
    ops.heartbeat("decide_quality")
    history = ops.attempts_history
    if not history:
        ops.publish_fallback("maker produced no extractable render across all attempts")
        return

    structural_stop = ops.consecutive_structural >= ops.structural_stop
    valid = [r for r in history if r.structurally_valid]
    if valid:
        chosen = best_attempt(valid)
        served_by = "maker"
        if structural_stop:
            reason = "structural_degradation"
        elif all(r.unscored for r in valid):
            reason = "checker_unavailable"
        else:
            reason = "non_convergent"
    else:
        chosen = best_attempt(history)
        served_by = "structural_violation"
        reason = "structural_violation"

    ops.publish_flagged(chosen, served_by=served_by, reason=reason)
