# Step 4: Agents as Colleagues, Not Tools — Playbook

> Synthesis of Research Note 04 (web: AI-teammate / marketplace / board craft) + Code
> Exploration 04 (preso v2/v3 board-arc, marketplace, résumé assets) into an opinionated,
> buildable design brief for the agent-colleague surfaces (US5, US6, US8, US9, US10).
> This is the **screen-design step**: it does not gather more references, it *decides what the
> mockup builds and what it throws away*. Every later build step executes from the verdicts here.
> **Agent:** cast-playbook-synthesizer · **Date:** 2026-06-11 · **Status:** ai
> **Framing (locked):** VISION-FIRST. Existing assets are terrain, not anchor. The preso slides
> are high-fidelity *mockups to lift the visual spec from*, never source code to keep.

---

## TL;DR

**Don't redesign these surfaces — re-author them.** The preso v2/v3 board arc (a08→a11) and
marketplace/résumé slides (a12/a13/s8b) are a near-complete, vocabulary-consistent, tone-compliant
screen-level design for US5 and most of US6. The entire colleague thesis collapses to **one
recurring visual unit — the five-element colleague-card lockup** (agent avatar + glyph · paired-checker
lockup · rework-budget meter · reversibility badge · in-flight pill) — used *identically* across
board, ticket, résumé, and hiring report. Lift the design-token system, the peer-but-distinguishable
avatar grammar, the ranked-options hierarchy, and the in-card pairing verbatim; **discard every
hand-laid SVG screenshot and rebuild as real HTML/CSS** so the assignee filter actually filters and
board→ticket→decision→escalation is four navigable screens with continuous chrome. The single
highest-leverage insight: the preso made agents *look* like colleagues with static SVG; the prototype
must make them *behave* like colleagues with real DOM — and the accountability triad (paired checker +
rework budget + reversibility gate) is what *earns* the peer-assignee seat that Linear deliberately
refuses to grant. The one greenfield concentration is the **hiring-funnel middle** (assessment →
federation → stack-ranked report → onboard); the marketplace and résumé endpoints already exist, the
flow between them does not.

---

## Recommended Stack / References

One opinionated north-star and one liftable pattern per surface. No "you could also use" — these are
the picks, drawn from where the seven research angles and the code terrain agree.

| Surface | North-star reference | What to lift (exact) | Why this over the alternative |
|---------|---------------------|----------------------|-------------------------------|
| Shared board (US5.S1) | **Linear board + GitHub agents panel** | preso **a08/s8a**: assignee-type filter chips `any·human·agent·checker`; peer-avatar grammar (human=solid `fill-text`, maker=outline, checker=accent dot) | Agents in the *same* assignee stack, not an "Automations" tab — the single most common CRUD-collapse |
| Ticket activity log (US5.S2, US4.S3) | **CodeRabbit / Greptile inline PR review** | preso **a09**: maker-checker conversation log, checker-speaks highlight band, rule codes M04/S03/R02, **rework meter 1/3** | A reviewable record, not a green/red pass-fail badge (US4.S3 forbids the badge) |
| Decision + escalation (US5.S3/S4, US10) | **ADR record + L3 propose-and-approve UX** | preso **a10/a11**: 5-field decision card, reversibility badge, **ranked 3-option rail** (hero A / outline B / ghost C) | Three pre-framed reversibility-keyed options on the board, not a generic Approve/Reject modal |
| Hiring funnel (US6.S1-4) | **Google structured-hiring packet + LMArena side-by-side + eval-kit radar** | *greenfield* — assessment matrix, federation fan-out, stack-ranked report card, onboarding checklist | An eval report card deep-linked to real produced work, not a SaaS feature/pricing grid |
| Marketplace + résumé (US6.S3/S5) | **Apify Actor store + A2A Agent Card** | preso **a12/a13/s8b**: "registry file" grid, track-record stat line, health badge, in-card pairing, "résumé artifact" detail | A track record (credibility), not a capabilities/config listing (a plugin, not a colleague) |
| Skill ops + catalogues (US8, US9) | **Backstage catalog + Roadie scorecards + LangSmith traces** | service-grade ops page: version history (SHA-pinned), scorecard, trace/metrics dashboard, unified public/private browser | Agents *operated like services*, not an agent "settings" page of toggles |
| Design system (all) | **cast-preso-visual-toolkit** | `:root` token block from `presentation_v3/presentation/index.html`; IBM Plex Mono + DM Sans; one-accent (`#D6235C`) opacity-as-hierarchy | A working, FR-018-compliant token system already exists — porting it is hours, reinventing is days |

---

## Implementation Steps

Ordered by dependency, not impact. The foundation (Steps 1-2) unblocks everything; the board arc
(3-6) is the highest-value reuse; the hiring middle (7) is the greenfield concentration; ops/Layer-2
(8) is the lowest-priority breadth.

### Step 1: Port the token system + build the colleague-card component
**Impact: High** | **Effort: ~0.5 day**

Lift the `:root` design-token block from `presentation_v3/presentation/index.html` verbatim and load
both web fonts. Then build the **five-element colleague-card lockup** as a single reusable component —
this is the visual thesis and it recurs on board, ticket, résumé, and hiring report, so it must be one
component or the set drifts.

```css
:root{
  --color-bg:#F5F4F0; --color-surface:#ECEAE4; --color-accent:#D6235C;
  --color-text:#1A1A28; --color-muted:#4A4860;
  --color-callout-bg:rgba(214,35,92,0.06); --color-callout-border:var(--color-accent);
  --color-question-bg:rgba(74,72,96,0.06); /* muted-tint annotations */
  --font-mono:'IBM Plex Mono','SF Mono','Fira Code',monospace; /* identity */
  --font-body:'DM Sans',system-ui,sans-serif;                  /* prose */
}
```

```html
<!-- the recurring lockup; render IDENTICALLY everywhere an agent acts -->
<article class="colleague-card" data-state="working">
  <span class="avatar agent" data-glyph="hex">CO</span>      <!-- maker, outlined+glyph -->
  <span class="avatar checker paired">CC</span>              <!-- paired-checker, never a 2nd card -->
  <span class="rework-meter" data-used="1" data-budget="3"></span> <!-- 3-segment, fills on iterate -->
  <span class="chip reversibility" data-level="L2">L2</span>
  <span class="pill inflight">crud-orchestrator · iteration 2/3</span>
</article>
```

Avatar grammar (the single most important "colleague" device): **human = dense `fill-text` circle ·
maker agent = outlined circle + subtle hex glyph · checker agent = accent-filled circle.** Same size,
same row, same card — parity — instantly role-readable. Build it once as `.avatar.{human|agent|checker}`.

### Step 2: Reconcile the fake-data spine into one coherent org
**Impact: High** | **Effort: ~0.5 day**

The preso played the spine loose (CAST-412 is "Add Postgres index" on the board but "Create Invoice
entity + CRUD stack" inside the ticket). Harmless in a deck, *jarring* in a clickable board→ticket
path. **Pick the Invoice CRUD stack (richest) and propagate it through every frame.** Lock the spine
as a single JSON the whole prototype reads from:

```js
const SPINE = {
  ticket: { id:'CAST-412', title:'Create Invoice entity + CRUD stack', status:'done', rework:'1/3' },
  agents: { CO:'crud-orchestrator', EC:'entity-creation', CC:'crud-compliance-checker', DA:'decision-agent' },
  human:  { handle:'@you', initials:'SJ' },
  rules:  { M04:'convention drift — SoftDeleteMixin missing', S03:'typing too permissive — Optional[Any]', R02:'missing index on FK' },
  iter:   ['10:02 CO picks up','10:11 EC v1','10:13 CC posts M04/S03/R02 → needs_work','10:17 EC v2','10:19 CC approves 5/5 → PR #2341'],
  escalation: { id:'CAST-417', title:'DROP table user_events', level:'L3', options:['A PROCEED SAFELY','B PRESERVE QUO','C DEFER TO SPIKE'] },
};
```

Standardize on **reversibility-keyed L1/L2/L3** (L1 decide-and-record / L2 decide-record-notify / L3
ask-first, per FR-022) and drop the preso's conflicting "decision-weight" gloss of L3 (the a11 brief
dual-use). Fill a13's three `AWAITING RUN LOG` placeholders with plausible fake numbers (FR-019) — do
not ship the honesty-placeholder chip into a polished mockup.

### Step 3: Build the shared board with a *working* assignee filter
**Impact: High** | **Effort: ~1 day**

Re-author a08/s8a as real DOM: four columns (Backlog / In progress / In review / Done), agents and
humans in the **same avatar stack** distinguished only by the glyph/ring, and a filter chip row
`Any · Human · Agent · Checker` that actually filters cards (the SVG version was decorative). Put the
in-flight pill on the card so an agent at work is visible without opening the ticket, and an escalation
inbox badge (`@you · 1`) top-right so blocked work surfaces at board level (US3.S3). Header framing
line: **"Publishes INTO your PM tool. It does not replace Linear / Jira / GitHub Projects."**

```js
chips.forEach(c => c.onclick = () => {
  document.querySelectorAll('.ticket-card').forEach(card =>
    card.hidden = c.dataset.type !== 'any' && card.dataset.assigneeType !== c.dataset.type);
});
```

### Step 4: Ticket activity log as a reviewed-PR thread + rework meter
**Impact: High** | **Effort: ~1 day**

Re-author a09 — the strongest single screen. Render the activity log as a **reverse-chronological
reviewed-PR thread**: each checker finding is an inline comment anchored to the artifact line, tagged
with its rule code (M04/S03/R02), a **severity**, and a **confidence** (lifted from Greptile); the
maker's revision threads beneath. Group by **iteration band** ("Iteration 1 → 2 findings; Iteration 2
→ 0, passed") so repeat passes are first-class history (FR-007). Header carries the maker-checker
paired-avatar lockup + the **3-segment rework meter** (the dramatic Diecast-original element). Footer:
the resulting PR link, and the escalation hand-off if the loop hit budget. Show the compliance
*checklist* (rules checked, passed/flagged inline) — never a lone pass/fail badge (US4.S3 hard rule).

### Step 5: Decision artifact + L3 escalation rail
**Impact: High** | **Effort: ~1 day**

Re-author a10 + a11. The decision card is an ADR rendered for agents: id, **reversibility badge**,
decision, rationale, timestamp, originating phase/agent, consequences, `spike_ref` link. The
escalation rail is the field-standard L3 propose-and-approve, made concrete: when a decision is L3 the
agent **stops** and hands `@you` **exactly three pre-framed option cards on the same board** — encode
rank as structural weight, never three equal cards (the a11 checker explicitly failed equal cards):

```
┌──────────────────────────┐  ┌─────────────────┐  ┌·················┐
│ A  PROCEED SAFELY     ◆   │  │ B PRESERVE QUO  │  : C DEFER TO SPIKE :
│ accent-filled, taller,    │  │ outline,        │  : ghost / muted,   :
│ white text · RECOMMENDED  │  │ regular weight  │  : reduced opacity  :
│ "consequence line…"       │  │ "consequence…"  │  : "consequence…"   :
└──────────────────────────┘  └─────────────────┘  └·················┘
```

Add the **decision trail** (US10.S4): a per-goal cross-phase timeline of decision cards
(requirements → exploration → planning → execution), and **in-context decision chips** (US10.S3) that
surface the relevant decision in place on the canvas/ticket and expand to the full card. Show the
policy-provenance line (`policy: decisions/…escalation-policy.md` — "auditable, not LLM judgment").

### Step 6: Marketplace grid + agent résumé
**Impact: High** | **Effort: ~1 day**

Re-author a12 (registry-file grid: 12 hires, 6 archetype facets, shipped=solid / proposed=dashed
encoding, **in-card pairing** `→ paired: <checker>`) and a13 (résumé artifact: role · I/O contract ·
autonomy level · paired checker · benchmark radar · sample output · track-record panel). Each card
carries the canonical credibility stat line (**"99.9% compliant in 2 maker-checker loops across 505
runs"** — Apify's success-rate restated in maker-checker vocabulary) and a freshness/health badge
(active / checker-flagged / benched). The résumé detail page = A2A Agent Card as a Diecast superset
(autonomy level + paired checker + benchmark are the native additions). Identity is always one click
away: **every agent avatar anywhere links to its résumé.**

### Step 7: Build the hiring-funnel middle (the greenfield concentration)
**Impact: High** | **Effort: ~1.5 days**

a12/a13/s8b give the marketplace and résumé *endpoints*; US6's flow *between* them is greenfield. Build
it as a 5-step wizard, each step a distinct screen:

1. **Commission assessment** — a tunable **dimension matrix** (user scale, internal/external software,
   …), not a blank form. Frames "we test them on *your* problem."
2. **Federation** — a live "casting to 5-10 candidates" screen; candidate avatars light up as each
   completes (the eval fan-out made visible).
3. **Stack-ranked hiring report (centerpiece)** — a leaderboard; each row expands to a candidate panel
   with a **per-dimension radar chart**, numeric score, judge-style pros/cons, and **deep links to the
   actual output the candidate produced** (US6.S2). A head-to-head toggle compares the top two outputs
   side-by-side (LMArena). The deep-link-to-real-work is the credibility keystone — lean all the way in.
4. **Hire** — one decisive action; the maker-checker pair is hired *together* (the checker is part of
   the hire, never a separate purchase).
5. **Onboard** — point the new hire at the org's data sources and tastes ("connect repo · load style
   guide · set autonomy dial"), framed as ramping a teammate, not an API-key form.

### Step 8: Skill ops + Layer-2 catalogues
**Impact: Medium** | **Effort: ~1 day**

Lowest-priority breadth (US8/US9 are P2). Build the agent ops page as a **service-grade** surface, not
a settings page: version history (each version SHA-pinned, à la Claude plugins), a Backstage-style
ownership line + scorecard (compliance / rework / usage), and a monitoring view = a trace/metrics
dashboard (LangSmith/AgentOps language: compliance-trend, cost/latency, last-N-run sparkline, replay
into the dispatch tree). One **unified discover-and-hire browser** over public (open Diecast modules)
and private (internal tested) catalogues, identical card chrome + a scope badge. Layer-2 proof
surfaces: a 12-contract catalogue, the 8-node agent-chain pipeline viz (refine → decompose → research →
synthesize → plan → detail → orchestrate → run), and a portfolio dashboard (proof by volume).

---

## Architecture / Navigation Flow

The arc is a connected SPA with **continuous chrome** (one shared shell, consistent vocabulary), not
the preso's independent slide jumps. The colleague-card lockup is the shared atom across every node.

```
                ┌──────────── continuous chrome: shared shell + canonical lexicon ────────────┐
                │  (@you · needs_work · rework budget · L1/L2/L3 · spike_ref · escalated-to-me) │
                └──────────────────────────────────────────────────────────────────────────────┘

   ENTRY (scenario chooser)
        │
        ▼
   ┌─ BOARD ──────┐  filter: any·human·agent·checker      ╔═══ colleague-card lockup ═══╗
   │ human+agent  │  in-flight pills · escalation inbox    ║ avatar+glyph · paired-checker║
   │ peer columns │                                        ║ rework-meter · reversibility ║
   └──────┬───────┘                                        ║ badge · in-flight pill       ║
          │ click ticket CAST-412                          ╚═══ recurs on ALL nodes ══════╝
          ▼
   ┌─ TICKET ─────┐  maker-checker reviewed-PR thread
   │ activity log │  rule codes M04/S03/R02 · rework 1/3 · iteration bands · PR #2341
   └──────┬───────┘
          │ M04 "next › decision"          ▲ decision pulled out of the log
          ▼                                │
   ┌─ DECISION ───┐  5-field ADR card · reversibility badge · spike_ref · co-signed
   │ artifact     │  ─── if L3 ──────────────┐
   └──────────────┘                          ▼
                              ┌─ ESCALATION ─────────────────┐
                              │ ranked 3 options A>B>C        │
                              │ routed @you · policy-file     │
                              │ board filter "escalated to me"│──── loops back to BOARD
                              └───────────────────────────────┘

   HIRING SIDE-ARC (parallel, off the board):
   chat "hire an rbac-agent"
        │
        ▼  assess (dim matrix) ─► federate (fan-out) ─► STACK-RANKED REPORT ─► hire (pair) ─► onboard
                                                          │ radar · pros/cons · deep-link to real work
                                                          ▼
   MARKETPLACE grid (12, 6 archetypes) ──► AGENT RÉSUMÉ (A2A superset) ──► [every avatar links here]

   OPS / LAYER-2 (P2 breadth): agent ops page (versions·scorecard·traces) · unified catalogue ·
                               12-contract catalogue · 8-node chain viz · portfolio dashboard
```

---

## Key Decisions

| Decision | Recommendation | Rationale (and the trade-off) |
|----------|----------------|-------------------------------|
| Peer assignee vs contributor | **Peer assignee** (build the board Linear refuses) | Diecast has the accountability triad Linear lacks (paired checker + rework budget + reversibility gate); the peer seat is *earned* by the triad, shown in-frame. Trade-off: must never show an agent assignee without its triad, or it reads as toy. |
| Reuse vs rebuild the preso surfaces | **Lift the visual spec, rebuild the implementation** | The SVG screenshots look like a product but nothing clicks; the prototype's bar is "IS clickable," which needs real DOM. Keep tokens/grammar/lockups; throw away SVG coordinate geometry. |
| L3 semantics | **Reversibility-keyed only** (drop decision-weight gloss) | The a10/a11 brief uses L3 two ways; FR-022 locks reversibility (ask-first). Standardize to avoid a contradictory mockup. |
| Pass/fail badge vs evidence | **Reviewable record always** | US4.S3 forbids the lone badge; a colleague shows their work. Render the checker's actual findings inline, not a green checkmark. |
| Checker rendering | **Paired in-card, never a separate card** | US6.S5 makes this load-bearing; it visually encodes "quality is a pairing, not a property." Use the s8b bracket-tie as the cleanest pair device. |
| Anthropomorphism dial | **Structure of employment, none of the theater** | Borrow résumé / hiring committee / onboarding / track record; reject mascot faces and "meet your AI employee" cosplay (Angle 6 + FR-018 no-GPT-isms). Credibility = track record, not a smiling avatar. |
| Hiring report shape | **Eval report card, not a pricing grid** | Head-to-head outputs + per-dimension radar + deep links to real produced work. The feature-comparison grid is the explicit death-state. |
| Fake-data ticket scope | **One coherent ticket (Invoice CRUD)** propagated everywhere | The clickable board→ticket path breaks if the title drifts (it does in the preso). Lock one spine JSON. |
| Agent glyph marker | **Subtle hex ring on the avatar** (open item, recommend resolve now) | Must keep agents *in* the human stack (parity) yet be unambiguous; a ring reads at avatar scale without a second color. |

---

## Pitfalls to Avoid

1. **The "Automations" tab.** The single most common way the board collapses into CRUD: relegating
   agents to a separate bots/automations lane. Agents must sit in the *same* columns, *same* assignee
   stack, *same* card format as humans — parity is structural, distinguished only by the glyph.
2. **Cargo-culting the SVG-screenshot decision.** The preso rebuilt every surface as inline SVG to pass
   a "looks like a product" checker for a static deck. The prototype's bar is the opposite — real DOM
   that clicks. Do not copy the SVG geometry; it has zero interactivity by construction.
3. **The lone pass/fail badge.** Replacing the checker's actual findings with a green/red "checker
   passed" badge is explicitly forbidden (US4.S3) and is the fastest way to make an agent read as a tool.
   Show the inline, line-anchored, rule-coded findings.
4. **Three equal escalation cards.** The a11 checker already failed this once. If the three options
   carry no visual ranking, the "recommended path" is lost. Encode rank as structural weight (hero-fill
   A / outline B / ghost C + RECOMMENDED badge).
5. **A pricing/feature-comparison grid for hiring.** Checkmarks across rows is the death-state the spec
   warns about. The report must be an eval report card with deep links to the *actual work* each
   candidate produced — capabilities-without-evidence is a brochure, not an assessment.
6. **A separate card for the checker.** US6.S5 is explicit: a maker's checker is never a separate card.
   Two cards breaks the "maker-checker is the quality unit" thesis. Pair them in-card every time.
7. **An agent avatar that goes nowhere.** Identity must be one click away from anywhere — board,
   activity log, dispatch tree, decision record. An avatar that doesn't open the résumé is a tool icon.
8. **Anthropomorphic mascot theater.** "Ava says hi!", personality avatars, fake faces. Borrow the
   *structure* of employment, never the cosplay. FR-018's no-GPT-isms rule extends to anthropomorphic slop.
9. **Shipping the `AWAITING RUN LOG` placeholders.** a13's honesty-mechanism chips are unresolved
   open-question stand-ins; in a polished mockup (FR-019) fill them with plausible fake numbers instead.
10. **An agent "settings" page standing in for ops.** US8 wants agents *operated like services* —
    versions as history, scorecards, trace dashboards — not a page of toggles and text fields.

---

## Success Metrics

- **Colleague test pass rate:** every agent-bearing screen answers ≥2 of {who is this worker / what did
  they do & why / are they accountable}. Target: **6/6 surfaces pass**; any screen that only answers
  "what are this object's config options" is rejected and redesigned.
- **Lockup consistency:** the five-element colleague-card renders from one shared component on board,
  ticket, résumé, and hiring report. Target: **1 component, 0 divergent copies.**
- **Filter actually filters:** the `any/human/agent/checker` board filter is functional, not decorative.
  Target: **4 working filter states**, each hiding the correct cards.
- **Connected arc:** board → ticket → decision → escalation are navigable as four screens with
  continuous chrome. Target: **3 forward links + 1 loop-back** ("escalated to me" → board) all live.
- **Hiring funnel completeness:** all 5 wizard steps clickable end-to-end with the stack-ranked report
  deep-linking to ≥1 real fake artifact per candidate. Target: **5/5 steps + ≥2 head-to-head outputs.**
- **Vocabulary fidelity (FR-018):** canonical lexicon (`@you`, `needs_work`, rework budget, L1/L2/L3,
  `spike_ref`, `→ paired:`, `escalated to me`) used verbatim; zero em dashes, zero GPT-isms. Target: **100%.**
- **Data-spine coherence:** CAST-412 carries one title/scope across all frames. Target: **0 drift
  instances** on the board→ticket path.

---

## Impact Rating: 9/10

**Justification:** This step designs the surfaces that carry the product's second aha — "Hire. Don't
install." / agents as accountable colleagues — which the goal names as the thing that dies if it looks
like admin CRUD (steps.ai.md Step 4). It is also the highest-leverage *reuse* in the entire goal: the
board arc and marketplace/résumé are already designed, vocabulary-consistent, and tone-compliant, so
the prototype inherits a near-complete screen set and concentrates net-new effort on one greenfield
funnel. It loses a point only because the hiring middle (US6 assessment→federation→report→onboard) has
no existing design and is the one place the playbook hands the mockup an outline rather than a finished
reference. Everything downstream — the clickable board demo (SC-001), the showable-without-apology bar
(SC-004), and the in-context decision records (SC-007) — depends on the lockup and accountability triad
defined here.
