---
status: refined
scope_mode: hold
confidence:
  intent: medium
  behavior: low
  constraints: low
  out_of_scope: low
open_unknowns: 0
questions_asked: 0
classification:
  family: "random_idea"
  confidence: 0.6
  alt_family: "new_initiative"
  reasoning: "A single jotted thought captured before any refinement — one paragraph of musing, no decisions, no scope, no acceptance. It is the structural floor: a problem worth remembering, nothing committed."
  uncertainty_factors:
    - "Could grow into a new_initiative later, but as captured it is just an idea with no shape."
  modifiers:
    irreversible: false
    unknown_cause: false
  confirmed_by: "manual"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

<!-- CORPUS-PROVENANCE: family=random_idea — authored from a real one-paragraph idea captured during v3 dogfooding (a glanceable health ribbon for the goals list). It is deliberately thin: the floor, honest about its thinness, never padded. -->

# Idea: a glanceable health ribbon for the goals list

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** (none yet — captured idea)

## Intent

**Job statement:** Jot down, before it evaporates, the idea that the goals list could carry a single glanceable health ribbon per goal — one strip of color and a couple of tokens that say, without a click, whether that goal's last render is fresh, flagged for human review, or stale.

This is just a thought, not a plan. While watching the goals list during dogfooding it kept feeling like the page makes me click into each goal to learn anything about its state — is the render current, did the last maker run get flagged, is a child still working. A goal is a living thing with a handful of states that already exist in the data: the render freshness, the `human_review` flag, whether a dispatch is in flight. None of that is surfaced where the eye already is. A thin ribbon — think of the colored left-border-plus-label pattern, not a dashboard — might let someone scan twenty goals and know which two need attention. I have not thought about what the exact states are, where the data comes from, whether it updates live or on load, or whether it is even worth the visual weight. It might be noise. It might be the single most useful thing on the page. Capturing it here so the idea survives long enough to find out; everything past this sentence is genuinely unknown and deliberately left blank rather than invented.
