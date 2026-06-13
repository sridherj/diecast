# Refine Requirements — Better Rendering (v3): Phase 3 — The WHAT→HOW Maker Pipeline Renders Bespoke HTML

> ## ✅ RESOLVED — OWNER OVERRIDE (2026-06-12): structural-violation policy is FINAL
> **This supersedes any contrary wording later in this document** — including §3c "Decision #4"
> and every "structurally-unusable output → no-output branch → deterministic fallback" passage.
>
> **Rule (binding):** a maker attempt that produced *some* output but is structurally broken
> (paraphrased / missing / invented id, or broken verbatim-carriage) is **served as the best
> attempt with a visible `structural_violation` "needs review" flag/badge** — it is **NOT**
> replaced by the deterministic page. The deterministic fallback fires **only** on a *literal
> no-output* failure (crash / timeout / empty / sentinel-extraction failure). "Never silently
> drop" still binds: degradation is surfaced (flag + badge), never hidden. Principle: **surface,
> don't suppress.** Canonical record:
> `docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md` (§ Post-reconciliation
> owner decisions). Already implemented in 3c/3d and proven live in 3e.

## Overview

This plan details **Phase 3 only** of the v3 high-level plan: on the happy path,
`GET /goals/{slug}/render` is served by a two-agent pipeline — `cast-requirements-what`
emits per-block/per-family communication intent, `cast-requirements-how` turns it into a
self-contained, bespoke, per-family HTML page selecting from the named cast-preso archetype
library — with the canonical `US-NN`/`FR-NNN`/`SC-NNN` ids carried verbatim as a **logical
(non-DOM) backbone**. The v2 deterministic renderer is demoted to a fallback branch served
only on a true no-output maker failure. Generation runs as a **background job**: a view of a
changed source serves a live "generating…" state immediately and swaps in the finished
render when ready; the comment path is independent and always instant; the v2 source-hash
lazy-regeneration cache is reused unchanged.

The pipeline-execution insight grounding this plan: the server already has a sanctioned
headless LLM-invocation pattern — `claude -p <msg> --append-system-prompt <agent.md>
--model <m> --tools ""` (the `eval_render_checker.py` harness and the
`claude --resume … -p /context` breakdown in `agent_service.py` both use it). The tmux
HTTP-dispatch path is **wrong** for this job: it opens a visible terminal
(`agent_service.py` notes "real headless dispatch is a separate follow-up"), and a page
view must never pop a terminal. Both new agents therefore run as tool-free `claude -p`
subprocesses driven by a new `render_job_service` — the same subagent-mode carve-out
(bare output, no `.output.json` envelope) already documented for the classifier, the
checker, and `cast-comment-reanchor` (render-spec FR-011/FR-027 precedent).

Planning only — this document specifies Phase 3; it does not implement it. It assumes both
Phase 1 gates pass (`spikes/PHASE1-GATE.md`: `1a: BEATS DETERMINISTIC yes`,
`1b: BACKBONE HOLDS`); if either gate failed, this plan is void and the owner revisit-fork
applies first.

## Operating Mode

**HOLD SCOPE** — `refined_requirements.collab.md` front matter pins `scope_mode: hold` and
the delegation context repeats it ("Honor scope_mode: hold"). Owner decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md` are binding and are
not re-opened here. Checker + rework loop (4a), diff/comment-resolution (4b), and gap-fill
upstream asks (5) are out of scope — this plan designs only the seams they plug into.

## Position in Overall Plan

```
Phase 1 (spike gates — MUST be green) ────┐
                                          ├──► Phase 3 (THIS PLAN) ──┬──► Phase 4a (checker/loop)
Phase 2 (commenting + fallback fixes) ────┘                          └──► Phase 4b (comment survival)
                                                                                  └──► Phase 5
```

Phase 3 sits on the critical path: 4a and 4b both consume its output (a working maker
pipeline + the logical id backbone guarantee), and Phase 5's gap-fill rides the WHAT-doc
schema seam reserved here.

## Depends On (from prior plans / seed decisions)

From the binding seed (`refine-requirements-better-rendering-v3-decisions-so-far.md`):

- **Anchor backbone:** ids are a logical backbone only; the served DOM keeps v2
  quote/verbatim-substring anchoring — **no** `id=`/`data-block-anchor` anywhere
  (render-spec US7/FR-012/FR-013 preserved verbatim).
- **Background-job render model**, **net-new agents reusing preso toolkit/archetypes**,
  **family-communication page vocabulary (never US/FR/SC slots)**, **fallback only on true
  no-output failure**, **v2 hash cache reused unchanged**, **maker never writes the
  canonical `.collab.md`** — all owner-resolved; adopted as-is.

From Phase 1 (planned; gates assumed green at execution time):

- The **id-audit acceptance pattern** (1a): id-token set equality source↔HTML **plus
  per-block correspondence** — Phase 3 productionizes exactly this audit as its gate.
- The **mark-placement harness semantics** (1b): per block container, concatenate
  descendant text-node content (stdlib `HTMLParser`) and `find(quoted_text)`, hit valid
  only within the intended container — Phase 3's verbatim-carriage gate reuses these
  semantics, byte-faithful to `requirements_comments.js`.
- The **sharpened risk**: DB-level orphaning cannot be caused by render variation; the real
  exposure is silent `<mark>`-placement loss on a paraphrased maker DOM. Phase 3's
  `/cast-update-spec` activity MUST add the **verbatim-carriage clause** to the maker
  contract (1b design-review carry-forward).

From Phase 2 (parallel; surfaces Phase 3 must not touch but does consume):

- `strip_inline_markdown` (pure helper in `goal_card.py`) — Phase 3's verbatim-carriage
  gate uses it to derive a block's anchorable plain text. `_split_first_sentence`,
  `.rr-controls`, the comment-affordance JS/CSS — **untouched** by this plan.

From v2 (consumed verbatim):

- `requirements_render_service.rerender_requirements_html` (atomic write, AUTO-GENERATED
  header + `source-hash` comment, lazy hash check) — becomes the fallback writer; its
  embedded-hash cache mechanism is reused unchanged for maker output.
- `parse_requirements` / `Block.ref` (in-memory `US1`/`FR-007`/`SC-001` refs),
  `is_stub` + `STUB_WORD_THRESHOLD`, `families.py` (`WorkFamily`, `FAMILY_RECIPES`,
  `RECIPE_REALIZATION` — the WHAT agent's starting vocabulary),
  `extract_zero_click_view`, FR-028 progressive enhancement (the only sanctioned script
  references in an otherwise self-contained file).

From cast-preso (reused, never coupled): `~/.claude/skills/cast-preso-visual-toolkit/`
(`visual_toolkit.human.md` style tokens; `templates/slide-archetypes/` — 11 named
archetypes: `build-up-sequence`, `close-cta`, `code-showcase`, `compare-contrast`,
`consulting-exhibit`, `diagram-annotated`, `illustrated-section-opener`, `one-statement`,
`single-stat-hero`, `timeline`, `title-slide`) and the what/how split discipline
(WHAT doc = outcome + L1/L2 hierarchy + verification criteria; HOW = brainstorm ≥2
approaches → archetype shortlist → brief → HTML). The preso slide agents themselves are
**pattern reference only** — never invoked, never extended.

---

## Sub-phase 3a: The WHAT and HOW Agents Exist and Speak a Checkable Contract

**Outcome:** `agents/cast-requirements-what/` and `agents/cast-requirements-how/` exist as
net-new, registry-discoverable agents (`<name>.md` + `config.yaml`, picked up by
`bin/generate-skills`), each runnable tool-free via `claude -p`; the WHAT agent emits a
**machine-checkable WHAT doc** (family-appropriate section plan with every canonical id
mapped exactly once); the HOW agent emits a complete self-contained HTML document between
sentinel markers, honoring the DOM contract and the verbatim-carriage obligation.

**Dependencies:** None within Phase 3 (parallel with 3b). Phase 1 gates green.
**Estimated effort:** 1.5 sessions.

**Verification:**
- Both agent dirs pass `/cast-agent-compliance` (allow-list audit, directory conventions,
  config shape).
- A hand-run `claude -p` of each agent over this goal's requirements produces: a WHAT doc
  whose YAML front matter parses and passes `check_what_doc` (3b), and an HTML document
  extracted cleanly from the sentinels that passes `check_html` (3b) — recorded as a
  smoke-run note, not a CI test (LLM output is gated, not snapshot-asserted).
- `bin/generate-skills` regenerated; the two skills appear without manual registry edits.

Key activities:

- **Author `agents/cast-requirements-what/cast-requirements-what.md`.** Input (all inlined
  in the user message by the runner — the agent is tool-free): the full canonical source
  text, the parsed block inventory (`ref`, kind, heading, body per block), the confirmed
  classification (family + confidence from front matter), and the family's
  `FAMILY_RECIPES` recipe as **starting vocabulary**. Output: ONE WHAT doc (markdown,
  YAML front matter) with:
  - `contract: cast-requirements-what/v1`, `goal_slug`, `family`, `source_hash`;
  - `sections[]` — family-appropriate communication sections (e.g. data_analysis →
    "Signal sources", "Directional inputs"; user-facing → "Key decisions", "Product
    principles"), each with `title`, `outcome` (what a reader must take away — the preso
    L1/L2 discipline), and `block_refs[]` (the canonical ids feeding it);
  - `unmapped_refs: []` — the contract requires every parsed ref to appear in exactly one
    section's `block_refs`; anything the agent cannot place goes here and fails the gate
    loudly rather than vanishing;
  - `gaps: []` — **reserved Phase 5 seam** (FR-015 comprehension gaps); schema field
    defined now, always empty in Phase 3, no behavior attached.
  - Body: per-section communication intent prose (L1 vs L2 emphasis, what to lead with),
    mirroring the cast-preso-what-worker doc shape — adapted to a scrolling document page.
  - Hard prompt rules: sections are NEVER named after US/FR/SC slots; ids are metadata the
    HOW layer will print as small anchor labels; the WHAT layer never invents content
    absent from the source.
- **Author `agents/cast-requirements-how/cast-requirements-how.md`.** Input (inlined by the
  runner): the gated WHAT doc, the full source text, the visual-toolkit style tokens +
  the named archetype library (the runner inlines `visual_toolkit.human.md` and the
  archetype template files — cost is explicitly not a constraint), and the DOM-contract
  rules. Workflow mirrors the preso-how discipline: brainstorm ≥2 visual approaches per
  section, shortlist archetypes **by name** from the library (e.g. single-stat-hero
  treatment for the Goal Card, compare-contrast for decisions, timeline for phases),
  write a short brief, then generate. Output: ONE complete HTML document between
  `<!-- BEGIN RENDER -->` / `<!-- END RENDER -->` sentinels. Hard prompt rules (each one
  enforced downstream by 3b's deterministic gate — the prompt states them, the gate proves
  them):
  - self-contained single file: CSS inline, no CDN fonts, no external fetches beyond the
    FR-028 sanctioned `/static/htmx.min.js` + `/static/requirements_comments.js` +
    `data-goal-slug` on `<body>`;
  - zero `id=` and zero `data-block-anchor` attributes; each requirement unit one
    contiguous semantic `<section>`/`<li>` under a real `<h2>`/`<h3>` (US7/FR-012/FR-013);
  - every canonical id from the WHAT doc emitted **verbatim exactly once** as a small
    visible anchor label on the block that carries that unit's text; never invented,
    never renamed (FR-003);
  - **verbatim carriage:** each unit's anchorable text (its source body with inline
    markdown stripped) appears verbatim and contiguous within that unit's container —
    layout, ordering, and section names may vary freely around it;
  - the HOW layer never invents the WHAT: content comes from the WHAT doc + source only;
  - empty recipe blocks are omitted, never padded (US2 Scenario 2).
- **Write both `config.yaml`s** following the carve-out precedent
  (`cast-comment-reanchor`): `dispatch_mode: subagent`, `interactive: false`,
  `context_mode: lightweight`, `allowed_delegations: []`; `timeout_minutes: 15` (WHAT) /
  `30` (HOW). `model:` is set to the `opus` default with an explicit
  `# [USER-DEFERRED] tier knob — placeholder, do not tune here` comment (the deferred
  owner decision stays deferred; the runner reads the tier from config so tuning later is
  a one-line change).
- → Delegate: `/cast-agent-compliance` over the two new agent dirs — review output for
  allow-list, naming, and directory-convention violations.
- → Delegate: consult `/cast-agent-design-guide` (I/O contract section) while authoring —
  the WHAT/HOW I/O contracts above go in each agent's `.md` as the contract block.

**Design review:**
- **Architecture ✓** — net-new agents per the owner decision; reuse is by *inlining toolkit
  content at dispatch time*, not by importing or extending preso agents — zero coupling to
  the slide pipeline.
- **Naming ✓** — `cast-requirements-what` / `cast-requirements-how` per FR-001/FR-010/FR-012
  (the refined-requirements naming, adopted verbatim from the seed decisions).
- **Error & rescue:** the WHAT contract makes "can't place a ref" a loud, gated failure
  (`unmapped_refs` non-empty → gate fail → bounded retry → fallback) — never a silently
  dropped requirement unit.
- **Spec consistency ⚠️** — these agents' I/O is new user-facing behavior under
  `cast-requirements-render.collab.md`; the spec gains the maker contract in 3e (already a
  planned activity; flagged so 3a's contract text and 3e's spec text are written to match).

## Sub-phase 3b: The Deterministic Maker Gate Productionizes the Spike Audits

**Outcome:** A pure, I/O-free module `cast_server/requirements_render/maker_gate.py`
exposes `check_what_doc(what_doc_text, parsed) -> GateReport` and
`check_html(html, parsed) -> GateReport` (a frozen `{passed: bool, violations: [str]}`),
encoding the Phase 1 audit semantics as production gates with full unit-test coverage —
the executable definition of "structurally valid maker output" that 3c enforces and 4a
later wraps its quality loop around.

**Dependencies:** None within Phase 3 (parallel with 3a; the contract shapes are fixed by
this plan, not discovered from 3a's prompts) — **plus one hard cross-phase prerequisite: Phase 2's `strip_inline_markdown` pure helper** (plan-review CQ1; block on it, never re-implement).
**Estimated effort:** 1 session.

**Verification:** `pytest cast-server/tests/test_maker_gate.py` green, covering for each
check at least one pass and one violation fixture (fixtures adapted from the Phase 1
`spikes/1a`/`1b` evidence HTML, plus minimal synthetic violators); golden structural
assertions from `test_requirements_renderer.py` (zero-`id`) replayed against a passing
fixture to prove gate↔golden consistency — **plus an assertion that the live v2 deterministic render (`render_requirements()` output) passes `check_html` in full, not just the zero-`id` subset** (plan-review T1): 3c publishes the fallback *ungated* on the trust that the deterministic substrate is always structurally valid, so a renderer change that silently made the fallback un-gateable — with no test catching it — would be a latent catastrophe behind the safety net; this test pins the trust.

Key activities:

- **`check_what_doc`:** front matter parses; `contract`/`source_hash` match; **id-mapping
  totality** — every `Block.ref` parsed from the source appears in exactly one section's
  `block_refs`, no ref appears twice, no ref exists that the parser didn't produce
  (invented), `unmapped_refs` is empty; section titles are non-empty and none equals a
  US/FR/SC slot name (`User Stories`, `Functional Requirements`, `Success Criteria` — the
  family-communication rule made checkable).
- **`check_html` — id parity + per-block correspondence (the 1a audit, productionized):**
  the set of `US-NN`/`FR-NNN`/`SC-NNN` tokens visible in the HTML text equals the parsed
  ref set (none missing, none invented, none renamed); each id label occurs exactly once;
  and the label's enclosing block container also carries that block's anchorable text
  (FR-003 is per-block, not set-membership — the 1a plan-review sharpening, kept).
- **`check_html` — verbatim carriage (the 1b harness, productionized):** per US/FR/SC
  block, derive the anchorable text = block body with inline markdown stripped (import
  the Phase 2 `strip_inline_markdown` helper from `goal_card.py`), then assert it appears
  verbatim and contiguous within ONE semantic container — using the exact
  `requirements_comments.js` placement semantics (stdlib `HTMLParser`, concatenate
  descendant text nodes per container, `find()`), hit valid only inside that block's
  container. Whitespace handling stays byte-faithful to the JS walker (the 1b
  harness-fidelity rule); the deliberately-split-across-inline-elements self-test case
  carries over as a unit test.
- **`check_html` — DOM + self-containment contract:** zero `id=` (no exceptions in the
  canonical render), zero `data-block-anchor`; no external `src`/`href` fetches beyond the
  two FR-028 sanctioned scripts; no CDN fonts; `data-goal-slug` present on `<body>`; a
  real `<h2>`/`<h3>` heading hierarchy exists.
- **`GateReport` violations are prompt-ready strings** (e.g. `"FR-003 label missing for
  SC-002"`, `"verbatim carriage failed for US1: …"`) — 3c feeds them back to the HOW agent
  verbatim on retry, and 4a will append checker findings to the same channel.

**Design review:**
- **Architecture ✓** — pure module beside `parser.py`/`block_diff.py`, same
  no-I/O/no-DB/no-LLM discipline as the rest of the package; the renderer never imports it
  (only the service layer does).
- **Code quality:** anchorable-text derivation is the one subtle spot — it must use the
  same inline-markdown strip the Goal Card uses (Phase 2 helper), not a new regex; a second stripper would be drift by construction. **Build-order hazard (plan-review CQ1):** Phase 2 and Phase 3 run in parallel, so `strip_inline_markdown` may not yet exist when 3b is built. The dependency is on *that one pure helper*; if Phase 2 has not landed it, 3b **blocks on the helper or lifts it to a shared pure module — it never inline-copies a second stripper** (copying is precisely the drift this flag forbids).
- **Known limitation (recorded, not solved):** a reader-selected quote spanning inline
  markdown (`some **bold** text`) can fail the v2 source-side verbatim backstop even on the
  deterministic render — a v2-inherited edge, unchanged by this plan; noted as Phase 4b
  input, not a Phase 3 gate condition.
- **Tests ✓** — every gate dimension gets a violation fixture; the gate is itself the
  acceptance machinery for FR-003/FR-007 — it must not be rubber-stamp-tested.

## Sub-phase 3c: The Render Service Runs the Maker as a Background Job

**Outcome:** A new `cast_server/services/render_job_service.py` executes the
WHAT→gate→HOW→gate→publish pipeline as a background job (single-flight per
`(goal_slug, source_hash)`), invoking both agents as tool-free `claude -p` subprocesses;
`requirements_render_service` gains the orchestrator seam: maker pipeline = primary branch,
`rerender_requirements_html`/`render_requirements()` demoted to the fallback branch,
publishing through the **unchanged** v2 atomic-write + AUTO-GENERATED header +
`source-hash` cache mechanism. The canonical `.collab.md` is structurally unwritable by
the maker (tool-free subprocess; the runner writes only the job dir and the final `.html`).

**Dependencies:** 3a + 3b.
**Estimated effort:** 2 sessions.

**Verification:**
- `pytest cast-server/tests/test_render_job_service.py` green with an **injected fake
  runner** (no LLM in default CI): happy path publishes; gate-violation → one feedback
  retry → second violation → deterministic fallback published + job `fallback` + reason
  recorded; subprocess crash/timeout/empty-output → fallback; two concurrent requests for
  the same `(slug, hash)` start exactly one job; source edited mid-job → compare-and-publish discards (`superseded`), no stale publish. These race-shaped cases are made **deterministic, not sleep-timed** (plan-review T2): the fake runner blocks on an injected latch the test releases, so "second view starts no job" and the mid-job-edit `superseded` path assert on a controlled interleaving rather than a flaky timing window.
- **Reaper test (plan-review T3):** a `render_jobs` row left `running` past the derived ceiling (A2) with no live thread is marked `failed` by the next `resolve_render`/status call and a fresh job starts — exercised by writing a stale `running` row directly and driving the ceiling check, so the restart-orphan recovery path is covered, not assumed.
- `test_fr007_readonly_guard.py` extended with a maker-path sweep: a full fake-runner
  pipeline run leaves the canonical `.collab.md` byte-identical.
- Existing service tests (`test_render_route_and_service.py` service half) stay green —
  the deterministic writer's behavior is unchanged, only its role is demoted.

Key activities:

- **`AgentRunner` seam:** a tiny protocol `run_agent(agent_name, user_msg, *, timeout_s)
  -> str`; production impl loads `agents/<name>/<name>.md` + `config.yaml` and runs
  `["claude", "-p", user_msg, "--append-system-prompt", agent_md, "--model",
  config.model, "--tools", ""]` (the `eval_render_checker.py` pattern verbatim);
  tests inject fakes. The runner inlines all agent inputs (source text, block inventory,
  classification, recipe vocabulary; toolkit + archetypes for HOW) into `user_msg`.
- **Pipeline stages as named functions** (the 4a seam): `run_what` → `gate_what`
  (`check_what_doc`) → `run_how` → `gate_html` (`check_html`) → `publish`. On a
  `gate_html`/`gate_what` violation: ONE structural retry of the failing stage with the
  `GateReport.violations` appended to the prompt; a second violation → **fallback**.
  Phase 4a will insert its checker + quality-driven rework loop between `gate_html` and
  `publish` and replace the fallback-on-quality branch with best-attempt-plus-flag; the
  stage seam is designed so 4a adds a stage, not a rewrite.
- **Fallback branch (the demotion):** crash, timeout, empty/unparseable output — **strict sentinel extraction** takes content from the *first* `<!-- BEGIN RENDER -->` to the *first* following `<!-- END RENDER -->`; missing, mis-ordered, or duplicate sentinels, a markdown-fenced/chatty wrapper around them, or unparseable WHAT front matter all count as no-output (the HOW agent's prose can never be silently truncated into a partial render) (plan-review CQ2) — or structural-gate exhaustion → call the existing
  `rerender_requirements_html` deterministic path and record `status=fallback` + the
  reason on the job row. This is the FR-006 "true no-output" branch; structural-gate
  exhaustion is classified as no-*usable*-output (see Decisions Made Autonomously #4).
- **Publish:** wrap the maker HTML in the same `AUTO-GENERATED` header +
  `source-hash: <h>` comment and `_atomic_write` it to `goals/{slug}/
  refined_requirements.html` — the v2 cache mechanism, byte-for-byte the same envelope,
  reused unchanged (FR-005/SC-005). **Compare-and-publish:** re-read the source hash at
  publish time; if it moved, mark the job `superseded` and write nothing (the next view
  starts a fresh job against the new hash).
- **Single-flight + threading model:** module-level registry `dict[(slug, hash), Job]`
  guarded by a `threading.Lock`; one daemon `threading.Thread` per job running
  `subprocess.run(..., timeout=...)` synchronously (page routes are sync `def` and run in
  the threadpool — threads avoid any event-loop interplay; the asyncio dispatcher/relay
  precedents in `app.py` stay untouched). A **global in-flight ceiling** — a bounded semaphore (config-driven, small default, e.g. 3) over distinct `(slug, hash)` jobs — caps concurrent maker subprocesses: single-flight dedupes *one* source but says nothing about a burst across *many* sources (a script touching many sources, many goals viewed at once), which could otherwise fork unbounded `claude -p` processes and exhaust memory / cascade API rate limits. Past the ceiling a new view serves the generating state and the job waits for a slot. This is a resource-safety guard analogous to the owner-sanctioned "high anti-infinite-loop safety ceiling," **not** a cost/latency constraint — cost and model tier remain explicitly unconstrained per the owner decision (plan-review P1).
- **`render_jobs` DB table** (schema.sql + the migration test pattern): `id`, `goal_slug`,
  `source_hash`, `status` (`running` | `published` | `fallback` | `superseded` | `failed`),
  `attempts`, `error`, `started_at`, `finished_at`. Rows are the observability/status
  surface and the seam where 4a will record its human-review flag; **readiness is never
  derived from the table** — the artifact's embedded `source-hash` is the single source of
  truth (see 3d). Orphaned `running` rows (server restart mid-job) are reaped lazily. The **reaper ceiling is defined concretely** as a generous multiple (≥2×) of the agents' summed worst-case attempt timeouts read from `config.yaml` (`what_timeout + how_timeout`, doubled for the one structural retry) — never a magic constant — so a slow-but-live job is never reaped mid-flight. After a restart the in-memory registry is empty, so the ceiling (not the registry check) is the real guard: a row `running` past that wall-clock bound is marked `failed` and the next view starts a fresh job (plan-review A2).
- **Job artifact retention (observability):** each job writes `what.md`,
  `attempt-N.html`, and gate reports under `build/render-jobs/{slug}/{hash12}/`
  (a new `RENDER_JOBS_DIR` constant in `config.py`; `build/` is already a non-goal,
  non-CI-collected runtime area) — never inside `goals/{slug}/` (FR-026 folder invariant
  stays trivially intact).
- **Stub short-circuit:** the service resolves stub/missing sources BEFORE any job logic —
  `is_stub(parsed)` → the deterministic prompt-to-begin render exactly as today (US1
  Scenario 2 unchanged); the maker is never invoked for a stub.

**Design review:**
- **Architecture ✓** — service owns all I/O and subprocess work; `requirements_render/`
  stays pure; mirrors the v2 renderer/service split.
- **Error & rescue (zero silent failures):** every terminal job state (`published`,
  `fallback`, `superseded`, `failed`) is a recorded row with a reason; fallback is never
  silent — the job row says why the reader is seeing the plain page.
- **Security:** agents run `--tools ""` — no filesystem, no network; the maker cannot
  write the canonical source *by construction*, not by convention (FR-008). The runner
  writes only `RENDER_JOBS_DIR` + the atomic `.html` publish. Slug is DB-validated before
  any path is built (the existing path-traversal rule). Subprocess env is cleaned to the production precedent in `agent_service.py` — **`env -u CLAUDECODE`** (a `claude -p` that inherits a parent Claude session's `CLAUDECODE`/working-dir context can hang or recurse), an explicit job-dir cwd, and `_clean_child_env`-style hygiene. The cited `eval_*` precedents live in `cast-server/tests/` (harness code); the only *production* server-side `claude -p` is `agent_service.py`'s `/context` call, so this runner is net-new request-path subprocess code and must not under-specify env isolation (plan-review A1).
- **Spec consistency ⚠️** — US2/FR-003 of the render spec say stale-hash regeneration is
  synchronous via `rerender_requirements_html`; this sub-phase changes that to an async
  job on the happy path → `/cast-update-spec` in 3e (planned).
- **Performance:** the maker loop is minutes-long by design (cost is not a constraint);
  the design guarantees it never blocks a request thread — the only latency-sensitive
  paths (cached view, comment API, stub) never enter the job machinery.

## Sub-phase 3d: The Route Serves a Live Generating State and Swaps In the Finished Render

**Outcome:** `GET /goals/{slug}/render` never blocks on generation: a fresh-hash view
serves the cached file untouched (unchanged); a stale-or-missing render starts the job
(idempotent) and immediately serves a live "generating…" state — the prior stale render
with a regenerating banner when one exists, else a dedicated generating page — which polls
a new status endpoint and swaps in the finished render; stub and 404 behavior are
unchanged; the comment path is untouched and instant.

**Dependencies:** 3c.
**Estimated effort:** 1.5 sessions.

**Verification:**
- Route tests (fake runner): fresh hash → 200 served file, byte-untouched, no job; stale
  hash → 200 generating state AND exactly one job started; repeat view while running → no
  second job; after fake job completes → next poll reports `ready` and a reload serves the
  new render; stub → 200 prompt-to-begin, no job; unknown slug → 404; maker fallback →
  status reports `ready` (the deterministic page IS the render) with `served_by: fallback`
  observable on the job row.
- Status endpoint tests: `ready` iff the artifact's embedded `source-hash` equals the
  current source hash; `generating` while a job row is `running`; `failed` surfaces only
  when no servable artifact exists at all.
- Manual e2e check: edit this goal's source, open `/render` → generating state appears
  immediately; finished render swaps in without a manual reload.

Key activities:

- **`requirements_render_service.resolve_render(goal_slug, …) -> RenderResolution`** — the
  orchestrator seam's read side: a frozen result with `state ∈ {ready, stub, missing,
  generating}`, the servable path (fresh `.html`, or the stale one when generating), and
  the current `source_hash`. The route becomes a thin dispatch over this.
- **Route rework in `pages.py`:** keep slug validation → `resolve_render` → `ready`:
  serve file (today's path); `missing`/`stub`: today's prompt-to-begin/deterministic
  behavior, unchanged; `generating`: `render_job_service.ensure_job(slug, hash)`
  (idempotent) then serve the generating state with HTTP 200.
- **Generating state, two flavors:**
  - *Stale render exists:* serve the stale `.html` with a response-layer injection (before
    `</body>`) of a `.render-refreshing` banner ("This page is regenerating — you're
    reading the previous version") + a small inline poll script. The file on disk is never
    modified — injection happens on the response only, so the cache artifact stays
    byte-stable.
  - *No render yet:* a small server-rendered generating page (new
    `requirements_render/templates/generating.html.j2`, themed with the existing
    `_theme.css.j2` tokens) with the same poll script and a `<noscript>` meta-refresh
    fallback (progressive enhancement in the FR-028 spirit — content never depends on JS;
    without JS the page still converges via refresh).
  - Poll script: `fetch` the status endpoint every ~4s; on `ready`, reload (`location.
    reload()`) — the route then serves the finished render. "Swap-in" = reload-on-ready;
    **on `failed`** (the terminal no-servable-artifact state — a first-generation crash before any fallback could publish, surfaced once the reaper marks the row `failed`) the script stops polling and swaps the banner/page for a terminal "generation failed — reload to retry" affordance rather than polling forever (a stale-render-exists failure instead publishes the deterministic fallback, so status returns `ready`, not `failed`); no streaming machinery (see Decisions Made Autonomously #3) (plan-review A3).
- **Status endpoint:** `GET /goals/{slug}/render/status` (page-adjacent, in `pages.py`
  beside the render route) → JSON `{state: "ready"|"generating"|"failed", source_hash}`.
  `ready` is **derived from the artifact** (embedded hash == current source hash —
  covers both maker and fallback publishes with zero extra state); `generating` from the
  live job registry/row; `failed` only when nothing servable exists. Slug validated → 404
  as everywhere.
- **Comment path untouched:** no change to `api_requirements.py`, the comment JS, or the
  tray fragments — asserted by leaving their tests untouched and green.

**Design review:**
- **Spec consistency ⚠️** — render-spec US1/FR-001 ("returns 200 with the render") gains
  the generating-state variant; recorded for 3e's `/cast-update-spec`.
- **Architecture ✓** — status endpoint derives readiness from the artifact, not a second
  state store; one source of truth, no cache-vs-table divergence possible.
- **Error & rescue:** a render exception on the serve path keeps today's contract (existing
  `.html` left intact, plain 500, no traceback); a *job* failure never 500s a view — the
  reader gets generating → then fallback render (which reports `ready`).
- **UX/golden safety:** the banner + poll script are response-layer and slug-scoped —
  they never enter the stored artifact, so golden snapshots of the deterministic substrate
  and the byte-stable cache contract are unaffected.
- **Naming:** `.render-refreshing` banner class lives in `_theme.css.j2` next to Phase 2's
  `.comment-affordance` additions — same convention, no inline styles.

## Sub-phase 3e: The Spec Records the Maker Happy Path, and the Pipeline Proves Itself End-to-End

**Outcome:** `cast-requirements-render.collab.md` (v2 → v3) records the new contract —
maker as happy path, deterministic renderer demoted to fallback, the generating-state
route behavior, the logical id-backbone as a maker-emitted non-DOM structure, and the
**verbatim-carriage clause** — and the full Phase 3 verification sweep passes against two
real families.

**Dependencies:** 3a–3d.
**Estimated effort:** 1 session.

**Verification (the phase gate, from the high-level plan):**
- End-to-end via the real pipeline (eval harness, not CI): this goal (`new_initiative`)
  and the Phase 1a `bug_fix` fixture doc render through WHAT→HOW; the two pages are
  visibly distinct with family-appropriate section names (assert: section-heading sets
  differ between the two renders and contain no US/FR/SC slot names) — plus the
  human-eyeball browser pass recorded as a carry-forward item (autonomous runs cannot
  drive a browser; static verdicts never block).
- `check_html` green on both: every canonical unit mapped to its logical id, none
  invented (FR-003); single self-contained file (FR-007).
- `test_fr007_readonly_guard.py` maker sweep green: canonical `.collab.md` never written.
- Generating-state e2e: changed source serves the generating state immediately and the
  finished render swaps in (manual + the fake-runner route tests from 3d).
- `bin/cast-spec-checker` green on the updated spec; `docs/specs/_registry.md` row bumped.

Key activities:

- → Delegate: `/cast-update-spec` on `cast-requirements-render.collab.md` with these
  deltas (review the diff before approval, per the skill's gate):
  1. **Happy path inversion:** the render is produced by the `cast-requirements-what` →
     `cast-requirements-how` pipeline; `render_requirements()` and
     `rerender_requirements_html` are the **fallback** branch, served only on true
     no-output maker failure (crash/timeout/empty/structurally-unusable output) —
     supersedes US2 Scenario 2 / FR-003's synchronous-regen wording.
  2. **Generating-state route behavior:** on a stale/missing render,
     `GET /goals/{slug}/render` starts a background job and serves a live generating
     state (stale render + banner when available) that polls
     `GET /goals/{slug}/render/status` and swaps in on `ready`; cached views, stubs,
     404s, and the comment API are unchanged and never wait on generation.
  3. **The logical id backbone as a non-DOM structure:** canonical `US-NN`/`FR-NNN`/
     `SC-NNN` ids are assigned upstream by the deterministic parser; the maker emits them
     verbatim, exactly once each, as visible anchor labels — the DOM contract
     (US7/FR-012/FR-013: zero `id=`, zero `data-block-anchor`, quote anchoring) is
     **explicitly preserved**, and the WHAT-doc id mapping is the structure the Phase 4b
     diff agent will read.
  4. **The verbatim-carriage clause (the Phase 1 carry-forward, mandatory):** the maker
     contract REQUIRES each requirement unit's anchorable text — its source body with
     inline markdown stripped — to appear verbatim and contiguous within one semantic
     container in the served DOM. Rationale recorded with it: the real orphan-exposure is
     silent `<mark>`-placement loss on a paraphrased DOM, not DB orphaning (anchor
     validation is source-side and the maker never writes the source).
  5. **Determinism scope narrowed:** SC-002's byte-stable/golden guarantee now covers the
     deterministic **fallback substrate** (and the unchanged cache envelope), not the
     happy path; the LLM-judged verification layer replacing the happy-path gate is
     recorded as Phase 4a scope, not specified here.
  6. New surfaces appended to `linked_files`: the two agent dirs, `maker_gate.py`,
     `render_job_service.py`, `generating.html.j2`.
- **Run the full sweep** (activities above) and record results + the human-eyeball
  carry-forward in the goal's artifacts.
- **Hand-off notes for 4a/4b** (one short section in the goal dir): where the checker
  stage slots in (between `gate_html` and `publish`), where the human-review flag lands
  (the `render_jobs` row), and where the WHAT-doc id mapping lives for the diff agent.

**Design review:**
- **Spec consistency ✓ (this IS the spec work)** — all four flagged conflicts from 3a/3c/3d
  resolve here in one `/cast-update-spec` pass; the DOM contract is asserted unchanged.
- **Process:** spec update lands AFTER 3a–3d exist but the clause texts were fixed by this
  plan up front — the spec records behavior, it does not retro-discover it.

---

## Build Order

```
Sub-phase 3a (agents + contracts) ──┐
                                    ├──► Sub-phase 3c (render job service) ──► 3d (route + generating state) ──► 3e (spec + e2e gate)
Sub-phase 3b (deterministic gate) ──┘
```

**Critical path:** 3a/3b (parallel) → 3c → 3d → 3e. Total **5.5–7 sessions**, matching the
high-level estimate (5-7 including the render-job + status surface).

## Design Review Flags

| Sub-phase | Flag | Action |
|-----------|------|--------|
| 3a | Maker I/O is new spec'd behavior; contract text must match the spec | Contract clauses fixed in this plan; `/cast-update-spec` in 3e records them verbatim |
| 3a | Agent allow-list/conventions drift | `/cast-agent-compliance` audit in 3a verification |
| 3b | A second inline-markdown stripper would drift from the Goal Card | Import Phase 2's `strip_inline_markdown` from `goal_card.py`; never re-implement |
| 3b | Quotes spanning inline markdown can fail the source-side backstop (v2-inherited) | Recorded as known limitation + Phase 4b input; not a Phase 3 gate condition |
| 3c | Stale-hash regen is spec'd synchronous (US2/FR-003 v2) | `/cast-update-spec` delta #1/#2 in 3e |
| 3c | Maker could write canonical source | Tool-free subprocess (`--tools ""`) + readonly-guard maker sweep |
| 3c | Server restart orphans `running` job rows | Lazy reaper: `running` past ceiling with no live thread → `failed`; next view restarts |
| 3c | Source edited mid-job → stale publish | Compare-and-publish: re-check hash at publish, else `superseded` |
| 3d | Route 200-with-render contract gains a generating-state variant | `/cast-update-spec` delta #2 in 3e |
| 3d | Banner/poll script leaking into the cached artifact would break byte-stability | Response-layer injection only; artifact on disk never modified |
| 3e | Spec version bump + registry row | Included in the `/cast-update-spec` activity |

## Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent-generated output can't reliably clear the structural gate (hand-crafted 1a HTML flattered the maker) | High | The 1a gate proved the ceiling; 3c's violation-feedback retry gives the agent the exact failing clause; persistent failure degrades safely to the deterministic fallback + recorded reason — the reader never sees a broken page. 4a's quality loop strengthens this further |
| `claude -p` subprocess flakiness (CLI exit ≠ 0, truncated stdout, rate limits) | Med | Sentinel-marker extraction + empty/unparseable ⇒ no-output branch ⇒ fallback; one structural retry; job row records the raw failure for diagnosis; timeout from agent config |
| Inlining the toolkit + archetypes blows the WHAT/HOW context | Low | Cost/model-tier explicitly not constraints (owner decision); HOW gets toolkit + archetypes, WHAT gets only source + inventory + vocabulary — payloads are asymmetric by design |
| Thread-based job runner races (double job, lost registry entry) | Med | Single-flight keyed registry under one lock; idempotent `ensure_job`; concurrency unit tests in 3c verification |
| Burst of distinct-source views forks unbounded `claude -p` subprocesses (memory / rate-limit cascade) | Med | Global in-flight semaphore (config-driven) over distinct `(slug, hash)` jobs; past the ceiling, views serve the generating state and queue for a slot (plan-review P1) |
| Generating-state UX confuses readers (stale content without noticing the banner) | Low | Banner is visually distinct (`.render-refreshing`, themed), and the page self-swaps on ready; human-eyeball pass carried forward |
| Route tests asserting synchronous regen break | Low (planned) | 3d updates route-level tests to the new contract; service-level deterministic-writer tests stay green unchanged |

## Open Questions

- None blocking. The single goal-level open item remains the **[USER-DEFERRED]**
  maker/checker model tier — honored here by reading `model:` from each agent's
  `config.yaml` (placeholder `opus` + an explicit tuning-knob comment), so the later
  decision is a config edit, not a code change.

## Decisions Made Autonomously (per the autonomous-run instruction)

1. **Agent execution mechanism: tool-free `claude -p` subprocesses from a new
   `render_job_service`,** not the tmux HTTP dispatcher. Grounds: the dispatcher opens a
   visible terminal ("real headless dispatch is a separate follow-up", `agent_service.py`);
   a page view must never pop a terminal; `eval_render_checker.py` and the `/context`
   breakdown are existing server-side `claude -p` precedents; `--tools ""` makes FR-008
   (maker never writes canonical) structural rather than behavioral.
2. **Job state architecture:** readiness derived from the artifact's embedded
   `source-hash` (the v2 cache IS the state); a `render_jobs` DB table only for
   observability, failure reasons, and the 4a human-review-flag seam; in-memory
   single-flight registry + per-job daemon thread (sync routes ⇒ threads over asyncio).
3. **Poll over stream; swap-in = reload-on-ready.** A 4-second status poll + reload is
   the whole surface; SSE/streaming buys nothing for a minutes-long job and adds a
   connection-lifetime liability. `<noscript>` meta-refresh keeps the no-JS path
   convergent (FR-028 spirit).
4. **Structurally-unusable output is classified as the no-output branch** (deterministic
   fallback), not as 4a-style non-convergence. Grounds: serving HTML with missing/invented
   ids or broken verbatim carriage would silently break mark placement — exactly the v2
   load-bearing rule "deterministic machinery where being wrong means silent data loss."
   The owner's best-attempt-plus-flag decision governs the 4a *quality* bar
   (comprehension/visual), which this plan does not touch; one bounded structural retry
   (with violation feedback) runs before falling back. If the owner prefers
   best-attempt-plus-flag even for structural violations, that is a 4a-adjacent revisit —
   flagged, not assumed.
   > **⛔ SUPERSEDED by the OWNER OVERRIDE banner at the top of this doc (2026-06-12).** The
   > owner *did* choose best-attempt-plus-flag for structural violations. As built: the one
   > bounded structural retry stays, but on exhaustion the best attempt is **served + flagged
   > `structural_violation`** (NOT the deterministic page); deterministic fallback fires only on
   > literal no-output. In-block placement misses surface via the `.comment-unplaced` badge.
5. **Stale-render-with-banner over a bare generating page** when a prior render exists:
   "the reader always gets the best available page" (owner fallback philosophy applied to
   the waiting state); implemented response-layer so the cached artifact stays untouched.
6. **WHAT-doc format: markdown body + machine-checkable YAML front matter** (id mapping,
   `unmapped_refs`, reserved `gaps[]`) — human-auditable like the preso WHAT docs, gateable
   like JSON; `gaps[]` reserves the Phase 5 seam with zero Phase 3 behavior.
7. **Anchorable text defined as block body with inline markdown stripped,** reusing Phase
   2's `strip_inline_markdown` — one stripper in the codebase, and the carriage gate
   measures what the comment JS actually needs (DOM text), per the 1b harness semantics.
8. **Job artifacts under `build/render-jobs/`** (new `RENDER_JOBS_DIR` in `config.py`),
   never in `goals/{slug}/` — keeps the FR-026 folder invariant trivially intact and the
   evidence inspectable.

## Suggested Revisions to Prior Sub-Phases

- None that change a decision. One coordination note: Phase 2's `strip_inline_markdown`
  is consumed here (3b anchorable-text derivation) — if Phase 2 execution renames or
  relocates that helper, 3b inherits the new name; the dependency is on the *pure helper
  in `goal_card.py`*, per the Phase 2 extract, and should be kept import-stable.

## Spec References

| Spec | Sections Referenced | Conflicts Found |
|------|---------------------|-----------------|
| `cast-requirements-render.collab.md` (Draft v2) | US1/FR-001 (route contract); US2/FR-003 (lazy sync regen — **superseded**); US4/FR-006/FR-007 (AUTO-GENERATED + read-only — preserved); US7/FR-012/FR-013 (DOM contract — preserved verbatim); FR-026 (folder invariant); FR-028 (progressive enhancement); SC-002 (determinism — scope narrowed to fallback); FR-011/FR-027 (subagent bare-output carve-out precedent the new agents follow) | 4 — all resolved by the single `/cast-update-spec` pass in 3e (happy-path inversion, generating-state route, id-backbone non-DOM structure + verbatim-carriage clause, determinism scope) |
| `cast-goal-classification.collab.md` (Draft v1) | `WorkFamily` nine-value enum; `FAMILY_RECIPES`/`RECIPE_REALIZATION` (WHAT agent starting vocabulary); classification front matter consumed by the runner | None — consumed, not modified |


---

## Plan Review Decisions (cast-plan-review, BIG CHANGE scope — autonomous)

Reviewed under HOLD scope; every fork auto-decided against the binding owner decisions in
`docs/plan/refine-requirements-better-rendering-v3-decisions-so-far.md`. **None of the
findings re-open an owner-resolved decision** (anchor backbone, background-job render,
net-new agents reusing the preso toolkit/archetypes, family-communication page vocabulary,
fallback only on true no-output failure, gap-fill change-request door, v2 hash cache reused
unchanged). All sharpen subprocess/job robustness, gate measurability, and test determinism
*within* the existing Phase-3 design. Phase 4a/4b/5 internals stayed out of scope (seams
only); planning-only — no implementation was reviewed. Per the B2 single-Write contract this
appendix and the inline body sharpenings above were committed in one write. Mirrors the depth
and appendix format of the Phase 1 review.

Summary: 9 issues found / 9 resolved / 0 deferred (Architecture 3, Code Quality 2, Tests 3,
Performance 1).

- **2026-06-12T08:35:00Z — A1 — Architecture: is the `claude -p` runner's env isolation specified to the production precedent?** — Decision: Sharpen — pin subprocess hygiene to `agent_service.py` (`env -u CLAUDECODE` + explicit cwd + clean env), not a vague `_clean_child_env`-style note. Rationale: the cited `eval_*` precedents are `cast-server/tests/` harness code; the only production server-side `claude -p` is `agent_service.py`'s `/context` call, which unsets `CLAUDECODE` — a runner that inherits a parent session's `CLAUDECODE`/cwd can hang or recurse, and this is net-new request-path subprocess code. The owner-resolved tool-free `claude -p` mechanism is unchanged. (Body patched: 3c Security.)
- **2026-06-12T08:35:00Z — A2 — Architecture: is the orphaned-`running`-row reaper ceiling a defined bound?** — Decision: Sharpen — define the ceiling as a generous multiple of the agents' summed `config.yaml` timeouts (including the one structural retry), not a magic constant; after a restart the registry is empty so the ceiling is the real guard. Rationale: an undefined ceiling either reaps slow-but-live jobs or never reaps dead ones; deriving it from config makes it correct by construction and tunable alongside the timeouts. (Body patched: 3c `render_jobs` table bullet.)
- **2026-06-12T08:35:00Z — A3 — Architecture: does the generating page handle the status endpoint's `failed` terminal state?** — Decision: Sharpen — the poll script must stop on `failed` and show a terminal "generation failed — reload to retry" affordance, not poll forever. Rationale: a first-generation crash with no stale artifact and no successful fallback publish would otherwise leave the reader on a generating banner that never converges; `failed` is already a defined status value but had no client handling. Stale-render-exists failures still publish the fallback (status → `ready`), so only the no-artifact case reaches client `failed`. (Body patched: 3d Poll script.)
- **2026-06-12T08:35:00Z — CQ1 — Code Quality: is 3b's `strip_inline_markdown` import safe given Phase 2 runs in parallel?** — Decision: Sharpen — name the cross-phase prerequisite on 3b's Dependencies line and forbid an inline re-implementation: if Phase 2 has not landed the helper, 3b blocks on it or lifts it to a shared pure module, never copies it. Rationale: a copied stripper is exactly the drift the plan's own flag forbids, and the parallel build order makes the missing-helper case real rather than hypothetical. (Body patched: 3b Dependencies + Code-quality review.)
- **2026-06-12T08:35:00Z — CQ2 — Code Quality: is HOW-output sentinel extraction strict enough to reject chatty/fenced output?** — Decision: Sharpen — specify strict extraction (first `BEGIN RENDER` to first following `END RENDER`; missing/mis-ordered/duplicate sentinels or a markdown-fenced wrapper ⇒ no-output branch). Rationale: an LLM that wraps its HTML in a ```` ```html ```` fence or adds prose around the sentinels would otherwise be silently truncated into a partial render; classifying every malformed framing as no-output routes it to the safe deterministic fallback. (Body patched: 3c Fallback branch.)
- **2026-06-12T08:35:00Z — T1 — Tests: is the deterministic fallback proven to pass `check_html` in full?** — Decision: Sharpen — add a gate-test asserting the live `render_requirements()` output passes `check_html` entirely, not just the zero-`id` golden subset. Rationale: 3c publishes the fallback *ungated* on the trust that the deterministic substrate is always structurally valid; without this test a future renderer change could make the fallback itself un-gateable and no test would catch it — a latent catastrophe behind the safety net. (Body patched: 3b Verification.)
- **2026-06-12T08:35:00Z — T2 — Tests: are the single-flight / `superseded` race tests deterministic or timing-based?** — Decision: Sharpen — require a fake-runner latch the test releases, so the concurrency and mid-job-edit cases assert on a controlled interleaving, not a sleep window. Rationale: thread-race tests written against wall-clock timing are flaky by construction; an injected synchronization point makes them deterministic, matching the well-tested/non-flaky bar. (Body patched: 3c Verification.)
- **2026-06-12T08:35:00Z — T3 — Tests: is the lazy reaper covered by a test?** — Decision: Sharpen — add an explicit reaper test (a `running` row past the A2 ceiling with no live thread → next resolve/status marks it `failed` and starts a fresh job). Rationale: the reaper is an error-recovery path with no listed coverage; restart-orphan handling is exactly the kind of failure mode that rots silently without a test. (Body patched: 3c Verification.)
- **2026-06-12T08:35:00Z — P1 — Performance: is there a global ceiling on concurrent maker subprocesses?** — Decision: Sharpen — add a small global in-flight semaphore (config-driven) over distinct `(slug, hash)` jobs; past it, views serve the generating state and wait for a slot. Rationale: single-flight dedupes one source but not a burst across many sources, which could fork unbounded `claude -p` processes and exhaust memory / cascade rate limits; this is a resource-safety guard analogous to the owner-sanctioned anti-infinite-loop ceiling — explicitly **not** a cost/latency constraint (those remain unconstrained per the owner decision). (Body patched: 3c threading model + Key Risks.)
