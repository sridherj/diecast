# Step 4 Research — Agents as COLLEAGUES, not Tools (screen-level design references)

> **Exploration step:** Step 4 of `exploration/steps.ai.md` — *How do agents appear as colleagues,
> not tools?*
> **Surfaces in scope:** US5 (board → ticket maker-checker log → decision → escalation), US6 (hiring:
> assessment → federation → stack-ranked report → hire → onboard; marketplace credibility + agent
> resume), US8 (skill ops: private/company-wide, versions, usage, monitoring), US9 (catalogues + Layer-2),
> with the autonomy thread (US10) where it touches these screens.
> **Author:** cast-web-researcher | **Date:** 2026-06-11
> **Audience:** the playbook synthesizer + the design-language pick. This is a *design-reference* brief —
> it hands the mockup phase a north-star and an anti-pattern for every surface.
> **Framing (locked):** VISION-FIRST. Existing assets are terrain, not anchor. The bar is "software built
> for the future." If a reference reads as admin CRUD, it is named only to be rejected.

---

## TL;DR — the doctrine and the six surfaces

**The thesis in one line:** an agent stops being a *tool* the moment the product gives it the three
things we give a human colleague — **an identity you can evaluate, a record of work you can read, and a
seat at the same table where the work is tracked.** Tools have settings pages; colleagues have résumés,
activity feeds, and assignments. Every surface below is graded on whether it delivers those three.

**The colleague test (use it as the rejection gate for every screen):**
A surface passes only if it answers, at a glance, at least two of: *(1) Who is this worker and would I
trust them with this?* (identity/résumé), *(2) What did they actually do and why?* (legible work record),
*(3) Are they on the board with me, accountable, the way a teammate is?* (peer presence). A surface that
only answers *"what are this thing's configuration options?"* is a tool page — it fails, redesign it.

**North-star reference per surface** (full screen-anatomy in §4):

| # | Surface (spec) | North-star reference(s) | The one move that kills "CRUD" |
|---|---|---|---|
| 1 | Shared board, human+agent peers (US5 S1) | **Linear for Agents**, GitHub **Agents panel** | Agents are rows/avatars *in the same board*, with a live "working…" pulse — not a separate "Automations" tab |
| 2 | Ticket maker-checker activity log (US5 S2, US4 S3) | **CodeRabbit / Greptile** inline review threads w/ severity + confidence; **Devin** session timeline | The checker's rule violations render as *inline review comments with a rework budget meter*, not a pass/fail badge |
| 3 | Decision artifact + escalation rail (US5 S3/S4, US10) | **ADR records** + L1–L5 **autonomy-scale** approval UX | Three pre-framed options handed to `@you` *on the board*, reversibility-keyed — not a generic "needs approval" modal |
| 4 | Hiring flow: assess→federate→report→hire→onboard (US6) | **Google structured-hiring packet** + **LMArena/LLM-judge** side-by-side + spider charts | A *stack-ranked hiring report with links to real produced output*, not a feature-comparison pricing grid |
| 5 | Marketplace credibility + agent résumé (US6 S3/S5) | **Apify Actor store** (success-rate/runs/ratings) + **A2A Agent Card** (the literal "résumé") | Every card carries a track-record stat line ("99.9% across 505 runs") and opens a *résumé*, with the checker shown *in-card* |
| 6 | Skill ops + public/private catalogues (US8, US9) | **Backstage** software catalog + scorecards; **Claude plugin marketplace** (user vs project scope) | One discover-and-hire surface over two catalogues; agents are *operated like services* (versions, scorecard, monitoring) — not toggled like settings |

**The single sharpest external signal** — and the one tension to resolve deliberately: **Linear, the
best-in-class board, refuses to make an agent a peer assignee.** When you delegate an issue to an agent,
"the human user remains the primary assignee, while the agent is added as a *contributor*"
([Linear Agents][linear-agents], [Linear docs][linear-docs]). Diecast's spec says the opposite — humans
and agents as *peer assignees* with an `any/human/agent/checker` filter (US5 S1, FR-010). This is not a
mistake to copy around; it is the **design decision that defines the product's posture.** Resolution in
§5: Diecast can show agents as peers *because* it pairs every maker with a checker and a reversibility
gate — the accountability Linear preserves with a human assignee, Diecast preserves with the
maker-checker-escalation triad. That triad is what *earns* the peer seat. Build the peer board, but make
the accountability visible in the same frame, or it reads as reckless rather than visionary.

---

## 1. First principles — what actually separates a colleague from a tool

Strip the question to its atoms. A **tool** is invoked, configured, and forgotten; its UI is a form and a
run button. A **colleague** is *evaluated before* you trust them, *observed during* the work, and *held
accountable after*. Three primitives fall out, and every surface in the spec maps to exactly one:

1. **Identity you can evaluate** → the **résumé / agent card** (US6). The A2A protocol independently
   arrived at exactly this metaphor: an Agent Card is "a digital business card… serving as a résumé or
   LinkedIn profile that allows agents to discover each other" ([A2A][a2a-card], [IBM A2A][ibm-a2a]). When
   the *machines* building agent ecosystems converge on "give every agent a résumé," that is the strongest
   possible validation that the colleague metaphor is the right substrate, not a skin.
2. **Work you can read** → the **maker-checker activity log + decision trail** (US5, US10). A colleague
   doesn't hand you a green checkmark; they show their work and you can see where they hesitated. Devin's
   teammate-feel comes precisely from "surfacing progress and accepting feedback mid-run… more like a
   teammate than an autocomplete engine" ([Cognition][devin-intro], [Devin docs][devin-docs]).
3. **A peer seat where work lives** → the **shared board** (US5). Not a console you visit; the same board
   your humans use, with agents present on it.

This is the rejection criterion the rest of the brief operationalizes: **a screen that serves only the
"configure and run" loop is a tool page and dies; a screen that serves identity-evaluation, work-legibility,
or peer-accountability is a colleague page and lives.**

---

## 2. The seven expert angles (the survey)

### Angle 1 — Expert Practitioner (PM-tool & dev-tool board craft)

The practitioners who have actually shipped "agents on a board" are Linear, GitHub, and the Devin/Cursor
class — and their craft converges on a few non-negotiables:

- **Agents are first-class workspace members, addressed exactly like people.** In Linear, agents are
  "full members of your workspace — assign them to issues, add them to projects, or @mention them in
  comments" ([Linear docs][linear-docs]). GitHub's coding agent is reachable from "the agents panel
  accessible on *every page*" and from a "Delegate to coding agent" button right inside the IDE
  ([GitHub blog][gh-agent]). The lesson for the Diecast board: the agent is not in a sidebar utility — it
  is in the **assignee picker**, the **@mention autocomplete**, and the **avatar stack**, indistinguishable
  in *placement* from a human, distinguished only by a subtle glyph/ring.
- **Delegation ≠ assignment, and the best tools show the difference.** GitHub's agent "opens a PR, writes
  the code, runs tests, and then *asks for your review*… revises until you approve" ([GitHub news][gh-news]).
  That ask-for-review loop is the colleague behavior; the board must render it as a state, not bury it.
- **Async progress is the teammate tell.** Devin 2.0's overhaul gave it "sessions you can pause, resume,
  share, and review like a teammate" and a persistent chat where it surfaces progress mid-run
  ([techpoint review][devin-review]). A colleague board shows *in-flight* state ("Devin is on CAST-412,
  iteration 2/3"), not just todo/done.

**Practitioner verdict:** put agents in the same pickers and avatar stacks as humans; render *delegation
state* (proposed / working / asking-for-review / done) as first-class; never relegate agents to an
"automations" tab. The "automations tab" is the single most common way this surface collapses into CRUD.

### Angle 2 — Tools & Technologies (marketplace credibility mechanics)

Apify is the most mature *public agent/actor marketplace* and its credibility surface is directly liftable
for US6 S3. Each listing carries a **right-rail metrics panel**: monthly active users, star rating,
**success rate**, response time, build/run counts, and creation/modification dates — explicitly framed as
"shorthand for potential users to assess reliability before trying it" ([Apify store basics][apify-store];
[Apify academy][apify-academy]). Apify also runs **automated daily health tests** — an actor that fails
its default-input run for three consecutive days is auto-labeled "under maintenance"
([Apify review][apify-review]). Two design takeaways:

- The spec's canonical credibility line ("99.9% compliant code in 2 maker-checker loops across 505 runs")
  is *exactly the Apify success-rate stat, re-expressed in Diecast's maker-checker vocabulary.* Lift the
  pattern (a dense stat line + a freshness/health badge), restate it in our terms.
- **A public "Issues/health" signal is itself a trust device.** Apify makes the issues tab public so "the
  level of activity… serves as an indicator of reliability." Diecast's analog: a public **track-record**
  (last 50 runs, compliance trend, last-active) on every agent card.

**Tools verdict:** the marketplace credibility surface is a *solved pattern* — dense stat line + freshness
badge + health signal + ratings. Lift Apify's anatomy wholesale; the only re-skin is vocabulary
(runs→runs, success-rate→compliance-rate, "under maintenance"→"checker-flagged / benched").

### Angle 3 — AI / ML Approaches (the hiring report = an eval leaderboard)

US6's "stack-ranked Google-style hiring report" is, mechanically, an **LLM evaluation leaderboard scoped to
one assessment.** The eval-UI literature hands us the exact components:

- **Side-by-side comparison as the primitive.** LMArena's pattern — same prompt, two (initially anonymous)
  models, vote, then reveal identity — is the credibility engine for "we actually tested them on *your*
  task" ([Artificial Analysis leaderboard][aa-leaderboard]). For Diecast: run the assessment, show
  candidate outputs head-to-head, *then* reveal the stack rank.
- **Dimension-wise scoring with spider + bar charts.** Mature eval kits show "dimension-wise evaluations
  and visualizations such as Summary, Spider Chart, Bar Chart, and Differences to clearly show relative
  strengths" (AITutor-EvalKit, arXiv 2512.03688). The hiring report's per-candidate panel should carry a
  **radar across the product dimensions** the assessment spanned (user scale, internal/external software,
  …) — this is what makes it read "Google hiring committee," not "pricing table."
- **Rank + quantitative metric + qualitative rationale, together.** Leaderboards pair a numeric rank with a
  metric *and* (in the best ones) a written rationale. The hiring report's per-candidate **pros/cons with
  links to actual produced output** (US6 S2) is the "LLM-as-judge rationale" rendered for a human decision.

**AI verdict:** design the hiring report as an *eval report card*, not a spec-comparison grid: head-to-head
outputs, per-dimension radar, numeric stack-rank, and judge-style pros/cons each *deep-linked to the real
artifact the candidate produced*. The deep-link to real output is what separates "credible assessment"
from "vendor brochure."

### Angle 4 — Community & Open Source (catalogues, scorecards, the résumé schema)

Three OSS precedents define the catalogue + ops + résumé surfaces:

- **Backstage** is the canonical *internal* catalogue: "a centralized system that tracks ownership and
  metadata for all software… makes everything and who owns it discoverable, eliminating orphan software"
  ([Backstage catalog][backstage]). Crucially, Roadie's **Tech Insights / scorecards** "measure software
  against organizational standards… governance without manual audits" ([Roadie scorecards][roadie]). This
  is the exact shape of US8/US9: a catalogue of agents-as-components, each with an **ownership line, a
  scorecard (compliance/rework/usage), and a health state** — agents *operated like services*. Backstage's
  metadata-YAML-beside-the-code model also mirrors Diecast's file-in-goal-dir ethos.
- **Claude Code plugin marketplace** gives the *private-vs-public* + *versioning* + *scope* mechanics for
  free: plugins install at **user (global) vs project (local) scope**; each plugin is "pinned to a specific
  commit SHA"; multiple marketplaces (official + custom) sit behind one discover-and-install surface
  ([Claude plugins docs][claude-plugins]). US8's "private vs company-wide skills" = user vs project scope;
  US9's "public + private catalogues behind one discover-and-hire mechanism" = official + custom
  marketplaces behind one browser. The pattern is shipped; lift it.
- **A2A Agent Card** is the literal **résumé schema** for US6 S3: identity (name, provider, version),
  **skills** (each with id, description, input/output modes, *usage examples*), **capabilities** (streaming,
  push), **auth**, endpoint ([A2A discovery][a2a-discovery]). Diecast's "role, I/O contract, autonomy level,
  paired checker, benchmark, sample output" is the Agent Card with three Diecast-native additions
  (autonomy level, paired checker, benchmark) — a clean superset.

**Community verdict:** the catalogue (Backstage), the scope/version model (Claude marketplace), and the
résumé schema (A2A Agent Card) are all standardized and liftable. Diecast's value-add is *binding them
together*: a Backstage-grade catalogue whose component pages are A2A-style résumés carrying maker-checker
scorecards.

### Angle 5 — Frameworks & Patterns (maker-checker as a reviewed-PR, autonomy as a graded scale)

- **Maker-checker is the AI-code-review pattern, already crafted.** CodeRabbit/Greptile show the exact
  component vocabulary the ticket activity log needs: **inline comments tied to specific lines, with
  severity rankings, one-click fixes, confidence scores, and PR summaries**
  ([CodeRabbit/Greptile compare][cr-greptile]; [Greptile][greptile]). US5 S2's "checker rule violations as
  inline comments (M04/S03/R02), a visible rework budget (1/3 used), resulting PR link" is *this surface*
  with two additions: a **named rule taxonomy** (the M/S/R codes) and a **rework-budget meter**. The budget
  meter is the Diecast-original move — it turns "the checker found things" into "the maker has 2 attempts
  left before escalation," which is dramatic and legible.
- **Autonomy is a graded scale with a known approval-UX per level.** The L1–L5 literature is settled:
  L1–L2 human-drives, **L3 agent-proposes/human-approves** (approval workflows, notifications, review
  dashboards — "nothing happens until a human says yes"), L4 act-then-audit, L5 environment-verifies
  ([ASDLC autonomy levels][asdlc]; [Swarmia 5 levels][swarmia]). Diecast's reversibility-keyed L1/L2/L3
  (decide-and-record / decide-record-notify / ask-first) is a *reversibility-indexed* projection of this
  scale. The design payoff: each level has an *established* UI treatment — L1 = silent ledger entry, L2 =
  a notification card, L3 = the **proposal-with-approval** escalation rail. Don't invent three new
  treatments; map to the three the field already knows.

**Patterns verdict:** render the ticket log as a *reviewed PR thread* (inline, severity, confidence,
summary) + a rework-budget meter; render the autonomy gate as the field-standard L3 *propose-and-approve*
card. Both are mature patterns — the originality is in the rework budget and the reversibility keying, not
in re-inventing the components.

### Angle 6 — Contrarian View (the peer-assignee gamble, and the "AI employee" cringe)

Two contrarian shots, both worth taking seriously:

- **Linear's refusal is a warning, not just a difference.** Best-in-class board craft *deliberately* keeps
  a human as primary assignee and demotes the agent to "contributor," because **accountability cannot be
  delegated to something that can't be fired or feel consequences** ([Linear approach][linear-sdk]). If
  Diecast shows an agent as a co-equal assignee with no human owner in frame, a skeptical senior IC (the
  US9 persona) reads it as *toy* — "who do I yell at when this ships a bug?" The contrarian demand:
  **never show an agent as an assignee without its accountability scaffold (paired checker + reversibility
  gate + a human escalation target) visible in the same frame.** The peer seat is earned by the triad, not
  asserted by an avatar.
- **The "AI employee" framing is a cringe minefield.** The digital-worker market (Artisan's "Ava," Lindy,
  Agentforce) leans hard on anthropomorphic "meet your AI employee" theater
  ([TeamDay market map][teamday]; [Artisan][artisan-wiki]; [Salesforce digital worker][sf-digital]). Some
  of it (Goldman onboarding Devin as "employee #1," [IBM][ibm-devin]) is genuinely evocative; much of it is
  HR-cosplay that ages badly. The contrarian guardrail: **borrow the *structure* of employment (résumé,
  hiring committee, onboarding, performance record) but not the *theater* (fake faces, "Ava says hi!",
  personality avatars).** Diecast's brand rules already forbid GPT-isms; extend that to anthropomorphic
  slop. Credibility comes from a *track record*, not a smiling avatar.

**Contrarian verdict:** the peer board is the right bet, but only if every peer-agent carries its
accountability triad in-frame; and the employment metaphor is right structurally but must be rendered with
the sobriety of a performance review, never the cringe of an "AI coworker" mascot.

### Angle 7 — Ops & Observability (operate agents like services, not features)

The agent-observability category (LangSmith, Langfuse, AgentOps) defines the US8 monitoring surface. The
shared anatomy: **hierarchical traces** (every LLM call, tool invocation, retrieval step), filterable by
user/session/cost/latency/metadata; **custom dashboards** for token usage, latency P50/P99, error rates,
cost; **session replays** for multi-step agent runs ([LangSmith][langsmith]; [Langfuse][langfuse];
[AgentOps via aimultiple][aimultiple]). The translation to Diecast US8:

- The agent-detail "monitoring" view = a **run-trace + metrics dashboard**: compliance-rate trend, rework
  loops per run, cost/latency, last-N-runs sparkline — the same shape an SRE sees for a service.
- The dispatch tree in the execution tab (US3 S2's "13 sub-agents") is literally an **agent-trace tree** —
  the LangSmith/AgentOps "multi-step session trace" rendered as Diecast's maker-checker hierarchy.

**Ops verdict:** model the US8 monitoring + US3 execution-tab surfaces on agent-observability dashboards
(traces, replays, metric tiles), so "operating agents looks as manageable as operating services" (US8
intent) is delivered by *adopting the dashboard language SREs already trust*.

---

## 3. The cross-cutting design doctrine (what makes all six surfaces cohere)

Before the per-surface anatomy, four rules that should govern every screen so the set reads as *one
product with colleagues*, not six admin panels:

1. **Identity is always one click away.** Any agent avatar, anywhere (board, activity log, dispatch tree,
   decision record), is a link to its **résumé**. Colleagues are knowable from wherever you encounter them.
2. **Work is always legible, never a black-box badge.** Replace every pass/fail badge with a *reviewable
   record*: the checker's actual comments, the decision's actual rationale, the run's actual trace. US4 S3
   makes this a hard requirement ("show the compliance evidence… not only a pass/fail badge").
3. **The maker-checker pair is the atomic unit, shown together.** US6 S5 is explicit: "a maker's checker is
   never a separate card." This is the single most distinctive Diecast craft move — it visually encodes
   that quality is a *pairing*, not a property. Carry the pair into the board (the checker's verdict rides
   the maker's ticket), the marketplace (paired in-card), and the résumé (paired-checker field).
4. **Accountability rides with autonomy.** Wherever an agent acts, its reversibility gate is in frame: L1
   acts (ledger), L2 acts+notifies (card), L3 asks (rail). This is what licenses the peer-assignee posture
   against Linear's contrarian warning.

---

## 4. Surface-by-surface screen-level design references (the deliverable)

Each surface: **north-star**, **screen anatomy** (concrete elements/layout), **lift list**, **anti-pattern**.

### Surface 1 — Shared board with human + agent peers (US5 S1, FR-010)

- **North-star:** Linear board + GitHub "agents panel"; agent presence model from Linear/Devin.
- **Screen anatomy:**
  - Standard issue board (columns: Backlog / In progress / In review / Done) — *familiar PM chrome on
    purpose* (the radical content is the assignees, not the layout).
  - **Assignee column shows agents and humans in the same avatar stack**, agents marked by a subtle ring/
    glyph (e.g., a hexagon frame) — distinguished, not segregated. The assignee **filter chips**:
    `Any · Human · Agent · Checker` (FR-010 canonical).
  - **In-flight state on the card itself:** a live pill — "🟢 crud-orchestrator · iteration 2/3" — so an
    agent at work is visible without opening the ticket (the Devin "working… mid-run" tell).
  - **Maker-checker pairing on the card:** the maker avatar with the checker avatar tucked behind it (a
    paired-avatar lockup), so the pair reads as one unit (rule 3).
  - **Header framing line:** "Publishes INTO your PM tool" — positions Diecast as feeding the board the team
    already uses, not replacing it (spec language).
  - Top-right: an **escalation inbox** badge ("@you · 1") so blocked work surfaces at board level (US3 S3).
- **Lift:** Linear's avatar-stack + filter chips + column craft; GitHub's "agents panel accessible
  everywhere"; Devin's in-flight progress pill.
- **Anti-pattern (reject):** a separate "Automations" or "Bots" tab; agents shown as a status icon on a row
  rather than as an *assignee*; a board where you can't tell an agent is *currently working*.

### Surface 2 — Ticket maker-checker activity log (US5 S2, US4 S3)

- **North-star:** CodeRabbit/Greptile inline PR-review thread (severity, confidence, one-click fix, PR
  summary); Devin session timeline.
- **Screen anatomy:**
  - **Ticket header:** CAST-412, WHAT one-liner, maker+checker paired-avatar lockup, current state, **rework
    budget meter** ("1 / 3 used" as a 3-segment meter — the dramatic Diecast-original element).
  - **Activity log as a reviewed-PR thread (reverse-chronological):** each checker finding is an **inline
    comment** anchored to the artifact line, tagged with its **rule code** (M04 / S03 / R02) and a
    **severity** + **confidence** (lifted from Greptile). The maker's response/revision threads beneath it.
  - **Iteration bands:** the log visually groups by iteration ("Iteration 1 → 2 findings; Iteration 2 → 0
    findings, passed") so repeat passes are first-class history (FR-007), with an iteration counter.
  - **Compliance evidence block (US4 S3):** the checklist of rules *checked*, passed/flagged inline — not a
    pass/fail badge. Greptile's "auto-generated sequence diagram" is the precedent for showing *how* it was
    verified.
  - **Footer:** resulting **PR link**, and (if the loop hit budget) the **escalation hand-off** to Surface 3.
- **Lift:** CodeRabbit's line-anchored severity comments + concise summary; Greptile's confidence scores +
  call-flow diagram; the iteration-band history idea is Diecast-native.
- **Anti-pattern (reject):** a flat log of timestamps; a single green/red "checker passed" badge with no
  readable findings (explicitly forbidden by US4 S3); hiding repeated passes.

### Surface 3 — Decision artifact + escalation rail (US5 S3/S4, US10)

- **North-star:** ADR (architecture decision record) discipline + the field-standard **L3 propose-and-approve**
  autonomy UX (review dashboard / approval card).
- **Screen anatomy:**
  - **Decision artifact card:** id, **reversibility level (L1/L2/L3)** as a prominent keyed badge, the
    *decision*, *rationale*, *timestamp*, *originating phase/agent*, *consequences*, and `spike_ref` link
    where a spike informed it (US2 S3 linkage). This is an ADR rendered for an agentic context.
  - **Decision trail (US10 S4):** a per-goal cross-phase timeline of decision cards (requirements →
    exploration → planning → execution), filterable, so the "why" behind the black-box is a readable spine.
  - **Escalation rail (US5 S4):** when a decision is L3, the agent **stops** and hands `@you` **exactly three
    pre-framed options** as choice cards (each with its consequence + reversibility), *on the same board*
    (not a modal popped elsewhere). This is the L3 "nothing happens until you say yes" pattern, made
    concrete and bounded to three.
  - **In-context decision chips (US10 S3):** on the canvas/ticket/requirements doc, the relevant decision
    surfaces *in place* as a chip that expands to the full card — decisions live where you'd look for them.
- **Lift:** ADR field structure; the L3 approval-card / review-dashboard convention; reversibility keying is
  Diecast-native (maps the autonomy scale onto consequence-severity).
- **Anti-pattern (reject):** a generic "Approve / Reject" modal with no framed options; a decision log buried
  in execution only (US10 generalizes it to every phase); silent black-box decisions with no record.

### Surface 4 — Hiring flow: assessment → federation → stack-ranked report → hire → onboard (US6)

- **North-star:** Google structured-hiring packet (committee report with evidence) + LMArena/LLM-judge
  side-by-side + eval-kit spider/bar charts.
- **Screen anatomy (a 5-step wizard, each step a distinct screen):**
  1. **Commission assessment:** define tasks spanning **product dimensions** (user scale, internal/external
     software, …) — rendered as a dimension matrix the user can tune, not a blank form. Frames "we will test
     them on *your* problem."
  2. **Federation:** a live "casting the assessment to 5–10 candidates" screen — candidate avatars light up
     as each completes, conveying parallel evaluation (the eval-harness fan-out, made visible).
  3. **Stack-ranked hiring report (the centerpiece):** a leaderboard of candidates by score, each row
     expandable to a **candidate panel** with: a **per-dimension radar chart**, a numeric score, **pros/cons**
     written judge-style, and **deep links to the actual output each candidate produced** (US6 S2 — the
     repo-style "here's what they actually built"). A **head-to-head** toggle compares the top two outputs
     side-by-side (LMArena pattern).
  4. **Hire:** a single decisive action on the winner; shows the maker-checker pair being hired together
     (the checker is part of the hire, not a separate purchase).
  5. **Onboard (US6 S4):** point the new hire at the org's **data sources and tastes** before first use — an
     onboarding checklist ("connect repo · load style guide · set autonomy dial"), framed as "ramping a new
     teammate," not "configuring a tool."
- **Lift:** Google packet's *evidence-backed committee* structure; LMArena head-to-head + reveal; eval-kit
  radar/bar visualizations; the deep-link-to-real-output is the credibility keystone.
- **Anti-pattern (reject):** a SaaS **pricing/feature-comparison grid** (checkmarks across rows) — this is
  the death state the spec warns about; a report with scores but *no link to real produced work*; an
  onboarding step that is just an API-key form.

### Surface 5 — Marketplace credibility + agent résumé (US6 S3, S5)

- **North-star:** Apify Actor store (right-rail metrics, health badge, ratings) + A2A Agent Card (the
  résumé schema).
- **Screen anatomy:**
  - **Marketplace grid:** agent cards, each with a **dense track-record stat line** — the canonical
    "99.9% compliant in 2 maker-checker loops across 505 runs" — plus a **freshness/health badge**
    (active / checker-flagged / benched, mirroring Apify's "under maintenance"), a star rating, and the
    **maker-checker pair shown in-card** (US6 S5 — paired, never two cards). **Archetype facets** down the
    side: Maker / Checker / Decision / Spike / Escalation / Mentor (US6 S5 archetype diversity).
  - **Agent résumé (detail page) = A2A Agent Card, Diecast-superset:** **role**, **I/O contract** (input/
    output modes + examples — straight from the Agent Card's `skills`), **autonomy level**, **paired
    checker** (linked), **benchmark** (the assessment scores + radar), **sample output** (real artifacts),
    and a **track-record panel** (last-N runs, compliance trend, last-active — the Apify metrics rail).
  - **Two catalogues, one card chrome:** public (open Diecast modules) and private (internal tested modules)
    agents use identical card design with a **scope badge** (public / company-wide / private) — the
    discover-and-hire surface is unified (US9 S3 / US8).
- **Lift:** Apify's metrics rail + health badge + ratings + categories; A2A Agent Card's résumé field set;
  the paired-checker-in-card and archetype facets are Diecast-native.
- **Anti-pattern (reject):** cards that show *capabilities/config* but no *track record* (that's a plugin
  listing, not a colleague); a separate card for a checker; anthropomorphic mascot faces standing in for
  evidence (Angle 6 cringe guard).

### Surface 6 — Skill ops + public/private catalogues + Layer-2 (US8, US9)

- **North-star:** Backstage software catalog + Roadie scorecards (operate-like-services); Claude plugin
  marketplace (scope + versioning); agent-observability dashboards (monitoring).
- **Screen anatomy:**
  - **Skill creation:** a near-zero-friction path (US8 S1) — framed as "it can be as simple as a Claude
    command" — with a **private vs company-wide** visibility toggle (= Claude's user vs project scope).
  - **Agent detail / ops page:** **version history** (each version pinned, à la Claude's commit-SHA pinning),
    **usage metrics** (runs, **compliance rate**, **rework loops**), and a **monitoring view** = a
    trace/metrics dashboard (LangSmith/AgentOps language: compliance-trend, cost/latency, last-N-run
    sparkline, session replay into the dispatch tree). Carries a **Backstage-style ownership line + scorecard**.
  - **Unified catalogue (US9 S3):** public + private behind one discover-and-hire browser (Backstage's
    "everything discoverable, no orphans" + Claude's official-plus-custom-marketplaces).
  - **Layer-2 proof surfaces (US9):** a **contract catalogue** (12 named workflow contracts as the
    proof-of-enumerability), an **agent-chain pipeline view** (refine → decompose → research → synthesize →
    plan → detail → orchestrate → run — an 8-node pipeline viz, the agent-trace tree from Angle 7), and a
    **portfolio dashboard** (projects shipped through the workflow — proof by volume, Backstage-portfolio
    shape).
- **Lift:** Backstage catalog + scorecard + ownership; Claude marketplace scope/version/pinning;
  LangSmith/AgentOps trace + metric tiles + replay for monitoring.
- **Anti-pattern (reject):** an agent "settings" page (toggles + text fields) standing in for an ops page;
  versions as a hidden dropdown rather than a history; a monitoring tab that is just a log file.

---

## 5. The decisive tension: peer-assignee (Diecast) vs contributor (Linear) — resolved

This deserves an explicit resolution because it is the design fork that defines the product's nerve.

**The conflict.** Linear — the strongest board craft in the market — *intentionally* will not let an agent
be a primary assignee: delegation keeps "the human user as the primary assignee, the agent as a
contributor… the human remains accountable" ([Linear docs][linear-docs], [Linear SDK approach][linear-sdk]).
The Diecast spec demands the opposite: agents as **peer assignees** with an `any/human/agent/checker`
filter (US5 S1, FR-010). One of them is wrong for Diecast's purpose.

**Why Diecast can — and should — take the bolder posture.** Linear demotes the agent because, in a generic
PM tool, *nothing else carries the accountability* if the agent does. Diecast has three mechanisms Linear
lacks, and together they re-create accountability without a human babysitter on every ticket:

1. **Every maker is paired with a checker** (rule 3, US6 S5) — work is independently reviewed before it
   lands; the green state *means something*.
2. **A rework budget bounds failure** (Surface 2) — an agent gets N attempts, then it *must* escalate; it
   cannot silently churn.
3. **A reversibility gate stops it at L3** (Surface 3, US10) — anything hard-to-undo lands on a human's desk
   as three framed options before it happens.

That triad is the accountability Linear preserves with a human assignee. **Diecast preserves it
structurally instead — and *shows* it in-frame.** So the resolution is not "ignore Linear" but: **build the
peer board Linear won't, and make the accountability triad visible on the same card** (paired checker +
rework meter + reversibility badge). The peer seat is *earned* by the triad. If a future design ever shows
an agent assignee *without* its triad in frame, it has regressed to the toy reading Linear rightly fears —
that is the line to hold.

**Design implication for the mockup:** the board's agent cards must never be just an avatar + status. The
minimum colleague-card = avatar (with agent glyph) + paired-checker lockup + rework meter + reversibility
badge + in-flight pill. That five-element lockup *is* the visual thesis of "agents as accountable
colleagues," and it should recur identically across board, ticket, and résumé.

---

## 6. Anti-pattern catalogue — "if these look like admin CRUD, the vision dies"

A concrete kill-list for the design phase. Each is a way the surface collapses into a tool:

| Surface | The CRUD trap | The colleague move that replaces it |
|---|---|---|
| Board | Agents in a separate "Automations" tab | Agents in the same assignee stack + filter, with in-flight pill |
| Ticket log | A green/red "checker passed" badge | Inline, line-anchored findings with rule codes + severity + rework meter |
| Decision | A generic "Approve/Reject" modal | Three pre-framed, reversibility-keyed option cards on the board |
| Hiring | A feature/pricing comparison grid | Eval report card: head-to-head outputs + radar + deep links to real work |
| Marketplace | A config/capabilities listing | A résumé with a track-record stat line + paired checker in-card |
| Skill ops | An agent "settings" page of toggles | A service-grade ops page: versions, scorecard, trace dashboard |
| Any agent ref | An avatar that goes nowhere | An avatar that opens the résumé (identity always one click away) |
| Whole product | Anthropomorphic "meet your AI employee" mascots | Sober performance-record credibility; structure of employment, none of the cosplay |

The throughline: **CRUD answers "what are this object's fields and actions"; a colleague surface answers
"who is this worker, what did they do, and are they accountable."** Grade every screen against the colleague
test (§TL;DR) before it ships.

---

## 7. Raise-the-bar moves (where to aim *higher* than the references)

The references get us to parity; these get us to "built for the future":

1. **The recurring five-element colleague-card lockup** (avatar+glyph · paired checker · rework meter ·
   reversibility badge · in-flight pill) used *identically* across board, ticket, résumé, and hiring report.
   No competitor has a single visual unit that encodes "accountable agent" — this is Diecast's signature.
2. **Hiring report deep-linked to real produced output**, head-to-head — most "agent marketplaces" show
   capabilities; almost none show *the actual work the candidate did on your task*. This is the strongest
   credibility move available and the spec already asks for it (US6 S2) — lean all the way in.
3. **Rework-budget-as-drama.** A 3-segment meter that fills as a maker-checker loop iterates, then visibly
   *trips the escalation rail* at exhaustion, turns an invisible quality process into a watchable, legible
   story. Nothing in the surveyed tools renders the *cost ceiling* of a quality loop.
4. **One discover-and-hire surface over public+private** that reads identically whether the agent is an open
   Diecast module or an internal tested one (Backstage + Claude-marketplace fused) — collapses the usual
   "internal portal vs public store" split into one motion.
5. **Decision trail as the black-box's readable spine** — a cross-phase timeline of *why* the AI did what it
   did (US10), which directly answers the goal's founding pain ("no one understands it"). This is the trust
   surface that makes the WHAT-primary/AI-blackbox posture safe to ship.

---

## 8. Open items to flag for the design-language pick & plan review

1. **Agent visual marker** — pick the one glyph/treatment that marks "this is an agent" across every avatar
   (hexagon ring vs badge vs color). It must be subtle enough to keep agents *in* the human stack (Angle 1)
   yet unambiguous. Resolve alongside the design-language directions (Step 1).
2. **Anthropomorphism dial** — confirm the sobriety stance (Angle 6): structure-of-employment yes, mascot
   faces no. This affects the marketplace and résumé heavily.
3. **Paired-checker rendering** — settle the paired-avatar lockup once (Surface 1/2/5 all depend on it);
   US6 S5 makes it load-bearing.
4. **Rework-budget meter as a shared component** — it appears on board card, ticket header, and résumé
   track-record; design it once as a reusable element.
5. **Reuse anchors (terrain, not boundary):** the preso v2/v3 slide designs (board arc a08–a11, marketplace
   grid, agent resume, contract catalogue, chain viz — per steps.ai.md Step 4 code-exploration note) are the
   strongest *existing* assets; the code-explorer's terrain map should be diffed against the references here,
   lifting only what already matches the colleague doctrine and rebuilding anything that reads as CRUD.

---

## Sources

**AI-teammate & board craft (primary references for Surfaces 1–3):**
- [Linear for Agents — agents as workspace members][linear-agents]
- [Linear docs — delegation: human stays primary assignee, agent is contributor][linear-docs]
- [Linear — approach to the Agent Interaction SDK (accountability rationale)][linear-sdk]
- [GitHub Copilot coding agent — assign issues, agents panel, asks for review][gh-agent]
- [GitHub blog — coding agent meets the team (async collaborator)][gh-news]
- [Cognition — introducing Devin (teammate progress mid-run)][devin-intro]
- [Devin docs — sessions you pause/resume/share/review][devin-docs]
- [Techpoint — Devin 2.0 IDE/session review][devin-review]
- [IBM — Goldman Sachs onboards Devin as "employee #1"][ibm-devin]

**Maker-checker / AI code review (Surface 2):**
- [CodeRabbit vs Greptile — inline severity comments, confidence, summaries][cr-greptile]
- [Greptile — code graph review, confidence scores, sequence diagrams][greptile]

**Hiring report / eval UX (Surface 4):**
- [Artificial Analysis LLM leaderboard — head-to-head, LMArena pattern][aa-leaderboard]
- AITutor-EvalKit — dimension-wise spider/bar comparison UI (arXiv 2512.03688)

**Marketplace credibility & agent résumé (Surface 5):**
- [Apify Store basics — metrics rail, success rate, health/"under maintenance"][apify-store]
- [Apify academy — credibility metrics as reliability shorthand][apify-academy]
- [Apify review — daily automated health tests][apify-review]
- [A2A Agent Card — the "résumé / business card" schema][a2a-card]
- [A2A discovery — agent card fields, registries, well-known URI][a2a-discovery]
- [IBM — Agent2Agent protocol overview][ibm-a2a]

**Catalogues, scope, ops (Surface 6):**
- [Backstage software catalog — ownership, discoverability, no orphans][backstage]
- [Roadie — Tech Insights scorecards over the catalog][roadie]
- [Claude Code plugin marketplace — user/project scope, SHA-pinned versions, multi-marketplace][claude-plugins]
- [LangSmith — agent observability, traces, metric dashboards][langsmith]
- [Langfuse — hierarchical traces, filtering][langfuse]
- [AI agent observability tools 2026 — AgentOps session traces/replays][aimultiple]

**Autonomy / approval UX (Surface 3, US10):**
- [ASDLC — L1–L5 AI agent autonomy scale][asdlc]
- [Swarmia — five levels of coding-agent autonomy][swarmia]

**Contrarian / "AI employee" market (Angle 6):**
- [TeamDay — 2026 AI-employee market map][teamday]
- [Artisan AI / "Ava" — Wikipedia][artisan-wiki]
- [Salesforce — what is a digital worker][sf-digital]

[linear-agents]: https://linear.app/agents
[linear-docs]: https://linear.app/docs/agents-in-linear
[linear-sdk]: https://linear.app/now/our-approach-to-building-the-agent-interaction-sdk
[gh-agent]: https://github.blog/ai-and-ml/github-copilot/assigning-and-completing-issues-with-coding-agent-in-github-copilot/
[gh-news]: https://github.blog/news-insights/product-news/github-copilot-meet-the-new-coding-agent/
[devin-intro]: https://cognition.ai/blog/introducing-devin
[devin-docs]: https://docs.devin.ai/get-started/devin-intro
[devin-review]: https://techpoint.africa/guide/devin-ai-review/
[ibm-devin]: https://www.ibm.com/think/news/goldman-sachs-first-ai-employee-devin
[cr-greptile]: https://www.getpanto.ai/blog/coderabbit-vs-greptile-ai-code-review-tools-compared
[greptile]: https://www.greptile.com/
[aa-leaderboard]: https://artificialanalysis.ai/leaderboards/models
[apify-store]: https://docs.apify.com/academy/actor-marketing-playbook/store-basics/how-store-works
[apify-academy]: https://docs.apify.com/academy/actor-marketing-playbook/store-basics/how-store-works
[apify-review]: https://use-apify.com/docs/what-is-apify/apify-review
[a2a-card]: https://www.agentcard.net/
[a2a-discovery]: https://a2a-protocol.org/latest/topics/agent-discovery/
[ibm-a2a]: https://www.ibm.com/think/topics/agent2agent-protocol
[backstage]: https://backstage.io/docs/features/software-catalog/
[roadie]: https://roadie.io/blog/3-strategies-for-a-complete-software-catalog/
[claude-plugins]: https://code.claude.com/docs/en/discover-plugins
[langsmith]: https://www.langchain.com/langsmith/observability
[langfuse]: https://langfuse.com/
[aimultiple]: https://aimultiple.com/agentic-monitoring
[asdlc]: https://asdlc.io/concepts/levels-of-autonomy/
[swarmia]: https://www.swarmia.com/blog/five-levels-ai-agent-autonomy/
[teamday]: https://www.teamday.ai/blog/ai-employees-market-map-2026
[artisan-wiki]: https://en.wikipedia.org/wiki/Artisan_AI
[sf-digital]: https://www.salesforce.com/agentforce/digital-worker/
