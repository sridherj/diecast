---
feature: cast-bulk-archive
module: cast-runtime
linked_files:
  - agents/cast-bulk-archive/cast-bulk-archive.md
last_verified: "2026-04-30"
---

# Cast Bulk Archive — Spec

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** agents/cast-bulk-archive/cast-bulk-archive.md

## Intent

Allow operators to archive completed runs in batches without manually
deleting each file. Frees inodes on the goal directory and simplifies
post-mortem inspection.

## User Stories

### US1 — Archive completed runs in one command (Priority: P1)

**As a** Diecast operator, **I want to** archive all completed runs older
than N days, **so that** my goal directory stays small.

**Independent test:** Seed 5 fake `.agent-run_*.output.json` with mtimes >7
days; run `cast-bulk-archive --older-than 7d`; assert all 5 are moved into
`archives/`.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `cast-bulk-archive --older-than 7d` runs, THE SYSTEM
  SHALL move every completed-status output file with mtime >7 days old into
  `<goal_dir>/archives/`.
- **Scenario 2:** WHEN `cast-bulk-archive` runs, IF a run is still
  `running`, THE SYSTEM SHALL skip it and log a `skipped: still running` line.

### US2 — Dry-run shows what would be archived (Priority: P2)

**As a** cautious operator, **I want to** preview the archive set before
committing, **so that** I do not accidentally archive a run I still need.

**Independent test:** Run with `--dry-run`; assert no files moved and the
preview list matches the would-archive set.

**Acceptance scenarios:**

- **Scenario 1:** WHEN `cast-bulk-archive --dry-run` runs, THE SYSTEM SHALL
  print the candidate file list and SHALL NOT move any files.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | Archive only files whose JSON `status` is `completed` or `partial`. | Skip `failed` to preserve forensic trail. |
| FR-002 | Move via `os.rename` (atomic on same filesystem). | Cross-fs requires fallback to copy+delete. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | Archives operation completes in <2s for 1000 files. | Pytest perf check. |
| SC-002 | Zero data loss across 100 random fault-injection runs. | Chaos test. |

## Open Questions

(none)
