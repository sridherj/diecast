# LinkedOut-Coupling Spike

> Sub-phase 2.4 spike — observation only. Phase 5 sub-phase 5.1 consumes
> the sibling JSON for structural validation; Phase 5 also plans the
> actual rewrites scored here.
> Locked schema (Issue #13 / D13): `agent_name`, `score`, `estimated_sessions`, `linkedout_isms`.
> Source: `~/workspace/linkedout-oss/.claude/agents/` (the upstream cast-crud family).
> Row count: 15 (one per inclusion-list crud-* agent in US3).

## Methodology

Per crud-* agent listed in US3 (refined-requirements §"cast-crud family"), the spike walks the upstream prompt for:
- LinkedIn / LinkedOut entity names (e.g., `connection`, `profile`, `company`).
- Schema column references (e.g., `li_url`, `li_handle`, `affinity_score`).
- Fixture data references (e.g., `connections.csv`, `gmail-contacts-subset.csv`).
- Hard-coded SJ paths (`/data/workspace/second-brain`, `~/workspace/linkedout`, `/tmp/linkedout-*/`).
- Prose mentions ("LinkedOut", "LinkedIn", "linkedout-setup", `/linkedout-*` slash commands).
- External reference-codebase paths (`./reference_code/...`) which are SJ-local but not LinkedOut-specific (scored yellow).

Score legend (Issue #13 / D13):
- `green` — rewrite trivial (no LinkedOut-isms detected; just rename the file and prefix).
- `yellow` — rewrite non-trivial but bounded (path constants and reference-code anchors to swap, no entity-model rewrites).
- `red` — rewrite is greenfield (heavy LinkedOut wiring; needs new prompt for diecast).

## Per-Agent Findings

| agent_name | score | estimated_sessions | linkedout_isms |
|---|---|---|---|
| `cast-controller` | green | 0.25 | (none — uses generic `project_mgmt/label` and `project_mgmt/priority` examples; no LinkedOut entity references) |
| `cast-controller-test` | green | 0.25 | (none — generic project_mgmt CRUD test patterns only) |
| `cast-crud-compliance-checker` | green | 0.25 | (none — checklist references generic `project_mgmt/label` entities) |
| `cast-crud-orchestrator` | green | 0.5 | (none — prose-clean orchestrator; checks slug naming and dispatch order, no entity assumptions) |
| `cast-custom-controller` | green | 0.25 | (none — `project_mgmt/task` status-transition example only) |
| `cast-entity-creation` | green | 0.25 | (none — `project_mgmt/label` and `project_mgmt/task` entity patterns; FK-to-project example) |
| `cast-integration-test-creator` | yellow | 0.5 | `tests/integration/project_mgmt/label/test_label_controller.py` and `from project_mgmt.enums import TaskStatus` are SJ-codebase anchors — not LinkedOut-specific but still need to be parameterized to the host project |
| `cast-integration-test-orchestrator` | red | 1.5 | `LinkedOut installation` prose, `/linkedout-setup --demo` and `/linkedout --demo` slash commands, `linkedout-sandbox` container name, `tests/e2e/fixtures/linkedin-connections-subset.csv` and `gmail-contacts-subset.csv` fixture paths, `goal_slug: linkedout-opensource`, hard-coded `output_dir: /home/sridherj/workspace/linkedout-oss`, `TmuxHarness("linkedout-test")` literal, `/tmp/linkedout-oss/decisions.jsonl` and `verdict.json` paths, `~/workspace/linkedout/.env.local` API-keys reference, "LinkedIn profiles for Apify enrichment" prose, $0.10 test budget tied to LinkedOut profile cost |
| `cast-repository` | green | 0.25 | (none — `project_mgmt/label` repository pattern only) |
| `cast-repository-test` | green | 0.25 | (none — `project_mgmt/label` repository test pattern only) |
| `cast-schema-creation` | yellow | 0.5 | `./reference_code/src/common/schemas/...` and `./reference_code/src/projects/schemas/...` are SJ-local reference-codebase anchors — not LinkedOut-specific, but still need to be relocated under a diecast-controlled `references/` dir before publish |
| `cast-seed-db-creator` | green | 0.25 | (none — generic seed-data instructions, no LinkedOut entities) |
| `cast-seed-test-db-creator` | green | 0.25 | (none — generic test-fixture seed instructions) |
| `cast-service` | green | 0.25 | (none — `project_mgmt/label` service-layer pattern only) |
| `cast-service-test` | green | 0.25 | (none — `project_mgmt/label` service-layer test pattern only) |

## Roll-up

| Score | Count | Total est. sessions |
|---|---|---|
| green | 12 | 3.25 |
| yellow | 2 | 1.0 |
| red | 1 | 1.5 |
| **All** | **15** | **5.75** |

## Decisions Honored

- Issue #13 / D13 — locked 4-field schema; sibling JSON is the canonical machine shape.
- Phase 5 sub-phase 5.1 verification clause (a.1) — JSON is structurally valid (assert via `python3 -m json.tool` and key-set check).

## Notes

- Row count target was ~14; this spike returned 15 because `cast-custom-controller` and `cast-seed-db-creator` / `cast-seed-test-db-creator` all live alongside the maker chain in `~/workspace/linkedout-oss/.claude/agents/` and were called out by name in the refined-requirements US16 inclusion list. No silent truncation.
- Spike is **observation only**. Phase 5 owns the rewrite per agent; estimates above are upper-bound CC-time budgets.
- The two yellow scores (`cast-integration-test-creator`, `cast-schema-creation`) are not LinkedOut-isms strictly — they are SJ-local reference-codebase paths. Phase 5 may downgrade them to green if it ships a `references/` bundle as part of the cast-crud worked example.
- The single red score (`cast-integration-test-orchestrator`) is the obvious rewrite-from-scratch case: its entire purpose is to drive the LinkedOut Docker installation. Phase 5 should plan to either (a) ship a generic "diecast end-to-end harness" replacement, or (b) defer this agent past v1.
