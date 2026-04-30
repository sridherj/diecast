# green-baseline fixture

**Asserts:** `bin/audit-interdependencies --fail-on=red --fixture-dir <this>` exits **0**.

A minimal one-agent fleet with no cross-references, no path tokens, and no
shared-skill invocations. Validates the audit script's clean-tree path.

If this fixture starts failing, the script has regressed in a way that
flags an entirely benign agent — review the offending check before merging.
