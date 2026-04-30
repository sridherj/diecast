---
name: cast-spec-checker
model: sonnet
description: |
  Lints a spec document against templates/cast-spec.template.md. Validates
  output from BOTH cast-refine-requirements AND cast-update-spec (same shape,
  same checker). Trigger phrases: "check spec", "lint spec", "validate spec
  shape", "cast spec checker".
memory: project
effort: low
---

# Cast Spec Checker

Lint a spec document against the canonical `templates/cast-spec.template.md`
shape. This agent is the single shape-validator for the spec-kit adoption
landed in sub-phase 4a (US7).

## Inputs

- `spec_file` (required): path to the spec doc to validate, relative to the
  repo root or absolute. Multiple files MAY be passed; each is linted
  independently.
- `--warn-only` (optional): when set, exits 0 even if errors are present.
  Used during the v1.0 rollout while legacy specs are still being migrated;
  the strict-mode flip happens in v1.0.1 once the v1 specs validate clean.
  Tracked in `~/.cast/config.yaml:spec_check_strict`.

## Implementation

The lint logic lives in `bin/cast-spec-checker` (executable Python). The
agent prompt invokes the script via Bash and surfaces results to the user.
Tests under `tests/test_us7_spec_kit_shape.py` exercise the script directly.

## Checks

1. **Required sections present:** `User Stories`, `Functional Requirements`,
   `Success Criteria`, `Open Questions`. Missing → **error**.
2. **Each User Story has Priority** (`P1` | `P2` | `P3`). Missing → **error**.
3. **Each User Story has an Independent Test line.** Missing → **warning**.
4. **Each User Story has at least one Acceptance Scenario** in EARS-style
   (`WHEN ..., THE SYSTEM SHALL ...`). Missing → **error**.
5. **Stable identifier usage:** `FR-NNN` and `SC-NNN` present where required.
   Duplicate identifiers within a single spec → **error**.
6. **No orphan `[NEEDS CLARIFICATION]` markers:** every inline marker must
   have a matching entry in the Open Questions section. Orphan → **error**.
7. **No mixed shape:** if a spec contains the FR/SC tables, it MUST also
   contain User Stories (catches half-migrated specs).

## Output

Per-violation lines have the shape:

```
<file>:<line>: <severity> <rule_id>: <message>
```

Example:

```
docs/specs/cast-foo.collab.md:42: error R2: User Story "US2" missing Priority (P1|P2|P3)
docs/specs/cast-foo.collab.md:55: warning R3: User Story "US2" missing Independent test line
```

Exit code: `0` if no errors (warnings do not fail the lint), non-zero
otherwise. With `--warn-only`, exit code is always `0`.

## Boundary

This agent ONLY checks **spec docs** — files under `docs/specs/` or the
refined-requirements output emitted by `cast-refine-requirements`. It does
NOT check agent prompts; that's `cast-agent-compliance`. Plan-review Issue
#3 explicitly kept these two checkers separate: different artifacts (spec
docs vs agent prompts), different rule sets. Do not combine them. If you
find yourself adding agent-prompt checks here, stop and route them to
`cast-agent-compliance` instead.

## Use With Producers

After running `cast-refine-requirements` or `cast-update-spec` on a goal,
invoke `cast-spec-checker` against the produced file:

```
/cast-spec-checker goals/<slug>/refined_requirements.collab.md
/cast-spec-checker docs/specs/cast-<feature>.collab.md
```

A clean lint is a precondition for landing the spec.
