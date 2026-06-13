# Sub-phase 5a: The Gap Contract & the Upstream Ask Loop

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase5/_shared_context.md` before starting —
> especially the **Applied Owner-Resolved Edits** (C5 `GAPFILL_MAX_GAPS`, C6 probe-`run_how`
> independence, opus tier) and the **Data Schemas & Contracts** section (the schemas below are fixed
> there — copy verbatim, do not re-derive).

## Objective

Bring the dormant `gaps[]` seam live end-to-end on the agent side. The WHAT agent detects and
declares comprehension gaps in a machine-checkable schema; the HOW agent reports gaps it finds
through a structured trailer **outside the sentinels** ("HOW asks WHAT"); a **net-new tool-free
`cast-requirements-gapfill` agent** answers open gaps **grounded-or-refuse** from the goal's own
upstream artifacts; `render_job_service` runs the bounded ask loop as named pipeline stages; the
service validates evidence server-side (the trust boundary); and `maker_gate.py` proves every piece
deterministically. **No change-request is emitted yet** (that is 5b) — 5a ends with a validated
`gaps-state.json` per job and `emit_change_requests` present only as a stage stub.

## Dependencies

- **Requires completed:** Phase 3 (pipeline stages `run_what → gate_what → run_how → gate_html →
  publish` in `render_job_service.py`; `maker_gate.py` with `check_what_doc`/`check_html` + strict
  sentinel extraction + the public `container_text_index`; the `AgentRunner` tool-free `claude -p`
  seam; `build/render-jobs/` artifact dir; `render_jobs` table; the reserved `gaps: []` WHAT
  front-matter field) and Phase 4a (the quality loop `run_checker → decide_quality` between
  `gate_html` and `publish`; `QUALITY_*` config knobs; the reaper ceiling derived from the stage list).
- **HARD single-helper prerequisites:** `validate_evidence` **imports and reuses** the existing
  `verbatim_locate` helper (NOT a raw `str.find()`); the gap code adds **no** second `strip_inline_markdown`
  and **no** second container walker.
- **Assumed codebase state:** `config.py` reserves a "GAPFILL_* keys (Phase 5)" slot beside the
  `QUALITY_*` block (~line 209); the `cast-requirements-what`/`-how` agents exist with their
  subagent carve-out config; `parser.Block.ref` is the in-memory ref space (`US1`/`FR-008`/`SC-001`).
- **Parallel with 5c.** Shared file: `agents/cast-requirements-what/*` (additive disjoint blocks —
  5a owns the gaps-schema + gap-detection block, 5c owns the per-family vocabulary block; second
  lander merges). See the manifest seam note.

## Scope

**In scope:**
- The `gaps[]` entry schema in the WHAT contract + the gap-detection prompt rule (US7 "materially
  help the reader" bar, `GAPFILL_MAX_GAPS` cap).
- The optional `<!-- GAPS-DETECTED … -->` trailer in the HOW contract, AFTER `<!-- END RENDER -->`.
- **NET-NEW** `agents/cast-requirements-gapfill/` (tool-free subagent carve-out, opus, grounded-or-refuse).
- New named pipeline stages in `render_job_service.py`: `ask_what`, `run_gapfill`, `validate_evidence`,
  and `emit_change_requests` **as a stub** (writes `gaps-state.json` only).
- Server-side `validate_evidence` (the deterministic trust boundary, reusing `verbatim_locate`).
- `maker_gate.py` extensions: gaps-schema rules in `check_what_doc`; gap-marker correspondence in
  `check_html`; rejection of out-of-enum gap status and `GAP-NN` as a canonical ref.
- `gaps-state.json` (the single closed status vocabulary).
- `config.py`: `GAPFILL_MAX_GAPS=5`, `GAPFILL_ASK_ROUNDS=1` (C5).
- Tests: `test_maker_gate.py` + `test_render_job_service.py` extensions; the smoke note.

**Out of scope (do NOT do these):**
- Do NOT emit a real change-request (5b fills the `emit_change_requests` body). 5a's stub writes
  `gaps-state.json` and nothing into `change_requests`.
- Do NOT render `.rr-gap` markers in the HOW output yet beyond the schema/correspondence the gate
  checks — the marker *content/status vocabulary* and CSS land in 5b. (5a's `check_html`
  correspondence rule asserts the structural contract; 5b authors the themed callout + status strings.)
- Do NOT flip `WRITEBACK_GATE_POLICY` (5b owns the GATE-ALL flip).
- Do NOT touch `change_request_service.py`, the outbox, or the relay (consumed unchanged).
- Do NOT add a second `verbatim_locate` / `strip_inline_markdown` / container walker.
- Do NOT move the `GAPS-DETECTED` trailer inside the sentinels or alter strict extraction.
- Do NOT debit `QUALITY_MAX_ATTEMPTS` for the probe `run_how`, nor `QUALITY_MAX_WHAT_REWORKS` for the
  `ask_what` re-run (C6 / A2 — independent counters).
- Do NOT edit the spec (5d's single pass records 5a's flagged deltas).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-requirements-gapfill/cast-requirements-gapfill.md` | Create | Does not exist |
| `agents/cast-requirements-gapfill/config.yaml` | Create | Does not exist |
| `agents/cast-requirements-what/cast-requirements-what.md` | Modify (append block) | Has WHAT contract + reserved `gaps: []`; gains the `gaps[]` entry schema + gap-detection rule |
| `agents/cast-requirements-how/cast-requirements-how.md` | Modify (append block) | Has HOW contract + sentinels; gains the optional `GAPS-DETECTED` trailer spec |
| `cast-server/cast_server/requirements_render/maker_gate.py` | Modify | `check_what_doc`/`check_html`/`container_text_index`; gains gaps-schema + marker-correspondence + GAP-NN/status rejection |
| `cast-server/cast_server/services/render_job_service.py` | Modify | Pipeline stages exist; insert `ask_what`/`run_gapfill`/`validate_evidence`/`emit_change_requests`(stub) between `gate_what` and final `run_how`; harvest the trailer on the probe `run_how` |
| `cast-server/cast_server/config.py` | Modify (append) | Reserves the GAPFILL_* slot; add `GAPFILL_MAX_GAPS=5`, `GAPFILL_ASK_ROUNDS=1` |
| `cast-server/tests/test_maker_gate.py` | Modify | Gains gaps-schema + marker-correspondence fixtures (incl. T3 two-open-gap) |
| `cast-server/tests/test_render_job_service.py` | Modify | Gains gap-stage flow + ask-bound + crash/demotion + T2 verbatim-locate parity cases |

> Confirm exact stage-insertion points before editing:
> `grep -n "def run_what\|def gate_what\|def run_how\|def gate_html\|def run_checker\|def publish\|_execute_pipeline" cast-server/cast_server/services/render_job_service.py`.

## Detailed Steps

### Step 5a.1: Config knobs (C5)

Append to the `config.py` GAPFILL_* slot (beside the `QUALITY_*` block):

```python
# --- Gap-fill upstream-ask loop (refine-requirements-v3 Phase 5a) ---
# Gap stages run ONCE per job, BEFORE the 4a quality loop (the gap set is a property of the source,
# not a rendering attempt). These counters are INDEPENDENT of the QUALITY_* loop knobs:
#   * GAPFILL_ASK_ROUNDS bounds the pre-loop HOW-asks-WHAT re-run; it does NOT debit
#     QUALITY_MAX_WHAT_REWORKS (Plan Review A2).
#   * The pre-loop trailer-harvest run_how does NOT debit QUALITY_MAX_ATTEMPTS (Plan Review C6).
# GAPFILL_MAX_GAPS caps WHAT-declared gaps per doc — a page is communication, not an audit.
GAPFILL_MAX_GAPS = int(os.environ.get("CAST_GAPFILL_MAX_GAPS", "5"))
GAPFILL_ASK_ROUNDS = int(os.environ.get("CAST_GAPFILL_ASK_ROUNDS", "1"))
```

### Step 5a.2: The `gaps[]` entry schema + gap-detection rule (`cast-requirements-what`)

Append a "Comprehension gaps" block to the WHAT agent contract (do NOT disturb the existing
front-matter/body contract). Specify the entry schema **verbatim from `_shared_context.md`**
(`gap_id`/`section_title`/`block_refs`/`question`/`why_it_matters`), the hard rules (sequential
unique ids; every `block_refs` member a real `Block.ref`; non-empty `question`; **the WHAT doc NEVER
contains a proposed answer**), and the detection bar:

> Detect a gap only when a missing detail **would materially help the reader** (US7 language,
> verbatim). A page is communication, not an audit — do NOT hunt trivia. Declare at most
> `GAPFILL_MAX_GAPS` gaps; if more seem present, keep the highest-value ones.

→ Delegate: consult `/cast-agent-design-guide` (I/O contract section) while wording this block.

### Step 5a.3: The HOW `GAPS-DETECTED` trailer (`cast-requirements-how`)

Append an optional trailer spec to the HOW contract: a `<!-- GAPS-DETECTED\n<yaml>\n-->` block placed
**AFTER** `<!-- END RENDER -->` (outside the strict extraction window). Entries
`{section_title, question, why_it_matters}` — **no ids** (the WHAT re-run assigns them). Emphasize:
the HOW layer NEVER invents the WHAT; when it needs a missing detail it *asks* via this trailer
rather than improvising. The trailer is optional and absent on a clean render.

### Step 5a.4: NET-NEW `agents/cast-requirements-gapfill/`

Author the agent dir following the `cast-requirements-what`/`-how` carve-out EXACTLY.

`config.yaml`:
```yaml
dispatch_mode: subagent
interactive: false
allowed_delegations: []
timeout_minutes: 15
model: opus            # [USER-DEFERRED] tier knob — opus confirmed as the starting tier (2026-06-12)
```

`cast-requirements-gapfill.md` — the contract:
- **Input** (inlined by the runner — tool-free; the agent reads nothing itself): the open gap list,
  the canonical source, and the **grounding corpus** (the goal's own upstream artifacts allowlist:
  `requirements.human.md`, `research_notes.human.md`, `exploration/` summary if present).
- **Output:** one YAML doc between sentinels, per gap — the `supplied: true` shape
  (`gap_id`/`answer`/`evidence:{file,quote}`/`proposed_change:{kind:"addition", section_hint,
  proposed_body}`) or the `supplied: false` shape (`gap_id`/`reason`). Copy the schema verbatim from
  `_shared_context.md`. `kind` is **LOCKED to `addition`** (a gap is missing content, never a rewrite).
- **Hard prompt rule:** supply only what the corpus **literally** supports, with a **verbatim**
  evidence quote; **when in doubt, REFUSE.** Refusal is a correct answer — the page will say so honestly.

→ Delegate: `/cast-agent-compliance` over `cast-requirements-gapfill` + the two modified agent dirs —
review output for carve-out and config-shape violations (fix before proceeding).

### Step 5a.5: Pipeline stages in `render_job_service.py`

Insert named stages at the Phase 3 seam, between `gate_what` and the **final** `run_how`. The full
ordering becomes:

1. `run_what → gate_what` (existing).
2. `run_how` **probe** (existing call, reused) — additionally **harvest the `GAPS-DETECTED` trailer**
   from the output. **This probe does NOT debit `QUALITY_MAX_ATTEMPTS` (C6).**
3. `ask_what` (NEW, bounded): if the trailer is non-empty AND `GAPFILL_ASK_ROUNDS` budget allows
   (default 1), re-run WHAT once with the HOW questions appended; the re-run either maps a question
   to source content the first pass under-served (the gap dissolves) or confirms it into `gaps[]`.
   Re-gate (`gate_what`). **This re-run is a SEPARATE counter from `QUALITY_MAX_WHAT_REWORKS` (A2).**
4. `run_gapfill` (NEW): if open gaps exist, run `cast-requirements-gapfill` **once per job** over ALL
   open gaps. Crash / timeout / garbage output → every open gap recorded `unfilled-ask-failed` on the
   job row; the pipeline **proceeds to a marked render** (never blocks, never fabricates).
5. `validate_evidence` (NEW, deterministic — Step 5a.6).
6. `emit_change_requests` (NEW — **STUB in 5a**: writes `gaps-state.json`, emits no CR; 5b fills it).
7. `run_how` **final** (with `gaps-state.json` inlined) → `gate_html` → 4a quality loop → `publish`
   (all existing). The quality loop reworks HOW attempts against a **fixed** WHAT doc + gap state.

> **Reaper / heartbeat note (forward to 5d drift sweep):** the reaper ceiling formula derives from
> the configured stage list — it must now include `gapfill_timeout` + the ask-round WHAT re-run, and
> `heartbeat_at` must fire at each new stage boundary. Land the heartbeats here; 5d verifies the
> ceiling formula extension.

### Step 5a.6: `validate_evidence` — the trust boundary (deterministic, service-side)

For each `supplied` gap from `run_gapfill`:
- Assert `evidence.file` is in the corpus allowlist AND `evidence.quote` **verbatim-locates** in that
  file by **reusing the existing `verbatim_locate` helper** (whitespace/smart-quote tolerant — NOT a
  raw `str.find()`; Plan Review CQ2). One locate implementation shared with the v2 writeback backstop.
- Failure → demote the gap to `cannot-supply`, record `evidence-validation-failed` on the job row
  (zero silent failures). An ungrounded answer **cannot** reach the change-request door.

### Step 5a.7: `maker_gate.py` extensions (pure, fixture-tested)

- `check_what_doc` gains the `gaps[]` schema rules (Step 5a.2): unique sequential ids; every
  `block_refs` member a parsed `Block.ref`; non-empty `question`; **no answer text in the WHAT doc**;
  **reject `GAP-NN` appearing as a canonical ref** (id-space collision guard).
- `check_html` gains **gap-marker correspondence**: every open gap in the WHAT doc has **exactly one**
  `.rr-gap` container in the HTML whose text contains that gap's `question` **verbatim**, and **no
  `.rr-gap` exists without a matching gap** (a gap is never silently dropped; a marker is never
  invented). Markers are **class-based** — zero `id=`, zero `data-block-anchor`. Reuse
  `container_text_index` (no second walker).
- `check_*` reject any `gaps-state.json` `status` outside the closed enum (Step 5a.8 / A3).

### Step 5a.8: `gaps-state.json` — the single closed status vocabulary

Write the service-owned resolution record to `build/render-jobs/{slug}/{hash12}/gaps-state.json`:
`{"gaps":[{"gap_id, status, cr_id?}]}` with `status` ∈ the closed enum from `_shared_context.md`
(`cr-proposed`/`cr-applied`/`unfilled-cannot-supply`/`unfilled-declined`/`unfilled-ask-failed`). In
5a (no CR yet) the reachable statuses are `unfilled-cannot-supply` (refused or evidence-demoted) and
`unfilled-ask-failed` (gapfill crash); a `supplied`+validated gap is recorded with a provisional
state the 5b emitter promotes to `cr-proposed`/`cr-applied`. The service annotates state **beside**
the agents' docs — it never mutates them.

## Verification

Verification is the heart of this sub-phase — cover every degradation branch and the trust boundary.

### Automated Tests (permanent)

`pytest cast-server/tests/test_maker_gate.py` extended and green:
- gaps-schema **pass** fixture (well-formed `gaps[]`).
- violation fixtures, one per rule: duplicate `gap_id`; non-sequential ids; unknown `block_ref`;
  empty `question`; **answer text smuggled into the WHAT doc**; `.rr-gap` marker present with no
  matching gap; open gap with no marker; `GAP-NN` used as a canonical ref; an out-of-enum
  `gaps-state` status.
- **T3 two-open-gap fixture:** exactly two `.rr-gap` containers, each matching its own `question`
  verbatim → pass; a render that **merges** two gaps into one marker, or **swaps** their questions,
  **fails** `check_html`.

`pytest cast-server/tests/test_render_job_service.py` extended (fake runners, latch pattern from 3c):
- WHAT-declared gaps flow to `gaps-state.json`.
- HOW trailer gaps trigger **exactly ONE** WHAT re-run (`GAPFILL_ASK_ROUNDS=1` honored); a second
  trailer in the same job does NOT trigger a second re-run.
- **C6/A2 counter independence:** assert the probe `run_how` did not decrement the
  `QUALITY_MAX_ATTEMPTS` budget, and the `ask_what` re-run did not decrement
  `QUALITY_MAX_WHAT_REWORKS` (the job retains its full in-loop budgets).
- gapfill agent crash / timeout / garbage output → every open gap recorded `unfilled-ask-failed` on
  the job row; the pipeline proceeds to a marked render (never blocks, never fabricates).
- **fabricated evidence** (quote that does not `verbatim_locate` in the cited file) → demoted to
  `cannot-supply`, `evidence-validation-failed` recorded.
- **T2 verbatim-locate parity:** an `evidence.quote` differing from the corpus **only by
  whitespace/smart-quote** MUST validate (via the shared `verbatim_locate`); a substantively-different
  quote MUST demote to `cannot-supply` with the reason recorded — pinning the trust-boundary locate
  semantics against silent drift.

### Validation Scripts (temporary)
- A hand-run `claude -p` **smoke** of `cast-requirements-gapfill` over THIS goal's corpus (one
  answerable gap, one unanswerable) producing a parseable grounded-or-refuse doc — recorded as a
  smoke-run note in the sub-phase output, **not** CI.

### Manual Checks
- `grep -n "def verbatim_locate\|str.find\|def strip_inline_markdown\|def container_text_index" cast-server/cast_server/requirements_render/*.py cast-server/cast_server/services/render_job_service.py`
  — confirm `validate_evidence` calls `verbatim_locate` (no raw `find()`); confirm no second stripper
  / second walker was added.
- Confirm the `GAPS-DETECTED` trailer is parsed from AFTER `<!-- END RENDER -->` and that
  `extract_render` (the strict first-`BEGIN`→first-`END` extractor) is byte-unchanged.
- Confirm `emit_change_requests` in 5a writes **only** `gaps-state.json` and inserts **no**
  `change_requests` row (`grep -n "change_request_service" render_job_service.py` → absent in 5a).
- → Delegate: `/cast-agent-compliance` over the three agent dirs — review output for carve-out /
  config-shape violations.

### Success Criteria
- [ ] `GAPFILL_MAX_GAPS=5` + `GAPFILL_ASK_ROUNDS=1` in `config.py` with `CAST_`-prefixed env overrides.
- [ ] `cast-requirements-gapfill` exists with the tool-free subagent carve-out (`--tools ""`,
      `dispatch_mode: subagent`, `allowed_delegations: []`, `model: opus` + `[USER-DEFERRED]` comment);
      passes `/cast-agent-compliance`.
- [ ] `gaps[]` entry schema + gap-detection rule in WHAT; `GAPS-DETECTED` trailer (outside sentinels)
      in HOW; both agent dirs pass compliance.
- [ ] `maker_gate` gaps-schema + marker-correspondence (incl. T3) + GAP-NN/status rejection — pure,
      all fixtures green.
- [ ] Stages `ask_what`/`run_gapfill`/`validate_evidence`/`emit_change_requests`(stub) inserted at the
      Phase 3 seam; gap stages run **once per job, before** the 4a quality loop.
- [ ] `validate_evidence` reuses the shared `verbatim_locate`; T2 parity test green; fabricated
      evidence demotes with the reason recorded.
- [ ] All degradations (ask-round exhausted, gapfill crash, evidence demotion) land on the job row
      AND in `gaps-state.json`; the render never blocks and never fabricates.
- [ ] `gaps-state.json` uses the single closed status enum; out-of-enum status is gate-rejected.
- [ ] NO CR emitted in 5a; `change_request_service` untouched.
- [ ] C6/A2 counter independence proven by test.

## Execution Notes

- **The trust boundary is server-side, not agent-side.** The gapfill agent can *claim* an answer;
  only `validate_evidence` (deterministic, shared `verbatim_locate`) lets it reach the CR door. "Never
  fabricates" is enforced here, not promised.
- **Counters are independent — do not collapse them.** The probe `run_how` (C6) and the `ask_what`
  re-run (A2) are pre-loop gap machinery; they must not debit the in-loop `QUALITY_*` budgets, or a
  gap-bearing render is silently throttled at the quality bar.
- **Single-helper discipline is load-bearing.** A second `verbatim_locate`/stripper/walker silently
  voids the trust-boundary and correspondence guarantees.
- **5a ends BEFORE emission.** `emit_change_requests` is a `gaps-state.json`-only stub here; resist
  the urge to wire `change_request_service.create` — that is 5b, where the GATE-ALL policy also lands.
- **Spec-linked files:** the gaps schema, trailer channel, ask bounds, and grounded-or-refuse
  contract are new spec'd behavior under `cast-requirements-render.collab.md`. **Flag for 5d's single
  `/cast-update-spec` pass — do not edit the spec here.** Clause texts are fixed in the source plan.
