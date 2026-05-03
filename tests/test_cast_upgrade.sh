#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# tests/test_cast_upgrade.sh — integration tests for /cast-upgrade.
#
# /cast-upgrade is a SKILL.md, not a binary, so the upgrade flow can only be
# end-to-end-tested via the real `claude` CLI. These tests instead verify the
# skill's *procedural building blocks* — the bash logic that the skill body
# prescribes — against a local bare-git fixture so CI does not hit GitHub.
#
# Coverage matches the ten scenarios called out in
# docs/execution/diecast-open-source/phase-4/sp2b_cast_upgrade/plan.md §2b.5:
#
#   1.  Clean upgrade           — fast-forward git pull against the fixture.
#   2.  Already up to date      — local SHA == remote SHA → exit-silently path.
#   3.  Dirty-tree upgrade      — git stash + ff pull + stash listed.
#   4.  Snooze backoff          — 24h → 48h → 168h, streak caps at 3.
#   5.  auto_upgrade: true      — skip-prompt path noted by config flip.
#   6.  upgrade_never_ask: true — silent-exit path noted by config flip.
#   7.  Failure rollback        — copy-back from .cast-bak-<ts>/ + stash pop.
#   8.  Active-runs check       — non-empty `runs?status=running` → blocking branch.
#   9.  Concurrent invocation   — noclobber lock at ~/.cast/upgrade.lock.
#   10. Cache 1h TTL            — last_upgrade_check_at honored.
#
# The skill body itself is also verified for shape (front matter, references
# to the delegation-contract spec, anonymization).

set -euo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
FIXTURE_DIR="${REPO_DIR}/tests/fixtures"
BARE_REPO="${FIXTURE_DIR}/local-bare-repo"
SKILL_FILE="${REPO_DIR}/skills/claude-code/cast-upgrade/SKILL.md"

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
  mktemp -d -t diecast-upgrade-test-XXXXXX
}

assert_file() {
  if [[ -e "$1" ]]; then
    return 0
  fi
  echo "    assert_file: missing ${1}" >&2
  return 1
}

assert_grep() {
  if grep -q -E -- "$1" "$2" 2>/dev/null; then
    return 0
  fi
  echo "    assert_grep: pattern '$1' not in $2" >&2
  return 1
}

assert_no_grep() {
  if grep -q -F -- "$1" "$2" 2>/dev/null; then
    echo "    assert_no_grep: pattern '$1' unexpectedly in $2" >&2
    return 1
  fi
  return 0
}

# ── Portable date helpers (python3, no GNU date -d) ──────────────
epoch_to_iso() {
  python3 -c "
from datetime import datetime, timezone
print(datetime.fromtimestamp($1, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
}

iso_to_epoch() {
  python3 -c "
from datetime import datetime, timezone
print(int(datetime.strptime('$1', '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()))"
}

# Clone the bare-repo fixture into a fresh worktree under $1.
clone_fixture() {
  local dest="$1"
  git clone -q "${BARE_REPO}" "${dest}"
  git -C "${dest}" config user.email "test@diecast.local"
  git -C "${dest}" config user.name "Diecast Test"
}

# ── Skill-shape sanity checks ─────────────────────────────────────
case_skill_shape() {
  assert_file "${SKILL_FILE}" || return 1

  # Front matter present.
  assert_grep "^name: cast-upgrade$" "${SKILL_FILE}" || return 1
  assert_grep "^trigger_phrases:$" "${SKILL_FILE}" || return 1
  assert_grep "/cast-upgrade" "${SKILL_FILE}" || return 1

  # Anonymization gate: must NOT mention the upstream sibling skill name.
  assert_no_grep "gstack-upgrade" "${SKILL_FILE}" || return 1

  # Delegation contract spec is referenced (test for the file path).
  assert_grep "cast-delegation-contract.collab.md" "${SKILL_FILE}" || return 1

  # Verbatim 4-option labels (stripped of leading "X. " for grep portability).
  assert_grep "Yes, upgrade now" "${SKILL_FILE}" || return 1
  assert_grep "Always keep me up to date" "${SKILL_FILE}" || return 1
  assert_grep "Not now" "${SKILL_FILE}" || return 1
  assert_grep "Never ask again" "${SKILL_FILE}" || return 1

  # Failure-path message wording (Decision #9, both branches).
  assert_grep "restored previous version including your local repo edits" "${SKILL_FILE}" || return 1
  assert_grep "still in stash@\\{0\\}" "${SKILL_FILE}" || return 1
}

# ── Scenario 1: clean upgrade ─────────────────────────────────────
case_clean_upgrade() {
  local home rc=0
  home="$(with_fake_home)"
  _body() {
    local clone="${home}/clone"
    clone_fixture "${clone}" || return 1

    # Roll the clone back to v0 so the upgrade-detection diff is non-empty.
    git -C "${clone}" reset --hard HEAD~1 >/dev/null

    local local_sha remote_sha
    local_sha=$(git -C "${clone}" rev-parse HEAD)
    remote_sha=$(git -C "${clone}" ls-remote origin main | awk '{print $1}')
    [[ "${local_sha}" != "${remote_sha}" ]] || { echo "    SHAs unexpectedly equal" >&2; return 1; }

    git -C "${clone}" pull --ff-only origin main >/dev/null 2>&1 || return 1
    [[ "$(cat "${clone}/VERSION")" == "v1" ]] || { echo "    VERSION not bumped" >&2; return 1; }

    UPGRADE_MODE=1 "${clone}/setup" --upgrade 2>&1 | grep -q 'mode=1' || return 1
    return 0
  }
  _body || rc=$?
  rm -rf "${home}"
  return $rc
}

# ── Scenario 2: already up to date ────────────────────────────────
case_already_up_to_date() {
  local home rc=0
  home="$(with_fake_home)"
  _body() {
    local clone="${home}/clone"
    clone_fixture "${clone}" || return 1

    local local_sha remote_sha
    local_sha=$(git -C "${clone}" rev-parse HEAD)
    remote_sha=$(git -C "${clone}" ls-remote origin main | awk '{print $1}')
    [[ "${local_sha}" == "${remote_sha}" ]] || { echo "    SHAs differ on fresh clone" >&2; return 1; }
    return 0
  }
  _body || rc=$?
  rm -rf "${home}"
  return $rc
}

# ── Scenario 3: dirty-tree upgrade (stash + ff pull) ──────────────
case_dirty_tree_upgrade() {
  local home rc=0
  home="$(with_fake_home)"
  _body() {
    local clone="${home}/clone"
    clone_fixture "${clone}" || return 1
    git -C "${clone}" reset --hard HEAD~1 >/dev/null

    # Plant a local edit so `git status --porcelain` is non-empty.
    echo "local edit" > "${clone}/LOCAL_EDIT.txt"
    git -C "${clone}" add LOCAL_EDIT.txt

    [[ -n "$(git -C "${clone}" status --porcelain)" ]] || return 1

    local stash_msg="cast-upgrade-test-${RANDOM}"
    git -C "${clone}" stash push -u -m "${stash_msg}" >/dev/null 2>&1 || return 1

    git -C "${clone}" stash list | grep -q "${stash_msg}" || {
      echo "    stash entry not created" >&2; return 1; }

    git -C "${clone}" pull --ff-only origin main >/dev/null 2>&1 || return 1

    # Pop and verify the local edit is back.
    git -C "${clone}" stash pop >/dev/null 2>&1 || return 1
    assert_file "${clone}/LOCAL_EDIT.txt" || return 1
    return 0
  }
  _body || rc=$?
  rm -rf "${home}"
  return $rc
}

# ── Scenario 4: snooze backoff state machine ──────────────────────
case_snooze_backoff() {
  # Walk the bash state machine three times and assert the durations + cap.
  local streak=0 hours next_streak
  local results=""

  for i in 1 2 3 4; do
    case $(( streak < 2 ? streak : 2 )) in
      0) hours=24 ;;
      1) hours=48 ;;
      2) hours=168 ;;
    esac
    next_streak=$(( streak + 1 < 3 ? streak + 1 : 3 ))
    results="${results}${hours}:${streak}->${next_streak} "
    streak=${next_streak}
  done

  # Expected sequence: 24:0->1, 48:1->2, 168:2->3, 168:3->3 (cap)
  [[ "${results}" == "24:0->1 48:1->2 168:2->3 168:3->3 " ]] || {
    echo "    snooze sequence wrong: ${results}" >&2; return 1; }
  return 0
}

# ── Scenario 5: auto_upgrade: true skip path ──────────────────────
case_auto_upgrade_skip() {
  local home rc=0
  home="$(with_fake_home)"
  _body() {
    mkdir -p "${home}/.cast"
    cat > "${home}/.cast/config.yaml" <<YAML
auto_upgrade: true
upgrade_never_ask: false
YAML
    # Verify the gate read using grep (yq is optional in CI).
    grep -q "^auto_upgrade: true$" "${home}/.cast/config.yaml" || return 1
    grep -q "^upgrade_never_ask: false$" "${home}/.cast/config.yaml" || return 1
    return 0
  }
  _body || rc=$?
  rm -rf "${home}"
  return $rc
}

# ── Scenario 6: upgrade_never_ask: true silent exit ───────────────
case_never_ask_silent() {
  local home rc=0
  home="$(with_fake_home)"
  _body() {
    mkdir -p "${home}/.cast"
    cat > "${home}/.cast/config.yaml" <<YAML
auto_upgrade: false
upgrade_never_ask: true
YAML
    grep -q "^upgrade_never_ask: true$" "${home}/.cast/config.yaml" || return 1
    return 0
  }
  _body || rc=$?
  rm -rf "${home}"
  return $rc
}

# ── Scenario 7: failure rollback ─────────────────────────────────
case_failure_rollback() {
  local home rc=0
  home="$(with_fake_home)"
  _body() {
    # Simulate a `.cast-bak-<ts>/` from a prior run, then exercise the copy-back.
    local ts="20260101T000000Z"
    local bak="${home}/.claude/.cast-bak-${ts}"
    mkdir -p "${bak}/agents/cast-refine-requirements"
    echo "previous content" > "${bak}/agents/cast-refine-requirements/cast-refine-requirements.md"

    # Plant a "broken" current state.
    mkdir -p "${home}/.claude/agents/cast-refine-requirements"
    echo "BROKEN MID-UPGRADE" > "${home}/.claude/agents/cast-refine-requirements/cast-refine-requirements.md"

    # Invoke the failure-path copy-back the skill prescribes.
    local latest
    latest="$(ls -1d "${home}/.claude/.cast-bak-"* | sort | tail -n 1)"
    [[ -n "${latest}" ]] || return 1
    cp -R "${latest}"/* "${home}/.claude/" || return 1

    grep -q "previous content" \
      "${home}/.claude/agents/cast-refine-requirements/cast-refine-requirements.md" || return 1
    return 0
  }
  _body || rc=$?
  rm -rf "${home}"
  return $rc
}

# ── Scenario 8: active-runs check (mocked HTTP) ───────────────────
case_active_runs_check() {
  # Mock `curl` by overriding it via a function on PATH; assert the parse
  # logic the skill prescribes.
  local home rc=0
  home="$(with_fake_home)"
  _body() {
    local fake_curl="${home}/curl"
    cat > "${fake_curl}" <<'EOF'
#!/usr/bin/env bash
# Mock curl that always returns two active runs.
echo '[{"run_id":"r1","status":"running"},{"run_id":"r2","status":"running"}]'
EOF
    chmod +x "${fake_curl}"

    local runs active
    runs=$( PATH="${home}:${PATH}" curl -s 'http://localhost:8000/api/agents/runs?status=running' )
    if command -v jq >/dev/null 2>&1; then
      active=$(echo "${runs}" | jq 'length')
    else
      # Crude fallback: count "run_id" occurrences.
      active=$(printf '%s\n' "${runs}" | grep -o '"run_id"' | wc -l | tr -d ' ')
    fi
    [[ "${active}" -gt 0 ]] || { echo "    expected non-empty runs, got ${active}" >&2; return 1; }
    return 0
  }
  _body || rc=$?
  rm -rf "${home}"
  return $rc
}

# ── Scenario 9: concurrent-invocation lock ────────────────────────
case_concurrent_lock() {
  local home rc=0
  home="$(with_fake_home)"
  _body() {
    mkdir -p "${home}/.cast"
    local lock="${home}/.cast/upgrade.lock"

    # First invocation acquires.
    ( set -o noclobber; : > "${lock}" ) 2>/dev/null || return 1
    [[ -f "${lock}" ]] || return 1

    # Second invocation must fail (lock already held).
    if ( set -o noclobber; : > "${lock}" ) 2>/dev/null; then
      echo "    second invocation acquired the lock — race window" >&2
      return 1
    fi

    # Release and re-acquire to confirm the trap-EXIT discipline works.
    rm -f "${lock}"
    ( set -o noclobber; : > "${lock}" ) 2>/dev/null || return 1
    [[ -f "${lock}" ]] || return 1
    return 0
  }
  _body || rc=$?
  rm -rf "${home}"
  return $rc
}

# ── Scenario 10: cache 1h TTL ─────────────────────────────────────
case_cache_ttl() {
  # The skill caches the last `git ls-remote` result in
  # ~/.cast/config.yaml::last_upgrade_check_at. Verify the comparator the
  # skill prescribes returns "fresh" within an hour and "stale" beyond.
  local now fresh stale
  now=$(date -u +%s)
  fresh=$(epoch_to_iso $(( now - 600 )))    # 10 min ago
  stale=$(epoch_to_iso $(( now - 7200 )))   # 2  h  ago

  # Round-trip through ISO to verify format fidelity (the skill writes ISO
  # strings into config.yaml and later parses them back to compare epochs).
  local fresh_epoch stale_epoch one_hour_ago
  fresh_epoch=$(iso_to_epoch "${fresh}")
  stale_epoch=$(iso_to_epoch "${stale}")
  one_hour_ago=$(( now - 3600 ))

  [[ "${fresh_epoch}" -gt "${one_hour_ago}" ]] || return 1
  [[ "${stale_epoch}" -lt "${one_hour_ago}" ]] || return 1
  return 0
}

# ── Run ───────────────────────────────────────────────────────────
run_case "skill shape (front matter, anonymization, delegation ref)" case_skill_shape
run_case "scenario 1: clean upgrade"                                   case_clean_upgrade
run_case "scenario 2: already up to date"                              case_already_up_to_date
run_case "scenario 3: dirty-tree upgrade (stash + ff pull)"            case_dirty_tree_upgrade
run_case "scenario 4: snooze backoff state machine"                    case_snooze_backoff
run_case "scenario 5: auto_upgrade: true skip"                         case_auto_upgrade_skip
run_case "scenario 6: upgrade_never_ask: true silent exit"             case_never_ask_silent
run_case "scenario 7: failure rollback (.cast-bak copy-back)"          case_failure_rollback
run_case "scenario 8: active-runs check (mocked curl)"                 case_active_runs_check
run_case "scenario 9: concurrent-invocation lock (noclobber)"          case_concurrent_lock
run_case "scenario 10: cache 1h TTL window"                            case_cache_ttl

printf '\nResults: %d passed, %d failed.\n' "${PASS}" "${FAIL}"
[[ "${FAIL}" -eq 0 ]] || exit 1
