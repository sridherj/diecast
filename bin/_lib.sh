#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# bin/_lib.sh — shared bash helpers for ./setup and bin/cast-doctor.
#
# Sourced, never executed. Provides:
#   * RUN_TIMESTAMP / CAST_BAK_ROOT — shared backup directory for one run
#   * log / warn / fail              — output helpers
#   * backup_if_exists <abs-path>    — move a path under CAST_BAK_ROOT (no-op if absent)
#   * prune_old_backups              — keep 5 newest .cast-bak-* dirs (Decision #6)
#
# DRY_RUN=1 turns every mutating helper into a logged dry-run.

set -euo pipefail

: "${RUN_TIMESTAMP:=$(date -u +%Y%m%dT%H%M%SZ)}"
: "${CAST_BAK_ROOT:=${HOME}/.claude/.cast-bak-${RUN_TIMESTAMP}}"
: "${DRY_RUN:=0}"

log()  { printf '[cast] %s\n' "$*"; }
warn() { printf '[cast] WARNING: %s\n' "$*" >&2; }
fail() { printf '[cast] ERROR: %s\n' "$*" >&2; exit 1; }

# backup_if_exists <abs-path>
#   Move <abs-path> to CAST_BAK_ROOT preserving the path tail relative to $HOME.
#   No-op when <abs-path> does not exist; honours DRY_RUN.
backup_if_exists() {
  local src="$1"
  [[ -e "$src" || -L "$src" ]] || return 0

  local rel
  if [[ "$src" == "$HOME"/* ]]; then
    rel="${src#"${HOME}"/}"
  else
    rel="${src#/}"
  fi
  local dest="${CAST_BAK_ROOT}/${rel}"

  if [[ "${DRY_RUN}" == "1" ]]; then
    log "DRY: backup ${src} -> ${dest}"
    return 0
  fi

  mkdir -p "$(dirname "$dest")"
  mv "$src" "$dest"
  log "Backed up ${src} -> ${dest}"
}

# prune_old_backups
#   Keep the 5 newest ~/.claude/.cast-bak-* directories (lex sort), rm -rf the rest.
prune_old_backups() {
  local root="${HOME}/.claude"
  [[ -d "$root" ]] || return 0

  local -a all=()
  while IFS= read -r line; do
    all+=("$line")
  done < <(find "$root" -maxdepth 1 -type d -name '.cast-bak-*' 2>/dev/null | sort)

  local count="${#all[@]}"
  (( count > 5 )) || return 0

  local prune_count=$(( count - 5 ))
  local i
  for ((i=0; i<prune_count; i++)); do
    if [[ "${DRY_RUN}" == "1" ]]; then
      log "DRY: prune ${all[i]}"
    else
      rm -rf "${all[i]}"
      log "Pruned old backup ${all[i]}"
    fi
  done
}
