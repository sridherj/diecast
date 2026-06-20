# Exploration Pipeline N×M: Sub-phase 2a — Single-hat researcher + the 8 hats

## Overview

This sub-phase builds the **lean single-hat researcher agent** (`cast-hat-researcher`) — the
atomic research unit of the N×M pipeline. It is param'd by ONE hat, takes ONE step, runs in a
clean isolated context, and writes ONE research note. It reuses *only* the web-fetch/resilient-
browser protocol from `cast-web-researcher`, deliberately discarding that agent's 7-in-one-context
structure (which is the priming/pollution source this whole goal exists to kill). The sub-phase
also authors all 8 hat prompts, carves the 80/20 notion OUT of First Principles, and implements
the new 90/10 hat exactly to spec. The single-hat agent's **I/O contract is the key interface
Phase 3a's Workflow consumes** — one cell = one invocation = one note file — so it is specified
here precisely and treated as a frozen contract.

The origin framing is load-bearing and non-negotiable: hats are **generative "thinking hats"**
that surface ideas and ways to do things *differently/faster*, never review/score/audit lenses.
gstack contributes **techniques only** (specificity ladder, anti-sycophancy phrasing, [EUREKA]
tags) — never its boil-the-ocean completeness ethos or its review/gate principles.

## Operating Mode

**HOLD SCOPE** — `refined_requirements.collab.md` frontmatter declares `scope_mode: hold`, and
Open Questions reads "None — all ambiguities were resolved during refinement." The 8-hat table,
the 90/10 six-question set, and the note shape are pinned in the spec. This sub-phase's job is
rigorous, exact implementation of a locked spec — bulletproof the hat-distinctness boundaries and
the 90/10 note shape, add nothing (no CEO/Security/Eng hats — explicitly Out of Scope), cut
nothing. Every activity is checked against "is this exactly what FR-003/004/005 and US1/US3
specify?"

## Position in Overall Plan

```
        ┌─ Phase 1a (spike: Workflow engine) ─────────────┐
        │                                                 ▼
Phase 1 ┤                              >>> Phase 2a <<< ─► Phase 3a ─┐
(spikes)│                               (THIS sub-phase)  (Workflow) │
        │                                                            ▼
        └─ Phase 1b (spike: viewer+comment) ─► Phase 2b ─► Phase 3b ─► Phase 4 ─► Phase 5
```

Phase 2a sits on the critical path (1a → **2a** → 3a → 4 → 5). It has **no dependencies** — the
agent is independently testable in isolation. Phase 3a wires it into the Workflow fan-out; the
I/O contract this sub-phase freezes is exactly what Phase 3a's `parallel()` over hats consumes.
It runs in parallel with Phase 2b (Track B viewer work).

## Depends On (from prior plans)

From `docs/plan/exploration-pipeline-nxm-decisions-so-far.md`:
- **Sub-phase 1a** establishes that the Workflow receives `(approved_steps, hat-matrix)` as args
  and invokes one clean-context agent per `(step, hat)` cell. This sub-phase's agent IS that
  per-cell agent — its invocation contract must match how 1a's toy Workflow calls a stub
  single-hat agent (one step + one hat in args). No interface conflict: 1a deliberately used a
  **stub** single-hat agent precisely so 2a can drop in the real one behind the same contract.
- No naming choices from prior rounds constrain the agent's name or note path beyond the spec's
  own `exploration/research/{NN}-{step}-{hat}.ai.md` convention (FR-009), which this sub-phase
  honors verbatim.

---

## Sub-phase 2a: Single-hat researcher + the 8 hats

**Outcome:** A new lean single-hat researcher agent (`cast-hat-researcher`) exists at
`agents/cast-hat-researcher/` and produces a clean-context research note for any one
`(step, hat)` cell — including the new 90/10 hat — with First Principles stripped of all 80/20
content. Running the agent across all 8 hats on one real step yields 8 distinct notes; the 90/10
note matches the spec's note shape exactly; the First Principles note contains zero 80/20 content.

**Dependencies:** None (agent is independently testable; Phase 3a wires it into the Workflow).
Soft-aligns with the 1a stub contract.

**Estimated effort:** 2–3 sessions (1 session: agent skeleton + I/O contract + 5 gateable hat
prompts reused from cast-web-researcher's angles; 1 session: the 3 always-on hats incl. the
First-Principles carve-out + the full 90/10 hat to spec; 0.5–1 session: 8-hat distinctness
verification run + gstack-technique fold-in + config/registry wiring).

**Verification:**
- Run `cast-hat-researcher` once per hat (8 invocations) on ONE real step from a sample goal →
  8 files land at `goals/{slug}/exploration/research/{NN}-{step}-{hat}.ai.md`, one per hat-id.
- **SC-002 / FR-003 check:** diff any two hat-agent prompts for the same step — they share no
  hat-specific framing; grep the agent body to confirm no hat prompt references another hat's
  question or output. Each note's front-matter records exactly one `hat:` value.
- **SC-003 check:** `grep -iE "80/20|80-20|laziest|10% of (the )?effort|cheapest path"` over the
  First Principles note returns nothing; the same grep over the 90/10 note is the only place that
  content lives.
- **90/10 note-shape check:** the 90/10 note contains all required sections (core / proposed cut /
  effort / self-checks / disqualifiers / deferred-decision log / verdict ∈ {RECOMMENDED CUT, CUT
  WITH CAUTION, DO NOT CUT} / sources) and answers all 6 always-ask questions.
- **Distinctness check:** read the First Principles, Contrarian, and 90/10 notes for the same step
  side-by-side — First Principles re-litigates *what the value is*; 90/10 accepts value as given
  and finds the cheapest path; Contrarian runs the broad adversarial failure-hunt. No two read the
  same.

### Key activities

**A. Scaffold the lean single-hat agent (`cast-hat-researcher`)**

- Create `agents/cast-hat-researcher/` with `cast-hat-researcher.md`, `config.yaml`, `README.md`,
  mirroring the directory shape of `agents/cast-web-researcher/`.
- **Split frontmatter vs config.yaml correctly (see Decision #1).** The fleet's `config.yaml`
  schema is `model / timeout_minutes / context_mode / proactive` (verified against
  `cast-web-researcher`, `cast-code-explorer`, `cast-playbook-synthesizer`). `effort`, `memory`,
  and `description` live in the **agent `.md` frontmatter**, NOT in `config.yaml`. There is no
  `interactive:` config key in this fleet — non-interactiveness is enforced by the Workflow
  launching the agent in a clean non-interactive context, not by a config flag.
  - `cast-hat-researcher.md` frontmatter: `name: cast-hat-researcher`, `model: opus`,
    `effort: high`, `memory: user`, `description: …`.
  - `config.yaml`: `model: opus`, `timeout_minutes: 60`, `context_mode: full`, `proactive: false`
    (a Workflow cell is not a proactive standalone run).
- **Do NOT put resilient-browser in `allowed_delegations` (see Decision #2).** `allowed_delegations`
  is the HTTP `cast-child-delegation` allow-list (per cast-agent-design-guide § Dispatcher Allow-List
  Contract). `/resilient-browser` is a **slash-command haiku subagent invoked via the Task tool**
  in-prompt (exactly as `cast-web-researcher` does it) — it is a skill named `resilient-browser`,
  and there is no `cast-resilient-browser` agent. Leave `allowed_delegations` unset/empty; the
  resilient-browser fallback is carried verbatim in the Web Fetching Protocol prompt block, not in
  config.
- → **Delegate (review step):** run `/cast-agent-design-guide` over the drafted agent to confirm
  it conforms to the single-purpose-agent I/O-contract canon. Review output for: correct
  frontmatter, declared I/O contract, non-interactive correctness. Don't expand the guide's
  feedback into a rewrite — apply only conformance fixes.

**B. Freeze the I/O contract (the Phase-3a interface — specify precisely)**

The agent is a pure function: `(step, hat, goal_context) → one note file`. This is the contract
Phase 3a's Workflow calls per cell. Specify in the agent body verbatim:

- **Input contract** — the agent receives exactly:
  - `step` — `{ index: NN (zero-padded 2-digit), slug: <kebab>, statement: <the problem-framed
    step text>, type/tags: <optional, for the agent's own framing — gating already happened
    upstream> }`. The agent researches THIS one step only.
  - `hat` — a single `hat_id` from the frozen vocabulary (below). The agent loads ONLY that hat's
    prompt block. **It MUST NOT see, load, or reference any other hat's framing** (FR-003, US1.S2).
  - `goal_context` — one short paragraph of goal-level context (title + one-line intent), so the
    note is grounded without importing other hats' findings. **Bound this precisely (Decision #4):**
    `goal_context` is a single string, max ~280 chars, drawn ONLY from the goal title + the one-line
    JTBD/intent. It MUST NOT contain: any other step's text, any hat's findings, prior research, or
    decomposition rationale. This bound is what makes angle-independence (FR-003) hold at the *input*
    boundary, not just the prompt-block-selection boundary — an over-stuffed `goal_context` is a
    priming-leak vector that the diff/grep verification would not catch. The Workflow (Phase 3a)
    constructs this string once and passes the identical value to every cell.
  - `output_dir` — the goal's exploration root, default `goals/{slug}/exploration/`.
- **Output contract** — exactly ONE note file, atomically written to:
  `goals/{slug}/exploration/research/{NN}-{step-slug}-{hat-id}.ai.md`
  (e.g. `03-learn-from-past-bugs-contrarian.ai.md`, `03-learn-from-past-bugs-90-10.ai.md`).
  - **On success:** file exists with the per-hat note body (shape below) + a YAML front-matter
    block recording `step_index`, `step_slug`, `hat: <hat_id>`, `date`, `sources_count`.
  - **On failure (so Phase 3a US12/FR-016 can drop the cell to `null`):** the agent writes its
    terminal **contract-v2 output JSON** (`docs/specs/cast-output-json-contract.collab.md`) with
    `status: "failed"` and does NOT write a partial note. **The failure signal is the standard
    contract-v2 envelope, not an ad-hoc `{status, hat, step, reason}` dict (see Decision #3).** The
    `hat`/`step`/`reason` detail rides in the contract's existing fields: `status: "failed"`,
    `errors: ["<reason>"]`, and `task_title` / per-agent extension fields carry the `(step, hat)`
    identity. The agent ALSO emits a contract-v2 envelope on success (`status: "completed"`,
    `artifacts: [{type: "research-note", path: …}]`). This keeps the agent on the same terminal-
    output contract as the rest of the fleet so any Workflow polling pattern (contract-v2 file at
    `<goal_dir>/.agent-run_<RUN_ID>.output.json`) works unchanged. (The Workflow owns the null-cell
    bookkeeping; the agent's job is to fail loudly and cleanly via the standard envelope, never to
    write a half-note that pollutes synthesis.) The note FILE is the success artifact; the output
    JSON is the always-written terminal signal — these are two distinct outputs and the I/O contract
    must name both.
- **Note body shape (all hats except 90/10):** `# {Hat Name}: {Step}` → framing one-liner →
  hat-specific findings (specific names/numbers/URLs, per the depth bar) → **Key Takeaways**
  (3–5 opinionated, actionable, non-obvious, tagged `[EUREKA]` where a genuine insight lands) →
  **Key Sources** (real URLs only). One hat = one angle's depth, not 7 angles compressed.
- **Note body shape (90/10 hat):** see activity E — distinct, spec-pinned shape.

**C. Author the 5 gateable hat prompts (reuse cast-web-researcher's angle text)**

These five map 1:1 onto existing `cast-web-researcher` angles — lift the search patterns, source-
priority ladders, and output framing, but reframe each as a **standalone single-hat prompt** (no
"Angle N of 7", no cross-angle assembly step):

- **`expert-practitioner`** — "How do the world's best people/orgs do this?" (cast-web-researcher
  Angle 1). Output: named orgs, approaches, specific results.
- **`tool-landscape`** — "Best tools — how do they really compare?" (Angle 2). Output: ranked tool
  list + comparison table (stars/pricing/pros-cons).
- **`ai-native`** — "What's newly possible with AI that wasn't 2 years ago?" (Angle 3). Output:
  specific AI tools, what they automate, vs traditional.
- **`community-wisdom`** — "What do practitioners who've actually done this say?" (Angle 4). Output:
  hard-won lessons, real quotes/paraphrases with source links.
- **`framework-methodology`** — "What structured approaches exist?" (Angle 5). Output: named
  frameworks + when-to-use.

Each prompt embeds the **Web Fetching Protocol** verbatim from `cast-web-researcher` (WebFetch →
resilient-browser haiku-subagent fallback → log+skip; never silently drop a 403 URL).

**D. Author the 2 remaining always-on hats — incl. the First Principles carve-out**

- **`contrarian`** (always-on) — "What does the majority get wrong?" (cast-web-researcher Angle 6).
  Broad adversarial failure-hunt: misconceptions, failure modes, when the popular approach is
  wrong. **Distinctness guard in-prompt:** this is the *broad* failure-hunt; it does NOT propose a
  specific cheap cut (that's 90/10's job).
- **`first-principles`** (always-on) — "From scratch, physics-only — what would you do? What IS the
  value here?" (cast-web-researcher Angle 7, **carved**). **CARVE-OUT (FR-005, SC-003):** strip
  every 80/20 / "20% of effort for 80% of value" / MVP-laziest-path sentence from the inherited
  Angle-7 text. The original Angle 7 explicitly says *"MVP approaches that get 80% of the value
  with 20% of the effort"* — that line and its kin are **deleted** here and re-homed in the 90/10
  hat. What remains: fundamental principles, what's truly essential vs convention, re-litigating
  *what the value even is* and reframing/shrinking the step. **Distinctness guard in-prompt:**
  First Principles may reframe or shrink the step (it re-opens *what the value is*); it must NOT
  propose effort-minimizing cuts to a given value (that's 90/10).

**E. Implement the 90/10 hat to spec (`90-10`, always-on, NEW)**

The single most spec-detailed deliverable. Build it as a **generative builder proposing the
laziest viable path**, NOT an auditor. It **accepts the step's value as given** and optimizes
effort to reach it.

- **Generative framing (verbatim, Buchheit):** *"accomplish 90% of what you want with only 10% of
  the work/effort/time… a 90% solution available right away beats a 100% solution that takes ages."*
- **The 6 always-ask questions** (the prompt forces all six, every time):
  1. What's the laziest path to ~90% of this step's value? The ONE thing the user must be able to
     do for it to count as working?
  2. What can be hardcoded / faked (Wizard-of-Oz) / manualized (concierge) / bought (no-code)
     instead of built?
  3. What's the embarrassing-but-shippable v0, and what gets cut to reach it?
  4. Is this a real 90/10 or a disguised 50/50? (Ninety-Ninety rule; does the remainder still
     clear the viability floor?)
  5. Does the cheap version stay on-path (deferred tail buildable later) or become a load-bearing
     dead end?
  6. Is the cut disqualified? (hard-10%-is-the-moat · regulated/trust-critical · irreversible/
     one-way-door)
- **Note output shape (pinned):** core (~90% value) · proposed cut (~10% effort: mechanic +
  concrete v0 + deferred tail) · effort estimate (core vs full; flag hidden 50/50) · self-checks
  (viability / tail-deferrable / on-path / reversibility) · disqualifiers · deferred-decision log ·
  **verdict** (RECOMMENDED CUT | CUT WITH CAUTION | DO NOT CUT) · sources.
- **Distinctness guards baked into the prompt** (verify in the SC-003 / distinctness check):
  - vs **First Principles:** 90/10 never re-opens the goal or re-litigates the value; it finds the
    cheapest path to the *given* value. (FP does the reframing.)
  - vs **Contrarian:** 90/10 proposes-a-cut-and-self-checks *only enough to keep that cut safe*;
    it does NOT run Contrarian's broad adversarial failure-hunt.
- The 90/10 hat still uses the Web Fetching Protocol (for no-code/buy-vs-build evidence,
  Wizard-of-Oz precedents) but its center of gravity is generative reasoning, not a literature
  sweep — keep it from drifting into a tool-landscape clone.

**F. Fold in gstack techniques (techniques ONLY — never principles)**

Apply across all 8 hat prompts:
- **Specificity ladder** — push every claim down to names/numbers/versions/URLs (reinforces the
  existing cast-web-researcher depth bar).
- **Anti-sycophancy phrasing** — prompt the hat to state the unflattering finding plainly; no
  hedging, no "it depends" in Key Takeaways.
- **[EUREKA] tags** — mark genuine non-obvious insights inline so synthesis (Phase 3a) can surface
  them.
- **Explicit guard:** do NOT import gstack's boil-the-ocean completeness ethos or any review/score/
  gate principle. Each hat stays generative and scoped to its one angle; "go deep on the best 3,
  not shallow on 10" (cast-web-researcher philosophy) overrides any completeness urge.

**G. Wire registration + a thin verification harness**

- Add `cast-hat-researcher` to the agent registry. **There is no `agents/REGISTRY.md` (Decision #5)**
  — the registry is `agents/README.md`; add the row there. Then **run `bin/generate-skills`** (it
  exists and is the auto-generator) to emit the skill stub, and verify the generated stub lands where
  the rest of the `cast-*` stubs do. Treat the agent as non-user-facing-triggerable: like
  `cast-subphase-runner`, it is invoked by the Workflow per cell, not by a human trigger phrase — so
  the generated skill description should make clear it is an internal pipeline unit, not a chat-
  invokable researcher (avoid collision with `cast-web-researcher`'s trigger phrases).
- Add a minimal `tests/` note or fixture under `agents/cast-hat-researcher/tests/` capturing the
  8-hat distinctness run as the acceptance check (the Verification block above), so Phase 3a
  inherits a known-good single-cell contract before fan-out. **Make the distinctness checks
  executable, not just prose (Decision #6):** the SC-002 (no cross-hat leak) and SC-003 (no 80/20 in
  First Principles) greps are deterministic and SHOULD be committed as a runnable script
  (e.g. `tests/check-distinctness.sh`) so the gate is reproducible by Phase 3a and CI, not a one-time
  manual read. The 90/10 note-shape check and the side-by-side semantic-distinctness read stay
  human/LLM-judged (they are taste calls), but the two grep-able invariants become a script with a
  non-zero exit on violation. This matches the fleet's "well-tested, more edge cases not fewer"
  bar and gives the carve-out risk a regression guard that survives past this sub-phase.
- **Add an explicit failure-path fixture (Decision #6):** one test case that forces the agent to fail
  (e.g. an unreachable step or injected fetch failure) and asserts (a) NO note file is written and
  (b) a contract-v2 output JSON with `status: "failed"` IS written. This is the FR-016/US12 contract
  Phase 3a depends on; it is currently only verified by prose. The happy path is well-covered; the
  failure path is load-bearing and untested in the plan as written.

### Design review

- **Spec consistency (refined_requirements):** Note path `{NN}-{step}-{hat}.ai.md` matches FR-009
  exactly ✓. The agent is the FR-004 "lean single-hat researcher, param'd by hat, reuses the web-
  fetch/resilient-browser protocol only" ✓. M_total=8 incl. 90/10 and 80/20-removed-from-FP
  matches FR-005 ✓. No product spec in `docs/specs/_registry.md` governs exploration-hat agent I/O
  (this is internal agent behavior, not a user-facing API/UI contract), so no `/cast-update-spec`
  needed for 2a — the user-facing render/comment surface is specced in Phase 2b/4, not here.
- **Naming:** agent name `cast-hat-researcher` follows the `cast-{noun}-{role}` fleet pattern
  (`cast-web-researcher`, `cast-code-explorer`, `cast-playbook-synthesizer`) ✓. Hat-id vocabulary
  is kebab-case and stable (see ledger summary) — `90-10` chosen over `9010`/`90_10` to read
  cleanly in the filename `{NN}-{step}-90-10.ai.md` and match the spec's `…-90-10.ai.md`
  independent-test string in US3 ✓.
- **Architecture / angle-independence:** the whole point is that NO hat prompt can reference
  another hat. Review check: a single agent body holding all 8 prompt blocks is fine *as a
  library*, but at invocation time exactly one block is loaded into context. Guard: structure the
  agent so the hat prompt is selected by `hat_id` and the unselected blocks are never emitted into
  the working context (FR-003 is a context-isolation requirement, not just a "don't mention it"
  requirement). Flag for Phase 3a: the Workflow must invoke this as a fresh clean-context cell per
  hat — if 2a's agent is ever invoked in a shared context, isolation breaks. (1a already proved
  per-cell isolation with the stub.)
- **Error & rescue:** the failure path is load-bearing for FR-016/US12. Review decision: the agent
  must **fail loudly with a structured signal and write NO partial note**, so the Workflow can drop
  the cell to `null` cleanly. A half-written note is worse than no note (it pollutes synthesis).
  This is the "surface, don't suppress" principle applied — the dropped cell is visible, never
  silently empty.
- **Security:** the agent writes one file into `goals/{slug}/exploration/research/`. Validate the
  `{slug}`/`{step-slug}`/`{hat-id}` components are sanitized (no `../`, no path separators) before
  composing the output path — low risk since inputs come from the upstream Workflow, but the agent
  shouldn't trust them blindly. Resilient-browser stays a haiku subagent (per the inherited
  protocol) so its 10–15k-token Chrome MCP responses never land in the hat agent's context.
- **Distinctness regression risk (carried from the high-level plan's risk table):** "90/10 overlaps
  First Principles after the carve-out (Med)." Mitigation is implemented here via the in-prompt
  distinctness guards (activities D + E) and is *verified* by the side-by-side distinctness check
  in Verification. This is the sub-phase that closes that risk.

---

## Build Order

Single sub-phase; internal activity order:

```
A (scaffold + I/O contract) ──► C (5 gateable hats) ──┐
        │                                              ├──► F (gstack techniques fold-in) ──► G (register + verify run)
        └──► B (freeze contract) ──► D (contrarian + FP carve-out) ──┤
                                     E (90/10 to spec) ──────────────┘
```

**Critical inner path:** A → B → E (the 90/10 hat) → F → G. The 90/10 hat (E) and the First-
Principles carve-out (D) are the highest-risk, highest-spec-density items — do them after the
contract is frozen (B) and before the verification run (G), which exists specifically to catch
distinctness leaks between D, E, and contrarian.

## Design Review Flags

| Item | Flag | Action |
|------|------|--------|
| Angle-independence (FR-003) | Isolation is a *context* requirement, not just a "don't mention" one | Select exactly one hat block by `hat_id` at invocation; never emit unselected blocks into context; flag to Phase 3a that each cell must be a fresh clean context |
| Failure path (FR-016/US12) | Agent must not write partial notes on failure | Emit structured `{status: failed, hat, step, reason}`; write NO file; let Workflow own the null-cell drop (surface-don't-suppress) |
| First Principles carve-out (SC-003) | Inherited Angle-7 text literally contains "80% of the value with 20% of the effort" | Delete that line + kin from `first-principles`; re-home in `90-10`; verify with grep in acceptance check |
| 90/10 vs FP vs Contrarian distinctness | Med risk of overlap post-carve | In-prompt distinctness guards (D+E) + side-by-side verification run |
| Output path composition | `{slug}/{step}/{hat}` come from upstream | Sanitize path components (no `../`/separators) before atomic write |
| gstack fold-in | Risk of importing principles, not just techniques | Explicit in-prompt guard: techniques only (specificity ladder, anti-sycophancy, [EUREKA]); no completeness/review ethos |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 90/10 drifts into an auditor/score lens (violates the generative origin) | High | Prompt is anchored on "builder proposing the laziest viable path, accepts value as given"; verdict is a build-recommendation (RECOMMENDED CUT / CUT WITH CAUTION / DO NOT CUT), not a grade; verified by reading the note in the acceptance run |
| 90/10 collapses into First Principles after the carve-out | Med | In-prompt distinctness guards both ways (FP re-opens value; 90/10 accepts it) + mandatory side-by-side distinctness check (closes the high-level plan's named risk) |
| Hat prompts leak cross-hat framing, breaking angle-independence | Med | One block loaded per invocation; grep/diff check across hat prompts in verification; flag fresh-context requirement to Phase 3a |
| 90/10 turns into a tool-landscape clone (over-researches instead of reasoning) | Med | Keep 90/10's center of gravity generative; web-fetch only for buy-vs-build / Wizard-of-Oz precedent, not a full literature sweep |
| I/O contract drifts from the 1a stub the Workflow expects | Med | Specify contract verbatim in the agent body; cross-check against 1a's stub-call shape `(step, hat) → note`; 1a used a stub precisely to absorb this |

## Open Questions

- **Failure-signal shape:** ~~open~~ **RESOLVED (Decision #3):** the failed-cell signal is the
  standard **contract-v2 output JSON** (`status: "failed"`), matching the rest of the fleet — NOT a
  bespoke dict and NOT a sentinel marker file. This is now specified in activity B's Output contract.
  Phase 1a/3a still owns the *polling cadence* and the null-cell bookkeeping, but the *envelope shape*
  is no longer open — it is the contract-v2 file every cast-* agent already writes. Does not block
  building the 8 hat prompts.
- **`90-10` hat-id literal:** spec's US3 independent test names `…-90-10.ai.md`; this plan adopts
  `90-10` as the hat-id so the filename matches verbatim. Confirm no downstream glob in Phase 3a/4
  assumes a single-token hat-id (none currently does). Non-blocking.

## Spec References

| Spec / Doc | Sections Referenced | Conflicts Found |
|------------|---------------------|-----------------|
| `refined_requirements.collab.md` | The 8 Hats table; The 90/10 hat (detail) — 6 questions + note shape + distinctness; FR-003/004/005/006/009/016; US1, US3, US12 | None — this sub-phase implements the spec verbatim |
| `agents/cast-web-researcher/cast-web-researcher.md` | Web Fetching Protocol; Angles 1–7 (lifted as standalone single-hat prompts); "go deep on the best 3" depth bar | None — reused as source material; the 7-in-one structure is intentionally NOT carried forward |
| `docs/plan/exploration-pipeline-nxm-decisions-so-far.md` | Sub-phase 1a stub-agent call shape `(approved_steps, hat-matrix)` → per-cell `(step, hat)` | None — 2a's real agent drops behind 1a's stub contract |
| `docs/specs/_registry.md` | (checked) no product spec governs exploration-hat agent I/O | n/a — internal agent behavior, no `/cast-update-spec` needed for 2a |

---

## Decisions

> Recorded by `cast-plan-review` (BIG CHANGE scope; AskUserQuestion unavailable in this
> environment, so each decision records the reviewer's grounded recommendation pending user
> override). Every entry maps to a numbered issue surfaced in the review.

- **2026-06-20T00:00:00Z — Issue #1: The proposed `config.yaml` mixes invented keys (`effort`, `memory`, `interactive`) with the real schema. Fix it?** — Decision: Yes — split frontmatter (`effort`/`memory`/`description`) from `config.yaml` (`model`/`timeout_minutes`/`context_mode`/`proactive`); drop the non-existent `interactive:` key. Rationale: Verified the fleet schema against `cast-web-researcher`, `cast-code-explorer`, `cast-playbook-synthesizer` — the plan as written would produce a non-conforming agent that the design guide's `/cast-agent-design-guide` review step (activity A) should already have caught. Explicit-over-clever; matches the canon.
- **2026-06-20T00:00:00Z — Issue #2: Should `cast-resilient-browser` go in `allowed_delegations`?** — Decision: No — leave `allowed_delegations` empty; carry `/resilient-browser` as an in-prompt Task-tool haiku subagent in the Web Fetching Protocol block. Rationale: `allowed_delegations` is the HTTP `cast-child-delegation` allow-list (design guide § Dispatcher Allow-List Contract); resilient-browser is a *skill* invoked via slash-command subagent, not an HTTP-dispatched `cast-*` agent. There is no `cast-resilient-browser` agent. Category error in the plan; a populated allow-list here would be misleading and the lint (`cast-agent-compliance`) would not even fire since no `cast-child-delegation` call exists.
- **2026-06-20T00:00:00Z — Issue #3: Is the failure signal an ad-hoc `{status, hat, step, reason}` dict or the contract-v2 envelope?** — Decision: The standard contract-v2 output JSON (`status: "failed"`), per `docs/specs/cast-output-json-contract.collab.md`; this also resolves the plan's first Open Question. Rationale: The whole fleet polls the contract-v2 file at `<goal_dir>/.agent-run_<RUN_ID>.output.json`; inventing a parallel dict shape forces Phase 3a to special-case this one agent and breaks the "contracts are the composition boundary" canon. `reason`→`errors[]`, `(step,hat)` identity→`task_title`/extension fields. The agent must also emit the envelope on SUCCESS (note file = artifact; JSON = terminal signal) — the I/O contract must name both outputs, which it previously conflated.
- **2026-06-20T00:00:00Z — Issue #4: `goal_context` is underspecified, leaving an angle-independence leak at the input boundary.** — Decision: Bound it — single string, ~280 chars, title + one-line intent only; explicitly forbid other steps' text, any hat's findings, prior research, decomposition rationale; Workflow passes the identical value to every cell. Rationale: FR-003 isolation is enforced in the plan only at prompt-block selection; an over-stuffed `goal_context` primes every hat identically and the diff/grep verification (which compares hat prompts to each other) would not catch a shared-input leak. This is the named angle-independence risk, closed at the boundary the verification misses.
- **2026-06-20T00:00:00Z — Issue #5: Registry wiring points at a non-existent `agents/REGISTRY.md`.** — Decision: Register in `agents/README.md` (the actual registry), run `bin/generate-skills`, and mark the generated stub as an internal pipeline unit (like `cast-subphase-runner`), not a chat-triggerable researcher. Rationale: `agents/REGISTRY.md` does not exist; `bin/generate-skills` does. Without the internal-unit framing the generated skill description risks trigger-phrase collision with `cast-web-researcher`, and a human could invoke the single-cell agent out of its Workflow context — which (per the plan's own Architecture flag) breaks isolation.
- **2026-06-20T00:00:00Z — Issue #6: Distinctness/carve-out invariants and the failure path are verified by prose only.** — Decision: Commit the two grep-able invariants (SC-002 cross-hat leak, SC-003 no-80/20-in-FP) as a runnable `tests/check-distinctness.sh` with non-zero exit on violation, and add a failure-path fixture asserting (no note file) + (contract-v2 `status: "failed"` JSON). Keep the 90/10 note-shape and side-by-side semantic reads as human/LLM-judged. Rationale: Well-tested code is non-negotiable and the carve-out regression risk (90/10 vs First Principles) is the named Med risk this sub-phase exists to close — a deterministic, reproducible guard that survives into Phase 3a/CI beats a one-time manual read. The failure path is load-bearing for US12 and is the single most under-tested contract in the plan.

## Plan Review Decisions (2026-06-20)

- **Issue #4 (Code Quality / DRY) — Decision: C1 A+B (accepted).**
  - (B) Extract the **Web Fetching Protocol into ONE shared block** referenced by all 8 hat prompts — do NOT embed it verbatim 8× in `cast-hat-researcher` (the clearest DRY violation in the fleet).
  - (A) For the 5 gateable hats lifted from `cast-web-researcher`, add a **provenance comment** (`derived from cast-web-researcher Angle N @ <commit>`) and a **divergence check** in the distinctness test so cross-agent drift is visible, not silent. Cross-agent angle text stays forked by design (single-hat versions are meant to diverge); full extraction is NOT done (would be over-engineering).
