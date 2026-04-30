# removed in Diecast scope-prune; see docs/scope-prune.md
"""Sync engine — stubbed; see docs/scope-prune.md."""

_REMOVED_MSG = "removed in Diecast scope-prune; see docs/scope-prune.md"


def full_sync(*args, **kwargs):
    raise NotImplementedError(_REMOVED_MSG)


def incremental_sync(*args, **kwargs):
    raise NotImplementedError(_REMOVED_MSG)
