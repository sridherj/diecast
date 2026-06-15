# Step 2 Research — Canvas + Chat Steering Mechanics (morph · nudge · promote · drill-in)

> **Exploration step:** Step 2 of `exploration/steps.ai.md` — *How should an opinionated canvas +
> chat steering actually behave so it feels fluid, not gimmicky?*
> **Locked model it serves:** canvas-primary WHAT-first workspace (FR-003) with a persistent chat rail
> that can visibly MORPH the canvas (FR-004), promotable chat artifacts (FR-005), WHAT-primary with
> HOW drill-in (FR-008), three access tiers terminal/chat/canvas over one substrate (FR-017).
> **Author:** cast-web-researcher | **Date:** 2026-06-11
> **Audience:** the playbook synthesizer + owner. This is a *decision-ready* interaction-model brief,
> written for a **static HTML clickable prototype** (no backend, scripted chat moments).

---

## TL;DR — The interaction model in one breath

The entire 2025–2026 field has converged on one shape, and it is exactly the shape the spec already
locked: **a persistent, intentionally-designed canvas is the source of truth; chat is an ephemeral
command rail that mutates and augments that canvas; the agent never free-generates UI — it emits
*typed intents* against a UI vocabulary the product controls.** Every serious voice says the same
thing from a different direction — Vercel paused its free-form RSC generative-UI track and now
recommends client-rendered tool parts; Shopify's MCP-UI thesis is *"agents shouldn't generate UIs
themselves… components bubble up intents the agent interprets"*; Google's A2UI renders only from a
*trusted widget catalog*; Geoffrey Litt calls chat *"slow, imprecise"* and argues for
direct-manipulation-primary with the LLM as a secondary modification loop; InfoWorld's own
"the agent is the front end" piece is openly skeptical that users want a UI regrown every session.

**The four mechanics, each as a concrete spec:**

| Mechanic | One-line model | Native primitive | Headline precedent | Headline anti-pattern |
|---|---|---|---|---|
| **Morph** | Chat course-change reshapes the canvas via a *shared-element* transition that preserves goal identity | CSS **View Transitions API** + `view-transition-name` | Material **Container Transform**; Apple **Dynamic Island** | Jarring hard swap (no shared identity) → cognitive reload; morph without undo |
| **Nudge** | Exactly one visually-dominant "recommended next step" per screen; every override path stays open & cheap | Primary/secondary/tertiary button hierarchy + ghost suggestion | **Linear** "one good way"; Copilot **Next Edit Suggestions**; Rails "sharp knives" | Competing equal-weight CTAs; forced/no-exit flow; over-nudging → alert fatigue |
| **Promote** | An *explicit, named* gesture lifts an ephemeral chat artifact into a durable, versioned canvas object | Tool-call → developer-authored component, then "pin" | Claude **Artifacts**, ChatGPT **Canvas**, NotebookLM **"Save to note"** | Lost-in-scrollback; artifact divergence (stale source of truth); auto-promote clutter |
| **Drill-in** | WHAT (outcome/state/evidence) above the fold; HOW (runs, dispatch tree, maker-checker) behind ≤2 disclosure levels | Progressive disclosure / master-detail tab | NN/g progressive disclosure; **Cursor** file-by-file diff drill | >2 disclosure levels ("users get lost"); hiding human-needed escalations inside HOW |

**The binding rule that ties all four together (the keystone):** the canvas is driven by *typed
events*, not by the model painting pixels. A chat turn resolves to one of a **small, named set of
canvas operations** — `morph(family)`, `nudge(step)`, `promote(artifact)`, `drillInto(node)`,
`pin(object)`. In the real product these are tool calls (CopilotKit `useCopilotAction` / Vercel
`streamUI` / AG-UI `TOOL_CALL_*` events / A2UI JSON). **In the static prototype they are scripted
step IDs** — a `data-step` attribute on each canned chat line that triggers the same canvas operation
deterministically. This makes the fluidity *demonstrable, not described* (SC-003) while keeping the
build a no-backend HTML file.

**The one risk to retire by design:** mode confusion across three surfaces ("did my chat edit land
in the canvas? is the canvas authoritative or is chat?"). Antidote, applied everywhere below: the
canvas is *always* the visible source of truth, chat actions produce a *visible canvas change plus a
receipt*, and nothing important lives only in scrollback.

---

## How the spec's locked moment maps to the mechanics

> US1 independent test: *"Type 'this is actually a bug, not a feature' in chat; the canvas visibly
> morphs from feature stages to the debug-loop shape without losing goal context."*

That single sentence exercises **all four mechanics in sequence**, which is why this is the core
thesis demo:
1. The goal opens showing the feature canvas with a **nudged** next step (FR-003).
2. The chat line is a **binding** event that resolves to `morph(debug)`.
3. The canvas **morphs** — shared elements (goal title, decisions, evidence) glide; feature stages
   crossfade out, hypothesis→experiment→observation fades in (FR-004).
4. The morph emits a **decision receipt** ("reclassified feature→bug") that is **promotable**/pinned
   and surfaced in-context (US10), and the debug canvas keeps a **drill-in** to the underlying runs.

Get this one transition right and the prototype proves its claim. The rest of the report specs each
mechanic to make that transition (and its three siblings) feel inevitable rather than gimmicky.

---

## Mechanic 1 — MORPH (chat course-change reshapes the canvas)

**Concrete interaction model.** A chat steering message resolves to `morph(targetFamily)`. The canvas
does **not** hard-swap; it runs a **shared-element transition** in which the elements that are
*conceptually the same object across both shapes* (the goal header, the decision trail, the evidence
strip, the chat rail itself) keep their identity and visibly glide/resize into their new positions,
while the *family-specific* stage structure crossfades (feature `req→explore→plan→execute` out,
debug `hypothesis→experiment→observation + iteration counter` in). Duration **~300–450ms** — the
Dynamic Island sweet spot: fast enough to feel responsive, slow enough to track. A short toast/receipt
confirms *what changed and why* ("Reclassified as bug — debug loop"), and the morph is **undoable**.

**Native primitive (real product) / cheapest fake (prototype).** The **CSS View Transitions API**
is the canonical tool and reached *Baseline newly-available* for same-document (SPA) transitions in
Oct 2025 (Chrome/Edge 111+, Safari 18+, Firefox 144+). `document.startViewTransition(() =>
swapCanvasState())` snapshots old + new DOM and interpolates between them; tag the persistent nodes
with `view-transition-name` so they morph position/size/shape rather than crossfade. For the static
prototype this is **~20 lines of zero-dependency JS keyed to scripted steps** — keep both canvas
layouts in the DOM, toggle a class inside the transition callback, put `view-transition-name` on the
3–4 anchor elements that persist. Fallback for unsupported/`prefers-reduced-motion`: an
opacity/transform crossfade (Material "Fade Through"). FLIP (Paul Lewis) and Framer Motion
`layout`/`layoutId` are the React-idiom equivalents if the real product goes that way.

**Named precedents.** Apple **Dynamic Island** — the definitive "one persistent container, inner
content swaps, outer shape fluidly resizes" study (compact↔banner↔card in ~0.3–0.5s). Material
Design **Container Transform** — the named pattern for "one thing turns into another" with a shared
outer container; its sibling rules (**Shared Axis** for related steps, **Fade Through** for unrelated
content) give the decision rule for *which* transition to use. **Arc** Spaces — per-context theming +
soft transitions signal "you changed context" without a reload. **Linear/Raycast** — command-driven
view switching where *speed > spectacle* (the right register for a power tool).

**Anti-patterns (do-not-do).**
- **Hard swap with no shared identity** → reads as two screens replacing each other, a cognitive
  reload. Always carry anchor elements across (the antidote *is* the shared-element morph).
- **Morph that hides structure** — a long, showy animation that obscures where things landed. Motion
  must *reveal* the new layout, not perform; keep it <500ms.
- **Morph without undo / un-addressable prior state** — NN/g "apple picking"/accordion-editing and
  the *Keyhole Effect* (arXiv 2602.00947) warn that users fear "did I lose my context?" Every morph
  must be reversible and the previous shape referenceable.
- **Surprise / consistency violation** (Nielsen) — never morph *unprompted*; a morph is always the
  visible consequence of an explicit user steer.
- **Motion sickness** — ~35% of adults 40+ have vestibular sensitivity; gate behind
  `prefers-reduced-motion` (WCAG 2.3.3), degrading to a sub-200ms fade.

*Refs:* MDN View Transitions `https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using` ·
Chrome 2025 update `https://developer.chrome.com/blog/view-transitions-in-2025` ·
web.dev Baseline `https://web.dev/blog/same-document-view-transitions-are-now-baseline-newly-available` ·
Material motion `https://m2.material.io/design/motion/the-motion-system.html` ·
Dynamic Island `https://arounda.agency/blog/what-is-dynamic-island-apple-and-how-to-use-it` ·
FLIP `https://css-tricks.com/animating-layouts-with-the-flip-technique/` ·
Framer Motion layout `https://motion.dev/docs/react-layout-animations` ·
Keyhole Effect `https://arxiv.org/pdf/2602.00947` ·
prefers-reduced-motion `https://web.dev/articles/prefers-reduced-motion`.

---

## Mechanic 2 — NUDGE (opinionated default next step, never a gate)

**Concrete interaction model.** Every canvas screen surfaces **exactly one visually-dominant
"recommended next step"** — a filled/high-contrast primary action that says what to do *and why now*
("Run exploration → 3 open questions block planning"). Secondary actions recede (tinted/outline);
override paths — chat, manual navigation, the execution tab — stay always-present and low-friction.
The nudge is a **suggestion, not a wall**: doing nothing or picking a sibling action costs nothing,
and a power user bypasses it entirely via chat or the terminal. This is the operational meaning of
the spec's "opinionated product, meaningful defaults" + "never a gate" (FR-003, FR-017).

**The defaults-are-the-design principle.** Thaler & Sunstein: a nudge "alters behavior predictably
*without forbidding any options*" and must be "easy and cheap to avoid." The product analog is
choice architecture: pre-select the sensible path, keep all others reachable. The failure modes sit
at both extremes — the **buffet** (no default → paralysis) and the **cage** (one path, forced flow →
dark pattern). The nudge lives in the middle: many options, one obviously recommended.

**Named precedents.** **Linear** — "we design it so there's one really good way of doing things,"
*graduated* opinion (most opinionated on atomic properties, looser on structure), keyboard shortcuts
as the always-open override. **Rails** "convention over configuration" + **"provide sharp knives"** —
the canonical "opinionated yet never locks you in" doctrine; escape hatches remain for the expert.
**Golden Paths / Paved Roads** (Spotify/Netflix) — the dev-tools analog: a recommended default stack
with "room for walking outside the beaten paths" (the directly-applicable model for an agentic tool).
**Superhuman** — opinionated onboarding with *self-removing training wheels* (enlarged labels vanish
after 7 days). **GitHub Copilot Next Edit Suggestions** — the reference *AI* nudge: dimmed ghost
suggestion + gutter arrow, **Tab to accept, ignore to dismiss** — salient, recommended, trivially
avoidable.

**Anti-patterns.**
- **Competing equal-weight CTAs** — no nudge survives two primaries (Apple HIG / Material: one
  preferred action per screen).
- **Misleading salience** — styling a *destructive/irreversible* action as the primary, or
  over-selling certainty on an AI suggestion that may be wrong (automation bias / rubber-stamping).
- **Forced flows / buried escape hatches** — a wizard with no skip, or an override that technically
  exists but is undiscoverable = functionally a cage.
- **Over-nudging → alert fatigue** — repeated suggestions get tuned out; nudge sparingly.
- **Confirmation-friction backfire** — a 2025 study (arXiv 2509.08514) found *adding* friction to
  override paths *increased* wrong-acceptance. Keep the override cheaper than the mistake.

*Refs:* Linear Method `https://www.figma.com/blog/the-linear-method-opinionated-software/` ·
Rails Doctrine `https://rubyonrails.org/doctrine` ·
Thoughtworks golden paths `https://www.thoughtworks.com/insights/blog/platforms/nudge-your-way-to-better-engineering-platforms` ·
Superhuman `https://www.growthmates.news/p/onboarding-lab-how-superhuman-and` ·
Copilot NES `https://code.visualstudio.com/blogs/2025/02/12/next-edit-suggestions` ·
Apple HIG buttons `https://developer.apple.com/design/human-interface-guidelines/buttons` ·
nudge vs dark patterns `https://uxplanet.org/dark-patterns-versus-behavioural-nudges-in-ux-e79633970b3f`.

---

## Mechanic 3 — PROMOTE (chat artifact → durable canvas object)

**Concrete interaction model.** Two surfaces, one source of truth: **chat is the ephemeral command
log; the canvas/panel is the durable object.** When chat produces something worth keeping (a hiring
report, a spike conclusion, a chart), it appears as an **artifact card in the rail** with an
**explicit, named promote gesture** — "Pin to canvas" / "Save to goal" — that lifts it into a
persistent, **versioned** canvas object carrying its provenance (which chat turn / agent / time made
it). Promoted objects get a back-reference; the chat keeps a lightweight stub ("Pinned ✓"). This is
FR-005 and US1 Scenario 3.

**Make the gesture explicit, not automatic.** The strongest precedents split on this and the explicit
camp wins for an opinionated tool: NotebookLM's **"Save to note"** (answers are ephemeral until you
click — *designs against lost-in-scrollback*), Notion AI's **"Insert below"** (turns ephemeral output
into a real editable block), Cursor/Windsurf's **"Keep Changes" / accept-diff** (a staging gate before
the durable file changes). Auto-promote (ChatGPT Canvas auto-opening, FigJam dropping shapes straight
onto the board) trades predictability for speed and creates mode confusion + canvas clutter. **Use an
explicit promote gesture with a staging gate.**

**Named precedents.** **Claude Artifacts** — auto-routes "significant, self-contained" content into a
right-side panel with version history + publish/remix; *but note the real gap relevant to us:* there
is **no "pin to Project"** — Projects hold conversations, not promoted artifacts, so the spec's
"pin to the goal canvas" is a genuine differentiator, not a copy. **ChatGPT Canvas** — split chat |
editing workspace, highlight-to-scope-edit, version arrows. **NotebookLM** — three-pane sources →
chat → Studio/notes with citation-preserving promotion. **Cursor vs Windsurf** — accept-diff as the
promote gate (the trust-vs-speed dial). The general framing: Hatchworks' *"Chat-First UX Fails"* names
the **"Infinite Chat Transcript"** anti-pattern — "complex work has structure… users shouldn't have to
reconstruct it from a wall of text" — fix is promoting structure *out* of chat into durable surfaces.

**Anti-patterns.**
- **Lost-in-scrollback** — important state living only in the transcript; the whole reason to promote.
- **Artifact divergence / stale source of truth** — Claude's "edits don't change the model's memory
  of the original" footgun: once promoted, the canvas object is canonical and chat must reference it,
  not a stale copy.
- **Auto-promote clutter** — no staging gate → speculative/bad output pollutes the durable canvas.
- **Destructive promote/unpublish** — promotion and its reversal must be non-destructive and
  reversible (Claude's "unpublishing permanently deletes storage" is the cautionary tale).
- **Provenance loss** — a promoted object with no link back to the turn/agent/decision that made it
  breaks the US10 decision trail.

*Refs:* Claude Artifacts `https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them` ·
ChatGPT Canvas `https://openai.com/index/introducing-canvas/` ·
NotebookLM 2026 `https://www.jeffsu.org/notebooklm-changed-completely-heres-what-matters-in-2026/` ·
Notion AI `https://www.notion.com/help/guides/notion-ai-for-docs` ·
Cursor vs Windsurf `https://www.devtoolsacademy.com/blog/cursor-vs-windsurf` ·
Hatchworks agent UX patterns `https://hatchworks.com/blog/ai-agents/agent-ux-patterns/`.

---

## Mechanic 4 — DRILL-IN (WHAT-primary, HOW behind progressive disclosure)

**Concrete interaction model.** The first screenful of any goal is **WHAT only** — outcome, current
state, evidence, the nudged next step (Mechanic 2). **HOW** — run list → one run's dispatch tree (e.g.
13 sub-agents) → maker-checker iteration with rework budget and named exits (fix/retry/escalate) —
lives behind an **execution tab**, revealed progressively. Crucially, **human-needed moments
(escalations, approvals) are promoted *up* to the WHAT level** — the user never has to poll the
execution tab to discover they are blocked (FR-008, US3 Scenario 3, US10). This is master-detail +
progressive disclosure, not a wall of logs.

**The progressive-disclosure discipline (NN/g).** Show "only a few of the most important options" up
front, "a larger set of specialized options upon request," with a **clear, labeled progression path**.
Two hard rules: (1) the right *feature split* — disclose what's *frequently needed* up front
(escalations are frequently needed → they belong at WHAT level, not buried); (2) **never exceed ~2
levels** — "3 or more levels typically have low usability because users get lost." For interdependent
detail, prefer freeform master-detail over a rigid wizard.

**Named precedents.** NN/g progressive disclosure (the foundational source). **Cursor** file-by-file
diff navigation — the scalable-detail model: "reading diffs in the terminal works for small changes
but not a 40-file migration — you need file-by-file navigation, accept/reject individual changes."
The Claude Code GUI discourse converges on the *legitimate* HOW-surface value-adds a terminal can't
render: **parallel-session management**, **diff review at scale**, **plan-mode step visualization you
can interrupt/redirect** — these are exactly what the execution tab should contain.

**Anti-patterns.**
- **>2 disclosure levels** → users get lost.
- **Burying human-needed escalations inside HOW** → the user is blocked and doesn't know it (the
  worst FR-008 failure).
- **WHAT screen that's actually a HOW screen** — leaking runs/dispatch/logs above the fold defeats
  the entire AI-does-execution posture.
- **Black-box "Done!" with no receipt** (Hatchworks "Black Box Action-Taking") — drill-in must always
  bottom out in *evidence* (US4), never a bare pass/fail badge.

*Refs:* NN/g progressive disclosure `https://www.nngroup.com/articles/progressive-disclosure/` ·
Cursor diff review `https://nimbalyst.com/blog/best-claude-code-gui-tools-2026/` ·
Claude Code GUI value-adds `https://www.mindstudio.ai/blog/claude-desktop-app-vs-terminal-agentic-work`.

---

## The binding substrate — how chat actually drives the canvas

This is the mechanic *underneath* the four above, and the most important architectural takeaway: **the
agent never paints the UI; it emits typed intents against a vocabulary the product owns.** The 2026
field splits into three rendering philosophies, and the safe/opinionated choice is clear:

1. **Developer components keyed by tool name** — CopilotKit `useCopilotAction({name, render})`, Vercel
   `streamUI` (a tool's `generate` async-generator yields `<Spinner/>` then returns `<WeatherCard/>`).
   The tool call is the trigger; a *developer-authored* component is the unit. **← recommended.**
2. **Declarative JSON from a trusted catalog** — Google **A2UI**: the agent emits a JSON component
   tree, the client renders only pre-approved widgets in the host's native styling. **← also safe.**
3. **Agent-generated sandboxed HTML** — MCP-UI/`ui://` iframes, tldraw "Make Real," Thesys C1. Powerful
   but the security/consistency loser; reserve for genuinely open-ended generation.

The **AG-UI protocol** is the emerging wire format (typed `TOOL_CALL_START/ARGS/END/RESULT` +
`STATE_SNAPSHOT`/`STATE_DELTA` events; backed by Google/LangChain/AWS/Microsoft). The principle for
Diecast: a chat turn resolves to **one of a small named set of canvas operations**
(`morph`/`nudge`/`promote`/`drillInto`/`pin`), validated against a schema. Shopify's MCP-UI thesis
states the rule bluntly: *"components don't directly modify state — they bubble up intents the agent
interprets,"* and *"agents shouldn't generate UIs themselves."*

**For the static prototype, this maps perfectly to a cheap, deterministic build:** each canned chat
line carries a `data-op` (e.g. `morph:debug`, `promote:hiring-report`, `nudge:run-exploration`). A
tiny dispatcher reads the op and calls the matching canvas function inside
`document.startViewTransition(...)`. No model, no backend — but the *interaction grammar* is identical
to the real product's tool-call binding, so the prototype is an honest preview, not a Potemkin facade.

**When to render structured UI vs stay in chat text** (cross-precedent consensus): render structured
UI for **constrained input** (forms, pickers, the morph itself), **comparison/scan** (cards, tables,
charts — the hiring report, evidence), and **committed actions** (buttons, promote, escalate-options).
Stay in plain chat text for **explanation, reasoning, open-ended exploration, ambiguous intent.**

*Refs:* CopilotKit AG-UI `https://www.copilotkit.ai/ag-ui` · AG-UI events `https://docs.ag-ui.com/sdk/js/core/events` ·
Vercel streamUI `https://ai-sdk.dev/docs/ai-sdk-rsc/streaming-react-components` (note: RSC track is
*experimental/paused* — Vercel recommends client-rendered `useChat` tool parts for production) ·
A2UI `https://developers.googleblog.com/introducing-a2ui-an-open-project-for-agent-driven-interfaces/` ·
MCP Apps `https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/` ·
Shopify MCP-UI `https://shopify.engineering/mcp-ui-breaking-the-text-wall` ·
InfoWorld "agent is the front end" `https://www.infoworld.com/article/4110010/generative-ui-the-ai-agent-is-the-front-end.html`.

---

## The three access tiers (terminal / chat / canvas over one substrate) — FR-017

**Concrete model.** One core engine; three thin shells. The canvas is a **value-add shell, never a
gate** — it can visualize and navigate things the terminal can't render, but it can never *do*
something the CLI/chat can't, and the substrate state is shared and observable from all three. The
spec's locked side-by-side moment (a terminal pane invoking a skill next to the canvas doing it with
defaults, *same artifact landing either way*) is the literal demonstration of parity.

**Named parity precedents.** **Stripe** — dashboard + CLI + API in parity, CLI auto-generated from the
OpenAPI spec so "the CLI ships a new resource the same day the API does." **GitHub `gh`** —
`<noun> <verb>` over the same REST API the web UI uses, with `gh api` as the raw escape hatch. **AWS**
console + CLI over one API. The *Command Line Interface Guidelines* (clig.dev) codify CLI as a
first-class human surface, not a degraded one.

**What the GUI must add to earn its place** (Claude Code 2025–2026 discourse): power users stay in the
terminal because a GUI that forfeits the environment (aliases, gitignored `.env`, editor integration)
"solves problems I don't have while creating problems I do." So the canvas must add what the terminal
*genuinely can't*: **parallel-session/portfolio overview, diff review at scale, plan/dispatch-tree
visualization you can interrupt and redirect, and evidence rendering** (screenshots, charts, rendered
HTML). Anthropic's own framing — "each surface connects to the same underlying engine, so your
CLAUDE.md, settings, and MCP servers work across all of them" — is the parity contract to echo.

**Anti-pattern.** A GUI with capabilities the CLI lacks (or vice versa) breaks trust and forces tool
abandonment; mode confusion about *which* surface owns authoritative state is the acute three-surface
risk (Norman mode-error) — antidote: the canvas is the always-visible source of truth, and every
chat/CLI action produces a visible canvas change.

*Refs:* Stripe CLI `https://docs.stripe.com/stripe-cli` · gh `https://cli.github.com/manual/` ·
clig.dev `https://clig.dev/` · Claude Code GUI vs terminal `https://vanja.io/claude-code-gui-vs-terminal-a-tale-of-two-workflows/` ·
Claude Code surfaces `https://claude.com/product/claude-code`.

---

## Seven-angle synthesis

**1. Expert Practitioner (product/interaction design).** The settled answer: persistent designed
surface + conversation that mutates it; chat is a *lever*, not the *stage*. One dominant action per
screen (Apple HIG/Material). Progressive disclosure capped at 2 levels (NN/g). This is mature,
low-risk craft — the spec's instincts match the discipline.

**2. Tools & Technologies.** CSS View Transitions API is *Baseline newly-available* (Oct 2025) and is
the exact, free, native primitive for the morph — and trivially fakeable for a static prototype.
FLIP / Framer Motion `layoutId` are the fallbacks. This mechanic is cheaper to build well than it
looks, which de-risks SC-003.

**3. AI/ML Approaches.** Binding = typed agent events (AG-UI `TOOL_CALL_*`), not pixel generation.
The whole industry is retreating from free-form generative UI toward *constrained vocabularies*
(Vercel paused RSC; A2UI's trusted catalog; Shopify's "agents shouldn't generate UIs"). Diecast
should bind chat to a small named canvas-operation set — which also happens to be the cheapest honest
way to script the prototype.

**4. Community & Open Source.** AG-UI (CopilotKit), MCP Apps/MCP-UI, A2UI are the open standards to
watch; CopilotKit and Vercel AI SDK are the reference OSS implementations. tldraw is the open spatial-
canvas + AI exemplar. None are needed to *build the prototype*, but they validate the architecture.

**5. Frameworks & Patterns.** Material **Container Transform** (morph), **progressive disclosure /
master-detail** (drill-in), **promote-ephemeral→persistent** with an explicit staging gate (promote),
**choice architecture / golden paths** (nudge). Each mechanic has a named, battle-tested pattern — the
prototype is assembling known patterns, not inventing UX.

**6. Contrarian View.** The loudest skeptics are worth heeding precisely because the spec already
agrees with them: Wattenberger ("chatbots have no affordances"), Litt ("chat is slow, imprecise" →
direct-manipulation-primary), NN/g ("a chatbot that re-skins browsing adds friction"), the Keyhole
Effect ("chat fails at data analysis — ephemeral, no spatial memory"). **Their collective verdict
endorses canvas-primary and warns against the rejected chat-first path.** The remaining contrarian risk
is *gimmick morph* — animation for its own sake; mitigated by "speed > spectacle" (Linear) and the
undo/receipt requirements.

**7. First Principles.** Why a canvas at all, in an AI-does-execution world? Because *attention is the
scarce resource* and structure must be perceivable, not reconstructed from scrollback. The canvas
holds the WHAT in stable space (spatial memory); chat changes direction; the agent does the HOW behind
a drill-in; humans are pulled in only when a decision exceeds expected autonomy. Each mechanic exists
to keep one thing true: **the user always knows where they are, what's recommended, what changed, and
why — without reading a log.**

---

## Consolidated anti-pattern catalogue (the "don't" list for the prototype)

1. **Don't hard-swap canvases** — morph with shared-element identity, <500ms, undoable, reduced-motion
   safe. *(Material/Dynamic Island/Keyhole/WCAG 2.3.3)*
2. **Don't morph unprompted** — a morph is always the visible result of an explicit steer. *(Nielsen
   consistency)*
3. **Don't show two equal primaries** — exactly one recommended next step per screen. *(Apple HIG)*
4. **Don't gate** — opinionated default + always-open, cheap override (chat/terminal/manual nav).
   *(Rails sharp knives, golden paths)*
5. **Don't over-nudge** — alert fatigue and automation-bias rubber-stamping. *(arXiv 2509.08514)*
6. **Don't leave value in scrollback** — explicit, named promote gesture with provenance + version.
   *(Hatchworks "Infinite Chat Transcript", NotebookLM)*
7. **Don't auto-promote** — staging gate prevents canvas clutter. *(Cursor accept-diff)*
8. **Don't exceed 2 disclosure levels** — and never bury human-needed escalations inside HOW.
   *(NN/g)*
9. **Don't free-generate UI** — bind chat to a small named canvas-operation vocabulary. *(Vercel
   paused RSC, A2UI, Shopify)*
10. **Don't let a surface out-power its peers** — terminal/chat/canvas parity over one substrate; the
    canvas is the always-visible source of truth. *(Stripe/gh, Norman mode-error)*
11. **Don't end a drill-in at a bare badge** — bottom out in evidence. *(Hatchworks "Black Box")*

---

## Build recipe for the prototype (per mechanic, no backend)

- **Morph:** both canvas layouts in the DOM; `data-op="morph:<family>"` on canned chat lines; a 20-line
  dispatcher calls `startViewTransition` with `view-transition-name` on ~4 persistent anchors; crossfade
  fallback under `prefers-reduced-motion`/no-support. **This is the single highest-ROI build item — it
  *is* SC-003.**
- **Nudge:** a reusable "next-step card" component — one filled primary button + receding secondaries —
  rendered per canvas state; chat and a manual nav menu are the visible overrides.
- **Promote:** chat artifact cards with an explicit "Pin to canvas" button that clones the card into a
  canvas slot with a version label + "from chat · <agent> · <time>" provenance stub.
- **Drill-in:** WHAT panel above the fold + an "Execution" tab that expands run list → dispatch tree →
  maker-checker (≤2 levels); a persistent "⚠ needs you" chip at WHAT level when a scripted escalation
  fires.
- **Three tiers:** the FR-017 side-by-side is a static two-pane mock — a faux terminal running
  `cast crud-orchestrator …` next to the canvas doing the same with defaults, same artifact card
  appearing in both. No logic needed; it's a parity *illustration*.

---

## What this resolves / hands off

- **Resolves for Step 2:** a concrete interaction model + native primitive + named precedent +
  anti-pattern set for each of morph / nudge / promote / drill-in, plus the binding substrate and the
  three-tier parity story. Sufficient to mock US1's morph moment and FR-017's side-by-side.
- **Feeds Step 1 (design language):** motion register (speed>spectacle, ~350ms, reduced-motion) and the
  "stable canvas, ephemeral chat" hierarchy are design-language constraints.
- **Feeds Step 3 (per-family canvases):** the morph mechanic is the connective tissue between the four
  family shapes; the drill-in + evidence rules feed the [USER-DEFERRED: evidence patterns] question.
- **Feeds Step 5 (decisions/autonomy):** the morph receipt and the WHAT-level "needs you" escalation
  chip are the same surface as the US10 decision/escalation rail.
- **Open for the owner:** none blocking. One judgment call to flag at plan review — whether the
  prototype fakes *one* hero morph (feature→debug, cheap, high-impact) or morphs across all four
  families (more build, diminishing demo return). Recommendation: **one hero morph done flawlessly.**
