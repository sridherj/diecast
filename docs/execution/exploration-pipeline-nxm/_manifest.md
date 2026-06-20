# Execution Manifest: Exploration Pipeline — N×M Workflow + 90/10 Hat + Diecast HTML Surface

## How to Execute

Each sub-phase runs in a **separate Claude context**. Read `_shared_context.md`, then execute the
sub-phase's `plan.md` (which points at the authoritative detailed plan). Update the Status column after each.

## Sub-Phase Overview

| # | Sub-phase | Directory/File | Depends On | Status | Notes |
|---|-----------|----------------|-----------|--------|-------|
| 1a | Spike: Workflow as exploration engine | `sp1a_spike_workflow/` | -- | Done | Autonomous. Gates 3a. Must prove handoff/terminal-signal semantics (review #1). |
| 1b | Spike: dual viewer + in-frame commenting | `sp1b_spike_viewer/` | -- | Done | **Browser-gated — needs human validation.** Gates 2b/3b. |
| G1 | GATE: resolve spike decisions | -- | 1a, 1b | Done | Human: record 1a VIABLE+mechanism+handoff; 1b srcdoc/bridge vs full-page fallback. Unblocks 2b/3a/3b. |
| 2a | Single-hat researcher + 8 hats | `sp2a_hat_agent/` | -- | Done | `cast-hat-researcher`. Dedup Web Fetching Protocol (review #4). |
| 2b | Dual md/html artifact viewer | `sp2b_dual_viewer/` | G1 | Done | iframe/srcdoc; `/cast-update-spec` on cast-requirements-render; adversarial srcdoc test (review #6). |
| 3a | N×M Workflow engine + gating + entrypoint | `sp3a_workflow_engine/` | G1, 2a | Done | Cost-at-gate (#8); barrier glob ∩ hat_id (#9); all-fail test (#7). |
| 3b | Diecast-wide HTML commenting | `sp3b_html_commenting/` | G1, 2b | Done | iframe registry + targetOrigin (#3); jsdom bridge test (#5). |
| 4 | Exploration WHAT/HOW HTML render | `sp4_exploration_render/` | 3a, 2b, 3b | Done | render_common shared core (#2A); degraded-step test (#7). |
| 5 | End-to-end integration & parity | `sp5_e2e_parity/` | 4 | Done | SC-001..009 matrix + parity-notes vs cast-explore. |

Status: Not Started → In Progress → Done → Verified → Skipped

## Dependency Graph

```
   sp1a (spike: engine)   sp1b (spike: viewer — BROWSER)     sp2a (hat agent, dep-free)
        \                      /                                   |
         └──────► G1 (gate) ◄──┘                                   |
                  /     \                                          |
              sp2b       └───────────────┐                         |
            (viewer)                     |                         |
               |                         ▼                         ▼
               ├──────────────────────► sp3b (commenting)   sp3a (engine) ◄── needs G1 + sp2a
               |                         |                         |
               └─────────────► sp4 (exploration render) ◄─────────┘  (also needs sp2b)
                                         |
                                       sp5 (e2e + parity)
```

## Execution Order

### Group 1 — Spikes (parallel)
1a (autonomous) · 1b (browser-gated, human validation)

### G1 — Decision Gate (human)
Resolve 1a + 1b decision gates; record verdicts; update statuses. Blocks Group 2+.

### Group 2 — Foundations (parallel, after G1; 2a has no spike dep but sequenced here)
2a · 2b

### Group 3 — Engine + commenting (parallel)
3a (needs 2a + G1) · 3b (needs 2b + G1)

### Group 4
4 (needs 3a, 2b, 3b)

### Group 5
5 (needs 4)
