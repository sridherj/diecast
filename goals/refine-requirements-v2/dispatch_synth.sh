#!/usr/bin/env bash
# Dispatches 7 playbook synthesizers (fable), one per step.
set -uo pipefail
SERVER="http://localhost:8005"
GOAL_SLUG="refine-requirements-v2"
PARENT_RUN_ID="run_20260611_092825_5fe138"
EXPL_DIR="/home/sridherj/workspace/diecast/.cast/exploration"
TRACK="/home/sridherj/workspace/diecast/.cast/.synth_run_ids"
: > "$TRACK"

# step | slug | has-code-research (1/0)
STEPS=(
"1|learn-from-existing-systems|1"
"2|canonical-source-of-truth|1"
"3|workflow-classification-taxonomy|0"
"4|annotation-and-iteration|1"
"5|html-first-render|1"
"6|phase-agnostic-router|1"
"7|living-source-of-truth-roundtrip|1"
)

for entry in "${STEPS[@]}"; do
  IFS='|' read -r num slug has_code <<< "$entry"
  nn=$(printf "%02d" "$num")
  arts="[\"goals/refine-requirements-v2/refined_requirements.collab.md\",\"exploration/steps.ai.md\",\"exploration/research/${nn}-${slug}.ai.md\""
  code_clause=""
  if [ "$has_code" = "1" ]; then
    arts="${arts},\"exploration/research/${nn}-${slug}-code.ai.md\""
    code_clause=" Also read ${EXPL_DIR}/research/${nn}-${slug}-code.ai.md — this maps the current codebase. This is a GO BROAD strategy: code exploration = where we ARE (the terrain map), web research = where we COULD BE (the full possibility space). Recommend the BEST approach — even if that means a complete rewrite, different architecture, or throwing away the current implementation. The code context helps understand the starting point and migration cost, but the recommendation should be unconstrained."
  fi
  arts="${arts}]"
  instr="Read research from ${EXPL_DIR}/research/${nn}-${slug}.ai.md and synthesize into an opinionated, actionable playbook.${code_clause} Also read exploration/steps.ai.md (your step is Step ${num}) and the refined requirements for intent. Pick ONE tool/approach per component, name exact libraries/versions, make it actionable. Structure: TL;DR, Recommended Stack table, 5-10 Implementation Steps each with Impact/Effort, Architecture diagram (ASCII), Key Decisions table, Pitfalls to Avoid, Success Metrics, and an Impact Rating 1-10 with one-line justification. This is for an OSS product (Diecast) designed for an AI-native future where agents are first-class producers and consumers of requirements. Write the playbook to ${EXPL_DIR}/playbooks/${nn}-${slug}.ai.md."
  payload=$(jq -n --arg gs "$GOAL_SLUG" --arg pr "$PARENT_RUN_ID" --arg instr "$instr" \
    --arg od "$EXPL_DIR" --arg exp "playbooks/${nn}-${slug}.ai.md" --argjson arts "$arts" '{
      goal_slug:$gs, parent_run_id:$pr,
      delegation_context:{
        agent_name:"cast-playbook-synthesizer", instructions:$instr,
        context:{ goal_title:"Refine Requirements v2", goal_phase:"requirements",
          relevant_artifacts:$arts,
          prior_output:"cast-explore pipeline: decomposition done, all 13 research children (7 web + 6 code) completed. You are the synthesis stage for one step.",
          constraints:["Be opinionated - ONE pick per component","OSS product - generalize beyond maintainer workspaces","Agents are first-class producers AND consumers","Go broad - unconstrained by current codebase"] },
        output:{ output_dir:$od, expected_artifacts:[$exp] } } }')
  rid=$(curl -s -X POST "$SERVER/api/agents/cast-playbook-synthesizer/trigger" -H "Content-Type: application/json" -d "$payload" | jq -r '.run_id')
  echo "synth|${nn}|${slug}|${rid}" | tee -a "$TRACK"
done
echo "=== DISPATCHED $(wc -l < "$TRACK") synthesizers ==="
