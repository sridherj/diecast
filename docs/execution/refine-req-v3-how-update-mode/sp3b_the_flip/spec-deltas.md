# Sub-phase 3b — spec deltas flagged for the Sub-phase 5 `/cast-update-spec` pass (v7 → v8)

> sp3b does NOT edit `cast-requirements-render.collab.md` (one spec pass, Sub-phase 5). These are the
> contract changes sp3b landed in code that Sub-phase 5 must record. Each is already live + tested.

## 1. US16 — verbatim-carriage clause SUPERSEDED (the flip)

The blanket "every unit's anchorable leaf text appears verbatim and contiguous within its container"
obligation is **removed**. CREATE mode now optimizes for the most human-readable delivery and may
paraphrase / distill leaf requirement text freely. **What survives (still HARD):** anchor labels
(each canonical id printed verbatim, owned by exactly one unit container) + the one-unit-one-container
DOM rule. `maker_gate.check_html` dropped the verbatim-carriage violation class; owner-finding now
keys on the anchor label alone (no lead-text predicate). Safe because comments anchor to the
published render snapshot (sp2), not the source — source-leaf verbatim carriage is no longer the
property keeping comments placeable.

## 2. US19 — survival classification re-oriented to RENDER space

`check_comment_survival` is render-space: a `anchor_space='render'` comment survives iff its quote
places inside the same `block_ref` container on the candidate render. **Unchanged-block miss =
structural violation** (UPDATE byte-identity makes it impossible on the happy path); **modified/
removed-block miss = expected**, never a violation, routed to the publish-boundary re-anchor; a
ref-less (`block_ref=None`) / cross-boundary miss = best-effort badge-only (Decision #1). Legacy
source-space comments keep the prior classification unchanged.

## 3. ⚠️ Architecture note — UPDATE mode BENDS the "one self-contained page" contract (splice won)

The 1a spike returned **FAIL → deterministic-splice** (`spikes/update-fidelity/verdict.md`). So in
**UPDATE mode the published artifact is SERVER-ASSEMBLED**, not a single maker-emitted page: the HOW
maker emits only changed-block fragments (`<!-- RR-FRAGMENT ref="…" -->` … `<!-- /RR-FRAGMENT -->`),
and `block_splice.splice_update` keeps the prior render's unchanged unit-container bytes verbatim +
splices the fragments in. `maker_gate.check_update_fidelity` verifies RAW-BYTE identity of unchanged
containers (the splice **construction guarantee**, not an LLM obligation). The gate-enforced-LLM-copy
branch (normalized-text comparison) is documented but **dead** (1a PASS never happened). Sub-phase 5
must spec this explicitly so the "maker emits ONE self-contained page between sentinels" contract
carries an UPDATE-mode carve-out rather than being papered over.

## 4. Known limitation (Open Question, HOLD SCOPE) — paraphrase meaning-drift is LLM-guarded only

With verbatim gone, nothing deterministic guards paraphrase *meaning*. The WHAT-doc total id-mapping +
the HOW never-invent rules remain the contract; the 4a checker keeps grading comprehension cold-reader;
comments are the human correction channel. **No dedicated meaning-fidelity checker** (HOLD SCOPE).
Spec records: "paraphrase meaning-drift is LLM-guarded only."

## 5. New degrade-to-CREATE preconditions (UPDATE only from clean maker priors stays)

`_prepare_mode` adds two CREATE-degrade triggers beyond the 3a mode decision (each a noted degrade,
never an error): (a) a **ref-less block changed** (no anchor label → the splice cannot key it);
(b) **no block-level change is localizable** (source hash changed but `block_diff` finds zero
added/modified/removed blocks — e.g. a resolved gap's answer the parser attaches ambiguously). Both
re-render fresh so an edit is never silently ignored by a no-op splice.

## 6. New: ONE publish-boundary `cast-comment-reanchor` v3 dispatch

After an UPDATE publish, the survival report's EXPECTED misses (render-space comments on changed
blocks) drive ONE `cast-comment-reanchor` v3 dispatch (render-space hints) to relocate/resolve/orphan.
A `relocated` quote not present on the served render is downgraded to orphan (the 422 verbatim
backstop at the service boundary); a crash / garbage verdict leaves comments open + badged, no retry.

## 7. HOW prompt "CONTRACT SOURCE OF TRUTH" pointer

`agents/cast-requirements-how/cast-requirements-how.md` now documents the two-mode contract inline;
its CONTRACT SOURCE OF TRUTH pointer is to be re-aimed at the **v8** `cast-requirements-render` spec
section in the Sub-phase 5 spec change.
