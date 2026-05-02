# Fix CI Workflows: Anonymization, E2E, Setup-Correctness

## Overview
Three GitHub workflows are red on `main` (commit `edeab40`): Anonymization Lint (real PII leaks),
E2E (missing `tmux` in test container), and Setup Correctness (broken fake-claude wiring in
the CI workflow). All three are independent and have well-understood root causes — this plan
fixes them in parallel and verifies green on push. No exploration needed.

## Operating Mode
**SCOPE REDUCTION** — User said "fix" with clear failing signals. No invitation to refactor CI,
restructure tests, or expand coverage. Cut scope to the minimum change that turns each workflow
green on the next push to main.

## Context: Decisions Locked Before Planning

User input gathered before this plan:
1. **ptyxis lint rule:** Drop from `FORBIDDEN_PATTERNS`. ptyxis is a public terminal app
   (like gnome-terminal/kitty) and is hardcoded as a supported terminal in `bin/cast-doctor`.
   Removing the rule eliminates 14 of the lint hits without any doc churn.
2. **Setup-correctness CI:** Fix it (don't delete). Install fake-claude as `claude` in the
   workflow — same trick e2e Dockerfile uses. The workflow gives bare-Ubuntu signal that the
   containerized e2e doesn't.
3. **Audit + sanity-log files:** Delete `docs/audit/linkedout-coupling-spike.ai.{md,json}` and
   `tests/dry-runs/_real_world_sanity.log`. Both are scratch/debug artifacts that don't belong
   in the public repo.

## Sub-phase 1: All Three Workflows Green on Push

**Outcome:** On the next push to `main`, all three currently-failing workflows
(Anonymization Lint, E2E, Setup Correctness) report success. Other workflows
(Interdependency Audit, shellcheck, pages-build) remain green.

**Dependencies:** None.

**Estimated effort:** 1 session (~1.5 hours). Three independent tracks (1a/1b/1c) run in
parallel; each is small.

**Verification (run all locally before push):**
- `bin/lint-anonymization` exits 0
- After editing `bin/lint-anonymization`, run `git diff bin/lint-anonymization` and confirm
  the only changes are (1) deletion of the `\bptyxis\b` `FORBIDDEN_PATTERNS` row and (2)
  deletion of any related comment lines. No other rule changes.
- `docker build -t diecast-e2e -f tests/Dockerfile.test-e2e . && docker run --rm -v "$(pwd):/work" diecast-e2e` reports `Pass: 10, Fail: 0`
- Scenario 3b probe (run before push to flush hidden config-write regression):
  `docker run --rm -v "$(pwd):/work" diecast-e2e bash -c './setup --no-prompt && grep upgrade_snooze ~/.cast/config.yaml'`
  must print both `upgrade_snooze_streak` and `upgrade_snooze_until`.
- `bash tests/setup-correctness-test.sh` reports `Results: 3 passed, 0 failed`. To simulate
  CI locally, symlink fake-claude into a tempdir and prepend it to PATH (do **not** copy to
  `~/.local/bin/claude` — that may clobber a real Claude Code install on a developer machine):
  `mkdir -p /tmp/diecast-ci-bin && ln -sf "$(pwd)/tests/fixtures/fake-claude" /tmp/diecast-ci-bin/claude && PATH="/tmp/diecast-ci-bin:${PATH}" bash tests/setup-correctness-test.sh`.
- After push: `gh run list --limit 5` shows all 3 target workflows green AND
  `gh pr checks <pr>` shows `e2e` and `setup-correctness` as `pass` (not `skipping`/`neutral`).
  A "neutral" status means the PR was missing the `run-e2e` / `run-setup-tests` label and
  the workflow did not actually exercise our fix.

### Track 1a: Anonymization — drop ptyxis rule, scrub residual leaks, delete stale files

Key activities:
- Edit `bin/lint-anonymization`: remove the `(r"\bptyxis\b", re.IGNORECASE)` entry from
  `FORBIDDEN_PATTERNS`. In the same edit pass, **drop** the `# diecast-lint: ignore-line`
  comment at `bin/cast-doctor:46` — it silences a rule that no longer exists, so it is
  dead metadata.
- `git rm docs/audit/linkedout-coupling-spike.ai.md docs/audit/linkedout-coupling-spike.ai.json`
  (scratch artifacts; ~10 PII hits removed).
- `git rm tests/dry-runs/_real_world_sanity.log` (stale dry-run trace; ~7 PII hits removed).
- Scrub remaining `\bSJ\b` hits — for each hit, read the surrounding sentence in context
  and replace with the role-appropriate noun: `"the maintainer"` or `"the reviewer"` for
  plan/review docs (whichever the surrounding sentence implies); `"the user"` for
  product-facing fixtures (e.g. `requirements.human.md`). No blind sed.
  - `docs/execution/terminal-intelligent-defaults/_review_summary.md` (lines 7, 14)
  - `docs/execution/terminal-intelligent-defaults/sp1_resolver_fixes/plan.md` (line 383)
  - `tests/fixtures/minimal-goal/requirements.human.md` (line 11)
- In `setup:5`, surgically delete the `"Mirrors ~/workspace/linkedout-oss/setup. "`
  sentence only. Keep the rest of the comment ("Takes a fresh clone of
  github.com/sridherj/diecast..." onward) intact — the canonical GitHub URL is
  allowlisted by the lint's `(?<!github\.com/)` lookaround for `\bsridherj\b`.
- Run `bin/lint-anonymization` locally; confirm exit 0.

**Design review:**
- **Spec consistency:** No spec governs the lint rule list (`bin/lint-anonymization` is its own
  source of truth per its docstring D6). No conflict.
- **Ripple check:** Dropping `ptyxis` from the lint must not silently weaken the broader
  anonymization contract. The pattern was an outlier (a public terminal name, not a
  PII token); removing it does not affect the SJ/sridherj/email/path rules. ✓
- **Verification gap:** Re-run the lint after each scrub batch — easy to miss a hit if you
  fix the obvious ones and skip a quoted form. ✓ (covered in activities)

### Track 1b: E2E — add `tmux` to the test container

Key activities:
- Edit `tests/Dockerfile.test-e2e`: add `tmux` to the `apt-get install` line that already
  installs `git curl ca-certificates bash procps`.
- Rebuild image locally: `docker build -t diecast-e2e -f tests/Dockerfile.test-e2e .`
- Run e2e locally: `docker run --rm -v "$(pwd):/work" diecast-e2e` — confirm `Pass: 10, Fail: 0`.
  In particular: Scenario 1 (clean install) now runs `setup --no-prompt` to completion;
  Scenario 1b (sentinel) preserves; Scenario 3b (snooze fields) finds them in
  `~/.cast/config.yaml` (Phase-1a setup writes the defaults at `setup:241-243`); Scenario 6
  (post-install anonymization lint) passes because Track 1a is in the same commit/branch.

**Design review:**
- **Cascade check:** Scenarios 1b, 3b, and 6 all cascade from Scenario 1's setup abort.
  Adding tmux unblocks Scenario 1, which should also unblock the cascades. Verify all
  4 turn green together — if 3b stays red after tmux fix, that's a real regression in
  config-write logic, not a CI bug. ✓
- **Container hygiene:** `tmux` adds ~10MB to the image. Acceptable; image is built per-run.
- **No spec conflict:** Dockerfile is internal infra, no spec coverage.

### Track 1c: Setup-Correctness CI — install fake-claude as `claude`

Key activities:
- Edit `.github/workflows/setup-correctness.yml`: between the "Install uv" and "Show prereq
  versions" steps, add an "Install fake claude" step that symlinks the fixture into a
  workflow-local `.ci-bin/` directory and prepends it to `$GITHUB_PATH`. This keeps the
  `~/.local/bin/` namespace clean (avoids clobbering a real `claude` binary on developer
  machines during local sim) and is self-documenting (`.ci-bin/` names its purpose):

  ```yaml
  - name: Install fake claude (CI-only shim)
    run: |
      mkdir -p .ci-bin
      ln -sf "$PWD/tests/fixtures/fake-claude" .ci-bin/claude
      echo "$PWD/.ci-bin" >> "$GITHUB_PATH"
  ```

- Also add `tmux` to the runner: under the "Show prereq versions" step add a setup step
  `- name: Install tmux\n  run: sudo apt-get update && sudo apt-get install -y tmux`.
  Without this, cast-doctor will RED on tmux just like the e2e container did. Keep this
  as a separate step (rather than consolidating with the fake-claude symlink) so failure
  attribution in the GH Actions UI is one click.
- Locally simulate the CI environment without touching `~/.local/bin/`:
  `mkdir -p /tmp/diecast-ci-bin && ln -sf "$(pwd)/tests/fixtures/fake-claude" /tmp/diecast-ci-bin/claude && PATH="/tmp/diecast-ci-bin:${PATH}" bash tests/setup-correctness-test.sh`.
  Ensure tmux is on PATH. Confirm `Results: 3 passed, 0 failed`.

**Design review:**
- **Why install at `$HOME/.local/bin/claude` not the test's `FIXTURE_DIR` PATH trick?**
  The test script's `PATH="${FIXTURE_DIR}:${PATH}"` injection only helps when a binary
  named `claude` lives in `FIXTURE_DIR`. The fixture is named `fake-claude`. Renaming the
  fixture is invasive (used by e2e's COPY-rename, by docs, by scripts). Installing it as
  `claude` once at workflow setup is the lightest fix and matches how e2e does it. ✓
- **Drift risk:** if the fake-claude fixture is ever renamed, both e2e Dockerfile and this
  workflow break together. Acceptable — it's the same drift surface, not a new one.
- **No spec conflict:** internal CI infra.

## Sub-phase 2: Push and Verify Green CI

**Outcome:** Branch merged to main; `gh run list` confirms all 3 target workflows green
on the merge commit.

**Dependencies:** Sub-phase 1.

**Estimated effort:** 15 minutes (push, watch, verify; possibly one rerun if a flake).

**Verification:**
- `gh run list --branch main --limit 10` shows the head commit's runs all green for:
  Setup Correctness, Anonymization Lint, E2E, Interdependency Audit, shellcheck.
- If any workflow is red, drop back into Sub-phase 1 to investigate the specific failure
  before declaring done.

Key activities:
- Stage Sub-phase 1 as **three separate commits on one fix branch** (one per track), so
  bisect/revert can isolate each change cleanly:
  1. `fix(ci): drop ptyxis lint rule, scrub residual PII, delete scratch files`
     — Track 1a edits (`bin/lint-anonymization`, `bin/cast-doctor:46`, the four `\bSJ\b`
     scrubs, `setup:5` sentence delete, `git rm` of the scratch files).
  2. `fix(ci): add tmux to e2e test container`
     — Track 1b edit to `tests/Dockerfile.test-e2e`.
  3. `fix(ci): install fake-claude shim and tmux in setup-correctness workflow`
     — Track 1c edits to `.github/workflows/setup-correctness.yml`.
- Push and open the PR with both labels baked into the create command (do NOT rely on a
  follow-up `gh pr edit --add-label`):

  ```
  gh pr create --label run-setup-tests --label run-e2e \
    --title "fix(ci): green up Anonymization Lint, E2E, Setup Correctness" \
    --body "..."
  ```

  Both labels are mandatory. Without `run-setup-tests`, setup-correctness skips. Without
  `run-e2e`, e2e skips. GitHub renders skips as "neutral" / "All checks have passed,"
  which looks like green but is silent failure to exercise the fix.
- After CI completes, run `gh pr checks <pr>` and confirm `e2e` and `setup-correctness`
  show status `pass` (NOT `skipping` / `neutral`). If either is missing, the labels did
  not take — re-add and re-run.
- Watch the runs via `gh run watch` or `gh run list`; merge when all green.

**Design review:**
- **Label gotcha:** The PR's setup-correctness and e2e jobs only run when the PR carries
  `run-setup-tests` / `run-e2e` labels. Without those, the PR will look "all green" but
  not actually exercise our fixes. Apply both labels before merging. ✓
- **Cascade check after merge:** post-merge push to main re-triggers both workflows
  (no label gate on push). Watch the main-branch run and confirm green. ✓

## Build Order

```
        ┌── Track 1a (anonymization) ──┐
Start ──┼── Track 1b (e2e tmux)        ┼── Sub-phase 2 (push + verify)
        └── Track 1c (setup-correct.)──┘
```

**Critical path:** none of the tracks dominates; expect ~30 min each in parallel,
then ~15 min for push/verify.

## Design Review Flags

| Sub-phase | Flag | Action |
|-------|------|--------|
| 1b | Scenarios 1b/3b/6 cascade from Scenario 1 — verify all 4 turn green together | Run e2e locally before push; if 3b stays red, investigate config-write regression separately |
| 1c | PR-gating labels (`run-setup-tests`, `run-e2e`) must be applied or the PR won't actually run our fixes | Apply both labels when opening the PR |
| 1a | Removing `\bptyxis\b` weakens lint surface — confirm no other PII tokens were also riding the same line | After scrub, run lint and visually scan a sample of changed files |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scenario 3b stays red after tmux fix (real config-write regression) | Med | `tests/e2e-test.sh:188` exits 1 if any single scenario fails — there is no "ship 9-of-10" path. If 3b stays red locally after the tmux fix, do NOT push. Use the Scenario 3b probe in the Verification block to confirm whether `setup --no-prompt` is writing the snooze keys; if not, fix the config-write regression in the same fix branch before pushing. Out-of-band follow-up only applies if the fix is genuinely outside this scope-reduction plan, in which case the plan's "all 3 workflows green" outcome is unmet and Sub-phase 1 is not done. |
| `bin/audit-interdependencies` or `bin/check-doc-links` (also run in anonymization-lint.yml) start failing once anon passes | Low | Run all 4 commands from the workflow locally before push: `bin/lint-anonymization && bin/audit-interdependencies && bin/check-doc-links && pytest tests/`. They were green before (passed when anon failed), so likely fine. |
| pytest `tests/` step in anonymization-lint.yml fails due to recent test changes | Low | Same local dry-run pre-push. Working tree shows `tests/test_agent_registry_filesystem.py` is modified — verify it still passes before pushing. |
| Setup-correctness still fails on a missed prereq even after tmux+claude added | Low | Read the cast-doctor output: it lists every check. If a new RED appears, add the missing tool to the workflow's setup steps. |

## Open Questions

None. All input gathered before plan was written.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| (none loaded) | — | — |

No spec covers CI workflows, anonymization rules, or the e2e/setup-correctness test scripts.
The lint script's docstring (D6) is the source of truth for the forbidden pattern list and
acknowledges that — no spec needed for that change.

## Decisions

Decisions captured during cast-plan-review on 2026-05-01. Each entry is dated, the
question is the one-line review prompt, the decision is the user's chosen option, and
the rationale records the load-bearing reason.

- **2026-05-01T00:00:00Z — Single consolidated commit vs three commits matching the three tracks?** — Decision: A — three commits on one branch, one PR. Rationale: tracks are file-disjoint, so per-track commits cost ~5min more but make `git bisect` and revert clean; bundled commit subject was already a comma-list of four distinct things, which is a tell that the unit-of-change was wrong.
- **2026-05-01T00:00:00Z — PR-label requirement documented as prose vs enforced via gh pr create + a positive verification gate?** — Decision: A — bake `--label run-setup-tests --label run-e2e` into the `gh pr create` invocation and add a `gh pr checks` line that confirms the workflows ran (not just that the PR is "green"). Rationale: GitHub renders skipped checks as "neutral / All checks have passed," indistinguishable from green; mechanical enforcement kills a real foot-gun.
- **2026-05-01T00:00:00Z — Track 1c: install fake-claude at `$HOME/.local/bin/claude` vs symlink into a workflow-local `.ci-bin/`?** — Decision: B — symlink into `.ci-bin/` and prepend to `$GITHUB_PATH`. Rationale: the original plan's local-sim instruction told developers to copy fake-claude to `~/.local/bin/claude`, which would silently clobber a real Claude Code binary on a developer machine. `.ci-bin/` is self-documenting and matches the lightweight intent. Renaming the fixture (option C) is over-engineered for two callers.
- **2026-05-01T00:00:00Z — Drop the `# diecast-lint: ignore-line` comment at `bin/cast-doctor:46` together with the ptyxis FORBIDDEN_PATTERNS row?** — Decision: A — drop both in the same edit. Rationale: dead metadata (a sentinel for a rule that no longer exists) is worse than no metadata; readers wonder what rule the comment is silencing. Same edit pass, no incremental risk.
- **2026-05-01T00:00:00Z — `\bSJ\b` scrub: specify the role-classification rule or punt with "(e.g.)" wording?** — Decision: A — specify the rule, not just an example. Plan/review docs use `"the maintainer"` or `"the reviewer"` (whichever the surrounding sentence implies); product-facing fixtures (`requirements.human.md`) use `"the user"`. No blind sed. Rationale: "explicit over clever"; example-driven instructions produce inconsistent or contextually wrong scrubs at execution time.
- **2026-05-01T00:00:00Z — Replace `~/workspace/linkedout-oss` in `setup:5` with invented prose, drop the path-bearing sentence, or anonymize the path only?** — Decision: A — surgical deletion of the `"Mirrors ~/workspace/linkedout-oss/setup. "` sentence; keep the rest of the comment ("Takes a fresh clone of github.com/sridherj/diecast..." onward) intact. Rationale: when scrubbing PII, default to deletion of the leaky line rather than invention of replacement prose. The remaining `github.com/sridherj/diecast` is exempt — `bin/lint-anonymization` allowlists `github.com/sridherj` via `(?<!github\.com/)` lookarounds (canonical public URL).
- **2026-05-01T00:00:00Z — Consolidate the workflow's prereq-install into one composite step, or keep separate steps for uv / tmux / fake-claude?** — Decision: A — keep separate `- name:` steps. Rationale: separate steps render as separate checkmarks in the GH Actions UI; failure attribution is one click instead of a log scroll. DRY win for consolidation is small; operability cost is real. No plan change.
- **2026-05-01T00:00:00Z — Scenario 3b cascade: tighten the Risk row + add a docker-based 3b probe, or accept the contradiction with the "all 3 workflows green" outcome?** — Decision: A — rewrite the Risk row to "do NOT push if 3b stays red after tmux fix; investigate config-write regression in same branch" and add the docker probe (`./setup --no-prompt && grep upgrade_snooze ~/.cast/config.yaml`) to the Verification block. Rationale: `tests/e2e-test.sh:188` exits 1 on any single scenario failure — there is no "ship 9-of-10 green" path; the original Risk row's mitigation contradicted the test contract. "More edge cases, not fewer."
- **2026-05-01T00:00:00Z — Add a "lint still bites" smoke check to Verification, trust visual diff inspection, or add per-pattern unit tests?** — Decision: A (tightened) — add a `git diff bin/lint-anonymization` inspection line to Verification specifying the exact allowed scope of changes; defer to existing `tests/test_lint_anonymization.py` + workflow's `pytest tests/` step for structural coverage. Rationale: per the test file's docstring (Phase-1.3 D9), per-pattern-fires tests are explicitly out of scope; reversing that decision in a scope-reduction plan would scope-creep.
- **2026-05-01T00:00:00Z — Add a per-test verification line for `tests/test_lint_anonymization.py` after Track 1a's lint-script edit?** — Decision: B — no plan change. Rationale: investigated `tests/test_lint_anonymization.py` directly; its four tests (clean-tree-zero, forbidden-fixture-excluded, exemption-marker-skip, performance) do NOT assert on `FORBIDDEN_PATTERNS` membership/count per the file's D9 docstring. Removing the ptyxis row will not break it. Existing `pytest tests/` line in Verification suffices. Recorded so the next reviewer does not re-raise.
- **2026-05-01T00:00:00Z — Add apt cache and/or Docker layer cache to speed up the workflows?** — Decision: A — no plan change; record as known-acceptable performance cost. Rationale: SCOPE REDUCTION mode declared at line 10. Sub-phase 1's outcome is "workflows green," not "workflows fast." `apt-get update` per-run (~10s) and Docker no-cache rebuild (~30-60s) are real future-work optimizations but adding them expands the plan from "fix CI" to "improve CI."
