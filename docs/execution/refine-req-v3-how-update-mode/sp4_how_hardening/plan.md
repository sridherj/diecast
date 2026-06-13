# Sub-phase 4: HOW Hardening — Invented IDs & Empty Shells

> **Pre-requisite:** Read `docs/execution/refine-req-v3-how-update-mode/_shared_context.md` — the
> ref-less-render rule (zero anchor labels, `block_ref=NULL` by construction) and the omit-never-pad
> contract.

## Objective

The two non-verbatim 5c findings are fixed at root cause: a **ref-less source** (`pilot_poc` — 0
canonical refs in source, HOW invented `SC-001`/`SC-002`) renders with **zero anchor labels and zero
invented ids**; a **thin source** (`random_idea`) renders **without empty placeholder sections**, and an
empty-shell render can no longer score 1.00 past the gates.

## Dependencies

- **Requires completed:** Sub-phase 3b — the prompts being hardened are the ones 3b rewrites. **Do not
  edit the HOW prompt twice in flight** — 4 follows 3b sequentially for exactly this reason.
- **Assumed codebase state:** the two-mode HOW prompt (3b); `maker_gate.check_html` (`:573`, blanket
  verbatim-carriage class already dropped by 3b); `check_what_doc` (`:350`); the family evals
  (`eval_family_sweep.py`) + `family_corpus/` fixtures.

## Scope

**In scope:**
- `pilot_poc` (invented ids): an explicit **zero-ref contract** in BOTH prompts — WHAT emits sections
  with empty `block_refs` for a source with no canonical refs; HOW renders a ref-less doc with NO anchor
  labels at all. Sharpen the gate's violation message to **name the invented ids**.
- `random_idea` (empty shells): a deterministic `check_html` violation — a unit/section container whose
  heading has no non-decorative text content is an empty shell. One negative example added to the HOW
  prompt's CREATE section.
- Re-run both family evals; record before/after in the job dirs.

**Out of scope (do NOT do these):**
- Do NOT modify the cold-reader checker (`cast-requirements-render-checker`) — the empty-shell fix is a
  **deterministic gate** over a checker-prompt tweak; the checker stays cold-reader + unmodified.
- Do NOT touch the two-mode contract, the mode decision, or the comment anchoring (sp2/3a/3b).
- Do NOT edit the spec — flag the new empty-shell gate check for the Sub-phase 5 spec pass.
- Do NOT re-introduce verbatim carriage (3b removed it deliberately).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-requirements-what/cast-requirements-what.md` | Modify | Add the zero-ref contract: a source with no canonical refs → sections with empty `block_refs` |
| `agents/cast-requirements-how/cast-requirements-how.md` | Modify | Zero-ref doc → NO anchor labels; one negative empty-shell example in the CREATE section |
| `cast-server/cast_server/requirements_render/maker_gate.py` | Modify | `check_html` (:573): sharpen the invented-id violation to NAME the ids; add the empty-shell violation class |
| `cast-server/tests/test_maker_gate_empty_shell.py` (or extend) | Create/Modify | Empty-shell fixture → `check_html` violation; zero-ref `check_what_doc` acceptance |

## Detailed Steps

### Step 4.1: `pilot_poc` — the zero-ref contract (root-cause, not retry-tuning)

The gate already catches invention (it's why the family served `structural_violation`) but the retry
never converged. Root-cause fix:
- **WHAT:** for a source with no canonical refs, emit sections with **empty `block_refs`**. Verify
  `check_what_doc` (`:350`) accepts a zero-ref source **cleanly** (no false violation on emptiness).
- **HOW:** render a ref-less doc with **NO anchor labels at all** (consistent with Sub-phase 2's
  `block_ref=NULL`-by-construction handling — a label-free page is correct, not broken).
- **Gate:** sharpen the `check_html` invented-id violation message to **name the invented ids** —
  feedback specificity is what makes the structural retry converge.

### Step 4.2: `random_idea` — the empty-shell deterministic gate

The contract already says omit-never-pad (US2 Scenario 2) but nothing deterministic enforced it and the
checker scored the padded render 1.00. Add a deterministic `check_html` violation:
- a unit/section container whose heading has **no non-decorative text content** is an empty shell →
  violation (prompt-ready message in the existing `check_html` style — it gets fed back as structural
  feedback).
- Add ONE negative example to the HOW prompt's CREATE section (a padded empty shell, marked as
  forbidden).
- Deterministic gate **over** a checker-prompt tweak — the checker stays cold-reader + unmodified.

### Step 4.3: Re-run both family evals

`eval_family_sweep.py --family pilot_poc` and `--family random_idea` → confirm `served_by=maker`,
`human_review=0`, `check_html` green. Record before/after in the job dirs.

## Verification

### Automated Tests (permanent)
`pytest` green over:
- **Empty-shell fixture → `check_html` violation:** a unit/section container with a heading + no
  non-decorative text content yields a prompt-ready empty-shell violation.
- **Zero-ref acceptance:** `check_what_doc` accepts a zero-ref source cleanly (no false emptiness
  violation); a WHAT doc with empty `block_refs` for a ref-less source passes.
- **Invented-id message specificity:** the `check_html` violation for invented ids **names** the
  offending ids (regression-pins the feedback-specificity fix).

### Validation Scripts (temporary / eval — not default CI)
- `eval_family_sweep.py --family pilot_poc` → `served_by=maker`, `human_review=0`, `check_html` green.
- `eval_family_sweep.py --family random_idea` → same; the rendered page has no empty placeholder section.

### Manual Checks
- Confirm the cold-reader checker (`cast-requirements-render-checker`) is **unchanged** (the empty-shell
  fix is a deterministic gate, not a checker tweak).
- Confirm a ref-less render emits **zero** anchor labels (consistent with sp2's NULL-by-construction).
- Confirm no verbatim-carriage class was re-introduced.

### Success Criteria
- [ ] A ref-less source renders with zero anchor labels + zero invented ids; the gate's invented-id
      message names the ids.
- [ ] `check_what_doc` accepts a zero-ref source cleanly (empty `block_refs`).
- [ ] An empty-shell container is a deterministic `check_html` violation; the HOW CREATE section carries
      a negative example.
- [ ] `eval_family_sweep.py --family pilot_poc` / `--family random_idea` → `served_by=maker`,
      `human_review=0`, `check_html` green; before/after recorded in the job dirs.
- [ ] The cold-reader checker is unmodified.

## Execution Notes

- **Root cause over retry-tuning.** The `pilot_poc` retry "never converged" — the fix is a structural
  zero-ref contract in both prompts + a specific gate message, not more retries.
- **Deterministic gate over checker-prompt tweak** for the empty shell — keeps the checker cold-reader
  and avoids a 1.00-on-padding regression by construction.
- **No spec conflict:** both fixes *implement* already-spec'd behavior (FR-003 never-invented, US2
  omit-never-pad). The Sub-phase 5 spec pass only needs the **new empty-shell gate check** recorded as an
  enforcement detail. **Flag it; do not edit the spec here.**
- The HOW/WHAT prompts being edited here are the ones Sub-phase 3b rewrote — this sub-phase runs AFTER
  3b precisely so they are not edited twice in flight.
