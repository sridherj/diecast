# Sub-phase 2a: Parser Package — `cast_server.requirements_render`

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase1/_shared_context.md` before starting.

## Objective

Build the core deliverable of Phase 1: the `requirements_render` package that turns a
`refined_requirements.collab.md` file into an ordered, typed block model (`ParsedRequirements`), plus the
tiny canonical `content_hash` used as the conflict-detection spine in Phase 5. The grammar is **not
reinvented** — it is bridged from `bin/cast-spec-checker` via importlib so the parser can never drift
from the FR-007 checker. This package is read-only: it never writes the file.

## Dependencies

- **Requires completed:** sp1 (the design note is the contract this implements).
- **Assumed codebase state:** `bin/cast-spec-checker` exists and is import-safe (module level = regex +
  dataclass defs, stdlib only). `cast-server/cast_server/` is an importable package.
- **Runs in parallel with sp2b** (disjoint files — sp2a touches only the new `requirements_render/`
  package; sp2b touches `db/` + the migration test).

## Scope

**In scope:**
- New package `cast-server/cast_server/requirements_render/` with five modules: `__init__.py`,
  `spec_grammar.py`, `blocks.py`, `parser.py`, `hashing.py`.
- The typed model (`BlockKind`, `Block`, `ParsedRequirements`) per the verbatim schema in `_shared_context.md`.
- The importlib grammar bridge re-exporting the checker regexes.
- `parse_requirements(text)` and `parse_requirements_file(path)` implementing the Section → kind mapping.
- The `content_hash(text)` one-liner in its own import-light module.

**Out of scope (do NOT do these):**
- Any DB code, schema, or service (sp2b / sp3).
- Any test file (sp4 owns `test_requirements_parser.py`, `test_fr007_readonly_guard.py`,
  `test_requirement_versions.py`). *Exception:* you MAY run an ad-hoc REPL/`python -c` parse against the
  live goal file to sanity-check while developing, but commit no test.
- Editing `bin/cast-spec-checker` in any way (not one byte).
- Any `ref`/anchor field that gets persisted, any `block_anchor`, any per-element ID. `Block.ref` is
  in-memory only.
- Making `blocks` tile the whole file. Blocks are landmarks; the gaps live in `source_text`.

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/requirements_render/__init__.py` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/spec_grammar.py` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/blocks.py` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/parser.py` | Create | Does not exist |
| `cast-server/cast_server/requirements_render/hashing.py` | Create | Does not exist |

## Detailed Steps

### Step 2a.1: First, read the checker to learn the real regex names

Before writing the bridge, open `bin/cast-spec-checker` and confirm the **actual** module-level names of
its compiled regexes and its `_section_spans` helper. The plan lists `US_HEADING_RE`, `FR_ID_RE`,
`SC_ID_RE`, `EARS_SCENARIO_RE`, `SECTION_HEADING_RE`, `NEEDS_CLAR_INLINE_RE` — verify each exists with
that exact name. If a name differs, re-export under the plan's canonical name with an aliasing assignment
AND leave a comment noting the source name, so downstream code uses the canonical name. Confirm the file
is import-safe (no top-level `argv` parsing / side effects that run on import — `cast-spec-checker` is
documented "Internal use", module level is defs).

### Step 2a.2: `hashing.py` (write this first — it has zero internal deps)

```python
"""Canonical content hashing for the requirements thin spine.

Deliberately tiny and import-light: Phases 4 and 5 import this WITHOUT importing the parser.
Phase 5 conflict detection MUST use this exact function — never reimplement sha256 elsewhere.
"""
import hashlib


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
```

### Step 2a.3: `spec_grammar.py` — the no-drift importlib bridge

```python
"""Single grammar source: re-export bin/cast-spec-checker's compiled regexes.

The checker is the canon for the FR-007 spec-kit shape. Loading its regexes (instead of copying them)
guarantees the parser can never drift from the checker. The checker file is NEVER modified.
"""
import importlib.util
from pathlib import Path

_CHECKER_PATH = Path(__file__).resolve().parents[3] / "bin" / "cast-spec-checker"
if not _CHECKER_PATH.exists():
    raise FileNotFoundError(f"spec-kit grammar source not found: {_CHECKER_PATH}")

_spec = importlib.util.spec_from_file_location("cast_spec_checker", _CHECKER_PATH)
_checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_checker)

US_HEADING_RE = _checker.US_HEADING_RE
FR_ID_RE = _checker.FR_ID_RE
SC_ID_RE = _checker.SC_ID_RE
EARS_SCENARIO_RE = _checker.EARS_SCENARIO_RE
SECTION_HEADING_RE = _checker.SECTION_HEADING_RE
NEEDS_CLAR_INLINE_RE = _checker.NEEDS_CLAR_INLINE_RE
# Reuse the checker's section-span algorithm if it exposes one (verify the name in the checker):
_section_spans = getattr(_checker, "_section_spans", None)
```

- **Verify `parents[3]`**: `__file__` is
  `cast-server/cast_server/requirements_render/spec_grammar.py`. `parents[0]` = `requirements_render/`,
  `[1]` = `cast_server/`, `[2]` = `cast-server/`, `[3]` = repo root. So `parents[3] / "bin" /
  "cast-spec-checker"` is correct **iff** the repo root is the parent of `cast-server/`. Confirm by
  printing `_CHECKER_PATH` once during development and checking it resolves to the real file. Adjust the
  index only if the directory depth differs — do not guess.
- A `spec_from_file_location` on a file without a `.py` extension works (the loader is explicit); the
  module name `"cast_spec_checker"` is arbitrary and internal.

### Step 2a.4: `blocks.py` — the typed model

Copy the `BlockKind` / `Block` / `ParsedRequirements` definitions **verbatim** from `_shared_context.md`
(Data Schemas & Contracts). Keep the inline comment on `ref` exactly: "parsed in-memory only; never
persisted to a DB column, never used as a comment anchor" (plan-review Decision #2). Both dataclasses are
`@dataclass(frozen=True)`.

### Step 2a.5: `parser.py` — the two entrypoints + Section → kind mapping

- Module docstring states the deliberate non-goals (blocks do NOT tile the file; inline `[NEEDS
  CLARIFICATION]` stays inside its `USER_STORY` body; **this is a render model, NOT a comment-anchoring
  index**).
- `parse_requirements(text: str) -> ParsedRequirements`:
  1. Split front matter (YAML between leading `---` fences) → `front_matter` dict. Use a minimal YAML
     parse; if PyYAML is already a dependency, use it, else a tolerant key:value parse is acceptable for
     the simple header (status/confidence/...). Confirm whether PyYAML is available before choosing.
  2. Extract `title` (the H1 text) and `preamble` (the blockquote between H1 and the first H2).
  3. Compute section spans from `SECTION_HEADING_RE` (reuse `_section_spans` if exposed — same algorithm
     as the checker), giving `(heading_text, start_line, end_line)` per H2.
  4. For each section, dispatch on the heading per the Section → kind mapping table in `_shared_context.md`.
     Emit `Block`s with byte-faithful `body` slices and correct `level`, `heading`, `ref`,
     `line_start`/`line_end` (1-indexed, within file bounds, monotonically ordered in source order).
  5. Any H2 whose heading matches none of the known sections → append its exact heading text to
     `unrecognized_sections` (a tuple; **never silently drop it**). Emit NO block for it.
  6. `source_text` = the full original text untouched; `content_hash` = `hashing.content_hash(source_text)`.
- `parse_requirements_file(path: Path) -> ParsedRequirements`: read the file (text, UTF-8), call
  `parse_requirements`. **Never writes.** No `open(..., "w")`, no temp rewrite — read-only.
- **Multi-line bullet grouping** (sp4 Decision #4 will test this): a bullet block spans from its `- `
  marker line through all continuation/wrapped lines AND nested sub-bullets, up to the next top-level
  marker or section end. A nested sub-bullet does NOT start a new block. Get this right now or sp4's test
  will catch a first-line-truncation bug.

### Step 2a.6: `__init__.py` — the public surface

```python
from .blocks import Block, BlockKind, ParsedRequirements
from .parser import parse_requirements, parse_requirements_file

__all__ = [
    "Block", "BlockKind", "ParsedRequirements",
    "parse_requirements", "parse_requirements_file",
]
```
(`content_hash` is intentionally NOT re-exported here — Phases 4/5 import it directly from
`requirements_render.hashing` to keep that import path light and parser-free.)

## Verification

### Automated Tests (permanent)
- None authored in this sub-phase — sp4 owns all parser tests. This keeps sp2a and sp4 on disjoint files
  and lets sp2a and sp2b run in parallel. (sp4 is where `pytest cast-server/tests/test_requirements_parser.py`
  proves the block counts: 1 Intent, 7 UserStory, 20 FR, 6 SC, 7 Constraint, 6 Scope, 1 Directional,
  6 OpenQuestion.)

### Validation Scripts (temporary — run during development, commit nothing)
- Import smoke (run from the cast-server package root so imports resolve):
  ```bash
  cd cast-server && python -c "
  from cast_server.requirements_render import parse_requirements_file
  from cast_server.requirements_render.hashing import content_hash
  from cast_server.requirements_render import spec_grammar as g
  print('grammar ok:', bool(g.US_HEADING_RE.match('### US1 — Foo')))
  pr = parse_requirements_file(__import__('pathlib').Path('../goals/refine-requirements-v2/refined_requirements.collab.md'))
  from collections import Counter
  print(Counter(b.kind.value for b in pr.blocks))
  print('unrecognized:', pr.unrecognized_sections)
  print('hash:', pr.content_hash[:12], 'len_source:', len(pr.source_text))
  "
  ```
- Eyeball that the counts are in the right ballpark (1 intent / 7 user_story / 20 fr / 6 sc / 7 constraint
  / 6 scope / 1 directional / 6 open_question). Exact pinning is sp4's job, but if a kind is wildly off
  (e.g. 0 fr), the mapping is wrong — fix before handing to sp4.
- `content_hash("")` and `content_hash` of the file are stable across two calls.

### Manual Checks
- `bin/cast-spec-checker` is byte-identical to before (`git diff --stat bin/cast-spec-checker` shows nothing).
- `Block` has no anchor/element-ID field; `requirements_render/` contains no DB import.
- `parse_requirements_file` contains no write call (`grep -n "open(" parser.py` shows read-mode only, or none).

### Success Criteria
- [ ] All five modules exist and import cleanly from the `cast-server/` package root.
- [ ] `spec_grammar` re-exports the six named regexes; missing checker raises `FileNotFoundError` with the path.
- [ ] Parsing the live goal file yields blocks of every expected kind, source-ordered, with in-bounds
      `line_start`/`line_end`, and `unrecognized_sections` is a tuple (empty for the clean fixture).
- [ ] `content_hash` lives in `hashing.py` and is stable/deterministic.
- [ ] `bin/cast-spec-checker` unchanged; no DB code in the package; parser never writes.

## Execution Notes

- **`parents[3]` is the single most likely bug.** Print the resolved checker path once and confirm it
  hits the real file before moving on. If `cast-server` nesting differs from the assumption, fix the index.
- The checker is import-safe by design ("Internal use", module-level defs). If importing it ever executes
  CLI code, that's a checker regression — raise it as a flag, do NOT add a guard that forks the grammar.
- Front-matter parsing: prefer reusing whatever the rest of cast-server uses for `.collab.md` headers
  (grep for existing front-matter handling) before hand-rolling, to stay consistent.
- Keep `hashing.py` dependency-free forever — Phases 4/5 rely on importing it without the parser.
- **Spec-linked files:** none. This sub-phase creates a brand-new package covered by no spec.
