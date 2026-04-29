# Iteration Budget by Complexity

| Complexity | Examples | Max Iterations | Rationale |
|------------|----------|----------------|-----------|
| Simple | Single SVG icon, badge, 2-3 node diagram | 2 | Few elements to get wrong. |
| Medium | Multi-element diagram, annotated illustration | 3 | Each iteration fixes 1-2 issues. |
| Complex | Multi-character scene, detailed technical illustration | 4 | Diminishing returns after 4. |

Default (if not specified by HOW maker): Medium (3 iterations).

## Hard Escalation Triggers (Override Remaining Budget)

1. **Oscillation detected:** Iteration N fixes issue A but reintroduces issue B from N-1.
2. **Pass 1 fails after 2 iterations:** Reject gate failing twice = prompt fundamentally broken.
3. **Issue count not decreasing:** Same or more issues than previous iteration.
4. **Subjective deadlock:** Cannot resolve brand/tone/taste questions.
5. **Quality score not improving:** Score improves < 0.1 between iterations.

## The Four Actions

| Action | When | Creator Response |
|--------|------|-----------------|
| STOP | All passes pass | Illustration approved |
| CONTINUE | Fixable issues found | Fix ONE variable, resubmit |
| BACKTRACK | Regression detected | Revert to previous prompt (from generation log) |
| RESTART | Wrong subject or broken prompt | Rewrite from scratch |
| ESCALATE | Budget exhausted, oscillation, or subjective | Human reviews best attempt |
