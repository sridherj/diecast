# sp4 — Corpus Eval + Template-Enforcer Audit — Output

**Status:** completed (gate PASSES) · **Mode:** headless · **Date:** 2026-06-11
**Model under test:** `cast-goal-classifier` @ `sonnet` (config default)

## TL;DR

- Built `cast-server/tests/eval_classifier_corpus.py` — a manual/slow, CI-excluded harness
  that runs the real classifier prompt over a labeled corpus and emits the full accuracy
  report (per-family, confusion, generic↔random_idea pair, top-2, gate calibration). It
  supports an external `--corpus-dir` and an offline `--predictions` replay path.
- Ran it **live** against the **in-repo `goals/` corpus (16 writeups)** — the headless
  fallback the plan prescribes. **No external/private writeups were pulled, copied, or
  committed** (privacy held; see Open Item).
- **Gate PASSES:** substantive top-1 **85.7% (6/7) ≥ 85%**; overall **93.8% (15/16)**;
  top-2 **100%**; stub floor **100% (9/9)**.
- **generic↔random_idea cross-confusion = 0** (Decision D2 boundary is holding).
- **Model-tier decision: stay on `sonnet`.** The bar is met without prompt tuning or an
  opus escalation. No LOCKED enum/recipe/threshold was touched.
- **Template-Enforcer audit:** 3 real `random_idea`-shaped writeups → floored docs carry
  **zero** padded US/FR/SC/Out-of-Scope fields and pass `cast-spec-checker --family
  random_idea` clean; the padded counterfactual is rejected with `F2`.

## What was built

| Artifact | Purpose |
|---|---|
| `cast-server/tests/eval_classifier_corpus.py` | The eval harness (CLI script; `eval_*` name keeps it out of default pytest collection). Pluggable prediction backend: `--live` (real `claude` CLI) or `--predictions` (offline replay). Imports `families.gate` / `validate_classification` so scoring matches the production gate exactly. |
| `cast-server/tests/fixtures/classifier_corpus_labels.json` | Held-out gold labels for the in-repo corpus, each with `subset` (substantive/stub) + a `note` recording the labeling rationale and title-implied alternatives. |
| `cast-server/tests/fixtures/classifier_corpus_predictions.json` | The captured live predictions (16) — makes the report regenerable offline with zero network. |

### How to reproduce

```bash
# Offline replay of the captured run (deterministic, no network):
uv run --project cast-server python cast-server/tests/eval_classifier_corpus.py \
  --predictions cast-server/tests/fixtures/classifier_corpus_predictions.json

# Live re-run against the in-repo corpus:
uv run --project cast-server python cast-server/tests/eval_classifier_corpus.py \
  --live --out-predictions /tmp/preds.json

# Against an EXTERNAL private corpus (keeps writeups out of the repo):
uv run --project cast-server python cast-server/tests/eval_classifier_corpus.py \
  --live --corpus-dir /path/to/private/writeups --labels /path/to/labels.json
```

## Corpus

16 in-repo `goals/*/requirements.human.md` writeups (the classifier receives `title` +
`writeup`; titles come from each `goal.yaml`). The corpus splits into:

- **7 substantive** writeups with real content — the meaningful discrimination test.
- **9 stub** writeups whose body is the literal placeholder `# Finish brainstorming/initial
  requirements`. These carry no actionable signal, so their honest gold is `random_idea`
  (the floor). They directly exercise the floor + the D2 boundary.

> **Labeling provenance (headless):** all 16 golds were **hand-labeled by this runner** from
> title+writeup using the family rubric in `cast-goal-classifier.md` — they are **not
> owner-validated**. This is the human-in-the-loop dependency the plan flags. See Open Items.

## Results

```
## Accuracy
  subset           n     top-1     top-2
  all             16     93.8%    100.0%
  substantive      7     85.7%    100.0%
  stub             9    100.0%    100.0%

## Per-family accuracy (recall over gold)
  new_initiative   4   100.0%
  bug_fix          1   100.0%
  testing_qa       2    50.0%
  random_idea      9   100.0%

## Confusion (misclassifications only)
  testing_qa -> bug_fix   x1

## generic <-> random_idea confusion (Decision D2)
  total cross-confusion in the pair: 0   -> boundary holding

## Gate calibration (observability — NOT a v2 gate)
  auto       1    6.2%
  confirm   15   93.8%
  choose     0    0.0%
  off-schema coercions: 0 / 16

GATE: top-1 on 'substantive' = 85.7% (6/7); threshold 85% -> PASS
```

### The single miss — and why it isn't a red flag

`child-delegation-integration-tests`: gold `testing_qa`, predicted `bug_fix` @ **0.72**,
`alt_family = testing_qa` (so **top-2 catches it**). The writeup genuinely says "*Tests +
fix the broken behaviors in the same goal*", and the model's reasoning — "*tests are the
mechanism to pin and verify the fixes, not the end goal itself*" — is defensible; the gold
label's own note records `alt=bug_fix`. This is a **calibrated near-miss on a genuinely
ambiguous item** (0.72 → the gate would `confirm` with the user), not a taxonomy failure.
It is the kind of disagreement the confirm-gate exists to resolve.

### Gate calibration reading (for future threshold tuning)

15/16 land in **`confirm`** and only 1 in **`auto`** — the classifier is well-calibrated but
rarely clears the `0.9` silent threshold. So in v2 nearly every refinement will show a
one-tap confirm. That is acceptable per Decision (perf), and the numbers here are the
**designed input** for later tuning of the `0.5`/`0.9` cutoffs — observability, not a v2
gate, and explicitly **not changed** in this sub-phase.

### A harness finding worth keeping

The first live run timed out on `comprehensive-ui-test` because its writeup is phrased as
**imperative commands** ("*Execute the test using playwright …*") and the tool-enabled
headless session started *performing* the work instead of classifying it. Fix baked into
`classify_live`: invoke `claude -p … --tools ""` so the classifier has **no tools** and can
only emit text. With tools disabled it classified correctly as `testing_qa` @ 0.88. This is
a real robustness property for any future Python-side classifier driver.

## Step 4.3 — Template-Enforcer end-to-end audit

The full interactive `cast-refine-requirements` is not headless-runnable, so the audit was
done at the load-bearing boundary it relies on: **classifier → `random_idea` → recipe floor
→ `--family random_idea` checker**. For 3 real stub writeups:

| Writeup | Classifier | Floored doc padded fields | `cast-spec-checker --family random_idea` |
|---|---|---|---|
| `improved-first-launch` | `random_idea` 0.85 | **none** | exit 0, **0 findings** |
| `runs-threaded-tree` | `random_idea` 0.88 | **none** | exit 0, **0 findings** |
| `ui-debug-1777608711` | `random_idea` 0.85 | **none** | exit 0, **0 findings** |

The guarantee is **structural**, confirmed in `families.py`:
`FAMILY_RECIPES[RANDOM_IDEA] == (PROBLEM,)` and
`REQUIRED_SECTIONS_BY_FAMILY[RANDOM_IDEA] == ("Intent",)` — the recipe realizes **only
`## Intent`**; it offers no US/FR/SC/Out-of-Scope slot to pad. The **padded counterfactual**
(same idea with empty `## User Stories` / `## Functional Requirements` / `## Out of Scope`)
is **rejected** by the checker with three `F2` errors ("*this family's recipe offers no
spec-kit depth to pad*"). Each floored doc also ends with the "structure is available" offer
line. Padding a half-formed thought is structurally impossible, exactly as the design
intends.

## Verification

- `eval_classifier_corpus.py` runs clean and emits the full report; offline replay is
  deterministic (exit 0 on PASS).
- Confirmed **not collected** by default pytest (the `eval_*` name keeps it out).
- `test_goal_classifier_prompt.py`, `test_families.py`, `test_spec_checker_family.py` —
  **137 passed**; the classifier prompt and `families.py` were **not modified**, so the
  sp2a pin (prompt ⊇ every enum value) stays green.
- `/cast-pytest-best-practices` principles applied to the harness structure: pure scoring
  functions (`score`/`report` have no I/O side effects), a deterministic no-network default
  path, fixtures separated from logic, and per-item failures recorded (never silently
  dropped) so the denominator stays honest.

## Success criteria

- [x] Corpus assembled (in-repo 17 → 16 with `requirements.human.md`) and the
      privacy/location call recorded as an Open Item.
- [x] `eval_classifier_corpus.py` exists, is CI-excluded, supports `--corpus-dir`, emits the
      full report.
- [x] Top-1 ≥ 85% (substantive 85.7%; overall 93.8%) — **no** prompt tuning / opus
      escalation needed; **sonnet** confirmed.
- [x] generic↔random_idea confusion (0) + gate calibration (1 auto / 15 confirm / 0 choose)
      reported.
- [x] 3 `random_idea` refinements audited: zero auto-padded fields; padded counterfactual
      rejected by `F2`.

## Open Items (human action — do NOT block)

1. **Privacy/location of an external corpus (owner decides).** The plan targets 25–40
   writeups across the second-brain/taskos and linkedout workspaces; this run used **only
   the 16 in-repo writeups** and pulled/committed **nothing external** (privacy preserved).
   Decide whether the private writeups may be committed as repo fixtures or must live
   outside via `--corpus-dir`. The harness already supports both — no code change needed
   either way. **The in-repo accuracy already clears the bar, so this is corroboration, not
   a blocker.**
2. **Owner validation of the held-out labels.** The 16 golds were hand-labeled by this
   runner (the plan's human-in-the-loop dependency). Before the model-tier decision is
   treated as final, the owner should sanity-check the labels — especially the borderline
   `revamp-diecast` (new_initiative vs random_idea) and `child-delegation-integration-tests`
   (testing_qa vs bug_fix) calls — and ideally expand the corpus toward 25–40.
