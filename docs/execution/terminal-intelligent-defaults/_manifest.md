# Execution Manifest: Terminal Intelligent Defaults

## How to Execute

Each sub-phase runs in a **separate Claude context** and corresponds to one commit in the planned 2-commit PR. For each sub-phase:

1. Start a new Claude session.
2. Tell Claude: "Read `docs/execution/terminal-intelligent-defaults/_shared_context.md` then execute `docs/execution/terminal-intelligent-defaults/spN_<name>/plan.md`."
3. After completion, update the Status column below and commit.

Both sub-phases land on the same branch / PR. Commit boundary == sub-phase boundary, per the plan's "Roll-out" section.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|---------------|-----------|--------|-------|
| 1 | Resolver Fixes (key alias + de-vendor + loud failure) | `sp1_resolver_fixes/` | — | Not Started | Commit 1 of the PR. Self-contained, fully unit-testable. Includes `test_b6_terminal_resolution.py` updates. |
| 2 | `bin/cast-doctor --fix-terminal` + docs + parity test | `sp2_cast_doctor_fix_terminal/` | 1 | Not Started | Commit 2 of the PR. Reads `_SUPPORTED.keys()` established by sp1; parity test asserts bash hardcoded list matches. |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
sp1_resolver_fixes  ──▶  sp2_cast_doctor_fix_terminal
   (commit 1)              (commit 2)
```

Strictly sequential. No parallelism — sp2 reads from interfaces sp1 establishes (`_SUPPORTED` final entries, `_autodetect()` helper signature) and the docs/parity-test changes describe behavior shipped by sp1.

## Execution Order

### Sequential Group 1
1. **sp1_resolver_fixes** — `agents/_shared/terminal.py` (alias + improved `ResolutionError` + `_autodetect`), `cast-server/cast_server/infra/terminal.py` (de-vendored to shim), `tmux_manager.py` (re-raise), `agent_service.py` (catch and fail), `tests/test_b6_terminal_resolution.py` (extended).

### Sequential Group 2 (after Group 1)
2. **sp2_cast_doctor_fix_terminal** — `bin/cast-doctor` (`--fix-terminal` flag + sync hardcoded list), `docs/reference/supported-terminals.md` (new flow + alias + first-run section), `tests/test_cast_doctor.py` (subprocess tests + parity).

## Open Questions

See `_review_summary.md` — must be resolved before sp1 starts (one of the questions affects the contents of `_SUPPORTED`, which sp2's parity test asserts on).

## Progress Log

<!-- Update after each sub-phase completes -->
