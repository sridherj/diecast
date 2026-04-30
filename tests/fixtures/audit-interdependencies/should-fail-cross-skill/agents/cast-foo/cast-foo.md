# cast-foo

A planted-failure agent used to assert the cross-skill gate.

## Purpose

Invokes Skill('cast-missing-skill') for delegation. The skill target is not
present in the fixture's `skills/` tree, so the auditor must classify the
reference as **red** ("target not found in fleet") and the script must exit 1
under `--fail-on=red`.
