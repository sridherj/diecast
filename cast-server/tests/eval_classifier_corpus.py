#!/usr/bin/env python
"""Corpus eval for the ``cast-goal-classifier`` agent (Phase 2, sp4 — Work Package G).

This is the **manual / slow** empirical sign-off for the LOCKED taxonomy: it runs the
classifier over a labeled writeup corpus, compares each top-1 prediction to a held-out
human label, and emits the accuracy report the plan calls for —

* per-family accuracy (recall),
* the full confusion matrix,
* the ``generic`` <-> ``random_idea`` confusion pair **explicitly** (Decision D2),
* the top-2 rate (gold in {family, alt_family}),
* gate calibration (the auto / confirm / choose split over the predicted confidences),
* the off-schema coercion count (how often ``validate_classification`` had to floor a result).

It is deliberately **excluded from default CI**: the file is named ``eval_*`` (not
``test_*``), so pytest's default collection skips it, and a live run shells out to the
``claude`` CLI (slow + network). Run it by hand:

    # Offline replay from a saved predictions file (deterministic, no network):
    uv run --project cast-server python cast-server/tests/eval_classifier_corpus.py \
        --predictions cast-server/tests/fixtures/classifier_corpus_predictions.json

    # Live run against the in-repo goals/ corpus (slow — one classifier call per writeup):
    uv run --project cast-server python cast-server/tests/eval_classifier_corpus.py \
        --live --out-predictions /tmp/preds.json

    # Against an EXTERNAL corpus (privacy: keeps private writeups out of the repo):
    uv run --project cast-server python cast-server/tests/eval_classifier_corpus.py \
        --live --corpus-dir /path/to/private/writeups --labels /path/to/labels.json

The prediction mechanism is intentionally pluggable. ``--live`` invokes the real agent
prompt through ``claude -p`` (the subagent-dispatch agent has no cast-server/HTTP path,
so the CLI is the faithful headless realization). ``--predictions`` replays a saved run,
which makes the report regenerable offline and the harness testable without an API key.

Gate (sp4 success criterion): top-1 >= 0.85 on the configured subset. Below the bar, the
*first* lever is the classifier prompt's family descriptions / few-shot examples (a content
edit to ``cast-goal-classifier.md``), then ``model: sonnet -> opus`` — never the LOCKED
enum / recipes / thresholds.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# --- Make `cast_server` importable when run as a standalone script (mirrors conftest.py) ---
_CAST_SERVER_DIR = Path(__file__).resolve().parents[1]
if str(_CAST_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(_CAST_SERVER_DIR))

from cast_server.requirements_render.families import (  # noqa: E402
    WorkFamily,
    gate,
    validate_classification,
)

_REPO_ROOT = _CAST_SERVER_DIR.parent
_CLASSIFIER_PROMPT = _REPO_ROOT / "agents" / "cast-goal-classifier" / "cast-goal-classifier.md"
_DEFAULT_CORPUS_DIR = _REPO_ROOT / "goals"
_DEFAULT_LABELS = _CAST_SERVER_DIR / "tests" / "fixtures" / "classifier_corpus_labels.json"

_STUB_BODY_MARKER = "Finish brainstorming/initial requirements"


# ---------------------------------------------------------------------------
# Corpus + label loading
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CorpusItem:
    """One labeled writeup: the classifier input (``title`` + ``writeup``) and its gold family."""

    slug: str
    title: str
    writeup: str
    gold: WorkFamily
    subset: str  # "substantive" | "stub" | "" (unknown)
    note: str = ""


def _read_goal_title(goal_dir: Path) -> str:
    """Best-effort read of ``title:`` from a goal.yaml without a YAML dependency."""
    goal_yaml = goal_dir / "goal.yaml"
    if not goal_yaml.is_file():
        return goal_dir.name
    for line in goal_yaml.read_text(encoding="utf-8").splitlines():
        if line.startswith("title:"):
            title = line[len("title:") :].strip().strip("'\"")
            if title:
                return title
    return goal_dir.name


def _discover_writeups(corpus_dir: Path) -> list[tuple[str, str, str]]:
    """Return ``(slug, title, writeup)`` triples from a corpus directory.

    Two layouts are auto-detected so an external ``--corpus-dir`` works either way:

    * **goals tree** — subdirectories each holding ``requirements.human.md`` (the in-repo
      layout). Title comes from the sibling ``goal.yaml``.
    * **flat directory** — loose ``*.md`` / ``*.human.md`` files. Title is the first H1
      heading, falling back to the file stem.
    """
    goal_items = [
        (sub.name, _read_goal_title(sub), (sub / "requirements.human.md").read_text(encoding="utf-8"))
        for sub in sorted(corpus_dir.iterdir())
        if sub.is_dir() and (sub / "requirements.human.md").is_file()
    ]
    if goal_items:
        return goal_items

    flat_items: list[tuple[str, str, str]] = []
    for md in sorted(corpus_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        title = next(
            (ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), md.stem
        )
        flat_items.append((md.stem, title, text))
    return flat_items


def load_corpus(corpus_dir: Path, labels: dict[str, dict]) -> list[CorpusItem]:
    """Join discovered writeups with their gold labels. Writeups with no label are skipped
    (with a warning) — an unlabeled corpus is a setup error, not a silent zero."""
    items: list[CorpusItem] = []
    for slug, title, writeup in _discover_writeups(corpus_dir):
        if slug not in labels:
            print(f"  [warn] no gold label for {slug!r} — skipping", file=sys.stderr)
            continue
        spec = labels[slug]
        gold_raw = spec["family"] if isinstance(spec, dict) else spec
        subset = spec.get("subset", "") if isinstance(spec, dict) else ""
        note = spec.get("note", "") if isinstance(spec, dict) else ""
        if subset == "" and _STUB_BODY_MARKER in writeup:
            subset = "stub"
        items.append(
            CorpusItem(
                slug=slug,
                title=title,
                writeup=writeup,
                gold=WorkFamily(gold_raw),
                subset=subset or "substantive",
                note=note,
            )
        )
    return items


# ---------------------------------------------------------------------------
# Prediction backends
# ---------------------------------------------------------------------------
def classify_live(item: CorpusItem, model: str, timeout_s: int = 180) -> dict:
    """Run the real classifier prompt over one writeup via ``claude -p`` and parse its
    bare-JSON reply. The prompt file is the single source of truth (also pinned by
    ``test_goal_classifier_prompt.py``), so this exercises exactly what ships."""
    prompt = _CLASSIFIER_PROMPT.read_text(encoding="utf-8")
    user_msg = f"title: {item.title}\n\nwriteup:\n{item.writeup}"
    # `--tools` with no values disables all tools: the classifier is pure text-in/JSON-out and
    # must never act. Without this, an imperative-phrased writeup ("Execute the test using
    # playwright ...") can lead the headless session to *perform* the work and time out instead
    # of classifying it. Belt-and-suspenders with the subagent-mode prompt contract.
    proc = subprocess.run(
        ["claude", "-p", user_msg, "--append-system-prompt", prompt, "--model", model, "--tools", ""],
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI failed for {item.slug}: {proc.stderr.strip()[:400]}")
    return _parse_classifier_json(proc.stdout)


def _parse_classifier_json(raw: str) -> dict:
    """Extract the single JSON object from a classifier reply (tolerant of stray fences)."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{") :]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in classifier output: {raw[:200]!r}")
    return json.loads(text[start : end + 1])


def run_predictions(items: list[CorpusItem], model: str) -> dict[str, dict]:
    """Classify every item live; collect raw replies keyed by slug. A per-item failure is
    recorded (never silently dropped) so the report's denominator stays honest."""
    predictions: dict[str, dict] = {}
    for i, item in enumerate(items, 1):
        print(f"  [{i}/{len(items)}] classifying {item.slug} ...", file=sys.stderr)
        try:
            predictions[item.slug] = classify_live(item, model)
        except Exception as exc:  # noqa: BLE001 — record, don't abort the whole run
            print(f"      ERROR: {exc}", file=sys.stderr)
            predictions[item.slug] = {"_error": str(exc)}
    return predictions


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
@dataclass
class Scored:
    """One scored item: the gold/predicted families plus the gate + coercion signals."""

    item: CorpusItem
    pred_family: WorkFamily
    alt_family: WorkFamily
    confidence: float
    gate_action: str
    coercions: tuple[str, ...]
    top1: bool
    top2: bool


def score(items: list[CorpusItem], predictions: dict[str, dict]) -> list[Scored]:
    """Validate each raw prediction onto the taxonomy and compare to gold. Validation is the
    same ``validate_classification`` the production gate uses, so off-schema model output is
    floored to ``random_idea`` here exactly as it would be in the real pipeline."""
    scored: list[Scored] = []
    for item in items:
        raw = predictions.get(item.slug, {})
        classification = validate_classification(raw)
        scored.append(
            Scored(
                item=item,
                pred_family=classification.family,
                alt_family=classification.alt_family,
                confidence=classification.confidence,
                gate_action=gate(classification.confidence),
                coercions=classification.coercions,
                top1=classification.family == item.gold,
                top2=item.gold in (classification.family, classification.alt_family),
            )
        )
    return scored


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def _pct(numerator: int, denominator: int) -> str:
    return f"{(numerator / denominator * 100):5.1f}%" if denominator else "  n/a"


def _accuracy(rows: list[Scored]) -> tuple[int, int]:
    return sum(r.top1 for r in rows), len(rows)


def report(scored: list[Scored], threshold: float, gate_subset: str) -> bool:
    """Print the full structured report. Returns True if the gated subset meets ``threshold``."""
    print("\n" + "=" * 78)
    print("CLASSIFIER CORPUS EVAL  —  cast-goal-classifier (Phase 2, sp4)")
    print("=" * 78)

    # --- Overall + per-subset top-1 / top-2 -------------------------------------------
    print("\n## Accuracy")
    subsets = ["all", "substantive", "stub"]
    print(f"  {'subset':<14}{'n':>4}{'top-1':>10}{'top-2':>10}")
    subset_rows: dict[str, list[Scored]] = {
        "all": scored,
        "substantive": [r for r in scored if r.item.subset == "substantive"],
        "stub": [r for r in scored if r.item.subset == "stub"],
    }
    for name in subsets:
        rows = subset_rows[name]
        if not rows:
            continue
        c1, n = _accuracy(rows)
        c2 = sum(r.top2 for r in rows)
        print(f"  {name:<14}{n:>4}{_pct(c1, n):>10}{_pct(c2, n):>10}")

    # --- Per-family recall ------------------------------------------------------------
    print("\n## Per-family accuracy (recall over gold)")
    print(f"  {'gold family':<20}{'n':>4}{'correct':>9}{'recall':>9}")
    by_gold: dict[WorkFamily, list[Scored]] = {}
    for r in scored:
        by_gold.setdefault(r.item.gold, []).append(r)
    for fam in WorkFamily:
        rows = by_gold.get(fam, [])
        if not rows:
            continue
        c, n = _accuracy(rows)
        print(f"  {fam.value:<20}{n:>4}{c:>9}{_pct(c, n):>9}")

    # --- Confusion matrix (gold -> pred), misses only ---------------------------------
    print("\n## Confusion (gold -> pred), misclassifications only")
    confusion = Counter((r.item.gold, r.pred_family) for r in scored if not r.top1)
    if not confusion:
        print("  (none — every top-1 correct)")
    for (gold, pred), count in confusion.most_common():
        print(f"  {gold.value:<20} -> {pred.value:<20} x{count}")

    # --- The D2 explicit pair: generic <-> random_idea --------------------------------
    print("\n## generic <-> random_idea confusion (Decision D2)")
    g_r = confusion.get((WorkFamily.GENERIC, WorkFamily.RANDOM_IDEA), 0)
    r_g = confusion.get((WorkFamily.RANDOM_IDEA, WorkFamily.GENERIC), 0)
    n_generic = len(by_gold.get(WorkFamily.GENERIC, []))
    n_random = len(by_gold.get(WorkFamily.RANDOM_IDEA, []))
    print(f"  gold=generic     -> pred=random_idea : {g_r}  (of {n_generic} generic golds)")
    print(f"  gold=random_idea -> pred=generic     : {r_g}  (of {n_random} random_idea golds)")
    print(f"  total cross-confusion in the pair    : {g_r + r_g}")
    if g_r + r_g == 0:
        print("  -> boundary holding: no bleed between the two low-structure fallbacks.")
    else:
        print("  -> bleed detected: sharpen the generic/random_idea boundary in the prompt first.")

    # --- Gate calibration -------------------------------------------------------------
    print("\n## Gate calibration (observability — NOT a v2 gate)")
    gate_counts = Counter(r.gate_action for r in scored)
    total = len(scored)
    for action in ("auto", "confirm", "choose"):
        print(f"  {action:<8}{gate_counts.get(action, 0):>4}  {_pct(gate_counts.get(action, 0), total)}")
    coerced = [r for r in scored if r.coercions]
    print(f"\n  off-schema coercions: {len(coerced)} / {total}")
    for r in coerced:
        print(f"    {r.item.slug}: {'; '.join(r.coercions)}")

    # --- Per-item detail --------------------------------------------------------------
    print("\n## Per-item detail")
    print(f"  {'slug':<38}{'gold':<18}{'pred':<18}{'conf':>5} {'t1':>3} {'t2':>3}")
    for r in sorted(scored, key=lambda s: (s.item.subset, s.item.slug)):
        mark1 = "OK" if r.top1 else "XX"
        mark2 = "OK" if r.top2 else "--"
        print(
            f"  {r.item.slug:<38}{r.item.gold.value:<18}{r.pred_family.value:<18}"
            f"{r.confidence:>5.2f} {mark1:>3} {mark2:>3}"
        )

    # --- Gate verdict -----------------------------------------------------------------
    gated = subset_rows.get(gate_subset, scored)
    c, n = _accuracy(gated)
    passed = n > 0 and (c / n) >= threshold
    print("\n" + "-" * 78)
    print(
        f"GATE: top-1 on '{gate_subset}' = {_pct(c, n).strip()} "
        f"({c}/{n}); threshold {threshold:.0%} -> {'PASS' if passed else 'BELOW BAR'}"
    )
    print("-" * 78)
    return passed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--corpus-dir", type=Path, default=_DEFAULT_CORPUS_DIR,
                   help="Corpus directory (goals tree or flat *.md dir). Default: in-repo goals/.")
    p.add_argument("--labels", type=Path, default=_DEFAULT_LABELS,
                   help="JSON gold-label file: {slug: family} or {slug: {family, subset, note}}.")
    p.add_argument("--predictions", type=Path, default=None,
                   help="Replay a saved predictions file ({slug: rawjson}) instead of going live.")
    p.add_argument("--live", action="store_true",
                   help="Classify each writeup live via the claude CLI (slow, network).")
    p.add_argument("--out-predictions", type=Path, default=None,
                   help="Write the live predictions to this path (for later offline replay).")
    p.add_argument("--model", default="sonnet", help="Model for live classification (default: sonnet).")
    p.add_argument("--threshold", type=float, default=0.85, help="Top-1 gate threshold (default: 0.85).")
    p.add_argument("--gate-subset", default="substantive", choices=("all", "substantive", "stub"),
                   help="Which subset the pass/fail gate applies to (default: substantive).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    labels = json.loads(args.labels.read_text(encoding="utf-8"))
    items = load_corpus(args.corpus_dir, labels)
    if not items:
        print("No labeled corpus items found — check --corpus-dir / --labels.", file=sys.stderr)
        return 2
    print(f"Loaded {len(items)} labeled writeups from {args.corpus_dir}", file=sys.stderr)

    if args.predictions and not args.live:
        predictions = json.loads(args.predictions.read_text(encoding="utf-8"))
    else:
        predictions = run_predictions(items, args.model)
        if args.out_predictions:
            args.out_predictions.write_text(json.dumps(predictions, indent=2), encoding="utf-8")
            print(f"Wrote predictions -> {args.out_predictions}", file=sys.stderr)

    scored = score(items, predictions)
    passed = report(scored, args.threshold, args.gate_subset)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
