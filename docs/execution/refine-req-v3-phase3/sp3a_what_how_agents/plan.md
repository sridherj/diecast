# Sub-phase 3a: The WHAT and HOW Agents Exist and Speak a Checkable Contract

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase3/_shared_context.md` before starting.

## Objective

Create `agents/cast-requirements-what/` and `agents/cast-requirements-how/` as net-new,
registry-discoverable agents (`<name>.md` + `config.yaml`, picked up by `bin/generate-skills`), each
runnable tool-free via `claude -p`. The WHAT agent emits a machine-checkable WHAT doc (family-
appropriate section plan with every canonical id mapped exactly once). The HOW agent emits a complete
self-contained HTML document between sentinel markers, honoring the DOM contract and the verbatim-
carriage obligation. These two agents are the maker pipeline's "brains"; everything downstream (3b
gates them, 3c runs them, 3d serves them, 3e specs them) depends on their contracts being fixed and
correct here.

## Dependencies

- **Requires completed:** None within Phase 3 (parallel with 3b). Phase 1 gates green (assumed).
- **Assumed codebase state:** `families.py` (`WorkFamily`, `FAMILY_RECIPES`, `RECIPE_REALIZATION`),
  `parser.py` (`Block.ref`), and the `cast-comment-reanchor` agent dir (carve-out precedent) all exist.

## Scope

**In scope:**
- Author `agents/cast-requirements-what/cast-requirements-what.md` (+ `config.yaml`).
- Author `agents/cast-requirements-how/cast-requirements-how.md` (+ `config.yaml`).
- Encode both I/O contracts (WHAT doc shape, HOW sentinel/DOM/verbatim-carriage rules) as the
  contract block inside each `.md`.
- Document the **optional `GAPS-DETECTED` trailer** (HOW) + the **reserved `gaps: []`** (WHAT) as a
  documentation-only forward reference (revision f) — Phase 5 activates them.
- Regenerate skills via `bin/generate-skills`.
- Smoke-run each agent by hand over this goal's requirements.

**Out of scope (do NOT do these):**
- Do NOT write any gate code (`maker_gate.py` is 3b).
- Do NOT write the runner / job service / route (3c / 3d).
- Do NOT edit the spec (3e owns the single `/cast-update-spec` pass).
- Do NOT write any parsing or behavior for the `GAPS-DETECTED` trailer or `gaps[]` — they are a
  documentation-only seam in Phase 3 (Phase 5 implements them).
- Do NOT invoke or extend the cast-preso slide agents — they are pattern reference only.
- Do NOT tune the model tier — it is `opus` with a `[USER-DEFERRED]` comment.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-requirements-what/cast-requirements-what.md` | Create | Does not exist |
| `agents/cast-requirements-what/config.yaml` | Create | Does not exist |
| `agents/cast-requirements-how/cast-requirements-how.md` | Create | Does not exist |
| `agents/cast-requirements-how/config.yaml` | Create | Does not exist |
| Generated skill files | Regenerate | Via `bin/generate-skills` |

## Detailed Steps

### Step 3a.1: Consult the agent design guide for the I/O-contract section

→ Delegate: `/cast-agent-design-guide` — read the I/O-contract section; the WHAT/HOW contracts below
go verbatim into each agent's `.md` as the contract block. Follow-up: confirm the directory
convention (`<name>.md` + `config.yaml`) and the subagent carve-out shape against the guide.

### Step 3a.2: Author `cast-requirements-what.md`

Input (all **inlined in the user message by the 3c runner** — the agent is tool-free): the full
canonical source text; the parsed block inventory (`ref`, kind, heading, body per block); the
confirmed classification (family + confidence from front matter); the family's `FAMILY_RECIPES`
recipe as **starting vocabulary**.

Output: ONE WHAT doc (markdown body + YAML front matter) exactly matching the
`cast-requirements-what/v1` schema in `_shared_context.md`:
- `contract`, `goal_slug`, `family`, `source_hash`;
- `sections[]` with `title` (family-appropriate, NEVER a US/FR/SC slot name), `outcome` (preso L1/L2
  takeaway), `block_refs[]`;
- `unmapped_refs: []` — every parsed ref appears in exactly one section's `block_refs`; anything the
  agent cannot place goes here and **fails the gate loudly** rather than vanishing;
- `gaps: []` — reserved Phase-5 seam; **always empty in Phase 3, zero behavior**;
- body: per-section communication-intent prose, mirroring the cast-preso-what-worker doc shape,
  adapted to a scrolling document page.

Hard prompt rules (stated here, proven by 3b's gate): sections NEVER named after US/FR/SC slots; ids
are metadata the HOW layer prints as small anchor labels; the WHAT layer never invents content absent
from the source.

### Step 3a.3: Author `cast-requirements-how.md`

Input (inlined by the runner): the gated WHAT doc; the full source text; the visual-toolkit style
tokens + the named archetype library (the runner inlines `visual_toolkit.human.md` and the archetype
template files — cost is explicitly not a constraint); the DOM-contract rules.

Workflow mirrors the preso-how discipline: brainstorm ≥2 visual approaches per section, shortlist
archetypes **by name** from the library (e.g. `single-stat-hero` for the Goal Card, `compare-contrast`
for decisions, `timeline` for phases), write a short brief, then generate.

Output: ONE complete HTML document between `<!-- BEGIN RENDER -->` / `<!-- END RENDER -->` sentinels.
Hard prompt rules (each enforced by 3b's gate):
- self-contained single file: CSS inline, no CDN fonts, no external fetches beyond the FR-028
  sanctioned `/static/htmx.min.js` + `/static/requirements_comments.js` + `data-goal-slug` on `<body>`;
- zero `id=` and zero `data-block-anchor`; each requirement unit one contiguous semantic
  `<section>`/`<li>` under a real `<h2>`/`<h3>` (US7/FR-012/FR-013);
- every canonical id from the WHAT doc emitted **verbatim exactly once** as a small visible anchor
  label on the block carrying that unit's text; never invented, never renamed (FR-003);
- **verbatim carriage:** each unit's anchorable text (source body with inline markdown stripped)
  appears verbatim and contiguous within that unit's container — layout/ordering/section names may
  vary freely around it;
- the HOW layer never invents the WHAT — content comes from the WHAT doc + source only;
- empty recipe blocks are omitted, never padded (US2 Scenario 2).

**Revision (f) — documentation-only forward reference.** Add a clearly-marked "Reserved (Phase 5)"
note to the HOW contract: an OPTIONAL `GAPS-DETECTED` trailer MAY be emitted **after**
`<!-- END RENDER -->` (outside the render sentinels). State explicitly that **Phase 3 ignores it**
(strict extraction stops at the first `END RENDER`) and that **it carries no behavior until Phase 5**.
Pair it with the WHAT doc's reserved `gaps: []`. Write NO handling code.

### Step 3a.4: Write both `config.yaml`s (carve-out precedent = `cast-comment-reanchor`)

```yaml
# agents/cast-requirements-what/config.yaml  (HOW: timeout_minutes: 30)
dispatch_mode: subagent
interactive: false
context_mode: lightweight
allowed_delegations: []
timeout_minutes: 15          # WHAT=15, HOW=30
model: opus                  # [USER-DEFERRED] tier knob — placeholder, do not tune here
```

The runner (3c) reads `model` and `timeout_minutes` from config, so later tier/timeout tuning is a
one-line config change, not a code change.

### Step 3a.5: Regenerate skills

Run `bin/generate-skills`. The two skills must appear **without manual registry edits**.

### Step 3a.6: Smoke-run each agent by hand

Hand-run a `claude -p` of each agent over this goal's requirements (WHAT first, then feed its output
to HOW). Record a short smoke-run note (NOT a CI test — LLM output is gated, not snapshot-asserted).

### Step 3a.7: Compliance audit

→ Delegate: `/cast-agent-compliance` over the two new agent dirs. Follow-up: review output for
allow-list, naming, directory-convention, and config-shape violations; fix any flagged.

## Verification

### Automated Tests (permanent)
- None new in 3a (agent output is gated by 3b, not snapshot-asserted). The gate fixtures that prove
  these agents' output shape live in 3b's `test_maker_gate.py`.

### Validation Scripts (temporary)
- Hand-run `claude -p` smoke runs (Step 3a.6); capture the WHAT doc + extracted HTML to a scratch dir
  for eyeballing. Discardable.

### Manual Checks
- `bin/generate-skills` then confirm both skills are listed (e.g. grep the generated skill index for
  `cast-requirements-what` / `cast-requirements-how`).
- Confirm each `config.yaml` carries `model: opus` + the `[USER-DEFERRED]` comment and the carve-out
  fields.

### Success Criteria
- [ ] Both agent dirs exist with `<name>.md` + `config.yaml` and pass `/cast-agent-compliance`.
- [ ] The WHAT `.md` contract block matches the `cast-requirements-what/v1` schema verbatim (incl.
      `unmapped_refs` + reserved `gaps: []`).
- [ ] The HOW `.md` contract block states all DOM/self-containment/verbatim-carriage rules AND the
      "Reserved (Phase 5)" `GAPS-DETECTED` trailer note (documentation-only).
- [ ] A hand-run produces a WHAT doc whose YAML parses and an HTML doc that extracts cleanly from the
      sentinels (recorded as a smoke-run note).
- [ ] `bin/generate-skills` surfaces both skills with no manual registry edits.
- [ ] No `GAPS-DETECTED`/`gaps[]` handling code was written (documentation-only seam).

## Execution Notes

- **Spec-linked files:** these agents' I/O is new behavior under `cast-requirements-render.collab.md`,
  but the spec edit happens in **3e**, not here. Write the contract text to **match** the 3e deltas
  (happy-path inversion + verbatim-carriage clause). Do not edit the spec in 3a.
- The payloads are **asymmetric by design**: HOW gets toolkit + archetypes; WHAT gets only source +
  inventory + vocabulary. Do not inline the toolkit into the WHAT agent.
- The contracts here are **fixed by the plan**, not discovered — 3b's gates encode exactly these
  rules, so any drift between 3a's contract text and 3b's checks is a bug in one of them.
