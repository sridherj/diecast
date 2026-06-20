<!-- SHARED BLOCK — referenced by ALL 8 hat prompts in cast-hat-researcher.md. -->
<!-- DRY (Plan Review Decision #4 / C1-B): authored ONCE here; do NOT embed verbatim per hat. -->
<!-- Provenance: lifted verbatim from cast-web-researcher §"Web Fetching Protocol" @ 8e5c6e7 -->

# Web Fetching Protocol (MANDATORY for every hat)

> **RULE: Every WebFetch call MUST have a resilient-browser fallback.**
>
> 1. Try `WebFetch` first.
> 2. If WebFetch returns **403**, **empty body**, **Cloudflare challenge**, or
>    **JS-only shell** (no meaningful text content): invoke `/resilient-browser`.
> 3. `/resilient-browser` MUST run as a **haiku subagent** (model="haiku") via the
>    **Task tool** — Chrome MCP responses are ~10–15k tokens; never run them in this
>    agent's context. (`/resilient-browser` is a *skill*, invoked as a slash-command
>    subagent — it is NOT an HTTP-dispatched `cast-*` agent and is NOT in
>    `allowed_delegations`.) Prefer Chrome MCP first; fall back to Playwright only if
>    Chrome MCP is unavailable.
> 4. If `/resilient-browser` also fails: log the failure, skip that source, continue
>    with remaining sources.
> 5. **Never silently drop a URL** that returned 403 — either fetch it via
>    resilient-browser or explicitly note the failure in the note's **Key Sources**
>    section (surface, don't suppress).

## Source-priority ladder (apply within every hat's searches)

For technical topics:
1. GitHub repos (actual code, real usage) and official documentation
2. Academic papers / conference proceedings (benchmark results, novel techniques)
3. Production case studies and postmortems (real-world validation)
4. Technical blog posts from practitioners (hard-won lessons)
5. Community discussions with high engagement (Reddit 100+ upvotes, HN 50+ points)
6. General articles and tutorials (lowest priority — often surface-level)

For non-technical topics:
1. Practitioner case studies with specific results/metrics
2. Community discussions from people who've actually done it (Reddit, HN, forums)
3. Expert guides and frameworks from known authorities in the field
4. Data-backed articles (studies, surveys, A/B test results)
5. Tool/platform reviews with real user experiences
6. General advice articles (lowest priority — often surface-level)

## Depth bar (the cast-web-researcher philosophy, inherited)

**"Go deep on the best 3 results, not shallow on 10."** Push every claim down to
names / numbers / versions / URLs. This depth bar OVERRIDES any urge toward
breadth/completeness — research the few best sources deeply rather than skimming many.
