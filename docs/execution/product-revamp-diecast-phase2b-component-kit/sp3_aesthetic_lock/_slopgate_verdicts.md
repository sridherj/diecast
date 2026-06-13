# Slop-gate verdicts — sub-phase 2b.3 (aesthetic lock)

**Run:** run_20260611_230342_b92fb0 · **Date:** 2026-06-12
**Signature screen:** `#/goal/CAST-412` canvas + Guide chat rail (composed entirely from the kit)
**Mode:** PROVISIONAL — **static source review** of the rendered component HTML/CSS (no browser in
autonomous runs; the project's established no-browser-visual-gate posture). The verdicts are the
externalized **checker-agent** judgments, not self-assessment. Re-run on a real 1440px Chrome
screenshot is carried forward as a human-eyeball action item.

**Artifact handed to both checkers:** `_slopgate_artifact.md` (REV 2 — post em-dash rework).
Both delegations inherited FULL AUTONOMY and the slide→app-screen adaptation note (ignore
slide-specific findings like projection viewport fit).

---

## `/cast-preso-check-visual` — scoped to `not-generic` / `not-ai-aesthetic`

| Dimension | Verdict |
|---|---|
| `not-generic` | **PASS** |
| `not-ai-aesthetic` | **PASS** (borderline) |

**Why PASS (grounded in source):** deliberate three-pane editorial shell with purpose-built named
zones (no header+sidebar+card-grid template); dot-grid radial-gradient canvas texture over `--cream`;
ink-tinted shadows (`rgba(26,26,40,…)`) not generic blue-black; raspberry structurally reserved to
needs-you; the Guide identity carried by a **diamond glyph + left-rule, not color** (an explicit
anti-slop choice); ink-filled NudgeCard CTA with no gradient; two-density ColleagueCard with shared
slot order. No gradient-glass, neon, bevel buttons, or symmetric icon grid.

**Borderline call-out (does NOT fail — logged to `borderline-calls.md` #6):** the Phase-1 chat
`.opbtn` ghost-pill (`border:1px solid var(--rasp-15); color:var(--rasp); background:var(--paper)`)
is the softest generic tell, but stays within system tokens and is contextually appropriate. Not
reworked — it is a Phase-1 chat affordance, not a 2b.3 signature-canvas zone (HOLD SCOPE). Suggested
future fix if it reads prominent in render: underline text-links instead of a bordered pill.

**Rework required: none.**

---

## `/cast-preso-check-tone` — scoped to UI-copy GPT-isms / em-dashes (FR-018)

**First pass: FLAGGED** — 3 em-dashes in on-screen copy (otherwise clean: no GPT-isms, no hedging,
no formulaic patterns):

1. Guide narration line — `"…tracking this goal — it flagged R02 …"`
2. Receipt-trail empty state — `"receipt trail — decision receipts appear here."`
3. Drill-in stub (dev/`#/dev`-gated) — `"…lifts here in Phase 3 — this labeled panel…"`

**Rework applied** (using the UI's own vocabulary, no literal `--`):
1. → `"The Guide is tracking this goal. It flagged ${FLAGGED_RULE} on the open PR and queued a review for you."` (two sentences)
2. → `"receipt trail · decision receipts appear here."` (`·` middot, matching `"Script complete · reload to replay"`)
3. → `"run_node.html lifts here in Phase 3 · this labeled panel proves the drillInto toggle."` (`·` middot)

**Re-run verdict: CLEAN.** "No em dashes, no GPT-isms, no hedging, no formulaic patterns anywhere in
the on-screen copy."

**Not assessed (carry-forward):** runtime/ORG copy the checker could not see in the markup —
`FEATURE.nudge.why` (`"…flagged R02 — unblocks 2 queued tasks"`) and the Phase-1 chat-script
narration still carry em-dashes. They are 2a/Phase-1-owned **data**, out of 2b.3 scope; a dedicated
copy pass (or 2a) should de-em-dash them.

---

## Outcome

**Slop gate GREEN (provisional).** Both visual dimensions PASS; tone CLEAN after rework + re-run. The
aesthetic is recorded as LOCKED in `docs/plan/product-revamp-diecast-decisions-so-far.md`; the
borderline visual pass is in `docs/plan/product-revamp-diecast-borderline-calls.md`. SC-004 is
de-risked for Phase 3. The single open dependency is environmental — a real-screenshot re-run — handled
by the provisional verdict + human-eyeball carry-forward, which by project posture does **not** block.
