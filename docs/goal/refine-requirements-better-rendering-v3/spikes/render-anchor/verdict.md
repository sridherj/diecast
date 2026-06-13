# Sub-phase 1b — Render-Anchor Dry-Run: Verdict & Migration Sizing

> **Read-only spike.** No production code edited (`cast-server/` + `agents/` untouched by this run —
> the dirty tree predates it, from prior phases). The render-space resolver prototyped here is
> productionized in **Sub-phase 2**, not here. This verdict **sizes** the sp2 migration; it does not
> re-open the (locked) anchoring decision.

## What was measured

The exact render-space procedure sp2's migration + creation path will productionize, run against the
**published render text** (not the `.collab.md`):

1. `idx = container_text_index(render_html)` — the **shared** byte-faithful walker (`maker_gate.py:259`),
   imported, never re-walked. `idx.find(quote)` is JS `concat.indexOf` parity (`requirements_comments.js`).
2. **Place:** `idx.find(quoted_text) >= 0`.
3. **Bridge:** `idx.unit_at(offset)` (`maker_gate.py:175`) → the innermost enclosing requirement-unit
   container; the single canonical anchor label visible in that unit (`_ID_RE` + `_norm_ref`, the same
   scan `check_html` bridges with) **is** the `block_ref`.
4. **Classify a miss:** cross-boundary / decoration-spanning / no-anchor-label (ref-less → NULL by
   construction).

`grep -c "container_text_index\|unit_at"` over the harness = **7**; the harness defines no walker and no
stripper of its own (single-implementation discipline held).

## Corpus (grounded, honestly bounded)

- **Production DB (`~/.cast/diecast.db`) carries ZERO comments**, and there are **no live v3-goal
  comments**. The only existing comments on disk are the prior-spike-seeded reviewer/maker corpus
  (`spikes/1b/scratch.sqlite`, goal `spike-1b-anchor-survival`) — realistic human-reviewer + maker-agent
  comments minted by selecting **rendered** text, the faithful stand-in for the v2 fixture pair.
- Their **current** stored `quoted_text` is the post-reanchor (v2-space) quote, so the **published
  render** validated against is `spikes/1b/feature-maker-v2.html` (a ref-bearing render carrying the
  full `US1/US2/FR-001..005/SC-001..003` anchor-label set in `*-unit` containers).
- **6 existing comments**: **5 open**, 1 already-terminal `orphaned`.

## Real-comment results (the placement / bridge rate)

| # | state | placed | block_ref | quote (clip) |
|---|-------|--------|-----------|--------------|
| 1 | open | ✅ | **US1** | "stakeholders receive the report on schedule…" |
| 3 | open | ✅ | **SC-003** | "lists runs newest-first with a status badge…" |
| 4 | open | ✅ | **FR-005** | "read-only history of the last fifty export runs" |
| 5 | open | ✅ | **FR-004** | "the report owner" |
| 6 | open | ✅ | **FR-001** | "accept a cron-style cadence expression…" |
| 2 | orphaned | ❌ not-on-render | NULL | "retain the three most recent export artifacts…" (already terminal-orphaned; correctly does not place) |

Every open comment places **and** resolves a **unique** `block_ref`. The lone non-placement is the
comment that was *already* orphaned by a prior reanchor — its non-placement is the expected, correct
signal (it is not an open comment and is not in the placement denominator).

## Resolver-classification probes (synthetic, read-only — gate the classifier, not the corpus)

The real corpus is entirely ref-bearing, so it never exercises the ref-less / cross-boundary /
decoration branches sp2's **creation** path must handle. Three quotes drawn **verbatim from the same
render** (never counted in the placement rate) pin each branch:

| probe (quote source) | expected | got | block_ref |
|----------------------|----------|-----|-----------|
| ref-less unit — "Not now" `<li>` bullet | `no-anchor-label` | ✅ `no-anchor-label` | **NULL by construction (SUCCESS)** |
| cross-boundary — FR-001→FR-002 span | `cross-boundary` | ✅ `cross-boundary` | **NULL (never guessed)** |
| decoration-spanning — hero title, outside every unit | `decoration-spanning` | ✅ `decoration-spanning` | **NULL** |

3/3 probes classify as designed — confirming sp2 can trust: a ref-less-render quote → `block_ref=NULL`
is a **placed success** (plan-review Decision #1), and a cross-boundary quote → `block_ref=NULL`
**never guessed** (orphan-over-guess at the resolver layer).

## Migration sizing (what Sub-phase 2 consumes)

`changed-set` against the **current** published render, per existing comment:

- **#flip-to-render = 5** — every open comment places cleanly and resolves a unique `block_ref`; sp2
  migrates each to `anchor_space='render'` with its resolved `block_ref` (US1, SC-003, FR-005, FR-004,
  FR-001). Zero re-render or re-anchor work needed for these.
- **#stay-source (badge) = 1** — the already-`orphaned` comment does not place on the current render;
  sp2 leaves it in its terminal state, **flagged** (surface-don't-suppress), never silently dropped or
  force-migrated.
- **#ref-less-NULL-by-construction = 0 (real corpus)** — no comment here landed on a ref-less unit.
  **The path is proven** by the ref-less probe: on a `pilot_poc` / `random_idea` page (zero anchor
  labels by design) **every** comment migrates with `block_ref=NULL` as a normal placed comment — the
  migration + displacement detector must treat that NULL as success, never an unplaced miss to
  retry/badge.

No "mysterious" (unclassified) miss occurred: every non-placement and every probe carries a concrete
`miss_class`.

```
VERDICT: PASS
PLACEMENT_RATE: 5/5
BLOCK_REF_UNIQUE_RATE: 5/5
MISS_BREAKDOWN: cross-boundary=0, decoration-spanning=0, no-anchor-label=0   (real open comments; all placed in-block)
RESOLVER_PROBES: 3/3 (ref-less→NULL-by-construction, cross-boundary→NULL-never-guessed, decoration-spanning→NULL)
MIGRATION_SIZING: flip-to-render=5, stay-source(badge)=1, ref-less-NULL-by-construction=0 (real; path proven by probe)
```

## Carry-forward into Sub-phase 2

- The render-space resolver (`find` → `unit_at` → single-`_ID_RE`-label = `block_ref`) productionizes
  **verbatim** in sp2's creation + migration path; reuse the shared walker, never a second one.
- Miss classification carries forward verbatim: cross-boundary → `block_ref=NULL` (never guessed);
  ref-less render → `block_ref=NULL` **by construction** (success, not a miss — and **not** an unplaced
  badge).
- A non-placing comment migrates as **stay-source + flagged**, never force-fit to a render anchor.
- **No browser** was driven (autonomous-run convention): the visual confirmation that a UI-minted quote
  highlights is a static verdict + human-eyeball carry-forward, never a blocking gate. The Python
  `container_text_index.find` re-implementation **is** the placement check `requirements_comments.js`
  performs on the live DOM.

## Reproduce

```
python3 docs/goal/refine-requirements-better-rendering-v3/spikes/render-anchor/dry_run.py
# writes: aggregate.json, probes.json, measurements/comment-0NN.json
```
