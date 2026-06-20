---
feature: cast-agent-definition
module: cast-agents
linked_files:
  - skills/cast-agent-design-guide/SKILL.md
  - skills/cast-agent-compliance/SKILL.md
  - docs/specs/cast-delegation-contract.collab.md
  - docs/specs/cast-output-json-contract.collab.md
  - docs/specs/cast-init-conventions.collab.md
  - docs/specs/cast-maker-checker-contract.collab.md
  - bin/generate-skills
  - bin/set-proactive-defaults.py
last_verified: "2026-06-19"
---

# Cast Agent-Definition Contract — Spec

> One-line: the canonical frontmatter for a cast-* agent (`agents/<name>/<name>.md`).
> It **reuses the harness-native keys as-is** and adds a namespaced **`cast:`** block for
> the DieCast/neoorg contract (role, pairing, context, stakes, autonomy, tags). The
> single home for the cast extension fields.

**Scope:** two zones of frontmatter — **Zone 1** the Claude Code-native keys we reuse
(`name`/`description`/`model`/`tools`/`memory`/`effort`/`permissionMode`/`maxTurns`/
`isolation`/…), and **Zone 2** the `cast:` namespace (`role`, `checked_by`/`checks`/
`checklist`/`verdict_contract`/`fresh_context`, `context_contract`, `stakes`, `autonomy`,
`tags`, `allowed_subagent_delegations`/`allowed_session_delegations`, `dispatch_mode`,
`proactive`, `evaluation`, `governed_by`, `aggregates`). Plus the defaults-cascade
(DRY), the override lifecycle, and `cast-agent-compliance` validation.

**Version:** 3 | **Updated:** 2026-06-19 — forward-facing cleanup: all agents are being
re-created against this spec, so the migration/coexistence framing is dropped —
`config.yaml` is **retired** (all config in frontmatter), `context_contract` is the
per-agent I/O source of truth (README a generated view), and the cast enums live in a
code module this spec documents. v2 — restructured to two zones after review:
reuse native keys (incl. `model: inherit`); split `allowed_delegations` →
`allowed_subagent_delegations` / `allowed_session_delegations`; `coordinator` →
`team_coordinator`; `decision_weight` → `stakes`; add `autonomy`
(`inherit|manual|low|medium|high`) and `tags`; role-based `memory` default; DRY via a
tooling defaults-cascade (Claude has no native cross-file DRY). **This spec keeps
evolving — new cast fields land in the `cast:` block here and bump the version.**
v1 (2026-06-19): initial flat schema.

**Status:** Draft

---

## Intent

This spec defines the **forward-facing** agent frontmatter — the single declarative
surface for every (re-created) cast-* agent. **All declarative config lives in the agent
`.md` frontmatter; `config.yaml` is retired.** It supersedes the old scattered approach
(thin `.md` frontmatter + a sibling `config.yaml` with `model` duplicated + the I/O
contract in README prose, with the richer dimensions — context contract, stakes,
autonomy, maker↔checker pairing — declared nowhere machine-readable).

Two facts shape the fix (verified against the harness):

1. **Claude Code already provides many keys natively** — so we **reuse**, never reinvent.
2. **Claude Code has no cross-file DRY** (no `extends:`/`$ref:`/include, no settings
   cascade, YAML anchors don't cross files) — so the "don't repeat standard flags" must be
   **our tooling**, and our extension fields are **namespaced under `cast:`** to keep the
   standard-vs-neoorg split clean and survive future native keys.

The result is one canonical, lintable, evolvable surface `cast-agent-compliance` can
enforce (e.g. "every maker has a registered, existing checker").

## Harness reality (Claude Code) — what we reuse vs. must build

- **Native frontmatter keys (reused):** `name`, `description`, `model`,
  `tools`/`disallowedTools`, `memory`, `effort`, `permissionMode`, `maxTurns`,
  `isolation`, `background`, `skills`, `mcpServers`, `hooks`, `color`.
- **`model: inherit`** is the native "use the caller's model"; it is the default when
  omitted. **Omitting `tools`** inherits all tools. **Omitting `effort`** inherits the
  session/caller effort. We lean on these for DRY.
- **No native cross-file DRY, no agent-defaults cascade, no tag/category field, unknown
  keys tolerated-but-undocumented.** → our extensions live under `cast:` (one tolerated
  key holding a mapping, not a dozen loose custom keys), and the defaults-cascade is
  DieCast tooling.
- **`permissionMode` is NOT our autonomy knob.** It governs harness permission-to-act
  (edits/tools); we run permissive (`bypassPermissions`/auto) and model decision autonomy
  ourselves in `cast.autonomy`.

## Not Included (no duplication — the boundaries)

Owns the **declaration** only; cross-references, never re-defines:

| Concern | Owned by |
|---------|----------|
| The native keys' own semantics | the Claude Code harness (we reuse, don't redefine) |
| Runtime output envelope (`.agent-run_*.output.json`, status set, `human_action_needed`) | `cast-output-json-contract.collab.md` |
| Delegation mechanics (output-file naming, polling, idle timeout) | `cast-delegation-contract.collab.md` — here we only *declare* the allow-lists + `dispatch_mode` |
| File authorship suffixes, write paths | `cast-init-conventions.collab.md` |
| Requirements-*document* front-matter (`classification.*`) | `cast-goal-classification.collab.md` |
| Maker/checker *behavior* (`CheckResult`, gate, rework loop, enforcement) | `cast-maker-checker-contract.collab.md` — here we declare only the *pairing* |
| Authoring guidance (philosophy, when-to-use, directory skeleton) | `cast-agent-design-guide` (skill) |

## The two zones

### Zone 1 — harness-native keys (reused as-is)

| Key | How we use it |
|-----|---------------|
| `name` | REQUIRED. kebab-case id; verdict-renderers end in `-checker`. |
| `description` | REQUIRED. one paragraph + trigger phrases; discovery + registry. |
| `model` | default **`inherit`** (caller's model); or `opus`/`sonnet`/`haiku`/`fable`/`<id>`. The single source of truth for the tier. |
| `tools` / `disallowedTools` | omit `tools` → inherit all; set to restrict. |
| `memory` | **role-based default** (see Zone 2 `role`): makers → `user`/`project`; checkers → `none` (neutrality). |
| `effort` | omit → inherit session effort; or `low|medium|high|xhigh|max`. |
| `permissionMode` | set permissive (`bypassPermissions`/auto). **Not the autonomy knob** — that's `cast.autonomy`. |
| `maxTurns`, `isolation`, `background`, `skills`, `mcpServers`, `hooks`, `color` | used as the harness defines them, when needed. |

### Zone 2 — the `cast:` namespace (the DieCast/neoorg contract)

```yaml
# ── Zone 1: native (Claude Code reads these) ──
name: cast-<base>
description: >
  <what this agent does>. Trigger phrases: "...", "...".
model: inherit                         # default = caller's model; or opus|sonnet|haiku|fable|<id>
memory: user                           # role-based default (maker→user/project, checker→none)
# effort / tools omitted → inherit session effort / all tools
permissionMode: bypassPermissions      # run permissive; NOT our autonomy knob (see cast.autonomy)

# ── Zone 2: the cast: namespace (DieCast/neoorg — kept separate from the standard keys) ──
cast:
  role: maker                          # REQUIRED. maker | checker | team_coordinator | orchestrator | tool.
  stakes: L2                           # how costly THIS agent's output is to get wrong (L1|L2|L3) →
                                       #   sets the checker's default enforcement. (Output-side; ≠ autonomy.)
  autonomy: inherit                    # how much it decides locally vs escalates:
                                       #   inherit (caller's) | manual | low | medium | high.
                                       #   manual = surface every decision … high = decide end-to-end, escalate only blockers.
  tags: [eng, backend]                 # org/domain tags for DISCOVERY (no native tag field). e.g. eng, marketing, data.
  context_contract:                    # THIS agent's I/O (the universal output/delegation contract is inherited, not redeclared).
    reads:    []
    writes:   []
    requires: []
    produces: []
  dispatch_mode: http                  # http = full child-run (delegation + output-json); subagent = bare result, outside them.
  allowed_subagent_delegations: []     # targets it may call AS A SUBAGENT (Task/inline; shared context; no output.json).
  allowed_session_delegations: []      # targets it may call AS A SESSION (HTTP/tmux; isolated; own run + output.json).
  proactive: false                     # next_steps render mode (cast-delegation-contract US14).
  evaluation:                          # evaluability surface (L-E; deep design owed — maker-checker §10).
    sample_output: <path>
    benchmark:     <path>
  governed_by: []                      # spec(s) this agent obeys (audit trail), e.g. the maker-checker contract.
```

> **DRY:** omit any key whose default is right — the defaults-cascade fills it (below).
> `model`/`autonomy` use `inherit`; `tools`/`effort` use omission. So a typical agent
> declares only its **deltas** from the defaults.

> **The I/O contract:** `context_contract` is the **per-agent** I/O and the *source of
> truth* — machine-readable and lintable. The **universal** contract (the output-json
> envelope + the delegation protocol) is common to every agent and inherited via
> `governed_by` + the other specs; it is **never redeclared per agent**. Any human-facing
> README is a **generated/thin rendering** of `context_contract`, not a separately-authored
> contract.

### MAKER delta (`cast.role: maker`)

```yaml
cast:
  role: maker
  produces: <artifact kind/path>       # mirrors context_contract.produces.
  checked_by:                          # REQUIRED. L-A: no maker ships without a checker. ONE OR MORE; each MUST exist.
    - cast-<base>-checker
    - cast-<base>-tone-checker         # add specialists for separable concerns.
  stakes: L2                           # default stakes of this maker's output (a per-rule weight in the checklist can override).
  autonomy: medium                     # e.g. settles routine/convention calls; escalates architectural/irreversible ones.
# No cast.checks / cast.checklist on a maker.
```

### CHECKER delta (`cast.role: checker`)

```yaml
cast:
  role: checker
  checks:                              # REQUIRED. the maker(s)/artifact it verifies; MUST exist.
    - cast-<base>
  checklist: checks/<base>.checklist.md # REQUIRED (rec). externalized, stable CHK-IDs; the maker reads the SAME file as its self-gate.
  verdict_contract: cast-check/v1      # the CheckResult shape it emits; the gate is code-owned.
  fresh_context: true                  # REQUIRED for LLM-judged checks: sees ONLY the artifact (neutrality).
                                       #   Re-run/tool gates (pylint, mypy, pytest-cov) set this false — they decide by re-running.
  dispatch_mode: subagent              # typical for bare-JSON checkers (CheckResult as final text).
# Zone-1 memory defaults to none for checkers (neutrality). model SHOULD differ from the maker's tier where feasible.
# No cast.checked_by on a checker.
```

### TEAM_COORDINATOR delta (`cast.role: team_coordinator`) — the team-lead

A **team_coordinator is a team lead**: it owns a *squad* of agents (makers and/or
checkers), fans work out, runs the cross-cutting/adversarial pass no single member can,
aggregates, and escalates upward. Checker-fan-out is one instance.

```yaml
cast:
  role: team_coordinator
  checks:                              # the maker whose output it gates (indirectly, via the squad).
    - cast-<base>
  aggregates:                          # the squad it dispatches and aggregates.
    - cast-<base>-content-checker
    - cast-<base>-tone-checker
    - cast-<base>-visual-checker
  allowed_subagent_delegations: [ <same squad> ]   # or allowed_session_delegations, per how it dispatches them.
# Aggregation rule (maker-checker §8): all-PASS + adversarial → approve; any-FAIL → rework;
#   worst-dimension score wins; oscillation in any dimension → escalate.
```

> **Why a team_coordinator and not the maker alone** (worked example): one preso *slide
> maker* is checked by **content + tone + visual** specialists. The team_coordinator adds
> what no single specialist can — it runs them in parallel, then a **cross-cutting
> adversarial pass** ("if you cut 50%, what survives?", "what would a skeptic reject?"),
> and aggregates. It is **optional** — only for separable concerns; a 1:1 maker→checker
> needs none.

## Autonomy & stakes — the two cast decision knobs (kept distinct)

These look similar but are orthogonal; conflating them was the v1 confusion.

| | `cast.stakes` | `cast.autonomy` |
|--|---------------|-----------------|
| On | the **output** | the **agent** |
| Answers | how bad if it's wrong | how much it decides alone |
| Drives | the **checker's** enforcement strictness | whether a decision is **taken locally or surfaced up** |
| Values | `L1` (irreversible) · `L2` (convention) · `L3` (local) | `inherit` · `manual` · `low` · `medium` · `high` |

- **`autonomy`** levels (escalate-vs-local): `manual` = surface every decision; `low` =
  only trivial/local calls, escalate anything consequential; `medium` = routine +
  convention calls, escalate architectural/irreversible/cross-cutting; `high` = run
  end-to-end documenting as it goes, escalate only true blockers; `inherit` = take the
  caller's level (default). Above its level, the agent escalates to its
  `team_coordinator` / parent / the human (via the escalation taxonomy).
- They **interact but are not the same**: a high-`stakes` task can run at high `autonomy`
  (the agent documents heavily *and* the checker gates hard); a low-`stakes` task under a
  `low`-autonomy agent still escalates often. Triage/escalation agents are typically
  `low`; trusted decision agents `medium`/`high`.

## DRY — the defaults-cascade (our tooling, since the harness has none)

Agents declare only **deltas**; omitted keys resolve by cascade (generalizing the
existing `set-proactive-defaults` resolution order):

```
per-invocation override  →  per-agent declared value  →  role default  →  global default
```

- Native `inherit` (`model`, `cast.autonomy`) and omission (`tools`, `effort`) are the
  harness-level DRY we ride on.
- Role defaults (e.g. `memory`: maker→`user`, checker→`none`) live in the cascade, not
  repeated per agent.
- The generator (`bin/generate-skills`) reads frontmatter-first and fills the rest.

## Override lifecycle (declared vs invocation vs runtime)

- **Declared (frontmatter)** = the agent's **defaults**.
- **Invocation-time overrides** = passed by the caller at dispatch (the Agent tool's
  `model`/`effort`/`mode` params; the delegation trigger). These beat the declared
  defaults for that run.
- **Runtime data** = the `delegation_context` / instructions (cast-delegation-contract) —
  per-run inputs, not config.

## Enum source of truth

The cast enums (`role`, `autonomy`, `stakes`, `dispatch_mode`) live in **one code module**
that `cast-agent-compliance` imports; this spec is their human documentation. This mirrors
`cast-goal-classification` (the `WorkFamily` enum lives in `families.py`; the spec cites it
as "Source of truth") and prevents spec-text-vs-validator drift. Native enums
(`model`/`effort`/`memory`) stay harness-owned.

## Validation (enforced by `cast-agent-compliance`)

- Zone-1 required keys (`name`, `description`) present; `model` ∈ {`inherit`, tiers, id}.
- `cast:` block present; `cast.role` ∈ {`maker`, `checker`, `team_coordinator`,
  `orchestrator`, `tool`}.
- `cast.role: maker` → `cast.checked_by` present, ≥1, **every checker exists**; no `cast.checks`.
- `cast.role: checker` → `cast.checks` resolvable; `cast.checklist` exists if given;
  `cast.verdict_contract` set; no `cast.checked_by`.
- `cast.role: team_coordinator` → `cast.aggregates` non-empty and mirrored in an
  `allowed_*_delegations` list.
- `cast.autonomy` ∈ {`inherit`,`manual`,`low`,`medium`,`high`}; `cast.stakes` ∈ {`L1`,`L2`,`L3`}.
- Any delegated target appears in the matching `allowed_subagent_delegations` /
  `allowed_session_delegations` list (no wildcard `*`; a "call anything" escape must be an
  explicit, loud opt-in).

## Decisions

| Date | Chose | Over | Because |
|------|-------|------|---------|
| 2026-06-19 | **Two-zone**: reuse native keys + a namespaced `cast:` block | flat custom keys; redefining native keys | Reuse beats reinvention; the `cast:` namespace keeps standard-vs-neoorg separate and survives new native keys (one tolerated key, not a dozen loose ones) |
| 2026-06-19 | **DRY via a tooling defaults-cascade** + native `inherit`/omission | repeating flags per agent | Claude has **no** native cross-file DRY — confirmed; agents declare only deltas |
| 2026-06-19 | `model: inherit` as default; `effort` omit-to-inherit | inventing `model: auto` / `effort: auto` | The harness already has these exact semantics |
| 2026-06-19 | `allowed_delegations` → **`allowed_subagent_delegations` + `allowed_session_delegations`** | one blanket list | The caller controls the *mode* (subagent vs session) of each delegation |
| 2026-06-19 | `coordinator` → **`team_coordinator`** (team-lead) | a checker-only "coordinator" | Maps to the org-hierarchy analogy; generalizes beyond checker-aggregation |
| 2026-06-19 | **`autonomy`**: one cast field, `inherit\|manual\|low\|medium\|high` | a 0–1 float; reusing `permissionMode` | Named levels are actionable; `permissionMode` is harness permission-to-act, a different dimension entirely |
| 2026-06-19 | **`stakes`** (renamed from `decision_weight_default`), kept distinct from `autonomy` | the opaque `decision_weight` name; one merged knob | stakes = output criticality (drives the checker); autonomy = agent latitude (drives escalation) |
| 2026-06-19 | `memory` **role-based default** (maker→user/project, checker→none) | flat `none` / flat `user` | A stateful checker carries bias across runs (breaks neutral verification); makers want the learning loop |
| 2026-06-19 | **`tags`** for discovery (cast-namespaced) | relying on `description` only | No native tag field; org/domain tags power the discovery/marketplace surface |
| 2026-06-19 | An explicit `cast.role` field | inferring role from the `-checker` suffix | Names drift; an explicit field makes pairing rules deterministic to lint |
| 2026-06-19 | **Forward-facing**: `config.yaml` retired, all config in frontmatter | a migration/coexistence plan | All agents are being re-created against this spec — no legacy to migrate; design the best end-state |
| 2026-06-19 | `context_contract` is the **per-agent I/O source of truth**; README a generated view; the universal contract inherited via `governed_by` | authoring a parallel README I/O contract | One machine-readable, lintable surface; avoids the drift we removed for config |
| 2026-06-19 | Cast enums live in a **code module** (source of truth); this spec documents them | spec-text canonical with the validator mirroring it | The `cast-goal-classification` / `families.py` precedent; prevents spec-vs-validator drift |

## Open Questions

- **[DEFERRED — dedicated design pass: interactive propagation]** — how an
  `AskUserQuestion` from a 2nd/3rd-level agent surfaces to the human (and the answer
  returns). Native AskUserQuestion only works at the interactive root; likely an
  escalate-up-the-tree relay (via the escalation taxonomy + the `autonomy` ladder) and/or
  a cast-server question bus — but it is **owed its own design**, load-bearing for any
  multi-level flow, intentionally not decided here.

*(Resolved 2026-06-19: `config.yaml` retired (all config in frontmatter); `context_contract`
is the I/O source of truth (universal contract inherited via `governed_by`); cast enums live
in a code module documented here — see Decisions.)*

## Cross-references

- **Behavioral pair contract:** `docs/specs/cast-maker-checker-contract.collab.md` —
  declares behavior; this declares the pairing.
- **Delegation:** `cast-delegation-contract.collab.md` — the allow-lists + `dispatch_mode` are declared here; mechanics live there.
- **Runtime output:** `cast-output-json-contract.collab.md`. **File conventions:** `cast-init-conventions.collab.md`. **Authoring:** `cast-agent-design-guide` (skill).

## Evolution & versioning

New declarative fields land in the **`cast:` block** here (native additions are the
harness's to make). To add one: append it with an inline comment, add a Field-reference /
validation entry, and **bump `Version`**. Since agents are (re)created against this spec,
they are **born conforming** — there is no migration/rollout; `cast-agent-compliance`
errors on a nonconforming agent from day one.
