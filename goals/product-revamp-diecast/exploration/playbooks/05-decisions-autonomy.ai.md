# Playbook — Decisions & Autonomy Surface (Step 5)

**Goal:** Product Revamp — Diecast Vision Prototype (clickable HTML mockup, spec v0.3.0).
**Step 5 owns:** the trust mechanism for the AI-blackbox posture — how decisions get *recorded*,
*surfaced in context*, *trailed across phases*, and *gated by autonomy* (the L1/L2/L3 reversibility
key shifted by a per-goal dial), and the one clarify-vs-proceed moment each of the four flows must
physically demonstrate.
**Synthesized from:** `research/05-decisions-autonomy.ai.md` (web, 7 lenses) + `steps.ai.md` (Step 5)
+ `refined_requirements.collab.md` (US5, US10; FR-021–023, FR-010, FR-016, FR-017; SC-007).
**Date:** 2026-06-11 · **Stance:** opinionated, one pick per component. This is a *static prototype* —
every recommendation below is something you mock with HTML + scripted CSS state, not something you build.

---

## TL;DR

**The locked model is already correct and fully precedented — your job is not to design it, it is to
make it *visible* with three mockable artifacts and one scripted mechanic.** The three artifacts: a
**decision atom** (an ADR plus two fields — `reversibility_level` and `originating_agent`), an
**in-context decision chip** (the atom rendered *on the thing it changed*), and a **cross-phase
decision trail** (the same atoms as one filterable, diff-first feed). The one mechanic: the
**clarify-vs-proceed clickthrough** — agent hits a judgment call → classifies it L1/L2/L3 → L1 drops a
silent chip, L2 batches into a digest, **L3 stops the agent and raises exactly three pre-framed options
on the board** (the *same* escalation component as US5 — instantiate once, reuse everywhere).

**The whole demo lives or dies on one discipline: keep L3 rare.** Exactly **one** L3 moment per flow
(maybe two), surrounded by mostly-silent L1s and a couple of L2 digest entries. A mocked flow where the
agent asks constantly has *failed the thesis* — it reads as a nagging tool, not a trusted colleague.
The dominant documented failure mode is confirmation fatigue (the "approve-approve-approve" reflex, a
real clickthrough vulnerability), and the reversibility key exists precisely to make the hard stop rare.

**The single best framing to put on every decision card is Amazon's one-way / two-way doors** (Bezos
2015). "Reversible ⇒ decide fast and silent; irreversible ⇒ stop and consult" *is* L1/L2/L3 — decades-
validated, instantly legible, and it makes the autonomy story feel principled rather than arbitrary.

**The autonomy dial is one CSS toggle, not a feature.** It is a three-position segmented control
(Conservative / **Balanced** / Autonomous) that re-keys the *same* reversibility engine — it shifts
where the L-thresholds sit. Mock it as a scripted state flip: move it from Balanced to Conservative and
watch one L2 "quiet digest" decision visibly promote into a "stop-and-confirm" card. Frame the dial as
*earned trust* (a "99.4% compliance across 312 runs" tooltip wired to the same fake stat the
marketplace shows), not as a risk knob — that is more honest and more compelling.

**Do not invent a fourth surface, a confidence meter, or a meta-decision log.** The research is
explicit: ~5–8 real decisions per goal is the legible target; 40 is audit theater. Log *judgment
calls*, never *steps* — the execution firehose belongs behind the HOW tab (US3), the curated "why"
belongs in the trail.

---

## Recommended Stack

Opinionated picks for *mocking* decisions & autonomy in a static prototype. "Build" below means
HTML/CSS/JS scripting, not real systems.

| Component | Pick | Why this, not the alternative |
|-----------|------|-------------------------------|
| **Decision record schema** | **ADR shape + `reversibility_level` + `originating_agent` + `influenced[]` PROV link** | The ADR (context/options/decision/rationale/consequences) already contains every field US10 wants; it is the field-proven primitive and reads as legible to anyone who's seen one. Inventing a bespoke schema buys nothing and loses portability. |
| **Autonomy key** | **Reversibility (L1/L2/L3) = Amazon one-way/two-way doors** | The *only* property that intrinsically determines how much a human should care is what a decision can't undo. Confidence, cost, and phase are weaker keys — reversibility is first-principles correct and decades-validated. |
| **In-context surface** | **Decision chip anchored to the artifact's stable element ID** (same ULID backbone as comments, Step 4) | "Rationale reachable without leaving the primary screen" is the XAI consensus. A chip on the element it shaped is recognition-in-flow; a separate decisions page is not. Decisions are a *third consumer* of one identity backbone — design the anchor once. |
| **Cross-phase surface** | **One filterable, diff-first trail per goal** (`time · phase · ⚖badge · title · who · [diff]`) | Audit logs "humans actually read" are diff-first (`feature → bug`), not prose blobs, and filterable by phase/actor/reversibility. This is the same any/human/agent filter as the board (FR-010), applied to history. |
| **Disclosure model** | **Three layers: badge → popover → full record** | Mirrors the WHAT/HOW split (US3). Default = one-line what + reversibility badge; click = rationale + options + revisit-if; deepest = originating run. Keeps decision records from competing with the WHAT for attention. |
| **Autonomy control** | **Three-position segmented control with a plain-language legend** (Conservative / **Balanced** / Autonomous) | Best-in-class dials are *policies that move thresholds*, not nag-frequency knobs (Claude Code Auto mode is the proof). Three positions + a teaching legend is the minimum that reads as graduated trust. A numeric slider would imply false precision. |
| **L3 escalation component** | **Reuse the US5 escalation rail — one component, two instantiations** | US10 Scenario 4 and US5 Scenario 4 are the *same* mechanism (stop agent, three pre-framed options on the board). Authoring a second escalation UI is duplicated work and inconsistent chrome. Instantiate at execution (US5) and other phases (US10). |
| **L2 notify component** | **A batched digest roll-up** ("3 decisions made while you were away"), non-modal, each row expandable | Reuse the same digest atom as US7's "requirements updated from planning" write-back notice — both are inform-without-nagging surfaces. One toast per decision is the canonical failure; batching is +35% engagement / −28% opt-outs in the literature. |
| **Decision IDs / fake-data spine** | **`DEC-CAST-412-03` on the canonical Northwind/CAST-### spine** | Reuse the locked fake-data spine (org Northwind, CAST-### tickets, crud-orchestrator, M04/S03/R02) so the trail feels like one product, not disconnected mocks (FR-018). |
| **Implementation technique** | **Scripted CSS-state clickthrough** (data-attributes + a tiny scenario script), no real classifier | The entire clarify-vs-proceed mechanic is a deterministic, pre-authored sequence. A real reversibility classifier is out of scope (FR-001); the dial toggle is a CSS state that re-labels which decisions are "asked" vs "auto." |

---

## Implementation Steps

Ordered by dependency, not by impact. Effort is *prototype-build* effort (HTML/CSS/JS), assuming the
Step 4 stable-ID anchoring and the US5 escalation component already exist as siblings.

### Step 1: Lock the decision atom as fake-data, not a schema
**Impact: High** | **Effort: ~2–3 hours**

Author the decision records as a small JSON array in the prototype's fake-data spine — one coherent set
keyed to the Northwind / CAST-### story. This is the source every chip and every trail row reads from,
so it must be written *first* and stay internally consistent across screens.

```js
// fake-data/decisions.js  — ~5–8 records per goal, NOT 40
{
  id: "DEC-CAST-412-03",
  goal_slug: "northwind-rbac",
  phase: "execution",                       // requirements | exploration | planning | execution
  title: "Classify CAST-412 as bug, not feature",   // one line, imperative
  reversibility: "L2",                      // L1 | L2 | L3  — drives the badge AND the autonomy gate
  rationale: "Repro is a regression from the v4.2 RBAC migration, not new scope.",
  options_considered: [                     // >=2; for L3, exactly 3 are surfaced
    { option: "Treat as feature", consequence: "New FR + estimate", chosen: false },
    { option: "Treat as bug",     consequence: "Hotfix lane, no re-scope", chosen: true }
  ],
  consequences: "Routes to debug-loop canvas; skips planning re-estimate.",
  revisit_if: "If the regression bisect lands outside the migration commit range.",  // the ADR trip-wire
  originating_agent: "cast-crud-orchestrator",
  author_type: "agent",                     // agent | human
  timestamp: "2026-06-11T14:22:00Z",
  status: "recorded",                       // recorded | awaiting_human | superseded
  supersedes: null, superseded_by: null,    // reversals are NEW records, never edits
  spike_ref: null,                          // FR-016 linkage when a spike settles it
  influenced: ["req-elem-FR-014", "canvas-stage-classify"]  // PROV: what this shaped → drives the chip
}
```

Two non-obvious fields earn their place: **`revisit_if`** (the trip-wire that makes the agent's
autonomy honest — it isn't claiming certainty, it's stating what would reopen the call) and
**`influenced[]`** (the PROV link that makes the chip *automatic* — render the decision wherever its
influenced-artifact renders).

### Step 2: Render the in-context decision chip with layered disclosure
**Impact: High** | **Effort: ~3–4 hours**

For each `influenced` artifact ID, render a small chip inline: `⚖ Decided: classification feature→bug · L2`.
The reversibility badge is colour-coded (L1 muted/grey, L2 amber, L3 red). Clicking opens a popover —
*not* a navigation — showing rationale + options-considered + revisit-if, with an "open full record →"
link into the trail focused on that decision.

```
[ ⚖ classification: feature → bug · L2 ]        ← chip, inline on the requirements element / canvas stage
        │ click
        ▼
 ┌─ popover ───────────────────────────────┐
 │ Why: regression from v4.2 RBAC migration │
 │ Considered: feature (re-scope) /         │
 │             bug (hotfix lane) ✓           │
 │ Revisit if: bisect lands outside the     │
 │             migration commit range        │
 │ by cast-crud-orchestrator · 14:22         │
 │                       [ open full record →] │
 └──────────────────────────────────────────┘
```

Chips must appear on **all three** anchor types to prove generality: a requirements element (US7), a
canvas stage (US1), and ticket CAST-412's activity log (US5). Same record, three projections.

### Step 3: Build the cross-phase decision trail
**Impact: High** | **Effort: ~3–4 hours**

One per goal, a filterable feed. This is the "reconstruct after the fact" surface to the chip's
"recognise in flow." Make it **diff-first** — the scan-line is the field diff, not a prose paragraph.

```
Filter:  [ all phases ▾ ]  [ any · human · agent ▾ ]  [ L1 · L2 · L3 ▾ ]  [ status ▾ ]

time   phase        ⚖   title                                  who                  diff
14:22  execution    L2  Classify CAST-412 as bug               cast-crud-orch       classification: feature → bug
13:05  planning     L1  Split FR-014 into routing + recording  cast-detailed-plan   FR-014 → FR-014a, FR-014b
11:40  exploration  L3  RBAC migration drops legacy column     @sj (resolved)       migration: additive → drop+snapshot
09:18  requirements L1  Chose REST over GraphQL for RBAC API    cast-refine-reqs     api-style: — → REST
```

Two behaviours the trail must show: **superseded decisions struck-through with a link to what replaced
them** (the product visibly "changing its mind, with reasons"), and the **actor filter matching the
board's** any/human/agent (FR-010) — the same filter applied to history, not a new vocabulary.

### Step 4: Mock the autonomy dial as a scripted state toggle
**Impact: High** | **Effort: ~2–3 hours**

A per-goal segmented control with a teaching legend. The legend *is* the documentation — it teaches the
model in one screen.

```
Autonomy:  [ Conservative ]  ( ● Balanced )  [ Autonomous ]
           ↑ agents ask more       ↑ default        ↑ agents act more, record after

Conservative — even reversible-but-notable (L2) calls pause for your OK. Best for a new goal/agent.
Balanced     — decide & record routine (L1), notify on notable (L2), stop to ask on irreversible
               (L3, three options).                                    (recommended default)
Autonomous   — handle L2 silently, self-decide some L3s for proven agents, record everything for review.

  ⓘ This goal's agents have a 99.4% compliance record across 312 runs.   ← earned-trust tooltip
```

Wire the credibility tooltip to the *same* fake stat the marketplace shows on agent resumes (US6) — the
dial's right edge unlocking is a *reward* for a track record, not a risk the user toggles blindly.

### Step 5: Script the clarify-vs-proceed mechanic (the core demo beat)
**Impact: High** | **Effort: ~4–6 hours**

The one mechanic that must be *demonstrated, not described* (SC-007). A scripted, CSS-state
clickthrough: the canvas shows the agent reaching a judgment call → a banner promotes the L3 to the
WHAT level (the user never polls the execution tab to discover they're blocked — US3 Scenario 3) → the
escalation card slides in with **exactly three** option buttons, each carrying its consequence → clicking
one resolves the stop, drops a decision chip onto the artifact, and writes a row into the trail with
`author_type: human`.

```
Agent reaches a judgment call
   │ classify reversibility
   ├─ L1 ─► decide ─► silent chip ─────────────────────────► continue
   ├─ L2 ─► decide ─► add to digest ("3 made while away") ──► continue   (batched, non-modal)
   └─ L3 ─► STOP ─► raise escalation card at WHAT level:
                     • evidence pack (what I want / what I tried)
                     • exactly 3 pre-framed options + consequence each
                     • revisit-if / spike option · "expires in 1h → falls back to @teammate"
                     └─ human picks ─► becomes a recorded decision (author=human) ─► chip + trail row
```

The escalation card carries an **evidence pack** (what the agent wants + what it tried) — the research's
single most actionable finding: with a complete evidence pack, the human decides in **10–30 seconds**,
not minutes. Do not offer a pre-highlighted "recommended — just hit OK" default; that invites the
rubber-stamp reflex. Three distinct options with three distinct consequences force a real, brief choice.

### Step 6: Mock the L2 digest roll-up
**Impact: Medium** | **Effort: ~2 hours**

A non-modal, glanceable informer on the canvas/goal surface: **"⚖ 3 decisions made while you were
away"**, each row expandable to its record. This is the difference between "the agent kept me informed"
and "the agent wouldn't stop pinging me." Reuse the *same* component as US7's downstream write-back
notice — both are the inform-without-nagging atom.

### Step 7: Show the "should've asked" correction loop (one click)
**Impact: Medium** | **Effort: ~1–2 hours**

The one real risk the prototype should concede and answer: reversibility classification is itself a
judgment the agent can get wrong. In the L2 digest, give any decision a one-click **"should've asked"**
promotion. Mocked, this does two visible things: corrects the record *and* nudges the agent's track-
record stat — making the human's oversight *productive* (it trains future classification), not
janitorial. One scripted instance is enough; don't over-build it.

### Step 8: Wire one L3 moment into each of the four flows
**Impact: High** | **Effort: ~3–4 hours** (mostly content, the component is reused)

Instantiate the Step 5 mechanic once per flow with the locked, on-brand content below. **One L3 per
flow** — resist adding more. Each L1/L2 is a thin chip/digest entry; the L3 is the scripted stop.

---

## Architecture / Surface Map

```
                         ONE decision atom (ADR + reversibility + originating_agent + influenced[])
                                              │
                 ┌────────────────────────────┼────────────────────────────┐
                 │                             │                            │
         (a) IN-CONTEXT CHIP            (b) CROSS-PHASE TRAIL        (c) AUTONOMY GATE
         render on influenced[]         list by time, diff-first      reversibility × dial
                 │                             │                            │
        ┌────────┼────────┐            filter: phase/actor/L/status   ┌─────┼─────────┐
   req elem  canvas stage  ticket           (= board filter)        L1     L2        L3
   (US7)     (US1)        (US5)                                    silent  digest   STOP→escalation
        │        │          │                                       chip   roll-up   rail (US5 reuse)
        └─ layered disclosure: badge → popover → full record ─┘                         │
                                                                          3 pre-framed options + evidence pack
                                                                          → human picks → new atom (author=human)

   Autonomy dial [Conservative · ●Balanced · Autonomous]  shifts WHERE L1/L2/L3 thresholds sit
        (Conservative ↑ : L2 stops too) ────── re-keys the SAME engine ────── (Autonomous ↓ : L2 silent, some L3 self-decide)

   SIGNAL DISCIPLINE per goal:  ~5–8 atoms total · mostly L1 · a couple L2 · EXACTLY 1 (max 2) L3
   PROVENANCE FILTER:  log judgment calls (reasoning) → trail.  steps (execution) → HOW tab (US3).
```

---

## The four locked L3 moments (hand these to the build step as demo beats)

| Flow | L1 (silent chip) | L2 (record + digest) | **L3 (ask-first, exactly 3 options)** | Lands on |
|---|---|---|---|---|
| **New feature** (CAST-412) | "Chose REST over GraphQL for the RBAC endpoint — matches existing API surface." | "Split FR-014 into routing + recording." → digest | **"The RBAC migration drops the legacy `roles` column — irreversible on prod data. (a) additive migration, keep column 90 days; (b) drop now with a backup snapshot; (c) spike a dual-write window first."** | CAST-412 + trail |
| **Bug fix / debug loop** | "Ruled out hypothesis A (cache) — repro persists with cache off." (iter 1/3) | "Switching repro from unit to integration harness." → digest | **"Root cause is in shared `auth` middleware; the fix changes behaviour for 4 other services. (a) narrow fix behind a feature flag; (b) fix middleware + notify owners; (c) escalate to the auth team."** | debug canvas + trail (L1s show as iteration history, FR-007) |
| **Spike / quick conclusion** | "Time-boxed the latency spike to 2h; measuring p95 only." | "Spike inconclusive at 2h — extending once to 3h." → digest | **"Spike shows the vendor SDK adds 180ms p95 (budget 200ms) — borderline; this gates the feature's go/no-go. (a) proceed, accept 180ms; (b) self-host the call; (c) renegotiate the budget with @you."** | conclusion artifact `spike_ref`'d by the decision (US2 S3 / FR-016) — the clearest `revisit_if` → spike link |
| **Data analysis / research** | "Excluded 1.2% null-region rows from the cohort — documented in method." | "Chose median over mean for the skewed latency set." → digest | **"Two sources disagree on Q2 revenue by 8%; the chart's headline depends on which I trust. (a) use source-of-record (finance DB); (b) show both with a reconciliation note; (c) flag for analyst review before publishing."** | drives which visualized output renders (US2 S4 / FR-009) |

**The cross-cutting beat:** in the feature flow, *toggle the dial* from Balanced → Conservative and show
the L2 "split FR-014" decision flip from a quiet digest entry into a stop-and-confirm card — SC-007's
"at least one autonomy-gated clarification moment," shown live, proving the dial re-keys the engine.

---

## Key Decisions

| Decision | Recommendation | Rationale (and the trade-off) |
|----------|---------------|-------------------------------|
| What keys autonomy? | **Reversibility (L1/L2/L3), not confidence or cost** | First-principles: what a decision can't undo is the only property that intrinsically sets how much a human should care. Confidence is a useful *secondary* flag, not the key. Trade-off: agent must classify reversibility — answered by Step 7's correction loop. |
| How many surfaces? | **Exactly two: chip + trail** (same atoms, two projections) | One PROV link (`influenced[]`) yields both automatically. A third surface is excess; a single surface loses either recognition-in-flow or after-the-fact reconstruction. |
| Escalation: new or reuse? | **Reuse the US5 rail, one component** | US10 S4 and US5 S4 are the same mechanism. Two components = inconsistent chrome and double the build. Trade-off: must coordinate with Step 4 (board/ticket chrome owner). |
| L2 notification shape | **Batched digest, never per-decision toast** | Per-decision toasts are *the* canonical fatigue failure. Batching is +35% engagement in the literature and reads as a colleague, not a pager. Trade-off: a decision sits unseen until the user glances — acceptable for L2 (reversible-but-notable). |
| Dial granularity | **Three named positions, not a numeric slider** | Three teach-by-legend positions map cleanly to progressive-autonomy (Audit/Assist/Automate). A slider implies false precision and has no legible labels. |
| Dial framing | **Earned trust (track-record stat), not risk tolerance** | Honest *and* compelling: the right edge is a reward for reliability, wired to the marketplace stat (US6). Framing it as a risk knob makes Autonomous feel reckless rather than proven. |
| What gets a record? | **Judgment calls only (~5–8/goal), never steps** | Reasoning-vs-execution provenance distinction. Logging steps produces audit theater no one reads. Trade-off: the line is itself a judgment — default to *under*-logging; the HOW tab holds the firehose. |
| Reversals: edit or supersede? | **Supersede — decisions are immutable; a reversal is a NEW record linking back** | Preserves the history of thinking (ADR practice). The trail then literally shows the product changing its mind, with reasons — the core "trust the blackbox without losing the why" payoff. |
| L3 frequency budget | **Exactly one per flow (max two)** | The thesis-defining discipline. More L3s actively damage the demo (nagging tool, not colleague) and train the rubber-stamp reflex. A hard, enforced budget. |
| Show the meta-decision (why L3)? | **No, by default** | Recording *why* the agent judged something L3 is a real flourish but clutters the curated trail. Keep the trail at ~5–8 legible atoms; only surface a meta-decision if one specific flow visibly benefits. |

---

## Pitfalls to Avoid

1. **Asking too often (confirmation fatigue).** The instinct is "more asking = more accountability."
   It is *backwards* — an L3 that fires constantly trains the human to approve-approve-approve and
   rubber-stamp the one that mattered. If a mocked flow shows the agent asking more than once or twice,
   it has failed the thesis. Budget L3 hard: one per flow.

2. **The pre-highlighted "recommended" option.** Offering three options with one pre-selected "just hit
   OK" defeats the purpose — it invites the reflex the L3 exists to prevent. Make the three options
   *equally weighted* with *distinct consequences* so the human engages briefly and genuinely.

3. **Logging every step (audit theater).** A trail with 40 entries for one goal is wrong — no human
   reads it, and it defeats the entire feature. Log *judgment calls between live alternatives*, not "ran
   the test suite." The execution firehose belongs behind the HOW tab (US3); ~5–8 curated atoms is the
   legible target.

4. **Prose-blob trail rows.** A decision trail of paragraph descriptions is unscannable. Lead with the
   **field diff** (`classification: feature → bug`), keep rationale one click away. Diff-first is the
   difference between an audit log humans read and one they ignore.

5. **Per-decision toast spam for L2.** Firing one notification per L2 decision is the canonical
   notification-design failure. Batch into a digest roll-up. The information is identical; the
   interrupt-cost of N toasts vastly exceeds one digest of N items.

6. **A second, inconsistent escalation UI.** Authoring a separate L3 escalation component for US10 when
   US5 already has one yields divergent chrome and vocabulary across the demo — exactly what FR-010's
   "continuous chrome and canonical vocabulary" forbids. Instantiate the one rail twice.

7. **Editing decisions in place.** Mutating a decision when it's reversed destroys the history of
   thinking and breaks the "watch the product change its mind" payoff. Supersede with a new linked
   record; render the old one struck-through.

8. **The dial as a nag-frequency knob.** If the dial just changes *how often* the agent pings, it's a
   gimmick. It must *re-key the reversibility engine* (shift where L-thresholds sit) and be framed as
   earned trust. Mock the threshold shift visibly (an L2 flipping to a stop) or the dial means nothing.

9. **Open-ended "what should I do?" escalations.** Handing the human an unframed question offloads the
   framing work back onto them — the exact thing the product exists to do *for* them. Always exactly
   three pre-framed options, each with its consequence and an evidence pack.

10. **Disconnected fake data across surfaces.** If the chip on CAST-412, the trail row, and the digest
    entry don't refer to the *same* decision with the *same* ID and rationale, the prototype reads as
    disconnected mocks. Author the decision atoms once in the shared spine (Step 1) and read every
    surface from it.

---

## Success Metrics

- **L3 rarity (the thesis metric):** exactly **1** hard-stop L3 moment per flow (max 2); verified by a
  per-flow count. More than two in any flow is a fail.
- **Trail legibility:** **5–8** decision atoms per goal, every row diff-first; zero prose-only rows.
- **Two-surface coverage:** every demonstrated decision appears as **both** an in-context chip *and* a
  trail row, reading from one shared record — verified by ID match across surfaces.
- **Anchor generality:** chips demonstrated on **all three** anchor types (requirements element, canvas
  stage, ticket) to prove the model isn't execution-only.
- **Autonomy demo (SC-007):** at least **one** live dial toggle visibly flips a decision's treatment
  (L2 digest → stop-and-confirm) — the autonomy-gated clarification moment, shown not described.
- **Decision-in-context (SC-007):** every one of the four flows shows **≥1** in-context decision record
  (rationale + time) — walkthrough check across all four.
- **Escalation speed signal:** every L3 card carries a complete evidence pack (what I want / what I
  tried) + three consequences — the "decide in 10–30s" shape, verified by card content.
- **Reuse integrity:** **one** escalation component instantiated for both US5 and US10; **one** digest
  component for both L2 notices and US7 write-back — verified by no duplicate components.

---

## Impact Rating: 9/10

**Justification:** Decisions & autonomy (US10, P1) is the trust mechanism on which the entire
AI-blackbox posture rests — the spec's product posture #5 and SC-007 both hinge on it, and "done wrong
it's either nagging or unaccountable" is the make-or-break of the whole vision. It scores a 9 rather
than 10 only because the *model* is already locked and well-precedented (this step's leverage is
execution craft, not invention) and because the surfaces ride on dependencies owned elsewhere — the
Step 4 stable-ID anchor and the US5 escalation rail. Get the L3-rarity discipline and the diff-first
trail right and this is the surface that makes a viewer say "this is a colleague I can trust," not "a
tool that won't stop asking"; get it wrong and it sinks the blackbox thesis the prototype exists to sell.

---

## Hand-offs to later steps

1. **Decision identity rides the Step 4 / Step 7 stable-ID backbone.** Chips anchor to the same element/
   artifact surrogates that comments and round-trip provenance use — decisions are a *third consumer* of
   one identity system. Design the anchor once; do not invent a decisions-only ID scheme.
2. **The L3 rail IS the US5 escalation rail.** Coordinate with Step 4 (agents-as-colleagues, board/ticket
   chrome owner): render *one* escalation component, instantiated at execution (US5) and other phases (US10).
3. **The L2 digest IS US7's write-back notification.** One digest/notification component serves both the
   L2 decision notices and the "requirements updated from planning" notice — coordinate with the Step 4
   annotation playbook.
4. **The dial's credibility tooltip IS the US6 marketplace stat.** Wire "99.4% compliance across 312
   runs" to the same fake stat the marketplace shows on agent resumes, so earned-trust framing is
   consistent across surfaces.
5. **Hand the four scripted L3 moments to the build step as locked demo beats.** Resist adding more —
   the L3 budget is a hard design constraint, not a guideline.
