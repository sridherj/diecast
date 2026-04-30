# Review Summary: Fix Trigger 500 on Malformed `delegation_context`

> **Review style:** SMALL CHANGE — at most 1 issue per section per sub-phase. The plan is intentionally minimal (3 files, ~30 LOC of server code, 1 line of docs, 3 new tests), so this review is lightweight.

## Open Questions

1. **(sp1a) Where exactly is `.delegation-<run_id>.json` written?** The test helper `_read_delegation_file` assumes the file lives under `<external_project_dir>/.cast/`, but the actual write site lives in `cast_server/services/agent_service.py`. The plan acknowledges this and tells the executor to grep for `\.delegation-` write sites and adjust. **Action for the user:** confirm this is acceptable as a discovery step, or pre-decide the path so sp1a doesn't have to discover it. **Recommendation:** leave it as a discovery step — the executor will see the existing `.delegation-run_*.json` files in `.cast/` and `goals/improved-first-launch/` and reverse-engineer quickly.
2. **(sp1a) Is the synchronous-write assumption true?** If `agent_service.trigger_agent` writes the delegation file *synchronously* during the request handler, the file-based assertion works. If the file is written by a background launcher subprocess, the test must instead capture the pydantic model in-flight (e.g., `monkeypatch.setattr(agent_service, "trigger_agent", ...)`). The plan documents the fallback, but the executor will need to make that judgment call. **Action for the user:** none unless you want to pre-decide; the executor has guidance.

## Review Notes by Sub-Phase

### sp1a_server_fix

- **Architecture** — *no issues.* All defaulting at route boundary via `setdefault`, mirrors existing `goal_slug` / `parent_run_id` pattern (Decision #2 from plan). Service-layer fallback (`agent_service.py:1001`) deliberately untouched; defense-in-depth retained.
- **Code Quality** — *no issues.* `include_url=False` chosen to avoid leaking pydantic version URLs in the 422 envelope. Try/except is narrowly scoped to the `DelegationContext(**...)` line, not the whole handler.
- **Tests** — *one concern.* The third test (`test_trigger_preserves_explicit_output_dir`) is the regression-test recommended in plan Decision #3. It is included. Coverage for the three plan-mandated cases (a/b/c) is complete. Single open question above on file-write-location discovery.
- **Performance** — *not applicable.* No hot path affected; only error-path construction adds a `try/except`.

### sp1b_skill_docs

- **Architecture** — *not applicable.* Documentation-only change.
- **Code Quality** — *no issues.* Single-line replacement, exact wording specified verbatim, surrounding bullets preserved. Plan explicitly forbids broader cleanup.
- **Tests** — *not applicable* — no test surface for SKILL.md content. Validation is a `git diff --stat` shape check (`1 insertion, 1 deletion`).
- **Performance** — *not applicable.*

## Cross-Sub-Phase Consistency

- The reworded SKILL.md line (sp1b) references `<goals>/<goal_slug>` and `cast-delegation-contract.collab.md:66`. The server fix (sp1a) implements exactly that fallback (`str(_config.GOALS_DIR / goal_slug)`). Server, spec, and skill text agree.
- The two sub-phases touch disjoint files; no merge conflict path.

## Risk Notes

- **Low risk overall.** The pydantic default-empty change widens what the model accepts; the route-level `setdefault` ensures the value is always populated before reaching `agent_service`. The `include_url=False` keyword is supported in pydantic v2 (`include_url` was added in 2.0); confirm the project pins pydantic ≥ 2.0 (a quick `grep pydantic cast-server/pyproject.toml` will tell you).
- **No breaking changes.** Callers passing an explicit `output_dir` see no change (locked down by test c). Callers passing `delegation_context = None` see no change. Only the previously-500ing path is affected, and only to upgrade it to 200/422.
