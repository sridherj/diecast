#!/usr/bin/env bash
# check-failure-path.sh — failure-path fixture for cast-hat-researcher (Decision #6).
#
# The failure path is load-bearing for FR-016 / US12: when a cell fails, Phase 3a must be
# able to drop it to `null`. The agent's contract (cast-hat-researcher.md §"Output contract")
# requires: on terminal failure → (a) NO note file is written, and (b) a contract-v2 output
# JSON with `status: "failed"` IS written.
#
# This fixture does NOT invoke the LLM agent. It (1) pins the EXACT contract the agent body
# specifies as a machine-checkable spec, and (2) asserts that spec's two invariants against a
# simulated failed-cell output dir built from that contract. If a future edit to the agent
# changes the failure contract, this test's expectations (and the agent body) must change
# together — that coupling is the point.
#
# Exit 0 = failure contract holds. Non-zero = violation.

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_MD="$HERE/../cast-hat-researcher.md"
fail=0
red() { printf '\033[31mFAIL\033[0m %s\n' "$1" >&2; }
ok()  { printf '\033[32mOK\033[0m   %s\n' "$1"; }

# --- 1. The agent body must SPECIFY the failure contract (no note + failed JSON). ---
if grep -q 'write NO note file' "$AGENT_MD" \
   && grep -q 'status: "failed"' "$AGENT_MD" \
   && grep -q 'NO note file on disk' "$AGENT_MD"; then
  ok "agent body specifies the failure contract (no note file + status:\"failed\")."
else
  red "agent body no longer specifies the failure contract verbatim."
  fail=1
fi

# --- 2. Simulate a failed cell built to the contract; assert the two invariants. ---
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
goal_dir="$tmp/goals/sample-goal"
research_dir="$goal_dir/exploration/research"
mkdir -p "$research_dir"
run_id="testrun-fail-90-10"

# Build EXACTLY what the contract says a failed 90-10 cell emits: no note file,
# and a contract-v2 envelope with status:"failed".
cat > "$goal_dir/.agent-run_${run_id}.output.json" <<'JSON'
{
  "contract_version": "2",
  "agent_name": "cast-hat-researcher",
  "task_title": "90-10 · step 03 learn-from-past-bugs",
  "status": "failed",
  "summary": "All candidate sources for the 90-10 cut evidence were unreachable; no usable content gathered.",
  "artifacts": [],
  "errors": ["all sources unreachable after resilient-browser fallback; no usable content"],
  "next_steps": [],
  "human_action_needed": false,
  "human_action_items": [],
  "started_at": "2026-06-20T10:00:00Z",
  "completed_at": "2026-06-20T10:03:00Z"
}
JSON

# Invariant (a): NO note file written.
if ls "$research_dir"/*.ai.md >/dev/null 2>&1; then
  red "(a) a note file exists in research/ on the failure path (must be absent)."
  fail=1
else
  ok "(a) no note file written on the failure path."
fi

# Invariant (b): contract-v2 JSON with status:\"failed\" IS written, and parses.
out_json="$goal_dir/.agent-run_${run_id}.output.json"
if [ ! -f "$out_json" ]; then
  red "(b) contract-v2 output JSON not written on the failure path."
  fail=1
else
  status="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["status"])' "$out_json" 2>/dev/null)"
  cv="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["contract_version"])' "$out_json" 2>/dev/null)"
  errs="$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["errors"]))' "$out_json" 2>/dev/null)"
  arts="$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["artifacts"]))' "$out_json" 2>/dev/null)"
  if [ "$status" = "failed" ] && [ "$cv" = "2" ] && [ "$errs" -ge 1 ] && [ "$arts" -eq 0 ]; then
    ok "(b) contract-v2 status=failed, errors[] non-empty, artifacts[] empty."
  else
    red "(b) failed envelope malformed: status=$status contract_version=$cv errors=$errs artifacts=$arts"
    fail=1
  fi
fi

if [ "$fail" -ne 0 ]; then
  printf '\n\033[31mFAILURE-PATH GATE FAILED\033[0m\n' >&2
  exit 1
fi
printf '\n\033[32mFAILURE-PATH GATE PASSED\033[0m\n'
