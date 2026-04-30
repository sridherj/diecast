# Spec Registry

All product specs for Diecast.

| Spec File | Feature | Module | Scope | Status | Version |
|-----------|---------|--------|-------|--------|---------|
| `cast-delegation-contract.collab.md` | cast-delegation-contract | cast-runtime | Parent-child file-based delegation contract: output-file naming, contract-v2 schema reference, terminal status set, polling backoff, idle-timeout, heartbeat-by-mtime, atomic write, RUN_ID-scoped path validation, test hooks | Draft | 1 |
| `cast-output-json-contract.collab.md` | cast-output-json-contract | cast-runtime | Contract-v2 schema for `<goal_dir>/.agent-run_<RUN_ID>.output.json`: field-by-field types, allowed status set, artifacts[] item shape, per-agent extension placeholder | Draft | 1 |
| `cast-init-conventions.collab.md` | cast-init-conventions | cast-init | File conventions for cast-* artifacts: authorship suffixes (`.human.md`/`.ai.md`/`.collab.md`), date prefixes (`YYYY-MM-DD-<slug>.md`), `_v2` versioning rule, `<goal_name>` flat-vs-folder heuristic, per-agent default write paths. Source of truth referenced by `/cast-init`'s `CLAUDE.md` template. | Draft | 1 |
