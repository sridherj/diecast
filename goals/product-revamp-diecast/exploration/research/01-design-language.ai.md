# Step 1 Research — What should Diecast look and feel like? (Design Language)

> **Exploration step:** Step 1 of `exploration/steps.ai.md` — *What are the 2026-grade design
> directions for an AI-native, agentic development workspace?*
> **Resolves / serves:** the `[USER-DEFERRED: design language]` open question (Q#11); FR-019 (consistent
> design system), FR-020 (greenfield, not bound to today's UI), SC-004 (showable without apology),
> FR-018 (brand/vocabulary continuity with preso v3).
> **Author:** cast-web-researcher | **Date:** 2026-06-11 | **Method:** 7-angle research, VISION-FIRST.
> **Audience:** the owner (SJ) — this brief ends in **3 NAMED directions to pick from**, each with
> concrete reference assets worth keeping. Opinionated and cited.

---

## TL;DR — Recommendation

The owner asked for **2-3 named design directions with concrete references to pick from**. Here they are,
as a deliberate spectrum from "safe craft" to "bold future":

1. **`Engineering Workbench`** — Linear-class dark command deck. Near-black canvas, one acid accent used
   as a *status light*, razor-thin type, monospace for system/agent voice, keyboard-/command-palette-first,
   restrained motion. The **lowest-friction** direction: it continues the cast-preso toolkit's existing
   mono+grid+accent craft and matches the eng-primary persona. References: **Linear, Vercel, Raycast, Warp.**
2. **`Studio Clarity`** — light, editorial, document-first. Generous whitespace, a refined sans for the WHAT,
   content as the hero, calm chrome. Optimized for the **2-minute-comprehension** test and the **PM-extensible**
   board/requirements surfaces — warmer and less "hacker" than #1. References: **Notion, Stripe docs, Linear
   light mode, Things 3.**
3. **`Living Canvas`** — the maximal "software built for the future" bet: a spatial/generative workbench where
   the canvas *literally morphs* per workflow family via view transitions, agent work shows as ambient
   streams, and dark glass panels surface AI output. Highest ceiling, highest slop-risk. References:
   **tldraw infinite canvas, Vercel AI SDK generative UI, Thesys C1, Arc, visionOS glass.**

**My opinionated pick: don't pick one — pick a spine and graft.** Build on **`Engineering Workbench` as the
spine** (it's craft-credible, on-brand, and the eng audience reads it instantly), **borrow `Living Canvas`
for exactly one moment** — the FR-004 chat-morphs-canvas fluidity demo, where a spatial view-transition
*earns* the spectacle — and **adopt `Studio Clarity`'s editorial treatment for the document surfaces**
(requirements render US7, the WHAT-first goal card, the board that a PM will read). One token system, three
registers. This directly serves the spec's own "canvas-primary + chat-steered, WHAT-first" thesis, which
maps almost perfectly onto **Linear's own stated "workbench metaphor" for the AI age** ([Linear: Design for
the AI age][linear-ai]).

**The single biggest mistake to avoid:** the 2026 default-AI aesthetic — *dark glassmorphism + gradient
borders + a purple/teal "AI" glow + an anthropomorphic assistant orb*. It is now a cliché ([groovyweb 2026
trends][groovy], [midrocket 2026][midrocket]). Diecast's craft signal is the *opposite*: restraint, real
data, typographic hierarchy, and motion that informs rather than decorates. If a screen looks like every
other "AI app" landing page, it has failed SC-004.

---

## Why this is hard (and what "design language" actually has to decide)

A design language is not a color picker. For this prototype it must settle four things at once:

1. **A register for the human surfaces** (canvas, board, requirements doc) — calm, scannable, WHAT-first.
2. **A register for the machine surfaces** (execution tab, dispatch trees, agent activity, maker-checker
   loops) — dense, legible, status-forward.
3. **A visual grammar for *agency itself*** — how an agent *looks* on a board next to a human, how its
   confidence/autonomy/status reads at a glance, how its work streams without becoming chat scrollback.
4. **A signature motion** — the one thing the prototype must *demonstrate not describe* (FR-004): chat
   reshaping the canvas. That single transition is where "design language" becomes a verb.

The VISION-FIRST framing means the existing cast-server tabs are a terrain map, not a boundary (FR-020).
But the cast-preso visual toolkit (mono type scale, 40px engineering grid, accent/muted token system,
density limits) is *craft already paid for* and brand-continuous (FR-018) — so the question is not "build a
new system" but "which of three coherent worlds do we commit the prototype to, and how much of the toolkit
carries over." (Answer: most of it carries into #1, some into #2, and #3 extends it with motion + spatial.)

---

## Angle 1 — Expert Practitioner (the design-engineering canon that defines "craft" right now)

**There is a named, dominant craft standard in 2026, and it has authors.** Emil Kowalski, Rauno Freiberg,
and Paco Coursey — the design engineers now at Linear — set the bar the whole industry copies; "their
excellence in craft ushered in a new design aesthetic that remains prevalent to this day"
([ui.land][uiland-rauno]). Practitioner consensus, load-bearing for Diecast:

- **Restraint is the signal.** Linear's 2025 redesign *cut color*, swapping "dull monochrome blue … for
  monochrome black/white with even fewer bold colors" — "a midnight command deck … a near-black canvas,
  razor-thin type, and one acid-lime accent that cuts through the dark like a status light"
  ([LogRocket: Linear design][logrocket-linear]). When you strip gradients and shadows, "every remaining
  element must pull its weight functionally" ([Chyshkala][chyshkala]). This is the antidote to AI-slop and
  the exact ethos of the cast-preso checkers (`not-generic`, `not-ai-aesthetic`).
- **Motion is Disney, applied with discipline.** Rauno's "Invisible Details of Interaction Design" treats
  UI motion through classic animation principles — his favorite is *follow-through and overlapping action*
  — and obsesses over "the timing of animations, the physics of motion, and the predictability of gestures"
  ([Rauno: interaction design][rauno-craft]). Emil Kowalski's throughline is **"restraint, speed, and
  purposeful motion"** ([motion-principles][motion-skill]). For Diecast: the canvas-morph must feel like a
  physical object reshaping (mass, easing, overlap), not a slideshow crossfade — but every *other* animation
  should be near-invisible and fast.
- **The 8px system + modular components, not a rigid grid.** Linear uses an 8/16/32/64 spacing scale and
  "a large number of modular components, each designed to present a certain content format in the best way …
  without being constrained by a traditional layout grid" ([LogRocket][logrocket-linear]). This is exactly
  the "block-recipe" model the html-first render research already landed — components composed per workflow
  family, not five hardcoded page layouts.

**Practitioner verdict:** the craft bar Diecast is measured against is *Linear-class restraint authored by
known design engineers*. The fastest path to "showable without apology" (SC-004) is to adopt that canon
explicitly — it is also the canon the cast-preso toolkit already half-implements.

**Sources:** [LogRocket — Linear design][logrocket-linear] · [Rauno — Invisible Details][rauno-craft] ·
[ui.land — Rauno interview][uiland-rauno] · [Chyshkala — Linear dark mode][chyshkala] · [motion principles][motion-skill]

---

## Angle 2 — Tools & Technologies (what the standout dev tools actually look like)

The reference set for "a dev tool with craft" is small and consistent: **Linear, Vercel, Raycast, Warp** —
plus the command-palette lineage they share.

- **The command palette is the shared spine.** It is "a fundamental UI pattern used in Linear, Figma,
  Notion, Vercel, Raycast" — keyboard-first, `Cmd-K`/`Cmd-P`, everything reachable without a mouse
  ([LogRocket — command palette][logrocket-palette-context]). For Diecast this *is* the chat-rail's quiet
  cousin: the canvas is the guided default, the palette/chat is the power lever (the spec's exact posture).
  A command palette is the cheapest, most credible "this is a serious tool" signal.
- **Warp's "UI surface" idea is directly transferable.** Warp built a cohesive dark shell by adding "a white
  overlay aligned with the core text color, creating a consistent 'UI surface' style for all overlay UI
  elements" over a themeable terminal ([Warp — designing themes][warp-themes]). Translation for Diecast:
  define **one elevation/overlay token** (a translucent light wash on dark) used for *every* panel, popover,
  and the chat rail — so chrome reads as one material. Warp also defaults to ~18% transparency and calm
  gray minimal themes (e.g. "Adeberry") rather than neon — restraint again.
- **Raycast = extensions-as-first-class, launched from anywhere.** The Raycast model (a launcher that hosts
  many capabilities behind one fast keyboard surface, triggered ~8×/day from inside other tools
  [Warp×Raycast][warp-raycast]) is the visual analog of Diecast's "skills/agents as a substrate, three
  access tiers" — the UI is a fast shell over a capability registry, never a gate (FR-017).
- **Cursor / Devin / Windsurf set the *agentic-workspace* layout conventions** worth matching or beating:
  Cursor splits a **tab view vs. an agents panel** and even instruments "focus share" between them;
  Windsurf's **Agent Command Center is a unified Kanban** of local + cloud agent sessions, with "Spaces"
  bundling sessions, PRs, files and context around one task; Devin **plans first, then executes in a
  sandbox, coordinating sub-agents and opening PRs** ([MarkTechPost 2026][marktechpost], [Nimbalyst][nimbalyst]).
  These validate the spec's surfaces (board of agent sessions, dispatch trees, execution tab, PR links) as
  *industry-standard*, so Diecast's job is to render them with more craft, not to invent the layout.

**Tools verdict:** the visual vocabulary of a credible 2026 dev tool is **dark, keyboard-first, command-palette-
centered, one-material chrome, restrained color**. Diecast should speak it fluently in the `Engineering
Workbench` direction; the agentic-workspace layout (panel-of-agents, Kanban of sessions, plan-then-execute)
is already conventionalized by Cursor/Windsurf/Devin and should be matched.

**Sources:** [Warp — designing themes][warp-themes] · [Warp×Raycast][warp-raycast] · [MarkTechPost — 2026
agents][marktechpost] · [Nimbalyst — best agents 2026][nimbalyst] · [Cursor product][cursor]

---

## Angle 3 — AI / ML Approaches (generative UI — how the canvas can "morph")

The FR-004 fluidity moment (chat reshapes the canvas) is, technically, **generative UI** — the hottest 2026
interface idea, and it comes with named patterns and a clear "don't" list.

- **"The AI agent is the front end."** GenUI in 2026 means "LLMs compose screens dynamically, guided by intent
  and context" rather than serving fixed layouts ([InfoWorld][infoworld], [knubisoft][knubisoft]). Three
  named approaches now compete: **Google A2UI** (declarative JSON describing *what* to render), **CopilotKit
  AG-UI** (event transport describing *how* agent↔UI messages flow), and **Vercel AI SDK RSC** (server-renders
  React components on the fly via `streamUI`) ([QubitTool — A2UI vs AG-UI vs Vercel][qubit], [Vercel AI SDK][vercel-genui]).
  **Thesys C1** is the productized version: an OpenAI-compatible endpoint that "returns structured UI instead
  of text" — cards, tables, Vega-Lite charts, forms ([Thesys — agentic UI][thesys-agentic], [Thesys C1][thesys-c1]).
- **For a *static* prototype, steal the *grammar* not the runtime.** Diecast's prototype has no backend, so it
  won't call C1 — but the **block-vocabulary** GenUI tools converge on (card / table / chart / form / timeline
  / plan-step) is exactly the component set the prototype should pre-build and *script* the chat to swap. The
  canvas-morph is then a **scripted view-transition between two pre-rendered block recipes**, not real
  generation — visually identical to GenUI, trivially cheap (the spec's own "CSS-transitioned panel swaps
  keyed to scripted chat steps" idea, confirmed by the GenUI literature as the right unit of change).
- **The hard-won AI-native UX rules** (from agent-UX practice) shape how *every* direction renders agents:
  - **Confidence as binary, not numeric** — "binary high-low indicators outperformed numeric percentages …
    users decide faster" ([fuselab — agent UX][fuselab]). → Diecast's classification pill and decision
    records show *high/low* confidence, never "73%".
  - **Activity panel separate from chat** — combining the two "fails as both a conversation and an activity
    tracker" ([fuselab][fuselab]). → This is independent corroboration of the spec's canvas-primary +
    chat-rail split: agent *work* lives on the canvas/execution tab; chat is conversation only.
  - **Plan-and-execute, visible** — show the step list before execution; completed steps check off, active
    steps pulse, steps stay editable ([fuselab][fuselab]). → directly the execution-tab + dispatch-tree
    treatment (US3) and the "nudged next step" (US1).
  - **Transparency / tool-use disclosure** — surface *what options were evaluated and what tools returned*,
    not a black-box output ([fuselab][fuselab]). → the maker-checker evidence and decision rationale (US10).
  - **Progressive delegation** — autonomy expands as trust accrues ([fuselab][fuselab]). → the literal
    mechanic behind US10's reversibility-keyed autonomy dial.

**AI verdict:** generative UI gives Diecast both the *aesthetic permission* to morph the canvas and the
*component grammar* to do it cheaply (scripted block-recipe swaps). And the agent-UX canon (binary confidence,
separate activity panel, visible plans, transparency, progressive delegation) is not Diecast-invented — it is
the 2026 standard, which means the spec's surfaces are well-founded and should be rendered in that idiom.

**Sources:** [InfoWorld — agent is the front end][infoworld] · [Thesys — agentic UI][thesys-agentic] ·
[Vercel AI SDK — generative UI][vercel-genui] · [QubitTool — A2UI/AG-UI/Vercel][qubit] · [fuselab — agent UX][fuselab]
· [knubisoft — AI-native UX 2026][knubisoft]

---

## Angle 4 — Community & Open Source (the agentic-workspace UIs you can actually look at)

The open / near-open tools are the most *concretely studyable* references — real screenshots, real layouts.

- **Vibe Kanban (open source) is the closest visual cousin to Diecast's board.** A "Kanban board for AI
  agents": a board to plan work, **workspaces where an agent runs with a branch + terminal + dev server**,
  **inline diff review with comments without leaving the UI**, a built-in browser preview, and PR creation —
  "trust is good, but verification is better" ([GitHub: vibe-kanban][vibe-gh], [VirtusLab][virtuslab]). This
  is US5 (board→ticket→activity) and US4 (evidence) already built in the wild; lift its information layout,
  beat its visual craft. (Note: Bloop shut down April 2026; project is community-maintained — a reference,
  not a dependency.)
- **Conductor** = "a dashboard next to your existing editor" for Mac ([Nimbalyst — multi-agent][nimbalyst-multi]) —
  the lighter-weight, sit-beside-your-IDE posture; a contrast point for how much chrome Diecast wants.
- **JetBrains Central** frames the whole category as "an open, AI-native system … where humans and agents
  collaborate throughout the full lifecycle" ([JetBrains blog][jetbrains]) — the institutional version of
  Diecast's "agents as colleagues" thesis; useful as positioning air-cover.
- **Microsoft 365 / Teams "agents as teammates"** gives the *interaction* vocabulary: agents that "have 1:1
  interactions … in a group setting," are "invoked through simple slash commands," and respond to "lightweight
  signals like emoji reactions" ([Microsoft 365 dev blog][ms365]). → Diecast's board should render agents as
  *peer assignees* with the same affordances humans get (assign, comment, react), which the spec already
  calls for (US5 Scenario 1).
- **Forum-vs-app debate is live.** The OpenAI community is actively arguing "native app vs web UI vs
  forum-style threads" as the best agent UI ([OpenAI community][openai-forum]) — evidence that the canvas
  vs. chat-thread tension Diecast resolves (canvas-primary) is a genuine open industry question, not a settled
  default. Diecast's opinionated answer is differentiating.

**Community verdict:** Diecast's board/ticket/evidence surfaces have direct open-source precedent (vibe-kanban);
its "agents as peer assignees with human affordances" has platform precedent (Teams/M365); its canvas-primary
stance is a *defensible position in a live debate*, not a me-too. Study vibe-kanban's layout closely; out-craft it.

**Sources:** [GitHub — vibe-kanban][vibe-gh] · [VirtusLab — vibe-kanban][virtuslab] · [Nimbalyst — multi-agent][nimbalyst-multi]
· [JetBrains Central][jetbrains] · [Microsoft 365 — collaborative agents][ms365] · [OpenAI — best agent UI 2026][openai-forum]

---

## Angle 5 — Frameworks & Patterns (named systems, mapped to a Diecast token spec)

| Pattern / system | What it gives | How Diecast uses it |
|---|---|---|
| **Linear "workbench" metaphor** ([Linear AI][linear-ai]) | A structured, bounded space where agents are deployed, run with guidelines, and output is reviewed/approved | The literal frame for the whole product: canvas = workbench, execution tab = where agents run, decisions/escalations = review/approve |
| **8px spacing scale** (Linear) | 8/16/32/64 rhythm | Adopt verbatim; the cast-preso grid already aligns |
| **One-accent / status-light color** (Linear 2025) | Monochrome canvas + a single accent reserved for *state*, not decoration | One accent = "needs you / live / changed". Everything else neutral. Kills AI-slop color |
| **Command palette** (Raycast/Linear/Vercel) | Keyboard-first capability surface | The power-lever next to the canvas; embodies the 3-access-tier story (FR-017) |
| **"UI surface" overlay material** (Warp) | One translucent-on-dark token for all chrome | Chat rail, popovers, panels all share one elevation material |
| **Generative-UI block grammar** (Vercel/Thesys/A2UI) | card/table/chart/form/timeline/plan-step as the unit of generated UI | The pre-built block set the scripted chat-morph swaps between |
| **Plan-and-execute + activity panel** (agent-UX) | Visible editable step list; work-stream separate from chat | Execution tab, dispatch tree, nudged next step (US1/US3) |
| **Binary confidence + progressive delegation** (agent-UX) | High/low not %, autonomy grows with trust | Classification pill, decision records, the autonomy dial (US10/FR-022) |
| **Diátaxis / shape-follows-purpose** (docs world) | Different content types get different structures | Per-workflow-family canvas shapes; per-family requirement render (US2/US7) |
| **cast-preso visual toolkit** (in-repo) | mono type scale, 40px engineering grid, accent/muted callout vs question-annotation, density limits | The reusable token/CSS layer all three directions inherit (FR-018) |

**Token-spec recommendation (works for all 3 directions, re-skinned):**
`--bg` (canvas), `--surface` (one overlay material), `--text` / `--muted` (two type tiers), `--accent` (the
single status light), `--maker` / `--checker` (a paired hue for the quality unit, used *only* on agent
chrome), plus the 8px scale and the mono/sans pairing. A direction = a *re-theme* of these tokens, not a
new system — which is what makes "pick one, graft the others" cheap.

**Patterns verdict:** Diecast is not inventing a design language; it is *composing* the Linear workbench
metaphor + 8px/one-accent restraint + command-palette + Warp's one-material chrome + GenUI block grammar +
the agent-UX canon, all expressible as a single token system the cast-preso toolkit already half-ships.

**Sources:** [Linear — Design for the AI age][linear-ai] · [LogRocket — Linear][logrocket-linear] ·
[Warp themes][warp-themes] · [Vercel AI SDK][vercel-genui] · [fuselab — agent UX][fuselab]

---

## Angle 6 — Contrarian View (where each direction fails, and the slop to avoid)

- **The #1 risk is the 2026 AI-slop default.** "Glassmorphism has evolved into … dark base surfaces
  (#0A0A0A–#1A1A2E) with translucent frosted panels … gradient borders and soft shadows" as the *generic*
  AI look ([groovyweb][groovy], [midrocket][midrocket]). If `Living Canvas` leans on dark-glass + gradient
  glow + an assistant orb, it becomes indistinguishable from every AI landing page — the exact opposite of
  SC-004. **Guardrail:** glass is allowed on *at most one* surface (the AI-output panel), never as the global
  chrome; no gradient borders; no glow; no anthropomorphic orb.
- **Generative/morphing UI can erode trust and learnability.** If the canvas reshapes too freely, users
  "re-learn the page each time" and the scannability the WHAT-first thesis depends on collapses (the same
  critique the html-first render research raised about over-varied family layouts). **Guardrail:** morph
  *between a small fixed set of family shapes*, with consistent block grammar inside each — variation in
  *which blocks appear*, consistency in *how each block looks*. The morph is a scripted, bounded transition,
  not free generation.
- **Dark-only (`Engineering Workbench`) underserves the PM-extensible surfaces.** A near-black command deck is
  perfect for eng/execution and alienating for the board/requirements doc a PM reads (the secondary persona,
  US7's PM commenter). **Guardrail:** the document/board register needs `Studio Clarity`'s light, editorial
  treatment — which is *why the recommendation is a hybrid, not a single dark world*.
- **Motion is the cheapest way to look amateur.** Emil Kowalski's whole thesis is restraint; over-animation
  reads as toy, not tool. **Guardrail:** exactly one signature motion (the canvas-morph); everything else
  ≤150ms, ease-out, near-invisible. No spinners-as-personality, no parallax, no decorative loops.
- **"Beautiful" that is slower to read than plain text is negative value.** SC-002 (a stranger understands the
  product in ~3 min) is a *comprehension* test; polish that fights the scan fails it. The cast-preso
  `not-generic` / `not-ai-aesthetic` checkers exist to catch exactly this and should gate the prototype's
  screens.
- **Over-indexing on Linear is its own trap.** Linear-clone is now a recognizable, slightly-tired SaaS trope
  ([LogRocket: "boring and bettering"][logrocket-linear]). Diecast's *differentiator* is the agent-colleague
  grammar (maker/checker pairing, autonomy dial, hiring report) — the design language must give *that* its own
  identity, not just reskin Linear's issue tracker.

**Contrarian verdict:** every direction has a specific failure mode (slop-glass for #3, dark-only-alienates-PM
for #1, re-learn-the-page for free morph). The hybrid recommendation exists precisely to take each
direction's strength where it's safe and avoid each one's failure where it isn't.

**Sources:** [groovyweb — 2026 AI trends][groovy] · [midrocket — 2026 UI trends][midrocket] ·
[LogRocket — Linear design][logrocket-linear] · [knubisoft — AI-native UX][knubisoft]

---

## Angle 7 — First Principles (reduce "look and feel" to its irreducible jobs)

Strip away references: a design language for *this* product exists to do four irreducible jobs, and the right
language is the one that does all four with the least decoration.

1. **Make the WHAT graspable in one glance.** → demands typographic hierarchy + restraint + one accent for
   state. (This is `Studio Clarity` on the doc surfaces, `Engineering Workbench` on the canvas.)
2. **Make agency legible.** A human must see, without reading, *who is acting (human/agent/checker), how sure
   it is (high/low), how autonomous it's allowed to be (L1/L2/L3), and whether it needs them.* → demands a
   dedicated agent-chrome grammar: a paired maker/checker hue, a binary-confidence mark, a status-light
   accent that means "needs you." This is the part *no existing tool fully solves* — Diecast's real design
   contribution.
3. **Make change visible.** The product's whole thesis is fluidity (FR-004/FR-007): course-changes, iteration
   history, requirement versions, decisions over time. → demands *motion as meaning* (the canvas-morph) and
   *history as a first-class visual* (iteration counters, version pills, decision trails) — not hidden state.
4. **Be showable without apology.** (SC-004) → demands the craft canon (Linear-class restraint, real data,
   no slop) as a non-negotiable floor, independent of which direction wins.

**The irreducible verdict:** "look and feel" reduces to *restraint + hierarchy for the WHAT, a purpose-built
grammar for agency, and motion-as-meaning for change.* Color/theme (dark vs light) is the most *negotiable*
layer — which is why three directions can share one token system and differ only in register. The
**non-negotiable** is the agent-colleague grammar and the no-slop floor; the **negotiable** is which world
(deck / studio / canvas) the owner wants to *feel* like.

**Sources:** synthesis of Angles 1–6; [Linear — Design for the AI age][linear-ai]; cast-preso visual toolkit (repo).

---

## The 3 named directions (the deliverable — pick from these)

Each is a coherent world. All inherit the same token spec (Angle 5) and the same no-slop floor; they differ
in register, color, and how much motion/spatial they spend.

### Direction A — `Engineering Workbench`  *(recommended spine)*

> **Feel:** a Linear-class midnight command deck for building software with a team of agents.
> **Color:** near-black canvas (`#0B0C0E`-ish), neutral grays, **one acid accent reserved for state**
> (needs-you / live / changed). Maker/checker get a single paired hue, used only on agent chrome.
> **Type:** a crisp grotesque sans for the WHAT, **monospace for system/agent voice** (run logs, decision
> IDs like `CAST-412`, `M04/S03/R02`), continuing the cast-preso mono identity.
> **Chrome:** one translucent-on-dark "UI surface" material (Warp) for the chat rail, popovers, panels.
> **Interaction:** command-palette-first; keyboard-driven; restrained ≤150ms motion everywhere except the
> one signature morph.
> **Best at:** the canvas, execution tab, dispatch trees, board, marketplace — the eng-primary surfaces.
> **Weak at:** PM-facing document reading (too dark/dense) → graft Direction B there.
> **Why recommend as spine:** lowest build friction (extends the cast-preso toolkit), most craft-credible to
> the primary audience, on-brand with preso v3 (FR-018).
> **Keep-these references:** Linear app + [linear.app/now][linear-ai] essays · Raycast · Warp · Vercel
> dashboard · Rauno's [Invisible Details][rauno-craft] (motion bible).

### Direction B — `Studio Clarity`

> **Feel:** a calm editorial studio — the WHAT reads like a beautifully typeset brief, not a terminal.
> **Color:** light/warm-neutral base, ink text, the *same single accent* for state; lots of whitespace.
> **Type:** a refined sans (or a sans/serif pairing) sized for comfortable reading; generous line-height.
> **Chrome:** minimal, near-invisible; content is the hero (Notion/Stripe-docs lineage).
> **Interaction:** document-like, progressive-disclosure (`<details>`), inline comments — directly serves
> the html-first render + requirements-loop research and the 2-minute-comprehension test (SC-002).
> **Best at:** requirements doc (US7), the WHAT-first goal card, the shared board a **PM** reads, evidence
> reports.
> **Weak at:** dense execution/agent-ops surfaces (light + airy hides density signal) → graft Direction A there.
> **Why offer:** it is the PM-extensibility direction and the comprehension-optimized one; if the owner wants
> Diecast to feel *approachable and document-first* rather than *hacker-deck*, this leads.
> **Keep-these references:** Notion · Stripe docs (layered disclosure) · Linear light mode · Things 3 (calm
> craft) · Diátaxis (shape-follows-purpose).

### Direction C — `Living Canvas`

> **Feel:** software built for the future — a spatial, generative workbench where the canvas is alive and the
> agents are ambient presences around your work.
> **Color:** dark base with **one** dark-glass output panel (strictly bounded — see slop guardrail); the
> accent does more work as motion/light.
> **Type:** as A, but motion carries more meaning.
> **Chrome:** spatial — an infinite/zoomable canvas (tldraw lineage); panels that arrive and reshape with
> physical view-transitions; agent activity as ambient streams, not chat lines.
> **Interaction:** the **FR-004 fluidity moment is the centerpiece** — chat says "this is a bug, not a
> feature" and the canvas *physically morphs* from the feature backbone to the debug loop (mass, easing,
> follow-through). Generative-UI block grammar (card/chart/timeline/plan-step) is the unit that swaps.
> **Best at:** the one demo moment that must be *felt* (SC-003); a wow opening for external showings.
> **Weak / risky at:** everything-everywhere — full-time spatial canvas is exhausting and slop-prone; this is
> a *spice*, not a *staple*.
> **Why offer:** it is the maximal "unconstrained vision" bet the framing invites; even if not chosen
> wholesale, **its morph belongs in the final prototype as the signature moment.**
> **Keep-these references:** tldraw ([tldraw.dev][tldraw]) · Vercel AI SDK generative UI ([ai-sdk.dev][vercel-genui])
> · Thesys C1 ([thesys.dev][thesys-c1]) · Arc browser · visionOS spatial (translucency *done with restraint*).

### Recommendation in one line

**Ship `Engineering Workbench` as the spine, render document/board surfaces in `Studio Clarity`, and spend
`Living Canvas` on exactly the one chat-morphs-canvas moment.** One token system, three registers — which the
spec's own canvas-primary/WHAT-first/fluidity thesis already implies.

---

## Curated inspiration assets worth keeping (the reference library)

| Asset | Type | Why keep it | Direction |
|---|---|---|---|
| **Linear app + linear.app/now essays** ([Design for the AI age][linear-ai], [redesign part II][linear-redesign], [Liquid Glass][linear-glass]) | live product + essays | The workbench metaphor + the craft canon, stated by its authors | A (spine) |
| **Rauno — Invisible Details of Interaction Design** ([rauno.me/craft][rauno-craft]) | essay | The motion/interaction bible for the signature morph | A, C |
| **Emil Kowalski — animations.dev / motion principles** ([skill][motion-skill]) | course/skill | Restraint-first motion discipline | all |
| **Warp — How we designed terminal themes** ([warp.dev blog][warp-themes]) | case study | The "one UI-surface material" chrome trick | A |
| **Raycast** | live product | Command-palette-as-substrate, extensions-first | A |
| **Vibe Kanban** ([GitHub][vibe-gh]) | open-source UI | Closest studyable board→workspace→diff layout | A |
| **Notion / Stripe docs** | live products | Layered, document-first clarity for the WHAT/PM surfaces | B |
| **tldraw** ([tldraw.dev][tldraw]) | SDK/demos | Infinite-canvas + sketch-to-UI; the spatial morph reference | C |
| **Vercel AI SDK generative UI / Thesys C1** ([ai-sdk.dev][vercel-genui], [thesys.dev][thesys-c1]) | docs/product | The GenUI block grammar the morph swaps between | C |
| **fuselab — UI design for AI agents** ([article][fuselab]) | reference | The agent-UX pattern catalog (confidence, activity panel, plan-execute) | all |
| **cast-preso visual toolkit** (in-repo) | code/tokens | The reusable token + type-scale + grid layer to extend | all |

**Video/dynamic references to collect (owner action):** Linear's product launch / "now" announcement videos
(craft + motion); Warp and Raycast product demos (command-palette feel); any tldraw "draw-a-ui" demo (spatial
morph); a Cursor/Windsurf agent-panel walkthrough (agentic-workspace layout). These are best *watched* for
motion timing, which static screenshots can't convey — flagged as the one inspiration-gathering step that
needs the owner's eyes, not just links.

---

## Open items to flag for the playbook synthesizer / owner

1. **Pick the register split.** Recommendation: A spine + B for docs/board + C for the one morph. Confirm,
   or collapse to a single world if the owner wants less variance.
2. **Dark vs light default.** A is dark-primary; B is light. If the owner wants *one* mode only, that choice
   forces the register split (dark-only sacrifices PM comprehension; light-only sacrifices the eng-deck
   credibility). Recommend dual-register over single.
3. **How much spatial/morph.** Confirm `Living Canvas` is a *spice* (one moment), not the staple — the
   contrarian angle argues full-time spatial is slop-prone and tiring.
4. **The agent-colleague grammar is the real net-new design work** (maker/checker hue, binary-confidence mark,
   autonomy-level chip, needs-you status light). No existing tool fully solves it; budget design time here,
   not on theme-picking.
5. **Slop guardrails are non-negotiable** regardless of direction: no gradient-border glass chrome, no AI-glow,
   no assistant orb, one signature motion only, real data not lorem. Wire the cast-preso `not-generic` /
   `not-ai-aesthetic` checkers as the prototype's screen gate.

---

## Sources

**Codebase / prior-step (primary):**
- `exploration/steps.ai.md` (Step 1 charter), `refined_requirements.collab.md` v0.3.0 (Intent, US1/US5/US6/US10,
  FR-004/017/018/019/020, SC-002/004), the html-first-render research note (block-recipe model, 2-minute test,
  cast-preso toolkit inventory).
- cast-preso visual toolkit (`skills/.../cast-preso-visual-toolkit`, `templates/css/{theme,typography,components}.css`)
  — token system, type scale, density limits, `not-generic`/`not-ai-aesthetic` checkers.

**Web (external corroboration):**
- [Linear — Design for the AI age][linear-ai]
- [Linear — How we redesigned the UI (part II)][linear-redesign]
- [Linear — A Linear spin on Liquid Glass][linear-glass]
- [LogRocket — Linear design: boring and bettering][logrocket-linear]
- [Chyshkala — Why Linear design systems break in dark mode][chyshkala]
- [Rauno Freiberg — Invisible Details of Interaction Design][rauno-craft]
- [ui.land — Rauno Freiberg interview][uiland-rauno]
- [Design Motion Principles (Kowalski/Krehel/Tompkins)][motion-skill]
- [Warp — How we designed themes for the terminal][warp-themes]
- [Warp × Raycast store][warp-raycast]
- [Cursor — product][cursor]
- [MarkTechPost — AI coding agents & platforms 2026][marktechpost]
- [Nimbalyst — best AI coding agents 2026][nimbalyst]
- [Nimbalyst — best multi-agent coding tools 2026][nimbalyst-multi]
- [GitHub — BloopAI/vibe-kanban][vibe-gh]
- [VirtusLab — vibe-kanban: a Kanban board for AI agents][virtuslab]
- [JetBrains — Introducing JetBrains Central][jetbrains]
- [Microsoft 365 dev — Build collaborative agents][ms365]
- [OpenAI community — Best agent UI in 2026][openai-forum]
- [InfoWorld — Generative UI: the AI agent is the front end][infoworld]
- [Thesys — Agentic UI: frameworks, protocols, patterns][thesys-agentic]
- [Thesys — C1 generative UI][thesys-c1]
- [Vercel AI SDK — Generative User Interfaces][vercel-genui]
- [QubitTool — A2UI vs AG-UI vs Vercel AI SDK][qubit]
- [fuselab — UI design for AI agents (agent UX 2026)][fuselab]
- [knubisoft — AI-native UX in 2026][knubisoft]
- [groovyweb — 12 UI/UX trends for AI apps 2026][groovy]
- [midrocket — UI design trends 2026][midrocket]
- [tldraw — Infinite Canvas SDK][tldraw]

[linear-ai]: https://linear.app/now/design-for-the-ai-age
[linear-redesign]: https://linear.app/now/how-we-redesigned-the-linear-ui
[linear-glass]: https://linear.app/now/linear-liquid-glass
[logrocket-linear]: https://blog.logrocket.com/ux-design/linear-design/
[chyshkala]: https://chyshkala.com/blog/why-linear-design-systems-break-in-dark-mode-and-how-to-fix-them
[rauno-craft]: https://rauno.me/craft/interaction-design
[uiland-rauno]: https://ui.land/interviews/rauno-freiberg
[motion-skill]: https://github.com/kylezantos/design-motion-principles
[warp-themes]: https://www.warp.dev/blog/how-we-designed-themes-for-the-terminal-a-peek-into-our-process
[warp-raycast]: https://www.raycast.com/warpdotdev/warp
[logrocket-palette-context]: https://blog.logrocket.com/ux-design/linear-design-ui-libraries-design-kits-layout-grid/
[cursor]: https://cursor.com/product
[marktechpost]: https://www.marktechpost.com/2026/06/10/ai-coding-agents-development-platforms-2026/
[nimbalyst]: https://nimbalyst.com/blog/best-ai-coding-agents-2026/
[nimbalyst-multi]: https://nimbalyst.com/blog/best-multi-agent-coding-tools-2026/
[vibe-gh]: https://github.com/BloopAI/vibe-kanban
[virtuslab]: https://virtuslab.com/blog/ai/vibe-kanban
[jetbrains]: https://blog.jetbrains.com/blog/2026/03/24/introducing-jetbrains-central-an-open-system-for-agentic-software-development/
[ms365]: https://devblogs.microsoft.com/microsoft365dev/build-collaborative-agents-where-work-happens/
[openai-forum]: https://community.openai.com/t/what-s-the-best-agent-ui-in-2026-native-app-web-ui-or-forum-style-threads/1375720
[infoworld]: https://www.infoworld.com/article/4110010/generative-ui-the-ai-agent-is-the-front-end.html
[thesys-agentic]: https://www.thesys.dev/blogs/agentic-ui
[thesys-c1]: https://www.thesys.dev/
[vercel-genui]: https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces
[qubit]: https://qubittool.com/blog/a2ui-vs-ag-ui-vercel-agent-ui-comparison
[fuselab]: https://fuselabcreative.com/ui-design-for-ai-agents/
[knubisoft]: https://knubisoft.medium.com/ai-native-ux-in-2026-a-builders-guide-97cdb2ef1a7b
[groovy]: https://www.groovyweb.co/blog/ui-ux-design-trends-ai-apps-2026
[midrocket]: https://midrocket.com/en/guides/ui-design-trends-2026/
[tldraw]: https://tldraw.dev/
