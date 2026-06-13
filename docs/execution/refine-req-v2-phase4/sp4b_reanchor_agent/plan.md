# Sub-phase 4b: `cast-comment-reanchor` agent + verdict application + loop + eval

> **Pre-requisite:** Read `docs/execution/refine-req-v2-phase4/_shared_context.md` before starting.

## Objective

Create the 4th first-class agent, `cast-comment-reanchor` — a subagent-mode worker whose only job is
to return `relocated`/`orphaned` verdicts for displaced comments. Wire the iteration loop into
`cast-refine-requirements` so that when a goal has open comments, the refine agent addresses them,
bumps the version, dispatches `cast-comment-reanchor` over `displaced_comment_ids`, and applies
verdicts through the same-door API (relocate/orphan). The deterministic backstop (verbatim
substring validation on relocate, sp1) guarantees zero silent mis-placement (decision #9). **Runs
parallel with sp4a** (file-disjoint). On the **critical path** (sp1 → sp3 → sp4b).

## Dependencies

- **Requires completed:** sp1 (the relocate/orphan API + the 422 verbatim backstop), sp3
  (`create_next` returning `displaced_comment_ids`).
- **Assumed codebase state:** `POST /comments/{id}/relocate` rejects non-verbatim quotes with 422;
  `POST /comments/{id}/orphan` exists; the classifier/checker subagent shape (Phase 2/3a) is the
  clone template; `bin/generate-skills` regenerates skill stubs from `agents/*/`.

## Scope

**In scope:**
- `agents/cast-comment-reanchor/cast-comment-reanchor.md` + `agents/cast-comment-reanchor/config.yaml`.
- Iteration-mode wiring in `agents/cast-refine-requirements/cast-refine-requirements.md` (lean,
  ~25 lines) + `allowed_delegations` addition in its `config.yaml`.
- `tests/eval_reanchor.py` (manual/slow, `eval_` prefix — excluded from default CI).
- Run `bin/generate-skills`; delegate compliance to `/cast-agent-compliance`.

**Out of scope (do NOT do these):**
- Any cast-server code (services, routes, templates, JS). The agent **never touches the DB or
  files** — it returns text; the parent applies verdicts through the API (FR-013 same door).
- Changing the relocate/orphan endpoints (sp1 owns them; this sub-phase only *calls* them).
- The full spec update + `/cast-agent-compliance` for `cast-refine-requirements`'s allow-list audit —
  that final compliance sweep is sp7 (this sub-phase runs compliance on the NEW agent + adds the
  delegation; sp7 re-audits the allow-list footgun).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `agents/cast-comment-reanchor/cast-comment-reanchor.md` | Create | Does not exist |
| `agents/cast-comment-reanchor/config.yaml` | Create | Does not exist |
| `agents/cast-refine-requirements/cast-refine-requirements.md` | Modify | Existing refine agent (~650-line ceiling) |
| `agents/cast-refine-requirements/config.yaml` | Modify | Has `allowed_delegations` |
| `tests/eval_reanchor.py` | Create | Does not exist |

## Detailed Steps

### Step 4b.1: The agent prompt + config (clone the checker/classifier shape)
`config.yaml`: `model: sonnet`, `dispatch_mode: subagent`, `interactive: false`,
`context_mode: lightweight`, `timeout_minutes: 10`. **Input** (delegation context from the parent):
the displaced open comments `{id, quoted_text, section_hint, body}`, the OLD version content, the
NEW current content. **Task:** for each comment, find where its commented-on content now lives in
the new text; return:
- `relocated` with `new_quoted_text` = a **verbatim substring of the new document** covering that
  content + the new nearest heading as `new_section_hint`; **or**
- `orphaned` if the content is genuinely gone.

**Prompt invariants (state these explicitly):** never paraphrase, never invent text; prefer
`orphaned` over a low-confidence guess (orphaning is surfaced and recoverable; a silent
mis-placement is not — decision #9's asymmetry). **Output:** EXACTLY ONE bare JSON object matching
the canonical verdict schema (`_shared_context.md`) — no prose, no fences. This is the documented
classifier/checker carve-out from `cast-delegation-contract.collab.md` — do NOT wrap it in an output
envelope.

### Step 4b.2: Iteration-mode wiring in `cast-refine-requirements.md`
Add a lean (~25-line) "Iteration mode" section, API-driven: when the goal has open comments
(`GET /comments?state=open`):
1. Address them in the new draft; write the `.collab.md`.
2. `POST /versions` → read `displaced_comment_ids` from the contract dict.
3. Dispatch `cast-comment-reanchor` (Agent tool — subagent mode) over the displaced comments + old/new content.
4. Apply verdicts via the API: `relocated` → `POST /comments/{id}/relocate` (a 422 rejection
   downgrades that verdict to `POST /comments/{id}/orphan` — the comment surfaces in the tray either
   way; zero silent loss, zero invented anchors).
5. Resolve the comments the new draft addressed (`POST /comments/{id}/resolve`) with a body-note
   pointing at the change.

Add `cast-comment-reanchor` to `cast-refine-requirements/config.yaml` `allowed_delegations`.

> ⚠️ **~650-line prompt ceiling (Phase 1b):** the prompt is already under pressure. If the
> Iteration-mode section doesn't fit, move the choreography to a referenced skill doc (the
> `cast-child-delegation` pattern) and keep only the trigger line in the prompt. **Flag the
> overage** in your sub-phase output — never silently trim Phase 1b/2 content to make room.
> → Consult `/cast-child-delegation` for the dispatch/poll/apply mechanics before writing this.

### Step 4b.3: Regenerate skills + compliance
- Run `bin/generate-skills` (regenerates the skill stub from the new agent dir).
- → **Delegate: `/cast-agent-compliance`** (which consults `/cast-agent-design-guide`) — validate
  `cast-comment-reanchor/config.yaml` fields + the subagent bare-JSON carve-out against fleet canon
  (the Phase 3a plan-review #2 precedent).
  **Review the delegated output for:** config keys match the Naming Contract exactly
  (`model: sonnet`, `dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`,
  `timeout_minutes: 10`); the bare-JSON verdict is recognized as the carve-out, not flagged as a
  contract violation. Fix any real config drift it finds; record (do not auto-"fix") the carve-out.

### Step 4b.4: `tests/eval_reanchor.py` (decision-#9 validate-during-build)
Fixture pair: the frozen Phase 1 fixture + `refined_requirements.v2-edit.collab.md` (sp2) with three
pre-seeded comments (one reworded → relocated, one deleted → orphaned, one unchanged control).
Dispatch `cast-comment-reanchor` over them. **Gate:**
- the reworded-quote comment → `relocated` with a **verbatim-present** `new_quoted_text`;
- the deleted-content comment → `orphaned`;
- **zero verdicts inventing text** (every `relocated.new_quoted_text` is a substring of the new doc).

Run before declaring the phase done; tune the prompt on failures (trust + iterate). Excluded from
default CI (the `eval_` prefix).

## Verification

### Automated Tests (permanent)
- The agent itself has no pytest (it's an LLM worker); its correctness gate is `eval_reanchor.py`.
- A cheap **structural** test is acceptable: assert `config.yaml` has the five canonical keys and
  `cast-refine-requirements/config.yaml` lists `cast-comment-reanchor` in `allowed_delegations`
  (pins the sp3c allow-list footgun). Place it where agent-config tests live, or inline in
  `eval_reanchor.py` as a fast pre-check.

### Validation Scripts (temporary / manual)
```bash
bin/generate-skills
cd cast-server && python tests/eval_reanchor.py     # the decision-#9 build gate (manual/slow)
grep -n "cast-comment-reanchor" agents/cast-refine-requirements/config.yaml   # allow-list present
wc -l agents/cast-refine-requirements/cast-refine-requirements.md             # check vs ~650 ceiling
```

### Manual Checks
- The agent emits ONE bare JSON object (no fences) — eyeball a dispatch.
- A relocate-rejection path: feed a verdict whose `new_quoted_text` is NOT in the new doc → the loop
  downgrades to orphan (the 422 backstop fires); confirm the comment lands in the tray, not lost.

### Success Criteria
- [ ] `agents/cast-comment-reanchor/` exists with the canonical config + bare-JSON verdict prompt.
- [ ] Iteration-mode wiring added to `cast-refine-requirements.md` (or moved to a referenced skill
      doc with a trigger line + overage flagged); `allowed_delegations` updated.
- [ ] `bin/generate-skills` run; `/cast-agent-compliance` output reviewed (config keys correct;
      carve-out recorded, not "fixed").
- [ ] `eval_reanchor.py` gate passes: reworded→relocated(verbatim), deleted→orphaned, zero invented text.
- [ ] No cast-server code touched in this sub-phase.

## Execution Notes

- **Error & rescue:** subagent failure/timeout/garbage JSON ⇒ the parent applies NO verdicts; the
  displaced comments simply stay in the tray (derived state degrades gracefully; nothing is lost;
  the next cycle retries). Write the loop so a bad dispatch is a no-op, never a crash.
- **The agent never writes state** — relocate is substring-validated server-side, orphan is the only
  other transition exposed. The verdict path cannot write arbitrary state.
- This sub-phase is on the critical path but is file-disjoint from sp4a — they can run in parallel.

**Spec-linked files:** none (agent prompts + an eval). The `cast-comment-reanchor` I/O contract +
carve-out are recorded in the spec by sp7. The `/cast-agent-compliance` delegation here validates
fleet config canon, not the requirements-render spec.
