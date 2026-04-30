# Diecast tests

Pytest unit tests live in `tests/test_*.py`. Bash integration tests live in
`tests/*.sh`. Fixtures (test doubles, golden files, fake binaries) live in
`tests/fixtures/`.

Run everything with:

```bash
uv run --project . pytest tests/                  # Python suite
bash tests/setup-correctness-test.sh              # ./setup correctness
```

CI runs the same commands in `.github/workflows/`.

## Bash integration tests

| Script | Scope |
|--------|-------|
| `tests/setup-correctness-test.sh` | Three local-only correctness scenarios for `./setup` (clean install, sentinel re-install, `--dry-run`). Wired into `.github/workflows/setup-correctness.yml`. |
| `tests/test_cast_upgrade.sh` | Eleven local-only scenarios for `/cast-upgrade` (skill shape, ten plan-numbered scenarios). Uses `tests/fixtures/local-bare-repo/` as the upstream "remote" so CI does not hit GitHub. |

The full Docker-fixture e2e for `./setup` is out of scope for sp1 — it lands
in sp3 as `tests/Dockerfile.test-e2e`.

## Local bare-repo fixture

`tests/fixtures/local-bare-repo/` is a checked-in **bare git repository**
that stands in for `origin` in `/cast-upgrade` integration tests. It carries
two commits on `main`:

1. `v0: initial fixture commit` — `VERSION=v0`, plus a `bin/marker.sh`
   that prints `marker v0` and a no-op `setup` shim.
2. `v1: bump marker` — `VERSION=v1`, `bin/marker.sh` prints `marker v1`.

Tests `git clone` the fixture into a per-test `mktemp -d`, optionally roll
back to `HEAD~1`, plant local edits, and exercise the `git stash` + `git
pull --ff-only` + `setup --upgrade` sequence the skill prescribes.

### Regenerating the fixture

If the fixture ever gets stale, regenerate it from a scratch worktree:

```bash
rm -rf tests/fixtures/local-bare-repo
mkdir -p tests/fixtures/local-bare-repo
( cd tests/fixtures/local-bare-repo && git init --bare -q . )

# Seed two commits via a scratch clone.
TMP=$(mktemp -d) && git clone -q tests/fixtures/local-bare-repo "$TMP"
( cd "$TMP" \
  && git config user.email fixture@diecast.local \
  && git config user.name "Diecast Fixture" \
  && echo v0 > VERSION \
  && mkdir -p bin \
  && printf '%s\n' '#!/usr/bin/env bash' 'echo "marker v0"' > bin/marker.sh \
  && printf '%s\n' '#!/usr/bin/env bash' '# fixture setup shim — no-op.' \
       'echo "[fixture-setup] mode=${UPGRADE_MODE:-0}" >&2' 'exit 0' > setup \
  && chmod +x bin/marker.sh setup \
  && git add -A && git commit -q -m "v0: initial fixture commit" \
  && git push -q origin HEAD:main \
  && echo v1 > VERSION \
  && printf '%s\n' '#!/usr/bin/env bash' 'echo "marker v1"' > bin/marker.sh \
  && chmod +x bin/marker.sh \
  && git add -A && git commit -q -m "v1: bump marker" \
  && git push -q origin HEAD:main )
rm -rf "$TMP"
```

The fixture is ~200K and ships in the repo. Do not add real upstream
content to it — it exists strictly as a local stand-in for `origin/main`
in tests.

## Fake `claude` CLI

`tests/fixtures/fake-claude` is a ~30-line bash script that stands in for the
real `claude` binary so integration tests do not need real Claude Code or an
API key. Tests prepend `tests/fixtures/` to `PATH` and the fake gets picked
up first.

The fake logs every invocation to the path in `$CLAUDE_FAKE_LOG` (default
`/tmp/claude-invocations.log`) so tests can assert what was called.

### CLI surface

| Invocation | Behavior | Log line |
|------------|----------|----------|
| `claude --version` | Prints `claude-fake 0.0.1-fake` to stdout, exits 0. | `version` |
| `claude --skill <name>` | No stdout, exits 0. | `skill <name>` |
| `claude -p '<prompt>'` | No stdout, exits 0. Prompt summary truncated to 80 chars. | `prompt <summary>` |
| `claude` (no args) | No stdout, exits 0. | `args=` |
| `claude <anything-else>` | No stdout, exits 0. | `args=<all-args>` |

### Test conventions

- Set `CLAUDE_FAKE_LOG` per test so concurrent tests do not stomp on each
  other:

  ```bash
  CLAUDE_FAKE_LOG="${TMPDIR:-/tmp}/case-$$.log" \
  PATH="${REPO_DIR}/tests/fixtures:${PATH}" \
  CAST_TERMINAL="" \
    "${REPO_DIR}/setup" --no-prompt
  ```

- Always set `HOME` to a `mktemp -d` so tests do not touch the real
  `~/.claude/` or `~/.cast/`.

- Always pass `--no-prompt` so `./setup` does not block waiting for
  interactive input.

### Extending the fake

If a new test needs behavior the fake does not expose, prefer adding a
narrow case to the existing `case "${1:-}"` block over forking a parallel
fake. Keep the script under ~50 lines and document any new flag here so
future contributors know what is exercised in CI.
