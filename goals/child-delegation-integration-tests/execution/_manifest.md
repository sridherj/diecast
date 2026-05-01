# Execution Manifest: Child Delegation Integration Tests

## How to Execute

Each sub-phase runs in a **separate Claude context**. For each sub-phase:

1. Start a new Claude session
2. Tell Claude: "Read `goals/child-delegation-integration-tests/execution/_shared_context.md`,
   then execute `goals/child-delegation-integration-tests/execution/<spX_Y_dir>/plan.md`"
3. After completion, update the Status column below
4. At gates (G prefix), STOP and surface the gate prompt to the human user

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|------------|--------|-------|
| sp1.1 | Verify `CAST_TEST_AGENTS_DIR` seam | `sp1_1_verify_seam/` | -- | Not Started | Read-only audit; output = 5-line note |
| sp1.2 | Author 4 fixture configs + literal prompts | `sp1_2_fixture_configs/` | -- | Not Started | Parallel with sp1.1, sp1.4 |
| sp1.3 | Conftest wiring (`CAST_TEST_AGENTS_DIR` + cache clear) | `sp1_3_conftest_wiring/` | sp1.1, sp1.2 | Not Started | |
| sp1.4 | Equivalence-map docstring stub | `sp1_4_equivalence_stub/` | -- | Not Started | Parallel-safe (creates new file) |
| **GA** | **Gate A: confirm fixture path + dispatch_modes + seam** | `gate_A_fixture_decisions.md` | sp1.1-sp1.4 | Not Started | **HUMAN DECISION** |
| sp2.1 | Allowlist + Depth + ChildLaunch + TerminalTitle classes + suite timeout | `sp2_1_allowlist_depth/` | GA | Not Started | |
| sp2.2 | DelegationContextFile + ResultSummary + FinalizeCleanup (BOTH finalizers) | `sp2_2_context_summary_cleanup/` | sp2.1 | Not Started | |
| sp2.3 | Preamble builders + DispatchModeValidator | `sp2_3_preamble_builders/` | sp2.1 | Not Started | Parallel with sp2.2, sp2.4 |
| sp2.4 | ContinueAgentRun (security-relevant tmux assertion) | `sp2_4_continuation_file/` | sp2.1 | Not Started | Parallel with sp2.2, sp2.3 |
| sp2.5 | Wall-clock budget gate + equivalence-map completion | `sp2_5_budget_gate/` | sp2.1-sp2.4 | Not Started | |
| **GB** | **Gate B: failing-test enumeration** | `gate_B_failing_tests.md` | sp2.5 | Not Started | **HUMAN DECISION** — anchors sp4 |
| sp3.1 | ExternalProjectDirPrecondition (additive only) | `sp3_1_external_project_dir/` | sp2.5 | Not Started | DRY check vs `test_dispatch_precondition.py` |
| sp3.2 | OutputJsonContractV2 + schema fixture | `sp3_2_output_json_v2/` | sp2.5 | Not Started | Parallel with sp3.1, sp3.3 |
| sp3.3 | MtimeHeartbeatRoundTrip (EXPECTED red until sp4a) | `sp3_3_mtime_heartbeat/` | sp2.5 | Not Started | NO xfail marker |
| sp4a | Parent stall after child finalize | `sp4a_parent_stall/` | Phase 3 + GB | Not Started | Detail deferred until GB |
| sp4b | Cleanup or contract drift | `sp4b_cleanup_contract_drift/` | Phase 3 + GB | Not Started | Detail deferred until GB |
| sp4c | Allowlist/depth/output-JSON silent violations | `sp4c_silent_violations/` | Phase 3 + GB | Not Started | Detail deferred until GB |
| sp5.1 | E2E happy path skeleton + session-scoped server fixture | `sp5_1_e2e_happy_path/` | Phase 4 | Not Started | |
| sp5.2 | E2E delegation_denied | `sp5_2_e2e_denied/` | sp5.1 | Not Started | Parallel with sp5.3, sp6.x |
| sp5.3 | E2E mid_flight_session_isolation | `sp5_3_e2e_session_isolation/` | sp5.1 | Not Started | Parallel with sp5.2, sp6.x |
| **GC** | **Gate C: T2 ptyxis CI strategy** | `gate_C_ptyxis_ci.md` | sp5.1-sp5.3 | Not Started | **HUMAN DECISION** |
| sp5.4 | Nightly CI workflow YAML | `sp5_4_ci_workflow/` | GC | Not Started | Detail deferred until GC |
| sp6.1 | TestSubagentOnlyPreamble | `sp6_1_subagent_preamble/` | Phase 4 | Not Started | Parallel with Phase 5 |
| sp6.2 | MANUAL_SUBAGENT_CHECKLIST.md | `sp6_2_manual_checklist/` | -- | Not Started | Independent of code path |
| sp7.1 | CI observation (≥3 consecutive green nights) | `sp7_1_ci_observation/` | sp5.4 + ≥3 nights | Not Started | Elapsed-time wait |
| sp7.2 | Equivalence-map review + checklist verified-by footer | `sp7_2_equivalence_review/` | Phase 4, 6 | Not Started | Parallel with sp7.1, sp7.3 |
| sp7.3 | Conditional spec update via `/cast-update-spec` | `sp7_3_spec_update/` | Phase 4 retro | Not Started | Conditional; may be no-op |
| sp7.4 | Flip goal status via `/cast-goals` | `sp7_4_close_goal/` | sp7.1, 7.2, 7.3 | Not Started | Final close-out |

Status transitions: `Not Started` → `In Progress` → `Done` → `Verified` → `Skipped`.
Gate rows (GA / GB / GC) pause the orchestrator for human decisions.

## Dependency Graph

```
sp1.1 ─┐
sp1.2 ─┼─► sp1.3 ─► [GATE A]
sp1.4 ─┘                │
                        ▼
                sp2.1 ─► sp2.2 ─┐
                        sp2.3 ─┼─► sp2.5 ─► [GATE B]
                        sp2.4 ─┘                │
                                                ▼
                                    sp3.1 ─┐
                                    sp3.2 ─┼─► (Phase 3 done) ─► sp4a/4b/4c (parallel)
                                    sp3.3 ─┘                              │
                                                                          ▼
                                            sp5.1 ─► sp5.2 ─┐
                                                    sp5.3 ─┴─► [GATE C] ─► sp5.4 ─┐
                                                                                   │
                                            sp6.1 (parallel with Phase 5)          │
                                            sp6.2 (independent)                    │
                                                                                   ▼
                                                            sp7.1 ─┐
                                                            sp7.2 ─┼─► sp7.4 (close-out)
                                                            sp7.3 ─┘
```

**Critical path:** sp1.1 → sp1.3 → GA → sp2.1 → sp2.5 → GB → sp3.x → sp4.x → sp5.1 → GC → sp5.4 → sp7.1 → sp7.4

## Execution Order

### Phase 1 — Fixture scaffolding (parallel-friendly)

Group 1a (parallel): sp1.1, sp1.2, sp1.4
Group 1b (after 1a): sp1.3
**[GATE A]** — surface fixture path + dispatch_modes + seam choice to user

### Phase 2 — T1 coverage parity (mostly serial)

Group 2a: sp2.1
Group 2b (after 2a, parallel): sp2.2, sp2.3, sp2.4
Group 2c (after 2b): sp2.5
**[GATE B]** — surface failing-test enumeration to user (anchors Phase 4 buckets)

### Phase 3 — T1 diecast-only additions (parallel)

Group 3 (after GB, parallel): sp3.1, sp3.2, sp3.3

### Phase 4 — Red→green fix sweep (parallel by symptom bucket)

Group 4 (after Phase 3 + GB, parallel): sp4a, sp4b, sp4c
**Each sub-phase commits ≥1 `fix(delegation): green <test_name>`.**

### Phase 5 — T2 live HTTP E2E

Group 5a (after Phase 4): sp5.1
Group 5b (after 5a, parallel): sp5.2, sp5.3
**[GATE C]** — surface ptyxis CI strategy to user
Group 5c (after GC): sp5.4

### Phase 6 — Subagent coverage (parallel with Phase 5)

Group 6 (parallel with Phase 5): sp6.1, sp6.2

### Phase 7 — Close-out

Group 7a (parallel after Phase 5+6): sp7.1, sp7.2, sp7.3
Group 7b (after 7a): sp7.4

## Progress Log

<!-- Update this after each sub-phase completion. Include date, sub-phase ID, and one-line outcome. -->
