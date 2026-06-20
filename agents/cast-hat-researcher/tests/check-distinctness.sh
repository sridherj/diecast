#!/usr/bin/env bash
# check-distinctness.sh — deterministic, reproducible gate for cast-hat-researcher.
# Decision #6: the two grep-able invariants (SC-002, SC-003) are committed as a runnable
# script with non-zero exit on violation, so Phase 3a/CI inherit a known-good guard.
# Plan Review Decision #4-A: also surfaces cross-agent angle drift (provenance check).
#
# Usage:
#   tests/check-distinctness.sh                  # static checks on the agent source
#   tests/check-distinctness.sh <research_dir>   # ALSO check produced notes in a dir
#
# Exit 0 = all invariants hold. Non-zero = a violation (printed to stderr).

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_MD="$HERE/../cast-hat-researcher.md"
RESEARCH_DIR="${1:-}"
fail=0

red()  { printf '\033[31mFAIL\033[0m %s\n' "$1" >&2; }
ok()   { printf '\033[32mOK\033[0m   %s\n' "$1"; }

# 80/20 signature used by SC-003. Kept in one place so FP and 90-10 checks agree.
EIGHTY_TWENTY_RE='80/20|80-20|80 ?% of (the )?value|20 ?% of (the )?effort|laziest|cheapest path|embarrassing-but-shippable'

# strip_sanctioned: remove the regions where cross-references / 80-20 mentions are
# SPEC-MANDATED rather than leaked — HTML comments (provenance + carve-out notes) and
# the explicit "Distinctness guard" paragraphs (which by design say "do NOT do X; that's
# the OTHER hat's job"). What remains is the generative framing/findings prose, where any
# cross-hat reference or 80/20 mention WOULD be an accidental leak. This is the meaningful
# scope of SC-002/SC-003: priming in the working framing, not the sanctioned guards.
strip_sanctioned() {
  # 1) drop HTML comment lines  2) drop lines from a "Distinctness guard" marker to the
  # next blank line (the guard paragraph).
  sed -e '/<!--/d' "$@" | awk '
    /[Dd]istinctness guard/ {skip=1}
    skip && /^[[:space:]]*$/ {skip=0; next}
    skip {next}
    {print}
  '
}

# ---------------------------------------------------------------------------
# SC-003: First Principles note/block must contain ZERO 80/20 content.
#         The 90-10 block is the ONLY place that content may live.
#         Scope: the generative framing/findings prose (sanctioned guards/comments
#         that PROHIBIT 80/20 here are stripped first — a "do NOT do 80/20" line is
#         the opposite of leakage).
# ---------------------------------------------------------------------------
fp_block="$(awk '/^### Hat: `first-principles`/{f=1} f&&/^### Hat: `90-10`/{f=0} f' "$AGENT_MD" | strip_sanctioned /dev/stdin)"
if printf '%s' "$fp_block" | grep -iqE "$EIGHTY_TWENTY_RE"; then
  red "SC-003: first-principles block contains 80/20 content (must be carved out)."
  printf '%s\n' "$fp_block" | grep -inE "$EIGHTY_TWENTY_RE" >&2
  fail=1
else
  ok "SC-003: first-principles block is free of 80/20 content (outside sanctioned guards)."
fi

# The 90-10 block MUST carry the 80/20 framing (it is the re-homed location).
nineten_block="$(awk '/^### Hat: `90-10`/{f=1} f&&/^## Error handling/{f=0} f' "$AGENT_MD")"
if printf '%s' "$nineten_block" | grep -iqE '90%|10%|laziest'; then
  ok "SC-003: 90-10 block carries the re-homed 90/10 framing."
else
  red "SC-003: 90-10 block is missing the 90/10 framing (carve-out re-home failed)."
  fail=1
fi

# ---------------------------------------------------------------------------
# SC-002: no hat prompt block references another hat's id/framing. The agent
#         body holds all blocks as a library, but no block may name another hat.
#         (We allow the explicit `vs <other-hat>` distinctness guards, which are
#         the SANCTIONED cross-references — they assert separation, not leakage.)
# ---------------------------------------------------------------------------
HATS=(expert-practitioner tool-landscape ai-native community-wisdom framework-methodology contrarian first-principles 90-10)
sc002_fail=0
for hat in "${HATS[@]}"; do
  # Extract the hat block, then strip sanctioned regions (provenance comments + the
  # explicit distinctness-guard paragraphs that legitimately name the other hat).
  block="$(awk -v h="### Hat: \`$hat\`" '
    $0 ~ h {f=1; next}
    f && /^### Hat: `/ {f=0}
    f && /^## Error handling/ {f=0}
    f {print}
  ' "$AGENT_MD" | strip_sanctioned /dev/stdin)"
  for other in "${HATS[@]}"; do
    [ "$other" = "$hat" ] && continue
    leak="$(printf '%s' "$block" | grep -iE '\b'"$other"'\b' )"
    if [ -n "$leak" ]; then
      red "SC-002: hat '$hat' references other hat '$other' outside a sanctioned guard:"
      printf '%s\n' "$leak" >&2
      sc002_fail=1; fail=1
    fi
  done
done
[ "$sc002_fail" -eq 0 ] && ok "SC-002: no unsanctioned cross-hat references in any hat's framing/findings."

# ---------------------------------------------------------------------------
# Provenance / divergence check (Plan Review Decision #4-A): the 7 lifted hats
# must each carry a provenance comment so cross-agent drift is visible, not silent.
# ---------------------------------------------------------------------------
for hat in expert-practitioner tool-landscape ai-native community-wisdom framework-methodology contrarian first-principles; do
  if ! awk -v h="### Hat: \`$hat\`" '$0 ~ h {found=1} found && /provenance: derived from cast-web-researcher/ {print; exit}' "$AGENT_MD" | grep -q .; then
    red "PROVENANCE: hat '$hat' is missing its 'derived from cast-web-researcher Angle N' comment."
    fail=1
  fi
done
[ "$fail" -eq 0 ] && ok "PROVENANCE: all 7 lifted hats carry a divergence-tracking provenance comment."

# ---------------------------------------------------------------------------
# Optional: same invariants over PRODUCED notes in a research dir.
# ---------------------------------------------------------------------------
if [ -n "$RESEARCH_DIR" ]; then
  if [ ! -d "$RESEARCH_DIR" ]; then
    red "research dir not found: $RESEARCH_DIR"; exit 2
  fi
  fp_note="$(ls "$RESEARCH_DIR"/*-first-principles.ai.md 2>/dev/null | head -1)"
  if [ -n "$fp_note" ] && grep -iqE "$EIGHTY_TWENTY_RE" "$fp_note"; then
    red "SC-003 (note): $fp_note contains 80/20 content."
    fail=1
  elif [ -n "$fp_note" ]; then
    ok "SC-003 (note): $(basename "$fp_note") is free of 80/20 content."
  fi
  # Each note's front-matter records exactly one hat: value.
  for note in "$RESEARCH_DIR"/*.ai.md; do
    [ -e "$note" ] || continue
    n="$(awk '/^hat:/{c++} END{print c+0}' "$note")"
    if [ "$n" -ne 1 ]; then
      red "SC-002 (note): $(basename "$note") has $n 'hat:' front-matter lines (expected 1)."
      fail=1
    fi
  done
fi

if [ "$fail" -ne 0 ]; then
  printf '\n\033[31mDISTINCTNESS GATE FAILED\033[0m\n' >&2
  exit 1
fi
printf '\n\033[32mDISTINCTNESS GATE PASSED\033[0m\n'
