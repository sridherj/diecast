# Sub-phase 3e: The Spec Records the Maker Happy Path, and the Pipeline Proves Itself End-to-End

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase3/_shared_context.md` before starting.

## Objective

Update `cast-requirements-render.collab.md` (v2 → v3) to record the new contract — maker as happy
path, deterministic renderer demoted to fallback, the generating-state route behavior, the logical
id-backbone as a maker-emitted non-DOM structure, the **verbatim-carriage clause**, and the
**structural-violation override** (flagged best-attempt served, not the deterministic page) — and run
the full Phase 3 verification sweep against two real families. This is the terminal sub-phase: it both
records behavior and proves the phase gate.

## Dependencies

- **Requires completed:** 3a, 3b, 3c, 3d (the full pipeline exists and its tests are green).
- **Assumed codebase state:** both agents, `maker_gate.py`, `render_job_service.py`, the route +
  status endpoint + generating templates all exist and pass their sub-phase tests.

## Scope

**In scope:**
- One `/cast-update-spec` pass on `cast-requirements-render.collab.md` with the six deltas below.
- The full end-to-end verification sweep (two real families).
- Hand-off notes for 4a/4b in the goal dir.
- `docs/specs/_registry.md` row bump.

**Out of scope (do NOT do these):**
- Do NOT change pipeline/gate/route code — 3e records and verifies; it does not re-implement.
- Do NOT specify the 4a checker/quality-loop behavior — that is Phase 4a scope (recorded as a forward
  pointer only).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `docs/specs/cast-requirements-render.collab.md` | Modify (v2 → v3) | Draft v2 |
| `docs/specs/_registry.md` | Modify | Has the v2 row |
| `docs/goal/refine-requirements-better-rendering-v3/phase3-handoff.md` | Create | Does not exist |

## Detailed Steps

### Step 3e.1: Run the spec update (inline approval gate)

→ Delegate: `/cast-update-spec` on `cast-requirements-render.collab.md` with these deltas. **Review the
diff before approval, per the skill's gate** (this is the one human-approval point in Phase 3 — present
the diff, wait for approval, do not auto-apply):

1. **Happy-path inversion:** the render is produced by the `cast-requirements-what` →
   `cast-requirements-how` pipeline; `render_requirements()` / `rerender_requirements_html` are the
   **fallback** branch, served only on a **literal no-output** maker failure (crash/timeout/empty/
   structurally-unusable-by-extraction output) — supersedes US2 Scenario 2 / FR-003's synchronous-regen
   wording.
2. **Generating-state route behavior:** on a stale/missing render, `GET /goals/{slug}/render` starts a
   background job and serves a live generating state (stale render + banner when available) that polls
   `GET /goals/{slug}/render/status` and swaps in on `ready`; cached views, stubs, 404s, and the
   comment API are unchanged and never wait on generation.
3. **Logical id backbone as a non-DOM structure:** canonical `US-NN`/`FR-NNN`/`SC-NNN` ids are assigned
   upstream by the deterministic parser; the maker emits them verbatim, exactly once each, as visible
   anchor labels — the DOM contract (US7/FR-012/FR-013: zero `id=`, zero `data-block-anchor`, quote
   anchoring) is **explicitly preserved**; the WHAT-doc id mapping is the structure the Phase 4b diff
   agent reads.
4. **Verbatim-carriage clause (mandatory — the Phase 1 carry-forward):** the maker contract REQUIRES
   each requirement unit's anchorable text (its source body with inline markdown stripped) to appear
   verbatim and contiguous within one semantic container in the served DOM. Rationale recorded with it:
   the real orphan-exposure is silent `<mark>`-placement loss on a paraphrased DOM, not DB orphaning.
5. **Determinism scope narrowed:** SC-002's byte-stable/golden guarantee now covers the deterministic
   **fallback substrate** (and the unchanged cache envelope), not the happy path; the LLM-judged
   verification layer replacing the happy-path gate is recorded as **Phase 4a scope**, not specified
   here.
6. **Structural-violation override (record the owner decision):** on structural-gate exhaustion the
   server serves the **best attempt + a `structural_violation` human-review flag** (surfaced via the
   `flagged` job status, the `served-by: structural_violation` artifact stamp, and the reader-visible
   "needs review" badge) — it does **NOT** fall to the deterministic page. The deterministic fallback
   fires **only** on literal no-output. "Never silently drop" binds: degradation is surfaced, not
   hidden. (The richer human-review flag columns + scoring are Phase 4a scope — forward pointer only.)
7. New surfaces appended to `linked_files`: the two agent dirs, `maker_gate.py`,
   `render_job_service.py`, `generating.html.j2`.

### Step 3e.2: Run the full verification sweep (the phase gate)

- **End-to-end via the real pipeline (eval harness, not CI):** this goal (`new_initiative`) and the
  Phase 1a `bug_fix` fixture doc render through WHAT→HOW; the two pages are visibly distinct with
  family-appropriate section names (assert: section-heading sets differ between the two renders and
  contain **no** US/FR/SC slot names) — plus the human-eyeball browser pass recorded as a
  carry-forward (autonomous runs cannot drive a browser; static verdict, never blocks).
- `check_html` green on both: every canonical unit mapped to its logical id, none invented (FR-003);
  single self-contained file (FR-007).
- `test_fr007_readonly_guard.py` maker sweep green: canonical `.collab.md` never written.
- Generating-state e2e: changed source serves the generating state immediately; finished render swaps
  in (manual + the 3d fake-runner route tests).
- `bin/cast-spec-checker` green on the updated spec; `docs/specs/_registry.md` row bumped.

### Step 3e.3: Write the 4a/4b hand-off notes

Create `phase3-handoff.md` in the goal dir (one short section each):
- where the **4a checker stage** slots in (between `gate_html` and `publish`);
- where the **human-review flag** lands (the `render_jobs` row — 4a-2 adds its four columns on top of
  Phase 3's `flagged` status + `served-by` stamp);
- where the **WHAT-doc id mapping** lives for the 4b diff agent;
- the **shared `container_text_index` walker** in `maker_gate.py` that 4b-1 imports (no-copy);
- the **reserved `gaps[]` + `GAPS-DETECTED` trailer** seam Phase 5 activates.

## Verification

### Automated Tests (permanent)
- `bin/cast-spec-checker` green on the updated `cast-requirements-render.collab.md`.
- All sub-phase test suites (3b `test_maker_gate.py`, 3c `test_render_job_service.py` +
  readonly-guard sweep, 3d `test_render_route_and_service.py`) green together.

### Validation Scripts (temporary)
- The eval-harness e2e driver rendering both families; capture both HTML outputs + their `check_html`
  reports for the sweep record. Discardable.

### Manual Checks
- Review the `/cast-update-spec` diff before approval (the inline gate).
- Eyeball the two family renders side-by-side (human carry-forward; non-blocking).
- Confirm `_registry.md` version row bumped to v3.

### Success Criteria
- [ ] Spec updated v2 → v3 with all six deltas (incl. the verbatim-carriage clause AND the
      structural-violation override) — approved via the diff gate.
- [ ] Two real families render distinct, family-named pages (no US/FR/SC slot headings); both pass
      `check_html`.
- [ ] Readonly-guard maker sweep green (canonical `.collab.md` never written).
- [ ] Generating-state e2e converges (route tests + manual).
- [ ] `bin/cast-spec-checker` green; `_registry.md` row bumped.
- [ ] `phase3-handoff.md` records the 4a/4b/5 seams (checker stage, flag columns, id mapping, shared
      walker, gaps seam).

## Execution Notes

- This is the **single** spec pass for Phase 3 — all four conflicts flagged in 3a/3c/3d resolve here.
  The DOM contract is asserted **unchanged**.
- The spec **records** behavior; the clause texts were fixed up front by the plan — do not
  retro-discover behavior here.
- Delta #6 (the override) is the owner decision from `decisions-so-far.md`; make sure the spec wording
  matches it (flagged best-attempt served; deterministic only on literal no-output).
- **Human-review surface note:** a minimal flagged-renders list (slug, reason, score, link) is folded
  into **Phase 5d**, not here — but Phase 3's `flagged` status + `served-by` stamp are what make those
  renders discoverable, so record that linkage in the hand-off.
