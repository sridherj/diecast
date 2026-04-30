# cast-foo

A planted-failure agent used to assert the folder-audit gate.

## Purpose

Writes the audit report to ~/.claude/output.md when the run completes. That
path lives under the user-home `~/.claude/` prefix, which violates US2
(install paths must remain user-local and project-portable). The folder
auditor must classify this as **red** and the script must exit 1 under
`--fail-on=red`.
