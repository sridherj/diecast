> **OWNER DECISION (2026-06-11, Q#15) — supersedes this playbook's register recommendation.**
> The prototype uses the **existing Diecast identity, one light world** (cream `#F5F4F0` /
> raspberry `#D6235C` / IBM Plex Mono + DM Sans — `design-samples/option-e-diecast-light.html`).
> No dark Workbench register: it was an aesthetic hypothesis, not a spec requirement; it cut
> against brand continuity (FR-018) and flow continuity for the morph demo. Refinements to the
> identity are welcome during build. **What survives from this playbook:** the agent-colleague
> grammar (actor chips, binary confidence, L1/L2/L3 pills, single status accent = raspberry),
> the fixed GenUI block library, the one-signature-morph motion register, the slop gate, and
> WHAT/HOW separation via surface tone instead of a theme flip.

# Design Language — Playbook

> **Step 1 of `exploration/steps.ai.md`** — resolves the `[USER-DEFERRED: design language]` open
> question (Q#11). Synthesized from `research/01-design-language.ai.md` (web, 7 angles) against the
> locked spec `refined_requirements.collab.md` v0.3.0 (FR-018/019/020, SC-002/004).
> **Author:** cast-playbook-synthesizer | **Date:** 2026-06-11 | **Audience:** owner pick + build-phase reference.

## TL;DR

**Commit to one token system rendered in three registers: ship `Engineering Workbench` (Linear-class
dark command deck) as the spine for every machine surface, render the document/board surfaces in
`Studio Clarity` (light, editorial) for the WHAT and the PM, and spend `Living Canvas` on exactly the
one FR-004 chat-morphs-canvas moment — nowhere else.** The research's central, non-obvious finding is
that "dark vs light" is the *most* negotiable layer (a re-theme of the same six tokens), while the real
net-new design work — the one thing no existing tool solves and the one thing that makes Diecast not a
Linear clone — is the **agent-colleague grammar**: a paired maker/checker hue, a *binary* high/low
confidence mark, an L1/L2/L3 autonomy chip, and a single status-light accent that means "needs you."
Budget your design time there, not on theme-picking. The single biggest failure mode is the 2026 AI-slop
default (dark glass + gradient borders + purple/teal glow + an assistant orb); if a screen looks like
every other AI landing page it has already failed SC-004, regardless of how polished it is.

## Recommended Stack

| Component | Choice | Why (and why not the alternative) |
|-----------|--------|-----------------------------------|
| Direction | **Hybrid: Workbench spine + Studio docs + one Living-Canvas morph** | A single dark world alienates the PM/requirements surfaces (SC-002 comprehension); a single light world forfeits eng-deck credibility; full-time spatial canvas is slop-prone and tiring. The hybrid takes each register where it's safe. |
| Token base | **Extend the in-repo `cast-preso-visual-toolkit`** (`templates/css/{theme,typography,components}.css`) | Craft already paid for and brand-continuous (FR-018). Six CSS custom properties re-skinned per register — not a new system. Building fresh tokens is net-new work for zero gain. |
| Accent model | **One acid accent reserved for *state*, never decoration** (`--accent: #C8FF3D` lime) | Linear's 2025 "status-light" model: monochrome canvas + a single accent that means needs-you / live / changed. Multi-color palettes read as AI-slop and destroy the scan. |
| Agent-colleague hue | **One paired maker/checker hue, used *only* on agent chrome** (`--maker: #7AA2F7` blue / `--checker: #BB9AF7` violet) | This pairing is the product's real identity (the quality unit, FR-018). Restricting it to agent chrome makes "who is acting" legible without reading. Two unrelated hues would just look decorative. |
| Confidence mark | **Binary high/low glyph, never a percentage** | Research-backed: "binary high-low indicators outperformed numeric percentages — users decide faster" (fuselab). "73%" implies false precision and slows the read. |
| Type — system/agent voice | **`JetBrains Mono`** (or the toolkit's existing mono) for run logs, IDs (`CAST-412`, `M04/S03/R02`), terminal pane | Continues the cast-preso mono identity; monospace *is* the visual signature of machine voice. |
| Type — human/WHAT voice | **`Inter`** (variable) for the canvas WHAT, board, requirements doc | A crisp grotesque sans is the Linear/Vercel canon; variable weight covers both deck density and editorial reading. Not a serif pairing — adds warmth the eng audience reads as "marketing site." |
| Chrome material | **One translucent-on-dark "UI surface" token** (`--surface`) for every panel, popover, chat rail | Warp's one-material trick: all overlay chrome reads as a single material. Per-panel backgrounds fragment the shell and invite glass-slop. |
| Spacing | **8px scale verbatim (8/16/32/64)** | Linear's rhythm; the cast-preso grid already aligns. Don't invent a scale. |
| Motion | **One signature motion (the canvas-morph); everything else ≤150ms ease-out** | Kowalski/Freiberg restraint canon. Over-animation is the cheapest way to look like a toy, not a tool. |
| Morph mechanism | **CSS View Transitions API** keyed to scripted chat steps, swapping pre-built block recipes | The spec's own "CSS-transitioned panel swaps" idea; native, cheap, no runtime LLM. Real generative-UI is out of scope (static prototype). |
| Block grammar | **Fixed GenUI set: card / table / chart / form / timeline / plan-step** | The unit the morph swaps between. Variation lives in *which blocks appear* per family; consistency lives in *how each block looks*. Free-form generation erodes learnability. |
| Slop gate | **Wire `not-generic` / `not-ai-aesthetic` cast-preso checkers as the screen gate** | The exact tools that exist to catch the AI-slop default. Make them a non-negotiable pass/fail on every prototype screen. |

## Implementation Steps

### Step 1: Lock the six-token core + the three register re-skins
**Impact: High** | **Effort: 0.5 day**

Everything downstream inherits this. Define six custom properties once, then provide three `data-register`
re-skins. A register is a re-theme, not a new file.

```css
/* base tokens — register-neutral structure */
:root {
  --space-1: 8px;  --space-2: 16px;  --space-3: 32px;  --space-4: 64px;
  --radius: 8px;
  --motion-fast: 120ms;  --motion-ease: cubic-bezier(0.2, 0.8, 0.2, 1);
  --accent:  #C8FF3D;          /* the single status light: needs-you / live / changed */
  --maker:   #7AA2F7;          /* agent chrome only */
  --checker: #BB9AF7;          /* agent chrome only */
  --font-mono: "JetBrains Mono", ui-monospace, monospace;  /* machine voice */
  --font-sans: "Inter", system-ui, sans-serif;             /* human / WHAT voice */
}

/* WORKBENCH — machine surfaces (canvas, execution, board, marketplace, agent-ops) */
[data-register="workbench"] {
  --bg:      #0B0C0E;          /* near-black canvas */
  --surface: rgba(255,255,255,0.06);   /* the ONE overlay material — Warp trick */
  --text:    #E6E8EB;
  --muted:   #8A8F98;
  --hairline: rgba(255,255,255,0.08);
}

/* STUDIO — document surfaces (requirements doc, WHAT goal card, PM board, evidence reports) */
[data-register="studio"] {
  --bg:      #FBFAF7;          /* warm-neutral paper */
  --surface: #FFFFFF;
  --text:    #1A1A18;          /* ink */
  --muted:   #6B6B66;
  --hairline: rgba(0,0,0,0.08);
}
```

The `--accent`, `--maker`, `--checker`, and both fonts are **identical across registers** — that
constancy is what makes the dark execution tab and the light requirements doc read as one product
(the fake-data-spine principle, FR-019). Only `--bg`/`--surface`/`--text`/`--muted`/`--hairline` flip.

### Step 2: Design the agent-colleague grammar (the real net-new work)
**Impact: High** | **Effort: 1.5 days**

This is the part no existing tool solves and the part that earns the "agents as colleagues" thesis.
Four primitives, each a small reusable component, used *everywhere* an agent appears (board assignee,
dispatch tree node, ticket activity line, marketplace card):

1. **Actor chip** — who is acting. Human = avatar; maker-agent = squared `--maker` chip; checker-agent
   = squared `--checker` chip. Shape + hue, so it reads pre-attentively without a label.
2. **Confidence mark** — a filled vs hollow glyph (●/○), `high`/`low` only. Never a percentage. Tooltip
   may carry the rationale, but the glance is binary (fuselab).
3. **Autonomy chip** — `L1 / L2 / L3` as a tiny monospace pill. L1 = quiet (decide-and-record),
   L2 = `--muted` ring (decide-record-notify), L3 = `--accent` ring (ask-first → escalation rail).
4. **Needs-you light** — the `--accent` status dot, the *only* place global accent appears at WHAT
   level, so "the system needs me" is one unmistakable signal the user never has to poll for (FR-008,
   US3 Scenario 3).

```html
<!-- maker-checker pairing rendered IN one card — never two separate cards (US6 S5) -->
<article class="agent-card" data-register="workbench">
  <span class="actor-chip actor-chip--maker">crud-orchestrator</span>
  <span class="confidence" data-level="high" aria-label="high confidence">●</span>
  <span class="autonomy-pill" data-level="L2">L2</span>
  <footer class="checker-row">
    <span class="actor-chip actor-chip--checker">mvcs-compliance-checker</span>
    <span class="stat">99.9% compliant · 2 loops · 505 runs</span>
  </footer>
</article>
```

Mock the *same* canonical agents the spec names (`crud-orchestrator`, `M04/S03/R02`, rework `1/3`) so
the grammar is consistent across screens.

### Step 3: Build the fixed GenUI block library
**Impact: High** | **Effort: 1 day**

Pre-build six block components as the vocabulary the canvas composes and the morph swaps between:
**card** (WHAT summary), **table** (run list, contract catalogue), **chart** (data-analysis output,
usage metrics — use a tiny lib like uPlot or hand-rolled SVG, no heavyweight charting), **form**
(assessment definition, skill creation), **timeline** (iteration history, decision trail), **plan-step**
(execution dispatch, visible editable step list). Each block is identical in *look* across families;
families differ only in *which blocks appear and in what order*. This is the "shape-follows-purpose"
discipline that lets four canvases feel distinct (SC-005) without four bespoke layouts.

### Step 4: Implement the one signature morph (FR-004 / SC-003)
**Impact: High** | **Effort: 1 day**

The feature-backbone canvas physically reshapes into the debug-loop canvas when the scripted chat says
"this is actually a bug, not a feature." Use the native View Transitions API — assign stable
`view-transition-name`s to blocks that persist (goal header, WHAT card) so they glide rather than
cross-fade, and let the family-specific blocks (feature stages out, hypothesis→experiment→observation in)
animate in with mass and follow-through (the Rauno motion bible — overlapping action, ease-out, ~400ms;
this is the *one* place you spend longer than 150ms).

```js
function morphCanvas(toFamily) {
  document.startViewTransition(() => renderCanvas(toFamily));  // persistent blocks glide; family blocks swap
}
```

Keep goal context visible throughout (the goal title/outcome never leaves) so the morph reads as
"same goal, new shape," not "new page" (US1 Scenario 2).

### Step 5: Apply the register split per surface
**Impact: Medium** | **Effort: 1 day**

Set `data-register` per surface, not per component, so the choice is one attribute:
- **Workbench (dark):** canvas, execution tab, dispatch trees, board, marketplace, agent-ops, Layer-2.
- **Studio (light):** requirements doc (US7), WHAT-first goal card when shown standalone, evidence
  reports, the PM-facing board view. The PM-commenter moment (Q#10) lands here.
- **Living Canvas (dark + the morph):** only the FR-004 demo and any "wow" opening screen. At most one
  bounded dark-glass panel (the AI-output surface) — never global glass chrome.

### Step 6: Stand up the command palette as the third access tier
**Impact: Medium** | **Effort: 0.5 day**

A `Cmd-K` palette is the cheapest, most credible "serious tool" signal and it embodies the
terminal/chat/canvas story (FR-017): canvas is the guided default, palette/chat is the power lever.
For the static prototype it only needs to *look* and *feel* real — a fuzzy-filter list over scripted
commands, keyboard-navigable, opening the same surfaces the canvas nudges toward.

### Step 7: Wire the slop gate
**Impact: Medium** | **Effort: 0.5 day**

Run every prototype screen through the cast-preso `not-generic` and `not-ai-aesthetic` checkers as a
pass/fail before it's considered done (FR-019, SC-004). Treat any gradient-border glass, AI-glow, or
anthropomorphic orb as a hard fail. This is the mechanism that keeps "showable without apology" honest
rather than aspirational.

## Architecture / Token Flow

```
                       ┌─────────────────────────────────────────────┐
                       │  cast-preso-visual-toolkit (extend, FR-018)  │
                       │  6 tokens · 8px scale · mono+sans · checkers │
                       └───────────────────────┬─────────────────────┘
                                                │ re-skin via [data-register]
            ┌───────────────────────────────────┼───────────────────────────────────┐
            ▼                                   ▼                                   ▼
   ┌──────────────────┐              ┌──────────────────┐              ┌──────────────────┐
   │  WORKBENCH (dark)│              │  STUDIO (light)  │              │  LIVING CANVAS   │
   │  machine surfaces│              │  document/PM     │              │  one morph moment│
   │  canvas·exec·board│             │  reqs·evidence   │              │  FR-004 / SC-003 │
   │  marketplace·ops  │             │  WHAT card·PMboard│             │  View Transitions│
   └────────┬─────────┘              └────────┬─────────┘              └────────┬─────────┘
            │  all three share, UNCHANGED:                                      │
            └──────────────►  --accent (status light) · --maker/--checker  ◄────┘
                              (agent chrome only) · Inter + JetBrains Mono
                                            │
                              ┌─────────────┴──────────────┐
                              │  AGENT-COLLEAGUE GRAMMAR    │  ← the net-new design work
                              │  actor chip · binary conf.  │
                              │  L1/L2/L3 chip · needs-you  │
                              └─────────────────────────────┘
                                            │ composes
                       ┌────────────────────┴─────────────────────┐
                       │  FIXED GENUI BLOCKS                       │
                       │  card·table·chart·form·timeline·plan-step │
                       │  (same look everywhere; per-family order) │
                       └───────────────────────────────────────────┘
```

## Key Decisions

| Decision | Recommendation | Rationale (trade-off) |
|----------|---------------|-----------------------|
| One world vs hybrid | **Hybrid (3 registers, 1 token system)** | Single dark forfeits PM comprehension (SC-002); single light forfeits eng credibility. Cost: two themes to maintain — cheap, since it's six flipped vars. |
| Dark-primary or light-primary | **Dark spine (Workbench), light for docs** | Eng is the primary persona; the deck is the home surface. Docs/board flip to light where reading dominates. |
| Accent count | **Exactly one, reserved for state** | Multi-color = AI-slop and kills the scan. The accent earning "needs-you" is worth more than any palette. |
| Maker/checker color | **One paired hue, agent chrome only** | Makes agency legible pre-attentively and *is* the brand (the quality unit). Spending it on non-agent chrome would dilute the signal. |
| Confidence display | **Binary high/low glyph** | Percentages imply false precision and slow decisions (fuselab). The rationale lives in the drill-in, not the glance. |
| Type pairing | **Inter (human) + JetBrains Mono (machine)** | Mono *is* the machine-voice signal; a sans/serif pairing would read as a marketing site to the eng audience. |
| Chrome material | **One translucent `--surface` for all overlays** | Warp's one-material shell; per-panel backgrounds fragment the UI and invite glass-slop. |
| Morph scope | **Exactly one signature morph; ≤150ms elsewhere** | The morph *earns* spectacle (SC-003); ambient animation reads as toy. Spending motion everywhere is the cheapest way to look amateur. |
| Morph tech | **Native CSS View Transitions, scripted** | Static prototype has no backend; real GenUI runtime is out of scope. View Transitions give the GenUI *look* for free. |
| Glass usage | **At most one bounded panel, never global** | Dark glass + gradient border + glow is the literal 2026 AI-slop signature; bounding it to one AI-output surface keeps the wow without the cliché. |
| Where to spend design hours | **Agent-colleague grammar, not theme-picking** | Theme is a re-skin; the colleague grammar is unsolved by every existing tool and is the actual differentiator. |

## Pitfalls to Avoid

1. **Shipping the 2026 AI-slop default.** Dark glassmorphism (#0A0A0A base) + frosted translucent panels
   + gradient borders + a purple/teal "AI" glow + an anthropomorphic assistant orb is now a recognizable
   cliché. It is the *opposite* of Diecast's craft signal. If a screen looks like an AI startup's landing
   page, it has failed SC-004 — gate it out with the cast-preso checkers.
2. **Letting the canvas morph too freely.** If the layout reshapes on every interaction, users re-learn
   the page each time and the WHAT-first scannability collapses. Morph *between a small fixed set of
   family shapes* with consistent block grammar inside each — variation in *which* blocks, consistency in
   *how* each block looks.
3. **Going dark-only.** A near-black command deck is perfect for execution and alienating for the
   requirements doc a PM reads. Dark-only quietly fails SC-002. This is the entire reason the
   recommendation is a hybrid, not one world.
4. **Over-animating.** Kowalski's whole thesis is restraint; spinners-as-personality, parallax, and
   decorative loops read as a toy. Exactly one signature motion (the morph); everything else
   near-invisible, ≤150ms, ease-out.
5. **"Beautiful" that's slower to read than plain text.** SC-002 is a *comprehension* test. Polish that
   fights the scan is negative value. If a treatment makes the WHAT harder to grasp in one glance, cut it.
6. **Reskinning Linear's issue tracker and calling it done.** Linear-clone is now a tired SaaS trope. The
   differentiator is the agent-colleague grammar (maker/checker pairing, autonomy dial, hiring report) —
   give *that* its own identity rather than inheriting Linear's.
7. **Numeric confidence and combined chat/activity panels.** Both are documented agent-UX failure modes:
   percentages slow decisions, and a panel that's both conversation and activity tracker fails as both.
   Keep confidence binary and keep agent *work* on the canvas/execution tab, chat for conversation only.
8. **Spreading the maker/checker hue onto non-agent chrome.** The moment those colors appear on buttons or
   nav, they stop meaning "an agent is here" and become decoration — destroying the one legibility win
   that's genuinely net-new.

## Success Metrics

- **Slop-gate pass rate:** 100% of prototype screens pass the cast-preso `not-generic` and
  `not-ai-aesthetic` checkers before sign-off. Any gradient-glass/glow/orb = hard fail.
- **Agency-legibility test:** a viewer can correctly identify, *without reading labels*, who is acting
  (human/maker/checker), the confidence (high/low), and the autonomy level (L1/L2/L3) on ≥4 of 5 sampled
  agent surfaces. Verified by a 30-second flash test on 1-2 peers.
- **Comprehension (SC-002):** an unfamiliar viewer states what the product does and how it differs from
  raw Claude Code within ~3 minutes of guided clickthrough.
- **Family-distinctness (SC-005):** in a side-by-side screenshot, the feature vs debug canvas shapes are
  obviously different to a viewer with no explanation.
- **Morph "felt" (SC-003):** at least one viewer describes the chat-driven canvas reshape as the canvas
  "changing" rather than "a new screen loading" — the morph reads as continuous.
- **Token discipline:** the entire prototype uses ≤1 accent color and exactly one maker + one checker
  hue; grep the CSS for stray hex values as the check.
- **Showable-without-apology (SC-004):** SJ self-reports the prototype is presentable to a company/peer
  after the first external showing.

## Impact Rating: 9/10

**Justification:** Design language is the through-line that makes every other surface in this goal cohere
— the same six tokens, the same agent-colleague grammar, and the same slop floor are inherited by the
canvas (Step 2 research), the family flows (Step 3), the agent-colleague screens (Step 4), and the
decision/autonomy UX (Step 5). It directly determines SC-002, SC-004, and SC-005, which are three of the
seven success criteria. It is a 9 rather than 10 only because the visual identity, while load-bearing, is
downstream of the interaction mechanics (Step 2) for the prototype's core fluidity thesis — but it is the
prerequisite that keeps that thesis from looking like every other AI app while it's demonstrated.
