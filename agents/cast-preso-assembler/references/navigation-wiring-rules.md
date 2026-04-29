# Navigation Wiring Rules

Single source of truth for how the assembler wires navigation. Follow these rules exactly — no improvisation, no per-deck deviation.

## 1. Core Flow Rules

- Core slides are always top-level `<section>` elements — **direct children of `.slides`**.
- Core slides are **never** nested inside another `<section>`.
- Order matches the narrative's slide outline table.
- Reveal.js horizontal navigation (arrow right / arrow left) walks core slides.

```html
<div class="slides">
  <section id="opening">...</section>
  <section id="problem">...</section>
  <section id="solution">...</section>
  <section id="evidence">...</section>
  <section id="close">...</section>
  <!-- Appendix stacks come after ALL core slides -->
</div>
```

## 2. Appendix Rules

- Appendix slides are grouped in **vertical stacks**: a parent `<section>` wraps nested `<section>` children.
- **One stack per parent core slide.** If two core slides both have appendix content, create two separate stacks.
- **One topic per stack.** Do not mix unrelated deep-dives.
- All stacks come **after all core slides** in the `.slides` container. Never interleave.
- **Every appendix slide has a back-link** to its parent core slide:

  ```html
  <a href="#/{parent_core_slide_id}" class="back-link">< Back to {Parent Title}</a>
  ```

Example for `02-problem` with two appendix entries:

```html
<section>
  <section id="problem-detail">
    <!-- Deep-dive content -->
    <a href="#/problem" class="back-link">< Back to Problem</a>
  </section>
  <section id="problem-data">
    <!-- Data deep-dive -->
    <a href="#/problem" class="back-link">< Back to Problem</a>
  </section>
</section>
```

## 3. Deep-Dive Link Rules

- Core slides with appendix content get a `<a class="deep-dive-link">` pointing at the first appendix entry slide.
- **Idempotent:** Check if `deep-dive-link` already exists in the source HTML before injecting — do not duplicate.
- Format:

  ```html
  <a href="#/{appendix_entry_id}" class="deep-dive-link">Deep-dive: {topic} ></a>
  ```

- **Verify target existence.** The `id` referenced must exist in the appendix output.
- Never use numeric index references. Always use `#/{id}`.

## 4. A/B Version Rules

When a slide has `versions/` alternatives:

- Wrap primary and versions in a vertical stack so versions appear **below** (not adjacent horizontal).
- Primary slide gets a `version-available-marker`:

  ```html
  <div class="version-available-marker">Version B available below &#8595;</div>
  ```

- Each version slide gets a `version-marker` and `data-state="version-slide"`:

  ```html
  <section id="{slide_id}-version-b" data-state="version-slide">
    <div class="version-marker">VERSION B — {slide_id}</div>
    <!-- version-b content -->
  </section>
  ```

- A/B stacks are **separate from appendix stacks** — they are attached to the primary slide's own stack, not the appendix.
- SJ removes rejected versions manually after review; the assembler does not auto-select.

## 5. Prohibited Patterns

- **No numeric index references** (`#/3/2`, `navigate(3)`). Always use `#/{id}`.
- **No `navigate()` JS calls** from slide content.
- **No external URLs** in `<script src>` or `<link href>` (must be bundled).
- **No duplicate IDs** anywhere in the assembled deck.
- **No absolute file paths** (`/Users/...`, `file://...`) — all relative.
- **No core slide nesting** — if a core slide is inside another `<section>`, it's a bug.
- **No orphaned appendix stacks** — every stack's back-links must resolve to a core slide.

## 6. Precedence

If a slide's source HTML already contains correct navigation markup, **preserve it**. Do not double-wrap, do not replace. The assembler is additive: inject only what is missing.
