# Assembler Pre-Flight Checklist

Run this checklist after assembly, before declaring complete.
This checks STRUCTURAL correctness. Functional/semantic checks happen in compliance.

- [ ] All core slides are horizontal `<section>` elements (not nested)
- [ ] All appendix slides are in vertical stacks after the core flow
- [ ] Every core slide has a unique `id`
- [ ] Every appendix entry slide has a unique `id`
- [ ] Deep-dive links use `href="#/{id}"` (not numeric indices)
- [ ] Every appendix slide has a back-link to its parent core slide
- [ ] `CALLOUT_ANIMATIONS` toggle matches consumption mode
- [ ] No `<script src>` or `<link href>` pointing to CDN URLs
- [ ] All images are either inline SVG, base64 data URIs, or bundled by Vite
- [ ] Speaker notes exist on every content slide (title/close may skip)
- [ ] Total file size is under 10 MB
- [ ] A/B version slides have visual markers (both primary and version)
- [ ] Asset paths are all relative (no absolute, no file://, no CDN)
- [ ] No duplicate `id` attributes across all slides

## How to run

After completing Workflow Step 7 (Notes and Questions Aggregation), walk this checklist against the generated `src/index.html` and the built `dist/index.html`. For each item:

- **Pass:** mark in your report and move on.
- **Fail:** either auto-fix if the rule in `navigation-wiring-rules.md` lets you, OR fail with a clear message pointing to the offending slide/section. Never silently ship a deck that fails structural checks.

## Relationship to Compliance

- Assembler pre-flight = **structural** (IDs, nesting, path relativity).
- Compliance Pass 6 = **functional** (link target makes topical sense, flow supports arc).
- No overlap. If a check here passes but compliance fails it later, update the rules — don't duplicate the check.
