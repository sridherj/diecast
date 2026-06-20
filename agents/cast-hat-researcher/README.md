# cast-hat-researcher

The **lean single-hat researcher** — the atomic research unit of the N×M exploration
pipeline. Param'd by ONE `hat_id`, takes ONE step, runs in a **clean isolated context**,
and writes ONE research note.

## Type

Claude Code Skill (internal pipeline unit — invoked per `(step, hat)` cell by the
exploration Workflow engine, **not** a chat-invokable researcher). For human-facing
multi-angle research, use `cast-web-researcher`.

## I/O Contract (frozen — this is the interface Phase 3a consumes)

- **Input:** `(step, hat_id, goal_context)` + `output_dir`.
  - `step` = `{ index: NN, slug, statement, type/tags? }` — one step only.
  - `hat_id` = one of the 8 frozen hats; **only that hat's block is loaded** (FR-003).
  - `goal_context` = single string, ≤~280 chars, title + one-line intent ONLY.
- **Output (TWO distinct outputs):**
  1. **Note file** (success artifact) — atomically written to
     `goals/{slug}/exploration/research/{NN}-{step-slug}-{hat-id}.ai.md`.
  2. **contract-v2 JSON** (always-written terminal signal) at
     `<goal_dir>/.agent-run_<RUN_ID>.output.json` — `completed` on success,
     `failed` (and NO note file) on failure, so the Workflow can drop the cell to `null`.

## The 8 hats (M_total = 8)

| `hat_id` | Always-on? | Lens |
|----------|-----------|------|
| `expert-practitioner`   | gateable | How the best orgs do it |
| `tool-landscape`        | gateable | Tool comparison |
| `ai-native`             | gateable | What AI makes newly possible |
| `community-wisdom`      | gateable | Practitioner lessons |
| `framework-methodology` | gateable | Structured approaches |
| `contrarian`            | always-on | Broad adversarial failure-hunt |
| `first-principles`      | always-on | What IS the value (80/20 carved OUT) |
| `90-10`                 | always-on | Laziest viable path to ~90% of the value |

## Design notes

- **Generative, never a gate.** Hats surface ideas; they do not score the step. The
  `90-10` verdict (`RECOMMENDED CUT | CUT WITH CAUTION | DO NOT CUT`) is a
  *build-recommendation*, not a grade.
- **DRY:** the Web Fetching Protocol lives in `web-fetching-protocol.md` and is referenced
  by all 8 hats — never embedded 8× (Plan Review Decision #4 / C1-B).
- **Provenance:** the 5 gateable hats + contrarian + first-principles are derived from
  `cast-web-researcher` Angles 1–7 @ commit `8e5c6e7`; each block carries a provenance
  comment. The single-hat versions are **meant to diverge** — `tests/check-distinctness.sh`
  surfaces drift rather than enforcing identity.
- **Carve-out:** all 80/20 content was deleted from `first-principles` and re-homed in
  `90-10` (FR-005, SC-003).

## Key Files

- `cast-hat-researcher.md` — agent instructions + the 8 hat prompt blocks + frozen I/O contract.
- `web-fetching-protocol.md` — shared Web Fetching Protocol (referenced by all 8 hats).
- `config.yaml` — `model / timeout_minutes / context_mode / proactive`.
- `tests/check-distinctness.sh` — runnable SC-002 (no cross-hat leak) + SC-003 (no 80/20 in FP) gate.
- `tests/check-failure-path.sh` — asserts the failure contract (no note file + contract-v2 `failed`).
- `tests/acceptance.md` — the 8-hat distinctness acceptance run (human/LLM-judged portions).
