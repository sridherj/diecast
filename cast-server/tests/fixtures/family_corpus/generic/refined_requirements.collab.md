---
status: refined
scope_mode: hold
confidence:
  intent: medium
  behavior: low
  constraints: low
  out_of_scope: low
open_unknowns: 3
questions_asked: 0
classification:
  family: "generic"
  confidence: 0.45
  alt_family: "data_analysis"
  reasoning: "A genuinely cross-cutting note that mixes a little investigation, a little cleanup, and a little documentation — it does not settle into any one family, so it lands in the model-selected generic fallback rather than being coerced."
  uncertainty_factors:
    - "Reads partly like data_analysis (figure out what's going on), partly like refactor_migration (tidy the layout), partly like a captured idea — no single family dominates."
    - "Low confidence by construction: this is the unmatched-fallback representative."
  modifiers:
    irreversible: false
    unknown_cause: false
  confirmed_by: "manual"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

<!-- CORPUS-PROVENANCE: family=generic — authored from a real ambiguous capture during v3 work: the recurring confusion about what each runtime directory (.cast/ vs build/ vs goals/) is actually for. Deliberately family-ambiguous to exercise the unmatched-fallback path. -->

# Untangle what each runtime directory is actually for

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** (several, unsettled)

## Intent

**Job statement:** Pin down — and then write down somewhere durable — what each of the runtime directories the system uses is actually for, because the boundaries between `.cast/`, `build/`, and `goals/` keep surprising me mid-task and I lose time rediscovering them.

I keep tripping over this and it is not clearly any one kind of work. Part of it is investigation: trace where render jobs, tracking symlinks, and goal artifacts each land, and confirm it against the code rather than my memory. Part of it is cleanup: if two of these overlap or a path is computed in more than one place, that is worth straightening. Part of it is just documentation: even if nothing changes, a single paragraph that says "`.cast/` is per-goal runtime tracking links, `build/` is non-goal non-CI scratch, `goals/<slug>/` is canonical artifacts" would save the next confused moment. I do not know yet whether the right output is a doc, a refactor, or just a note to myself — which is exactly why this does not fit a tidy family. It is a real, recurring friction worth capturing before it dissolves into "I'll just remember next time," which I won't.

## Open Questions

- **[OPEN]** Is the right deliverable a short reference doc, a refactor that removes an overlap, or both — and does that decision change which family this even is?
- **[OPEN]** Are there more than three runtime areas in play (does the alembic/migration scratch or the test fixtures dir count), or are those clearly out of this scope?
- **[OPEN]** Who else trips over this — is it just me, or is it worth a shared note in the repo rather than a personal one?
