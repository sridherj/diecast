# should-fail-naming fixture

**Asserts:** `bin/audit-interdependencies --fail-on=red --fixture-dir <this>` exits **1**.

The agent references `/cast-doesnotexist` — a name that is not present in the
fixture's fleet. The naming auditor must classify this as **red** with reason
`"target not found in fleet"`. Pytest asserts both the non-zero exit code and
the presence of that reason string in the `--json` output.

If this fixture starts passing (exit 0), the naming check has regressed —
broken cross-references would no longer fail CI.
