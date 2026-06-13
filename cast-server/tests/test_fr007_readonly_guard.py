"""FR-007 guard: the requirements file is byte-canonical and is NEVER mutated.

Three enforcement legs:
  * Byte-identity — sha256 of the fixture is identical before and after a full parse +
    version-snapshot round-trip (a snapshot copies *into* the DB; the file is untouched).
  * Spec-kit shape — ``bin/cast-spec-checker`` exits 0 on the fixture, run as a subprocess so
    the canon grammar checker (never imported, never modified) validates the frozen file.
  * Sole-mutator (Phase 5) — after the ONE sanctioned mutation (the
    ``cast-requirements-writeback`` apply), the file changed *only* the target region, and NO other
    code path (render / rerender / parse / version snapshot) mutates it. The structural complement:
    the apply module has **no whole-file overwrite path** — ``Path.write_text`` / ``save_artifact``
    never appear as executable code (only as forbidding prose), so US7's silent-drift bug cannot
    recur by construction. The writer is the only mutator, and it is surgical.

There is no prior ``test_us7_spec_kit_shape.py`` in this repo — this module establishes the
subprocess-checker pattern. ``REPO_ROOT`` is ``parents[2]`` from ``cast-server/tests/`` (verified).
"""
from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path

from cast_server.db.connection import get_connection, init_db
from cast_server.requirements_render import parse_requirements, parse_requirements_file
from cast_server.requirements_render.diff_render import render_diff
from cast_server.services import change_request_service
from cast_server.services import comment_service
from cast_server.services import requirement_version_service as version_service
from cast_server.services import requirements_render_service

# Phase 5b: the demo-goal gap-fill pipeline fixtures (imported, not forked) for the read-only
# extension — a full gap-fill run that emits a CR must still leave canonical byte-identical.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)
from test_render_job_service import (  # noqa: E402
    _GAP_MARKED_HTML,
    _PASS_HTML,
    _gapfill_doc,
    _gapped_what,
    _gaps_state,
    _gf_supplied,
    _wrap,
    _write_corpus,
    FakeRunner,
    goal,  # noqa: F401  (fixture)
    _request,
    _reset_module_state,  # noqa: F401  (autouse fixture — resets the render registry per test)
)

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "refine_requirements_v2"
    / "refined_requirements.collab.md"
)

# cast-server/tests/<file> -> parents[0]=tests, [1]=cast-server, [2]=repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "bin" / "cast-spec-checker"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_goal(db_path: Path, slug: str) -> None:
    """Insert the parent goals row so the requirement_versions FK resolves."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, "FR-007 guard goal", slug),
        )
        conn.commit()
    finally:
        conn.close()


def test_parse_and_snapshot_never_mutate_the_file(tmp_path):
    before = _sha256(FIXTURE)

    db_path = tmp_path / "guard.db"
    init_db(db_path)
    _seed_goal(db_path, "fr007-guard")

    parsed = parse_requirements_file(FIXTURE)
    row = version_service.create_snapshot(
        "fr007-guard", parsed.source_text, created_by="test", db_path=db_path
    )
    assert row["version"] == 1  # snapshot landed in the DB (proves we exercised the write path)

    after = _sha256(FIXTURE)
    assert before == after, "parse + snapshot must not mutate the byte-canonical file (FR-007)"


def test_rerender_html_never_mutates_the_collab_source(tmp_path):
    """The day HTML generation lands, FR-007 still holds: generating the read-only `.html`
    render reads the canonical `.collab.md` and never writes it.

    We copy the frozen fixture into a tmp goal dir, point ``rerender_requirements_html`` at
    it (so the real fixture on disk is never touched at all), generate the render, and assert
    the source `.collab.md` bytes are byte-identical before/after — and that the generated
    `.html` actually landed (proving we exercised the write path, not a no-op early return).
    The spec-checker stays green on the post-render source.
    """
    goal_slug = "fr007-render-guard"
    goal_dir = tmp_path / "goals" / goal_slug
    goal_dir.mkdir(parents=True)
    source_path = goal_dir / "refined_requirements.collab.md"
    shutil.copyfile(FIXTURE, source_path)

    before = _sha256(source_path)

    db_path = tmp_path / "guard.db"
    init_db(db_path)
    _seed_goal(db_path, goal_slug)

    html_path = requirements_render_service.rerender_requirements_html(
        goal_slug, goals_dir=tmp_path / "goals", db_path=db_path
    )
    assert html_path is not None and html_path.exists(), "render must generate the .html artifact"

    after = _sha256(source_path)
    assert before == after, "rerender must not mutate the byte-canonical .collab.md (FR-007)"
    assert _sha256(FIXTURE) == before, "the frozen fixture on disk must be untouched"

    # The post-render source still passes the canon grammar checker (SC-004 lock).
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(source_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"cast-spec-checker rejected the post-render source (exit {result.returncode}):\n"
        f"{result.stderr or result.stdout}"
    )


def test_phase4_operations_never_mutate_the_collab_source(tmp_path):
    """The FR-007 lock holds across EVERY Phase 4 operation (the WP-F guarantee).

    WP-F's defining property: displacement is derived at read time and the save path gains
    *zero* machinery (decision #1). This test proves the byte-canonical ``.collab.md`` is
    immutable across the full Phase 4 surface — comment CRUD (create / resolve / reopen /
    relocate / orphan), the version gate ``create_next()`` (snapshots INTO the DB; never
    writes the file), and ``render_diff()`` (pure; served fresh, never persisted).

    We operate on a tmp copy of the frozen fixture so the real fixture is never touched, then
    assert the source bytes are byte-identical before/after the whole sequence — and that the
    frozen fixture on disk is untouched too. The spec-checker stays green on the post-op source.
    """
    goal_slug = "fr007-phase4-guard"
    goal_dir = tmp_path / "goals" / goal_slug
    goal_dir.mkdir(parents=True)
    source_path = goal_dir / "refined_requirements.collab.md"
    shutil.copyfile(FIXTURE, source_path)

    before = _sha256(source_path)
    src_text = source_path.read_text()

    db_path = tmp_path / "guard.db"
    init_db(db_path)
    _seed_goal(db_path, goal_slug)

    # Seed v1 so comments + create_next have a current snapshot to hang off of.
    version_service.create_snapshot(goal_slug, src_text, created_by="test", db_path=db_path)

    # --- Comment CRUD: create -> resolve -> reopen -> relocate -> orphan ----------------
    # A verbatim slice of the source guarantees the quote really exists in the file.
    anchor = "FR-007"
    quote = src_text[src_text.index(anchor): src_text.index(anchor) + 24]
    second_anchor = "FR-013"
    quote2 = src_text[src_text.index(second_anchor): src_text.index(second_anchor) + 24]

    c1 = comment_service.create_comment(
        goal_slug, quote, "Functional Requirements", "needs tightening",
        "tester", "human", db_path=db_path,
    )
    comment_service.resolve_comment(c1["id"], "tester", db_path=db_path)
    comment_service.reopen_comment(c1["id"], "tester", db_path=db_path)
    comment_service.relocate_comment(
        c1["id"], quote2, "Functional Requirements", "tester", db_path=db_path,
    )

    # An agent-authored comment exercises the FR-013 same-door path, then gets orphaned.
    c2 = comment_service.create_comment(
        goal_slug, quote2, "Functional Requirements", "stale anchor",
        "cast-comment-reanchor", "agent", db_path=db_path,
    )
    comment_service.orphan_comment(c2["id"], "cast-comment-reanchor", db_path=db_path)

    # --- create_next(): reads content, snapshots INTO the DB, never writes the file ------
    edited_text = src_text + "\n<!-- a downstream edit that never touches the canonical file -->\n"
    result = version_service.create_next(
        goal_slug, edited_text, created_by="test", db_path=db_path,
    )
    assert result["version"]["version"] == 2, "create_next must land the next snapshot in the DB"

    # --- render_diff(): pure, served fresh, never persisted ------------------------------
    old_parsed = parse_requirements(src_text)
    new_parsed = parse_requirements(edited_text)
    rendered = render_diff(old_parsed, new_parsed, base_version=1, head_version=2)
    assert rendered.html, "render_diff must produce a tracked-changes view"

    # --- FR-007 lock: the canonical source bytes are unchanged across ALL of the above ---
    after = _sha256(source_path)
    assert before == after, (
        "no Phase 4 operation may mutate the byte-canonical .collab.md (FR-007)"
    )
    assert _sha256(FIXTURE) == before, "the frozen fixture on disk must be untouched"

    # The post-op source still passes the canon grammar checker (SC-004 lock).
    check = subprocess.run(
        [sys.executable, str(CHECKER), str(source_path)],
        capture_output=True,
        text=True,
    )
    assert check.returncode == 0, (
        f"cast-spec-checker rejected the post-op source (exit {check.returncode}):\n"
        f"{check.stderr or check.stdout}"
    )


# --------------------------------------------------------------------------- #
# Phase 5 — the sole-mutator leg: the writeback apply is the ONLY mutation      #
# --------------------------------------------------------------------------- #

def _seed_rt_goal(db_path: Path, slug: str, folder_path: str) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, "Round-trip FR-007 goal", folder_path),
        )
        conn.commit()
    finally:
        conn.close()


def test_writeback_is_the_sole_mutator_and_surgical(tmp_path):
    """The writeback apply is the ONE sanctioned mutation; it touches only the target region.

    We copy the frozen, spec-compliant fixture into a tmp goal dir (the real fixture is never
    touched), apply ONE accepted addition (a new FR row under ``## Functional Requirements``), and
    assert the file gained exactly that line with **every other byte identical** — removing it
    reproduces the original bytes. Then the read-only surfaces — rerendering the ``.html``, a version
    snapshot, and a re-parse — leave the post-write source byte-for-byte unchanged: the writer is the
    *only* mutator. The canon grammar checker stays green on the spliced source (SC-004 lock holds),
    which is why a full spec-shaped fixture (not a toy doc) is used here.
    """
    slug = "fr007-writeback-guard"
    goal_dir = tmp_path / "goals" / slug
    goal_dir.mkdir(parents=True)
    source_path = goal_dir / "refined_requirements.collab.md"
    shutil.copyfile(FIXTURE, source_path)
    original = source_path.read_text(encoding="utf-8")

    db_path = tmp_path / "guard.db"
    init_db(db_path)
    _seed_rt_goal(db_path, slug, str(goal_dir))
    version_service.create_snapshot(slug, original, created_by="test", db_path=db_path)

    # The single sanctioned mutation: an accepted addition (fresh unique FR id) applied surgically.
    added = "| FR-901 | The system MUST trace round-trip provenance end-to-end. | US7 |"
    cr = change_request_service.create(
        slug, kind="addition", proposed_body=added, base_version=1,
        section_hint="Functional Requirements", author="cast-high-level-planner",
        author_type="agent", origin_phase="planning", origin_artifact_path="plan.collab.md",
        status="applied", db_path=db_path)
    change_request_service.apply_change_request(
        cr["id"], goal_dir=goal_dir, allowed_root=tmp_path / "goals", db_path=db_path)

    spliced = source_path.read_text(encoding="utf-8")
    # Surgical: removing the one inserted line reproduces the original byte-for-byte.
    assert added in spliced
    assert spliced.replace(added + "\n", "", 1) == original
    assert _sha256(FIXTURE) == hashlib.sha256(original.encode("utf-8")).hexdigest(), \
        "the frozen fixture on disk must be untouched"
    post_write_sha = _sha256(source_path)

    # No OTHER path mutates the post-write source: render, a version snapshot, and a re-parse.
    requirements_render_service.rerender_requirements_html(
        slug, goals_dir=tmp_path / "goals", db_path=db_path)
    version_service.create_snapshot(slug, spliced, created_by="test", db_path=db_path)
    parse_requirements_file(source_path)
    assert _sha256(source_path) == post_write_sha, (
        "only the writeback apply may mutate the .collab.md — no other path may touch it (FR-007)"
    )

    # The spliced source still passes the canon grammar checker (SC-004 lock).
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(source_path)], capture_output=True, text=True)
    assert result.returncode == 0, (
        f"cast-spec-checker rejected the post-writeback source (exit {result.returncode}):\n"
        f"{result.stderr or result.stdout}"
    )


def test_writer_has_no_whole_file_overwrite_path():
    """Structural negative: the apply module never *executes* a whole-file overwrite.

    The silent-drift bug US7 kills can only recur through a whole-file rewrite path. ``write_text``
    and ``save_artifact`` appear in the apply module only as forbidding prose (docstrings/comments
    explaining why they are banned). This tokenizes the module and asserts neither name occurs as an
    executable NAME token — comments and string literals are excluded — so the ban is enforced by a
    test, not just convention. The only sanctioned write is the verified surgical splice via
    ``_commit_spliced`` (tmp file + ``os.replace``).
    """
    module_path = Path(change_request_service.__file__)
    source = module_path.read_text(encoding="utf-8")

    code_names: list[str] = []
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    for tok in tokens:
        if tok.type == tokenize.NAME:
            code_names.append(tok.string)
    # `write_text` / `save_artifact` must never appear as executable identifiers (only `read_text`).
    assert "write_text" not in code_names, "apply module must not execute a whole-file write_text"
    assert "save_artifact" not in code_names, "apply module must not call save_artifact (overwrite)"
    # Sanity: the legitimate surgical-write seam and the read are present (proves we tokenized code).
    assert "_commit_spliced" in code_names
    assert "read_text" in code_names


# --------------------------------------------------------------------------- #
# Phase 3c — the maker pipeline never writes the canonical .collab.md           #
# --------------------------------------------------------------------------- #

class _FakeRunner:
    """Deterministic WHAT/HOW outputs for the FR-007 maker sweep (no LLM)."""

    def __init__(self, *, what, how):
        self._what, self._how = list(what), list(how)
        self.what_calls = self.how_calls = 0

    def run_agent(self, agent_name, user_msg, *, timeout_s):
        if agent_name == "cast-requirements-what":
            self.what_calls += 1
            return self._yield(self._what, self.what_calls)
        self.how_calls += 1
        return self._yield(self._how, self.how_calls)

    @staticmethod
    def _yield(seq, n):
        item = seq[min(n, len(seq)) - 1] if seq else ""
        if isinstance(item, BaseException):
            raise item
        return item


def _seed_render_goal(db_path: Path, slug: str, folder_path: str) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, "FR-007 maker goal", folder_path),
        )
        conn.commit()
    finally:
        conn.close()


def test_maker_pipeline_never_mutates_the_collab_source(tmp_path):
    """The FR-007 lock holds across the full maker pipeline — published/flagged AND fallback.

    A full fake-runner run (extractable-but-degraded HTML → the flagged best-attempt branch, then a
    no-output run → the deterministic fallback branch) must leave the canonical ``.collab.md``
    byte-identical: ``--tools ""`` makes the maker structurally unable to write the source, and the
    service only ever reads it (for hashing + the deterministic fallback). The generated ``.html``
    lands (proving the publish path ran), and the frozen fixture on disk is untouched.
    """
    from cast_server.services import render_job_service

    slug = "fr007-maker-guard"
    goal_dir = tmp_path / "goals" / slug
    goal_dir.mkdir(parents=True)
    source_path = goal_dir / "refined_requirements.collab.md"
    shutil.copyfile(FIXTURE, source_path)
    before = _sha256(source_path)

    db_path = tmp_path / "guard.db"
    init_db(db_path)
    _seed_render_goal(db_path, slug, str(goal_dir))
    render_job_service._reset_state()

    extractable = (
        "<!-- BEGIN RENDER -->\n"
        "<!doctype html><html><body data-goal-slug='x'><main class='rr-document'>"
        "<h2>Degraded</h2><section class='rr-unit'><h3>unit</h3><p>body</p></section>"
        "</main></body></html>\n"
        "<!-- END RENDER -->\n"
    )

    # The quality-loop flagged best-attempt branch (4a-2 OVERRIDE): extractable but gate-failing →
    # the loop scores every attempt and lands a flagged best-attempt at `status=published`
    # (human_review=1), still publishing an .html. The FR-007 invariant we assert here is unchanged:
    # the maker pipeline never touches the canonical .collab.md.
    flagged = render_job_service.request_render(
        slug, runner=_FakeRunner(what=["bogus WHAT doc, no front matter"], how=[extractable, extractable]),
        goals_dir=tmp_path / "goals", db_path=db_path, wait=True,
    )
    assert flagged["state"] == "published"
    assert (goal_dir / "refined_requirements.html").exists()
    assert _sha256(source_path) == before, "the flagged maker branch must not touch .collab.md (FR-007)"

    # Branch 1 — no extractable output → deterministic fallback (also publishes an .html).
    render_job_service._reset_state()
    fallback = render_job_service.request_render(
        slug, runner=_FakeRunner(what=["bogus WHAT doc"], how=["no sentinels", "still none"]),
        goals_dir=tmp_path / "goals", db_path=db_path, wait=True,
    )
    assert fallback["state"] == "fallback"
    assert _sha256(source_path) == before, "the fallback maker branch must not touch .collab.md (FR-007)"
    assert _sha256(FIXTURE) == before, "the frozen fixture on disk must be untouched"

    # The post-pipeline source still passes the canon grammar checker (SC-004 lock).
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(source_path)], capture_output=True, text=True)
    assert result.returncode == 0, (
        f"cast-spec-checker rejected the post-maker source (exit {result.returncode}):\n"
        f"{result.stderr or result.stdout}"
    )


def test_full_gapfill_run_leaves_canonical_byte_identical(goal):
    """FR-007 across the Phase-5b gap-fill emitter: a full gap-fill run that EMITS a change-request
    (a supplied, evidence-validated gap reconciled through the gate) leaves the canonical
    ``.collab.md`` byte-identical.

    The gap CR lands ``proposed`` (GATE-ALL → awaiting the human gate); the ONLY canonical writer
    remains the ``cast-requirements-writeback`` apply on approval. The emitter never fabricates the
    answer into the file, never auto-applies — so the byte-canonical source is untouched by the new
    downstream emitter.
    """
    _write_corpus(goal)
    before = _sha256(goal.source_path)

    runner = FakeRunner(
        what=[_gapped_what(goal.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],
        gapfill=[_gapfill_doc(_gf_supplied())],
    )
    result = _request(goal, runner, wait=True)
    assert result["state"] == "published"
    # The emitter ran (the gap reconciled to a proposed CR) ...
    assert _gaps_state(goal)["gaps"][0]["status"] == "cr-proposed"
    # ... yet the canonical source is byte-identical — no auto-apply, no fabrication into the file.
    assert _sha256(goal.source_path) == before, (
        "the gap-fill emitter must not mutate the byte-canonical .collab.md — the writeback apply "
        "on approval is the sole writer (FR-007)"
    )


def test_checker_binary_is_discoverable():
    assert CHECKER.exists(), f"spec checker not found at {CHECKER}"


def test_checker_clean_on_fixture():
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(FIXTURE)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"cast-spec-checker rejected the frozen fixture (exit {result.returncode}):\n"
        f"{result.stderr or result.stdout}"
    )
