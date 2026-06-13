# Sub-phase 3b: The Deterministic Maker Gate Productionizes the Spike Audits

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase3/_shared_context.md` before starting.

## Objective

Create the pure, I/O-free module `cast_server/requirements_render/maker_gate.py` exposing
`check_what_doc(what_doc_text, parsed) -> GateReport` and `check_html(html, parsed) -> GateReport`
(a frozen `{passed: bool, violations: [str]}`), encoding the Phase 1 audit semantics as production
gates with full unit-test coverage. This module is the **executable definition of "structurally valid
maker output"** that 3c enforces and 4a later wraps its quality loop around. It also exposes the
**shared container-text walker** (`container_text_index`) that 4b-1 imports (no-copy prerequisite).

## Dependencies

- **Requires completed:** None within Phase 3 (parallel with 3a; the contract shapes are fixed by the
  plan, not discovered from 3a's prompts).
- **HARD cross-phase prerequisite:** **Phase 2's `strip_inline_markdown` pure helper** in
  `goal_card.py`. Phase 2 runs in parallel, so the helper may not yet exist when 3b is built. The
  dependency is on *that one pure helper*. If Phase 2 has not landed it, **block on the helper or lift
  it to a shared pure module — never inline-copy a second stripper** (copying is precisely the drift
  this gate forbids).
- **Assumed codebase state:** `parser.py` (`Block.ref`, block body access), `renderer.py`
  (`render_requirements()` deterministic output) exist.

## Scope

**In scope:**
- `maker_gate.py` with `check_what_doc`, `check_html`, the `GateReport` shape, and the **public
  module-level `container_text_index(html)` helper** (revision b).
- Full unit-test coverage in `cast-server/tests/test_maker_gate.py`, including an **independent**
  test class for `container_text_index`.

**Out of scope (do NOT do these):**
- Do NOT import this module from `renderer.py` (only the service layer imports it).
- Do NOT write any LLM, I/O, DB, or subprocess code — this module is pure.
- Do NOT implement comment-survival checking (`check_comment_survival` is 4b-1, additive later).
- Do NOT re-implement `strip_inline_markdown` — import Phase 2's.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/maker_gate.py` | Create | Does not exist |
| `cast-server/tests/test_maker_gate.py` | Create | Does not exist |

## Detailed Steps

### Step 3b.1: Define `GateReport` + `check_what_doc`

`GateReport` = frozen `{"passed": bool, "violations": list[str]}`. Violations are **prompt-ready
strings** (3c feeds them back to the HOW agent verbatim on retry; 4a appends to the same channel).

`check_what_doc(what_doc_text, parsed)` asserts:
- front matter parses; `contract` == `cast-requirements-what/v1`; `source_hash` matches;
- **id-mapping totality:** every `Block.ref` parsed from source appears in exactly one section's
  `block_refs`; no ref appears twice; no ref exists that the parser didn't produce (invented);
  `unmapped_refs` is empty;
- section titles non-empty and none equals a US/FR/SC slot name (`User Stories`,
  `Functional Requirements`, `Success Criteria` — the family-communication rule made checkable).

### Step 3b.2: Expose the shared container-text walker (revision b)

Implement the HTMLParser descendant-text-concatenation walker as a **named, module-level, public
helper** — not buried inside `check_html`:

```python
def container_text_index(html: str) -> ...:
    """Walk the HTML (stdlib HTMLParser), concatenating descendant text-node content per
    container, byte-faithful to requirements_comments.js. Returns the per-container text index
    used for verbatim placement checks. PUBLIC: imported by check_html AND by Phase 4b-1
    (cast-comment-reanchor survival gate). No-copy shared helper."""
```

- Whitespace handling stays **byte-faithful to the JS walker** (the 1b harness-fidelity rule).
- `check_html` calls this helper internally; it is **not** re-implemented inline anywhere.
- It gets its **own independent unit-test class** (see Verification) so 4b-1 can import it on a
  proven contract.

### Step 3b.3: `check_html` — id parity + per-block correspondence (the 1a audit)

- the set of `US-NN`/`FR-NNN`/`SC-NNN` tokens visible in the HTML text equals the parsed ref set
  (none missing, none invented, none renamed); each id label occurs exactly once;
- the label's enclosing block container also carries that block's anchorable text (FR-003 is
  **per-block**, not set-membership — the 1a plan-review sharpening).

### Step 3b.4: `check_html` — verbatim carriage (the 1b harness, productionized)

- per US/FR/SC block, derive anchorable text = block body with inline markdown stripped — **import
  Phase 2's `strip_inline_markdown` from `goal_card.py`** (never a new regex);
- assert it appears verbatim and contiguous within ONE semantic container, using
  `container_text_index` (Step 3b.2) + `find()`; hit valid only inside that block's container;
- the deliberately-split-across-inline-elements self-test case carries over as a unit test.

### Step 3b.5: `check_html` — DOM + self-containment contract

- zero `id=` (no exceptions in the canonical render); zero `data-block-anchor`;
- no external `src`/`href` fetches beyond the two FR-028 sanctioned scripts; no CDN fonts;
- `data-goal-slug` present on `<body>`; a real `<h2>`/`<h3>` heading hierarchy exists.

### Step 3b.6: Write `test_maker_gate.py`

Cover for **each check** at least one pass and one violation fixture. Fixtures adapted from the Phase 1
`spikes/1a`/`1b` evidence HTML, plus minimal synthetic violators. Plus:
- an **independent `container_text_index` test class** (split-across-inline-elements, nested
  containers, whitespace fidelity) so the shared helper is proven on its own contract for 4b-1;
- golden structural assertions from `test_requirements_renderer.py` (zero-`id`) replayed against a
  passing fixture (gate↔golden consistency);
- **T1 (plan-review):** assert the live v2 deterministic render (`render_requirements()` output)
  passes `check_html` **in full**, not just the zero-`id` subset — 3c publishes the fallback *ungated*
  on the trust that the deterministic substrate is always structurally valid; this test pins that
  trust so a future renderer change can't silently make the fallback un-gateable.

## Verification

### Automated Tests (permanent)
- `pytest cast-server/tests/test_maker_gate.py` — green.
  - `check_what_doc`: ≥1 pass + ≥1 violation per dimension (front matter, totality, slot-name).
  - `check_html`: ≥1 pass + ≥1 violation per dimension (id parity, per-block correspondence,
    verbatim carriage, DOM/self-containment).
  - `container_text_index`: independent class (split inline elements, nesting, whitespace fidelity).
  - gate↔golden consistency replay.
  - **T1:** `check_html(render_requirements(...)) .passed is True` in full.

### Validation Scripts (temporary)
- One-off: run `check_html` over a Phase-1 1a evidence HTML file and print the `GateReport` to confirm
  violation strings are prompt-ready. Discardable.

### Manual Checks
- Confirm `renderer.py` does **not** import `maker_gate` (grep). Confirm `maker_gate.py` imports
  `strip_inline_markdown` from `goal_card.py` and does **not** define its own stripper.

### Success Criteria
- [ ] `maker_gate.py` is pure (no I/O/DB/LLM/subprocess imports).
- [ ] `check_what_doc` + `check_html` return the frozen `GateReport` shape with prompt-ready violations.
- [ ] `container_text_index` is public, module-level, and independently unit-tested (revision b).
- [ ] `strip_inline_markdown` is **imported**, never re-implemented (2a→3b hard edge).
- [ ] T1 passes: the live deterministic render clears `check_html` in full.
- [ ] All `test_maker_gate.py` cases green.

## Execution Notes

- **Build-order hazard:** if Phase 2's `strip_inline_markdown` isn't landed yet, do NOT proceed by
  copying it. Block on it or lift it to a shared pure module — a second stripper is drift by
  construction.
- **Known limitation (record, don't solve):** a reader-selected quote spanning inline markdown
  (`some **bold** text`) can fail the v2 source-side verbatim backstop even on the deterministic
  render — a v2-inherited edge, unchanged by this plan; note it as a Phase 4b input, NOT a Phase 3
  gate condition.
- The gate **is** the acceptance machinery for FR-003/FR-007 — it must not be rubber-stamp-tested;
  every dimension gets a real violation fixture.
- **Spec-linked files:** `maker_gate.py` is appended to the spec's `linked_files` in **3e** — no spec
  edit here.
