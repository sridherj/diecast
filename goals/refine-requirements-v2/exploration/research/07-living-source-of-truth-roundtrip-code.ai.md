# Code Exploration: Living Source of Truth — Round-Trip Write-Back (Step 7)

**Goal context:** Refine Requirements v2 — keep requirements a *living* source of truth so downstream phases (exploration / planning / execution) write requirement-affecting changes *back* into the requirements artifact, with provenance, user notification, change-summary inclusion, and conflict surfacing instead of silent overwrite (US7, FR-018→FR-020).
**Codebase:** /home/sridherj/workspace/diecast
**Date:** 2026-06-11
**Tooling note:** code-review-graph MCP graph was not built for this session (SessionStart reported "No knowledge graph found"). Exploration done with Grep/Read/Bash. No fabrication — every claim below carries a file:line.

> **Go-broad framing:** This maps where we ARE so the synthesizer sees the starting point and migration cost. The headline finding is that **none of the Step-7 round-trip mechanism exists today** — but the codebase already contains *four strong, reusable precedents* for the hard parts (provenance, content-addressed conflict detection, surgical structured-edit-by-ID, and generated-render sync). The best answer assembles those primitives; it is not constrained to bolt onto the current file-overwrite edit path (which is, in fact, the anti-pattern US7 exists to kill).

---

## 1. Data Model & Schema

The canonical store is **split**: goals/tasks/runs are DB rows; requirements are **flat files**.

**DB entities** (`cast-server/cast_server/db/schema.sql`):
- `goals` (slug PK, status, phase, `folder_path`, `external_project_dir`) — lines 1-14.
- `tasks` (id, goal_slug, `task_artifacts` = "JSON array of relative-to-goal file paths", `completion_notes`) — lines 16-39. Note `task_artifacts` is the only DB↔file linkage and it stores **paths, not content**.
- `agent_runs` (id PK, agent_name, goal_slug, `output` = JSON from output.json, `artifacts` = JSON array of `{path,type,description}`, `needs_attention`, `parent_run_id`, `claude_agent_id`) — lines 72-92. This is the table that records *who ran* and *what they produced*.
- `agent_error_memories` (referenced in `services/error_memory_service.py`) — `agent_name`, `pattern_hash`, `run_ids` JSON, `occurrence_count`, `resolution_status`. **Not in schema.sql** — created via migration in `db/connection.py`.

**Requirements live as files, not entities.** `cast-server/cast_server/config.py:53-54`:
```python
PHASE_ARTIFACTS = {
    "requirements": ["requirements.human.md", "refined_requirements.collab.md"],
    ...
}
```
There is **no `requirements` table, no `requirement_element` table, no `comment`/`version`/`change` table.** The refined spec (`refined_requirements.collab.md`) is a hand/agent-authored markdown file with `US#`, `FR-NNN`, `SC-NNN` headings — but those IDs exist only as **text in the file**; nothing in the DB references them. Step 2's "stable element identity" keystone does **not** exist yet, and Step 7 depends on it (a write-back targeting "FR-014" has no durable anchor today).

**Authorship is encoded in the filename suffix, not a column** (`config.py:60-76`):
```python
AUTHORSHIP_TYPES = {"human": {...}, "ai": {...}, "collab": {...}}
ARTIFACT_DEFAULTS = {"requirements": "human", "refined_requirements": "collab", "research": "ai", ...}
```
`.human.md` = human-authored, `.collab.md` = human+agent collaborative, `.ai.md` = AI-generated. This is **file-granularity provenance**. Step 7 needs *element-* and *write-back-event-* granularity provenance ("FR-021 originated from the planning phase, run_X, 2026-06-11") — which has no home in this model.

**ASCII — current vs. needed:**
```
TODAY:                                   STEP 7 NEEDS (absent):
goals(slug) ──< tasks(task_artifacts[paths])    requirement_element(id, goal, kind, body, ...)
            ──< agent_runs(output JSON,            └─< writeback_event(element_id, origin_run_id,
                          artifacts[path])                       origin_phase, kind, status, ts)
requirements.*.md  (opaque text blob)            └─< version / change_summary (element-diff)
   FR-014 = just a string in the file               conflict(element_id, incoming, existing, state)
```

---

## 2. Existing Implementation (what's relevant to round-trip)

There is **no requirements round-trip feature**. But five existing mechanisms are the load-bearing precedents a Step-7 design should reuse.

### 2a. The agent output.json contract — the *existing* write-back vehicle (child → parent)
`cast-server/cast_server/models/agent_output.py` defines `AgentOutput` (contract v2): `agent_name`, `status`, `summary`, `artifacts[]`, `errors[]`, `next_steps[]`, **`human_action_needed`**, **`human_action_items[]`**, `started_at`, `completed_at`. Every cast-* agent writes `<goal_dir>/.agent-run_<RUN_ID>.output.json` on close-out (spec: `docs/specs/cast-output-json-contract.collab.md`). This is **already a structured, provenance-tagged, agent-originated message** — `agent_name` is the origin, `artifacts[]` is what changed. **It is the natural carrier for a "requirements_writeback" payload** (a new artifact `type`, or a new typed field), and it already round-trips up the delegation tree. Consumed by `_finalize_run()` at `services/agent_service.py:1702-1844`.

### 2b. `human_action_needed` / `needs_attention` — the *existing* user-notification primitive
`_finalize_run` (`services/agent_service.py:1758-1764`):
```python
needs_attention = 0
if output_data and output_data.get("human_action_needed"):
    needs_attention = 1
if status == "partial":
    needs_attention = 1
```
Persisted on the run (`update_agent_run(..., needs_attention=...)`, line 1812) and surfaced in the UI (`templates/fragments/task_item.html`) via HTMX polling. **This is the closest thing to FR-019's "notify the user."** Today it only flags *that* attention is needed; it does not carry *what changed + from where* in a structured, requirement-anchored way. A Step-7 notification ("requirements updated from planning: FR-021 added") would extend this rail, not invent a new one.

### 2c. `cast-update-spec` — the closest precedent for human-approved canonical write-back
`agents/cast-update-spec/cast-update-spec.md`. It is explicitly the **"sole write path"** for specs (lines 16-17: "No other agent creates or modifies spec files. Other agents… can FLAG drift but only you EDIT specs."). Its workflow *is* a write-back protocol:
- **Diff-before-write** (Step 4, lines 78-98): show Current vs Proposed.
- **Human-approval gate** (Step 5, lines 100-106): "Do not edit the spec until the user explicitly approves."
- **Version bump + changelog note** (Step 6, lines 108-114): `Version: N → N+1`, `**Updated:** <date> — <what changed>`.

This is a working model of FR-018/FR-020's "additions reviewed as a delta, never silent." **Gaps vs. Step 7:** it is (1) *human-triggered*, not downstream-agent-originated; (2) *file-level*, no element IDs; (3) targets `docs/specs/`, not `requirements`; (4) has no *conflict detection* (it assumes the human resolves conflicts by eye); (5) "flag drift" is prose-only — there is no machine signal a downstream phase can emit to trigger it.

### 2d. `error_memory_service` — the strongest analog for provenance + conflict + feedback-loop
`services/error_memory_service.py`. This subsystem already does, for *errors*, almost exactly what Step 7 must do for *requirement changes*:
- **Provenance capture:** rows carry `agent_name` + an appended `run_ids` JSON list — "which runs originated this" (lines 96-124).
- **Content-addressed identity / dedup:** `normalize_pattern()` strips dynamic segments, `compute_pattern_hash()` SHA-256s it (lines 36-56). Upsert keys on `UNIQUE(agent_name, pattern_hash)`. **This is the conflict/duplicate-detection primitive** Step 7 needs — "is this incoming change the same as / contradicting an existing element?" reduces to a hash/similarity check.
- **Surface-not-silent escalation:** `if new_count >= 3: resolution_status = "escalated"` + `logger.warning("ESCALATED...")` (lines 101-108) — a precedent for "raise to the user rather than absorb silently" (US7 Scenario 4).
- **Feedback loop back into agents:** `inject_as_context` + `get_relevant_memories()` re-inject past errors into the next run's context (lines 129-156). This is the *living* round-trip pattern in miniature — downstream signal flows back into upstream behavior.

### 2e. Generated-render & surgical-edit precedents (the FR-018 "additions not rewrites" mechanics)
- **DB-canonical → read-only file render:** `goal_service._write_goal_yaml()` (`services/goal_service.py:337-363`) writes `goal.yaml` with an `# AUTO-GENERATED: Read-only render of DB state. Do not edit directly.` banner. This is the exact "DB is canonical, file is a generated mirror" pattern Step 2 is weighing — already in production for goals.
- **Surgical in-place structured edit keyed by ID:** `orchestration_service.update_manifest_status()` (`services/orchestration_service.py:218-259`) finds the Status column by header, matches a row by `phase_id`, and rewrites *only that cell*, leaving the rest of the markdown table byte-identical. **This is a working "edit one element by its ID, append/annotate without rewriting the whole doc" implementation** — directly transferable to FR-018 (write-back as a targeted addition/annotation, not a silent full-file rewrite).
- **Derived-artifact staleness sync:** `context_map.ensure_context_map()` (`services/context_map.py:87-153`) regenerates `.context-map.md` from `*.ai.md` using **mtime staleness detection** to skip unchanged files. The pattern "keep a derived view in lockstep with its sources, only touch what changed" is the engine that keeps a render current after a write-back.

---

## 3. Gap Analysis (the core of this exploration)

Prioritized; severity = blast radius for Step 7.

| # | Gap | Severity | Evidence |
|---|-----|----------|----------|
| G1 | **No write-back path at all.** Nothing reads a downstream artifact and writes a requirement change into `requirements.*.md`. The only writers of requirements files are humans (via `api_artifacts.save_artifact`) and `cast-refine-requirements`. `grep refined_requirements cast-server/**/*.py` → only `config.py` references (paths), zero writers in services. | **Critical** | `config.py:54,84`; no hits elsewhere |
| G2 | **No stable element identity in the DB.** `FR-014`/`US7`/`SC-006` exist only as text in markdown. A write-back has nothing durable to anchor to; re-rendering or re-refining would orphan any anchor. Step 7 is *blocked* on Step 2. | **Critical** | `schema.sql` (no element table); spec headings are plain `##`/`|` rows |
| G3 | **No conflict detection.** Nothing compares an incoming change against existing requirements. `cast-update-spec` relies on a human eyeballing the diff; `error_memory` has hash-equality but only for identical errors, not *contradiction*. US7 Scenario 4 ("contradicts an existing requirement → surface, never overwrite") has no implementation and no near-analog beyond error-hash dedup. | **Critical** | no comparator in any service |
| G4 | **The current requirements-edit path is a blind full-file overwrite.** `api_artifacts.save_artifact` (`routes/api_artifacts.py:81-107`): `resolved.write_text(content)` — no diff, no version, no provenance, no conflict check, no merge. This is precisely the "silent overwrite / silent drift" behavior US7/FR-018 exist to prevent. Any round-trip built on this path inherits the bug. | **High** | `api_artifacts.py:94` |
| G5 | **No versioning / change-summary / diff machinery.** No version table, no element-diff, no `change_summary` generator. FR-017/FR-020 ("new version emits a change summary anchored to affected elements") have zero substrate. `cast-update-spec`'s "version bump" is a hand-typed string in the file, not computed. | **High** | no diff util in `cast_server/` |
| G6 | **Notification is poll-only and content-thin.** `needs_attention` is a boolean flag surfaced by HTMX polling; there is **no push** (no SSE/websocket — `grep EventSource\|websocket\|event-stream` → 0 hits in `cast_server/`). FR-019 wants "*what* changed + *which phase/source*" — today the run's `summary`/`human_action_items` carry prose, but nothing structures "requirements changed: +FR-021 from planning." | **Medium** | grep (no SSE); `agent_service.py:1758-1764` |
| G7 | **cast-server is contractually forbidden from writing artifact content.** `docs/specs/cast-delegation-contract.collab.md` Intent: "cast-server is a read-through HTTP API… **it never writes them**." So a server-side write-back service would *contradict the delegation contract* — the write-back must be performed by an **agent** (the FR-013 "agent-as-source" door), with the server only observing. This is an architectural constraint, not a bug, but it dictates *where* the mechanism can live. | **Medium** | delegation-contract Intent section |
| G8 | **No "flag drift" machine signal.** `cast-update-spec` says other agents "can FLAG drift" but the flag is prose in a summary — there is no structured event (`drift_detected{element_id, proposed_change, origin}`) a downstream agent emits and a write-back consumer subscribes to. | **Medium** | `cast-update-spec.md:16-17` |
| G9 | **Provenance is file-granular only.** `.human/.collab/.ai` suffix + `ARTIFACT_DEFAULTS` give whole-file authorship. No per-element, per-edit origin trail. FR-020 ("preserve provenance, present in change summary") needs the `error_memory.run_ids`-style append-list lifted to the element level. | **Medium** | `config.py:60-76` |

---

## 4. Patterns & Conventions (what a Step-7 design must fit)

- **MVCS, service-returns-data:** routes → services → db; services return dicts/`AgentOutput`, not ORM rows (`services/*`, `cast-mvcs-compliance` skill). A write-back belongs in a new service (e.g. `requirements_writeback_service`) called by an agent, not in a route.
- **File-on-disk is canonical for agent I/O; DB mirrors it.** Output.json is canonical; the server reads through (`delegation-contract`). Conversely goal.yaml is a *render* of canonical DB state. The product decision (Step 2) determines which polarity requirements take; **both polarities already exist in the codebase as working patterns** — there is no greenfield risk either way.
- **Single-write-path discipline.** `cast-update-spec` is the *sole* spec writer; everyone else flags. The obvious Step-7 shape mirrors this: one **requirements-write-back agent/service** is the sole writer of requirement changes; downstream phases *emit signals*, they don't edit requirements directly. This keeps provenance and conflict handling in one place.
- **Human-approval gate via `AskUserQuestion`** (`cast-interactive-questions` skill, used by `cast-update-spec`). Conflicts (US7 S4) and contradicting write-backs should surface through this same gate.
- **AUTO-GENERATED banners** on rendered files (`goal_service.py:359-362`) — convention for "don't hand-edit a derived view."
- **Content-hash identity for dedup/conflict** (`error_memory_service.normalize_pattern`/`compute_pattern_hash`) — the house style for "are these two the same thing?"
- **Append-not-replace provenance lists** (`error_memory.run_ids` JSON append, lines 96-98) — the house style for accumulating origin trails.
- **Additive-only contract evolution** (`output-json-contract` spec: "Parents MUST ignore unknown fields") — a write-back payload can ride the existing output.json by *adding* fields without breaking parents.

---

## 5. Entry Points & Flow

**Today — a downstream agent finishes (no requirements ever change):**
```
downstream agent (planner/executor)
  └─ writes .agent-run_<id>.output.json   [models/agent_output.py]
       └─ _finalize_run()                  [agent_service.py:1702]
            ├─ AgentOutput(**raw)          parse/validate
            ├─ needs_attention = human_action_needed?  [:1758]
            ├─ update_agent_run(output, artifacts, needs_attention)  [:1799]
            └─ _wire_artifacts_to_task(paths→task.task_artifacts)    [:1676]
   UI (HTMX poll) ── shows needs_attention badge   [templates/fragments/task_item.html]
   ❌ requirements.*.md is NEVER touched. Drift starts here.
```

**Today — a human edits requirements (the overwrite anti-pattern):**
```
UI edit  ─PUT /api/artifacts/save→  save_artifact()  [api_artifacts.py:81]
            └─ resolved.write_text(content)   ❌ blind overwrite, no diff/version/provenance
            └─ HX-Trigger toast "Artifact saved"
```

**Where Step 7 must hook (proposed seam, consistent with constraint G7):**
```
downstream agent discovers a requirement-affecting change
  └─ emits structured writeback in output.json
       artifacts[]: {type:"requirements_writeback", element_id, change, origin_phase}
        OR new typed field (additive — output-json-contract allows it)
  └─ requirements-writeback AGENT (sole writer; mirrors cast-update-spec single-write-path)
       ├─ resolve element_id → anchor        [needs Step 2 stable IDs]
       ├─ conflict check vs current element  [reuse pattern_hash-style comparator]
       │    └─ contradiction? → AskUserQuestion gate  (US7 S4)  ── never silent
       ├─ apply as targeted addition/annotation  [reuse update_manifest_status surgical-edit style]
       ├─ append provenance {origin_run, origin_phase, ts}  [reuse error_memory run_ids append]
       ├─ bump version + element-diff change summary  (FR-017/FR-020)
       └─ set human_action_needed + structured "what changed + from where"  → needs_attention (FR-019)
  server OBSERVES the files (never writes them — delegation-contract G7)
```

---

## 6. Tests & Coverage

- **Delegation / output-contract is well tested:** `tests/test_b5_atomic_write.py`, `tests/test_b5_file_polling.py`, `tests/test_b6_terminal_resolution.py`, `tests/test_us13_no_open_questions.py`, `tests/test_us14_next_steps_typed.py`, `tests/test_us7_spec_kit_shape.py`. These lock down the output.json schema and the atomic write/poll the round-trip would ride on — **good news: the carrier is already test-covered.**
- **Zero coverage for anything Step-7-shaped:** no test references `provenance`, `write.?back`, `change.?summary`, or conflict surfacing (`grep` over `tests/` → only `test_b4_review_delegation` / `b5_*` hits, all about the existing contract). Because the feature doesn't exist.
- **Test infra to reuse:** `tests/fixtures/synthetic_child.py` (a fake child that writes a valid output.json) is the obvious harness for testing a write-back payload end-to-end; `cast-update-spec/tests/` is the model for testing a diff-before-write/approval flow.
- **Untested critical path that will matter:** conflict detection (G3) and provenance-append (G9) have no analog tests beyond `error_memory` — whoever builds Step 7 inherits a clean test surface and should mirror `error_memory`'s upsert/escalation test style.

---

## 7. Config & Dependencies

- **Phase→artifact mapping** (`config.py:52-58`): `requirements → [requirements.human.md, refined_requirements.collab.md]`. The write-back target is fixed here.
- **Authorship config** (`config.py:60-76`): `AUTHORSHIP_TYPES`, `ARTIFACT_DEFAULTS` — extend here if provenance grows a vocabulary (e.g. an `origin_phase` dimension).
- **No realtime transport:** stack is FastAPI + Jinja + **HTMX polling** (`grep` for SSE/websocket → none in `cast_server/`). Notifications are pull-based via `HX-Trigger` toasts (`utils/responses.py:toast_header`) and `needs_attention` badges. FR-019 must work within poll-and-flag unless a transport is added (out of scope for v2 per the broader spec).
- **Libraries already present:** `pydantic` (output model + would model a writeback payload), `markdown` (`api_artifacts.py:5` — render), `pyyaml` (goal render), stdlib `sqlite3`, `hashlib`/`re` (the error-memory hashing toolkit — reusable for conflict detection). **No diff library** is vendored — an element-diff (FR-017) would need one added or hand-rolled.
- **External constraint (G7):** `docs/specs/cast-delegation-contract.collab.md` fixes "server never writes artifact files." Any write-back implementation that puts file-writing in cast-server violates a ratified spec — the writer must be an agent.

---

## Key Takeaways

1. **The single biggest constraint: Step 7 is blocked on Step 2's stable element identity (G2).** A write-back targeting "FR-014" needs a durable anchor that survives re-render and re-refinement; today `FR-014` is just text in a markdown file with no DB referent. Until elements have IDs, every round-trip feature (provenance, conflict, change-summary) degrades to fragile text matching. This dependency is already correctly sequenced in `steps.ai.md` — confirmed by the code.

2. **Nothing round-trips today, but four primitives already solve the hard sub-problems.** Provenance → `error_memory.run_ids` append-list. Conflict/dedup → `error_memory.pattern_hash` content-addressing + the `>=3 escalated` surface-not-silent pattern. Surgical additive edit → `orchestration_service.update_manifest_status` (edit one ID-keyed row, leave the rest byte-identical = FR-018 "additions not rewrites"). Render sync → `context_map.ensure_context_map` mtime staleness. **Step 7 is an assembly job, not a from-scratch invention.**

3. **`cast-update-spec` is the proven template for the *write-back protocol* (diff → approve → version-bump → changelog), and its "single write path, everyone else flags" discipline is the right architecture** — but it is human-triggered and conflict-blind. Step 7 = `cast-update-spec`'s protocol + a downstream-agent trigger (the `output.json` artifact carrier) + element IDs + a real conflict comparator.

4. **What would break on the naive approach:** building round-trip on the existing requirements-edit path (`api_artifacts.save_artifact`'s `write_text` overwrite, G4) reproduces the exact silent-overwrite/drift bug US7 exists to kill — and putting the file write in cast-server violates the delegation contract (G7). The write-back must be performed by an **agent** through the `output.json` door (FR-013's "agent-as-source" is therefore not just future-facing — it's *architecturally mandatory* here), with the server only observing.

5. **The most impactful, low-friction opportunity:** the `output.json` contract is additive-evolution-safe ("parents ignore unknown fields") and already test-covered (`b5_*`). A `requirements_writeback` artifact type (or typed field) lets a downstream agent emit a structured, provenance-tagged change *today* without breaking any existing parent — that is the cheapest possible seam to land the round-trip on, and it reuses the `human_action_needed → needs_attention` rail for FR-019 notification.

6. **Notification is the soft spot.** Poll-based `needs_attention` is a boolean; FR-019 wants "what changed + from where." This is a content/structure gap, not an architecture gap — extend the run's surfaced payload with a structured change descriptor; no new transport (SSE/websocket) is needed for v2.

7. **The store-polarity question (Step 2) is de-risked: both polarities already ship.** "DB-canonical → generated file render" exists (`goal.yaml`) and "file-canonical, server reads through" exists (`output.json` / delegation contract). Step 7 works under either — but it strongly *prefers* DB-or-structured element identity, because every round-trip operation (anchor, diff, conflict, provenance) is trivial against IDs and painful against raw text.

## Key Files
- `cast-server/cast_server/models/agent_output.py` — the v2 output contract; the natural write-back carrier (human_action_needed/artifacts).
- `cast-server/cast_server/services/agent_service.py:1702-1844` — `_finalize_run()`: where output.json is ingested and `needs_attention` is set; the hook point for FR-019.
- `cast-server/cast_server/services/error_memory_service.py` — provenance (`run_ids`), content-hash conflict/dedup (`pattern_hash`), surface-not-silent escalation, feedback-loop injection. The strongest reusable analog.
- `agents/cast-update-spec/cast-update-spec.md` — proven diff→approve→version-bump→changelog write-back protocol + single-write-path discipline.
- `cast-server/cast_server/services/orchestration_service.py:218-259` — `update_manifest_status()`: surgical ID-keyed markdown edit (FR-018 "additions not rewrites" precedent).
- `cast-server/cast_server/services/goal_service.py:337-363` — `_write_goal_yaml()`: DB-canonical → AUTO-GENERATED read-only file render pattern.
- `cast-server/cast_server/services/context_map.py:87-153` — `ensure_context_map()`: derived-render staleness sync (mtime-based).
- `cast-server/cast_server/routes/api_artifacts.py:81-107` — `save_artifact()`: the blind-overwrite edit path (the anti-pattern to avoid; G4).
- `cast-server/cast_server/config.py:52-76` — PHASE_ARTIFACTS (write-back target) + AUTHORSHIP_TYPES/ARTIFACT_DEFAULTS (file-granular provenance).
- `cast-server/cast_server/db/schema.sql` — confirms no requirement/element/version/comment/conflict tables exist.
- `docs/specs/cast-delegation-contract.collab.md` — "server never writes artifact files" (G7); the constraint that forces the writer to be an agent.
- `docs/specs/cast-output-json-contract.collab.md` — additive-evolution rule that lets a write-back payload ride output.json safely.
- `cast-server/cast_server/services/subagent_invocation_service.py` — parent↔child wiring (the existing up-tree round-trip the down-tree write-back parallels).
- `tests/test_b5_atomic_write.py` / `tests/test_b5_file_polling.py` / `tests/fixtures/synthetic_child.py` — the carrier's existing test coverage + the harness to reuse for write-back tests.
