"""Throwaway 1b test-bed driver — anchor-backbone survival under a varying maker render.

NOT a pytest file (``spike_*`` under ``spikes/1b/``; pytest never collects it). Drives the
EXISTING, UNMODIFIED v2 services against a scratch SQLite DB (injectable ``db_path``) and a
scratch goal slug — never the live house DB, never a real ``goals/{slug}`` folder.

Two phases (DB state persists in scratch.sqlite between them):

  python spike_backbone.py build   # fresh DB, seed 6 comments, measure v1, create_next(edited),
                                    # write reanchor_input.json  (the displaced-comment payload)
  # --- dispatch cast-comment-reanchor (subagent), write reanchor_verdicts.json ---
  python spike_backbone.py apply    # FR-019 backstop + same-door relocate/orphan, measure v2,
                                    # diff_blocks determinism check, write metrics.json

The split keeps the LLM re-anchor judgement a real, out-of-band delegation (never fabricated).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# cast_server lives under <repo>/cast-server — make it importable regardless of CWD.
sys.path.insert(0, str(HERE.parents[4] / "cast-server"))

from cast_server.db.connection import get_connection, init_db          # noqa: E402
from cast_server.services import comment_service, requirement_version_service  # noqa: E402
from cast_server.requirements_render import block_diff, parser          # noqa: E402

sys.path.insert(0, str(HERE))
from spike_mark_placement import MakerDom                              # noqa: E402

SLUG = "spike-1b-anchor-survival"
DB = HERE / "scratch.sqlite"
SRC = HERE / "source"
ORIGINAL = (SRC / "original.collab.md").read_text(encoding="utf-8")
EDITED = (SRC / "edited.collab.md").read_text(encoding="utf-8")
V1_HTML = HERE / "feature-maker-v1.html"
V2_HTML = HERE / "feature-maker-v2.html"

# The six seeded comments. ``case`` documents the role; ``intended`` is the maker-DOM
# requirement-unit container the comment's <mark> must land in (the scoped-placement gate).
SEED = [
    dict(case="reword",  intended="US1",    section_hint="User Stories",
         quoted_text="delivered on time without manual effort",
         body="Is 'on time' defined by an SLA, or best-effort?", author_kind="human"),
    dict(case="delete",  intended="FR-003", section_hint="Functional Requirements",
         quoted_text="retain the three most recent export artifacts per schedule",
         body="Why three? Should retention be configurable?", author_kind="agent"),
    dict(case="stay",    intended="SC-003", section_hint="Success Criteria",
         quoted_text="lists runs newest-first with a status badge per run",
         body="Confirm the badge covers partial-success runs.", author_kind="human"),
    dict(case="move",    intended="FR-005", section_hint="Functional Requirements",
         quoted_text="read-only history of the last fifty export runs",
         body="Fifty feels arbitrary — paginate instead?", author_kind="agent"),
    dict(case="generic", intended="FR-004", section_hint="Functional Requirements",
         quoted_text="the owner",
         body="Notify the owner specifically, not the whole team.", author_kind="human"),
    dict(case="section", intended="FR-001", section_hint="Functional Requirements",
         quoted_text="accept a cron-style cadence expression and validate it before saving",
         body="Which cron dialect — 5-field or 6-field?", author_kind="agent"),
]


def _assert_isolated() -> None:
    """Belt-and-suspenders: never touch the live house DB or a real goal folder."""
    from cast_server.config import DB_PATH, GOALS_DIR
    assert DB.resolve() != Path(DB_PATH).resolve(), "refusing to run against the live house DB"
    assert "spike" in SLUG and SLUG != "system-ops", "scratch slug guard"
    real_goal = Path(GOALS_DIR) / SLUG
    assert not real_goal.exists(), f"refusing: a real goal folder exists at {real_goal}"


def _seed_goal(conn) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT OR IGNORE INTO goals (slug, title, status, in_focus, origin,
                                        folder_path, created_at)
           VALUES (?, 'Spike 1b Anchor Survival', 'accepted', 0, 'manual', ?, ?)""",
        (SLUG, SLUG, now),
    )
    conn.commit()


def _measure(html_path: Path, comments: list[dict], quote_key: str) -> list[dict]:
    """Run the byte-faithful harness for each comment; scope the hit to its intended unit."""
    dom = MakerDom(html_path.read_text(encoding="utf-8"))
    out = []
    for c in comments:
        p = dom.place(c[quote_key], intended_unit=c["intended"])
        out.append(dict(id=c["id"], case=c["case"], intended=c["intended"],
                        quote=c[quote_key], found=p.found, landed=p.landed_unit,
                        in_intended=p.in_intended))
    return out


def build() -> None:
    _assert_isolated()
    if DB.exists():
        DB.unlink()                       # fresh throwaway DB every build
    init_db(DB)
    conn = get_connection(DB)
    try:
        _seed_goal(conn)
    finally:
        conn.close()

    # v1: snapshot the original source, then seed the six open comments against it.
    requirement_version_service.create_next(SLUG, ORIGINAL, created_by="spike", db_path=DB)
    comments = []
    for s in SEED:
        row = comment_service.create_comment(
            SLUG, s["quoted_text"], s["section_hint"], s["body"],
            author=("maker-agent" if s["author_kind"] == "agent" else "reviewer"),
            author_kind=s["author_kind"], db_path=DB)
        c = dict(s); c["id"] = row["id"]
        comments.append(c)

    # Pre-edit verbatim sanity: every seed quote IS in the original source (valid anchor).
    for c in comments:
        assert c["quoted_text"] in ORIGINAL, f"seed {c['case']} not verbatim in original"

    v1 = _measure(V1_HTML, comments, "quoted_text")

    # Regenerate-with-moved-text: cut v2 from the EDITED source; capture displaced ids.
    res = requirement_version_service.create_next(SLUG, EDITED, created_by="spike", db_path=DB)
    displaced_ids = set(res["displaced_comment_ids"])
    by_id = {c["id"]: c for c in comments}

    expected_displaced = {c["id"] for c in comments if c["case"] in ("reword", "delete", "generic")}
    expected_survive = {c["id"] for c in comments if c["case"] in ("stay", "move", "section")}

    state = dict(
        slug=SLUG, db=str(DB),
        comments=comments,
        v1=v1,
        displaced_ids=sorted(displaced_ids),
        displaced_cases=sorted(by_id[i]["case"] for i in displaced_ids),
        expected_displaced=sorted(expected_displaced),
        survive_ids=sorted(expected_survive),
        convergence=res["convergence"],
        version=res["version"]["version"],
        assertions=dict(
            displaced_equals_reword_delete_generic=(displaced_ids == expected_displaced),
            untouched_did_not_displace=(expected_survive.isdisjoint(displaced_ids)),
        ),
    )
    (HERE / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    # The reanchor INPUT payload (v2 contract: new_content is the new SOURCE markdown, not HTML).
    displaced_comments = [
        dict(id=i, quoted_text=by_id[i]["quoted_text"],
             section_hint=by_id[i]["section_hint"], body=by_id[i]["body"])
        for i in sorted(displaced_ids)
    ]
    (HERE / "reanchor_input.json").write_text(json.dumps(dict(
        comments=displaced_comments, old_content=ORIGINAL, new_content=EDITED,
    ), indent=2), encoding="utf-8")

    print("=== BUILD ===")
    print(f"version cut: v{state['version']}  convergence: {state['convergence']}")
    print(f"v1 placement (scoped to intended unit):")
    for r in v1:
        flag = "OK " if r["in_intended"] else ("FALSE-PLACE" if r["found"] else "MISS")
        print(f"  [{flag:>11}] {r['case']:<8} id={r['id']} intended={r['intended']:<7} landed={r['landed']}")
    print(f"displaced ids={state['displaced_ids']} cases={state['displaced_cases']}")
    print(f"assert displaced=={{reword,delete,generic}}: {state['assertions']['displaced_equals_reword_delete_generic']}")
    print(f"assert untouched did NOT displace: {state['assertions']['untouched_did_not_displace']}")
    print(f"wrote reanchor_input.json ({len(displaced_comments)} displaced comments)")


def apply() -> None:
    state = json.loads((HERE / "state.json").read_text(encoding="utf-8"))
    verdicts = json.loads((HERE / "reanchor_verdicts.json").read_text(encoding="utf-8"))["verdicts"]
    by_id = {c["id"]: c for c in state["comments"]}

    # Apply each verdict through the SAME-DOOR service, replicating the route's FR-019
    # verbatim-substring backstop: a relocate whose new_quoted_text is NOT in the new source
    # is rejected (would be a 422) and DOWNGRADES to orphan — counting AGAINST the gate.
    applied = []
    for v in verdicts:
        cid = v["comment_id"]
        if v["verdict"] == "relocated":
            nq = v.get("new_quoted_text")
            backstop_ok = bool(nq) and (nq in EDITED)
            if backstop_ok:
                comment_service.relocate_comment(cid, nq, v.get("new_section_hint"),
                                                 actor="cast-comment-reanchor", db_path=DB)
                outcome = "relocated"
            else:
                comment_service.orphan_comment(cid, actor="fr019-backstop", db_path=DB)
                outcome = "relocate_rejected_downgraded_to_orphan"
            applied.append(dict(id=cid, case=by_id[cid]["case"], verdict="relocated",
                                new_quoted_text=nq, backstop_ok=backstop_ok, outcome=outcome,
                                confidence=v.get("confidence")))
        else:  # orphaned
            comment_service.orphan_comment(cid, actor="cast-comment-reanchor", db_path=DB)
            applied.append(dict(id=cid, case=by_id[cid]["case"], verdict="orphaned",
                                new_quoted_text=None, backstop_ok=True, outcome="orphaned",
                                confidence=v.get("confidence")))

    # Build the v2 measurement set: open comments use their CURRENT quoted_text (relocated ones
    # now carry the new span). Orphaned comments are tray-only — excluded from placement.
    open_now = comment_service.list_comments(SLUG, state="open", current_text=EDITED, db_path=DB)
    open_by_id = {c["id"]: c for c in open_now}
    measure_set = [
        dict(id=cid, case=by_id[cid]["case"], intended=by_id[cid]["intended"],
             cur_quote=open_by_id[cid]["quoted_text"])
        for cid in sorted(open_by_id)
    ]
    v2 = _measure(V2_HTML, measure_set, "cur_quote")

    orphaned_ids = sorted(c["id"] for c in
                          comment_service.list_comments(SLUG, state="orphaned", db_path=DB))
    deleted_id = next(c["id"] for c in state["comments"] if c["case"] == "delete")

    # --- diff_blocks determinism + partition invariant (maker HTML plays NO role here) ---
    old = parser.parse_requirements(ORIGINAL)
    new = parser.parse_requirements(EDITED)
    d1 = block_diff.diff_blocks(old, new)
    d2 = block_diff.diff_blocks(old, new)
    s1 = block_diff.summarize(d1)
    s2 = block_diff.summarize(d2)
    deterministic = (json.dumps(s1, sort_keys=True) == json.dumps(s2, sort_keys=True))

    # Partition invariant: every old block exactly once across removed ∪ modified.old ∪ unchanged.old
    old_seen = ([id(b) for b in d1.removed]
                + [id(m.old) for m in d1.modified]
                + [id(m.old) for m in d1.unchanged])
    new_seen = ([id(b) for b in d1.added]
                + [id(m.new) for m in d1.modified]
                + [id(m.new) for m in d1.unchanged])
    old_ok = (sorted(old_seen) == sorted(id(b) for b in old.blocks)) and len(old_seen) == len(set(old_seen))
    new_ok = (sorted(new_seen) == sorted(id(b) for b in new.blocks)) and len(new_seen) == len(set(new_seen))

    removed_refs = sorted(b.ref for b in d1.removed if b.ref)
    added_refs = sorted(b.ref for b in d1.added if b.ref)
    modified_refs = sorted(m.new.ref for m in d1.modified if m.new.ref)

    metrics = dict(
        applied=applied,
        v2=v2,
        orphaned_ids=orphaned_ids,
        deleted_comment_id=deleted_id,
        only_deleted_orphaned=(orphaned_ids == [deleted_id]),
        surviving_all_placed=all(r["in_intended"] for r in v2),
        v2_placement_rate=f"{sum(r['in_intended'] for r in v2)}/{len(v2)}",
        diff=dict(
            deterministic=deterministic,
            partition_old_ok=old_ok, partition_new_ok=new_ok,
            counts=s1["counts"],
            removed_refs=removed_refs, added_refs=added_refs, modified_refs=modified_refs,
        ),
    )
    (HERE / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("=== APPLY ===")
    for a in applied:
        print(f"  {a['case']:<8} id={a['id']} verdict={a['verdict']:<10} "
              f"backstop_ok={a['backstop_ok']} -> {a['outcome']}  conf={a['confidence']}")
    print(f"orphaned ids={orphaned_ids}  (deleted comment id={deleted_id})")
    print(f"only the deleted-block comment orphaned: {metrics['only_deleted_orphaned']}")
    print("v2 placement (scoped to intended unit):")
    for r in v2:
        flag = "OK " if r["in_intended"] else ("FALSE-PLACE" if r["found"] else "MISS")
        print(f"  [{flag:>11}] {r['case']:<8} id={r['id']} intended={r['intended']:<7} landed={r['landed']}")
    print(f"v2 placement rate (surviving): {metrics['v2_placement_rate']}")
    print(f"diff deterministic={deterministic} partition_old_ok={old_ok} partition_new_ok={new_ok}")
    print(f"diff counts={s1['counts']} removed={removed_refs} added={added_refs} modified={modified_refs}")


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"build": build, "apply": apply}[phase]()
