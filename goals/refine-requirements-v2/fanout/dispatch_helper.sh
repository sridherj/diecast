#!/usr/bin/env bash
# Fan-out dispatch helper for cast-detailed-plan children.
# Usage: dispatch <phase_key> <goal_phase> <section_file> <deps> <instructions> <expected_artifact> [decisions_path] [prior_plans_csv]
set -u
PARENT_RUN_ID="run_20260611_140426_cf6da5"
GOAL_SLUG="refine-requirements-v2"
FANOUT_DIR="/home/sridherj/workspace/diecast/goals/refine-requirements-v2/fanout"

dispatch() {
  local phase_key="$1" goal_phase="$2" section_file="$3" deps="$4" instructions="$5" expected="$6"
  local decisions_path="${7:-}" prior_plans_csv="${8:-}"

  # Build relevant_artifacts + optional decisions/prior-plan pointers
  local prior_output="First wave — no prior sub-phase decisions yet."
  local decisions_arg='null'
  if [ -n "$decisions_path" ]; then
    prior_output="Prior sub-phase decisions are summarized at $decisions_path. ADOPT their module names, table/column names, function signatures, and the three new agent names unless you have a strong reason to deviate; if you must deviate, document it under a 'Suggested Revisions to Prior Sub-Phases' section."
    decisions_arg="\"$decisions_path\""
  fi
  # prior plan paths as JSON array
  local prior_plans_json='[]'
  if [ -n "$prior_plans_csv" ]; then
    prior_plans_json=$(printf '%s' "$prior_plans_csv" | jq -R 'split(",")')
  fi

  jq -n \
    --arg slug "$GOAL_SLUG" \
    --arg parent "$PARENT_RUN_ID" \
    --arg gp "$goal_phase" \
    --arg instr "$instructions" \
    --arg deps "$deps" \
    --arg prior "$prior_output" \
    --arg expected "$expected" \
    --argjson decisions "$decisions_arg" \
    --argjson prior_plans "$prior_plans_json" \
    --rawfile section "$section_file" \
    '{
      goal_slug: $slug,
      parent_run_id: $parent,
      delegation_context: {
        agent_name: "cast-detailed-plan",
        instructions: $instr,
        context: {
          goal_title: "Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement",
          goal_phase: $gp,
          relevant_artifacts: ["goal.yaml","plan.collab.md","refined_requirements.collab.md","exploration/summary.ai.md"],
          prior_output: $prior,
          subphase_section: $section,
          dependencies: $deps,
          decisions_so_far: $decisions,
          prior_subphase_plans: $prior_plans
        },
        output: {
          output_dir: "docs/plan/",
          expected_artifacts: [$expected]
        }
      }
    }' > "$FANOUT_DIR/${phase_key}_body.json"

  local rid
  rid=$(curl -s -X POST http://localhost:8005/api/agents/cast-detailed-plan/trigger \
    -H "Content-Type: application/json" --data @"$FANOUT_DIR/${phase_key}_body.json" | jq -r '.run_id // empty')
  echo "$rid"
}
