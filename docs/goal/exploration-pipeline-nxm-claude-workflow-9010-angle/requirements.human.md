# Exploration Pipeline: N×M Claude Workflow + 90/10 Angle

Raw requirements (verbatim intent from SJ, 2026-06-20).

## 1. Make the starter-exploration a Claude Workflow with N×M fan-out

Would it be possible to make the **starter-exploration** (the `cast-explore` pipeline) into a
**Claude workflow** (the deterministic Workflow orchestration, not an orchestrator agent that
hand-rolls child delegation)?

I want to **spawn separate agents for different angles across different steps — N × M** — unlike
how it does today. Today the pipeline dispatches **one** `cast-web-researcher` per step (N agents),
and that single agent covers all 7 angles *inside one context*. I want each (step × angle) pair to
be its own agent with **fresh, isolated context**, so we **avoid unnecessary context overlap** —
angles bleeding into each other, one agent's framing contaminating another's.

So: N steps × M angles = N×M research agents, each isolated, orchestrated deterministically by a
Workflow script (fan-out, then synthesize).

## 2. Add a new "90/10 solution" angle

I want **one more angle** around **what the 90/10 solution will look like**.

Reference: YC's Essential Startup Advice — https://www.ycombinator.com/library/4D-yc-s-essential-startup-advice
(the "find the 90/10 solution" idea). There should be more material on this around the internet —
**do solid research**. This is a **very useful angle**: for any step, what's the version that gets
~90% of the value for ~10% of the effort?

> Canonical source (verbatim, attributed to YC partner **Paul Buchheit**): *"look for the '90/10
> solution'. That is, look for a way in which you can accomplish 90% of what you want with only 10%
> of the work/effort/time. If you search hard for it, there is almost always a 90/10 solution
> available. Most importantly, a 90% solution to a real customer problem which is available right
> away, is much better than a 100% solution that takes ages to build."*

## 3. (Reference) Mine gstack for more angles / better prompts

Refer to `~/workspace/reference_repos/gstack` for ideas — additional angles or better per-angle
prompts. Its review/lens skills (CEO, eng, design, devex, security/cso, office-hours, investigate)
are candidate exploration angles and prompt-pattern sources. Enrichment, not a mandate to add all.

## 3b. Angles are generative "thinking hats," not review verdicts (framing)

Important framing: when I explore, I'm trying to find ideas to **do things differently / faster**.
Each angle is a **hat someone wears** — *"if someone were to wear the 90/10 hat, how would they go
about this problem?"* — and it should surface that perspective's **ideas**, not a pass/fail verdict.

This generative, idea-finding model **is the whole point of the starter exploration** — it is not
negotiable and not borrowed from anywhere.

**Hard rule on gstack: borrow TECHNIQUES, never PRINCIPLES.**
- ✅ TECHNIQUES (prompt mechanics) we may borrow: specificity ladders ("push once, then push
  again"), anti-sycophancy phrasing ("take a position; name what evidence would change it"),
  three-layer synthesis + [EUREKA] tags, mandatory-alternatives-with-effort/risk stamps,
  cognitive-patterns-as-instincts to give each hat a distinct voice.
- ❌ PRINCIPLES we must NOT import: gstack's "Boil the Ocean" completeness ethos, its
  review/score/refute/gate stance, its verdict-oriented output. Those contradict the exploration's
  generative, do-it-differently/faster purpose.
- The pipeline keeps each hat's take **distinct and rich**. **I collate** across hats myself — the
  pipeline should not prematurely blend perspectives into a single verdict.

## 4. Polished HTML output, rendered in Diecast, commentable

This time the workflow should produce a **great HTML output — not the md files** — and that output
should be **rendered in Diecast in the place where md files are shown now**. Essentially Diecast
should support **both HTML and MD rendering** in its artifact viewer.

`/cast-refine-requirements` already has a **great way of splitting the WHAT to show from the HOW to
show, leveraging sub-agents** to achieve it (the cast-requirements-what / cast-requirements-how /
requirements_render pipeline). Get inspired by that.

We should also be able to **comment on the HTML using the `/cast-comment-html` utility**.

The md files are **still produced** (machine-readable substrate that downstream planners consume);
HTML renders **on top, for visualization** — dual md/html in the artifact viewer. The rendered HTML
may be stored under `docs/visualization/` if useful.

### 4b. HTML + commenting becomes a Diecast-wide capability (not exploration-only)

This is **horizontal**: dual md/html rendering **and** commenting become **part of the entire
Diecast artifact surface**, with exploration and refined-requirements as the **first two consumers**.
Concretely: even **`/cast-refine-requirements` output should show its HTML in the Diecast artifact
viewer** — today it does not (the requirements HTML render lives on a separate `/goals/{slug}/render`
page reached by a button, never inline in the viewer where md shows). The goal makes the viewer
render both .md and polished .html for ANY artifact, with `/cast-comment-html`-style commenting
available across the board.

(Acknowledged: this is a sizable, multi-pillar expansion — N×M workflow + 90/10 hat + a general
Diecast dual-md/html + commenting artifact surface.)
