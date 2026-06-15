# Code Exploration — Step 5: HTML-First Human-Consumption Render

**Goal context:** Refine Requirements v2 — make an unfamiliar reader state a goal's WHAT (job/outcome/scope) in ~2 minutes (SC-001) from an HTML render that replaces markdown for humans (SC-003), while still emitting spec-kit markdown for downstream agents (FR-007).
**Codebase:** `/home/sridherj/workspace/diecast` (→ `/data/workspace/diecast`); render kit in `skills/claude-code/cast-preso-visual-toolkit/`.
**Date:** 2026-06-11
**Method:** GO-BROAD. Maps where the *render* terrain is today so the synthesizer understands the starting point and migration cost — does **not** constrain the recommendation to current code. Step 1 §C already mined cast-preso at a summary level; this brief goes deeper on the *actual render pipeline, templates, CSS, and serving model* and assigns concrete migration costs.

> **Headline up front:** The current "render" is **structure-blind markdown→HTML** — `md.markdown(text, extensions=[fenced_code, tables, toc, codehilite])` dumped into a `.markdown-body` div. It styles markdown; it does **not** do information architecture. There is **no L1/L2/L3 semantic mapping, no element IDs for US/FR/SC, no classification pill, no WHAT/HOW separation, and no per-family variation** in the render path. **But** the visual *foundation* is already 90% there and shared with cast-preso: identical design tokens, identical fonts, native `<details>` progressive disclosure, an existing pill/badge component family, and — critically — a **working precedent for serving a pre-generated standalone HTML artifact** (`/preso/review/{goal_slug}`). The real new work is a **spec-kit-aware structured renderer**, not a CSS project.

---

## 1. Data Model & Schema

The render consumes **files, not entities** — confirmed and unchanged from Step 1/2.

- **Source of the render today:** the markdown artifact on disk (`requirements.human.md`, `refined_requirements.collab.md`), read at request time and converted to HTML inline. The DB is blind to artifact *content* — `goals`(slug PK) and `tasks`(int PK) in `cast-server/cast_server/db/schema.sql` carry no artifact rows, no element rows, no render cache.
- **No element identity in the data model.** US/FR/SC elements exist only as text inside the markdown. The spec-kit markdown *does* use textual IDs (`US1`, `FR-007`, `SC-001`) — see `refined_requirements.collab.md` — but nothing in the schema or render path treats them as anchors. The `markdown` lib's `toc` extension auto-slugs *headings* (`<h2 id="functional-requirements">`), which is a partial, heading-level ID seed — **not** element-level (`id="fr-007"`).
- **What a structured render needs but the data model lacks:** an element→level mapping (which content is L1 vs L2 vs L3), a family classification field on the goal, and per-element stable IDs. Step 2's recommendation (hybrid: files canonical + thin `artifact_versions`/`artifact_comments` DB layer keyed to `id="req-NNN"`) is the substrate this render would emit IDs *into*. **Step 5's render is the producer of those stable IDs** (assign `id` at generation time) — every downstream consumer (comments, diffs, round-trip) depends on the render doing this.

**Implication:** the render is the *origin point* of element identity. If Step 5 emits `<section id="fr-007" data-level="1" data-kind="FR">`, Steps 2/4/7 inherit anchors for free. If it emits generic `md.markdown()` output, every later feature is back to fragile text-anchoring.

---

## 2. Existing Implementation — the render pipeline as it actually exists

### 2a. The one and only markdown→HTML path

Two copies of the same converter (duplication noted as a gap):

| Location | Call | Used by |
|---|---|---|
| `routes/api_artifacts.py:14,132` | `md.markdown(content, extensions=MD_EXTENSIONS, extension_configs=...)` | artifact sidebar (`/api/artifacts/artifact-sidebar`) |
| `routes/api_goals.py:271,276–281` | `render_md()` (same extensions, `try/except`→`<pre>` fallback) | phase tab content (`/api/goals/{slug}/tab/{phase}`) |

`MD_EXTENSIONS = ["fenced_code", "tables", "toc", "codehilite"]`. That is the *entire* render intelligence. There is no spec-kit awareness, no section reordering, no level assignment, no pill injection. Output is wrapped verbatim:

```jinja
{# macros/markdown_viewer.html #}
{% macro artifact_content(html) %}
<div class="artifact-content markdown-body">{{ html | safe }}</div>
{% endmacro %}
```

### 2b. Where the render surfaces in the UI

```
goal_detail page (pages.py:77 goal_detail)
  └─ phase tabs (Jinja) → HTMX GET /api/goals/{slug}/tab/{phase}  (api_goals.py:263)
        └─ render_md(file.read_text()) per artifact
        └─ fragments/phase_tab_content.html
              └─ <details class="artifact-section" {open if loop.first}>   ← progressive disclosure (per-FILE)
                    <summary>{{ artifact_header(...) }}</summary>
                    {{ artifact_content(html) }}
```

- **Artifacts render as collapsible `<details>` blocks**, first one `open`. So *progressive disclosure already exists* — but at **file granularity** (whole `refined_requirements.collab.md` collapses as one unit), not **section granularity** (summary visible, rationale/edge-cases collapsed). FR-006's "summary first, details expandable" needs intra-document disclosure the current path doesn't do.
- **Artifact list is auto-discovered** from `PHASE_ARTIFACTS` (`config.py:53–58`) by globbing the goal folder (`api_goals.py:327–354`); labels derived from filename (`f.stem.replace("-"," ").title()`). Adding an HTML artifact means either registering it here or serving it via a dedicated route (see 2c).

### 2c. **The standalone-HTML serving precedent (most important existing implementation for Step 5)**

`routes/pages.py:299–307`:

```python
@router.get("/preso/review/{goal_slug}")
def preso_review(goal_slug: str):
    path = Path(_config.GOALS_DIR) / goal_slug / "presentation" / "review.html"
    if not path.exists():
        return HTMLResponse("<p>No presentation review...</p>", status_code=404)
    return HTMLResponse(path.read_text(encoding="utf-8"))
```

This is **exactly the serving model a generated requirements HTML render wants**: an agent generates a self-contained `.html` file into the goal folder; a thin route serves it raw. The cast-preso pipeline already *produces* such single-file HTML (the assembler inlines `theme.css` into one file). So the end-to-end "agent generates standalone HTML → server serves it" loop **already works in this repo for presentations** — Step 5 generalizes it to requirements. Migration cost: **LOW** (copy the route shape, point at `refined_requirements.html`).

### 2d. The editing model (constrains the annotation story, not the render)

- `fragments/artifact_editor.html` + EasyMDE (`base.html:153–168`, `static/vendor/easymde/`) = a **markdown-source** editor. Save writes the file directly (`api_artifacts.py:81–107`), no DB. Only `.human.md`/`.collab.md` are editable (`validate_artifact_path`).
- **Consequence for Step 5:** the human edits *markdown source*, then the HTML is *re-generated*. The HTML render is a **read (consumption) artifact**, like preso review — not an editable surface. This cleanly separates Step 5 (read render) from Step 4 (annotation overlay on the read render). The render does not need to be round-trippable to markdown; markdown stays the edit source (and the agent contract, FR-007).

---

## 3. Gap Analysis (what's missing for SC-001 / FR-001–006), prioritized

| # | Gap | Severity | Evidence |
|---|---|---|---|
| 1 | **No semantic structure in render** — `md.markdown()` is structure-blind; cannot lead with WHAT, cannot rank by level, cannot vary by family | **CRITICAL** | `api_goals.py:276`, `api_artifacts.py:132` — generic converter only |
| 2 | **No L1/L2/L3 mapping** — `.markdown-body` styles by HTML tag (h1/h2/p/li), not by requirement *importance*. h1≠L1 conceptually | **CRITICAL** | `style.css:2526–2604` styles tags, not levels; cast-preso `.l1-body/.l2-body/.source-citation` classes exist in the kit but are **absent from `style.css`** |
| 3 | **No element-level stable IDs** — only `toc` heading slugs; US/FR/SC get no `id` | **CRITICAL** (keystone per Step 2) | `MD_EXTENSIONS` has `toc` (headings only); no per-element id injection |
| 4 | **No classification pill** (FR-002) | **HIGH** | render has no goal-family field; no pill in `markdown_viewer.html`. (Pill *styling* is trivial — see §4.) |
| 5 | **No WHAT/HOW separation** (FR-001, US1) — "Directional ideas" section renders as plain markdown indistinguishable from binding requirements | **HIGH** | `refined_requirements.collab.md` has a `## Directional Ideas` heading but it renders identically to `## Functional Requirements` |
| 6 | **No intra-document progressive disclosure** (FR-006) — disclosure is per-file, not per-section | **HIGH** | `phase_tab_content.html:65` `<details>` wraps whole artifact |
| 7 | **No per-family structural variation** (FR-005, US3 S3) — one render shape for all goals | **HIGH** | single `render_md()` path; no family branch |
| 8 | **No illustration/diagram support** | MEDIUM | no SVG pipeline in render; cast-preso has the rules (`diagram-annotated.html`) but unused here |
| 9 | **Duplicated converter** (two copies of `MD_EXTENSIONS`/`render_md`) | MEDIUM | `api_artifacts.py` vs `api_goals.py` — refactor target before adding a 3rd render mode |
| 10 | **HTML read-path is blocked** — `validate_artifact_path_read` rejects non-`.md` (`api_artifacts.py:55`); the sidebar can't display a `.html` artifact | MEDIUM | must serve HTML via a `/preso`-style route, not the artifact sidebar |
| 11 | **No timed-read validation harness** (SC-001) | LOW | none exists; cast-preso's 8-pass compliance checker is the portable template |

**The gap is overwhelmingly *information architecture*, not styling.** Items 1–3,5,7 are "the converter doesn't understand requirements." Items 4,6,8 are render features. Only the *visual primitives* (tokens, fonts, disclosure, pills) are already solved (§4).

---

## 4. Patterns & Conventions — what the render kit and the app already share

### 4a. **The design-token system is already identical to cast-preso** (the single biggest cost-saver)

`cast-server/cast_server/static/style.css:2–48` `:root` is **byte-for-byte the same palette/fonts** as `skills/claude-code/cast-preso-visual-toolkit/base-template/theme.css:12–31`:

| Token | Both files |
|---|---|
| `--color-bg` | `#F5F4F0` |
| `--color-text` | `#1A1A28` |
| `--color-muted` | `#4A4860` |
| `--color-surface` | `#ECEAE4` |
| `--color-accent` | `#D6235C` |
| `--color-callout-bg` / `--color-question-bg` | `rgba(214,35,92,.06)` / `rgba(74,72,96,.06)` |
| `--font-heading` | `'IBM Plex Mono', …` |
| `--font-body` | `'DM Sans', …` |

Fonts are already loaded app-wide (`base.html:12`, Google Fonts: IBM Plex Mono + DM Sans + Caveat). **→ Adopting cast-preso render classes carries ZERO token/font migration.** The "lift the `:root` block" advice from Step 1 §C is already done — they converged independently.

### 4b. What cast-preso has that `style.css` does NOT yet have (the lift list)

These classes live in the kit (`base-template/theme.css:100–192`, `templates/css/components.css`) but are **not** in `style.css`'s markdown-body. They are the L1/L2/L3 + semantic-annotation vocabulary Step 5 needs:

- `.slide-title` (mono, 1.6em, 700) → requirement **section assertion heading**
- `.l1-body` (sans, 1.1em, 600, text) → **primary requirement** (survives a 50% cut)
- `.l2-body` (sans, 0.9em, 400, muted) → **supporting constraint/rationale** (first to cut)
- `.source-citation` (0.5em, muted) → **acceptance criteria / provenance / element ID**
- `.callout` (numbered, accent left-border) → "**this is decided**" (a stated requirement)
- `.question-annotation` (muted italic, "?" icon) → "**this is open / a risk**" (an Open Question / NEEDS CLARIFICATION) — maps *perfectly* onto the spec's `[NEEDS CLARIFICATION]` markers and `## Open Questions`.

Rule enforced by cast-preso's content checker: **L2 must never visually out-weigh L1** (`l1-l2-hierarchy` criterion).

### 4c. **Pill/badge components already exist** (the classification pill is a restyle, not a build)

`style.css` already ships a pill/badge family with the same idiom FR-002 wants:
- `.status-badge[data-status="…"]` (`style.css:395–411`)
- `.phase-badge[data-phase="…"]` (`:1979–1992`) — tinted-bg + colored-text per category
- `.authorship-badge` (`:2024`), `.run-status-pill` (`:2156`), `.badge-phase/-effort/-spike/-agent/-type` (`:1440–1460`)

The classification pill ("You are building a new feature for XYZ") is `<span class="classification-pill" data-family="feature">` reusing this exact `[data-*]`→tint pattern. **Migration: LOW.**

### 4d. Progressive disclosure convention is native `<details>/<summary>`

Used in `phase_tab_content.html:65` (`.artifact-section`) and elsewhere (`.expandable summary`, `style.css:961,1822`). cast-preso independently confirms `<details>` as the disclosure mechanism. **→ Intra-document disclosure (FR-006) uses the same primitive the app already styles — extend it from per-file to per-section.** Works with zero JS.

### 4e. Authoring disciplines portable from cast-preso (zero-cost rules, not code)

From `visual_toolkit.human.md §5` + archetypes: **assertion-format headings** ("Users authenticate via SSO" not "Authentication") — *the* highest-leverage rule for 2-minute comprehension; **write L1 first, fill L2 second** (hierarchy is a planning pass); hard density limits (≤50 words/block, ≤15/bullet, ≤6 elements/unit, ≥30% whitespace) → make these **render-time warnings**. The **consulting-exhibit archetype** (`templates/slide-archetypes/consulting-exhibit.html`: action-title → subtitle → bold-lead bullets → source line) is the **ideal shape of a single requirement block**.

### 4f. App architecture conventions the render must fit

Flat MVCS: thin FastAPI routers → fat service fns (inline SQLite + file I/O) → Jinja2 templates + HTMX (server-rendered, no JS framework). `.human/.collab/.ai` authorship suffix convention (`utils/file_utils.py`). Generated files carry an `AUTO-GENERATED` header. A generated `refined_requirements.html` fits as either a new `.ai`/`.collab` HTML render or a `/preso`-style served file.

---

## 5. Entry Points & Flow

### Current flow (what exists)
```
USER opens goal → /goals/{slug} (pages.py:77)
  → clicks phase tab → HTMX GET /api/goals/{slug}/tab/requirements (api_goals.py:263)
     → glob PHASE_ARTIFACTS["requirements"] = [requirements.human.md, refined_requirements.collab.md]
     → for each: render_md(read_text())   ← GENERIC markdown→html, no structure
     → phase_tab_content.html → <details>{markdown-body}</details>   ← per-file disclosure
PRESENTATION (the template to imitate):
  agent generates goals/{slug}/presentation/review.html (self-contained)
  → GET /preso/review/{slug} (pages.py:299) → HTMLResponse(raw file)
```

### Proposed v2 render flow (where Step 5 lands — terrain-mapping, not a constraint)
```
refine-requirements agent
  ├─ emits refined_requirements.collab.md   (spec-kit markdown — FR-007, UNCHANGED, agent contract)
  └─ emits refined_requirements.html        (structured, family-shaped, L1/L2/L3, id="fr-007" anchors)
        ↑ NEW: a spec-kit-AWARE renderer (parse US/FR/SC → level-mapped semantic HTML),
          NOT md.markdown(); consumes Step-3 per-family template; injects classification pill;
          confines HOW to a .directional section; wraps detail in <details>.
SERVE: GET /goals/{slug}/render  (clone of /preso/review)  → HTMLResponse(refined_requirements.html)
        or register .html in PHASE_ARTIFACTS + relax validate_artifact_path_read for .html
ANNOTATE (Step 4, separate): vanilla-JS annotator binds to id="fr-007" anchors on this HTML
```
**The fork is the renderer box:** generic `md.markdown()` (today) vs. a **structured spec-kit→HTML transformer** (v2). That transformer is the substantive new build; everything around it (serving, tokens, disclosure, pills) is reuse.

---

## 6. Tests & Coverage

- **No render tests exist** for structure/levels/pill/family (features don't exist). `cast-server/conftest.py` + `tests/ui/` (UI harness) + `tests/integration/` + `tests/e2e/` are the homes for new coverage.
- **The regression surface to protect is FR-007/SC-004:** downstream agents (planner, task-suggester, spec-checker) consume the *markdown* render unchanged. Step 5 must add the HTML render *alongside* markdown without altering the `.collab.md` bytes those agents read. **Define a golden-file/byte-compat check** on `refined_requirements.collab.md` so adding HTML generation can't regress the markdown contract.
- **SC-001 (2-minute comprehension) is a human-timed test**, not automatable — but cast-preso ships a portable proxy: three 0–1.0 checkers (content/visual/tone) + an **8-pass compliance checker** (`agents/cast-preso-check-{content,visual,tone}.md`, `cast-preso-compliance-checker.md`). Directly reusable criteria: `achieves-stated-outcome`, `one-clear-takeaway` (<5s scan), `l1-l2-hierarchy`, `not-generic`, `not-ai-aesthetic`. Wire these as a render-quality gate.
- **Snapshot the HTML** per family (one golden render per family) to catch structural regressions as templates evolve.

---

## 7. Config & Dependencies

- **Already present, sufficient for the render:** `jinja2>=3.1`, `markdown>=3.5` (3.10.2 installed), HTMX (`static/htmx.min.js`), Google Fonts (IBM Plex Mono / DM Sans / Caveat). **No new dependency is required to build the structured render** — Jinja2 templates + a spec-kit parser (stdlib `re` or the existing `markdown` lib's AST/`toc`) suffice.
- **`PHASE_ARTIFACTS` registry** (`config.py:53–58`) is the discovery hook; `ARTIFACT_DEFAULTS` (`:64–73`) maps authorship. Adding `refined_requirements.html` touches these.
- **`validate_artifact_path_read` (`api_artifacts.py:52–57`) hard-rejects non-`.md`** — the one config-level blocker to serving HTML through the artifact sidebar. Either relax it for `.html` (read-only) or bypass it with a `/preso`-style dedicated route (lower-risk; recommended).
- **Annotation libs (Step 4):** none vendored yet; a vanilla-JS annotator (Hypothesis/@duckyb/recogito) would be additive (`static/vendor/`), **no framework migration** — consistent with Step 1/4 findings. Out of Step 5's scope but the render must emit the `id` anchors they bind to.
- **EasyMDE** (`static/vendor/easymde/`) stays the *markdown-source* editor; unrelated to the read render.

---

## Key Takeaways (opinionated, cross-cutting)

1. **The hard problem is a structured renderer, not CSS.** Today's render is `md.markdown(extensions=[fenced_code,tables,toc,codehilite])` — it converts markdown but understands nothing about requirements. SC-001 ("WHAT in 2 minutes") cannot be hit by styling generic markdown; it needs a transformer that knows US/FR/SC, assigns L1/L2/L3, leads with WHAT, confines HOW, injects the pill, and varies by family. **Budget the build here; everything else is reuse.**

2. **The visual foundation is already paid for — tokens and fonts are literally identical to cast-preso.** `style.css:2–48` ≡ `theme.css:12–31`. Adopting cast-preso's `.l1-body/.l2-body/.source-citation/.callout/.question-annotation` classes is a copy-in with zero token/font conflict. Step 1 §C's "lift the `:root`" recommendation is *already true*; the only missing pieces are the level/annotation classes, which append cleanly.

3. **A standalone-HTML serving precedent already ships: `/preso/review/{goal_slug}`.** The "agent generates a self-contained `.html` into the goal folder → thin route serves it raw" loop works *today* for presentations. Generalizing it to `refined_requirements.html` is **LOW** cost and side-steps the `.md`-only artifact-read validation. Recommend this over retrofitting the artifact sidebar.

4. **The render is the *origin* of stable element IDs — the keystone every later step consumes.** If Step 5 emits `<section id="fr-007" data-kind="FR" data-level="1">` at generation time, Step 2's comment/version DB layer, Step 4's diffs, and Step 7's round-trip provenance all inherit durable anchors. The spec-kit markdown already uses `US1/FR-007/SC-001` textually — the render just has to *promote them to DOM ids*. This is the single most leveraged decision in Step 5.

5. **Three render features are cheap because the primitives exist:** the classification pill reuses the `[data-*]`→tint badge pattern (`.phase-badge` et al.); progressive disclosure reuses native `<details>` (already styled, already used per-file — extend to per-section); the WHAT/HOW split reuses `.callout` (decided) vs `.question-annotation` (open/directional). The `## Directional Ideas` and `[NEEDS CLARIFICATION]` markers in the existing spec map 1:1 onto these.

6. **Per-family variation (FR-005) forces the renderer to be template-driven, not hardcoded — and it must consume Step 3's templates.** The corpus (Step 1 §D) shows real structure varies by family (bug = symptom/repro structured; ideation = loose narrative; research = question→findings). The renderer should be a thin engine that selects a family template (and a generic fallback) — not five copied functions. This is also where the "stub = render-state, not family" rule lives: a 2-line input renders a **prompt-to-begin**, not an empty template.

7. **Markdown stays the edit-and-agent source; HTML is a generated read artifact.** EasyMDE edits markdown; downstream agents read markdown (FR-007). The HTML render is *derived and read-only* (like preso review), which keeps Step 5 decoupled from Step 4 (annotation overlay) and Step 2 (storage). Protect the markdown bytes with a golden-file regression check so HTML generation can never break SC-004.

---

## Key Files (read these to ground Step 5)

- `cast-server/cast_server/routes/api_goals.py:263–354` — phase-tab render flow + the generic `render_md()` that must be replaced/supplemented for requirements.
- `cast-server/cast_server/routes/api_artifacts.py:14,52–57,132` — the *other* `md.markdown()` copy; the `.md`-only read validation that blocks serving HTML through the sidebar.
- `cast-server/cast_server/routes/pages.py:299–307` — `/preso/review/{goal_slug}`: the standalone-HTML serving precedent to clone for the requirements render.
- `cast-server/cast_server/templates/macros/markdown_viewer.html` — `artifact_content`/`artifact_header` macros; where the `.markdown-body` wrapper lives.
- `cast-server/cast_server/templates/fragments/phase_tab_content.html:62–73` — `<details class="artifact-section">` per-file disclosure (extend to per-section).
- `cast-server/cast_server/static/style.css:2–48` — the `:root` token block (≡ cast-preso); `:395–411,1979–1992,2024,2156` pill/badge family; `:2466–2604` `.artifact-section`/`.markdown-body` styles to augment with L1/L2/L3.
- `cast-server/cast_server/templates/base.html:8–13,153–168` — CSS/font loading + EasyMDE init (markdown-source editor).
- `cast-server/cast_server/config.py:52–73` — `PHASE_ARTIFACTS` discovery hook + `ARTIFACT_DEFAULTS` authorship; where `refined_requirements.html` registers.
- `skills/claude-code/cast-preso-visual-toolkit/base-template/theme.css:100–192` — `.slide-title/.l1-body/.l2-body/.source-citation/.callout/.question-annotation` — the level + annotation classes to lift.
- `skills/claude-code/cast-preso-visual-toolkit/templates/slide-archetypes/consulting-exhibit.html` — the ideal single-requirement-block shape (assertion title → bold-lead bullets → source line); also `compare-contrast.html` (scope/in-vs-out), `build-up-sequence.html` (ordered/dependency reqs).
- `skills/claude-code/cast-preso-visual-toolkit/visual_toolkit.human.md §5` — density limits + assertion-heading rule (render-time constraints).
- `goals/refine-requirements-v2/exploration/research/01-learn-from-existing-systems-code.ai.md §C` — Step 1's cast-preso inventory this brief builds on.

---

## Migration-Cost Summary (for the synthesizer)

| Capability | Cost | Why |
|---|---|---|
| Adopt cast-preso tokens/fonts | **~0** | already identical in `style.css` |
| Lift L1/L2/L3 + callout/question classes | **LOW** | append to `style.css`, no token conflict |
| Classification pill | **LOW** | restyle of existing `[data-*]` badge pattern |
| Intra-doc progressive disclosure | **LOW** | native `<details>` already styled/used |
| Serve a standalone HTML render | **LOW** | clone `/preso/review/{goal_slug}` |
| WHAT/HOW visual separation | **LOW–MED** | uses callout vs question-annotation; needs renderer to segment sections |
| **Structured spec-kit→HTML renderer w/ element IDs** | **MEDIUM** (the real build) | replaces structure-blind `md.markdown()`; must parse US/FR/SC, map levels, emit `id="fr-007"` |
| Per-family template selection | **MEDIUM** | depends on Step 3 templates; engine + fallback + stub-state |
| Illustration/SVG support | **MEDIUM** | greenfield; cast-preso rules exist but unused here |
| Render-quality gate (SC-001 proxy) | **MEDIUM** | port cast-preso 3-checker + 8-pass compliance rubric |

**Net:** no framework migration, no new runtime dependency, no data-model rewrite required for the render itself. The investment concentrates in **one structured renderer** that turns the existing spec-kit markdown into level-mapped, id-anchored, family-shaped HTML — sitting beside (never replacing) the markdown that downstream agents still consume.
