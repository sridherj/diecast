#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# tests/setup-correctness-test.sh — three local-only correctness scenarios
# for ./setup. Heavier matrix lives in tests/Dockerfile.test-e2e (sp3).
#
# Scenarios:
#   1. Clean install            — fake HOME, ./setup --no-prompt, assert plumbing.
#   2. Re-install with sentinel — sentinel survives in .cast-bak-<ts>/.
#   3. --dry-run                — exits 0, leaves filesystem alone.
#
# Uses tests/fixtures/fake-claude to stand in for `claude` so we don't need
# real Claude Code or an API key in CI.

set -euo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
FIXTURE_DIR="${REPO_DIR}/tests/fixtures"

PASS=0
FAIL=0

run_case() {
  local name="$1"
  shift
  printf '\n── %s ──\n' "${name}"
  if "$@"; then
    printf '  [PASS] %s\n' "${name}"
    PASS=$((PASS + 1))
  else
    printf '  [FAIL] %s\n' "${name}" >&2
    FAIL=$((FAIL + 1))
  fi
}

with_fake_home() {
  # echo path to a freshly-created tmp dir to use as $HOME (caller cleans it up).
  mktemp -d -t diecast-setup-test-XXXXXX
}

assert_file() {
  if [[ -e "$1" ]]; then
    return 0
  fi
  echo "    assert_file: missing ${1}" >&2
  return 1
}

assert_no_file() {
  if [[ ! -e "$1" ]]; then
    return 0
  fi
  echo "    assert_no_file: unexpected ${1}" >&2
  return 1
}

assert_grep() {
  if grep -q -- "$1" "$2" 2>/dev/null; then
    return 0
  fi
  echo "    assert_grep: pattern '$1' not in $2" >&2
  return 1
}

# ── Scenario 1: clean install ──────────────────────────────────────
case_clean_install() {
  local fake_home rc=0
  fake_home="$(with_fake_home)"

  _case_clean_install_body() {
    HOME="${fake_home}" \
    PATH="${FIXTURE_DIR}:${PATH}" \
    CLAUDE_FAKE_LOG="${fake_home}/claude-invocations.log" \
    CAST_TERMINAL="" \
      "${REPO_DIR}/setup" --no-prompt --dry-run >/dev/null

    # --dry-run leaves filesystem untouched. Re-run for-real to assert plumbing.
    HOME="${fake_home}" \
    PATH="${FIXTURE_DIR}:${PATH}" \
    CLAUDE_FAKE_LOG="${fake_home}/claude-invocations.log" \
    CAST_TERMINAL="" \
      "${REPO_DIR}/setup" --no-prompt >/dev/null || return 1

    assert_file "${fake_home}/.cast/config.yaml" || return 1
    assert_grep "^terminal_default:" "${fake_home}/.cast/config.yaml" || return 1
    assert_grep "auto_upgrade:" "${fake_home}/.cast/config.yaml" || return 1

    # gstack-pattern install seam: ~/.claude/skills/diecast symlink → repo,
    # binaries reachable through bin/. No PATH shim at ~/.local/bin/cast-server.
    assert_no_file "${fake_home}/.local/bin/cast-server" || return 1
    if [[ ! -L "${fake_home}/.claude/skills/diecast" ]]; then
      echo "    ~/.claude/skills/diecast is not a symlink" >&2
      return 1
    fi
    assert_file "${fake_home}/.claude/skills/diecast/bin/cast-server" || return 1
    assert_file "${fake_home}/.claude/skills/diecast/bin/cast-hook" || return 1

    # At least one cast-* agent landed.
    if ! ls "${fake_home}/.claude/agents/" 2>/dev/null | grep -q '^cast-'; then
      echo "    no cast-* agents materialized under ~/.claude/agents/" >&2
      return 1
    fi
    return 0
  }

  _case_clean_install_body || rc=$?
  rm -rf "${fake_home}"
  return $rc
}

# ── Scenario 2: re-install preserves a sentinel via .cast-bak-* ────
case_reinstall_sentinel() {
  local fake_home rc=0
  fake_home="$(with_fake_home)"

  _case_reinstall_sentinel_body() {
    HOME="${fake_home}" \
    PATH="${FIXTURE_DIR}:${PATH}" \
    CLAUDE_FAKE_LOG="${fake_home}/claude-invocations.log" \
    CAST_TERMINAL="" \
      "${REPO_DIR}/setup" --no-prompt >/dev/null

    local sentinel="${fake_home}/.claude/agents/cast-refine-requirements/sentinel.txt"
    mkdir -p "$(dirname "${sentinel}")"
    echo "I am a planted sentinel" > "${sentinel}"

    # Sleep 1 second so the second run gets a distinct UTC RUN_TIMESTAMP.
    sleep 1

    HOME="${fake_home}" \
    PATH="${FIXTURE_DIR}:${PATH}" \
    CLAUDE_FAKE_LOG="${fake_home}/claude-invocations.log" \
    CAST_TERMINAL="" \
      "${REPO_DIR}/setup" --no-prompt >/dev/null

    # Sentinel must now live under ~/.claude/.cast-bak-<ts>/agents/cast-refine-requirements/
    local found
    found="$(find "${fake_home}/.claude" -path '*.cast-bak-*/agents/cast-refine-requirements/sentinel.txt' -print -quit 2>/dev/null || true)"
    if [[ -z "${found}" ]]; then
      echo "    sentinel not preserved into a .cast-bak-* dir" >&2
      return 1
    fi
    assert_grep "I am a planted sentinel" "${found}" || return 1
    return 0
  }

  _case_reinstall_sentinel_body || rc=$?
  rm -rf "${fake_home}"
  return $rc
}

# ── Scenario 3: --dry-run leaves filesystem alone ─────────────────
case_dry_run() {
  local fake_home rc=0
  fake_home="$(with_fake_home)"

  _case_dry_run_body() {
    HOME="${fake_home}" \
    PATH="${FIXTURE_DIR}:${PATH}" \
    CLAUDE_FAKE_LOG="${fake_home}/claude-invocations.log" \
    CAST_TERMINAL="" \
      "${REPO_DIR}/setup" --no-prompt --dry-run >/dev/null || return 1

    assert_no_file "${fake_home}/.claude" || return 1
    assert_no_file "${fake_home}/.cast" || return 1
    assert_no_file "${fake_home}/.local/bin/cast-server" || return 1
    return 0
  }

  _case_dry_run_body || rc=$?
  rm -rf "${fake_home}"
  return $rc
}

# ── Run ────────────────────────────────────────────────────────────
run_case "clean install"            case_clean_install
run_case "re-install with sentinel" case_reinstall_sentinel
run_case "--dry-run is read-only"   case_dry_run

printf '\nResults: %d passed, %d failed.\n' "${PASS}" "${FAIL}"
[[ "${FAIL}" -eq 0 ]] || exit 1
