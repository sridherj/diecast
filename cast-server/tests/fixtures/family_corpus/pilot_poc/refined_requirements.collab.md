---
status: refined
scope_mode: hold
confidence:
  intent: high
  behavior: medium
  constraints: medium
  out_of_scope: high
open_unknowns: 2
questions_asked: 0
classification:
  family: "pilot_poc"
  confidence: 0.9
  alt_family: "new_initiative"
  reasoning: "A time-boxed spike that validates whether an LLM maker render can beat the deterministic v2 page before committing to the full Phase-3 build. It probes a hypothesis and recommends a disposition; it does not ship the feature."
  uncertainty_factors:
    - "Could be read as new_initiative since it precedes a real build, but its deliverable is evidence + a gate recommendation, not shipped code."
  modifiers:
    irreversible: false
    unknown_cause: false
  confirmed_by: "manual"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

<!-- CORPUS-PROVENANCE: family=pilot_poc — authored from the real Phase-1 maker quality-ceiling spike (sp1a, run_20260612_102118_059586, spikes/1a/spike-results.md). -->

# Spike: does an LLM maker render beat the deterministic v2 page?

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** docs/goal/refine-requirements-better-rendering-v3/spikes/1a/spike-results.md

## Intent

**Job statement:** Before committing to a full Phase-3 maker pipeline, prove by hand that an LLM-crafted requirements page can clearly out-communicate the v2 deterministic render for at least two work families — or surface, with evidence, that it cannot.

The open question driving v3 is whether giving up render determinism buys enough reader comprehension to be worth it. This spike answers it the cheapest honest way: a human crafts maker pages for two real classified documents following the cast-preso-how discipline by hand, then audits them against the deterministic baselines for canonical-id coverage, single-file self-containment, and above-the-fold scannability. The spike validates a ceiling — it establishes the bar exists and can be cleared, not that an unaided agent will clear it. It is explicitly time-boxed: two families is the gate bar, and the stretch third family is descoped the moment budget runs thin. The deliverable is a recommended gate disposition plus the audit artifacts, handed to the owner at G1, who makes the binding maker-vs-hybrid call.

## Decisions

- **Recommended disposition: PROCEED to Phase 3.** The quality bar — a maker render that clearly beats the v2 page for two families, carries every canonical id verbatim on the correct block, and stays a self-contained single file — is reachable by hand for both `bug_fix` and `new_initiative`.
- **`bug_fix` is the strong, structural win.** The deterministic baseline silently drops five of seven canonical ids; the maker surfaces all seven in family-appropriate sections. That is a measured comprehension gap, not a taste call.
- **`new_initiative` is the qualified win.** Id coverage is at parity, but the maker keeps the whole WHAT open in under half the bytes where the baseline collapses depth behind thirteen `<details>` — a hierarchy and scannability win that needs the human-eyeball confirmation.
- **One anomaly recorded as Phase-4a input, not acted on here:** the v2 SC-001 checker is necessary-but-not-sufficient — it passes the deterministic baseline too, so it cannot be the quality gate for a varying render.

## Open Questions

- **[DEFERRED]** Family breadth across all nine families is not proven by a two-family ceiling spike — it is re-validated agent-generated in Phase 5 (SC-002), out of scope here.
- **[DEFERRED]** Whether the eventual Phase-3 agent clears the bar unaided; the spike only proves the bar is reachable by hand, and Phase 3 re-proves it agent-generated reusing the spike's id-audit pattern.
