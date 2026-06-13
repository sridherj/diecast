"""Tests for Phase 3c — the background maker render-job pipeline (render_job_service).

The pipeline (`run_what → gate_what → run_how → gate_html → publish`) is exercised with an
**injected fake runner** (no LLM in default CI). The branches under test:

* happy path → clean maker publish (`status=published`, `served-by: maker`);
* gate-violation → one feedback retry → second violation → **BEST ATTEMPT published**
  (`status=flagged`, `served-by: structural_violation`, reason recorded) — the OWNER OVERRIDE; it
  must NOT serve the deterministic page;
* subprocess crash / timeout / empty / sentinel-extraction failure → **deterministic fallback**
  (`status=fallback`, reason recorded) — the literal no-output branch;
* **T2 (latch-deterministic):** two concurrent requests for one `(slug, hash)` start exactly one
  job; a source edited mid-job → compare-and-publish discards (`status=superseded`);
* **T3 (reaper):** a stale `running` row past the derived ceiling with no live thread is marked
  `failed`, its in-flight slot is released, and a fresh job starts;
* stub short-circuit → deterministic prompt-to-begin, the maker never invoked.

The fake-runner fixtures reuse the *proven* gate-passing source + HTML from `test_maker_gate`
(hand-crafted so source and maker markup are both under test control); a long Intent paragraph
lifts the doc over the stub threshold without disturbing the US1/FR-001/SC-001 blocks the gate
checks.
"""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CAST_SERVER_DIR = REPO_ROOT / "cast-server"
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))

from cast_server.requirements_render import parse_requirements  # noqa: E402
from cast_server.services import render_job_service as svc  # noqa: E402
from cast_server.services import requirements_render_service  # noqa: E402

BEGIN = "<!-- BEGIN RENDER -->"
END = "<!-- END RENDER -->"

# A non-stub source (>200 words via a padded Intent) whose US1/FR-001/SC-001 blocks are byte-identical
# to test_maker_gate's proven fixture, so the proven _PASS_HTML still passes check_html against it.
_PAD = " ".join(["The export must be dependable and observable across the whole nightly window."] * 20)
_SOURCE = f"""\
---
classification:
  family: new_initiative
  confidence: 0.95
---
# Demo Goal

## Intent

The team wants a dependable nightly report export so downstream data lands on time. {_PAD}

## User Stories

### US1 — export cadence

As a user I want a recurring cadence for a report export.

Acceptance: the export runs nightly.

## Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-001 | The system must export nightly. | US1 |

## Success Criteria

| ID | Criterion | Measure |
|---|---|---|
| SC-001 | Exports complete within ten minutes. | timed |
"""

# The proven gate-passing maker page (test_maker_gate._PASS_HTML).
_PASS_HTML = """\
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Demo Goal</title>
<style>.rr-unit{margin:0}</style></head>
<body data-goal-slug="demo-goal">
<main class="rr-document">
<h2>Delivery story</h2>
<section class="rr-unit">
<h3>US1 — export cadence</h3>
<p>As a user I want a recurring cadence for a report export.</p>
<details><summary>US1 — export cadence</summary>
<p>Acceptance: the export runs nightly.</p></details>
</section>
<h2>What it must do</h2>
<ul>
<li><strong>FR-001</strong> The system must export nightly.</li>
</ul>
<h2>How we will know</h2>
<ul>
<li><strong>SC-001</strong> Exports complete within ten minutes.</li>
</ul>
</main>
<script src="/static/requirements_comments.js" defer></script>
</body>
</html>
"""


def _good_what(parsed) -> str:
    """A WHAT doc that passes check_what_doc (real source hash, every ref mapped once)."""
    return (
        "---\n"
        "contract: cast-requirements-what/v1\n"
        "goal_slug: demo-goal\n"
        "family: new_initiative\n"
        f"source_hash: {parsed.content_hash}\n"
        "sections:\n"
        "  - title: Delivery cadence\n"
        "    outcome: Readers see the export rhythm.\n"
        "    block_refs: [US1, FR-001]\n"
        "  - title: Confidence measures\n"
        "    outcome: Readers see how success is proven.\n"
        "    block_refs: [SC-001]\n"
        "unmapped_refs: []\n"
        "gaps: []\n"
        "---\n\n"
        "Communication-intent prose goes here.\n"
    )


def _wrap(html: str, *, chatter: bool = True) -> str:
    """Wrap an HTML body in the render sentinels (+ optional chatter / a Phase-5 trailer that the
    strict extractor must byte-ignore)."""
    lead = "Here is the render you asked for:\n" if chatter else ""
    trailer = "\nGAPS-DETECTED: (reserved Phase-5 trailer — must be ignored)\n"
    return f"{lead}{BEGIN}\n{html}\n{END}{trailer}"


_FLAGGED_HTML = _PASS_HTML.replace(
    '<section class="rr-unit">', '<section class="rr-unit" id="leak">'
)  # an `id=` attribute → check_html fails, but the page is still extractable (best attempt).


def _verdict(*, can_state_what=True, missing=None, issues=None, rework_feedback=None, score=1.0):
    """A bare-JSON `cast-requirements-render-checker/v1` verdict string (the checker's output shape)."""
    import json
    return json.dumps({
        "contract": "cast-requirements-render-checker/v1",
        "can_state_what": can_state_what,
        "restated_job": "j", "restated_outcome": "o",
        "restated_scope": {"in": ["a"], "out": ["b"]},
        "missing": missing or [],
        "issues": issues or [],
        "score": score,
        "rework_feedback": rework_feedback or [],
    })


_PASS_VERDICT = _verdict()  # clean: can_state_what, nothing missing, zero issues → derive_pass True


# --------------------------------------------------------------------------- #
# Fake runner                                                                  #
# --------------------------------------------------------------------------- #
class FakeRunner:
    """Inject deterministic WHAT/HOW/CHECKER outputs. Each of `what` / `how` / `checker` is a list
    consumed per successive call (the last value repeats once exhausted); an item that is an
    exception instance is raised. `checker` defaults to a single PASS verdict (so the structural
    Phase-3 tests don't have to thread one through). An optional `how_latch` blocks every HOW call
    until released (T2); the checker is never latched."""

    def __init__(self, *, what, how, checker=None, gapfill=None, reanchor=None,
                 how_latch: threading.Event | None = None):
        self._what = list(what)
        self._how = list(how)
        self._checker = list(checker) if checker is not None else [_PASS_VERDICT]
        self._gapfill = list(gapfill) if gapfill is not None else [""]
        # sp3b: the publish-boundary cast-comment-reanchor v3 dispatch. Default: a no-verdict object.
        self._reanchor = list(reanchor) if reanchor is not None else ['{"verdicts": []}']
        self.what_calls = 0
        self.how_calls = 0
        self.checker_calls = 0
        self.gapfill_calls = 0
        self.reanchor_calls = 0
        self.how_latch = how_latch
        # Capture for the 4a-2 loop tests: per-agent prompts (CQ1 verbatim feedback) + call order.
        self.prompts: dict[str, list[str]] = {
            "what": [], "how": [], "checker": [], "gapfill": [], "reanchor": []
        }
        self.order: list[str] = []

    def run_agent(self, agent_name: str, user_msg: str, *, timeout_s: int) -> str:
        if agent_name == "cast-requirements-what":
            self.what_calls += 1
            self.prompts["what"].append(user_msg)
            self.order.append("what")
            return self._resolve(self._what, self.what_calls)
        if agent_name == "cast-requirements-render-checker":
            self.checker_calls += 1
            self.prompts["checker"].append(user_msg)
            self.order.append("checker")
            return self._resolve(self._checker, self.checker_calls)
        if agent_name == "cast-requirements-gapfill":
            self.gapfill_calls += 1
            self.prompts["gapfill"].append(user_msg)
            self.order.append("gapfill")
            return self._resolve(self._gapfill, self.gapfill_calls)
        if agent_name == "cast-comment-reanchor":
            self.reanchor_calls += 1
            self.prompts["reanchor"].append(user_msg)
            self.order.append("reanchor")
            return self._resolve(self._reanchor, self.reanchor_calls)
        self.how_calls += 1
        self.prompts["how"].append(user_msg)
        self.order.append("how")
        if self.how_latch is not None:
            self.how_latch.wait(timeout=10)
        return self._resolve(self._how, self.how_calls)

    @staticmethod
    def _resolve(seq, n):
        item = seq[min(n, len(seq)) - 1] if seq else ""
        if isinstance(item, BaseException):
            raise item
        return item


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def _reset_module_state():
    """Clear the single-flight registry + in-flight semaphore before and after each test."""
    svc._reset_state()
    yield
    svc._reset_state()


@pytest.fixture
def goal(tmp_path, isolated_db, monkeypatch):
    """A seeded goal with a non-stub `.collab.md`, plus a per-test render-jobs build dir.

    Returns a small namespace: slug, goals_dir, db_path, source_path, parsed, source_hash.
    """
    slug = "demo-goal"
    goals_dir = tmp_path / "goals"
    (goals_dir / slug).mkdir(parents=True)
    source_path = goals_dir / slug / "refined_requirements.collab.md"
    source_path.write_text(_SOURCE, encoding="utf-8")

    # Seed the goals row so the render_jobs FK resolves.
    from cast_server.db.connection import get_connection
    conn = get_connection(isolated_db)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, "Demo Goal", str(goals_dir / slug)),
        )
        conn.commit()
    finally:
        conn.close()

    # Per-test build dir for job artifacts (keeps them out of the repo build/).
    import cast_server.config as config
    monkey_dir = tmp_path / "render-jobs"
    monkeypatch.setattr(config, "RENDER_JOBS_DIR", monkey_dir)

    parsed = parse_requirements(_SOURCE)

    class _Goal:
        pass

    g = _Goal()
    g.slug = slug
    g.goals_dir = goals_dir
    g.db_path = isolated_db
    g.source_path = source_path
    g.parsed = parsed
    g.source_hash = parsed.content_hash
    g.jobs_dir = monkey_dir
    return g


def _published_html(g) -> str:
    return (g.goals_dir / g.slug / "refined_requirements.html").read_text(encoding="utf-8")


def _request(g, runner, **kw):
    return svc.request_render(
        g.slug, runner=runner, goals_dir=g.goals_dir, db_path=g.db_path, **kw
    )


def _survival_json(g, source_hash=None):
    """The full SurvivalReport the gate wrote for the job (defaults to the goal's original hash; pass
    a `source_hash` to read an UPDATE/edited job's dir), or None if absent."""
    import json
    p = g.jobs_dir / g.slug / (source_hash or g.source_hash)[:12] / "survival.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# --------------------------------------------------------------------------- #
# Happy path                                                                   #
# --------------------------------------------------------------------------- #
def test_happy_path_publishes_clean_maker_render(goal):
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)])
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published"
    assert row["error"] is None
    assert row["finished_at"] and row["heartbeat_at"]

    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html
    assert f"<!-- source-hash: {goal.source_hash} -->" in html
    assert "As a user I want a recurring cadence" in html  # the maker body, not a stub card
    # 5a: every job now runs ONE pre-loop gap-probe `run_how` (harvests the GAPS-DETECTED trailer;
    # C6 — does NOT debit QUALITY_MAX_ATTEMPTS) + ONE final loop attempt = 2 HOW calls. WHAT once.
    assert runner.what_calls == 1 and runner.how_calls == 2  # probe + the single clean attempt


# --------------------------------------------------------------------------- #
# OVERRIDE: structural-gate exhaustion → flagged best attempt (NOT deterministic)
# --------------------------------------------------------------------------- #
def test_gate_exhaustion_serves_flagged_best_attempt_not_deterministic(goal):
    # HOW returns extractable-but-failing HTML on every attempt (id= attribute). Default PASS
    # verdict → the checker never blocks; the structural gate keeps failing, so the loop reworks to
    # the structural-stop and lands a flagged best-attempt (the OVERRIDE: published, NOT flagged-
    # status, NOT the deterministic page).
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_FLAGGED_HTML), _wrap(_FLAGGED_HTML)])
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published"
    assert row["human_review"] == 1
    assert row["review_reason"] == "structural_violation"  # zero structurally-valid attempts
    assert row["error"] and "id=" in row["error"]  # the structural_violation reason is recorded

    html = _published_html(goal)
    # The OVERRIDE: the best (broken) attempt is served + flagged, NOT the deterministic page.
    assert "<!-- served-by: structural_violation -->" in html
    assert "<!-- human-review: 1 -->" in html
    assert 'id="leak"' in html  # the actual (degraded) maker markup was served
    assert "<!-- served-by: maker -->" not in html

    # The loop stopped at QUALITY_STRUCTURAL_STOP (3) consecutive structural failures.
    # 5a adds ONE pre-loop gap-probe run_how (not a quality attempt, never checked): 1 probe + 3
    # loop attempts = 4 HOW calls; the checker still scores only the 3 loop attempts.
    assert runner.how_calls == 4
    assert runner.checker_calls == 3  # every extractable LOOP attempt is still scored (the OVERRIDE)


def test_what_gate_exhaustion_retries_with_feedback(goal):
    # WHAT fails its gate (wrong contract) on both attempts; HOW yields a structurally-clean page.
    bad_what = _good_what(goal.parsed).replace(
        "cast-requirements-what/v1", "cast-requirements-what/v2"
    )
    runner = FakeRunner(what=[bad_what, bad_what], how=[_wrap(_PASS_HTML)])
    result = _request(goal, runner, wait=True)

    # WHAT exhausted → no CLEAN publish (clean needs gate_what to pass); the loop reworks to the
    # structural-stop and serves the best gate_html-valid attempt, flagged (surface the inconsistency).
    assert result["state"] == "published"
    assert runner.what_calls == 2  # one structural retry of run_what
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published" and row["human_review"] == 1
    assert row["review_reason"] == "structural_degradation"
    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html  # the served HTML is gate_html-valid
    assert "<!-- human-review: 1 -->" in html


# --------------------------------------------------------------------------- #
# Literal no-output → deterministic fallback                                   #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "how_seq, label",
    [
        ([svc.AgentRunError("boom"), svc.AgentRunError("boom")], "crash"),
        (["", ""], "empty"),
        (["no sentinels here at all", "still none"], "sentinel-failure"),
    ],
)
def test_no_output_serves_deterministic_fallback(goal, how_seq, label):
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=how_seq)
    result = _request(goal, runner, wait=True)

    assert result["state"] == "fallback", label
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "fallback"
    assert row["error"]  # a reason is always recorded (zero silent failures)

    html = _published_html(goal)
    # The deterministic page is UNstamped (the v2 cache format) — no served-by line.
    assert "<!-- served-by:" not in html
    assert "AUTO-GENERATED" in html


def test_what_crash_falls_back_without_running_how(goal):
    runner = FakeRunner(what=[svc.AgentRunError("what down")], how=[_wrap(_PASS_HTML)])
    result = _request(goal, runner, wait=True)

    assert result["state"] == "fallback"
    assert runner.how_calls == 0  # no WHAT doc → HOW never runs


# --------------------------------------------------------------------------- #
# T2 — single-flight + compare-and-publish (latch-deterministic)               #
# --------------------------------------------------------------------------- #
def test_single_flight_one_job_and_superseded_on_mid_job_edit(goal):
    latch = threading.Event()
    runner = FakeRunner(
        what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)], how_latch=latch
    )

    # First request starts a job; its HOW call blocks on the latch.
    r1 = _request(goal, runner, wait=False)
    assert r1["started"] is True and r1["state"] == "generating"

    # A concurrent request for the SAME (slug, hash) must NOT start a second job.
    r2 = _request(goal, runner, wait=False)
    assert r2["started"] is False
    assert r2["job_id"] == r1["job_id"]

    # Edit the source mid-job → compare-and-publish must discard the in-flight render.
    goal.source_path.write_text(_SOURCE + "\n## Extra\n\nA late edit that moves the hash.\n",
                                encoding="utf-8")

    latch.set()  # release the blocked HOW call so the pipeline reaches publish.
    job = svc._registry.get((goal.slug, goal.source_hash))
    # The job may have already drained; join via the recorded thread if still present.
    if job is not None and job.thread is not None:
        job.thread.join(timeout=10)

    row = svc.get_job_row(r1["job_id"], goal.db_path)
    assert row["status"] == "superseded"
    # Nothing was published for the stale hash.
    assert not (goal.goals_dir / goal.slug / "refined_requirements.html").exists()


# --------------------------------------------------------------------------- #
# T3 — lazy reaper releases the orphan's slot + a fresh job starts             #
# --------------------------------------------------------------------------- #
def test_reaper_marks_orphan_failed_releases_slot_and_allows_fresh_job(goal, monkeypatch):
    import cast_server.config as config
    # Tiny ceiling so a back-dated heartbeat is immediately "past ceiling".
    monkeypatch.setattr(config, "RENDER_STAGE_TIMEOUTS", [("run_what", 1), ("publish", 1)])
    monkeypatch.setattr(config, "RENDER_REAPER_CEILING_MULTIPLE", 2)

    # Insert a stale `running` row (old heartbeat) and register an orphan JobState that holds a
    # slot but whose thread never started (simulates a crashed-thread orphan).
    row_id = svc._insert_job(goal.slug, goal.source_hash, goal.db_path)
    svc._update_job(row_id, goal.db_path, heartbeat_at="2000-01-01T00:00:00+00:00")

    key = (goal.slug, goal.source_hash)
    orphan = svc.JobState(
        key=key, goal_slug=goal.slug, source_hash=goal.source_hash, parsed=goal.parsed,
        goal_dir=goal.goals_dir / goal.slug, goals_dir=goal.goals_dir, db_path=goal.db_path,
        runner=FakeRunner(what=[], how=[]), job_dir=goal.jobs_dir / "x", row_id=row_id,
    )
    orphan.thread = None  # no live thread → a genuine orphan
    with svc._registry_lock:
        svc._registry[key] = orphan
    svc._acquire_slot(orphan)
    assert key in svc.slots_held()

    reaped = svc.reap_stale_jobs(db_path=goal.db_path)

    assert row_id in reaped
    row = svc.get_job_row(row_id, goal.db_path)
    assert row["status"] == "failed"
    assert "reaped" in row["error"]
    assert key not in svc.slots_held()  # revision a: the leaked slot was released

    # A fresh job can now start and publish (the reaper unblocked the path).
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)])
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"


def test_reaper_skips_live_thread_jobs(goal):
    """A `running` row past the ceiling but with a LIVE thread is not an orphan — never reaped."""
    import cast_server.config as config
    row_id = svc._insert_job(goal.slug, goal.source_hash, goal.db_path)
    svc._update_job(row_id, goal.db_path, heartbeat_at="2000-01-01T00:00:00+00:00")

    key = (goal.slug, goal.source_hash)
    live_thread = threading.Thread(target=lambda: threading.Event().wait(2), daemon=True)
    live_thread.start()
    state = svc.JobState(
        key=key, goal_slug=goal.slug, source_hash=goal.source_hash, parsed=goal.parsed,
        goal_dir=goal.goals_dir / goal.slug, goals_dir=goal.goals_dir, db_path=goal.db_path,
        runner=FakeRunner(what=[], how=[]), job_dir=goal.jobs_dir / "y", row_id=row_id,
        thread=live_thread,
    )
    with svc._registry_lock:
        svc._registry[key] = state

    reaped = svc.reap_stale_jobs(db_path=goal.db_path)
    assert row_id not in reaped
    assert svc.get_job_row(row_id, goal.db_path)["status"] == "running"
    live_thread.join(timeout=3)


# --------------------------------------------------------------------------- #
# Stub short-circuit + missing source                                         #
# --------------------------------------------------------------------------- #
def test_stub_short_circuits_to_deterministic_without_invoking_maker(goal):
    goal.source_path.write_text(
        "---\nclassification:\n  family: generic\n---\n# Tiny\n\n## Intent\n\nToo short.\n",
        encoding="utf-8",
    )
    runner = FakeRunner(what=["SHOULD NOT BE CALLED"], how=["SHOULD NOT BE CALLED"])
    result = _request(goal, runner, wait=True)

    assert result["state"] == "stub"
    assert runner.what_calls == 0 and runner.how_calls == 0  # maker never invoked for a stub
    assert (goal.goals_dir / goal.slug / "refined_requirements.html").exists()


def test_missing_source_returns_missing(goal):
    goal.source_path.unlink()
    result = _request(goal, FakeRunner(what=[], how=[]), wait=True)
    assert result["state"] == "missing"


# --------------------------------------------------------------------------- #
# Phase 5d — read-only flagged-renders list (honest degraded-page surface)     #
# --------------------------------------------------------------------------- #
def test_list_flagged_renders_returns_only_flagged_rows(goal):
    """`list_flagged_renders` surfaces every `human_review=1` render with its flag
    columns (reason/score) and the slug for linking — and only those rows."""
    clean = svc._insert_job(goal.slug, "hash-clean", goal.db_path)
    svc._update_job(clean, goal.db_path, status="published", human_review=0,
                    published_score=0.95, finished_at="2026-06-12T10:00:00+00:00")
    flagged = svc._insert_job(goal.slug, "hash-flagged", goal.db_path)
    svc._update_job(flagged, goal.db_path, status="published", human_review=1,
                    review_reason="structural_violation", published_score=0.90,
                    published_attempt=3, finished_at="2026-06-12T11:00:00+00:00")

    rows = svc.list_flagged_renders(db_path=goal.db_path)

    assert [r["id"] for r in rows] == [flagged]  # the clean publish is excluded
    row = rows[0]
    assert row["goal_slug"] == goal.slug
    assert row["review_reason"] == "structural_violation"
    assert row["published_score"] == 0.90
    assert "human_review" not in row or row.get("human_review") in (1, None)


def test_list_flagged_renders_empty_when_no_flags(goal):
    """No flagged renders → empty list (the list section renders nothing — additive)."""
    row_id = svc._insert_job(goal.slug, goal.source_hash, goal.db_path)
    svc._update_job(row_id, goal.db_path, status="published", human_review=0)
    assert svc.list_flagged_renders(db_path=goal.db_path) == []


# --------------------------------------------------------------------------- #
# sp4b-1 — the comment-survival gate widening of gate_html (DECISION #10 OVERRIDE)
# --------------------------------------------------------------------------- #
# The maker keeps FR-001's label but drops its carried text → check_html carriage AND the
# survival gate both fail for the comment anchored to "The system must export nightly.".
_SURVIVAL_MISS_HTML = _PASS_HTML.replace(
    "<li><strong>FR-001</strong> The system must export nightly.</li>",
    "<li><strong>FR-001</strong></li>",
)


def _add_comment(g, quote: str, *, body: str = "look here", served_render_html: str | None = None) -> int:
    """Create a comment. `served_render_html` (sp2) lets a test resolve the render-space `block_ref`
    deterministically (the comment is minted against THAT render); omitted → no served render at
    creation → `block_ref=None` (a cross-boundary / displaced render-space comment)."""
    from cast_server.services import comment_service
    row = comment_service.create_comment(
        g.slug, quote, None, body, "tester", "human", db_path=g.db_path,
        served_render_html=served_render_html,
    )
    return row["id"]


def test_in_block_survival_miss_merges_and_serves_flagged_best_attempt(goal):
    """OVERRIDE branch: an in-block survival miss merges into the EXISTING structural channel →
    one structural retry → on exhaustion `publish()` serves the best attempt + structural_violation
    flag (NOT the deterministic page). The merged reason carries the comment-specific survival
    violation string (proving the merge — check_html alone never names a comment id)."""
    # sp2/sp3b: the comment is minted against the served render (_PASS_HTML) so its render-space
    # block_ref resolves to FR-001. The re-render DROPS FR-001's text → a render-space survival miss
    # on an UNCHANGED block (CREATE) = a structural violation that merges into the structural channel.
    cid = _add_comment(goal, "The system must export nightly.", served_render_html=_PASS_HTML)
    runner = FakeRunner(
        what=[_good_what(goal.parsed)],
        how=[_wrap(_SURVIVAL_MISS_HTML), _wrap(_SURVIVAL_MISS_HTML)],
    )
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published" and row["human_review"] == 1
    assert row["review_reason"] == "structural_violation"
    # The survival-specific (comment-named) violation rode into the structural reason → MERGE proven.
    assert row["error"] and f"comment {cid}" in row["error"] and "FR-001" in row["error"]

    html = _published_html(goal)
    # OVERRIDE: best attempt served + flagged, NOT swapped for the deterministic page. The serve
    # carries the maker's OWN markup ("Delivery story" is a maker heading the deterministic page
    # never emits), stamped structural_violation.
    assert "<!-- served-by: structural_violation -->" in html
    assert "<!-- served-by: maker -->" not in html
    assert "Delivery story" in html  # the degraded maker markup was served, not the deterministic page

    surv = _survival_json(goal)
    assert surv is not None
    assert cid in surv["unplaced"] and not surv["passed"]
    assert any(f"comment {cid}" in v for v in surv["violations"])
    assert runner.how_calls == 4  # 1 pre-loop gap-probe + 3 loop attempts to the structural-stop


def test_cross_boundary_only_miss_publishes_clean_maker(goal):
    """A comment whose ONLY miss is cross-boundary (not within any single block's anchorable text,
    absent from the DOM) never blocks: both gates pass → clean maker publish. The miss is still
    recorded in survival.json (surfaced read-time via the badge), never a violation."""
    cid = _add_comment(goal, "a quote that lives in no single source block at all")
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)])
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html

    surv = _survival_json(goal)
    assert surv is not None
    assert surv["passed"] is True              # cross-boundary never flips passed
    assert surv["violations"] == []            # cross-boundary never a violation
    assert cid in surv["unplaced"]             # but it IS surfaced, not silently dropped


def test_comment_created_mid_job_is_included_at_gate_stage(goal):
    """Mirror of Phase 3 T2 (latch-deterministic): a comment created AFTER job start but BEFORE the
    `gate_html` stage entry is included in the survival check — proving the fetch reads at the gate
    stage (re-read per attempt, Decision #9), not at job start."""
    import time
    latch = threading.Event()
    runner = FakeRunner(
        what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)], how_latch=latch
    )

    r = _request(goal, runner, wait=False)
    assert r["started"] is True

    # Wait until the job is blocked inside run_how (HOW reached) — strictly before gate_html.
    deadline = time.time() + 10
    while runner.how_calls < 1 and time.time() < deadline:
        time.sleep(0.01)
    assert runner.how_calls == 1

    # Create the comment NOW (mid-job, post-start, pre-gate) then let the pipeline proceed.
    cid = _add_comment(goal, "The system must export nightly.")
    latch.set()

    job = svc._registry.get((goal.slug, goal.source_hash))
    if job is not None and job.thread is not None:
        job.thread.join(timeout=10)

    surv = _survival_json(goal)
    assert surv is not None
    assert cid in surv["placed"]  # the mid-job comment was fetched at the gate stage and placed


def test_survival_json_written_on_clean_pass_no_render_jobs_column(goal):
    """`survival.json` lands in the job artifact dir after a `gate_html` pass, and NO `render_jobs`
    column was added/written by this sub-phase (survival observability is file-only — 4a property
    untouched)."""
    _add_comment(goal, "The system must export nightly.")
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)])
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"

    surv = _survival_json(goal)
    assert surv is not None and set(surv) == {
        "passed", "violations", "unplaced", "placed", "expected_misses"
    }

    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert "survival" not in row  # no survival column smuggled onto render_jobs
    assert "unplaced" not in row


# --------------------------------------------------------------------------- #
# Reaper ceiling derives from the configured stage list (no magic constant)    #
# --------------------------------------------------------------------------- #
def test_reaper_ceiling_derives_from_stage_timeout_list(monkeypatch):
    import cast_server.config as config
    monkeypatch.setattr(config, "RENDER_STAGE_TIMEOUTS",
                        [("run_what", 100), ("run_how", 200), ("publish", 10)])
    monkeypatch.setattr(config, "RENDER_REAPER_CEILING_MULTIPLE", 3)
    # 3 * (sum=310 + worst-stage retry=200) = 3 * 510 = 1530.
    assert svc.reaper_ceiling_seconds() == 1530


# --------------------------------------------------------------------------- #
# sp5a — the gap contract & the upstream-ask loop                             #
# --------------------------------------------------------------------------- #
# Corpus that grounds GAP-01's answer. Includes a smart-apostrophe span for the T2 parity case.
_CORPUS_TEXT = (
    "The export is sourced from the nightly Postgres replica at 02:00 UTC; "
    "it's the system's source of truth for downstream data.\n"
)
_GAP_Q = "What is the upstream data source for the export?"
_GAPS_ONE = (
    "\n"
    "  - gap_id: GAP-01\n"
    "    section_title: Delivery cadence\n"
    "    block_refs: [FR-001]\n"
    f"    question: {_GAP_Q}\n"
    "    why_it_matters: A reader cannot trust the export without its source.\n"
)
# A HOW render that carries the open gap's `.rr-gap` marker (passes gap-marker correspondence).
_GAP_MARKED_HTML = _PASS_HTML.replace(
    '<main class="rr-document">',
    '<main class="rr-document">\n'
    f'<div class="rr-gap"><p>{_GAP_Q}</p><p>proposed upstream, awaiting review</p></div>',
)
# A real HOW `GAPS-DETECTED` trailer (outside the sentinels) — the "HOW asks WHAT" channel.
_HOW_TRAILER = (
    f"{BEGIN}\n{_PASS_HTML}\n{END}\n"
    "<!-- GAPS-DETECTED\n"
    "- section_title: Delivery cadence\n"
    f"  question: {_GAP_Q}\n"
    "  why_it_matters: A reader cannot trust the export without its source.\n"
    "-->\n"
)


def _gapped_what(parsed, gaps_yaml=_GAPS_ONE) -> str:
    return _good_what(parsed).replace("gaps: []\n", f"gaps: {gaps_yaml}\n")


def _gf_supplied(gap_id="GAP-01", quote="sourced from the nightly Postgres replica",
                 file="requirements.human.md") -> str:
    return (
        f"- gap_id: {gap_id}\n"
        "  supplied: true\n"
        '  answer: "The export is sourced from the nightly Postgres replica."\n'
        "  evidence:\n"
        f'    file: "{file}"\n'
        f'    quote: "{quote}"\n'
        "  proposed_change:\n"
        "    kind: addition\n"
        '    section_hint: "Delivery cadence"\n'
        '    proposed_body: "The export is sourced from the nightly Postgres replica."\n'
    )


def _gf_refused(gap_id="GAP-01", reason="the corpus does not state it") -> str:
    return f"- gap_id: {gap_id}\n  supplied: false\n  reason: \"{reason}\"\n"


def _gapfill_doc(*entries: str) -> str:
    return svc._GAPFILL_BEGIN + "\n" + "".join(entries) + svc._GAPFILL_END + "\n"


def _write_corpus(g, text=_CORPUS_TEXT, name="requirements.human.md") -> None:
    (g.goals_dir / g.slug / name).write_text(text, encoding="utf-8")


def _gaps_state(g):
    p = g.jobs_dir / g.slug / g.source_hash[:12] / "gaps-state.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _job_state(g, runner, **kw):
    """A bare JobState for unit-testing individual gap stages (row_id=None → no DB writes)."""
    job_dir = g.jobs_dir / g.slug / g.source_hash[:12]
    return svc.JobState(
        key=(g.slug, g.source_hash), goal_slug=g.slug, source_hash=g.source_hash,
        parsed=g.parsed, goal_dir=g.goals_dir / g.slug, goals_dir=g.goals_dir,
        db_path=g.db_path, runner=runner, job_dir=job_dir, row_id=None, **kw,
    )


def test_what_declared_gap_flows_to_gaps_state_cr_proposed(goal):
    """A WHAT-declared gap, grounded by the corpus and evidence-validated, lands `cr-proposed` with a
    REAL `cr_id` in gaps-state.json — 5b's emitter creates the change-request through the v2 gate (one
    `kind="addition"` row, GATE-ALL → `proposed`) — and the render carries its `.rr-gap` marker. The
    deeper emit/provenance/dedupe/convergence coverage lives in `test_gap_reconciliation.py`."""
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],  # probe (no trailer), then marked render
        gapfill=[_gapfill_doc(_gf_supplied())],
    )
    result = _request(goal, runner, wait=True)

    assert result["state"] == "published"
    assert runner.gapfill_calls == 1  # gapfill ran ONCE over the open gap
    gs = _gaps_state(goal)
    assert [g["gap_id"] for g in gs["gaps"]] == ["GAP-01"]
    assert gs["gaps"][0]["status"] == "cr-proposed"
    assert isinstance(gs["gaps"][0]["cr_id"], int)  # 5b: the real CR id, not the 5a provisional None
    # The served render carries the gap marker (the question, never the answer).
    html = _published_html(goal)
    assert _GAP_Q in html
    assert "Postgres replica" not in html  # the ANSWER never reaches the page (FR-016)
    # 5b: EXACTLY ONE change-request row was created (the gap CR, through the gate).
    from cast_server.db.connection import get_connection
    conn = get_connection(goal.db_path)
    try:
        n = conn.execute("SELECT COUNT(*) AS c FROM change_requests").fetchone()["c"]
    finally:
        conn.close()
    assert n == 1


def test_gapfill_refusal_lands_unfilled_cannot_supply(goal):
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],
        gapfill=[_gapfill_doc(_gf_refused())],
    )
    _request(goal, runner, wait=True)
    gs = _gaps_state(goal)
    assert gs["gaps"] == [{"gap_id": "GAP-01", "status": "unfilled-cannot-supply"}]


@pytest.mark.parametrize("gapfill_out", [svc.AgentRunError("gapfill down"), "garbage no sentinels"])
def test_gapfill_crash_or_garbage_lands_unfilled_ask_failed(goal, gapfill_out):
    """A gapfill crash / unparseable output → every open gap `unfilled-ask-failed`; the pipeline
    proceeds to a marked render (never blocks, never fabricates)."""
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],
        gapfill=[gapfill_out],
    )
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"  # proceeds to a (marked) render, never blocks
    gs = _gaps_state(goal)
    assert gs["gaps"] == [{"gap_id": "GAP-01", "status": "unfilled-ask-failed"}]


def test_fabricated_evidence_demotes_to_cannot_supply(goal):
    """A `supplied` answer whose quote does NOT verbatim-locate in the cited file is demoted to
    `unfilled-cannot-supply`, and `evidence-validation-failed` is recorded on the job row."""
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],
        gapfill=[_gapfill_doc(_gf_supplied(quote="sourced from the nightly MySQL cluster"))],
    )
    result = _request(goal, runner, wait=True)
    gs = _gaps_state(goal)
    assert gs["gaps"] == [{"gap_id": "GAP-01", "status": "unfilled-cannot-supply"}]
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["error"] and "evidence-validation-failed" in row["error"]


def test_evidence_file_outside_allowlist_demotes(goal):
    """Citing a file that is not in the corpus allowlist (even if the quote text exists somewhere)
    fails validation → demoted. The wider repo is never a requirements source."""
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],
        gapfill=[_gapfill_doc(_gf_supplied(file="README.md"))],
    )
    _request(goal, runner, wait=True)
    gs = _gaps_state(goal)
    assert gs["gaps"] == [{"gap_id": "GAP-01", "status": "unfilled-cannot-supply"}]


# --- T2: verbatim-locate parity (the trust-boundary locate semantics, pinned) ------------- #
@pytest.mark.parametrize("quote", [
    "sourced from the nightly  Postgres replica",   # whitespace-only difference (double space)
    "it’s the system’s source of truth",            # smart-quote-only difference
])
def test_T2_whitespace_or_smartquote_variant_validates(goal, quote):
    """A quote differing from the corpus ONLY by whitespace/smart-quote MUST validate via the
    shared verbatim_locate (tolerant fold) → the gap reaches `cr-proposed`."""
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],
        gapfill=[_gapfill_doc(_gf_supplied(quote=quote))],
    )
    _request(goal, runner, wait=True)
    gs = _gaps_state(goal)
    assert gs["gaps"][0]["status"] == "cr-proposed"


def test_T2_substantively_different_quote_demotes(goal):
    """A substantively different quote (not just whitespace/smart-quote) MUST demote."""
    _write_corpus(goal)
    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],
        gapfill=[_gapfill_doc(_gf_supplied(quote="sourced from a wholly different system entirely"))],
    )
    _request(goal, runner, wait=True)
    assert _gaps_state(goal)["gaps"][0]["status"] == "unfilled-cannot-supply"


# --- the HOW-asks-WHAT trailer → exactly ONE ask_what re-run (GAPFILL_ASK_ROUNDS=1) -------- #
def test_how_trailer_triggers_exactly_one_what_rerun(goal):
    """The probe harvests a HOW `GAPS-DETECTED` trailer → exactly ONE `ask_what` WHAT re-run
    (GAPFILL_ASK_ROUNDS=1). The re-run confirms the gap into `gaps[]`; gapfill then answers it."""
    _write_corpus(goal)
    # WHAT pass 1: no gaps. The probe's trailer triggers ask_what → WHAT pass 2 declares GAP-01.
    runner = FakeRunner(
        what=[_good_what(goal.parsed), _gapped_what(goal.parsed)],
        how=[_HOW_TRAILER, _wrap(_GAP_MARKED_HTML)],  # probe carries the trailer; then marked render
        gapfill=[_gapfill_doc(_gf_supplied())],
    )
    _request(goal, runner, wait=True)
    # WHAT ran exactly twice: the initial pass + the single ask_what re-run (not more).
    assert runner.what_calls == 2
    assert runner.gapfill_calls == 1
    assert _gaps_state(goal)["gaps"][0]["status"] == "cr-proposed"


# --- C6 / A2 counter independence (unit-level, on the stage functions directly) ----------- #
def test_C6_probe_run_how_does_not_debit_quality_attempts(goal):
    """The pre-loop gap-probe `run_how` harvests the trailer but NEVER touches `how_attempts`
    (QUALITY_MAX_ATTEMPTS budget) — C6."""
    runner = FakeRunner(what=[], how=[_HOW_TRAILER])
    state = _job_state(goal, runner, what_doc=_good_what(goal.parsed))
    svc.run_how_probe(state)
    assert state.gaps_trailer and state.gaps_trailer[0]["question"] == _GAP_Q  # trailer harvested
    assert state.how_attempts == 0  # C6: the probe did NOT debit the quality-attempt budget
    assert runner.how_calls == 1


def test_A2_ask_what_does_not_debit_what_reworks_and_caps_at_budget(goal):
    """`ask_what` re-runs WHAT on its OWN counter (`ask_rounds`), never debiting
    `QUALITY_MAX_WHAT_REWORKS`; a second trailer in the same job does NOT trigger a second re-run
    (GAPFILL_ASK_ROUNDS=1) — A2."""
    runner = FakeRunner(what=[_gapped_what(goal.parsed)], how=[])
    state = _job_state(goal, runner, what_doc=_good_what(goal.parsed))
    state.gaps_trailer = [{"section_title": "Delivery cadence", "question": _GAP_Q, "why_it_matters": "x"}]

    svc.ask_what(state)
    assert state.ask_rounds == 1
    assert state.what_reworks == 0          # A2: the in-loop WHAT-rework budget is untouched
    assert runner.what_calls == 1
    assert state.open_gaps and state.open_gaps[0]["gap_id"] == "GAP-01"  # re-run confirmed the gap

    # A second ask_what (a second trailer) must NOT re-run WHAT again — the round budget is spent.
    svc.ask_what(state)
    assert state.ask_rounds == 1
    assert runner.what_calls == 1


def test_gapless_job_writes_empty_gaps_state_and_no_gapfill(goal):
    """A clean (gapless) job still writes a valid (empty) gaps-state.json and NEVER calls gapfill."""
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)])
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"
    assert runner.gapfill_calls == 0
    assert _gaps_state(goal) == {"gaps": []}


# --------------------------------------------------------------------------- #
# HOW-update-mode 3a: two-mode plumbing (mode decision, recovery, inert UPDATE) #
# --------------------------------------------------------------------------- #
def _job_dir(g, source_hash):
    return g.jobs_dir / g.slug / source_hash[:12]


def _edit_source(g, extra="One more dependability note about the nightly export window."):
    """Append a sentence to the Intent narrative (a non-ref block) → a small changed-set that leaves
    US1 / FR-001 / SC-001 intact, so the proven _PASS_HTML + _good_what still gate-pass. Returns the
    new parsed doc (its content_hash is the new source_hash)."""
    text = g.source_path.read_text(encoding="utf-8")
    text = text.replace(
        "so downstream data lands on time.",
        f"so downstream data lands on time. {extra}",
    )
    g.source_path.write_text(text, encoding="utf-8")
    return parse_requirements(text)


def _edit_fr_source(g, new_text="The system must export nightly and verifiably."):
    """Edit FR-001's description cell — a REF-BEARING block — so UPDATE fires (no ref-less change).
    US1 / SC-001 stay byte-identical → a single modified ref (`FR-001`). Returns the new parsed doc."""
    text = g.source_path.read_text(encoding="utf-8")
    text = text.replace(
        "| FR-001 | The system must export nightly. | US1 |",
        f"| FR-001 | {new_text} | US1 |",
    )
    g.source_path.write_text(text, encoding="utf-8")
    return parse_requirements(text)


def _fragment(ref: str, inner: str) -> str:
    """One HOW UPDATE-mode RR-FRAGMENT block (byte-aligned with `block_splice.parse_fragments`)."""
    return f'<!-- RR-FRAGMENT ref="{ref}" -->\n{inner}\n<!-- /RR-FRAGMENT -->'


def test_first_render_stamps_mode_create_and_persists_recovery_artifacts(goal):
    """A first render has no recoverable prior → mode=create. The recovery inputs land in the job dir:
    source.md at job start, what-doc.md at the gate_what pass (making _what_doc_job_ref real)."""
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)])
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"

    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["mode"] == "create"  # no prior render → CREATE, stamped on the row

    jd = _job_dir(goal, goal.source_hash)
    assert (jd / "source.md").read_text(encoding="utf-8") == goal.parsed.source_text
    assert (jd / "what-doc.md").exists()  # persisted at the gate_what pass


def test_refless_block_edit_degrades_to_create(goal):
    """sp3b: a change to a REF-LESS block (the Intent narrative — no anchor label in the render)
    cannot be keyed by the splice, so `_prepare_mode` degrades the job to CREATE (owner principle:
    every UPDATE precondition failure degrades to CREATE, noted, never errored)."""
    r1 = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)])
    assert _request(goal, r1, wait=True)["state"] == "published"

    new_parsed = _edit_source(goal)  # edits the ref-less Intent prose
    r2 = FakeRunner(what=[_good_what(new_parsed)], how=[_wrap(_PASS_HTML)])
    result = svc.request_render(
        goal.slug, runner=r2, goals_dir=goal.goals_dir, db_path=goal.db_path, wait=True
    )
    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["mode"] == "create"  # ref-less change → degrade to CREATE, full fresh re-render
    assert r2.what_calls >= 1 and r2.how_calls >= 2  # the CREATE path ran (run_what + gap-probe + loop)


def test_build_how_update_section_carries_fragment_subcontract(goal):
    """The UPDATE prompt section (1a verdict FAIL → deterministic-splice) asks HOW for CHANGED
    fragments only via the RR-FRAGMENT protocol, names the splice mechanism, and inlines the prior
    render + changed-set — byte-aligned with `block_splice.parse_fragments`."""
    new_parsed = _edit_fr_source(goal)
    state = _job_state(goal, FakeRunner(what=[], how=[]))
    state.parsed = new_parsed
    state.source_hash = new_parsed.content_hash
    state.prior_parsed = goal.parsed
    state.prior_html = "<html><!-- prior render --></html>"
    state.update_modified_refs = frozenset({"FR-001"})

    section = svc._build_how_update_section(state)
    assert "UPDATE MODE" in section
    assert "deterministic-splice" in section
    assert "RR-FRAGMENT" in section          # the fragment delimiter protocol
    assert "FR-001" in section               # the changed ref to render
    assert "prior render" in section.lower()
    # The CREATE prompt (mode unset) does NOT carry it.
    create_prompt = svc._build_how_prompt(_job_state(goal, FakeRunner(what=[], how=[])))
    assert "UPDATE MODE" not in create_prompt


# --------------------------------------------------------------------------- #
# HOW-update-mode 3b: the flip — live UPDATE splice + publish-boundary reanchor #
# --------------------------------------------------------------------------- #
# The new FR-001 body (a REWORD that does NOT contain the old quote) + its UPDATE fragment.
_FR_REWORD = "Nightly report delivery is mandatory."
_FR_FRAGMENT = _fragment("FR-001", f"<li><strong>FR-001</strong> {_FR_REWORD}</li>")


def _publish_prior(goal):
    """Job 1: a clean maker publish of _PASS_HTML — the prior render a later UPDATE recovers."""
    r1 = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(_PASS_HTML)])
    assert _request(goal, r1, wait=True)["state"] == "published"
    assert "<!-- served-by: maker -->" in _published_html(goal)


def test_update_publishes_maker_keeps_unchanged_byte_identical(goal):
    """An UPDATE over an edited (ref-bearing) bug_fix-shaped doc publishes served_by=maker; the
    splice keeps the UNCHANGED unit containers (US1, SC-001) byte-identical to the prior render and
    swaps only the modified FR-001 unit. WHAT is reused (no run_what), gap emit skipped."""
    _publish_prior(goal)
    # The unchanged SC-001 unit's exact bytes on the prior published render (the splice must preserve).
    sc1_unit = "<li><strong>SC-001</strong> Exports complete within ten minutes.</li>"
    assert sc1_unit in _published_html(goal)

    new_parsed = _edit_fr_source(goal, _FR_REWORD)
    r2 = FakeRunner(what=[_good_what(new_parsed)], how=[_wrap(_FR_FRAGMENT)])
    result = svc.request_render(
        goal.slug, runner=r2, goals_dir=goal.goals_dir, db_path=goal.db_path, wait=True
    )
    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["mode"] == "update" and row["status"] == "published" and row["human_review"] == 0

    html = _published_html(goal)
    assert "<!-- served-by: maker -->" in html
    assert _FR_REWORD in html                       # the modified unit was re-rendered
    assert "The system must export nightly." not in html   # old FR-001 bytes gone
    assert sc1_unit in html                          # SC-001 kept byte-identical (splice guarantee)
    assert "As a user I want a recurring cadence" in html  # US1 kept byte-identical
    assert html.count("<!-- AUTO-GENERATED") == 1    # exactly ONE envelope (no double-wrap)
    assert r2.what_calls == 0                         # UPDATE reuses the prior WHAT doc
    assert r2.reanchor_calls == 0                     # no expected misses → no reanchor dispatch


def test_update_unchanged_block_comment_survives_structurally(goal):
    """A comment on an UNCHANGED block (SC-001) places on the served UPDATE render — survival is
    structural by the byte-identity splice guarantee; it never blocks the publish or routes to
    reanchor."""
    _publish_prior(goal)
    cid = _add_comment(goal, "Exports complete within ten minutes.", served_render_html=_PASS_HTML)

    new_parsed = _edit_fr_source(goal, _FR_REWORD)
    r2 = FakeRunner(what=[_good_what(new_parsed)], how=[_wrap(_FR_FRAGMENT)])
    result = svc.request_render(
        goal.slug, runner=r2, goals_dir=goal.goals_dir, db_path=goal.db_path, wait=True
    )
    assert result["state"] == "published"
    surv = _survival_json(goal, new_parsed.content_hash)
    assert surv is not None and cid in surv["placed"]
    assert surv["passed"] and surv["expected_misses"] == []
    assert r2.reanchor_calls == 0
    # The comment stays open + placed (not displaced) — list_comments confirms it places on the render.
    from cast_server.services import comment_service
    rows = comment_service.list_comments(goal.slug, state="open", db_path=goal.db_path,
                                          goals_dir=goal.goals_dir)
    assert any(c["id"] == cid and c["displaced"] is False for c in rows)


def test_update_modified_block_comment_relocated_by_publish_boundary_dispatch(goal):
    """A comment on the MODIFIED block (FR-001) becomes an EXPECTED survival miss → the ONE
    publish-boundary cast-comment-reanchor v3 dispatch relocates it to a verbatim span of the new
    render (never silently dropped)."""
    _publish_prior(goal)
    cid = _add_comment(goal, "The system must export nightly.", served_render_html=_PASS_HTML)

    new_parsed = _edit_fr_source(goal, _FR_REWORD)
    # The reanchor agent relocates the comment to a verbatim substring of the new FR-001 render.
    reanchor_verdict = json.dumps({
        "narration": None,
        "verdicts": [{
            "comment_id": cid, "verdict": "relocated",
            "new_quoted_text": _FR_REWORD, "new_section_hint": "Functional Requirements",
            "confidence": 0.9, "reasoning": "FR-001 reworded; same requirement."
        }],
    })
    r2 = FakeRunner(
        what=[_good_what(new_parsed)], how=[_wrap(_FR_FRAGMENT)], reanchor=[reanchor_verdict]
    )
    result = svc.request_render(
        goal.slug, runner=r2, goals_dir=goal.goals_dir, db_path=goal.db_path, wait=True
    )
    assert result["state"] == "published"
    surv = _survival_json(goal, new_parsed.content_hash)
    assert surv is not None and cid in surv["expected_misses"]
    assert surv["passed"]                        # an expected miss never flips passed → clean publish
    assert r2.reanchor_calls == 1                # exactly ONE publish-boundary dispatch

    from cast_server.services import comment_service
    row = comment_service.get_comment(cid, db_path=goal.db_path)
    assert row["state"] == "open" and row["quoted_text"] == _FR_REWORD   # relocated, still open


def test_update_reanchor_dispatch_failure_leaves_comments_open_and_badged(goal):
    """The publish-boundary reanchor SUBPROCESS crash → the comment stays open + badged (displaced),
    no retry loop. The publish itself already succeeded (the row is terminal before reanchor runs)."""
    _publish_prior(goal)
    cid = _add_comment(goal, "The system must export nightly.", served_render_html=_PASS_HTML)

    new_parsed = _edit_fr_source(goal, _FR_REWORD)
    r2 = FakeRunner(
        what=[_good_what(new_parsed)], how=[_wrap(_FR_FRAGMENT)],
        reanchor=[svc.AgentRunError("reanchor subprocess crashed")],
    )
    result = svc.request_render(
        goal.slug, runner=r2, goals_dir=goal.goals_dir, db_path=goal.db_path, wait=True
    )
    assert result["state"] == "published"        # publish succeeded despite the reanchor crash
    assert r2.reanchor_calls == 1                # ONE attempt, no retry loop

    from cast_server.services import comment_service
    rows = comment_service.list_comments(goal.slug, state="open", db_path=goal.db_path,
                                          goals_dir=goal.goals_dir)
    # The comment stays OPEN and displaced (badged read-time) — never silently dropped or relocated.
    target = next(c for c in rows if c["id"] == cid)
    assert target["state"] == "open" and target["displaced"] is True


def test_create_paraphrased_render_publishes_clean_no_verbatim_flag(goal):
    """CREATE (the unedited doc) with a maker page that PARAPHRASES FR-001's leaf text publishes a
    CLEAN maker render — the verbatim-carriage flag is gone (the flip). Anchor labels + DOM hold."""
    paraphrased = _PASS_HTML.replace(
        "<li><strong>FR-001</strong> The system must export nightly.</li>",
        "<li><strong>FR-001</strong> A reworded, more readable nightly-export requirement.</li>",
    )
    runner = FakeRunner(what=[_good_what(goal.parsed)], how=[_wrap(paraphrased)])
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"
    row = svc.get_job_row(result["job_id"], goal.db_path)
    assert row["status"] == "published" and row["human_review"] == 0   # clean, NOT flagged
    assert "<!-- served-by: maker -->" in _published_html(goal)
