# Sub-phase 4b-2: The Diff Agent — `cast-comment-reanchor` Contract v2 Narrates & Re-anchors

> **Pre-requisite:** Read `docs/execution/refine-req-v3-phase4b/_shared_context.md` before starting.

## Objective

Extend `cast-comment-reanchor` **in place** to a backward-compatible **contract v2**: given the
deterministic change set and the displaced comments with their block context, it returns (a)
re-anchor / resolve / orphan verdicts that reason block-wise, and (b) a narration of the diff keyed
**exactly** to the deterministic items. Existing verdicts-only call sites keep working
byte-unchanged (every new input is optional). Wire the refine-loop dispatch site to pass the new
context, apply the new `resolved` verdict through the v2 state machine, and POST the narration
(to the 4b-3 endpoint).

## Dependencies

- **Requires completed:** None within 4b (parallel with 4b-1). Phase 3's WHAT-doc id-mapping exists;
  `block_diff.summarize` (the `change_set` shape) exists at `block_diff.py:174`.
- **Provides to 4b-3:** the `narration` output shape **is** the schema 4b-3 stores — 4b-3 depends on
  this sub-phase.
- **Assumed codebase state:** `agents/cast-comment-reanchor/{cast-comment-reanchor.md,config.yaml}`;
  the refine-loop dispatch site in `agents/cast-refine-requirements/` (Phase-4 loop, step 3);
  `tests/eval_reanchor.py` (the `eval_` agent gate); `comment_service.resolve_comment` /
  `relocate_comment` / `reopen` (the v2 state machine).

## Scope

**In scope:**
- Extend `agents/cast-comment-reanchor/cast-comment-reanchor.md` to the contract-v2 superset
  (optional `change_set` + per-comment `block_ref`/`block_disposition` inputs; `narration` output;
  third `resolved` verdict; anchor-pickability rule; trust-boundary hard rule). Update the `.md`
  title to "Diecast Comment Re-anchor & Diff Narrator".
- `config.yaml`: `timeout_minutes: 15`; keep `dispatch_mode: subagent`; keep `model: sonnet` and add
  a `# [USER-DEFERRED] tier knob` comment. Everything else unchanged.
- Update the refine-loop dispatch site (`cast-refine-requirements`, Phase-4 loop step 3) to pass
  `change_set` + per-comment block context; apply `relocated` / `orphaned` exactly as today, apply
  the new `resolved` through the state machine, then POST the narration; a failed/timed-out/
  unparseable dispatch stays a **no-op**.
- Extend `tests/eval_reanchor.py` (the `eval_` gate).

**Out of scope (do NOT do these):**
- Do NOT create a new agent or rename the directory (extend in place — Decisions #1).
- Do NOT touch the writeback dispatch site (`change_request_service` / writeback agent) — its
  verdicts-only use stays valid under v2 by construction (optional inputs). Adopting narration there
  is a Phase-5/reconciliation choice.
- Do NOT change the v1 verdict fields or the 422 verbatim relocate backstop — carry them untouched.
- Do NOT store narration here (that is 4b-3); this sub-phase only POSTs to the 4b-3 endpoint at the
  dispatch site (which can land after 4b-3, or guard the POST so the eval gate runs independently).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-comment-reanchor/cast-comment-reanchor.md` | Modify | v1 contract (verdicts-only); extend to v2 superset; title updated |
| `agents/cast-comment-reanchor/config.yaml` | Modify | `model: sonnet`, `dispatch_mode: subagent`; bump `timeout_minutes: 15` + `[USER-DEFERRED]` comment |
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modify | Phase-4 loop step 3 dispatch; pass `change_set` + block context; apply `resolved`; POST narration |
| `tests/eval_reanchor.py` | Modify | v1 eval fixtures; add v2 narration + adversarial + moved-reworded + markdown-seam fixtures |

> Confirm the exact dispatch-site file/section with `grep -rn "cast-comment-reanchor" agents/cast-refine-requirements/` before editing.

## Detailed Steps

### Step 4b2.1: Extend the agent contract to v2 (the `.md`)

Add the contract-v2 block to `cast-comment-reanchor.md` exactly as the v1 contract block is laid out
today (I/O contract section). Use the verbatim shape in the shared context's "contract v2" schema:
- **Inputs (all additions OPTIONAL):** `change_set` (the `summarize()` dict); per displaced comment
  `block_ref` (the `Block.ref` whose OLD body held the quote — derived deterministically by the
  parent from the parsed old version) + `block_disposition` (`modified`/`removed`/`unchanged`).
  Legacy `{comments, old_content, new_content}` calls ⇒ verdicts only, unchanged.
- **Outputs:** `{"narration": null | {overview, item_notes:[{change, heading_or_ref, note}]},
  "verdicts": [...]}`. `narration` emitted **only** when `change_set` was provided. Every
  `(change, heading_or_ref)` in `item_notes` MUST equal an entry in `change_set.items` — never
  merged, added, or reworded keys.
- **Third verdict `resolved`** with honest confidence + reasoning; only on a demonstrable fix. State
  the safety asymmetry + bias order **`relocated` > `resolved` > `orphaned`-when-unsure** in the
  prompt.
- **Anchor-pickability rule:** `new_quoted_text` must remain a verbatim substring of `new_content`
  (unchanged backstop) and SHOULD avoid inline-markdown markers (`**`, `` ` ``).
- **Trust boundary (hard rule):** narration describes ONLY entries of `change_set.items`; if the set
  looks wrong, say so in `overview` wording — never add an item.
- Update the `.md` title to "Diecast Comment Re-anchor & Diff Narrator" (the directory name stays;
  accepted under-description, Decisions #1).

### Step 4b2.2: `config.yaml` minimal update

`timeout_minutes: 15` (narration adds output volume). Keep `dispatch_mode: subagent`,
`interactive: false`, `context_mode: lightweight`, `allowed_delegations: []`, bare output. Keep
`model: sonnet`, append a `# [USER-DEFERRED] tier knob` comment (the deferred owner decision stays a
one-line config edit — the reanchor agent is NOT one of the four opus pipeline agents).

### Step 4b2.3: Wire the refine-loop dispatch site

In `cast-refine-requirements` Phase-4 loop step 3:
- Build `change_set` from `GET …/requirements/changes?base=N-1&head=N` JSON; derive each displaced
  comment's `block_ref` + `block_disposition` deterministically from the parsed old version.
  - **Quote → `block_ref` helper (no existing one — add a tiny pure helper):** `comment_service`
    displacement is a whole-document string-find, so there is **no** existing quote→block resolver.
    Add a small pure helper (e.g. in `requirements_render/` or beside the dispatch logic) that
    `parse_requirements(old_content)` then finds the `Block.ref` whose `strip_inline_markdown(body)`
    contains the comment's `quoted_text` — reusing the same stripper 4b-1 uses (no second stripper).
    `block_disposition` comes from the `change_set` item for that ref (`modified`/`removed`) or
    `unchanged` if the ref is not in `items`. `block_ref` stays **optional** by contract: when the
    helper finds no single containing block (cross-boundary quote), omit it and let the agent reason
    from `old_content` — do NOT guess a ref.
- Dispatch (Agent tool, subagent mode) with the v2 inputs.
- On return, apply verdicts **exactly as today plus the new one**:
  - `relocated` → relocate (422 verbatim backstop downgrades to orphan — unchanged);
  - `orphaned` → orphan;
  - `resolved` → `POST …/comments/{id}/resolve` with `actor=cast-comment-reanchor`, **respecting the
    v2 state machine**: if the comment is no longer `open` at apply time (a human resolved/reopened
    it between dispatch and verdict), the resolve POST is a clean no-op/rejection — never a forced
    overwrite (symmetric to relocate's 422 downgrade; the state machine owns the final transition —
    Decision #11).
- Then POST the narration to the 4b-3 endpoint
  (`POST /api/goals/{slug}/requirements/versions/{head}/narration` with `{base, overview,
  item_notes}`, `created_by` = the dispatching parent's actor id). A 422 (key mismatch) → one retry,
  then proceed narration-less (the deterministic panel is the floor).
- A failed / timed-out / unparseable dispatch is a **no-op**: no verdicts applied, no narration —
  the tray + the deterministic panel carry the load; the next cycle retries.

### Step 4b2.4: Extend `tests/eval_reanchor.py`

Add fixtures (keep the `eval_` prefix — not default CI):
- legacy verdicts-only fixture **unchanged** (proves backward compatibility);
- a narration fixture where every `item_note` keys to a real `summarize()` item;
- an **adversarial** fixture proving the agent does NOT emit a note for a change absent from the set;
- a **moved+reworded block** fixture re-anchored (not orphaned) using the block-context hint;
- a **markdown-seam** fixture where the returned `new_quoted_text` avoids inline-markdown markers;
- an **over-eager `resolved`** fixture (the agent should prefer `relocated` when content survives);
- a **dry-run dispatch** over this goal's v2 fixture pair returning one bare JSON object parsing
  against the v2 schema.

## Verification

### Automated / eval gate
- `python tests/eval_reanchor.py` (or its runner) green with all fixtures above; the legacy fixture
  asserts byte-identical verdicts-only behavior.
- A dry-run dispatch (Agent tool, subagent mode) over the v2 fixture pair returns one bare JSON
  object parsing against the v2 schema (no `.output.json` envelope — the carve-out holds).

### Delegations
- → Delegate: `/cast-agent-compliance` over `agents/cast-comment-reanchor/` — review output for
  carve-out and config-shape violations (config shape, bare-output conventions intact).
- → Delegate: consult `/cast-agent-design-guide` (I/O contract section) while extending — the v2
  contract block goes in the agent `.md` exactly as the v1 block is today. Review for I/O-contract
  conformance.

### Manual Checks
- `grep -n "dispatch_mode\|model\|timeout_minutes\|USER-DEFERRED" agents/cast-comment-reanchor/config.yaml`
  — `subagent`, `sonnet` + deferred comment, `15`.
- Confirm the writeback dispatch site is **untouched** (`git diff --stat` shows only the refine-loop
  site changed among dispatch sites).
- Confirm the directory name is unchanged and the `.md` title now reads "…& Diff Narrator".

### Success Criteria
- [ ] Contract v2 is a strict superset: legacy verdicts-only calls behave byte-unchanged.
- [ ] `narration` emitted only when `change_set` provided; every `item_note` keys to a real item.
- [ ] `resolved` verdict present with the recoverability rationale + `relocated > resolved >
      orphaned` bias; applied through the v2 state machine (no-op/reject if not `open`).
- [ ] Anchor-pickability rule + trust-boundary hard rule stated in the prompt.
- [ ] `config.yaml`: `subagent`, `sonnet` (+ `[USER-DEFERRED]` comment), `timeout_minutes: 15`.
- [ ] Refine-loop dispatch passes `change_set` + block context (via the pure quote→`block_ref`
      helper; `block_ref` omitted, never guessed, for cross-boundary quotes), applies all three
      verdicts, POSTs narration (with `created_by` = its own actor id), and stays a no-op on a bad
      dispatch.
- [ ] Writeback site untouched; verdict safety machinery (orphan-over-guess, 422 backstop,
      no-op-on-garbage) carried over untouched.
- [ ] `/cast-agent-compliance` passes; eval gate green.

## Execution Notes

- **Extend, never replace.** The verdict safety machinery is the load-bearing protection against
  silent data loss — it must carry over untouched, not be re-implemented. One dispatch serves both
  narrate + resolve at the same version boundary.
- **The `resolved` state-machine guard is a real concurrency fix** (Decision #11 / CQ2): the
  dispatch→apply window is genuine (the agent runs async). The state machine, not the stale verdict,
  owns the final transition.
- **Narration POST coupling:** 4b-3 owns the endpoint. If 4b-2 lands first, guard the POST (or land
  the dispatch-site narration wiring after 4b-3) so the eval gate — which does not need the endpoint
  — runs independently. The verdict application does not depend on 4b-3.
- **Spec-linked files:** FR-027's schema + US13's verdict enumeration change (superset). **Flag for
  4b-4's `/cast-update-spec` — do not edit the spec here.**
