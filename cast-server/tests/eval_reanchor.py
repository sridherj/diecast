#!/usr/bin/env python
"""Build-time eval for the ``cast-comment-reanchor`` agent (Phase 4, sp4b — decision #9).

This is the **manual / slow** correctness gate for the re-anchor subagent. The agent is an LLM
worker with no pytest of its own; its contract is "displaced comments + old/new document text in,
``relocated``/``orphaned`` verdicts out, NEVER inventing text." This harness exercises exactly
that against the frozen Phase-1 fixture and its sp2 ``.v2-edit`` sibling, with three pre-seeded
comments engineered to hit each branch:

* **reworded**  — FR-001 was reworded between versions; its old quote is no longer verbatim, but
  the same content survives. Gate: verdict ``relocated`` with a ``new_quoted_text`` that is a
  **verbatim substring of the new document**.
* **deleted**   — the "exploration pipeline" exclusion line was removed entirely. Gate: ``orphaned``.
* **control**   — an unchanged bullet that still exists verbatim. Gate: not orphaned, and any
  ``new_quoted_text`` it returns is verbatim-present (it must never invent text either).

The load-bearing gate across ALL verdicts: **zero invented text** — every ``relocated``
``new_quoted_text`` must be a literal substring of the new document. That mirrors the server-side
422 backstop (``POST .../relocate`` rejects a non-verbatim quote), so a passing eval predicts a
loop that cannot silently mis-place a comment.

Deliberately **excluded from default CI**: named ``eval_*`` (not ``test_*``), and a live run shells
out to the ``claude`` CLI (slow + network). Run it by hand:

    # Live run against the in-repo fixtures (slow — one reanchor dispatch):
    uv run --project cast-server python cast-server/tests/eval_reanchor.py --live

    # Offline replay from a saved verdict file (deterministic, no network):
    uv run --project cast-server python cast-server/tests/eval_reanchor.py \
        --verdicts cast-server/tests/fixtures/reanchor_verdicts.json

    # Structural pre-check only (fast, no model): config keys + allow-list pin.
    uv run --project cast-server python cast-server/tests/eval_reanchor.py --structural-only

On failure, the *first* lever is the agent prompt (``cast-comment-reanchor.md`` matching rules /
the orphan-over-guess instruction), then ``model: sonnet -> opus`` — never the verbatim-substring
invariant, which is the whole point.
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

import yaml

# --- Make repo paths resolvable when run as a standalone script (mirrors eval_classifier_corpus) ---
_CAST_SERVER_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _CAST_SERVER_DIR.parent
_REANCHOR_PROMPT = _REPO_ROOT / "agents" / "cast-comment-reanchor" / "cast-comment-reanchor.md"
_REANCHOR_CONFIG = _REPO_ROOT / "agents" / "cast-comment-reanchor" / "config.yaml"
_REFINE_CONFIG = _REPO_ROOT / "agents" / "cast-refine-requirements" / "config.yaml"
_FIXTURE_DIR = _CAST_SERVER_DIR / "tests" / "fixtures" / "refine_requirements_v2"
_OLD_FIXTURE = _FIXTURE_DIR / "refined_requirements.collab.md"
_NEW_FIXTURE = _FIXTURE_DIR / "refined_requirements.v2-edit.collab.md"
# Golden contract-v2 reply for offline replay (sp4b-2). Deterministic, no model.
_V2_GOLDEN = _CAST_SERVER_DIR / "tests" / "fixtures" / "reanchor_verdicts_v2.json"

# cast_server is importable under `uv run --project cast-server`; the render package is pure
# (no I/O at import). These power the deterministic v2 gates (change-set keys, block context).
sys.path.insert(0, str(_CAST_SERVER_DIR))
from cast_server.requirements_render.block_diff import diff_blocks, summarize  # noqa: E402
from cast_server.requirements_render.comment_anchor import resolve_block_context  # noqa: E402
from cast_server.requirements_render.parser import parse_requirements  # noqa: E402

# Canonical subagent config keys (the Naming Contract in _shared_context.md).
_CANONICAL_CONFIG = {
    "model": "sonnet",
    "dispatch_mode": "subagent",
    "interactive": False,
    "context_mode": "lightweight",
    "timeout_minutes": 15,  # bumped in sp4b-2 — contract v2 narration adds output volume
}

# The three pre-seeded comments. `expect` is the gated branch; ids are arbitrary but stable.
_COMMENTS = [
    {
        "id": 101,
        "quoted_text": (
            "The refined output shall lead with WHAT content; HOW content shall be confined "
            "to a clearly-marked, non-binding"
        ),
        "section_hint": "Functional Requirements",
        "body": "Make sure HOW stays non-binding after the reword.",
        "expect": "relocated",
    },
    {
        "id": 102,
        "quoted_text": "Changes to the exploration pipeline (cast-explore) itself.",
        "section_hint": "Out of Scope",
        "body": "Is cast-explore still out of scope?",
        "expect": "orphaned",
    },
    {
        "id": 103,
        "quoted_text": "Workflow classification could surface as standard pills at the top of the document.",
        "section_hint": "Directional Ideas",
        "body": "Like this pill idea — keep it.",
        "expect": "control",  # unchanged content; must not be orphaned, must not invent text
    },
]


# ---------------------------------------------------------------------------
# Structural pre-check (fast, no model) — the cheap permanent-style gate
# ---------------------------------------------------------------------------
def structural_check() -> list[str]:
    """Return a list of failure strings (empty == pass). Pins the five canonical config keys
    and the cast-refine-requirements allow-list footgun (sp4b adds cast-comment-reanchor)."""
    failures: list[str] = []

    if not _REANCHOR_CONFIG.is_file():
        return [f"missing config: {_REANCHOR_CONFIG}"]
    cfg = yaml.safe_load(_REANCHOR_CONFIG.read_text(encoding="utf-8")) or {}
    for key, want in _CANONICAL_CONFIG.items():
        if cfg.get(key) != want:
            failures.append(f"config.yaml[{key!r}] = {cfg.get(key)!r}, expected {want!r}")

    if not _REANCHOR_PROMPT.is_file():
        failures.append(f"missing prompt: {_REANCHOR_PROMPT}")

    refine = yaml.safe_load(_REFINE_CONFIG.read_text(encoding="utf-8")) or {}
    if "cast-comment-reanchor" not in (refine.get("allowed_delegations") or []):
        failures.append("cast-refine-requirements/config.yaml allowed_delegations is missing 'cast-comment-reanchor'")

    return failures


# ---------------------------------------------------------------------------
# Live dispatch + parse (mirrors eval_classifier_corpus.classify_live)
# ---------------------------------------------------------------------------
def reanchor_live(old_content: str, new_content: str, comments: list[dict],
                  model: str = "sonnet", timeout_s: int = 240) -> dict:
    """Run the real re-anchor prompt over the displaced comments via ``claude -p`` and parse its
    bare-JSON reply. The prompt file is the single source of truth, so this exercises what ships."""
    prompt = _REANCHOR_PROMPT.read_text(encoding="utf-8")
    payload = {
        "comments": [{k: c[k] for k in ("id", "quoted_text", "section_hint", "body")} for c in comments],
        "old_content": old_content,
        "new_content": new_content,
    }
    user_msg = json.dumps(payload, ensure_ascii=False)
    # `--tools ""` disables all tools: the agent is pure text-in/JSON-out and must never act.
    proc = subprocess.run(
        ["claude", "-p", user_msg, "--append-system-prompt", prompt, "--model", model, "--tools", ""],
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {proc.stderr.strip()[:400]}")
    return _parse_verdict_json(proc.stdout)


def _parse_verdict_json(raw: str) -> dict:
    """Extract the single JSON object from a verdict reply (tolerant of stray fences)."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in reanchor output: {raw[:200]!r}")
    return json.loads(text[start:end + 1])


# ---------------------------------------------------------------------------
# Scoring / gate
# ---------------------------------------------------------------------------
def evaluate(verdicts_obj: dict, new_content: str) -> tuple[bool, list[str]]:
    """Apply the decision-#9 gate. Returns (passed, report_lines)."""
    lines: list[str] = []
    by_id = {v.get("comment_id"): v for v in verdicts_obj.get("verdicts", [])}

    # Global invariant first: zero invented text across ALL verdicts.
    invented = [
        v for v in verdicts_obj.get("verdicts", [])
        if v.get("verdict") == "relocated"
        and (v.get("new_quoted_text") or "") not in new_content
    ]
    no_invention = not invented
    lines.append(
        f"  [{'PASS' if no_invention else 'FAIL'}] zero invented text "
        f"({len(invented)} relocated verdict(s) with a non-verbatim quote)"
    )
    for v in invented:
        lines.append(f"        invented by comment {v.get('comment_id')}: {v.get('new_quoted_text')!r}")

    ok = no_invention
    for c in _COMMENTS:
        v = by_id.get(c["id"])
        verdict = (v or {}).get("verdict")
        if c["expect"] == "relocated":
            present = (v or {}).get("new_quoted_text", "") in new_content if v else False
            passed = verdict == "relocated" and present
            lines.append(
                f"  [{'PASS' if passed else 'FAIL'}] reworded comment {c['id']} -> "
                f"relocated(verbatim): got verdict={verdict!r}, verbatim_present={present}"
            )
        elif c["expect"] == "orphaned":
            passed = verdict == "orphaned"
            lines.append(
                f"  [{'PASS' if passed else 'FAIL'}] deleted comment {c['id']} -> "
                f"orphaned: got verdict={verdict!r}"
            )
        else:  # control: must not be orphaned; any quote it returns is already verbatim-checked above
            passed = verdict in ("relocated", None) and verdict != "orphaned"
            lines.append(
                f"  [{'PASS' if passed else 'FAIL'}] control comment {c['id']} -> "
                f"not orphaned: got verdict={verdict!r}"
            )
        ok = ok and passed

    return ok, lines


# ---------------------------------------------------------------------------
# Contract v2 (sp4b-2): narration + re-anchor/resolve/orphan, backward-compatible superset
# ---------------------------------------------------------------------------
_V2_VERDICTS = {"relocated", "resolved", "orphaned"}


def fixture_change_set() -> dict:
    """The deterministic `summarize(diff_blocks(old, new))` for the fixture pair — the v2
    `change_set` input AND the source of truth the narration's `item_notes` must key to."""
    old = parse_requirements(_OLD_FIXTURE.read_text(encoding="utf-8"))
    new = parse_requirements(_NEW_FIXTURE.read_text(encoding="utf-8"))
    return summarize(diff_blocks(old, new))


def _change_set_keys(change_set: dict) -> set[tuple[str, str]]:
    return {(it.get("change"), it.get("heading_or_ref")) for it in change_set.get("items", [])}


def reanchor_live_v2(old_content: str, new_content: str, comments: list[dict],
                     change_set: dict, model: str = "sonnet", timeout_s: int = 300) -> dict:
    """Live v2 dispatch: passes `change_set` + per-comment deterministic block context (via the
    pure `resolve_block_context`) so a live run exercises the superset, not just legacy verdicts."""
    prompt = _REANCHOR_PROMPT.read_text(encoding="utf-8")
    block_ctx = resolve_block_context(old_content, comments, change_set)
    payload_comments = []
    for c in comments:
        entry = {k: c[k] for k in ("id", "quoted_text", "section_hint", "body")}
        entry.update(block_ctx.get(c["id"], {}))  # block_ref/block_disposition only when resolved
        payload_comments.append(entry)
    payload = {"comments": payload_comments, "old_content": old_content,
               "new_content": new_content, "change_set": change_set}
    user_msg = json.dumps(payload, ensure_ascii=False)
    proc = subprocess.run(
        ["claude", "-p", user_msg, "--append-system-prompt", prompt, "--model", model, "--tools", ""],
        capture_output=True, text=True, timeout=timeout_s,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {proc.stderr.strip()[:400]}")
    return _parse_verdict_json(proc.stdout)


def validate_v2_schema(obj: dict, new_content: str, change_set: dict) -> list[str]:
    """Deterministic v2-schema gate (no model). Returns failure strings (empty == pass)."""
    fails: list[str] = []
    legal_keys = _change_set_keys(change_set)

    narration = obj.get("narration", None)
    if narration is not None:
        if not isinstance(narration, dict):
            fails.append("narration is neither null nor an object")
        else:
            if not isinstance(narration.get("overview"), str) or not narration.get("overview").strip():
                fails.append("narration.overview missing or not a non-empty string")
            notes = narration.get("item_notes")
            if not isinstance(notes, list):
                fails.append("narration.item_notes is not a list")
            else:
                for n in notes:
                    key = (n.get("change"), n.get("heading_or_ref"))
                    if key not in legal_keys:  # TRUST BOUNDARY — no invented items
                        fails.append(f"narration item_note keys an invented change: {key!r}")
                    if not isinstance(n.get("note"), str):
                        fails.append(f"item_note for {key!r} has a non-string note")

    verdicts = obj.get("verdicts")
    if not isinstance(verdicts, list) or not verdicts:
        fails.append("verdicts missing or empty")
        return fails
    for v in verdicts:
        verdict = v.get("verdict")
        cid = v.get("comment_id")
        if verdict not in _V2_VERDICTS:
            fails.append(f"comment {cid}: verdict {verdict!r} not in {sorted(_V2_VERDICTS)}")
        if verdict == "relocated":
            nqt = v.get("new_quoted_text") or ""
            if nqt not in new_content:
                fails.append(f"comment {cid}: relocated new_quoted_text not verbatim in new_content")
            if "**" in nqt or "`" in nqt:  # anchor-pickability / markdown-seam
                fails.append(f"comment {cid}: relocated new_quoted_text carries inline-markdown markers")
        elif verdict in ("resolved", "orphaned"):
            if v.get("new_quoted_text") is not None:
                fails.append(f"comment {cid}: {verdict} must have new_quoted_text=null")
    return fails


def v2_offline_selfcheck() -> tuple[bool, list[str]]:
    """Model-free v2 gate over the golden reply: schema + narration-keys + markdown-seam +
    backward-compat verdict gate, PLUS a negative trust-boundary case (an invented note must be
    rejected) and an over-eager-resolved guard (surviving content re-anchors, never resolves).

    Deterministic, fast, no network — this is what makes ``python eval_reanchor.py`` green offline.
    """
    lines: list[str] = []
    new_content = _NEW_FIXTURE.read_text(encoding="utf-8")
    change_set = fixture_change_set()
    golden = json.loads(_V2_GOLDEN.read_text(encoding="utf-8"))

    # 1. Golden passes the full v2 schema gate (schema + narration-keys + markdown-seam + verbatim).
    schema_fails = validate_v2_schema(golden, new_content, change_set)
    lines.append(f"  [{'PASS' if not schema_fails else 'FAIL'}] golden v2 reply passes the schema/trust/seam gate")
    for f in schema_fails:
        lines.append(f"        {f}")

    # 2. Backward-compat: the legacy three-comment verdict gate still holds on the golden verdicts.
    legacy_ok, _legacy_lines = evaluate(golden, new_content)
    lines.append(f"  [{'PASS' if legacy_ok else 'FAIL'}] golden verdicts satisfy the legacy decision-#9 gate (101 relocated/verbatim, 102 orphaned, 103 not-orphaned)")

    # 3. Narration emitted only WITH a change_set; legacy verdicts-only stays narration-free.
    legacy_only = {"verdicts": golden["verdicts"]}
    no_narr_fails = validate_v2_schema(legacy_only, new_content, change_set)
    lines.append(f"  [{'PASS' if not no_narr_fails else 'FAIL'}] legacy verdicts-only object (no narration) still validates (superset is backward-compatible)")

    # 4. Adversarial / trust boundary: an invented item_note MUST be rejected.
    poisoned = copy.deepcopy(golden)
    poisoned["narration"]["item_notes"].append(
        {"change": "modified", "heading_or_ref": "FR-999", "note": "a change absent from the deterministic set"}
    )
    rejected = any("invented change" in f for f in validate_v2_schema(poisoned, new_content, change_set))
    lines.append(f"  [{'PASS' if rejected else 'FAIL'}] adversarial: an invented item_note ('FR-999') is rejected by the trust-boundary gate")

    # 5. Over-eager resolved: comment 101's content survives (FR-001 reworded), so it MUST be
    #    relocated, never resolved (bias order relocated > resolved when content survives).
    v101 = next((v for v in golden["verdicts"] if v.get("comment_id") == 101), {})
    over_eager_ok = v101.get("verdict") == "relocated"
    lines.append(f"  [{'PASS' if over_eager_ok else 'FAIL'}] over-eager guard: surviving content (comment 101) re-anchors (relocated), not resolved")

    # 6. Block-context hint is derived deterministically (cross-boundary quote gets NO block_ref).
    ctx = resolve_block_context(_OLD_FIXTURE.read_text(encoding="utf-8"), _COMMENTS, change_set)
    hint_ok = ctx.get(101, {}).get("block_ref") == "FR-001" and "block_ref" not in ctx.get(102, {})
    lines.append(f"  [{'PASS' if hint_ok else 'FAIL'}] block-context: 101->FR-001(modified); 102 cross-boundary -> no block_ref (never guessed)")

    ok = (not schema_fails) and legacy_ok and (not no_narr_fails) and rejected and over_eager_ok and hint_ok
    return ok, lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true", help="dispatch the agent live via claude CLI (slow, network)")
    ap.add_argument("--v2", action="store_true", help="with --live, dispatch the contract-v2 payload (change_set + block context) and run the v2 schema gate")
    ap.add_argument("--verdicts", type=Path, help="replay a saved verdicts JSON file (offline)")
    ap.add_argument("--structural-only", action="store_true", help="config-keys + allow-list pin only (fast)")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--out-verdicts", type=Path, help="write the live verdicts to this path")
    args = ap.parse_args()

    print("=" * 78)
    print("REANCHOR EVAL  —  cast-comment-reanchor (Phase 4, sp4b, decision #9 + sp4b-2 contract v2)")
    print("=" * 78)

    # --- Structural pre-check (always runs) ---
    print("\n## Structural pre-check (config keys + allow-list pin)")
    failures = structural_check()
    if failures:
        for f in failures:
            print(f"  [FAIL] {f}")
    else:
        print("  [PASS] config has the five canonical keys; allow-list lists cast-comment-reanchor")
    structural_ok = not failures

    if args.structural_only:
        print("\nstructural-only:", "PASS" if structural_ok else "FAIL")
        return 0 if structural_ok else 1

    old_content = _OLD_FIXTURE.read_text(encoding="utf-8")
    new_content = _NEW_FIXTURE.read_text(encoding="utf-8")

    # --- Contract-v2 offline self-check (always runs; model-free, deterministic) ---
    print("\n## Contract-v2 offline self-check (sp4b-2 — schema, narration-keys, trust boundary, seam)")
    v2_ok, v2_lines = v2_offline_selfcheck()
    for ln in v2_lines:
        print(ln)

    # --- Obtain verdicts (live or replay) ---
    change_set = fixture_change_set()
    verdicts_obj = None
    if args.verdicts:
        verdicts_obj = json.loads(args.verdicts.read_text(encoding="utf-8"))
    elif args.live:
        mode = "v2" if args.v2 else "v1 (legacy verdicts-only)"
        print(f"\n## Dispatching cast-comment-reanchor (live, {mode}) ...")
        if args.v2:
            verdicts_obj = reanchor_live_v2(old_content, new_content, _COMMENTS, change_set, model=args.model)
        else:
            verdicts_obj = reanchor_live(old_content, new_content, _COMMENTS, model=args.model)
        if args.out_verdicts:
            args.out_verdicts.write_text(json.dumps(verdicts_obj, indent=2, ensure_ascii=False), encoding="utf-8")

    gate_ok = True
    if verdicts_obj is not None:
        print("\n## Verdict gate (decision #9)")
        gate_ok, lines = evaluate(verdicts_obj, new_content)
        for ln in lines:
            print(ln)
        if args.v2 or verdicts_obj.get("narration") is not None:
            print("\n## Contract-v2 schema gate (live/replay output)")
            schema_fails = validate_v2_schema(verdicts_obj, new_content, change_set)
            if schema_fails:
                for f in schema_fails:
                    print(f"  [FAIL] {f}")
                gate_ok = False
            else:
                print("  [PASS] v2 schema, narration-keys, trust boundary, and markdown-seam hold")
    else:
        print("\n(no --live / --verdicts given — ran structural + v2 offline self-check only)")

    overall = structural_ok and v2_ok and gate_ok
    print("\n" + "=" * 78)
    print("RESULT:", "PASS" if overall else "FAIL")
    print("=" * 78)
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
