# Code Exploration: 04 — Agents as Colleagues (preso v2/v3 board, marketplace, resume assets)

**Goal context:** Product Revamp: Diecast — Vision Prototype. Clickable HTML mockup whose
"agents-as-colleagues" surfaces (US5 board→ticket→decision→escalation arc; US6
marketplace/resume/hiring) need screen-level design. Quality bar is "software built for the
future"; existing assets are a **terrain map, not an anchor** — lift only what serves the vision.
**Codebase:** `/data/workspace/second-brain/taskos/goals/taskos-gtm/presentation_v2/` and
`presentation_v3/` (the preso-pipeline slide assets a08–a13, s8a, s8b).
**Date:** 2026-06-11

> Scope note: this is a *design-asset* terrain, not an application codebase. The 7 angles are
> adapted accordingly: the "schema" is the canonical fake-data spine + design-token system; the
> "implementation" is the rendered slides; "tests" are the preso-pipeline checker reports.
> Everything here is HTML+inline-SVG slide craft (reveal.js fragments) — **none of it is
> interactive UI**. The single biggest reuse caveat lives in §3.

---

## 0. What was reviewed (and what these assets are)

The delegation named a08–a13 as "the strongest existing assets." They are six reveal.js slides
that already design exactly the four-frame arc US5 asks for plus the marketplace/resume US6 asks
for. v3 re-skinned two of them as core slides. Concretely:

| Asset | File (relative to taskos-gtm) | Vision surface it pre-designs | US/FR |
|-------|-------------------------------|-------------------------------|-------|
| a08-board-view | `presentation_v2/how/a08-board-view/slide.html` | Shared human+agent board, assignee filter | US5.S1, FR-010 |
| a09-one-ticket | `presentation_v2/how/a09-one-ticket/slide.html` | Ticket activity log = maker-checker iteration | US5.S2, FR-008/010 |
| a10-decision-artifact | `presentation_v2/how/a10-decision-artifact/slide.html` | Structured decision record on the ticket | US5.S3, US10, FR-010/021 |
| a11-escalation | `presentation_v2/how/a11-escalation/slide.html` | L3 escalation rail, 3 pre-framed options | US5.S4, US10, FR-010/022 |
| a12-marketplace-grid | `presentation_v2/how/a12-marketplace-grid/slide.html` | 12-agent catalogue, 6 archetypes, in-card pairing | US6.S5, FR-011 |
| a13-agent-resume | `presentation_v2/how/a13-agent-resume/slide.html` | One agent's full resume | US6.S3, FR-011 |
| s8a-board-view (v3) | `presentation_v3/how/s8a-board-view/slide.html` | a08 re-skinned: Cast→Diecast, core slide | US5.S1 |
| s8b-hire-dont-install (v3) | `presentation_v3/how/s8b-hire-dont-install/slide.html` | 7-agent "starter team" dossier + self-gen prompt | US6, FR-011 |

Each `how/<slide>/` dir also carries a `brief.collab.md` (the regeneration blueprint), a
`what/<slide>.md` design-intent doc (read separately — `presentation_v2/what/`), and
`check-*.json` / `checker_feedback.md` (the quality-gate verdicts). The intent docs are the
authoritative "why"; the slide.html is the authoritative "what it looks like."

---

## 1. Canonical fake-data spine & design-token "schema"

The single most valuable thing to lift wholesale is the **internally-consistent fake-data spine**.
The requirements (Directional Ideas, Constraints) explicitly want "one coherent fictional
org/project reused everywhere." These slides already built it and it recurs across all four board
frames. The prototype should adopt this spine verbatim so screens feel like one product.

**Entities & canonical IDs (reuse exactly):**

- **Ticket `CAST-412`** — the spine ticket. ⚠️ **Inconsistency to reconcile:** on the board
  (a08/s8a) its title is "Add Postgres index on users.email" assigned to `crud-orchestrator`;
  inside a09 it is "Create Invoice entity + CRUD stack." a10's decision is about *task* soft-delete.
  The slides played loose because each was a standalone jump-in; a *clickable* prototype where you
  navigate board→ticket needs ONE coherent title/scope. **Pick one (recommend the Invoice CRUD
  stack from a09, it's the richest) and propagate.**
- **Agents** (all real, on disk): `crud-orchestrator` (CO, maker/orchestrator),
  `entity-creation` (EC, sub-maker), `compliance-checker` / `crud-compliance-checker-agent`
  (CC, checker), `decision-agent` (DA, drafts decision artifacts).
- **Human:** `@you`, avatar initials `SJ`.
- **Rule-violation codes:** `M04` (convention drift — `SoftDeleteMixin` missing), `S03` (typing
  too permissive — `Optional[Any]`), `R02` (missing index on FK). These are load-bearing and recur.
- **Iteration spine (a09):** 10:02 CO picks up → 10:11 EC v1 → 10:13 CC posts M04/S03/R02,
  `status→needs_work` → 10:17 EC v2 → 10:19 CC approves 5/5 → `PR #2341` auto-opens. Rework `1/3`.
- **Decision artifact (a10):** file `decisions/2026-04-15-task-soft-delete.md`, status `accepted`,
  5 required fields `id / reversibility:L2 / escalation / spike_ref / consequences`, `revisit_when`,
  co-signed `sj · decision-agent`, `spike_ref: CAST-412-spike-softdelete`.
- **Escalation (a11):** ticket `CAST-417` "DROP table user_events", `L3 reversibility`,
  `status: needs_work`, routed to `@you`, **3 ranked options A/B/C**, policy file
  `decisions/2026-03-12-escalation-policy.md`, board filter `escalated to me`.
- **Marketplace (a12):** 12 hires — 7 Makers/2 Checkers/4 Specialists; 7 shipped / 5 proposed;
  6 archetypes (Maker, Checker, Decision, Spike, Escalation, Mentor).
- **Weight classes:** `L1` architectural/irreversible · `L2` codebase-wide convention ·
  `L3` local-detail/reversibility-trigger. (Note the L3 dual-use flagged in a11 brief — see §5.)

**Design-token "schema"** — defined once in `presentation_v3/presentation/index.html` and
referenced by every slide via CSS custom properties. This *is* the design system to inherit:

```
--color-bg:        #F5F4F0   (warm paper)
--color-surface:   #ECEAE4   (panel)
--color-accent:    #D6235C   (magenta/pink — the single accent; agents, checkers, primary action)
--color-text:      #1A1A28   (near-black)
--color-muted:     #4A4860   (slate)
--color-callout-bg:     rgba(214,35,92,0.06)   (accent tint)
--color-callout-border: var(--color-accent)
--color-question-bg:    rgba(74,72,96,0.06)    (muted tint — annotations)
--color-question-border:var(--color-muted)
--font-heading / mono:  'IBM Plex Mono','SF Mono','Fira Code', monospace
--font-body:            'DM Sans', system-ui, sans-serif
```

Typographic grammar: **mono for identity** (agent slugs, ticket IDs, file paths, rule codes,
status chips) and **DM Sans for prose** (callouts, role descriptions). This mono/sans split is the
backbone of the "this is a developer's tool" feel and should carry into the prototype.

---

## 2. Existing design implementation (screen-by-screen, what's actually built)

### The shared archetype: "Consulting Exhibit"
Every one of these slides uses the same archetype: **left-aligned action title + a hero panel
that is an inline-SVG "screenshot" of the product + a right-hand column of numbered callouts.**
The SVG-as-screenshot technique is the key craft move — v1 had rendered these as 400–600-line
div-grid simulations and the checker failed them (criterion-10); v2 rebuilt each hero as a single
inline `<svg viewBox>` with class-mapped fills (`.fill-accent {fill: var(--color-accent)}` etc.).
For a *static deck* this was the right call. For a *clickable prototype* it is the opposite call —
see §3. But the **visual language** the SVGs encode is exactly right and fully transferable.

### a08 / s8a — Board view (US5.S1) — STRONGEST anchor
- Layout: 62/36 flex split. Hero = Linear-style PM board SVG (`viewBox 0 0 760 520`): left sidebar
  (`diecast_` workspace badge, Inbox/My issues, TEAMS, VIEWS) + 4 columns (BACKLOG/IN PROGRESS/IN
  REVIEW/DONE) + 6 ticket cards.
- **The load-bearing affordance:** an `Assignee type:` filter chip row with exactly four pills —
  `any` (active, accent-filled) / `human` / `agent` / `checker`. `checker` as a first-class
  assignee type is the whole thesis in one control.
- **Peer-avatar grammar (critical to lift):** each ticket shows an assignee dot + role label.
  Human = solid `fill-text` dot + `human @you`; agent = solid `fill-accent` dot + `agent
  crud-orchestrator`; checker = dashed outline `fill-muted` dot + `checker compliance`. Humans and
  agents sit in the *same columns, same card format* — parity is structural, not a separate lane.
- 3 callouts: (1) parity, (2) the four-value filter, (3) "Diecast publishes INTO your PM tool. It
  does not replace Linear/Jira/GitHub Projects."
- v3 changes vs v2: `cast_`→`diecast_`, callout 3 "Cast"→"Diecast", removed S9/S10 back-links,
  subline became "press Down for ticket, decision, escalation" (vertical stack nav).

### a09 — One ticket / activity log (US5.S2) — STRONGEST single screen
- 62/38 split. Hero SVG (`viewBox 0 0 760 620`) is a full PM ticket: breadcrumb → title → status
  chip (`done`) + **rework chip (`1 / 3 rework`)** → description strip → **two-column body**:
  left = 6-row activity log, right = aside metadata panel.
- **Activity log = maker-checker conversation.** Rows carry timestamp, a role-styled avatar circle
  (CO/EC outlined; **CC accent-filled** — the checker is visually distinct), and the action text.
  The checker's 3-violation row gets an **accent left-border highlight band** (`fill-callout-bg` +
  3px `fill-accent` stripe) — this is the visual treatment for "checker spoke." M04 carries a
  `next slide › decision` forward-cue pill.
- Aside panel: ASSIGNEE (CO, maker) · CHECKER (CC, checker) · STATUS · **REWORK BUDGET 1/3 used
  (contract-defined)** · LINKED PR #2341 · ATTACHMENTS · ROLES-IN-LOG legend.
- Header band frames PM integration: `Cast agents → webhook → Linear · Jira · GitHub Projects`.
- 3 muted "annotation" callouts (note: these use `--color-question-*` tinting, not accent — a
  second, quieter callout style): "Observability for free / PM-native comments / Bounded by contract."

### a10 — Decision artifact (US5.S3, US10) — directly serves decision-tracking
- Hero SVG = a decision-artifact "card" on the ticket: filename title
  `decisions/2026-04-15-task-soft-delete.md`, chips `accepted` + **loud `L2 · codebase-wide
  convention` badge** (the primary signal) + `co-signed`.
- **5 numbered YAML frontmatter fields** rendered as a checklist (`id / reversibility / escalation
  / spike_ref / consequences`), field 2 (reversibility) given the accent highlight band.
- Aside: SIGNED BY (SJ human "TL sign-off" + decision-agent) · TICKET · SPIKE chip · REVISIT_WHEN
  · **WEIGHT-CLASS legend (L1/L2/L3 with L2 highlighted "← this")** · "Greppable. Diff-able.
  Committed with the code."
- `fixes: artifact loss` tag (ties back to the failure-mode taxonomy) and a dashed "if
  reversibility had been L3 → next slide" tee-up pill.

### a11 — Escalation rail (US5.S4, US10 autonomy) — most design-rich
- Hero SVG (`760 620`): ticket `CAST-417` "DROP table user_events", `needs_work` + **loud `L3 ·
  reversibility trigger` badge** + `routed to @you` chip; 3-row escalation activity log (EC drafts
  → **CC flags L3** highlight band → human SJ avatar "routed to @you").
- **Ranked three-option rail** — the standout pattern. v1 drew 3 identical cards; the checker
  failed it for not encoding the narrative's A>B>C ranking. v2 encodes rank as *structural visual
  weight*: **Option A** = accent-filled hero card, taller, white text, `RECOMMENDED` micro-badge;
  **Option B** = outline card, regular weight; **Option C** = ghost/muted-stripe card, reduced
  opacity. Each card = letter + role label (`PROCEED SAFELY` / `PRESERVE QUO` / `DEFER TO SPIKE`)
  + 2-line headline + italic consequence.
- Two-way-rail note ("when you pick, the agent resumes with your choice; ticket needs_work→active")
  + **policy-provenance line** (`policy: decisions/...escalation-policy.md` — "threshold is a file
  in the repo. auditable. not LLM judgment").
- Aside repeats STATUS · REVERSIBILITY (L3 second sighting) · ESCALATED TO @you · POLICY FILE ·
  **BOARD FILTER `escalated to me`** (closes the loop back to a08's board) · "Agents know when to stop."
- Note: a11 has **no fragments** — fully formed at rest (designed for cold jump-in).

### a12 — Marketplace grid (US6.S5) — STRONGEST catalogue
- 68/30 split. Hero is NOT a card grid — it's a single SVG **"registry file"** (`tier_1_marketplace.registry`)
  styled like a code editor (traffic-light dots, filename, `12 HIRES` chip) with **3 grouped
  sections via accent-opacity left strips**: `# MAKERS` (rows 01–06, 100% strip) / `# CHECKERS`
  (07–08, 75%) / `# SPECIALISTS` (09–12, 55%).
- Each row = line-number + mono agent slug + archetype pill + a `//` code-comment role/benchmark
  gloss. **In-card pairing rule honored:** every Maker row ends `→ paired: <checker>` inline —
  the checker is NEVER a separate card; only the 2 standalone Checkers get their own rows.
- **Shipped vs proposed encoding:** shipped = solid accent pill, full opacity; proposed = dashed
  accent-outline pill, `0.68` group opacity, `(proposed)` end-of-row tag. Legend band + footer
  `$ 7 shipped · 5 proposed · 6 archetypes` + `src: linkedout-oss + taskos registry`.

### a13 — Agent resume (US6.S3) — deep-on-one
- 70/28 split. Hero SVG **"resume artifact"** (`crud-orchestrator-agent.resume`) with code-editor
  chrome + chips `SHIPPED / MAKER / LINKEDOUT-OSS`, and 3 accent-opacity sections: `# PRIMARY
  CLAIM` (role + benchmark scenario/pass) / `# SAMPLE OUTPUT` (inset code panel: 7-line directory
  tree, dashed separator, paired-checker report excerpt with `PASS`/`FAIL at line N`) / `# RESUME
  DETAILS` (i/o · pair · tests rows).
- **Honesty mechanism:** three `AWAITING RUN LOG` chips stand in for unmeasured numbers (blocking
  open question OQ-3). Footer shell line: `$ interview --run-on=your-codebase
  --read=compliance-report.md` — "that is the interview."

### s8b — v3 "starter team" dossier — a refined, tighter US6 take
- Single-column: oversized `Hire. Don't install.` title + resume-vocab subline + SVG dossier
  (`s8b_starter_team.hires`, 7 agents in 3 sections: **FLAGSHIP PAIR** with a literal
  **bracket-tie** SVG path linking rows 01+02 labeled `THE PAIR`; **CRUD BENCH** 3 makers sharing
  one checker; **CROSS-CODEBASE SAME PATTERN** 2 taskos agents) + a fragment **self-generation
  prompt** banner ("Which agents in your current work would you like to hire? — pause. the room
  answers."). This bracket-tie is a cleaner "the pair is the unit" device than a12's inline arrow.

---

## 3. Gap analysis (what these assets DON'T give the vision prototype)

Prioritized by how much it blocks reuse.

- **[CRITICAL] Static SVG screenshots ≠ clickable UI.** Every hero is a hand-laid inline SVG with
  absolute x/y coordinates (e.g. `<rect x="303" y="118" width="145" height="92">`). It looks like
  a product but nothing is a real DOM element — no hover, no click, no filter that actually
  filters, no board→ticket navigation. The prototype (FR-001, clickable end-to-end) must
  **re-implement these as real HTML/CSS components.** Lift the *visual spec* (layout proportions,
  the token system, the avatar grammar, the chip styles, the ranked-option hierarchy) — discard the
  SVG coordinate geometry. Treat the SVGs as high-fidelity mockups, not source.
- **[CRITICAL] No interactivity / state.** The vision needs: a working assignee filter (any/human/
  agent/checker), board→ticket→decision→escalation as four navigable screens with "continuous
  chrome" (FR-010), and the canvas-morph + chat rail (US1, FR-004). None exist. The four frames
  are designed as *independent jump-in slides*, not a connected SPA. The "continuous chrome /
  consistent vocabulary" the slides achieve by hand must become a shared component shell.
- **[HIGH] Fake-data inconsistency** (CAST-412 title drift across a08/a09/a10 — see §1). Harmless
  in a deck where you only ever see one frame at a time; visible and jarring in a clickable
  prototype. Must be reconciled into one coherent ticket scope before reuse.
- **[HIGH] Open question OQ-3 (a13):** the three resume benchmark numbers are unresolved
  `AWAITING RUN LOG` placeholders. The prototype uses "realistic fake data" (FR-019) so it can
  simply *fill these with plausible fake numbers* — but someone must decide the numbers; don't
  ship the literal "AWAITING RUN LOG" chip into a polished mockup unless intentionally showing the
  honesty mechanism.
- **[MEDIUM] Hiring *flow* is absent.** a12/a13/s8b show the marketplace and resume *artifacts*,
  but US6's full flow (assessment definition → federation to 5–10 candidates → stack-ranked hiring
  report with pros/cons → hire → onboarding to data sources/tastes) has **no existing design**.
  Only the catalogue and resume endpoints exist. The middle of the funnel is greenfield.
- **[MEDIUM] No "execution drill-in" parent context.** US3/FR-008 wants WHAT-level → execution
  tab → run list → dispatch tree (13 sub-agents) → maker-checker loop. a09 is the *leaf* of that
  drill-in (one ticket's loop), but the run-list and dispatch-tree levels above it are not designed
  here (they may exist in other slides — A-v2-a05 one-agent-end-to-end, A-v3-chain — not in scope
  of this review).
- **[MEDIUM] PM-secondary persona is implied, not shown.** The board is "the PM surface" but
  there is no PM-framed moment in these assets (the one PM moment lives in US7's requirements loop,
  a different surface).
- **[LOW] Desktop-only, fixed reveal.js viewport.** Slides assume a 960-ish-wide slide canvas and
  `em`-relative sizing keyed to reveal.js root font. Re-deriving for a full-bleed app canvas is
  trivial but not free.
- **[LOW] Two callout styles coexist** (accent `.callout` vs muted `.annotation`) without a
  documented rule for when to use which — the prototype should formalize this (e.g. accent =
  product claim, muted = observation).

---

## 4. Patterns & conventions (the reusable design grammar)

These are the high-value, directly-liftable conventions:

1. **Peer-but-distinguishable avatar system.** Three render styles encode role on a shared board:
   human = dense `fill-text` circle; maker agent = outlined (`fill-bg` + `stroke-text`) circle;
   checker agent = accent (`fill-accent`/`stroke-accent`) circle. Same size, same row, same card —
   parity — but instantly role-readable. **This is the single most important pattern for
   "colleagues, not tools."**
2. **Mono-for-identity / sans-for-prose** typographic split (§1).
3. **One accent color, opacity as hierarchy.** `#D6235C` is the only accent; rank/emphasis is
   carried by opacity (section strips at 100/75/55%; proposed rows at 0.68) and fill-vs-outline,
   not by a second hue. Cheap, consistent, scalable.
4. **Status/weight as chips.** `done`, `needs_work`, `1/3 rework`, `L2`, `L3`, `co-signed`,
   `routed to @you`, `escalated to me` — all small rounded-rect chips, mono text. A reusable chip
   component covers most of the board arc.
5. **Checker-speaks highlight band:** `fill-callout-bg` panel + 3px `fill-accent` left stripe marks
   any checker/decision intervention in an activity log. Consistent across a09/a11.
6. **Ranked-options hierarchy (a11):** when presenting N choices with a recommendation, encode rank
   as structural weight (hero-fill A / outline B / ghost C + `RECOMMENDED` badge), never N equal
   cards. Directly reusable for the escalation rail and any autonomy-gated clarification (US10.S2).
7. **In-card pairing (a12/a13/s8b):** a maker's checker is always a field/continuation of the
   maker, never a separate entity — `→ paired: <checker>` inline, or the s8b bracket-tie. Encodes
   "maker-checker is the quality unit" structurally.
8. **"Registry file" / "resume artifact" framing:** rendering catalogues and resumes as
   code-editor documents (traffic-light chrome, line numbers, `//` comments, `$` shell footer)
   makes them read as developer artifacts. Strong, on-brand, reusable for any
   agent/skill/contract listing (US8, US9 contract catalogue).
9. **Numbered priority callouts** in a right rail (accent circle + short DM Sans line), 3 per
   surface, priority-ordered. A clean annotation pattern if the prototype keeps an explainer rail.
10. **Canonical-vocabulary discipline:** `@you`, `needs_work`, `rework budget`, `L1/L2/L3`,
    `spike_ref`, `escalated to me`, `→ paired:` recur verbatim across all frames. FR-018 mandates
    continuity — adopt this exact lexicon.

**Brand transform log (v2→v3), for vocabulary compliance (FR-018):** `Cast`→`Diecast` (product),
`cast_`→`diecast_` (workspace badge), `Tier`→`Layer`, appendix back-links removed (slides became
core + vertical press-down stack). Ticket keys kept uppercase `CAST-###` (Jira-style issue key) —
distinct from lowercase `cast-*` module slugs; both conventions coexist intentionally.

---

## 5. Surface flow & navigation (how the four frames connect)

The arc is designed as a **linked story** but wired as slide jumps, not app routes:

```
                 ┌─────────────── canonical vocabulary spine ───────────────┐
   s8a/a08       a09                a10                  a11
   BOARD   ──►   TICKET        ──►  DECISION        ──►  ESCALATION
  (parity +     (maker-checker     (L2 artifact,        (L3 trigger,
   assignee      activity log,      5 fields,            3 ranked options,
   filter)       rework 1/3,        co-signed,           routed @you,
                 PR #2341)          fixes artifact-loss) board filter
                      │                  ▲                "escalated to me")
                      │  M04 comment ────┘  pulled out as the decision        │
                      └─ forward-cue pill "next slide › decision"             │
                 a11 board filter "escalated to me" ──── loops back to a08 ───┘

   s8b/a12/a13 = the HIRING side-arc (parallel, off the board):
   s8b starter team ─► a12 full catalogue (12) ─► a13 one resume (deep)
```

- **Forward/back cues are explicit in-asset:** a09's M04 row carries a `next slide › decision`
  pill; a10 carries an `if L3 → next slide` tee-up; a11 carries an `A8›A9›A10›A11 · arc end`
  breadcrumb; a11's `escalated to me` board filter explicitly references "the same A8 board." The
  arc is self-aware — these cues become real nav links in the prototype.
- **L3 dual-use caveat (from a11 brief):** the deck uses `L3` both as "decision weight = local
  detail" (thesis Principle 5) AND as "reversibility trigger = most consequential/irreversible."
  a10 and a11 lean on the *reversibility* reading. The requirements (US10/FR-022) lock
  reversibility-keyed autonomy (L1 decide-and-record / L2 decide-record-notify / L3 ask-first),
  which matches the *reversibility* reading. **The prototype should standardize on
  reversibility-keyed L1/L2/L3 and not import the conflicting decision-weight gloss.**

---

## 6. Quality-gate signals (checker reports — reuse-readiness)

The preso pipeline ran content/visual/tone checkers on each slide; verdicts live in each `how/`
dir (`check-results.json`, `checker_feedback.md`, `check-content/visual/tone.json`). Signal worth
carrying forward:

- The **v2 regeneration of all six slides (2026-04-18) was driven by a single recurring failure:
  criterion-10** — v1 rendered product surfaces as massive div-grid simulations (a08 was 466 lines,
  a09 618, a12 449, a13 255) and the visual checker rejected them as not reading like real product
  screenshots. v2's fix was the inline-SVG-screenshot archetype. **Lesson for the prototype:** the
  bar that these passed is "reads like a real product surface" — but for a *clickable* prototype the
  pendulum swings back to real DOM components (the div approach v1 took, done well), since now you
  need actual interactivity, not a screenshot. Don't cargo-cult the SVG decision.
- a11's regeneration specifically fixed "3 identical option cards" → ranked hierarchy. That fix is
  a design requirement worth preserving (§4.6).
- a13 carries an **unresolved blocking open question** (`OQ-3`, the AWAITING-RUN-LOG numbers) — its
  `open_questions.md` is the place to look before reusing the resume numbers.
- Tone checkers enforced: **no em dashes, no GPT-isms** (leverage/orchestrated/cutting-edge/etc.),
  short sentences, hyphens only. FR-018 carries the same rule — the slide copy is already compliant
  and can be lifted as-is for microcopy.

---

## 7. Config & dependencies (what the assets rely on)

- **Design tokens:** the full token set is defined in `presentation_v3/presentation/index.html`
  (and the v2 assembly `index.html`) and consumed by every slide via `var(--color-*)`. To reuse
  any slide standalone you must port this `:root` block. This is the design-system contract.
- **Fonts:** IBM Plex Mono (heading/mono) + DM Sans (body) — web fonts, loaded by the presentation
  shell, not the slide. The prototype must load both.
- **Framework:** reveal.js. Slides depend on `.fragment.custom.callout-appear` for staged reveals
  and reveal's `em`-relative root sizing. The prototype is NOT reveal.js, so fragment/`aside.notes`
  machinery is dropped; only the static markup + CSS + token references transfer.
- **Visual toolkit provenance:** the shared craft (archetypes, tokens, chip/callout patterns) comes
  from the `cast-preso-visual-toolkit` skill — which the requirements (Directional Ideas,
  Constraints) already name as reusable craft for the prototype's design system. The board/
  marketplace/resume slides are the most product-shaped application of that toolkit.
- **No backend/data dependency** — everything is hand-authored static content. Good: nothing to
  stub. The fake-data spine (§1) is the only "data" and it lives inline in the SVGs.

---

## Key Takeaways

1. **The four-frame board arc (a08→a11) is a near-complete screen-level design for US5 and should
   anchor the prototype's "agents-as-colleagues" surfaces.** Board parity + assignee filter +
   maker-checker activity log + structured decision artifact + ranked escalation rail are all
   designed, vocabulary-consistent, and tone-compliant. This is the highest-leverage reuse in the
   whole goal — adopt the *design*, re-author the *implementation*.
2. **The peer-but-distinguishable avatar system is the core "colleague" device** — humans, maker
   agents, and checker agents share the board/columns/card format (parity) but carry three distinct
   circle render styles (role legibility). Lift this exactly; it answers the goal's central
   question ("colleagues, not tools") more directly than any copy.
3. **Biggest constraint / what breaks on reuse: it's all static inline-SVG, zero interactivity.**
   These are high-fidelity mockups, not components. The prototype must re-implement every surface
   as real HTML/CSS to get the clickable filter, board→ticket nav, and continuous chrome the vision
   needs. Treat the SVG geometry as throwaway; keep the visual spec, tokens, and grammar.
4. **Surprisingly good and worth preserving verbatim:** the design-token system, the
   mono/sans split, the one-accent-opacity-as-hierarchy discipline, the ranked-options hierarchy
   (a11), the in-card maker-checker pairing (a12/s8b bracket-tie), and the entire canonical fake-
   data spine + lexicon. These are exactly the "reuse before re-author" assets the requirements call
   for, and they're already FR-018 brand-compliant.
5. **Most impactful gap to fill: the hiring funnel middle (assessment → federation → stack-ranked
   report → onboarding) is greenfield.** a12/a13/s8b give the marketplace and resume endpoints but
   not the flow between them. That's where new design work concentrates for US6.
6. **One cleanup blocker before reuse:** reconcile the CAST-412 title drift across frames into one
   coherent ticket so the clickable board→ticket path holds together, and standardize on
   reversibility-keyed L1/L2/L3 (dropping the conflicting decision-weight gloss of L3).
7. **Don't cargo-cult the SVG-screenshot decision.** It was the right answer to the deck's
   "looks-like-a-product" checker bar; the prototype's bar is "IS a clickable product," which
   points back to real DOM components done well.

## Key Files
- `presentation_v2/how/a08-board-view/slide.html` — shared board, assignee filter, peer-avatar grammar (US5.S1 anchor).
- `presentation_v3/how/s8a-board-view/slide.html` — a08 re-skinned to Diecast brand; use as the brand-correct board reference.
- `presentation_v2/how/a09-one-ticket/slide.html` — ticket + maker-checker activity log + rework budget + aside metadata (US5.S2; the strongest single screen).
- `presentation_v2/how/a10-decision-artifact/slide.html` — 5-field structured decision record, L2 badge, weight legend (US5.S3 / US10).
- `presentation_v2/how/a11-escalation/slide.html` — L3 rail, ranked 3-option hierarchy, policy provenance, board-filter loop-back (US5.S4 / US10; richest design).
- `presentation_v2/how/a12-marketplace-grid/slide.html` — 12-agent "registry file", 6 archetypes, shipped/proposed encoding, in-card pairing (US6.S5).
- `presentation_v2/how/a13-agent-resume/slide.html` — one-agent "resume artifact", sample output + paired-checker report, interview footer (US6.S3).
- `presentation_v3/how/s8b-hire-dont-install/slide.html` — tighter 7-agent dossier, bracket-tie pairing, self-generation prompt (US6 refined take).
- `presentation_v2/what/a08..a13-*.md` (six files) — authoritative design-intent (L1/L2 outcomes, content locks, verification criteria) behind each slide.
- `presentation_v3/presentation/index.html` — the `:root` design-token block (colors + fonts) every slide depends on; the design-system contract to port.
- `presentation_v2/how/<slide>/brief.collab.md` — per-slide regeneration blueprints (layout rationale, the criterion-10 fix story).
- `presentation_v2/how/<slide>/checker_feedback.md` + `check-*.json` — quality-gate verdicts; a13's `open_questions.md` holds the blocking AWAITING-RUN-LOG question.
- `presentation_v3/narrative.collab.md` — v3 brand/vocabulary lock (Diecast, Layer, cast-* modules) the requirements link as the continuity source.
