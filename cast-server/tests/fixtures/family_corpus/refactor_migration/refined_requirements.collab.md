---
status: refined
scope_mode: hold
confidence:
  intent: high
  behavior: high
  constraints: high
  out_of_scope: high
open_unknowns: 1
questions_asked: 0
classification:
  family: "refactor_migration"
  confidence: 0.9
  alt_family: "bug_fix"
  reasoning: "A structural change to how runtime tracking links are laid out — a per-directory singleton symlink becomes a directory of per-goal symlinks — with a migration path for the legacy layout. The shape of an existing mechanism changes; it is not a one-line defect patch."
  uncertainty_factors:
    - "A collision bug motivates it, but the work is the layout change plus a legacy migration, which is refactor/migration in shape."
  modifiers:
    irreversible: true
    unknown_cause: false
  confirmed_by: "manual"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

<!-- CORPUS-PROVENANCE: family=refactor_migration — authored from real commit b2e9661 "namespace .cast per goal so multiple goals can share one external repo". -->

# Namespace the `.cast` runtime link per goal

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** cast-server/cast_server/services/goal_service.py, cast-server/cast_server/services/agent_service.py

## Intent

**Job statement:** Change the runtime tracking link from a per-directory singleton `<ext>/.cast` symlink into a directory of per-goal symlinks `<ext>/.cast/<slug>`, so two goals sharing one external project directory no longer silently misroute each other's runtime writes — and migrate any existing bare-symlink layout in place.

Today `<ext>/.cast` is a single symlink pointing at one goal's runtime directory, recreated on every dispatch. When two goals share an `external_project_dir`, dispatching one repoints `.cast` away from the other, and the other's runtime writes land in the wrong place with no error. The change is structural: the singleton becomes a namespace. Because it rewrites an on-disk layout that older checkouts already created, it is a one-way migration and must carry the legacy case forward rather than assume a clean slate.

## Decisions

- **`.cast` becomes a directory of per-goal symlinks.** `ensure_cast_symlink` writes `<ext>/.cast/<slug> -> goals_dir/<slug>`, and migrates a legacy bare `.cast` symlink to the new directory form on first touch.
- **Removal is per-goal and self-cleaning.** `remove_cast_symlink` takes a slug, removes only that goal's link, and deletes `.cast` only when it is empty; both `update_config` callers are updated to pass the slug.
- **Dispatch resolves through the namespace.** `agent_service` dispatch and invoke tracking directories now resolve to `.cast/<slug>` rather than the bare link.

## Out of Scope

- Changing where runtime directories themselves live (`goals_dir/<slug>`) — only the link layout under the external repo changes.
- Any change to the dispatch or monitoring contract beyond the path the tracking directory resolves to.
- Backfilling links for goals that were never dispatched into the shared repo; links are created on dispatch, not eagerly.

## Open Questions

- **[OPEN]** Whether an orphaned `.cast/<slug>` link whose goal was deleted out-of-band should be garbage-collected on the next dispatch, or left until the empty-directory cleanup removes the parent.
