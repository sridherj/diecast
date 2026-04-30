# SPDX-License-Identifier: Apache-2.0
"""Trivial fixture migration for the e2e test.

Lives outside `migrations/` so it never applies to user installs. The
e2e test invokes:

    bin/run-migrations.py \
        --migrations-dir tests/migrations-fixtures \
        --applied-file /tmp/migrations.applied

…to keep `bin/run-migrations.py`'s code path warm without polluting the
v1 production migration set.
"""


def up(config: dict) -> None:
    """No-op apply — exists to exercise the runner."""


def down(config: dict) -> None:
    """No-op rollback — symmetric to up()."""
