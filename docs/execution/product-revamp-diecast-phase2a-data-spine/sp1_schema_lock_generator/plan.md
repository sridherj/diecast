# Sub-phase 1 (2a.1): Schema Lock & Self-Validating Generator

> **Pre-requisite:** Read `docs/execution/product-revamp-diecast-phase2a-data-spine/_shared_context.md`
> before starting. It carries the binding constraints (NO TESTS, `file://` legality, F4
> single-source rule), the full `window.ORG` schema, and the canonical-vocabulary table.
>
> **Also read first (binding context the runner MUST load):**
> `docs/plan/product-revamp-diecast-decisions-so-far.md` and
> `docs/plan/2026-06-11-product-revamp-diecast-phase2a-data-spine.md`.

## Objective

Stand up `prototype/data/_build/generate-org.mjs` so it runs under node and deterministically
emits a **schema-complete (content-thin)** `prototype/data/org.js`, and **refuses to emit**
when any spine invariant is violated (printing the violated rule). After this sub-phase the
`window.ORG` schema is **real code, not prose** — 2b can swap its fixtures against the
skeleton immediately, and 2a.2 has an invariant gate to author against. This is the schema
lock + the machine-enforced drift gate; content authoring is 2a.2.

## Dependencies

- **Requires completed:** None. Phase 1 *plan* contracts only (appState shape + packaging
  rule). Phase 1 *execution* need not be complete — the only runtime coupling is one
  `<script src>` line, deferred to 2a.3.
- **Assumed codebase state:** `prototype/index.html` exists (Phase 1). `prototype/data/`
  may not exist yet — create it.

## Scope

**In scope:**
- `prototype/data/_build/package.json` pinning `@faker-js/faker` to an exact version;
  gitignore `node_modules`.
- `prototype/data/_build/generate-org.mjs`: seeded (`faker.seed(42)`) generator with
  canonical values as hardcoded top-of-file constants, hand-tuned prose in string constants,
  the fixed fictional demo timeline, and the **invariant gate folded into the generator**
  (a `check(rules, data)` pass before the file write — NOT a separate file).
- Emit `prototype/data/org.js` as a classic script:
  `window.ORG = Object.freeze(<json>);` with the GENERATED header comment.
- The 11 top-level keys present and structurally valid (content can be thin/skeletal here —
  2a.2 fills the prose and the full atom/roster/hiring/layer2 content).
- Freeze-policy documentation in the `org.js` header and `meta.owner_notes`.

**Out of scope (do NOT do these):**
- Full prose content, the 24 decision atoms' bodies, the 6 hiring candidates, the 12
  Layer-2 contracts' prose — that is **2a.2**. Here, the structures exist and pass the gate
  with skeletal/minimal-but-valid content.
- Wiring `org.js` into `index.html` — that is **2a.3**.
- Any test file, test suite, harness, or CI (banned — see NO TESTS).
- Real per-family stage vocabulary — `stageModels` ships `placeholder:true` (2c owns it).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `prototype/data/_build/package.json` | Create | Does not exist |
| `prototype/data/_build/.gitignore` (or root `.gitignore` entry) | Create/Modify | `node_modules` must be ignored |
| `prototype/data/_build/generate-org.mjs` | Create | Does not exist |
| `prototype/data/org.js` | Create (generated) | Does not exist — emitted by the generator |

## Detailed Steps

### Step 1.1: Authoring tooling — `_build/package.json`
Create `prototype/data/_build/package.json` pinning `@faker-js/faker` to an **exact**
version (same pin-for-stability rationale as Phase 1's CDN pins; e.g.
`"@faker-js/faker": "9.x.y"` exact, no `^`). Set `"type": "module"`. Gitignore
`prototype/data/_build/node_modules/`.

This is **authoring tooling, not a build step and not a test harness**: the browser never
touches `_build/`, `org.js` is committed, and FR-001's "no build step" governs *opening* the
prototype, which stays double-clickable. Document this in a top comment of the file/dir.

### Step 1.2: Generator skeleton — `generate-org.mjs`
Write `prototype/data/_build/generate-org.mjs`:
- `import { faker } from '@faker-js/faker'; faker.seed(42);`
- **Canonical values are hardcoded constants at the top** — never faker output. (See the
  canonical-vocabulary table in `_shared_context.md`: `Northwind`, `CAST-412`, `M04/S03/R02`,
  `crud-orchestrator`, the cred-stat strings, etc.) Faker supplies only structured filler:
  portfolio person names, commit SHAs, relative timestamps, candidate latency numbers.
- Hand-tuned prose lives in plain string constants alongside (the bodies are authored in
  2a.2; here they can be short valid placeholders or stubs that still satisfy the gate).
- Build the `window.ORG` object with all **11 top-level keys** (`meta · org · humans ·
  guide · agents · stageModels · goals · board · decisions · hiring · layer2`) per the schema
  in `_shared_context.md`.

### Step 1.3: Fixed fictional demo timeline
Encode all timestamps as a fixed fictional demo timeline — **one working day**,
`2026-06-11T09:00Z`–`18:00Z`, matching Phase 1's `17:52` receipt. Derive each from seeded
offsets, **never `Date.now()`** (determinism is what makes the freeze verifiable). Provide a
small helper (e.g. `t(offsetMinutes)`) that maps an offset into that day.

### Step 1.4: The invariant gate (inside the generator)
Implement a `check(rules, data)` pass that runs **before** the file write and, on any
violation, **prints the violated rule and exits non-zero without writing `org.js`**. Encode
these rules (from the high-level plan's verification — all machine-enforced here):
- Per goal **5–8 decision atoms** and **exactly one** `L3`.
- Every atom's `goal_slug` / `originating_agent` / `influenced[]` resolve to real entities.
- `spike_ref` integrity is **bidirectional** (the E4 verdict references the atom that
  references it).
- Every `L3` has **exactly 3 ranked options**, none `chosen`, with an evidence pack
  (`what_i_want`, `what_i_tried`).
- Every ticket assignee exists in `humans`/`agents`.
- Every artifact/work-stream step reference and every `spine_state.current` exists in its
  family's `stageModels` step ids.
- Supersede links pair correctly (`supersedes`/`superseded_by` are reciprocal).
- All four `stageModels` families carry `placeholder: true` (until 2c).
- Each goal's `autonomy.trust` equals the aggregate computed from its roster agents' `stats`
  fields.
- Every atom carries a **non-empty `diff`**.

(In 2a.1 the skeletal content must itself satisfy these rules — so seed each goal with the
minimum valid shape: e.g. 5 atoms incl. exactly one well-formed L3, placeholder stageModels,
a resolvable roster. 2a.2 then grows the content while keeping the gate green.)

### Step 1.5: Emit `org.js` with the GENERATED header
Write `prototype/data/org.js` as:
```js
// GENERATED by _build/generate-org.mjs — edit the generator, not this file.
// Classic script on purpose: file:// forbids fetch/imports.
window.ORG = Object.freeze(/* <serialized JSON> */);
```
- Serialize deterministically (stable key order) so re-runs are byte-identical.
- The file must contain **zero `require`/`import`** and start with the GENERATED header.
- `Object.freeze` is **shallow** (top-level only) — deliberate (see decisions-so-far).

### Step 1.6: Freeze-policy documentation
Document the **freeze policy** in the `org.js` header and `meta.owner_notes`: after 2a,
values are frozen; later phases may *extend* with new keys at designated extension points
but **never mutate existing values** — with **one standing exception: the `stageModels`
region is 2c-owned** and will be rewritten once by 2c's derived stage vocabulary (via the
generator, which re-runs the invariant gate at that moment). This is the **F4 single-source
rule** made explicit in the artifact.

## Verification

> Per the NO-TESTS rule: **no test files, no suite, no CI.** All checks below are
> manual commands a human runs, plus the generator's own refuse-to-emit gate.

### Validation Commands (run by hand; not committed as tests)
1. **Generate + determinism:**
   ```bash
   cd prototype/data/_build && npm install && node generate-org.mjs
   # emits ../org.js. Run it twice:
   node generate-org.mjs && git diff --quiet prototype/data/org.js && echo "DETERMINISTIC"
   ```
   Running it twice must produce a **byte-identical** file (`git diff --quiet` exits 0).
2. **Gate refuses on violation (authoring sanity check):** temporarily add a **second L3
   atom** to one goal's constants in the generator → re-run **refuses to emit** and **names
   the rule** → revert the edit.
3. **Standalone load:**
   ```bash
   node -e "global.window={}; require('./prototype/data/org.js'); console.log(Object.keys(window.ORG))"
   ```
   prints the **eleven** top-level keys.
4. **Hygiene:** `prototype/data/_build/node_modules/` is gitignored; `org.js` contains zero
   `require`/`import` and starts with the GENERATED header comment.

### Success Criteria (binary — every item must pass)
- [ ] `node generate-org.mjs` emits `prototype/data/org.js`.
- [ ] A second run produces a byte-identical file (`git diff --quiet` passes).
- [ ] Adding a second L3 to a goal makes the generator refuse to emit and print the rule.
- [ ] Standalone `node -e` load prints exactly the 11 top-level keys.
- [ ] `org.js` starts with the GENERATED header and contains no `require`/`import`.
- [ ] `node_modules/` is gitignored; `org.js` is committed.
- [ ] All four `stageModels` families carry `placeholder: true`.

## Design Review

- **Zero silent failures:** every budget and referential rule from the high-level plan's
  verification is an executable refusal inside the authoring tool — drift cannot be
  *authored*, rather than being caught later by a suite the owner has banned.
- **NO-TESTS compliance:** no test files, no harness, no CI; the gate lives **inside** the
  generator and runs only when an author regenerates the spine. Flagged explicitly so no
  reviewer mistakes the generator for a test suite — **do not** extract a standalone
  validator.
- **Naming:** decision atoms snake_case (playbook 05 / 2b locked); agent records camelCase
  stat fields (2b locked) — the mixed convention is **deliberate and documented in the schema
  comment**: atoms follow the ADR artifact idiom, agent records follow 2b's component-prop
  idiom. Everything else: kebab-case slugs, `DEC-<goal>-NN`, `CAST-4xx`, `<family>-NN` step
  ids.
- **Security:** static fake data, no user input, no network at runtime — no flags.

## Design Review Flags (from the plan)

| Flag | Action |
|------|--------|
| npm/node in `_build/` could be mistaken for a runtime build step (FR-001) | Confine to `_build/`, gitignore `node_modules`, commit generated `org.js`, document in file header |
| A standalone validator file could be read as a test file under NO-TESTS | Invariant gate folded **into** the generator (refuses to emit); no separate validator, no suite, no CI |
| Non-deterministic generation (`Date.now`, unseeded faker) would make the freeze unverifiable | Seed 42, fixed fictional timeline, byte-identical re-run check |

## Execution Notes

- **`_build/` is invisible to the browser.** The "no build step" rule (FR-001) is about
  *opening* the prototype; `org.js` is committed and double-clickable. Never let `_build/`
  artifacts leak into the runtime path.
- The skeletal content you author here must already satisfy the gate — seed each goal with
  the minimum valid shape (5 atoms, exactly one valid L3, resolvable references) so 2a.2
  starts from green.
- Do **not** create a separate validator file under any name — the gate must live inside
  `generate-org.mjs`. A standalone validator would read as a banned test artifact.
- **Spec-linked files:** none. No spec covers `prototype/` (FR-020 greenfield).
