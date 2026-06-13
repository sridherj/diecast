# Sub-phase 5 proof — three families clean, survival regression, spec v8 (staged)

> Terminal sub-phase of `refine-req-v3-how-update-mode`. Mode: autonomous (no browser). Date: 2026-06-13.

## Step 5.1 — three-family validation + nine-family no-regression — ✅ PASS

`eval_family_sweep.py --golden` (real `claude -p` maker per family, full nine-family corpus):

| Family | Terminal | served_by | human_review | check_html | empty shells | slot headings |
|--------|----------|-----------|--------------|------------|--------------|---------------|
| bug_fix `(was flagged)` | published | maker | 0 | ✓ | none | none |
| pilot_poc `(was flagged)` | published | maker | 0 | ✓ | none | none |
| random_idea `(was flagged)` | published | maker | 0 | ✓ | none | none |
| new_initiative | published | maker | 0 | ✓ | none | none |
| data_analysis | published | maker | 0 | ✓ | none | none |
| generic | published | maker | 0 | ✓ | none | none |
| personal_non_eng | published | maker | 0 | ✓ | none | none |
| refactor_migration | published | maker | 0 | ✓ | none | none |
| testing_qa | published | maker | 0 | ✓ | none | none |

- **9/9 CLEAN** (`served-by maker`, no flag, no finding), pairwise heading-set distinctness **PASS**,
  no `US`/`FR`/`SC` slot names. **Acceptance bar met: the three previously-flagged families publish
  clean, not flagged best-attempts; the six previously-clean families did not regress** (paraphrase
  freedom did not reduce quality).
- Goldens regenerated **once, gated** → `signoff/golden/` (nine renders + index). Evidence dir:
  `build/family-sweep/sp5/`.

## Step 5.2 — survival regression (`eval_sc003_survival.py`) — ✅ PASS

All blocks green (deterministic blocking gate), including the new render-anchor + UPDATE-mode
regressions:

- **(a)** same-source re-render → render-anchored comments place, ZERO DB changes, canonical untouched.
- **(b)** small ref-bearing edit → UPDATE mode: comment on an UNCHANGED block places byte-identically,
  no reanchor dispatch.
- **(c)** comment on a MODIFIED block → relocated by the ONE publish-boundary `cast-comment-reanchor`
  v3 dispatch; never silently dropped, never auto-resolved.
- **(d)** massive edit → CREATE mode (degrade-safe): survivor places, full CREATE path runs.
- **(e)** trust boundary: `block_ref` is server-resolved (no client param), `anchor_space='render'`,
  an absent quote yields `block_ref=NULL` (honest, never guessed).
- **(f) gap-CR idempotency under UPDATE** *(required, plan-review Decisions #2/#5)*: an UPDATE re-render
  of a doc carrying an open gap emits **ZERO** new gap change-requests (reuse prior `gaps-state.json`,
  skip `emit_change_requests`). Pinned so a future refactor cannot silently reintroduce the
  source-hash-keyed dedupe duplication.

Pre-existing block 2 (Phase-4b source-edit loop) was **reconciled** to the v3 render-anchor contract
(displacement now checked against the served render's container text via the `render_text` seam) —
this eval is `eval_`-prefixed and not in default CI, so the sp2 anchoring move had not been re-run
against it until now.

## Verification — ✅

- **Default-CI:** `pytest cast-server/tests/test_*.py` → **1077 passed** (additive schema + gate
  changes from sp2/3a/3b/4 don't regress the suite).
- **`bin/cast-spec-checker`** exits 0 on the current v7 spec (baseline); will be re-run on v8 at landing.
- **No-browser:** the nine-family visual / tray-badge human-eyeball pass is a static verdict +
  carry-forward (project convention) — never blocks.

## Step 5.3 — single spec pass v7 → v8 — ✅ APPROVED + LANDED

The `/cast-update-spec` human-approval gate was **approved by the owner** (2026-06-13) and the spec is
**landed at v8** (`bin/cast-spec-checker` exit 0; `_registry.md` render row bumped to v8). The change
brief at `docs/plan/2026-06-13-refine-requirements-v3-spec-v8-change-brief.md` records the reviewed
diff. Landed: the HOW two-mode contract + threshold knobs (`RENDER_UPDATE_*`) + the decided-`mode` row
stamp (FR-055/FR-056); **US16 verbatim-carriage SUPERSEDED in part** (anchor labels + one-unit-one-
container survive; CREATE leaf-text copy-exact dropped, with FR-060's empty-shell gate as the new CREATE
floor); comment anchoring re-spec to the render snapshot (US8/US12 re-targeted, `block_ref`/`anchor_space`
columns, server-resolved bridge, ref-less-NULL-is-success, FR-057); US19 survival reorientation +
publish-boundary reanchor (FR-058/FR-059); reanchor **contract v3** (US13 Scenario 5 / FR-044); the
paraphrase-meaning-drift known-limitation (Open Questions v8); the `check_update_fidelity`
NORMALIZED-text + the splice-assembles-the-published-artifact architecture note (1a verdict FAIL →
deterministic-splice); SC-022–SC-024; and the registry bump. The HOW prompt's "CONTRACT SOURCE OF
TRUTH" pointer was re-aimed at the v8 spec section.

## Step 5.4 — roundtrip cross-reference — ✅ no change needed

`cast-requirements-roundtrip.collab.md` (v2): its `target_quote` is canonical-content conflict
detection (a CR locates its modification region by quote in the canonical content) — a separate concern
from comment anchor space, unaffected by the source→render anchoring move. Its only `cast-comment-
reanchor` mention is a cross-reference to the render spec's surface. No source-anchored-quote wording in
the comment→change-request bridge → the conditional one-line fix does **not** apply; contract untouched.

## Step 5.5 — outcome recorded — ✅

- `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md` — new
  "Post-Phase-5 follow-up (EXECUTED)" section.
- `signoff/SIGNOFF.md` — the "Principal post-sign-off follow-up" section updated to **EXECUTED**;
  supersedes the 5d "3 HOW-layer flagged family renders" carry-forward.
