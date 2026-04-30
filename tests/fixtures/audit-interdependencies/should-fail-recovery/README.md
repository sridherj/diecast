# should-fail-recovery fixture

**Asserts:** `bin/audit-interdependencies --fail-on=red --fixture-dir <this>` exits **1**.

The agent reads `goal.yaml` with no fallback prose, no early-exit, and no
user prompt nearby. The recovery auditor must emit a **red** finding with
reason `"No fallback / no early-exit / no user prompt"`. Pytest asserts both
the non-zero exit code and the presence of that reason string in the `--json`
output.

If this fixture starts passing (exit 0), the recovery check has regressed and
agents could silently crash on missing inputs without surfacing the failure
to the user.

> NOTE: The full recovery-finding class is currently deferred to GitHub
> issue #2 (Phase 3a tightens the classifier). The planted fixture still
> exercises the existing classifier so a regression in its red-emission path
> is caught.
