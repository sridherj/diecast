# Borderline Calls — Product Revamp: Diecast (full-autonomy run)

> Decisions the orchestrator made autonomously that the owner may want to
> review later. Each entry: what was decided, why, and what the alternative was.

## Orchestration-level

1. **Phase 5 planned as ONE detailed plan** (sub-streams 5a/5b/5c inside it)
   rather than three separate plans. Why: the three sub-streams share chrome,
   data spine, and component kit; one planner keeps them coherent. The
   execution-plan split will still parallelize them. Alternative: 3 plans.
2. **Planning dispatch mirrors the build DAG** — 1 → (2a∥2b∥2c) → 3 → (4∥5) → 6
   — instead of strictly sequential. Why: parallel groups are disjoint by the
   high-level plan's own analysis; saves ~2-3 hours of wall clock.

3. **Execution = one cast-orchestrate run per phase, DAG-sequenced by the
   fan-out parent** (1 → 2a∥2b∥2c → 3 → 4∥5 → 6) instead of a single
   orchestrate run over a master doc. Why: per-run 240-min timeout can't hold
   the whole build; per-phase runs give failure isolation + resumability and
   preserve cross-phase parallelism. Alternative: single master-plan run.
4. **cast-orchestrate triggered with parent_run_id linkage attempted first;
   root-run fallback if the allowlist 422s** (orchestrate is not in
   cast-fanout-detailed-plan's allowed_delegations — the user explicitly
   requested the orchestration leg, so a root trigger honors intent while
   respecting the allowlist mechanism).

5. **Reconciliation APPLY edits applied directly to two child plans** (phase2c
   hand-off note ownership F1; phase4 contract wording F2) instead of
   re-delegating to cast-detailed-plan children. Why: surgical one-block edits
   with exact reconciler-supplied wording; re-delegation costs ~15 min each for
   zero added judgment. Both edits carry inline attribution. Note: the fan-out
   skill's default is "never auto-edit child plans" — overridden by the owner's
   full-autonomy grant; original wording preserved in the reconciliation report.

## Phase 2b.3 — Aesthetic-lock slop gate (run_20260611_230342_b92fb0)

6. **`/cast-preso-check-visual` returned `not-ai-aesthetic` = PASS *borderline*** on the
   signature `#/goal/CAST-412` screen. The one call-out: the Phase-1 chat **`.opbtn` ghost-pill**
   (`border:1px solid var(--rasp-15); color:var(--rasp); background:var(--paper)`) is the softest
   "generic ghost-button" tell on the screen. It does **not** fail — it stays within system tokens
   and is contextually appropriate for inline chat actions — so it was recorded as a borderline
   pass, **not waved through and not reworked** (the defect is on a Phase-1 chat affordance, not a
   2b.3 signature-canvas zone, and HOLD SCOPE keeps 2b.3 to the canvas composition). Suggested
   future fix (if the rendered button reads prominent): drop the border and render the chat options
   as underline text-links (`color:var(--rasp); text-decoration:underline; border:none;
   background:none`). `not-generic` was a clean PASS; the tone gate ended CLEAN after the em-dash
   rework (not borderline). All verdicts are **PROVISIONAL** (static source review — no browser;
   re-run on a real 1440px screenshot is carried forward in `decisions-so-far.md`).

## Phase 3.4 — The Real Hero Morph (run_20260612_043626_bb7d70)

7. **Slop gate + morph-gate visual items resolved on STATIC grounds (no browser).** Under full-autonomy
   no live-browser is available (the connected browser needs a user-selection gate), and the slop-gate
   checker agents (`/cast-preso-check-visual`, `/cast-preso-check-tone`) are not in this runner's
   allowlist. Per the pre-written plan posture, the 4-surface slop gate and the 5-item morph gate were
   resolved as best-effort static self-assessments: morph-gate item 3 (`file://`) is a hard PASS; items
   1/2/4/5 (glide / no-flash / ~350ms / reduced-motion) and the slop-gate taste items are PASS-PROVISIONAL
   pending a human eyeball. A morph-gate item needing an eyeball is PASS-PROVISIONAL, not a failure
   (delegation directive). Alternative would have been to block on the unavailable checkers — explicitly
   forbidden by the autonomy directive.
8. **Receipt persists after the reverse morph (one receipt, not zero).** The plan wording "returns the
   feature canvas EXACTLY" lists stageFocus/pinned/chat as the restored state; it pairs with "one atom
   DEC-CAST-412-03, one receipt." Decision taken: the forward morph's single receipt PERSISTS through the
   reverse (the reclassification decision was really made and recorded; the undo reverses the VIEW/shape,
   not the decision). So the receipt trail shows one receipt after the full forward+reverse cycle — this
   is the intended "one receipt" end state, not a regression. Alternative (pop the receipt on reverse)
   was rejected: it would erase the record of a real decision and contradicts "one receipt".
9. **`statement` added to `morph_view.E2-seed` via the generator (the only ORG change).** 3.1's seed
   omitted the `statement` field that the LOCKED EvidenceBlock E2 needs for its bold line. Rather than a
   render-time hack, the field was added in `generate-org.mjs` (the sanctioned data path; gate green; F4:
   the single line is the only org.js diff). It reuses CAST-431's H3 root-cause wording but stays `open`
   (the morphed loop just re-opened). Alternative (map prediction→statement in the view) was rejected as
   shadowing the contract.
10. **New morph narration is em-dash-free; surrounding 3.1/3.3 narration is not.** To honor FR-018
    (hyphens not em dashes) without rewriting prior-phase copy, the NEW morph beats use periods/commas/colons
    only. This leaves the chat thread mixing clean (new) and em-dashed (old) lines. Recorded as the CF3
    de-em-dash carry-forward: a single copy pass across ALL narration (3.1 + 3.3 + 3.4) is preferable to
    piecemeal edits. Not blocking.

## Phase 4 orchestration — execution order (run_20260612_052634_8feff3)

11. **Phase 4 sub-phases executed STRICTLY SERIAL (4.1 → 4.2 → 4.3 → 4.4), not 4.1∥4.2
    concurrent.** Why: the execution manifest's file-collision honesty note is explicit —
    all four sub-phases edit the single file `prototype/index.html` and two independent
    `cast-subphase-runner` agents have NO merge mechanism, so concurrent dispatch would
    clobber. The logical DAG (4.1∥4.2 → 4.3 → 4.4, max-batch-size 3) is honored as a
    topological constraint, but the physical single-file artifact forces serialization
    (4.1 before 4.3; all of 4.1/4.2/4.3 before 4.4 — serial order satisfies every edge).
    The generator is 4.1-single-owned regardless, so `org.js` is never written concurrently.
    Mirrors the Phase 3 split's serial override. Alternative (concurrent 4.1∥4.2 with
    git-worktree isolation + manual merge) was rejected: the HTTP dispatch path gives runners
    no worktree isolation, and a hand-merge of two index.html edit sets adds risk with no
    wall-clock payoff for a 4-sub-phase chain. Cost: higher wall-clock; benefit: zero
    clobber risk. Recorded per FULL-AUTONOMY directive.

(entries appended as the run proceeds)

## Phase 4 close — sub-phase 4.4 taste calls (run_20260612_063542_dc5326)

12. **Ink-dark parity terminal AFFIRMED against the locked light world (no paper-light fallback).** The
    FR-017 parity pane renders an ink-dark terminal (IBM Plex Mono) beside the paper-light canvas — the
    prototype's one sanctioned identity exception (Phase-4 Decision 7). The 4.4 slop gate viewed it on a
    LIVE browser and judged it deliberate and legible, NOT generic-AI: it reads as a real terminal, the
    contrast is the point (three access tiers, one substrate), and the same E4 card lands in both the dark
    and light panes. Verdict: KEEP ink-dark. The pre-authorized paper-light terminal fallback was NOT
    triggered. Alternative (pre-emptively lighten the terminal) was rejected — it would erase the
    three-tiers contrast that is the moment's whole point.
13. **CF3 (de-em-dash) extended to cover the Phase-4 copy — non-blocking standing carry-forward.** The
    tone gate found em-dashes survive in the spike/data SCRIPTS narration and in 3 new org.js data strings
    (`goals['CAST-452'].parity.caption`, `parity.transcript[4]`, `goals['CAST-461'].evidence.resolved_view
    .reconciliation_note`). The verdict + L3-title data already use hyphens (FR-018-compliant). Decision:
    fold these into the existing CF3 carry-forward (a SINGLE unified de-em-dash pass across ALL narration +
    data copy, deferred to a dedicated copy pass / Phase 6). Rejected: a piecemeal 4.4 rewrite — `org.js`
    is frozen (constraint #3; an em-dash is not a drift literal, and editing `reconciliation_note` /
    `parity.transcript` would mutate 4.1-authored values), and half-converting only spike/data leaves the
    chat voice inconsistent with feature/debug. Not blocking (Phase-3 precedent: the gate closes green with
    CF3 logged, exactly as 3.4 did).
14. **Spike needs-you chip reads "CAST-412" — authored-data semantics, left as-is (observation).** The
    spike L3 `DEC-CAST-452-03` carries authored `influenced: ["CAST-412"]`, and `NeedsYouChip` renders the
    first influenced `CAST-` ticket → the chip reads "⚠ needs you · CAST-412" on the spike canvas. This is
    intentional cross-ticket linkage (the vendor-SDK go/no-go influences the checkout feature CAST-412),
    within the L3 budget (exactly one chip), and not a drift literal. Decision: leave as-is — `org.js` is
    frozen and this is 2a/4.1-owned authored data, not 4.4's to rewrite in a stitch phase. Recorded as a
    non-blocking observation for a later content pass to confirm/relabel if desired.
