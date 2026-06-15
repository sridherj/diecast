# Research Note 01 — Learn from Existing Systems & the Maintainer's Corpus

> **Step 1** of the *Refine Requirements v2* exploration. Foundational, runs first; every
> later step (2–7) is meant to cite this brief instead of re-researching.
> **Agent:** cast-web-researcher · **Date:** 2026-06-11 · **Status:** ai (no human edits yet)
>
> **Method:** four parallel code/corpus explorations (Diecast `cast-server`, gbrain/gstack
> skills, `cast-preso*` agents, the maintainer's writeup corpus across 3 workspaces) +
> five external web searches. All code claims carry `file:line` citations from the
> exploration; external claims carry source links (see **Sources** at the end).

---

## 0. Executive Summary — what the ground truth says about the owner's three bets

The refined spec rests on three hypotheses the owner explicitly deferred to exploration.
Step 1's job was to confirm or refute them *cheaply, from evidence that already exists*.
Verdicts up front:

1. **"DB-canonical, generated renders" is real and reusable — but it does NOT exist for
   requirements today, and it has *no versioning/diff/stable-ID/comment* machinery.** Diecast
   genuinely implements DB→file one-way renders for `goal.yaml` and `tasks.md`
   (`goal_service.py:337`, `task_service.py:389`). But the requirements artifacts
   (`refined_requirements.collab.md` etc.) are the *opposite* pattern — **file-canonical, DB
   stores only a path pointer** (`schema.sql:35` `task_artifacts`). So Step 2 is not "copy the
   goal pattern"; it's "choose between two patterns Diecast *already runs side by side*, then
   add the three things neither has: stable element IDs, versioning, and comment anchoring."

2. **The 5-family taxonomy captures only ~45–55% of the maintainer's real corpus cleanly.**
   Empirical sampling of 22 real docs found a *large* unrepresented cluster —
   **Evaluation/Testing** — plus recurring **Refactor/Migration**, **Decision/ADR**, and
   **Design/UX-spec** shapes. This is hard evidence the taxonomy axis needs adjustment before
   Step 3 cements five boxes (it confirms the spec's own "axis may be wrong" worry).

3. **The "needs React" worry is very likely a false premise** — and there is a W3C standard
   (Web Annotation Data Model) plus mature JS libraries (Hypothesis/Annotator.js,
   Annotorious) that anchor comments to content *without* a SPA. This pre-loads Step 4's
   verdict: element-anchored comments on stable IDs over server-rendered DOM is a well-trodden
   path. (Full decision is Step 4's; Step 1 supplies the prior art.)

Two strong *positive* discoveries the owner should lean on:

- **gstack's `/spec` and `/office-hours` skills are near-exact prior art** for an AI-native
  requirements authoring loop — phased interrogation, "read the code before asking," testable
  acceptance criteria, an **adversarial reviewer subagent** quality gate, and the **0-10
  rate→gap→fix→re-rate** review loop. These are the highest-value imports in the whole brief.
- **`cast-preso*` is a working, in-house library** for exactly the HTML information-architecture
  problem Step 5 must solve: a named-archetype catalog, L1/L2 hierarchy as a *typed, checkable
  field*, WHAT/HOW separation enforced across agents, and a tone/AI-slop checker. Reuse the
  *architecture*, retune the *density thresholds* (slides ≠ docs).

---

## 1. Diecast's DB-canonical → generated-renders pattern (substep 1)

**Bottom line:** Diecast runs *two* artifact patterns simultaneously. Naming them precisely is
the single most useful thing this section gives Step 2.

### 1a. The runtime is NOT what the MVCS framing implies
Despite MVCS-flavored tooling, goals/tasks persist via **SQLite + hand-written `sqlite3` SQL +
Pydantic models** — there are **no SQLAlchemy entities and no repository layer**
(`db/` contains only `connection.py` + `schema.sql`). Render-to-disk is a **service-layer
side-effect** appended after `conn.commit()` (`task_service.py:172-173`). Any "requirements as
DB entities" design that assumes a clean ORM/repository to extend is mismatched with today's
reality — it would be *new* infrastructure, not an extension.

### 1b. Pattern A — DB-canonical, file is a disposable one-way render
- `goal.yaml`: `goal_service._write_goal_yaml()` (`goal_service.py:337-363`), field-patched by
  `_update_goal_yaml_fields()` (`:366-386`). Stamped `# AUTO-GENERATED: Read-only render of DB
  state. Do not edit directly.` (`:358`).
- `tasks.md`: `task_service._rerender_tasks_md()` (`:389-455`) — **full re-render from DB on
  every mutation** (not a diff/patch), called from every write path (`:173,206,237,274,385`).
- **No reverse sync.** An exhaustive grep found no file→DB loader for goals/tasks; the only
  `yaml.safe_load` of `goal.yaml` is a self-merge (`:375`). Hand-edits to these files are
  silently lost on next mutation.
- IDs: **goals use a human-readable slug** derived from title (`_slugify`, `:389-395`) that is
  PK + directory name + FK target — but it is **not collision-guarded** and immutable once the
  dir exists. **Tasks use an int autoincrement** (`schema.sql:17`).

### 1c. Pattern B — file-canonical, DB stores only a pointer (today's requirements artifacts)
- `requirements.human.md`, `refined_requirements.collab.md`, `plan.collab.md`, all `*.ai.md`
  research outputs: **the file IS the source of truth.** The DB stores only a relative-path
  reference in `tasks.task_artifacts` (JSON array, `schema.sql:35`), path-validated against the
  goal dir (`task_service.py:15-43`). Files are directly writable via PUT `/api/artifacts/save`
  (`api_artifacts.py:94`), suffix-gated so only `.human.md`/`.collab.md` are editable (`:44-49`).

### 1d. The `.human/.ai/.collab` suffix convention (documented + enforced)
Canonical spec: `docs/specs/cast-init-conventions.collab.md:141-143`.
| Suffix | Meaning | Editable in UI? |
|---|---|---|
| `.human.md` | Human-authored | ✅ |
| `.ai.md` | Agent-authored, no human edits yet | ❌ (read via `.context-map.md`) |
| `.collab.md` | Mixed authorship over time | ✅ |
A **graduation rule** renames `.ai.md`→`.collab.md` when a human edits ≥20% of lines or
adds/removes a section (`:120,145`). `.context-map.md` is a *third* render type — a file→file
TOC index over all `*.ai.md`, mtime-staleness-skipped (`context_map.py:87-153`), so agents read
one index instead of every `.ai.md` (the token-savings move this very note benefits from).

### 1e. Reusability verdict for the requirements store (feeds Step 2)
| Capability the requirements store needs | Does Diecast have it today? | Verdict |
|---|---|---|
| DB-canonical body + generated md/html render | Yes for goal/task (Pattern A) — **as a copyable template** (`_rerender_tasks_md` + read-only stamp + suffix gate) | **REUSE the mechanic**, but it's a full-rewrite per render |
| Stable element IDs (US/FR/SC anchors) | **No.** Goal slugs aren't collision-safe; tasks are opaque ints; element-level IDs don't exist | **BUILD NEW** (Step 2 keystone) |
| Versioning / archival of old versions | **No.** Prior render is overwritten (`task_service.py:453`); no history | **BUILD NEW** (US5) |
| Diff / change-summary between versions | **No** | **BUILD NEW** (FR-017, Step 4) |
| Comments anchored to elements | **No** | **BUILD NEW** (US4, Step 4) |
| Round-trip (downstream → requirements) | **No** for goals/tasks; the `agents`/`scratchpad` tables *do* carry a `synced_at` column (`schema.sql:46,69`) hinting a 2-way pattern exists elsewhere to study | **BUILD NEW**, study `synced_at` precedent (Step 7) |
| Downstream md contract (planner/task-suggester/spec-checker) | Yes — they read `refined_requirements.collab.md` in spec-kit shape today | **PRESERVE byte-compatibly** (FR-007/SC-004) |

**Contrarian flag for Step 2:** the spec's Directional Ideas lean toward Pattern A ("requirements
as DB entities"). But Pattern B (file-canonical + DB metadata/pointer) is *also already in
production* and is the lighter migration — it keeps FR-007 trivially satisfied (the file is
already the markdown the downstream agents read). The real question Step 2 must answer is not "DB
vs file" in the abstract but **"do stable IDs + versioning + comments *require* a DB-canonical
body, or can they be a DB sidecar keyed to a stable-ID-annotated file?"** Evidence below (§5,
W3C Web Annotation) says a sidecar keyed to stable IDs is viable — which would make Pattern B
the cheaper, contract-preserving choice. This is the highest-leverage open question to resolve.

---

## 2. gbrain / gstack — portable requirements-handling ideas, keep/drop (substep 2)

gstack skills live at `/data/workspace/reference_repos/gstack/<skill>/SKILL.md`. The most
relevant skill is one **not in the original ask: `/spec`** — gstack's requirements-authoring
engine, an almost-exact analog of `cast-refine-requirements`. Plus `/office-hours` (pre-spec
ideation) and the four `/plan-*-review` skills (review-loop mechanics).

### 2a. `/spec` — phased interrogation that produces a backlog-ready doc
- **HARD GATE:** *"Do NOT produce an issue after the first message. Always start with Phase 1."*
  This is the exact anti-one-shot discipline `cast-refine-requirements` should adopt.
- Phases: **Why** (5 locked questions: who / current behavior *verified* / desired / why-now /
  how-we'll-know-done) → **Scope** (out-of-scope locked *early*) → **Technical Interrogation**
  (*read the code FIRST, cite `path:line`* — "the magical moment… grounded in their actual
  code, not generic checklists") → **Draft Review** → **Quality Gate** (a *second model* scores
  the spec **0–10 for "executability by an unfamiliar implementer"**; ≥7 passes, <7 loops, max 3).
- **Template:** Context → Current State (verified, file:line) → Proposed Change → Acceptance
  Criteria (numbered, pass/fail) → Testing Plan → Rollback → Effort → Files Reference → Out of
  Scope → Related. **Epics add a Child-Issues table + Dependency Graph + Sequencing Rationale.**
- **"Match template to content"** rule: bug fixes skip architecture diagrams; new subsystems
  skip "current vs expected." → *direct support for family-shaped documents (Step 3).*

### 2b. `/office-hours` — ideation → design doc, with a revision chain
- Produces a **design doc** (never code), with a **`Supersedes:` field** referencing the prior
  doc on that branch → a *traceable revision chain across sessions* (a lightweight versioning
  model worth copying for US5).
- **Spec Review Loop (high value):** before showing the user, it dispatches an **independent
  adversarial reviewer subagent with fresh context that sees only the document, not the
  conversation**, scoring 1-10 across **Completeness / Consistency / Clarity / Scope /
  Feasibility**, max-3-iteration convergence guard, **fail-soft** if the subagent is
  unavailable. Diecast's child-delegation makes this trivial to port.
- **Work-type classification + routing + mid-flow re-classification:** office-hours classifies
  the work (startup/intrapreneurship/hackathon/OSS/learning/fun) → routes mode → routes *which*
  questions fire, and supports upgrading mid-session ("actually this could be a real company").
  → *direct prior art for US2 classification + US6 routing + reclassification (US6 Sc.4).*

### 2c. The review-loop mechanics (from `/plan-*-review`)
- **0-10 rate→gap→fix→re-rate loop** (design + devex reviews): *Rate "IA: 4/10" → Gap "a 10
  would have…" → Fix → Re-rate "now 8/10, still missing X" → AskUserQuestion only if a real
  choice remains → repeat.* Re-runnable; 8+ dimensions get a quick pass. This is a concrete,
  visceral, idempotent review UX — a strong model for the comment/iteration loop (US4).
- **Confidence calibration + "quote the verbatim motivating line" pre-emit gate** (eng review):
  every finding carries 1-10 confidence; unquotable findings are force-dropped. An auditable
  false-positive killer → maps to "this requirement is ambiguous because «quote»."
- **Decision-brief AskUserQuestion contract** (shared across all skills): ELI10 + stakes +
  always-present recommendation + Completeness A=X/10 + ✅/❌ + dual human/CC effort + one
  `(recommended)`; **one issue = one question, never batch.** Diecast already has
  `cast-interactive-questions` covering part of this.
- **Decisions Log table inside the doc** (Date / Decision / Rationale) — from `DESIGN.md`; a
  lightweight in-document audit trail of *why* each choice was made.

### 2d. Keep / Drop verdicts
**KEEP (port to cast-refine-requirements / the v2 design):**
| Idea | Source | Rationale |
|---|---|---|
| Hard "no output after first message" + named phases | /spec | Forces real refinement vs one-shot rewrite |
| The 5 "Why" questions | /spec Ph1 | Tight reusable completeness checklist |
| Read code before asking, cite `path:line` | /spec Ph3 | Kills generic-checklist feel; Diecast has `cast-code-explorer` to feed it |
| Testable acceptance criteria + quantify-or-acknowledge | /spec | Biggest single quality lever; matches Diecast's existing EARS "WHEN…THE SYSTEM SHALL" |
| Out-of-scope locked early | /spec Ph2 | Cheap anti-creep insurance |
| Adversarial reviewer subagent (5-dim 1-10, max-3, fail-soft) | /office-hours | Self-contained quality gate; degrades gracefully |
| 0-10 rate→gap→fix→re-rate loop | plan-design/devex | The interactive review UX the owner wants (US4) |
| Confidence calibration + quote-the-line gate | plan-eng | Auditable ambiguity flagging |
| Work-type classification routing questions AND template, with mid-flow reclassification | office-hours / /spec | Direct prior art for US2 + US6 |
| `Supersedes:` revision chain + durable decision log | office-hours | Real doc versioning; prevents re-litigating settled calls (US5/US7) |
| AI-slop / Voice ban list (em dashes, "delve/robust/comprehensive", happy-talk) | every skill | Keeps generated prose human; Diecast's `cast-preso-check-tone` already mirrors it |
| In-doc Decisions Log table | DESIGN.md | Lightweight provenance of *why* (feeds US7 provenance) |
| Carved-skeleton + on-demand `sections/` + "read in full, don't work from memory" | all reviewers | Keeps the skill small while supporting deep review content |

**DROP (and why):**
| Idea | Why not |
|---|---|
| Pretext-native HTML / 30KB inline engine / smart API routing | Solves pixel-faithful UI mockups; a requirements doc doesn't need computed text reflow. Use `cast-preso*` for HTML instead |
| Full DESIGN.md design-system generation (font/color/motion tokens) | Out of scope; only the *Decisions Log* sub-pattern is worth lifting |
| gstack preamble/telemetry/brain-cache/builder-profile (~600-760 lines) | Diecast has its own server/HTTP persistence (`cast-goals`, `cast-runs`) |
| plan-tune's full question-preference engine (`<gstack-qid>` markers, PreToolUse hooks, dual-track profile) | Powerful but heavy; the *concept* (silence recurring questions) is nice-to-have, the impl is its own project. Defer |
| Codex CLI as the second-opinion model | Hardwires OpenAI; port the *cross-model review concept* with a Claude subagent (gstack itself falls back to one) |
| GitHub-issue filing + secret/PII redaction sink | /spec files to GitHub; Diecast persists to its own store; redaction is public-repo safety, irrelevant internally |

---

## 3. cast-preso* — reusable visual-hierarchy / progressive-disclosure patterns (substep 3)

`cast-preso*` is a four-stage WHAT→HOW pipeline with a shared **visual toolkit skill**
(`~/.claude/skills/cast-preso-visual-toolkit/`, source of record `visual_toolkit.human.md`).
Its single most transferable idea: **it separates WHAT (content contract) from HOW (rendering)
into different agents, enforces a named-archetype catalog instead of improvised layouts, and
makes L1/L2 hierarchy a first-class checkable field.** All three map cleanly onto a requirements
doc.

### 3a. Named-archetype catalog (maps to "document section types" for Step 5)
11 archetypes (`SKILL.md:23`): `single-stat-hero`, `compare-contrast`, `timeline`,
`diagram-annotated`, `code-showcase`, `consulting-exhibit`, `one-statement`,
`illustrated-section-opener`, `build-up-sequence`, `title-slide`, `close-cta`. Each carries
when-to-use + density limits + checker criteria (`visual_toolkit.human.md:183-323`). Rule:
*"NEVER improvise a slide layout — pick a named archetype"* (`SKILL.md:46`).
**Most reusable for requirements: the Consulting Exhibit** — *action-title (a complete sentence
asserting a finding, verb required) + evidence body + source line; "no orphan data"*
(`:259-272`). This is almost exactly a well-formed requirement: assertion + acceptance criteria +
rationale/traceability. "No orphan data" ↔ "no requirement without rationale."

### 3b. L1/L2 hierarchy as a typed, operationally-defined, triple-encoded field
- **Typed + checkable:** the what-planner sets it, the what-worker copies it verbatim, the
  how-maker styles it, three checkers verify it. Operational definitions (`what-planner.md:104-111`):
  **L1 = survives a 50% content cut; L2 = first to cut when dense.** Far sharper than "important
  vs less important," and a great prioritization forcing-function.
- **Triple visual encoding:** L1 vs L2 differ on **size + weight + color simultaneously**
  (`visual_toolkit.human.md:42-43`: L1 1.1em/600/text vs L2 0.9em/400/muted), not just indentation.
- **Summary-first / "read only the titles" test** (`:95`): *"can someone read ONLY the titles and
  understand the full argument?"* → for requirements: reading only headers + L1 lines conveys the
  whole scope. This is the 2-minute-comprehension mechanism (SC-001) in nascent form.
- **Progressive disclosure with a static fallback:** reveal.js fragments give focus
  (fade-in-then-semi-out), but the `?callout=none` mode renders everything expanded
  (`:114-120`) — *ship that as the print/search/accessibility fallback.*

### 3c. Token system + checkers (what "good" looks like, encoded as negative space)
- CSS custom-property tokens with per-deck `:root` override; **"NEVER hardcode hex"**
  (`SKILL.md:45`). Reuse the *token architecture*; reconsider the *values* (deck cream+navy+mono
  ≠ a dense doc).
- **Three checkers** (visual / content / tone), each emitting `{dimension, verdict, score,
  issues[]}` where every issue carries `what_good_looks_like` (the fix) + `what_worked` (preserve
  on rework). Flagship rules: visual `not-generic` (*"default title+bullets+image-right ⇒ FAIL"*),
  `not-ai-aesthetic` (icon-grid / cyan-magenta gradients / uniform boxes), content
  `one-clear-takeaway` (<5s), tone **em-dashes = hard FAIL** + a banned-GPT-ism list + an
  "Authorship Spectrum" holistic test. → reuse the *schema + AI-slop criteria*; **retune the
  density numbers** (max-50-words / min-30%-whitespace are projector constraints, not doc ones).

### 3d. Transferable-patterns shortlist for Step 5 (each with the slides≠docs caveat)
1. **Named section archetypes** (single-metric/SLA, before-vs-after, system-flow, phased-rollout,
   decision-with-options, API/schema snippet). *Caveat:* drop the per-slide density caps.
2. **L1/L2 as a declared, triple-encoded tier** + the 50%-cut definition. *Caveat:* requirements
   often need ≥3 tiers (MoSCoW) + traceability IDs — extend, don't copy 1:1.
3. **Assertion headings + "read only the titles" validation.** *Caveat:* a doc should never
   *withhold* — drop the talk's hook/reveal tension; every heading maximally informative.
4. **Progressive disclosure with `callout=none` static fallback** (`<details>` for rationale/edge
   cases). *Caveat:* drop timed auto-advance animation.
5. **CSS-token theming with per-doc override.** 6. **WHAT/HOW as two layers/passes, not two
   services.** 7. **"Don't collapse roles into uniform boxes"** (hero requirement vs sub-items vs
   notes get distinct visual weight) — achieved via typography/layout, not the preso SVG mandate.
8. **The three-dimension checker harness** (content/structure/tone) with fix + preserve per
   issue, including the em-dash/GPT-ism ban. 9. **Consulting-Exhibit = default requirement block.**

---

## 4. The maintainer's corpus, bucketed by family — taxonomy ground truth (substep 4)

22 real docs sampled across `second-brain`, `linkedout-oss`, `diecast`. **This is the empirical
input that Step 3 must classify against rather than trusting the owner's intuition.**

### 4a. Distribution across the proposed 5 families
- **(1) New initiative/PRD** — moderately present. Big initiatives start as **freeform prose
  vision docs** (`second-brain/docs/writeup/task_os_writeup.md`) and only later get a PRD-shaped
  refined doc (`linkedout-oss/docs/writeup/2026-04-08-demo-seed-refined-requirements.human.md`).
- **(2) Small pilot feature/POC** — **well represented; the dominant "real work" family.** Agent
  designs (`linkedout-oss/docs/writeup/task_triage_agent.human.md`), subsystem specs, stubs.
- **(3) Bug fix/debug** — present but **usually hybrid.** Pure case:
  `diecast/docs/plan/2026-05-01-fix-trigger-500-malformed-delegation-context.collab.md` (pasted
  stack trace → enumerated root causes → "Recommended fix (minimal, resilient)" with code diffs +
  file:line). More often debug shades into infra or testing. Small bugs likely never get a writeup.
- **(4) Data analysis/research** — present but **narrow and domain-shifted** — shows up almost
  entirely in `second-brain` non-software goals (`market-research-credit-cards-india-scapia/`),
  not in code repos. Shape: `Goal:` / `Desired outcomes:` / `My notes:` + a deep nested
  *question tree*; `goal.yaml` tagged `research`.
- **(5) Random ideas/exploration** — present **mostly as 1-3 line seeds/stubs**
  (`kids-tv-app/requirements.human.md`), which quickly graduate or stall.

### 4b. Documents that DON'T fit — the taxonomy needs more axes (the key finding)
A large fraction (~half) doesn't map cleanly. Missing families/axes that emerged, by frequency:
1. **Evaluation / Testing — the biggest unrepresented cluster.** E2E harnesses, "improve
   testing," red-test-then-fix goals (`child-delegation-integration-tests/`, `cast-ui-testing`,
   `second-brain/.../improve-testing/`). The 5-family list buries this as "add tests," but in this
   corpus it's a first-class, spec-heavy workflow with its own shape. **Strongest evidence for a
   6th first-class family.**
2. **Refactor / Migration / Re-architecture** — "overhaul, no backward compat", "remove
   Procrastinate", "generalize MVCS" (`phase_2_mvcs_tenantbu.collab.md`). Driven by
   **Pre/Post-conditions + Definition of Done**, not user stories. Includes one-time data
   migrations (SQLite→Postgres).
3. **Decision / ADR** — a whole `linkedout-oss/docs/decision/` tree (20+ files):
   Question → Key Findings → Decision → Implications → References. Output is a *choice*, not a feature.
4. **Design / UX spec & design-review findings** — UX interaction-inventory tables
   (`setup-flow-ux.human.md`) and `### FINDING-NNN (severity)` + file:line + **Fix:** reports.
5. **Infra / Platform / setup-reliability** — "make terminal resolution Just Work", evidence-driven
   with empirical verification gates.
6. **Positioning / Narrative / GTM** — POV/office-hours outputs, prose with locked decisions + tone
   discipline.
7. **Personal logistics / life-admin** — trip planning etc. (present because second-brain/TaskOS is
   a life-OS, not just a code repo).

**An orthogonal axis also appears:** *domain* (software / research / life-admin / positioning) is
**separate from** *workflow type*. A research goal and a feature goal can both be "software," and a
research goal can be life-admin. Step 3 should consider modeling these as two dimensions, not one
flat list — this is the contrarian "the axis may be wrong" worry, now evidence-backed.

### 4c. Structural conventions the maintainer naturally reaches for (per family)
- **New initiative (early):** freeform prose, `Goal:` + nested bullets, explicit "grill me / I went
  with my thought flow" disclaimers, References block. No user stories.
- **Feature (refined):** YAML confidence frontmatter (`status: refined`, intent/behavior/constraints
  confidence) → `## Intent` with a bold **Job statement** → `## User Stories` (US1, "As a/I
  want/so that", **Independent test:**, EARS "WHEN…THE SYSTEM SHALL"). *This is the house style for
  mature `.collab.md` specs — and exactly the shape of `refined_requirements.collab.md` for this
  very goal.*
- **Subsystem spec:** YAML frontmatter (feature/module/linked_files/last_verified/version) →
  one-line scope → version history with reversibility notes → `## Intent` → `## Behaviors`.
- **Bug:** pasted log/trace → enumerated root causes → "Recommended fix (minimal, resilient)" with
  code diffs + file:line; often an empirical repro transcript.
- **Research:** `Goal:` / `Desired outcomes:` / `My notes:` + nested question tree.
- **Refactor/Migration:** Goal / Pre-Conditions / **Post-Conditions (Definition of Done)** / "Key
  Findings from Code Review" status table.
- **Decision/ADR:** Date/Status/Deciders → Question → Key Findings → Decision → Implications → References.
- **Design/UX:** Phase/Status/DESIGN GATE header → inventory tables. Review: `### FINDING-NNN` + Fix.
- **Idea stub:** 1-3 lines.

### 4d. Style diversity — correlates with *lifecycle stage*, two registers by suffix
- Terse↔verbose continuum tracks **maturity**, not mood: 2-line stubs → 300-400 line specs, same
  author/project.
- **`.human.md` = the maintainer's own voice** (freeform, bulleted, stream-of-consciousness, open
  questions, "grill me"). **`.collab.md` = the refined/agent-collaborated artifact** (YAML
  frontmatter, EARS, user stories, version history). *Implication: HTML-first rendering should
  honor both registers — the loose human seed and the structured refined doc are different
  consumption modes, not one.*
- Strong **tone discipline** when prose matters (explicit "no em dashes," GPT-ism ban) — confirms
  the AI-slop checker import (§3c) fits the owner's taste.
- **Data-quality note:** in diecast, most `refined_requirements.collab.md` are empty 2-line stubs;
  only 3 are populated. The real diecast signal lives in the `.human.md` raw files — refinement
  hasn't been run on most goals yet. So the corpus over-weights second-brain/linkedout for refined
  shapes; weight that when generalizing for the OSS-product constraint (FR-012).

---

## 5. External prior art — how other tools/communities model spec + comment + version (substep 5)

Six external reference points, each with the pattern and the anti-pattern.

### 5a. PRD vs RFC vs ADR vs Design-doc vs Spike (the work-type vocabulary)
The industry already cuts requirement docs by **work type**, validating Step 3's family axis — but
the cuts differ from the owner's five:
- **RFC** = collect feedback, explore options, async; light-touch design for a non-trivial problem.
- **ADR** = record a *decision* (permanent); an accepted RFC can yield multiple ADRs.
- **PRD** = product manager's "what to build," run beside an eng design doc.
- **Design doc** = longer-form, supplements an ADR.
- **Spike** = time-boxed investigation; its outcome is written up into an ADR.
- **Sizing rule (portable):** *lightweight templates for team-scope changes, heavyweight for
  org-wide* — i.e. **match doc weight to blast radius**, echoing /spec's "match template to content."
- *Anti-pattern:* not every change needs an RFC — forcing heavyweight ceremony on small changes
  "produces noise." (This is the Template-Enforcer risk in industry form.)
→ **For Step 3:** the owner's families (PRD / POC / bug / research / ideas) are a *product-work*
cut; RFC/ADR/spike are an *engineering-decision* cut. The corpus (§4b) shows the maintainer needs
**both** — Decision/ADR was a recurring unfit. Consider ADR-as-a-family or as a downstream artifact.

### 5b. GitHub Spec-Kit — spec-driven development (the closest external analog)
Open-source toolkit; flow **Specify → Plan → Tasks → Implement**, *each phase a Markdown artifact
that feeds the next*. `/specify` focuses on **what/why, not tech detail**; `/plan` adds technical
direction; `/tasks` breaks the plan into a dependency-ordered, parallel-marked task list (each user
story → a separate implementation phase). Agent-agnostic (30 integrations incl. Claude). Workflows
chain commands + human checkpoints with conditional logic, loops, **fan-out/fan-in, pause/resume.**
→ **Validates Diecast's own phase model** (requirements→plan→tasks) and the **keep-markdown-as-the-
interchange-format** decision (FR-007). Spec-Kit deliberately keeps the spec in **plain markdown,
not a DB** — a data point *against* over-investing in a DB-canonical body and *for* a
file-canonical + sidecar approach (§1e). Diecast already has the fan-out/resume orchestration
Spec-Kit added later.

### 5c. Notion / Linear / Jira — doc + comment + version data models
- **Notion = block-based architecture.** Every block is addressable; **inline comments anchor to
  any block**; a comment can become a task. **Page History** = timeline + restore + change
  tracking (who/when) + side-by-side comparison — but **version retention is capped (30–90 days by
  plan).** → the **block = stable-ID-anchored unit** is exactly the model Step 2/Step 4 need; the
  **retention cap is the anti-pattern** (the owner wants archival without data loss, US5).
- **Linear** = streamlined, software-focused; "comments simple but adequate."
- **Jira** = heavyweight full-lifecycle issue tracking.
→ **Takeaway:** the winning model for anchored comments is **content decomposed into addressable
units with stable IDs** (Notion blocks), with comments as **rows keyed to those IDs** and versions
as **snapshots with a diff/compare view**. This is achievable on server-rendered DOM — no SPA
required (confirmed by §5d).

### 5d. W3C Web Annotation Data Model + libraries (kills the "needs React" premise)
- **W3C standard** (since 2017): an Annotation has a **Body** (the comment) and a **Target**; a
  **Selector** pinpoints the target — including by **stable identifier** *or* by surrounding text
  (`TextQuoteSelector`: prefix/exact/suffix). Standardized model + vocabulary + protocol.
- **Libraries:** **Hypothesis** (built on Annotator.js) does web-wide highlight+annotate on
  rendered HTML; **Annotorious** implements a streamlined W3C-compatible model. Both work on
  **server-rendered pages with vanilla JS** — no framework migration.
→ **Pre-loads Step 4's verdict:** if every requirement element carries a stable DOM-anchored ID
(`id="FR-008"`), comments become W3C-style annotations = **plain DB rows {target: element-id, body:
comment, state: open/resolved}** layered onto FastAPI+Jinja with a sprinkle of JS. **The React/Next
question is very likely "no."** The standard even provides the fallback (TextQuoteSelector) for
when an ID is missing — but stable IDs (Step 2) make it robust. *Caveat:* the final
yes/no-on-React decision is Step 4's to make with a UX prototype; Step 1 only supplies the prior art.

### 5e. Jupyter / Observable notebooks — the "research-type work" shape
- **Literate computing / computational narrative:** weave human prose + live code + results into one
  document, *read and re-run by others*. Cells = code + markdown narrative.
- **Observable** = web-based, **reactive** (change one cell, the whole document updates) — a model
  for *living* documents where a change propagates (conceptually relevant to US7 round-trip:
  requirements that update as downstream work changes them).
- **Provenance is a first-class reason notebooks are reused** (track provenance, reproducibility,
  presentation) — directly supports US7's provenance requirement.
→ **For the research/data-analysis family (Step 3) and the living-doc thread (Step 7):** the
notebook model says a research requirements doc should be **question-tree + narrative + (later)
linked results**, and that **provenance/reactivity is the feature that makes a doc "living" rather
than a snapshot.** *Anti-pattern from the notebook literature: notebooks notoriously rot into
un-reproducible, out-of-order messes* — the cautionary tale for "living source of truth": without
disciplined provenance + conflict surfacing (US7 Sc.4), a living doc degrades faster than a static one.

### 5f. EARS / acceptance-criteria notation (already in-house)
The corpus (§4c) and this goal's own `refined_requirements.collab.md` already use **EARS**
("WHEN <trigger> THE SYSTEM SHALL <response>") and **"Independent test:"** lines — matching gstack
`/spec`'s "testable acceptance criteria" discipline. No migration needed; **keep and reinforce.**

---

## 6. Seven-angle synthesis

- **Expert Practitioner.** A senior would *not* greenfield this. Two production patterns
  (DB-canonical render; file-canonical + pointer) already coexist in `cast-server`; gstack `/spec`
  is a battle-tested authoring loop; `cast-preso*` is a working HTML-IA library. The job is
  **assembly + three net-new primitives (stable IDs, versioning, anchored comments)**, not invention.
- **Tools & Technologies.** W3C Web Annotation + Hypothesis/Annotorious + Notion's block model
  collectively say: *stable-ID-anchored DOM + comment rows + version snapshots with a diff view*,
  buildable on FastAPI+Jinja+vanilla JS. Spec-Kit + EARS say *keep markdown as the interchange format.*
- **AI/ML Approaches.** The agent-native wins are gstack's: **read-the-code-before-asking** grounding,
  the **adversarial reviewer subagent**, the **0-10 rate/gap/fix loop**, and **classification routing
  questions + template**. The "same door for humans and agents" (FR-013) is satisfied by making
  comments/versions/routing **plain data+API rows** (W3C annotation style) that a UI and an agent
  both POST to — not a GUI feature with an API bolted on.
- **Community & Open Source.** Industry validates work-type-cut docs (PRD/RFC/ADR/spike) and
  spec-driven markdown pipelines (Spec-Kit), but the cuts differ from the owner's five — and the OSS
  constraint (FR-012) means the taxonomy must generalize beyond a life-OS corpus skewed toward
  second-brain. Don't ship five hardcoded boxes; ship families + a generic fallback + a re-classify path.
- **Frameworks & Patterns.** Reusable scaffolds to lift wholesale: the **WHAT/HOW two-pass**
  (cast-preso), the **named-archetype catalog**, the **L1/L2 typed-field with 50%-cut definition**,
  the **three-dimension checker schema (fix + preserve + AI-slop)**, the **decision-brief
  AskUserQuestion contract**, the **carved-skeleton + sections/ on-demand** structure, the
  **`Supersedes:` revision chain**, and the **in-doc Decisions Log**.
- **Contrarian View.** (1) The keystone may not be "DB vs files" but **"can stable IDs + versioning
  + comments be a DB sidecar on a stable-ID-annotated file?"** — evidence says yes, which favors the
  *lighter* file-canonical Pattern B and keeps FR-007 free. (2) The **5-family taxonomy is
  empirically ~half-right**; Evaluation/Testing is a missing first-class family and *domain* is a
  separate axis from *work-type*. (3) **React is probably unnecessary** (W3C annotation on
  server-rendered DOM). Three of the goal's biggest assumptions are challenged by evidence *before*
  any design spend.
- **First Principles.** Every downstream feature (comments, diffs, change summaries, round-trip
  provenance, cross-references) reduces to **one primitive: a durable element identity that survives
  edits and re-renders.** Diecast has slugs (goals) and ints (tasks) but **no element-level stable
  ID** today. Get that one primitive right (Step 2) and everything else becomes plain rows keyed to
  it; get it wrong and every feature degrades to fragile text-anchor matching. This is why Step 1's
  loudest signal is: *stable element IDs are the keystone, and they do not exist yet.*

---

## 7. What each later step can cite from this brief

| Step | Resolved / supplied by Step 1 | Key citations |
|---|---|---|
| **2 — canonical store + IDs + archive** | Both Diecast patterns named (A vs B) + reusability table; the real question reframed (DB-canonical body vs stable-ID-annotated file + DB sidecar); slug/int ID precedents and their gaps; `synced_at` 2-way precedent to study; W3C/Notion stable-ID models; Spec-Kit "keep markdown" data point | §1, §5b–5d |
| **3 — families + per-family templates** | Empirical taxonomy validation: 5 families ≈ half the corpus; **Evaluation/Testing = candidate 6th family**; Refactor/Migration, Decision/ADR, Design/UX, Infra as recurring unfits; *domain* as a separate axis; external PRD/RFC/ADR/spike cuts; per-family structural conventions the maintainer already uses; /spec "match template to content"; Template-Enforcer anti-pattern in industry form | §4, §5a, §2a |
| **4 — annotation + versioning + change-summary** | W3C Web Annotation + Hypothesis/Annotorious + Notion blocks → **React likely unnecessary**; comment = {target-id, body, state} rows; `Supersedes:` chain; 0-10 review loop; office-hours adversarial reviewer; agent-parity via plain data+API | §5c–5d, §2b–2c |
| **5 — 2-minute HTML render** | cast-preso archetype catalog, L1/L2 typed field + 50%-cut def + triple encoding, assertion-titles "read only the titles" test, progressive disclosure + `callout=none` fallback, token theming, three-dimension checker, Consulting-Exhibit = default requirement block; two registers (.human vs .collab) as two consumption modes | §3 |
| **6 — phase-agnostic router** | office-hours classification→mode→question routing + **mid-flow re-classification** (US6 Sc.4); CLAUDE.md skill-routing table; routing recorded on the entity (parallels goal/task DB records) | §2b, §5a |
| **7 — living source of truth / round-trip** | `synced_at` 2-way precedent in `agents`/`scratchpad` tables; Observable reactive model + notebook **provenance**; in-doc Decisions Log for provenance; notebook-rot cautionary tale → disciplined provenance + conflict surfacing required | §1b, §5e, §2c |

---

## 8. Open questions this brief resolves vs. leaves open

**Resolved / strongly de-risked (with evidence):**
- *gbrain improvements?* → **Yes, substantial.** §2 keep/drop list; top imports are `/spec`'s
  phased gate, the adversarial reviewer subagent, the 0-10 loop, and classification routing.
- *Classification taxonomy validation?* → **Partially refuted.** §4 — five families ≈ half the real
  corpus; Evaluation/Testing is a strong 6th candidate; domain is a separate axis. (Final taxonomy
  is Step 3's to set; Step 1 supplies the data.)
- *Annotation needs React?* → **Almost certainly no.** §5d — W3C Web Annotation on stable-ID DOM via
  vanilla JS. (Final yes/no is Step 4's, ideally with a small prototype.)

**Left open for the owning step (Step 1 supplies inputs, not the decision):**
- *Canonical source of truth (DB-entities-with-renders vs file-canonical-with-DB-sidecar)?* →
  **Step 2.** Step 1 reframes it (§1e) and tilts the evidence toward the lighter sidecar option, but
  the trade-off matrix + migration path is Step 2's deliverable.
- *Archive mechanism (folder vs DB)?* → **Step 2**, resolved jointly with the store.
- *Router placement (inside refine-requirements vs extracted service)?* → **Step 6** (office-hours'
  extracted-and-routed model is the prior art; phase-agnostic invocation implies extraction).

**Flagged for human attention:**
- The corpus is **skewed toward second-brain/linkedout** for *refined* shapes (most diecast
  `refined_requirements.collab.md` are empty stubs). Generalizing the taxonomy for the OSS-product
  constraint (FR-012) should weight this skew — validate families against *external* users, not just
  this three-workspace corpus, before cementing them in Step 3.

---

## Sources

**Code / corpus (this repo + maintainer workspaces, via exploration — `file:line` cited inline):**
- `cast-server/cast_server/services/goal_service.py`, `task_service.py`, `context_map.py`
- `cast-server/cast_server/db/schema.sql`, `routes/api_artifacts.py`, `config.py`
- `docs/specs/cast-init-conventions.collab.md` (suffix convention)
- `~/.claude/skills/cast-preso-visual-toolkit/visual_toolkit.human.md`, `SKILL.md`; `agents/cast-preso-*` (narrative, what-planner, what-worker, how, check-visual/content/tone, illustration-creator)
- `/data/workspace/reference_repos/gstack/{spec,office-hours,plan-ceo-review,plan-eng-review,plan-design-review,plan-devex-review,autoplan,design-consultation,design-html,design-review,document-generate}/SKILL.md`
- Maintainer corpus (22 docs) across `~/workspace/second-brain`, `~/workspace/linkedout-oss`, `~/workspace/diecast` — paths cited inline in §4.

**External (web):**
- [ADRs and RFCs: differences & templates — Candost](https://candost.blog/adrs-rfcs-differences-when-which/)
- [Engineering Planning with RFCs, Design Docs, and ADRs — Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/rfcs-and-design-docs)
- [GitHub Spec-Kit](https://github.com/github/spec-kit) · [Spec-Kit docs](https://github.github.com/spec-kit/) · [Spec-driven development with AI — GitHub Blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [Notion Page History / version control](https://ones.com/blog/notion-page-history-version-control/) · [Linear vs Notion — Nuclino](https://www.nuclino.com/solutions/linear-vs-notion) · [Notion vs Jira — Notion](https://www.notion.com/compare-against/notion-vs-jira)
- [W3C Web Annotation Data Model](https://www.w3.org/TR/annotation-model/) · [Web Annotation overview — Devopedia](https://devopedia.org/web-annotation) · [Annotorious data model](https://annotorious.dev/guides/data-model/)
- [Project Jupyter: Computational Narratives — Jupyter Blog](https://blog.jupyter.org/project-jupyter-computational-narratives-as-the-engine-of-collaborative-data-science-2b5fb94c3c58) · [Ten Simple Rules for Reproducible Research in Jupyter Notebooks (arXiv)](https://arxiv.org/pdf/1810.08055)
