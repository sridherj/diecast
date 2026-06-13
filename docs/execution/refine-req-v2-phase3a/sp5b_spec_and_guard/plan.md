# Sub-phase 5b: Spec Lockstep + FR-007 Guard Extension — WP-G

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase3a/_shared_context.md` before starting.
> **Parallel with sp5a** — distinct files, no conflicts.

## Objective
Lock the new user-facing contracts into a spec (the document Phase 4 will cite) and extend Phase 1's
FR-007 read-only guard to cover the day HTML generation lands. This is documentation lockstep + a
regression pin — no product behaviour changes.

## Dependencies
- **Requires completed:** sp4 (the route + service + generated-artifact behaviours are settled and
  real, so the spec documents what exists). sp5a's checker I/O wording is coordinated (the verdict
  schema + PASS rule are already fixed in `_shared_context.md` — adopt verbatim; do not wait on
  sp5a's code).
- **Assumed codebase state:** `GET /goals/{slug}/render` + `rerender_requirements_html()` exist;
  Phase 1's `tests/test_fr007_readonly_guard.py` exists; the frozen fixture exists.

## Scope
**In scope:**
- Create `docs/specs/cast-requirements-render.collab.md` via `/cast-update-spec` (create mode),
  documenting: the `GET /goals/{slug}/render` route semantics (lazy regen, prompt-to-begin state,
  404 rule); the generated `refined_requirements.html` artifact class (AUTO-GENERATED header,
  `source-hash`, read-only, exempt from authorship suffixes — a render like `tasks.md`/`goal.yaml`);
  the zero-click extractor contract; the checker agent I/O (canonical verdict schema + PASS rule +
  the outside-the-delegation-contract carve-out); and the **Phase 4 DOM contract** (selectable
  units, nearest-heading derivation, **NO ids/anchors**).
- Register the spec in `docs/specs/_registry.md`.
- Extend `tests/test_fr007_readonly_guard.py`: after `rerender_requirements_html()` on the frozen
  fixture, source bytes identical + `bin/cast-spec-checker` exit 0.

**Out of scope (do NOT do these):**
- Any renderer/service/route/agent code (sp1–sp5a own those).
- Editing `cast-init-conventions.collab.md` or `cast-delegation-contract.collab.md` — the new spec
  **records** the generated-render classification + the checker carve-out; it does not silently
  extend those specs.
- Re-adding FR-008 / stable IDs anywhere (superseded by plan-review decision #1).

## Files to Create/Modify
| File | Action | Current State |
|------|--------|---------------|
| `docs/specs/cast-requirements-render.collab.md` | Create | Does not exist (via `/cast-update-spec`) |
| `docs/specs/_registry.md` | Modify | Add the new spec entry |
| `cast-server/tests/test_fr007_readonly_guard.py` | Modify | Extend with the post-render byte-identity + spec-checker assertion |

## Detailed Steps

### Step 5b.1: Author the spec
→ Delegate: `/cast-update-spec` (create mode) — author `docs/specs/cast-requirements-render.collab.md`.
Provide it the contracts from `_shared_context.md` → "Data Schemas & Contracts (the Naming
Contract)". The spec must cover, as SAV (stated-and-verifiable) behaviours:
- **Route:** `GET /goals/{slug}/render` — 200 + lazy regen on stale hash; no-op (byte-identical) on
  fresh; 200 prompt-to-begin when goal exists but no/stub requirements; 404 on unknown slug
  (path-traversal kill).
- **Generated artifact:** `goals/{slug}/refined_requirements.html` — AUTO-GENERATED header,
  `source-hash` comment, read-only, **render class** (like `tasks.md`/`goal.yaml`), exempt from the
  `.human/.ai/.collab` authorship suffixes per `cast-init-conventions.collab.md`'s generated-render
  treatment. Records the classification explicitly rather than extending the conventions spec.
- **Zero-click extractor:** `extract_zero_click_view(html) -> str` contract (keeps open surface +
  `<summary>`; drops closed `<details>` bodies).
- **Checker agent I/O:** canonical verdict schema + binary PASS rule (`can_state_what` + `missing[]`,
  not `score`) + the **outside-`cast-delegation-contract`** carve-out (subagent-mode, bare JSON, no
  `.output.json`).
- **Phase 4 DOM contract:** every rendered block = one semantic, contiguous, text-selectable unit
  under a real heading; **NO `id=`, NO `data-block-anchor`**; Phase 4 stores the quote + derives the
  nearest-heading hint.
Review the `/cast-update-spec` output: **names must match `_shared_context.md`'s Naming Contract
exactly** (Phase 4 will cite this spec).

### Step 5b.2: Register the spec
Add the entry to `docs/specs/_registry.md` (scope one-liner + linked files:
`routes/pages.py`, `requirements_render/renderer.py`, `requirements_render/zero_click.py`,
`services/requirements_render_service.py`, `agents/cast-requirements-checker/`).

### Step 5b.3: Extend the FR-007 guard
Extend `tests/test_fr007_readonly_guard.py`: load the frozen fixture
(`tests/fixtures/refine_requirements_v2/refined_requirements.collab.md`), snapshot its bytes, call
`rerender_requirements_html()` (pointed at it), assert the `.collab.md` bytes are **identical**
after, and `bin/cast-spec-checker` exits 0 — the FR-007/SC-004 lock, extended the day HTML
generation lands.

## Verification

### Automated Tests (permanent)
- `cd cast-server && pytest tests/test_fr007_readonly_guard.py` — frozen fixture bytes identical
  before/after a render; `bin/cast-spec-checker` exit 0.

### Validation Scripts (temporary)
- `bin/cast-spec-checker docs/specs/cast-requirements-render.collab.md` (if the checker validates
  spec docs) or the `/cast-spec-checker` skill — the new spec lints clean.
- `grep -n cast-requirements-render docs/specs/_registry.md` — registered.

### Manual Checks
- Diff the new spec's contract names against `_shared_context.md` Naming Contract — exact match.
- Confirm the spec records the generated-render classification + checker carve-out **without**
  editing `cast-init-conventions.collab.md` / `cast-delegation-contract.collab.md`.

### Success Criteria
- [ ] `docs/specs/cast-requirements-render.collab.md` exists, covering route + artifact class +
      zero-click + checker I/O + Phase 4 DOM contract; names match the Naming Contract exactly.
- [ ] Registered in `docs/specs/_registry.md`.
- [ ] `tests/test_fr007_readonly_guard.py` extended; frozen fixture bytes identical post-render;
      `bin/cast-spec-checker` exit 0.
- [ ] No edits to `cast-init-conventions.collab.md` / `cast-delegation-contract.collab.md`; no
      FR-008 / stable-ID language reintroduced.

## Execution Notes
- This spec is the contract Phase 4 cites — precision on names matters more than prose. The DOM
  contract (no ids/anchors, contiguous selectable units) is the load-bearing handoff.
- The generated `.html` is a **render**, not an authored artifact — say so explicitly in the spec so
  a future reader doesn't apply authorship-suffix rules to it.

**Spec-linked files:** this sub-phase reads `cast-init-conventions.collab.md` and
`cast-delegation-contract.collab.md` to record classifications/carve-outs accurately. Read both
before authoring; verify no SAV behaviour in either is contradicted (the plan's design review
confirms no conflict — record, don't extend).
