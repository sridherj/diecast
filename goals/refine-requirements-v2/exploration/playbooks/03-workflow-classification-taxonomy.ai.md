# Workflow Classification & Per-Family Document Shaping — Playbook

> **Step 3 of Refine Requirements v2.** Classify a goal into a work family and shape its
> requirements *document* per family — without becoming a Template Enforcer. (Routing the
> *goal* into downstream pipelines is Step 6; same classification, different effect.)

## TL;DR

Keep the owner's 5 families as **human-facing pill labels**, but **do not** build 5 rigid
templates behind them. Model the requirements document as **~6 composable blocks**
(`problem, evidence, decision, scope, question, open`); each family is just a *recipe* that
selects which blocks render. Classify once with a **single Claude strict-tool-call** that
returns `{family, confidence, reasoning, uncertainty_factors, alt_family}`, persist it as
**machine-readable front-matter** (humans read the pill, agents read the field — FR-013),
and let **code thresholds — not the model — drive the confirm-on-ambiguity gate**. The
non-obvious insight every elite source agrees on: the *loosest* family ("random ideas") is
the **default and the floor**, a deliberate first-class mode — not a degraded PRD. Structure
**accretes as confidence is earned**; it is never imposed at minute zero. This is genuine
whitespace: no shipping tool auto-classifies *and* shapes a requirements doc per family.

## Recommended Stack

| Component | Choice | Why |
|-----------|--------|-----|
| **Document data model** | **6 composable blocks** (`problem/evidence/decision/scope/question/open`) | Families-as-recipes degrade gracefully (wrong guess = one extra/missing optional block); 5 hardcoded templates fail hard (wrong guess = wrong document). Diátaxis proves shape-follows-purpose reduces to a few axes, not a flat list. |
| **Classifier** | **Claude strict tool-call** with enum-typed `family` argument | Diecast is Claude-native; a forced tool call *cannot* emit an off-taxonomy label (the structured-outputs guarantee). One call returns family + confidence + reasoning. No fine-tuning, no training data. |
| **Confidence gate** | **Code-side thresholds** (≥0.9 silent · 0.5–0.9 confirm · <0.5 forced top-2) | "Are LLM Decisions Faithful to Verbal Confidence?" shows models verbalize uncertainty but don't act on it. *You* threshold; the model never decides whether to ask. |
| **Fast pre-filter (optional)** | **Lexical signals** (lead verb, `?`, repro/stack-trace, metric) before the LLM | 4 near-free regex signals get ~80% routing accuracy with zero latency/cost; LLM only resolves the ambiguous tail. |
| **Family vocabulary** | **5 labels + 1 generic fallback**, "random ideas" = default | Maps one-for-one to real genres (PRD, Spike, bug report, notebook, Shape-Up pitch). The fallback satisfies FR-002/003 Scenario 4 by emitting `problem`-only. |
| **Persistence** | **YAML front-matter** on the requirements artifact | One classification, emitted once, consumed twice — pill for humans, field for downstream agents/router (fuses FR-002 + FR-013 + Step 6). |
| **Family → genre mapping** | Borrow **Jira Spike** terminology for non-build work | Don't invent vocabulary; "Spike" is the industry precedent for research/POC/exploration families. |

Opinionated picks only — block model **over** literal-5-templates; thresholds-in-code
**over** model-self-gating; loose-default **over** generic-fallback-on-failure.

## Implementation Steps

### Step 1: Define the 6-block document model
**Impact: High** | **Effort: ~0.5 day**

This is the keystone decision and it changes the Step 2 store. Define blocks as the atomic
units of shared understanding. A family is a *recipe* (ordered list of blocks + which are
required vs. suggested), not a file.

```python
# blocks.py — the document data model
from enum import Enum

class Block(str, Enum):
    PROBLEM  = "problem"    # what's wrong / what we want  (ALWAYS present — the writeup itself)
    EVIDENCE = "evidence"   # what we observed: repro, logs, data, links
    DECISION = "decision"   # what we'll do / chose: a verb of intent ("build", "migrate")
    SCOPE    = "scope"      # boundaries, in/out
    QUESTION = "question"   # what we're answering: a "?", "why", "whether", "investigate"
    OPEN     = "open"       # unknowns / risks  (ALWAYS allowed, NEVER required)

# Families are recipes over blocks, not separate templates.
FAMILY_RECIPES = {
    "new_initiative": [Block.PROBLEM, Block.DECISION, Block.SCOPE, Block.OPEN],   # heaviest
    "pilot_poc":      [Block.QUESTION, Block.DECISION, Block.OPEN],               # light
    "bug_fix":        [Block.PROBLEM, Block.EVIDENCE, Block.OPEN],                # minimal
    "data_research":  [Block.QUESTION, Block.EVIDENCE, Block.OPEN],               # HOW often N/A
    "random_idea":    [Block.PROBLEM],                                            # DEFAULT/floor
    "generic":        [Block.PROBLEM, Block.OPEN],                                # unmatched fallback
}
```

The win: an unclassifiable goal still emits `problem` — there is no failure state.

### Step 2: Build the classifier as a Claude strict tool-call
**Impact: High** | **Effort: ~1 day**

Force a tool call whose schema makes an invalid family *impossible*. Return confidence and
reasoning in the same call. Feed title + raw writeup; optionally prepend cheap lexical hints.

```python
CLASSIFY_TOOL = {
    "name": "classify_work_family",
    "description": "Classify a raw goal writeup into exactly one work family.",
    "input_schema": {
        "type": "object",
        "properties": {
            "family": {
                "type": "string",
                "enum": ["new_initiative", "pilot_poc", "bug_fix",
                         "data_research", "random_idea", "generic"],
                "description": (
                    "new_initiative: big goal needing architecture (PRD). "
                    "pilot_poc: small prototype to answer a question. "
                    "bug_fix: something broke; symptom+repro exists. "
                    "data_research: a question to investigate against data. "
                    "random_idea: fuzzy pre-goal ideation — DEFAULT when unsure. "
                    "generic: matches nothing above."
                ),
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reasoning": {"type": "string"},
            "uncertainty_factors": {"type": "array", "items": {"type": "string"},
                "description": "What specifically makes this hard to classify."},
            "alt_family": {"type": "string",
                "enum": ["new_initiative","pilot_poc","bug_fix","data_research","random_idea","generic"]},
        },
        "required": ["family", "confidence", "reasoning", "uncertainty_factors", "alt_family"],
    },
}
# claude.messages.create(..., tools=[CLASSIFY_TOOL], tool_choice={"type":"tool","name":"classify_work_family"})
```

Validate the returned `family` against the enum whitelist in code anyway (defence in depth);
off-schema → fall back to `random_idea`, never crash the run.

### Step 3: Gate confirm-on-ambiguity in code, not the model
**Impact: High** | **Effort: ~0.5 day**

The model returns a number; *your code* decides whether to ask. This is the direct
implementation of FR-004.

```python
def gate(result) -> dict:
    c = result["confidence"]
    if c >= 0.9:
        return {"action": "auto", "pill": result["family"]}            # silent pill
    if c >= 0.5:
        return {"action": "confirm",                                   # pill + one-click accept/override
                "pill": result["family"], "reason": result["reasoning"]}
    return {"action": "choose",                                        # forced top-2 + escape hatch
            "options": [result["family"], result["alt_family"], "random_idea"]}
```

Always include **"just notes / not sure yet"** (= `random_idea`, the loose default) in the
choose-path. The pill is *pre-filled* (accept = one click — the GitHub template-chooser
pattern), so it is a nudge, not a required field.

### Step 4: Render the family pill + persist front-matter
**Impact: High** | **Effort: ~0.5 day**

One classification, surfaced two ways. The pill goes at the top of the HTML render (Step 5
consumes it); the front-matter serves downstream agents and the Step 6 router.

```yaml
# Front-matter on refined_requirements.collab.md — machine-readable, agent-consumable (FR-013)
classification:
  family: bug_fix
  confidence: 0.82
  alt_family: data_research
  reasoning: "Describes a 500 error with a repro; no new scope introduced."
  confirmed_by: user        # user | auto | agent
  revisable: true           # NEVER binding; Step 6 re-resolves from this field
```

```html
<!-- Pill at top of HTML render — reasoning on hover -->
<span class="family-pill family-pill--bug" title="Describes a 500 error with a repro…">
  🐛 You are fixing a bug in <em>checkout flow</em>
</span>
```

### Step 5: Encode the two secondary modifiers (reversibility + uncertainty)
**Impact: Medium** | **Effort: ~0.5 day**

Modulate doc weight *within* a family — do not add families. A "bug" that is a never-seen
complex failure should pick up `question` (route to a spike shape); a one-way-door initiative
escalates to include `scope` + alternatives. Encode as block-inclusion modifiers off two
cheap signals.

```python
def modulate(recipe, signals):
    if signals.get("irreversible"):          # Type 1 door → heavier
        recipe = recipe + [Block.SCOPE]
    if signals.get("unknown_cause"):         # Cynefin complex → spike shape
        recipe = recipe + [Block.QUESTION]
    return list(dict.fromkeys(recipe))       # dedupe, preserve order
```

### Step 6: Implement the Template-Enforcer guard structurally
**Impact: High** | **Effort: ~0.5 day**

Make over-structuring *impossible* for the loose family rather than relying on discipline.
The `random_idea` renderer literally has no scope/metric/acceptance-scenario slots to fill —
it cannot pad. Structure is offered as a suggestion ("want to add scope?"), never
auto-generated as empty mandatory fields. HOW is omitted (not padded) when the family makes
it irrelevant (US1 Scenario 3 — e.g. `data_research` drops the Directional section).

### Step 7: Wire the lexical fast-path (optional, cost-saver)
**Impact: Low** | **Effort: ~0.5 day**

Skip the LLM call entirely on unambiguous writeups. ~80% accuracy from 4 signals; fall
through to the LLM on conflict/absence.

```python
import re
def fast_guess(text):
    if re.search(r"\b(traceback|stack ?trace|repro|steps to reproduce)\b", text, re.I):
        return "bug_fix"
    if re.search(r"\b(investigate|analy[sz]e|why|whether)\b", text, re.I) or text.count("?") >= 2:
        return "data_research"
    if re.search(r"\b(build|launch|ship|add|migrate)\b", text, re.I) and re.search(r"\d", text):
        return "new_initiative"
    return None   # → escalate to LLM (the semantic-router None-abstain pattern)
```

## Architecture / Process Flow

```
 raw writeup + title
        │
        ▼
 ┌─────────────────┐   None    ┌──────────────────────────┐
 │ lexical fast-   │──────────▶│ Claude strict tool-call  │
 │ path (regex)    │           │ classify_work_family     │
 └────────┬────────┘           └──────────┬───────────────┘
          │ confident hit                 │ {family, confidence,
          ▼                               ▼  reasoning, alt_family}
        ┌──────────────────────────────────────┐
        │ whitelist-validate family (code)      │  off-schema → random_idea
        └──────────────────┬───────────────────┘
                           ▼
          ┌────────────── confidence gate (CODE) ──────────────┐
          │  ≥0.9 silent      0.5–0.9 confirm      <0.5 choose  │
          └──────────────────────┬─────────────────────────────┘
                                 ▼
         ┌───────────────────────────────────────────────┐
         │ family → FAMILY_RECIPES[family]               │  + reversibility/uncertainty
         │ (ordered blocks)        + modulate(signals)   │    modifiers
         └───────────────┬───────────────────────────────┘
                         ▼
        ┌────────────────────────────────┐     ┌──────────────────────────────┐
        │ front-matter  (agents, Step 6) │◀────│ ONE classification result    │
        │ family pill   (humans, Step 5) │     │ emitted once, consumed twice │
        └────────────────────────────────┘     └──────────────────────────────┘
```

## Key Decisions

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Data model: 5 templates vs. composable blocks | **Composable blocks; families = recipes** | Every deep framework (Cynefin, Type1/2, set-based) + first-principles converge: a flat list of 5 is brittle under novelty. Blocks degrade gracefully; templates fail hard. **Owner sign-off needed — changes Step 2 store.** |
| Who decides whether to ask the user | **Code thresholds, not the model** | Models verbalize uncertainty but don't reliably act on it (arXiv faithfulness study). Gate in code or you get confident-wrong silent labels. |
| Default family when unsure | **`random_idea` (loose), not `generic`** | Shape-Up "It's Rough", Oxide "ideation", Google "informal by design" all treat low-structure as deliberate first-class. Loose default = the floor, not a failure mode. |
| Is the label binding downstream? | **No — revisable, non-binding** | Forced classification fields increase drop-off and produce noise the pipeline then trusts as signal. US6 reclassification already anticipates change; never silently anchor. |
| Classify with LLM or embeddings | **LLM strict tool-call (+ optional lexical pre-filter)** | 6-class short-doc triage: zero-shot with rich enum descriptions suffices. semantic-router is a cost optimization, not a requirement at v2 scale. |
| Reversibility/uncertainty: new families or modifiers | **Modifiers (block-inclusion), not families** | Keeps the 5-family vocabulary clean while honoring that a "bug" can be a spike. Answers Step 3 substep 1: *keep the axis, modulate it.* |
| Where the classifier lives | **One classification, shared by US2 (shape) + US6 (route)** | Overlaps Step 6's router-placement question. Emit once, persist as front-matter, consume twice — do not classify twice. |
| Long-tail families (add-tests, heavy-UI, PRD-only) | **Designed-for via block recipes, out of v2 scope** | They're just other recipes — the block model absorbs them for free later without re-architecture. |

## Pitfalls to Avoid

1. **Cementing 5 rigid templates ("concrete galoshes").** The HN-named failure: a 2-pager
   grows to 10 pages as every stakeholder adds a section, turning agile work into a waterfall
   behemoth. Blocks + recipes prevent this structurally — there is no fixed form to bloat.

2. **Letting the model self-gate the confirm prompt.** If you ask "should I ask the user?",
   RL-tuned models trend overconfident and skip the question on genuinely ambiguous input.
   Always threshold the numeric confidence in your own code.

3. **Forcing scope/metric/acceptance fields onto the `random_idea` family.** This is *the*
   Template-Enforcer anti-pattern and the spec's named risk. Fiction in a requirements doc is
   negative value — it actively misleads the next human/agent. Make those slots structurally
   absent for family #5, not merely "discouraged."

4. **Treating confirm-on-ambiguity as a required field.** Every required choice is friction
   users satisfice through (pick whatever ends the prompt) — the label becomes noise the
   pipeline trusts as signal. Pre-fill the pill (accept = one click) and always offer "just
   notes / not sure yet."

5. **Classifying up front and anchoring the frame.** The sharpest contrarian point: an early
   label installs a sticky frame at the most fragile moment (diagnostic-anchoring / "diagnosis
   momentum"). Mitigate by keeping the label **revisable and non-binding**, defaulting loose,
   and never letting it silently filter downstream evidence.

6. **Inventing new family vocabulary.** "POC", "research", "exploration" already have an
   industry name — Jira's **Spike**. Reuse known genres (PRD, Spike, bug report, notebook,
   Shape-Up pitch) so users recognize the shape instead of learning yours.

7. **Equal doc weight regardless of stakes.** A reversible two-way-door experiment should
   never carry a 7-section RFC; a one-way-door initiative warrants more. Skipping the
   reversibility/uncertainty modifiers re-introduces the "is this just overhead?" failure.

8. **Classifying twice (US2 shape + US6 route separately).** Two classifications drift and
   contradict. Emit one result, persist it as front-matter, consume it for both document
   shaping and routing.

9. **Dumping raw body text into the classifier.** GitHub's IssueCrush found structured
   metadata (title, existing labels, repo) beats raw text. Feed title + lexical signals
   alongside the body, not the body alone.

## Success Metrics

- **Family accuracy on the maintainer's corpus**: classify the real writeups across the
  three workspaces; ≥85% match human-assigned family on a held-out sample (validates the
  taxonomy empirically, per Step 1's corpus).
- **Confirm-gate calibration**: of goals the gate flags `confirm`/`choose`, ≥70% have the
  user actually change or hesitate on the label (low rate ⇒ thresholds too aggressive →
  friction; tune the 0.5/0.9 cutoffs).
- **Template-Enforcer guard holds**: 0 instances of empty/auto-padded `scope`, `metric`, or
  `acceptance` fields appearing in any `random_idea`-family render (audit N renders).
- **Generic-fallback coverage (FR-002/003 S4)**: 100% of unmatched goals still emit a valid
  `problem` block and a noted classification — no failure/crash state.
- **Agent round-trip (FR-013)**: a downstream agent reads `classification.family` from
  front-matter and routes correctly without re-running the classifier (trace 1 goal).
- **Single-classification invariant**: front-matter `family` and the Step 6 routing handle
  derive from the same field on 100% of goals (no second classification call).
- **HOW-omission (US1 S3)**: `data_research`-family renders omit the Directional section
  entirely rather than padding it (verify on 3+ research goals).

## Impact Rating: 9/10

**Justification:** This step defines the most visible output (the pill) *and* the data model
that Steps 5 (per-family render) and 6 (routing) both consume — get the families/blocks wrong
and an OSS product's users feel their work doesn't fit, while over-structuring the ideas
family kills ideation (the explicitly-named anti-pattern the whole goal is judged against).
The block-model-over-templates decision is the single highest-leverage architecture fork in
the goal and cleanly satisfies the generic-fallback and agent-consumer requirements. Not a 10
only because it depends on the Step 2 canonical-store decision to persist blocks/front-matter,
and the block-vs-5-templates fork needs owner sign-off before it can be locked.

---

### Sources (load-bearing)
- [Shape Up — Principles of Shaping](https://basecamp.com/shapeup/1.1-chapter-02) — "It's Rough"; keep early work loose.
- [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/) — informal-by-design; scale-to-scope; the don't-write-one rule.
- [Oxide RFD 1](https://rfd.shared.oxide.computer/rfd/0001) — state-as-classifier; structure accretes over time.
- [Rust RFC-0002](https://github.com/rust-lang/rfcs/blob/master/text/0002-rfc-process.html) — the explicit "what needs NO doc" list; minimal bug-fix shape.
- [Jira issue types & screen schemes](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/) — type-as-first-class-field + data-driven shape; **Spike**.
- [GitHub issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) — declarative typed fields + chooser + blank-issue escape hatch.
- [OpenAI Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) — strict enum guarantees a valid label (Claude tool-use equivalent).
- [arXiv: faithfulness to verbal confidence](https://arxiv.org/html/2601.07767) — models verbalize uncertainty but don't act on it → gate in code.
- [Aurelio semantic-router](https://github.com/aurelio-labs/semantic-router) — fast classify with built-in `None`→abstain.
- [Diátaxis](https://diataxis.fr/start-here/) — shape-follows-purpose reduces to a small set of axes, not a flat list.
- [Cynefin](https://en.wikipedia.org/wiki/Cynefin_framework) + [Type 1/2 doors](https://www.scarletink.com/p/from-one-way-to-two-way-doors-rethinking) — the modifiers that modulate doc weight within a family.
- [Typology or Taxonomy? — Cynefin Co](https://thecynefin.co/typology-or-taxonomy/) — why fixed taxonomies are "plain dangerous" under novelty.
