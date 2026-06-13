# sp2a — Parser Package (`cast_server.requirements_render`) — Output

**Status:** completed. All Detailed Steps executed, all verification run, every success criterion met.

## What was built

New self-contained package `cast-server/cast_server/requirements_render/` with five modules:

| Module | Purpose |
|--------|---------|
| `hashing.py` | `content_hash(text) -> str` — sha256 hex of UTF-8. The conflict-detection spine. Import-light (stdlib `hashlib` only); Phases 4/5 import it WITHOUT the parser. **Not** re-exported from `__init__`. |
| `spec_grammar.py` | importlib bridge re-exporting `bin/cast-spec-checker`'s six compiled regexes (`US_HEADING_RE`, `FR_ID_RE`, `SC_ID_RE`, `EARS_SCENARIO_RE`, `SECTION_HEADING_RE`, `NEEDS_CLAR_INLINE_RE`) plus `_section_spans`. No-drift, no fork. Raises `FileNotFoundError` with the path if the checker is missing. |
| `blocks.py` | `BlockKind`, `Block`, `ParsedRequirements` dataclasses — verbatim from `_shared_context.md`. `Block.ref` is in-memory only (Decision #2 comment kept). Both frozen. |
| `parser.py` | `parse_requirements(text)` / `parse_requirements_file(path)` — the Section → kind mapping. Read-only. |
| `__init__.py` | Public surface: `Block`, `BlockKind`, `ParsedRequirements`, `parse_requirements`, `parse_requirements_file`. |

## Key implementation notes (for downstream sub-phases)

- **`parents[3]` confirmed correct** — `spec_grammar.py` → repo root → `bin/cast-spec-checker` (verified by resolving at build time; the file exists there).
- **Extensionless import required two non-obvious fixes** beyond the plan's snippet:
  1. `spec_from_file_location` returns `None` for a file with no `.py` suffix → pass an explicit `SourceFileLoader`.
  2. The checker's module-level `@dataclass` needs the module registered in `sys.modules` before `exec_module` (else `cls.__module__` resolves to `None`). Registered as `"cast_spec_checker"`.
  These are the kind of thing sp4's tests should keep pinned.
- **Front matter** uses PyYAML (`yaml.safe_load`) — already a cast-server dependency (`services/goal_service.py`). Tolerant: malformed/non-dict YAML → `{}`.
- **`Block.body` is byte-faithful** — `source_text.split("\n")` then `"\n".join(slice)` reproduces the exact substring; verified equal for every block.
- **Multi-line bullet grouping (Decision #4):** a bullet block runs from its column-0 `- `/`* ` marker to the line before the next top-level marker (or section end), then trailing blank lines are trimmed. Continuation/wrapped lines AND nested (indented) sub-bullets are grouped into the same block; nested sub-bullets do NOT start a new block. Verified on a synthetic doc.
- **Unknown H2 (Decision #3):** any H2 not in the known set is appended to `unrecognized_sections` (a tuple) and emits NO block. Verified `## Appendix` → `unrecognized_sections == ('Appendix',)`.
- **`_section_spans`** is reused from the checker when exposed (it is); a byte-identical inlined fallback exists for safety.

## Verification results

Live goal file (`goals/refine-requirements-v2/refined_requirements.collab.md`) block counts — **exact match** to the pinning sp4 will assert:

```
intent: 1   user_story: 7   fr: 20   sc: 6
constraint: 7   scope: 6   directional: 1   open_question: 6
unrecognized_sections: ()
```

- Line ranges all in-bounds `[1, 375]` and monotonically source-ordered.
- `content_hash` stable across calls; `content_hash("") == e3b0c44298fc…` (known empty-string sha256).
- Title and preamble (the spec-maturity blockquote) extracted correctly; front matter parsed to the nested `confidence` dict.
- Missing-checker path raises `FileNotFoundError` carrying the expected path.

Manual checks:
- `git diff --stat bin/cast-spec-checker` → empty (checker untouched).
- No DB import anywhere in the package.
- `parser.py` has no write call (read-only).
- `blocks.py` has no anchor/element-ID field (the only "anchor" mentions are the Decision-#2 comments stating `ref` is *not* an anchor).

## Out of scope (left for the named sub-phases)

- No test files authored — sp4 owns `test_requirements_parser.py`, `test_fr007_readonly_guard.py`, `test_requirement_versions.py`.
- No DB/schema/service code — sp2b / sp3.

## Downstream contract reminders

- `content_hash` import path for Phases 4/5: `from cast_server.requirements_render.hashing import content_hash` (deliberately parser-free).
- `sp3`'s version service will compute `content_hash(content)` via this exact function.
- sp4 can rely on the pinned counts above against a FROZEN fixture copy of the goal file.
