# Sub-phase 4: Corpus Eval + Template-Enforcer Audit

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase2/_shared_context.md` before starting.
> Source: Work Package G of `docs/plan/2026-06-11-refine-requirements-v2-phase2-classification.md`.

## Objective

Prove the classifier is accurate enough and the Template-Enforcer guard actually holds end-to-end.
Assemble a labeled writeup corpus across the maintainer's three workspaces, run the classifier against
held-out human labels (gate: ≥85% top-1), and audit real `random_idea` refinements for zero
auto-padded fields. This is the empirical sign-off that the LOCKED taxonomy + the structural floor
were the right calls — the deterministic CI tests in sp1–sp3 prove correctness; this proves *fit*.

## Dependencies
- **Requires completed:** sp3a (the full refine→classify→emit→check pipeline). Transitively
  sp1/sp2a/sp2b/sp2c.
- **Assumed codebase state:** `cast-refine-requirements` Step 0 classifies and persists; the
  classifier agent + gate bin + `--family` checker all work end-to-end.
- **Parallel with:** none — this is the terminal sub-phase.

## Scope

**In scope:**
- Assemble the labeled corpus (25–40 writeups across the 3 workspaces).
- `tests/eval_classifier_corpus.py` (manual/slow, excluded from default CI).
- The accuracy report (per-family accuracy, confusion pairs incl. `generic`↔`random_idea`, top-2 rate,
  gate calibration).
- End-to-end refine of 3+ real `random_idea`-shaped writeups + the zero-padding audit.

**Out of scope (do NOT do these):**
- Tuning `families.py` / the classifier prompt **structure** — if accuracy < 85%, the *first* lever is
  the prompt's family descriptions / few-shot examples (a content edit to `cast-goal-classifier.md`),
  then `model: sonnet → opus`; do NOT change the enum set, the recipes, or the gate thresholds (those
  are LOCKED). Record the miss and the tuning, re-eval; only escalate the model after prompt tuning.
- Committing the corpus **without resolving the privacy question** (see Open Questions / Step 4.1).
- Adding the eval to default CI — it is manual/slow by design.

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `tests/eval_classifier_corpus.py` | Create (manual/slow, CI-excluded) | Does not exist |
| corpus fixtures (location TBD — see Step 4.1) | Create or reference via `--corpus-dir` | Does not exist |
| `agents/cast-goal-classifier/cast-goal-classifier.md` | Modify (ONLY if eval misses 85% — prompt tuning) | From sp2a |

## Detailed Steps

### Step 4.1: Assemble + label the corpus  ⚠️ human action
- Gather `requirements.human.md` / raw writeups: this repo's `goals/` has ~17; pull the rest from the
  maintainer's second-brain/taskos and linkedout workspaces — **target 25–40 total**.
- **Owner hand-labels each** with a held-out `WorkFamily` (human action — this sub-phase pauses for it
  if running interactively; if headless, record the dependency and proceed with the in-repo ~17).
- **Privacy/location call (Open Question — owner decides):** can the second-brain/linkedout writeups be
  committed to this repo as eval fixtures, or must the corpus live outside the repo? The eval script
  must support an external `--corpus-dir` path either way (build it that way regardless).

### Step 4.2: `tests/eval_classifier_corpus.py` (manual/slow)
- Run the classifier on each writeup; compare top-1 to the held-out label.
- Report: per-family accuracy, confusion pairs, **the `generic`↔`random_idea` confusion pair
  explicitly (Decision D2)** — a high cross-rate means the sharpened prompt boundary (sp2a) isn't
  landing and is the first thing to tune. Also report top-2 rate and **gate calibration** (what share
  landed in confirm/choose — to tune the 0.5/0.9 cutoffs later; observability, not a v2 gate).
- **Gate: ≥85% top-1.** Below the bar → tune the prompt's family descriptions / add few-shot examples
  → re-eval → only then consider `model: opus`.
- Exclude from default CI (mark slow / put outside the collected test paths).

→ **Delegate:** `/cast-pytest-best-practices` over the eval harness structure. Review output.

### Step 4.3: Template-Enforcer end-to-end audit
- Refine **3+ real `random_idea`-shaped writeups** end-to-end through `cast-refine-requirements`.
- Audit each output for **zero** empty/auto-padded scope/metric/acceptance fields. (The sp2c
  padded-fixture test guards this forever after; this is the live confirmation on real inputs.)

## Verification

### Automated Tests (permanent, but CI-excluded)
- `tests/eval_classifier_corpus.py` runs cleanly and emits the structured report (accuracy, confusion
  pairs, top-2, gate calibration). It is the designed resolver for the model-tier question.

### Validation Scripts (temporary)
```bash
uv run --project cast-server python tests/eval_classifier_corpus.py --corpus-dir <path>   # ≥85% top-1
# Audit 3 random_idea refinements: no empty US/FR/SC/Out-of-Scope tables
for f in <three_random_idea_docs>; do
  grep -E '^## (User Stories|Functional Requirements|Success Criteria|Out of Scope)' "$f" && echo "PADDED: $f" || echo "clean: $f"
done
```

### Manual Checks
- The eval report shows ≥85% top-1 (or, if below, the prompt-tuning iterations + re-eval are recorded,
  and the decision to escalate `model: opus` (or not) is documented with the numbers).
- The `generic`↔`random_idea` confusion pair is reported explicitly.
- Three `random_idea` refinements: zero padded fields, each ends with the "structure is available"
  offer line.
- Gate-calibration share (confirm/choose %) recorded for future threshold tuning.

### Success Criteria
- [ ] Corpus assembled (≥ the in-repo 17; target 25–40 with owner labels) and the privacy/location call
      recorded.
- [ ] `tests/eval_classifier_corpus.py` exists, is CI-excluded, supports `--corpus-dir`, emits the full
      report.
- [ ] Top-1 ≥ 85% (or the miss + tuning + model-tier decision documented with numbers).
- [ ] `generic`↔`random_idea` confusion + gate calibration reported.
- [ ] 3+ `random_idea` refinements audited: zero auto-padded fields.

## Execution Notes
- This is the **only** sub-phase with a real human-in-the-loop dependency (corpus labeling + privacy
  call). If running headless, do NOT fabricate labels — run on the in-repo `goals/` writeups, report
  what you can, and flag the owner action in your output (`human_action_needed: true`).
- Accuracy tuning is **prompt content, then model tier** — never the LOCKED taxonomy/recipes/thresholds.
- The corpus eval is the *designed resolver* for the open "classifier model tier" question — let the
  numbers decide `sonnet` vs `opus`, not vibes.

**Spec-linked files:** none modified here beyond the (conditional) classifier prompt. If you tune the
prompt, the sp2a pin test (prompt ⊇ every enum value) must stay green.
