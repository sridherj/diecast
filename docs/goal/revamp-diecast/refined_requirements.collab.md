---
status: refined
scope_mode: hold
confidence:
  intent: medium
open_unknowns: 3
questions_asked: 1
classification:
  family: "random_idea"
  confidence: 0.65
  alt_family: "new_initiative"
  reasoning: "Revamp DieCast / launch v2 is a large multi-direction product initiative, but the owner chose to keep it as a captured brainstorm to prioritize before scoping."
  uncertainty_factors:
    - "writeup is a vague prioritization brainstorm, not a scoped feature"
    - "strong exploration/catch-up flavor up front"
  modifiers:
    irreversible: false
    unknown_cause: false
  confirmed_by: "user"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

# Revamp DieCast — v2 Direction

> **Spec maturity:** notes (random_idea floor — captured, not yet scoped)
> **Version:** 0.1.0

## Intent

**Job statement:** Take stock of what the AI-coding industry now ships, decide what DieCast should absorb, lock down who it is for, and turn a pile of candidate directions into a prioritized v2 I can hand to engineers and PMs at a few companies.

A few months after v1, a lot of what I hand-rolled now ships in the platform itself — Claude /goals, /workflow, and far stronger sub-agents — alongside a wave of memory and self-learning tooling (gstack, gbrain, hermes). Before building more, I want to take stock, then sequence the work.

Primary user for v2: fairly solid engineers — competent ICs, not necessarily leaders — and PMs at a typical office, not an AI-native shop. They can code and reason, but they do not build their own AI harness and won't; DieCast is the harness and the opinions so they don't have to. Engineers who build (or want to build) their own harness are an explicit non-target. That one choice turns three things into blockers rather than nice-to-haves: near-zero setup friction, a legible UI, and an onboarding on-ramp.

Directions on the table, not yet prioritized:

1. Catch up and integrate — survey what Claude and the memory and self-learning tools now ship, then decide what DieCast should absorb and what it should drop. This is the stated first move.
2. Workflow orchestration — lean on Claude workflows and goals, rethink the tmux-spawning model, and consider a conductor-style UI (build it, or pull from open source).
3. Sharpen ICP and adoption — make DieCast land for a solid engineer and a PM at a typical office, and get a few companies actually using it.
4. Lower setup friction — support Claude, Codex, and maybe Copilot across Linux, Mac, and Windows with minimal breakage.
5. Make DieCast legible — improve the UI and the framing so a newcomer understands what it is.
6. Docs as product — render requirements and reports as commentable standalone HTML, a Google-Docs equivalent; the cast-preso tooling already gestures at this.
7. Workflow streams — give each kind of dev work its own stream: bug fix, data analysis, debug, small pilot, big initiative, PRD, add tests, POC. Parts already exist in the family taxonomy and the vision prototype.
8. Prototype as a phase — make prototyping a first-class step in the flow.
9. Skillify — a meta-skill that turns one of my manual workflows into sub-agents, complete with maker, tests, and checker.
10. Onboarding video — a short how-to, ideally made unnecessary by the product being obvious.

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-12 | Capture as notes (random_idea) | Full spec depth (new_initiative); pilot_poc | Keep exploring and prioritize before committing to a scoped v2 spec; structure is offered when ready. |
| 2026-06-12 | ICP: solid engineers and PMs at a typical office | AI-native harness-builders (explicit non-target); a design-partner-only start | Land v2 for capable but non-harness-building teams, which makes setup, legibility, and onboarding first-class. |

## Open Questions

- **[NEEDS CLARIFICATION: product-vs-deck messaging]** — the GTM deck targets AI-native harness-builders, but the product target is the opposite. Decide whether to re-aim the deck, run two messages, or treat the deck as aspirational. Resolve before GTM work builds on this spec.
- **[NEEDS CLARIFICATION: catch-up scope]** — "catch up on the industry" has no boundary yet. Decide whether the output is a written survey, a timeboxed spike, or just input to the next planning pass.
- **[NEEDS CLARIFICATION: v2 success signal]** — nothing yet says whether v2 worked. Pick a signal, such as a number of companies using it weekly, or a new engineer onboarding in under thirty minutes without me.

---

*This is a captured brainstorm (random_idea floor). Full structure — user stories, functional requirements, success criteria, and a scoped out-of-scope — is available whenever you want to promote a direction into a scoped initiative.*
