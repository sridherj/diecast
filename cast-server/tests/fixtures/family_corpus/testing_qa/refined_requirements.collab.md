---
status: refined
scope_mode: hold
confidence:
  intent: high
  behavior: high
  constraints: medium
  out_of_scope: high
open_unknowns: 1
questions_asked: 0
classification:
  family: "testing_qa"
  confidence: 0.92
  alt_family: "bug_fix"
  reasoning: "The work builds end-to-end UI test infrastructure and stabilizes the runner-dispatch path under test — the deliverable is coverage and a trustworthy harness, not a single product feature or defect."
  uncertainty_factors:
    - "Some of the hardening fixes real dispatch defects, but the framing and deliverable are a test sweep and the harness it runs on."
  modifiers:
    irreversible: false
    unknown_cause: false
  confirmed_by: "manual"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

<!-- CORPUS-PROVENANCE: family=testing_qa — authored from the real cast-ui-test-harness work (e2e UI test infra + 9 noop test agents, runner-dispatch hardening; commits 27bc9c8 / 58f2661 / 25f16b8). -->

# Stand up the cast UI test harness and harden runner dispatch

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** cast-server/tests/ui/runner.py, cast-server/tests/ui/test_runner_dispatch.py

## Intent

**Job statement:** Build an end-to-end UI test harness for cast-server — a real runner that dispatches lightweight no-op test agents through the production path — and stabilize the dispatch contract under that harness so the suite is a trustworthy signal rather than a flake generator.

The render and delegation surfaces had grown faster than their test coverage. Manual clicking was the only way to confirm a dispatch actually launched, threaded its children, and wrote the canonical output envelope. The job is to make that automatic: a sweep that drives the real UI runner against a small fleet of no-op agents, asserts the dispatch and completion contract end to end, and fails loudly when the runner regresses. Where the harness exposes genuine dispatch defects, those are fixed; where a test is red for a known unfixed reason, it is skipped explicitly with the reason recorded — never silently disabled.

## Evidence

- **The harness exercises the production runner.** `tests/ui/runner.py` drives dispatch through the same path the live UI uses, not a stubbed shortcut, so a green run is real evidence the contract holds.
- **A fleet of nine no-op test agents** gives the sweep deterministic, cheap children to launch, thread, and complete without invoking real model work.
- **The canonical envelope was the first thing to break.** An early run showed test agents not writing the canonical `.agent-<run_id>.output.json` envelope; the fix made the no-op agents emit it, which is exactly what the completion assertions key on.
- **Honest red-state handling.** Nine delegation/UI tests that fail for known, unfixed reasons are marked skipped with their reason attached rather than deleted, so the suite's denominator stays truthful and the debt stays visible.

## Out of Scope

- Replacing the existing unit tests — the UI sweep is additive end-to-end coverage, not a rewrite of `test_*.py`.
- Fixing every red delegation test in this pass; the known failures are skipped-with-reason and tracked separately.
- Performance or load testing of the dispatcher; this harness asserts correctness of the dispatch-and-complete contract, not throughput.

## Open Questions

- **[OPEN]** Whether the nine skipped delegation/UI tests should block the suite once their underlying fixes land, or remain opt-in until the delegation surface itself stabilizes.
