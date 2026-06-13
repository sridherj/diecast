#!/usr/bin/env python3
"""Sub-phase 1a — UPDATE byte-fidelity spike harness (THROWAWAY measurement; no production edits).

Answers the one load-bearing unknown: *can the production `cast-requirements-how` agent hold
unchanged unit containers byte-identical when handed a prior render + a `block_diff` changed-set
and a copy-exact obligation?* The verdict selects the Sub-phase 3b UPDATE mechanism
(PASS -> gate-enforced-llm-copy ; FAIL -> deterministic-splice).

It drives the REAL agents (`cast-requirements-what`, `cast-requirements-how`) through the same
`ProductionAgentRunner` subprocess path the production pipeline uses, and measures unchanged-unit
byte-identity with the SHARED `container_text_index` walker (imported, never re-walked).

Read-only against production code. Nothing here is imported by the app; this whole directory is
spike evidence.

Usage:
    python harness.py --doc bug_fix --trials 5
    python harness.py --all --trials 5        # 3 docs x 5 trials (+1 WHAT per doc)
    python harness.py --aggregate             # recompute verdict.md from existing trial JSON
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

# --------------------------------------------------------------------------------------
# Locate the repo root (the dir that contains `cast-server/`) and import production code.
# --------------------------------------------------------------------------------------
HERE = Path(__file__).resolve()
REPO = next(p for p in HERE.parents if (p / "cast-server").is_dir())
sys.path.insert(0, str(REPO / "cast-server"))

from cast_server.requirements_render import parse_requirements  # noqa: E402
from cast_server.requirements_render.block_diff import diff_blocks, summarize  # noqa: E402
from cast_server.requirements_render.maker_gate import container_text_index  # noqa: E402
from cast_server.services.render_job_service import (  # noqa: E402
    ProductionAgentRunner,
    _build_how_prompt,
    _build_what_prompt,
    extract_render,
)

SPIKE_DIR = HERE.parent
CORPUS = REPO / "cast-server" / "tests" / "fixtures" / "family_corpus"
GOLDEN = (
    REPO / "docs" / "goal" / "refine-requirements-better-rendering-v3"
    / "signoff" / "golden"
)
EDITS_DIR = SPIKE_DIR / "edits"
TRIALS_DIR = SPIKE_DIR / "trials"

WHAT_AGENT = "cast-requirements-what"
HOW_AGENT = "cast-requirements-how"
WHAT_TIMEOUT_S = 15 * 60
HOW_TIMEOUT_S = 20 * 60


# --------------------------------------------------------------------------------------
# Edits: surgical, isolated source changes per doc. Each is applied EXACTLY ONCE (loud on miss).
#   old_marks  -> distinctive OLD-side substrings that mark a render container as CHANGED
#                 (so a regrouped ref-less render container that absorbed an edit is excluded
#                  from the unchanged set even without a canonical ref).
#   new_marks  -> distinctive NEW-side substrings used to confirm added/modified blocks rendered.
#   gone_marks -> OLD-side substrings that MUST be absent from the candidate (removed-block drop).
# --------------------------------------------------------------------------------------
@dataclass
class Edit:
    find: str
    replace: str


@dataclass
class DocSpec:
    name: str
    edits: list[Edit]
    changed_refs: set[str]
    old_marks: list[str]
    new_marks: list[str]
    gone_marks: list[str]


DOCS: dict[str, DocSpec] = {
    "bug_fix": DocSpec(
        name="bug_fix",
        edits=[
            # 1) modified FR body (FR-002 — append a clause; ref preserved -> "modified")
            Edit(
                find="while staying a single contiguous `<li>` with no fragmenting spans.",
                replace="while staying a single contiguous `<li>` with no fragmenting spans. "
                "The kicker line directly above the assertions resolves inline markdown the same way.",
            ),
            # 2) added SC (SC-004)
            Edit(
                find="| SC-003 | A markdown-free source renders a byte-identical Goal Card to the "
                "pre-fix output. | Golden-snapshot diff on an emphasis-free fixture. |",
                replace="| SC-003 | A markdown-free source renders a byte-identical Goal Card to the "
                "pre-fix output. | Golden-snapshot diff on an emphasis-free fixture. |\n"
                "| SC-004 | The kicker line above the Goal Card assertions renders inline markdown "
                "with zero literal markdown characters visible. | Render a fixture whose kicker "
                "carries backtick-code and assert no backticks survive. |",
            ),
            # 3) removed bullet (the Open Questions DEFERRED bullet)
            Edit(
                find="\n- **[DEFERRED]** Whether the sibling `_first_sentence` "
                "abbreviation-truncation defect should be fixed in the same change or tracked as "
                "its own bug. Leaning separate — different root cause, different test, and bundling "
                "risks scope creep in a one-file fix.\n",
                replace="\n",
            ),
        ],
        changed_refs={"FR-002", "SC-004"},
        old_marks=["abbreviation-truncation defect should be fixed in the same change"],
        new_marks=["kicker line above the Goal Card assertions renders inline markdown"],
        gone_marks=["abbreviation-truncation defect should be fixed in the same change"],
    ),
    "data_analysis": DocSpec(
        name="data_analysis",
        edits=[
            # 1) modified evidence bullet (ref-less -> drops to removed+added in block_diff; fine)
            Edit(
                find="A live capture showed the API returning 2 running while the database held 7.",
                replace="A live capture showed the API returning 1 running while the database held 7.",
            ),
            # 2) added evidence bullet
            Edit(
                find="- **The signature is diagnostic.**",
                replace="- **The reaper never fires on idle panes.** The monitor's terminal-output "
                "contract has no idle-timeout branch, so a session parked at a selection menu is "
                "indistinguishable from one mid-task and is never reaped.\n"
                "- **The signature is diagnostic.**",
            ),
            # 3) removed bullet (Open Questions DEFERRED)
            Edit(
                find="\n- **[DEFERRED]** Whether the status API's `running` filter should be "
                "reconciled to the raw DB count, or whether the divergence is intentional and only "
                "the documentation needs to warn against trusting it.\n",
                replace="\n",
            ),
        ],
        changed_refs=set(),
        old_marks=[
            "returning 2 running while the database held 7",
            "running` filter should be",
            "filter should be reconciled to the raw DB count",
        ],
        new_marks=["reaper never fires on idle panes"],
        gone_marks=[
            "returning 2 running while the database held 7",
            "reconciled to the raw DB count, or whether the divergence is intentional",
        ],
    ),
    "new_initiative": DocSpec(
        name="new_initiative",
        edits=[
            # 1) modified FR body (FR-005 — append a clause; ref preserved -> "modified")
            Edit(
                find="reusing the v2 embedded-source-hash lazy-regeneration mechanism unchanged.",
                replace="reusing the v2 embedded-source-hash lazy-regeneration mechanism unchanged. "
                "The cache key additionally folds in the resolved work-family so a re-classification "
                "forces a fresh render.",
            ),
            # 2) added SC (SC-009)
            Edit(
                find="| SC-008 | On non-convergence, the reader is served the best-scoring attempt "
                "with a human-review flag recorded, never the plain deterministic page. | Force the "
                "checker to never pass; confirm best-attempt is served and a flag is raised. |",
                replace="| SC-008 | On non-convergence, the reader is served the best-scoring "
                "attempt with a human-review flag recorded, never the plain deterministic page. | "
                "Force the checker to never pass; confirm best-attempt is served and a flag is "
                "raised. |\n"
                "| SC-009 | A re-classification of a goal's work family invalidates its cached "
                "render and forces a regenerate, even when the source bytes are unchanged. | "
                "Re-classify a fixture and confirm a fresh maker call. |",
            ),
            # 3) removed bullet (Out of Scope)
            Edit(
                find="\n- Rendering documents other than refined requirements.",
                replace="",
            ),
        ],
        changed_refs={"FR-005", "SC-009"},
        old_marks=["Rendering documents other than refined requirements"],
        new_marks=["folds in the resolved work-family so a re-classification"],
        gone_marks=["Rendering documents other than refined requirements"],
    ),
}


# --------------------------------------------------------------------------------------
# Raw-HTML unit-slice extractor: byte-faithful outerHTML per unit element (li/section/article/
# *-unit div) so we can compare RAW bytes, not just walker text. Offsets tracked via getpos().
# --------------------------------------------------------------------------------------
_UNIT_TAGS = frozenset({"li", "section", "article"})
_UNIT_DIV_CLASSES = frozenset({"user-story", "rr-unit", "req-unit"})
_VOID = frozenset({"meta", "br", "img", "hr", "input", "link", "source", "area", "base", "col", "wbr"})


def _is_unit_tag(tag: str, classes: frozenset[str]) -> bool:
    if tag in _UNIT_TAGS:
        return True
    if tag in ("div", "aside"):
        return bool(classes & _UNIT_DIV_CLASSES or any(c.endswith("-unit") for c in classes))
    return False


class _RawUnitParser(HTMLParser):
    """Record the raw outerHTML byte-span of every requirement-unit element."""

    def __init__(self, html: str) -> None:
        super().__init__(convert_charrefs=True)
        self._html = html
        self._line_starts = [0]
        for i, ch in enumerate(html):
            if ch == "\n":
                self._line_starts.append(i + 1)
        self._stack: list[tuple[str, int, bool]] = []  # (tag, abs_start, is_unit)
        self.units: list[str] = []

    def _abs(self) -> int:
        line, col = self.getpos()
        return self._line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in _VOID:
            return
        classes = frozenset((dict(attrs).get("class") or "").split())
        self._stack.append((tag, self._abs(), _is_unit_tag(tag, classes)))

    def handle_startendtag(self, tag, attrs):  # self-closing: never a unit container with text
        pass

    def handle_endtag(self, tag):
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                t, start, is_unit = self._stack[i]
                end = self._abs() + len(f"</{tag}>")
                if is_unit:
                    self.units.append(self._html[start:end])
                del self._stack[i:]
                return


def raw_unit_slices(html: str) -> list[str]:
    p = _RawUnitParser(html)
    p.feed(html)
    p.close()
    return p.units


# --------------------------------------------------------------------------------------
# A minimal JobState stand-in: the two prompt builders only read these attributes.
# --------------------------------------------------------------------------------------
@dataclass
class _St:
    goal_slug: str
    source_hash: str
    parsed: object
    family: str | None
    what_doc: str | None = None
    open_gap_markers: list = field(default_factory=list)


# No trailing \b: in a rendered unit container the anchor id is concatenated directly to the
# following text node ("FR-002Functional requirement …"), so a trailing word boundary never
# matches. A leading negative-lookbehind keeps us from matching inside a larger token.
_REF_RE = re.compile(r"(?<![A-Za-z0-9])(US|FR|SC)-?(\d+)")


def _refs_in(text: str) -> set[str]:
    return {f"{m.group(1)}{m.group(2)}" for m in _REF_RE.finditer(text)}


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------------------------------
# Edits + UPDATE prompt
# --------------------------------------------------------------------------------------
def apply_edits(old_src: str, spec: DocSpec) -> str:
    new_src = old_src
    for e in spec.edits:
        n = new_src.count(e.find)
        if n != 1:
            raise SystemExit(
                f"[{spec.name}] edit not applied exactly once (count={n}): {e.find[:60]!r}"
            )
        new_src = new_src.replace(e.find, e.replace)
    return new_src


def build_update_prompt(state: _St, prior_html: str, change_summary: dict) -> str:
    create_shape = _build_how_prompt(state)
    update_section = (
        "\n========== UPDATE MODE (this is an UPDATE of an existing render, NOT a fresh CREATE) "
        "==========\n"
        "A prior PUBLISHED render of this page already exists (inlined below). The source changed "
        "ONLY in the blocks named in the CHANGED-SET. Your obligations, in priority order:\n"
        "  1. COPY every unchanged unit container BYTE-EXACT from the prior render — identical "
        "text, identical markup, identical attributes, identical whitespace. Do NOT paraphrase, "
        "re-word, re-order, re-format, or 'improve' any block that is not named in the CHANGED-SET.\n"
        "  2. RE-RENDER only the added/modified blocks named in the CHANGED-SET, in the prior "
        "page's existing structure and visual style.\n"
        "  3. DROP every block named 'removed' in the CHANGED-SET.\n"
        "  4. Emit the COMPLETE self-contained page (head + body) between the same sentinels, "
        "exactly as in CREATE mode. Keep every anchor id verbatim.\n"
        "\n----- BEGIN PRIOR PUBLISHED RENDER (copy unchanged containers byte-exact) -----\n"
        f"{prior_html}\n"
        "----- END PRIOR PUBLISHED RENDER -----\n"
        "\n----- BEGIN CHANGED-SET (block_diff.summarize — the ONLY blocks you may add/re-render/"
        "drop) -----\n"
        f"{json.dumps(change_summary, indent=2)}\n"
        "----- END CHANGED-SET -----\n"
    )
    return create_shape + update_section


# --------------------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------------------
def measure(prior_html: str, cand_html: str, spec: DocSpec) -> dict:
    prior_idx = container_text_index(prior_html)
    cand_idx = container_text_index(cand_html)
    cand_text = cand_idx.document_text

    prior_units = list(prior_idx.units())
    prior_raw = raw_unit_slices(prior_html)
    # Pair walker-units with raw slices by matched normalized text (best-effort; raw used only as a
    # secondary strict signal). Build a lookup: normalized walker text -> raw slice.
    raw_by_text: dict[str, str] = {}
    for r in prior_raw:
        rt = _norm_ws(container_text_index(r).document_text)
        raw_by_text.setdefault(rt, r)

    changed_refs_norm = {r.replace("-", "") for r in spec.changed_refs}

    def is_changed(unit_text: str) -> bool:
        # _refs_in strips hyphens (FR-002 -> FR002); normalize the spec side to match so a
        # modified/added ref-bearing container is correctly excluded from the UNCHANGED set.
        if changed_refs_norm and (_refs_in(unit_text) & changed_refs_norm):
            return True
        return any(m in unit_text for m in spec.old_marks)

    expected_unchanged = [c for c in prior_units if not is_changed(c.text)]

    text_survive = 0
    raw_survive = 0
    whitespace_only = 0
    reworded = 0
    nonsurvivors: list[dict] = []
    for c in expected_unchanged:
        t = c.text
        text_ok = t in cand_text
        if text_ok:
            text_survive += 1
        else:
            if _norm_ws(t) in _norm_ws(cand_text):
                whitespace_only += 1
                kind = "whitespace-only"
            else:
                reworded += 1
                kind = "reworded"
            nonsurvivors.append({"kind": kind, "text_excerpt": _norm_ws(t)[:160]})
        raw = raw_by_text.get(_norm_ws(t))
        if raw is not None and raw in cand_html:
            raw_survive += 1

    n = len(expected_unchanged)
    # changed-block correctness / removed-block drop
    added_modified_ok = all(m in cand_text for m in spec.new_marks)
    removed_dropped = all(m not in cand_text for m in spec.gone_marks)

    return {
        "prior_units_total": len(prior_units),
        "expected_unchanged": n,
        "text_byte_identical": text_survive,
        "raw_byte_identical": raw_survive,
        "text_identity_rate": (text_survive / n) if n else None,
        "raw_identity_rate": (raw_survive / n) if n else None,
        "divergence_whitespace_only": whitespace_only,
        "divergence_reworded": reworded,
        "added_modified_rendered": added_modified_ok,
        "removed_block_dropped": removed_dropped,
        "nonsurvivors": nonsurvivors,
    }


# --------------------------------------------------------------------------------------
# Per-doc setup (edits + WHAT once) and trials (HOW xN)
# --------------------------------------------------------------------------------------
def log(msg: str) -> None:
    print(msg, flush=True)


def setup_doc(spec: DocSpec, runner_cwd: Path) -> dict:
    old_src = (CORPUS / spec.name / "refined_requirements.collab.md").read_text(encoding="utf-8")
    new_src = apply_edits(old_src, spec)
    doc_edits = EDITS_DIR / spec.name
    doc_edits.mkdir(parents=True, exist_ok=True)
    (doc_edits / "new.collab.md").write_text(new_src, encoding="utf-8")

    parsed_old = parse_requirements(old_src)
    parsed_new = parse_requirements(new_src)
    diff = diff_blocks(parsed_old, parsed_new)
    change_summary = summarize(diff)
    (doc_edits / "changed-set.json").write_text(json.dumps(change_summary, indent=2), encoding="utf-8")

    prior_html = (GOLDEN / f"{spec.name}.html").read_text(encoding="utf-8")

    # Generate the WHAT doc for the NEW source via the production WHAT agent (once; reused across
    # trials so trial variance is purely HOW stochasticity).
    state = _St(
        goal_slug=f"spike-{spec.name}",
        source_hash=parsed_new.content_hash,
        parsed=parsed_new,
        family=spec.name,
    )
    runner = ProductionAgentRunner(runner_cwd)
    log(f"[{spec.name}] running WHAT (new source)…")
    what_raw = runner.run_agent(WHAT_AGENT, _build_what_prompt(state), timeout_s=WHAT_TIMEOUT_S)
    state.what_doc = what_raw
    (TRIALS_DIR / spec.name).mkdir(parents=True, exist_ok=True)
    (TRIALS_DIR / spec.name / "what.md").write_text(what_raw, encoding="utf-8")

    update_prompt = build_update_prompt(state, prior_html, change_summary)
    (TRIALS_DIR / spec.name / "update-prompt.txt").write_text(update_prompt, encoding="utf-8")

    return {
        "spec": spec,
        "state": state,
        "prior_html": prior_html,
        "update_prompt": update_prompt,
        "change_summary": change_summary,
        "runner": runner,
    }


def run_trials(ctx: dict, trials: int) -> list[dict]:
    spec: DocSpec = ctx["spec"]
    out = TRIALS_DIR / spec.name
    out.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    for i in range(1, trials + 1):
        log(f"[{spec.name}] HOW trial {i}/{trials}…")
        try:
            raw = ctx["runner"].run_agent(HOW_AGENT, ctx["update_prompt"], timeout_s=HOW_TIMEOUT_S)
        except Exception as exc:  # noqa: BLE001 — a crash is a trial datum, not a harness abort
            log(f"[{spec.name}] trial {i} agent error: {exc}")
            rec = {"trial": i, "error": str(exc), "extractable": False}
            (out / f"trial-{i}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
            results.append(rec)
            continue
        cand = extract_render(raw)
        (out / f"trial-{i}.raw.txt").write_text(raw or "", encoding="utf-8")
        if cand is None:
            rec = {"trial": i, "extractable": False, "note": "no extractable render (sentinel miss)"}
            (out / f"trial-{i}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
            results.append(rec)
            continue
        (out / f"trial-{i}.html").write_text(cand, encoding="utf-8")
        m = measure(ctx["prior_html"], cand, spec)
        rec = {"trial": i, "extractable": True, **m}
        (out / f"trial-{i}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        log(
            f"[{spec.name}] trial {i}: text={m['text_byte_identical']}/{m['expected_unchanged']} "
            f"raw={m['raw_byte_identical']}/{m['expected_unchanged']} "
            f"(ws={m['divergence_whitespace_only']} reworded={m['divergence_reworded']}) "
            f"add/mod_ok={m['added_modified_rendered']} removed_dropped={m['removed_block_dropped']}"
        )
        results.append(rec)
    return results


# --------------------------------------------------------------------------------------
# Aggregation + verdict
# --------------------------------------------------------------------------------------
def aggregate() -> dict:
    docs = {}
    for name in DOCS:
        doc_dir = TRIALS_DIR / name
        if not doc_dir.is_dir():
            continue
        trials = []
        for f in sorted(doc_dir.glob("trial-*.json")):
            trials.append(json.loads(f.read_text(encoding="utf-8")))
        if not trials:
            continue
        valid = [t for t in trials if t.get("extractable")]
        tot_unchanged = sum(t["expected_unchanged"] for t in valid)
        tot_text = sum(t["text_byte_identical"] for t in valid)
        tot_raw = sum(t["raw_byte_identical"] for t in valid)
        ws = sum(t["divergence_whitespace_only"] for t in valid)
        rw = sum(t["divergence_reworded"] for t in valid)
        docs[name] = {
            "trials_total": len(trials),
            "trials_extractable": len(valid),
            "unchanged_containers_measured": tot_unchanged,
            "text_byte_identical": tot_text,
            "raw_byte_identical": tot_raw,
            "text_identity_pct": (100.0 * tot_text / tot_unchanged) if tot_unchanged else None,
            "raw_identity_pct": (100.0 * tot_raw / tot_unchanged) if tot_unchanged else None,
            "divergence_whitespace_only": ws,
            "divergence_reworded": rw,
            "added_modified_rendered_all": all(t["added_modified_rendered"] for t in valid) if valid else False,
            "removed_block_dropped_all": all(t["removed_block_dropped"] for t in valid) if valid else False,
            "per_trial_raw_rate": [t["raw_identity_rate"] for t in valid],
            "per_trial_text_rate": [t["text_identity_rate"] for t in valid],
        }
    return docs


def write_verdict(docs: dict) -> None:
    # PASS iff every doc has >=5 extractable trials AND raw byte-identity >= 95% per doc.
    BAR = 95.0
    MIN_TRIALS = 5
    per_doc_pass = {}
    for name, d in docs.items():
        ok = (
            d["trials_extractable"] >= MIN_TRIALS
            and d["raw_identity_pct"] is not None
            and d["raw_identity_pct"] >= BAR
        )
        per_doc_pass[name] = ok
    all_present = set(docs) >= set(DOCS)
    verdict = "PASS" if (all_present and all(per_doc_pass.values())) else "FAIL"
    mechanism = "gate-enforced-llm-copy" if verdict == "PASS" else "deterministic-splice"

    tot_unchanged = sum(d["unchanged_containers_measured"] for d in docs.values())
    tot_raw = sum(d["raw_byte_identical"] for d in docs.values())
    tot_text = sum(d["text_byte_identical"] for d in docs.values())
    overall_raw = (100.0 * tot_raw / tot_unchanged) if tot_unchanged else 0.0
    overall_text = (100.0 * tot_text / tot_unchanged) if tot_unchanged else 0.0
    ws = sum(d["divergence_whitespace_only"] for d in docs.values())
    rw = sum(d["divergence_reworded"] for d in docs.values())

    (SPIKE_DIR / "aggregate.json").write_text(
        json.dumps(
            {"verdict": verdict, "mechanism": mechanism, "per_doc": docs,
             "per_doc_pass": per_doc_pass, "overall_raw_pct": overall_raw,
             "overall_text_pct": overall_text, "whitespace_only": ws, "reworded": rw},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n=== AGGREGATE ===\nVERDICT: {verdict}\nMECHANISM: {mechanism}")
    print(f"overall raw byte-identity: {overall_raw:.1f}%   text byte-identity: {overall_text:.1f}%")
    for name, d in docs.items():
        print(
            f"  {name}: raw={d['raw_identity_pct']}% text={d['text_identity_pct']}% "
            f"trials={d['trials_extractable']}/{d['trials_total']} "
            f"unchanged={d['unchanged_containers_measured']} pass={per_doc_pass[name]}"
        )
    print(f"divergence: whitespace-only={ws}  reworded={rw}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", choices=list(DOCS))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument(
        "--remeasure", action="store_true",
        help="re-run measure() over already-saved trial-*.html (no agent calls), rewrite JSON",
    )
    args = ap.parse_args()

    if args.remeasure:
        for name, spec in DOCS.items():
            prior_html = (GOLDEN / f"{name}.html").read_text(encoding="utf-8")
            doc_dir = TRIALS_DIR / name
            for html_f in sorted(doc_dir.glob("trial-*.html")):
                i = int(re.search(r"trial-(\d+)", html_f.name).group(1))
                cand = html_f.read_text(encoding="utf-8")
                rec = {"trial": i, "extractable": True, **measure(prior_html, cand, spec)}
                (doc_dir / f"trial-{i}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
                log(
                    f"[{name}] trial {i}: text={rec['text_byte_identical']}/"
                    f"{rec['expected_unchanged']} raw={rec['raw_byte_identical']}/"
                    f"{rec['expected_unchanged']} (ws={rec['divergence_whitespace_only']} "
                    f"reworded={rec['divergence_reworded']})"
                )
        write_verdict(aggregate())
        return

    if args.aggregate:
        write_verdict(aggregate())
        return

    names = list(DOCS) if args.all else [args.doc] if args.doc else []
    if not names:
        ap.error("pass --doc <name> or --all (or --aggregate)")

    for name in names:
        spec = DOCS[name]
        runner_cwd = TRIALS_DIR / name / "_cwd"
        try:
            ctx = setup_doc(spec, runner_cwd)
            run_trials(ctx, args.trials)
        except SystemExit:
            raise
        except Exception:  # noqa: BLE001
            log(f"[{name}] SETUP/RUN FAILED:\n{traceback.format_exc()}")

    write_verdict(aggregate())


if __name__ == "__main__":
    main()
