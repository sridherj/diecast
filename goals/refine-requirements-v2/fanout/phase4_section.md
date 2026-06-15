## Phase 4: Iteration — Annotation & Versioning Engine
**Outcome:** Reviewers (human or agent) leave **block-anchored** comments with an open/resolved
lifecycle and retained trail; unresolved comments mark the spec unconverged and drive new versions;
each new version emits a deterministic **block-level change summary**; only the current version lives
in the goal folder, older versions archived in the DB with comments intact. Built **API-first** so an
agent uses the same door as the human UI.
**Dependencies:** Phase 1 (thin spine + version/comment schema) + Phase 3a (selectable DOM to capture
quotes from).
**Estimated effort:** 3-4 sessions
**Verification:** A single dual-assertion test proves **agent parity** (one handler returns JSON to a
header-less call, HTML fragment to an `HX-Request` call). A comment left on a quote in v2 is re-located
to the right place after an unrelated edit by the re-anchor subagent, and becomes `orphaned` (not lost)
when its quote genuinely no longer exists. A spec with any open comment reports `unconverged`; the next
version flips it to `converged`. `find cast-server -name package.json` stays empty (no framework added).

Key activities:
- **Build the comment API *before any UI*** (the FR-013 forcing function): `comment_service.py` +
  `POST/GET …/comments`, `POST …/comments/{id}/resolve`, content-negotiated on `HX-Request` (JSON for
  agents, HTML fragment for HTMX) — the exact pattern already in `api_agents.py`. `author_kind` is the
  *only* human-vs-agent distinction; **no privileged UI write path.**
- **Store comments by quote, re-locate by subagent** (the thin-spine decision): a comment row holds the
  `quoted_text` + `section_hint` + `version` it was left against — **no stored block anchor.** On
  display against a changed file, a **Claude re-anchor subagent** finds where each open comment now
  belongs from its quote; an unfindable quote → `orphaned`, surfaced for triage (never silently lost).
  This is the deliberate trade: less determinism, far less machinery, intelligence handles drift.
- **Ship a ~150-line vanilla-JS comment layer** over the selectable DOM (selection → capture quote +
  nearest heading → popover → `hx-post`), wired on `htmx:afterSwap`. **No React, no annotation
  library.**
- **Keep the editable textarea + re-anchor on save** (resolves the human-edit-model question): a human
  whole-file edit is allowed; on save, the re-anchor subagent re-locates open comments against the new
  text. No need to forbid free-text editing — the subagent absorbs the drift.
- **Version snapshot + comment carry-over:** `create_next()` gates on open-comment count (open ⇒
  unconverged), snapshots the current file to a new `version` (with its content hash), marks the prior
  archived. Open comments carry forward and are re-located by quote; unfindable → `orphaned`. Only the
  current version's files land in the goal folder (FR-011).
- **Change summary (FR-017):** diff the parsed blocks of two version snapshots
  (`added/removed/modified/unchanged`, matched by heading + content) — the structural diff is the
  source of truth; a Claude subagent may *narrate* it into prose but never *invent* it. **Build this
  reusable — Phase 5 consumes the same engine.**
- **Archive retrieval (US5 S3):** an archived version returns *with* its comments and resolution state
  (the append-only `comment_events` trail makes this free).

---
