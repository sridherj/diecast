# Refine Requirements — Better Rendering (v3)

## The problem

When I run refine-requirements and open the rendered `refined_requirements.html`, the
output is not what I pictured. I expected a beautiful, very-easy-to-consume HTML per
classification of work — closer to what `cast-preso` produces for slides. What I got is
functional but plain, and it has visible defects.

I had assumed there was a separate **presentation subagent** that *generates* a gorgeous
HTML out of the `.collab.md`, drawing heavily on cast-preso. There isn't. What got built
in refine-requirements v2 (Phase 3a) is a **deterministic Python + Jinja renderer**
(`renderer.py` + `goal_card.py` + `templates/document.html.j2` + `_theme.css.j2`). It
*borrows* cast-preso's CSS tokens, the pill idiom, and the `/preso/review` serve loop, and
it uses cast-preso-style LLM agents only as a **checker** (`cast-requirements-checker`,
the SC-001 gate), a **classifier** (`cast-goal-classifier`), a **comment re-anchorer**, and
a **diff narrator** — never as the maker of the page. A fully-LLM render was explicitly
rejected in the v2 plan (determinism floor), and "illustrations: none in v2" / HOLD SCOPE
closed any move toward preso-grade bespoke generation.

So the beauty ceiling today = the Jinja template + the Goal Card heuristics. That is the
gap I want to close in v3.

## Concrete defects found by dogfooding (the revamp-diecast refine run)

1. **Goal Card leaks raw inline markdown.** `goal_card.py` is markdown-unaware by design
   and `renderer.py` injects its output without converting/stripping, so `**bold**` and
   `` `code` `` show up as literal characters on the card.
2. **Sentence-splitter truncates on abbreviations.** `_first_sentence` / `_SENTENCE_END_RE`
   treat `vs.`, `e.g.`, `30 min.` as sentence ends, so the card's job statement and
   assertion leads get cut mid-thought ("…absorb vs.").
3. **General polish gap.** Even with clean input, the deterministic template doesn't reach
   the "very easy to consume" bar I want for handing this to engineers and PMs at a typical
   office (ties to the revamp-diecast ICP and direction #6, docs-as-product).

## The fork I need to decide

- **Deterministic polish:** keep the pure renderer (free, reproducible, snapshot-tested),
  fix the two defects, and raise the Jinja template + heuristics to real preso-grade polish.
- **Preso-style maker:** add a new LLM maker agent (a `cast-requirements-how` cousin of
  `cast-preso-how`) that generates a bespoke beautiful HTML per classification. This is a
  scope expansion v2 deliberately deferred, and it gives up determinism/reproducibility.
- **Hybrid:** deterministic structural render as the substrate, with an optional LLM
  "beautify/illustrate" pass on top (the preso checker stays the gate).

## Constraints / context I care about

- Must keep the server-served, self-healing regenerate-on-view loop
  (`/goals/{slug}/render`) and not break the existing comment/version layer (Phase 4) that
  anchors to the rendered DOM.
- Whatever we choose, every classification (new_initiative, bug_fix, data_analysis,
  random_idea, pilot_poc, testing_qa, refactor_migration, personal_non_eng, generic) must
  render cleanly — no family should look broken.
- Reuse cast-preso assets where it's cheap; don't rebuild a visual system from scratch.
- Determinism matters where being wrong matters (diffs, anchoring). Beauty is allowed to be
  less deterministic if we go that way — but the trade has to be explicit.

## What "done" feels like

I open the render for any goal, in any family, and within a few seconds I understand the
job, the outcome, and what's in/out of scope — and it looks good enough that I'd happily
put it in front of someone at a customer without apologizing for it.
