# cast-foo

A planted-failure agent used to assert the naming-audit gate.

## Purpose

Delegates to /cast-doesnotexist to handle downstream work. The target is not
present in this fixture's fleet, so the naming auditor must classify the
reference as **red** ("target not found in fleet") and the script must exit 1
under `--fail-on=red`.
