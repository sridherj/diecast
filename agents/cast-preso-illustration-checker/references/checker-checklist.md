# Illustration Checker Checklist (Authoritative Source)

> This file is the runtime source of truth for all checker passes.
> The agent brain's inline checklists are summaries — this file governs.

## Pass 1 — Reject Gate (< 10 seconds)

Binary checks. Catches ~60% of problems.

| # | Check | Pass/Fail Criteria | Failure Action |
|---|-------|--------------------|----------------|
| 1.1 | Correct subject | Image depicts the requested subject | FAIL → RESTART |
| 1.2 | Major elements present | All elements named in scene brief are visible | FAIL → CONTINUE |
| 1.3 | No garbled text | If any text is visible (shouldn't be), it's legible | FAIL → CONTINUE |
| 1.4 | No catastrophic anatomy | No extra limbs, impossible joints, face-melting | FAIL → CONTINUE |
| 1.5 | Correct aspect ratio | 16:9 for backgrounds, as-specified for inline | FAIL → CONTINUE |
| 1.6 | Minimum resolution | 1920x1080 for full-bleed, 800px+ for inline | FAIL → CONTINUE |

**Exit logic:** 1.1 fails → RESTART. Any other fails → CONTINUE with feedback. All pass → Pass 2.

## Pass 2 — Accuracy Audit (structured, 30-60 seconds)

Element-by-element comparison. Only reached if Pass 1 succeeds.

| # | Check | What to Compare |
|---|-------|-----------------|
| 2.1 | Element count | Expected N (from brief) vs observed (from blind description) |
| 2.2 | Spatial relationships | Positions described in brief vs actual layout |
| 2.3 | Labels/text accuracy | SVG only: every label matches spec letter-by-letter |
| 2.4 | Data accuracy | Numbers, percentages, data points match source material |
| 2.5 | All components identifiable | Every requested component is recognizable |
| 2.6 | Scale/proportion | Elements sized correctly relative to each other |

**Exit logic:** Critical item fails → CONTINUE. Same items fail after 2 iterations → ESCALATE. All pass → Pass 3.

**Counting note:** Multimodal LLMs cannot reliably count above ~5 objects. Flag uncertainty for > 5 elements.

## Pass 3 — Style & Polish (subjective, only if Passes 1-2 succeed)

| # | Check | Criteria |
|---|-------|----------|
| 3.1 | Style match | Matches Style Bible aesthetic |
| 3.2 | Deck consistency | Compare to style anchor (if exists): color palette, line quality, mood, detail level. Rate 1-5 per dimension. Flag < 3. |
| 3.3 | Visual hierarchy | Clear focal point. No competing elements. Eye knows where to look. |
| 3.4 | Communication value | Illustration reinforces the slide's message (Slot 6). Not decorative. |
| 3.5 | Craft level | Meets minimum quality bar. |
| 3.6 | No AI slop | No smooth plastic, no purple-to-blue gradients, no stock-photo feel. |

**Exit logic:**
- 3.4 fails → ESCALATE (communication value is human judgment)
- 3.1-3.2 fail → CONTINUE (style can be corrected)
- 3.5-3.6 fail with severity=critical → ESCALATE; severity=warning → CONTINUE
- All pass → STOP (approved)
