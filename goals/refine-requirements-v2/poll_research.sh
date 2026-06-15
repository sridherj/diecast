#!/usr/bin/env bash
# Waits for all dispatched research children to land their output.json.
set -uo pipefail
CAST_DIR="/home/sridherj/workspace/diecast/.cast"
GOALS_DIR="/data/workspace/diecast/goals/refine-requirements-v2"
TRACK="$CAST_DIR/.research_run_ids"
DONE="$CAST_DIR/.research_done"
TIMEOUT=2700; ELAPSED=0
: > "$DONE"

mapfile -t LINES < "$TRACK"

out_path () { # $1=run_id -> echoes path if found
  if [ -f "$CAST_DIR/.agent-$1.output.json" ]; then echo "$CAST_DIR/.agent-$1.output.json"; return; fi
  if [ -f "$GOALS_DIR/.agent-$1.output.json" ]; then echo "$GOALS_DIR/.agent-$1.output.json"; return; fi
}

while [ $ELAPSED -lt $TIMEOUT ]; do
  pending=0; done_n=0; failed_n=0
  for line in "${LINES[@]}"; do
    rid="${line##*|}"
    p="$(out_path "$rid")"
    if [ -n "$p" ]; then
      st=$(jq -r '.status // "?"' "$p" 2>/dev/null)
      [ "$st" = "failed" ] && failed_n=$((failed_n+1)) || done_n=$((done_n+1))
    else
      pending=$((pending+1))
    fi
  done
  if [ $((ELAPSED % 60)) -eq 0 ]; then
    echo "[$((ELAPSED/60))m] done=$done_n failed=$failed_n pending=$pending / ${#LINES[@]}"
  fi
  if [ $pending -eq 0 ]; then echo "ALL_TERMINAL done=$done_n failed=$failed_n" | tee "$DONE"; break; fi
  sleep 15; ELAPSED=$((ELAPSED+15))
done

if [ $ELAPSED -ge $TIMEOUT ]; then echo "TIMEOUT pending=$pending" | tee "$DONE"; fi

# Final ledger
echo "=== RESEARCH LEDGER ===" | tee -a "$DONE"
for line in "${LINES[@]}"; do
  rid="${line##*|}"; tag="${line%%|*}"; slug=$(echo "$line" | cut -d'|' -f2,3)
  p="$(out_path "$rid")"
  if [ -n "$p" ]; then st=$(jq -r '.status // "?"' "$p" 2>/dev/null); else st="MISSING"; fi
  echo "${tag} ${slug} ${rid} -> ${st}" | tee -a "$DONE"
done
