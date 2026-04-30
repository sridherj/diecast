# Execution Manifest: Cast-Server First-Run Launch

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session in `/data/workspace/diecast`.
2. Tell Claude: "Read `docs/execution/cast-server-first-run-launch/_shared_context.md` then execute `docs/execution/cast-server-first-run-launch/spN_<name>/plan.md`."
3. After completion, update the Status column below and commit.

Each sub-phase corresponds to a section of the source plan (§A–§H). One commit per sub-phase is the recommended boundary. The full plan ships as one PR.

## Sub-Phase Overview

| #  | Phase                                                  | File                          | Depends On      | Status      | Notes |
|----|--------------------------------------------------------|-------------------------------|-----------------|-------------|-------|
| 1  | Port seam (`CAST_HOST` / `CAST_PORT` / `CAST_BIND_HOST`, default → 8005) | `sp1_port_seam/plan.md`           | —               | Done | §A. Foundation; markdown-aware sweep across ~30 sites; new `bin/sweep-port-refs.py`. |
| 2  | `bin/cast-doctor` extended preflight (python3 ≥3.11, tmux) | `sp2_doctor_preflight/plan.md`    | —               | Done | §D. Adds two RED-list checks with OS-aware install hints. |
| 3  | Alembic migrations + boot-time `_ensure_db_at_head()`   | `sp3_alembic_migrations/plan.md`  | —               | Done | §E. Hand-authored baseline (Decision #14); `tests/test_migrations.py`. |
| 4  | Server-log `RotatingFileHandler` (`server.log` 10MB×5)  | `sp4_log_rotation/plan.md`        | 1               | Not Started | §F. Edits `config.py` after sp1's constants land. `bootstrap.log` is owned by sp8. |
| 5  | Shellcheck CI (shebang-aware sweep over `setup` + `bin/*`) | `sp5_shellcheck_ci/plan.md`       | —               | Done | §G. New workflow + initial violation cleanup. Independent of all other sub-phases. |
| 6  | `/cast-doctor` skill + `/api/health` + bin docstring sweep | `sp6_cast_doctor_skill/plan.md`   | 1, 2            | Not Started | §H + Decision #19. Overrides terminal-defaults' user-discovery wording in 4 sites + `ResolutionError`. |
| 7  | README "Run the server" subsection + mental-model postscript | `sp7_readme_run_server/plan.md`   | 1               | Not Started | §C + §H step 6. Single owner of `README.md` edits. |
| 8  | `setup` step 8: launch + browser + alembic + PATH check | `sp8_setup_launch_step/plan.md`   | 1, 2, 3, 4, 6   | Not Started | §B. Renumber Step X/7 → X/8; calls `bin/cast-doctor --fix-terminal`; `alembic upgrade head` between step 5 and step 8. |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
sp1 ─────┬──▶ sp4 ──┐
         │           │
         ├──▶ sp6 ──┤
         │     ▲     │
sp2 ─────┘     │     ├──▶ sp8
               │     │
sp3 ───────────┴─────┤
                     │
sp7 ◀── sp1          │
                     │
sp5  (independent ─ may run anytime)
```

No gates. No skip-conditional branches.

## Execution Order

### Parallel Group 1 (no dependencies — kick off together)
1. **sp1_port_seam** — env-var seam, sweep, server-side URL constants, config.yaml DEFAULTS dict.
2. **sp2_doctor_preflight** — extend `bin/cast-doctor` RED list with python3 ≥3.11 and tmux.
3. **sp3_alembic_migrations** — Alembic baseline + boot-time check + migration tests.
5. **sp5_shellcheck_ci** — new workflow + clean SC2086/SC2155 violations.

### Parallel Group 2 (after sp1 and sp2 complete)
4. **sp4_log_rotation** — `RotatingFileHandler` for `server.log` (depends on sp1's `config.py` changes landing first to avoid merge conflicts on the same file).
6. **sp6_cast_doctor_skill** — `/cast-doctor` skill + `/api/health` + bin docstring sweep (depends on sp1 for `CAST_HOST`/`CAST_PORT` in the new endpoint, sp2 for the cast-doctor RED-list shape used by `/api/health`).
7. **sp7_readme_run_server** — `README.md` subsection (depends on sp1 for the new port number).

### Sequential Group 3 (after sp1, sp2, sp3, sp4, sp6 — sp5/sp7 can still be in flight or done)
8. **sp8_setup_launch_step** — `setup` step 8 launch + browser + PATH check + alembic invocation + `print_next_steps` rewrite. Step counter renumber Step X/7 → X/8 across 8 sed targets.

## Files Touched by More Than One Sub-Phase

| File | Sub-phases | Region split |
|------|-----------|---------------|
| `cast-server/cast_server/config.py` | sp1, sp4 | sp1 owns the new `DEFAULT_CAST_*` constants; sp4 owns the `RotatingFileHandler` block. Sequential dep enforces clean diffs. |
| `bin/cast-doctor` | sp2, sp6 | sp2 owns the RED-list additions (python3, tmux); sp6 owns header docstring at lines 8–12 + presentation-shift wording at 12, 57, 224, 241. Sequential dep. |
| `setup` | sp1, sp8 | sp1 owns the `step6_write_config` `DEFAULTS` dict additions only; sp8 owns the new `step8_*` function, alembic invocation, `print_next_steps` rewrite, and the Step X/7→X/8 renumber. Sequential dep. |
| `README.md` | sp7 only | sp7 owns the new "Run the server" subsection AND the §H step 6 mental-model postscript — single owner avoids merge conflicts. |
| `cast-server/README.md` | sp1 only | Swept by `bin/sweep-port-refs.py` along with all other markdown. |

## Out-of-Manifest

The following plan items intentionally have **no sub-phase**:

- "Out of scope" items in the plan (cloud deployment, multi-tenant routing, `/cast-init` parity, process supervision, etc.) — deferred to dedicated plans.
- `tests/test_cast_upgrade.sh:298` literal `:8000` — explicitly excluded from sp1's sweep (mock-curl payload, not a real URL).

## Progress Log

<!-- Update after each sub-phase completes. -->
