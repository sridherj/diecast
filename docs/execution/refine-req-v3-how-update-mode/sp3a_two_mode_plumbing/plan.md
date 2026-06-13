# Sub-phase 3a: Two-Mode Plumbing — Mode Detection & Prior-Render Recovery

> **Pre-requisite:** Read `docs/execution/refine-req-v3-how-update-mode/_shared_context.md` — the mode
> decision contract, the UPDATE-skips-`emit_change_requests` rule (plan-review Decision #2), and the
> `RENDER_UPDATE_MAX_PRIOR_BYTES` precondition (plan-review Decision #6). **Read the 1a verdict first**
> (`docs/goal/refine-requirements-better-rendering-v3/spikes/update-fidelity/verdict.md`) — it shapes
> the byte-copy vs. fragment obligation the UPDATE prompt section carries.

## Objective

`render_job_service` deterministically decides CREATE vs UPDATE at job start and assembles every UPDATE
input (prior render, prior parsed source, changed-block set, reused WHAT doc) — **while production
behavior is still 100% CREATE** (the UPDATE prompt path exists but is flag-gated off until Sub-phase 3b
flips it). Every UPDATE precondition failure degrades to CREATE with a job `_note`; CREATE is always safe.

## Dependencies

- **Requires completed:** Sub-phase 1a — its **verdict** selects whether the UPDATE prompt section
  carries a "copy unchanged containers byte-exact" obligation (PASS / gate-enforced LLM copy) or a
  "render changed-block fragments only" sub-contract (FAIL / deterministic splice). **If the verdict
  file is missing, stop and run/surface 1a first** — do not guess the mechanism.
- **Runs in parallel with Sub-phase 2.** Disjoint files: this sub-phase owns `render_job_service.py`,
  `config.py`, and the HOW prompt's UPDATE section (built **inert** here, wired live in 3b); sp2 owns
  `comment_service.py` / `comment_anchor.py` / `api_requirements.py` / `schema.sql`. No shared files.
- **Assumed codebase state:** `JobState` (`render_job_service.py:247`), `_build_how_prompt` (`:557`),
  `gate_html` (`:670`), `emit_change_requests` (`:1188`), `_what_doc_job_ref` (`:1125`),
  `reaper_ceiling_seconds` (`:1600`, reads `RENDER_STAGE_TIMEOUTS`), `_start_job` (`:1665`);
  `block_diff.diff_blocks`/`summarize`/`_key`; `config.RENDER_STAGE_TIMEOUTS` (`:183`).

## Scope

**In scope:**
- Persist recovery inputs at job time: `source.md` (parsed source text) at job start + the gated WHAT
  doc as `what-doc.md` at `gate_what` pass (make the `_what_doc_job_ref` promise real).
- Prior-render recovery at `_start_job`: read the existing `goals/{slug}/refined_requirements.html`;
  extract embedded `source-hash` / `served-by` / `human-review`; recover prior source from the prior
  job dir (fallback: a content-hash-matching `requirement_versions` snapshot; nothing → CREATE).
- A **pure, unit-testable mode-decision function** (the contract in shared context).
- Two config knobs: `RENDER_UPDATE_MAX_CHANGED_FRACTION` (default 0.4) + `RENDER_UPDATE_MAX_PRIOR_BYTES`.
- `JobState` additions: `mode`, `prior_html`, `prior_parsed`, `changed_refs`; a nullable `mode` column
  on `render_jobs` (additive observability).
- `_build_how_prompt` gains an UPDATE section (built + tested, **inert** — flag-gated off until 3b).
- WHAT reuse in UPDATE mode + **UPDATE SKIPS `emit_change_requests` entirely** (plan-review Decision #2).

**Out of scope (do NOT do these):**
- Do NOT flip production to UPDATE — the UPDATE path is **inert/flag-gated** until Sub-phase 3b. Every
  wait=True job in this sub-phase must still publish via the CREATE path.
- Do NOT implement `check_update_fidelity` or the re-scoped gates (Sub-phase 3b).
- Do NOT edit the HOW prompt's CREATE contract or the verbatim-carriage gate (3b).
- Do NOT fork `block_diff` — consume `diff_blocks`/`summarize` unchanged (FR-024).
- Do NOT touch `comment_service.py` / `comment_anchor.py` / `schema.sql`'s comment columns (sp2).

## Files to Create/Modify

| File | Action | Current State |
|------|--------|---------------|
| `cast-server/cast_server/services/render_job_service.py` | Modify | `_start_job` (:1665) persists `source.md`, recovers prior render; `gate_what` persists `what-doc.md`; new pure `decide_mode(...)`; `JobState` (:247) gains `mode`/`prior_html`/`prior_parsed`/`changed_refs`; `_build_how_prompt` (:557) gains the inert UPDATE section; UPDATE skips `emit_change_requests` (:1188) |
| `cast-server/cast_server/config.py` | Modify | Add `RENDER_UPDATE_MAX_CHANGED_FRACTION` (0.4) + `RENDER_UPDATE_MAX_PRIOR_BYTES` (env-overridable, `RENDER_*` convention) |
| `cast-server/cast_server/db/schema.sql` | Modify | `render_jobs` gains nullable `mode TEXT` (additive observability — same pattern as the 4a flag columns) |
| `cast-server/tests/test_schema_migration.py` | Modify | Cover the new `render_jobs.mode` column |
| `cast-server/tests/test_render_mode_decision.py` | Create | Pure mode-decision unit tests (threshold boundaries, every degrade-to-CREATE path) |

## Detailed Steps

### Step 3a.1: Config knobs

```python
# config.py — RENDER_* convention, env-overridable like QUALITY_*
RENDER_UPDATE_MAX_CHANGED_FRACTION = float(os.environ.get("CAST_RENDER_UPDATE_MAX_CHANGED_FRACTION", "0.4"))
RENDER_UPDATE_MAX_PRIOR_BYTES      = int(os.environ.get("CAST_RENDER_UPDATE_MAX_PRIOR_BYTES", "<choose a sane default>"))
```

- **0.4 is a starting value**, recorded as a tune-after-first-runs knob, not a researched constant.
- `RENDER_UPDATE_MAX_PRIOR_BYTES` bounds the *total bytes inlined* (the changed-fraction bounds only
  the changed work). Pick a default comfortably under the context budget; document it as a tune knob.

### Step 3a.2: Persist recovery inputs at job time

- At `_start_job`: write `source.md` (the parsed source text) into the job dir
  `build/render-jobs/{slug}/{hash12}/`.
- At `gate_what` pass: persist the gated WHAT doc as `what-doc.md` at the stable
  `_what_doc_job_ref(state)` path (`render-jobs/{slug}/{hash12}/what-doc.md` — the path already
  promised; make it real).

### Step 3a.3: Prior-render recovery at `_start_job`

- Read the existing `goals/{slug}/refined_requirements.html` (it IS the prior render until publish
  overwrites it).
- Extract its embedded `source-hash`, `served-by`, `human-review` stamps.
- Recover the prior source from `build/render-jobs/{slug}/{prior_hash12}/source.md`; fallback: a
  `requirement_versions` snapshot whose content-hash matches; **nothing found → CREATE**.

### Step 3a.4: The pure mode decision

```python
def decide_mode(*, prior_html, prior_served_by, prior_human_review, prior_source,
                changed_fraction, prior_render_bytes, workflow_family_changed) -> tuple[str, str | None]:
    """Returns (mode, note). mode in {'create','update'}; note is the degrade reason or None.
    UPDATE iff ALL preconditions hold; otherwise CREATE with a note. Pure — no I/O."""
```

UPDATE iff **all** of:
- a prior render exists AND `prior_served_by == 'maker'` AND not `prior_human_review` (never UPDATE
  *from* a flagged/fallback render — that would propagate the flaw; recovering from a flagged render is
  exactly what a fresh CREATE is for);
- `prior_source` is recoverable;
- `changed_fraction <= RENDER_UPDATE_MAX_CHANGED_FRACTION`;
- `prior_render_bytes <= RENDER_UPDATE_MAX_PRIOR_BYTES` (plan-review Decision #6 — a large prior page
  near the context budget can silently truncate, dropping tail unchanged containers the maker was told
  to copy → a fidelity flag on an edit that touched none of them; a fresh CREATE never needs the prior
  page in context);
- `workflow_family` unchanged.

`changed_fraction = (added + removed + modified) / max(old_blocks, new_blocks)` from
`block_diff.diff_blocks` (consumed unchanged). **Every** precondition failure → `('create', <reason>)`
— never a job error.

### Step 3a.5: `JobState` + `render_jobs.mode` + the inert UPDATE prompt section

- `JobState` gains `mode`, `prior_html`, `prior_parsed`, `changed_refs` (keyed the way `block_diff._key`
  keys blocks).
- `render_jobs` gains a nullable `mode TEXT` column (additive observability; stamp `create`/`update`).
- `_build_how_prompt` gains an UPDATE section: prior render inlined + changed-block refs + **the
  byte-copy obligation (PASS / gate-enforced LLM copy) OR the fragment-rendering sub-contract (FAIL /
  splice), per the 1a verdict**. **Built and tested, INERT** — flag-gated off; production stays CREATE.

### Step 3a.6: WHAT reuse + UPDATE skips `emit_change_requests` (plan-review Decision #2 — load-bearing)

- **WHAT reuse in UPDATE:** skip `run_what`, reuse the prior job's gated `what-doc.md` (the section plan
  must not reshuffle under a small edit). If the diff adds/removes refs, patch the WHAT doc's id-mapping
  deterministically where trivial (added ref → the section its neighbors live in); otherwise **fall back
  to CREATE** rather than re-running WHAT against a stale structure.
- **Gap stages:** an UPDATE job reuses the prior job's `gaps-state.json` unchanged AND **SKIPS the
  `emit_change_requests` gap-emission stage entirely.** This is **load-bearing, not an optimization:**
  the gap-CR dedupe fingerprint rides `origin_artifact_path = _what_doc_job_ref(state)`, keyed by the
  *current* `source_hash[:12]`. An UPDATE runs under a NEW source hash, so re-emitting would write the
  gap CR against a new provenance path the dedupe pre-check can't match → a **DUPLICATE gap CR**.
  Reuse-without-re-emit keeps gap CRs idempotent; any diff that would actually change the gap set has
  already flipped the job to CREATE via the WHAT-patch fallback above.

## Verification

### Automated Tests (permanent)
`pytest` green over:
- **`test_render_mode_decision.py` (pure):** UPDATE happy path; each precondition independently forcing
  CREATE — missing prior source → CREATE, flagged prior (`served-by != maker` OR `human-review`) →
  CREATE, `changed_fraction` just over the threshold → CREATE (and just under → UPDATE),
  `prior_render_bytes` just over `RENDER_UPDATE_MAX_PRIOR_BYTES` → CREATE, `workflow_family` changed →
  CREATE. Each CREATE carries a non-empty `note`.
- **Schema migration:** `render_jobs.mode` present after migration; old rows read NULL.
- **Inert-path proof:** a wait=True job against an **edited corpus doc** still publishes via the CREATE
  path (UPDATE flag off) but logs `mode=update` + the changed-set in the job dir — proving detection +
  assembly work while production behavior is unchanged.
- **`emit_change_requests` skip (unit):** a job marked UPDATE does not call `emit_change_requests`;
  reuses the prior `gaps-state.json`. (Pairs with Sub-phase 5's gap-CR idempotency regression.)
- **Recovery artifacts:** `source.md` written at job start; `what-doc.md` written at `gate_what` pass at
  the `_what_doc_job_ref` path.

### Validation Scripts (temporary)
- A wait=True job against an edited corpus doc → inspect the job dir: confirm `mode=update`, the
  changed-set, the inlined prior render, and that publish still came from CREATE.

### Manual Checks
- `grep -n "RENDER_STAGE_TIMEOUTS" cast-server/cast_server/services/render_job_service.py` → confirm
  `reaper_ceiling_seconds` (:1600) still reads the stage list and **no new agent stage was added** (the
  UPDATE path adds no new stage; if a stage was registered, verify the reaper formula absorbs it).
- Confirm `block_diff.py` is **unedited** (consumed, not forked).
- Confirm production behavior is 100% CREATE (UPDATE flag-gated off).

### Success Criteria
- [ ] `decide_mode` is pure + unit-tested at every threshold boundary; every degrade-to-CREATE carries
      a `note`; zero silent failures, zero job errors.
- [ ] `RENDER_UPDATE_MAX_CHANGED_FRACTION` (0.4) + `RENDER_UPDATE_MAX_PRIOR_BYTES` added (env-overridable).
- [ ] `source.md` + `what-doc.md` persisted at job time; prior-render recovery reads the embedded stamps.
- [ ] `JobState`/`render_jobs.mode` additions land; `_build_how_prompt` UPDATE section built + **inert**.
- [ ] UPDATE reuses WHAT + `gaps-state.json` and **skips `emit_change_requests`** (idempotency-preserving).
- [ ] `block_diff` unedited; reaper ceiling unaffected (or correctly extended); production stays CREATE.

## Execution Notes

- **The whole sub-phase is plumbing — production stays CREATE.** The single most important invariant:
  the UPDATE path is built, tested, and INERT. Sub-phase 3b removes the flag-gate.
- **Job-dir lifecycle:** `build/render-jobs/` now carries cross-job recovery state. Document (in the
  job-dir README or a code comment) that wiping it only costs UPDATE capability for the next render
  (degrades to CREATE) — never make publish depend on the job dir surviving.
- **Read the 1a verdict before writing the UPDATE prompt section** — PASS vs FAIL changes the obligation
  text (byte-copy vs fragment-only). The verdict is a recorded dependency (owner decision), not an
  orchestrator gate; read the file.
- **Spec-linked files:** the two-mode contract + threshold knob + `mode` column are new behavior under
  `cast-requirements-render.collab.md`. **Flag for the Sub-phase 5 `/cast-update-spec` pass — do not edit
  the spec here.**
