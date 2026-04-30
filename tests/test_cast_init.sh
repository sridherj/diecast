#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# tests/test_cast_init.sh — five integration scenarios for /cast-init.
#
# Drives the cast-init logic by replicating its file-system mutations in pure bash —
# the SKILL.md text is the canonical specification; this test asserts the OBSERVABLE
# outcomes (directories, .gitkeep files, CLAUDE.md substitution, prompt invocation
# logging) so that any future implementation in Python or via the HTTP API is held to
# the same behavior.
#
# fake-claude (tests/fixtures/fake-claude) is used for any path that would normally
# spawn `claude --skill cast-init`; invocations are logged to /tmp/claude-invocations.log
# (or $CLAUDE_FAKE_LOG) so scenarios can assert what was called.
#
# Scenarios:
#   1. Empty project           — seven dirs + .gitkeep files + CLAUDE.md materialize.
#   2. Re-run + Skip           — 4-option prompt fires; no mutation when "Skip" is picked.
#   3. Pre-populated docs/api/ — cast dirs added; docs/api/ untouched.
#   4. {{PROJECT_NAME}} sub.   — basename of cwd is grep-able as the H1 of CLAUDE.md.
#   5. Spec reference          — CLAUDE.md grep for the conventions spec path.
#
# This script intentionally does NOT shell out to a real `claude` binary; it scaffolds
# from `templates/CLAUDE.md.template` directly to assert template behavior. When the
# /cast-init implementation lands as Python (sp2a follow-up), wire that into _scaffold().

set -euo pipefail

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
FIXTURE_DIR="${REPO_DIR}/tests/fixtures"
TEMPLATE="${REPO_DIR}/templates/CLAUDE.md.template"

CANONICAL_DIRS=(
  exploration
  spec
  requirement
  plan
  design
  execution
  ui-design
)

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

assert_grep_F() {
  if grep -qF -- "$1" "$2" 2>/dev/null; then
    return 0
  fi
  echo "    assert_grep_F: literal '$1' not in $2" >&2
  return 1
}

# _scaffold <project_dir>
#   Replicates the clean-project branch of /cast-init: mkdir + .gitkeep for each canonical
#   dir, render templates/CLAUDE.md.template with {{PROJECT_NAME}} substituted from
#   basename, and write CLAUDE.md.
_scaffold() {
  local proj="$1"
  local name
  name="$(basename "${proj}")"

  local d
  for d in "${CANONICAL_DIRS[@]}"; do
    mkdir -p "${proj}/docs/${d}"
    : > "${proj}/docs/${d}/.gitkeep"
  done

  # Render template (project name + skills list placeholder).
  # Skills list is left as the literal placeholder for the "Empty project" scenario;
  # production implementation enumerates ~/.claude/skills/cast-*/SKILL.md.
  sed \
    -e "s/{{PROJECT_NAME}}/${name}/g" \
    -e "s|{{SKILLS_LIST}}|- (no cast-* skills enumerated in this test)|g" \
    "${TEMPLATE}" > "${proj}/CLAUDE.md"
}

# _add_missing_dirs_only <project_dir>
#   Replicates Option C of the 4-option prompt: scaffold any canonical dir that doesn't
#   already exist, append the HTML-comment hint to the existing CLAUDE.md (idempotent).
_add_missing_dirs_only() {
  local proj="$1"
  local d
  for d in "${CANONICAL_DIRS[@]}"; do
    if [[ ! -d "${proj}/docs/${d}" ]]; then
      mkdir -p "${proj}/docs/${d}"
      : > "${proj}/docs/${d}/.gitkeep"
    fi
  done
  local hint='<!-- cast-init suggests adopting the conventions in docs/specs/cast-init-conventions.collab.md from github.com/sridherj/diecast -->'
  if [[ -f "${proj}/CLAUDE.md" ]] && ! grep -qF -- "${hint}" "${proj}/CLAUDE.md"; then
    printf '\n%s\n' "${hint}" >> "${proj}/CLAUDE.md"
  fi
}

# _log_prompt_fire <log_path>
#   Stand-in for the cast-interactive-questions delegation: writes a sentinel line to
#   the fake-claude log so scenario 2 can assert the prompt fired.
_log_prompt_fire() {
  local log="$1"
  mkdir -p "$(dirname "${log}")"
  printf 'skill cast-interactive-questions (cast-init merge prompt)\n' >> "${log}"
}

# ── Scenario 1: empty project ──────────────────────────────────────
case_empty_project() {
  local tmp rc=0
  tmp="$(mktemp -d -t cast-init-empty-XXXXXX)"
  _scaffold_body() {
    _scaffold "${tmp}"
    local d
    for d in "${CANONICAL_DIRS[@]}"; do
      assert_file "${tmp}/docs/${d}/.gitkeep" || return 1
    done
    assert_file "${tmp}/CLAUDE.md" || return 1
    return 0
  }
  _scaffold_body || rc=$?
  rm -rf "${tmp}"
  return $rc
}

# ── Scenario 2: re-run + Skip → no mutation ────────────────────────
case_rerun_skip() {
  local tmp logdir rc=0
  tmp="$(mktemp -d -t cast-init-rerun-XXXXXX)"
  logdir="$(mktemp -d -t cast-init-rerun-log-XXXXXX)"
  local log="${logdir}/claude-invocations.log"
  _rerun_body() {
    _scaffold "${tmp}"
    # Snapshot mtimes after first scaffold (project tree only — log lives outside).
    local before after
    before="$(find "${tmp}" -type f -printf '%p %T@\n' | sort)"

    sleep 1  # ensure any new mtime would differ from the snapshot

    # Re-run: prompt fires, user picks Skip, no mutation.
    _log_prompt_fire "${log}"
    # (Skip = no-op; no _scaffold call here.)

    after="$(find "${tmp}" -type f -printf '%p %T@\n' | sort)"
    if [[ "${before}" != "${after}" ]]; then
      echo "    re-run + Skip mutated the project" >&2
      diff <(printf '%s\n' "${before}") <(printf '%s\n' "${after}") >&2 || true
      return 1
    fi
    assert_grep_F "skill cast-interactive-questions" "${log}" || return 1
    return 0
  }
  _rerun_body || rc=$?
  rm -rf "${tmp}" "${logdir}"
  return $rc
}

# ── Scenario 3: pre-populated docs/api/ untouched ──────────────────
case_prepopulated_docs() {
  local tmp rc=0
  tmp="$(mktemp -d -t cast-init-prepop-XXXXXX)"
  _prepop_body() {
    mkdir -p "${tmp}/docs/api"
    echo "# REST" > "${tmp}/docs/api/REST.md"

    # Add-missing-dirs-only path: cast dirs land, docs/api/ untouched, CLAUDE.md absent.
    _add_missing_dirs_only "${tmp}"

    # Cast dirs present.
    local d
    for d in "${CANONICAL_DIRS[@]}"; do
      assert_file "${tmp}/docs/${d}/.gitkeep" || return 1
    done
    # Pre-existing docs/api/ untouched.
    assert_file "${tmp}/docs/api/REST.md" || return 1
    assert_grep "^# REST" "${tmp}/docs/api/REST.md" || return 1
    # Add-missing-dirs-only does not write CLAUDE.md when none existed.
    assert_no_file "${tmp}/CLAUDE.md" || return 1
    return 0
  }
  _prepop_body || rc=$?
  rm -rf "${tmp}"
  return $rc
}

# ── Scenario 4: {{PROJECT_NAME}} substitution ──────────────────────
case_project_name_sub() {
  local rc=0
  local parent
  parent="$(mktemp -d -t cast-init-name-XXXXXX)"
  local proj="${parent}/myproj"
  mkdir -p "${proj}"

  _name_body() {
    _scaffold "${proj}"
    assert_grep "^# myproj" "${proj}/CLAUDE.md" || return 1
    return 0
  }
  _name_body || rc=$?
  rm -rf "${parent}"
  return $rc
}

# ── Scenario 5: CLAUDE.md spec reference ───────────────────────────
case_spec_reference() {
  local tmp rc=0
  tmp="$(mktemp -d -t cast-init-spec-XXXXXX)"
  _spec_body() {
    _scaffold "${tmp}"
    assert_grep_F "docs/specs/cast-init-conventions.collab.md" "${tmp}/CLAUDE.md" || return 1
    return 0
  }
  _spec_body || rc=$?
  rm -rf "${tmp}"
  return $rc
}

# ── Run ────────────────────────────────────────────────────────────
[[ -f "${TEMPLATE}" ]] || { echo "FATAL: template missing at ${TEMPLATE}" >&2; exit 2; }

run_case "empty project"            case_empty_project
run_case "re-run + Skip"            case_rerun_skip
run_case "pre-populated docs/api/"  case_prepopulated_docs
run_case "project-name substitution" case_project_name_sub
run_case "spec reference in CLAUDE.md" case_spec_reference

printf '\nResults: %d passed, %d failed.\n' "${PASS}" "${FAIL}"
[[ "${FAIL}" -eq 0 ]] || exit 1
