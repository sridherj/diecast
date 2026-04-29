# Test Cases: taskos-preso-check-visual

Six test cases covering the 9 base criteria and the 3 image-specific criteria (Chrome MCP path).

## Test 1: Clean Pass

**Mock Input:**
- `how/test-01/slide.html`: timeline archetype (4 milestones, current one highlighted, future ones muted)
- Uses toolkit tokens: bg `#FAFAF7`, text `#1A1A28`, accent `#FF6B35`, IBM Plex Mono heading, IBM Plex Sans body
- 4 distinct elements, ~40% whitespace, min font 22px
- No images referenced (skip criteria 10-12)
- `brief.collab.md`: names the archetype as "timeline"

**Expected Output:**
- `verdict`: PASS
- All 9 base criteria pass
- `score`: > 0.90

---

## Test 2: Default Layout (Generic AI Pattern)

**Mock Input:**
- `how/test-02/slide.html`: title top-left, 3 bullet points middle, stock-style illustration right-aligned
- Uses correct toolkit tokens (colors and fonts are on-brand)
- No archetype identified in brief

**Expected Output:**
- `verdict`: FAIL
- Primary issues:
  - `not-generic` (error) — "Layout is the default 'title + bullets + image-right' pattern. No archetype chosen. Brief does not name a visual approach."
  - `not-ai-aesthetic` (error) — "Pattern matches AI-generated slide template: bullet list with decorative right-aligned image."
- `what_worked`: "Tokens are on-brand. Whitespace is adequate."

Score range: < 0.70.

---

## Test 3: Cramped

**Mock Input:**
- `how/test-03/slide.html`: 8 distinct elements, dense packing, ~20% whitespace
- Footnotes at 12px, body at 14px

**Expected Output:**
- `verdict`: FAIL
- Issues:
  - `max-6-elements` (error) — "Element count: 8 (limit: 6). Consolidate or split across slides."
  - `min-30pct-whitespace` (error) — "Estimated whitespace: 20% (min: 30%). Slide feels cramped."
  - `min-18pt-font` (error) — "Footnotes at 12px; body at 14px. Minimum: 18px."

Score range: < 0.55.

---

## Test 4: Off-Brand Colors

**Mock Input:**
- `how/test-04/slide.html`: uses `#333` for text instead of toolkit's `#1A1A28`; uses a cyan accent (`#00AEEF`) instead of toolkit's warm orange (`#FF6B35`)
- Otherwise clean archetype, good hierarchy, good whitespace

**Expected Output:**
- `verdict`: FAIL
- Primary issue: `toolkit-consistent` (error) — "Text color `#333` differs from toolkit `#1A1A28`. Accent `#00AEEF` (cyan) differs from toolkit `#FF6B35` (warm orange). Using off-brand tokens."
- `what_good_looks_like`: "Replace text with toolkit text color; replace accent with toolkit warm accent."
- `what_worked`: "Layout is specific, hierarchy is clear."

Score range: 0.80-0.90.

---

## Test 5: Decorative Illustration

**Mock Input:**
- `how/test-05/slide.html`: clean compare/contrast archetype for two product options
- Large decorative watercolor of a mountain in the background — beautiful, but doesn't reinforce the comparison

**Expected Output:**
- `verdict`: PASS (warnings only)
- Warning: `illustrations-functional` — "Watercolor background does not reinforce the compare/contrast message. Could be removed without losing meaning. Consider removing or replacing with comparison-relevant visual."

Score range: 0.90-0.95.

---

## Test 6: Image-Heavy Slide (Chrome MCP Path)

**Mock Input:**
- `how/test-06/slide.html`: hero layout with 2 illustrations (one main, one inset)
- References 2 assets in `assets/`

**Expected Behavior:**
- Rendering decision: 2 images → run Chrome MCP screenshot
- Criteria 10-12 get run after the screenshot:
  - `image-integration` — does the illustration integrate or float disconnected?
  - `image-sizing` — is the main illustration sized appropriately for the hero position?
  - `image-quality` — is the illustration sharp with no compression or uncanny-valley artifacts?

**Expected Output:**
- `verdict`: PASS or FAIL depending on fixture
- `checks_performed` includes all 12 criteria (9 base + 3 image-specific)
- If Chrome MCP unavailable: criteria 10-12 skipped; warning added: "Image integration not verified — Chrome MCP unavailable. Manual review recommended." (slide not auto-failed)

---

## Notes

- All 9 base criteria run for every slide
- Criteria 10-12 only run when 1+ images are referenced AND Chrome MCP is available
- If Chrome MCP fails, add warning but do NOT fail solely on that
- `checks_performed` list must reflect what actually ran (not the full 12 if images absent)
