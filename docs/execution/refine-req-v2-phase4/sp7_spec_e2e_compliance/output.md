# sp7 — Spec lockstep + e2e harness + compliance (settle the phase) — OUTPUT

**Status:** ✅ COMPLETE — all Detailed Steps executed, all verification run, every success
criterion met. **No production behavior changed** (only the spec, the registry, the e2e test
harness, and an agent test-dir were touched).

This is the last sub-phase. sp1–sp6 all landed (verified: `comment_service.py`,
`api_requirements.py`, `block_diff.py`, `diff_render.py`, `requirements_comments.js`,
`agents/cast-comment-reanchor/`, and the Phase-4 tables/tests all present and green).

## Step 7.1 — Spec extension (`/cast-update-spec` single-write-path)

Extended `docs/specs/cast-requirements-render.collab.md` (**v1 → v2**) with the full Phase 4
surface, using the exact Naming-Contract tokens from `_shared_context.md` (Phase 5 cites this
spec, so names are token-for-token):

- **Front matter:** added the 14 Phase-4 linked files + the Phase-4 plan; `last_verified` kept
  2026-06-12; maturity banner **Version: 2**.
- **Intent:** added a Phase-4 paragraph (iteration loop, same-door FR-013, deterministic-where-
  silent-data-loss rule, derived displacement, Phase-5 reuse of `block_diff`).
- **User Stories US8–US13:** US8 same-door comment authoring (dual-assertion parity); US9 the
  resolve/reopen/relocate/orphan state machine (409/422 guards + relocate verbatim backstop);
  US10 versioned snapshots + carry-forward + convergence (`create_next`); US11 deterministic
  `block_diff`/`summarize` + `/changes` + `/render/diff`; US12 derived displacement + surfaced
  tray (save path untouched — decision #1); US13 the `cast-comment-reanchor` bare-JSON carve-out
  + orphan-over-guess (decision #9). Each has an Independent test + EARS scenarios.
- **FR-014–FR-028:** the API prefix + slug-404 rule, the dual-assertion `POST /comments`, the
  negotiated `GET /comments` with derived `displaced`, content validation (422), the state
  machine, the relocate verbatim backstop, the `comment_service` flat-fn naming contract,
  `create_next`'s contract dict, the convergence rule, the versions/changes/`render/diff`
  endpoints, **the transient-`id` exception (FR-025) — the only sanctioned exception to the
  zero-`id` thin-spine rule, scoped to the diff view**, the FR-011 folder invariant, the
  `cast-comment-reanchor` subagent carve-out (FR-027), and the **progressive-enhancement note
  (FR-028)** (file:// degrades to a readable read-only render).
- **SC-005–SC-009:** same-door parity, transactional versioning + carry-forward, deterministic
  diff (partition invariant + `/changes`==`summarize()`), no-mutation/folder-invariant/zero-`id`,
  and the e2e render-page coverage.
- **Open Questions:** none blocking; the two deliberate exceptions (transient-`id`, bare-JSON
  carve-out) recorded as intentional, not drift.
- **Registry:** bumped the `cast-requirements-render.collab.md` row to **v2** with a Phase-4
  scope summary + the v2 linked files/plan.

`bin/cast-spec-checker docs/specs/cast-requirements-render.collab.md` → **exit 0**. (Two
self-referential FR-token mentions inside table-row Notes initially tripped the duplicate-ID
rule R5; reworded to prose so the checker stays green — no semantic change.)

## Step 7.2 — e2e harness (cast-ui-testing US2)

Added a **`requirements_render` screen** to the existing agent-orchestrated Playwright harness
under `cast-server/tests/ui/`, targeting the real selectors this plan names. Code lands and its
unit/wiring tests are green; the **live four-flow run executes in a browser-capable CI** (the
sweep entry `test_full_sweep.py::test_ui_e2e` is `@pytest.mark.skip` pending the CI browser env,
pre-existing).

- **`runner.py`** — new `_assert_requirements_render(page, ctx)` + `_seed_render_goal(base_url)`
  (creates a `ui-test-render-*` goal, copies the real Phase-1 fixture into its goal dir, snapshots
  v1) + `_select_and_pill()` helper; registered in `SCREEN_DISPATCH`. The four locked flows:
  - **Flow A** — select `.rr-document` text → `.comment-pill` → `.comment-composer` → submit →
    `mark.comment-mark` (decision #7).
  - **Agent parity (FR-013)** — a comment POSTed through the **same** `/requirements/comments`
    door (`author_kind="agent"`) also yields a `<mark>`.
  - **Flow B** — resolve via `.comment-resolve-btn` on an open `.comment-thread-item` →
    `data-state="resolved"`.
  - **Flow D** — reword the source + `POST …/versions` (asserts `displaced_comment_ids` non-empty)
    → the displaced comment appears under `.comment-tray [data-group="displaced"]`
    (`data-displaced="true"`), never as a body `<mark>` (decision #1).
  - **Flow C** — `.version-toggle__diff` → `/goals/{slug}/render/diff` → the tracked-changes view
    (`.diff-changed-panel`/`.diff-added`/`.diff-removed`) (decision #8).
- **`agents/cast-ui-test-requirements-render/`** — new screen-child agent (`config.yaml` +
  `.md`), mirroring the sibling contract (runner invocation + contract-v2 envelope).
- **Orchestrator** wired the new child into `phase_2_parallel` (counts updated 6→7 / 7→8).
- Pins updated: `test_runner_dispatch.py` (8-screen set), `test_full_sweep.py` (total 8),
  `test_registry_visibility.py` (10-agent census).

> **No-browser carry-forward (project default):** this autonomous run cannot drive Chrome, so the
> four *live* render-page flows carry a **static PASS-by-construction verdict + human-eyeball
> carry-forward**; the harness code is landed and its dispatch/registry unit tests are green
> (8 passed). The selectors were verified against the landed JS/templates
> (`.comment-pill`, `.comment-composer`, `mark.comment-mark`, `.comment-tray`,
> `.version-toggle__diff`, `.diff-changed-panel`).

## Step 7.3 — Compliance sweep (`/cast-agent-compliance`) — CLEAN

- **`cast-comment-reanchor`** — config canon **exact**: the five subagent keys
  (`model: sonnet`, `dispatch_mode: subagent`, `interactive: false`, `context_mode: lightweight`,
  `timeout_minutes: 10`) + `allowed_delegations: []` (correct — it is a leaf worker that dispatches
  nothing, so the empty list is NOT the footgun). Structure matches the subagent-mode peers
  (`cast-goal-classifier`, `cast-requirements-checker`): `{name}.md` + `config.yaml` only — the
  documented carve-out, not a missing-wrapper violation. Verdict schema matches the canonical
  `{verdicts:[{comment_id, verdict, new_quoted_text, new_section_hint, confidence, reasoning}]}`.
  **0 violations.**
- **`cast-refine-requirements` allow-list** — `allowed_delegations` lists `cast-goal-classifier`
  **and** `cast-comment-reanchor`; both exist as sibling `agents/cast-*/` dirs (no typo); the
  entry is well-formed and the comment documents intent (subagent dispatch). **Recognized as
  intentional, 0 violations.**
- **Recorded finding (non-blocking, routed back, not patched here):** sp4b flagged the
  `cast-refine-requirements.md` prompt at **661 lines, ~11 over the ~650 *soft* ceiling**. This is
  not one of the auditor's 14 checks; trimming it would be a production-content change, out of
  sp7's "no production behavior change" scope (HOLD SCOPE). Suggested lever (deferred): move the
  Phase-4 Iteration block to a referenced skill doc, leaving a one-line trigger.

## Step 7.4 — SC-002 manual dry run — PASS

Ran the dry run against **this goal's real `refined_requirements.collab.md`**, in an **isolated
temp DB + temp goals dir** (so the live goal's comment/version tables are never mutated —
good-citizen / HOLD SCOPE). A read-only probe confirmed the live render works:
`GET /goals/refine-requirements-v2/render → HTTP 200`.

Sequence + result:
- v1 snapshot from the real content; two comments left through the **same door** (one
  `author_kind="human"`, one `"agent"` — FR-013 parity).
- Editor save rewords one comment's quote out → `create_next()` (the `POST /versions` path):
  - `convergence = "unconverged"` (open comments drive the bump);
  - **both comments carry forward, still `open`, still at their original `v1`** (no row copy);
  - `displaced_comment_ids = [<reworded comment>]` (the deterministic string-find);
  - `list_comments` (derived, read-time): the reworded comment `displaced=True` → **surfaces in
    the tray, not as a `<mark>`**; the stable comment `displaced=False` → stays a `<mark>`;
  - archived v1 still retrievable with its 2 comments + content preserved.
- **Verdict: PASS** — carry-forward + unconverged + displaced→tray all confirmed on real content.

## Verification (all run, all green)

```
bin/cast-spec-checker docs/specs/cast-requirements-render.collab.md   → exit 0
grep cast-requirements-render docs/specs/_registry.md                 → row present, | Draft | 2 |
uv run pytest tests/ui/test_runner_dispatch.py tests/ui/test_registry_visibility.py → 8 passed
SC-002 in-process dry run (real content, isolated DB)                 → PASS
live render probe GET /goals/refine-requirements-v2/render            → HTTP 200
```

## Success criteria — all met
- [x] `cast-requirements-render.collab.md` extended with the full Phase 4 surface; registry bumped; checker exit 0.
- [x] e2e flows (select→pill→composer→`<mark>`, resolve, toggle→diff, displaced→tray) exist and target the named selectors (live run carried forward to browser-capable CI per the no-browser default).
- [x] `/cast-agent-compliance` clean for `cast-comment-reanchor` + the allow-list addition.
- [x] SC-002 dry run recorded (comment carries forward through a version bump; displaced→tray confirmed).
- [x] No production behavior changed (the 661-line prompt overage recorded as a finding, not patched).

## Files created / modified
| File | Action |
|------|--------|
| `docs/specs/cast-requirements-render.collab.md` | Modify (v1→v2: front matter, Intent, US8–US13, FR-014–FR-028, SC-005–SC-009) |
| `docs/specs/_registry.md` | Modify (bump render row to v2 + Phase-4 scope/links) |
| `cast-server/tests/ui/runner.py` | Modify (+`requirements_render` screen, seed + select helpers) |
| `cast-server/tests/ui/agents/cast-ui-test-requirements-render/config.yaml` | Create |
| `cast-server/tests/ui/agents/cast-ui-test-requirements-render/cast-ui-test-requirements-render.md` | Create |
| `cast-server/tests/ui/agents/cast-ui-test-orchestrator/cast-ui-test-orchestrator.md` | Modify (+child in phase_2; counts 6→7/7→8) |
| `cast-server/tests/ui/test_full_sweep.py` | Modify (expected total 7→8; instructions) |
| `cast-server/tests/ui/test_runner_dispatch.py` | Modify (8-screen dispatch set) |
| `cast-server/tests/ui/test_registry_visibility.py` | Modify (10-agent census) |

## Handoff / notes
- Phase 5 imports `block_diff`/`summarize` and cites the same-door API from this spec — the
  token-exact names are why it won't reimplement the engine.
- The one finding to route back (not for sp7): `cast-refine-requirements.md` prompt soft-ceiling
  overage (661 vs ~650). Deferred lever recorded above.
- Phase 4 is settled: spec in lockstep, e2e harness landed, compliance clean, SC-002 confirmed.
