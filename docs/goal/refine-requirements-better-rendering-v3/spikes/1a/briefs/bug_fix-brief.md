# Maker brief — `bug_fix` family (spike 1a)

> **Conscious non-delegation (record it):** `/cast-preso-how` is **NOT** invoked. Only its
> 8-step discipline is followed by hand, adapted to a scrolling document page. Do not invoke
> the slide agent at execution time, and do not skip the discipline.

Source: `spikes/1a/fixtures/goal-card-markdown-leak.collab.md` — authored from the **real**
v2 dogfooding defect (the `goal_card.py` / `renderer.py` raw-markdown leak onto the zero-click
Goal Card). Authored from the actual code path, not synthesized fiction.

## The deterministic-baseline gap this family exposes (the reason bug_fix is a strong test)

The bug_fix family recipe is `PROBLEM → EVIDENCE → OPEN` (`Intent`, `Evidence`,
`Open Questions`). The deterministic renderer therefore **realizes none of the FR or SC
tables** for a bug_fix doc — measured: the baseline HTML carries **2** id tokens (one is a
prose mention `(this is SC-001)`, one is an `FR-012` reference inside a CSS comment in the
inlined theme), while the source defines **7** canonical ids (FR-001…004, SC-001…003). A
reader of the deterministic bug_fix page **cannot see what the fix is or how it will be
verified** — the fix scope and the acceptance checks are silently dropped. This is the single
clearest "maker beats deterministic" case in the corpus, and it is a real property of the
shipped recipe, not a contrivance.

## Step 1 — Brainstorm 2–3 visual approaches

**Approach A — "Forensic report" (what broke ▸ the evidence ▸ the fix ▸ how we'll know).**
A defect-report layout: a red/raspberry "what broke" hero, an evidence exhibit quoting the
two offending emit sites, then the fix as a checklist of FRs, then the SC acceptance row.
*Pro:* mirrors how an engineer actually reads a bug; surfaces the dropped FR/SC the baseline
hides. *Con:* needs restraint so the accent-red doesn't shout. *Steve-Jobs test:* **passes** —
it reads like a bug, which is exactly US2's promise.

**Approach B — "Before/after code diff hero."** Lead with the literal bad-vs-good emit line
(`escape(x)` → `_md_to_html(x)`).
*Pro:* visceral. *Con:* over-indexes on one FR and buries the others; a render is not a PR.
*Steve-Jobs test:* **partial** — fold the diff in as *evidence*, don't make it the whole page.

**Approach C — "Plain incident table."** *Con:* this is essentially the deterministic
baseline; no comprehension lift. *Steve-Jobs test:* **fails** — it's the thing we're beating.

**Chosen: Approach A**, folding B's before/after line into the Evidence exhibit.

## Step 2 — Archetype shortlist

| Scroll section | Archetype borrowed | Why |
|---|---|---|
| Defect Goal Card | **single-stat-hero** | "0 markdown characters should reach the card" — the bug stated as a target. |
| What broke | **one-statement** + short prose | The problem in one line, then the mechanism. |
| The evidence | **diagram-annotated** / **code-showcase** vocabulary | The two emit sites, annotated; the before→after line. |
| The fix | **build-up-sequence** (FR checklist) | FR-001…004 as ordered, each a complete thought — *the content the baseline drops*. |
| How we'll know it's fixed | **consulting-exhibit** | SC-001…003 as measurable checks — *also dropped by the baseline*. |
| Open question | **one-statement** (muted) | The deferred sibling-defect call. |

## Step 3 — (this brief)

## Step 4 — Craft discipline (applied in `bug_fix-maker.html`)

- Same verbatim toolkit tokens as the `new_initiative` page (one shared visual system —
  Constraint: reuse the toolkit, don't build a new one). The **accent is dialed toward the
  red end of the raspberry** for the "what broke" hero to make the family read distinct from
  the initiative page (US2: a bug fix should *look* like a bug fix).
- Family-appropriate section names: *"What broke," "The evidence," "The fix,"
  "How we'll know it's fixed"* — never US/FR/SC slots.
- Every canonical id (FR-001…004, SC-001…003) appears exactly once as a visible anchor label
  on the block it identifies — **including the FR/SC the deterministic baseline omits.**
- DOM contract identical to the other page: contiguous semantic units, zero `id=`, zero
  `data-block-anchor`, FR-028 script tags + `data-goal-slug` present.

## Step 5–8 — covered by the audits + checker (see `spike-results.md`).
