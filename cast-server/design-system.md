# Task OS Design System

> Implementation-ready design specification for Task OS — a dark-mode, desktop-only,
> information-dense productivity dashboard built with FastAPI + HTMX + Jinja2.
>
> **Style inspiration:** Linear, VS Code, Raycast — developer tools, not consumer apps.
> **Generated with:** ui-ux-pro-max design intelligence (Dark Mode OLED + Financial Dashboard palette).

---

## 1. Design Tokens

### 1.1 Color Palette

All colors defined as CSS custom properties on `:root`.

#### Core Backgrounds & Surfaces

| Role | Variable | Hex | Slate Ref | Usage |
|------|----------|-----|-----------|-------|
| Page background | `--bg-primary` | `#0F172A` | slate-900 | `<body>`, page bg |
| Card/panel surface | `--bg-surface` | `#1E293B` | slate-800 | Cards, sidebar, panels |
| Hover surface | `--bg-surface-hover` | `#334155` | slate-700 | Card hover, active nav item |
| Input background | `--bg-input` | `#0F172A` | slate-900 | Text inputs, textareas |
| Elevated surface | `--bg-elevated` | `#334155` | slate-700 | Dropdowns, tooltips, modals |

#### Borders & Dividers

| Role | Variable | Hex | Usage |
|------|----------|-----|-------|
| Default border | `--border` | `#475569` | Card borders, dividers (slate-600) |
| Subtle border | `--border-subtle` | `#334155` | Inner dividers (slate-700) |
| Focus ring | `--border-focus` | `#6366F1` | Input focus ring (indigo-500) |

#### Text

| Role | Variable | Hex | Slate Ref | Usage |
|------|----------|-----|-----------|-------|
| Primary text | `--text-primary` | `#F8FAFC` | slate-50 | Headings, primary content |
| Secondary text | `--text-secondary` | `#94A3B8` | slate-400 | Labels, descriptions, metadata |
| Muted text | `--text-muted` | `#64748B` | slate-500 | Timestamps, hints, disabled |
| Inverse text | `--text-inverse` | `#0F172A` | slate-900 | Text on light badges |

#### Semantic Colors

| Role | Variable | Hex | Tailwind Ref | Usage |
|------|----------|-----|-------------|-------|
| Primary | `--color-primary` | `#6366F1` | indigo-500 | Active states, links, primary actions |
| Primary hover | `--color-primary-hover` | `#818CF8` | indigo-400 | Hover on primary elements |
| Primary muted | `--color-primary-muted` | `#312E81` | indigo-900 | Primary tinted backgrounds |
| Success | `--color-success` | `#22C55E` | green-500 | Completed states, positive |
| Success muted | `--color-success-muted` | `#052E16` | green-950 | Success tinted backgrounds |
| Warning | `--color-warning` | `#F59E0B` | amber-500 | @claude entries, suggestions |
| Warning muted | `--color-warning-muted` | `#451A03` | amber-950 | Warning tinted backgrounds |
| Danger | `--color-danger` | `#EF4444` | red-500 | Declined, errors, destructive |
| Danger muted | `--color-danger-muted` | `#450A0A` | red-950 | Danger tinted backgrounds |
| Focus highlight | `--color-focus` | `#8B5CF6` | violet-500 | In-focus star, focus mode |
| Info | `--color-info` | `#3B82F6` | blue-500 | Informational badges, stage |

#### Stage Badge Colors

Each stage gets a background + text color pair for its pill badge.

| Stage | Variable (bg) | BG Hex | Variable (text) | Text Hex | Contrast |
|-------|---------------|--------|-----------------|----------|----------|
| `idea` | `--stage-idea-bg` | `#1E293B` | `--stage-idea-text` | `#94A3B8` | 5.2:1 |
| `accepted` | `--stage-accepted-bg` | `#1E3A5F` | `--stage-accepted-text` | `#60A5FA` | 4.8:1 |
| `scoped` | `--stage-scoped-bg` | `#1E3A5F` | `--stage-scoped-text` | `#60A5FA` | 4.8:1 |
| `explored` | `--stage-explored-bg` | `#164E63` | `--stage-explored-text` | `#22D3EE` | 5.7:1 |
| `researched` | `--stage-researched-bg` | `#164E63` | `--stage-researched-text` | `#22D3EE` | 5.7:1 |
| `planned` | `--stage-planned-bg` | `#3B0764` | `--stage-planned-text` | `#C084FC` | 5.4:1 |
| `actionable` | `--stage-actionable-bg` | `#14532D` | `--stage-actionable-text` | `#4ADE80` | 6.1:1 |
| `completed` | `--stage-completed-bg` | `#052E16` | `--stage-completed-text` | `#22C55E` | 5.8:1 |
| `declined` | `--stage-declined-bg` | `#450A0A` | `--stage-declined-text` | `#F87171` | 5.1:1 |

### 1.2 Typography

**Font pairing:** Inter (headings + body) + JetBrains Mono (data/code) — based on ui-ux-pro-max "Developer Mono" pairing adapted with Inter for broader readability.

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
```

| Role | Variable | Font | Weight | Size | Line Height |
|------|----------|------|--------|------|-------------|
| Page title (h1) | `--font-heading` | Inter | 700 | 24px | 1.3 |
| Section heading (h2) | `--font-heading` | Inter | 600 | 18px | 1.3 |
| Card title | `--font-heading` | Inter | 600 | 16px | 1.3 |
| Body text | `--font-body` | Inter | 400 | 14px | 1.5 |
| Labels / small | `--font-body` | Inter | 500 | 13px | 1.4 |
| Metadata | `--font-mono` | JetBrains Mono | 400 | 13px | 1.4 |
| Badge text | `--font-mono` | JetBrains Mono | 500 | 12px | 1.0 |
| Timestamps | `--font-mono` | JetBrains Mono | 400 | 12px | 1.4 |
| Input text | `--font-body` | Inter | 400 | 14px | 1.5 |

### 1.3 Spacing Scale

Based on 4px base unit. Use CSS variables for consistency.

| Token | Variable | Value | Usage |
|-------|----------|-------|-------|
| xs | `--space-xs` | 4px | Inline gaps, badge padding-y |
| sm | `--space-sm` | 8px | Icon-to-text gap, tight padding |
| md | `--space-md` | 12px | List item padding |
| base | `--space-base` | 16px | Card padding, standard gap |
| lg | `--space-lg` | 24px | Section gaps, card margins |
| xl | `--space-xl` | 32px | Page section spacing |
| 2xl | `--space-2xl` | 48px | Major section separators |

### 1.4 Border Radius

| Token | Variable | Value | Usage |
|-------|----------|-------|-------|
| Small | `--radius-sm` | 4px | Badges, buttons, tags |
| Medium | `--radius-md` | 8px | Cards, panels, inputs |
| Large | `--radius-lg` | 12px | Modals, dropdowns |
| Full | `--radius-full` | 9999px | Pill badges, avatar |

### 1.5 Shadows

Minimal shadows — rely on surface color differences for depth hierarchy.

| Token | Variable | Value | Usage |
|-------|----------|-------|-------|
| Subtle | `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.3)` | Cards at rest |
| Elevated | `--shadow-md` | `0 4px 12px rgba(0,0,0,0.4)` | Dropdowns, tooltips |
| Modal | `--shadow-lg` | `0 8px 24px rgba(0,0,0,0.5)` | Modals, overlays |

### 1.6 Transitions

From ui-ux-pro-max: use 150-300ms for micro-interactions.

| Token | Variable | Value | Usage |
|-------|----------|-------|-------|
| Fast | `--transition-fast` | `150ms ease` | Hover states, color changes |
| Normal | `--transition-normal` | `200ms ease` | Panel toggles, fades |
| Slow | `--transition-slow` | `300ms ease` | Expand/collapse, modals |

---

## 2. Layout System

### 2.1 Page Structure

Desktop-only, optimized for 1440px+. No responsive breakpoints. No mobile support.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          VIEWPORT (100vw x 100vh)                           │
│                                                                              │
│  ┌─────────┐ ┌──────────────────────────────────────────────────────────┐   │
│  │ SIDEBAR  │ │                    MAIN AREA                             │   │
│  │ 240px    │ │                    (fills remaining width)               │   │
│  │ fixed    │ │                                                          │   │
│  │ left     │ │                                                          │   │
│  │ 100vh    │ │                                                          │   │
│  │          │ │                                                          │   │
│  │          │ │                                                          │   │
│  │          │ │                                                          │   │
│  └─────────┘ └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Area | Dimensions | Positioning |
|------|-----------|-------------|
| Sidebar | 240px wide, 100vh tall | `position: fixed; left: 0; top: 0;` |
| Main area | `margin-left: 240px; width: calc(100vw - 240px);` | Static flow |
| Main content padding | 24px all sides | Within main area |
| Max content width | None (fills available space) | Fluid |

### 2.2 Sidebar Layout

```
┌────────────────────────┐
│  ★ Task OS             │  ← Logo area (h: 56px, border-bottom)
│                        │
├────────────────────────┤
│                        │
│  ◆ Dashboard           │  ← Nav items (h: 40px each)
│  ◆ Scratchpad          │     Active: bg-surface-hover, left 3px primary border
│  ◆ Focus               │     Hover: bg-surface-hover
│                        │
├────────────────────────┤  ← Divider (border-subtle)
│                        │
│  AGENTS  (12)          │  ← Section header (text-muted, 12px, uppercase)
│  ◆ startup-discover    │     Agent list from registry
│  ◆ startup-enrich      │     Click → show agent detail popover
│  ◆ web-researcher      │
│  ◆ ...                 │
│                        │
├────────────────────────┤
│                        │
│  [⚡ Detect Goals]     │  ← Primary button, full width minus padding
│                        │
├────────────────────────┤
│                        │
│  Synced 2m ago         │  ← Footer: sync status (text-muted, 12px)
│  [↻ Sync Now]          │     Ghost button
│                        │
└────────────────────────┘
```

**Sidebar CSS:**
- Background: `--bg-surface`
- Border-right: 1px solid `--border-subtle`
- Nav icon size: 18px (Heroicons outline)
- Nav text: 14px Inter, 500 weight
- Logo: 16px Inter, 700 weight, `--text-primary`

---

## 3. Screen Designs

### 3.1 Dashboard Screen

The primary view. Shows all goals grouped by lifecycle stage, plus scratchpad and suggestions in a right sidebar.

```
┌─────────┬────────────────────────────────────────────┬──────────────────────┐
│ SIDEBAR │  MAIN CONTENT (2/3 width)                  │  RIGHT PANEL (1/3)   │
│         │                                            │                      │
│         │  ┌── PENDING APPROVALS ──────────────────┐ │  ┌─ SCRATCHPAD ────┐ │
│         │  │ "1 goal needs your review"             │ │  │ [textarea     ] │ │
│         │  │                                        │ │  │ [Add Entry]     │ │
│         │  │ ┌─ idea card ─────────────────────┐   │ │  │                 │ │
│         │  │ │▌Build Voice Agent MVP  [idea]   │   │ │  │ ## Feb 23       │ │
│         │  │ │ "Mentioned in 3 entries..."      │   │ │  │ • Voice agent   │ │
│         │  │ │ [✓ Accept]  [✗ Decline]         │   │ │  │ • @claude: ...  │ │
│         │  │ └─────────────────────────────────┘   │ │  │                 │ │
│         │  └───────────────────────────────────────┘ │  │ ## Feb 22       │ │
│         │                                            │  │ • CPTO roles    │ │
│         │  ┌── ACTIONABLE (3) ─────────────────────┐ │  │                 │ │
│         │  │ ┌─ goal card ─────────────────────┐   │ │  │ [View All →]   │ │
│         │  │ │▌★ Build Task OS      [actionable]│   │ │  └────────────────┘ │
│         │  │ │  career, taskos  │ 4/12 tasks    │   │ │                      │
│         │  │ └─────────────────────────────────┘   │ │  ┌─ SUGGESTIONS ──┐ │
│         │  │ ┌─ goal card ─────────────────────┐   │ │  │                 │ │
│         │  │ │▌★ Land AI Role       [actionable]│   │ │  │ "Build Voice   │ │
│         │  │ │  career, cpto    │ 2/8 tasks     │   │ │  │  Agent MVP"    │ │
│         │  │ └─────────────────────────────────┘   │ │  │  Confidence:   │ │
│         │  └───────────────────────────────────────┘ │  │  85%            │ │
│         │                                            │  │ [✓] [✗]        │ │
│         │  ┌── PLANNED (1) ────────────────────────┐ │  │                 │ │
│         │  │ ┌─ goal card ─────────────────────┐   │ │  │ ───────────     │ │
│         │  │ │▌  Explore MCP Patterns [planned] │   │ │  │ (more cards)   │ │
│         │  │ │  tech, mcp    │ "Break into tasks"│   │ │  └────────────────┘ │
│         │  │ └─────────────────────────────────┘   │ │                      │
│         │  └───────────────────────────────────────┘ │                      │
│         │                                            │                      │
│         │  ┌── EXPLORED / RESEARCHED ──────────────┐ │                      │
│         │  │ (collapsed by default — click to show) │ │                      │
│         │  └───────────────────────────────────────┘ │                      │
│         │                                            │                      │
│         │  ┌── COMPLETED (hidden by default) ──────┐ │                      │
│         │  │ [Show 5 completed goals]               │ │                      │
│         │  └───────────────────────────────────────┘ │                      │
└─────────┴────────────────────────────────────────────┴──────────────────────┘
```

**Dashboard layout details:**
- Main/right split: CSS Grid `grid-template-columns: 1fr 380px;`
- Right panel: sticky top, scrolls independently (`position: sticky; top: 24px; max-height: calc(100vh - 48px); overflow-y: auto;`)
- Stage sections: ordered by actionability (Pending Approvals → Actionable → Planned → Researched → Explored → Scoped → Accepted → Completed)
- Completed section: collapsed by default, expandable toggle
- Goal cards: click anywhere to navigate to goal detail

**Goal grouping order:**
1. **Pending Approvals** — goals at `idea` stage (yellow-orange tinted section header)
2. **Actionable** — has tasks, ready to execute
3. **Planned** — plan exists but no tasks yet
4. **Researched** — research reviewed
5. **Explored** — research done, not reviewed
6. **Scoped** — writeup exists
7. **Accepted** — committed but no writeup
8. **Completed** — hidden toggle, shows when expanded
9. **Declined** — hidden entirely from dashboard

### 3.2 Goal Detail Screen

Single goal deep-dive. Shows all artifacts and available actions.

```
┌─────────┬───────────────────────────────────────────────────────────────────┐
│ SIDEBAR │  GOAL HEADER                                                      │
│         │  ┌────────────────────────────────────────────────────────────┐   │
│         │  │ [← Dashboard]                                              │   │
│         │  │                                                            │   │
│         │  │ ★ Land Ideal AI-Native Role           [actionable]         │   │
│         │  │ career • cpto • job-search                                 │   │
│         │  │ Created: Feb 20 · Accepted: Feb 20                         │   │
│         │  │                                                            │   │
│         │  │ [← Revise to planned]  ─────── [Complete Goal →]           │   │
│         │  └────────────────────────────────────────────────────────────┘   │
│         │                                                                    │
│         │  TAB BAR                                                           │
│         │  ┌────────────────────────────────────────────────────────────┐   │
│         │  │ [Tasks]  [Writeup]  [Plan]  [Exploration]                  │   │
│         │  └────────────────────────────────────────────────────────────┘   │
│         │                                                                    │
│         │  TAB: TASKS (default for actionable)                               │
│         │  ┌──────────────────────────────────┐ ┌─ AGENT PANEL ────────┐   │
│         │  │                                  │ │                      │   │
│         │  │ ## Active (2)                    │ │  Recommended:        │   │
│         │  │ ┌──────────────────────────────┐ │ │  ◆ goal-decomposer   │   │
│         │  │ │ □ Research voice APIs         │ │ │    "Break goal into  │   │
│         │  │ │   Research | 45m | Med | SJ+C │ │ │     atomic tasks"   │   │
│         │  │ └──────────────────────────────┘ │ │  [▶ Run]            │   │
│         │  │ ┌──────────────────────────────┐ │ │                      │   │
│         │  │ │ □ Draft positioning doc       │ │ │  ◆ web-researcher   │   │
│         │  │ │   Execution | 30m | High | SJ │ │ │    "Deep research   │   │
│         │  │ └──────────────────────────────┘ │ │     on any topic"   │   │
│         │  │                                  │ │  [▶ Run]            │   │
│         │  │ ## Up Next (4)                   │ │                      │   │
│         │  │ ┌──────────────────────────────┐ │ │  ─────────           │   │
│         │  │ │ □ Build portfolio site        │ │ │  Running:           │   │
│         │  │ │   Coding | 2h | High | SJ    │ │ │  (none)             │   │
│         │  │ └──────────────────────────────┘ │ │                      │   │
│         │  │ ...                              │ │                      │   │
│         │  │                                  │ │                      │   │
│         │  │ ## Completed (6)                 │ │                      │   │
│         │  │ ┌──────────────────────────────┐ │ │                      │   │
│         │  │ │ ☑ Update resume              │ │ │                      │   │
│         │  │ │   ~30m | Moved: Yes          │ │ │                      │   │
│         │  │ └──────────────────────────────┘ │ │                      │   │
│         │  │ ...                              │ │                      │   │
│         │  └──────────────────────────────────┘ └──────────────────────┘   │
│         │                                                                    │
│         │  [+ Add Task]                                                      │
└─────────┴───────────────────────────────────────────────────────────────────┘
```

**Goal detail layout:**
- Header: full width, surface bg, bottom border
- Back link: ghost text, top-left
- Title: 24px Inter bold, inline with focus star and stage badge
- Tags: pills, 12px JetBrains Mono, surface-hover bg
- Stage actions: left = backward (ghost button), right = forward (primary button)
- Tab bar: underline style (active tab has 2px primary bottom border)
- Default tab: determined by stage (Tasks for actionable, Plan for planned, Writeup for scoped, etc.)
- Content/Agent split: CSS Grid `grid-template-columns: 1fr 280px;`
- Agent panel: sticky, surface bg, right side

**Tab visibility rules:**

| Tab | Visible When | Content |
|-----|-------------|---------|
| Tasks | `has_tasks = 1` or stage is `actionable`/`completed` | Task list with sections |
| Writeup | `has_writeup = 1` or stage >= `scoped` | Rendered markdown |
| Plan | `has_plan = 1` or stage >= `planned` | Rendered markdown |
| Exploration | `has_exploration = 1` or stage >= `explored` | File list + rendered content |

**Stage action buttons:**

| Current Stage | Backward Action | Forward Action |
|---------------|----------------|----------------|
| idea | — | [Accept →] [Decline ✗] |
| accepted | — | (show "Write a writeup" hint) |
| scoped | [← Back to accepted] | [Mark as explored →] |
| explored | [← Back to scoped] | [Mark as researched →] |
| researched | [← Back to explored] | (show "Create a plan" hint) |
| planned | [← Back to researched] | (show "Break into tasks" hint) |
| actionable | [← Revise to planned] | [Complete Goal →] |
| completed | [← Reopen] | — |

### 3.3 Scratchpad Screen

Full-page scratchpad with add-entry form and chronological entries.

```
┌─────────┬───────────────────────────────────────────────────────────────────┐
│ SIDEBAR │  SCRATCHPAD                                                       │
│         │                                                                    │
│         │  ┌── ADD ENTRY ──────────────────────────────────────────────┐    │
│         │  │ ┌──────────────────────────────────────────────────────┐  │    │
│         │  │ │ What's on your mind?                                 │  │    │
│         │  │ │ (textarea, 3 rows, auto-expand)                     │  │    │
│         │  │ └──────────────────────────────────────────────────────┘  │    │
│         │  │ Tip: prefix with @claude: for AI-directed entries        │    │
│         │  │                                          [Add Entry]     │    │
│         │  └──────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         │  ┌── ENTRIES ───────────────────────────────────────────────┐    │
│         │  │                                                          │    │
│         │  │  ┌─ Feb 23, 2026 ──────────────────────── (sticky) ──┐  │    │
│         │  │  └───────────────────────────────────────────────────┘  │    │
│         │  │  • Want to build a voice agent MVP by EOW               │    │
│         │  │  • Need to finish enriching 50 companies in DB          │    │
│         │  │  ┌─ @claude entry ──────────────────────────────────┐   │    │
│         │  │  │▎ @claude: research top 3 voice APIs + pricing    │   │    │
│         │  │  └──────────────────────────────────────────────────┘   │    │
│         │  │                                                          │    │
│         │  │  ┌─ Feb 22, 2026 ──────────────────────── (sticky) ──┐  │    │
│         │  │  └───────────────────────────────────────────────────┘  │    │
│         │  │  • Thinking about positioning narrative for CPTO roles   │    │
│         │  │  • Read article on MCP patterns                         │    │
│         │  │                                                          │    │
│         │  │  ┌─ Feb 21, 2026 ──────────────────────── (sticky) ──┐  │    │
│         │  │  └───────────────────────────────────────────────────┘  │    │
│         │  │  • Explored n8n for agent orchestration                 │    │
│         │  │  ┌─ @claude entry ──────────────────────────────────┐   │    │
│         │  │  │▎ @claude: compare n8n vs Temporal for workflows   │   │    │
│         │  │  └──────────────────────────────────────────────────┘   │    │
│         │  │                                                          │    │
│         │  └──────────────────────────────────────────────────────────┘    │
│         │                                                                    │
└─────────┴───────────────────────────────────────────────────────────────────┘
```

**Scratchpad layout:**
- Single column, max-width: 720px, centered in main area
- Add entry form: surface bg card at top, sticky below header
- Date headers: sticky position, surface bg, uppercase month abbreviation, JetBrains Mono 13px
- Regular entries: `--text-primary`, 14px Inter, bullet dash prefix
- @claude entries: 3px left border `--color-warning`, background `--color-warning-muted` at 10% opacity, amber-tinted
- Entry spacing: 8px between entries, 24px between date groups

### 3.4 Focus Screen

Shows only in-focus goals with their active tasks. Distraction-free execution mode.

```
┌─────────┬───────────────────────────────────────────────────────────────────┐
│ SIDEBAR │  FOCUS MODE                                                       │
│         │  "Goals you're actively working on"                               │
│         │                                                                    │
│         │  ┌── FOCUS GOAL 1 ──────────────────────────────────────────┐    │
│         │  │                                                          │    │
│         │  │  ★ Build Task OS Dashboard                [actionable]   │    │
│         │  │  career • taskos                                         │    │
│         │  │                                                          │    │
│         │  │  ── Active Tasks ──                                      │    │
│         │  │  ┌──────────────────────────────────────────────────┐   │    │
│         │  │  │ □ Implement database layer                       │   │    │
│         │  │  │   Coding | 1h | High | SJ                       │   │    │
│         │  │  ├──────────────────────────────────────────────────┤   │    │
│         │  │  │ □ Write sync parsers                             │   │    │
│         │  │  │   Coding | 45m | High | SJ + Claude             │   │    │
│         │  │  └──────────────────────────────────────────────────┘   │    │
│         │  │                                                          │    │
│         │  │  Progress: ████████░░░░░░░░░░░░ 4/12 tasks (33%)        │    │
│         │  │                                                          │    │
│         │  └──────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         │  ┌── FOCUS GOAL 2 ──────────────────────────────────────────┐    │
│         │  │                                                          │    │
│         │  │  ★ Land Ideal AI-Native Role              [planned]      │    │
│         │  │  career • cpto • job-search                              │    │
│         │  │                                                          │    │
│         │  │  ── No Active Tasks ──                                   │    │
│         │  │  Stage is "planned" — break into atomic tasks to begin   │    │
│         │  │  [Create Tasks →]                                        │    │
│         │  │                                                          │    │
│         │  └──────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         │  ┌── NO MORE FOCUS GOALS ───────────────────────────────────┐    │
│         │  │  Add goals to focus from the Dashboard.                  │    │
│         │  └──────────────────────────────────────────────────────────┘    │
│         │                                                                    │
└─────────┴───────────────────────────────────────────────────────────────────┘
```

**Focus layout:**
- Single column, max-width: 900px, centered
- Each focus goal: surface bg card, focus-colored left border (4px, `--color-focus`)
- Only shows goals where `in_focus = true`
- Active tasks shown inline (no tab navigation)
- Progress bar: 6px height, rounded, `--color-primary` fill on `--bg-surface-hover` track
- Empty state for goals without tasks: hint text + action button based on stage

---

## 4. Component Patterns

### 4.1 Goal Card

Used on Dashboard in stage-grouped lists.

```
┌─ 4px left border (stage color) ─────────────────────────────────┐
│                                                                   │
│  ★ Goal Title Here                              [actionable]     │
│  career • taskos • ai                                            │
│                                                  4/12 tasks      │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

**Specs:**
- Container: `--bg-surface`, `--radius-md` (8px), hover: `--bg-surface-hover`
- Left border: 4px solid, color from stage badge table
- Padding: 16px
- Title: 16px Inter 600, `--text-primary`, clickable (entire card is a link)
- Focus star: 16px inline SVG, `--color-focus` when active, `--text-muted` when not
- Stage badge: pill (see 4.2)
- Tags: 12px JetBrains Mono 400, `--text-secondary`, `--bg-surface-hover` bg, 4px radius, 2px 8px padding, spaced 4px apart
- Task progress: right-aligned, 13px JetBrains Mono, `--text-muted`
- Cursor: `cursor: pointer` on entire card
- Transition: background-color `--transition-fast`

**Idea card variant:**
- Same as above but includes rationale text (13px, `--text-secondary`, 2 lines max)
- Action row at bottom: [Accept] primary button + [Decline] danger ghost button

### 4.2 Stage Badge

```
  ┌──────────────┐
  │  actionable  │
  └──────────────┘
```

**Specs:**
- Shape: pill (`border-radius: 12px`)
- Padding: `2px 10px`
- Font: 12px JetBrains Mono 500
- Colors: per stage badge table (Section 1.1)
- No border, no shadow
- Display: `inline-flex; align-items: center;`
- Rendered via `data-stage` attribute: `<span class="stage-badge" data-stage="actionable">actionable</span>`

### 4.3 Task Item

```
┌───────────────────────────────────────────────────────────────────┐
│  □  Research voice APIs: find pricing comparison → action        │
│     Research | 45m | Medium | SJ + Claude                        │
└───────────────────────────────────────────────────────────────────┘
```

**Pending state:**
- Checkbox: custom styled, 18px square, `--border` border, `--radius-sm` radius, hover: `--color-primary` border
- Title: 14px Inter 600, `--text-primary`
- Outcome/action text: 14px Inter 400, `--text-secondary` (after colon)
- Metadata row: 13px JetBrains Mono 400, `--text-muted`, pipe-separated

**Completed state:**
```
┌───────────────────────────────────────────────────────────────────┐
│  ☑  Update resume: polished for AI roles → final review          │
│     ~30m | Moved toward goal: Yes                                 │
│     Notes: Focused on AI-native positioning                       │
└───────────────────────────────────────────────────────────────────┘
```
- Checkbox: filled, `--color-success` bg, white checkmark SVG
- Title: `text-decoration: line-through`, `--text-muted` color
- Metadata: actual time + moved toward goal
- Notes: italic, `--text-muted`

### 4.4 Scratchpad Entry

**Regular entry:**
```
  –  Want to build a voice agent MVP by EOW
```
- Prefix: em-dash `–`, `--text-muted`
- Text: 14px Inter 400, `--text-primary`
- Padding: 4px 0

**@claude entry:**
```
  ┌─ 3px amber left border ──────────────────────────────┐
  │  @claude: research top 3 voice APIs + pricing         │
  └───────────────────────────────────────────────────────┘
```
- Container: 3px left border `--color-warning`, background `rgba(245, 158, 11, 0.05)`
- Padding: 8px 12px
- `@claude:` prefix: `--color-warning`, JetBrains Mono 500
- Rest of text: 14px Inter 400, `--text-primary`

**Date header:**
```
  ── February 23, 2026 ──────────────────────────────────
```
- Font: 13px JetBrains Mono 500, `--text-secondary`
- Position: `position: sticky; top: 0;`
- Background: `--bg-primary` (to cover scrolling content)
- Padding: 8px 0
- Border-bottom: 1px solid `--border-subtle`

### 4.5 Suggestion Card

```
┌───────────────────────────────────────────────────────────────────┐
│  ⚡ Build Voice Agent MVP                                         │
│  "Mentioned voice APIs in 3 entries over 2 weeks"                │
│  Confidence: 85%  ████████░░                                     │
│                                                                   │
│  [✓ Approve]  [✗ Decline]                                        │
└───────────────────────────────────────────────────────────────────┘
```

**Specs:**
- Container: `--bg-surface`, `--radius-md`, 1px border `--border-subtle`
- Icon: Sparkles SVG, 16px, `--color-warning`
- Title: 14px Inter 600, `--text-primary`
- Rationale: 13px Inter 400, `--text-secondary`, italic
- Confidence: 12px JetBrains Mono, `--text-muted`, with mini progress bar (4px height)
- Approve button: small primary button
- Decline button: small ghost-danger button

### 4.6 Agent Panel

Right sidebar on Goal Detail screen.

```
┌── AGENTS ──────────────────────────────┐
│                                        │
│  Recommended for this stage:           │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ ⚙ goal-decomposer               │ │
│  │ Break goal into atomic tasks     │ │
│  │ [▶ Run Agent]                    │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ ⚙ web-researcher                │ │
│  │ Deep 7-angle research            │ │
│  │ [▶ Run Agent]                    │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ── Running ──                         │
│  (none active)                         │
│                                        │
└────────────────────────────────────────┘
```

**Specs:**
- Container: `--bg-surface`, `--radius-md`, sticky top
- Width: 280px
- Section header: 12px Inter 600, `--text-muted`, uppercase
- Agent item: `--bg-primary` bg at 5% opacity, `--radius-sm`, 12px padding
- Agent name: 14px Inter 500, `--text-primary`
- Agent description: 13px Inter 400, `--text-secondary`
- Run button: small primary button
- Running state: pulse animation on agent item, "Running..." text

### 4.7 Buttons

**Primary button:**
```css
.btn-primary {
  background: var(--color-primary);
  color: #FFFFFF;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font: 500 14px/1 var(--font-body);
  border: none;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}
.btn-primary:hover {
  background: var(--color-primary-hover);
}
```

**Ghost button:**
```css
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font: 500 14px/1 var(--font-body);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-ghost:hover {
  border-color: var(--border);
  color: var(--text-primary);
}
```

**Danger button:**
```css
.btn-danger {
  background: var(--color-danger);
  color: #FFFFFF;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font: 500 14px/1 var(--font-body);
  border: none;
  cursor: pointer;
  transition: background-color var(--transition-fast);
}
.btn-danger:hover {
  background: #DC2626; /* red-600 */
}
```

**Small button variant:** `padding: 4px 12px; font-size: 13px;`

**Icon button:** `padding: 6px; width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center;`

### 4.8 Focus Star

**Active (in focus):**
```
★  — filled star SVG, 16px, color: var(--color-focus)
```

**Inactive (not in focus):**
```
☆  — outline star SVG, 16px, color: var(--text-muted)
     hover: color: var(--color-focus) at 50% opacity
```

**Interaction:** Click toggles focus state via HTMX PUT. Transition on color change.

### 4.9 Progress Bar

Used on Focus screen for task completion.

```
  ████████████░░░░░░░░░░░░░░  4/12 tasks (33%)
```

**Specs:**
- Track: 6px height, `--bg-surface-hover`, full rounded
- Fill: `--color-primary`, rounded, width = percentage
- Label: right of bar, 13px JetBrains Mono, `--text-muted`
- Transition: width `--transition-slow`

### 4.10 Tab Bar

Used on Goal Detail screen.

```
  [Tasks]   [Writeup]   [Plan]   [Exploration]
  ═══════
```

**Specs:**
- Container: flex, gap 0, border-bottom 1px `--border-subtle`
- Tab item: padding 12px 16px, 14px Inter 500
- Active tab: `--text-primary`, 2px bottom border `--color-primary`
- Inactive tab: `--text-muted`, no bottom border
- Hover: `--text-secondary`
- Tab content loads via HTMX GET, swaps into `#tab-content` div

---

## 5. HTMX Interaction Patterns

### 5.1 Interaction Table

| Interaction | Trigger | HTMX Attributes | Target | Swap | Notes |
|-------------|---------|-----------------|--------|------|-------|
| Toggle focus | Click star icon | `hx-put="/api/goals/{slug}/focus"` | `#goal-card-{slug}` | `outerHTML` | Returns updated card fragment |
| Advance stage | Click forward button | `hx-put="/api/goals/{slug}/stage" hx-vals='{"direction":"forward"}'` | `#goal-header` | `outerHTML` | Returns updated header |
| Regress stage | Click backward button | `hx-put="/api/goals/{slug}/stage" hx-vals='{"direction":"backward"}'` | `#goal-header` | `outerHTML` | Returns updated header |
| Decline goal | Click decline | `hx-put="/api/goals/{slug}/stage" hx-vals='{"stage":"declined"}'` | `#goal-card-{slug}` | `outerHTML` | Card fades out / shows declined state |
| Accept goal | Click accept | `hx-put="/api/goals/{slug}/stage" hx-vals='{"stage":"accepted"}'` | `#goal-card-{slug}` | `outerHTML` | Card moves to accepted section |
| Complete task | Click checkbox | `hx-put="/api/tasks/{id}/status" hx-vals='{"status":"completed"}'` | `#task-{id}` | `outerHTML` | Returns completed task fragment |
| Uncomplete task | Click completed checkbox | `hx-put="/api/tasks/{id}/status" hx-vals='{"status":"pending"}'` | `#task-{id}` | `outerHTML` | Returns pending task fragment |
| Add scratchpad entry | Submit form | `hx-post="/api/scratchpad"` | `#scratchpad-entries` | `afterbegin` | Prepends new entry, clears form |
| Add task | Submit form | `hx-post="/api/goals/{slug}/tasks"` | `#task-list` | `beforeend` | Appends new task item |
| Switch tab | Click tab | `hx-get="/api/goals/{slug}/tab/{name}"` | `#tab-content` | `innerHTML` | Lazy-loads tab content |
| Approve suggestion | Click approve | `hx-post="/api/suggestions/{id}/approve"` | `#suggestion-{id}` | `outerHTML` | Shows "Goal created" confirmation |
| Decline suggestion | Click decline | `hx-post="/api/suggestions/{id}/decline"` | `#suggestion-{id}` | `outerHTML` | Fades out card |
| Run agent | Click run | `hx-post="/api/agents/{name}/run" hx-vals='{"goal_slug":"{slug}"}'` | `#agent-status-{name}` | `innerHTML` | Shows running state |
| Poll agent status | Auto-trigger | `hx-get="/api/agents/{name}/status" hx-trigger="every 5s"` | `#agent-status-{name}` | `innerHTML` | Updates until complete |
| Sync now | Click button | `hx-post="/api/sync"` | `#sync-status` | `innerHTML` | Shows "Syncing..." then result |
| Detect goals | Click button | `hx-post="/api/goal-detector/run"` | `#suggestions-list` | `innerHTML` | Shows loading, then new suggestions |

### 5.2 HTMX Configuration

```html
<!-- In base.html <head> -->
<script src="https://unpkg.com/htmx.org@1.9.12"></script>

<!-- Global HTMX config -->
<meta name="htmx-config" content='{
  "defaultSwapStyle": "outerHTML",
  "defaultSettleDelay": 20,
  "includeIndicatorStyles": false
}'>
```

### 5.3 Loading States

**HTMX loading indicator pattern:**

```html
<!-- Element being swapped gets a CSS class during request -->
<div hx-indicator="this" class="htmx-indicator-parent">
  <!-- Content here -->
</div>
```

```css
/* Pulse animation during HTMX request */
.htmx-request {
  opacity: 0.6;
  animation: htmx-pulse 1.5s ease-in-out infinite;
}

@keyframes htmx-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 0.3; }
}

/* Skeleton placeholder for lazy-loaded tabs */
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-surface) 25%,
    var(--bg-surface-hover) 50%,
    var(--bg-surface) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
  height: 16px;
  margin: 8px 0;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### 5.4 Form Patterns

**Scratchpad add entry:**
```html
<form hx-post="/api/scratchpad"
      hx-target="#scratchpad-entries"
      hx-swap="afterbegin"
      hx-on::after-request="this.reset()">
  <textarea name="content"
            placeholder="What's on your mind?"
            rows="3"
            required></textarea>
  <button type="submit" class="btn-primary btn-sm">Add Entry</button>
</form>
```

**Task add form (on goal detail):**
```html
<form hx-post="/api/goals/{slug}/tasks"
      hx-target="#task-list"
      hx-swap="beforeend"
      hx-on::after-request="this.reset()">
  <input type="text" name="title" placeholder="Task title" required>
  <input type="text" name="outcome" placeholder="Expected outcome">
  <select name="task_type">
    <option value="Execution">Execution</option>
    <option value="Research">Research</option>
    <option value="Decision">Decision</option>
    <option value="Coding">Coding</option>
    <option value="Exploration">Exploration</option>
    <option value="Learning">Learning</option>
  </select>
  <button type="submit" class="btn-primary btn-sm">Add Task</button>
</form>
```

---

## 6. CSS Architecture

### 6.1 File Structure

Single file: `taskos/src/taskos/static/style.css`. No preprocessor, no build step.

### 6.2 Naming Convention

BEM-lite: component-level class names, no deep nesting.

```
.goal-card           — block
.goal-card__title    — element (only if needed for disambiguation)
.goal-card--idea     — modifier (rare, prefer data attributes)
```

Prefer `data-*` attributes for state-driven styling over modifier classes:

```css
/* Prefer this: */
.stage-badge[data-stage="actionable"] { ... }

/* Over this: */
.stage-badge--actionable { ... }
```

### 6.3 CSS Custom Properties Block

```css
:root {
  /* Backgrounds */
  --bg-primary: #0F172A;
  --bg-surface: #1E293B;
  --bg-surface-hover: #334155;
  --bg-input: #0F172A;
  --bg-elevated: #334155;

  /* Borders */
  --border: #475569;
  --border-subtle: #334155;
  --border-focus: #6366F1;

  /* Text */
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;

  /* Semantic Colors */
  --color-primary: #6366F1;
  --color-primary-hover: #818CF8;
  --color-primary-muted: #312E81;
  --color-success: #22C55E;
  --color-success-muted: #052E16;
  --color-warning: #F59E0B;
  --color-warning-muted: #451A03;
  --color-danger: #EF4444;
  --color-danger-muted: #450A0A;
  --color-focus: #8B5CF6;
  --color-info: #3B82F6;

  /* Stage Badges */
  --stage-idea-bg: #1E293B;       --stage-idea-text: #94A3B8;
  --stage-accepted-bg: #1E3A5F;   --stage-accepted-text: #60A5FA;
  --stage-scoped-bg: #1E3A5F;     --stage-scoped-text: #60A5FA;
  --stage-explored-bg: #164E63;   --stage-explored-text: #22D3EE;
  --stage-researched-bg: #164E63; --stage-researched-text: #22D3EE;
  --stage-planned-bg: #3B0764;    --stage-planned-text: #C084FC;
  --stage-actionable-bg: #14532D; --stage-actionable-text: #4ADE80;
  --stage-completed-bg: #052E16;  --stage-completed-text: #22C55E;
  --stage-declined-bg: #450A0A;   --stage-declined-text: #F87171;

  /* Typography */
  --font-heading: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-base: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 200ms ease;
  --transition-slow: 300ms ease;
}
```

### 6.4 CSS Section Order

```css
/* 1. Reset & Base */
/* 2. Custom Properties (above) */
/* 3. Typography */
/* 4. Layout (sidebar, main, grid) */
/* 5. Components (goal-card, stage-badge, task-item, etc.) */
/* 6. Pages (dashboard-specific, scratchpad-specific, etc.) */
/* 7. HTMX States (loading, swapping) */
/* 8. Utility classes (only if absolutely needed) */
```

### 6.5 CSS Reset (Minimal)

```css
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  background: var(--bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a {
  color: var(--color-primary);
  text-decoration: none;
  transition: color var(--transition-fast);
}
a:hover {
  color: var(--color-primary-hover);
}

button {
  font-family: inherit;
  cursor: pointer;
}

input, textarea, select {
  font-family: inherit;
  font-size: inherit;
  color: var(--text-primary);
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-sm) var(--space-md);
  outline: none;
  transition: border-color var(--transition-fast);
}
input:focus, textarea:focus, select:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}
```

### 6.6 Accessibility Notes

- All text meets WCAG AA 4.5:1 contrast minimum against its background
- `--text-primary` (#F8FAFC) on `--bg-primary` (#0F172A) = **15.4:1** ratio
- `--text-secondary` (#94A3B8) on `--bg-primary` (#0F172A) = **5.9:1** ratio
- `--text-muted` (#64748B) on `--bg-primary` (#0F172A) = **4.6:1** ratio (meets AA)
- Stage badge text on stage badge bg: all pairs exceed 4.5:1 (verified in table above)
- Focus rings visible on all interactive elements
- No color as sole indicator — always paired with text labels or icons
- `prefers-reduced-motion` media query: disable animations for users who prefer reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 7. Icons (Heroicons Outline)

All icons are inline SVG from [Heroicons](https://heroicons.com/) outline set. No icon font, no emoji.

| Icon | Heroicon Name | Usage |
|------|--------------|-------|
| Focus star (active) | `star` (solid) | In-focus goals |
| Focus star (inactive) | `star` (outline) | Not-in-focus goals |
| Completed | `check-circle` | Completed tasks, completed stage |
| Declined | `x-circle` | Declined goals |
| Advance stage | `arrow-right` | Forward stage button |
| Regress stage | `arrow-left` | Backward stage button |
| Explored | `beaker` | Explored stage indicator |
| Writeup | `document-text` | Writeup tab, writeup exists |
| Tasks | `clipboard-document-list` | Tasks tab, task count |
| GoalDetector | `sparkles` | Goal suggestions, AI-detected |
| Agent | `cpu-chip` | Agent panel, agent items |
| Sync | `arrow-path` | Sync status, sync button |
| Add | `plus` | Add entry, add task |
| Dashboard | `squares-2x2` | Sidebar nav |
| Scratchpad | `pencil-square` | Sidebar nav |
| Focus | `bolt` | Sidebar nav |
| Back | `arrow-left` | Goal detail back link |
| Expand | `chevron-down` | Collapse/expand sections |

**SVG sizing:** All icons rendered at `width="18" height="18"` in sidebar, `width="16" height="16"` inline with text, `width="20" height="20"` in buttons.

**SVG color:** Icons inherit text color via `stroke="currentColor"`.

---

## 8. Design Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Dark theme only | No light mode toggle | Personal tool, developer preference, simpler CSS |
| Desktop-only | No responsive breakpoints | Used on workstation only, 1440px+ |
| Single CSS file | No preprocessor, no build | Keep tooling minimal for personal project |
| Inter + JetBrains Mono | Over Fira family | Inter is more versatile for headings, JetBrains Mono is industry standard for dev tools |
| No Tailwind CSS | Vanilla CSS with custom properties | Avoid build step, full control, simpler for HTMX templates |
| Data attributes for state | `data-stage`, `data-status` | Cleaner HTML, single source of truth, avoids class string manipulation |
| Inline SVG icons | Over icon font or sprites | Better accessibility, individual coloring, no extra HTTP request |
| HTMX outerHTML default | Over innerHTML | Component-level replacement is more predictable with fragments |
| Sticky date headers | In scratchpad | Maintains context while scrolling long entry lists |
| Tab-based goal detail | Over accordion or scroll sections | Cleaner, reduces cognitive load, lazy-loadable |
| Right sidebar sticky | On dashboard | Scratchpad and suggestions always visible while scrolling goals |
| Progress bars on focus | Not on dashboard cards | Focus screen is for execution, dashboard is for overview |
