# Agent-Driven Development 101

A short narrative deck for testing the Stage-1 renderer. Content is fake but
shaped like a real `narrative.collab.md`.

## Opening: why agents now

**Outcome:** The audience understands why agent-driven development became a durable workflow shift in 2026.

Agents moved from novelty to infrastructure in under eighteen months. Three
forces drove the change:

- Context windows large enough to hold real codebases
- Tool-use APIs that stopped being brittle
- Reviewers who trust machine output when the machine shows its work

This deck argues the third point is the one still undercounted.

## What changed in the tooling

Tooling catalogued below. Note the move from single-call LLM wrappers to
multi-turn agents with memory.

| Year | Primary Pattern  | Tool Example         |
|------|------------------|----------------------|
| 2023 | Single completion | ChatGPT              |
| 2024 | Chain of tools    | LangChain agents     |
| 2025 | Persistent agents | Claude Code, Cursor  |
| 2026 | Agent teams       | Diecast, Codex swarms |

The shift is quiet but total: the unit of work is now a *run*, not a *call*.

## The review gap

**Outcome:** We frame human review as the bottleneck that the industry hasn't
designed for, and set up the reader to see why dedicated review surfaces matter.

Every team using agents hits the same wall within six weeks: the agents ship
faster than humans can read. The teams that survive invest in review surfaces;
the teams that don't quietly ratchet down autonomy until the agents feel like
autocomplete again.

## Three design principles

These are the principles we'll defend in the rest of the deck:

1. Review surfaces must be **stage-shaped** — narrative, what, how, assembly
2. Edits must be **one-click exportable** without round-tripping through chat
3. Open questions must be **first-class slides**, not free-text sidebars

## Roadmap

What ships in P1 vs. what waits:

- **P1 (now):** edit mode, decision mode, server export
- **P2:** annotate mode for Stage-3 HTML
- **P3:** assembly mode for Stage-4 reveal.js decks
- **P4:** orchestrator round-trip so decisions re-dispatch maker agents

The goal for P1 is to prove the shell. P2-P4 extend it without reshaping it.

## Closing

One sentence to take home: **review is a product, not a form field.** If a team
treats review as a textarea, they've already lost the week.
