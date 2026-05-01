# Diecast Release Checklist

Run this checklist on the release branch before each tag. Items here
exist because something will rot if a maintainer ships without checking
— don't skip steps.

## cast-crud worked example regeneration (Phase 5 — v1)

This is the **US15 coherent-unit acceptance gate**. The
`docs/maker-checker.md` walkthrough plus the manual end-to-end test
below is what verifies the cast-crud reference family — there is no
CI invariant (`bin/smoke-cast-crud` was dropped 2026-04-30 per
Q#25 + Q#28). If this section is incomplete, do not tag.

- [ ] Re-invoke the cast-crud chain against
      `Widget { id, name, sku, price_cents, created_at }` in a clean
      tmp goal directory (`/tmp/cast-crud-e2e-$(date +%s)`).
- [ ] Capture the orchestrator dispatch log,
      `cast-crud-compliance-checker` output,
      `cast-integration-test-orchestrator` output,
      `cast-seed-db-creator` output (first run + re-run).
- [ ] Diff captured output against the current
      `docs/maker-checker.md` "real output" blocks. If the chain
      produces different output (an agent prompt changed somewhere),
      verify the change is intentional and update the blocks.
- [ ] Run `pytest tests/cast-crud-worked-example/` — must be green.
- [ ] Run `pytest tests/cast-crud-note-fixture/` — must be green
      (generality regression net per sp2 verification (g) /
      Q#27).
- [ ] Run `bin/lint-anonymization` over the whole repo — must report
      clean across `agents/cast-{crud,schema,entity,repository,service,controller,seed}-*/`,
      `tests/cast-crud-worked-example/`, `tests/cast-crud-note-fixture/`,
      `tests/cast-crud/`, `docs/maker-checker.md`, and
      `docs/release-checklist.md`. Any remaining repo-wide hits must
      be cleared by Phase 6.1; if not, escalate before tagging.
- [ ] Run the manual end-to-end test (steps below) and record the
      result in the log section.
- [ ] Mark US15 coherent-unit acceptance: PASS / FAIL on this release
      in the log section below.

### Manual end-to-end test (the US15 gate)

Walk the `docs/maker-checker.md` walkthrough exactly as a maintainer
would. Do not skip steps; do not skim.

1. Open a fresh goal directory:
   ```bash
   mkdir -p /tmp/cast-crud-e2e-$(date +%s) && cd "$_"
   ```
2. Invoke `/cast-crud-orchestrator` with the Widget shape from the
   walkthrough Step 1.
3. Confirm each maker step produces output matching the "real output"
   blocks in `docs/maker-checker.md`. Allow minor diff in timestamps,
   IDs, and absolute paths; flag any structural diff (different field
   set, different filter spec, different MVCS layer wiring).
4. Run `pytest` against the generated test directory — must be green
   on first try.
5. Run the seed agents twice and confirm idempotency — second run
   inserts 0 rows.
6. Record the result in the log section below with date + tag.

## How to record failure

If the chain breaks on the release branch (orchestrator dispatch
fails, pytest red, checker fires false-positive on the worked example,
seed agent re-run inserts duplicates):

1. Identify which agent failed; attach the relevant
   `.agent-run_*.output.json` excerpt to the release-checklist note in
   the log below.
2. Decide:
   - **Fix-and-retry** — file a GitHub issue, patch the agent prompt,
     re-run the chain, re-tick the boxes.
   - **Block-the-tag** — the chain is fundamentally broken; do not
     ship until fixed. Record the reason in `CHANGELOG.md` for
     traceability.
3. Record the decision and the issue / PR URL in
   `CHANGELOG.md` so the next release maintainer can find the
   investigation trail.

## How to record success

```markdown
### v1.0 — 2026-XX-XX

- [x] cast-crud chain re-run against Widget shape: PASS
- [x] cast-crud chain re-run against Note shape: PASS (generality)
- [x] pytest tests/cast-crud-worked-example/: PASS
- [x] pytest tests/cast-crud-note-fixture/: PASS
- [x] bin/lint-anonymization: clean
- [x] docs/maker-checker.md "real output" blocks: no diff
- [x] Manual end-to-end test: PASS
- [x] US15 coherent-unit acceptance: PASS

Maintainer: <name>
Run logs: <path or PR link>
```

## Log

<!-- Append one block per tag. Most recent on top. -->

### v1 (Phase 5 close-out — 2026-04-30)

- [x] `docs/maker-checker.md` authored from real captured output
      (Widget dry-run from `tests/cast-crud-worked-example/dry_run_widget.md`,
      Note generality dry-run from
      `tests/cast-crud-note-fixture/dry_run_note.md`).
- [x] `docs/release-checklist.md` authored with regeneration policy.
- [ ] Manual end-to-end test against Widget shape — DEFERRED to v1
      release tag (requires live cast-server invocation in a fresh
      tmp goal dir; cannot be run from sp4 in unattended mode).
- [ ] `/cast-agent-compliance` clean on walkthrough invocations —
      DEFERRED to v1 release tag (requires live agent dispatch).
- [ ] `bin/lint-anonymization` clean repo-wide. Phase 6.1
      launch-readiness sweep must clear any remaining hits before tag.
- [ ] US15 coherent-unit acceptance: PENDING (gated on the four
      DEFERRED items above).

Maintainer: Phase 5 sp4 dispatcher
