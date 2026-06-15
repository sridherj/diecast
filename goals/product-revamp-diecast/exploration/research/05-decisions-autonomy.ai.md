# Web Research: Decisions & Autonomy — How Decisions and Autonomy Should Surface in an AI-Does-The-Execution Product (Step 5)

**Goal context:** Product Revamp — Diecast Vision Prototype (spec v0.3.0). Step 5 designs the
trust mechanism for the AI-blackbox posture. The product delegates most execution to agents
(WHAT-primary, HOW behind a tab), so the human's leverage is no longer *doing* the work — it is
*governing* it: knowing what was decided and why, and being asked at exactly the right moments.
US10 / FR-021–023 lock the model this note must make concrete and mockable.

**Date:** 2026-06-11
**Researcher angle:** cast-web-researcher (7 expert lenses)
**Locked model this note grounds against (do not relitigate, make *real*):**
- **Decisions at EVERY phase** (requirements, exploration, planning, execution) recorded with
  `rationale + timestamp + originating-phase/agent + reversibility level`.
- **Autonomy = reversibility-keyed defaults:** **L1** decide-and-record · **L2**
  decide-record-and-**notify** · **L3** **ask-first** (stop the agent, hand `@you` exactly
  **three pre-framed options** — reuses the US5 escalation rail).
- **A per-goal autonomy dial** (conservative / balanced / autonomous) that *shifts those
  thresholds* — opinionated default, user override on top.
- **Decisions surfaced IN CONTEXT** on the goal surfaces (canvas, requirements doc, ticket)
  **plus a cross-phase decision trail** per goal.

**Deliverable for the synthesizer:** decision-surfacing patterns + autonomy-dial precedents
concrete enough to mock the clarify-vs-proceed moment in each of the four flows.

---

## TL;DR — The Verdict (for the synthesizer)

1. **The locked model is *correct and well-precedented* — every piece of it maps onto a named,
   shipping pattern. This note's job is not to invent; it is to (a) confirm the model against the
   field and (b) make the surfaces concrete and mockable.** The four load-bearing precedents:
   - **Reversibility as the autonomy key = Amazon's one-way / two-way doors** (Bezos 2015
     shareholder letter). "Reversible ⇒ decide fast and low; irreversible ⇒ slow down and consult"
     is *literally* the L1/L2/L3 keying. This is the single best framing to cite on every decision
     card and is decades-validated. ([Bezos framework](https://thynkiq.com/blog/reversible-vs-irreversible-decisions))
   - **The decision record = the ADR, evolved for agents.** Context → options considered →
     decision → rationale/trade-offs → consequences → *conditions under which you'd revisit*, with
     **supersede-links** when a later decision overturns an earlier one. ([adr.github.io](https://adr.github.io/),
     [MS Well-Architected ADR](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record))
   - **The autonomy dial = "autonomy is a dial, not a switch" + progressive-autonomy ladders**,
     already shipping in Claude Code's own permission modes (plan / normal / auto / bypass).
     ([Claude Code permission modes](https://code.claude.com/docs/en/permission-modes),
     [auto mode](https://www.anthropic.com/engineering/claude-code-auto-mode))
   - **The L3 ask-first rail = HITL interrupt with an "evidence pack" + pre-framed options**, the
     2026-converged production pattern (LangGraph `interrupt()` → approve/edit/reject/respond).
     ([LangChain HITL](https://docs.langchain.com/oss/python/langchain/human-in-the-loop))

2. **The whole design lives or dies on ONE discipline: keep the L3 signal rare and high-stakes.**
   The dominant, repeatedly-documented failure mode is **confirmation fatigue** — "when approval
   requests come too often, people stop reading them and develop a reflex: approve, approve,
   approve," a documented *clickthrough vulnerability*, not merely bad UX
   ([digitalapplied](https://www.digitalapplied.com/blog/human-in-the-loop-escalation-design-ai-agents-2026)).
   Its mirror image is **automation bias / complacency** — humans rubber-stamp because the system
   is *usually* right ([Springer XAI review](https://link.springer.com/article/10.1007/s00146-025-02422-7)).
   The reversibility key exists precisely to make L3 rare. **Design implication the prototype must
   physically show:** in any flow, *most* decisions are L1 (silent record), a *few* are L2 (record
   + a non-blocking notification), and *exactly one or two* are L3 (a hard stop). If a mocked flow
   shows the agent asking constantly, it has failed the thesis — it looks like a nagging tool, not
   a trusted colleague.

3. **Decisions need TWO surfaces, not one, and the prototype must show both:**
   - **(a) In-context decision chips** — the decision appears *on the artifact it shaped* (a chip
     on the requirements element it changed, on the canvas stage it advanced, on ticket CAST-412).
     "Every automated decision needs a logged rationale reachable *without leaving the primary
     screen*" ([Eleken XAI](https://www.eleken.co/blog-posts/explainable-ai-ui-design-xai)).
   - **(b) A cross-phase decision trail** — one chronological, filterable log per goal answering
     who/what/when/why, with **field-level diffs** ("classification: feature → bug") so it is
     *scannable*, not a wall of prose ([audit-log UX](https://medium.com/@tony.infisical/guide-to-building-audit-logs-for-application-software-b0083bb58604)).
   The chip is for *recognition in flow*; the trail is for *reconstruction after the fact*. They
   are the same records, two projections.

4. **Use layered disclosure on every decision, exactly like the WHAT/HOW split.** Default view = a
   one-line *what + reversibility badge*; one click = rationale + options-considered + consequences;
   deepest = the originating run/agent. This is the XAI "layered visibility: basic by default,
   deeper on demand" consensus ([Eleken](https://www.eleken.co/blog-posts/explainable-ai-ui-design-xai)),
   and it keeps decision records from competing with the WHAT for attention.

5. **The autonomy dial should be framed as *graduated trust*, not just *risk tolerance*.** The
   richest precedent (progressive autonomy: Audit → Assist → Automate) earns autonomy from a
   *track record* — "as the agent's track record becomes boringly reliable, those boundaries
   relax" ([MindStudio progressive autonomy](https://www.mindstudio.ai/blog/progressive-autonomy-ai-agents-safe-deployment)).
   For the prototype this is a one-screen *aha*: the dial isn't a nag-frequency knob, it's *how
   much rope this goal's agents have earned*. Conservative = even L2 stops to ask; Autonomous =
   even some L3s self-decide-and-record for a *trusted* agent. Mock the dial moving and watch a
   borderline decision flip from "asked" to "auto-recorded."

---

## How this maps to Step 5's research targets

| Research target (from steps.ai.md / delegation) | Where answered |
|---|---|
| Decision-record patterns (ADRs evolved for agentic work) | §Lens 1, §Lens 5 (the record schema), §Lens 4 (provenance standards) |
| Audit trails humans actually read | §Lens 1 (field-diffs), §Lens 5 (the trail), §Lens 7 |
| Autonomy / permission dials in agentic products | §Lens 2 (Claude Code, ladders), §Lens 5 (the dial design) |
| Escalation UX (the L3 ask-first rail) | §Lens 3, §Lens 5 ("clarify-vs-proceed"), §Lens 6 |
| Notification design that informs without nagging (the L2 layer) | §Lens 3, §Lens 6 (fatigue), §Lens 5 (notify layer) |
| Concrete mockable clarify-vs-proceed moments per flow | §"Mockable moments per flow" |

---

## Lens 1 — Expert Practitioner: how teams actually record decisions, and what makes a log get read

**The ADR is the field-proven primitive — and it already contains every field US10 wants.** The
canonical ADR (Nygard lineage, now an ecosystem at adr.github.io and baked into Microsoft's
Well-Architected Framework) records: **context** (the forces), **options considered**, the
**decision**, the **rationale/trade-offs**, and the **consequences**. Two practices from the ADR
world map *directly* onto the agentic case and should be lifted verbatim:

- **Superseding, not editing.** "When a decision changes, a new record supersedes the original and
  *links the two together*, preserving the history of thinking and making it clear when and why the
  direction shifted" ([search synthesis], [adr.github.io](https://adr.github.io/)). For Diecast:
  decisions are **immutable**; a reversal is a *new* decision that points at the one it overturns.
  The cross-phase trail then literally shows the product changing its mind, with reasons — exactly
  the "trust the blackbox without losing the why" goal.
- **Record the revisit-condition.** Mature ADRs "record the conditions under which you'd revisit a
  decision" ([MS Well-Architected](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record)).
  This is gold for agentic work and underused elsewhere: a decision card should carry a
  **"revisit if…"** line (e.g., *"revisit if the spike shows latency > 200ms"*). It pre-wires the
  link to spike_ref (FR-016) and makes the autonomy story honest — the agent isn't claiming
  certainty, it's stating the trip-wire that would reopen the call.

**Agents are now first-class ADR authors.** There is an active 2025–26 movement of ADR-writer
agents and "ADR-as-deterministic-pre-generation-check" tools (Mneme HQ feeding Claude Code/Cursor/
Copilot; macromania/adr-agent; the Piethein Strengholt ADR-writer agent) — i.e., the industry
already treats *the agent* as the thing that drafts the decision record, with the human reviewing.
([AI-generated ADR](https://adolfi.dev/blog/ai-generated-adr/),
[adr-agent](https://github.com/macromania/adr-agent)). Diecast's "originating-agent" field on each
record is therefore not exotic; it's where the field is heading.

**What makes an audit trail *actually read* (the hard-won UX lesson):** logs "turn into junk fast"
when they store too much or too little; the cure is **a human-readable description + field-level
diffs**. "Status: Pending → Approved" beats a JSON blob; the log must answer the interrogatives —
*who* changed it, *what* was affected, *what* changed, *when*, and *where it came from* (UI / import
/ API / **automation**) — and be **filterable by actor / action / object / time**
([Infisical audit-log guide](https://medium.com/@tony.infisical/guide-to-building-audit-logs-for-application-software-b0083bb58604),
[AppMaster](https://appmaster.io/blog/audit-logging-internal-tools-activity-feed),
[UX Patterns: Activity Feed](https://uxpatterns.dev/patterns/social/activity-feed)). The "where it
came from = automation" column is the agentic twist: the trail must mark *which agent* (or human)
authored each decision, and the board's any/human/agent/checker filter (FR-010) is the same filter
applied to the trail.

**Practitioner verdict:** the decision record = an ADR with two agentic additions —
`originating_agent` and `reversibility_level` — rendered as a scannable diff-first feed, never a
prose dump. The model is already right; the craft is in making it *legible at a glance*.

---

## Lens 2 — Tools & Technologies: autonomy dials that actually ship

The market has converged on a slogan and a shape: **"autonomy is a dial, not a switch"**
([Galileo](https://galileo.ai/blog/human-in-the-loop-agent-oversight), corroborated across
Strata, Trantor). The concrete dials in shipping products:

| Product | The dial / rungs | What gates each rung |
|---|---|---|
| **Claude Code permission modes** | **Plan** (read-only) · **Normal** (ask before edit/shell/network) · **Auto** (a *classifier model* approves routine actions, blocks anything that "escalates beyond your request, targets unrecognized infrastructure, or appears driven by hostile content") · **Bypass** (no checks) | Per-mode policy + a model-based risk classifier in Auto. This is *exactly* a reversibility/risk-keyed dial shipping today. ([modes](https://code.claude.com/docs/en/permission-modes), [auto mode](https://www.anthropic.com/engineering/claude-code-auto-mode)) |
| **The "Permission Ladder"** (MindStudio) | **Read access** → **Action access** → **Decision access** (financial/legal consequence) | Each rung is a higher-consequence capability; you grant up the ladder deliberately. ([ladder](https://www.mindstudio.ai/blog/ai-agent-permission-ladder-autonomy-levels)) |
| **Progressive autonomy** (MindStudio / Mighty / Elixir) | **Audit** (AI executes, human reviews *everything*) → **Assist** (AI handles routine, human clears *exceptions*) → **Automate** (AI end-to-end, human *monitors*) | **Earned by track record** — boundaries relax as reliability is demonstrated. ([progressive autonomy](https://www.mindstudio.ai/blog/progressive-autonomy-ai-agents-safe-deployment), [Mighty](https://www.mightybot.ai/blog/what-is-progressive-autonomy)) |
| **Cursor background agents** | Incremental approve (yes / yes-always / no) up to fully-autonomous cloud VM agents | Per-action consent, with "yes-always" as a manual trust-promotion. ([Cursor vs CC](https://www.wiz.io/academy/ai-security/claude-code-vs-cursor)) |
| **LangGraph HITL middleware** | `interrupt_before` on chosen nodes; resume with approve / **edit** / **reject** / **respond** | Developer marks *which* tool calls are consequential (e.g., write file, execute SQL). ([LangChain HITL](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)) |

**The crucial design lesson for Diecast's three-position dial (conservative / balanced /
autonomous):** the best dials are **not** global nag-frequency knobs — they are *policies that move
thresholds*. Claude Code's Auto mode is the proof-of-concept: a **classifier decides per-action**
whether to proceed, and the *mode* sets how permissive that classifier is. Map directly:

- The **reversibility level (L1/L2/L3)** is the per-decision classifier output (what kind of door
  is this?).
- The **autonomy dial** is the *mode* that shifts where the L-thresholds sit:
  - **Conservative** → shift everything up one notch: L1 still silent, but L2 *stops to confirm*,
    and L3 always stops. (Mirrors progressive-autonomy "Audit": human reviews more.)
  - **Balanced** (default, opinionated) → the locked defaults: L1 record, L2 record+notify, L3 ask.
  - **Autonomous** → shift down: L2 becomes silent-record, and *some* L3s (for an agent with a
    strong track record) self-decide-and-record with a prominent post-hoc notification. (Mirrors
    "Automate": human monitors.)

This makes the dial a **one-knob reframing of the same reversibility engine** — cheap to mock
(it's a CSS state toggle that re-labels which decisions "asked" vs "auto"), and it tells a true,
field-grounded story.

**Regulatory tailwind worth a single backdrop sentence (not a flow):** HITL oversight is now both
best practice *and* law — EU AI Act Art. 14 mandates human-oversight interfaces for high-risk
systems (Aug 2 2026 deadline); analysis of late-2025→early-2026 agent traffic found **73% of agent
tool-calls had a human in the loop in some form** ([Anthropic: measuring agent autonomy](https://www.anthropic.com/research/measuring-agent-autonomy),
[Strata HITL 2026](https://www.strata.io/blog/agentic-identity/practicing-the-human-in-the-loop/)).
The autonomy dial is therefore a *governance* surface, not just a convenience — a credible note on
the positioning/about screen.

---

## Lens 3 — AI/ML Approaches: the L3 ask-first rail and the L2 notify layer, done right

**The L3 escalation is the most-engineered HITL pattern of 2026, and the field hands Diecast a
ready blueprint.** The convergence ([digitalapplied 2026](https://www.digitalapplied.com/blog/human-in-the-loop-escalation-design-ai-agents-2026),
[Omnithium](https://dev.to/omnithium/human-in-the-loop-patterns-for-high-stakes-ai-agent-decisions-1fg6),
[understandingdata](https://understandingdata.com/posts/human-in-the-loop-patterns/)):

1. **Asynchronous, state-managed interruption** — the agent *freezes state durably* and notifies;
   it does not busy-wait. (LangGraph `interrupt()` + checkpoint; resume with `Command(resume=…)`.)
   *Diecast implication:* the L3 stop is a first-class goal state ("blocked on @you"), surfaced at
   the **WHAT level** (FR-008/US3 Scenario 3) — the user never polls the execution tab to discover
   they're blocking.
2. **Risk-tiered, so escalation is rare** — the canonical four-tier model is **read-only ·
   reversible · external · high-risk/irreversible**, reserving mandatory human approval for actions
   "where the cost of a mistake exceeds the value of the automation." This *is* the reversibility
   key; cite it as the external validation of L1/L2/L3.
3. **An "evidence pack" accompanies every escalation** — "a summary of what the caller wants and
   what the agent attempted; when reviewers get a complete evidence pack, approval decisions take
   **10–30 seconds instead of minutes**." This is the single most actionable UX finding for the L3
   rail: the escalation card must carry *context + attempt + the consequence of each option*, so the
   human decides in seconds.
4. **Pre-framed options, not open-ended prompts** — LangGraph's resume verbs are
   **approve / edit / reject / respond**; the SAP/enterprise pattern presents *bounded choices*.
   Diecast's locked **"exactly three pre-framed options"** is the strongest version of this: it
   forces the agent to do the framing work (here are your real choices and their consequences),
   which is what makes the human's call fast and high-quality.
5. **Timeouts + auto-escalation to a backup** — each action type gets a window (e.g., 5 min for
   customer-facing, 60 min internal) and rolls to a backup approver if the primary is silent. For a
   *static* prototype this is just a visible "expires in 1h · falls back to @teammate" line on the
   escalation card — cheap, and it signals the system is production-shaped.
6. **Confidence-based routing** — act autonomously on HIGH confidence, escalate MEDIUM/LOW. A
   useful *secondary* axis to reversibility: an L2 decision the agent is *unsure* about can be shown
   as "recorded, but flagged low-confidence — confirm?" without becoming a full L3 stop.

**The L2 notify layer is where most products fail, and it's the subtlest design problem.** L2 =
"decide, record, and *notify*" — inform without blocking and without nagging. The notification
literature is unambiguous about how (see Lens 6): **batch L2s into a digest**, don't fire one
toast per decision. The prototype should show L2 decisions accruing into a **"3 decisions made
while you were away"** roll-up on the canvas/goal surface — a glanceable, non-modal informer — with
each expandable to its record. This is the difference between "the agent kept me informed" and "the
agent wouldn't stop pinging me."

**Reasoning-vs-execution provenance (an AI-native subtlety to bake in):** provenance research
stresses distinguishing *reasoning failures* from *execution failures*
([PROV-AGENT](https://arxiv.org/pdf/2508.02866)). A decision record should make clear whether the
agent *chose* something (reasoning — the interesting, reviewable part) vs merely *ran* a step. Only
**reasoning decisions** deserve a decision record; execution steps belong in the run log behind the
execution tab. This keeps the decision trail signal-dense — it's the *judgment calls*, not the
key-presses.

---

## Lens 4 — Community & Open Source: the standards that make decisions portable and machine-readable

- **ADR ecosystem (adr.github.io, MADR templates)** — the open, community-owned decision-record
  format. Adopt the *template* (status, context, decision, consequences, links) as the schema
  backbone; add `reversibility_level` and `originating_agent`. Using a recognized shape means a
  Diecast decision is legible to anyone who's seen an ADR — and exportable. ([adr.github.io](https://adr.github.io/))
- **W3C PROV / provenance model** — "a record that describes the people, institutions, entities,
  and activities involved in producing, influencing, or delivering" a result
  ([Decision provenance synthesis](https://www.mdpi.com/2306-5729/11/4/66)). This is the formal
  backing for the cross-phase trail: a decision *links to* the artifact it influenced and the
  run/agent that produced it. The same `entity ← activity ← agent` triple the W3C uses is the
  `decision ← run ← agent` link Diecast needs — and it unifies cleanly with Step 4 (annotation)
  and Step 7 (round-trip provenance) which already lean on stable IDs.
- **HITL is now a documented OSS production pattern, not research** — LangGraph/LangChain ship HITL
  middleware with approve/edit/reject/respond as named verbs; "the ability to interrupt, review,
  and modify AI execution is becoming a *core requirement, not an optional feature*"
  ([LangChain HITL](https://docs.langchain.com/oss/python/langchain/human-in-the-loop),
  [TDS](https://towardsdatascience.com/building-human-in-the-loop-agentic-workflows/)). Diecast's
  escalation rail is squarely on the main line of where open agent frameworks are going.
- **Observability stacks (LangSmith / Langfuse / Arize / Braintrust)** as the "execution-tab"
  precedent — 2026 agent observability records "node-by-node state diffs, conditional edge
  transitions, retry timelines, and HITL interrupt timing"
  ([observability 2026](https://www.digitalapplied.com/blog/agent-observability-platforms-langsmith-langfuse-arize-2026)).
  This is the *raw* trace; Diecast's contribution is the **editorial layer on top** — promoting the
  handful of *judgment calls* out of the trace into human-legible decision records. The trace is the
  HOW (execution tab); the decision trail is the curated WHAT-level "why."

**Community consensus:** anchor decisions to a recognized record format (ADR), link them with a
provenance model (PROV-style `decision→artifact`/`decision→run`), and treat machine authorship as
first-class. All three are already where the open ecosystem is — Diecast isn't betting against the
grain, it's productizing the grain.

---

## Lens 5 — Frameworks & Patterns: the concrete recommended design (mockable)

### 5a. The decision record (the atom)

```
Decision {
  id,                      // e.g. DEC-CAST-412-03
  goal_slug, phase∈{requirements,exploration,planning,execution},
  title,                   // one line, imperative: "Classify CAST-412 as bug, not feature"
  reversibility∈{L1,L2,L3},// the door type — drives autonomy AND the badge
  rationale,               // why — the trade-off, in plain language
  options_considered: [ {option, consequence, chosen:bool} ],  // ≥2; for L3, exactly 3 surfaced
  consequences,            // what this sets in motion
  revisit_if,              // the ADR trip-wire — links to spike_ref when a spike would settle it
  originating_agent,       // who decided (agent id or @human)
  author_type∈{agent,human},
  timestamp,
  status∈{recorded, awaiting_human, superseded},
  supersedes?, superseded_by?,   // immutable history — reversals are NEW records
  spike_ref?,              // FR-016 linkage
  influenced: [artifact_ref]     // PROV link: which canvas stage / requirement elem / PR this shaped
}
```

This is an ADR + `reversibility` + `originating_agent` + PROV `influenced` links. Nothing here is
speculative — each field has a precedent above.

### 5b. The two surfaces (both must appear in the prototype)

**(a) In-context decision chip** — rendered *on the artifact it influenced*:
- On a **requirements element**: a small chip "⚖ Decided: classification feature→bug · L2" (ties to
  US7 / FR-014's element-anchored model from Step 4 — chips hang off the same stable element IDs as
  comments).
- On a **canvas stage**: a chip on the stage the decision advanced ("⚖ chose hypothesis B · L1").
- On **ticket CAST-412**: the decision artifact in the activity log (US5 Scenario 3) — *this is the
  same record*, just the execution-phase instance.
- **Layered disclosure:** chip (what + reversibility badge) → click → popover (rationale +
  options-considered + revisit-if) → "open full record" → the cross-phase trail focused on it.
  Rationale is always "reachable without leaving the primary screen"
  ([Eleken XAI](https://www.eleken.co/blog-posts/explainable-ai-ui-design-xai)).

**(b) Cross-phase decision trail** — one per goal, a filterable feed:
- Columns/scan-line: `time · phase · ⚖badge(L1/L2/L3) · title · who(agent/human) · [diff]`.
- **Field-level diffs** for legibility ("classification: feature → bug"), never prose blobs.
- **Filter by phase / actor (any/human/agent) / reversibility / status** — the same any/human/agent
  filter as the board (FR-010), applied to history.
- Superseded decisions shown struck-through with a link to what replaced them — the product visibly
  "changing its mind, with reasons."
- This is the audit trail "humans actually read" because it's diff-first and filterable, not a dump.

### 5c. The autonomy dial (one knob, three positions)

A per-goal control, rendered as a labeled segmented control with a plain-language legend:

```
Autonomy:  [ Conservative ]  ( Balanced )  [ Autonomous ]
           ↑ agents ask more         ↑ default        ↑ agents act more, record after

Conservative — even reversible-but-notable (L2) calls pause for your OK. Best for a new goal or new agent.
Balanced     — agents decide & record routine calls (L1), notify you of notable ones (L2), and
               stop to ask on irreversible calls (L3, three options). (recommended default)
Autonomous   — agents handle L2 silently and self-decide some L3s for agents with a strong track
               record, recording every call for your review. Best when the team is proven.
```

The legend itself teaches the model. Moving the dial **re-keys the same reversibility engine**
(Lens 2). Crucially, frame the right end as *earned* (progressive-autonomy "Automate" — track
record relaxes boundaries), not as recklessness — a tooltip "this goal's agents have a 99.4%
compliance record across 312 runs" ties the dial to the marketplace credibility stats (US6) and
makes Autonomous feel *earned*, not *risky*.

### 5d. The clarify-vs-proceed decision flow (the core mockable mechanic)

```
Agent reaches a judgment call
   │
   ├─ classify reversibility ──► L1 ──► decide ──► record (silent chip) ──► continue
   │                              │
   │                             L2 ──► decide ──► record ──► add to digest ("notify") ──► continue
   │                              │                              (batched, non-modal)
   │                             L3 ──► STOP ──► raise escalation card to @you at WHAT level:
   │                                              • evidence pack (what I want / what I tried)
   │                                              • exactly 3 pre-framed options + consequence each
   │                                              • "revisit-if" / spike option
   │                                              • expires in 1h → falls back to @teammate
   │                                     └─ human picks ──► becomes a recorded decision (author=human)
   │
   └─ autonomy dial shifts where the L-thresholds sit (Conservative ↑ / Autonomous ↓)
```

For a **static prototype** this entire mechanic is a scripted, CSS-state clickthrough: the canvas
shows the agent reaching the call, a banner promotes the L3 to the WHAT level, the escalation card
slides in with three option buttons, clicking one resolves the stop and drops a decision chip onto
the artifact and a row into the trail. **One L3 moment per flow, demonstrated not described.**

---

## Mockable clarify-vs-proceed moments per flow (the deliverable)

One concrete, on-brand decision moment for each of the four locked families — each with its
reversibility level and which surface it lands on. (Reuse the canonical fake-data spine: org
"Northwind", project, CAST-### tickets, crud-orchestrator, M04/S03/R02.)

| Flow | L1 (silent record) | L2 (record + notify) | **L3 (ask-first, 3 options)** |
|---|---|---|---|
| **New feature** (CAST-412) | "Chose REST over GraphQL for the RBAC endpoint — matches existing API surface." | "Split FR-014 into routing + recording (two FRs) during planning." → digest | **"The RBAC migration drops the legacy `roles` column — irreversible on prod data. Pick: (a) additive migration, keep column 90 days; (b) drop now with a backup snapshot; (c) spike a dual-write window first."** → escalation rail; lands on CAST-412 + trail. |
| **Bug fix / debug loop** | "Ruled out hypothesis A (cache) — repro persists with cache disabled." (iteration 1/3) | "Switching repro strategy from unit to integration harness." → digest | **"Root cause is in shared `auth` middleware; the fix changes behavior for 4 other services. Pick: (a) narrow fix guarded by feature flag; (b) fix middleware + notify owners; (c) escalate to the auth team."** Note: debug-loop L1s show as *iteration history* (FR-007), not hidden. |
| **Spike / quick conclusion** | "Time-boxed the latency spike to 2h; measuring p95 only." | "Spike inconclusive at 2h — extending once to 3h." → digest | **"Spike shows the vendor SDK adds 180ms p95 (budget 200ms) — borderline. This decision gates the feature's go/no-go. Pick: (a) proceed, accept 180ms; (b) self-host the call; (c) renegotiate the budget with @you."** The conclusion artifact is `spike_ref`'d by the resulting decision (US2 S3 / FR-016) — the *clearest* place to show the `revisit_if` → spike linkage. |
| **Data analysis / research** | "Excluded 1.2% null-region rows from the cohort — documented in method." | "Chose median over mean for the skewed latency dataset." → digest | **"Two data sources disagree on Q2 revenue by 8%; the chart's headline depends on which I trust. Pick: (a) use source-of-record (finance DB); (b) show both with a reconciliation note; (c) flag for analyst review before publishing."** Resolution drives which visualized output renders (US2 S4 / FR-009). |

**The cross-cutting demo beat:** in the feature flow, *toggle the autonomy dial* from Balanced to
Conservative and show the L2 "split FR-014" decision flip from a quiet digest entry to a *stop-and-
confirm* card — proving the dial re-keys the engine (SC-007's "at least one autonomy-gated
clarification moment," shown live).

---

## Lens 6 — Contrarian View: the model is right; the ways to ruin it are specific

**Kill premise: "more decision records + more asking = more trust/accountability." FALSE, and
backwards.** Two documented failure modes punish over-doing it:

1. **Confirmation fatigue → the approve-approve-approve reflex.** "When approval requests come too
   often, people stop reading them"; it's a *documented clickthrough vulnerability*
   ([digitalapplied](https://www.digitalapplied.com/blog/human-in-the-loop-escalation-design-ai-agents-2026)).
   An L3 that fires often is *worse than no L3* — it trains the human to rubber-stamp the one that
   mattered. **Therefore L3 must be visibly rare in every mocked flow** (one stop, not five).
2. **Automation bias / complacency → over-trust the records you do show.** When a system is usually
   right, humans stop scrutinizing; "verification-related cognitive engagement is the critical
   debiasing mechanism" ([Springer XAI review](https://link.springer.com/article/10.1007/s00146-025-02422-7),
   [Frontiers trust calibration](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.652776/full)).
   Design consequence: the L3 card should *force a real choice* (three distinct options with
   distinct consequences), not offer a pre-highlighted "recommended — just hit OK" that invites the
   reflex. Make the human *engage*, briefly, exactly when it counts.

**Kill premise: "log every decision."** No — log every *judgment call*, not every *step*. Provenance
research's reasoning-vs-execution distinction (Lens 3) is the filter: a decision record is for a
**choice between live alternatives**, not for "ran the test suite." Over-logging produces *audit
theater* — a trail so noisy no human reads it, defeating the entire purpose. The execution tab
(HOW) holds the firehose; the decision trail (WHAT-level) holds the curated judgment calls. **If a
mocked trail has 40 entries for one goal, it's wrong; ~5–8 real decisions per goal is the legible
target.**

**Sharpen, don't kill: "the autonomy dial is a safety control."** It's *also* a trust-status
display. The contrarian reframing (from progressive autonomy) is that the dial's *position is
earned* — its right edge unlocking is a *reward* for a track record, not a risk the user toggles
blindly. Showing the dial with a "why this is available" credibility stat turns a scary knob into a
confidence signal. This is more honest *and* more compelling for the demo.

**One real risk to concede:** reversibility classification is itself a judgment the agent can get
wrong (mislabel an L3 as L2 and act irreversibly). Mitigation the prototype can *show*: the L2
digest is reviewable and any L2 can be **promoted to "should've asked"** by the human with one
click, which (a) corrects the record and (b) is the training signal that makes the agent's future
classification better — closing the loop and making the human's oversight *productive*, not just
janitorial. (This also seeds the agent's track-record stat that gates the dial.)

---

## Lens 7 — First Principles: decompose to irreducible primitives

Strip "decisions & autonomy" to atoms and the design falls out:

- **What is a decision (vs a step)?** *A commitment to one option among live alternatives, made
  under uncertainty.* The irreducible fields are therefore **alternatives + the chosen one + why +
  what it can't easily undo**. "What it can't undo" = reversibility — and reversibility is the
  *only* property that intrinsically determines how much a human should care. Hence: **reversibility
  is the correct key for autonomy.** (Bezos arrived here for org design; it's the same physics.)

- **What does "autonomy" reduce to?** *Who gets to commit without asking.* Two variables only:
  **(1) the stakes of the commitment** (reversibility) and **(2) how much the human trusts this
  agent for this goal** (track record). The dial is just variable (2); the L-level is just variable
  (1). The locked model is the *minimal* correct model: a per-decision stakes classifier × a
  per-goal trust setting. Nothing is missing; nothing is excess.

- **What does "surfaced in context" reduce to?** *The decision is rendered on the thing it changed.*
  The atom is the **`decision → influenced-artifact` link** (PROV). Given that link, the in-context
  chip is automatic (render the decision wherever its influenced-artifact renders) and the trail is
  automatic (list decisions by time). One link primitive yields both surfaces. (This is the *same*
  stable-ID anchoring Step 4 and Step 7 rest on — decisions, comments, and round-trip provenance
  are three consumers of one identity backbone.)

- **What does "ask the human" minimally require?** *That the human can decide in seconds.* Which
  requires the agent to have **already done the framing** — the alternatives, their consequences,
  the recommendation's trip-wire. The "three pre-framed options + evidence pack" isn't UX garnish;
  it's the *minimum* that makes a fast, good human decision possible. An open-ended "what should I
  do?" violates the atom (it offloads framing back to the human, the thing the product exists to
  do for them).

- **What does "notify without nagging" reduce to?** *Match interrupt-cost to decision-stakes.* L1 =
  zero interrupt (silent record). L3 = full interrupt (hard stop). L2 = the only interesting case,
  and the atom is *aggregate, don't serialize* — batch into a digest, because the cost of N
  separate interrupts ≫ the cost of one digest of N items, while the information is identical
  ([notification batching: 35% higher engagement, 28% fewer opt-outs](https://docs.suprsend.com/docs/best-practices-for-batching-digest),
  [Smashing notifications guidelines](https://www.smashingmagazine.com/2025/07/design-guidelines-better-notifications-ux/)).

**First-principles conclusion:** the entire feature is three primitives — **(reversibility-keyed
decision atom) × (a `decision→artifact` link) × (a two-variable autonomy function: stakes × trust)**
— and the locked model is exactly their composition. The research did not find a better model; it
found the *names, precedents, and failure modes* that make this one credible and mockable. The work
left is craft: keep L3 rare, keep the trail diff-first and curated, render chips on the artifacts,
and frame the dial as earned trust.

---

## Open questions / hand-offs for the playbook & later steps

1. **Decision identity rides the Step 4 / Step 7 stable-ID backbone.** In-context chips anchor to
   the same element/artifact surrogates that comments and round-trip provenance use. Flag to the
   synthesizer that decisions are a *third consumer* of one identity system — design it once.
2. **The L3 rail IS the US5 escalation rail — reuse, don't re-author.** US10 Scenario 4 and US5
   Scenario 4 are the same mechanism (stop agent, three pre-framed options on the board). The
   prototype should render *one* escalation component, instantiated at execution (US5) and at other
   phases (US10). Coordinate with Step 4 (agents-as-colleagues) which owns the board/ticket chrome.
3. **The L2 digest overlaps US7's "requirements updated from planning" notification.** Both are
   "inform-without-nagging" surfaces; recommend one digest/notification component for both
   (downstream write-back notices and L2 decision notices are the same UX atom). Coordinate with
   the Step 4 annotation note.
4. **The autonomy-dial credibility tooltip overlaps US6 marketplace stats.** "This goal's agents
   have a 99.4% compliance record" is the same stat the marketplace shows on agent resumes — wire
   the dial's "earned trust" framing to the same fake-data stat for consistency.
5. **Reversibility classification could itself be a (meta) decision worth showing once** — i.e., the
   agent records *why* it judged something L3. Optional flourish; only if it doesn't clutter. Default
   to NOT showing it (keep the trail curated) unless a flow specifically benefits.
6. **Per-flow L3 count is a hard design budget:** exactly one (maybe two) L3 moments per flow.
   Hand the four scripted L3 moments above to the design/build step as locked demo beats; resist
   adding more — the contrarian lens says more L3s actively damage the thesis.

---

## Citation index

- Bezos / one-way / two-way doors (reversibility = autonomy key): https://thynkiq.com/blog/reversible-vs-irreversible-decisions
- Amazon one-door/two-door framework (Cub Think Tank): https://www.cubthinktank.com/posts/article-two-door
- ADR ecosystem (canonical decision-record format): https://adr.github.io/
- Microsoft Well-Architected — maintain an ADR (revisit-conditions, supersede): https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record
- AI-generated ADRs (agents as ADR authors): https://adolfi.dev/blog/ai-generated-adr/
- adr-agent (ADR-writer agent): https://github.com/macromania/adr-agent
- Building an ADR writer agent (Strengholt): https://piethein.medium.com/building-an-architecture-decision-record-writer-agent-a74f8f739271
- Claude Code permission modes (plan/normal/auto/bypass dial): https://code.claude.com/docs/en/permission-modes
- Claude Code auto mode — classifier-gated autonomy (the shipping dial): https://www.anthropic.com/engineering/claude-code-auto-mode
- The Permission Ladder — read/action/decision access (MindStudio): https://www.mindstudio.ai/blog/ai-agent-permission-ladder-autonomy-levels
- Progressive autonomy — Audit/Assist/Automate, earned by track record (MindStudio): https://www.mindstudio.ai/blog/progressive-autonomy-ai-agents-safe-deployment
- Progressive autonomy — earn trust incrementally (Mighty): https://www.mightybot.ai/blog/what-is-progressive-autonomy
- Progressive autonomy — four phases (Elixir): https://www.elixirdata.co/blog/progressive-autonomy
- "Autonomy is a dial, not a switch" + HITL oversight (Galileo): https://galileo.ai/blog/human-in-the-loop-agent-oversight
- HITL escalation design 2026 — risk tiers, evidence pack (10–30s), timeouts, confirmation fatigue: https://www.digitalapplied.com/blog/human-in-the-loop-escalation-design-ai-agents-2026
- HITL patterns for high-stakes decisions (interrupt, durable state): https://dev.to/omnithium/human-in-the-loop-patterns-for-high-stakes-ai-agent-decisions-1fg6
- HITL patterns: approval / input / escalation (Just Understanding Data): https://understandingdata.com/posts/human-in-the-loop-patterns/
- LangChain/LangGraph HITL — interrupt + approve/edit/reject/respond: https://docs.langchain.com/oss/python/langchain/human-in-the-loop
- Building HITL agentic workflows (TDS): https://towardsdatascience.com/building-human-in-the-loop-agentic-workflows/
- Anthropic — measuring agent autonomy in practice (73% HITL): https://www.anthropic.com/research/measuring-agent-autonomy
- Strata — HITL: a 2026 guide to AI oversight (EU AI Act Art. 14): https://www.strata.io/blog/agentic-identity/practicing-the-human-in-the-loop/
- Notification batching & digest best practices (35% engagement / 28% fewer opt-outs): https://docs.suprsend.com/docs/best-practices-for-batching-digest
- Reducing notification fatigue — 7 strategies (Courier): https://www.courier.com/blog/how-to-reduce-notification-fatigue-7-proven-product-strategies-for-saas
- Smashing — design guidelines for better notifications UX: https://www.smashingmagazine.com/2025/07/design-guidelines-better-notifications-ux/
- Signal detection theory in UX (alerts vs noise): https://www.ux-bulletin.com/signal-detection-theory-in-ux/
- Audit logs for application software — who/what/when/where, field diffs (Infisical): https://medium.com/@tony.infisical/guide-to-building-audit-logs-for-application-software-b0083bb58604
- Audit logging for internal tools — clean change-history / activity feed (AppMaster): https://appmaster.io/blog/audit-logging-internal-tools-activity-feed
- Activity Feed pattern (UX Patterns for Developers): https://uxpatterns.dev/patterns/social/activity-feed
- Explainable AI UI design — layered visibility, rationale on primary screen (Eleken): https://www.eleken.co/blog-posts/explainable-ai-ui-design-xai
- Designing UIs for agentic AI — show what/why, avoid black-box launch (Codewave): https://codewave.com/insights/designing-agentic-ai-ui/
- Automation bias in human–AI collaboration — implications for XAI (Springer): https://link.springer.com/article/10.1007/s00146-025-02422-7
- Calibrated trust & reliance in automation (Frontiers): https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.652776/full
- How transparency modulates trust in AI (ScienceDirect): https://www.sciencedirect.com/science/article/pii/S2666389922000289
- PROV-AGENT — unified provenance for agent interactions (reasoning vs execution failures): https://arxiv.org/pdf/2508.02866
- Decision processes, tool interactions & provenance links in agents (MDPI): https://www.mdpi.com/2306-5729/11/4/66
- Agent observability 2026 — state diffs, interrupt timing (LangSmith/Langfuse/Arize): https://www.digitalapplied.com/blog/agent-observability-platforms-langsmith-langfuse-arize-2026
- Claude Code vs Cursor — incremental approve / background agents (Wiz): https://www.wiz.io/academy/ai-security/claude-code-vs-cursor
- **Internal dependencies:** Step 4 annotation note (stable-ID anchoring for in-context chips) and
  Step 7 round-trip note (PROV `decision→artifact` links) — decisions are a third consumer of the
  same identity backbone.
