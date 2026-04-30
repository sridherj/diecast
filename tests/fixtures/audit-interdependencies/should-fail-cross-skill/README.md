# should-fail-cross-skill fixture

**Asserts:** `bin/audit-interdependencies --fail-on=red --fixture-dir <this>` exits **1**.

The agent invokes `Skill('cast-missing-skill')` — a skill that is not present
in the fixture's `skills/` tree. The auditor (naming mode picks this up,
since cross-skill mode only routes through skills already in the fleet) must
emit a **red** finding with reason `"target not found in fleet"`. Pytest
asserts both the non-zero exit code and the presence of that reason string
in the `--json` output.

If this fixture starts passing (exit 0), the cross-skill / naming check has
regressed and `Skill(...)` invocations targeting deleted or renamed skills
would no longer fail CI.

> NOTE: cross-skill mode currently only emits **yellow** (mixed invocation
> patterns across SHARED_SKILLS); reds for missing skill targets are surfaced
> via naming mode. The fixture still asserts the gate functions for missing
> skills regardless of which sub-mode classifies it.
