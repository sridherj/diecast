# sp2a_hat_agent — B4 post-execution review followup

## Classification (Step R.1)

**coding** — Rule #1 of `docs/reference/subphase-coding-classifier.ai.md` applies
unambiguously: the verification section names test scripts (`tests/check-distinctness.sh`,
`tests/check-failure-path.sh`) and specific file paths (`agents/cast-hat-researcher/…`), and
the activities are `Write`/`Edit`/file-creation. Closest worked example: #2
(`sp2_b6_terminal_portability` — creates files under `agents/`, edits prompts). Not ambiguous,
so no `cast-interactive-questions` prompt was needed.

## cast-review-code dispatch (Step R.2b / R.4)

**Status: review-unavailable (recorded, non-blocking).**

`cast-review-code` launches an *independent reviewer in a separate terminal tab* and the B4
dispatch is routed through `/cast-child-delegation`, which performs an HTTP `/trigger` against
a running cast-server with a live tmux dispatch loop. This sub-phase executed in an autonomous
single-context run with no live dispatch loop and no terminal-tab surface available, so the
child reviewer could not be launched. Per the runner's Step R.4 failure-handling rule, this is
recorded here and the pipeline continues — it does NOT block sp2a.

**To run the review manually:**

```
/cast-review-code agents/cast-hat-researcher/
```

## What stood in for the external review (honest substitute, not a replacement)

The load-bearing correctness of this deliverable is guarded deterministically and was exercised
in-run:

- `tests/check-distinctness.sh` — PASS (SC-002 no cross-hat leak, SC-003 no-80/20-in-FP,
  provenance/divergence check). Also exercised in note-mode against synthetic notes: passes on
  clean notes, exits non-zero on an injected 80/20 leak in the first-principles note.
- `tests/check-failure-path.sh` — PASS (FR-016/US12: no note file + contract-v2 `status:"failed"`).
- `bash -n` syntax check on both scripts — clean (shellcheck not installed on this host;
  recommend running `shellcheck agents/cast-hat-researcher/tests/*.sh` when the external review runs).
- `/cast-agent-design-guide` conformance review (Activity A) — clean on all four dimensions
  (frontmatter, I/O contract, non-interactive correctness, empty `allowed_delegations`).
- `bin/generate-skills` — agent discovered; stub emitted with internal-pipeline-unit framing
  (no `cast-web-researcher` trigger collision).

## Open items for the manual reviewer to confirm

1. **`headless: true` divergence (conscious choice).** The closest structural peer,
   `cast-subphase-runner`, sets `headless: true` / `headless`-style keys in its `config.yaml`,
   and so does `cast-requirements-gapfill`. This agent does NOT, because (a) the binding plan
   Decision #1 pinned the 4-key schema `model/timeout_minutes/context_mode/proactive`, and
   (b) `grep` finds ZERO runtime consumers of `headless` in `cast-server/src`, `bin`, or
   `agents/_shared` — it is inert/advisory metadata today. Honoring the binding decision over an
   inert key. Flag for the reviewer if fleet convention later makes `headless` load-bearing.
2. The 8-hat **live acceptance run** (8 real invocations on a real step) is NOT executed — it
   requires live web research + a sample goal. It is recorded as the standing Phase-3a
   first-fan-out acceptance procedure in `tests/acceptance.md`. The deterministic gates that
   CAN run without live web access all pass.
