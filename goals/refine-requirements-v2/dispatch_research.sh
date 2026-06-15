#!/usr/bin/env bash
# Dispatches web researchers (all 7 steps) + code explorers (steps 1,2,4,5,6,7).
set -uo pipefail
SERVER="http://localhost:8005"
GOAL_SLUG="refine-requirements-v2"
PARENT_RUN_ID="run_20260611_092825_5fe138"
EXPL_DIR="/home/sridherj/workspace/diecast/.cast/exploration"
GOALS_ARTIFACTS=(
  "goals/refine-requirements-v2/refined_requirements.collab.md"
  "goals/refine-requirements-v2/requirements.human.md"
  "goals/refine-requirements-v2/exploration/steps.ai.md"
)
CODEBASE_DIR="/home/sridherj/workspace/diecast"
TRACK="/home/sridherj/workspace/diecast/.cast/.research_run_ids"
: > "$TRACK"

# step number | slug | one-line problem | code-explore? (1/0)
STEPS=(
"1|learn-from-existing-systems|Learn from existing systems + the maintainer's own corpus before designing: Diecast's own DB-canonical+generated-renders pattern for goals/tasks, gbrain (~/workspace/second-brain) requirements handling (keep/drop), cast-preso* visual-hierarchy/progressive-disclosure patterns, the maintainer's real writeup corpus across second-brain/linkedout-oss/diecast bucketed by apparent workflow family, and external prior art (PRD/RFC/ADR/spike templates, GitHub spec-kit, Linear/Notion/Jira doc+comment+version models, Jupyter/Observable notebooks for research-type work).|1"
"2|canonical-source-of-truth|PRIMARY architecture decision: should requirements be DB entities with auto-generated HTML+markdown renders (mirroring Diecast's goal/task pattern) OR files-canonical with a thin DB layer only for comments/versions? Include the stable-ID scheme for every US/FR/SC element (must survive edits + re-renders to anchor comments and diffs - FR-008) and the archive mechanism for superseded versions (DB rows vs archive folder, comments+resolution must travel with archived versions - US5). Must preserve the downstream spec-kit markdown contract (FR-007).|1"
"3|workflow-classification-taxonomy|Validate the owner's 5 priority families (new initiative/PRD, small pilot/POC, bug fix/debug, data analysis/research, random ideas/exploration) against how other teams/OSS communities classify work (PRD vs RFC vs ADR vs spike vs notebook; Shape-Up; risk/reversibility/producer-vs-consumer axes). Design per-family DOCUMENT templates + a classifier that surfaces a family pill and confirms on ambiguity (FR-004), with an explicit guard against the Template-Enforcer anti-pattern (keep the 'random ideas' family loose). Generalize beyond the maintainer (OSS product, FR-012).|0"
"4|annotation-and-iteration|Inline comment/annotation UX (Google-Docs-style, anchored to stable requirement-element IDs), open/resolved lifecycle + retained resolution trail, version progression (unresolved comments drive v2/v3), and per-version change summaries (diff of stable-ID elements - FR-017). CRITICAL: kill-or-confirm with evidence whether this requires migrating the FastAPI+Jinja server-rendered stack to React/Next.js, OR whether standard JS annotation libraries / element-anchored comments on stable IDs suffice on the existing stack. Design so an AGENT can comment/resolve/version through the SAME API as a human (FR-013). Single-writer/async, no realtime co-editing.|1"
"5|html-first-render|HTML-first human-consumption render that lets an unfamiliar reader state a goal's WHAT (job/outcome/scope) in ~2 minutes (SC-001): information architecture, progressive disclosure (summary first, details expandable), L1/L2/L3 visual hierarchy with distinct color/size/design per level, WHAT-before-HOW ordering with HOW confined to a marked non-binding 'Directional' section (omitted when irrelevant), the classification pill, illustrations, and per-family structural variation. Mine cast-preso* patterns. Must keep emitting spec-kit markdown for downstream agents (FR-007).|1"
"6|phase-agnostic-router|Phase-agnostic workflow router: given a goal's classification, resolve a family-specific downstream-workflow handle (bug -> logs/RCA/confirm/fix-test; prototype -> spike/demo/learnings), record the routing decision on the goal (FR-014), and make it invokable from ANY phase without re-running refinement (FR-016). Decide the seam: does classify+route live inside cast-refine-requirements or get extracted as a standalone agent/service? v2 ships the seam + named pipeline STUBS, not real pipelines (FR-015). Unimplemented families route to a named stub, never a silent generic fallback. Agent-as-caller parity (FR-013).|1"
"7|living-source-of-truth-roundtrip|Round-trip mechanism so downstream phases (exploration/planning/execution) write requirement-affecting changes BACK into the requirements artifact: write-back path (additions/annotations, not silent rewrites - FR-018), provenance capture (which phase/agent originated it, surfaced in the version change summary - FR-020), user notification (what changed + from where - FR-019), and conflict detection/surfacing (contradicting changes raised to the user, never silently overwritten - US7 Scenario 4). Downstream agents are the typical write-back source (FR-013). Research notification/event patterns + provenance/audit-trail designs.|1"
)

artifacts_json=$(printf '%s\n' "${GOALS_ARTIFACTS[@]}" | jq -R . | jq -s .)

dispatch () { # $1=agent $2=instructions $3=expected_artifact
  local agent="$1" instr="$2" expected="$3"
  local payload
  payload=$(jq -n --arg gs "$GOAL_SLUG" --arg pr "$PARENT_RUN_ID" --arg ag "$agent" \
    --arg instr "$instr" --arg od "$EXPL_DIR" --arg exp "$expected" \
    --argjson arts "$artifacts_json" '{
      goal_slug:$gs, parent_run_id:$pr,
      delegation_context:{
        agent_name:$ag, instructions:$instr,
        context:{ goal_title:"Refine Requirements v2", goal_phase:"requirements",
          relevant_artifacts:$arts,
          prior_output:"cast-explore starter exploration. Decomposition done (steps.ai.md). Go BROAD: do not over-constrain to the current codebase - best answer may imply a rewrite/different architecture.",
          constraints:["OSS product - generalize beyond maintainer workspaces","Design for AI-native future: agents are first-class producers AND consumers","Go broad - current code is the starting point, not a constraint"] },
        output:{ output_dir:$od, expected_artifacts:[$exp] } } }')
  curl -s -X POST "$SERVER/api/agents/$agent/trigger" -H "Content-Type: application/json" -d "$payload" | jq -r '.run_id'
}

for entry in "${STEPS[@]}"; do
  IFS='|' read -r num slug problem code <<< "$entry"
  nn=$(printf "%02d" "$num")
  # --- Web researcher (all steps) ---
  winstr="Research this exploration step from your 7 expert angles (Expert Practitioner, Tools & Technologies, AI/ML Approaches, Community & Open Source, Frameworks & Patterns, Contrarian View, First Principles). First read exploration/steps.ai.md (your step is Step ${num}) and refined_requirements.collab.md for full intent. STEP ${num} PROBLEM: ${problem} Produce a thorough, citation-backed research note that an opinionated playbook can be synthesized from. Write markdown to exploration/research/${nn}-${slug}.ai.md."
  wrid=$(dispatch "cast-web-researcher" "$winstr" "research/${nn}-${slug}.ai.md")
  echo "web|${nn}|${slug}|${wrid}" | tee -a "$TRACK"
  # --- Code explorer (code-relevant steps only) ---
  if [ "$code" = "1" ]; then
    cinstr="Explore the codebase at ${CODEBASE_DIR} to map the CURRENT terrain relevant to this step (what exists, how it's built, what's missing). Read exploration/steps.ai.md (Step ${num}) for context. STEP ${num} FOCUS: ${problem} This is a GO-BROAD exploration: map where we ARE so the synthesizer understands the starting point and migration cost - but do NOT constrain recommendations to the current code. codebase_dir=${CODEBASE_DIR}. Write markdown to exploration/research/${nn}-${slug}-code.ai.md."
    crid=$(dispatch "cast-code-explorer" "$cinstr" "research/${nn}-${slug}-code.ai.md")
    echo "code|${nn}|${slug}|${crid}" | tee -a "$TRACK"
  fi
done

echo "=== DISPATCHED ==="
wc -l < "$TRACK" | xargs echo "total children:"
