# Sub-phase 5b: Reconciliation Through the Gate & Honest Page Markers

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase5/_shared_context.md` before starting —
> especially **Applied Owner-Resolved Edits #1 (GATE-ALL)**, the **Marker status vocabulary**, the
> **Gap CR provenance**, and the **Dedupe fingerprint** schemas (fixed there — copy verbatim).

## Objective

Supplied, evidence-validated gap answers become normal change-requests through the v2 same-door gate
(deduped, provenance-stamped, policy-laned by the **now-GATE-ALL** global `WRITEBACK_GATE_POLICY`);
the page renders an honest `.rr-gap` marker per open gap — **question + a fixed status string, NEVER
the proposed answer text** — and un-marks naturally when the approved detail lands in canonical and
the next view regenerates. SC-007 (the gap-injection realization) is green, in both arms. The gate
function, policy lanes, conflict predicate, writeback agent, outbox, and relay are all **consumed
byte-unchanged** — 5b is a *proposer* and a *renderer of markers*, not a new writer.

## Dependencies

- **Requires completed:** 5a (the `gaps[]` schema, the gapfill agent, the pipeline stages with
  `emit_change_requests` as a `gaps-state.json`-only stub, `validate_evidence`, the maker_gate
  correspondence rules, the `gaps-state.json` status enum).
- **Consumed unchanged:** `change_request_service.create(...)`,
  `gate_status(kind, target_quote, policy)`, `detect_conflict`, `cast-requirements-writeback`, the
  transactional outbox + relay, `idx_change_requests_goal_status`. **None of this is modified.**
- **Assumed codebase state:** `change_requests` columns `kind`/`base_version`/`origin_*`/`author`/
  `author_type`; `requirement_versions.version`; the v2 cache/version regen machinery (source-hash →
  stale render → regenerate). `_theme.css.j2` carries `.render-refreshing`/`.comment-unplaced`.
- **Parallel with 5c** (5c is the long pole, parallel to the whole 5a → 5b chain).

## Scope

**In scope:**
- The `emit_change_requests` stage body (filling 5a's stub): `change_request_service.create` per
  `supplied`+validated gap, with the fixed provenance column values.
- **The GATE-ALL flip:** `config.py` `WRITEBACK_GATE_POLICY` default → `"gate-all"` (env override
  preserved).
- Structural fingerprint dedupe (`_normalize_gap_question` + the block_refs/section key) before propose.
- `.rr-gap` marker rendering in the HOW output (question + a fixed status string from the table) +
  CSS in `_theme.css.j2`.
- The one-line checker gap-amnesty clause in `cast-requirements-render-checker` (reconciled with the
  spec's existing SC-014 anticipation).
- Tests: `test_gap_reconciliation.py` (new); `test_fr007_readonly_guard.py` extension; survival +
  carriage regression on a marked render.

**Out of scope (do NOT do these):**
- Do NOT modify `change_request_service.py`, `gate_status`, `detect_conflict`, the writeback agent,
  the outbox, or the relay — call `create(...)`; never re-implement intake or change the gate.
- Do NOT add a new column for the dedupe fingerprint (HOLD; it rides `origin_artifact_path#gap=`).
- Do NOT render `proposed_body` anywhere on the page (FR-016 structural — it lives only on the CR surface).
- Do NOT build a per-origin gate policy — the GATE-ALL flip is **global** (the sanctioned knob).
- Do NOT add `id=`/`data-block-anchor` to markers (class-based only).
- Do NOT change the gap-detection / gapfill / evidence-validation logic (5a's).
- Do NOT edit the spec (5d records 5b's flagged deltas).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/render_job_service.py` | Modify | 5a's `emit_change_requests` is a `gaps-state.json` stub; fill the body to dedupe + `create` + promote `gaps-state` status |
| `cast-server/cast_server/config.py` | Modify | `WRITEBACK_GATE_POLICY` default `"gate-except-additions"` → `"gate-all"` (env override preserved) |
| `agents/cast-requirements-how/cast-requirements-how.md` | Modify | Gains the `.rr-gap` callout rendering rule (question + fixed status; never `proposed_body`) |
| `agents/cast-requirements-render-checker/cast-requirements-render-checker.md` | Modify (one line) | Gains the gap-amnesty clause (reconcile with SC-014's existing anticipation) |
| `cast-server/cast_server/templates/.../_theme.css.j2` | Modify (append) | Append a `.rr-gap` block beside `.render-refreshing`/`.comment-unplaced` (disjoint additive) |
| `cast-server/tests/test_gap_reconciliation.py` | Create | Does not exist |
| `cast-server/tests/test_fr007_readonly_guard.py` | Modify | Extend: a full gap-fill run leaves canonical byte-identical |

> Confirm the `_theme.css.j2` path: `grep -rl "render-refreshing" cast-server/cast_server/templates/`.
> Confirm the `create` signature + `gate_status` keys before wiring:
> `grep -n "def create\|def gate_status" cast-server/cast_server/services/change_request_service.py`.

## Detailed Steps

### Step 5b.1: The GATE-ALL flip (config — global, owner-resolved)

In `config.py`, flip the default and annotate it as the goal's resolved policy:

```python
#   "gate-all"  → everything gated ('proposed');  ...
# refine-requirements-v3 (owner decision, 2026-06-12): the goal's global writeback policy is
# GATE-ALL — every change-request (gap-fill additions included) awaits explicit human approval
# before touching canonical. The gate mechanism is consumed UNCHANGED; only this value changes.
# Global by design (a per-origin policy would change the gate, which HOLD forbids).
WRITEBACK_GATE_POLICY = os.environ.get("CAST_WRITEBACK_GATE_POLICY", "gate-all")
```

This is the ONLY policy change. `gate_status` already returns `"proposed"` for every kind under
`gate-all` — no code edit to the gate. **Note the blast radius:** this gates ALL writebacks (not just
gap CRs); that is the sanctioned global behavior the owner chose.

### Step 5b.2: `emit_change_requests` stage body (filling 5a's stub)

For each `supplied` + evidence-validated gap (from 5a's `validate_evidence`):
1. **Dedupe before propose** (Step 5b.3) — skip if a live fingerprint match exists.
2. Call `change_request_service.create` **directly** with the fixed provenance values from
   `_shared_context.md`: `kind="addition"`, `target_quote=None`, `section_hint` from the proposal,
   `proposed_body` = the evidence-validated answer, `base_version` = current
   `requirement_versions.version` (**read at emit time** — the v2 conflict predicate then guards a
   canonical that moved between ask and approval), `author="cast-requirements-gapfill"`,
   `author_type="agent"` (**hard-coded at the emitter** — no spoof surface),
   `origin_phase="render-gapfill"`, `origin_activity_id`=job id,
   `origin_artifact_path="{what_doc_job_path}#gap={fp12}"`,
   `status=gate_status(kind, target_quote, WRITEBACK_GATE_POLICY)` (derived exactly as the route does
   — under GATE-ALL this is always `"proposed"`).
3. Promote the gap's `gaps-state.json` status: `cr-proposed` (gated lane) or `cr-applied` (only if a
   non-gate-all policy fast-tracked it — not reachable under this goal's GATE-ALL default, but the
   mechanism stays correct so a policy change elsewhere still works). A `rejected` dedupe match →
   `unfilled-declined`. `cr_id` recorded.
4. **CR creation failure (DB error)** → gap recorded `unfilled-ask-failed`, marker still renders, job
   row records the error — the render never blocks on the proposal store; next regen retries naturally
   (dedupe finds no row).

### Step 5b.3: Dedupe (no CR spam — structural fingerprint)

`fp12 = sha256(...)[:12]` over the **structural** key: `sorted(block_refs) + " " + section_title`
(primary) + the question folded through a NAMED normalizer `_normalize_gap_question`
(casefold → collapse whitespace → strip trailing punctuation) (secondary; Plan Review CQ1 — keying on
block_refs/section keeps the fingerprint stable across LLM re-wording). Before `create`: query
`change_requests` filtered by `goal_slug` FIRST (`idx_change_requests_goal_status`), then
substring-match the `#gap={fp12}` fragment (O(CRs-per-goal); Plan Review P1 — never a global scan).
Skip when ANY row with the fingerprint exists in `proposed`/`applied`/`conflicted`/`rejected`; only
`superseded` frees re-proposal. A `rejected` match maps the gap to `unfilled-declined` ("asked and
answered — do not re-ask the human").

### Step 5b.4: `.rr-gap` marker rendering (HOW contract)

Add to the HOW agent contract: render **one** themed `.rr-gap` callout per open gap, inside its
section, containing the `question` + a status line from the **FIXED vocabulary** (the
`_shared_context.md` table) — and **nothing else**. Each status string maps **1:1** to the
`gaps-state.json` status enum. **The `proposed_body` NEVER appears on the page** (FR-016 — the page
never shows content that exists nowhere else; the CR DB is not "the page"). Markers are **class-based**
(zero `id=`, zero `data-block-anchor`), sit **between** block containers (anchorable block text
untouched, so carriage + survival gates stay green), visually distinct (the honest-gap affordance
SC-007 demands).

### Step 5b.5: `.rr-gap` CSS (`_theme.css.j2`)

Append a `.rr-gap` block beside `.render-refreshing`/`.comment-unplaced` — **additive, disjoint**. A
distinct themed callout (muted, "missing detail" affordance). Class-based selectors only.

### Step 5b.6: Checker gap-amnesty (4a coordination — one line)

Add to the `cast-requirements-render-checker` prompt: *"an explicitly-marked gap (`.rr-gap`) is
honest communication, not a comprehension failure — judge the page given the gap; do not fail it for
having one."* Without this the quality loop reworks forever against a gap only a human can close.
**Reconcile with the spec:** SC-014 already references gap amnesty ("a `.rr-gap` page is not failed
for a missing outcome") — if the checker prompt already carries the clause (verify by grep), this is
a no-op/confirmation; if not, add it. Do NOT duplicate; checker input stays artifact + family.

### Step 5b.7: Un-mark is the existing machinery — verified, not built

Approval → writeback surgical apply → version bump → source-hash change → stale render → next view
regenerates → WHAT (reading the now-complete source) declares no gap → no marker, no new CR. **Build
nothing here** — the convergence tests (Step 5b.8) pin it; a manual e2e walks it in a browser
(non-blocking carry-forward).

### Step 5b.8: Notification-surface check

A gap CR rides the existing outbox → relay → `recent_writebacks` descriptor with its provenance badge
sourced from `origin_*` ("from render-gapfill, by cast-requirements-gapfill"). Assert the badge
renders from existing code paths with **zero new notification code**. (Under GATE-ALL a `proposed`
CR queues no outbox FYI — the badge appears once the CR is approved/applied; the mechanism test that
exercises the FYI lane sets a non-gate-all policy in-test.)

## Verification

### Automated Tests (permanent)

`pytest cast-server/tests/test_gap_reconciliation.py` (new — fake runners + real service + real DB):
- **Emit shape:** a supplied gap produces **exactly one** `change_requests` row with `kind="addition"`,
  `base_version` = current `requirement_versions.version`, `author="cast-requirements-gapfill"`,
  `author_type="agent"`, `origin_phase="render-gapfill"`, `origin_activity_id` = job id, and the gap
  fingerprint in `origin_artifact_path`; intake status matches `gate_status` under the live policy —
  **under GATE-ALL: `proposed`, no outbox FYI.** A parametrized mechanism case sets
  `gate-except-additions` and asserts the fast-track `applied` + one FYI (proves the gate is
  consumed-unchanged and only the policy value drives the lane).
- **Dedupe:** re-render same source → zero new CRs; CR `rejected` → re-render → zero new CRs AND
  marker reads "declined"; CR `superseded` → re-propose allowed. Plus a **re-wording stability** case:
  the WHAT agent emits a re-worded `question` for the same block_refs/section → same fingerprint →
  zero new CR (proves CQ1).
- **Gated-lane convergence (T1, the FR-016 headline — under GATE-ALL this is the LIVE lane):** emit a
  gated gap CR, approve it in-test via `change_request_service` apply, re-render with fake runners →
  assert the marker is **gone**, the detail renders as normal canonical content, and **NO** new CR is
  created. (This is the deterministic regression for the human-gated lane the goal actually runs.)
- **Auto-apply convergence (mechanism, parametrized to a fast-track policy):** a fast-track-applied
  addition bumps the version + changes the source hash → the in-flight job is `superseded`
  (compare-and-publish) → the fresh job's WHAT run no longer detects the gap → no marker, no new CR.
  Asserts the loop terminates (no propose-regen-propose cycle).
- **Read-only guard** (`test_fr007_readonly_guard.py` extended): a full gap-fill pipeline run (fake
  runners) leaves the canonical `.collab.md` **byte-identical** — the ONLY mutation path remains the
  v2 writeback agent on CR approval.
- **Gap-injection (SC-007):** from a corpus fixture, delete a key detail (e.g. a metric's data
  source), run the pipeline → assert (a) a gap was declared, (b) **either** a CR exists (answerable —
  detail present in the fixture's `requirements.human.md`) **or** the render carries an explicit
  `.rr-gap` marker — and in **NO** branch does an unmarked, silently-incomplete render publish. Run
  **both arms:** answerable (detail in raw upstream) and unanswerable (detail nowhere).
- **Survival + carriage regression:** `gate_html` green on a marked render (markers sit between block
  containers; anchorable text untouched).

### Manual Checks
- `grep -n "WRITEBACK_GATE_POLICY" cast-server/cast_server/config.py` → default is `"gate-all"`.
- `grep -n "def create\|def gate_status\|def detect_conflict" cast-server/cast_server/services/change_request_service.py`
  + `git diff --stat cast-server/cast_server/services/change_request_service.py` → **no changes** to
  the gate/intake (consumed unchanged).
- Confirm no template/agent path renders `proposed_body` (`grep -rn "proposed_body" cast-server/cast_server/templates/ agents/cast-requirements-how/` → absent on the page).
- Confirm `.rr-gap` markers carry zero `id=`/`data-block-anchor`.

### Static / carry-forward (no browser in autonomous runs)
- The manual e2e of the gated un-mark lane (propose → marker visible → approve in the CR surface →
  re-view → marker gone, detail rendered as canonical content) is a **static verdict + human-eyeball
  carry-forward** recorded for 5d's sign-off. The automated gated-lane convergence test (T1) is the
  CI regression; the browser walk never blocks.

### Success Criteria
- [ ] `WRITEBACK_GATE_POLICY` default is `"gate-all"` (global, env-overridable); `change_request_service`
      is byte-unchanged.
- [ ] `emit_change_requests` creates exactly one `kind="addition"` CR per supplied+validated, deduped
      gap, with the fixed provenance columns and `base_version` read at emit time; `author_type` hard-coded.
- [ ] Under GATE-ALL every gap CR intakes `proposed` (no FYI); the parametrized fast-track mechanism
      case still passes (gate consumed-unchanged).
- [ ] Structural fingerprint dedupe is stable across LLM re-wording (CQ1); the pre-check filters by
      `goal_slug` first (P1); only `superseded` re-proposes; `rejected` → `unfilled-declined`.
- [ ] `.rr-gap` markers render question + a fixed status string only, class-based, between blocks;
      `proposed_body` never on the page (FR-016 structural).
- [ ] Checker gap-amnesty clause present (reconciled with SC-014, not duplicated).
- [ ] Both convergence lanes green (gated T1 = live lane; auto-apply = parametrized mechanism); SC-007
      gap-injection green both arms; read-only guard green; survival/carriage green on a marked render.
- [ ] No unmarked, silently-incomplete render can publish.

## Execution Notes

- **GATE-ALL is the live lane for this goal.** Write the tests so the human-gated convergence (T1) is
  the primary regression; keep the fast-track auto-apply convergence as a *parametrized mechanism*
  test (set the policy in-test) so the gate-consumed-unchanged guarantee is still proven without
  resting the goal's behavior on it.
- **`create` directly, never self-HTTP-POST** (Decision #4) — `create` IS the governed write path;
  the emitter stamps exactly what the route's agent lane would. If a reviewer prefers the literal
  one-door reading, it's a one-function swap (noted, not done).
- **FR-016 is structural, not a promise.** There is no code path by which un-approved text reaches a
  reader as requirement content — the marker carries the question + status, the answer lives only on
  the CR surface, and the page always regenerates from canonical.
- **Spec-linked files:** the marker contract, the gap-CR-as-change-request behavior, and the GATE-ALL
  policy value are spec-relevant under `cast-requirements-render.collab.md` + (consumer-side)
  `cast-requirements-roundtrip.collab.md`. **Flag for 5d — do not edit the spec here.**
