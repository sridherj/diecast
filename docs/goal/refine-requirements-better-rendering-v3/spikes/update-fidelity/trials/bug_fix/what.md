---
contract: cast-requirements-what/v1
goal_slug: spike-bug_fix
family: bug_fix
source_hash: 049fd854a84419abc01cfecaeb58fecfa92ddfb7820be00a5912b3d1b719e369
sections:
  - title: What's leaking onto the first screen a reader sees
    outcome: >-
      L1 — The Goal Card, the one above-the-fold surface a first-time reader meets, prints
      literal markdown syntax (`**bold**`, backtick-code, `_emphasis_`) instead of formatted
      prose, so the very first impression is raw source like `Replace the **plain** render`
      rather than a clean sentence. The fix routes the job statement, the L2 assertions, and
      the kicker line through the same inline-markdown path the recipe sections already use.
      L2 — The defect is data-dependent (a source with no inline markdown looks fine, which is
      why it slipped past the golden snapshot); "fixed" means zero literal `*` / `` ` `` / `_`
      characters survive into the rendered card.
    block_refs: [FR-001, FR-002, SC-001, SC-004]
  - title: What the fix is not allowed to break
    outcome: >-
      L1 — This is a narrow, contained fix: it must preserve the thin-spine DOM contract — no
      element `id=`, no `data-block-anchor` — that the comment-and-version layer anchors
      against, which forces inline-only conversion (a renderer that emits header ids would
      violate it). L2 — A markdown-free source must render byte-identical to today so the
      change is invisible except where it fixes the leak, protecting existing golden snapshots;
      verified by grepping the regenerated markup and a golden-snapshot diff. A sibling
      sentence-splitter defect lives one call deeper in the same file and is named only so a
      fixer does not conflate it — it is deliberately out of scope here.
    block_refs: [FR-003, FR-004, SC-002, SC-003]
unmapped_refs: []
gaps: []
---

## What's leaking onto the first screen a reader sees

**L1 takeaway:** The Goal Card has one job above all others — let a reader grasp the job, outcome, and scope in seconds from the card alone — and during v2 dogfooding it betrayed that job by printing raw markdown syntax. The reader's first impression was `Replace the **plain** deterministic render`, asterisks and all. The fix makes the job statement, every L2 assertion, and the kicker line resolve inline markdown through the shared `_md_to_html` path the recipe sections already use, so `**bold**`, `` `code` ``, and `_emphasis_` render as formatted text.

**L2 supporting points:**
- The leak is real and observed on this goal's own render — backtick and asterisk characters showed up in assertions drawn from Success-Criteria rows.
- The defect is *data-dependent*: a source carrying no inline markdown looks correct, which is exactly why it escaped the golden-HTML snapshot until an author used emphasis. The reader takeaway is that "looks fine on my fixture" was never proof.
- The success bar is concrete and reader-facing: a card built from a source with `**bold**`, `` `code` ``, and `_emphasis_` shows formatted text with *zero* literal markdown characters visible — including in the kicker line directly above the assertions.

**Source content that carries this:** Intent ("Job statement" and the SC-001 framing of the card's one job); FR-001 (job statement through `_md_to_html`, reusing the shared instance); FR-002 (assertions and kicker resolve inline markdown, staying a single contiguous `<li>`; the "no markdown wrapper" comment *is* the bug); SC-001 (formatted text, no literal markdown); SC-004 (kicker line specifically).

## What the fix is not allowed to break

**L1 takeaway:** This is a narrow defect with a known cause and a known surface, and the riskiest thing about it is the blast radius, not the change itself. The reader must walk away trusting that the fix touches only the Goal Card emit path: it preserves the thin-spine DOM contract — no `id=`, no `data-block-anchor` — that the comment-and-version layer depends on, and it leaves every markdown-free render byte-identical to today.

**L2 supporting points:**
- Inline-only conversion is *required*, not incidental: a markdown renderer that emitted header ids would violate the thin-spine contract. The constraint shapes the implementation.
- "Invisible except where it fixes the leak" is the explicit safety property — markdown-free fixtures must produce identical output, protecting the existing golden snapshots.
- Both guardrails are independently verifiable: grep the regenerated card for `id=` / `data-block-anchor`, and run a golden-snapshot diff on an emphasis-free fixture.
- One honest boundary: a sibling sentence-splitter defect (`_first_sentence` truncating at `e.g.` / `v2.`) sits in the same file and is *named but out of scope*, tracked separately so a fixer doesn't conflate the two.

**Source content that carries this:** FR-003 (no `id=` / `data-block-anchor`; inline-only conversion); FR-004 (byte-identical output for markdown-free sources); SC-002 (grep the markup); SC-003 (golden-snapshot diff); plus the Evidence section's named-but-deferred sentence-splitter note.
