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
  family: "bug_fix"
  confidence: 0.95
  alt_family: "refactor_migration"
  reasoning: "A scoped defect in an existing, shipped renderer: the Goal Card prints raw markdown syntax instead of formatted text. Known cause, known surface, narrow fix."
  uncertainty_factors: []
  modifiers:
    irreversible: false
    unknown_cause: false
  confirmed_by: "manual"
  classified_at: "2026-06-12"
  taxonomy_version: 1
---

<!-- CORPUS-PROVENANCE: family=bug_fix — authored from the real v2 dogfooding defect: goal_card.py / renderer.py raw-markdown leak (spikes/1a). -->

# Goal Card leaks raw markdown onto the zero-click surface

> **Spec maturity:** draft
> **Version:** 0.1.0
> **Linked files:** cast-server/cast_server/requirements_render/goal_card.py, cast-server/cast_server/requirements_render/renderer.py

## Intent

**Job statement:** Stop the Goal Card from printing literal markdown syntax — `**bold**`, backtick-code, and `_emphasis_` — so the one above-the-fold surface a first-time reader sees reads as clean prose instead of source.

The refined-requirements render has one job above all others: a reader who opens a goal grasps the job, the outcome, and the scope in seconds, from the Goal Card alone (this is SC-001). During v2 dogfooding the card betrayed that job. The job statement and the 3–5 L2 assertions are emitted through `escape()` only — never through the markdown renderer — so any inline markdown an author wrote in the Intent or Success-Criteria cells survives to the screen as raw syntax. A reader's very first impression is `Replace the **plain** deterministic render`, asterisks and all. The fix is narrow and contained to the Goal Card emit path; it must not regress the deliberate thin-spine DOM contract (no `id=`, no `data-block-anchor`) that the comment layer depends on.

## Evidence

The leak is in two emit sites in `renderer.py`, both fed by the pure heuristics in `goal_card.py`:

- **The job statement.** `renderer._render_goal_card` builds `job_html` as `f'<p ...>{escape(job_statement)}</p>'`. `escape()` HTML-escapes but does not interpret markdown, so a `**Job statement:** Replace the **plain** render` source line renders the inner `**plain**` verbatim as four asterisks around the word.
- **The L2 assertions.** `_render_assertions` emits each assertion as `f'<li ...>{escape(a)}</li>'` with an explicit code comment, "no markdown wrapper." Success-Criteria cells routinely contain backtick-wrapped identifiers (`refined_requirements.html`, `GET /goals/{slug}/render`) and `_emphasis_`; all of it leaks.

Observed on this very goal's own render: the `new_initiative` Goal Card shows backtick and asterisk characters in the assertions drawn from its Success-Criteria rows. The defect is data-dependent — a source with no inline markdown looks fine — which is exactly why it escaped the golden-HTML snapshot until an author used emphasis.

A sibling sentence-splitter defect lives one call deeper: `goal_card._first_sentence` splits on `(?<=[.!?])\s+`, so a job statement containing `e.g.` or `v2.` is truncated at the abbreviation. It is **out of scope here** (tracked separately) but named so a fixer does not conflate the two while in the same file.

## Functional Requirements

| ID | Requirement | Notes |
|----|-------------|-------|
| FR-001 | The Goal Card job statement is rendered through the same inline-markdown path the recipe sections already use (`_md_to_html`), so `**bold**`, `` `code` ``, and `_emphasis_` resolve to formatted HTML instead of literal syntax. | Reuse the existing shared markdown instance; do not add a second renderer. |
| FR-002 | Each L2 assertion on the Goal Card resolves inline markdown the same way, while staying a single contiguous `<li>` with no fragmenting spans. The kicker line directly above the assertions resolves inline markdown the same way. | The "no markdown wrapper" comment is the bug, not the contract. |
| FR-003 | The fix introduces no element `id=` and no `data-block-anchor` anywhere on the Goal Card, preserving the thin-spine DOM contract the comment-and-version layer anchors against. | A markdown renderer that emits header ids would violate this — inline-only conversion is required. |
| FR-004 | A render whose source contains no inline markdown produces byte-identical Goal Card output to today, so the change is invisible except where it fixes the leak. | Protects the existing golden snapshots for markdown-free fixtures. |

## Success Criteria

| ID | Criterion | How verified |
|----|-----------|--------------|
| SC-001 | The Goal Card of a source containing `**bold**`, `` `code` ``, and `_emphasis_` renders formatted text with zero literal markdown characters visible. | Render a fixture carrying inline markdown; assert no stray `*` / `` ` `` / `_` in the Goal Card HTML text. |
| SC-002 | No `id=` and no `data-block-anchor` appear anywhere in the regenerated Goal Card markup. | Grep the rendered Goal Card section. |
| SC-003 | A markdown-free source renders a byte-identical Goal Card to the pre-fix output. | Golden-snapshot diff on an emphasis-free fixture. |
| SC-004 | The kicker line above the Goal Card assertions renders inline markdown with zero literal markdown characters visible. | Render a fixture whose kicker carries backtick-code and assert no backticks survive. |

## Open Questions

