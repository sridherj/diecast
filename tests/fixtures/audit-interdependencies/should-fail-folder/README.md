# should-fail-folder fixture

**Asserts:** `bin/audit-interdependencies --fail-on=red --fixture-dir <this>` exits **1**.

The agent writes to `~/.claude/output.md` — a disallowed user-home path that
violates US2 portability. The folder auditor must emit a **red** finding with
reason `"User-home Claude config; violates US2"`. Pytest asserts both the
non-zero exit code and the presence of that reason string in the `--json`
output.

If this fixture starts passing (exit 0), the folder check has regressed and
agents could silently smuggle non-portable paths into the published fleet.
