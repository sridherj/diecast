# Research: Workflow Classification Taxonomy & Per-Family Document Shaping (without becoming a Template Enforcer)

**Goal context:** Refine Requirements v2 — Workflow-Aware, HTML-First Requirements Refinement (Step 3 of the exploration). Validate the owner's 5 priority work families (new initiative/PRD, small pilot/POC, bug fix/debug, data analysis/research, random ideas/exploration) against how teams and OSS communities actually classify work, then design per-family **document** templates + a classifier that surfaces a family pill and confirms on ambiguity (FR-002/003/004) — with an explicit guard against the **Template-Enforcer** anti-pattern (keep the "random ideas" family loose). Must generalize beyond the maintainer (OSS product, FR-012) and treat AI agents as first-class producers AND consumers (FR-013).
**Date:** 2026-06-11
**Researcher:** cast-web-researcher (7-angle parallel research)

> **Scope discipline:** This step shapes the *requirements document* per family (US2). It is **separate** from the downstream workflow routing in Step 6 (US6) — same classification, two distinct effects. This note covers taxonomy validation + document shaping + the classifier UX; routing-into-pipelines is Step 6's problem.

---

## 1. Expert Practitioner Insights

**The single most important finding: the best orgs do not have one document type — they run a *triage* that routes work to the lightest artifact that fits, and they explicitly protect early/fuzzy work from rigid templates.** Every elite source makes the same two-part move: (a) match document weight to the work's ambiguity and blast radius, and (b) name a deliberate "rough/loose" mode for ideation that must NOT be over-specified. This directly validates the 5-family hypothesis — and the strongest evidence is that family #5 (fuzzy exploration) is treated as a *first-class, intentionally-loose* mode by the best teams, not as an immature version of the others.

**Basecamp / 37signals Shape-Up — the gold standard for "keep early work loose."** Shape-Up draws an explicit line between a **raw idea** and **shaped work**, and insists shaping is *deliberately rough*. The first property of shaped work is literally "It's Rough": "Work in the shaping stage is rough. Everyone can tell by looking at it that it's unfinished." The named failure mode is over-specifying too early: *"Work that's too fine, too early commits everyone to the wrong details... When design leaders go straight to wireframes or high-fidelity mockups, they define too much detail too early. This leaves designers no room for creativity."* Shaped work has exactly three properties — **Rough, Solved, Bounded** — and "Bounded" is enforced by **appetite** ("the amount of time we want to spend on a project, as opposed to an estimate"). The output artifact is a **pitch** (raw idea + use case + appetite + solution + rabbit holes + no-gos) — but only *after* shaping, and pitches are written at "a higher level of abstraction than wireframes." This is the canonical named evidence that fuzzy work gets a *different, looser* shape. [Principles of Shaping | Shape Up](https://basecamp.com/shapeup/1.1-chapter-02)

**Google — Malte Ubl's "Design Docs at Google" explicitly rejects a strict template.** The doc is the model for "informal by design": *"Design docs are informal documents and thus don't follow a strict guideline for their content. Rule #1 is: Write them in whatever form makes the most sense for the particular project."* Crucially it gives an explicit **don't-write-one rule**: if a doc just says "this is how we'll implement it" without trade-offs/alternatives, *"then it would probably have been a better idea to write the actual program right away."* It scales the artifact to scope — **mini design docs of 1–3 pages** for incremental work, **10–20 pages** for large projects — and warns that review is "a dangerous trap of overhead." Early-stage docs should be "as lightweight as possible so that changes are quick." This validates families #1 (big initiative → full doc) vs #2 (pilot/POC → mini-doc) and the principle that obviousness/ambiguity, not size alone, decides the template. [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)

**Oxide Computer — RFD states formalize the fuzzy→committed gradient.** Oxide's Request-for-Discussion process is the clearest example of *state-as-classifier*: a single artifact moves through **ideation → prediscussion → discussion → published → committed**. The **ideation** state is explicitly "a scratchpad for related ideas... no expectation that it is undergoing active revision"; **prediscussion** is "a collaborative extension of an engineer's notebook." Their rule: *"States shouldn't be used for ideas that have been committed to... by the time an idea represents the consensus or direction, it should be in the published state."* This is a powerful design pattern for the feature: rather than 5 disjoint templates, fuzzy work can be the *early state* of the same document that hardens over time. [RFD 1: Requests for Discussion | Oxide](https://rfd.shared.oxide.computer/rfd/0001)

**Amazon — narrative type is chosen by *purpose*, not size.** Amazon runs a small fixed menu of narrative types and picks by intent: the **PR/FAQ** is "future-looking and focuses on vision and strategy" (used for new products/initiatives → maps to family #1); the **six-pager** is for decision-making meetings ("six pages was determined to be the right length for an hour meeting"); slides are reserved for broadcast-to-many, not for evoking discussion. Bezos's 2004 narrative mandate is the rationale for prose-over-template: writing "in complete sentences and complete paragraphs... forces a deeper clarity of thought," and "narratives convey about 10 times as much information as presentations." Takeaway: classify by *what the work is for* (launch a new thing vs decide vs broadcast), which is exactly a family-routing function. [The Amazon Working Backwards PR/FAQ Process](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/)

**RFC vs ADR vs design doc — the engineering taxonomy that maps cleanly to families.** The widely-cited framing: *"RFC is the brainstorming meeting before a decision; ADR is the official memo after the decision."* RFCs are for open, multi-team, contentious decisions (→ family #1 big initiative); ADRs capture a decision already made by a small group (lightweight, → family #2/#3). The explicit guidance is **lightweight-by-default**: "not every change requires an RFC—most of the time you need to move fast... Teams should simplify processes for smaller changes with lightweight templates, while creating more heavyweight templates for large-scale changes." Templates exist "to nudge people's thinking," not to gate. [ADRs and RFCs: Their Differences and When to Use Which | Candost's Blog](https://candost.blog/adrs-rfcs-differences-when-which/) · [Engineering Planning with RFCs, Design Documents and ADRs | Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/rfcs-and-design-docs)

**Rust RFCs — the canonical "what does NOT need structure" list (directly validates family #3, bug fix/debug).** Rust's RFC-0002 is the sharpest named boundary for skipping heavy process: *"Many changes, including bug fixes and documentation improvements can be implemented and reviewed via the normal GitHub pull request workflow."* Explicitly **no RFC required** for: "Rephrasing, reorganizing, refactoring, or otherwise 'changing shape does not change meaning'"; "Additions that strictly improve objective, numerical quality criteria (warning removal, speedup...)"; and changes "only likely to be noticed by other developers-of-rust, invisible to users-of-rust." Bug fixes and refactors are first-class *no-document* work — strong support for giving family #3 a minimal-to-zero spec shape. [rust-lang/rfcs text/0002-rfc-process.md](https://github.com/rust-lang/rfcs/blob/master/text/0002-rfc-process.md)

**Synthesis for the feature design:**
- **Two axes drive classification, not one.** Every source routes on (a) *ambiguity/contention* and (b) *blast radius / commitment level* — not raw size. A "small" change that is contentious still gets an RFC; a "big" but obvious change can skip the doc (Google, Rust, Candost all say this).
- **The fuzzy family must be a named first-class mode, not a degraded PRD.** Shape-Up "Rough" and Oxide "ideation" are explicit, deliberate, low-structure states. Forcing family #5 into trade-off tables / acceptance criteria is the exact anti-pattern these orgs warn against.
- **Prefer state-progression over disjoint templates (Oxide pattern).** The strongest model lets a fuzzy idea *harden into* a fuller spec rather than starting from a heavy template — reduces the cost of misclassification.
- **Templates "nudge, don't gate."** Keep per-family templates as prompts/scaffolds, and always allow the lighter artifact (or none) — the universal lightweight-by-default principle.
- **Classify by purpose for the heavy end.** Amazon's PR/FAQ vs six-pager split shows family #1 itself may warrant a "vision/launch" framing (working-backwards) distinct from a "decision" framing.

**Sources**
- https://basecamp.com/shapeup/1.1-chapter-02
- https://www.industrialempathy.com/posts/design-docs-at-google/
- https://rfd.shared.oxide.computer/rfd/0001
- https://workingbackwards.com/concepts/working-backwards-pr-faq-process/
- https://candost.blog/adrs-rfcs-differences-when-which/
- https://newsletter.pragmaticengineer.com/p/rfcs-and-design-docs
- https://github.com/rust-lang/rfcs/blob/master/text/0002-rfc-process.md

---

## 2. Tool/Product Landscape

| Tool | Work-type taxonomy | Per-type templates? | How type is selected | Notes |
|------|-------------------|--------------------|--------------------|-------|
| **Jira** | Epic / Story / Task / Bug / **Spike** / Subtask (custom types addable) | **Yes** — per issue type via *issue type screen schemes* (different fields/screens per type) | Type picker dropdown on issue create; admin binds types to a project via *issue type scheme* | Closest mature model to "classify then shape doc." Spike type = research/investigation work family — directly analogous to "data analysis/research" + "exploration" families. |
| **Linear** | 3-level hierarchy: **Initiative → Project → Issue** (+ labels for type/effort/area) | Issue templates + **Project templates** (predefine issues, milestones, lead, status, linked initiative) | Pick a template when creating issue/project; labels for classification | Hierarchy maps cleanly to PRD (initiative/project) vs small task (issue). Classification is via labels, not a hard "type" field. |
| **GitHub Issues** | Defined entirely by repo: `bug_report` vs `feature_request` vs custom (e.g. `3-epic`) | **Yes** — one file per type in `.github/ISSUE_TEMPLATE/`; Markdown or structured **issue forms** (`.yml`) | **Template chooser** UI; `config.yml` controls order/labels and `blank_issues_enabled` | The chooser + form-schema is the cleanest reference UX for "pick a work-type pill, get a shaped doc." Forms render to standardized markdown. |
| **GitHub Spec Kit** | Phase artifacts, not work types: `constitution → spec → plan → tasks` | Templates per **phase** (one spec.md shape), not per work family | `specify init`; `/speckit.*` slash commands drive each phase | ~111k stars. Spec-driven-development canon. Single spec shape — does NOT branch by work family, which is the gap your feature fills. |
| **Notion** | User-defined; marketplace has PRD / RFC / bug-report / research / tech-spec templates | **Yes** — *database templates* (one-click page structures) + 30k+ marketplace templates | Pick a database template from a dropdown when creating a page | "Docs database for product teams" ships PRD + RFC + Brainstorm + Technical Spec templates as separate one-click shapes — a direct multi-family analog. |
| **Aha!** | **Strategy → Goals → Initiatives → Releases → Features** (5-level) | Per-level views, scoring, fields | Create at the level you want; strategy-first workflow | Strongest strategic-altitude taxonomy. "Initiative vs Feature" ≈ "new initiative/PRD vs small pilot." |
| **Productboard** | Objectives → Initiatives (feature groups) → Features | Lighter per-level structure | Tie features to objectives/initiatives | Feedback-engine positioning; shallower hierarchy than Aha!. |
| **MADR / adr-tools** | Single family: architecture decision | **One** template (MADR `NNNN-title.md`); `adr new` scaffolds numbered file | CLI `adr new <title>` / `log4brains` | adr-tools 5.5k stars. Single shape, no branching — but proves the "scaffold a typed doc from a CLI" pattern. |

### Deep dives on the most relevant tools

**Jira — the canonical "classify then shape" model.** Jira separates *what kind of work* (issue type) from *what fields that work needs* (screen scheme), bound together by an **issue type screen scheme**. A `Bug` shows a "steps to reproduce / severity" screen; a `Story` shows acceptance criteria; a **`Spike`** is explicitly "a short, focused effort to research or investigate a particular technology or approach" ([Atlassian: work types](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/)). This is the strongest precedent for the design: the *type* is a first-class field, and the *document shape* (which fields/sections appear) is data-driven off that type. The 5 work families map roughly to Story/Epic (new initiative/PRD), Task (small pilot), Bug (bug fix/debug), Spike (data analysis/research **and** random ideas/exploration).

**GitHub issue forms + template chooser — the best selection UX reference.** When a contributor clicks "New issue," GitHub shows a **template chooser** listing each file in `.github/ISSUE_TEMPLATE/`; `config.yml` controls ordering (number-prefix filenames like `1-bug.yml`), labels, and whether a blank option is allowed ([Configuring issue templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)). **Issue forms** go further: a YAML schema declares typed fields (dropdowns, checkboxes, textareas) that render to a standardized markdown body ([Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)). This is the cleanest "pick a pill → fill a shaped form → get a normalized doc" loop in the wild, and it's declarative/data-driven — exactly the architecture a classifier-fed feature wants. **Critically, GitHub always keeps a "blank issue" escape hatch** (`blank_issues_enabled`) — the built-in Template-Enforcer guard.

**GitHub Spec Kit — the spec-driven baseline, and its gap.** Spec Kit (~111k stars, [github/spec-kit](https://github.com/github/spec-kit)) is the dominant 2026 spec-driven-development toolkit. Its loop is **Constitution → Specify → (Clarify) → Plan → Tasks → Implement**, each a markdown artifact the next phase reads, driven by `/speckit.*` slash commands ([spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md)). Critically, Spec Kit branches by **phase**, not by **work family** — there is one `spec.md` shape regardless of whether you're shipping a PRD or debugging. That is precisely the whitespace this feature occupies: classify into ~5 families *first*, then shape the requirements doc per family before the spec/plan/tasks pipeline runs.

**Notion — multi-family doc templates as one-click shapes.** Notion's "docs database for product teams" ships distinct one-click templates for **PRD, RFC, Brainstorm, and Technical Spec** within a single database ([documents database guide](https://www.notion.com/help/guides/documents-database-for-product-teams)). Database templates "let you define and replicate certain page structures with one click" ([Database templates](https://www.notion.com/help/database-templates)). This validates the core bet: teams genuinely want *different document skeletons per work type*, selectable at creation time — but Notion leaves classification entirely manual (the human picks the template), whereas this feature auto-classifies the goal.

### Synthesis for the feature
- **Type as first-class + data-driven shape** is the proven pattern (Jira screen schemes, GitHub issue forms). Make the work family a field; make the doc sections a function of that field.
- **Selection UX**: GitHub's template chooser (pills with descriptions + a "blank/other" escape hatch) is the strongest reference; combine with auto-classification (the differentiator) so the pill is *pre-selected*, not blank.
- **Whitespace**: every spec-driven tool (Spec Kit, ADR/MADR) uses a *single* doc shape. None branch by work family. The "classify into ~5 families, then shape the requirements doc" move is genuinely uncovered ground.
- **Spike is the precedent** for non-build work families (research/analysis/exploration) — lean on Jira's framing rather than inventing terminology.

### Sources
- https://linear.app/docs/initiatives
- https://linear.app/docs/conceptual-model
- https://linear.app/docs/project-templates
- https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/
- https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository
- https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
- https://github.com/github/spec-kit
- https://github.com/github/spec-kit/blob/main/spec-driven.md
- https://www.notion.com/help/guides/documents-database-for-product-teams
- https://www.notion.com/help/database-templates
- https://www.notion.com/templates/category/product-requirements-doc
- https://github.com/npryce/adr-tools
- https://github.com/thomvaill/log4brains
- https://adr.github.io/madr/
- https://www.aha.io/blog/aha-roadmaps-vs-productboard-how-to-choose-the-best-roadmap-software
- https://support.productboard.com/hc/en-us/articles/25194993652627-Initiative-management-in-Productboard

---

## 3. AI-Native Approaches

**The consequential shift (2024→2026):** classification into a fixed taxonomy is no longer a brittle prompt-parsing problem. With **OpenAI Structured Outputs (`strict: true` + `json_schema` enum)**, released Aug 2024, the model *cannot* emit a label outside your enum — gpt-4o-2024-08-06 scored 100% on schema adherence vs <40% for older models. This collapses "classify the writeup into one of {PRD, pilot, bug, analysis, exploration}" into a single constrained-decoding call that is guaranteed to return a valid family. JSON mode is now legacy; strict `json_schema` is the production default. The same guarantee exists across providers (Claude tool-use / Gemini structured output) ([OpenAI Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/), [Logic structured-outputs guide](https://logic.inc/resources/structured-outputs-guide)). *(Diecast is a Claude-native stack — the equivalent is a forced tool call with an enum-typed `family` argument.)*

**Zero-shot vs few-shot for short-doc triage.** For a 5-class work-family taxonomy, zero-shot with rich label *definitions* in the schema description is usually enough; few-shot seed examples per family materially raise accuracy on ambiguous writeups. The taxonomy-anchored pattern — give the LLM the *complete* taxonomy with per-category definitions a priori, then ask it to map text into the fixed set — is the current best practice for issue triage ([Vellum intent guide](https://www.vellum.ai/blog/how-to-build-intent-detection-for-your-chatbot), [Label Your Data, intent classification 2026](https://labelyourdata.com/articles/machine-learning/intent-classification)). Feed *structured metadata* (title, author, existing labels, repo) rather than dumping the raw body — GitHub's IssueCrush found "labels and author context matter more than you'd think" and that organized metadata beats raw text ([GitHub blog, Copilot SDK triage](https://github.blog/ai-and-ml/github-copilot/building-ai-powered-github-issue-triage-with-the-copilot-sdk/)).

**Concrete classify → pill → confirm pattern.** The canonical 2025 schema for this exact problem comes from the open-source AI triage bots:

- The bot returns **structured JSON: `category` (enum), `priority`, a `confidence` score, a one-line summary, suggested labels, and a `reasoning` string** ([squaredtech AI triage bot](https://www.squaredtech.co/ai-issue-triage-bot-built-in-500-lines-of-typescript-heres-how-it-wo)). Map `category` directly to the work-family pill; `reasoning` becomes the hover/explanation; `confidence` drives the confirm gate.
- Validate the LLM output against a **strict whitelist/schema — anything off-schema falls back to sensible defaults rather than crashing** the run. Combined with strict mode this gives two layers of safety.
- GitHub's **Agentic Workflows** (tech preview, 2026) generalize this: automation goals (incl. auto-triage + labeling) written as Markdown, executed by a coding agent ([InfoQ, GitHub Agentic Workflows](https://www.infoq.com/news/2026/02/github-agentic-workflows/)).

**Confidence — the load-bearing mechanism for "confirm when ambiguous."** Three techniques, in increasing robustness:
1. **Verbalized confidence** — ask the model to rate 0–1 in the same structured call. Cheapest; reasonably calibrated across models, but RL-tuned models trend overconfident and verbalized scores saturate to coarse buckets ([Verbalized Confidence Scores](https://www.emergentmind.com/topics/verbalized-confidence-scores)).
2. **Logprobs-based confidence** — compute confidence from token probabilities over the answer span (top-k); more reliable as a *ranking/thresholding* signal than verbalized scores.
3. **Caveat to design around:** models verbalize uncertainty but often **fail to act on it** — "Are LLM Decisions Faithful to Verbal Confidence?" shows the gap. So don't let the model decide whether to ask; *you* threshold the score and gate the UI ([arXiv: faithfulness to verbal confidence](https://arxiv.org/html/2601.07767)).

A practical system-prompt calibration scheme seen in the field: **0.9+ = certain (auto-apply pill silently), 0.5–0.9 = likely-but-ambiguous (show pill, ask to confirm), <0.5 = guessing (show top-2 families, force a choice)** — plus "uncertainty factors" / "confidence basis" fields that force the model to state *what* makes it unsure, which also gives the human the info to correct fast ([Ideafloats HITL 2025](https://blog.ideafloats.com/human-in-the-loop-ai-in-2025/), [DEV: HITL patterns for high-stakes decisions](https://dev.to/omnithium/human-in-the-loop-patterns-for-high-stakes-ai-agent-decisions-1fg6)).

**Confirm-on-ambiguity is now a named pattern: confidence-based routing / escalation.** "If the agent can't confidently classify, the workflow pauses and escalates to a human instead of guessing." Below-threshold → defer to human; this is the standard HITL building block ([Zapier HITL patterns](https://zapier.com/blog/human-in-the-loop/), [WorkOS HITL](https://workos.com/blog/why-ai-still-needs-you-exploring-human-in-the-loop-systems)). The pill-with-confirm UX *is* this pattern surfaced in the doc: a guess the human can one-click accept or override. This is the direct implementation of **FR-004**.

**Classifier-as-router (the cheap/fast alternative & complement).** If you want sub-100ms family classification without an LLM round-trip, **Aurelio `semantic-router`** defines each family as a `Route` with seed utterances, embeds the writeup, and picks the nearest route in vector space — and crucially **returns `None` when nothing clears the decision threshold** (i.e., built-in "abstain → ask the user"). ~5000ms→~100ms vs LLM generation ([semantic-router GitHub](https://github.com/aurelio-labs/semantic-router)). **RouteLLM** (LMSYS, ICLR 2025) and **vLLM Semantic Router** (ModernBERT classifier, Sept 2025) are the same idea applied to model selection / reason-vs-fast routing — directly reusable as "is this writeup big enough to warrant full PRD treatment?" ([vLLM Semantic Router](https://vllm-semantic-router.com/)). A hybrid is strong: semantic-router for the cheap first guess + `None`→LLM fallback for the ambiguous tail.

**Spec-driven tooling — how they classify *kind of work* before generating.** Worth noting the adjacent ecosystem because the doc must serve AI producers/consumers: **AWS Kiro** (launched Jul 2025) forces an *upfront mode choice* — **"spec mode"** (define spec → generate tasks, producing `requirements.md` in EARS / `design.md` / `tasks.md`) vs **"prompt mode"** (free-form). That binary mode selection is itself a coarse work-family classifier, and it's a UX precedent for surfacing the choice up front ([AWS Builder Center, Kiro](https://builder.aws.com/content/31u60Xzm1ymjMpCi5kTmFutCyiN/hands-on-project-using-kiro-spec-driven-development), [SDD definitive guide](https://thebcms.com/blog/spec-driven-development)). The implication: emit the family classification + confidence as **machine-readable front-matter** so downstream agents route to the right spec template (PRD-heavy vs lightweight pilot vs bug-fix checklist) — the classification becomes a routing key for both humans (the pill) and agents (the schema field). This is how FR-002 and FR-013 fuse.

**The grounding precedent — Mozilla BugBug.** The pre-LLM SOTA for auto-triage: classifies bugs by product/component and a **bugtype classifier (crash/memory/performance/security)**, with a separate "is this actually a bug?" classifier — proving the multi-classifier, auto-labeled-from-history approach works at Firefox scale. Modern LLM versions replace the trained models with strict-schema enum calls but keep the architecture ([mozilla/bugbug](https://github.com/mozilla/bugbug)).

**Net recommendation for this tool:** single strict-schema (Claude tool-call) classification returning `{family: enum, confidence: float, reasoning: str, uncertainty_factors: str[], alt_family: enum}`; threshold confidence (≥0.9 silent pill / 0.5–0.9 pill+confirm / <0.5 two-option forced choice); optionally front it with semantic-router for a free fast-path + `None`-driven escalation; persist the result as front-matter so downstream AI consumers route on it.

**Sources**
- https://openai.com/index/introducing-structured-outputs-in-the-api/
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://logic.inc/resources/structured-outputs-guide
- https://github.blog/ai-and-ml/github-copilot/building-ai-powered-github-issue-triage-with-the-copilot-sdk/
- https://www.squaredtech.co/ai-issue-triage-bot-built-in-500-lines-of-typescript-heres-how-it-wo
- https://www.infoq.com/news/2026/02/github-agentic-workflows/
- https://www.vellum.ai/blog/how-to-build-intent-detection-for-your-chatbot
- https://labelyourdata.com/articles/machine-learning/intent-classification
- https://www.emergentmind.com/topics/verbalized-confidence-scores
- https://arxiv.org/html/2601.07767
- https://blog.ideafloats.com/human-in-the-loop-ai-in-2025/
- https://dev.to/omnithium/human-in-the-loop-patterns-for-high-stakes-ai-agent-decisions-1fg6
- https://zapier.com/blog/human-in-the-loop/
- https://workos.com/blog/why-ai-still-needs-you-exploring-human-in-the-loop-systems
- https://github.com/aurelio-labs/semantic-router
- https://vllm-semantic-router.com/
- https://builder.aws.com/content/31u60Xzm1ymjMpCi5kTmFutCyiN/hands-on-project-using-kiro-spec-driven-development
- https://thebcms.com/blog/spec-driven-development
- https://github.com/mozilla/bugbug

---

## 4. Community Wisdom

**The strongest recurring sentiment: practitioners overwhelmingly agree that the *value is in the thinking, not the template* — and that forcing rich templates onto early/uncertain work converts agile iteration into waterfall.** The single most-engaged recent thread on this is "Spec-Driven Development: The Waterfall Strikes Back" ([HN, 225 points, 191 comments](https://news.ycombinator.com/item?id=45935763)). The top counter-wisdom there directly validates keeping an exploratory family LOOSE:

- **"You will never know as little about the problem as you do on day one. Your knowledge will only grow."** — SideburnsOfDoom ([HN](https://news.ycombinator.com/item?id=45935763)). Paired with 4ndrewl: *"we don't even understand our problem well, let alone understanding a solution to it."* This is the core argument that heavy upfront structure is wrong precisely when ideas are fuzzy.
- **"I tend to keep my initial instructions succinct, then build them up iteratively... speccing ahead in great detail can sometimes be detrimental."** — danielbln ([HN](https://news.ycombinator.com/item?id=45935763)). Echoed by podgorniy: *"you can start with a vague spec, missing some sections, and clarify it with iterations."* Direct support for a loose-by-default doc that hardens over time.
- **Double-overhead complaint:** *"I don't like the idea of primarily reviewing specs... Plus, I'm going to be reviewing the code too... so having spec AND code is now double the text to read."* — dwb ([HN](https://news.ycombinator.com/item?id=45935763)).

**"Design Docs at Google"** is the canonical high-engagement thread on when docs help vs. hurt ([HN, 459 points, 187 comments](https://news.ycombinator.com/item?id=23915521)):

- The "Template Enforcer" failure mode, named vividly: **"These became 'concrete galoshes' that turned what should have been an agile, iterative project into a waterfall behemoth that cost a mint, took forever to make, and delivered a result that no one wanted."** — ChrisMarshallNY ([HN](https://news.ycombinator.com/item?id=23915521)).
- Right-sizing to team, not cargo-culting big-co templates: **"One of the more common mistakes... is adopting tools and processes of companies that don't look like yours. The needs of a spec for... Google are probably pretty different for a team of 10 in constant communication."** — AnonC ([HN](https://news.ycombinator.com/item?id=23915521)).
- Rigidity makes docs shallow: **"Each team/problem space is different and too strict of rules can often lead to documents that may end up being shallow."** — taeric ([HN](https://news.ycombinator.com/item?id=23915521)). This is the precise risk of forcing mandatory fields.
- Proportional effort: **"The overhead of creating and reviewing a design doc may not be compatible with prototyping and rapid iteration. However, most software projects do have a set of actually known problems."** — theptip ([HN](https://news.ycombinator.com/item?id=23915521)) — i.e., classify by certainty, not by ritual.

**Lobsters "Decision Logs"** thread is the clearest statement of the lightweight-wins counter-wisdom ([lobste.rs](https://lobste.rs/s/fckbue/decision_logs)):

- **"Once it starts morphing into something resembling an RFC or anything that would take more than an hour or two to write up, it's time to revisit it."** — belak. A concrete time-box heuristic for "is this template too heavy?"
- **The mandatory-approval trap:** *"If the document has to be approved, then people quietly make decisions without recording it anywhere."* — ahobson. Process rigor backfires into *less* documentation.
- The value is one line, not a form: *"One liner will return its weight tenfold: 'User id is only their email. Why: arbitrary decision by John from Sales.'"* — kubanczyk.

**RFC-fatigue at scale (the Uber/Twitter pattern):** practitioner write-ups converge on tiered/lightweight processes. Pragmatic Engineer documents that as Uber passed ~2,000 engineers, *"hundreds of RFCs went out weekly... which overwhelmed more experienced engineers"* and that Twitter's backend RFC template *"accumulated required sections... and was in the ballpark of 14 pages — before being filled in"* before being cut back ([Pragmatic Engineer](https://blog.pragmaticengineer.com/rfcs-and-design-docs/)). The prescribed fix is uniformly *tiered templates sized to change criticality* — small/lightweight for routine, formal only for high-impact — which is exactly the "classify into families, shape the doc per family" design. Mike Cvet's failure-modes piece adds the proportionality rule: *"the amount of effort invested in any given RFC should be proportional to its likely improvement of outcomes"* ([Better Programming](https://betterprogramming.pub/goals-and-failure-modes-for-rfcs-and-technical-design-documents-c4ee1d1da6ff)).

**Shape Up / PRD camp** reinforces the loose-for-fuzzy stance from the product side: Basecamp deliberately rejects detailed specs, keeping pitches at a level of abstraction where builders decide details during building; and PM consensus is that one-page beats comprehensive — *"the longer the doc, the less it gets read... if you're forced to limit the brief to one page, you will get much better at describing the problem"* ([Shape Up — Bets, Not Backlogs](https://basecamp.com/shapeup/2.1-chapter-07)).

### Common mistakes practitioners call out
- **Cargo-culting big-company templates** onto small/fast teams ("concrete galoshes").
- **Mandatory fields nobody can fill early** → either shallow box-checking or quiet non-documentation.
- **Template creep** — sections accumulate from every stakeholder until the blank form is 14 pages (the "Template Enforcer" endgame).
- **Requiring approval/sign-off**, which suppresses recording decisions at all.
- **Reviewing spec *and* code** as duplicated overhead with no iteration loop.
- **Equal effort regardless of risk** — treating a spike like a launch.
- **Specs that ossify on day one**, when that's when you understand the problem least.

### Sources
- https://news.ycombinator.com/item?id=45935763 (Spec-Driven Development: The Waterfall Strikes Back — 225 pts, 191 comments)
- https://news.ycombinator.com/item?id=23915521 (Design Docs at Google — 459 pts, 187 comments)
- https://lobste.rs/s/fckbue/decision_logs (Lobsters: Decision Logs)
- https://blog.pragmaticengineer.com/rfcs-and-design-docs/ (Pragmatic Engineer — Uber & Twitter RFC examples)
- https://newsletter.pragmaticengineer.com/p/rfcs-and-design-docs (Pragmatic Engineer — tiered process & PRD length)
- https://betterprogramming.pub/goals-and-failure-modes-for-rfcs-and-technical-design-documents-c4ee1d1da6ff (Mike Cvet — Goals & Failure Modes for RFCs)
- https://basecamp.com/shapeup/2.1-chapter-07 (Shape Up — Bets, Not Backlogs)

> **Source-access note:** Reddit (r/ExperiencedDevs, r/ProductManagement) is blocked for both WebSearch and WebFetch in this environment (Anthropic crawler disallowed by reddit.com), so verbatim Reddit quotes/upvote counts could not be pulled. The sentiment is well-covered by the Lobsters and HN threads above, which carry verifiable engagement numbers. No quotes or vote counts were fabricated.

---

## 5. Frameworks & Methodologies

The owner cut work into 5 families by asking **"what document layout do I need?"** That is a real, named tradition — Diátaxis proves "shape follows purpose" works for docs — but the established frameworks reveal that *layout* is a downstream symptom of two deeper axes: **reversibility** (how costly is being wrong?) and **uncertainty/risk** (do we know cause-and-effect yet?). Below: the named frameworks, the axis each cuts on, their canonical sections, and a direct assessment of the 5-family axis.

### 5.1 Framework reference table

| Framework | Axis it cuts on | Canonical doc sections | When to use |
|---|---|---|---|
| **PRD** (Product Requirements Doc) | Producer→consumer handoff; "what to build" for a new initiative | Problem/background, goals, user stories/requirements, success metrics, scope/out-of-scope | New initiative with defined intent; aligns PM→eng |
| **RFC** ([Rust](https://rust-lang.github.io/rfcs/0002-rfc-process.html), [Squarespace](https://engineering.squarespace.com/blog/2019/the-power-of-yes-if)) | Soliciting **consensus** on a substantial/contested change *before* building | Summary, motivation/problem, detailed design, drawbacks, **alternatives**, risks, dependencies, unresolved questions | "Substantial" change where stakeholder buy-in matters; async review |
| **ADR** ([Nygard 2011](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)) | Recording a **single architectural decision** + its forces, immutably over time | Title, **Status** (proposed/accepted/deprecated/superseded), **Context** (forces), **Decision**, **Consequences** | One decision worth remembering *why*; append-only log |
| **MADR** ([adr.github.io/madr](https://adr.github.io/madr/)) | Same as ADR but extends to **option comparison** | Context, **Decision Drivers**, **Considered Options** (pros/cons each), Decision Outcome, Consequences | Decisions with several viable options needing tradeoff capture |
| **Google Design Doc** ([industrialempathy](https://www.industrialempathy.com/posts/design-docs-at-google/)) | High-level implementation strategy + **tradeoffs** before coding | Context, **Goals & Non-Goals**, design/solution, alternatives considered, cross-cutting concerns (security, privacy, i18n, storage) | Non-trivial build where design choices have lasting impact |
| **Spike** ([Mountain Goat](https://www.mountaingoatsoftware.com/blog/spikes), XP) | **Uncertainty reduction** under a fixed timebox; produces *information, not shippable code* | Question to answer, timebox, findings, recommendation/decision (prototype/PoC as throwaway) | Blocking uncertainty about how a feature works or will be built |
| **PR/FAQ** ([Working Backwards](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/), Amazon) | **Customer-desirability** validation; works backwards from the launch | 1-page press release (7 paragraphs), internal FAQ, external FAQ | Vetting whether a new initiative is worth building at all |
| **Research notebook** (Jupyter/Observable) | **Literate, exploratory computing** — interleaved narrative + code + output | Narrative cells + executable cells + inline results; no fixed schema | Data analysis / iterative investigation where the path is the artifact |
| **Diátaxis** ([diataxis.fr](https://diataxis.fr/start-here/)) | **User need**: study-vs-work × skill-vs-knowledge → 4 doc types | Tutorial / How-to / Reference / Explanation (each a distinct shape) | Documentation taxonomy; the cleanest "shape follows purpose" precedent |
| **arc42** ([faq.arc42.org](https://faq.arc42.org/questions/B-17/)) | Complete architecture *documentation* template | 12 fixed chapters (context, constraints, building blocks, runtime, deployment, crosscutting, decisions, quality, risks) | Comprehensive, long-lived system documentation |
| **C4 model** | Architecture **visualization** (abstraction-first) | Context / Container / Component / Code diagrams (no requirements/risk sections) | Communicating static structure; complements arc42, not a doc template |

### 5.2 The cross-cutting axes the 5-family scheme ignores

**Reversibility — Amazon Type 1 vs Type 2** ([Bezos 2015 letter](https://www.scarletink.com/p/from-one-way-to-two-way-doors-rethinking)). One-way doors (irreversible, high-stakes) deserve heavyweight deliberation and review; two-way doors (cheaply reversible) should be made fast and lightly. The crucial insight: *most decisions are Type 2 but get over-processed as Type 1*. This maps **directly to doc weight** — a reversible experiment should never carry a 7-section RFC.

**Uncertainty — Cynefin** ([Snowden](https://en.wikipedia.org/wiki/Cynefin_framework)). Clear → best-practice (checklist/runbook); Complicated → expert analysis (design doc/ADR); Complex → probe-sense-respond (spike/experiment); Chaotic → act-first (incident note). The *right document shape is a function of which domain you're in*, which the owner's families only partially encode.

**Appetite — Shape Up** ([Basecamp](https://basecamp.com/shapeup/1.1-chapter-02)). Fixed time, variable scope: "appetites start with a number and end with a design." The time you're *willing* to spend is itself a classifier and a constraint on doc weight — orthogonal to document-type.

**Set-based vs point-based** ([Lean.org](https://www.lean.org/lexicon-terms/set-based-concurrent-engineering/)). Carry multiple options and eliminate the inferior ones late vs commit early to one. This is the deep rationale behind MADR's "Considered Options" and RFC's "Alternatives" sections — a high-uncertainty problem *demands* a set-based doc shape.

### 5.3 Assessment: does the owner's 5-family (doc-layout) axis hold up?

**Where it holds.** The axis has a strong precedent in **Diátaxis**: documentation genuinely fractures along *purpose*, and forcing a tutorial into reference shape (or a PRD into spike shape) is the classic failure mode. The 5 families map cleanly to recognized genres — PRD↔new initiative, PoC↔spike, debug↔incident/runbook, data analysis↔research notebook, exploration↔(Shape-Up shaping / set-based sketching). So as a *first-cut router to a template*, the axis is defensible and matches industry artifacts almost one-for-one.

**Where it leaks.** Document-layout is a **proxy, not a primitive**. Two of the families collapse distinctions the deeper frameworks treat as load-bearing:

1. **"New initiative/PRD" conflates desirability, decision, and design.** Amazon splits this into PR/FAQ (should we?), then design doc/RFC (how?). A one-way-door initiative and a two-way-door initiative want *different doc weights* despite sharing a "layout." Reversibility cross-cuts this family.
2. **"Bug fix/debug" and "data analysis" both span Cynefin domains.** A clear bug = runbook; a complex, never-seen-before failure = spike. The family name can't tell which.

**Recommended cross-check.** Keep the 5-family layout axis as the **primary router** (it's concrete, it maps to real templates, and it's what the user actually asks — "what do I write?"). But validate each classification against **two secondary gates** before fixing doc weight:
- **Reversibility gate** (Type 1/Type 2): one-way doors escalate to a heavier template + review even within a family; two-way doors get a lighter variant.
- **Uncertainty gate** (Cynefin/spike): if cause-and-effect is unknown, route to a *spike/notebook* shape regardless of the nominal family, because the output is information, not a decision.

In short: the owner's axis is the right *surface* (matches Diátaxis precedent and real artifacts) but should be **modulated, not replaced**, by reversibility and uncertainty. A robust taxonomy is **5 families × {reversible?, uncertain?}**, not 5 families alone.

### Sources
- https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- https://adr.github.io/madr/ , https://adr.github.io/adr-templates/
- https://rust-lang.github.io/rfcs/0002-rfc-process.html
- https://engineering.squarespace.com/blog/2019/the-power-of-yes-if
- https://www.industrialempathy.com/posts/design-docs-at-google/
- https://www.mountaingoatsoftware.com/blog/spikes
- https://workingbackwards.com/concepts/working-backwards-pr-faq-process/
- https://www.scarletink.com/p/from-one-way-to-two-way-doors-rethinking
- https://en.wikipedia.org/wiki/Cynefin_framework
- https://basecamp.com/shapeup/1.1-chapter-02 , https://basecamp.com/shapeup/1.2-chapter-03
- https://www.lean.org/lexicon-terms/set-based-concurrent-engineering/
- https://diataxis.fr/start-here/
- https://faq.arc42.org/questions/B-17/ , https://docs.arc42.org/section-9/

---

## 6. Contrarian Perspectives

**The sharpest objection:** This feature optimizes the wrong moment. The hardest, highest-leverage cognitive work in early-stage requirements is *resisting premature framing* — staying in the question long enough to discover what the work actually is. A classifier that fires up front does the opposite: it makes the first decision the system asks the user to commit to be "which of 5 boxes is this?" That is the single most anchoring possible intervention, applied at the single most fragile moment. The spec's named "Template Enforcer" risk is real, but it under-states the problem: the damage isn't only rigid *structure*, it's the rigid *frame* the classification installs before anyone understands the work. You can soften the template to nothing and still inherit the anchoring cost of the label.

### Specific misconceptions and failure modes

- **"Categories describe the work." → Categories *filter* the work.** Once a taxonomy exists, novelty gets quietly forced into the nearest box instead of recognized as new. Dave Snowden's case: IBM's taxonomy couldn't classify a genuinely new consulting model, so it got buried under "marketing," and the knowledge taxonomy "took three years to catch up" — obsolete before completion. "Where things are subject to rapid change and the possibility of encountering novelty is high they are plain dangerous." [Typology or Taxonomy? — Cynefin Co](https://thecynefin.co/typology-or-taxonomy/)

- **"5 boxes cover the space." → Real work spans families and mutates.** A "bug" turns out to be a redesign; a "spike" becomes an initiative; a "chore" exposes an architecture problem. The categorization tax compounds because the system filters subsequent evidence through the original label — the same mechanism as diagnostic *anchoring* and "diagnosis momentum" in medicine, where an early label "gathers momentum until it becomes definitive and makes other possibilities overshadowed," even when contradictory findings appear. [Anchoring Bias — AHRQ PSNet](https://psnet.ahrq.gov/web-mm/anchoring-bias-critical-implications)

- **"Per-type templates raise quality." → They reliably decay into theater.** Documentation "is often treated as decorative — something you write to satisfy a process, not something the system depended on," and a "simple two-pager grows into ten pages as every stakeholder request adds another section." More structure means more unread structure. [Why Nobody Reads Your Docs — Earlyhacks](https://earlyhacks.com/why-nobody-reads-your-docs-and-what-to-do-about-it/) · [The Document Nobody Read — Tim O'Brien](https://medium.com/@tobrien/the-document-nobody-read-just-became-the-system-8e659adb7a49)

- **"A heavier doc process is rigor." → Overhead must be proportional or it's just overhead.** The RFC literature is explicit: "If all design considerations could be captured in code review for simpler changes, then the RFC is just overhead… effort invested in any given RFC should be proportional to its likely improvement of outcomes." A per-family template that imposes the same weight regardless of stakes inverts this. [Goals and Failure Modes for RFCs — Mike Cvet](https://betterprogramming.pub/goals-and-failure-modes-for-rfcs-and-technical-design-documents-c4ee1d1da6ff)

- **"Asking the user to pick a type is a quick, helpful step." → Every required choice is friction users resent and route around.** Form research is unambiguous: "each additional required field increases friction and drop-off," and even making a field *optional* rather than removing it can lift completion 10%+. A confirm-on-ambiguity gate is a required classification field by another name — users will satisfice (pick whatever ends the prompt) and the label becomes noise the rest of the pipeline trusts as signal. [Required Fields in Forms — UX Tigers](https://www.uxtigers.com/post/required-fields) · [Zuko — form field UX](https://www.zuko.io/blog/which-form-fields-cause-the-biggest-ux-problems)

- **"Categorizing organizes the work." → Categorizing builds prisons.** "The borders we draw for ourselves create a prison of thought and collaboration, inhibiting movement, connectivity, and learning." Boxing work early suppresses the cross-cutting relationships and feedback loops that early ideation exists to surface. [The Tyranny of Categorization — Dominic Hofstetter](https://medium.com/in-search-of-leverage/the-tyranny-of-categorization-8ae57dd3a0fe)

### The honest counter-evidence (steelman)

The "blank page is paralyzing" critique of pure freedom is real and well-supported: a structureless prompt produces the tyranny of the blank page. But the empirical relationship is a **U-curve, not a slope** — a review of 145 studies found creativity rises with constraint up to a point, then falls; "too many constraints can be stifling, too little causes complacency." [Creativity from constraints (145 studies) — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1871187122001870). This *cuts both ways*: it justifies *some* scaffolding, but it argues against *family-specific rigidity*, because the optimal constraint level varies by how fuzzy the work is — which a fixed-per-family template can't sense. The right constraint is "one good prompt + a couple of forcing questions," not five divergent rigid skeletons.

### When this feature is WRONG

- **Early/exploratory work** where the goal is to discover the problem, not document a known one — classification anchors the scope before it's understood.
- **Work that straddles families** (the bug-that's-a-redesign) — the label becomes a lie the downstream pipeline trusts.
- **High-novelty work** — taxonomies force novelty into the wrong box; this is precisely where rigid categories are "plain dangerous."
- **Low-stakes work** — where a per-family template imposes overhead disproportionate to outcome; the RFC test ("is this just overhead?") fails.
- **When the user is uncertain** — confirm-on-ambiguity converts genuine uncertainty into a coerced, low-quality label via satisficing.
- **Any time the taxonomy is fixed but the work isn't** — the IBM "three years to catch up" failure.

**Simpler alternatives that may beat classification:**
1. **Progressive structure** — start with one loose prompt; add structure only when the work *earns* it (it survives, grows, gets contested). YAGNI applied to docs. [Agile Manifesto principles](https://agilemanifesto.org/principles.html)
2. **One flexible template** with optional sections the author can ignore — captures the U-curve benefit of *some* scaffolding without the anchoring and friction of a forced upfront pick.
3. **No template, better prompts** — a small set of forcing questions ("what breaks if we don't do this? what's the narrowest version?") delivers the constraint benefit without installing a sticky category.
4. **Classify *late and silently*, never up front** — if a family signal is useful for tooling, infer it after the requirements exist and surface it as a soft, revisable hint rather than a label the human anchors to.

### Sources
- https://thecynefin.co/typology-or-taxonomy/
- https://medium.com/in-search-of-leverage/the-tyranny-of-categorization-8ae57dd3a0fe
- https://psnet.ahrq.gov/web-mm/anchoring-bias-critical-implications
- https://earlyhacks.com/why-nobody-reads-your-docs-and-what-to-do-about-it/
- https://medium.com/@tobrien/the-document-nobody-read-just-became-the-system-8e659adb7a49
- https://betterprogramming.pub/goals-and-failure-modes-for-rfcs-and-technical-design-documents-c4ee1d1da6ff
- https://www.uxtigers.com/post/required-fields
- https://www.zuko.io/blog/which-form-fields-cause-the-biggest-ux-problems
- https://www.sciencedirect.com/science/article/abs/pii/S1871187122001870
- https://agilemanifesto.org/principles.html
- https://www.techtarget.com/whatis/definition/You-arent-gonna-need-it

---

## 7. First Principles Analysis

**The irreducible core.** A requirements document exists for exactly one reason: to create *shared understanding cheap enough that the work doesn't get redone*. Everything else — sections, templates, families — is scaffolding around that single job. Strip a "requirements doc" to its atoms and three primitives remain: (1) *what reality are we in* (problem/context/evidence), (2) *what do we intend to change about it* (decision/scope), and (3) *what don't we know yet* (open questions). If a document conveys those three to a competent stranger — human or agent — it has done its job. A bug report that says "X broke, here's the repro, fix it" satisfies all three in two sentences. A PRD satisfies them in ten pages. **The job is constant; only the dosage varies.** The templates encode *dosage*, not *purpose*, and dosage should be a function of uncertainty, not of a category label chosen up front.

**The minimum viable classification.** Five families do not earn their complexity. They collapse to **two axes**:

- **Axis 1 — Epistemic stance: question vs. change.** Is the goal to *learn something* (the answer is currently unknown) or to *make something* (the action is roughly known, execution is the work)? Data-analysis/research and random-ideas/exploration are both *questions*. Bug-fix and new-initiative are both *changes*. Small-pilot/POC straddles — it's "a change made *in order to* answer a question," which is exactly why a third family for it is over-engineering: it's a question-goal with a build attached.
- **Axis 2 — Confidence/scope: how much is already known.** A bug fix is a high-confidence narrow change; a PRD is a low-confidence broad change. A scratch idea is a low-confidence question; a defined analysis is a higher-confidence question.

The 5 candidate families are just the quadrants of (question×change) × (low×high confidence), with the fifth ("random ideas") being the **origin of the graph** — zero confidence, undeclared stance. This mirrors how [Diátaxis](https://diataxis.fr/) reduced the sprawl of "doc types" to a single 2×2: *shape follows purpose*, and purpose decomposes into a tiny number of orthogonal axes rather than a flat list of named buckets. A flat list of 5 forces a premature commitment and hides the fact that most goals *move* between quadrants as they mature.

**The 80/20.** Maintenance literature's "60/60 rule" finds ~60% of effort is enhancement (changing requirements), ~23% adaptive, ~17% bug fix ([endertech](https://endertech.com/blog/software-maintenance-bug-fixing-4-types-maintenance)); new-vs-maintenance commonly splits ~70/30. Translation: the *change* axis dominates raw volume, but it fragments across many sub-shapes, so building one rigid "feature template" misses most of the mass. The honest 80/20 conclusion is **not** "optimize the PRD" — it's "optimize the *block set* that all changes share, then let blocks compose." For arbitrary OSS users and agent-authored goals, the distribution is even flatter and noisier than enterprise data, which further argues against betting the design on any one named family.

**A concrete stripped-down design: blocks, not templates.** Define ~6 reusable blocks, each a self-contained unit of shared understanding:

| Block | Answers | Cheap signal it's needed |
|---|---|---|
| `problem` | what's wrong / what we want | always present (the writeup itself) |
| `evidence` | what we observed | repro steps, logs, data, links |
| `decision` | what we'll do / chose | a verb of intent ("build", "migrate", "switch to") |
| `scope` | boundaries, in/out | breadth words ("across", "all", "system") |
| `question` | what we're trying to answer | a `?`, "why", "whether", "investigate" |
| `open` | unknowns / risks | always allowed, never required |

Families become *assembly recipes*, not files: bug fix = `problem + evidence + open`; research goal = `question + evidence + open`; PRD = `problem + decision + scope + open`; POC = `question + decision(small) + open`; raw idea = `problem` only. This is the literate-programming / lightweight-RFC insight applied structurally: an RFC template should be "minimal… the required attributes only, used as the starting point" ([Sourcegraph handbook](https://github.com/sourcegraph/handbook/blob/main/content/company-info-and-process/communication/rfcs/index.md), [Lambros Petrou — RFC template](https://www.lambrospetrou.com/articles/rfc-template/)) — i.e. the field already converged on *one composable minimum* plus optional sections, not five fixed forms. Blocks beat templates on every first-principles axis: **fewer total concepts** (6 blocks vs. 5×N sections), **graceful degradation** (an unclassifiable goal still emits `problem`), **agent-friendliness** (an agent fills blocks it has evidence for and omits the rest, no "template said so" filler), and **mutability** (as a goal earns confidence, you *add* a `decision` block rather than migrating documents).

**Loosest-family-as-default — yes, argue it.** The default must be the origin of the graph: a single `problem` block, no forced structure. Three reasons. (1) **Information you don't have can't be a requirement.** Forcing a `scope` or `metric` field on a half-formed idea manufactures fiction, and fiction in a requirements doc is *negative* — it actively misleads the next human/agent. (2) **Confidence is earned, not declared.** Structure should accrete as evidence arrives — a goal that starts as "random idea" routinely becomes a PRD. A loose default lets the document grow into its shape instead of being cast in the wrong mold at minute zero. (3) **The cost asymmetry favors loose.** Under-structuring costs a follow-up question; over-structuring costs wasted authoring plus the rework of dismantling wrong scaffolding. Default loose, *prompt* for the next block only when a cheap signal says it's warranted.

**Minimal classifier — no ML needed for the first pass.** Four near-free signals get ~80% routing accuracy: (1) **lead verb / intent** ("fix/repair" → change-narrow; "build/launch/add" → change-broad; "investigate/analyze/why" → question); (2) **presence of repro steps or a stack trace** → bug-fix recipe; (3) **presence of a `?` / interrogative** → question recipe; (4) **presence of a metric/number/target** → adds `scope`+`decision` weight. These map to *which blocks to suggest*, not to a locked label — a classifier that picks blocks degrades gracefully (wrong guess = one extra/missing optional block), whereas one that picks a template fails hard (wrong guess = wrong document). When signals conflict or are absent, fall through to the loose default.

**Essential vs. convention.** *Essential:* the three understanding primitives (reality/intent/unknowns); the question-vs-change axis; the confidence-grows-over-time dynamic; the loose default. *Convention:* the specific count "5 families," any fixed section ordering, document length norms, and the names themselves. The families are a useful *vocabulary* for talking to users ("this looks like a bug fix") but a harmful *data model* if hardcoded. **Build the data model on blocks + two axes; keep the five family names only as human-facing labels mapped onto block recipes.**

**Sources:**
- https://diataxis.fr/
- https://www.lambrospetrou.com/articles/rfc-template/
- https://github.com/sourcegraph/handbook/blob/main/content/company-info-and-process/communication/rfcs/index.md
- https://newsletter.pragmaticengineer.com/p/software-engineering-rfc-and-design
- https://endertech.com/blog/software-maintenance-bug-fixing-4-types-maintenance
- https://pegotec.net/software-maintenance-cost-percentage-2026-industry-benchmarks/
- https://moldstud.com/articles/p-balancing-features-and-bug-fixes-in-your-software-development-project

---

## Key Takeaways

1. **The 5 families are validated as a human-facing *vocabulary*, but should NOT be the *data model*.** They map almost one-for-one to real industry genres (PRD↔new initiative, Spike↔POC/research, bug report/runbook↔bug fix, Jupyter notebook↔data analysis, Shape-Up shaping/Oxide ideation↔random ideas). Diátaxis proves "shape follows purpose." But every deep framework (Cynefin, Type1/Type2, set-based design) and the first-principles analysis converge on the same warning: a flat list of 5 hardcoded templates is brittle. **Model the document as ~6 composable blocks (`problem, evidence, decision, scope, question, open`); express each family as a block *recipe*; show the family name as a pill.** This is the single highest-leverage design decision and it cleanly satisfies the generic-fallback requirement (FR-002/003 Scenario 4): an unmatched goal still emits the `problem` block.

2. **Make the "random ideas / exploration" family the DEFAULT and the floor, not a degraded PRD.** Shape-Up ("It's Rough"), Oxide ("ideation: a scratchpad… no expectation of active revision"), Google ("informal by design"), and Rust ("no RFC for bug fixes/refactors") all treat low-structure work as a deliberate first-class mode. The Template-Enforcer guard is concrete: the ideas family renders only `problem` (+ optional `open`); **never** auto-insert acceptance scenarios, success metrics, scope tables, or FR grids into it; structure *accretes* as confidence is earned (the Oxide state-progression pattern), never imposed at minute zero.

3. **Classify with a single strict-schema (Claude tool-call) classification returning `{family, confidence, reasoning, uncertainty_factors, alt_family}`, and let *thresholds* — not the model — drive the confirm gate.** Calibration that satisfies FR-004: ≥0.9 → show pill silently; 0.5–0.9 → show pill + one-click confirm/override; <0.5 → present top-2 families and ask. Models verbalize uncertainty but don't reliably act on it, so gate in code. Optionally front with a `semantic-router`-style fast path that returns `None`→escalate for a cheap first guess.

4. **Two secondary gates should modulate doc weight *within* a family: reversibility (Type 1/Type 2) and uncertainty (Cynefin).** A "bug" that's actually a never-seen-before complex failure should route to a spike/notebook shape; a one-way-door initiative warrants more structure than a two-way-door one. Encode these as block-inclusion modifiers, not new families. This directly answers Step 3 substep 1 ("confirm, merge, or re-cut the axis"): **keep the axis, modulate it.**

5. **Confirm-on-ambiguity must include a real escape hatch or it becomes friction users satisfice through.** The contrarian/forms evidence is strong: a forced classification field increases drop-off and produces noise labels the pipeline then trusts. Mitigations: the pill is *pre-filled* (accept = one click, the GitHub-chooser pattern), always offer "just notes / not sure yet" (= the loose default), and make the label **revisable and non-binding** — it never silently anchors downstream (US6 reclassification already anticipates this).

6. **No existing tool does "auto-classify → shape the requirements doc per family." That's genuine whitespace.** Jira/GitHub-forms prove "type as first-class field + data-driven shape" works but require *manual* type selection; Spec Kit and ADR/MADR use a *single* shape. Diecast's differentiator is auto-classification feeding the block-recipe — and emitting the family + confidence as **machine-readable front-matter** so downstream agents (FR-013) route on the same signal humans see in the pill.

7. **Per-family inspiration templates to cite as design references (substep 5):** New initiative → Amazon PR/FAQ + Google design doc + PRD (problem/goals/non-goals/user-stories/metrics/scope); POC/pilot → XP **Spike** (question/timebox/findings/recommendation) + Google "mini design doc" (1–3 pp); Bug fix → GitHub `bug_report` issue form (symptom/repro/expected-vs-actual/environment) + incident runbook; Data analysis → Jupyter/Observable literate notebook (question → data sources → method → expected output shape); Random ideas → Shape-Up pitch *pre-shaping* (problem + raw idea only) / Oxide RFD `ideation` state.

---

## Design Implications for Step 3 (playbook-ready)

This section translates the research into the concrete deliverables Step 3's success criteria call for.

### A. Validated family taxonomy (substep 1)
**Verdict: keep the 5 families as labels; back them with a 2-axis + block-recipe data model; add an explicit generic fallback.**

| Family (pill label) | Maps to industry genre | Block recipe (default sections) | Doc weight |
|---|---|---|---|
| **New initiative / PRD** | PR/FAQ + Google design doc + PRD | `problem + decision + scope + open` (+ goals/non-goals, success metrics, alternatives) | Heaviest; escalates if one-way-door |
| **Small pilot / POC** | XP Spike + mini design doc | `question + decision(small) + open` | Light; one-screen WHAT |
| **Bug fix / debug** | GitHub bug_report + runbook | `problem + evidence + open` (symptom / repro / expected-vs-actual) | Minimal; may need no spec at all (Rust precedent) |
| **Data analysis / research** | Jupyter/Observable notebook | `question + evidence + open` (question / data sources / expected output shape) | Light-medium; HOW often irrelevant → omit Directional (US1 S3) |
| **Random ideas / exploration** | Shape-Up pre-shaping / Oxide ideation | `problem` only (+ optional `open`) | **Loosest — the default/floor** |
| **Generic fallback (unmatched)** | — | `problem + open`, note unmatched classification | Loose |

### B. Classifier design (substep 3) — implements FR-002 + FR-004
- **Signals it reads:** raw writeup text + title; cheap lexical signals first (lead verb, presence of `?`, repro/stack-trace, metric/number, breadth words); LLM strict-schema classification for the ambiguous tail.
- **Output schema:** `{family: enum[6], confidence: float, reasoning: str, uncertainty_factors: str[], alt_family: enum}` — persisted as front-matter (serves humans via pill + agents via FR-013).
- **Surface:** a pill at the top of the HTML render ("You are **fixing a bug** in X") with `reasoning` on hover.
- **Confirm gate (FR-004):** ≥0.9 silent · 0.5–0.9 pill + confirm/override · <0.5 top-2 forced choice. Always include a "just notes / not sure" option that selects the loose default.
- **Reversibility/uncertainty modifiers:** secondary gates that add or drop optional blocks within the chosen family.

### C. Template-Enforcer guard (substep 4) — the explicit rules
1. **Loose is the default**, not a fallback for failure. Absent strong signal → `problem`-only.
2. **The ideas family is structurally incapable of forced sections** — the renderer for family #5 has no scope/metric/acceptance-scenario slots to fill; it cannot pad.
3. **Structure accretes, never imposed** (Oxide state-progression): blocks are *added* as confidence/evidence grows, surfaced as suggestions ("want to add scope?"), never auto-generated as empty mandatory fields.
4. **Pills nudge, don't gate** — classification is always one-click revisable and never blocks the user from writing freely.
5. **HOW is omitted when the family makes it irrelevant** (US1 Scenario 3) — e.g., data-analysis/research drops the Directional section rather than padding it.
6. **Proportionality check** — borrow the Lobsters heuristic: if shaping a family's template would take "more than an hour or two," it's too heavy for that family.

### D. Open items to carry into design/plan review
- **Block-model vs literal-5-templates** is a real architecture fork — recommend block model, but the owner should sign off (it changes the data model in Step 2's store).
- **Where the classifier lives** overlaps Step 6's router-placement question — classification is shared by US2 (document shaping) and US6 (routing); design it as one classification emitted once, consumed twice.
- **Long-tail families** (add-tests, heavy-UI-flow, PRD-only) — designed-for via the block model (they're just other recipes) but flagged out of v2 scope.

---

## Key Sources

- [Shape Up — Principles of Shaping (Rough/Solved/Bounded, appetite)](https://basecamp.com/shapeup/1.1-chapter-02) — the canonical "keep early work loose" doctrine.
- [Design Docs at Google — Malte Ubl](https://www.industrialempathy.com/posts/design-docs-at-google/) — "informal by design," scale-to-scope, the don't-write-one rule.
- [Oxide RFD 1 — Requests for Discussion](https://rfd.shared.oxide.computer/rfd/0001) — state-as-classifier (ideation→committed); the model for structure-accretes-over-time.
- [Rust RFC-0002](https://github.com/rust-lang/rfcs/blob/master/text/0002-rfc-process.html) — the explicit "what does NOT need a doc" list; validates minimal bug-fix shape.
- [Amazon Working Backwards PR/FAQ](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/) — classify-by-purpose; narrative-over-template.
- [Pragmatic Engineer — RFCs, Design Docs and ADRs](https://newsletter.pragmaticengineer.com/p/rfcs-and-design-docs) — tiered/lightweight-by-default templates sized to change criticality.
- [Atlassian — Jira issue types & screen schemes](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/) — the proven "type as first-class field + data-driven doc shape" pattern (incl. Spike).
- [GitHub — Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) — declarative typed-field forms + template chooser + blank-issue escape hatch (best selection UX reference).
- [GitHub spec-kit](https://github.com/github/spec-kit) — dominant spec-driven toolkit (~111k★); branches by phase not family → the whitespace this feature fills.
- [OpenAI Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) — strict `json_schema`/enum guarantees a valid family label (Claude tool-use equivalent).
- [Aurelio semantic-router](https://github.com/aurelio-labs/semantic-router) — fast embedding router with built-in `None`→abstain (cheap classify + escalate-on-uncertainty).
- [Diátaxis](https://diataxis.fr/start-here/) — the cleanest "shape follows purpose" precedent; doc types reduce to a 2×2.
- [Cynefin framework](https://en.wikipedia.org/wiki/Cynefin_framework) & [Type 1/Type 2 doors](https://www.scarletink.com/p/from-one-way-to-two-way-doors-rethinking) — the reversibility + uncertainty axes that should modulate doc weight within a family.
- [Typology or Taxonomy? — Cynefin Co](https://thecynefin.co/typology-or-taxonomy/) — why fixed taxonomies are "plain dangerous" under novelty (the IBM 3-years-to-catch-up case).
- [HN: Design Docs at Google (459 pts)](https://news.ycombinator.com/item?id=23915521) & [HN: Spec-Driven Development: The Waterfall Strikes Back (225 pts)](https://news.ycombinator.com/item?id=45935763) — the "concrete galoshes" Template-Enforcer failure and the loose-by-default counter-wisdom.
- [Creativity from constraints — review of 145 studies (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S1871187122001870) — constraint→creativity is a U-curve; justifies *some* scaffolding but not per-family rigidity.
