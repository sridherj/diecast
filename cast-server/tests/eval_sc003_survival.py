"""eval_sc003_survival — sub-phase 4b-4 SC-003 END-TO-END gate (comments survive the maker).

The Phase-4b phase gate, run as an **eval harness** (the `eval_` prefix excludes it from default
pytest, like `eval_maker_pipeline_e2e.py` / `eval_quality_gate.py`). It proves SC-003 — *a maker
regenerate leaves every open comment anchored with **zero new orphans*** — against the REAL
pipeline code, in the three verification blocks sub-phase 4b-4's plan fixes:

    uv run python tests/eval_sc003_survival.py            # the deterministic blocking gate
    uv run python tests/eval_sc003_survival.py --live     # + one real `claude -p` maker (carry-forward)

The comment + version layer is **source-side**: comments anchor to a verbatim quote validated
against `refined_requirements.collab.md`, versions snapshot the source, `block_diff` diffs parsed
*source* versions, displacement is a source-side string-find. A maker regenerate (same source, new
HTML) therefore **cannot** orphan a comment at the DB layer — the genuine exposure is silent
`<mark>`-placement loss on a paraphrased maker DOM, which the pure `check_comment_survival` gate
closes. SC-003 is consequently a **deterministic** property; the blocking gate exercises it with the
proven injected fake runner (the same discipline as `test_quality_loop` / the Phase-4a eval), and
the live `claude -p` maker is a non-blocking human-eyeball carry-forward (autonomous runs do not
gate on a stochastic LLM — the project's no-live-LLM-block convention, recorded in
`phase4a-gate-evidence.md`).

Three blocks (every one drives REAL service / pipeline code — no behaviour is re-implemented here):

  1. **Same-source regenerate (render-only):** with N open comments placed, run the real
     `request_render` pipeline (`run_what → gate_what → run_how → gate_html → run_checker →
     decide_quality → publish`) → the survival gate is GREEN (every in-block mark places on the new
     DOM) and the render makes **zero** DB changes of any kind (comment / version / narration rows
     byte-identical before/after; canonical `.collab.md` untouched).
  2. **Source-edit regenerate (the full loop):** edit the source so one commented block is
     reworded+moved, one is deleted, one untouched → `create_next` reports `displaced_comment_ids`
     == exactly {reworded, deleted} → apply the re-anchor verdicts through the same-door services
     (reworded `relocated` — the verbatim backstop predicate holds; deleted-block `orphaned`) →
     **zero new orphans beyond the genuinely-deleted block**, the untouched comment never displaced,
     and the new render's `check_comment_survival` is GREEN with the relocated mark placed.
  3. **Trust boundary:** `save_narration` recomputes `summarize(diff_blocks(old, new))` server-side
     and accepts notes **only** when every `(change, heading_or_ref)` keys to a deterministic item
     (server-accepted == recomputed set); a bogus key is rejected all-or-nothing (no silent
     note-drop) — the panel can never show a change absent from the source.

Evidence (a JSON summary + the survival reports) is written under a run dir and echoed.
"""
from __future__ import annotations

import inspect
import json
import sys
import tempfile
from pathlib import Path

CAST_SERVER_DIR = Path(__file__).resolve().parent.parent
if str(CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(CAST_SERVER_DIR))
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

import cast_server.config as config  # noqa: E402
from cast_server.db.connection import get_connection, init_db  # noqa: E402
from cast_server.requirements_render import parse_requirements  # noqa: E402
from cast_server.requirements_render.block_diff import diff_blocks, summarize  # noqa: E402
from cast_server.requirements_render.maker_gate import (  # noqa: E402
    check_comment_survival,
    container_text_index,
)
from cast_server.requirements_render import comment_anchor  # noqa: E402
from cast_server.requirements_render.renderer import render_requirements  # noqa: E402
from cast_server.services import comment_service  # noqa: E402
from cast_server.services import render_job_service as svc  # noqa: E402
from cast_server.services import requirement_version_service as vsvc  # noqa: E402

# Reuse the PROVEN gate-passing source + maker markup + fake runner (no fork) — the same fixtures
# `test_render_job_service` / `test_quality_loop` pin the pipeline with.
from test_render_job_service import (  # noqa: E402
    _PASS_HTML,
    _SOURCE,
    _good_what,
    _verdict,
    _wrap,
    FakeRunner,
    # refine-req-v3 sp5 — render-anchor + UPDATE-mode survival regressions (a)–(f):
    _FR_REWORD,
    _FR_FRAGMENT,
    _edit_fr_source,
    _CORPUS_TEXT,
    _GAP_MARKED_HTML,
    _gapped_what,
    _gapfill_doc,
    _gf_supplied,
)


# ======================================================================================
# Helpers
# ======================================================================================
def _seed_goal(db_path: Path, goals_dir: Path, slug: str, source: str) -> Path:
    """Seed a goals row + goal dir with `source`; return the goal dir."""
    goal_dir = goals_dir / slug
    goal_dir.mkdir(parents=True, exist_ok=True)
    (goal_dir / "refined_requirements.collab.md").write_text(source, encoding="utf-8")
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, slug, str(goal_dir)),
        )
        conn.commit()
    finally:
        conn.close()
    return goal_dir


def _comment_table(db_path: Path, slug: str) -> list[dict]:
    """A stable, fully-ordered snapshot of EVERY comment row + event for `slug` (the DB-change
    witness — byte-comparable before/after a render)."""
    conn = get_connection(db_path)
    try:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM requirement_comments WHERE goal_slug = ? ORDER BY id", (slug,)
        ).fetchall()]
        events = [dict(r) for r in conn.execute(
            "SELECT e.* FROM comment_events e JOIN requirement_comments c ON e.comment_id = c.id "
            "WHERE c.goal_slug = ? ORDER BY e.id", (slug,)
        ).fetchall()]
    finally:
        conn.close()
    return {"comments": rows, "events": events}  # type: ignore[return-value]


def _counts(db_path: Path, slug: str) -> dict:
    conn = get_connection(db_path)
    try:
        v = conn.execute(
            "SELECT COUNT(*) n FROM requirement_versions WHERE goal_slug = ?", (slug,)
        ).fetchone()["n"]
        n = conn.execute(
            "SELECT COUNT(*) n FROM version_diff_narrations WHERE goal_slug = ?", (slug,)
        ).fetchone()["n"]
    finally:
        conn.close()
    return {"versions": v, "narrations": n}


def _survival_json(jobs_dir: Path, slug: str, source_hash: str) -> dict | None:
    p = jobs_dir / slug / source_hash[:12] / "survival.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# ======================================================================================
# Block 1 — same-source regenerate (render-only): survival green + zero DB changes
# ======================================================================================
def block1_same_source(run_dir: Path) -> dict:
    from test_render_job_service import _SOURCE  # the proven non-stub source for _PASS_HTML

    db_path = run_dir / "b1.db"
    init_db(db_path)
    goals_dir = run_dir / "b1-goals"
    slug = "sc003-same-source"
    goal_dir = _seed_goal(db_path, goals_dir, slug, _SOURCE)
    source_path = goal_dir / "refined_requirements.collab.md"
    parsed = parse_requirements(_SOURCE)

    config.RENDER_JOBS_DIR = run_dir / "b1-render-jobs"
    svc._reset_state()

    # Cut version 1, then create N open comments on in-block quotes (substrings of a block body
    # that the proven _PASS_HTML carries verbatim → they MUST place).
    vsvc.create_next(slug, _SOURCE, "tester", db_path=db_path)
    quotes = [
        "As a user I want a recurring cadence for a report export.",  # US1 body
        "The system must export nightly.",                            # FR-001 body
    ]
    for q in quotes:
        assert q in _SOURCE, f"fixture drift: quote not in source: {q!r}"
        assert q in _PASS_HTML, f"fixture drift: quote not in maker HTML: {q!r}"
        comment_service.create_comment(slug, q, None, "please confirm", "tester",
                                       db_path=db_path)

    before = _comment_table(db_path, slug)
    before_counts = _counts(db_path, slug)
    before_md = source_path.read_bytes()

    # The REAL pipeline with the injected fake maker (clean WHAT + the proven passing HOW HTML).
    runner = FakeRunner(what=[_good_what(parsed)], how=[_wrap(_PASS_HTML)], checker=[_verdict()])
    result = svc.request_render(slug, runner=runner, goals_dir=goals_dir, db_path=db_path, wait=True)

    survival = _survival_json(config.RENDER_JOBS_DIR, slug, parsed.content_hash)
    after = _comment_table(db_path, slug)
    after_counts = _counts(db_path, slug)
    after_md = source_path.read_bytes()
    comment_ids = sorted(c["id"] for c in after["comments"])

    checks = {
        "published_by_maker": result.get("state") == "published",
        "survival_recorded": survival is not None,
        "survival_passed": bool(survival and survival["passed"]),
        "all_comments_placed": bool(survival and sorted(survival["placed"]) == comment_ids),
        "zero_unplaced": bool(survival and survival["unplaced"] == []),
        "zero_violations": bool(survival and survival["violations"] == []),
        "comment_rows_byte_identical": after == before,
        "no_new_version_or_narration": after_counts == before_counts,
        "canonical_md_untouched": after_md == before_md,
    }
    return {"block": "1_same_source_regenerate", "checks": checks,
            "survival": survival, "comment_ids": comment_ids,
            "version_count": after_counts["versions"], "all_passed": all(checks.values())}


# ======================================================================================
# Block 2 — source-edit regenerate (the full loop): displacement → relocate/orphan,
#           zero new orphans beyond the deleted block, relocated mark places.
# ======================================================================================
_CLS = "---\nclassification:\n  family: new_initiative\n  confidence: 0.95\n---\n"
_INTENT_PAD = " ".join(
    ["A dependable morning digest keeps every downstream desk in sync across the window."] * 16
)

_QA = "Readers receive the alpha digest every single morning at dawn."   # US1 body @ V1 (reworded+moved)
_QA_NEW = "Readers receive the morning alpha digest promptly by seven sharp."  # US1 body @ V2 (relocate target)
_QC = "The exporter retries a failed upload three times before paging."   # FR-001 body (untouched)
_QB = "Operators receive a pager alert on a total export failure event."  # FR-002 body (deleted @ V2)

_SOURCE_V1 = f"""\
{_CLS}# Morning Digest

## Intent

The team wants a dependable morning alpha digest. {_INTENT_PAD}

## User Stories

### US1 — morning cadence

{_QA}

## Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-001 | {_QC} | US1 |
| FR-002 | {_QB} | US1 |

## Success Criteria

| ID | Criterion | Measure |
|---|---|---|
| SC-001 | The digest lands before the morning standup. | timed |
"""

# V2: US1 reworded+moved (its body changes to _QA_NEW, _QA gone), FR-002 DELETED (_QB gone),
# FR-001 untouched (_QC stays). A pure SC-001 reword keeps the diff honest about "modified".
_SOURCE_V2 = f"""\
{_CLS}# Morning Digest

## Intent

The team wants a dependable morning alpha digest. {_INTENT_PAD}

## Functional Requirements

| ID | Requirement | Source |
|---|---|---|
| FR-001 | {_QC} | US1 |

## User Stories

### US1 — morning cadence

{_QA_NEW}

## Success Criteria

| ID | Criterion | Measure |
|---|---|---|
| SC-001 | The digest lands well before the morning standup. | timed |
"""


def block2_source_edit(run_dir: Path) -> dict:
    db_path = run_dir / "b2.db"
    init_db(db_path)
    goals_dir = run_dir / "b2-goals"
    slug = "sc003-source-edit"
    _seed_goal(db_path, goals_dir, slug, _SOURCE_V1)

    # Version 1, then three open comments (reworded / untouched / deleted).
    vsvc.create_next(slug, _SOURCE_V1, "tester", db_path=db_path)
    cA = comment_service.create_comment(slug, _QA, None, "reword?", "tester", db_path=db_path)
    cC = comment_service.create_comment(slug, _QC, None, "keep", "tester", db_path=db_path)
    cB = comment_service.create_comment(slug, _QB, None, "deleting", "tester", db_path=db_path)

    # Edit the source → version 2; the deterministic displacement detector fires.
    nxt = vsvc.create_next(slug, _SOURCE_V2, "tester", db_path=db_path)
    displaced = sorted(nxt["displaced_comment_ids"])
    expected_displaced = sorted([cA["id"], cB["id"]])

    # Apply the re-anchor verdicts through the SAME-DOOR services (the LLM verdict itself is the
    # live carry-forward; here the deterministic application + backstop predicate are the gate).
    backstop_ok = _QA_NEW in _SOURCE_V2  # the route's verbatim-substring backstop predicate
    comment_service.relocate_comment(cA["id"], _QA_NEW, None, "cast-comment-reanchor", db_path=db_path)
    comment_service.orphan_comment(cB["id"], "cast-comment-reanchor", db_path=db_path)

    # The new maker DOM: the deterministic substrate render of V2 (guaranteed verbatim-contiguous,
    # never regresses below the gate) stands in for the maker render — the relocated + untouched
    # quotes must survive on it.
    parsed_v2 = parse_requirements(_SOURCE_V2)
    candidate_html = render_requirements(parsed_v2).html
    # sp2 reconciliation: comments anchor to the RENDER snapshot now (`anchor_space='render'`), so
    # displacement is checked against the served render's container text — NOT the source. The V2
    # substrate render is that served artifact; pass its container text via the `render_text` seam
    # (the old `current_text=` source seam is ignored for render-space comments).
    render_text = container_text_index(candidate_html).document_text
    open_now = comment_service.list_comments(slug, state="open", render_text=render_text,
                                             db_path=db_path)
    orphaned_now = comment_service.list_comments(slug, state="orphaned", db_path=db_path)
    open_ids = {c["id"] for c in open_now}
    displaced_open = {c["id"] for c in open_now if c.get("displaced")}

    survivors = [{"id": cA["id"], "quoted_text": _QA_NEW}, {"id": cC["id"], "quoted_text": _QC}]
    survival = check_comment_survival(candidate_html, parsed_v2, survivors)

    checks = {
        "displaced_is_reworded_and_deleted": displaced == expected_displaced,
        "untouched_never_displaced": cC["id"] not in displaced,
        "relocate_backstop_predicate_holds": backstop_ok,
        "reworded_relocated_open_not_displaced": cA["id"] in open_ids and cA["id"] not in displaced_open,
        "untouched_open_not_displaced": cC["id"] in open_ids and cC["id"] not in displaced_open,
        "exactly_one_orphan": [c["id"] for c in orphaned_now] == [cB["id"]],
        "zero_new_orphans_beyond_deleted": {c["id"] for c in orphaned_now} == {cB["id"]},
        "new_render_survival_green": survival["passed"],
        "relocated_and_untouched_marks_place": sorted(survival["placed"]) == sorted([cA["id"], cC["id"]]),
    }
    return {"block": "2_source_edit_loop", "checks": checks,
            "displaced": displaced, "expected_displaced": expected_displaced,
            "orphaned": [c["id"] for c in orphaned_now], "survival": survival,
            "all_passed": all(checks.values())}


# ======================================================================================
# Block 3 — trust boundary: narration accepted only when every note keys to summarize()
# ======================================================================================
def block3_trust_boundary(run_dir: Path) -> dict:
    db_path = run_dir / "b3.db"
    init_db(db_path)
    goals_dir = run_dir / "b3-goals"
    slug = "sc003-narration"
    _seed_goal(db_path, goals_dir, slug, _SOURCE_V1)

    vsvc.create_next(slug, _SOURCE_V1, "tester", db_path=db_path)   # version 1
    vsvc.create_next(slug, _SOURCE_V2, "tester", db_path=db_path)   # version 2

    # The deterministic key set the server will recompute (never trusting the poster).
    recomputed = summarize(diff_blocks(parse_requirements(_SOURCE_V1), parse_requirements(_SOURCE_V2)))
    valid_items = recomputed["items"]
    valid_keys = [[it["change"], it["heading_or_ref"]] for it in valid_items]

    # Post a note for EVERY deterministic item → must be accepted, returned byte-for-byte.
    good_notes = [{"change": it["change"], "heading_or_ref": it["heading_or_ref"],
                   "note": f"note about {it['heading_or_ref']}"} for it in valid_items]
    stored = vsvc.save_narration(slug, 1, 2, "overview of the change set", good_notes,
                                 "cast-refine-requirements", db_path=db_path)
    accepted_keys = [[n["change"], n["heading_or_ref"]] for n in stored["item_notes"]]

    # Post a note with a BOGUS key (a change absent from the deterministic set) → 422 all-or-nothing.
    bogus_rejected = False
    try:
        vsvc.save_narration(slug, 1, 2, "ov",
                            good_notes + [{"change": "added", "heading_or_ref": "FR-999",
                                           "note": "invented"}],
                            "cast-refine-requirements", db_path=db_path)
    except vsvc.NarrationValidationError as exc:
        bogus_rejected = "FR-999" in str(exc)

    # The GET /changes sibling: counts/items stay byte-for-byte summarize(); narration rides alongside.
    fetched = vsvc.get_narration(slug, 1, 2, db_path=db_path)

    checks = {
        "narration_accepted": stored is not None and len(stored["item_notes"]) == len(valid_items),
        "server_accepted_equals_recomputed_set": sorted(map(tuple, accepted_keys)) == sorted(map(tuple, valid_keys)),
        "bogus_key_rejected_all_or_nothing": bogus_rejected,
        "rejection_did_not_persist_partial": fetched is not None
        and len(fetched["item_notes"]) == len(valid_items),
        "has_deterministic_items": len(valid_items) > 0,
    }
    return {"block": "3_trust_boundary", "checks": checks,
            "recomputed_keys": valid_keys, "accepted_keys": accepted_keys,
            "all_passed": all(checks.values())}


# ======================================================================================
# refine-req-v3 sp5 — render-anchor + UPDATE-mode survival regressions (a)–(f)
# ======================================================================================
# These extend the Phase-4b SC-003 gate to the v3 contract: comments now anchor to the
# **published render snapshot** (`anchor_space='render'`, a server-resolved `block_ref`
# bridge), and a small edit re-renders in **UPDATE mode** (the deterministic splice keeps
# unchanged unit containers byte-identical). Each regression drives the REAL services /
# pipeline with the proven injected FakeRunner (no behaviour re-implemented here) — the
# same discipline as blocks 1–3. (f) pins the load-bearing gap-CR idempotency guarantee
# (plan-review Decisions #2/#5): an UPDATE re-render of a doc carrying an open gap emits
# ZERO new gap change-requests, because UPDATE reuses the prior `gaps-state.json` and
# SKIPS `emit_change_requests` entirely (re-emitting under the new source-hash would write
# a DUPLICATE the source-hash-keyed dedupe fingerprint can't match).


class _G:  # a goal namespace matching the test_render_job_service `goal` fixture shape
    pass


def _setup_goal(run_dir: Path, slug: str, source: str = _SOURCE) -> _G:
    """Seed a goal (goals row + `.collab.md`) + a per-block render-jobs dir, exactly like the
    pytest `goal` fixture — so the imported `_edit_fr_source` / `_FR_FRAGMENT` helpers apply."""
    db_path = run_dir / f"{slug}.db"
    init_db(db_path)
    goals_dir = run_dir / f"{slug}-goals"
    goal_dir = goals_dir / slug
    goal_dir.mkdir(parents=True, exist_ok=True)
    source_path = goal_dir / "refined_requirements.collab.md"
    source_path.write_text(source, encoding="utf-8")
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO goals (slug, title, folder_path) VALUES (?, ?, ?)",
            (slug, slug, str(goal_dir)),
        )
        conn.commit()
    finally:
        conn.close()
    config.RENDER_JOBS_DIR = run_dir / f"{slug}-render-jobs"
    svc._reset_state()
    parsed = parse_requirements(source)
    g = _G()
    g.slug = slug
    g.goals_dir = goals_dir
    g.db_path = db_path
    g.source_path = source_path
    g.parsed = parsed
    g.source_hash = parsed.content_hash
    g.jobs_dir = config.RENDER_JOBS_DIR
    return g


def _g_survival(g: _G, source_hash: str) -> dict | None:
    p = g.jobs_dir / g.slug / source_hash[:12] / "survival.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _g_published_html(g: _G) -> str:
    return (g.goals_dir / g.slug / "refined_requirements.html").read_text(encoding="utf-8")


def _cr_count(db_path: Path) -> int:
    conn = get_connection(db_path)
    try:
        return conn.execute("SELECT COUNT(*) n FROM change_requests").fetchone()["n"]
    finally:
        conn.close()


def _add_render_comment(g: _G, quote: str, served: str | None = None) -> int:
    return comment_service.create_comment(
        g.slug, quote, None, "please confirm", "tester", "human",
        db_path=g.db_path, served_render_html=served,
    )["id"]


def _publish_prior(g: _G) -> None:
    """Job 1: a clean maker publish of _PASS_HTML — the prior render a later UPDATE recovers."""
    r1 = FakeRunner(what=[_good_what(g.parsed)], how=[_wrap(_PASS_HTML)], checker=[_verdict()])
    res = svc.request_render(g.slug, runner=r1, goals_dir=g.goals_dir, db_path=g.db_path, wait=True)
    assert res["state"] == "published", f"prior publish failed: {res}"
    assert "<!-- served-by: maker -->" in _g_published_html(g)


# --- (a) same-source re-render → render-anchored comments place, ZERO DB changes -------
def reg_a_same_source(run_dir: Path) -> dict:
    g = _setup_goal(run_dir, "rega-same-source")
    vsvc.create_next(g.slug, _SOURCE, "tester", db_path=g.db_path)
    quotes = ["As a user I want a recurring cadence for a report export.",  # US1 unit
              "Exports complete within ten minutes."]                       # SC-001 unit
    cids = []
    for q in quotes:
        assert q in _PASS_HTML, f"fixture drift: {q!r} not in served render"
        cids.append(_add_render_comment(g, q, served=_PASS_HTML))

    anchored = comment_service.list_comments(g.slug, db_path=g.db_path, goals_dir=g.goals_dir)
    before_rows = _comment_table(g.db_path, g.slug)
    before_counts = _counts(g.db_path, g.slug)
    before_md = g.source_path.read_bytes()

    runner = FakeRunner(what=[_good_what(g.parsed)], how=[_wrap(_PASS_HTML)], checker=[_verdict()])
    result = svc.request_render(g.slug, runner=runner, goals_dir=g.goals_dir,
                                db_path=g.db_path, wait=True)

    survival = _g_survival(g, g.source_hash)
    after_rows = _comment_table(g.db_path, g.slug)
    after_counts = _counts(g.db_path, g.slug)
    after_md = g.source_path.read_bytes()

    checks = {
        "published_by_maker": result.get("state") == "published",
        "comments_anchor_space_render": all(c.get("anchor_space") == "render" for c in anchored),
        "block_refs_server_resolved": all(c.get("block_ref") for c in anchored),
        "survival_passed": bool(survival and survival["passed"]),
        "all_comments_placed": bool(survival and sorted(survival["placed"]) == sorted(cids)),
        "comment_rows_byte_identical": after_rows == before_rows,
        "no_new_version_or_narration": after_counts == before_counts,
        "canonical_md_untouched": after_md == before_md,
    }
    return {"block": "a_same_source_render_anchor_zero_db", "checks": checks,
            "survival": survival, "all_passed": all(checks.values())}


# --- (b) small edit → UPDATE: comment on UNCHANGED block places byte-identically ------
def reg_b_update_unchanged_block(run_dir: Path) -> dict:
    g = _setup_goal(run_dir, "regb-update-unchanged")
    _publish_prior(g)
    # A comment on the UNCHANGED SC-001 unit (the splice keeps it byte-identical).
    cid = _add_render_comment(g, "Exports complete within ten minutes.", served=_PASS_HTML)

    new_parsed = _edit_fr_source(g, _FR_REWORD)   # ref-bearing FR-001 edit → UPDATE fires
    r2 = FakeRunner(what=[_good_what(new_parsed)], how=[_wrap(_FR_FRAGMENT)], checker=[_verdict()])
    result = svc.request_render(g.slug, runner=r2, goals_dir=g.goals_dir, db_path=g.db_path, wait=True)
    row = svc.get_job_row(result["job_id"], g.db_path)
    survival = _g_survival(g, new_parsed.content_hash)
    open_rows = comment_service.list_comments(g.slug, state="open", db_path=g.db_path,
                                              goals_dir=g.goals_dir)

    checks = {
        "published_by_maker": result.get("state") == "published",
        "mode_is_update": row is not None and row["mode"] == "update",
        "no_human_review_flag": row is not None and row["human_review"] == 0,
        "survival_passed": bool(survival and survival["passed"]),
        "unchanged_comment_placed": bool(survival and cid in survival["placed"]),
        "no_reanchor_dispatch_needed": r2.reanchor_calls == 0,
        "comment_open_not_displaced": any(
            c["id"] == cid and c["displaced"] is False for c in open_rows),
    }
    return {"block": "b_update_unchanged_block_byte_identical", "checks": checks,
            "mode": row["mode"] if row else None, "survival": survival,
            "all_passed": all(checks.values())}


# --- (c) comment on MODIFIED block → relocated by publish-boundary dispatch ------------
def reg_c_update_modified_block(run_dir: Path) -> dict:
    g = _setup_goal(run_dir, "regc-update-modified")
    _publish_prior(g)
    cid = _add_render_comment(g, "The system must export nightly.", served=_PASS_HTML)  # FR-001

    new_parsed = _edit_fr_source(g, _FR_REWORD)
    reanchor_verdict = json.dumps({
        "narration": None,
        "verdicts": [{
            "comment_id": cid, "verdict": "relocated",
            "new_quoted_text": _FR_REWORD, "new_section_hint": "Functional Requirements",
            "confidence": 0.9, "reasoning": "FR-001 reworded; same requirement.",
        }],
    })
    r2 = FakeRunner(what=[_good_what(new_parsed)], how=[_wrap(_FR_FRAGMENT)],
                    checker=[_verdict()], reanchor=[reanchor_verdict])
    result = svc.request_render(g.slug, runner=r2, goals_dir=g.goals_dir, db_path=g.db_path, wait=True)
    survival = _g_survival(g, new_parsed.content_hash)
    row = comment_service.get_comment(cid, db_path=g.db_path)

    checks = {
        "published_by_maker": result.get("state") == "published",
        "modified_comment_is_expected_miss": bool(survival and cid in survival["expected_misses"]),
        "expected_miss_never_flips_passed": bool(survival and survival["passed"]),
        "exactly_one_publish_boundary_dispatch": r2.reanchor_calls == 1,
        "comment_relocated_not_dropped": row["state"] == "open" and row["quoted_text"] == _FR_REWORD,
        "never_auto_resolved": row["state"] != "resolved",
    }
    return {"block": "c_update_modified_block_relocated", "checks": checks,
            "survival": survival, "comment_state": row["state"], "all_passed": all(checks.values())}


# --- (d) massive edit → CREATE mode: survivor places, never a silent UPDATE -----------
def reg_d_massive_edit_creates(run_dir: Path) -> dict:
    g = _setup_goal(run_dir, "regd-massive-edit")
    _publish_prior(g)
    # A comment on the UNCHANGED SC-001 unit (survives a fresh CREATE re-render of _PASS_HTML).
    cid = _add_render_comment(g, "Exports complete within ten minutes.", served=_PASS_HTML)

    # Force the FR-001 edit over the massive-change threshold so the mode decision picks CREATE
    # (a massive edit re-renders fresh — never an UPDATE splice). Restore the knob after.
    saved = config.RENDER_UPDATE_MAX_CHANGED_FRACTION
    config.RENDER_UPDATE_MAX_CHANGED_FRACTION = 0.0
    try:
        new_parsed = _edit_fr_source(g, _FR_REWORD)
        r2 = FakeRunner(what=[_good_what(new_parsed)], how=[_wrap(_PASS_HTML)], checker=[_verdict()])
        result = svc.request_render(g.slug, runner=r2, goals_dir=g.goals_dir,
                                    db_path=g.db_path, wait=True)
        row = svc.get_job_row(result["job_id"], g.db_path)
    finally:
        config.RENDER_UPDATE_MAX_CHANGED_FRACTION = saved

    survival = _g_survival(g, new_parsed.content_hash)
    open_rows = comment_service.list_comments(g.slug, state="open", db_path=g.db_path,
                                              goals_dir=g.goals_dir)
    checks = {
        "published": result.get("state") == "published",
        "mode_is_create": row is not None and row["mode"] == "create",
        "ran_full_create": r2.what_calls >= 1 and r2.how_calls >= 2,  # run_what + gap-probe + loop
        "survivor_places_or_badged": bool(survival and cid in survival["placed"]),
        "comment_not_dropped": any(c["id"] == cid for c in open_rows),
    }
    return {"block": "d_massive_edit_degrades_to_create", "checks": checks,
            "mode": row["mode"] if row else None, "all_passed": all(checks.values())}


# --- (e) trust boundary: block_ref is SERVER-resolved, never client-supplied ----------
def reg_e_trust_boundary(run_dir: Path) -> dict:
    g = _setup_goal(run_dir, "rege-trust-boundary")
    # The service API has NO `block_ref` parameter — a client cannot supply (or spoof) one.
    sig = inspect.signature(comment_service.create_comment)
    no_client_block_ref = "block_ref" not in sig.parameters

    # A placed quote → the stored block_ref equals the SERVER-side resolver's verdict (FR-001).
    cid = _add_render_comment(g, "The system must export nightly.", served=_PASS_HTML)
    stored = comment_service.get_comment(cid, db_path=g.db_path)
    server_resolved = comment_anchor.resolve_render_anchor(
        _PASS_HTML, "The system must export nightly.").block_ref

    # A quote ABSENT from the served render → block_ref is None (honest, never guessed).
    cid_absent = _add_render_comment(g, "This phrase is not on the published render at all.",
                                     served=_PASS_HTML)
    stored_absent = comment_service.get_comment(cid_absent, db_path=g.db_path)

    checks = {
        "no_client_block_ref_param": no_client_block_ref,
        "anchor_space_is_render": stored["anchor_space"] == "render",
        "block_ref_matches_server_resolver": stored["block_ref"] == server_resolved == "FR-001",
        "absent_quote_block_ref_is_null_not_guessed": stored_absent["block_ref"] is None,
    }
    return {"block": "e_trust_boundary_server_resolved_block_ref", "checks": checks,
            "server_resolved": server_resolved, "all_passed": all(checks.values())}


# --- (f) gap-CR idempotency under UPDATE: an UPDATE re-render emits ZERO new gap CRs ---
def reg_f_gap_cr_idempotency_under_update(run_dir: Path) -> dict:
    g = _setup_goal(run_dir, "regf-gap-idempotency")
    # Ground GAP-01's answer in the goal's own corpus (the gapfill allowlist).
    (g.goals_dir / g.slug / "requirements.human.md").write_text(_CORPUS_TEXT, encoding="utf-8")

    # CREATE render with an open, grounded gap → emits exactly ONE gap change-request.
    r1 = FakeRunner(
        what=[_gapped_what(g.parsed)],
        how=[_wrap(_PASS_HTML), _wrap(_GAP_MARKED_HTML)],   # gap probe, then the .rr-gap-marked render
        gapfill=[_gapfill_doc(_gf_supplied())],
        checker=[_verdict()],
    )
    res1 = svc.request_render(g.slug, runner=r1, goals_dir=g.goals_dir, db_path=g.db_path, wait=True)
    crs_after_create = _cr_count(g.db_path)

    # A small ref-bearing edit → UPDATE: prior gaps-state.json is REUSED and emit is SKIPPED.
    new_parsed = _edit_fr_source(g, _FR_REWORD)
    r2 = FakeRunner(what=[_good_what(new_parsed)], how=[_wrap(_FR_FRAGMENT)], checker=[_verdict()])
    res2 = svc.request_render(g.slug, runner=r2, goals_dir=g.goals_dir, db_path=g.db_path, wait=True)
    row2 = svc.get_job_row(res2["job_id"], g.db_path)
    crs_after_update = _cr_count(g.db_path)

    checks = {
        "create_published": res1.get("state") == "published",
        "create_emitted_one_gap_cr": crs_after_create == 1,
        "gapfill_ran_once_on_create": r1.gapfill_calls == 1,
        "update_published": res2.get("state") == "published",
        "update_mode_active": row2 is not None and row2["mode"] == "update",
        "update_skipped_gap_emit": r2.gapfill_calls == 0,
        "zero_new_gap_crs_under_update": crs_after_update == crs_after_create == 1,
    }
    return {"block": "f_gap_cr_idempotency_under_update", "checks": checks,
            "crs_after_create": crs_after_create, "crs_after_update": crs_after_update,
            "all_passed": all(checks.values())}


def render_anchor_regressions(run_dir: Path) -> list[dict]:
    """The six sp5 render-anchor + UPDATE-mode survival regressions (a)–(f)."""
    return [
        reg_a_same_source(run_dir),
        reg_b_update_unchanged_block(run_dir),
        reg_c_update_modified_block(run_dir),
        reg_d_massive_edit_creates(run_dir),
        reg_e_trust_boundary(run_dir),
        reg_f_gap_cr_idempotency_under_update(run_dir),
    ]


# ======================================================================================
# Live carry-forward (best-effort, NON-blocking) — one real `claude -p` maker render.
# ======================================================================================
def live_carry_forward(run_dir: Path) -> dict:
    from test_render_job_service import _SOURCE

    db_path = run_dir / "live.db"
    init_db(db_path)
    goals_dir = run_dir / "live-goals"
    slug = "sc003-live"
    _seed_goal(db_path, goals_dir, slug, _SOURCE)
    parsed = parse_requirements(_SOURCE)
    config.RENDER_JOBS_DIR = run_dir / "live-render-jobs"
    svc._reset_state()

    vsvc.create_next(slug, _SOURCE, "tester", db_path=db_path)
    for q in ("As a user I want a recurring cadence for a report export.",
              "The system must export nightly."):
        comment_service.create_comment(slug, q, None, "confirm", "tester", db_path=db_path)

    runner = svc.ProductionAgentRunner(config.RENDER_JOBS_DIR / slug / parsed.content_hash[:12])
    try:
        result = svc.request_render(slug, runner=runner, goals_dir=goals_dir,
                                    db_path=db_path, wait=True)
        survival = _survival_json(config.RENDER_JOBS_DIR, slug, parsed.content_hash)
        return {"ran": True, "state": result.get("state"), "survival": survival,
                "survival_passed": bool(survival and survival["passed"])}
    except Exception as exc:  # noqa: BLE001 — live LLM is best-effort, never blocks the gate
        return {"ran": False, "error": f"{type(exc).__name__}: {exc}"}


# ======================================================================================
# main
# ======================================================================================
def main() -> int:
    live = "--live" in sys.argv[1:]
    run_dir = Path(tempfile.mkdtemp(prefix="sc003-survival-"))
    print(f"[sc003] run dir: {run_dir}")

    blocks = [block1_same_source(run_dir), block2_source_edit(run_dir),
              block3_trust_boundary(run_dir)]
    # sp5 — the render-anchor + UPDATE-mode survival regressions (a)–(f).
    regressions = render_anchor_regressions(run_dir)

    summary = {"blocks": blocks, "regressions": regressions,
               "all_passed": all(b["all_passed"] for b in blocks)
               and all(r["all_passed"] for r in regressions)}

    print("\n[sc003] ===== SC-003 GATE (deterministic, blocking) =====")
    for b in blocks:
        print(f"[sc003] {'PASS' if b['all_passed'] else 'FAIL'}  block {b['block']}")
        for k, v in b["checks"].items():
            print(f"[sc003]     {'ok ' if v else 'XXX'} {k}")

    print("\n[sc003] ===== sp5 render-anchor + UPDATE-mode regressions (a)–(f) =====")
    for r in regressions:
        print(f"[sc003] {'PASS' if r['all_passed'] else 'FAIL'}  {r['block']}")
        for k, v in r["checks"].items():
            print(f"[sc003]     {'ok ' if v else 'XXX'} {k}")

    if live:
        print("\n[sc003] ----- live carry-forward: one real claude -p maker render -----")
        lv = live_carry_forward(run_dir)
        summary["live_carry_forward"] = lv
        if lv["ran"]:
            print(f"[sc003]   ran: state={lv['state']} survival_passed={lv['survival_passed']}")
        else:
            print(f"[sc003]   not run (non-blocking): {lv['error']}")

    out = run_dir / "sc003_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\n[sc003] evidence: {out}")
    print(f"[sc003] ALL PASSED (blocking gate): {summary['all_passed']}")
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
